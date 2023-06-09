# OVOS Personal Backend

Personal backend for OpenVoiceOS, written in flask

This allows you to manage multiple devices from a single location

:warning: there are no user accounts :warning:

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
- [ovos-stt-plugin-selene](https://github.com/OpenVoiceOS/ovos-stt-plugin-selene) - stt plugin for selene/local backend (DEPRECATED)


## Configuration

configure backend by editing/creating ```~/.config/mycroft/ovos_backend.conf```


```json
{
  "lang": "en-us",
  "date_format": "DMY",
  "system_unit": "metric",
  "time_format": "full",
  "location": {
    "city": {"...": "..."},
    "coordinate": {"...": "..."},
    "timezone": {"...": "..."}
  },

  "stt": {
    "module": "ovos-stt-plugin-server",
    "ovos-stt-plugin-server": {"url": "https://stt.openvoiceos.org/stt"}
  },

  "server": {
    "admin_key": "",
    "port": 6712,
    "database": "sqlite:////home/user/.local/share/ovos_backend.db",
    "skip_auth": false,
    "geolocate": true,
    "override_location": false,
    "version": "v1"
  },

  "listener": {
     "record_utterances": false,
     "record_wakewords": false
  },

  "microservices": {
    "wolfram_key": "$KEY",
    "owm_key": "$KEY",
    "email": {
       "recipient": "",
       "smtp": {
            "username": "",
            "password": "",
            "host": "smtp.mailprovider.com",
            "port": 465
       }
    }
  }

}
```

database can be sqlite or mysql
eg. `mysql+mysqldb://scott:tiger@192.168.0.134/test?ssl_ca=/path/to/ca.pem&ssl_cert=/path/to/client-cert.pem&ssl_key=/path/to/client-key.pem`


## Docker

There is also a docker container you can use

```bash
docker run -p 8086:6712 -d --restart always --name local_backend ghcr.io/openvoiceos/local-backend:dev
```
