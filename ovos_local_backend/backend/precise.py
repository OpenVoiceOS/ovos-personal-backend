from flask import request

from ovos_local_backend.backend import API_VERSION
from ovos_local_backend.backend.decorators import noindex, requires_auth
from ovos_local_backend.configuration import CONFIGURATION
from ovos_local_backend.database import save_ww_recording

def get_precise_routes(app):
    @app.route('/precise/upload', methods=['POST'])
    @noindex
    @requires_auth
    def precise_upload():
        success = False
        if CONFIGURATION["record_wakewords"]:
            auth = request.headers.get('Authorization', '').replace("Bearer ", "")
            uuid = auth.split(":")[-1]  # this split is only valid here, not selene
            success = save_ww_recording(uuid, request.files)

        return {"success": success,
                "sent_to_mycroft": False,
                "saved": CONFIGURATION["record_wakewords"]}

    @app.route(f'/{API_VERSION}/device/<uuid>/wake-word-file', methods=['POST'])
    @noindex
    @requires_auth
    def precise_upload_v2(uuid):
        success = False
        if 'audio' not in request.files:
            return "No Audio to upload", 400

        if CONFIGURATION["record_wakewords"]:
            success = save_ww_recording(uuid, request.files)

        return {"success": success,
                "sent_to_mycroft": False,
                "saved": CONFIGURATION["record_wakewords"]}

    return app
