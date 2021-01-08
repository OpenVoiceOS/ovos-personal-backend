from json_database import JsonDatabaseXDG


class UtteranceRecording:
    def __init__(self, utterance_id, transcription, path):
        self.utterance_id = utterance_id
        self.transcription = transcription
        self.path = path


class JsonUtteranceDatabase(JsonDatabaseXDG):
    def __init__(self):
        super().__init__("mycroft_utterances")

    def add_utterance(self, transcription, path):
        utterance_id = self.total_utterances() + 1
        utterance = UtteranceRecording(utterance_id, transcription, path)
        self.add_item(utterance)

    def total_utterances(self):
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

