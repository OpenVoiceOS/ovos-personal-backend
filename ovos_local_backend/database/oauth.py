from json_database import JsonStorageXDG


class OAuthTokenDatabase(JsonStorageXDG):
    def __init__(self):
        super().__init__("ovos_oauth")

    def add_token(self, oauth_service, token_data):
        self[oauth_service] = token_data

    def total_tokens(self):
        return len(self)
