from setuptools import setup
import os


def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths


extra_files = package_files('mock_mycroft_backend')

setup(
    name='mock-mycroft-backend',
    version='0.2.1',
    packages=['mock_mycroft_backend',
              'mock_mycroft_backend.backend',
              'mock_mycroft_backend.database'],
    install_requires=['Flask>=0.12', 'requests>=2.2.1', 'Flask-Mail',
                      'speech2text', 'pyOpenSSL', "flask_sslify",
                      "json_database"],
    package_data={'': extra_files},
    include_package_data=True,
    url='https://github.com/OpenJarbas/mock-backend',
    license='Apache-2.0',
    author='jarbasAI',
    author_email='jarbasai@mailfence.com',
    description='mock mycroft backend',
    entry_points={
        'console_scripts': [
            'mock-mycroft-backend=mock_mycroft_backend.__main__:main'
        ]
    }
)
