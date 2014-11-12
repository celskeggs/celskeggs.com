import webapp2, os, cgi, datetime, sys, time, logging, json

#- url: /static
#  static_dir: static
#  secure: always

class MainPage(webapp2.RequestHandler):
	def get(self):
		self.response.headers["Content-Type"] = "text/html"
		with open("index.html", "r") as f:
			while True:
				x = f.read(4096)
				if not x: break
				self.response.write(x)

application = webapp2.WSGIApplication([
	('/', MainPage)
])
