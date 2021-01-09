# OVOS Local Backend

Personal mycroft backend alternative to mycroft.home, written in flask

This repo is an alternative to the backend meant for personal usage, this allows you to run fully offline, This is NOT meant to be used as a backend, but rather to run on the mycroft
devices directly.

No frontend functionality is provided, you will lose:

- web skill settings interface
- web device configuration interface

For a full backend experience, the official mycroft backend has been open sourced, read the [blog post](https://mycroft.ai/blog/open-sourcing-the-mycroft-backend/)

NOTE: There is no pairing, devices will just work

## Install

from pip

```bash
pip install ovos-local-backend
```

## Configuration

configure backend by editing/creating ```~/.config/json_database/ovos_backend.json```

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
  "data_path": "~",
  "record_utterances": false,
  "record_wakewords": false,
  "wolfram_key": "BUNDLED_DEMO_KEY",
  "owm_key": "BUNDLED_DEMO_KEY",
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
    - a searchable [json_database](https://github.com/HelloChatterbox/json_database) can be found at `~/.local/share/json_database/ovos_wakewords.jsondb`
- if record_utterances is set, recordings can be found at `DATA_PATH/utterances`
    - a searchable [json_database](https://github.com/HelloChatterbox/json_database) can be found at `~/.local/share/json_database/ovos_utterances.jsondb`
- if mycroft is configured to upload metrics a searchable [json_database](https://github.com/HelloChatterbox/json_database) can be found at `~/.local/share/json_database/ovos_metrics.jsondb`

### Email

add the following section to your .conf

```json
"email": {
  "username": "sender@gmail.com",
  "password": "123456",
  "to": "receiver@gmail.com",
}
```
This uses [yagmail](https://github.com/kootenpv/yagmail), it is centered on gmail usage, but should also work with other email providers

You will need to [enable less secure apps](https://hotter.io/docs/email-accounts/secure-app-gmail/) in your gmail account

I recommend you setup an [Application Specific Password](https://support.google.com/accounts/answer/185833)


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
$ ovos-local-backend -h
usage: ovos-local-backend [-h] [--flask-port FLASK_PORT] [--flask-host FLASK_HOST]

optional arguments:
  -h, --help            show this help message and exit
  --flask-port FLASK_PORT
                        Mock backend port number
  --flask-host FLASK_HOST
                        Mock backend host

```

# Project Timeline

- Jan 2018 - [initial release](https://github.com/OpenVoiceOS/OVOS-mock-backend/tree/014389065d3e5c66b6cb85e6e77359b6705406fe) of reverse engineered mycroft backend - by JarbasAI
- July 2018 - Personal backend [added to Mycroft Roadmap](https://mycroft.ai/blog/many-roads-one-destination/)
- October 2018 - Community [involved in discussion](https://mycroft.ai/blog/mycroft-personal-server-conversation/)
- Jan 2019 - JarbasAI implementation [adopted by Mycroft](https://github.com/MycroftAI/personal-backend/tree/31ee96a8189d96f8102276bf4b9073811ee9a9b2)
  - NOTE: this should have been a fork or repository transferred, but was a bare clone
  - Original repository was archived
- October 2019 - Official mycroft backend [open sourced under a restrictive license](https://mycroft.ai/blog/open-sourcing-the-mycroft-backend/)
- Jun 2020 - original project [repurposed to be a mock backend](https://github.com/OpenJarbas/ZZZ-mock-backend) instead of a full alternative, [skill-mock-backend](https://github.com/JarbasSkills/skill-mock-backend) released
- Jan 2021 - mock-backend adopted by OpenVoiceOS, original repo unarchived and ownership transferred