import traceback
import socket
from stem.control import Controller
from flask import Flask

from common import Common
from config import Config
from onion import Onion


# Create a common object
common = Common()

# Load the config
config = Config(common)

# Create the onion object
onion = Onion(common, config)


app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"


@app.route("/tor")
def tor():
    try:
        # Make a DNS query to learn tor's IP, because stem doesn't work with hostnames
        tor_ip = socket.gethostbyname('tor')

        # Connect to the tor controller
        controller = Controller.from_port(tor_ip, 9051)
        controller.authenticate()

        return "connected";

    except:
        return "failed to connect: <pre>{}</pre>".format(traceback.format_exc())


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
