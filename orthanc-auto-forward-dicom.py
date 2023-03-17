import orthanc, json

# The list of Orthanc DICOM Nodes to forward to. If left empty, the list is loaded dynamically on start-up and forwarding is enabled to ALL DICOM Nodes
MODALITY_LIST = []
# C-Store configuration, see https://api.orthanc-server.com/#tag/Networking/paths/~1modalities~1{id}~1store/post
moveOriginatorAet = 'MoveOriginatorAet'
moveOriginatorID = 0

def OnChange(changeType, level, resourceId):
    global MODALITY_LIST, moveOriginatorAet, moveOriginatorID

    if changeType == orthanc.ChangeType.ORTHANC_STARTED: # Server start-up
        if len(MODALITY_LIST) == 0:
            MODALITY_LIST = json.loads(orthanc.RestApiGet('/modalities/'))
        print('Modality list: %s' % MODALITY_LIST)

    if changeType == orthanc.ChangeType.STABLE_STUDY: # Study has stopped receiving news instances/series
        print('Stable study: %s' % resourceId)
        for modality in MODALITY_LIST:
            orthanc.RestApiPost(f'/modalities/{modality}/store', '{"Asynchronous": false,"Compress": true,"Permissive": true,"Priority": 0,"Resources": ["' + resourceId + '"],"Synchronous": false, "MoveOriginatorAet": "' + moveOriginatorAet + '", "MoveOriginatorID": ' + str(moveOriginatorID) + ', "Permissive": true, "StorageCommitment": true}')


orthanc.RegisterOnChangeCallback(OnChange)
