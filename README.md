MPD YouTube Stream Proxy
========================

This proxy acts as HTTP server and serves the audio stream of a given
YouTube video as mp3 stream. The video is converted to mp3 on the fly
using ffmpeg.

Install
-------

In the folder run:

    > virtualenv2 myenv
    > source myenv/bin/activate
    > pip install flask python-mpd2 youtube-dl gunicorn
    > gunicorn mpd_youtube:app

Navigate to http://localhost:8000 (gunicorn default) and enter a youtube URL or
ID (see /watch?v=<id>). The application adds the required proxied URL to MPD.