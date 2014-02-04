import urllib2
import fcntl
import os
from subprocess import Popen, PIPE

import requests
from youtube_dl import YoutubeDL
from flask import Flask, Response, request, abort, render_template
from mpd import MPDClient

app = Flask(__name__)

ydl = YoutubeDL({
    'forceurl': True,
    'quiet': True
})

ydl.add_default_info_extractors()

def get_info(url):
    return ydl.extract_info(url, download=False)

@app.route('/stream')
def stream():
    if not request.args.has_key('v'):
        abort(404)
    vurl = request.args.get('v')
    if vurl.startswith('http') or vurl.startswith('www'):
        vurl = urllib2.unquote(vurl)
    else:
        vurl = 'http://www.youtube.com/watch?v=' + request.args.get('v')
    r = requests.get(get_info(vurl)['url'], stream=True)
    if r.status_code == 200:
        p = Popen(["ffmpeg", "-i", "-", "-f", "mp3", "-strict", "-2", "-"],
                  stdin=PIPE, stdout=PIPE)
        fcntl.fcntl(p.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        def generate():
            for chunk in r.iter_content(1024):
                p.stdin.write(chunk)
                try:
                    output = p.stdout.read(1024)
                    if output == '': return
                    yield output
                except IOError as e:
                    pass
    return Response(generate())

@app.route('/', methods=['GET', 'POST'])
def index():
    url = request.form.get('url', '')
    if url:
        mpd = MPDClient()
        mpd.connect(host="localhost", port="6600")
        mpd.add("http://localhost:8000/stream?t=%s&v=%s" % (urllib2.quote(get_info(url)['title']), urllib2.quote(url)))
    return render_template('index.html', url=url)
