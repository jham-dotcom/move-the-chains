"""Insert the exported data into template.html and write ../index.html."""
import os
here = os.path.dirname(os.path.abspath(__file__))
t = open(os.path.join(here, "template.html"), encoding="utf-8").read()
g = open("game_data.json", encoding="utf-8").read().replace("</", "<\\/")
f = open("fourth_data.json", encoding="utf-8").read().replace("</", "<\\/")
assert "__GAME_DATA__" in t and "__FOURTH_DATA__" in t
open(os.path.join(here, "..", "index.html"), "w", encoding="utf-8").write(t.replace("__GAME_DATA__", g).replace("__FOURTH_DATA__", f))
print("index.html written")
