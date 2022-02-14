# YubiSnooze
Slack bot to automatically delete yubisneeze / accidental yubikey presses as well as invalidate them against yubico so they cannot be used again.

It will search using the regex ~~`"[cbdefghijklnrtuv]{44}"`~~ `"[cc|vv]{2}[cbdefghijklnrtuv]{42}"` and if that is the entire message will replace it with a response. If the token is within a message it will simply just the token with a reaction.

It will react to the new message in both cases.

# Example

https://user-images.githubusercontent.com/1465995/153814518-ab95d8dc-953e-41e4-a64e-2f1f8b73eae9.mov

# Updated example with invalidating token

https://user-images.githubusercontent.com/1465995/153815088-94b5f130-95d1-41a5-813d-10b6a2901126.mov


# Installation
## Python install
Install the app on an Internet facing server (or configure ngrok/other):

`pip3 install -r requirements.txt`

## Setup Slack API
- Create a Slack app on https://api.slack.com/apps
- Add a bot user for your app
- Add user token scopes as per your requirements:
![Slack API token scope](images/scopes.png)
- Set the `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` env variables
- Configure python script where neccessary if you want to change the port / messages / reactions
- Run the python script 
- Configure the events API with your Internet facing URL (eg http://<my_ip>:3000/yubisnooze/)
- Add relevant event subscriptions:
![Slack API event subscription](images/events.png)
- Install to workspace



