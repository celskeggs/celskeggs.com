function fetch_data(x) {
	fetch("/comments", {method: "GET", mode: "same-origin", credentials: "same-origin", cache: "no-cache"}).then(res => res.json()).then(x);
}
function post_data(json, cb) {
	fetch("/comments", {method: "POST", body: JSON.stringify(json), mode: "same-origin", credentials: "same-origin", cache: "no-cache"}).then(cb);
}
window.onload = function() {
	fetch_data(function(json) {
		var cs = document.getElementsByClassName("comments");
		var ces = {};
		for (var i = 0; i < cs.length; i++) {
			var c = cs[i];
			var post_id = parseInt(c.getAttribute("num"));
			ces[post_id] = c;
		}
		for (var i = 0; i < json.comments.length; i++) {
			var j = json.comments[i];
			var c = ces[j.post_id];
			if (c) {
				var b = document.createElement("div");
				b.className = "comment";
				var date = new Date(j.date * 1000).toLocaleString();
				b.textContent = "(" + date + ") " + j.user + ": " + j.content;
				c.appendChild(b);
			} else {
				console.log("no post for:", j);
			}
		}
		for (var i = 0; i < cs.length; i++) {
			var c = cs[i];
			if (json.is_logged_in) {
				var b = document.createElement("div");
				b.className = "addcomment";
				var twrap = document.createElement("div");
				twrap.className = "addcommentwrap";
				var tdiv = document.createElement("div");
				tdiv.className = "addcommentdiv";
				var tdiv2 = document.createElement("div");
				tdiv2.className = "addcommentbtnpad";
				var tbtn = document.createElement("div");
				tbtn.className = "addcommentbtn";
				var text = document.createElement("input");
				text.type = "text";
				text.value = "";
				text.post_id = parseInt(c.getAttribute("num"));
				text.placeholder = "Write a comment... (your Google account nickname will be publicly shown)";
				var button = document.createElement("button");
				button.onclick = function() {
					if (this.value == "") { return false; }
					post_data({"content": this.value, "post_id": this.post_id}, function() {
						this.value = "";
					}.bind(this));
					if (this.value != "") {
						this.value = "...";
					}
					return false;
				}.bind(text);
				text.onkeyup = function(e) {
					if ((e || window.event).keyCode == 13) {
						this.onclick();
						return false;
					}
					return true;
				}.bind(button);
				button.textContent = "Add";
				tbtn.appendChild(button);
				b.appendChild(tbtn);
				tdiv.appendChild(tdiv2);
				tdiv2.appendChild(text);
				b.appendChild(tdiv);
				twrap.appendChild(b);
				c.appendChild(twrap);
			}
			var linkbox = document.createElement("div");
			linkbox.className = "loginbox";
			var a = document.createElement("a");
			a.textContent = json.is_logged_in ? "Log out" : "Log in via Google";
			a.href = json.is_logged_in ? json.logout_url : json.login_url;
			linkbox.appendChild(a);
			c.appendChild(linkbox);
		}
	});
};
