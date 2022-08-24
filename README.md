# OVOS Local Backend

Personal mycroft backend alternative to mycroft.home, written in flask

This repo is an alternative to the backend meant for personal usage, this allows you to run without mycroft servers

:warning: there are no user accounts :warning:

This is NOT meant to provision third party devices, but rather to run on the mycroft devices directly or on a private network

No frontend functionality is provided, for that check out the companion project [OVOS Dashboard](https://github.com/OpenVoiceOS/OVOS-Dashboard)

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
  "wolfram_key": "BUNDLED_DEMO_KEY",
  "owm_key": "BUNDLED_DEMO_KEY",
  "lang": "en-us",
  "date_format": "DMY",
  "system_unit": "metric",
  "time_format": "full",
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

- stt config follows the same format of mycroft.conf and
  uses [ovos-plugin-manager](https://github.com/OpenVoiceOS/OVOS-plugin-manager)
- if override location is True, then location will be set to configured value
- if geolocate is True then location will be set from your ip address
- set wolfram alpha key for wolfram alpha proxy expected by official mycroft skill
- set open weather map key for wolfram alpha proxy expected by official mycroft skill
- if record_wakewords is set, recordings can be found at `DATA_PATH/wakewords`
- if record_utterances is set, recordings can be found at `DATA_PATH/utterances`


## Databases

Since the local backend is not meant to provision hundreds of devices or manage user accounts it works only with [json databases](https://github.com/OpenJarbas/json_database)

- metadata about uploaded wakewords can be found at `~/.local/share/json_database/ovos_wakewords.jsondb`
- metadata about uploaded utterances can be found at `~/.local/share/json_database/ovos_utterances.jsondb`
- database of uploaded metrics can be found at `~/.local/share/json_database/ovos_metrics.jsondb`
- paired devices database can be found at `~/.local/share/json_database/ovos_devices.json`
- per device skill settings database can be found at `~/.local/share/json_database/ovos_skill_settings.json`
- shared skill settings database can be found at `~/.local/share/json_database/ovos_shared_skill_settings.json`

metrics, wake words and utterances respect the individual devices `opt_in` flag, nothing will be saved unless devices opt_in (default True)

## Admin api

Since there is no UI some endpoints are provided to manage your devices

By default admin api is disabled, to enable it add `"admin_key": "unique_super_secret_key"` to the backend configuration

you need to provide that key in the request headers for [admin endpoints](./ovos_local_backend/backend/admin.py)

TODO - [selene_api](https://github.com/OpenVoiceOS/selene_api) support

## Device Settings

Each paired device has a few settings that control behaviour backend side

- `name` - default `"Device-{uuid}"`, friendly device name for display
- `opt_in` - default `True`, flag to control if metrics and speech from this device will be saved
- `device_location` - default `"unknown"`, friendly name for indoor location
- `email` - default from backend config, email to send notifications to
- `isolated_skills` - default `False`, flag to control if skill settings are shared across devices (ovos only)


- you can change these settings per device via the [admin api](./ovos_local_backend/backend/admin.py)
- you can also change these settings per device by manually editing paired devices database

## Location

Device location can be updated via the backend, mycroft-core will request this info on it's own from time to time

- if override location is True, then location will be set to configured default value
- if geolocate is True then location will be set from your ip address
- you can set a default location per device via the [admin api](./ovos_local_backend/backend/admin.py)
- you can also set a default location per device by manually editing paired devices database

## Device Preferences

Some settings can be updated via the backend, mycroft-core will request this info on it's own from time to time

default values comes from the local backend config file
```json
{
  "lang": "en-us",
  "date_format": "DMY",
  "system_unit": "metric",
  "time_format": "full"
}
```

- these settings are also used for wolfram alpha / weather default values
- you can set these values per device via the [admin api](./ovos_local_backend/backend/admin.py)
- you can also set these values per device by manually editing paired devices database

## Skill settings

in selene all device share skill settings, with local backend you can control this per device via `isolated_skills` flag

"old selene" supported a single endpoint for both skill settings and settings meta, this allowed devices both to download and upload settings

"new selene" split this into two endpoints, settingsMeta (upload only) and settings (download only), this disabled two way sync across devices

- you can set `isolated_skills` per device via the [admin api](./ovos_local_backend/backend/admin.py)
- you can also set `isolated_skills` per device by manually editing paired devices database
- both endpoints are available, but mycroft-core by default will use the new endpoints and does not support two way sync
- you can edit settings by using the "old selene" endpoint
- you can also edit settings by manually editing settings database

## Email

Mycroft skills can request the backend to send an email to the account used for pairing the device

- Email will be sent to a pre-defined recipient email since there are no user accounts
- you can set a recipient email per device via the [admin api](./ovos_local_backend/backend/admin.py)
- you can set a recipient email per device by manually editing paired devices database

with the local backend you need to configure your own SMTP server and recipient email, add the following section to your .conf

```json
{
  "email": {
    "smtp": {
      "username": "sender@gmail.com",
      "password": "123456",
      "host": "",
      "port": 465
    },
    "recipient": "receiver@gmail.com"
  }
}
```

If using gmail you will need to [enable less secure apps](https://hotter.io/docs/email-accounts/secure-app-gmail/)

## Mycroft Setup

update your mycroft config to use this backend, delete `identity2.json` and restart mycroft

```json
{
  "server": {
    "url": "http://0.0.0.0:6712",
    "version": "v1",
    "update": true,
    "metrics": true
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

## Docker

There is also a docker container you can use

```bash
docker run -p 8086:6712 -d --restart always --name local_backend ghcr.io/openvoiceos/local-backend:dev
```

## Project Timeline

- Jan 2018 - [initial release](https://github.com/OpenVoiceOS/OVOS-mock-backend/tree/014389065d3e5c66b6cb85e6e77359b6705406fe) of reverse engineered mycroft backend - by JarbasAI
- July 2018 - Personal backend [added to Mycroft Roadmap](https://mycroft.ai/blog/many-roads-one-destination/)
- October 2018 - Community [involved in discussion](https://mycroft.ai/blog/mycroft-personal-server-conversation/)
- Jan 2019 - JarbasAI implementation [adopted by Mycroft](https://github.com/MycroftAI/personal-backend/tree/31ee96a8189d96f8102276bf4b9073811ee9a9b2)
  - NOTE: this should have been a fork or repository transferred, but was a bare clone
  - Original repository was archived
- October 2019 - Official mycroft backend [open sourced under a viral license](https://mycroft.ai/blog/open-sourcing-the-mycroft-backend/)
- Jun 2020 - original project [repurposed to be a mock backend](https://github.com/OpenJarbas/ZZZ-mock-backend) instead of a full alternative, [skill-mock-backend](https://github.com/JarbasSkills/skill-mock-backend) released
- Jan 2021 - mock-backend adopted by OpenVoiceOS, original repo unarchived and ownership transferred
