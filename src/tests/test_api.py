import json
import base64


def get_auth_header(client, username="UUID1"):
    res = client.post("/register", json={"username": username})

    auth_token = json.loads(res.data)["auth_token"]

    # Create authorization header
    encoded_credentials = base64.b64encode(f"{username}:{auth_token}".encode()).decode()
    return {"Authorization": f"Basic {encoded_credentials}"}


def test_index_is_404(client):
    assert client.get("/").status_code == 404


def test_register_with_bad_json(client):
    res = client.post(
        "/register", headers={"Content-Type": "application/json"}, data="not json"
    )
    assert res.status_code == 400


def test_register_without_username(client):
    res = client.post("/register", json={})
    assert res.status_code == 400


def test_register_invalid_username(client):
    res = client.post("/register", json={"username": "usernames can't have spaces"})
    assert res.status_code == 400

    res = client.post(
        "/register", json={"username": "they_can't_have_apostrophers_EITHER"}
    )
    assert res.status_code == 400

    res = client.post(
        "/register", json={"username": "but_they_can-have-dashes_and-underscores"}
    )
    assert res.status_code == 200


def test_register_cannot_register_existing_username(client):
    res = client.post("/register", json={"username": "UUID1"})
    assert res.status_code == 200

    res = client.post("/register", json={"username": "UUID1"})
    assert res.status_code == 400


def test_register_with_name(client):
    res = client.post("/register", json={"username": "UUID1", "name": "Nick Fury"})
    assert res.status_code == 200


def test_ping_invalid_auth(client):
    res = client.get("/ping")
    assert res.status_code == 401


def test_ping_valid_auth(client):
    res = client.get("/ping", headers=get_auth_header(client))
    assert res.status_code == 200


def test_submit_no_auth(client):
    res = client.post("/submit", json={})
    assert res.status_code == 401


def test_submit_invalid_auth(client):
    username = "UUID1"
    # Create authorization header
    encoded_credentials = base64.b64encode(f"{username}:bad_pass:".encode()).decode()
    res = client.post(
        "/submit",
        json=[{"hostIdentifier": username}],
        headers={"Authorization": f"Basic notanauthstring"},
    )
    assert res.status_code == 401


def test_submit_with_bad_json(client):
    res = client.post(
        "/submit",
        data="not json",
        headers={"Content-Type": "not json", **get_auth_header(client)},
    )
    assert res.status_code == 400


def test_submit_valid_auth(client):
    username = "UUID1"
    res = client.post(
        "/submit",
        json=[{"hostIdentifier": username}],
        headers=get_auth_header(client, username),
    )
    assert res.status_code == 200


def test_submit_valid_auth_with_invalid_host_identifier(client):
    auth_header = get_auth_header(client)
    res = client.post("/submit", json=[{}], headers=auth_header,)
    assert res.status_code == 400

    res = client.post(
        "/submit", json=[{"hostIdentifier": "something_wrong"}], headers=auth_header,
    )
    assert res.status_code == 400


def test_submit_list(client):
    username = "UUID4444"
    auth_header = get_auth_header(client, username)

    def submit(data):
        res = client.post("/submit", json=data, headers=auth_header)
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
