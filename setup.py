import os

from setuptools import setup


def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths


extra_files = package_files('ovos_local_backend')

setup(
    name='ovos-local-backend',
    version='0.1.2',
    packages=['ovos_local_backend',
              'ovos_local_backend.utils',
              'ovos_local_backend.backend',
              'ovos_local_backend.database'],
    install_requires=['Flask>=0.12', 'requests>=2.26.0', "yagmail",
                      'ovos-plugin-manager>=0.0.2a2',
                      'ovos-stt-plugin-chromium', 'pyOpenSSL', "geocoder",
                      "timezonefinder", "json_database"],
    package_data={'': extra_files},
    include_package_data=True,
    url='https://github.com/OpenVoiceOS/OVOS-local-backend',
    license='Apache-2.0',
    author='jarbasAI',
    author_email='jarbasai@mailfence.com',
    description='mock mycroft backend',
    entry_points={
        'console_scripts': [
            'ovos-local-backend=ovos_local_backend.__main__:main'
        ]
    }
)
