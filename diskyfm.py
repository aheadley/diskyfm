#!/usr/bin/env python

import subprocess
import random
import json
import urllib2
import itertools
import os.path
import time
import hashlib
from functools import wraps
try:
    from bs4 import BeautifulSoup
except ImportError:
    try:
        from BeautifulSoup import BeautifulSoup
    except ImportError:
        BeautifulSoup = None

class InvalidMode(Exception): pass
class InvalidStream(Exception): pass
class StreamError(Exception): pass
class ConfigError(Exception): pass

MODES = ['di', 'sky']

QUALITIES = {
    'mp3': [
        'premium_high',         #256k
        'premium',              #128k
        'public3',              #96k
    ],
    'aac': [
        'premium_medium',       #64k
        'premium_low',          #40k
        'public2',              #40k
    ],
    # 'wma': [
    #    'premium_wma',          #128k
    #    'premium_wma_low',      #64k
    #    'public5',              #40k
    # ],
}

DEFAULT_PLAYER = 'mplayer -really-quiet {stream_url}'

def identify_stream(wrapped):
    @wraps(wrapped)
    def wrapper(self, stream=None, **kwargs):
        if stream is None:
            stream = self._identify_stream(**kwargs)
        return wrapped(self, stream)
    return wrapper

def identify_stream_and_mode(wrapped):
    @wraps(wrapped)
    @identify_stream
    def wrapper(self, stream, mode=None):
        if mode is None:
            mode = self._identify_stream_mode(stream)
        return wrapped(self, stream, mode)
    return wrapper

class AudioAddictSite(object):
    _mode = None
    player = None
    quality = None

    STREAM_CACHE_TTL = 86400

    def __init__(self, mode='all', quality='public3',
            player=DEFAULT_PLAYER, **kwargs):
        self._mode = mode
        self.quality = quality
        self.player = player
        self._config = kwargs
        self._soups = dict((m, None) for m in MODES)

    @property
    def stream_list(self):
        if self._mode == 'all':
            return list(itertools.chain.from_iterable(
                self._get_stream_list(mode) for mode in MODES))
        else:
            return self._get_stream_list(self._mode)

    @identify_stream_and_mode
    def get_stream_icon(self, stream, mode):
        if self._soups[mode] is None:
            icons_url = 'http://{mode}.fm/'.format(mode=mode)
            if BeautifulSoup is not None:
                self._soups[mode] = BeautifulSoup(urllib2.urlopen(icons_url))
            else:
                raise Exception('Icon support requires the BeautifulSoup module')
        soup = self._soups[mode]
        stream_icon = soup.find('img', title=stream['name']).get('src', '')
        return stream_icon

    @identify_stream
    def play_stream(self, stream):
        stream_url = self.get_stream_url(stream=stream)
        try:
            with open('/dev/null', 'w') as dev_null:
                return subprocess.call(self.player.format(stream_url=stream_url),
                    stdin=sys.stdin,
                    stdout=sys.stdout,
                    stderr=dev_null,
                    shell=True)
        except TypeError as err:
            raise StreamError(err)

    @identify_stream
    def get_stream_url(self, stream):
        pls_url = stream['playlist']
        if self.quality.startswith('premium'):
            try:
                pls_url = '{url}?{auth_key}'.format(
                    url=pls_url,
                    auth_key=self._config['auth_key'])
            except KeyError:
                raise ConfigError('Premium quality stations require auth_key')
        return random.choice([line.strip().split('=')[1] \
            for line in urllib2.urlopen(pls_url).read().strip().split('\n') \
                if '=' in line and line.startswith('File')])

    def _get_stream_list(self, mode):
        if mode in MODES:
            url = 'http://listen.{mode}.fm/{quality}/'.format(
                mode=mode,
                quality=self.quality)
            with open(self._get_stream_list_cache_file(url), 'r') as strm_cache:
                data = json.load(strm_cache)
            return data
        else:
            raise InvalidMode(mode)

    def _get_stream_list_cache_file(self, stream_list_url):
        filename = '/var/tmp/diskyfm_stream_list_{url_hash}'.format(
            url_hash=hashlib.md5(stream_list_url).hexdigest())
        if not os.path.exists(filename) or \
                time.time() - os.path.getmtime(filename) > self.STREAM_CACHE_TTL:
            with open(filename, 'w') as strm_cache:
                strm_cache.write(urllib2.urlopen(stream_list_url).read())
        return filename

    def _identify_stream_mode(self, stream):
        for (m, s) in ((m, s) for m in MODES for s in self._get_stream_list(m)):
            if stream == s:
                return m
        else:
            raise InvalidStream(stream)

    def _identify_stream(self, mode=None, **kwargs):
        if not len(kwargs):
            raise InvalidStream()
        if mode is None:
            stream_list = self.stream_list
        else:
            stream_list = (s for m in MODES for s in self._get_stream_list(m))
        for stream in stream_list:
            if all(stream[key] == value for (key, value) in kwargs.iteritems()):
                return stream
        else:
            raise InvalidStream(kwargs)

if __name__ == '__main__':
    import sys
    import optparse
    import os.path
    import ConfigParser

    def get_options():
        parser = optparse.OptionParser()
        parser.add_option('-C', '--config-file', dest='config_file',
            help='Use an alternate config file', metavar='FILE')
        parser.add_option('-P', '--player', dest='player',
            help='Use an alternate audio player', metavar='PLAYER')
        parser.add_option('-m', '--mode', dest='mode', type='choice',
            choices=MODES+['all'])
        parser.add_option('-q', '--quality', type='choice',
            choices=[x for k in QUALITIES.values() for x in k], help='Set the stream quality')
        parser.add_option('-a', '--auth-key',
            help='Set the auth key for premium streams')
        parser.add_option('-l', '--list-streams', action='store_true',
            help='List the available streams')
        parser.add_option('-u', '--show-url', action='store_true',
            help='Don\'t play the stream, just show the URL')
        return parser.parse_args()

    def get_config(config_file):
        defaults = {
            'player': DEFAULT_PLAYER,
            'quality': 'public3',
            'mode': 'all',
        }
        parser = ConfigParser.RawConfigParser(defaults)
        try:
            with open(config_file, 'r') as cf:
                parser.readfp(cf, config_file)
        except OSError:
            pass
        return dict(parser.items('global'))

    (opts, args) = get_options()
    opts = dict((k,v) for (k,v) in vars(opts).items() if v is not None)
    try:
        config = get_config(opts['config_file'])
    except KeyError:
        config = get_config(os.path.expanduser('~/.diskyfmrc'))
    config.update(opts)

    streamer = AudioAddictSite(**config)
    if 'list_streams' in config:
        stream_list = streamer.stream_list
        stream_key_width = max(len(s['key']) for s in stream_list)
        print '\n'.join('{s[key]: <{width}} -- {s[name]}: {s[description]}'.format(
            width=stream_key_width, s=s) for s in stream_list)
    else:
        try:
            stream_key = args[0]
        except IndexError:
            stream_key = config['default_stream_key']
        if 'show_url' in config:
            print streamer.get_stream_url(key=stream_key)
        else:
            print 'Streaming {stream_key} @ {quality}...'.format(
                stream_key=stream_key,
                quality=streamer.quality)
            streamer.play_stream(key=stream_key)
