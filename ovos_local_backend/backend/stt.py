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
import time
from os import makedirs
from os.path import join, isdir
from tempfile import NamedTemporaryFile

from flask import request
from ovos_local_backend.backend import API_VERSION
from ovos_local_backend.backend.decorators import noindex
from ovos_local_backend.configuration import CONFIGURATION
from ovos_local_backend.database.utterances import JsonUtteranceDatabase
from ovos_plugin_manager.stt import OVOSSTTFactory
from speech_recognition import Recognizer, AudioFile

recognizer = Recognizer()
engine = OVOSSTTFactory.create(CONFIGURATION["stt"])


def get_stt_routes(app):
    @app.route("/" + API_VERSION + "/stt", methods=['POST'])
    @noindex
    def stt():
        flac_audio = request.data
        lang = str(request.args.get("lang", "en-us"))
        with NamedTemporaryFile() as fp:
            fp.write(flac_audio)
            with AudioFile(fp.name) as source:
                audio = recognizer.record(
                    source)  # read the entire audio_only file
            try:
                utterance = engine.execute(audio, language=lang)
            except:
                utterance = "speak speech recognition failed"
        if CONFIGURATION["record_utterances"]:
            if not isdir(join(CONFIGURATION["data_path"], "utterances")):
                makedirs(join(CONFIGURATION["data_path"], "utterances"))
            wav = audio.get_wav_data()
            path = join(CONFIGURATION["data_path"], "utterances",
                        utterance + str(time.time()).replace(".", "") + ".wav")
            with open(path, "wb") as f:
                f.write(wav)
            with JsonUtteranceDatabase() as db:
                db.add_utterance(utterance, path)
        return json.dumps([utterance])

    return app
