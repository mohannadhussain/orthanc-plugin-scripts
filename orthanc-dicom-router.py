import orthanc, json, rule_engine
from typing import Dict

# C-Store configuration, see https://api.orthanc-server.com/#tag/Networking/paths/~1modalities~1{id}~1store/post
moveOriginatorAet = 'MoveOriginatorAet'
moveOriginatorID = 0
requestedTags = '00080061' # Comma separated
rulesFilePath = '/var/lib/orthanc/db/dicom-routing-rules.json' # Somewhere safe to be persisted if the server restarts


# The routing rules - they can be updated via a POST to /dicom-router/rules
ROUTING_RULES = [
    {
      "rule": "'CT' in ModalitiesInStudy and StudyDate > 20000101",
      "destinations": [
        "somedestination", "siimhackathon"
      ]
    },
    {
      "rule": "PatientSex == 'F' and 'ABDOMEN' in StudyDescription",
      "destinations": [
        "researchpacs"
      ]
    }
]


def initializeRules():
    """
    Compiles all the rules pre-emptively for maximum performance
    """
    global ROUTING_RULES
    for rule in ROUTING_RULES:
        rule["compiledRule"] = rule_engine.Rule(rule["rule"])
    print("Compiled all rules")


def updateRules(output, uri, **request):
    """
    Allows the rules to be updated via an HTTP POST call, or inspected during run-time via HTTP GET

    :param output: Provided by the Orthanc API
    :param uri: Provided by the Orthanc API
    :param request: Provided by the Orthanc API
    :return: None
    """
    global ROUTING_RULES, rulesFilePath

    if request['method'] == 'GET': # Echo the rules back, allows to run-time introspection of rules
        # Remove the compiled rules to avoid a TypeError due to failed serialization
        rules = []
        for rule_old in ROUTING_RULES:
            rule_new = {}
            for key, value in rule_old.items():
                if key not in ["compiledRule"]:
                    rule_new[key] = value
            rules.append(rule_new)

        output.AnswerBuffer(json.dumps(rules, indent=2), 'application/json')

    elif request['method'] == 'POST': # Allow the rules to be updated
        try:
            rules = json.loads(request['body'])
            rules_str = json.dumps(rules, indent=2)
            #TODO Perform some error checking?!?
            ROUTING_RULES = rules

            # Store a copy of the rules onto disk, so they are available on start-up
            try:
                file = open(rulesFilePath, 'w')
                file.write(rules_str)
                file.close()
            except Exception as e:
                print(f"Caught an exception while attempting to write rules to {rulesFilePath}: {e}")

            print(f"Routing rules: {ROUTING_RULES}")
            initializeRules()
            output.AnswerBuffer(rules_str, 'application/json')
        except Exception as e:
            msg = f"Caught exception while updating config rules: {e}"
            print(msg)
            output.SendHttpStatus(500, msg, len(msg))
            return

    else: # Only accepts GET and POST
        output.SendMethodNotAllowed('GET,POST')
        return

orthanc.RegisterRestCallback('/dicom-router/rules', updateRules)


def readRulesFromDisk():
    """
    Reads the JSON rules from disk, if they were persisted previously

    :return: None
    """
    global rulesFilePath

    try:
        file = open(rulesFilePath, 'r')
        ROUTING_RULES = json.loads(file.read())
        print(f"Routing rules: {ROUTING_RULES}")
        file.close()
    except Exception as e:
        print(f"Caught an exception while attempting to read rules from {rulesFilePath}: {e}")

    initializeRules()


def expandDicomAttrbutes(dict_in : Dict):
    """
    Unpack DICOM data types (arrays, date/time) into native python types

    :param dict_in: The raw data from Orthanc's API to be unpacked
    :return: Updated dictionay with values coverted into python native types like integers and arrays
    """
    dict_out = {}
    for key in dict_in.keys(): #TODO This logic is too simple, there's definitely room for improvement here :)
        try:
            if "Date" in key or "Time" in key:
                dict_out[key] = float(dict_in[key])
            elif "\\" in dict_in[key]:
                dict_out[key] = dict_in[key].split("\\")
            else:
                dict_out[key] = dict_in[key]
        except Exception as e:
            print(f"Caught exception while processing key {key}: {e}")

    return dict_out

def onChange(changeType, level, resourceId):
    """
    Method listening to Orthanc's onChange event

    :param changeType: Provided by the Orthanc API
    :param level: Provided by the Orthanc API
    :param resourceId: Provided by the Orthanc API
    :return: None
    """
    global ROUTING_RULES, moveOriginatorAet, moveOriginatorID, requestedTags

    if changeType == orthanc.ChangeType.ORTHANC_STARTED: # Server start-up
        readRulesFromDisk()

    if changeType == orthanc.ChangeType.STABLE_STUDY: # Study has stopped receiving news instances/series
        # print("===========================================================")
        # print(f"Routing rules: {ROUTING_RULES}")

        study = json.loads(orthanc.RestApiGet(f'/studies/{resourceId}?requestedTags={requestedTags}'))
        study_data = expandDicomAttrbutes({**study['MainDicomTags'], **study['PatientMainDicomTags'], **study['RequestedTags']})
        #print(f"study_data={study_data}")

        for rule in ROUTING_RULES:
            if rule["compiledRule"].matches(study_data):
                #print(f"Study matched rule: {rule['rule']}")
                for modality in rule["destinations"]:
                    print(f"Forwarding study {resourceId} to modality {modality}")
                    try:
                        orthanc.RestApiPost(f'/modalities/{modality}/store', '{"Asynchronous": false,"Compress": true,"Permissive": true,"Priority": 0,"Resources": ["' + resourceId + '"],"Synchronous": false, "MoveOriginatorAet": "' + moveOriginatorAet + '", "MoveOriginatorID": ' + str(moveOriginatorID) + ', "Permissive": true, "StorageCommitment": false}')
                    except Exception as e:
                        print(f"Caught an exception while attempting to forward a study {e}")
            else:
                continue
                #print(f"Study DID NOT match rule: {rule['rule']}")


orthanc.RegisterOnChangeCallback(onChange)

