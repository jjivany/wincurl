import re

# main.py
with open("main.py", "r") as f: text = f.read()
text = text.replace('VERSION = "32"', 'VERSION = "33"')
with open("main.py", "w") as f: f.write(text)

# setup.py
with open("setup.py", "r") as f: text = f.read()
text = text.replace("version='3.0.32'", "version='3.0.33'")
with open("setup.py", "w") as f: f.write(text)

# buildozer.spec
with open("buildozer.spec", "r") as f: text = f.read()
text = text.replace("version = 32", "version = 33")
text = text.replace("android.numeric_version = 32", "android.numeric_version = 33")
with open("buildozer.spec", "w") as f: f.write(text)
