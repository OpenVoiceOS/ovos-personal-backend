from flask import request
from ovos_local_backend.backend.decorators import noindex, requires_auth
from ovos_local_backend.configuration import CONFIGURATION
from ovos_local_backend.database.wakewords import JsonWakeWordDatabase
from ovos_local_backend.database.settings import DeviceDatabase
import time
from os.path import join, isdir
from os import makedirs
import json


def _save_ww(uploads):
    if not isdir(join(CONFIGURATION["data_path"], "wakewords")):
        makedirs(join(CONFIGURATION["data_path"], "wakewords"))
    name = str(time.time()).replace(".", "")
    wav_path = join(CONFIGURATION["data_path"], "wakewords",
                    name + ".wav")
    meta_path = join(CONFIGURATION["data_path"], "wakewords",
                     name + ".meta")
    for precisefile in uploads:
        fn = uploads[precisefile].filename
        if fn == 'audio':
            uploads[precisefile].save(wav_path)
        if fn == 'metadata':
            uploads[precisefile].save(meta_path)
    with open(meta_path) as f:
        meta = json.load(f)
    # {"name": "hey-mycroft",
    # "engine": "0f4df281688583e010c26831abdc2222",
    # "time": "1592192357852",
    # "sessionId": "7d18e208-05b5-401e-add6-ee23ae821967",
    # "accountId": "0",
    # "model": "5223842df0cdee5bca3eff8eac1b67fc"}
    with JsonWakeWordDatabase() as db:
        db.add_wakeword(meta["name"], wav_path, meta)


def get_precise_routes(app):
    @app.route('/precise/upload', methods=['POST'])
    @noindex
    @requires_auth
    def precise_upload():
        if CONFIGURATION["record_wakewords"]:
            auth = request.headers.get('Authorization', '').replace("Bearer ", "")
            uuid = auth.split(":")[-1]  # this split is only valid here, not selene
            device = DeviceDatabase().get_device(uuid)
            if device and device.opt_in:
                _save_ww(request.files)

        # TODO - share upstream setting
        uploaded = False

        return {"success": True,
                "sent_to_mycroft": uploaded,
                "saved": CONFIGURATION["record_wakewords"]}

    return app
