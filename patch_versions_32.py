import re

# main.py
with open("main.py", "r") as f: text = f.read()
text = text.replace('VERSION = "31"', 'VERSION = "32"')
with open("main.py", "w") as f: f.write(text)

# setup.py
with open("setup.py", "r") as f: text = f.read()
text = text.replace("version='3.0.31'", "version='3.0.32'")
with open("setup.py", "w") as f: f.write(text)

# buildozer.spec
with open("buildozer.spec", "r") as f: text = f.read()
text = text.replace("version = 31", "version = 32")
text = text.replace("android.numeric_version = 31", "android.numeric_version = 32")
with open("buildozer.spec", "w") as f: f.write(text)
