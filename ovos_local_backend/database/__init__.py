from flask_sqlalchemy import SQLAlchemy
from ovos_local_backend.backend.decorators import requires_opt_in
import time
import json


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
            ww = db.session.query(WakeWordDefinition).\
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
           # "optIn": self.opt_in, # backend should not be able to decide this, needs to happen device side
            "systemUnit": self.system_unit,
            "timeFormat": self.time_fmt,
            "uuid": self.uuid,
            "lang": self.lang,
            "location": json.loads(self.location_json),
            "listenerSetting": listener,
            "hotwordsSetting": ww_cfg,  # not present in selene, parsed correctly by core
            'ttsSettings': tts_settings
        }


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
