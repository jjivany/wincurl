import urllib.parse
import os

subreddit = "IndieGaming"
title = "I couldn't find a good Curling game for Android, so I spent the last few months building my own in Python. It's completely free and open-source."
body = """Hey everyone,

I’ve always loved the strategy and physics of curling, but mobile stores are mostly filled with hyper-casual knockoffs. I wanted something with a real physics engine, a story mode, and challenging AI. 

So, I built **WinCurl 3.0**. I just released Build 49 today, which adds high-res portraits, deeper story mode cutscenes, Mario Kart style trophies for beating bosses, and a bunch of Android performance optimizations (it runs super smooth now!).

**Features:**
*   Realistic stone physics and sweeping mechanics
*   A full Story Mode with unique opponents and cutscenes
*   Challenge modes and local multiplayer
*   Built entirely in Python/Pygame!

It's completely free, no ads, no microtransactions. I just want people to play it and tell me what they think!

**Links:**
🔗 Download the Android APK: https://github.com/jjivany/wincurl/releases/latest
🔗 GitHub Repo (Open Source): https://github.com/jjivany/wincurl

Let me know if you have any feedback or run into any bugs!"""

url = f"https://www.reddit.com/r/{subreddit}/submit?title={urllib.parse.quote(title)}&text={urllib.parse.quote(body)}"

os.system(f"firefox '{url}'")
