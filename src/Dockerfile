# python:3.7.2-stretch (on 2019-03-26)
FROM python@sha256:6ff53856b07aa04bce29829338aab09da2f7d240de4046c7d3d1cd239a4fba5a

# Copy code
WORKDIR /app
COPY . /app

# Install python dependencies
RUN pip install pipenv
RUN pipenv install --dev

EXPOSE 5000

ENV FLASK_APP gateway

CMD ["pipenv", "run", "python", "-u", "app.py"]
