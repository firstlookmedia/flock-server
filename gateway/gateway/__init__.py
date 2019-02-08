import os
import json
from functools import wraps
from flask import Flask, request, Response
from elasticsearch import Elasticsearch

from .tokens import Tokens


def create_app(test_config=None):
    # Flask
    app = Flask(__name__)
    if test_config is None:
        app.config.update({'TOKENS_PATH': '/data/tokens.json'})
    else:
        app.config.update(test_config)

    # Load tokens
    tokens = Tokens(app.config['TOKENS_PATH'])

    # Connect to ElasticSearch
    es = Elasticsearch(['elasticsearch:9200'])

    def check_auth(username, password):
        return tokens.exists(username) and password == tokens.get(username)


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
        return "<html><head><title>Flock gateway</title></head><body><p style='font-size: 20em; text-align: center;'>🦉</p></body></html>"


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

        if tokens.exists(username):
            return api_error("That username is already registered")

        token = tokens.generate(username)
        return api_success( {"auth_token": token })


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
