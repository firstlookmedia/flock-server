import os
from datetime import datetime

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError
from elasticsearch_dsl import connections, Date, Document, Index, Text


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
        elastic_password = os.environ['ELASTIC_PASSWORD']
    else:
        elastic_password = ''

    connections.create_connection(
        hosts=[elasticsearch_url], timeout=20,
        use_ssl=True, verify_certs=True, ca_certs=ca_cert_path,
        http_auth=('elastic', elastic_password)
    )
    es = Elasticsearch(
        hosts=[elasticsearch_url], timeout=20,
        use_ssl=True, verify_certs=True, ca_certs=ca_cert_path,
        http_auth=('elastic', elastic_password)
    )
else:
    connections.create_connection(hosts=[elasticsearch_url], timeout=20)
    es = Elasticsearch([elasticsearch_url], timeout=20)


class User(Document):
    username = Text()
    token = Text()
    created_at = Date()

    class Index:
        name = 'user'

    def save(self, ** kwargs):
        self.created_at = datetime.now()
        return super(User, self).save(** kwargs)
