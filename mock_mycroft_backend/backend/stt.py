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
from tempfile import NamedTemporaryFile
import json
from flask import request
from speech_recognition import Recognizer, AudioFile
import time
from os.path import join, isdir
from os import makedirs
from mock_mycroft_backend.backend import API_VERSION
from mock_mycroft_backend.configuration import CONFIGURATION
from mock_mycroft_backend.backend.decorators import noindex
from mock_mycroft_backend.database.utterances import JsonUtteranceDatabase
from speech2text import STTFactory

recognizer = Recognizer()
engine = STTFactory.create(CONFIGURATION["stt"])


def get_stt_routes(app):
    @app.route("/" + API_VERSION + "/stt", methods=['POST'])
    @noindex
    def stt():
        flac_audio = request.data
        lang = str(request.args.get("lang", "en-us"))
        with NamedTemporaryFile() as fp:
            fp.write(flac_audio)
            with AudioFile(fp.name) as source:
                audio = recognizer.record(source)  # read the entire audio file
            try:
                utterance = engine.execute(audio, language=lang)
            except:
                utterance = "speak speech recognition failed"
        if CONFIGURATION["record_utterances"]:
            wav = audio.get_wav_data()
            path = join(CONFIGURATION["utterances_path"],
                        str(time.time()).replace(".", "") + ".wav")
            if not isdir(CONFIGURATION["utterances_path"]):
                makedirs(CONFIGURATION["utterances_path"])
            with open(path, "wb") as f:
                f.write(wav)
            with JsonUtteranceDatabase() as db:
                db.add_utterance(utterance, path)
        return json.dumps([utterance])

    return app
