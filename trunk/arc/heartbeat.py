# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import sys, urllib

from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from twisted.internet.defer import TimeoutError
from twisted.web.error import Error as twistedError
from twisted.web.client import getPage

from arc.constants import *
from arc.logger import ColouredLogger

debug = (True if "--debug" in sys.argv else False)

class Heartbeat(object):
    """
    Deals with registering with the ClassiCube main server every so often.
    The Salt is also used to help verify users' identities.
    """

    def __init__(self, factory):
        self.factory = factory
        self.logger = factory.logger
        self.loop = LoopingCall(self.sendHeartbeat)
        self.loop.start(25) # In the future for every spoofed heartbeat it would deduct by 2 seconds, but not now
        self.logger.info("Heartbeat sending process initiated.")
        self.factory.runHook("heartbeatBuilt")

    @property
    def hbdata(self):
        return urllib.urlencode({
            "port": self.factory.server_port,
            "users": len(self.factory.clients),
            "max": self.factory.max_clients,
            "name": self.factory.server_name,
            "public": self.factory.public,
            "version": 7,
            "salt": self.factory.salt,
			"software": "Arc",
            })

    def sendHeartbeat(self):
        self._sendHeartbeat()

    def _sendHeartbeat(self):
        hburl = "http://www.classicube.net/heartbeat.jsp"
        getPage(hburl, method="POST", postdata=self.hbdata,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}, timeout=30).addCallback(
            self.heartbeatSentCallback).addErrback(self.heartbeatFailedCallback)

    def heartbeatSentCallback(self, result):
        self.url = result
        self.logger.info("Heartbeat Sent. URL (saved to docs/SERVERURL): %s" % self.url)
        fh = open('config/data/SERVERURL', 'w')
        fh.write(self.url)
        fh.flush()
        fh.close()
        self.factory.runHook("heartbeatSent")

    def heartbeatFailedCallback(self, err, id):
        if isinstance(err, TimeoutError):
            self.logger.error(
                "Heartbeat sending%s timed out." % self.factory.heartbeats[id][0])
        elif isinstance(err, twistedError):
            self.logger.error("Heartbeat failed to send. Error:")
            self.logger.error(str(err))
        else:
            self.logger.error("Unexpected error in heartbeat sending process%s. Error:" % self.factory.heartbeats[id][0])
            self.logger.error(str(err))