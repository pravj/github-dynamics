import os
import json
import requests as r

# using maximum allowed 'per_page' to minimize api requests
per_page_count = 100

token = os.environ['GITHUB_TOKEN']
headers = {'Authorization': 'token {}'.format(token)}

def get_user_following(username):
	print 'collecting followings for user @{0}'.format(username)
	# pagination support
	page = 1

	# follower list to return
	result = []

	while True:
		url = "https://api.github.com/users/{0}/following".format(username)
		params = {'page': page, 'per_page': per_page_count}

		try:
			res = r.get(url, params=params, headers=headers)
		except Exception, e:
			raise e

		users = res.json()
		if (len(users) == 0):
			break

		for user in users:
			result.append(user['login'])

		page += 1

	return result

def save_user_following(username):
	result = get_user_following(username)
	data = {'user': username, 'followings': result}

	with open("{0}_followings.json".format(username), 'w') as f:
		json.dump(data, f, indent=4)

#save_user_following('UmesH-JhingoniA')
