# debian:stretch-slim (on 2019-01-30)
FROM debian@sha256:15ff3a968745e30585ddd28bb9707139d91a215ba3d2730e9036dba513c5dc77

# Install apt dependencies
RUN apt-get update && apt-get install -y gnupg apt-transport-https socat

# Copy code
WORKDIR /app
COPY . /app

# Fetch tor repo key
#RUN mkdir ~/.gnupg && \
#  chmod 700 ~/.gnupg && \
#  echo "disable-ipv6" >> ~/.gnupg/dirmngr.conf
#
#RUN gpg --batch --recv A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89
#RUN gpg --export A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89 | apt-key add -

# Actually import it locally, to avoid keyserver headaches
RUN cat torproject.asc | apt-key add -

# Add Tor repo, and install Tor
RUN echo "deb https://deb.torproject.org/torproject.org stretch main" >> /etc/apt/sources.list
RUN apt-get update && apt-get install -y tor deb.torproject.org-keyring

EXPOSE 9051

CMD ["sh", "start.sh"]
