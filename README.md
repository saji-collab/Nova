# NOVA for Android

NOVA is an unofficial Android client project based on the public Telegram for Android source code.

> **Status:** Phase 0 / upstream build foundation. This repository currently contains the reproducible source-bootstrap workflow, not a rebranded or release-ready NOVA APK.

## Upstream

- Source: https://github.com/DrKLO/Telegram
- License: GNU GPL v2 or later. See the upstream license and preserve all copyright and license notices.
- Upstream build requirements currently documented by the project: Android Studio 2025.1.4, Android SDK 36, Android NDK 27.2.12479018.

The workflow fetches the upstream repository including its submodules at build time. It does not copy or claim ownership of Telegram source files in this repository.

## Build the upstream baseline

1. Open **Actions**.
2. Select **NOVA Android baseline build**.
3. Choose **Run workflow**.
4. Download the `NOVA-debug-apk` artifact when the job completes.

The artifact is a development baseline from upstream. It is **not yet the branded NOVA release**.

## NOVA roadmap

1. Establish reproducible upstream build.
2. Apply NOVA application identity, package ID, app name, icons and dark visual identity.
3. Add NOVA-specific features behind isolated modules/feature flags.
4. Configure NOVA-owned Telegram API credentials, Firebase configuration and release signing.
5. Run regression/security checks and publish source changes and release artifacts.

## Required before public release

- A Telegram API ID and API hash created for this application: https://my.telegram.org
- NOVA-owned Firebase Android app configuration if push notifications are enabled.
- A private release signing key. Never commit keystores or passwords.
- Publication of the modified source and all required license notices.

NOVA is an independent, unofficial project and is not affiliated with Telegram.
