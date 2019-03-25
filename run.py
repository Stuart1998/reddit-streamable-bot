import traceback
import threading
import logging
import time
import sys

import praw

from reddit_streamable_bot import Bot
from config import *


def _show_status():
	old_l = 0
	while True:
		errors =  f' || Errors: {bot._errors}'
		if stop:
			to_print = '>>> Stopped.' + errors
			to_print += (old_l - len(to_print)) * ' '
			print(to_print, flush=True)
			break
		elif bot._offline:
			to_print = f'>>> Connection issue, retrying in {bot.CE_SLEEP} s'
		else:
			to_print = '>>> Running...'
		to_print += errors
		to_print += (old_l - len(to_print)) * ' '
		print(to_print, end='\r', flush=True)
		old_l = len(to_print)
		time.sleep(0.1)


if __name__ == '__main__':
	logger = logging.getLogger('reddit_streamable_bot')
	file_handler = logging.FileHandler('reddit_streamable_bot.log')
	formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
	file_handler.setFormatter(formatter)
	logger.setLevel(logging.INFO)
	logger.addHandler(file_handler)
	try:
		reddit = praw.Reddit(client_id=CLIENT_ID,
							 client_secret=CLIENT_SECRET,
							 user_agent=USER_AGENT,
							 username=USERNAME,
							 password=PASSWORD)
		mod = reddit.subreddit(SUBREDDIT_NAME).moderator(reddit.user.me())
		if (STICKY_COMMENT and 
				(not mod or not any(perm in mod[0].mod_permissions 
									for perm in ['posts', 'all']))):
			raise PermissionError
		streamable_auth = (STREAMABLE_EMAIL, STREAMABLE_PASSWORD)
		bot = Bot(reddit, SUBREDDIT_NAME, streamable_auth=streamable_auth,
				  streamable_user_agent=STREAMABLE_USER_AGENT, domains=DOMAINS, 
				  sticky=STICKY_COMMENT)
		if REPLY_TEMPLATE_FILE:
			f = open(REPLY_TEMPLATE_FILE)
			bot.REPLY_TEMPLATE = f.read().strip()
			f.close()
		stop = False	
		thread = threading.Thread(target=_show_status)
		print('Reddit Streamable Bot\n')
		thread.start()
		bot.run()
		stop = True
		thread.join()
	except PermissionError:
		print('To sticky the reply comment, the bot must be a moderator on the '
			  'subreddit and have posts permission.')
	except KeyboardInterrupt:
		stop = True
		thread.join()
		sys.exit()
	except Exception:
		traceback.print_exc()
	input('\nPress Enter to exit.')
