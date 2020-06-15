from flask import request
from mock_mycroft_backend.backend.decorators import noindex
from mock_mycroft_backend.configuration import CONFIGURATION
from mock_mycroft_backend.database.wakewords import JsonWakeWordDatabase
import time
from os.path import join, isdir
from os import makedirs
import json
from io import BytesIO, StringIO
import requests


def upload_wake_word(audio, metadata,
                     upload_url="https://training.mycroft.ai/precise/upload"):
    return requests.post(
        upload_url, files={
            'audio': BytesIO(audio),
            'metadata': StringIO(json.dumps(metadata))
        }
    )


def get_precise_routes(app):
    @app.route('/precise/upload', methods=['POST'])
    @noindex
    def precise_upload():
        uploads = request.files
        if CONFIGURATION["record_wakewords"]:

            if not isdir(CONFIGURATION["wakewords_path"]):
                makedirs(CONFIGURATION["wakewords_path"])

            for precisefile in uploads:
                fn = uploads[precisefile].filename
                name = str(time.time()).replace(".", "")
                if fn == 'audio':
                    path = join(CONFIGURATION["wakewords_path"], name + ".wav")
                    uploads[precisefile].save(path)

                if fn == 'metadata':
                    path = join(CONFIGURATION["wakewords_path"],
                                name + ".meta")
                    uploads[precisefile].save(path)
                    with open(path) as f:
                        meta = json.load(f)
                    # {"name": "hey-mycroft",
                    # "engine": "0f4df281688583e010c26831abdc2222",
                    # "time": "1592192357852",
                    # "sessionId": "7d18e208-05b5-401e-add6-ee23ae821967",
                    # "accountId": "0",
                    # "model": "5223842df0cdee5bca3eff8eac1b67fc"}
                    with JsonWakeWordDatabase() as db:
                        path = join(CONFIGURATION["wakewords_path"],
                                    name + ".wav")
                        db.add_wakeword(meta["name"], path, meta)

        uploaded = False
        if CONFIGURATION["upload_wakewords_to_mycroft"]:
            uploaded = False
            audio = None
            meta = None
            for precisefile in uploads:
                fn = uploads[precisefile].filename
                if fn == 'audio':
                    audio = uploads[precisefile]

                if fn == 'metadata':

                    meta = uploads[precisefile]
            if audio and meta:
                upload_wake_word(audio, meta)
                uploaded = True
        if CONFIGURATION["upload_wakewords_to_community"]:
            # TODO PR to https://github.com/MycroftAI/Precise-Community-Data
            uploaded = False

        return {"success": True,
                "sent_to_mycroft": uploaded,
                "saved": CONFIGURATION["record_wakewords"]}

    return app
