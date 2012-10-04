
import supybot.utils as utils
from supybot.commands import *
import supybot.conf as conf
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.ircdb as ircdb
import supybot.callbacks as callbacks
import supybot.world as world
import supybot.log as log

import simplejson
import urllib2

from TraktTVDB import *

class TraktTV(callbacks.PluginRegexp):

    APIURL = "http://api.trakt.tv"
    APIKEY = ""

    def __init__(self, irc):
        self.__parent = super(TraktTV, self)
        self.__parent.__init__(irc)
        self.db = TraktTVDB(dbfilename)
        world.flushers.append(self.db.flush)
        APIKEY = self.db.getKey()

    def die(self):
        if self.db.flush in world.flushers:
            world.flushers.remove(self.db.flush)
        self.db.close()
        self.__parent.die()

    def setUserId(self, irc, msg, args, newId):
        """<id>

        Sets the TraktTV ID for the caller and saves it in a database.
        """

        self.db.set(msg.nick, newId)

        irc.reply("TraktTV ID changed.")
        #self.profile(irc, msg, args)

    set = wrap(setUserId, ["something"])

    def apikey(self, irc, msg, args, key):
        """ set the trakt.tv API key """

        try:
            caller = ircdb.users.getUser(msg.prefix)
            isOwner = caller._checkCapability('owner')
        except KeyError:
            caller = None
            isOwner = False
            irc.error("you must be an owner to use this command")
            return False

        if isOwner:
            print "key: %s" %(key)
            self.db.setKey(key)
            self.APIKEY = key
            irc.reply("key set")
        else:
            irc.error("you must be an owner to use this command")
            return False

    apikey = wrap(apikey, [optional("something")])

    def keyCheck(self, irc):
        if len(self.APIKEY) < 1:
            irc.reply("you can't use this command until you've set an API key")
            return False
        else:
            return True

    def trendingMovies(self, irc, msg, args, wtf):
        """Get a list of movies trending right now"""

        if not self.keyCheck(irc):
            return False

        url = "%s/movies/trending.json/%s" % (self.APIURL, self.APIKEY)

        try:
           f = urllib2.urlopen(url)
        except urllib2.HTTPError, e:
            irc.error("Error: %s" % (e.code))
            print e.read()
            return

        data = simplejson.load(f)

        movies = 0
        for movie in data:
            movies += 1

            people = "people"
            if movie["watchers"] == 1:
                people = "person";

            are = "are"
            if movie["watchers"] == 1:
                are = "is"

            irc.reply(("%d %s %s now watching: %s (%d) | %s | %d%% | Trailer: %s" % ( movie["watchers"], people, are, movie["title"], movie["year"], movie["url"], movie["ratings"]["percentage"], movie["trailer"] )))
            if movies >= 5:
                break
        
    tm = wrap(trendingMovies, [optional("something")])

    def trendingShows(self, irc, msg, args, wtf):
        """Get a list of shows trending right now"""

        if not self.keyCheck(irc):
            return False

        url = "%s/shows/trending.json/%s" % (self.APIURL, self.APIKEY)

        try:
           f = urllib2.urlopen(url)
        except urllib2.HTTPError, e:
            irc.error("Error: %s" % (e.code))
            print e.read()
            return

        data = simplejson.load(f)

        shows = 0
        for show in data:
            shows += 1

            people = "people"
            if show["watchers"] == 1:
                people = "person";

            are = "are"
            if show["watchers"] == 1:
                are = "is"

            irc.reply(("%d %s %s now watching: %s (%d) | %s | Rating: %d%%" % ( show["watchers"], people, are, show["title"], show["year"], show["url"], show["ratings"]["percentage"] )))
            if shows >= 5:
                break

    ts = wrap(trendingShows, [optional("something")])

    def episodeSummary(self, irc, msg, args, tvdbID, season, episode):
        """Get a summary for an episode of a show"""

        url = "%s/show/episode/summary.json/%s/%s/%s/%s" % (self.APIURL, self.APIKEY, tvdbID, season, episode)

        try:
           f = urllib2.urlopen(url)
        except urllib2.HTTPError, e:
            if e.code == 404:
               irc.error("Episode not found.")
            else:
               irc.error("Error: %s" % (e.code))
            print e.read()
            return

        data = simplejson.load(f)
        return data

    def movieSummary(self, irc, msg, args, imdbID):
        """Get a summary for a movie"""

        url = "%s/movie/summary.json/%s/%s" % (self.APIURL, self.APIKEY, imdbID)

        try:
           f = urllib2.urlopen(url)
        except urllib2.HTTPError, e:
            if e.code == 404:
               irc.error("Movie not found.")
            else:
               irc.error("Error: %s" % (e.code))
            print e.read()
            return

        data = simplejson.load(f)
        return data

    def nw(self, irc, msg, args, optionalId):
        """Show what a user is currently watching"""

        if not self.keyCheck(irc):
            return False

        id = (optionalId or self.db.getId(msg.nick) or msg.nick)

	url = "%s/user/watching.json/%s/%s" % (self.APIURL, self.APIKEY, id)

        try:
            f = urllib2.urlopen(url)
        except urllib2.HTTPError, e:
	    if e.code == 404:
	       irc.error("Unknown user (%s).  Please set using the 'set' command." % (id))
	    else:
               irc.error("Error: %s" % (e.code))
	    print e.read()
            return

	data = simplejson.load(f)
        if data:
            if data["type"] == "movie":
                certification = data["movie"]["certification"]
                if certification == "":
                    certification = "Unknown"
                movieSummary = self.movieSummary(self, irc, msg, data["movie"]["imdb_id"])
                if movieSummary:
                    moviePercentage = movieSummary["ratings"]["percentage"]
                    irc.reply(("You are now watching: %s (%s) | %s | %s%% | %s" % (data["movie"]["title"], data["movie"]["year"], certification, moviePercentage, data["movie"]["url"])).encode("utf-8"))
                else:
                    irc.reply(("You are now watching: %s (%s) | %s | %s" % (data["movie"]["title"], data["movie"]["year"], certification, data["movie"]["url"])).encode("utf-8"))

            elif data["type"] == "episode":
                episodeSummary = self.episodeSummary(self, irc, msg, data["show"]["tvdb_id"], data["episode"]["season"], data["episode"]["number"])
                if episodeSummary:                                                                                                                                                                                                                  
                    showPercentage = episodeSummary["show"]["ratings"]["percentage"]
                    showVotes = episodeSummary["show"]["ratings"]["votes"]
                    showLoved = episodeSummary["show"]["ratings"]["loved"]
                    showHated  = episodeSummary["show"]["ratings"]["hated"]
                    epPercentage = episodeSummary["episode"]["ratings"]["percentage"]
                    epVotes = episodeSummary["episode"]["ratings"]["votes"]
                    epLoved = episodeSummary["episode"]["ratings"]["loved"]
                    epHated  = episodeSummary["episode"]["ratings"]["hated"]
                    irc.reply(("You are now watching: %s (%s) - %sx%s - %s | %s%%/%s%% | %s" % \
			(data["show"]["title"], data["show"]["year"], data["episode"]["season"], data["episode"]["number"], data["episode"]["title"], showPercentage, epPercentage, data["episode"]["url"])).encode("utf-8"))
                else:
                    irc.reply(("You are now watching: %s (%s) - %sx%s - %s | %s" % \
			(data["show"]["title"], data["show"]["year"], data["episode"]["season"], data["episode"]["number"], data["episode"]["title"], data["episode"]["url"])).encode("utf-8"))
	else:
	    irc.reply("You are not currently watching anything.")
        
    nw = wrap(nw, [optional("something")])


dbfilename = conf.supybot.directories.data.dirize("TraktTV.db")

Class = TraktTV
