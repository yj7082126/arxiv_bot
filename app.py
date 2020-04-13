import os
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
def send_arxiv(user_id: str, channel: str):
    arxivParser = ArxivParser(channel)
    arxivParser.parse_from_arxiv()
    message = arxivParser.create_json()
    response = slack_web_client.chat_postMessage(**message)
    assert response["ok"]

@slack_events_adapter.on("message")
def message(payload):
    event = payload.get("event", {})

    channel_id = event.get("channel")
    user_id = event.get("user")
    text = event.get("text")

    if text and text.lower() == "search":
        return send_arxiv(user_id, channel_id)

if __name__ == "__main__":
    ssl_context = ssl_lib.create_default_context(cafile=certifi.where())
    app.run()