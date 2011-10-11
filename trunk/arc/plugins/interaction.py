# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import cPickle, math, random, traceback

from arc.constants import *
from arc.decorators import *
from arc.irc_client import *
from arc.plugins import ProtocolPlugin
from arc.timer import ResettableTimer
#from arc.serverplugins import inbox

class InteractionPlugin(ProtocolPlugin):
    "Commands for player interactions."

    commands = {
        "say": "commandSay",
        "msg": "commandSay",
        "me": "commandMe",
        "away": "commandAway",
        "afk": "commandAway",
        "brb": "commandAway",
        "back": "commandBack",
        "slap": "commandSlap",
        "punch": "commandPunch",
        "roll": "commandRoll",
        "kill": "commandKill",

        "count": "commandCount",
        "countdown": "commandCount",

        "s": "commandSendMessage",
        "sendmessage": "commandSendMessage",
        "inbox": "commandCheckMessages",
        "c": "commandClear",
        "clear": "commandClear",
        "clearinbox": "commandClear",

        "rainbow": "commandRainbow",
        "fabulous": "commandRainbow",
        "fab": "commandRainbow",
        "mefab": "commandMeRainbow",
        "merainbow": "commandMeRainbow",
    }

    def gotClient(self):
        self.num = int(0)
        # Check with the server plugin if we have a message waiting
        # The method will get back to you later
        # self.client.factory.serverPlugins["OfflineMessagePlugin"].checkMessage(self.client.username)

    def sendgo(self):
        self.client.sendPlainWorldMessage("&2[COUNTDOWN] GO!")
        self.num = 0

    def sendcount(self, count):
        if not int(self.num) - int(count) == 0:
            self.client.sendPlainWorldMessage("&2[COUNTDOWN] %s" % (int(self.num) - int(count)))

    @config("category", "player")
    def commandBack(self, parts, fromloc, overriderank):
        "/back - Guest\nPrints out message of you coming back."
        self.client.factory.queue.put((self.client, TASK_AWAYMESSAGE, "%s is now %sback." % (self.client.username, COLOUR_DARKGREEN)))
        self.client.gone = 0

    @config("category", "player")
    def commandAway(self, parts, fromloc, overriderank):
         "/away reason - Guest\nAliases: afk, brb\nPrints out message of you going away."
         if len(parts) == 1:
            self.client.factory.queue.put((self.client, TASK_AWAYMESSAGE, "%s has gone AFK" % self.client.username))
            self.client.gone = 1
         else:
            self.client.factory.queue.put((self.client, TASK_AWAYMESSAGE, "%s has gone AFK (%s)" % (self.client.username, " ".join(parts[1:]))))
            self.client.gone = 1

    @config("category", "player")
    def commandMe(self, parts, fromloc, overriderank):
        "/me action - Guest\nPrints 'username action'"
        if len(parts) == 1:
            self.client.sendServerMessage("Please type an action.")
        else:
            if self.client.isSilenced():
                self.client.sendServerMessage("You are Silenced and lost your tongue.")
            else:
                self.client.factory.queue.put((self.client, TASK_ACTION, (self.client.id, self.client.userColour(), self.client.username, " ".join(parts[1:]))))

    @config("rank", "mod")
    def commandSay(self, parts, fromloc, overriderank):
        "/say message - Mod\nAliases: msg\nPrints out message in the server color."
        if len(parts) == 1:
            self.client.sendServerMessage("Please type a message.")
        else:
            self.client.factory.queue.put((self.client, TASK_SERVERMESSAGE, ("[MSG] %s" % " ".join(parts[1:]))))

    @config("category", "player")
    def commandSlap(self, parts, fromloc, overriderank):
        "/slap username [with object] - Guest\nSlap username [with object]."
        if len(parts) == 1:
            self.client.sendServerMessage("Please enter the name for the slappee.")
        else:
            stage = 0
            name = ''
            object = ''
            for i in range(1, len(parts)):
                if parts[i] == "with":
                    stage = 1
                    continue
                    if stage == 0 :
                        name += parts[i]
                        if (i+1 != len(parts) ) :
                            if (parts[i+1] != "with"):
                                name += " "
                    else:
                        object += parts[i]
                        if (i != len(parts)-1):
                            object += " "
                else:
                    if stage == 1:
                        self.client.sendWorldMessage("* %s%s slaps %s with %s!" % (COLOUR_PURPLE, self.client.username, name, object))
                        self.client.factory.irc_relay.sendServerMessage("%s slaps %s with %s!" % (self.client.username, name, object))
                    else:
                        self.client.sendWorldMessage("* %s%s slaps %s with a giant smelly trout!" % (COLOUR_PURPLE, self.client.username, name))
                        self.client.factory.irc_relay.sendServerMessage("* %s slaps %s with a giant smelly trout!" % (self.client.username, name))

    @config("category", "player")
    def commandPunch(self, parts, fromloc, overriderank):
        "/punch username [bodypart to punch] - Punch username [in a bodypart]."
        if len(parts) == 1:
            self.client.sendServerMessage("Please enter the name for the punchee.")
        else:
            stage = 0
            name = ''
            object = ''
            for i in range(1, len(parts)):
                if parts[i] == "by":
                    stage = 1
                    continue
                    if stage == 0 :
                        name += parts[i]
                        if (i+1 != len(parts)):
                            if (parts[i+1] != "by"):
                                name += " "
                    else:
                        object += parts[i]
                        if (i != len(parts)-1):
                            object += " "
                else:
                    if stage == 1:
                        self.client.sendWorldMessage("* %s%s punches %s in the %s!" % (COLOUR_PURPLE, self.client.username, name, object))
                        self.client.factory.irc_relay.sendServerMessage("%s punches %s in the %s!" % (self.client.username, name, object))
                    else:
                        self.client.sendWorldMessage("* %s%s punches %s in the face!" % (COLOUR_PURPLE, self.client.username, name))
                        self.client.factory.irc_relay.sendServerMessage("* %s punches %s in the face!" % (self.client.username, name))

    @config("rank", "mod")
    @username_command
    def commandKill(self, user, fromloc, overriderank, params=[]):
        "/kill username [reason] - Mod\nKills the user for reason (optional)."
        killer = self.client.username
        user.teleportTo(user.world.spawn[0], user.world.spawn[1], user.world.spawn[2], user.world.spawn[3])
        if killer == user.username:
            user.sendServerMessage("You have died.")
            self.client.factory.queue.put((self.client, TASK_SERVERURGENTMESSAGE, "%s has died" % (user.username)))
        else:
            user.sendServerMessage("You have been killed by %s." % self.client.username)
            self.client.factory.queue.put((self.client, TASK_SERVERURGENTMESSAGE, "%s has been killed by %s." % (user.username, killer)))
            if params:
                self.client.factory.queue.put((self.client, TASK_SERVERURGENTMESSAGE, "Reason: %s" % (" ".join(params))))
            else:
                return

    @config("rank", "mod")
    @only_username_command
    def commandSmack(self, username, fromloc, overriderank, params=[]):
        "/smack username [reason] - Mod\Smacks the user for reason (optional)"
        smacker = self.client.username
        if user.isMod():
            self.client.sendServerMessgae("You can't smack staff!")
        else:
            if user.world == "default":
                user.teleportTo(self.factory.worlds["default"].spawn[0], self.factory.worlds["default"].spawn[1], self.factory.worlds["default"].spawn[2])
            else:
                user.changeToWorld("default")
            user.sendServerMessage("You have been smacked by %s." % self.client.username)
            self.client.factory.queue.put((self.client, TASK_SERVERURGENTMESSAGE, "%s has been smacked by %s." % (user.username, smacker)))
            if params:
                self.client.factory.queue.put((self.client, TASK_SERVERURGENTMESSAGE, "Reason: %s" % (" ".join(params))))

    def commandRoll(self, parts, fromloc, overriderank):
        "/roll max - Guest\nRolls a random number from 1 to max. Announces to world."
        if len(parts) == 1:
            self.client.sendServerMessage("Please enter a number as the maximum roll.")
        else:
            try:
                roll = roll = int(math.floor((random.random() * (int(parts[1])-1)+1)))
            except ValueError:
                self.client.sendServerMessage("Please enter an integer as the maximum roll.")
            else:
                self.client.sendWorldMessage("%s rolled a %s" % (self.client.username, roll))

    @config("rank", "builder")
    def commandCount(self, parts, fromloc, overriderank):
        "/count [number] - Builder\nAliases: countdown\nCounts down from 3 or from number given (up to 15)"
        if self.num != 0:
            self.client.sendServerMessage("You can only have one count at a time!")
            return
        if len(parts) > 1:
            try:
                self.num = int(parts[1])
            except ValueError:
                self.client.sendServerMessage("Number must be an integer!")
                return
        else:
            self.num = 3
        if self.num > 15:
            self.client.sendServerMessage("You can't count from higher than 15!")
            self.num = 0
            return
        counttimer = ResettableTimer(self.num, 1, self.sendgo, self.sendcount)
        self.client.sendPlainWorldMessage("&2[COUNTDOWN] %s" %self.num)
        counttimer.start()

    def commandSendMessage(self,parts, fromloc, overriderank):
        "/s username message - Guest\nAliases: sendmessage\nSends an message to the users Inbox."
        if len(parts) < 3:
            self.client.sendServerMessage("You must provide a username and a message.")
        else:
            try:
                from_user = self.client.username
                to_user = parts[1]
                
                if to_user in messages:
                    messages[to_user]+= "\n" + from_user + ": " + mess
                else:
                    messages[to_user] = from_user + ": " + mess
                file = open('config/data/inbox.dat', 'w')
                cPickle.dump(messages, file)
                file.close()
                self.client.factory.usernames[to_user].MessageAlert()
                self.client.sendServerMessage("A message has been sent to %s." % to_user)
            except:
                self.client.sendServerMessage("Error sending message.")

    def commandCheckMessages(self, parts, fromloc, overriderank):
        "/inbox [mode] - Guest\nChecks your inbox of messages.\nModes: NEW, ALL"
        file = open('config/data/inbox.dat', 'r')
        messages = cPickle.load(file)
        file.close()
        if self.client.username.lower() in messages:
            self.client._sendMessage(COLOUR_DARKPURPLE, messages[self.client.username.lower()])
            self.client.sendServerMessage("NOTE: Might want to do /c now.")
        else:
            self.client.sendServerMessage("You do not have any messages.")

#    def commandCheckMessages_DOESNOTWORK(self, parts, fromloc, overriderank):
#        "/inbox [mode] - Guest\nChecks your inbox of messages.\nModes: NEW, ALL"
#        if len(parts) > 0:
#            if parts[1].lower() in ["new", "all"]:
#                selection = parts[1].lower()
#            else:
#                self.client.sendServerMessage("Mode %s not recongized. Using 'all' instead." % parts[1].lower())
#                selection = "all"
#        else:
#            selection = "all"
#        entries = self.client.factory.serverPlugins["OfflineMessageServerPlugin"].getMessages(self.client.username, "to")
#        if entries == False:
#            self.client.sendServerMessage("You do not have any messages in your inbox.")
#            return
#        else:
#            for entry in entries:
#                id, from_user, to_user, message, date, status = entry
#                if status == STATUS_UNREAD and selection in ["new", "all"]:
#                    meetCriteria = True
#                elif status == STATUS_READ and selection == "all":
#                    meetCriteria = True
#                else:
#                    meetCriteria = False
#                if meetCriteria:
#                    self.client.sendServerMessage("Message sent by %s at %s: (ID: %s)" % (from_user, date, id))
#                    self.client.sendSplitServerMessage(message)
#                    self.client.sendServerMessage("------------------")

    def commandClear(self,parts, fromloc, overriderank):
        "/c - Guest\nAliases: clear, clearinbox\nClears your Inbox of messages."
        target = self.client.username
        if len(parts) == 2:
            target = parts[1]
        elif self.client.username.lower() not in self.client.factory.messages:
            self.client.sendServerMessage("You have no messages to clear.")
            return False
        self.client.factory.messages.pop(target)
        file = open('config/data/inbox.dat', 'w')
        cPickle.dump(messages, file)
        file.close()
        self.client.sendServerMessage("All your messages have been deleted.")

    @config("disabled", True)
    def commandRainbow(self, parts, fromloc, overriderank):
        "/rainbow - Guest\nAliases: fabulous, fab\nMakes your text rainbow."
        if len(parts) == 1:
            self.client.sendServerMessage("Please include a message to rainbowify.")
        else:
            stringInput = parts[1:]
            input  = ""
            for a in stringInput:
                input = input + a + " "
            output = ""
            colorNum = 0
            for x in input:
                if x != " ":
                    output = output + self.colors[colorNum] + x
                    colorNum = colorNum + 1
                    if colorNum >= 9:
                        colorNum = 0
                if x == " ":
                    output = output + x
            self.client.factory.queue.put((self.client, TASK_ONMESSAGE, " "+self.client.userColour()+self.client.username+": "+output))

    @config("disabled", True)
    def commandMeRainbow(self, parts, fromloc, overriderank):
        "/mefab - Guest\nAliases: merainbow\nSends an action in rainbow colors."
        if len(parts) == 1:
            self.client.sendServerMessage("Please include an action to rainbowify.")
        else:
            stringInput = parts[1:]
            input  = ""
            for a in stringInput:
                input = input + a + " "
            output = ""
            colorNum = 0
            for x in input:
                if x != " ":
                    output = output + colors[colorNum] + x
                    colorNum = colorNum + 1
                    if colorNum >= 9:
                        colorNum = 0
                if x == " ":
                    output = output + x
            self.client.factory.queue.put((self.client, TASK_ONMESSAGE, "* "+self.client.userColour()+self.client.username+": "+output))