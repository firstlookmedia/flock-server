import os
import json
import secrets


class Tokens(object):
    def __init__(self):
        self.path = '/data/tokens.json'
        self.load()

    def load(self):
        if not os.path.exists(self.path):
            self.tokens = {}
            self.save()
        else:
            with open(self.path) as f:
                self.tokens = json.load(f)

    def save(self):
        with open(self.path, 'w') as f:
            json.dump(self.tokens, f)

    def get(self, username):
        if self.exists(username):
            return self.tokens[username]
        else:
            return None

    def exists(self, username):
        return username in self.tokens

    def generate(self, username):
        token = secrets.token_hex(16)
        self.tokens[username] = token
        self.save()
        return token
