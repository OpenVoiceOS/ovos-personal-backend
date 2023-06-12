import os.path

from ovos_config.utils import init_module_config

init_module_config("ovos_local_backend",
                   "ovos_local_backend",
                   {"config_filename": "ovos_backend.conf",
                    "base_folder" :"ovos_backend",
                    "default_config_path": f"{os.path.dirname(__file__)}/ovos_backend.conf"})

from ovos_local_backend.backend import start_backend
