import os

with open("main.py", "r") as f:
    code = f.read()

code = code.replace("import collections\n", "import collections\nimport asyncio\nimport sys\n")
code = code.replace('.wav"', '.ogg"')
code = code.replace(".wav',", ".ogg',")
code = code.replace("    def run(self):\n", "    async def run(self):\n")
code = code.replace(
    "            pygame.display.flip()\n", "            pygame.display.flip()\n            await asyncio.sleep(0)\n"
)

net_patch = """        if sys.platform == "emscripten":
            self.connecting = False
            self.running = False
            self.connection_error = "Multiplayer unsupported on Web"
            return
            
        import threading"""
code = code.replace(
    '        self.connection_error = ""\n        import threading', '        self.connection_error = ""\n' + net_patch
)
code = code.replace("def main():\n", "async def main():\n")
code = code.replace("    game.run()\n", "    await game.run()\n")
code = code.replace("    main()\n", "    asyncio.run(main())\n")

with open("main-pygbag.py", "w") as f:
    f.write(code)
print("Patching complete.")
