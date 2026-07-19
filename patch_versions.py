import re

# main.py
with open("main.py", "r") as f: text = f.read()
text = text.replace('VERSION = "30"', 'VERSION = "31"')
with open("main.py", "w") as f: f.write(text)

# setup.py
with open("setup.py", "r") as f: text = f.read()
text = text.replace("version='3.0.30'", "version='3.0.31'")
with open("setup.py", "w") as f: f.write(text)

# buildozer.spec
with open("buildozer.spec", "r") as f: text = f.read()
text = text.replace("version = 30", "version = 31")
text = text.replace("android.numeric_version = 30", "android.numeric_version = 31")
with open("buildozer.spec", "w") as f: f.write(text)
