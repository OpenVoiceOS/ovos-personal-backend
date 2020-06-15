# Copyright 2019 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import base64
from requests import get
from mock_mycroft_backend.backend.decorators import noindex
from mock_mycroft_backend.utils import nice_json
from flask import send_file, request


def build_response(audio_file, visimes=None):
    if visimes is not None:
        with open(audio_file, "rb") as f:
            audio_data = f.read()
        encoded_audio = base64.b64encode(audio_data)
        res = {
            "audio_base64": encoded_audio.decode("utf-8"),
            "visimes": visimes
        }
        return nice_json(res)
    else:
        return send_file(
            audio_file,
            mimetype="audio/wav")


def get_tts_routes(app):
    @app.route("/synthesize/mimic2/<voice>/<lang>", methods=['GET'])
    @noindex
    def mimic2_proxy(voice, lang):
        # TODO cache results to save calls to mycroft.ai
        return get("https://mimic-api.mycroft.ai/synthesize", params=request.args).content

    return app
