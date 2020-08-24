# Nostalgiabot II

> A bot to remind us of what we'd all rather forget we said.
>
> \- Martin Petkov

Nostalgiabot II is the sequel to Nostalgiabot, originally written by Martin Petkov.

## Steps to Create Slack Bot

1. Create a new .env file in the root directory of the project using .env.example as a template
   ```
   cp .env.example .env
   ```

   *Do not commit this new file as it will contain secret keys!*

2. Create a new bot and assign it to a workspace https://api.slack.com/apps?new_app=1

3. Install the app from the api.slack.com site under the OAuth & Permissions Feature. Save the **Bot User OAuth Access Token** and assign it to `SLACK_BOT_TOKEN` in the .env file created in step 1.

4. Still on api.slack.com, enable events under th Event Subscriptions Feature. Subscribe to the bot event `app_mention`.

5. A request url is needed for step 4. In development, it's easiest to use ngrok to generate a url that will forward to the Flask app's port. Follow the first three steps [here] (https://api.slack.com/tutorials/tunneling-with-ngrok). Assign the forwarding url as the Request URL under the Event Subscription Feature.

5. Reinstall the Slack Bot app.

6. Under the Slack Bot app's Basic Information, copy the Client Secret and assign it to `SLACK_SIGNING_SECRET` in the .env file created in step 1.

7. The bot should be ready to use and can now access the running Flask server.

*Note ngrok will randomly assign a new url each time it is run, so step 5 may need to be repeated each time ngrok is restarted.*
