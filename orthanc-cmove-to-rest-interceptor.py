'''
NOTE: The Orthanc Docker image won't contain additional packages, like requests. Therefore,
    you'll have to build your own image and add these dependencies using pip. See example at:
    https://stackoverflow.com/questions/66595413/getting-no-module-named-requests-with-jodogne-orthanc-python
'''
import orthanc, sys, json, requests


def cmove_to_rest(**request):
    '''
    Sample request:
    {
        "AccessionNumber": "",
        "Level": "STUDY",
        "OriginatorAET": "BLAH",
        "OriginatorID": 1,
        "PatientID": "",
        "SOPInstanceUID": "",
        "SeriesInstanceUID": "",
        "SourceAET": "ORTHANC",
        "StudyInstanceUID": "1.3.6.1.4.1.14519.5.2.1.6279.6001.300027087262813745730072134723",
        "TargetAET": "BLAH"
    }
    '''
    level = request['Level']
    if level != 'STUDY':
        raise Exception("Cannot handle any C-MOVE **not** on the STUDY level")

    study_uid = request['StudyInstanceUID'] if 'StudyInstanceUID' in request else None
    target_aet= request['TargetAET']

    if study_uid is None or study_uid == '':
        raise Exception("Cannot handle any C-MOVE without Study Instance UID")

    # Make call to RESTful API and provide these two bits of information
    # GET Example
    url = f"https://myserver/endpoint?study_uid={study_uid}&target_aet={target_aet}"
    print(url)
    response = requests.request(
        method="GET",
        url=url,
        headers={'Content-Type': 'application/json'}
    )
    print(response.text)

    # POST payload Example
    '''
    payload = {'study_uid':study_uid, 'target_aet': target_aet}
    response = requests.request(
        method="POST",
        url="https://myserver/endpoint",
        headers={'Content-Type': 'application/json'},
        data=payload
    )
    print(response.text)
    '''


orthanc.RegisterMoveCallback(cmove_to_rest)