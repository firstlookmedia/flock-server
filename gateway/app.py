import json
from flask import Flask, request, Response

from tokens import Tokens

# Keep track of all tokens
tokens = Tokens()

# The flask app
app = Flask(__name__)


def api_error(error_msg):
    return Response(json.dumps({
        "error": True,
        "error_msg": error_msg
    }), status=400, mimetype="application/json")


def api_success(success_obj):
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
def submit():
    return api_error("Not implemented yet")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
