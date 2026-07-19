import re
import os
import math
import struct

def patch_main():
    filepath = 'main.py'
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        return

    with open(filepath, 'r') as f:
        content = f.read()

    # 1. Fixed Fractal Position (Y=600 for mobile clearance)
    draw_menu_pattern = r"(canvas\.blit\(rotated_fractal, \(cx - rotated_fractal\.get_width()//2, \d+ - rotated_fractal\.get_height()//2\)\))"
    content = re.sub(draw_menu_pattern, "canvas.blit(rotated_fractal, (cx - rotated_fractal.get_width()//2, 600 - rotated_fractal.get_height()//2))", content)

    # 2. Improved VOSIM (Damped-Sine Formant Synthesis for Vocal Clarity)
    # Replaces additive sine with Damped-Sinusoid pulses which sound human, not 'chiptune'
    vosim_full_pattern = r"def _synthesize_vosim_phrase\(self, phrase, duration\):[\s\S]*?return self\._create_wav_sound\(buf, 44100\)"
    
    new_vosim = """def _synthesize_vosim_phrase(self, phrase, duration):
        steps = int(44100 * duration); buf = bytearray(steps * 4)
        # Formants (F1, F2) for vocal clarity
        f1, f2 = (600, 1800) if phrase == "HURRY" else (500, 1600) if phrase == "HARD" else (400, 1900)
        
        # Damped pulse synthesis (Simulates vocal tract resonances)
        for i in range(steps):
            t = i / 44100
            # Vocal pulse train: damped sine waves per formant
            phase = (i * 120 / 44100) % 1.0 # 120Hz fundamental pitch
            pulse = math.exp(-phase * 15.0) 
            # Damped Sinusoids = Actual Vocal Sound
            val = (pulse * math.sin(2 * math.pi * f1 * phase) + 0.6 * pulse * math.sin(2 * math.pi * f2 * phase))
            # Hard consonant transient boost for clarity
            if i < 200: val += 0.5 * math.sin(2 * math.pi * 3000 * t) 
            
            sample = int(max(-1.0, min(1.0, val)) * 28000)
            struct.pack_into('<hh', buf, i * 4, sample, sample)
        return self._create_wav_sound(buf, 44100)"""
    
    content = re.sub(vosim_full_pattern, new_vosim, content)

    # 3. Restore "WinCurl" Scream (Hard-switched square wave sweep, no wobble)
    sega_method = """    def _synthesize_sega_speech(self):
        steps = int(44100 * 0.25); buf = bytearray(steps * 4) # Shorter, punchier
        for i in range(steps):
            t = i / 44100; freq = 880 - (i * 600 / steps) # Pure descending sweep
            # Hard-switched Square wave for scream attack (no wobble oscillator)
            val = 1.0 if math.sin(2*math.pi*freq*t) > 0 else -1.0
            val *= math.exp(-i / (steps * 0.4)) # Crisp decay
            sample = int(max(-1.0, min(1.0, val)) * 28000)
            struct.pack_into('<hh', buf, i * 4, sample, sample)
        return self._create_wav_sound(buf, 44100)
"""
    # Clean out any old version first
    if "def _synthesize_sega_speech" in content:
        content = re.sub(r"    def _synthesize_sega_speech\(self\):[\s\S]*?return self\._create_wav_sound\(buf, 44100\)\n", "", content)
    
    # Insert new version (placed before _create_wav_sound to be safe)
    content = content.replace("    def _create_wav_sound", sega_method + "\n    def _create_wav_sound")
    
    # Ensure it's called
    if "self.snd_scream =" not in content:
        # Looking for init block
        init_pattern = r"(self\.ch_voice = pygame\.mixer\.Channel\(6\))"
        content = re.sub(init_pattern, r"\1\n        self.snd_scream = self._synthesize_sega_speech()\n        self.ch_sfx.play(self.snd_scream)", content)

    with open(filepath, 'w') as f:
        f.write(content)
    print("Patch applied: Vocal formant synthesis restored and scream stabilized.")

if __name__ == "__main__":
    patch_main()
