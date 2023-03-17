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
from speech_recognition import Recognizer, AudioFile
from ovos_local_backend.backend import API_VERSION
from ovos_local_backend.backend.decorators import noindex, requires_auth, requires_opt_in
from ovos_local_backend.configuration import CONFIGURATION
from ovos_local_backend.database import add_stt_recording
from ovos_plugin_manager.stt import OVOSSTTFactory

recognizer = Recognizer()
engine = OVOSSTTFactory.create(CONFIGURATION["stt"])


@requires_opt_in
def save_stt_recording(uuid, audio, utterance):
    audio_bytes = audio.get_wav_data()
    add_stt_recording(uuid, audio_bytes, utterance)


def get_stt_routes(app):
    @app.route("/" + API_VERSION + "/stt", methods=['POST'])
    @noindex
    @requires_auth
    def stt():
        flac_audio = flask.request.data
        lang = str(flask.request.args.get("lang", "en-us"))
        with NamedTemporaryFile() as fp:
            fp.write(flac_audio)
            with AudioFile(fp.name) as source:
                audio = recognizer.record(source)  # read the entire audio file
            try:
                utterance = engine.execute(audio, language=lang)
            except:
                utterance = ""

        if CONFIGURATION["record_utterances"]:
            auth = flask.request.headers.get('Authorization', '').replace("Bearer ", "")
            uuid = auth.split(":")[-1]  # this split is only valid here, not selene
            save_stt_recording(uuid, audio, utterance)

        return json.dumps([utterance])

    return app
