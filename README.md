# Orthanc Plugin Scripts 
A collection of Orthanc plugins, written in Python, to add miscellaneous functionality to the already very utilitarian 
[Orthanc DICOM Server](https://www.orthanc-server.com/).

## Before you get started
Ensure the python plugin is enabled in `orthanc.json` 😉️

Some of these scripts make use of additional Python packages, e.g. `requests`, which are not available out of the box
in standard Docker images such as `jodogne/orthanc-python`, therefore, you'll need to build an image that incorporates 
them. For convenience, I've provided a `Dockerfile` in this repository that allows you to build one like so:
```commandline
docker build . -t mohannadhussain/orthanc-python-plugins
```

Once built, you can run the container and map any of these python scripts into it like so:
```commandline
docker run -d -p 4242:4242 -p 8042:8042 --rm -v /path-to-your-orthanc-config-file/orthanc.json:/etc/orthanc/orthanc.json:ro -v /path-to-this-repo/orthanc-plugin-scripts/orthanc-cmove-to-rest-interceptor.py:/etc/orthanc/orthanc-cmove-to-rest-interceptor.py mohannadhussain/orthanc-python-plugins
```

## Plugin Scripts In This Package

### 1. Orthanc Auto Forwarding/Routing
Adds auto-forwarding functionality to Orthanc as a plugin, with automatic initialization of destinations. There are two 
versions of this script:
1. **Modalities**: Forwards studies to DICOM destinations using DIMSE C-STORE. Probably the default choice for most people.
2. **Peers**: Forwards to other Orthanc instances using Orthanc's APIs over HTTP/HTTPS.

Once configured, Upload/C-STORE studies, and after X seconds, you should see them being forwarded. The number of seconds depends on the value of `StableAge` in your `orthanc.json` - default is 60 seconds.

### 2. Orthanc Purge Old Studies
Simple plugin to allow purging studies based on their age. It registers a REST API endpoint as seen below: 
```commandline
http://localhost:8042/purge-old-studies?since=20000101
```

The example above will delete any studies with a study date **on or before** January 1, 2000. I.e. the date matching is 
inclusive. If all goes well, the API will return an HTTP `200 OK` status, along with a message indicating
the number of studies purged.

### 3. Orthanc Intercept C-MOVE and convert to REST API Call
Useful for notifying a service/API outside Orthanc of an incoming C-MOVE request. Say you want to create audit records 
of these calls elsewhere. Or perhaps, you have other DICOM nodes that may contain the requested study. The script shows
an example of performing such calls over HTTP GET and POST, making it easy to adapt to anyone's needs.

Once configured, you can use a toolkit like [dcm4che](https://github.com/dcm4che/dcm4che) to issue a C-MOVE request, e.g.:
```commandline
~/dcm4che-5.23.2/bin/movescu -b BLAH -c ORTHANC@localhost:4242 --dest BLAH -m StudyInstanceUID=1.2.3.4
```
Doing so will cause the plugin to make a REST call (over GET and/or POST) to your service/API, providing the Study 
Instance UID (1.2.3.4) and target DICOM AET (BLAH).


### 4. Orthanc Rule-Based DICOM Router
Sometimes you need to forward certain studies based on somewhat-dynamic rules. This plugin demonstrates a sample 
implementation that utilizes the [Python Rule-Engine](https://zerosteiner.github.io/rule-engine/index.html) to apply 
human-readable logic. Example rules:
```commandline
'CT' in ModalitiesInStudy and StudyDate > 20000101
or 
PatientSex == 'F' and 'ABDOMEN' in StudyDescription
```
As incoming studies are marked stable (see `StableAge` in Orthanc's configuration), the rules are applied in sequence. 
Each rule can then specify one or more destinations (Orthanc Modalities, i.e. other DICOM servers, not literally 
modalities) to forward matching studies to.

The plugin also adds two features to be even more useful...

#### 1. Allow rules to be updated via REST 
The JSON-based rules can be updated via a REST API call. The plugin listens at `http://localhost:4242/dicom-router/rules`
where you can post something like the JSON structure below to update the rules:
```commandline
[
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
```
#### 2. Persist rules onto disk storage
When the rules are updated, the plugin writes a cached copy onto disk storage (default location is
`/var/lib/orthanc/db/dicom-routing-rules.json` but it is configurable). When the server starts up it attempts to read a 
previously cached copy of the rules, reducing the burden of having to initialize the rules after every restart.

#### Notes
1. The script works st the study level, but the logic can easily be extended to work at the series or even instance level.
2. Logic to convert DICOM attributes from strings to native python types (integer, arrays, etc) is hacky and leaves much to be desired. You've been warned!!
3. When updating rules, no error checking is being performed at this time so that part isn't very robust.
3. Due to python dependencies, you'll need to build your own Orthanc image that incorporates those python packages
4. Important: show the Orthanc team some love! Consider [donating](https://opencollective.com/orthanc).


## Usage
### File placement
If you are running Orthanc via Docker, then you can map the script(s) into the container like so:
#### 1. `docker run`
Addd a `-v` like so:

```-v /path/to/python-script/orthanc-auto-forward-peer.py:/etc/orthanc/orthanc-auto-forward-peer.py:ro```

#### 2. `docker-compose`
Under `volumes` add a mapping like so:

```- /path/to/python-script/orthanc-auto-forward-peer.py:/etc/orthanc/orthanc-auto-forward-peer.py```

### Configuration
Whether you are using docker or have Orthanc installed directly into your Operating System, you now have to add the script to your `orthanc.json` like so:
`"PythonScript" : "/etc/orthanc/orthanc-auto-forward-peer.py"`
Currently, Orthanc only allows configuring one Python script at a time. If you need functionality from multiple scripts, 
you'll have to manually combine them into one Python file, then point to that file in your configuration.

---
## Licensing & Contribution
* License: GPLv3 as mandated by [Orthanc's licensing model](https://book.orthanc-server.com/faq/licensing.html)
* Condtribution: Fork this repository, make your changes, then submit a pull request.
* Other: Contact [Mohannad Hussain](https://github.com/mohannadhussain) 
