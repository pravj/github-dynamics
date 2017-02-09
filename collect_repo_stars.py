import os
import time
import sys
import requests as req
import rethinkdb as rdb

# using custom media type to collect 'star creation timestamp'
token = os.environ['GITHUB_TOKEN']
headers = {'Authorization': 'token {}'.format(token), 'Accept': 'application/vnd.github.v3.star+json'}

db_name = 'repo_stars'

con = rdb.connect()

per_page = 100

def collect_stars(repo, table_name):
	page = 165
	total_stars = 0

	while True:
		api_url = 'https://api.github.com/repos/{0}/stargazers'.format(repo)
		params = {'page': page, 'per_page': per_page}

		try:
			res = req.get(api_url, params=params, headers=headers)
		except Exception, e:
			raise e

		stars = res.json()
		num_stars = len(stars)
		if num_stars == 0:
			break

		batch_stars = []
		for star in stars:
			batch_stars.append({
				'starred_at': star['starred_at'],
				'user': star['user']['login']
				})

		try:
			rdb.db(db_name).table(table_name).insert(batch_stars).run(con)
		except Exception, e:
			raise e

		total_stars += num_stars
		print 'Collected {0} stars, total {1}, page {2}'.format(num_stars, total_stars, page)

		page += 1


def main(table):
	if db_name not in rdb.db_list().run(con):
		rdb.db_create(db_name).run(con)

	# RethinkDB uses (A-Za-z0-9_) only
	table_name = table.replace('/', '_')
	table_name = table_name.replace('-', '_')

	# allowing duplicate star collection for same repository
	# (collecting after a time)
	table_name = table_name + '_dup'

	if table_name not in rdb.db(db_name).table_list().run(con):
		rdb.db(db_name).table_create(table_name).run(con)

	collect_stars(table, table_name)

if __name__ == '__main__':
	print int(time.time())
	main(sys.argv[1])
