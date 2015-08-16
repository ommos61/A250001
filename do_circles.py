#!/usr/bin/env python
#
#  Description:
#       This program is intended to generated the combinations for
#       the integer series A250001 which is described on oeis.org
#
#       Apart from generating the sequences, it will also create an
#       image for the various circle configurations
#
#  History:
#       2015-08-14 Martin Smits
#               Created some initial code which only handles
#               non-intersectinng circles
#

# modules we need
import os, sys
import argparse
import copy
import Image, ImageDraw

# some generic functions for outputting information
DEBUG = True
def debug(msg):
    if DEBUG:
        print "DEBUG: " + msg
def info(msg):
    print "Info: " + msg

#------------------------------------------------------------------------
#  Class for the complete image that supports drawing circles
#
class CirclesImage:
    def __init__(self, width, height):
        self.im = Image.new("RGB", (width, height), "white")
        self.canvas = ImageDraw.Draw(self.im)

    def draw_circle(self, x, y, r):
        self.canvas.ellipse((x-r, y-r, x+r, y+r), outline=(0,0,0))

    def draw_text(self, x, y, msg):
        self.canvas.text((x, y), msg, fill=(0, 0, 0))

    def save(self, filename):
        self.filename = filename
        self.im.save(self.filename)

    def show(self):
        self.im.show()

    def upload(self):
        os.system("scp " + self.filename + " ommos.net:public_html/A250001")
        info("Image available at http://www.ommos.net/~msmits/A250001/{}".format(self.filename))

#------------------------------------------------------------------------
#  A collection of configurations
#
class CirclesCollection:
    def __init__(self, level):
        self._level = level
        self.collection = []
        self.index = 0

    def __iter__(self):
        self.index = 0
        return self

    def next(self):
        if self.index >= len(self.collection):
            raise StopIteration
        self.index += 1
        return self.collection[self.index - 1]

    @staticmethod
    def new(level):
        return CirclesCollection(level)

    def next_level(self):
        debug("Creating new collection with level " + str(self.level() + 1))
        new_collection = CirclesCollection.new(self.level() + 1)
        for config in self.collection:
            # create new configs with one circle added
            new_configs = config.add_circle()
            for new_config in new_configs:
                equiv = False
                for test_config in new_collection:
                    equiv |= test_config.equivalent(new_config)
                if not equiv:
                    new_collection.add(new_config)
        return new_collection

    def add(self, configuration):
        self.collection.append(configuration)

    def count(self):
        return len(self.collection)

    def level(self):
        return self._level

    def create_image(self, upload):
        info("Create image for level {}.".format(self.level()))
        configs_image = CirclesImage(1024,2048)
        scale = 10
        offset_y = 0.5 * scale
        for config in self.collection:
            debug("configuration: " + str(config))
            circles = config.get_circles(config.get_nesting(), 0)
            radius_max = 0
            for circle in circles:
                if (circle[2] * scale) > radius_max:
                    radius_max = circle[2] * scale
            offset_x = (radius_max + 0.5 * scale)
            offset_y += radius_max
            configs_image.draw_text(300, offset_y, str(config))
            for circle in circles:
                configs_image.draw_circle(
                    circle[0] * 2.5 * scale + offset_x,
                    circle[1] * scale + offset_y,
                    circle[2] * scale
                )
            offset_y += (radius_max + 1.5 * scale)
        configs_image.save("circles_{}.png".format(self.level()))
        if upload:
            configs_image.upload()

#------------------------------------------------------------------------
#  Representation of one circles configuration
#
class CircleSet:
    def __init__(self):
        self.contents = []

    def __str__(self):
        if len(self.contents) == 0:
            contents = "[ ]"
        else:
            contents = "[ "
            first = True
            for c in sorted(self.contents, cmp=lambda x, y: cmp(y.get_nesting(), x.get_nesting())):
                if first:
                    contents += str(c)
                    first = False
                else:
                    contents += ", " + str(c)
            contents += " ]"
        return contents

    def add(self, what):
        self.contents.append(what)

    def add_circle(self):
        debug("Generating new circle configurations with one additional circle")
        # generate new configurations with one additional circle
        new_sets = []
        # new configuration can be:
        # - add circle outside on top-level
        new_set = copy.deepcopy(self)
        new_set.add(Circle())
        new_sets.append(new_set)
        # - inside anything existing
        for i in range(len(self.contents)):
            new_circles = self.contents[i].add_circle()
            for c in new_circles:
                new_set = copy.deepcopy(self)
                new_set.contents[i] = c
                new_sets.append(new_set)
        # return the new configurations
        return new_sets

    def equivalent(self, config):
        # check on equivalence with configs already in
        # the new collection
        debug("Comparing {} with {}".format(str(config), str(self)))
        return (str(config) == str(self))

    def get_nesting(self):
        if len(self.contents) == 0:
            return 0
        else:
            max_nesting = 0
            for c in self.contents:
                nesting = c.get_nesting()
                if nesting > max_nesting:
                    max_nesting = nesting
            return max_nesting

    def get_circles(self, nesting, offset):
        circles = []
        for c in self.contents:
            new_circles = c.get_circles(nesting, offset)
            for nc in new_circles:
                circles.append(nc)
            offset += nesting
        # debug("Drawable circles: " + str(circles))
        return circles

#------------------------------------------------------------------------
# Representation of a circle
#
class Circle:
    def __init__(self):
        self.contents = []
        # TODO Intersections
        #self.intersects = []

    def __str__(self):
        if len(self.contents) == 0:
            contents = "C"
        else:
            contents = "C "
            for c in self.contents:
                contents += str(c)
        return contents

    def add_circle(self):
        debug("Adding a circle to an existing one")
        # generate all variations for adding one circle
        if len(self.contents) == 0:
            circle = copy.deepcopy(self)
            # create new CircleSet with one Circle
            new_set = CircleSet()
            new_set.add(Circle())
            circle.contents.append(new_set)
            return [ circle ]
        else:
            new_circles = [ ]
            new_sets = self.contents[0].add_circle()
            for s in new_sets:
                new_circle = Circle()
                new_circle.contents.append(s)
                new_circles.append(new_circle)
            return new_circles

    def get_nesting(self):
        if len(self.contents) == 0:
            return 1
        else:
            max_nesting = 1
            for c in self.contents:
                nesting = c.get_nesting()
                if nesting + 1 > max_nesting:
                    max_nesting = nesting + 1
            return max_nesting

    def get_circles(self, nesting, offset):
        circles = [ ]
        count = 1
        if len(self.contents) != 0:
            count += len(self.contents) - 1
            sub_circles = self.contents[0].get_circles(nesting - 1, offset)
            for sc in sub_circles:
                circles.append(sc)
        circle = (1 + offset, 1, nesting * count)
        circles.append(circle)
        return circles

#========================================================================
# The main program
#========================================================================

parser = argparse.ArgumentParser(description="Generate A250001 circles")
parser.add_argument('circles', metavar='N', type=int, default=4, nargs='?',
                    help='the number of circles per configuration')
parser.add_argument('-image', dest='image', default=False, action='store_true',
                    help='output images for each level')
parser.add_argument('-upload', dest='upload', default=False, action='store_true',
                    help='upload the image to some website')
parser.add_argument('-debug', dest='debug', default=False, action='store_true',
                    help='turn on some debugging output')
args = parser.parse_args()
level = args.circles
image = args.image
upload = args.upload
DEBUG = args.debug

collections = [ CirclesCollection.new(0) ]
collections[0].add(CircleSet())

for i in range(level):
    c_new = collections[len(collections) - 1].next_level()
    collections.append(c_new)


print "{:10} {:10}".format("Level", "Count")
for c in collections:
    if c.level() > 0:
        print "{:<10} {:<10}".format(c.level(), c.count())
for c in collections:
    if c.level() > 0:
        if image:
            c.create_image(upload)
