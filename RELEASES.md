# WinCurl Releases History

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

## Build 119
- Initial optimizations for the Android build pipeline.
- Gameplay balance tweaks for Story Mode.
