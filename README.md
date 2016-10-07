[![Coverage Status](https://jenkins.groupso.me/badges/coverage.svg)](https://jenkins.groupso.me/badges/coverage.svg)

# Groupsome

Groupsome offers the brilliant opportunity to manage and view content from your Telegram groups in a web application. You can view the recently posted content of your groups in a feed, view all the photos, collect your videos, files, audios and links. We also offer additional features besides just organising your telegram group content: You can create albums or view the chat history for posted photos. Additionally, you can start events, share whether or not you attend and will be reminded in your corresponding telegram group. Furthermore you can initiate group surveys, vote and view the results. Participation and Voting are available via the web application or in inline mode.

Our service is accessible over [groupso.me](http://groupso.me), but you can also host it yourself.

## Creating a bot account

The groupsome bot needs credentials for Telegram. You can create a bot account by contacting `@BotFather` on Telegram. Make sure to disable the privacy mode which allows the bot to read all messages written within groups.

## Installation

### Method 1: Docker (recommended)

We provide a Dockerfile as an easy way to get startet with groupsome. It includes Mariadb, Redis and all the other requirements.

Start it this way (replace `mygroupsomebot` and `mybottoken` with your bot credentials):

```
TELEGRAM_BOT_USERNAME=mygroupsomebot TELEGRAM_TOKEN=mybottoken docker-compose up
```

You can further adjust the configuration in `messengerext/config/settings_docker.py` and `docker/`.

### Method 2: Manual installation

Groupsome is a standard Django application written in Python 3. We recommend gunicorn and nginx for serving http requests. Groupsome also needs Mysql and Redis.

First install the following requirements using your default package manager:

```
sudo apt-get install gettext webp ffmpeg
```

Then install everything else using pip:

```
pip install -r requirements_production.txt
```

[Stylus](http://stylus-lang.com/) is used as an CSS preprocessor and JS gets compressed using [yuglify](https://www.npmjs.com/package/yuglify). You can install both using npm.

The configuration can be adjusted in `messengerext/config/settings_production.py`.

Groupsome stores media files in `media/`, this directory needs to be writable.

We use [python-rq](http://python-rq.org/) for asynchronous tasks like downloading files and converting videos. You can start a python-rq worker using:

```
python manage.py rqworker
```

Groupsome needs two tasks to be executed periodically, for example as an cronjob or systemd timer:

`python manage.py cleanuptokens` removes old login tokens from the database, it should be called every minute.

`python manage.py cleanupmedia` removes old, unused media files from the filesystem. It should be called at least daily.

The bot includes two ways to communicate with telegram:

#### 1. Polling new messages from telegram

You can start polling telegram for new messages with `python manage.py polltelegram`. This method is not recommended for production.

Polling disables any configured webhooks.

#### 2. Webhook

Using a Webhook Telegram makes an POST request on your server for every new message. This is recommended but requires your webserver to be accessible for Telegram and also required HTTPS. You can set your Webhook url on Telegram with `python manage.py setwebhook <hostname>`.

You can disable the webhook with `python manage.py disablewebhook` or by starting to poll messages.

