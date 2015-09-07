import os, markdown

with open("blog.html", "w") as out:
	with open("header.html", "r") as p:
		out.write("".join(p))
	out.write("\n")
	for name in sorted(os.listdir("posts")):
		with open(os.path.join("posts", name), "r") as p:
			out.write("<div style='padding: 30px;'>\n")
			out.write("Date: %s\n" % name.split(" ",1)[0])
			out.write(markdown.markdown("".join(p)))
			out.write("\n</div>\n\n")
	with open("footer.html", "r") as p:
		out.write("".join(p))
	out.write("\n")
