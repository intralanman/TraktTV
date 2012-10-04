import supybot.utils as utils
from supybot.commands import *
import supybot.conf as conf
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.world as world
import supybot.conf as conf
import supybot.plugins as plugins

class TraktTVDB(plugins.ChannelUserDB):
    """Holds the TraktTV IDs of all known nicks

    (This database is case insensitive and channel independent)
    """

    def __init__(self, *args, **kwargs):
        plugins.ChannelUserDB.__init__(self, *args, **kwargs)

    def serialize(self, v):

        return list(v)

    def deserialize(self, channel, id, L):
        (id,) = L
        return (id,)

    def set(self, nick, id):
        """ 
        if nick.lower() == id.lower():
            del self['x', nick.lower()] # FIXME: Bug in supybot(?)
        else:"""
        self['x', nick.lower()] = (id,)

    def setKey(self, key):
        self['system', 'apiKey'] = (key,)

    def getKey(self):
        try:
            return self['system', 'apiKey'][0]
        except:
            return

    def getId(self, nick):
        try:
            return self['x', nick.lower()][0]
        except:
            return # entry does not exist

filename = conf.supybot.directories.data.dirize("TraktTV.db")

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
