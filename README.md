# Flock

_**⚠️ This software is under development. It's not ready to be used in production.**_

Flock is a privacy-preserving fleet management system powered by osquery and the Elastic Stack.

The goal of Flock is to gain visibility into a fleet of laptops while protecting the privacy of the laptop users. It achieves this by only collecting information needed to inform security decisions, and by not allow the IT team to access arbitrary files, or execute arbitrary code, on the laptops they are monitoring.

See also:

- [Flock Agent](https://github.com/firstlookmedia/flock-agent), the macOS agent that runs on endpoints, collects data, and shares it with the gateway.
- [Flock Gateway](https://github.com/firstlookmedia/flock-gateway), the API that agents submit logs to, and stashes them in ElasticSearch.

## About the Flock server

The Flock server includes several components that run in different containers. These include:

**elasticsearch:** This container holds osquery data for the entire fleet.

**kibana:** This container runs Kibana, which visualizes the data from ElasticSearch, with custom dashboards showing whatever information we feel is most useful. For example, we can make pie charts of OS patch levels, and see which users have obscure or sketchy Chrome extensions, and which users have insecure configurations, like aren’t using FileVault or have their firewall disabled.

**gateway:** This container hosts a web service used as a gateway between endpoints and ElasticSearch. Endpoints can _register_ themselves and get assigned an authentication token, and they can _submit_ logs, authenticating using that token. It's write-only; they can't read anything from ElasticSearch.

## Getting started

You need **Docker** and **Docker Compose**.

Docker Compose expects `../flock-gateway` to exist. Make sure to clone the [Flock Gateway](https://github.com/firstlookmedia/flock-gateway) git repo into the parent directory before proceeding.

First you must generate the certificates. (This command generates keys and certificates in `data/certs/certs`. If you want to regenerate them, delete that folder and run the command again.)

```sh
docker-compose -f create-certs.yml up
```

Then start all containers.

```sh
docker-compose up
```

The gateway web interface will be at http://127.0.0.1:5000, and Kibana will be https://127.0.0.1:5601 (with a self-signed cert).
