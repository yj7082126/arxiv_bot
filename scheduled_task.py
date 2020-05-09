#!/usr/bin/python3.6
import os
from slack import WebClient
from arxiv_parser import ArxivParser

#%%
slack_web_client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])
channel = os.environ['CHANNEL_ID']
#%%
arxivParser = ArxivParser(channel, True)

arxivParser.parse_from_arxiv(["cs.CL", "cs.CV"], ['tacotron', 'face', 'facial',
           'speech', 'keypoint', 'deepfake'], [], keywords_or=True)
message = arxivParser.create_json(5)
response = slack_web_client.chat_postMessage(**message)