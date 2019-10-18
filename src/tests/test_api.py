import json
import base64


def test_index_is_404(client):
    assert client.get("/").status_code == 404


def test_register_without_username(client):
    res = client.post("/register", data={})
    assert res.status_code == 400


def test_register_invalid_username(client):
    res = client.post("/register", data={"username": "usernames can't have spaces"})
    assert res.status_code == 400

    res = client.post(
        "/register", data={"username": "they_can't_have_apostrophers_EITHER"}
    )
    assert res.status_code == 400

    res = client.post(
        "/register", data={"username": "but_they_can-have-dashes_and-underscores"}
    )
    assert res.status_code == 200


def test_register_cannot_register_existing_username(client):
    res = client.post("/register", data={"username": "UUID1"})
    assert res.status_code == 200

    res = client.post("/register", data={"username": "UUID1"})
    assert res.status_code == 400


def test_register_with_name(client):
    res = client.post("/register", data={"username": "UUID1", "name": "Nick Fury"})
    assert res.status_code == 200


def test_ping_invalid_auth(client):
    res = client.get("/ping")
    assert res.status_code == 401


def test_ping_valid_auth(client):
    username = "UUID1"

    res = client.post("/register", data={"username": username})
    assert res.status_code == 200

    auth_token = json.loads(res.data)["auth_token"]

    # Create authorization header
    encoded_credentials = base64.b64encode(
        "{}:{}".format(username, auth_token).encode()
    ).decode()

    res = client.get(
        "/ping", headers={"Authorization": "Basic {}".format(encoded_credentials)}
    )
    assert res.status_code == 200


def test_submit_invalid_auth(client):
    res = client.post("/submit", data="[{}]")
    assert res.status_code == 401


def test_submit_valid_auth(client):
    username = "UUID1"

    res = client.post("/register", data={"username": username})
    assert res.status_code == 200

    auth_token = json.loads(res.data)["auth_token"]

    # Create authorization header
    encoded_credentials = base64.b64encode(
        "{}:{}".format(username, auth_token).encode()
    ).decode()

    res = client.post(
        "/submit",
        data=json.dumps([{"hostIdentifier": username}]),
        headers={"Authorization": "Basic {}".format(encoded_credentials)},
    )
    assert res.status_code == 200


def test_submit_valid_auth_with_invalid_host_identifier(client):
    username = "UUID42"
    res = client.post("/register", data={"username": username})
    auth_token = json.loads(res.data)["auth_token"]
    encoded_credentials = base64.b64encode(
        "{}:{}".format(username, auth_token).encode()
    ).decode()

    res = client.post(
        "/submit",
        data=json.dumps([{}]),
        headers={"Authorization": "Basic {}".format(encoded_credentials)},
    )
    assert res.status_code == 400

    res = client.post(
        "/submit",
        data=json.dumps([{"hostIdentifier": "something_wrong"}]),
        headers={"Authorization": "Basic {}".format(encoded_credentials)},
    )
    assert res.status_code == 400


def test_submit_list(client):
    username = "UUID4444"

    res = client.post("/register", data={"username": username})
    assert res.status_code == 200

    auth_token = json.loads(res.data)["auth_token"]
    encoded_credentials = base64.b64encode(
        "{}:{}".format(username, auth_token).encode()
    ).decode()

    def submit(data):
        res = client.post(
            "/submit",
            data=json.dumps(data),
            headers={"Authorization": "Basic {}".format(encoded_credentials)},
        )
        return res

    # Submit a log object, not a list of log objects
    res = submit({"hostIdentifier": username})
    assert res.status_code == 400

    # Submit 1 log object
    res = submit([{"hostIdentifier": username}])
    assert res.status_code == 200
    assert json.loads(res.data)["processed_count"] == 1

    # Submit 3 log objects, one of them invalid
    res = submit(
        [
            {"hostIdentifier": username},
            {"hostIdentifier": "invalid_username"},
            {"hostIdentifier": username},
        ]
    )
    assert res.status_code == 400

    # Submit 3 log objects
    res = submit(
        [
            {"hostIdentifier": username},
            {"hostIdentifier": username},
            {"hostIdentifier": username},
        ]
    )
    assert res.status_code == 200
    assert json.loads(res.data)["processed_count"] == 3
