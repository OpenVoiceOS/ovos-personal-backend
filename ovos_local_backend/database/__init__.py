import json
import time
from copy import deepcopy
from typing import Tuple

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_json import NestedMutableJson
from ovos_utils.log import LOG
from ovos_local_backend.backend.decorators import requires_opt_in
from ovos_local_backend.configuration import CONFIGURATION
from ovos_local_backend.utils.geolocate import Location, get_request_location

# create the extension
db = SQLAlchemy()

_mail_cfg = CONFIGURATION.get("email", {})
_ww_cfg = CONFIGURATION.get("ww_configs", {})
_tts_cfg = CONFIGURATION.get("tts_configs", {})


def connect_db(app):
    # configure the SQLite database, relative to the app instance folder

    # "mysql+mysqldb://scott:tiger@192.168.0.134/test?ssl_ca=/path/to/ca.pem&ssl_cert=/path/to/client-cert.pem&ssl_key=/path/to/client-key.pem"
    # "sqlite:///ovos_backend.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = CONFIGURATION["database"]
    # initialize the app with the extension
    db.init_app(app)

    with app.app_context():
        db.create_all()

    return app, db


class VoiceDefinition(db.Model):
    voice_id = db.Column(db.String(255), primary_key=True)
    lang = db.Column(db.String(255), default="en-us", nullable=False)
    module = db.Column(db.String(255), default="", nullable=False)  # "module" in mycroft.conf
    voice_config = db.Column(NestedMutableJson, default={}, nullable=False)  # arbitrary data for mycroft.conf/OPM
    offline = db.Column(db.Boolean, default=False, nullable=False)
    # optional metadata
    gender = db.Column(db.String(255), default="")

    def serialize(self):
        return {
            "voice_id": self.voice_id,
            "lang": self.lang,
            "module": self.module,
            "voice_config": self.voice_config,
            "offline": self.offline,
            "gender": self.gender
        }


def get_voice_config(tts_voice: str) -> Tuple[str, dict]:
    config: dict = _tts_cfg.get(tts_voice, {})
    module = config.get("module")
    lang = config.get("lang", "en-us")
    offline = config.get("offline", False)
    gender = config.get("gender", "unknown")

    if not config:
        return None, None
    
    definition = {
        "module": module,
        "lang": lang,
        "voice_config": config,
        "offline": offline,
        "gender": gender
    }
    
    # taken from https://github.com/OpenVoiceOS/ovos-plugin-manager/pull/131
    # skip_keys = ["module", "meta"]
    # keys = sorted([f"{k}_{v}" for k, v in config.items() if k not in skip_keys])
    # voiceid = f"{module}_{lang}_{keys}.json".replace("/", "_")
    voiceid = f"{module}_{lang}_{hash(str(config))}.json"
    return voiceid, definition


def add_voice_definition(**definition) -> VoiceDefinition:
    entry = VoiceDefinition(**definition)

    db.session.add(entry)
    db.session.commit()

    return entry


def get_voice_definition(ident) -> VoiceDefinition:
    return VoiceDefinition.query.filter_by(voice_id=ident).first()


def update_voice_definition(ident, **kwargs) -> dict:

    definitions: VoiceDefinition = get_voice_definition(ident)
    if not definitions:
        definitions = add_voice_definition(voice_id=ident, **kwargs)
    
    else:
        if "lang" in kwargs:
            definitions.lang = kwargs["lang"]
        if "module" in kwargs:
            definitions.module = kwargs["module"]
        if "voice_config" in kwargs:
            definitions.voice_config = kwargs["voice_config"]
        if "offline" in kwargs:
            definitions.offline = kwargs["offline"]
        if "gender" in kwargs:
            definitions.gender = kwargs["gender"]
        db.session.commit()

    return definitions.serialize()


class WakeWordDefinition(db.Model):
    ww_id = db.Column(db.String(255), primary_key=True)
    wake_word = db.Column(db.String(255), default="", nullable=False)
    module = db.Column(db.String(255), default="", nullable=False)  # "module" in mycroft.conf
    ww_config = db.Column(NestedMutableJson, default={}, nullable=False)  # arbitrary data for mycroft.conf/OPM

    def serialize(self):
        return {
            "ww_id": self.ww_id,
            "wake_word": self.wake_word,
            "module": self.module,
            "ww_config": self.ww_config
        }


def get_wakeword_config(wake_word):

    config = _ww_cfg.get(wake_word, {})
    module = config.get("module")

    # ww_name = data.get("default_ww")
    # ww_cfg = data.get("default_ww_cfg") or {}
    # ww_module = ww_cfg.get("module")
    if not all((wake_word, config, module)):
        return None, None
    
    definition = {"wake_word": wake_word,
                  "module": module,
                  "ww_config": config}
    
    # taken from https://github.com/OpenVoiceOS/ovos-plugin-manager/pull/131
    # skip_keys = ["display_name", "meta"]
    # keys = sorted([f"{k}_{v}" for k, v in config.items() if k not in skip_keys])
    # voiceid = f"{module}_{wake_word}_{keys}.json".replace("/", "_")
    ww_id = f"{module}_{wake_word}_{hash(str(config))}.json"
    return ww_id, definition


def add_wakeword_definition(**definition):
    entry = WakeWordDefinition(**definition)

    db.session.add(entry)
    db.session.commit()

    return entry


def get_wakeword_definition(ident):
    return WakeWordDefinition.query.filter_by(ww_id=ident).first()


def update_wakeword_definition(ident, **kwargs):

    definitions: WakeWordDefinition = get_wakeword_definition(ident)
    if not definitions:
        definitions = add_wakeword_definition(ww_id=ident, **kwargs)
    
    else:
        if "wake_word" in kwargs:
            definitions.wake_word = kwargs["wake_word"]
        if "plugin" in kwargs:
            definitions.module = kwargs["module"]
        if "ww_config" in kwargs:
            definitions.ww_config = kwargs["ww_config"]
        db.session.commit()
    
    data = definitions.serialize()

    return data


class Device(db.Model):
    uuid = db.Column(db.String(100), primary_key=True)
    token = db.Column(db.String(100))  # access token, sent to device during pairing
    
    # device backend preferences
    name = db.Column(db.String(100))
    placement = db.Column(db.String(50), default="somewhere")  # indoor location
    isolated_skills = db.Column(db.Boolean, default=False)
    opt_in = db.Column(db.Boolean,
                       default=CONFIGURATION.get("selene", {}).get("opt_in", False))
    email = db.Column(db.String(50),
                      default=_mail_cfg.get("recipient") or _mail_cfg.get("smtp", {}).get("username"))  # for sending email api, not registering
    # remote mycroft.conf settings
    date_fmt = db.Column(db.String(5),
                         default=CONFIGURATION.get("date_format", "DMY"))
    time_fmt = db.Column(db.String(5),
                         default=CONFIGURATION.get("time_format", "full"))
    system_unit = db.Column(db.String(10),
                            default=CONFIGURATION.get("system_unit", "metric"))
    lang = db.Column(db.String(5), default=CONFIGURATION.get("lang", "en-us"))

    # location
    _def_loc = Location(CONFIGURATION.get("default_location"))
    city = db.Column(db.String(50), default=_def_loc.city)
    address = db.Column(db.String(255), default=_def_loc.address)
    state = db.Column(db.String(50), default=_def_loc.state)
    country = db.Column(db.String(50), default=_def_loc.country)
    country_code = db.Column(db.String(5), default=_def_loc.country_code)
    region = db.Column(db.String(50), default=_def_loc.region)
    latitude = db.Column(db.Float, default=_def_loc.latitude)
    longitude = db.Column(db.Float, default=_def_loc.longitude)
    tz_short = db.Column(db.String(10), default=_def_loc.tz_short)
    tz_code = db.Column(db.String(25), default=_def_loc.tz_code)

    voice_id = db.Column(db.String(255))
    ww_id = db.Column(db.String(255), default=CONFIGURATION.get("default_ww").replace(" ", "_"))

    # this can return the old or new structure in the meantime
    @property
    def location(self):
        return Location({
            'city': self.city,
            'address': self.address,
            'state': self.state,
            'country': self.country,
            'country_code': self.country_code,
            'region': self.region,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'tz_short': self.tz_short,
            'tz_code': self.tz_code
        })


    @property
    def selene_device(self):
        return {
            "description": self.placement,
            "uuid": self.uuid,
            "name": self.name,

            # not tracked / meaningless
            # just for api compliance with selene
            'coreVersion': "unknown",
            'platform': 'unknown',
            'enclosureVersion': "",
            "user": {"uuid": self.uuid}  # users not tracked
        }

    @property
    def selene_settings(self):
        # this endpoint corresponds to a mycroft.conf
        # location is usually grabbed in a separate endpoint
        # in here we return it in case downstream is
        # aware of this and wants to save 1 http call

        hotwords = {}
        listener = {}
        if self.ww_id:
            ww: WakeWordDefinition = get_wakeword_definition(self.ww_id)
            if ww:
                # NOTE - selene returns the full listener config
                # this SHOULD NOT be done, since backend has no clue of hardware downstream
                # we return only wake word config
                hotwords[ww.wake_word] = ww.ww_config
                listener["wakeWord"] = ww.wake_word.replace(" ", "_")

        tts_settings = {}
        if self.voice_id:
            voice: VoiceDefinition = get_voice_definition(self.voice_id)
            if voice:
                tts_settings = {"module": voice.module,
                                voice.module: voice.voice_config}

        return {
            "dateFormat": self.date_fmt,
            "optIn": self.opt_in,
            "systemUnit": self.system_unit,
            "timeFormat": self.time_fmt,
            "uuid": self.uuid,
            "lang": self.lang,
            "location": self.location.old_conf,
            "listenerSetting": listener,
            "hotwordsSetting": hotwords,  # not present in selene, parsed correctly by core
            'ttsSettings': tts_settings
        }

    @staticmethod
    def deserialize(data):
        if isinstance(data, str):
            data = json.loads(data)

        voice_id, _ = get_voice_config(data.get("tts_module") or CONFIGURATION.get("default_tts"))
        ww_id, _ = get_wakeword_config(data.get("wake_word") or CONFIGURATION.get("default_ww"))

        location = Location(data.get("location") or CONFIGURATION["default_location"])

        email = data.get("email") or \
                _mail_cfg.get("recipient") or \
                _mail_cfg.get("smtp", {}).get("username")

        return update_device(data["uuid"],
                             token=data["token"],
                             lang=data.get("lang") or CONFIGURATION.get("lang") or "en-us",
                             placement=data.get("device_location") or "somewhere",
                             name=data.get("name") or f"Device-{data['uuid']}",
                             isolated_skills=data.get("isolated_skills", False),
                             city = location.city,
                             address = location.address,
                             state = location.state,
                             country = location.country, 
                             country_name = location.country_code,
                             latitude = location.latitude,
                             longitude = location.longitude,
                             tz_short = location.tz_short,
                             tz_code = location.tz_code,
                             opt_in=data.get("opt_in"),
                             system_unit=data.get("system_unit") or CONFIGURATION.get("system_unit") or "metric",
                             date_fmt=data.get("date_format") or CONFIGURATION.get("date_format") or "DMY",
                             time_fmt=data.get("time_format") or CONFIGURATION.get("time_format") or "full",
                             email=email,
                             ww_id=ww_id,
                             voice_id=voice_id)

    def serialize(self):
        
        default_tts = None
        default_tts_cfg = {}
        if self.voice_id:
            voice: VoiceDefinition = get_voice_definition(self.voice_id)
            if voice:
                default_tts_cfg = voice.voice_config
                default_tts = voice.module

        default_ww = None
        default_ww_cfg = {}
        if self.ww_id:
            ww: WakeWordDefinition = get_wakeword_definition(self.ww_id)
            if ww:
                default_ww_cfg = ww.ww_config
                default_ww = ww.wake_word

        return {
            "uuid": self.uuid,
            "token": self.token,
            "isolated_skills": self.isolated_skills,
            "opt_in": self.opt_in,
            "name": self.name,
            "device_location": self.placement,
            "email": self.email,
            "time_format": self.time_fmt,
            "date_format": self.date_fmt,
            "system_unit": self.system_unit,
            "lang": self.lang,
            'city': self.city,
            'address': self.address,
            'state': self.state,
            'country': self.country,
            'country_code': self.country_code,
            'region': self.region,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'tz_short': self.tz_short,
            'tz_code': self.tz_code,
            "default_tts": default_tts,
            "default_tts_cfg": default_tts_cfg,
            "default_ww": default_ww,
            "default_ww_cfg": default_ww_cfg
        }


def add_device(uuid, token, name=None, **kwargs):

    device_config = get_device_location()
    # TODO change CONFIGURATION key from "default_ww" to "wake_word"?
    ww_id, ww_definition = get_wakeword_config(kwargs.get("wake_word") or \
                                               CONFIGURATION.get("default_ww"))
    voice_id, voice_definition = get_voice_config(kwargs.get("tts_module") or \
                                                  CONFIGURATION.get("default_tts"))

    device_config["ww_id"] = ww_id
    device_config["voice_id"] = voice_id

    entry = Device(uuid=uuid,
                   token=token,
                   name=name or f"Device-{uuid}",
                   **device_config)
    db.session.add(entry)
    db.session.commit()

    update_wakeword_definition(ww_id, **ww_definition)
    update_voice_definition(voice_id, **voice_definition)


def get_device(uuid) -> Device:
    if uuid is None:
        return None
    return Device.query.filter_by(uuid=uuid).first()


def update_device(uuid, **kwargs):

    device: Device = Device.query.filter_by(uuid=uuid).first()
    if not device:
        raise ValueError(f"unknown uuid - {uuid}")

    if "name" in kwargs:
        device.name = kwargs["name"]
    if "lang" in kwargs:
        device.lang = kwargs["lang"]
    if "opt_in" in kwargs:
        device.opt_in = kwargs["opt_in"]
    if "device_location" in kwargs:
        device.placement = kwargs["device_location"]
    if "placement" in kwargs:
        device.placement = kwargs["placement"]
    if "email" in kwargs:
        device.email = kwargs["email"]
    if "isolated_skills" in kwargs:
        device.isolated_skills = kwargs["isolated_skills"]
    if "city" in kwargs:
        device.city = kwargs["city"]
    if "address" in kwargs:
        device.address = kwargs["address"]
    if "state" in kwargs:
        device.state = kwargs["state"]
    if "country_code" in kwargs:
        device.country_code = kwargs["country_code"]
    if "country" in kwargs:
        device.country = kwargs["country"]
    if "region" in kwargs:
        device.region = kwargs["region"]
    if "latitude" in kwargs:
        device.latitude = kwargs["latitude"]
    if "longitude" in kwargs:
        device.longitude = kwargs["longitude"]
    if "tz_short" in kwargs:
        device.tz_short = kwargs["tz_short"]
    if "tz_code" in kwargs:
        device.tz_code = kwargs["tz_code"]
    if "time_format" in kwargs:
        device.time_format = kwargs["time_format"]
    if "date_format" in kwargs:
        device.date_format = kwargs["date_format"]
    if "time_fmt" in kwargs:
        device.time_format = kwargs["time_fmt"]
    if "date_fmt" in kwargs:
        device.date_format = kwargs["date_fmt"]
    if "system_unit" in kwargs:
        device.system_unit = kwargs["system_unit"]

    if "tts_module" in kwargs:
        voice_id, voice_definition = get_voice_config(kwargs["tts_module"])
        update_voice_definition(voice_id, **voice_definition)
        device.voice_id = voice_id

    if "wake_word" in kwargs:
        ww_id, ww_definition = get_wakeword_config(kwargs["wake_word"])
        update_wakeword_definition(ww_id, **ww_definition)
        device.ww_id = ww_id
    
    db.session.commit()

    return device.serialize()


def get_device_location(uuid=None, old_conf=False):
    device = get_device(uuid)
    if device:
        location = device.location
    else:
        try:
            location = get_request_location()
        except:
            location = Location(CONFIGURATION["default_location"])
        
    if old_conf:
        return location.old_conf
    else:
        return location.serialize


class SkillSettings(db.Model):
    remote_id = db.Column(db.String(255),
                          primary_key=True)  # depends on Device.isolated_skills, @{uuid}|{skill_id} or {skill_id}
    display_name = db.Column(db.String(255))  # for friendly UI, default to skill_id
    settings_json = db.Column(NestedMutableJson, nullable=False, default="{}")  # actual skill settings file
    metadata_json = db.Column(NestedMutableJson, nullable=False, default="{}")  # how to display user facing settings editor

    def serialize(self):
        # settings meta with updated placeholder values from settings
        # old style selene db stored skill settings this way
        meta = deepcopy(self.metadata_json)
        # settings = json.loads(self.settings_json)
        for idx, section in enumerate(meta.get('sections', [])):
            for idx2, field in enumerate(section["fields"]):
                if "value" not in field:
                    continue
                if field["name"] in self.settings_json:
                    meta['sections'][idx]["fields"][idx2]["value"] = \
                            self.settings_json[field["name"]]
        return {'skillMetadata': meta,
                "skill_gid": self.remote_id,
                "display_name": self.display_name}

    @staticmethod
    def deserialize(data):
        if isinstance(data, str):
            data = json.loads(data)

        skill_json = {}
        skill_meta = data.get("skillMetadata") or {}
        for s in skill_meta.get("sections", []):
            for f in s.get("fields", []):
                if "name" in f and "value" in f:
                    val = f["value"]
                    if isinstance(val, str):
                        t = f.get("type", "")
                        if t == "checkbox":
                            if val.lower() == "true" or val == "1":
                                val = True
                            else:
                                val = False
                        elif t == "number":
                            if val == "False":
                                val = 0
                            elif val == "True":
                                val = 1
                            else:
                                val = float(val)
                        elif val.lower() in ["none", "null", "nan"]:
                            val = None
                        elif val == "[]":
                            val = []
                        elif val == "{}":
                            val = {}
                    skill_json[f["name"]] = val

        remote_id = data.get("skill_gid") or data.get("identifier")
        # this is a mess, possible keys seen by logging data
        # - @|XXX
        # - @{uuid}|XXX
        # - XXX

        # where XXX has been observed to be
        # - {skill_id}  <- ovos-core
        # - {msm_name} <- mycroft-core
        #   - {mycroft_marketplace_name} <- all default skills
        #   - {MycroftSkill.name} <- sometimes sent to msm (very uncommon)
        #   - {skill_id.split(".")[0]} <- fallback msm name
        # - XXX|{branch} <- append by msm (?)
        # - {whatever we feel like uploading} <- SeleneCloud utils
        fields = remote_id.split("|")
        skill_id = fields[0]
        if len(fields) > 1 and fields[0].startswith("@"):
            skill_id = fields[1]

        display_name = data.get("display_name") or \
                       skill_id.split(".")[0].replace("-", " ").replace("_", " ").title()
        
        settings = {
            "display_name": display_name,
            "settings_json": skill_json,
            "metadata_json": skill_meta
        }

        return update_skill_settings(remote_id, **settings)


def add_skill_settings(**kwargs):

    entry = SkillSettings(**kwargs)
    db.session.add(entry)
    db.session.commit()

    return entry


def get_skill_settings(ident):
    return SkillSettings.query.filter_by(remote_id=ident).first()


def update_skill_settings(ident, **kwargs):

    settings: SkillSettings = get_skill_settings(ident)
    if not settings:
        settings = add_skill_settings(remote_id=ident, **kwargs)
    
    else:
        if "display_name" in kwargs:
            settings.display_name = kwargs["display_name"]
        if "settings_json" in kwargs:
            settings.settings_json = kwargs["settings_json"]
        if "metadata_json" in kwargs:
            settings.metadata_json = kwargs["metadata_json"]
        db.session.commit()

    return settings.serialize()


class Metric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    metric_type = db.Column(db.String(255), nullable=False)
    metadata_json = db.Column(NestedMutableJson, nullable=False)  # arbitrary data
    # TODO - extract explicit fields from json for things we want to be queryable
    # query Metric for last id  => metric.metadata_json["x"]

    # TODO 2 primary keys?
    timestamp = db.Column(db.Integer, primary_key=True)  # unix seconds
    uuid = db.Column(db.String(255))  # TODO - link to devices table


@requires_opt_in
def save_metric(uuid, name, data):
    entry = Metric(
        id=db.session.query(Metric).count() + 1,
        metric_type=name,
        metadata_json=data,
        uuid=uuid,
        timestamp=time.time()
    )
    db.session.add(entry)
    db.session.commit()


class UtteranceRecording(db.Model):
    utterance_id = db.Column(db.Integer, primary_key=True)
    transcription = db.Column(db.String(255), nullable=False)
    metadata_json = db.Column(NestedMutableJson)  # arbitrary metadata
    sample = db.Column(db.LargeBinary(16777215), nullable=False)  # audio data

    timestamp = db.Column(db.Integer, primary_key=True)  # unix seconds
    uuid = db.Column(db.String(255))  # TODO - link to devices table


@requires_opt_in
def save_stt_recording(uuid, audio, utterance):
    entry = UtteranceRecording(
        utterance_id=db.session.query(UtteranceRecording).count() + 1,
        transcription=utterance,
        sample=audio.get_wav_data(),
        metadata_json={},  # TODO - allow expanding in future

        uuid=uuid,
        timestamp=time.time()
    )
    db.session.add(entry)
    db.session.commit()


class WakeWordRecording(db.Model):
    wakeword_id = db.Column(db.Integer, primary_key=True)
    transcription = db.Column(db.String(255))
    audio_tag = db.Column(db.String(255))  # "untagged" / "wake_word" / "speech" / "noise" / "silence"
    speaker_tag = db.Column(db.String(255))  # "untagged" / "male" / "female" / "children"
    metadata_json = db.Column(NestedMutableJson, nullable=False)  # arbitrary metadata
    sample = db.Column(db.LargeBinary(16777215), nullable=False)  # audio data

    timestamp = db.Column(db.Integer, primary_key=True)  # unix seconds
    uuid = db.Column(db.String(255))  # TODO - link to devices table


@requires_opt_in
def save_ww_recording(uuid, uploads):
    for ww_file in uploads:
        # Werkzeug FileStorage objects
        fn = uploads[ww_file].filename
        if fn == 'audio':
            audio = uploads[ww_file].read()
        if fn == 'metadata':
            meta = json.load(uploads[ww_file])

    if not audio:
        return False

    # classic mycroft devices send
    # {"name": "hey-mycroft",
    # "engine": "0f4df281688583e010c26831abdc2222",
    # "time": "1592192357852",
    # "sessionId": "7d18e208-05b5-401e-add6-ee23ae821967",
    # "accountId": "0",
    # "model": "5223842df0cdee5bca3eff8eac1b67fc"}

    entry = WakeWordRecording(
        wakeword_id=db.session.query(WakeWordRecording).count() + 1,
        transcription=meta.get("wake_word", "").replace("_", " "),
        sample=audio,
        metadata_json=meta,

        uuid=uuid,
        timestamp=time.time()
    )
    db.session.add(entry)
    db.session.commit()
    return True