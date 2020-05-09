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
def send_arxiv(user_id, channel, categories = ["cs.CL", "cs.CV"],
               keywords = [], conferences = [], is_compact = False,
               max_results = 5):
    arxivParser = ArxivParser(channel, is_compact)
    if len(categories) == 0:
        categories = ["cs.CL", "cs.CV"]
    else:
        categories = categories

    if len(max_results) != 1:
        max_results = 5
    else:
        max_results = max_results[0]

    arxivParser.parse_from_arxiv(categories, keywords, conferences, keywords_or=True)
    message = arxivParser.create_json(max_results)
    response = slack_web_client.chat_postMessage(**message)
    assert response["ok"]

def send_help(user_id, channel):
    arxivParser = ArxivParser(channel, False)
    message = arxivParser.create_help_message()
    response = slack_web_client.chat_postMessage(**message)
    assert response["ok"]

@slack_events_adapter.on("message")
def message(payload):
    event = payload.get("event", {})

    channel_id = event.get("channel")
    user_id = event.get("user")
    text = event.get("text")

    print('Channel_id: %s'%(channel_id))

    if text:
        text = text.split()
        if text[0] == "help":
            return send_help(user_id, channel_id)
        elif ((text[0] == "search") or (text[0] == "compact_search")):
            categories = [y for y in text[1:] if "." in y]
            categories = [y.split('|')[1][:-1] if "|" in y else y for y in categories]
            categories = [y for y in categories if y[re.search("\.", y).start()-1].islower()
                          and y[re.search("\.", y).start()+1].isupper()]
            keywords = [y for y in text[1:] if y.islower()]
            conferences = [y for y in text[1:] if y.isupper()]
            is_compact = False if text[0] == "search" else True
            max_results = [int(y) for y in text[1:] if y.isnumeric()]

            return send_arxiv(user_id, channel_id, categories, keywords,
                              conferences, is_compact, max_results)

if __name__ == "__main__":
    ssl_context = ssl_lib.create_default_context(cafile=certifi.where())
    app.run()