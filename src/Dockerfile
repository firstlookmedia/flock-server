FROM python:3.7.4-buster

# Copy code
WORKDIR /app
COPY . /app

# Install python dependencies
RUN pip install pipenv
RUN pipenv --python /usr/local/bin/python install --dev

EXPOSE 5000

ENV FLASK_APP flock_server

CMD ["pipenv", "run", "python", "-u", "app.py"]
