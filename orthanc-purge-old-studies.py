import orthanc, sys, json, re

REGEX_DICOM_DATE = re.compile("[0-9]{8}") # DICOM date format, e.g. 20231107

def purge_old_studies(output, uri, **request):
    if request['method'] != 'GET':
        output.SendMethodNotAllowed('GET')
        return

    # Check a valid date was provided
    study_date = request['get']['since'] if 'since' in request['get'] else None
    if study_date is None or study_date == '' or not REGEX_DICOM_DATE.fullmatch(study_date):
        msg = f"Invalid DICOM date supplied for the 'since' parameter: {study_date}"
        output.SendHttpStatus(400, msg, len(msg))
        return

    search_query = {
          "CaseSensitive": False,
          "Expand": False,
          "Full": False,
          "Level": "Study",
          "Limit": 0,
          "Query": {
              "StudyDate": f"19000101-{study_date}" # matching is inclusive
          },
          "Short": True,
          "Since": 0
    }

    try:
        # Step 1: Get a list of all studies pre-dating the provided date
        studies = json.loads(orthanc.RestApiPost('/tools/find', json.dumps(search_query))) # Returns a list of studies

        # Step 2: Perform a bulk delete of said studies
        orthanc.RestApiPost('/tools/bulk-delete', json.dumps({ "Resources": studies })) # Does not return anything

        # Return 200 OK
        msg = f"Successfully deleted {len(studies)} studies"
        print(msg)
        output.SendHttpStatus(200, msg, len(msg))
    except:
        errorInfo = sys.exc_info()
        msg = "Unknown error occurred. Error message was: " + errorInfo[0]
        print(f"{msg} \n {errorInfo[2]}")
        output.SendHttpStatus(500, msg, len(msg))
    return

orthanc.RegisterRestCallback('/purge-old-studies', purge_old_studies)