# Nostalgiabot II

> A bot to remind us of what we'd all rather forget we said.
>
> \- Martin Petkov

Nostalgiabot II is the sequel to Nostalgiabot, originally written by Martin Petkov.

## Tech Stack
NB2 is a simple Flask app. You should be familiar with these technologies:

- [Python](https://www.python.org/), specifically 3.6
- [Flask](https://flask.palletsprojects.com/en/1.1.x/)
- [Flask-RESTful](https://flask-restful.readthedocs.io/en/latest/)

## Development Setup

### Clone the repository

```
git clone git@github.com:revangel/nostalgiabot2.git
```

### Setup virtual environment

```
mkvirtualenv nb2
workon nb2
```

### Dependencies
Run the following to install all the Python dev dependencies:
```
pip install -r requirements/dev
```

### Environment & Configs
Create a new .env file in the root directory of the project using .env.example as a template
   ```
   cp .env.example .env
   ```

   *Do not commit this new file as it will contain secret keys!*

Set `FLASK_ENVIRONMENT` to `development`. This enables the debugger and hot reloading.


### Precommit & Linting
We use [pre-commit](https://pre-commit.com/) to manage and run linters and autoformatting on a git commit hook. To initialize pre-commit hooks, run the following:
```
pre-commit install
```

### Database

To initialize the SQLite database, run:
```
flask db upgrade
```

### Run the bot

```
flask run
```
You should now see a url in your console pointing you to where NB2 is running

## Steps to Create Slack Bot

1. Create a new bot and assign it to a workspace https://api.slack.com/apps?new_app=1

2. Enable socket mode.

![Socket Mode](./readme_assets/socket_mode.png?raw=true)

3. Generate a token with `connection:write` scope.

![App Token](./readme_assets/app_token.png?raw=true)

4. Copy the token and paste it under the `SLACK_APP_TOKEN` variable in your local `.env` file.

5. Enable event subscriptions and subscribe to the `app_mention` bot event.

![Event Subscription](./readme_assets/event_subscription.png?raw=true)

6. Under `OAuth & Permissions`, install to workspace.

![Install](./readme_assets/install.png?raw=true)

7. Set the following bot scopes: `app_mentions:read`, `chat:write`, `users:read`

![Bot Scopes](./readme_assets/bot_scopes.png?raw=true)

8. Copy `Bot User OAuth Token` and paste it under the `SLACK_BOT_TOKEN` variable in your local `.env` file.

![Bot Token](./readme_assets/slack_bot_token.png?raw=true)

9. Under `Basic Information` copy the `Signing Secret` and paste it under the `SLACK_SIGNING_SECRET` variable in your local `.env` file.

![Signing Secret](./readme_assets/signing_secret.png?raw=true)

10. The bot should be ready to use and can now access the running Flask server.
