import os

from urllib.parse import unquote, quote
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
app.config['DOWNLOAD_FOLDER'] = '/mnt/data/Music/youtube'


def get_info(url):
    ydl = YoutubeDL({
        'forceurl': True,
        'quiet': True
    })

    ydl.add_default_info_extractors()
    return ydl.extract_info(url, download=False)


def get_url(info):
    for fmt in info['formats']:
        if fmt['format_id'] == u'141':  # prefer 141 = m4a [256k] (DASH Audio)
            return fmt['url']
    for fmt in info['formats']:
        if fmt['format_id'] == u'140':  # prefer 140 = m4a [128k] (DASH Audio)
            return fmt['url']
    return info['url']  # otherwise use the default


@app.route('/stream')
def stream():
    if not 'v' in request.args:
        abort(404)
    video_url = request.args.get('v')
    if video_url.startswith('http') or video_url.startswith('www'):
        video_url = unquote(video_url)
    else:
        video_url = 'http://www.youtube.com/watch?v=' + request.args.get('v')

    yt_info = get_info(video_url)

    if app.config['DOWNLOAD_FOLDER']:
        cached_file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], secure_filename(yt_info['title'] + '.mp3'))
        if os.path.exists(cached_file_path):
            return make_response(open(cached_file_path, 'rb').read())

    def generate():
        cache_file, p = None, None
        cache_filename = os.path.join(app.config['DOWNLOAD_FOLDER'], secure_filename(yt_info['title'] + '.mp3'))
        try:
            if app.config['DOWNLOAD_FOLDER']:
                cache_file = open(cache_filename + '.part', 'wb')
            p = Popen(["ffmpeg", "-i", get_url(yt_info), "-f", "mp3", "-vn", "-ab", "256k", "-strict", "-2", "-"],
                      stdout=PIPE)
            output = p.stdout.read(256 * 128)
            while output:
                if cache_file:
                    cache_file.write(bytearray(output))
                yield output
                output = p.stdout.read(256 * 128)
            if cache_file:
                cache_file.close()
                Popen(['lame', '--mp3input', '-h', '-b', '256', '--add-id3v2', '--tt', yt_info['title'],
                       cache_filename + '.part', cache_filename]).wait()
                os.remove(cache_filename + '.part')
        finally:
            if cache_file:
                cache_file.close()
            if p:
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
                    mpd.add(url_for('stream', _external=True) + "?t=%s&v=%s" % (
                        quote(secure_filename(yt_info['title'])), quote(url)))
                    flash("Added '" + yt_info['title'] + "' to the MPD queue.", "success")
            except Exception as e:
                flash("Could not add video to MPD: " + str(e), "danger")
    except Exception as e:
        flash("Could not connect to MPD. " + str(e), "danger")
    return render_template('index.html', url=url, )

