"""
Create stargazers connection graph using NetworkX library
"""

from __future__ import division
from math import floor
import os
import json
import requests as r
import rethinkdb as rdb
import networkx as nx
from collections import defaultdict
from networkx.readwrite import json_graph

bot_users = ['angusshire']

# instead of inifinity, using a constant value to find local clusters
MAX_DISTANCE = 1000

def minimum_key_value(d):
	"""
	return the key-value pair with minimum numeric key in a defaultdict
	"""

	if len(d) == 0:
		return MAX_DISTANCE, []
	else:
		min_key, min_val = d.items()[0]
		for k, v in d.items():
			if k < min_key:
				min_key, min_val = k, v
		return min_key, min_val


# collect ordered WatchEvents as they appeared
con = rdb.connect()
stargazers = rdb.db('repo_stars').table('pravj_Doga').order_by('starred_at').run(con)

# stargazers' mutual following network for repository 'pravj/Doga'
with open('/home/pravendra/projects/gitworld/collector/pravj_Doga_stargazers.json', 'r') as f:
	graph_data = json.load(f)
	stargazers_following_graph = json_graph.adjacency_graph(graph_data)

# stargazers connection graph
stargazers_network_graph = nx.DiGraph()

# add root node (creator of the repo) and its attributes
stargazers_network_graph.add_node('pravj')
nx.set_node_attributes(stargazers_network_graph, 'distance', {'pravj': 0})
nx.set_node_attributes(stargazers_network_graph, 'order', {'pravj': 0})
nx.set_node_attributes(stargazers_network_graph, 'connections', {'pravj': []})

# iterate over all the stargazers except bots
user_order = 1
for u in stargazers:
	user = u['user']
	if user not in bot_users:
		# for each stargazer, check if it has a link to previous stargazers
		# A is linked to B, if A follows B.
		node_distances, is_linked = [], False
		connected_users = defaultdict(lambda: [])
		
		for n in stargazers_network_graph.nodes():
			if stargazers_following_graph.has_edge(user, n):
				stargazers_network_graph.add_node(user)
				#stargazers_network_graph.add_edge(user, n)

				is_linked = True
				distances = nx.get_node_attributes(stargazers_network_graph, 'distance')
				node_distances.append(distances[n])
				connected_users[distances[n]].append(n)
			else:
				stargazers_network_graph.add_node(user)

		# set chronological order of the user (as it appeared)
		nx.set_node_attributes(stargazers_network_graph, 'order', {user: user_order})

		# add nearest/shortest connections to a node
		min_dis, min_dis_connections = minimum_key_value(connected_users)
		nx.set_node_attributes(stargazers_network_graph, 'connections', {user: min_dis_connections})

		# add edges only to the nearest nodes, if any
		for c in min_dis_connections:
			stargazers_network_graph.add_edge(user, c)

		if is_linked:
			nx.set_node_attributes(stargazers_network_graph, 'distance', {user: min_dis + 1})
		else:
			nx.set_node_attributes(stargazers_network_graph, 'distance', {user: MAX_DISTANCE})

		user_order += 1

# to sort the nodes chronologically and their order by name
node_dict, order_dict = {}, {}

network_degrees = stargazers_network_graph.in_degree()

for node, node_data in stargazers_network_graph.nodes(data=True):
	node_data['name'] = node
	node_data['in_degree'] = network_degrees[node]

	order_dict[node] = node_data['order']
	node_dict[node_data['order']] = node_data

# append nodes to respective node-level list
node_level_data = defaultdict(lambda: [])
for node_order, node_data in node_dict.iteritems():
	node_level_data[node_data['distance']].append(node_data)

# nearest connected nodes for each node
node_connections = nx.get_node_attributes(stargazers_network_graph, 'connections')

width, height = 960, 1300
diff_y, gape_y = 40, 100

chart_data = {
	'nodes': [],
	'links': [],
	'connected_links': defaultdict(lambda: []),
	'connected_nodes': defaultdict(lambda: []),
	'axis': []};

left_padding = 60
width -= left_padding

# node diameters per level
node_diameters = [1, 10, 10, 8, 6, 4, 8, 8, 8]

node_index = 0
ordered_nodes = {}

level_texts = {0: '0', 1: '1', 2: '2', 3: '3', 4: '4', 1000: 'N', 1001: 'N+1', 1002: 'N+2', 1003: 'N+3'}

for level, node_data_list in node_level_data.iteritems():
	_level = level
	if level >= 1000:
		_level = (level - 1000) + 5

	if _level > 0:
		gape_y = 200

	"""
	direction = None
	if 4 >=_level >= 2:
		direction = 's'
	else:
		direction = 'n'
	"""

	g, d = None, None

	number_nodes = len(node_data_list)
	print _level, number_nodes
	continue
	D = node_diameters[_level]

	if number_nodes == 1:
		g = (width - D) / 2
		d = 0
	else:
		d = floor((width - ((number_nodes + 2)*D))/(number_nodes - 1))
		g = ((width - (number_nodes*D)) - (d*(number_nodes - 1))) / 2

	start_x = left_padding + g + (D/2)

	# every circle node on each level are at a same height
	node_y = gape_y + (diff_y * _level)
	chart_data['axis'].append({
		'x': 20,
		'y': node_y+5,
		'value': level_texts[level]})

	#print _level
	for i in range(number_nodes):
		node_x = start_x + (i*(D+d))
		node_data = node_data_list[i]

		_name = node_data['name']
		_degree = node_data['in_degree']

		ordered_nodes[_name] = node_index
		node_index += 1

		chart_data['nodes'].append({
			'name': _name.encode('utf-8'),
			'order': node_data['order'],
			'distance': node_data['distance'],
			'level': _level,
			'in_degree': _degree,
			'x': 0,
			'y': 0,
			'fixed':True,
			'radius': (D/2) + (_degree)})
		

"""
print chart_data['nodes']

link_index = 0
source_target_nodes = defaultdict(lambda: [])

for level, node_data_list in node_level_data.iteritems():
	#print level
	for node_data in node_data_list:
		for c_node_name in node_data['connections']:
			source_target_nodes[node_data['name']].append((c_node_name, link_index))

			#print link_index

			#print node_data['name'], node_data['order'], c_node_name
			chart_data['links'].append({
				'source': ordered_nodes[node_data['name']],
				'target': ordered_nodes[c_node_name],
				'source_name': node_data['name'],
				'target_name': c_node_name,
				'link_index': link_index})

			link_index += 1


# return the link index for all possible paths from the given node to root
def root_path(_node_name, _root_name, _node_links=[]):
	result = _node_links

	_node_connections = source_target_nodes[_node_name]

	for _node, _link_index in _node_connections:
		if _node == _root_name:
			result.append(_link_index)
		else:
			result.append(_link_index)
			root_path(_node, _root_name, result)

	return result

# return all the nodes in possible paths to the root
def root_path_nodes(_node_name, _root_name, _nodes=[]):
	if len(_nodes) == 0:
		_nodes.append(_node_name)

	for c in stargazers_network_graph.neighbors(_node_name):
		_nodes.append(c)
		root_path_nodes(c, _root_name, _nodes)

	return list(set(_nodes))

for node in stargazers_network_graph.nodes_iter():
	chart_data['connected_links'][node] += (root_path(node, 'pravj', []))
	chart_data['connected_nodes'][node] += (root_path_nodes(node, 'pravj', []))


with open('chart_data.json', 'w') as f:
	json.dump(chart_data, f)
"""