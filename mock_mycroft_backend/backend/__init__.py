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

from flask import Flask
from flask_mail import Mail
from mock_mycroft_backend.configuration import CONFIGURATION

API_VERSION = CONFIGURATION["api_version"]


def create_app():
    app = Flask(__name__)

    mail = Mail(app)

    from mock_mycroft_backend.utils import nice_json
    from mock_mycroft_backend.backend.decorators import noindex
    from mock_mycroft_backend.backend.auth import get_auth_routes
    from mock_mycroft_backend.backend.device import get_device_routes
    from mock_mycroft_backend.backend.stt import get_stt_routes
    from mock_mycroft_backend.backend.tts import get_tts_routes
    from mock_mycroft_backend.backend.precise import get_precise_routes
    from mock_mycroft_backend.backend.external_apis import get_services_routes
    app = get_auth_routes(app)
    app = get_device_routes(app, mail)
    app = get_stt_routes(app)
    app = get_tts_routes(app)
    app = get_precise_routes(app)
    app = get_services_routes(app)

    @app.route("/", methods=['GET'])
    @noindex
    def hello():
        return nice_json({
            "message": "Welcome to Mock Mycroft Backend",
            "donate": "https://liberapay.com/jarbasAI",
            "author": "JarbasAI"
        })

    return app


def start_backend(port=CONFIGURATION["backend_port"], host="127.0.0.1"):
    app = create_app()
    app.run(port=port, use_reloader=False, host=host)
    return app


if __name__ == "__main__":
    start_backend()
