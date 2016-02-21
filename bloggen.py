import os, markdown

with open("blog.html", "w") as out:
	out.write("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Cel "Colby" Skeggs - CS Project Blog</title>
<link rel="stylesheet" type="text/css" href="blog.css" />
<script src="blog.js"></script>
</head>
<body>
	<div id="blog">
		<h2>Cel's (Colby's) CompSci Project Blog</h2>
""")
	posts = os.listdir("posts")
	for ri, name in enumerate(sorted(posts, reverse=True)):
		i = len(posts) - ri - 1
		with open(os.path.join("posts", name), "r") as p:
			out.write("<div class='post'>\n")
			out.write("Date: %s\n" % name.split(" ",1)[0])
			out.write(markdown.markdown("".join(p)))
			out.write("\n<div class='comments' num='%d'>Comments<br></div></div>\n" % i)
	out.write("""	</div>
</body>
</html>
""")
