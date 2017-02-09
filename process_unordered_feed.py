import rethinkdb as r

con = r.connect()

db_name = 'unordered_feed'
table_name = 'feed'

db_ref = r.db(db_name).table(table_name)

# add a new column (usefull document or not) for all events
db_ref.update({'inert': 0}).run(con)

# group all the events by their repository name
grouped_events = db_ref.group('repo').order_by('time').run(con)

# event groups having a single entry
single_event_groups = db_ref.group('repo').count().ungroup().filter({'reduction': 1}).pluck('group').run(con)
single_event_groups = [g['group'] for g in single_event_groups]

# tag single event groups as useless for further use
for group in single_event_groups:
	db_ref.filter({'repo': group}).update({'inert': 1}).run(con)

useful_events = db_ref.filter({'inert': 0}).group('repo').order_by('time').run(con)
print len(useful_events)
