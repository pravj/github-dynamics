import os
import gc
import json
import time
import requests as req
import rethinkdb as rdb
from collections import defaultdict

token = os.environ['GITHUB_TOKEN']
headers = {'Authorization': 'token {}'.format(token)}

# following relations cache, to reduces the API consumption
following_cache = defaultdict(lambda: defaultdict(lambda: False))

# collaborative relations
collaboration_cache = defaultdict(lambda: defaultdict(lambda: False))

def is_following(user, target_user):
	"""
	Return 1 if 'user' is following 'target_user'
	"""

	if following_cache[user][target_user]:
		print 'Follwing Cache Hit'
		print '-*-' * 10
		return 1
	else:
		url = 'https://api.github.com/users/{0}/following/{1}'.format(user, target_user)

		try:
			res = req.get(url, headers=headers)
		except Exception, e:
			raise e

		if res.status_code == 204:
			following_cache[user][target_user] = True
			return 1
		elif res.status_code == 404:
			return 0


def is_contributor(user, repository):
	"""
	Return True if the 'user' is a contributor to the 'repo'.
	"""

	_repo = repository.split('/')
	owner, _repo = _repo[-2], _repo[-1]

	print owner, _repo

	if collaboration_cache[user][owner]:
		print 'Collaboration Cache Hit'
		return 1
	else:
		print 'checking stats'
		url = 'https://api.github.com/repos/{0}/{1}/stats/contributors'.format(owner, _repo)

		try:
			res = req.get(url, headers=headers)
		except Exception, e:
			raise e

		value, result = 0, None

		if res.status_code == 202:
			print 'sleeping'
			time.sleep(3)
			return is_contributor(user, repository)
		elif res.status_code == 200:
			for contributor in res.json():
				if contributor['author']['login'] == user:
					value = 1
					print 'in contributor list'
					break

		if value == 1:
			result = value
		elif value == 0:
			result = is_following(user, owner)

		if result == 1:
			collaboration_cache[user][owner] = True

		return result


con = rdb.connect()
db_name, table_name = 'member_events', 'year_2016'

db_ref = rdb.db(db_name).table(table_name)

if db_name not in rdb.db_list().run(con):
	rdb.db_create(db_name).run(con)

if table_name not in rdb.db(db_name).table_list().run(con):
	rdb.db(db_name).table_create(table_name).run(con)


for i in range(2, 7):
	print '2016, {0}'.format(i)

	with open('{0}.json'.format(i)) as f:
		events = json.load(f)
		events = events[0]

	entries = []

	# on IST timestamp 1486385213
	top_users = ["torvalds", "JakeWharton", "tj", "addyosmani", "paulirish", "ruanyf", "mojombo", "defunkt", "sindresorhus", "gaearon", "daimajia", "mbostock", "douglascrockford", "kennethreitz", "jeresig", "mdo", "mattt", "yyx990803", "jlord", "schacon", "Trinea", "JacksonTian", "michaelliao", "substack", "jashkenas", "yinwang0", "chrisbanes", "dhh", "lifesinger", "mrdoob", "cloudwu", "LeaVerou", "hadley", "angusshire", "taylorotwell", "stormzhang", "tpope", "mitsuhiko", "onevcat", "pjhyett", "clowwindy", "karpathy", "wycats", "JeffreyWay", "ibireme", "vczh", "johnpapa", "phodal", "laruence", "hakimel", "buckyroberts", "getify", "antirez", "BYVoid", "romannurik", "ryanb", "fat", "fabpot", "CoderMJLee", "isaacs", "astaxie", "hongyangAndroid", "muan", "sofish", "liaohuqiu", "josevalim", "tekkub", "agentzh", "ry", "koush", "charliesome", "justjavac", "tenderlove", "RubyLouvre", "chriscoyier", "ChenYilong", "cusspvz", "feross", "nzakas", "fouber", "necolas", "commonsguy", "matz", "tangqiaoboy", "igrigorik", "holman", "maxogden", "wintercn", "lepture", "zenorocha", "mitchellh", "romainguy", "benbalter", "programthink", "rauchg", "chenshuo", "hackedteam", "singwhatiwanna", "mathiasbynens", "jtleek"]

	# number of events
	size = len(events['user'])

	for j in range(size):
		user = events['user'][str(j)]
		repo = events['repository'][str(j)]

		payload = json.loads(events['payload'][str(j)])
		member = payload['member']['login']
		action = payload['action']

		if action == 'added' and member in top_users:
			score = is_contributor(member, repo)
			print repo

			entries.append({
				'user': user,
				'repository': repo,
				'member': member,
				'score': score,
				'month': i
				})

			print '{0} added {1} in {2} : score {3}'.format(user, member, repo, score)

	gc.collect()

	db_ref.insert(entries).run(con)
	print i, len(entries)

gc.collect()
