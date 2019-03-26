import time
import requests

from gateway import User, create_app, elasticsearch_url


if __name__ == '__main__':
    # Wait for ElasticSearch to start
    print('Waiting for ElasticSearch')
    while True:
        try:
            r = requests.get(elasticsearch_url)
            print('{} is ready'.format(elasticsearch_url))
            break

        except:
            print('{} not ready, waiting ...'.format(elasticsearch_url))
            time.sleep(5)

    # Initialize models
    try:
        print('Initializing user model')
        User.init()
    except:
        pass

    # Start web service
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
