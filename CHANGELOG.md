# WinCurl 3.0 Changelog

## Build 97 & 97.post1
- **Clipboard Fixes**: 
  - Fixed an issue on Linux systems where `pygame.scrap` would cache the clipboard and constantly paste stale history. It now properly fetches the latest text using a forced `pygame.scrap.init()`.
  - Added safety checks to only paste the first line of the clipboard, preventing multi-line spam in the chat input.
- **Crash Fixes**: 
  - Fixed an `UnboundLocalError` crash on Android devices caused by a shadowing local `import sys` statement inside the main event loop.

## Build 96 & 96.post1
- **Mac Support**: 
  - Added `Cmd+V` paste support specifically for macOS devices.
  - Added `Cmd+Enter` to toggle fullscreen.

