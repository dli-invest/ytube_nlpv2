from __future__ import unicode_literals
import youtube_dl
import argparse
import requests
import os
from polling import TimeoutException, poll
from gen_report import vid_report
import json
import datetime

class MyLogger(object):
    def debug(self, msg):
        print(msg)
        pass

    def warning(self, msg):
        print(msg)
        pass

    def error(self, msg):
        print(msg)


def is_transcript_ready(response):
    data = response.json()
    status = data.get('status')
    return status == 'completed'

def transcript_mp3(filename):
  # upload audio file
  api_token = os.getenv("ASSEMBLY_API_TOKEN")
  headers = {'authorization': api_token}
  response = requests.post('https://api.assemblyai.com/v2/upload',
                          headers=headers,
                          data=read_file(filename))
  data = response.json()
  audio_url = data.get('upload_url')
  transcript_resp = upload_video(audio_url)

  # get the transcript id used to poll
  transcript_id = transcript_resp.get('id')
  endpoint = "https://api.assemblyai.com/v2/transcript/" + transcript_id

  headers = {
      "authorization": api_token,
  }

  response = requests.get(endpoint, headers=headers)
  transcript = None
  try:
      transcript = poll(
        lambda: requests.get(endpoint, headers=headers),
        check_success=is_transcript_ready,
        timeout=15*1000,
        step=10
      )
      # save data to examine
      text_data = transcript.json()
      text_file = filename + '.json'
      # just use existing filename with appended json extension
      with open(text_file, 'w') as fp:
        json.dump(text_data, fp)
      return text_data

  except TimeoutException as tee:
      print("Value was not registered")
      print(tee)
      print(transcript)
      # terminate here, taking longer to annotate video
      raise Exception('FAILED TO ANNOTATE VIDEO IN TIME')
  
def upload_video(audio_url):
  endpoint = "https://api.assemblyai.com/v2/transcript"

  json = {
    "audio_url": audio_url
  }
  api_token = os.getenv("ASSEMBLY_API_TOKEN")
  headers = {
      "authorization": api_token,
      "content-type": "application/json"
  }

  response = requests.post(endpoint, json=json, headers=headers)
  transcript_resp = response.json()
  return transcript_resp

def read_file(filename, chunk_size=5242880):
    with open(filename, 'rb') as _file:
        while True:
            data = _file.read(chunk_size)
            if not data:
                break
            yield data

def main(video_id):
    # video finished downloading
    def hook_dl_finished(d):
        if d['status'] == 'finished':
            print('Done downloading, now converting ...')
            filename=d['filename']
            # send video to assemblyAI
            output_file = os.path.splitext(filename)[0]+'.html'
            text_data = transcript_mp3(filename)
            print('Transcript Complete, generating report ...')
            report_name = vid_report(text_data, video_id, output_file)
            # send data to nlp

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'recordings/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'logger': MyLogger(),
        'progress_hooks': [hook_dl_finished]
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        # ydl.download(['https://www.youtube.com/watch?v=GwrN5anVK5A'])
        video_url = 'https://www.youtube.com/watch?v=' + video_id
        ydl.download([video_url])

if __name__ == "__main__":
    begin_time = datetime.datetime.now()
    if os.getenv('ASSEMBLY_API_TOKEN') == None:
        raise Exception('NEED ASSEMBLY_API_TOKEN')
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--video_id', '-id', help='video id', default='BaW_jenozKc')
    args = parser.parse_args()
    video_id = args.video_id
    # make sure assemblyAI token is valid
    main(video_id)
    print("execution time: -----")
    print(datetime.datetime.now() - begin_time)
