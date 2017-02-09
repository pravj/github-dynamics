import requests as req
import rethinkdb as rdb
import time
from urlparse import urlparse

con = rdb.connect()

db_name = 'hn_gh_stories'
table_name = 'stories_with_url'

db_ref = rdb.db(db_name).table(table_name)

if db_name not in rdb.db_list().run(con):
    rdb.db_create(db_name).run(con)

if table_name not in rdb.db(db_name).table_list().run(con):
    rdb.db(db_name).table_create(table_name).run(con)

max_hit = 1000
tag = 'story'

# GMT Oct. 9, 2016
limiting_timestamp = 1475971200

cursor_timestamp = int(time.time())

api_url = 'http://hn.algolia.com/api/v1/search_by_date'

total_stories = 0

while (cursor_timestamp > limiting_timestamp):
	params = {
		'hitsPerPage': max_hit,
		'tags': 'story',
		'numericFilters': 'created_at_i<{0}'.format(cursor_timestamp)
		}

	try:
		res = req.get(api_url, params=params)
	except Exception, e:
		print e

	stories = res.json()['hits']

	# instead of adding every story, it will batch insert them
	bacth_data = []

	for story in stories:
		try:
			# some URLs were raising exceptions for this
			# I have introduced this try-else block
			# assuming that github URLs will follow along.
			# "move fast without* breaking things"
			url = story['url']
			parsed_url = urlparse(url)
			url_tld = parsed_url.netloc

			# only selecting URLs from 'github.com'
			# format 'http(s)://github.com/{user}/{repo}'
			# lame approach? - yes!
			if url_tld == 'github.com' and len(parsed_url.path.split('/')) == 3:
				bacth_data.append({
					'timestamp': story['created_at_i'],
					'sid': story['objectID'],
					'num_comments': story['num_comments'],
					'points': story['points'],
					'url': url
					})
		except Exception, e:
			pass

	try:
		db_ref.insert(bacth_data).run(con)
		print bacth_data
	except Exception, e:
		bacth_data
		print e

	total_stories += len(bacth_data)
	print 'inserting {0} stories, total {1}'.format(len(bacth_data), total_stories)

	cursor_timestamp = stories[-1]['created_at_i']
	time.sleep(3600/10000)