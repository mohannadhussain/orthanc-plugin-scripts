# Orthanc Auto Forward
Python scripts to add auto-forwarding functionality to Orthanc as a plugin

---
# Usage
## 1. Note
The python plugin must be enabled for this to work.

## 2. File placement
If you are running Orthanc via Docker, then you can map the script(s) into the container like so:
### `docker run`
Addd a `-v` like so:

```-v /path/to/python-script/orthanc-auto-forward-peer.py:/etc/orthanc/orthanc-auto-forward-peer.py:ro```

### `docker-compose`
Under `volumes` add a mapping like so:

```- /path/to/python-script/orthanc-auto-forward-peer.py:/etc/orthanc/orthanc-auto-forward-peer.py```

## 3. Configuration
Whether you are using docker or have Orthanc installed directly into your Operating System, you now have to add the script to your `orthanc.json` like so:

```"PythonScript" : "/etc/orthanc/orthanc-auto-forward-peer.py"```

## 4. Restart Orthanc
Upload/C-STORE studies, and after X second, you should see them being forwarded. The number of seconds depends on the value of `StableAge` in your `orthanc.json` - default is 60 seconds.

---
# Contribution
* Code: Fork this repository, make your changes, then submit a poll request.
* Other: Contact [Mohannad Hussain](https://github.com/mohannadhussain) 
