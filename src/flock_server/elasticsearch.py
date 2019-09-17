import os
from datetime import datetime

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError
from elasticsearch_dsl import connections, Date, Document, Index, Text, Boolean


# Configure ElasticSearch default connection
if 'ELASTIC_CA_CERT' in os.environ:
    ca_cert_path = os.environ['ELASTIC_CA_CERT']
else:
    ca_cert_path = None
if 'ELASTICSEARCH_HOSTS' in os.environ:
    elasticsearch_url = os.environ['ELASTICSEARCH_HOSTS']
else:
    elasticsearch_url = 'https://elasticsearch:9200'

# Connect using both high-level and low-level elasticsearch clients
if elasticsearch_url.startswith('https://'):
    if 'ELASTIC_PASSWORD' in os.environ:
        http_auth = ('elastic', os.environ['ELASTIC_PASSWORD'])
    else:
        http_auth = None

    connections.create_connection(
        hosts=[elasticsearch_url], timeout=20,
        use_ssl=True, verify_certs=True, ca_certs=ca_cert_path,
        http_auth=http_auth
    )
    es = Elasticsearch(
        hosts=[elasticsearch_url], timeout=20,
        use_ssl=True, verify_certs=True, ca_certs=ca_cert_path,
        http_auth=http_auth
    )
else:
    connections.create_connection(hosts=[elasticsearch_url], timeout=20)
    es = Elasticsearch([elasticsearch_url], timeout=20)


class User(Document):
    username = Text()
    name = Text()
    token = Text()
    created_at = Date()

    class Index:
        name = 'user'

    def save(self, ** kwargs):
        self.created_at = datetime.now()
        return super(User, self).save(** kwargs)


class Setting(Document):
    key = Text()
    value = Text()

    class Index:
        name = 'setting'


class KeybaseNotification(Document):
    notification_type = Text()
    details = Text()
    delivered = Boolean()
    created_at = Date()

    class Index:
        name = 'keybase_notification'
