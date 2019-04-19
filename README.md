# Flock

_**⚠️ This software is under development. It's not ready to be used in production.**_

Flock is a privacy-preserving fleet management system. The goal of Flock is to gain visibility into a fleet of laptops while protecting the privacy of the laptop users. It achieves this by only collecting information needed to inform security decisions, and by not allowing the IT team to access arbitrary files or execute arbitrary code on the laptops they are monitoring.

See also [Flock Agent](https://github.com/firstlookmedia/flock-agent), the macOS agent that runs on endpoints, collects data, and shares it with the server.

## About the Flock server

The purpose of Flock server is to accept data from all of the agents (collected by osquery) and save it in an Elasticsearch database. Agents register themselves with the server and get assigned an authentication token, then they use these credentials to submit logs from osquery, which get saved to the database. Agents have write-only access; they cannot read anything from the database.

How you configure Elasticsearch and Kibana (for data visualizations) are outside the scope of this project. However we do provide a pre-built Kibana dashboard ([coming soon](https://github.com/firstlookmedia/flock/issues/1)) for visualizations we find useful.

The server also includes a [Keybase](https://keybase.io/) bot ([coming soon](https://github.com/firstlookmedia/flock/issues/2)) to send encrypted notifications to a Keybase team, and security staff send messages to the bot in order to administer the server.

## Developer notes

### Test status

[![CircleCI](https://circleci.com/gh/firstlookmedia/flock/tree/master.svg?style=svg)](https://circleci.com/gh/firstlookmedia/flock/tree/master)

### Running a local server

To run a local server, you need Docker Compose.

First you must generate the certificates. (This command generates keys and certificates in `data/certs/certs`. If you want to regenerate them, delete that folder and run the command again.)

```sh
docker-compose -f create-certs.yml up
```

Then start all containers.

```sh
docker-compose up
```

The server web interface will be at http://127.0.0.1:5000, and Kibana will be https://127.0.0.1:5601 (with a self-signed cert).

### Running tests

Here's how to run server tests:

```
cd src
./run_tests.sh
```

### Modifying pip dependencies

To edit pip dependencies in the gateway container, start a new container and then run `pipenv` commands, like `pipenv install requests`. You can start the container with pipenv like:

```
cd src
./pipenv_shell.sh
```

### Server API

#### POST /register

Register to receive an authentication token.

Example request:

```
curl --data "username=insert_endpoint_uuid_here" \
     http://127.0.0.1:5000/register
```

Example response:

```
{
  "auth_token": "3b0be5105ad4fd89efc3f2420f6074f3",
  "error": false
}
```

#### GET /ping

Make sure credentials exist on server. (Note that the authorization header is base64-encoded `insert_endpoint_uuid_here:3b0be5105ad4fd89efc3f2420f6074f3`.)

Example request:

```
curl -H "Authorization: Basic aW5zZXJ0X2VuZHBvaW50X3V1aWRfaGVyZTozYjBiZTUxMDVhZDRmZDg5ZWZjM2YyNDIwZjYwNzRmMw==" \
     http://127.0.0.1:5000/ping
```

Example response:

```
{
  "error": false
}
```

#### POST /submit

Send logs to the server.

Example request:

```
curl -H "Authorization: Basic aW5zZXJ0X2VuZHBvaW50X3V1aWRfaGVyZTozYjBiZTUxMDVhZDRmZDg5ZWZjM2YyNDIwZjYwNzRmMw==" \
     -H "Content-Type: application/json" \
     --data '[{"host_uuid": "insert_endpoint_uuid_here", "other_arbitrary_data": "goes here"}]' \
     http://127.0.0.1:5000/submit
```

Example response:

```
{
  "error": false
}
```
