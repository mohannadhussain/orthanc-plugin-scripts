FROM jodogne/orthanc-python
RUN apt-get update && apt-get install -y python3-pip
RUN python3 -m pip install requests
