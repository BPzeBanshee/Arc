# Arc is copyright 2009-2011 the Arc team and other contributors.
# Arc is licensed under the BSD 2-Clause modified License.
# To view more details, please see the "LICENSING" file in the "docs" folder of the Arc Package.

import sys, urllib

try:
    import pil
except ImportError:
    print ("Failed to load PIL, imagedraw is now disabled")
    noimagedraw = True

from twisted.internet import defer, reactor

from arc.constants import *
from arc.decorators import *
from arc.globals import *
from arc.plugins import ProtocolPlugin

class InternetPlugin(ProtocolPlugin):
    "Commands for communicating with internet services."

    commands = {
        "tlog": "commandTlogin",
        "tdetails": "commandTDetails",
        "tweet": "commandTweet",
        "rec_url": "commandRec_url",
        "imagedraw": "commandImagedraw",
        }

    def gotClient(self):
        self.tuser = ""
        self.tpass = ""
        makefile("logs/twitter.log")
        try:
            getattr(self.client.factory, "twlog")
        except AttributeError:
            self.client.factory.twlog = open("logs/twitter.log", "a")
        self.url = ""

    @config("custom_cmdlog_msg", "just logged into Twitter.")
    @config("category", "info")
    @config("disabled_cmdblocks", True)
    def commandTlogin(self, parts, fromloc, overriderank):
        "/tlog username password - Guest\nReplace username and password to login to Twitter."
        if len(parts) < 3:
            self.client.sendServerMessage("Please input a username and password.")
        else:
            self.tuser = str(parts[1])
            self.tpass = str(parts[2])
            self.client.sendServerMessage("Username: " + COLOUR_RED + self.tuser)
            self.client.sendServerMessage("Password: " + COLOUR_RED + self.tpass)
            self.client.factory.twlog.write(
                self.tuser + "(" + self.client.username + ")" + " has logged into twitter.\n")
            self.client.factory.twlog.flush()

    @config("category", "info")
    @config("disabled_cmdblocks", True)
    def commandTweet(self, parts, fromloc, overriderank):
        "/tweet tweet - Guest\nSend a tweet to Twitter after using /tlog."
        if self.tuser == "":
            self.client.sendServerMessage("Please do /tlog first.")
        else:
            msg = urllib.quote(" ".join(parts[1:]) + " #Arc")
            data = urllib.urlencode({"status": " ".join(parts[1:]) + " #Arc"})
            urllib.urlopen(("http://%s:%s@twitter.com/statuses/update.xml" % (self.tuser, self.tpass)), data)
            self.client.sendServerMessage("You have successfully tweeted.")
            self.client.factory.twlog.write(
                self.tuser + "(" + self.client.username + ")" + " has tweeted: " + msg + "\n")
            self.client.factory.twlog.flush()

    @config("category", "info")
    @config("disabled_cmdblocks", True)
    def commandTDetails(self, parts, fromloc, overriderank):
        "/tdetails - Guest\nGives you your Twitter login details, from /tlog."
        if self.tuser == "":
            self.client.sendServerMessage("Username: " + COLOUR_RED + "Not entered!")
        else:
            self.client.sendServerMessage("Username: " + COLOUR_RED + self.tuser)
        if self.tpass == "":
            self.client.sendServerMessage("Password: " + COLOUR_RED + "Not entered!")
        self.twlog.write(self.tuser + "(" + self.client.username + ")" + " has checked their Twitter details.\n")
        self.twlog.flush()

    @config("category", "build")
    @config("rank", "admin")
    def commandRec_url(self, parts, fromloc, overriderank):
        "/rec_url URL - Builder\nRecords an url to later imagedraw it."
        if noimagedraw == True:
            self.client.sendServerMessage("Imagedraw is currently disabled due to server problems.")
        else:
            if len(parts) == 1:
                self.client.sendSplitServerMessage(
                    "Please specify an url (and '//' in the beginning to extend an existing url)")
                return
            else:
                if parts[0] == '//rec_url':
                    self.url += (" ".join(parts[1:])).strip()
                else:
                    self.url = (" ".join(parts[1:])).strip()
            var_divisions64 = int(len(self.client.url) / 64)
            self.client.sendServerMessage("The url has been recorded as:")
            for i in range(var_divisions64):
                self.client.sendServerMessage(self.client.url[i * 64:(i + 1) * 64])
            self.client.sendServerMessage(self.client.url[var_divisions64 * 64:])

    @config("category", "build")
    @config("rank", "admin")
    def commandImagedraw(self, parts, fromloc, overriderank):
        "/imagedraw flip rotation [x y z x2 y2 z2] - Builder\nSets all blocks in this area to image.\nFlip: Flip the image or not\nRotation: Rotate the image by how many degrees."
        if noimagedraw == True:
            self.client.sendServerMessage("Imagedraw is currently disabled due to server problems.")
        else:
            if len(parts) < 8 and len(parts) != 3:
                self.client.sendServerMessage("Please enter whether to flip or not (rotation)")
                self.client.sendServerMessage("(and possibly two coord triples)")
            else:
                # Try getting the rotation
                try:
                    rotation = int(parts[2])
                except ValueError:
                    self.client.sendServerMessage("Rotation must be an integer.")
                    return
                    # Try to get flip
                flip = parts[1].lower()
                if flip not in ["true", "false"]:
                    self.client.sendServerMessage("Flip must be true or false.")
                    return
                    # Try to get url
                if self.url == "":
                    self.client.sendServerMessage("You have not recorded an url yet (use /rec_url).")
                    return
                if self.url.find('http:') == -1:
                    self.client.sendServerMessage("Only the http protocol is supported.")
                    return
                    # If they only provided the type argument, use the last two block places
                if len(parts) == 2:
                    try:
                        x, y, z = self.client.last_block_changes[0]
                        x2, y2, z2 = self.client.last_block_changes[1]
                    except IndexError:
                        self.client.sendServerMessage("You have not clicked two corners yet.")
                        return
                else:
                    try:
                        x = int(parts[3])
                        y = int(parts[4])
                        z = int(parts[5])
                        x2 = int(parts[6])
                        y2 = int(parts[7])
                        z2 = int(parts[8])
                    except ValueError:
                        self.client.sendServerMessage("All coordinate parameters must be integers.")
                        return
                if y == y2:
                    height = abs(x2 - x) + 1
                    width = abs(z2 - z) + 1
                    orientation = 0
                elif z == z2:
                    height = abs(x2 - x) + 1
                    width = abs(y2 - y) + 1
                    orientation = 1
                else:
                    x2 = x
                    height = abs(y2 - y) + 1
                    width = abs(z2 - z) + 1
                    orientation = 2
                try:
                    u = urllib.urlopen(self.url)
                    f = StringIO.StringIO(u.read())
                    image = Image.open(f)
                except:
                    self.client.sendServerMessage("The url of the image is invalid or unaccesible.")
                    return
                if rotation != 0:
                    image = image.rotate(rotation, 3, 1)
                image = image.resize((width, height), 1)
                image = image.convert("RGBA")
                if x > x2:
                    x, x2 = x2, x
                if y > y2:
                    y, y2 = y2, y
                if z > z2:
                    z, z2 = z2, z
                limit = self.client.getBlbLimit()
                if limit != -1:
                    # Stop them doing silly things
                    if (height * width > limit) or limit == 0:
                        self.client.sendServerMessage(
                            "Sorry, that area is too big for you to draw images (limit is %s)" % limit)
                        return
                    # Draw all the blocks on, I guess
                # We use a generator so we can slowly release the blocks
                # We also keep world as a local so they can't change worlds and affect the new one
                world = self.client.world

                def generate_changes():
                    try:
                        for i in range(x, x2 + 1):
                            for j in range(y, y2 + 1):
                                for k in range(z, z2 + 1):
                                    if not self.client.AllowedToBuild(i, j, k) and not overriderank:
                                        return
                                    if flip == "true":
                                        if orientation == 0:
                                            r, g, b, a = image.getpixel((abs(k - z), abs(i - x)))
                                        elif orientation == 1:
                                            r, g, b, a = image.getpixel((abs(j - y), abs(i - x)))
                                        else:
                                            r, g, b, a = image.getpixel((abs(k - z), abs(j - y)))
                                    else:
                                        if orientation == 0:
                                            r, g, b, a = image.getpixel((width - (abs(k - z) + 1), abs(i - x)))
                                        elif orientation == 1:
                                            r, g, b, a = image.getpixel((width - (abs(j - y) + 1), abs(i - x)))
                                        else:
                                            r, g, b, a = image.getpixel((width - (abs(k - z) + 1), abs(j - y)))
                                    if a < 25:
                                        block = BLOCK_AIR
                                    else:
                                        r = int(round(float(r) / 50)) * 50
                                        if r == 0:
                                            r = 50
                                        if r == 250:
                                            r = 200
                                        g = int(round(float(g) / 50)) * 50
                                        if g == 0:
                                            g = 50
                                        if g == 250:
                                            g = 200
                                        b = int(round(float(b) / 50)) * 50
                                        if b == 0:
                                            b = 50
                                        if b == 250:
                                            b = 200
                                        if r == 50:
                                            if g == 100:
                                                g = 50
                                            if g == 150:
                                                g = 200
                                        if r == 100:
                                            if g == 50:
                                                g = 100
                                            if g == 200:
                                                g = 150
                                        if r == 150:
                                            if g == 100:
                                                g = 150
                                        if r == 50 and g == 50:
                                            b = 50
                                        if r == 50 and g == 200:
                                            if b == 100:
                                                b = 150
                                        if r == 100 and g == 100:
                                            b = 100
                                        if r == 100 and g == 150:
                                            b = 200
                                        if r == 150 and g == 50:
                                            b = 200
                                        if r == 150 and g == 150:
                                            if b == 50 or b == 100:
                                                b = 150
                                        if r == 150 and g == 200:
                                            b = 50
                                        if r == 200 and g == 50:
                                            if b == 100:
                                                b = 150
                                        if r == 200 and g == 100:
                                            b = 200
                                        if r == 200 and g == 150:
                                            b = 50
                                        if r == 200 and g == 200:
                                            if b == 100:
                                                b = 50
                                            if b == 150:
                                                b = 200
                                        if (r, g, b) == (200, 50, 50):
                                            block = BLOCK_RED
                                        if (r, g, b) == (200, 150, 50):
                                            block = BLOCK_ORANGE
                                        if (r, g, b) == (200, 200, 50):
                                            block = BLOCK_YELLOW
                                        if (r, g, b) == (150, 200, 50):
                                            block = BLOCK_LIME
                                        if (r, g, b) == (50, 200, 50):
                                            block = BLOCK_GREEN
                                        if (r, g, b) == (50, 200, 150):
                                            block = BLOCK_TURQUOISE
                                        if (r, g, b) == (50, 200, 200):
                                            block = BLOCK_CYAN
                                        if (r, g, b) == (100, 150, 200):
                                            block = BLOCK_BLUE
                                        if (r, g, b) == (150, 150, 200):
                                            block = BLOCK_INDIGO
                                        if (r, g, b) == (150, 50, 200):
                                            block = BLOCK_VIOLET
                                        if (r, g, b) == (200, 100, 200):
                                            block = BLOCK_PURPLE
                                        if (r, g, b) == (200, 50, 200):
                                            block = BLOCK_MAGENTA
                                        if (r, g, b) == (200, 50, 150):
                                            block = BLOCK_PINK
                                        if (r, g, b) == (100, 100, 100):
                                            block = BLOCK_BLACK
                                        if (r, g, b) == (150, 150, 150):
                                            block = BLOCK_GRAY
                                        if (r, g, b) == (200, 200, 200):
                                            block = BLOCK_WHITE
                                        if (r, g, b) == (50, 50, 50):
                                            block = BLOCK_OBSIDIAN
                                    block = chr(block)
                                    world[i, j, k] = block
                                    self.client.queueTask(TASK_BLOCKSET, (i, j, k, block), world=world)
                                    self.client.sendBlock(i, j, k, block)
                                    yield
                    except AssertionError:
                        self.client.sendServerMessage("Out of bounds imagedraw error.")
                        return

                    # Now, set up a loop delayed by the reactor
                block_iter = iter(generate_changes())

                def do_step():
                    # Do 10 blocks
                    try:
                        for x in range(10): # 10 blocks at a time, 10 blocks per tenths of a second, 100 blocks a second
                            block_iter.next()
                        reactor.callLater(0.01,
                            do_step)  # This is how long(in seconds) it waits to run another 10 blocks
                    except StopIteration:
                        if fromloc == "user":
                            #self.client.finalizeMassCMD('imagedraw', self.client.total)
                            self.client.sendServerMessage("Your imagedraw just completed.")
                        pass

                do_step()