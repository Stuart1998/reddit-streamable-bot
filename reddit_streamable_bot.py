"""Reddit Streamable bot.

A bot for Reddit that mirror videos from posts of specified domains
to Streamable and replies with the link.
"""
import logging
import traceback
import time
from logging import INFO, ERROR

from prawcore.exceptions import Forbidden, RequestException, ResponseException
from requests.exceptions import Timeout, ConnectionError, ReadTimeout, HTTPError
from requests import request


log = logging.getLogger('reddit_streamable_bot')


class Bot:
	_UPLOAD_URL = 'https://api.streamable.com/import?url={url}'
	_VIDEO_URL = 'https://streamable.com/{shortcode}'
	_VREDDIT_URL = 'https://vredd.it/ajax_process.php'
	_RETRY_STATUSES = {500, 502, 503, 504}
	CE_SLEEP = 10  # Seconds to sleep in case of ConnectionError.
	REPLY_TEMPLATE = ('[Streamable Mirror]({link})\n\n'
					  '*I am a bot, and this action was performed '
					  'automatically.*')

	@staticmethod
	def _log(lvl, post, msg):
		for string in [f'Submission: {post.shortlink}',
					   f'Submission_url: {post.url}',
					   f'Mirror: {msg}']:
			log.log(lvl, string)
				
	def __init__(self, reddit, subreddit_name, *, streamable_auth, domains,
				 streamable_user_agent, sticky=False):
		"""Initialize a Bot instance.

		Parameters:
			reddit: authenticated (not read-only) praw.Reddit instance.
			subreddit_name: string, name of the subreddit.
			streamable_auth: tuple, streamable credentials (username, password).
			domains: list of domains.
			sticky: boolean, if True the comment will be sticky.
		"""
		self._reddit = reddit
		self._subreddit = self._reddit.subreddit(subreddit_name)
		self._streamable_auth = streamable_auth
		self._streamable_headers = {'User-Agent': streamable_user_agent}
		self._errors = 0
		self._offline = False
		self.domains = domains
		self.sticky = sticky

	def _request(self, method, url, *, max_retries=3, **kwargs):
		retries = 0
		while True:
			try:
				r = request(method, url, timeout=10, **kwargs)
				if (r.status_code not in self._RETRY_STATUSES 
						or retries >= max_retries):
					return r
				time.sleep(5)
			except (Timeout, ConnectionError) as exception:
				if retries >= max_retries:
					raise
				if isinstance(exception, ConnectionError):
					time.sleep(self.CE_SLEEP)
			retries += 1

	def _video_url(self, submission):
		if submission.domain == 'v.redd.it':
			self._request('POST', self._VREDDIT_URL,
						  data={'url': submission.url})
			return f'https://vredd.it/files/{submission.url[18:]}.mp4'
		return submission.url

	def main(self, submission):
		try:
			resp = self.mirror(self._video_url(submission))
			if resp is None:
				msg = "Video over 10 min or couldn't be processed"
				self._log(INFO, submission, msg)
			elif isinstance(resp, int):
				if resp == 404:
					self._log(INFO, submission, 'Invalid video link')
				else:
					raise HTTPError(f'Streamable HTTP {resp} response')
			else:
				self._log(INFO, submission, resp)
				reply = self.REPLY_TEMPLATE.format(link=resp)
				comment = submission.reply(reply)
				log.info(f'Reply: https://www.reddit.com{comment.permalink}')
				if self.sticky:
					comment.mod.distinguish(how='yes', sticky=True)
			return None
		except HTTPError as http_error:
			self._log(ERROR, submission, str(http_error))
		except KeyboardInterrupt:
			self._log(INFO, submission, 'User interrupted process')
			raise
		except Exception:
			self._log(ERROR, submission, 'Error\n' + traceback.format_exc())
		self._errors += 1

	def mirror(self, url):
		"""Upload a video from url to Streamable.
		
		Parameters:
			url: string, the URL of the video.

		Returns: Streamable video URL if the upload was successful,
			None if the video is over 10 min or the server can't
			process the video else the HTTP response status code.
		"""
		r = self._request('GET', self._UPLOAD_URL.format(url=url),
						  headers=self._streamable_headers,
						  auth=self._streamable_auth)
		if r.status_code == 200:
			video_link = self._VIDEO_URL.format(shortcode=r.json()['shortcode'])
			time.sleep(10)
			r = self._request('HEAD', video_link)
			if r.status_code == 200:
				return video_link
			elif r.status_code == 404:
				return None
		return r.status_code

	def run(self):
		stream = self._subreddit.stream.submissions
		log.info('Starting')
		while True:
			try:
				self._offline = False
				for submission in stream(skip_existing=True):
					if submission.domain in self.domains:
						self.main(submission)
			except KeyboardInterrupt:
				log.info('User interrupted the program')
				raise
			except Exception as exception:
				if (isinstance(exception, RequestException) and
						isinstance(exception.original_exception,
								   (ReadTimeout, ConnectionError))):
					oe = exception.original_exception
					if isinstance(oe, ConnectionError):
						self._offline = True
						time.sleep(self.CE_SLEEP)
					continue
				self._errors += 1
				if (isinstance(exception, ResponseException) and 
						exception.response.status_code in self._RETRY_STATUSES):
					code = exception.response.status_code
					log.error(f'Reddit HTTP {code} response')
					log.debug('Restarting in 5 s')
					time.sleep(5)
				else:
					log.exception('Error\n')
					log.info('Stopping')
					break
