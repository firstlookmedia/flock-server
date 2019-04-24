import time
import requests

from flock_server import User, create_app, elasticsearch_url


if __name__ == '__main__':
    # Wait for ElasticSearch to start
    print('Waiting for ElasticSearch')
    while True:
        try:
            r = requests.get(elasticsearch_url, verify='/usr/share/ca-certificates/ca.crt')
            print('{} is ready'.format(elasticsearch_url))
            break

        except:
            print('{} not ready, waiting ...'.format(elasticsearch_url))
            time.sleep(5)

    # Initialize models
    print('Initializing user model')
    User.init()

    # Start web service
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
