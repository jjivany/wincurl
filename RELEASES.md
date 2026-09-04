# WinCurl Releases

## v1.2.0 (Latest)
* **Android GPU Acceleration & Pygame-CE Migration:** We finally resolved a week-long blocker in the Android build chain! 
  * **The Problem:** Transitioning to Pygame-CE's SDL2 backend caused severe conflicts with Android's surface scaling. Using `pygame.SCALED` and `pygame.RESIZABLE` resulted in decoupled touch inputs, broken aspect ratios, and aggressive letterboxing.
  * **The Fix:** We rewrote the rendering pipeline to use a dedicated hardware-accelerated `GPUCanvas` wrapping `pygame._sdl2.video.Renderer`. By initializing the display with `pygame.FULLSCREEN` at `(0, 0)` and deferring to SDL's `logical_size` for coordinate mapping, we achieved pixel-perfect touch input and aspect ratio adaptation without redundant manual scaling.
  * **The Result:** The GL performance on Android is now higher than ever *ever*. The game runs buttery smooth, offloading nearly all rendering to the GPU.
* **Story Mode Grid Expansion:** Fixed an issue where the background grid in the Story Mode cutscenes would fail to cover the bottom-left bounds on ultra-tall modern Android screens by expanding the procedural grid projection.
