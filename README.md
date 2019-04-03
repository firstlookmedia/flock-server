# Flock

_**⚠️ This software is under development. It's not ready to be used in production.**_

Flock is a privacy-preserving fleet management system powered by osquery and the Elastic Stack.

The goal of Flock is to gain visibility into a fleet of laptops while protecting the privacy of the laptop users. It achieves this by only collecting information needed to inform security decisions, and by not allow the IT team to access arbitrary files, or execute arbitrary code, on the laptops they are monitoring.

See also the [Flock Agent](https://github.com/firstlookmedia/flock-agent).

## About the Flock server

The Flock server includes several components, running in containers, which will make them easy to deploy in cloud hosting services or on physical hardware. They include:

**elasticsearch:** This container holds osquery data for the entire fleet.

**kibana:** This container runs Kibana, which visualizes the data from ElasticSearch, with custom dashboards showing whatever information we feel is most useful. For example, we can make pie charts of OS patch levels, and see which users have obscure or sketchy Chrome extensions, and which users have insecure configurations, like aren’t using FileVault or have their firewall disabled.

**gateway:** This container hosts a web service used as a gateway between endpoints and ElasticSearch. Endpoints can _register_ themselves and get assigned an authentication token, and they can _submit_ logs, authenticating using that token. It's write-only; they can't read anything from ElasticSearch.

## Getting started

You need **Docker** and **Docker Compose**.

First you must generate the certificates. (This command generates keys and certificates in `certificates/certs`. If you want to regenerate them, delete that folder and run the command again.)

```sh
docker-compose -f create-certs.yml up
```

Then start all containers.

```sh
docker-compose up
```

The gateway web interface will be at http://127.0.0.1:5000, and Kibana will be https://127.0.0.1:5601 (with a self-signed cert).

## To run tests

```
./run_tests.sh
```

## Developer notes

### Gateway API

#### Register to receive an authentication token

Example request:

```
curl -v \
       --data "username=insert_endpoint_uuid_here" \
       http://127.0.0.1:5000/register
```

Example response:

```
{
  "auth_token": "3b0be5105ad4fd89efc3f2420f6074f3",
  "error": false
}
```

#### Send logs to the gateway

Example request (note that the authorization header is base64-encoded `insert_endpoint_uuid_here:3b0be5105ad4fd89efc3f2420f6074f3`):

```
curl -v \
       -H "Authorization: Basic aW5zZXJ0X2VuZHBvaW50X3V1aWRfaGVyZTozYjBiZTUxMDVhZDRmZDg5ZWZjM2YyNDIwZjYwNzRmMw==" \
       -H "Content-Type: application/json" \
       --data '{"host_uuid": "insert_endpoint_uuid_here", "other_arbitrary_data": "goes here"}' \
       http://127.0.0.1:5000/submit
```

Example response:

```
{
  "error": false
}
```

### Modifying gateway pip dependencies

To edit pip dependencies in the gateway container, start a new container and then run `pipenv` commands, like `pipenv install requests`. You can start the container with pipenv like:

```
cd gateway
./pipenv_shell.sh
```
