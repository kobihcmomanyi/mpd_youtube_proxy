from youtube_dl import YoutubeDL
from flask import Flask, Response, request, abort
import requests, time
from subprocess import Popen, PIPE
import fcntl, os
import tornado

app = Flask(__name__)

ydl = YoutubeDL({
    'forceurl': True,
    'quiet': True
})

ydl.add_default_info_extractors()

def get_url(url):
    return ydl.extract_info(url, download=False)['url']
    #for format in info['formats']:
    #    if format['format_id'] == u'22':
    #        return format['url']

import urllib2
@app.route('/')
def stream():
    if not request.args.has_key('v'):
        abort(404)
    vurl = request.args.get('v')
    if vurl.startswith('http'):
        vurl = urllib2.unquote(vurl)
    else:
        vurl = 'http://www.youtube.com/watch?v=' + request.args.get('v')
    r = requests.get(get_url(vurl), stream=True)
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

app.run(host='0.0.0.0', debug=True)
