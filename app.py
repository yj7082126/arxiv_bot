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
app = Flask(__name__)
slack_events_adapter = SlackEventAdapter(os.environ['SLACK_SIGNING_SECRET'], "/slack/events", app)
slack_web_client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])

#%%
def send_arxiv(user_id, channel, categories = ["cs.CL", "cs.CV"], keywords = [], is_compact = False):
    arxivParser = ArxivParser(channel)
    arxivParser.parse_from_arxiv(categories, keywords)
    message = arxivParser.create_json(is_compact)
    response = slack_web_client.chat_postMessage(**message)
    assert response["ok"]
    
def send_help(user_id, channel):
    arxivParser = ArxivParser(channel)
    message = arxivParser.create_help_message()
    response = slack_web_client.chat_postMessage(**message)
    assert response["ok"]

@slack_events_adapter.on("message")
def message(payload):
    event = payload.get("event", {})

    channel_id = event.get("channel")
    user_id = event.get("user")
    text = event.get("text")

    if text:
        text = text.split()
        if text[0] == "search":
            categories = [y for y in text[1:] 
                          if "." in y and y[re.search("\.", y).start()-1].islower() 
                          and y[re.search("\.", y).start()+1].isupper()]
            keywords = [y for y in text[1:] if y.islower()]
            return send_arxiv(user_id, channel_id, categories, keywords, False)
        elif text[0] == "compact_search":
            categories = [y for y in text[1:] 
                          if "." in y and y[re.search("\.", y).start()-1].islower() 
                          and y[re.search("\.", y).start()+1].isupper()]
            keywords = [y for y in text[1:] if y.islower()]
            return send_arxiv(user_id, channel_id, categories, keywords, True)
        elif text[0] == "help":
            return send_help(user_id, channel_id)

if __name__ == "__main__":
    ssl_context = ssl_lib.create_default_context(cafile=certifi.where())
    app.run()