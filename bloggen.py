import os, markdown

with open("blog.html", "w") as out:
	out.write("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Colby Skeggs - CS Project Blog</title>
<link rel="stylesheet" type="text/css" href="blog.css" />
</head>
<body>
	<div id="blog">
		<h2>Colby's CompSci Project Blog</h2>
""")
	for name in sorted(os.listdir("posts"), reverse=True):
		with open(os.path.join("posts", name), "r") as p:
			out.write("<div class='post'>\n")
			out.write("Date: %s\n" % name.split(" ",1)[0])
			out.write(markdown.markdown("".join(p)))
			out.write("\n</div>\n")
	out.write("""	</div>
</body>
</html>
""")
