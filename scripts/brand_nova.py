#!/usr/bin/env python3
"""Apply NOVA's first branding and package-identity patch to the upstream Telegram checkout."""
from pathlib import Path
import json
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

# Supply a build-only Firebase placeholder for NOVA's package ID.
# Push notifications / Firebase services remain unconfigured until NOVA has its own project.
firebase = ROOT / "TMessagesProj_App/google-services.json"
firebase.write_text(json.dumps({
    "project_info": {
        "project_number": "000000000000",
        "project_id": "nova-build-placeholder",
        "storage_bucket": "nova-build-placeholder.invalid"
    },
    "client": [{
        "client_info": {
            "mobilesdk_app_id": "1:000000000000:android:00000000000000000000000000000000",
            "android_client_info": {"package_name": "org.nova.messenger"}
        },
        "api_key": [{"current_key": "NOVA_BUILD_ONLY_NO_FIREBASE_KEY"}],
        "services": {}
    }],
    "configuration_version": "1"
}, indent=2) + "\n", encoding="utf-8")

print("NOVA branding patch applied:")
print("- App label: NOVA")
print("- Application ID: org.nova.messenger")
print("- Official-only passkey entry point disabled")
print("- Android RTL support enabled")
print("- Build-only Firebase placeholder generated; Firebase services are not configured")

# Add a NOVA shortcuts section that routes to Telegram's real native feature screens.
# These are functional entry points, not placeholder controls: passcode/privacy,
# download/data management, and smart chat folders are handled by upstream screens.
settings = ROOT / "TMessagesProj/src/main/java/org/telegram/ui/SettingsActivity.java"
src = settings.read_text(encoding="utf-8")
row_anchor = '        items.add(SettingCell.Factory.of(10, IconBackgroundColors.PURPLE.top, IconBackgroundColors.PURPLE.bottom, R.drawable.settings_language, getString(R.string.SettingsLanguage), LocaleController.getCurrentLanguageName()));'
if src.count(row_anchor) != 1:
    raise SystemExit("Settings language row anchor changed; refusing unsafe patch")
nova_rows = """
        items.add(UItem.asShadow(null));
        items.add(SettingCell.Factory.of(28, IconBackgroundColors.GREEN.top, IconBackgroundColors.GREEN.bottom, R.drawable.settings_privacy, "NOVA Privacy", "Passcode and account privacy"));
        items.add(SettingCell.Factory.of(29, IconBackgroundColors.BLUE_DEEP.top, IconBackgroundColors.BLUE_DEEP.bottom, R.drawable.settings_data, "NOVA Downloads", "Storage and download controls"));
        items.add(SettingCell.Factory.of(30, IconBackgroundColors.BLUE_ALT.top, IconBackgroundColors.BLUE_ALT.bottom, R.drawable.settings_folders, "NOVA Smart Folders", "Organize chats and conversations"));
"""
src = src.replace(row_anchor, row_anchor + nova_rows, 1)
click_anchor = """            case 10:
                presentSettingFragment(new LanguageSelectActivity());
                break;"""
if src.count(click_anchor) != 1:
    raise SystemExit("Settings click handler anchor changed; refusing unsafe patch")
nova_cases = """
            case 28:
                presentSettingFragment(new PrivacySettingsActivity());
                break;
            case 29:
                presentSettingFragment(new DataSettingsActivity());
                break;
            case 30:
                presentSettingFragment(new FiltersSetupActivity());
                break;"""
src = src.replace(click_anchor, click_anchor + nova_cases, 1)
settings.write_text(src, encoding="utf-8")
print("NOVA native shortcuts added: Privacy, Downloads, Smart Folders")
