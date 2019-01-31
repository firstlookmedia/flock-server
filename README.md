# Flock

Flock is a privacy-preserving fleet management system powered by osquery, the Elastic Stack, and Tor onion services.

**Dependencies:**

- Docker
- Docker Compose

**Adding python dependencies to admin**

We should improve this in the future, but for now you need python 3 on your computer, and you need to install pipenv:

```
pip3 install pipenv
```

Then, you can modify the `Pipfile` and `Pipfile.lock` files using pipenv, like:

```
pipenv install requests
```
