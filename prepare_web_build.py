import os

with open("main.py", "r") as f:
    code = f.read()

code = code.replace("import collections\n", "import collections\nimport asyncio\nimport sys\n")
code = code.replace('.wav"', '.ogg"')
code = code.replace(".wav',", ".ogg',")





with open("main-pygbag.py", "w") as f:
    f.write(code)
print("Patching complete.")
