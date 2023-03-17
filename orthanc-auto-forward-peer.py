import orthanc, json

# The list of Orthanc Peers to forward to. If left empty, the list is loaded dynamically on start-up and forwarding is enabled to ALL peers
PEER_LIST = []

def OnChange(changeType, level, resourceId):
    global PEER_LIST

    if changeType == orthanc.ChangeType.ORTHANC_STARTED: # Server start-up
        if len(PEER_LIST) == 0:
            PEER_LIST = json.loads(orthanc.RestApiGet('/peers/'))
        print('Peer list: %s' % PEER_LIST)

    if changeType == orthanc.ChangeType.STABLE_STUDY: # Study has stopped receiving news instances/series
        print('Stable study: %s' % resourceId)
        for peer in PEER_LIST:
            orthanc.RestApiPost(f'/peers/{peer}/store', '{"Asynchronous": false,"Compress": true,"Permissive": true,"Priority": 0,"Resources": ["' + resourceId + '"],"Synchronous": false}')


orthanc.RegisterOnChangeCallback(OnChange)
