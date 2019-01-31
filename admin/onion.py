from stem.control import Controller


class Onion(object):
    """
    All of the Tor-related logic goes here.
    """
    def __init__(self, common, config):
        self.c = common
        self.config = config

        self.c.log('Onion.__init__', 'init')
