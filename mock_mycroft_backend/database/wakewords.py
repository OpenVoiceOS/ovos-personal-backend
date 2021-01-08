from json_database import JsonDatabaseXDG
import json


class WakeWordRecording:
    def __init__(self, wakeword_id, transcription, path, meta="{}"):
        self.wakeword_id = wakeword_id
        self.transcription = transcription
        self.path = path
        if isinstance(meta, str):
            meta = json.loads(meta)
        self.meta = meta


class JsonWakeWordDatabase(JsonDatabaseXDG):
    def __init__(self):
        super().__init__("mycroft_wakewords")

    def add_wakeword(self, transcription, path, meta="{}"):
        wakeword_id = self.total_wakewords() + 1
        wakeword = WakeWordRecording(wakeword_id, transcription, path, meta)
        self.add_item(wakeword)

    def total_wakewords(self):
        return len(self)

    def __enter__(self):
        """ Context handler """
        return self

    def __exit__(self, _type, value, traceback):
        """ Commits changes and Closes the session """
        try:
            self.commit()
        except Exception as e:
            print(e)


