diskyfm
=======

Simple CLI wrapper for listening to DI.FM and Sky.FM music streams.

Info
----

This wrapper was created because I was tired of manually finding the URL for
DI.FM streams to copy and paste into mplayer. Currently it supports both free
and premium (if you have an account) streams on both the DI.FM and Sky.FM sites.

Usage
-----

It's as simple as:

    $ diskyfm <stream_key>

where `stream_key` is the short code for the various streams. You can see a list
of streams with the `-l` option. Other options are also available for selecting
the stream quality, which streams are available (mode), and the backend media
player. Use `-h` to see the full help output.

Additionally, you can set options in a `~/.diskyfmrc` config file to avoid
having to pass them every time. See the `diskyfmrc-example` file for the
available options.

The auth_key required for premium quality streams currently has to be found
manually (I hope to add support for logging in and finding it automatically at
some point). You can find it on the site by logging in and looking at the link
for any of the playlists. It will look something like
`http://listen.di.fm/premium_high/vocalchillout.pls?xxxxxxxxxxxxxxx` . The part
after the `?` (question mark) is the auth_key.

_A note on the `mode` option:_ The default is to glob both DI.FM and Sky.FM sites
together so you can just pick a station from either site and it will
_just work_(TM). However, the `mode` option will let you limit your choices to
one site or the other if you want to (for whatever reason). Valid modes are `di`,
`sky`, or `all`.

Installation
------------

Since it's just a simple script there is no real installation process, but you
can throw it in `/usr/local/bin/` (or any other place in `$PATH`) if you want
to avoid typing out the full path to the script every time. The default backend
media player is mplayer, but that can be changed via the `-P` option or `player`
config value. Beyond that, the only real dependancy is Python 2.6 or higher.

Examples
--------

Get the list of DI.FM stations with the word "vocal" in them:

    $ diskyfm -m di -l | grep vocal
    vocalchillout      -- Vocal Chillout: Enjoy the relaxing vocal sounds of Ibiza chillout
    vocaltrance        -- Vocal Trance: A fusion of trance, dance, and chilling vocals together!
    classicvocaltrance -- Classic Vocal Trance: Classic sounds of Vocal Trance

Play the Vocal Trance station at 64k AAC quality (see the top of the `diskyfm`
file for the available quality selections):

    $ diskyfm -q premium_medium vocaltrance
