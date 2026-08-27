### What's New in Build 114
- **Controller Navigation Improvements**: The left analog stick can now be used to navigate menus, matching the D-pad functionality.
- **Menu Highlight Fixes**: Fixed a bug where controller selection didn't highlight the "BACK TO MENU" button in the story map and the "QUIT TO MENU" button in the pause menu. They now light up correctly when selected.
- **Audio Pitch Fixes**: Corrected the frequency parameters for the "HARD" synth speech voice, resolving the distorted audio when sweeping.
- **Web Build Fixes**: Re-built the web version (`pygbag`) to apply the recent controller and audio fixes, resolving an issue where the web version was stuck on a grey screen.

### What's New in Build 113
- **Automated iOS IPA Builds**: A new GitHub Actions pipeline has been implemented to automatically build and deploy an `.ipa` to itch.io for iOS users! (Note: The `.ipa` is currently unsigned, so it requires side-loading via tools like AltStore).
- **Crucial Mac Audio Fixes (From 112)**: Resolved an issue where background music and audio initialization would crash the game on macOS (especially in virtualized environments like QEMU). The audio system now correctly catches initialization failures and silences the game rather than crashing it.
- **Steam Controller Module Optional (From 112)**: The `sc_driver` Steam Controller library is now 100% optional. In previous builds, requiring it to be loaded strictly broke the game for Mac users. It will now gracefully fallback to standard controls if the module isn't present or throws an error.
- **Itch.io Mac Packaging (From 112)**: The Mac build is now packaged as a standard `.zip` file on itch.io instead of a `.dmg`, allowing the Itch desktop app to natively install and launch it seamlessly!
