MPD YouTube Stream Proxy
========================

This program acts as HTTP streaming server and serves the audio stream of a given
YouTube video as mp3 stream. The video is converted to mp3 on the fly using ffmpeg.

A small web client can be used to add youtube links to MPD's play queue.

Requirements
------------

* Python 3
* [ffmpeg](http://www.ffmpeg.org/)
* [lame](http://lame.sourceforge.net/)

Install
-------

Adjust the app.config settings at the beginning of mpd_youtube.py

In the folder run:

    > virtualenv myenv
    > source myenv/bin/activate
    > pip install flask python-mpd2 youtube-dl gunicorn
    > gunicorn -w 10 -b 0.0.0.0 -t 999999999 mpd_youtube:app

Navigate to [http://localhost:8000](http://localhost:8000) (gunicorn default) and
enter a youtube URL or ID (see /watch?v=<id>). The application adds the required
proxied URL to MPD.

Attributions
------------

static/sound.png by http://brsev.com/
