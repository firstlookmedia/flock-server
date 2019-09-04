import time
import requests
import os
import asyncio

from flock_server import User, create_app, elasticsearch_url


if __name__ == '__main__':
    # Wait for ElasticSearch to start
    print('Waiting for ElasticSearch')
    while True:
        try:
            if 'ELASTIC_CA_CERT' in os.environ:
                ca_cert_path = os.environ['ELASTIC_CA_CERT']
            else:
                ca_cert_path = None

            r = requests.get(elasticsearch_url, verify=ca_cert_path)
            print('{} is ready'.format(elasticsearch_url))
            break

        except:
            print('{} not ready, waiting ...'.format(elasticsearch_url))
            time.sleep(5)

    # Initialize models
    print('Initializing user model')
    User.init()

    if os.environ.get('FLOCK_KEYBASE') == "1":
        print("KEYBASE MODE")

    else:
        # Start web service
        app = create_app()
        app.run(host='0.0.0.0', port=5000, debug=True)
