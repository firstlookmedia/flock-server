# Flock

Flock is a privacy-preserving fleet management system powered by osquery, the Elastic Stack, and Tor onion services.

## Getting started

You need **Docker** and **Docker Compose**. To start all the containers:

```sh
docker-compose up
```

You can visit http://127.0.0.1:5000/ to view the admin web app.

You can visit http://127.0.0.1:5601/ to see Kibana.


## Development notes

**Adding python dependencies to admin**

We should improve this in the future, but for now you need python 3 on your computer, and you need to install pipenv:

```
pip3 install pipenv
```

Then, you can modify the `Pipfile` and `Pipfile.lock` files using pipenv, like:

```
pipenv install requests
```
