# Mock Mycroft Backend

Personal mycroft backend alternative to mycroft.home, written in flask

Official mycroft backend has been open sourced, read the [blog post](https://mycroft.ai/blog/open-sourcing-the-mycroft-backend/)

This repo is an alternative to the backend meant for personal usage, this allows you to run fully offline, see [Mock Backend Skill](https://github.com/JarbasSkills/skill-mock-backend)

No frontend functionality is provided


## Install

from pip

```bash
pip install mock-mycroft-backend
```

## Configuration

configure backend by editing/creating ```~/.mycroft/mock_backend/mock_backend.conf```

```json
{
    "lang": "en-us",
    "stt": {
        "module": "google"
    },
    "backend_port": 6712,
    "ssl": false,
    "ssl_cert": null,
    "ssl_key": null,
    "mail_user": "xxx@gmail.com",
    "mail_password": "xxx",
    "mail_server": "smtp.googlemail.com",
    "mail_port": 465,
    "default_location": {
        "city": {
            "code": "Lawrence",
            "name": "Lawrence",
            "state": {
                "code": "KS",
                "name": "Kansas",
                "country": {
                    "code": "US",
                    "name": "United States"
                }
            }
        },
        "coordinate": {
            "latitude": 38.971669,
            "longitude": -95.23525
        },
        "timezone": {
            "code": "America/Chicago",
            "name": "Central Standard Time",
            "dstOffset": 3600000,
            "offset": -21600000
        }
    },
    "geolocate": false,
    "override_location": false,
    "data_dir": "/home/user/.mycroft/mock_backend",
    "metrics_db": "/home/user/.mycroft/mock_backend/metrics.json",
    "api_version": "v1",
    "email": "xxx@gmail.com",
    "record_utterances": false,
    "utterances_path": "/home/user/.mycroft/mock_backend/utterances",
    "utterances_db": "/home/user/.mycroft/mock_backend/utterances.json"
}
```

## Mycroft Setup

update your mycroft config to use this backend

```json
{
    "server": {
        "url": "http://0.0.0.0:6712",
        "version": "v1",
        "update": true,
        "metrics": true
      },
    "tts": {
      "module":"mimic2",
	  "mimic2": {
	      "url": "http://0.0.0.0:6712/synthesize/mimic2/kusal/en?text="
      }
   }
}
```
     

## usage

start backend 

```bash
$ mock-mycroft-backend -h
usage: mock-mycroft-backend [-h] [--flask-port FLASK_PORT] [--flask-host FLASK_HOST]

optional arguments:
  -h, --help            show this help message and exit
  --flask-port FLASK_PORT
                        Mock backend port number
  --flask-host FLASK_HOST
                        Mock backend host

```

