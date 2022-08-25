from flask import request

from ovos_local_backend.backend.decorators import noindex, requires_auth
from ovos_local_backend.configuration import CONFIGURATION
from ovos_local_backend.database.wakewords import save_ww_recording


def get_precise_routes(app):
    @app.route('/precise/upload', methods=['POST'])
    @noindex
    @requires_auth
    def precise_upload():
        if CONFIGURATION["record_wakewords"]:
            auth = request.headers.get('Authorization', '').replace("Bearer ", "")
            uuid = auth.split(":")[-1]  # this split is only valid here, not selene
            save_ww_recording(uuid, request.files)

        # TODO - share with upstream setting
        # contribute to mycroft open dataset
        # may require https://github.com/OpenVoiceOS/OVOS-local-backend/issues/20
        uploaded = False

        return {"success": True,
                "sent_to_mycroft": uploaded,
                "saved": CONFIGURATION["record_wakewords"]}

    return app
