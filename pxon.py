#! /usr/bin/env python
# module to read and write PXON data format
# PXON was designed by Jenn Schiffer, for fun.
#
# Why PXON?
# PXON is a mashup of JSON and EXIF 
# with a bespoke and unique 'pxif' pixel data structure at it's core.
# 
# This file uses pxon with the additional time (in milliseconds) attribute for animation.
import time
import datetime
import json
import os
import sys
from collections import OrderedDict #, defaultdict
import copy
from colour import Color    # pip3 install colour

"""
class OrderedDefaultDict(OrderedDict, defaultdict):
    def __init__(self, default_factory=None, *args, **kwargs):
        #in python3 you can omit the args to super
        super(OrderedDefaultDict, self).__init__(*args, **kwargs)
        self.default_factory = default_factory
"""

# pxon_colours = {
    # 'black': (0, 0, 0),
    # 'red': (255, 0, 0),
    # 'green': (0, 255, 0),
    # 'blue': (0, 0, 255),
    # 'white': (255, 255, 255),
    # 'yellow': (0, 255, 255),
    # 'grey': (128, 128, 128),
    # 'light-grey': (192, 192, 192),
    # 'dark-grey': (64, 64, 64)
# }

pxon_timeFormat = '{{:0{:d}d}}'.format(len(repr(sys.maxsize)))

#def obj_dict(obj):
#    """ default object serialiser for json use for Pixel """
#    return obj.__dict__


def rgba(r, g, b, l):
    # ignore l, preumsed to be luminance
    return Color(rgb=(r/256, g/256, b/256))


class Pixel():
    """
    Class for a single pixel
    
    A pixel is at an x and Y position, with an 8-bit RGB colour 
    and a time in milliseconds.
    """
    def __init__(self, x, y, colour, time = None):
        assert isinstance(x, int) and x >= 0
        assert isinstance(y, int) and y >= 0
        assert isinstance(colour, tuple) and len(colour) == 3
        assert isinstance(colour[0], int) and colour[0] >= 0
        assert isinstance(colour[1], int) and colour[1] >= 0
        assert isinstance(colour[2], int) and colour[2] >= 0
        if time: assert isinstance(time, int)
        
        self.pixeldict = OrderedDict()
        # add individually as constructor input is not ordered
        self.pixeldict['x'] = x
        self.pixeldict['y'] = y
        self.pixeldict['color'] = colour
        self.pixeldict['time'] = time
    
    @classmethod
    def pxon(cls, pxonpixel):
        """ Constructor using pxon pxif pixel input

        pxonpixel is a dictionary with four items 'x', 'y', 'color', 'time'
        """
        # Check each pixel is valid
        assert len(pxonpixel) == 4
        assert isinstance(pxonpixel['x'], int) 
        assert 0 <= pxonpixel['x'] <= 255
        assert isinstance(pxonpixel['y'], int)
        assert 0 <= pxonpixel['y'] <= 255
        assert isinstance(pxonpixel['color'], str)
        if pxonpixel['color'][:4] == 'rgba':
            c_str = pxonpixel['color']
            #assert isinstance(eval(c_str if '__' not in c_str else 'None',{'__builtins__':None}), Color)
        assert isinstance(pxonpixel['time'], int) 
        
        # convert color to rgb triple colour
        c_str = pxonpixel['color']
        if c_str[:4] == 'rgba':
            # rgba string has already been checked so eval safely.
            c = eval(c_str)
        else:
            c = Color(c_str)
        # Color rgb returns triple of floats so convert to ints
        colour = (int(c.rgb[0]), int(c.rgb[1]), int(c.rgb[2]))
        #colour = (int(primary) for primary in c.rgb)
        # create with default class initialiser
        return cls(pxonpixel['x'], pxonpixel['y'], colour, time=pxonpixel['time'])

    @property
    def x(self):
        return self.pixeldict['x']
    @property
    def y(self):
        return self.pixeldict['y']
    @property
    def colour(self):
        return self.pixeldict['color']
    @property
    def time(self):
        return self.pixeldict['time']
    @time.setter
    def time(self, time):
        assert isinstance(time, int)
        self.pixeldict['time'] = time

    def pixelencoder(self):
        #print('pixelencoder')
        pxonpixel = copy.deepcopy(self.pixeldict)
        pxonpixel['color'] = 'rgba({:d}, {:d}, {:d}, 1)'.format(self.pixeldict['color'][0],
                                                                self.pixeldict['color'][1],
                                                                self.pixeldict['color'][2])
        #print('pxonpixel={}'.format(pxonpixel))
        return pxonpixel
    
    def __repr__(self):
        pxonpixel = copy.deepcopy(self.pixeldict)
        #print('[color]={}'.format(self.pixeldict['color']))
        pxonpixel['color'] = 'rgba({:d}, {:d}, {:d}, 1)'.format(self.pixeldict['color'][0],
                                                                self.pixeldict['color'][1],
                                                                self.pixeldict['color'][2])
        #print('pxonpixel [color]={}'.format(pxonpixel['color']))
        #print('pxonpixel={}'.format(pxonpixel))
        #print('repr of pxonpixel={}'.format(repr(pxonpixel)))
        #print('type of repr of pxonpixel={}'.format(type(repr(pxonpixel))))
        return repr(pxonpixel)

    def notrepr(self):
        return self.__repr__()


class PixelEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Pixel):
            #print('got Pixel, calling pixelencoder')
            #print('pixelencoder={}'.format(obj.pixelencoder()))
            return obj.pixelencoder()
        else:
            #print('other type=', type(obj))
            pass
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)

    
class Pxon:
    """
    This class defines and handles a PXON.
    
    PXON is a mashup of JSON and EXIF designed by Jenn Schiffer, for fun,
    with a bespoke and unique 'pxif' pixel data structure at it's core.

    pixels is list of pixel
    a pixel is a dictionary of 'x', 'y', 'color', 'time'
    x and y are positive integers
    color is an 8bit colour string in any of the following formats:
        "rgba(0, 0, 0, 1)" - decimal integers (0-255) for red, green, blue and float for alpha (0 to 1)
        "#cc9999" - '#' followed by three 2-character hex numbers for R, G, B
        "magenta" - known colour
    """
    def __init__(self, artist, software=None, imageDescription='', userComment='', copyright=None, dateTime=None, pixels=None):
        assert isinstance(artist, str)
        assert isinstance(imageDescription, str)
        assert isinstance(userComment, str)
                        
        if not software:
            self.software = 'pxon.py'
        else:
            assert isinstance(software, str)
            self.software = software
        self.artist = artist
        self.imageDescription = imageDescription
        self.userComment = userComment
        if not copyright:
            self.copyright = '{:s} {:d}'.format(artist, datetime.date.today().year)
        else:
            assert isinstance(copyright, str)
            self.copyright = copyright
        if not dateTime:
            self.dateTime = datetime.datetime.now().isoformat() # "2018-02-23T18:09:51.761"
        else:
            self.dateTime = dateTime
        if not pixels:
            self.pixels = OrderedDict()
        else:
            assert isinstance(pixels, dict)
            self.pixels = pixels

    @staticmethod
    def _convert_pixels(pxonpixels):
        """ Convert pixels to Pixel and label with time. """
        #print('in _convert_pixels')
        #print('pxonpixels', pxonpixels)
        rndpixels = {}
        for pxonpixel in pxonpixels:
            #print('pxonpixel', pxonpixel)
            # create pixel with check and conversion from pxon
            pixel = Pixel.pxon(pxonpixel)
            #print('pixel', pixel)
            # add pixel label pixel with padded time for sorting
            rndpixels[pxon_timeFormat.format(pixel.time)] = pixel
        #print('rndpixels', rndpixels)
        pixels = OrderedDict()
        #print(sorted(rndpixels.items()))
        for rkey, rpx in sorted(rndpixels.items()):
            pixels[rkey] = rpx
        #print('pixels', pixels)
        #print('leaving _convert_pixels')
        return pixels

    @staticmethod        
    def _unconvert_pixels(pixels):
        """ Unconvert Pixels to pxif pixels list of pixel dictionaries and remove time label. """
        #print('pixels={}'.format(pixels))
        pxonpixels = []
        for pxtime, pixel in sorted(pixels.items()):
            #print('pixel={}'.format(pixel))
            pxonpixels.append(pixel)
        #for pxonpixel in pxonpixels:
        #    pxonpixel.pixelencoder()
        #print('pxonpixels', pxonpixels)
        return pxonpixels
            

    @classmethod
    def load(cls, filename):
        """ Load pxon from file """
        assert os.access(filename, os.R_OK)  
            
        with open(filename, "r", encoding='utf-8') as px_file:
            new_pxon = json.load(px_file)
        #print('new_pxon', new_pxon)    
        assert len(new_pxon) == 2
        
        assert not new_pxon['exif'] is None
        exif = new_pxon['exif']
        
        # Check that any exif label that exists is a string.
        assert len(exif) <= 6
        assert exif['software'] is None or isinstance(exif['software'], str)
        assert exif['artist'] is None or isinstance(exif['artist'], str)
        assert exif['imageDescription'] is None or isinstance(exif['imageDescription'], str)
        assert exif['userComment'] is None or isinstance(exif['userComment'], str)
        assert exif['copyright'] is None or isinstance(exif['copyright'], str)
        assert exif['dateTime'] is None or isinstance(exif['dateTime'], str)
    
        # Sort after converting pixels to Pixel objects and labelling with time.
        pixels = cls._convert_pixels(new_pxon['pxif']['pixels'])
        #print('type pixels', type(pixels))
        #print('pixels', pixels)
        return cls(artist=exif['artist'], 
            software=exif['software'],
            imageDescription=exif['imageDescription'],
            userComment=exif['userComment'],
            copyright=exif['copyright'],
            dateTime=exif['dateTime'],
            pixels=pixels)
        
        
    def add(self, pixel):
        assert isinstance(pixel, Pixel)
        px_timedelta = datetime.datetime.now() - datetime.datetime.strptime(self.dateTime,
                                '%Y-%m-%dT%H:%M:%S.%f')
        # print(px_timedelta)
        # print('seconds in ms={}, ms={}'.format(px_timedelta.seconds * 1000, round(px_timedelta.microseconds / 1000)))
        pixel.time = int(px_timedelta.seconds * 1000 + round(px_timedelta.microseconds / 1000))
        # print('time label={}'.format(pxon_timeFormat.format(pixel.time)))
        self.pixels[pxon_timeFormat.format(pixel.time)] = pixel
    
    
    def save(self, filename):
        """ Save pxon to file """
        #print(filename)
        if os.path.isfile(filename):
            assert os.access(filename, os.W_OK)  

        # create exif part of pxon
        exif = OrderedDict()
        exif['software'] = self.software
        exif['artist'] = self.artist
        exif['userComment'] = self.userComment
        exif['imageDescription'] = self.imageDescription
        exif['copyright'] = self.copyright
        exif['dateTime'] = self.dateTime
        #print('exif={}'.format(exif))
        #print('encode={}'.format(json.JSONEncoder().encode(exif)))
        #print('exif json={}'.format(json.dumps(exif)))
        #create pxif part of pxon
        #print('self pixels ''pixels'' values={}'.format({'pixels': self.pixels.values()}))
        pxif = {'pixels': self._unconvert_pixels(self.pixels)}
        #print('pxif={}'.format(pxif))
        #print('pxif json={}'.format(json.dumps(pxif, sort_keys=True, cls=PixelEncoder)))
        # create pxon
        pxon = OrderedDict()
        pxon['exif'] = exif
        pxon['pxif'] = pxif
        #print('pxon=',pxon)
        #print('json=',json.dumps(pxon, cls=PixelEncoder))
            
        with open(filename, "w", encoding='utf-8') as px_file:
            #print('save pxon')
            json.dump(pxon, px_file, cls=PixelEncoder)
            
    """
        example
        {'exif': {
            'software': "pxon.py",
            'artist': "Nick Young",
            'imageDescription': "",
            'userComment': "",
            'copyright': "Nick Young 2018",
            'dateTime': "" # "2018-02-23T18:09:51.761Z"
            },
        'pxif': {
            'pixels': [
                {
                    "x": 15,
                    "y": 15,
                    "color": "rgba(0, 0, 0, 1)",
                },      
                {
                    "x": 45,
                    "y": 45,
                    "color": "#cc9999",
                },
                {
                    "x": 35,
                    "y": 25,
                    "color": "magenta",
                }
                ]
            }
        }
    """

""" 
TODO

Pxon - unconvert the Pixels
""" 

def display(pixels, quick = True):
    assert isinstance(pixels, dict)
    old_time = 0
    for px_time, pixel in sorted(pixels.items()):
        if not quick:
            time.sleep((pixel.time - old_time) / 1000)
            old_time = pixel.time
        print('s.set_pixel({:d}, {:d}, {})'.format(pixel.x, pixel.y, pixel.colour))
        # s.set_pixel(pixel.x, pixel.y, pixel.color)


def test():
    
    # new
    print('new')
    px = Pxon(artist="Nick Young")
    print('display pixels at default speed, quick')
    display(px.pixels)

    # add pixels
    print('add pixel 0')
    pixel0 = Pixel(1, 2, (255, 0, 0))
    px.add(pixel0)
    print('display after add 0')
    display(px.pixels)

    time.sleep(2.5)

    print('add pixel 1')
    pixel1 = Pixel(2, 1, (0, 255, 0))
    px.add(pixel1)
    print('display after add 1')
    display(px.pixels)

    # show slowly
    print('display pixels in time')
    display(px.pixels, False)

    #save
    print('save')
    px.save("gallery.pxon") 
    print('display after save')
    display(px.pixels)

    # reset
    print('reset to new')
    px = Pxon(artist="Nick Young")
    print('display after reset')
    display(px.pixels)

    # reload
    print('load')
    px = Pxon.load("gallery.pxon")
    display(px.pixels)

    # show slowly
    print('display pixels in time')
    display(px.pixels, False)

"""
def json_test():
    example = {'exif': {
            'software': "pxon.py",
            'artist': "Nick Young",
            'imageDescription': "drawing a blank",
            'userComment': "Some comment",
            'copyright': "Nick Young 2018",
            'dateTime': "2018-02-23T18:09:51.761"
            },
        'pxif': {
            'pixels': [
                {
                "x": 15,
                "y": 15,
                "color": "rgba(0, 0, 0, 1)",
                "time": 0,
                },      
                {
                "x": 45,
                "y": 45,
                "color": "#cc9999",
                "time": 500,
                },
                {
                "x": 35,
                "y": 25,
                "color": "magenta",
                "time":1000
                },
                Pixel(10,10,(0,0,0),1500)
                ]
            }
        }
    
    print(example)
    print('json dumps with PixelEncoder',json.dumps(example, cls=PixelEncoder))
"""

if __name__ == "__main__":
    #json_test()
    test()
    
