import webapp2, os, cgi, datetime, sys, time, logging, json
from google.appengine.api import urlfetch, xmpp, memcache

files = {"/": "index.html", "/awards": "awards.html", "/ccre": "ccre.html", "/style.css": "style.css", "/blog": "blog.html", "/blog.css": "blog.css", "/gender_110240": "gender.html"}

class MainPage(webapp2.RequestHandler):
	def get(self):
		path = self.request.path
		assert path in files, "Bad path (somehow?): %s" % path
		self.response.headers["Content-Type"] = "text/css" if path.endswith(".css") else "text/html"
		with open(files[path], "r") as f:
			while True:
				x = f.read(4096)
				if not x: break
				self.response.write(x)

from secrets import *

def trello_get_labels(cid):
	result = urlfetch.fetch("https://api.trello.com/1/card/%s/labels?key=%s&token=%s" % (cid, KEY, TOKEN), validate_certificate=True)
	assert result.status_code == 200
	return [label["name"] for label in json.loads(result.content) if "name" in label]

def toggl_headers():
	return {"Content-Type": "application/json", "Authorization": TOGGL_HEADER}

def toggl_list_projects(workspace=TOGGL_WORKSPACE):
	key = "toggl.workspaces.projects.%d" % workspace
	old = memcache.get(key)
	if old is not None:
		j = json.loads(old)
	else:
		result = urlfetch.fetch("https://www.toggl.com/api/v8/workspaces/%d/projects" % workspace, headers=toggl_headers(), validate_certificate=True)
		assert result.status_code == 200
		jr = result.content
		memcache.add(key, jr, time=30)
		j = json.loads(jr)
	return [(project["name"], project["id"]) for project in j if "id" in project and "name" in project]

def toggl_current_timer():
	result = urlfetch.fetch("https://www.toggl.com/api/v8/time_entries/current", headers=toggl_headers(), validate_certificate=True)
	assert result.status_code == 200
	return json.loads(result.content).get("data",{})

def toggl_start_timer(description, project):
	assert type(project) == int
	request = {"time_entry": {"description": description, "pid": project, "created_with": "custom toggl-trello integration"}}
	result = urlfetch.fetch("https://www.toggl.com/api/v8/time_entries/start", payload=json.dumps(request), method="POST", headers=toggl_headers(), validate_certificate=True)
	assert result.status_code == 200
	return json.loads(result.content).get("data",{}).get("id",None)

def toggl_stop_timer(timer):
	result = urlfetch.fetch("https://www.toggl.com/api/v8/time_entries/%d/stop" % timer, method="PUT", headers=toggl_headers(), validate_certificate=True)
	assert result.status_code == 200

def toggl_lookup_project(name):
	return dict(toggl_list_projects()).get(name, None)

class TogglTrelloWebhook(webapp2.RequestHandler):
	def head(self):
		self.response.headers["Content-Type"] = "text/plain"
		self.response.write("OK")
	def get(self):
		self.response.headers["Content-Type"] = "text/plain"
		self.response.write("OK")
	def post(self):
		if self.request.remote_addr not in ["107.23.104.115", "107.23.149.70", "54.152.166.250", "54.164.77.56"]:
			self.abort(403)
		jobj = json.loads(self.request.body)
		data = jobj.get("action",{}).get("data",{})
		name = data.get("card",{}).get("name",None)
		cid = data.get("card",{}).get("id",None)
		if data and data.get("old",{}).get("idList",None) != None and name != None and cid != None:
			if data.get("listAfter",{}).get("id",None) == DOING_LIST:
				start = True
			elif data.get("listBefore",{}).get("id",None) == DOING_LIST:
				start = False
			else:
				start = None
			if start != None:
				labels = trello_get_labels(cid)
				if len(labels) == 1:
					label = labels[0]
					message = "Started working on: %s (%s) -> %s" if start else "Stopped working on: %s (%s) -> %s"
					project = toggl_lookup_project(label)
					current = toggl_current_timer()
					if current == None and start:
						toggl_start_timer(name, project)
						done = "started timer"
					elif current != None and current.get("pid", None) == project and not start:
						toggl_stop_timer(current["id"])
						done = "stopped timer"
					else:
						done = "nothing"
#					xmpp.send_message(["EMAIL@gmail.com"], message % (name, label, done))
		self.response.headers["Content-Type"] = "text/plain"
		self.response.write("OK")

application = webapp2.WSGIApplication([
	(key, MainPage)
    for key in files.keys()
] + [("/trello-webhook", TogglTrelloWebhook)])
