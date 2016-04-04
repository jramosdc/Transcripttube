#!/usr/bin/env python2.7
# encoding=utf-8
from __future__ import unicode_literals
import youtube_dl
import re, os
import requests
import json
from flask import Flask
from flask import request
from flask import render_template
from celery import Celery

application = app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

@celery.task
##extract video id from youtube url
def youtube_url_validation(url):
    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')

    youtube_regex_match = re.match(youtube_regex, url)
    if youtube_regex_match:
        return youtube_regex_match.group(6)

    return youtube_regex_match

@app.route('/')
def my_form():
    return render_template("input.html")

@app.route('/', methods=['POST'])
def processyoutube():

    video_url = request.form['video_url']
    video_lan = request.form['video_lan']
 ##youtube-dl options
    ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': 'temp/%(id)s.%(ext)s',
    'audioformat' : 'wav',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'wav',
        'preferredquality': '192',
    }]}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=True)
        video_title = info_dict.get('title', None)
      ##video_url = info_dict.get("url", None)

    
    ##extract id to use in filename
    video_id = youtube_url_validation(video_url)
    ##build the filename for speech recognition
    directory='temp/'
    filename=''.join([directory,video_id,'.wav'])
    ##speech recognition
    
    model ='_'.join([video_lan,'BroadbandModel'])

    url = ''.join(['https://stream.watsonplatform.net/speech-to-text/api/v1/recognize?continuous=true&model=', model])

    username = '25ce03dd-7fbe-4b9e-8f3f-29a434ed9fe9'

    password = 'QxdU3aIayU7X'

    headers={'Content-Type': 'audio/wav'}

    audio = open(filename, 'rb')

    r = requests.post(url, data=audio, headers=headers, auth=(username, password))

    os.remove(filename)

    data= r.json()
    
    return render_template("results.html",data=data,video_id=video_id)


if __name__ == '__main__':
    application.debug = True
    application.run()
