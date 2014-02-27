window.$ = function(query) {
    var res =  document.querySelectorAll(query);
    if(res.length == 1) {
        return res[0];
    }
    return res;
};

if (!String.prototype.trim) {
    String.prototype.trim = function () {
        return this.replace(/^\s+|\s+$/g, '');
    };
}

function toggleVisibility(id, on) {
    var el = document.getElementById(id);
    for(var i = 0; i < el.children.length; i++) {
        var cur = el.children[i];
        if(cur.tagName === "PRE") {
            if(on && cur.className.indexOf("hidden") !== -1) {
                cur.className = cur.className.replace("hidden", "");
                cur.className = cur.className.trim();
            }else if(!on && cur.className.indexOf("hidden") === -1) {
                cur.className += " hidden";
            }
        }
    }
}

function unhide(self, id) {
    self.innerHTML = "Piilota";
    toggleVisibility(id, true);
    self.onclick = function() { hide(self, id); };
}

function hide(self, id) {
    self.innerHTML = "Näytä";
    toggleVisibility(id, false);
    self.onclick = function() { unhide(self, id); };
}

function to_random() {
    var all = $(".entries");
    var randel = all.children[Math.floor(Math.random()*all.children.length)];
    window.location.hash = "#"+randel.id;
}

function to_top() {
    window.location.hash = "";
    window.scroll(0,0);
}

function to_bottom() {
    window.location.hash = "";
    window.scroll(0,99999999);
}

function on_hash_change() {
    try {
        window.scrollBy(0,-$("#sticky").offsetHeight-5);
    } catch (err) {

    }
}

window.onhashchange = function() {
    on_hash_change();
};

function change_votes(id, meth) {
    post("/onvote", meth+":"+id, function(data) {
        if(data.indexOf("error") !== -1) {
            alert(data.replace("error", "virhe"));
        }else if(data.indexOf("success") !== -1) {
            var spl = data.split(":");
            var meth = spl[1];
            var id = spl[2];
            var el = document.getElementById(id).getElementsByTagName('*');
            var res = false;
            for(var i = 0; i < el.length; i++) {
                var cur = el[i];
                if(cur.className === "points") {
                    var value = parseInt(cur.innerHTML);
                    cur.innerHTML = value+(meth==="up"?1:-1);
                }
                if(cur.className.indexOf("voted") !== -1) {
                    cur.className = cur.className.replace("voted", "");
                    cur.className = cur.className.trim();
                    res = true;
                }
            }
            if(res===false) {
                for(var i = 0; i < el.length; i++) {
                    var cur = el[i];
                    if(meth==="up" && cur.className.indexOf("upvote") !== -1) {
                        cur.className += " voted";
                    }else if(meth==="down" && cur.className.indexOf("downvote") !== -1) {
                        cur.className += " voted";
                    }
                }
            }
        }
    });
}

function upvote(id) {
    change_votes(id, "up");
}
function downvote(id) {
    change_votes(id, "down");
}

function post(url, data, cb) {
    var httpRequest = new XMLHttpRequest();

    if (!httpRequest) {
      return false;
    }

    httpRequest.onreadystatechange = function() {
        if (httpRequest.readyState === 4) {
            if (httpRequest.status === 200 || httpRequest.status === 400) {
                cb(httpRequest.responseText);
            }
        }
    };

    httpRequest.open('POST', url, true);
    httpRequest.send(data);
}
