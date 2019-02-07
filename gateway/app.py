import json
from flask import Flask, request, Response


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

    return api_success({})


@app.route("/submit", methods=["POST"])
def register():
    return api_error("Not implemented yet")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
