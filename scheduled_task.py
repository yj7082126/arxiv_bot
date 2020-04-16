import os
import re
import logging
from flask import Flask
from slack import WebClient
from slackeventsapi import SlackEventAdapter
import ssl as ssl_lib
import certifi
from arxiv_parser import ArxivParser

#%%
slack_web_client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])
channel = os.environ['CHANNEL_ID']
#%%
arxivParser = ArxivParser(channel)

arxivParser.parse_from_arxiv(["cs.CL", "cs.CV"], [], [])
message = arxivParser.create_json(True, 5)
response = slack_web_client.chat_postMessage(**message)