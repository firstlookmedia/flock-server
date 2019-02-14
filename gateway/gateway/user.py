import secrets
from elasticsearch_dsl import Date, Document, Text


class User(Document):
    username = Text()
    token = Text()
    created_at = Date()

    class Index:
        name = 'user'

    def save(self, ** kwargs):
        self.created_at = datetime.now()
        return super(Token, self).save(** kwargs)
