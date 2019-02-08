import os
import json
from functools import wraps
from flask import Flask, request, Response
from elasticsearch import Elasticsearch

from .tokens import Tokens


# Load tokens
tokens = Tokens()

# Connect to ElasticSearch
es = Elasticsearch(['elasticsearch:9200'])


def create_app():
    # Flask
    app = Flask(__name__)


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
