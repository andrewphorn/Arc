# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

from arc.constants import *
from arc.decorators import *
from arc.plugins import ProtocolPlugin

class MsgblockPlugin(ProtocolPlugin):
    commands = {
        "mb": "commandMsgblock",
        "mbend": "commandMsgblockend",
        "mbshow": "commandShowmsgblocks",
        "mbdel": "commandMsgblockdel",
        "mdel": "commandMsgblockdel",
        "mbdelend": "commandMsgblockdelend",
        }

    hooks = {
        "blockchange": "blockChanged",
        "poschange": "posChanged",
        "newworld": "newWorld",
        }

    def gotClient(self):
        self.msgblock_message = None
        self.msgblock_remove = False
        self.last_block_position = None

    def newWorld(self, world):
        "Hook to reset portal abilities in new worlds if not op."
        if not self.client.isOp():
            self.msgblock_message = None

    def blockChanged(self, x, y, z, block, selected_block, fromloc):
        "Hook trigger for block changes."
        if self.client.world.has_msgblock(x, y, z):
            if self.msgblock_remove:
                self.client.world.delete_msgblock(x, y, z)
                self.client.sendServerMessage("You deleted a message block.")
            else:
                self.client.sendServerMessage("That is a message block, you cannot change it. (/mbdel?)")
                return False # False = they weren't allowed to build
        if self.msgblock_message:
            self.client.sendServerMessage("You placed a message block.")
            self.client.world.add_msgblock(x, y, z, self.msgblock_message)

    def posChanged(self, x, y, z, h, p):
        "Hook trigger for when the user moves"
        rx = x >> 5
        ry = y >> 5
        rz = z >> 5
        # Or a message?
        try:
            if self.client.world.has_msgblock(rx, ry, rz) and (rx, ry, rz) != self.last_block_position:
                for message in self.client.world.get_msgblock(rx, ry, rz).split('\n'):
                    self.client._sendMessage(COLOUR_GREEN, message)
        except AssertionError:
            pass
        self.last_block_position = (rx, ry, rz)

    @config("rank", "op")
    def commandMsgblock(self, parts, fromloc, overriderank):
        "/mb message - Op\nMakes the next block you place a message block.\n Use /mb \\message to append to the last message, or use /mb message to make a new line."
        msg_part = (" ".join(parts[1:])).strip()
        if not msg_part:
            self.client.sendServerMessage("Please enter a message.")
            return
        new_message = False
        if not self.msgblock_message:
            self.msgblock_message = ""
            self.client.sendServerMessage("You are now placing message blocks.")
            new_message = True
        if msg_part[-1] == "\\":
            self.msgblock_message += msg_part[:-1] + " "
        else:
            self.msgblock_message += msg_part + "\n"
        if len(self.msgblock_message) > 200:
            self.msgblock_message = self.msgblock_message[:200]
            self.client.sendServerMessage("Your message ended up longer than 200 chars, and was truncated.")
        elif not new_message:
            self.client.sendServerMessage("Message extended; you've used %i characters." % len(self.msgblock_message))

    @config("rank", "op")
    def commandMsgblockend(self, parts, fromloc, overriderank):
        "/mbend - Op\nStops placing message blocks."
        self.msgblock_message = None
        self.client.sendServerMessage("You are no longer placing message blocks.")

    @config("rank", "op")
    def commandShowmsgblocks(self, parts, fromloc, overriderank):
        "/mbshow - Op\nShows all message blocks as green, only to you."
        for offset in self.client.world.msgblocks.keys():
            x, y, z = self.client.world.get_coords(offset)
            self.client.sendPacked(TYPE_BLOCKSET, x, y, z, BLOCK_GREEN)
        self.client.sendServerMessage("All msgblocks appearing green temporarily.")

    @config("rank", "op")
    def commandMsgblockdel(self, parts, fromloc, overriderank):
        "/mbdel - Op\nAliases: mdel\nEnables msgblock-deleting mode."
        self.client.sendServerMessage("You are now able to delete msgblocks. /mbdelend to stop")
        self.msgblock_remove = True

    @config("rank", "op")
    def commandMsgblockdelend(self, parts, fromloc, overriderank):
        "/mbdelend - Op\nDisables msgblock-deleting mode."
        self.client.sendServerMessage("Msgblock deletion mode ended.")
        self.msgblock_remove = False