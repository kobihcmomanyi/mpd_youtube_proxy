import urllib2, io, fcntl, os, time
from subprocess import Popen, PIPE

from youtube_dl import YoutubeDL
from flask import Flask, Response, request, abort, render_template, stream_with_context
from mpd import MPDClient

app = Flask(__name__)
app.config["DEBUG"] = True

ydl = YoutubeDL({
    'forceurl': True,
    'quiet': True
})

ydl.add_default_info_extractors()

def get_info(url):
    return ydl.extract_info(url, download=False)

def get_url(info):
    for format in info['formats']:
        if format['format_id'] == u'140':
            return format['url']
    return info['url']

@app.route('/stream')
def stream():
    if not request.args.has_key('v'):
        abort(404)
    vurl = request.args.get('v')
    if vurl.startswith('http') or vurl.startswith('www'):
        vurl = urllib2.unquote(vurl)
    else:
        vurl = 'http://www.youtube.com/watch?v=' + request.args.get('v')

    yt_info = get_info(vurl)

    def generate():
        p = Popen(["ffmpeg", "-i", get_url(yt_info), "-f", "mp3", "-vn", "-ab", "256k", "-strict", "-2", "-"],
                  stdout=PIPE)
        output = p.stdout.read(256*128)
        while output:
            yield output
            output = p.stdout.read(256*128)
        p.stdout.close()
        p.wait()
    return Response(stream_with_context(generate()),
                    headers={
                        "Content-Type": "audio/mp3",
                        "icy-name": yt_info['title'],
                        "icy-bitrate": "256",
                        "ice-audio-info": "bitrate=256",
                        "Cache-Control": "no-cache"})

@app.route('/', methods=['GET', 'POST'])
def index():
    url = request.form.get('url', '')
    if url:
        mpd = MPDClient()
        mpd.connect(host="localhost", port="6600")
        mpd.add("http://localhost:8000/stream?v=%s" % (urllib2.quote(url),))
    return render_template('index.html', url=url)