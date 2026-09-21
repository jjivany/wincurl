# WinCurl Releases History

## Build 125 💍 ☮️ 😄 💍 ✌️ 😃 💍 ☮️
- **Cut-Scene Visuals:** Fixed transparent pixel artifacting by using proper BLEND_RGBA_MULT masking.
- **Customization Options:** Replaced generic goggles with stylized sunglasses on all avatars!
- **Challenge Mode Tweaks:** The "clear the house" rules now count opponent stones knocked out of the active rings (distance > 252) as successes.
- **Crowd Controls:** Added an option to completely toggle off the crowd to maximize FPS on low-end devices, along with a festive new "Holiday Lights" mode!
- **Performance Polish:** Pre-generated cut-scene assets and boss portraits significantly reduce loading stutters.
- **Onward and Upward:** The core engine is cleaner than ever. We're onward and upward from here!

## Build 123 (Final Revision) 💍 ☮️ 😄 💍 ✌️ 😃 💍 ☮️
- **Animation Fix:** Fixed a rendering issue on mobile where the curler's legs were getting cut off at the bottom of the screen during the throwing animation!

## Build 123 (Revision 9) 💍 ☮️ 😄 💍 ✌️ 😃 💍 ☮️
- **Web Build Fixes:** Fixed a critical bug causing the game to fail to load on Itch.io CDNs.
- **Hair Customization:** The in-game curler animation now perfectly reflects your chosen hair length and style!
- **Options Preview:** Character customization choices are now instantly previewed in the Options Menu! 
- **Menu Navigation:** Fixed an issue where clicking Options from the pause menu incorrectly directed to the Main Menu.

## Build 123 (Revision 8)
- **Game Customization:** Corrected the UI option handling so characters inside the game use the selected hair style and colour.
- **Window Title:** Cleaned up the window title formatting and removed emojis.

## Build 123 (Revision 6)

- **Universal APK Harmonization:** We have harmonized what used to be two separate downloads (64-bit and 32-bit legacy) into a single, unified Android file. This single APK automatically runs at peak efficiency on both modern and older legacy devices.
- **Uncapped GL Performance:** Removed the Pygame software framerate limit (`clock.tick(60)`) on Android. The game now relies entirely on native hardware VSync, allowing it to run at the absolute maximum refresh rate of your display (e.g., 90Hz, 120Hz, or 144Hz) for buttery-smooth rendering without frame pacing stutters.

## Build 123 (Revision 5)

- **Replay System Disabled:** Removed the "action replay" feature at the end of ends and matches, as it was causing glitches and breaking the bot mode simulation.

## Build 123 (Revision 4)

- **Critical Lockup Fix:** Addressed a severe bug introduced in Revision 3 (Build 123) that caused the game to completely lock up (freeze) immediately upon clicking "New Match" or completing the first Story Mode cutscene. This was due to a typo in a surface reference when transitioning to the `COIN_TOSS` state, which silently crashed the Android render thread.
- **AI Personalities:** Story Mode AI opponents now have distinct playstyles and difficulties based on their character (e.g., aggressive, defensive, balanced).
- **Match Highlight Replays:** The very last stone of an end is now automatically recorded and played back seamlessly as a highlight replay, adding dramatic flair without slowing down the pacing of the rest of the game.

## Build 123 (Revision 3)
*Note: This should be the final revision to build 123.*

- **Android GL Performance:** Enforced explicit matching of the native Android `ABGR8888` GL texture format in the Pygame-CE software canvas. This completely bypassed the heavy CPU-bound pixel conversions and effectively eliminated the Android framerate bottleneck, achieving peak performance.
- **Full Screen Fix:** Added the missing `pygame.SCALED` flag when toggling full screen on desktop, ensuring the window correctly scales rather than awkwardly resizing.
- **Story Mode Crash Fix:** Resolved an internal Pygame-CE crash on Android (`ValueError: width greater than radius`) triggered when completing the first match by safely rendering solid inner geometry for the trophies.
- **Ring Emoji:** Added the ring emoji to the version identifier to commemorate the ring choice feature update.

## Build 120 (Latest)

First and foremost: **I want to sincerely apologize to the community for the broken and missing builds over the past week.** 

As some of you noticed, the transition from Build 119 to 120 has been rocky. We completely overhauled the Android build chain to finally fix the persistent scaling and performance issues, which caused a domino effect of broken compilation pipelines, failing CI/CD `butler` deployments to itch.io, and unplayable preview builds. We appreciate your patience while we wrestled with the infrastructure to get things right.

The good news is that the struggle was worth it. We have fully migrated away from SDL2's flawed scaling flags and implemented a custom `GPUCanvas` wrapper using Pygame-CE's `Renderer`. This means that **GL performance on Android is now higher than ever.** 

To put it bluntly: we have genocided all of the bugs in WinCurl 3, especially those impacting Android. We've swept up the code so thoroughly that I can guarantee there are absolutely no insect bodies left for you to find.

### Changes in Build 120:
- **Major Android Engine Overhaul:** Switched to `GPUCanvas` hardware rendering locked at native resolution for maximum framerates without visual artifacts.
- **Fixed UI Elements:** The strike-through line in the challenge menu and the curler's pants (which were both disappearing due to a rotation math bug in the new renderer) have been fixed!
- **Fixed Trajectory Line:** Dotted and 1-pixel trajectory lines are now drawn with solid texture quads to prevent missing pixels on high-DPI Android displays.
- **Fixed Story Mode Grid:** The background grid in cutscenes now properly extends across ultra-wide mobile displays.
- **Fixed Mute Button:** Restored touch event routing for the mute button on the main menu.
- **Fixed Pause Screen:** Replaced the buggy alpha surface overlay with native hardware-accelerated translucent textures.
- **Fixed Multiplayer Online Match:** Joining an online match after playing a Challenge level would mistakenly limit each team to 1 rock. Network state initialization has been fixed to ensure you always get the full 8 rocks.

### Build 120 (Revision 1)
- **IRC Matchmaking:** Replaced the legacy Dalnet IRC server with a newer, less laggy server (Rizon) for much faster and more reliable matchmaking connection speeds.
- **Outer Rings:** Re-styled the "Outer Rings" settings menu option to feature colored text and drop shadows for better contrast and legibility.
- **Android Heat Management:** Restructured the main game loop from a `tick_busy_loop` to a standard `tick` on Android to drastically reduce processor load and prevent thermal throttling.
- **UI Enhancements:** Restored background rendering on the options menu that was occasionally being clipped, fixed head/hat aspect ratios for the character portrait, and added a green curling rock icon to the pause menu.

## Build 119
- Initial optimizations for the Android build pipeline.
- Gameplay balance tweaks for Story Mode.
