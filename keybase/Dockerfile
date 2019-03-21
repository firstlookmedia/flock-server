# node:11-stretch (on 2019-03-21)
FROM node@sha256:5f8540d908ecbf82538cb9f02152bd0650d59f6b58072bb70e8a2072906915b5

# Copy code
WORKDIR /app
COPY . /app

# Install keybase
RUN curl --remote-name https://prerelease.keybase.io/keybase_amd64.deb && \
    sudo dpkg -i keybase_amd64.deb && \
    sudo apt-get install -f && \
    rm keybase_amd64.deb

ENV ELASTICSEARCH_HOST elasticsearch

CMD ["node", "bot.js"]
