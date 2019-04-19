# Flock Gateway

_**⚠️ This software is under development. It's not ready to be used in production.**_

Flock is a privacy-preserving fleet management system powered by osquery and the Elastic Stack.

The goal of Flock is to gain visibility into a fleet of laptops while protecting the privacy of the laptop users. It achieves this by only collecting information needed to inform security decisions, and by not allow the IT team to access arbitrary files, or execute arbitrary code, on the laptops they are monitoring.

This is the gateway component. You must run it in conjunction with other components. Check out the [Flock repo](https://github.com/firstlookmedia/flock) for information on running it with Docker Compose.

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
