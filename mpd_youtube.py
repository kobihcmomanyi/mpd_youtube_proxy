import urllib2
import os
from subprocess import Popen, PIPE

from youtube_dl import YoutubeDL
from flask import Flask, Response, request, abort, render_template, stream_with_context, flash, url_for, make_response
from werkzeug.utils import secure_filename
from mpd import MPDClient

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'not so secret'
app.config['MPD_HOST'] = "localhost"
app.config['MPD_PORT'] = "6600"
app.config['MPD_PASSWORD'] = ""
app.config['SERVER_URL'] = 'http://localhost'
app.config['DOWNLOAD_FOLDER'] = '/tmp'

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

    if app.config['DOWNLOAD_FOLDER']:
        cached_file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], secure_filename(yt_info['title'] + '.mp3'))
        if os.path.exists(cached_file_path):
            print "Serving from cache."
            return make_response(open(cached_file_path, 'rb').read())

    def generate():
        cache_file = None
        cache_filename = os.path.join(app.config['DOWNLOAD_FOLDER'], secure_filename(yt_info['title'] + '.mp3'))
        try:
            if app.config['DOWNLOAD_FOLDER']:
                cache_file = open(cache_filename + '.part', 'wb')
            p = Popen(["ffmpeg", "-i", get_url(yt_info), "-f", "mp3", "-vn", "-ab", "256k", "-strict", "-2", "-"],
                      stdout=PIPE)
            output = p.stdout.read(256*128)
            while output:
                if cache_file:
                    cache_file.write(output)
                yield output
                output = p.stdout.read(256*128)
            if cache_file:
                cache_file.close()
                os.rename(cache_filename + '.part', cache_filename)
        finally:
            if cache_file:
                cache_file.close()
            p.stdout.close()
            p.wait()
    return Response(stream_with_context(generate()),
                    headers={
                        "Content-Type": "audio/mp3",
                        "icy-name": yt_info['title'].encode('latin-1', 'ignore'),
                        "icy-bitrate": "256",
                        "ice-audio-info": "bitrate=256",
                        "Cache-Control": "no-cache"})

@app.route('/', methods=['GET', 'POST'])
def index():
    url = request.form.get('url', '')
    try:
        mpd = MPDClient()
        mpd.connect(host=app.config["MPD_HOST"], port=app.config["MPD_PORT"])
        if app.config["MPD_PASSWORD"]:
            mpd.password(app.config["MPD_PASSWORD"])
        if url:
            try:
                yt_info = get_info(url)
                if not 'title' in yt_info:
                    flash("Could not find the video", "danger")
                else:
                    mpd.add(url_for('stream', _external=True) + "?t=%s&v=%s" % (urllib2.quote(secure_filename(yt_info['title'])), urllib2.quote(url)))
                    flash("Added '" + yt_info['title'] + "' to the MPD queue.", "success")
            except Exception as e:
                flash("Could not add video to MPD: " + str(e), "danger")
    except Exception as e:
        flash("Could not connect to MPD. " + str(e), "danger")
    return render_template('index.html', url=url, )