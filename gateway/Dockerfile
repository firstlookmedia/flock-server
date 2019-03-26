# python:3.7.2-stretch (on 2019-01-30)
FROM python@sha256:8bfb2d646119faeb1892ddf9668eeb08a8938626f64b91100a31a8dea46ec67d

# Copy code
WORKDIR /app
COPY . /app

# Install python dependencies
RUN pip install pipenv
RUN pipenv install --dev

EXPOSE 5000

ENV FLASK_APP gateway

CMD ["pipenv", "run", "python", "-u", "app.py"]
