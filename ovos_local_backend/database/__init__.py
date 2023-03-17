from flask_sqlalchemy import SQLAlchemy
from ovos_local_backend.backend.decorators import requires_opt_in
import time


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
    plugin = db.Column(db.String, nullable=False)  # "module" in mycroft.conf
    ww_cfg = db.Column(db.String, nullable=False)  # arbitrary data for mycroft.conf/OPM
    # optional metadata
    fallback_ww_id = db.Column(db.String)  # TODO - link to ww table


class Device(db.Model):
    uuid = db.Column(db.String, primary_key=True)
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
    voice_id = db.Column(db.String)  # TODO - link to voices table
    ww_id = db.Column(db.String)  # TODO - link to ww table


class SkillSettings(db.Model):
    remote_id = db.Column(db.String,
                          primary_key=True)  # depends on Device.isolated_skills, @{uuid}|{skill_id} or {skill_id}
    display_name = db.Column(db.String)  # for friendly UI, default to skill_id
    settings_json = db.Column(db.String, nullable=False)  # actual skill settings file
    metadata_json = db.Column(db.String, nullable=False)  # how to display user facing settings editor


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
