from __future__ import unicode_literals, print_function
import spacy
from jinja2 import Template
import json

def convert(seconds): 
  seconds = seconds % (24 * 3600) 
  hour = seconds // 3600
  seconds %= 3600
  minutes = seconds // 60
  seconds %= 60
    
  return "%d:%02d:%02d" % (hour, minutes, seconds) 

def vid_report(data, video_id, output_file, html_template='report.jinja2'):
  # iterate across each word
  # if the word has the first letter capitalized
  # the sentence length is currently greater than 1
  # add period, timestamp in the other pandas dataframe column
  # if a word has a period, make a new sentence
  nlp = spacy.load("en_core_web_lg")
  raw_text = data.get('text')
  words = data.get('words')
  nlp.add_pipe(nlp.create_pipe('sentencizer')) # updated
  doc = nlp(raw_text)
  sentences = [sent.string.strip() for sent in doc.sents]
  total_words = 0
  lines = []
  for sentence in sentences:
    sent_num_words = len(sentence.split())
    words_in_sent = words[total_words:total_words+sent_num_words]
    total_words += sent_num_words
    start_time = words_in_sent[0].get('start')
    end_time = words_in_sent[-1].get('end')
    start_time_label = convert(start_time / 1000)
    end_time_label = convert(end_time / 1000)
    curr_sent = {
      "text": sentence,
      "start": int(start_time / 1000),
      "start_label": start_time_label,
      "end": int(end_time / 1000),
      "end_label": end_time_label
    }
    sent_doc = nlp(sentence)
    curr_sent["ents"] = list(sent_doc.ents)
    curr_sent["sentiment"] = sent_doc.sentiment
    lines.append(curr_sent)

  with open(html_template) as file_:
    template = Template(file_.read())

  options = dict(Version="2.0.0", LINES=lines, VIDEO_ID=video_id)
  renderer_template = template.render(**options)
  with open(output_file, "w", errors="ignore") as f:
      f.write(renderer_template)
  pass

def is_proper_noun(word):
  pass


if __name__ == "__main__":
  # read data from json file
  with open('data.json') as f:
    data = json.load(f)
  vid_report(data, "BaW_jenozKc")
  pass