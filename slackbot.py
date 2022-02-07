from slackeventsapi import SlackEventAdapter
from slack_sdk.web import WebClient
from slack_sdk.errors import SlackApiError
import re
import random
import os

# Grab token from environment variables
slack_signing_secret = os.environ["SLACK_SIGNING_SECRET"]
slack_bot_token = os.environ["SLACK_BOT_TOKEN"]

# create Slack event adapter and web client
slack_events_adapter = SlackEventAdapter(slack_signing_secret, endpoint="/yubisnooze/")
slack_client = WebClient(slack_bot_token)

# responses and reactions (without :'s)
responses = [
    "Aaaahchoo!",
    "Hayfever really is bad this time of year",
    "*tissues*",
    "No one will know I just yubisneezed",
]
response_reaction = ["yubisneeze", "safety_pin", "safety_vest", "closed_lock_with_key"]


# Listen for all messages
@slack_events_adapter.on("message")
def handle_message(event_data):

    # Fetch event information
    event_details = event_data["event"]

    # Fetch specific event details
    event_type = event_details.get("type")
    event_subtype = event_details.get("subtype")
    event_channel = event_details.get("channel")
    event_timestamp = event_details.get("ts")
    user_text = event_details.get("text")

    # edge case for updated messages (changed)
    if event_subtype == "message_changed":
        new_message_details = event_details.get("message")
        user_text = new_message_details.get("text")
        event_timestamp = new_message_details.get("ts")

    # Return if we don't have a text message (like a message has been deleted)
    if user_text == None:
        print(
            f"No text found for event type '{event_type}' and subtype '{event_subtype}'"
        )
        print(f"full details\n{event_details}")
        return

    # Search to see if the incoming message matches yubikey 44 char code
    yubiRegex = "[cbdefghijklnrtuv]{44}"
    if re.search(yubiRegex, user_text):

        # Lets see if the entire message is a yubi code or if we should just replace the key
        test_message = re.sub(yubiRegex, "", user_text)

        if test_message.strip() == "":
            # replace the code with a random response
            new_message = random.choice(responses)
        else:
            # lets just replace yubi code with an emoji
            new_message = re.sub(
                yubiRegex, f":{random.choice(response_reaction)}:", user_text
            )

        try:
            # update message
            slack_client.chat_update(
                channel=event_channel, ts=event_timestamp, text=new_message
            )

            # add reaction
            slack_client.reactions_add(
                name=random.choice(response_reaction),
                channel=event_channel,
                timestamp=event_timestamp,
            )

        except SlackApiError as e:
            print(f"An error occured:{str(e)}")


# Start the server on port 3000
slack_events_adapter.start(port=3000, host="0.0.0.0")
