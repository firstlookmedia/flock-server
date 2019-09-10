import json
import secrets
from datetime import datetime
from functools import wraps

from flask import Flask, request, Response
from elasticsearch_dsl import Index, Search

from .elasticsearch import es, User


def create_api_app(test_config=None):
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


    @app.route("/es-test")
    def es_test():
        r = Search(index="user").query("match", username="user1").execute()
        return str(r.hits)


    @app.route("/register", methods=["POST"])
    def register():
        username = request.form.get('username')
        name = request.form.get('name', '')

        if not username:
            return api_error("You must provide a username")

        # Validate username
        valid_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01234567890_-'
        for c in username:
            if c not in valid_chars:
                return api_error("Usernames must only contain letters, numbers, '-', or '_'")

        # Strip invalid characters from name
        new_name = ''
        invalid_chars = '`{}!@#$%^&*_'
        for c in name:
            if c not in invalid_chars:
                new_name += c
        name = new_name

        # Is the user already registered?
        r = Search(index="user").query("match", username=username).execute()
        if len(r) != 0:
            return api_error("Your computer ({}) is already registered with this server".format(username))

        # Add user, and force a refresh of the index
        user = User(username=username, name=name, token=secrets.token_hex(16))
        user.save()
        Index('user').refresh()

        return api_success( {"auth_token": user.token })


    @app.route("/ping")
    @requires_auth
    def info():
        # Ping the server, to make sure settings are configured correctly
        return api_success()


    @app.route("/submit", methods=["POST"])
    @requires_auth
    def submit():
        # Validate that the data is JSON
        try:
            docs = json.loads(request.data)
        except:
            return api_error("Invalid JSON object")

        if type(docs) != list:
            return api_error("Data is not an array")

        # Validate
        for i, doc in enumerate(docs):
            # Item should be an object
            if type(doc) != dict:
                return api_error("Item {} is not an object".format(i))

            # hostIdentifier should be the username
            if ('hostIdentifier' not in doc) or (request.authorization['username'] != doc['hostIdentifier']):
                return api_error("Item {} does not contain the correct hostIdentifier".format(i))

        # Add data to ElasticSearch
        for doc in docs:
            # Convert 'unixTime' to '@timestamp'
            if 'unixTime' in doc:
                doc['@timestamp'] = datetime.utcfromtimestamp(int(doc['unixTime'])).strftime('%Y-%m-%dT%H:%M:%S.000Z')

            # Add data
            index = 'flock-{}'.format(datetime.now().strftime('%Y-%m-%d'))
            es.index(index=index, doc_type='osquery', body=doc)

        return api_success({'processed_count': len(docs)})

    return app
