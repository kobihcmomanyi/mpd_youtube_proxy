import urllib2, io, fcntl, os, time
from subprocess import Popen, PIPE

from youtube_dl import YoutubeDL
from flask import Flask, Response, request, abort, render_template, stream_with_context
from mpd import MPDClient

app = Flask(__name__)

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

    def generate():
        p = Popen(["ffmpeg", "-i", get_url(get_info(vurl)), "-f", "mp3", "-ab", "256k", "-strict", "-2", "-"],
                  stdout=PIPE)
        #fcntl.fcntl(p.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        while True:
            try:
                # Send output at slightly more than 256k (the encoding bitrate)
                # to avoid overfilling buffers or something...
                time.sleep(0.99)
                output = p.stdout.read(256*128)
                if not output:
                    print "Done"
                    return
                yield output
            except IOError as e:
                time.sleep(0.01)
    return Response(stream_with_context(generate()))

@app.route('/', methods=['GET', 'POST'])
def index():
    url = request.form.get('url', '')
    if url:
        mpd = MPDClient()
        mpd.connect(host="localhost", port="6600")
        mpd.add("http://localhost:8000/stream?t=%s&v=%s" % (urllib2.quote(get_info(url)['title']), urllib2.quote(url)))
        print
    return render_template('index.html', url=url)