#!/usr/bin/env python3
"""Apply NOVA's first branding and package-identity patch to the upstream Telegram checkout."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "upstream"

def replace_once(path: str, old: str, new: str) -> None:
    p = ROOT / path
    data = p.read_text(encoding="utf-8")
    count = data.count(old)
    if count != 1:
        raise SystemExit(f"Expected exactly one match in {path}, found {count}: {old!r}")
    p.write_text(data.replace(old, new, 1), encoding="utf-8")

# Give NOVA its own Android application identity (debug builds install as this exact package).
props = ROOT / "gradle.properties"
data = props.read_text(encoding="utf-8")
data, count = re.subn(r"(?m)^APP_PACKAGE=.*$", "APP_PACKAGE=org.nova.messenger", data)
if count != 1:
    raise SystemExit(f"Expected one APP_PACKAGE entry, found {count}")
props.write_text(data, encoding="utf-8")

# Remove Telegram's beta suffix so the installed application ID is org.nova.messenger.
replace_once(
    "TMessagesProj_App/build.gradle",
    '            applicationIdSuffix ".beta"\n',
    ""
)

# Brand all launcher/app labels, including the beta label used by the debug manifest.
replace_once(
    "TMessagesProj/src/main/res/values/strings.xml",
    '<string name="AppName">Telegram</string>',
    '<string name="AppName">NOVA</string>'
)
replace_once(
    "TMessagesProj/src/main/res/values/strings.xml",
    '<string name="AppNameBeta">Telegram Beta</string>',
    '<string name="AppNameBeta">NOVA</string>'
)

# Telegram passkeys are restricted to official application IDs; do not expose a broken entry point.
replace_once(
    "TMessagesProj/src/main/java/org/telegram/messenger/BuildVars.java",
    "public static boolean SUPPORTS_PASSKEYS = true;",
    "public static boolean SUPPORTS_PASSKEYS = false;"
)

# Enable Android's RTL layout support for Persian/Arabic UI rendering.
manifest = ROOT / "TMessagesProj/config/debug/AndroidManifest.xml"
data = manifest.read_text(encoding="utf-8")
data, count = re.subn(r'android:supportsRtl="false"', 'android:supportsRtl="true"', data, count=1)
if count != 1:
    raise SystemExit("Could not enable RTL support in debug manifest")
manifest.write_text(data, encoding="utf-8")

print("NOVA branding patch applied:")
print("- App label: NOVA")
print("- Application ID: org.nova.messenger")
print("- Official-only passkey entry point disabled")
print("- Android RTL support enabled")
