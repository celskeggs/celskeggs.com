import webapp2, os, cgi, datetime, sys, time, logging, json
from google.appengine.ext import ndb
from google.appengine.api import urlfetch, xmpp, memcache, users

files = {"/": "index.html", "/awards": "awards.html", "/ccre": "ccre.html", "/style.css": "style.css", "/blog": "blog.html", "/blog.js": "blog.js", "/blog.css": "blog.css", "/gender_110240": "gender.html"}

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

class Comment(ndb.Model):
	post_id = ndb.IntegerProperty(required=True)
	content = ndb.StringProperty(required=True)
	nick = ndb.StringProperty(required=True)
	user = ndb.StringProperty(required=True)
	email = ndb.StringProperty(required=True)
	date = ndb.DateTimeProperty(auto_now_add=True, required=True)

class EndpointAPI(webapp2.RequestHandler):
	def get(self, *a):
		self.response.headers["Content-Type"] = "application/json"
		obj, code = self.process_get(*a)
		self.response.write(json.dumps(obj))
		if code != 200:
			self.abort(code)
	def process_get(self, *a):
		self.abort(405)
	def post(self, *a):
		self.response.headers["Content-Type"] = "application/json"
		param = json.loads(self.request.body)
		obj, code = self.process_post(param, *a)
		self.response.write(json.dumps(obj))
		if code != 200:
			self.abort(code)
	def process_post(self, *a):
		self.abort(405)

def date_to_stamp(x):
	return time.mktime(x.timetuple())

def process_nick(x):
	if "@" in x:
		a, b = x.split("@", 1)
		head, ext = b.rsplit(".", 1)
		return "%s [at] %s...%s.%s" % (a, head[0], head[-1], ext)
	else:
		return x

class CommentsAPI(EndpointAPI):
	def process_get(self):
		comments = memcache.get("comments")
		if comments is None:
			comments_raw = Comment.query().fetch()
			comments = {"comments": [{"content": comment.content, "user": process_nick(comment.nick), "post_id": comment.post_id, "date": date_to_stamp(comment.date)} for comment in comments_raw]}
			memcache.add("comments", comments, 3600)
		logging.debug("The user: %s" % users.get_current_user())
		comments["is_logged_in"] = bool(users.get_current_user())
		if not comments["is_logged_in"]:
			comments["login_url"] = users.create_login_url('/blog')
		else:
			comments["logout_url"] = users.create_logout_url('/blog')
		return comments, 200
	def process_post(self, jbody):
		if type(jbody) != dict or type(jbody.get("content", None)) not in (str, unicode) or type(jbody.get("post_id",None)) != int:
			logging.debug("The bad request: %s" % (jbody,))
			return {"error": "invalid parameter"}, 400
		user = users.get_current_user()
		if not user:
			return {"error": "you must log in"}, 403
		content = jbody["content"]
		post_id = jbody["post_id"]
		assert type(content) in (str, unicode) and type(post_id) == int
		Comment(content=content, user=user.user_id(), email=user.email(), nick=user.nickname(), post_id=post_id).put()
		memcache.delete("comments", 1)
		return {"status": "success"}, 200

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
] + [("/trello-webhook", TogglTrelloWebhook), ("/comments", CommentsAPI)])
