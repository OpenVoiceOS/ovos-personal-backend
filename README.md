# Mock Mycroft Backend

Personal mycroft backend alternative to mycroft.home, written in flask

This repo is an alternative to the backend meant for personal usage, this allows you to run fully offline, This is NOT meant to be used as a backend, but rather to run on the mycroft
devices directly.

No frontend functionality is provided, you will lose:

- web skill settings interface
- web device configuration interface
- send emails functionality (WIP)

For a full backend experience, the official mycroft backend has been open sourced, read the [blog post](https://mycroft.ai/blog/open-sourcing-the-mycroft-backend/)

NOTE: There is no pairing, devices will just work

## Install

from pip

```bash
pip install mock-mycroft-backend
```

## Configuration

configure backend by editing/creating ```~/.config/json_database/mycroft_backend.json```

default configuration is

```json
{
  "stt": {
    "module": "google"
  },
  "backend_port": 6712,
  "geolocate": false,
  "override_location": false,
  "api_version": "v1",
  "data_path": "~/.mycroft/mock_backend",
  "record_utterances": false,
  "record_wakewords": false,
  "wolfram_key": "FREE_DEMO_KEY_PROBABLY_RATE_LIMITED",
  "owm_key": "FREE_DEMO_KEY_PROBABLY_RATE_LIMITED",
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
  }
}
```
- stt config follows the same format of mycroft.conf and uses [speech2text](https://github.com/HelloChatterbox/speech2text)
- if override location is True, then location will be set to configured value
- if geolocate is True then location will be set from your ip address
- set wolfram alpha key for wolfram alpha proxy expected by official mycroft skill
- set open weather map key for wolfram alpha proxy expected by official mycroft skill
- if record_wakewords is set, recordings can be found at `DATA_PATH/wakewords`
    - a searchable [json_database](https://github.com/HelloChatterbox/json_database) can be found at `~/.local/share/json_database/mycroft_wakewords.jsondb`
- if record_utterances is set, recordings can be found at `DATA_PATH/utterances`
    - a searchable [json_database](https://github.com/HelloChatterbox/json_database) can be found at `~/.local/share/json_database/mycroft_utterances.jsondb`
- if mycroft is configured to upload metrics a searchable [json_database](https://github.com/HelloChatterbox/json_database) can be found at `~/.local/share/json_database/mycroft_metrics.jsondb`

### Email

CONFIGURATION NOT YET IMPLEMENTED

will work if [default values](https://pythonhosted.org/Flask-Mail/) are valid

add the following section to your .conf

```json
{
  "email": "emails_are_sent_to_this_address"
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
   },
   "listener": {
        "wake_word_upload": {
            "url": "http://0.0.0.0:6712/precise/upload"
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

# Credits

JarbasAI