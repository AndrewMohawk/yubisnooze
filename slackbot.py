from dataclasses import replace
from slackeventsapi import SlackEventAdapter
from slack_sdk.web import WebClient
from slack_sdk.errors import SlackApiError
import secrets
import string
import requests
import re
import random
import os

# Grab token from environment variables
slack_signing_secret = os.environ["SLACK_SIGNING_SECRET"]
slack_bot_token = os.environ["SLACK_BOT_TOKEN"]

# create Slack event adapter and web client
slack_events_adapter = SlackEventAdapter(slack_signing_secret, endpoint="/yubisnooze/")
slack_client = WebClient(slack_bot_token)

#Options? lol.
TOKEN_REPLACE_WITH_EMOJI = False #Set true to replace the token with an emoji
REACT_AFTER_REPLACE = True # if true, react to the message after replacement

# responses and reactions (without :'s)
replacement_text = [
    "Aaaahchoo!",
    "Hayfever really is bad this time of year",
    "*tissues*",
    "No one will know I just yubisneezed",
]
emojis = ["yubisneeze", "safety_pin", "safety_vest", "closed_lock_with_key"]

# Invalidate the OTPs against Yubico's server
def invalidate_yubikeyOTP(otp_token):
    validation_url = "https://api.yubico.com/wsapi/2.0/verify"
    
    alphabet = string.ascii_letters + string.digits
    nonce = ''.join(secrets.choice(alphabet) for i in range(16))

    id=1
    url = f"{validation_url}?otp={otp_token}&id={id}&nonce={nonce}"
    #make the request to invalidate the token
    response = requests.get(url)
    response_text = response.text
    #parse the response line by line
    for line in response_text.splitlines():
        #get key value pairs
        key, value = line.split("=",1)
        #if the key is status, return the value
        if key == "status":
            return value
    
    # Error state where we didn't get a valid response
    print(f"Error: Invalid response from Yubico server: {response_text}")
    return False



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

    #We can ignore messages that are not text or updates
    ignorable_events = ["message_deleted"]
    if(event_subtype in ignorable_events):
        return True
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
    # yubiRegex = "[cbdefghijklnrtuv]{44}"
    yubiRegex = "[cc|vv]{2}[cbdefghijklnrtuv]{42}" #better regex for yubikeys

    #findall possible keys
    yubikey_otp_matches = re.findall(yubiRegex, user_text)
    
    for otp_token in yubikey_otp_matches:
        
        # Lets see if the entire message is a yubi code or if we should just replace the key
        test_message = user_text.replace(otp_token,"") 

        if test_message.strip() == "":
            # replace the code with a random response
            if TOKEN_REPLACE_WITH_EMOJI:
                new_message = random.choice(replacement_text)
            else:
                new_message = ""
        else:
            # lets just replace yubi code with an emoji
            # new_message = re.sub(
            #     otp_token, f":{random.choice(response_reaction)}:", user_text
            # )
            if TOKEN_REPLACE_WITH_EMOJI:
                new_message = user_text.replace(otp_token, f":{random.choice(emojis)}:")
            else:
                new_message = user_text.replace(otp_token, "")

        try:
            #invalidate yubikey OTP
            response = invalidate_yubikeyOTP(otp_token)

            if(response != "OK"):
                #might not be safe to print since it could use a different validation server
                print(f"Yubikey OTP invalidation failed with status: {response} for token")
            else:
                #safe to print since it has been used/invalidated
                print(f"Yubikey OTP {otp_token} invalidated successfully")

            # We should still strip this out because the keys might have a different validation server

            if(new_message == ""):
                #lets delete the message
                slack_client.chat_delete(channel=event_channel, ts=event_timestamp)
            else:
                # update message
                slack_client.chat_update(
                    channel=event_channel, ts=event_timestamp, text=new_message
                )

            if REACT_AFTER_REPLACE and new_message != "":
                # add reaction
                slack_client.reactions_add(
                    name=random.choice(emojis),
                    channel=event_channel,
                    timestamp=event_timestamp,
                )

        except SlackApiError as e:
            print(f"An error occured:{str(e)}")


# Start the server on port 3000
slack_events_adapter.start(port=3000, host="0.0.0.0")

