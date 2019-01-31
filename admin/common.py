class Common(object):
    """
    Common functionality between all modules goes here.
    """
    def __init__(self):
        self.log('Common.__init__', 'init')

    def log(self, src, message):
        print("💬 {} | {}".format(src, message))
