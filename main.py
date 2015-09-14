import webapp2, os, cgi, datetime, sys, time, logging, json

#- url: /static
#  static_dir: static
#  secure: always

files = {"/": "index.html", "/awards": "awards.html", "/ccre": "ccre.html", "/style.css": "style.css", "/blog": "blog.html", "/blog.css": "blog.css"}

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

application = webapp2.WSGIApplication([
	(key, MainPage)
    for key in files.keys()
])
