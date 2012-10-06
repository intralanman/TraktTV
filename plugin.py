
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
import urllib
import socket

from TraktTVDB import *

class TraktTV(callbacks.PluginRegexp):

    socket.setdefaulttimeout(60)

    SITEURL = "http://trakt.tv"
    APIURL = "http://api.trakt.tv"

    def __init__(self, irc):
        self.__parent = super(TraktTV, self)
        self.__parent.__init__(irc)
        self.db = TraktTVDB(dbfilename)
        world.flushers.append(self.db.flush)
        self.APIKEY = self.registryValue("apikey")

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

    def keyCheck(self, irc):
        if len(self.APIKEY) < 1:
            irc.reply("You can't use this command until you've set an API key!")
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

            irc.reply(("%d %s %s now watching: %s (%d) | %s | %d%% | Trailer: %s" % ( movie["watchers"], people, are, movie["title"], movie["year"], movie["url"], movie["ratings"]["percentage"], movie["trailer"] )).encode("utf-8"))
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

            irc.reply(("%d %s %s now watching: %s (%d) | %s | Rating: %d%%" % ( show["watchers"], people, are, show["title"], show["year"], show["url"], show["ratings"]["percentage"] )).encode("utf-8"))
            if shows >= self.registryValue("maxSearchResults"):
                break

    ts = wrap(trendingShows, [optional("something")])

    def showSummary(self, irc, msg, args, tvdbID):
        """Get a summary for a TV show"""

        url = "%s/show/summary.json/%s/%s" % (self.APIURL, self.APIKEY, tvdbID)

        try:
           f = urllib2.urlopen(url)
        except urllib2.HTTPError, e:
            if e.code == 404:
               irc.error("Show not found.")
            else:
               irc.error("Error: %s" % (e.code))
            print e.read()
            return

        data = simplejson.load(f)
        return data

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
                    irc.reply(("You are now watching: %s (%d) | %s | %s%% | %s" % (data["movie"]["title"], data["movie"]["year"], certification, moviePercentage, data["movie"]["url"])).encode("utf-8"))
                else:
                    irc.reply(("You are now watching: %s (%d) | %s | %s" % (data["movie"]["title"], data["movie"]["year"], certification, data["movie"]["url"])).encode("utf-8"))

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
                    irc.reply(("You are now watching: %s (%s) - %dx%d - %s | %s%%/%s%% | %s" % \
			(data["show"]["title"], data["show"]["year"], data["episode"]["season"], data["episode"]["number"], data["episode"]["title"], showPercentage, epPercentage, data["episode"]["url"])).encode("utf-8"))
                else:
                    irc.reply(("You are now watching: %s (%d) - %dx%d - %s | %s" % \
			(data["show"]["title"], data["show"]["year"], data["episode"]["season"], data["episode"]["number"], data["episode"]["title"], data["episode"]["url"])).encode("utf-8"))
	else:
	    irc.reply("You are not currently watching anything.")
        
    nw = wrap(nw, [optional("something")])

    def peopleSearch(self, irc, msg, args, query):
	"""<query>
	   Search for people including actors, directors, producers, and writers.
	"""
	if not self.keyCheck(irc):
	    return False

	url = "%s/search/people.json/%s/%s" % (self.APIURL, self.APIKEY, urllib.quote_plus(query))

	try:
	    f = urllib2.urlopen(url)
	except urllib2.HTTPError, e:
	    if e.code == 404:
                irc.error("Nobody found by that name.")
            print e.read()
	    return
        
	data = simplejson.load(f)
        if data:
            found = "Found %d results" % len(data)
	    if len(data) > self.registryValue("maxSearchResults"):
	        found += (", returning the first %s.  More here: %s/search/people?q=%s" % (self.registryValue("maxSearchResults"), self.SITEURL, urllib.quote_plus(query)))

	    irc.reply(found.encode("utf-8"))
            people = 0
            for person in data:
                people += 1
                irc.reply(("%s | %s" % \
                    (person["name"], person["url"])).encode("utf-8"))

                if people >= self.registryValue("maxSearchResults"):
                    break
        else:
            irc.reply(("No people found matching: %s" % (query)).encode("utf-8"))
	    
    person = wrap(peopleSearch, ['text'])
        

    def episodeSearch(self, irc, msg, args, query):
        """<query>
	   Search for a given TV episode name
	"""

        if not self.keyCheck(irc):
            return False

        url = "%s/search/episodes.json/%s/%s" % (self.APIURL, self.APIKEY, urllib.quote_plus(query))

	try:
	    f = urllib2.urlopen(url)
	except urllib2.HTTPError, e:
	    if e.code == 404:
                irc.error("Episode not found")
            print e.read()
	    return
        
	data = simplejson.load(f)
        if data:
            found = "Found %d results" % len(data)
	    if len(data) > self.registryValue("maxSearchResults"):
	        found += (", returning the first %s.  More here: %s/search/episodes?q=%s" % (self.registryValue("maxSearchResults"), self.SITEURL, urllib.quote_plus(query)))

	    irc.reply(found.encode("utf-8"))
            eps = 0
            for ep in data:
                eps += 1
                irc.reply(("%s (%d) - %dx%d - %s | %s" % \
                    (ep["show"]["title"], ep["show"]["year"], ep["episode"]["season"], ep["episode"]["episode"], ep["episode"]["title"], ep["episode"]["url"])).encode("utf-8"))

                if eps >= self.registryValue("maxSearchResults"):
                    break
        else:
            irc.reply(("No episode titles found matching: %s" % (query)).encode("utf-8"))
	    
    tvep = wrap(episodeSearch, ['text'])
        
    def showSearch(self, irc, msg, args, query, ret=False):
        """<query>
           Search for a given TV show name
        """

        if not self.keyCheck(irc):
            return False

        url = "%s/search/shows.json/%s/%s" % (self.APIURL, self.APIKEY, urllib.quote_plus(query))

        try:
            f = urllib2.urlopen(url)
        except urllib2.HTTPError, e:
            if e.code == 404:
                irc.error("Show not found")
            print e.read()
            return

        data = simplejson.load(f)

	if ret:
	    return data

	if data:
            found = "Found %d results" % len(data)
            if len(data) > self.registryValue("maxSearchResults"):
                found += (", returning the first %s.  More here: %s/search/shows?q=%s" % (self.registryValue("maxSearchResults"), self.SITEURL, urllib.quote_plus(query)))

            irc.reply(found.encode("utf-8"))
	    shows = 0
            for show in data:
                shows += 1
                irc.reply(("%s (%d) | %s" % (show["title"], show["year"], show["url"])).encode("utf-8"))

                if shows >= self.registryValue("maxSearchResults"):
                    break
	else:
	    irc.reply(("No shows found matching: %s" % (query)).encode("utf-8"))

    tvshow = wrap(showSearch, ['text'])


    def showRatingSearch(self, irc, msg, args, query):
	"""<query>
	   Return the ratings for the given TV show.
	"""
	   
	if not self.keyCheck(irc):
	    return False

	shows = self.showSearch(irc, msg, args, query, ret=True)

	if shows:
	    count = 0
	    for item in shows:
		count += 1
	        show = self.showSummary(irc, msg, args, item["tvdb_id"])
                irc.reply(("%s (%s) | %d%% of %d votes | %s" % \
                    (show["title"], show["year"], show["ratings"]["percentage"], show["ratings"]["votes"], show["url"])).encode("utf-8"))

	        if count >= self.registryValue("maxSearchResults"):
		    break
	else:
	    irc.reply(("No shows found matching: %s" % (query)).encode("utf-8"))

    rating = wrap(showRatingSearch, ['text'])

dbfilename = conf.supybot.directories.data.dirize("TraktTV.db")

Class = TraktTV
