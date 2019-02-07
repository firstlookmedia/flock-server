# Flock

Flock is a privacy-preserving fleet management system powered by osquery and the Elastic Stack.

**The goal of Flock is to gain visibility into a fleet of laptops while protecting the privacy of the laptop users. It achieves this by only collecting information needed to inform security decisions, and by not allow the IT team to access arbitrary files, or execute arbitrary code, on the laptops they are monitoring.**

See also the [Flock Agent](https://github.com/firstlookmedia/flock-agent).

## About the Flock server

The Flock server includes several components, running in containers, which will make them easy to deploy in cloud hosting services or on physical hardware. They include:

**elasticsearch:** This container holds osquery data for the entire fleet.

**kibana:** This container runs Kibana, which visualizes the data from ElasticSearch, with custom dashboards showing whatever information we feel is most useful. For example, we can make pie charts of OS patch levels, and see which users have obscure or sketchy Chrome extensions, and which users have insecure configurations, like aren’t using FileVault or have their firewall disabled.

**gateway:** This container hosts a web service used as a gateway between endpoints and ElasticSearch. Endpoints can _register_ themselves and get assigned an authentication token, and they can _submit_ logs, authenticating using that token. It's write-only; they can't read anything from ElasticSearch.

**keybase:** This container runs a Keybase bot, for real-time security alerts. The bot can be a member of a Keybase team, and post alerts to the team.

## Getting started

You need **Docker** and **Docker Compose**. To start all the containers:

```sh
docker-compose up
```

## Developer notes

### Gateway API

#### Register to receive an authentication token

Example request:

```
$ curl https://flock-gateway/register --data "username=insert_unique_uuid_here"
```

Example response:

```
{
  "error": false,
  "auth_token": "d7fda212e0a1d309131e874523037031"
}
```

#### Send logs to the gateway

Example request:

```
$ curl https://flock-gateway/submit -H "Authentication: Basic insert_unique_uuid_here:ZDdmZGEyMTJlMGExZDMwOTEzMWU4NzQ1MjMwMzcwMzE="
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
