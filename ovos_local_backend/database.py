import json
import time
from copy import deepcopy

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_json import NestedMutableJson

from ovos_local_backend.backend.decorators import requires_opt_in
from ovos_local_backend.configuration import CONFIGURATION

# create the extension
db = SQLAlchemy()

_mail_cfg = CONFIGURATION.get("email", {})


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


def get_voice_id(plugin_name, lang, tts_config):
    # taken from https://github.com/OpenVoiceOS/ovos-plugin-manager/pull/131
    skip_keys = ["module", "meta"]
    keys = sorted([f"{k}_{v}" for k, v in tts_config.items() if k not in skip_keys])
    voiceid = f"{plugin_name}_{lang}_{keys}.json".replace("/", "_")
    return voiceid


def get_ww_id(plugin_name, ww_name, ww_config):
    # taken from https://github.com/OpenVoiceOS/ovos-plugin-manager/pull/131
    skip_keys = ["display_name", "meta"]
    keys = sorted([f"{k}_{v}" for k, v in ww_config.items() if k not in skip_keys])
    voiceid = f"{plugin_name}_{ww_name}_{keys}.json".replace("/", "_")
    return voiceid


class VoiceDefinition(db.Model):
    voice_id = db.Column(db.String(255), primary_key=True)
    lang = db.Column(db.String(255), default="en-us", nullable=False)
    plugin = db.Column(db.String(255), default="", nullable=False)  # "module" in mycroft.conf
    tts_config = db.Column(NestedMutableJson, default={}, nullable=False)  # arbitrary data for mycroft.conf/OPM
    offline = db.Column(db.Boolean, default=False, nullable=False)
    # optional metadata
    gender = db.Column(db.String(255), default="")

    def serialize(self):
        return {
            "voice_id": self.voice_id,
            "lang": self.lang,
            "plugin": self.plugin,
            "tts_config": self.tts_config,
            "offline": self.offline,
            "gender": self.gender
        }


def add_voice_definition(**definition) -> VoiceDefinition:
    entry = VoiceDefinition(**definition)

    db.session.add(entry)
    db.session.commit()

    return entry


def get_voice_definition(voice_id) -> VoiceDefinition:
    return VoiceDefinition.query.filter_by(voice_id=voice_id).first()


def update_voice_definition(voice_id, **kwargs) -> dict:
    voice_def: VoiceDefinition = get_voice_definition(voice_id)
    if not voice_def:
        voice_def = add_voice_definition(voice_id=voice_id, **kwargs)
    else:
        if "lang" in kwargs:
            voice_def.lang = kwargs["lang"]
        if "plugin" in kwargs:
            voice_def.plugin = kwargs["plugin"]
        if "tts_config" in kwargs:
            voice_def.tts_config = kwargs["tts_config"]
        if "offline" in kwargs:
            voice_def.offline = kwargs["offline"]
        if "gender" in kwargs:
            voice_def.gender = kwargs["gender"]
        db.session.commit()

    return voice_def.serialize()


class WakeWordDefinition(db.Model):
    ww_id = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), default="", nullable=False)
    plugin = db.Column(db.String(255), default="", nullable=False)  # "module" in mycroft.conf
    ww_config = db.Column(NestedMutableJson, default={}, nullable=False)  # arbitrary data for mycroft.conf/OPM

    def serialize(self):
        return {
            "ww_id": self.ww_id,
            "name": self.name,
            "plugin": self.plugin,
            "ww_config": self.ww_config
        }


def add_wakeword_definition(**definition):
    entry = WakeWordDefinition(**definition)

    db.session.add(entry)
    db.session.commit()

    return entry


def get_wakeword_definition(ww_id):
    return WakeWordDefinition.query.filter_by(ww_id=ww_id).first()


def update_wakeword_definition(ww_id, **kwargs):
    ww_def: WakeWordDefinition = get_wakeword_definition(ww_id)
    if not ww_def:
        ww_def = add_wakeword_definition(ww_id=ww_id, **kwargs)

    else:
        if "name" in kwargs:
            ww_def.name = kwargs["name"]
        if "plugin" in kwargs:
            ww_def.plugin = kwargs["plugin"]
        if "ww_config" in kwargs:
            ww_def.ww_config = kwargs["ww_config"]
        db.session.commit()

    return ww_def.serialize()


class Device(db.Model):
    uuid = db.Column(db.String(100), primary_key=True)
    token = db.Column(db.String(100))  # access token, sent to device during pairing

    # device backend preferences
    name = db.Column(db.String(100))
    placement = db.Column(db.String(50), default="somewhere")  # indoor location
    isolated_skills = db.Column(db.Boolean, default=False)
    opt_in = db.Column(db.Boolean, default=False)
    # for sending email api, not registering
    email = db.Column(db.String(100), default=_mail_cfg.get("recipient") or _mail_cfg.get("smtp", {}).get("username"))
    # remote mycroft.conf settings
    date_fmt = db.Column(db.String(5), default=CONFIGURATION.get("date_format", "DMY"))
    time_fmt = db.Column(db.String(5), default=CONFIGURATION.get("time_format", "full"))
    system_unit = db.Column(db.String(10), default=CONFIGURATION.get("system_unit", "metric"))
    lang = db.Column(db.String(5), default=CONFIGURATION.get("lang", "en-us"))

    # location fields, explicit so we can query them
    city = db.Column(db.String(length=50, default="TODO"))
    state = db.Column(db.String(length=50))
    state_code = db.Column(db.String(length=10))
    country = db.Column(db.String(length=50))
    country_code = db.Column(db.String(length=10))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    tz_code = db.Column(db.String(length=25))
    tz_name = db.Column(db.String(length=15))
    # ww settings
    voice_id = db.Column(db.String(255), default=get_voice_id(CONFIGURATION.get("default_tts")))
    ww_id = db.Column(db.String(255), default=get_wakeword_id(CONFIGURATION.get("default_ww")))

    @property
    def location_json(self):
        return {
            "city": {
                "name": self.city,
                "state": {
                    "name": self.state,
                    "code": self.state_code,
                    "country": {
                        "name": self.country,
                        "code": self.country_code
                    }
                }
            },
            "coordinate": {
                "latitude": self.latitude,
                "longitude": self.longitude
            },
            "timezone": {
                "code": self.tz_code,
                "name": self.tz_name
            }
        }

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
                hotwords[ww.name] = ww.ww_config
                listener["wakeWord"] = ww.name.replace(" ", "_")

        tts_settings = {}
        if self.voice_id:
            voice: VoiceDefinition = get_voice_definition(self.voice_id)
            if voice:
                tts_settings = {"module": voice.plugin,
                                voice.plugin: voice.tts_config}

        return {
            "dateFormat": self.date_fmt,
            "optIn": self.opt_in,
            "systemUnit": self.system_unit,
            "timeFormat": self.time_fmt,
            "uuid": self.uuid,
            "lang": self.lang,
            "location": self.location_json,
            "listenerSetting": listener,
            "hotwordsSetting": hotwords,  # not present in selene, parsed correctly by core
            'ttsSettings': tts_settings
        }

    @staticmethod
    def deserialize(data):
        if isinstance(data, str):
            data = json.loads(data)

        lang = data.get("lang") or CONFIGURATION.get("lang") or "en-us"

        voice_id = None
        tts_module = data.get("default_tts")
        tts_config = data.get("default_tts_cfg") or {}
        if tts_module:
            voice_id = get_voice_id(tts_module, lang, tts_config)

        ww_id = None
        ww_name = data.get("default_ww")
        ww_config = data.get("default_ww_cfg") or {}
        ww_module = ww_config.get("module")
        if ww_module:
            ww_id = get_ww_id(ww_module, ww_name, ww_config)

        loc = data.get("location") or CONFIGURATION["default_location"]

        email = data.get("email") or \
                _mail_cfg.get("recipient") or \
                _mail_cfg.get("smtp", {}).get("username")

        return update_device(uuid=data["uuid"],
                             token=data["token"],
                             lang=data.get("lang") or CONFIGURATION.get("lang") or "en-us",
                             placement=data.get("device_location") or "somewhere",
                             name=data.get("name") or f"Device-{data['uuid']}",
                             isolated_skills=data.get("isolated_skills", False),
                             city=loc["city"]["name"],
                             state=loc["city"]["state"]["name"],
                             country=loc["city"]["state"]["country"]["name"],
                             state_code=loc["city"]["state"]["code"],
                             country_code=loc["city"]["state"]["country"]["code"],
                             latitude=loc["coordinate"]["latitude"],
                             longitude=loc["coordinate"]["longitude"],
                             tz_name=loc["timezone"]["name"],
                             tz_code=loc["timezone"]["code"],
                             opt_in=data.get("opt_in"),
                             system_unit=data.get("system_unit") or CONFIGURATION.get("system_unit") or "metric",
                             date_fmt=data.get("date_format") or CONFIGURATION.get("date_format") or "DMY",
                             time_fmt=data.get("time_format") or CONFIGURATION.get("time_format") or "full",
                             email=email,
                             ww_id=ww_id,
                             voice_id=voice_id)

    def serialize(self):
        email = self.email or \
                _mail_cfg.get("recipient") or \
                _mail_cfg.get("smtp", {}).get("username")

        default_tts = None
        default_tts_cfg = {}
        if self.voice_id:
            voice: VoiceDefinition = get_voice_definition(self.voice_id)
            if voice:
                default_tts_cfg = voice.tts_config
                default_tts = voice.plugin

        default_ww = None
        default_ww_cfg = {}
        if self.ww_id:
            ww: WakeWordDefinition = get_wakeword_definition(self.ww_id)
            if ww:
                default_ww_cfg = ww.ww_config
                default_ww = ww.name

        return {
            "uuid": self.uuid,
            "token": self.token,
            "isolated_skills": self.isolated_skills,
            "opt_in": self.opt_in,
            "name": self.name or f"Device-{self.uuid}",
            "device_location": self.placement or "somewhere",
            "email": email,
            "time_format": self.time_fmt,
            "date_format": self.date_fmt,
            "system_unit": self.system_unit,
            "lang": self.lang or CONFIGURATION.get("lang") or "en-us",
            "location": self.location_json,
            "default_tts": default_tts,
            "default_tts_cfg": default_tts_cfg,
            "default_ww": default_ww,
            "default_ww_cfg": default_ww_cfg
        }


def add_device(uuid, token, name=None, device_location="somewhere", opt_in=False,
               location=None, lang=None, date_format=None, system_unit=None,
               time_format=None, email=None, isolated_skills=False,
               ww_id="hey mycroft", voice_id=None):
    lang = lang or CONFIGURATION.get("lang") or "en-us"

    email = email or \
            _mail_cfg.get("recipient") or \
            _mail_cfg.get("smtp", {}).get("username")

    loc = location or CONFIGURATION["default_location"]
    entry = Device(uuid=uuid,
                   token=token,
                   lang=lang,
                   placement=device_location,
                   name=name or f"Device-{uuid}",
                   isolated_skills=isolated_skills,
                   city=loc["city"]["name"],
                   state=loc["city"]["state"]["name"],
                   country=loc["city"]["state"]["country"]["name"],
                   state_code=loc["city"]["state"]["code"],
                   country_code=loc["city"]["state"]["country"]["code"],
                   latitude=loc["coordinate"]["latitude"],
                   longitude=loc["coordinate"]["longitude"],
                   tz_name=loc["timezone"]["name"],
                   tz_code=loc["timezone"]["code"],
                   opt_in=opt_in,
                   system_unit=system_unit or CONFIGURATION.get("system_unit") or "metric",
                   date_fmt=date_format or CONFIGURATION.get("date_format") or "DMY",
                   time_fmt=time_format or CONFIGURATION.get("time_format") or "full",
                   email=email,
                   ww_id=ww_id,
                   voice_id=voice_id)
    db.session.add(entry)
    db.session.commit()

    #update_wakeword_definition(ww_id, **ww_definition)
    #update_voice_definition(voice_id, **voice_definition)


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
    if "location" in kwargs:
        loc = kwargs["location"]
        if isinstance(loc, str):
            loc = json.loads(loc)
        device.city = loc["city"]["name"]
        device.state = loc["city"]["state"]["name"]
        device.country = loc["city"]["state"]["country"]["name"]
        device.state_code = loc["city"]["state"]["code"]
        device.country_code = loc["city"]["state"]["country"]["code"]
        device.latitude = loc["coordinate"]["latitude"]
        device.longitude = loc["coordinate"]["longitude"]
        device.tz_name = loc["timezone"]["name"]
        device.tz_code = loc["timezone"]["code"]
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
        tts_plug = kwargs["tts_module"]
        if "tts_config" in kwargs:
            tts_config = kwargs["tts_config"]
        elif tts_plug in CONFIGURATION["tts_configs"]:
            tts_config = CONFIGURATION["tts_configs"][tts_plug]
        else:
            tts_config = {}
        voice_id = get_voice_id(tts_plug, device.lang, tts_config)
        voice = VoiceDefinition.query.filter_by(voice_id=voice_id).first()
        if not voice:
            pass  # TODO add voice def

        # update_voice_definition(voice_id, **voice_definition)
        device.voice_id = voice_id

    if "wake_word" in kwargs:
        default_ww = kwargs["wake_word"]
        ww_module = kwargs["ww_module"]
        if "ww_config" in kwargs:
            ww_config = kwargs["ww_config"]
        elif default_ww in CONFIGURATION["ww_configs"]:
            ww_config = CONFIGURATION["ww_configs"][default_ww]
        else:
            ww_config = {}
        ww_id = get_ww_id(ww_module, default_ww, ww_config)
        ww = WakeWordDefinition.query.filter_by(ww_id=ww_id).first()
        if not ww:
            pass  # TODO add ww def

        # update_wakeword_definition(ww_id, **ww_definition)
        device.ww_id = ww_id

    db.session.commit()

    return device.serialize()



class SkillSettings(db.Model):
    remote_id = db.Column(db.String(255), primary_key=True)  # depends on Device.isolated_skills, @{uuid}|{skill_id} or {skill_id}
    display_name = db.Column(db.String(255))  # for friendly UI, default to skill_id
    settings_json = db.Column(NestedMutableJson, nullable=False, default="{}")  # actual skill settings file
    metadata_json = db.Column(NestedMutableJson, nullable=False, default="{}")  # how to display user facing settings editor

    def serialize(self):
        # settings meta with updated placeholder values from settings
        # old style selene db stored skill settings this way
        meta = deepcopy(self.metadata_json)
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
    timestamp = db.Column(db.Integer)  # unix seconds
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
    meta = {}
    audio = None
    for ww_file in uploads:
        # Werkzeug FileStorage objects
        fn = uploads[ww_file].filename
        if fn == 'audio':
            audio = uploads[ww_file].read()
        if fn == 'metadata':
            meta = json.load(uploads[ww_file])

    if not audio:
        return False  # TODO - some error? just ignore entry for now

    # classic mycroft devices send
    # {"name": "hey-mycroft",
    # "engine": "0f4df281688583e010c26831abdc2222",
    # "time": "1592192357852",
    # "sessionId": "7d18e208-05b5-401e-add6-ee23ae821967",
    # "accountId": "0",
    # "model": "5223842df0cdee5bca3eff8eac1b67fc"}

    entry = WakeWordRecording(
        wakeword_id=db.session.query(WakeWordRecording).count() + 1,
        transcription=meta.get("name", "").replace("_", " "),
        sample=audio,
        metadata_json=meta,
        uuid=uuid,
        timestamp=time.time()
    )
    db.session.add(entry)
    db.session.commit()
    return True
