import json
import time

from flask_sqlalchemy import SQLAlchemy

from ovos_local_backend.backend.decorators import requires_opt_in
from ovos_local_backend.configuration import CONFIGURATION

# create the extension
db = SQLAlchemy()


def connect_db(app):
    # configure the SQLite database, relative to the app instance folder
    # TODO - path from config
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
    # initialize the app with the extension
    db.init_app(app)

    with app.app_context():
        db.create_all()

    return app, db


class VoiceDefinition(db.Model):
    voice_id = db.Column(db.String, primary_key=True)
    lang = db.Column(db.String, nullable=False)
    plugin = db.Column(db.String, nullable=False)  # "module" in mycroft.conf
    voice_cfg = db.Column(db.String, nullable=False)  # arbitrary data for mycroft.conf/OPM
    offline = db.Column(db.Boolean, nullable=False)
    # optional metadata
    gender = db.Column(db.String)


def get_voice_id(plugin_name, lang, tts_cfg):
    # taken from https://github.com/OpenVoiceOS/ovos-plugin-manager/pull/131
    skip_keys = ["module", "meta"]
    keys = sorted([f"{k}_{v}" for k, v in tts_cfg.items() if k not in skip_keys])
    voiceid = f"{plugin_name}_{lang}_{keys}.json".replace("/", "_")
    return voiceid


def get_ww_id(plugin_name, ww_name, ww_cfg):
    # taken from https://github.com/OpenVoiceOS/ovos-plugin-manager/pull/131
    skip_keys = ["display_name", "meta"]
    keys = sorted([f"{k}_{v}" for k, v in ww_cfg.items() if k not in skip_keys])
    voiceid = f"{plugin_name}_{ww_name}_{keys}.json".replace("/", "_")
    return voiceid


class WakeWordDefinition(db.Model):
    ww_id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    plugin = db.Column(db.String, nullable=False)  # "module" in mycroft.conf
    ww_cfg = db.Column(db.String, nullable=False)  # arbitrary data for mycroft.conf/OPM


class Device(db.Model):
    uuid = db.Column(db.String, primary_key=True)
    token = db.Column(db.String)  # access token, sent to device during pairing
    # device backend preferences
    name = db.Column(db.String)
    placement = db.Column(db.String)  # indoor location
    isolated_skills = db.Column(db.Boolean)
    opt_in = db.Column(db.Boolean)
    email = db.Column(db.String)  # for sending email api, not registering
    # remote mycroft.conf settings
    date_fmt = db.Column(db.String)
    time_fmt = db.Column(db.String)
    system_unit = db.Column(db.String)
    lang = db.Column(db.String)
    location_json = db.Column(db.String)  # we don't care about querying sub data

    voice_id = db.Column(db.String)
    ww_id = db.Column(db.String)

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

        ww_cfg = {}
        listener = {}
        if self.ww_id:
            ww = db.session.query(WakeWordDefinition). \
                filter(WakeWordDefinition.ww_id == self.ww_id).first()

            if ww:
                cfg = json.loads(ww.ww_cfg)
                ww_cfg = {ww.name: cfg}
                # NOTE - selene returns the full listener config
                # this SHOULD NOT be done, since backend has no clue of hardware downstream
                # we return only wake word config
                listener = {"wakeWord": ww.name.replace(" ", "_")}

        tts_settings = {}
        if self.voice_id:
            voice = db.session.query(VoiceDefinition). \
                filter(VoiceDefinition.voice_id == self.voice_id).first()

            if voice:
                cfg = json.loads(voice.voice_cfg)
                tts_settings = {"module": voice.plugin,
                                voice.plugin: cfg}

        return {
            "dateFormat": self.date_fmt,
            "optIn": self.opt_in,
            "systemUnit": self.system_unit,
            "timeFormat": self.time_fmt,
            "uuid": self.uuid,
            "lang": self.lang,
            "location": json.loads(self.location_json),
            "listenerSetting": listener,
            "hotwordsSetting": ww_cfg,  # not present in selene, parsed correctly by core
            'ttsSettings': tts_settings
        }

    @staticmethod
    def deserialize(data):
        if isinstance(data, str):
            data = json.loads(data)

        lang = data.get("lang") or CONFIGURATION.get("lang") or "en-us"

        voice_id = None
        tts_module = data.get("default_tts")
        tts_cfg = data.get("default_tts_cfg") or {}
        if tts_module:
            voice_id = get_voice_id(tts_module, lang, tts_cfg)

        ww_id = None
        ww_name = data.get("default_ww")
        ww_cfg = data.get("default_ww_cfg") or {}
        ww_module = ww_cfg.get("module")
        if ww_module:
            ww_id = get_ww_id(ww_module, ww_name, ww_cfg)

        location_json = data.get("location") or CONFIGURATION["default_location"]
        if isinstance(location_json, dict):
            location_json = json.dumps(location_json)

        mail_cfg = CONFIGURATION.get("email", {})
        email = data.get("email") or \
                mail_cfg.get("recipient") or \
                mail_cfg.get("smtp", {}).get("username")

        return Device(uuid=data["uuid"],
                      token=data["token"],
                      placement=data.get("device_location") or "somewhere",
                      name=data.get("name") or f"Device-{data['uuid']}",
                      isolated_skills=data.get("isolated_skills", False),
                      location_json=location_json,
                      opt_in=data.get("opt_in"),
                      system_unit=data.get("system_unit") or CONFIGURATION.get("system_unit") or "metric",
                      date_fmt=data.get("date_format") or CONFIGURATION.get("date_format") or "DMY",
                      time_fmt=data.get("time_format") or CONFIGURATION.get("time_format") or "full",
                      email=email,
                      ww_id=ww_id,
                      voice_id=voice_id)

    def serialize(self):
        mail_cfg = CONFIGURATION.get("email", {})
        email = self.email or \
                mail_cfg.get("recipient") or \
                mail_cfg.get("smtp", {}).get("username")
        location = self.location_json or CONFIGURATION["default_location"]
        if isinstance(location, str):
            location = json.loads(location)

        default_tts = None
        default_tts_cfg = {}
        if self.voice_id:
            voice = db.session.query(VoiceDefinition). \
                filter(VoiceDefinition.voice_id == self.voice_id).first()
            if voice:
                default_tts_cfg = json.loads(voice.voice_cfg)
                default_tts = voice.plugin

        default_ww = None
        default_ww_cfg = {}
        if self.ww_id:
            ww = db.session.query(WakeWordDefinition). \
                filter(WakeWordDefinition.ww_id == self.ww_id).first()
            if ww:
                default_ww_cfg = json.loads(ww.ww_cfg)
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
            "location": location,
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

    mail_cfg = CONFIGURATION.get("email", {})
    email = email or \
            mail_cfg.get("recipient") or \
            mail_cfg.get("smtp", {}).get("username")

    entry = Device(uuid=uuid,
                   token=token,
                   lang=lang,
                   placement=device_location,
                   name=name or f"Device-{uuid}",
                   isolated_skills=isolated_skills,
                   location_json=json.dumps(location),
                   opt_in=opt_in,
                   system_unit=system_unit or CONFIGURATION.get("system_unit") or "metric",
                   date_fmt=date_format or CONFIGURATION.get("date_format") or "DMY",
                   time_fmt=time_format or CONFIGURATION.get("time_format") or "full",
                   email=email,
                   ww_id=ww_id,
                   voice_id=voice_id)
    db.session.add(entry)
    db.session.commit()


def get_device(uuid):
    return Device.query.filter_by(uuid=uuid).first()


def update_device(uuid, **kwargs):

    device = Device.query.filter_by(uuid=uuid).first()
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
        if isinstance(loc, dict):
            loc = json.dumps(loc)
        device.location_json = loc
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
            tts_cfg = kwargs["tts_config"]
        elif tts_plug in CONFIGURATION["tts_configs"]:
            tts_cfg = CONFIGURATION["tts_configs"][tts_plug]
        else:
            tts_cfg = {}
        voice_id = get_voice_id(tts_plug, device.lang, tts_cfg)
        voice = VoiceDefinition.query.filter_by(voice_id=voice_id).first()
        if not voice:
            pass  # TODO add voice def
        device.voice_id = voice_id

    if "wake_word" in kwargs:
        default_ww = kwargs["wake_word"]
        ww_module = kwargs["ww_module"]
        if "ww_config" in kwargs:
            ww_cfg = kwargs["ww_config"]
        elif default_ww  in CONFIGURATION["ww_configs"]:
            ww_cfg = CONFIGURATION["ww_configs"][default_ww]
        else:
            ww_cfg = {}
        ww_id = get_ww_id(ww_module, default_ww, ww_cfg)
        ww = WakeWordDefinition.query.filter_by(ww_id=ww_id).first()
        if not ww:
            pass  # TODO add ww def
        device.ww_id = ww_id

    data = device.serialize()
    db.session.commit()

    return data


class SkillSettings(db.Model):
    remote_id = db.Column(db.String,
                          primary_key=True)  # depends on Device.isolated_skills, @{uuid}|{skill_id} or {skill_id}
    display_name = db.Column(db.String)  # for friendly UI, default to skill_id
    settings_json = db.Column(db.String, nullable=False)  # actual skill settings file
    metadata_json = db.Column(db.String, nullable=False)  # how to display user facing settings editor

    def serialize(self):
        # settings meta with updated placeholder values from settings
        # old style selene db stored skill settings this way
        meta = json.loads(self.metadata_json)
        settings = json.loads(self.settings_json)
        for idx, section in enumerate(meta.get('sections', [])):
            for idx2, field in enumerate(section["fields"]):
                if "value" not in field:
                    continue
                if field["name"] in settings:
                    meta['sections'][idx]["fields"][idx2]["value"] = settings[field["name"]]
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

        settings_json = json.dumps(skill_json)
        metadata_json = json.dumps(skill_meta)
        return SkillSettings(settings_json=settings_json,
                             metadata_json=metadata_json,
                             display_name=display_name,
                             remote_id=remote_id)


class Metric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    metric_type = db.Column(db.String, nullable=False)
    metadata_json = db.Column(db.String, nullable=False)  # arbitrary data
    # TODO - extract explicit fields from json for things we want to be queryable

    timestamp = db.Column(db.Integer, primary_key=True)  # unix seconds
    uuid = db.Column(db.String)  # TODO - link to devices table


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
    transcription = db.Column(db.String, nullable=False)
    metadata_json = db.Column(db.String)  # arbitrary metadata
    sample = db.Column(db.LargeBinary, nullable=False)  # audio data

    timestamp = db.Column(db.Integer, primary_key=True)  # unix seconds
    uuid = db.Column(db.String)  # TODO - link to devices table


@requires_opt_in
def save_stt_recording(uuid, audio, utterance):
    entry = UtteranceRecording(
        utterance_id=db.session.query(UtteranceRecording).count() + 1,
        transcription=utterance,
        sample=audio.get_wav_data(),
        metadata_json="{}",  # TODO - allow expanding in future

        uuid=uuid,
        timestamp=time.time()
    )
    db.session.add(entry)
    db.session.commit()


class WakeWordRecording(db.Model):
    wakeword_id = db.Column(db.Integer, primary_key=True)
    transcription = db.Column(db.String, nullable=False)
    audio_tag = db.Column(db.String)  # "untagged" / "wake_word" / "speech" / "noise" / "silence"
    speaker_tag = db.Column(db.String)  # "untagged" / "male" / "female" / "children"
    metadata_json = db.Column(db.String, nullable=False)  # arbitrary metadata
    sample = db.Column(db.LargeBinary, nullable=False)  # audio data

    timestamp = db.Column(db.Integer, primary_key=True)  # unix seconds
    uuid = db.Column(db.String)  # TODO - link to devices table


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
        return  # TODO - some error? just ignore entry for now

    # classic mycroft devices send
    # {"name": "hey-mycroft",
    # "engine": "0f4df281688583e010c26831abdc2222",
    # "time": "1592192357852",
    # "sessionId": "7d18e208-05b5-401e-add6-ee23ae821967",
    # "accountId": "0",
    # "model": "5223842df0cdee5bca3eff8eac1b67fc"}

    entry = WakeWordRecording(
        wakeword_id=db.session.query(WakeWordRecording).count() + 1,
        transcription=meta["name"],
        sample=audio,
        metadata_json=json.dumps(meta),

        uuid=uuid,
        timestamp=time.time()
    )
    db.session.add(entry)
    db.session.commit()
