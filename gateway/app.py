import time
import requests

from elasticsearch_dsl import Index

from gateway import User, create_app, elasticsearch_host


if __name__ == '__main__':
    # Wait for ElasticSearch to start
    print('Waiting for ElasticSearch')
    elasticsearch_url = 'http://{}/'.format(elasticsearch_host)
    while True:
        try:
            r = requests.get(elasticsearch_url)
            print('{} is ready'.format(elasticsearch_url))
            break
            
        except:
            print('{} not ready, waiting ...'.format(elasticsearch_url))
            time.sleep(5)

    # Initialize models
    if not Index('user').exists():
        print('Initializing user model')
        User.init()

    # Start web service
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
