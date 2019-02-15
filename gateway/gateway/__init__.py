import os
import json
import secrets
from datetime import datetime
from functools import wraps

from flask import Flask, request, Response
from elasticsearch.exceptions import ConnectionError
from elasticsearch_dsl import connections, Date, Document, Index, Search, Text


# Configure ElasticSearch default connection
if 'ELASTICSEARCH_HOST' in os.environ:
    elasticsearch_host = '{}:9200'.format(os.environ['ELASTICSEARCH_HOST'])
else:
    elasticsearch_host = 'elasticsearch:9200'
connections.create_connection(hosts=[elasticsearch_host], timeout=20)


class User(Document):
    username = Text()
    token = Text()
    created_at = Date()

    class Index:
        name = 'user'

    def save(self, ** kwargs):
        self.created_at = datetime.now()
        return super(User, self).save(** kwargs)


def create_app(test_config=None):
    # Flask
    app = Flask(__name__)
    if test_config:
        app.config.update(test_config)


    def check_auth(username, token):
        r = Search(index="user") \
            .query("match", username=username) \
            .query("match", token=token) \
            .execute()
        return len(r) == 1


    def authenticate():
        return Response(status=401, mimetype="application/json")


    def requires_auth(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = request.authorization
            if not auth or not check_auth(auth.username, auth.password):
                return authenticate()
            return f(*args, **kwargs)
        return decorated


    def api_error(error_msg):
        return Response(json.dumps({
            "error": True,
            "error_msg": error_msg
        }), status=400, mimetype="application/json")


    def api_success(success_obj=None):
        if not success_obj:
            success_obj = {}
        success_obj["error"] = False
        return Response(json.dumps(success_obj), status=200, mimetype="application/json")


    @app.route("/")
    def index():
        return "<html><head><title>Flock gateway</title></head><body><p style='font-size: 20em; text-align: center;'>flock</p></body></html>"

    @app.route("/es-test")
    def es_test():
        r = Search(index="user").query("match", username="user1").execute()
        return str(r.hits)


    @app.route("/register", methods=["POST"])
    def register():
        username = request.form.get('username')

        if not username:
            return api_error("You must provide a username")

        # Validate username
        valid_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01234567890_-'
        for c in username:
            if c not in valid_chars:
                return api_error("Usernames must only contain letters, numbers, '-', or '_'")

        # Is the user already registered?
        r = Search(index="user").query("match", username=username).execute()
        if len(r) != 0:
            return api_error("That username is already registered")

        # Add user, and force a refresh of the index
        user = User(username=username, token=secrets.token_hex(16))
        user.save()
        Index('user').refresh()

        return api_success( {"auth_token": user.token })


    @app.route("/submit", methods=["POST"])
    @requires_auth
    def submit():
        # Validate that the data is JSON
        try:
            obj = json.loads(request.data)
        except:
            return api_error("Invalid JSON object")

        # Validate that host_uuid is the username
        if ('host_uuid' not in obj) or (request.authorization['username'] != obj['host_uuid']):
            return api_error("Data does not contain the corrent host_uuid")

        # TODO: push data into ElasticSearch

        return api_success()

    return app
