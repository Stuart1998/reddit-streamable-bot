# Reddit Streamable bot:
A bot for Reddit that mirror videos from posts of specified domains to Streamable and replies with the link.

## Requirements:
- [Python](https://www.python.org/) 3+
- Third-party libraries: [PRAW](https://praw.readthedocs.io/en/latest/getting_started/installation.html) 6+ and [Requests](http://docs.python-requests.org/en/master/)

      pip install requests praw
## How to run:
1. [Create a reddit script app](https://www.reddit.com/prefs/apps/):
    - Click `are you a developer? create an app...` or `create another app...`
    - Name your app, select script and put a redirect uri (http://localhost:8080 should work) and click `create app` https://i.imgur.com/6L8YNiJ.png
    - Now you have a reddit client id (under personal use script) and a reddit client secret. https://i.imgur.com/lQdqav0.png
2. [Create a Streamable account](https://streamable.com/signup) and verify the email.
3. Download the following files and put them in the same folder:
    - `reddit_streamable_bot.py`
    - `config.py`
    - `run.py`
    - `reply template.txt`
4. Open `config.py` with a text editor and add the required credentials.
5. Save it.
6. Run `run.py`.
  
**Notes**: 
  - If STICKY_COMMENT is set to `True`, the bot must be a moderator on the subreddit and have posts permission.
  - The reply comment can be edited in `reply template.txt`.
  - Videos that are over 10 minutes will not be mirrored.

## License
  [The MIT License](https://opensource.org/licenses/MIT)
