"""
Create following neighbourhood graph using NetworkX library
"""

import os
import json
import requests as r
import networkx as nx
from networkx.readwrite import json_graph

from followings import get_user_following

token = os.environ['GITHUB_TOKEN']
headers = {'Authorization': 'token {}'.format(token)}

# save a directed graph of mutual followership
def save_following_network_graph(user_list, file_name):
	graph = nx.DiGraph()

	for user in user_list:
		print user
		user_followings = get_user_following(user)

		graph_edges = [(user, u) for u in user_followings]
		graph.add_edges_from(graph_edges)

		print 'added {1} edges for user @{0}'.format(user, len(graph_edges))

	graph_data = json_graph.adjacency_data(graph)

	with open(file_name, 'w') as f:
		json.dump(graph_data, f, indent=4)

"""
with open('pravj_followings.json', 'r') as f:
	file_data = json.load(f)

first_degree_users = file_data['followings']

save_following_network_graph(first_degree_users, 'pravj_graph.json')
"""

"""
bot_users = ['angusshire']
user_list = [u['user'] for u in stargazers if u['user'] not in bot_users]
save_following_network_graph(user_list, 'pravj_Doga_stargazers.json')
"""