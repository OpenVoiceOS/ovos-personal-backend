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
import json
from tempfile import NamedTemporaryFile

import flask
import requests
from ovos_config import Configuration
from speech_recognition import Recognizer, AudioFile, AudioData

from ovos_local_backend.backend import API_VERSION
from ovos_local_backend.backend.decorators import noindex, requires_auth, requires_opt_in
from ovos_local_backend.database import add_stt_recording


def transcribe(audio: AudioData, lang: str):
    urls = Configuration().get("stt_servers") or ["https://stt.openvoiceos.org/stt"]

    for url in urls:
        try:
            response = requests.post(url, data=audio.get_wav_data(),
                                     headers={"Content-Type": "audio/wav"},
                                     params={"lang": lang})
            if response:
                return response.text
        except:
            continue
    return ""


def bytes2audiodata(data: bytes):
    recognizer = Recognizer()
    with NamedTemporaryFile() as fp:
        fp.write(data)
        with AudioFile(fp.name) as source:
            audio = recognizer.record(source)
    return audio


@requires_opt_in  # this decorator ensures the uuid opted-in
def save_stt_recording(uuid: str, audio: AudioData, utterance: str):
    allowed = Configuration()["listener"].get("record_utterances") or \
              Configuration()["listener"].get("save_utterances")  # backwards compat
    if allowed:
        audio_bytes = audio.get_wav_data()
        add_stt_recording(uuid, audio_bytes, utterance)


def get_stt_routes(app):
    # makes personal backend a valid entry in ovos-stt-plugin-server
    # DOES NOT save data
    @app.route("/stt", methods=['POST'])
    @noindex
    def stt_public_server():
        audio_bytes = flask.request.data
        lang = str(flask.request.args.get("lang", "en-us"))
        audio = bytes2audiodata(audio_bytes)
        utterance = transcribe(audio, lang)
        return json.dumps([utterance])

    # DEPRECATED - compat for old selene plugin
    # if opt-in saves recordings
    @app.route("/" + API_VERSION + "/stt", methods=['POST'])
    @noindex
    @requires_auth
    def stt():
        flac_audio = flask.request.data
        lang = str(flask.request.args.get("lang", "en-us"))
        audio = bytes2audiodata(flac_audio)
        utterance = transcribe(audio, lang)

        auth = flask.request.headers.get('Authorization', '').replace("Bearer ", "")
        uuid = auth.split(":")[-1]  # this split is only valid here, not selene
        save_stt_recording(uuid, audio, utterance)

        return json.dumps([utterance])

    return app
