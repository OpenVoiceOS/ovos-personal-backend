import base64
import json
import time
from copy import deepcopy

from flask_sqlalchemy import SQLAlchemy
from ovos_config import Configuration
from ovos_plugin_manager.tts import get_voice_id
from ovos_plugin_manager.wakewords import get_ww_id
from ovos_utils.xdg_utils import xdg_data_home
from sqlalchemy_json import NestedMutableJson

# create the extension
db = SQLAlchemy()

_cfg = Configuration()
_mail_cfg = _cfg["microservices"]["email"]
_loc = _cfg["location"]
_default_voice_id = _cfg["default_values"]["voice_id"]
_default_ww_id = _cfg["default_values"]["ww_id"]


def connect_db(app):
    # configure the SQLite database, relative to the app instance folder

    # "mysql+mysqldb://scott:tiger@192.168.0.134/test?ssl_ca=/path/to/ca.pem&ssl_cert=/path/to/client-cert.pem&ssl_key=/path/to/client-key.pem"
    # "sqlite:///ovos_backend.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = _cfg["server"].get("database") or \
                                            f"sqlite:///{xdg_data_home()}/ovos_backend.db"
    print(f"sqlite:///{xdg_data_home()}/ovos_backend.db")
    # initialize the app with the extension
    db.init_app(app)

    with app.app_context():
        db.create_all()

    return app, db


class OAuthToken(db.Model):
    # @{uuid}|{oauth_id} -> @{uuid}|spotify
    token_id = db.Column(db.String(255), primary_key=True)
    data = db.Column(NestedMutableJson, default={}, nullable=False)


class OAuthApplication(db.Model):
    # @{uuid}|{oauth_id} -> @{uuid}|spotify
    token_id = db.Column(db.String(255), primary_key=True)
    client_id = db.Column(db.String(255), nullable=False)
    auth_endpoint = db.Column(db.String(255), nullable=False)
    token_endpoint = db.Column(db.String(255), nullable=False)
    callback_endpoint = db.Column(db.String(255), nullable=False)
    # afaik some oauth implementations dont require these
    scope = db.Column(db.String(255), default="")
    client_secret = db.Column(db.String(255))
    refresh_endpoint = db.Column(db.String(255))
    # ovos GUI flag
    shell_integration = db.Column(db.Boolean, default=True)

    def serialize(self):
        return {
            "oauth_service": self.oauth_service,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "auth_endpoint": self.auth_endpoint,
            "token_endpoint": self.token_endpoint,
            "refresh_endpoint": self.refresh_endpoint,
            "callback_endpoint": self.callback_endpoint,
            "scope": self.scope,
            "shell_integration": self.shell_integration
        }


class VoiceDefinition(db.Model):
    voice_id = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    lang = db.Column(db.String(5), default="en-us", nullable=False)
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


class WakeWordDefinition(db.Model):
    ww_id = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), default="", nullable=False)
    lang = db.Column(db.String(5), default="en-us", nullable=False)
    plugin = db.Column(db.String(255), default="", nullable=False)  # "module" in mycroft.conf
    ww_config = db.Column(NestedMutableJson, default={}, nullable=False)  # arbitrary data for mycroft.conf/OPM

    def serialize(self):
        return {
            "ww_id": self.ww_id,
            "name": self.name,
            "lang": self.lang,
            "plugin": self.plugin,
            "ww_config": self.ww_config
        }


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
    date_fmt = db.Column(db.String(5), default=_cfg.get("date_format", "DMY"))
    time_fmt = db.Column(db.String(5), default=_cfg.get("time_format", "full"))
    system_unit = db.Column(db.String(10), default=_cfg.get("system_unit", "metric"))
    lang = db.Column(db.String(5), default=_cfg.get("lang", "en-us"))

    # location fields, explicit so we can query them
    city = db.Column(db.String(length=50), default=_loc["city"]["name"])
    state = db.Column(db.String(length=50), default=_loc["city"]["state"]["name"])
    state_code = db.Column(db.String(length=10), default=_loc["city"]["state"]["code"])
    country = db.Column(db.String(length=50), default=_loc["city"]["state"]["country"]["name"])
    country_code = db.Column(db.String(length=10), default=_loc["city"]["state"]["country"]["code"])
    latitude = db.Column(db.Float, default=_loc["coordinate"]["latitude"])
    longitude = db.Column(db.Float, default=_loc["coordinate"]["longitude"])
    tz_code = db.Column(db.String(length=25), default=_loc["timezone"]["name"])
    tz_name = db.Column(db.String(length=15), default=_loc["timezone"]["code"])
    # ww settings
    voice_id = db.Column(db.String(255), default=_default_voice_id)
    ww_id = db.Column(db.String(255), default=_default_ww_id)

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

        lang = data.get("lang") or _cfg.get("lang") or "en-us"

        voice_id = data.get("voice_id")
        if not voice_id:
            tts_module = data.get("default_tts")
            tts_config = data.get("default_tts_cfg") or {}
            if tts_module:
                voice_id = get_voice_id(tts_module, lang, tts_config)

        ww_id = data.get("ww_id")
        if not ww_id:
            ww_name = data.get("default_ww")
            ww_config = data.get("default_ww_cfg") or {}
            ww_module = ww_config.get("module")
            if ww_module:
                ww_id = get_ww_id(ww_module, ww_name, ww_config)

        loc = data.get("location") or _loc

        email = data.get("email") or \
                _mail_cfg.get("recipient") or \
                _mail_cfg.get("smtp", {}).get("username")

        return update_device(uuid=data["uuid"],
                             token=data["token"],
                             lang=data.get("lang") or _cfg.get("lang") or "en-us",
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
                             system_unit=data.get("system_unit") or _cfg.get("system_unit") or "metric",
                             date_fmt=data.get("date_format") or _cfg.get("date_format") or "DMY",
                             time_fmt=data.get("time_format") or _cfg.get("time_format") or "full",
                             email=email,
                             ww_id=ww_id,
                             voice_id=voice_id)

    def serialize(self):
        email = self.email or \
                _mail_cfg.get("recipient") or \
                _mail_cfg.get("smtp", {}).get("username")

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
            "lang": self.lang or _cfg.get("lang") or "en-us",
            "location": self.location_json,
            "voice_id": self.voice_id,
            "ww_id": self.ww_id
        }


class SkillSettings(db.Model):
    remote_id = db.Column(db.String(255),
                          primary_key=True)  # depends on Device.isolated_skills, @{uuid}|{skill_id} or {skill_id}
    display_name = db.Column(db.String(255))  # for friendly UI, default to skill_id
    settings = db.Column(NestedMutableJson, nullable=False, default="{}")  # actual skill settings file
    meta = db.Column(NestedMutableJson, nullable=False, default="{}")  # how to display user facing settings editor

    @property
    def skill_id(self):
        return self.remote_id.split("|", 1)[-1]

    def serialize(self):
        # settings meta with updated placeholder values from settings
        # old style selene db stored skill settings this way
        meta = deepcopy(self.meta)
        for idx, section in enumerate(meta.get('sections', [])):
            for idx2, field in enumerate(section["fields"]):
                if "value" not in field:
                    continue
                if field["name"] in self.settings:
                    meta['sections'][idx]["fields"][idx2]["value"] = \
                        self.settings[field["name"]]
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

        return update_skill_settings(remote_id,
                                     display_name=display_name,
                                     settings_json=skill_json,
                                     metadata_json=skill_meta)


class Metric(db.Model):
    # metric_id = f"@{uuid}|{name}|{count}"
    metric_id = db.Column(db.String(255), primary_key=True)
    metric_type = db.Column(db.String(255), nullable=False)
    metadata_json = db.Column(NestedMutableJson, nullable=False)  # arbitrary data
    timestamp = db.Column(db.Integer)  # unix seconds
    uuid = db.Column(db.String(255))

    def serialize(self):
        return {"metric_id": self.metric_id,
                "metric_type": self.metric_type,
                "metadata_json": self.metadata_json,
                "uuid": self.uuid,
                "timestamp": self.timestamp}

    @staticmethod
    def deserialize(data):
        return Metric(**data)


class UtteranceRecording(db.Model):
    #  rec_id = f"@{uuid}|{transcription}|{count}"
    recording_id = db.Column(db.String(255), primary_key=True)
    transcription = db.Column(db.String(255), nullable=False)
    metadata_json = db.Column(NestedMutableJson)  # arbitrary metadata
    sample = db.Column(db.LargeBinary(16777215), nullable=False)  # audio data

    timestamp = db.Column(db.Integer, primary_key=True)  # unix seconds
    uuid = db.Column(db.String(255))

    def serialize(self):
        data = {
            "recording_id": self.recording_id,
            "transcription": self.transcription,
            "metadata_json": self.metadata_json,
            "uuid": self.uuid,
            "timestamp": self.timestamp,
            "audio_b64": base64.encodebytes(self.sample).decode("utf-8")
        }
        return data

    @staticmethod
    def deserialize(data):
        b64_data = data.pop("audio_b64")
        data["sample"] = base64.decodestring(b64_data)
        return UtteranceRecording(**data)


class WakeWordRecording(db.Model):
    #  rec_id = f"@{uuid}|{transcription}|{count}"
    recording_id = db.Column(db.String(255), primary_key=True)
    transcription = db.Column(db.String(255))
    audio_tag = db.Column(db.String(255))  # "untagged" / "wake_word" / "speech" / "noise" / "silence"
    speaker_tag = db.Column(db.String(255))  # "untagged" / "male" / "female" / "children"
    metadata_json = db.Column(NestedMutableJson, nullable=False)  # arbitrary metadata
    sample = db.Column(db.LargeBinary(16777215), nullable=False)  # audio data

    timestamp = db.Column(db.Integer, primary_key=True)  # unix seconds
    uuid = db.Column(db.String(255))

    def serialize(self):
        data = {
            "recording_id": self.recording_id,
            "transcription": self.transcription,
            "audio_tag": self.audio_tag,
            "speaker_tag": self.speaker_tag,
            "metadata_json": self.metadata_json,
            "uuid": self.uuid,
            "timestamp": self.timestamp,
            "audio_b64": base64.encodebytes(self.sample).decode("utf-8")
        }
        return data

    @staticmethod
    def deserialize(data):
        b64_data = data.pop("audio_b64")
        data["sample"] = base64.decodestring(b64_data)
        return WakeWordRecording(**data)


def add_metric(uuid, metric_type, metadata):
    count = db.session.query(Metric).count() + 1
    metric_id = f"@{uuid}|{metric_type}|{count}"
    entry = Metric(
        metric_id=metric_id,
        metric_type=metric_type,
        metadata_json=metadata,
        uuid=uuid,
        timestamp=time.time()
    )
    db.session.add(entry)
    db.session.commit()
    return entry


def get_metric(metric_id):
    return Metric.query.filter_by(metric_id=metric_id).first()


def delete_metric(metric_id):
    entry = get_metric(metric_id)
    if not entry:
        return False
    db.session.delete(entry)
    db.session.commit()
    return True


def update_metric(metric_id, metadata):
    metric: Metric = get_metric(metric_id)
    if not metric:
        uuid, name, count = metric_id.split("|")
        uuid = uuid.lstrip("@")
        metric = add_metric(uuid, name, metadata)
    else:
        metric.metadata_json = metadata
        db.session.commit()
    return metric


def list_metrics():
    return Metric.query.all()


def add_wakeword_definition(name, lang, ww_config, plugin):
    ww_id = get_ww_id(plugin, name, ww_config)
    entry = WakeWordDefinition(ww_id=ww_id, lang=lang, name=name,
                               ww_config=ww_config, plugin=plugin)
    db.session.add(entry)
    db.session.commit()
    return entry


def get_wakeword_definition(ww_id):
    return WakeWordDefinition.query.filter_by(ww_id=ww_id).first()


def delete_wakeword_definition(ww_id):
    entry = get_wakeword_definition(ww_id)
    if not entry:
        return False
    db.session.delete(entry)
    db.session.commit()
    return True


def list_wakeword_definition():
    return WakeWordDefinition.query.all()


def list_voice_definitions():
    return VoiceDefinition.query.all()


def update_wakeword_definition(ww_id, name=None, lang=None, ww_config=None, plugin=None):
    ww_def: WakeWordDefinition = get_wakeword_definition(ww_id)
    if not ww_def:
        ww_def = add_wakeword_definition(ww_id=ww_id, lang=lang, name=name,
                                         ww_config=ww_config, plugin=plugin)
    else:
        if name:
            ww_def.name = name
        if plugin:
            ww_def.plugin = plugin
        if lang:
            ww_def.lang = lang
        if ww_config:
            ww_def.ww_config = ww_config
        db.session.commit()
    return ww_def


def add_device(uuid, token, name=None, device_location="somewhere", opt_in=False,
               location=None, lang=None, date_format=None, system_unit=None,
               time_format=None, email=None, isolated_skills=False,
               ww_id=None, voice_id=None):
    lang = lang or _cfg.get("lang") or "en-us"

    email = email or \
            _mail_cfg.get("recipient") or \
            _mail_cfg.get("smtp", {}).get("username")

    loc = location or _loc
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
                   system_unit=system_unit or _cfg.get("system_unit") or "metric",
                   date_fmt=date_format or _cfg.get("date_format") or "DMY",
                   time_fmt=time_format or _cfg.get("time_format") or "full",
                   email=email,
                   ww_id=ww_id,
                   voice_id=voice_id)
    db.session.add(entry)
    db.session.commit()
    return entry


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
        if loc:
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
        elif tts_plug in _cfg["tts"]:
            tts_config = _cfg["tts"][tts_plug]
        else:
            tts_config = {}
        voice_id = get_voice_id(tts_plug, device.lang, tts_config)
        update_voice_definition(voice_id,
                                lang=device.lang,
                                tts_config=tts_config,
                                plugin=tts_plug)
        device.voice_id = voice_id

    if "wake_word" in kwargs:
        default_ww = kwargs["wake_word"]
        ww_module = kwargs["ww_module"]
        if "ww_config" in kwargs:
            ww_config = kwargs["ww_config"]
        elif default_ww in _cfg["hotwords"]:
            ww_config = _cfg["hotwords"][default_ww]
        else:
            ww_config = {}
        ww_id = get_ww_id(ww_module, default_ww, ww_config)
        update_wakeword_definition(ww_id,
                                   name=default_ww,
                                   ww_config=ww_config,
                                   plugin=ww_module)
        device.ww_id = ww_id

    db.session.commit()

    return device


def list_devices():
    return Device.query.all()


def delete_device(uuid):
    device = get_device(uuid)
    if not device:
        return False
    db.session.delete(device)
    db.session.commit()
    return True


def add_skill_settings(remote_id, display_name=None,
                       settings_json=None, metadata_json=None):
    entry = SkillSettings(remote_id=remote_id,
                          display_name=display_name,
                          settings_json=settings_json,
                          metadata_json=metadata_json)
    db.session.add(entry)
    db.session.commit()
    return entry


def list_skill_settings():
    return SkillSettings.query.all()


def get_skill_settings(remote_id):
    return SkillSettings.query.filter_by(remote_id=remote_id).first()


def get_skill_settings_for_device(uuid):
    device = get_device(uuid)
    if not device or not device.isolated_skills:
        return list_skill_settings()
    return SkillSettings.query.filter(SkillSettings.remote_id.startswith(f"@{uuid}|")).all()


def delete_skill_settings(remote_id):
    entry = get_skill_settings(remote_id)
    if not entry:
        return False
    db.session.delete(entry)
    db.session.commit()
    return True


def delete_skill_settings_for_device(uuid):
    entry = get_skill_settings_for_device(uuid)
    if not entry:
        return False
    db.session.delete(entry)
    db.session.commit()
    return True


def update_skill_settings(remote_id, display_name=None,
                          settings_json=None, metadata_json=None):
    settings: SkillSettings = get_skill_settings(remote_id)
    if not settings:
        settings = add_skill_settings(remote_id=remote_id,
                                      display_name=display_name,
                                      settings_json=settings_json,
                                      metadata_json=metadata_json)

    else:
        if display_name:
            settings.display_name = display_name
        if settings_json:
            settings.settings = settings_json
        if metadata_json:
            settings.meta = metadata_json
        db.session.commit()

    return settings


def add_ww_recording(uuid, byte_data, transcription, meta):
    count = db.session.query(WakeWordRecording).count() + 1
    rec_id = f"@{uuid}|{transcription}|{count}"
    entry = WakeWordRecording(
        recording_id=rec_id,
        transcription=transcription,
        sample=byte_data,
        metadata_json=meta,
        uuid=uuid,
        timestamp=time.time()
    )
    db.session.add(entry)
    db.session.commit()
    return entry


def update_ww_recording(rec_id, transcription, metadata):
    entry = get_ww_recording(rec_id)
    if entry:
        if transcription:
            entry.transcription = transcription
        if metadata:
            entry.metadata_json = metadata
        db.session.commit()
    return entry


def get_ww_recording(rec_id):
    return WakeWordRecording.query.filter_by(recording_id=rec_id).first()


def delete_ww_recording(rec_id):
    entry = get_ww_recording(rec_id)
    if not entry:
        return False
    db.session.delete(entry)
    db.session.commit()
    return True


def list_ww_recordings():
    return WakeWordRecording.query.all()


def add_stt_recording(uuid, byte_data, transcription, metadata=None):
    count = db.session.query(UtteranceRecording).count() + 1
    rec_id = f"@{uuid}|{transcription}|{count}"
    entry = UtteranceRecording(
        recording_id=rec_id,
        transcription=transcription,
        sample=byte_data,
        metadata_json=metadata or {},
        uuid=uuid,
        timestamp=time.time()
    )
    db.session.add(entry)
    db.session.commit()
    return entry


def update_stt_recording(rec_id, transcription, metadata):
    entry = get_stt_recording(rec_id)
    if entry:
        if transcription:
            entry.transcription = transcription
        if metadata:
            entry.metadata_json = metadata
        db.session.commit()
    return entry


def get_stt_recording(rec_id):
    return UtteranceRecording.query.filter_by(recording_id=rec_id).first()


def delete_stt_recording(rec_id):
    entry = get_stt_recording(rec_id)
    if not entry:
        return False
    db.session.delete(entry)
    db.session.commit()
    return True


def list_stt_recordings():
    return UtteranceRecording.query.all()


def add_oauth_token(token_id, token_data):
    entry = OAuthToken(token_id=token_id, data=token_data)
    db.session.add(entry)
    db.session.commit()
    return entry


def get_oauth_token(token_id):
    return OAuthToken.query.filter_by(token_id=token_id).first()


def update_oauth_token(token_id, token_data):
    entry = get_oauth_token(token_id)
    if entry:
        entry.data = token_data
        db.session.commit()
    return entry


def delete_oauth_token(token_id):
    entry = get_oauth_token(token_id)
    if not entry:
        return False
    db.session.delete(entry)
    db.session.commit()
    return True


def list_oauth_tokens():
    return OAuthToken.query.all()


def add_oauth_application(token_id, client_id, client_secret,
                          auth_endpoint, token_endpoint, refresh_endpoint,
                          callback_endpoint, scope, shell_integration=True):
    entry = OAuthApplication(token_id=token_id,
                             client_id=client_id,
                             client_secret=client_secret,
                             auth_endpoint=auth_endpoint,
                             token_endpoint=token_endpoint,
                             refresh_endpoint=refresh_endpoint,
                             callback_endpoint=callback_endpoint,
                             scope=scope,
                             shell_integration=shell_integration)
    db.session.add(entry)
    db.session.commit()

    return entry


def update_oauth_application(token_id=None, client_id=None, client_secret=None,
                             auth_endpoint=None, token_endpoint=None, refresh_endpoint=None,
                             callback_endpoint=None, scope=None, shell_integration=None):
    entry = get_oauth_application(token_id)
    if not entry:
        shell_integration = shell_integration or True
        entry = add_oauth_application(token_id, client_id, client_secret,
                                      auth_endpoint, token_endpoint, refresh_endpoint,
                                      callback_endpoint, scope, shell_integration)

    if client_id is not None:
        entry.client_id = client_id
    if client_secret is not None:
        entry.client_secret = client_secret
    if auth_endpoint is not None:
        entry.auth_endpoint = auth_endpoint
    if token_endpoint is not None:
        entry.token_endpoint = token_endpoint
    if refresh_endpoint is not None:
        entry.refresh_endpoint = refresh_endpoint
    if callback_endpoint is not None:
        entry.callback_endpoint = callback_endpoint
    if scope is not None:
        entry.scope = scope
    if shell_integration is not None:
        entry.shell_integration = shell_integration
    db.session.commit()
    return entry


def get_oauth_application(token_id):
    return OAuthApplication.query.filter_by(token_id=token_id).first()


def delete_oauth_application(token_id):
    entry = get_oauth_application(token_id)
    if not entry:
        return False
    db.session.delete(entry)
    db.session.commit()
    return True


def list_oauth_applications():
    return OAuthApplication.query.all()


def add_voice_definition(plugin, lang, tts_config,
                         name=None, offline=None, gender=None) -> VoiceDefinition:
    voice_id = get_voice_id(plugin, lang, tts_config)
    name = name or voice_id
    entry = VoiceDefinition(voice_id=voice_id, name=name, lang=lang, plugin=plugin,
                            tts_config=tts_config, offline=offline, gender=gender)

    db.session.add(entry)
    db.session.commit()
    return entry


def get_voice_definition(voice_id) -> VoiceDefinition:
    return VoiceDefinition.query.filter_by(voice_id=voice_id).first()


def delete_voice_definition(voice_id):
    entry = get_voice_definition(voice_id)
    if not entry:
        return False
    db.session.delete(entry)
    db.session.commit()
    return True


def update_voice_definition(voice_id, name=None, lang=None, plugin=None,
                            tts_config=None, offline=None, gender=None) -> dict:
    voice_def: VoiceDefinition = get_voice_definition(voice_id)
    if not voice_def:
        if not plugin:
            plugin = voice_id.split("_")[0]
        if not lang:
            lang = voice_id.split("_")[1]
        voice_def = add_voice_definition(name=name, lang=lang, plugin=plugin,
                                         tts_config=tts_config, offline=offline,
                                         gender=gender)
    else:
        if name:
            voice_def.name = name
        if lang:
            voice_def.lang = lang
        if plugin:
            voice_def.plugin = plugin
        if tts_config:
            voice_def.tts_config = tts_config
        if offline:
            voice_def.offline = offline
        if gender:
            voice_def.gender = gender
        db.session.commit()

    return voice_def
