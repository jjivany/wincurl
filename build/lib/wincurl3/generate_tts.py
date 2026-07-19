from gtts import gTTS
import os

phrases = {
    "challenge_complete.mp3": "Challenge mode complete.",
    "red_wins.mp3": "Red team wins!",
    "yellow_wins.mp3": "Yellow team wins!"
}

for filename, text in phrases.items():
    tts = gTTS(text=text, lang='en', slow=False)
    tts.save(filename)
    # Convert to wav using ffmpeg if possible
    os.system(f"ffmpeg -y -i {filename} -ar 44100 -ac 2 {filename.replace('.mp3', '.wav')}")
    os.remove(filename)
