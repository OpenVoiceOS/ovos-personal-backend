# OVOS Personal Backend

Personal mycroft backend alternative to mycroft.home, written in flask

This repo is an alternative to the backend meant for personal usage, this allows you to run without mycroft servers

:warning: there are no user accounts :warning:

This is NOT meant to provision third party devices, but rather to run on the mycroft devices directly or on a private network

Documentation can be found at https://openvoiceos.github.io/community-docs/personal_backend

NOTES: 
- this backend moved to SQL databases on release 0.2.0, json databases from older version are not compatible
- at the time of writing, backend manager does not yet work with this backend version
- backend-client now includes a CRUD api to interact with databases https://github.com/OpenVoiceOS/ovos-backend-client/pull/30


## Install

from pip

```bash
pip install ovos-local-backend
```


## Companion projects

- [ovos-backend-client](https://github.com/OpenVoiceOS/ovos-backend-client) - reference python library to interact with backend
- [ovos-backend-manager](https://github.com/OpenVoiceOS/ovos-backend-manager) - graphical interface to manage all things backend
- [ovos-stt-plugin-selene](https://github.com/OpenVoiceOS/ovos-stt-plugin-selene) - stt plugin for selene/local backend


## Configuration

configure backend by editing/creating ```~/.config/json_database/ovos_backend.json```

see default values [here](./ovos_local_backend/configuration.py)

```json
{
  "stt": {
    "module": "ovos-stt-plugin-server",
    "ovos-stt-plugin-server": {"url": "https://stt.openvoiceos.com/stt"}
  },
  "backend_port": 6712,
  "geolocate": true,
  "override_location": false,
  "api_version": "v1",
  "data_path": "~",
  "record_utterances": false,
  "record_wakewords": false,
  "wolfram_key": "$KEY",
  "owm_key": "$KEY",
  "lang": "en-us",
  "date_format": "DMY",
  "system_unit": "metric",
  "time_format": "full",
  "default_location": {
    "city": {"...": "..."},
    "coordinate": {"...": "..."},
    "timezone": {"...": "..."}
  }
}
```

- stt config follows the same format of mycroft.conf and
  uses [ovos-plugin-manager](https://github.com/OpenVoiceOS/OVOS-plugin-manager)
- set wolfram alpha key for wolfram alpha proxy expected by official mycroft skill
- set open weather map key for weather proxy expected by official mycroft skill


## Docker

There is also a docker container you can use

```bash
docker run -p 8086:6712 -d --restart always --name local_backend ghcr.io/openvoiceos/local-backend:dev
```
