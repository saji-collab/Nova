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

# Install the first native NOVA feature: a working Privacy Center entry in Settings.
privacy_java = ROOT / "TMessagesProj/src/main/java/org/telegram/ui/NovaPrivacyActivity.java"
privacy_java.write_text(r'''package org.telegram.ui;

import android.app.Activity;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.CompoundButton;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Switch;
import android.widget.TextView;
import android.graphics.Color;
import android.graphics.Typeface;
import android.content.SharedPreferences;
import android.view.Window;
import android.view.WindowManager;

public class NovaPrivacyActivity extends Activity {
    private static final int BG = 0xFF101116;
    private static final int PANEL = 0xFF1B1D25;
    private static final int TEXT = 0xFFF4F5F8;
    private static final int MUTED = 0xFF9DA3B2;
    private SharedPreferences prefs;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(BG);
        prefs = getSharedPreferences("nova_privacy", MODE_PRIVATE);
        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(BG);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(20), dp(24), dp(20), dp(28));
        scroll.addView(root);
        TextView title = new TextView(this);
        title.setText("NOVA Privacy Center");
        title.setTextColor(TEXT);
        title.setTextSize(25);
        title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        root.addView(title);
        TextView subtitle = new TextView(this);
        subtitle.setText("کنترل‌های امنیت و حریم خصوصی این دستگاه");
        subtitle.setTextColor(MUTED);
        subtitle.setTextSize(14);
        subtitle.setPadding(0, dp(8), 0, dp(22));
        root.addView(subtitle);
        addSwitch(root, "محافظت از اسکرین‌شات", "جلوگیری از ثبت تصویر صفحه در بخش‌های NOVA که این محافظت را پشتیبانی می‌کنند.", "secure_screens", false);
        addInfo(root, "قفل برنامه و چت", "در حال توسعه؛ تا زمان تکمیل قفل سراسری، این گزینه فعال‌نمایی نشده است.");
        addInfo(root, "حریم خصوصی حساب", "تنظیمات آخرین بازدید، شماره تلفن و وضعیت آنلاین از کنترل‌های رسمی حساب تلگرام استفاده می‌کنند.");
        setContentView(scroll);
    }

    private void addSwitch(LinearLayout root, String name, String detail, String key, boolean def) {
        LinearLayout card = card(root);
        LinearLayout column = new LinearLayout(this);
        column.setOrientation(LinearLayout.VERTICAL);
        column.setPadding(dp(16), dp(14), dp(16), dp(14));
        card.addView(column);
        Switch toggle = new Switch(this);
        toggle.setText(name);
        toggle.setTextColor(TEXT);
        toggle.setTextSize(16);
        toggle.setChecked(prefs.getBoolean(key, def));
        column.addView(toggle);
        TextView description = new TextView(this);
        description.setText(detail);
        description.setTextColor(MUTED);
        description.setTextSize(13);
        description.setPadding(0, dp(8), 0, 0);
        column.addView(description);
        toggle.setOnCheckedChangeListener((button, checked) -> {
            prefs.edit().putBoolean(key, checked).apply();
            if (checked) getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
            else getWindow().clearFlags(WindowManager.LayoutParams.FLAG_SECURE);
        });
        if (prefs.getBoolean(key, def)) getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
    }

    private void addInfo(LinearLayout root, String name, String detail) {
        LinearLayout card = card(root);
        LinearLayout column = new LinearLayout(this);
        column.setOrientation(LinearLayout.VERTICAL);
        column.setPadding(dp(16), dp(15), dp(16), dp(15));
        card.addView(column);
        TextView heading = new TextView(this);
        heading.setText(name);
        heading.setTextColor(TEXT);
        heading.setTextSize(16);
        heading.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        column.addView(heading);
        TextView body = new TextView(this);
        body.setText(detail);
        body.setTextColor(MUTED);
        body.setTextSize(13);
        body.setPadding(0, dp(7), 0, 0);
        column.addView(body);
    }

    private LinearLayout card(LinearLayout root) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setBackgroundColor(PANEL);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, -2);
        lp.bottomMargin = dp(12);
        root.addView(card, lp);
        return card;
    }
    private int dp(float v) { return (int)(v * getResources().getDisplayMetrics().density + 0.5f); }
}
''', encoding="utf-8")

# Register the native screen in the app manifest.
app_manifest = ROOT / "TMessagesProj/src/main/AndroidManifest.xml"
manifest_text = app_manifest.read_text(encoding="utf-8")
needle = '    <application'
idx = manifest_text.find(needle)
if idx < 0:
    raise SystemExit("Could not find application element in main manifest")
activity = '        <activity android:name="org.telegram.ui.NovaPrivacyActivity" android:exported="false" android:screenOrientation="unspecified" />\n'
if "NovaPrivacyActivity" not in manifest_text:
    app_open = manifest_text.find(">", idx)
    if app_open < 0:
        raise SystemExit("Malformed application element in main manifest")
    manifest_text = manifest_text[:app_open + 1] + "\n" + activity + manifest_text[app_open + 1:]
app_manifest.write_text(manifest_text, encoding="utf-8")

# Add a Settings row and route it to the native NOVA screen.
settings = ROOT / "TMessagesProj/src/main/java/org/telegram/ui/SettingsActivity.java"
src = settings.read_text(encoding="utf-8")
row_needle = '        items.add(SettingCell.Factory.of(10, IconBackgroundColors.PURPLE.top, IconBackgroundColors.PURPLE.bottom, R.drawable.settings_language, getString(R.string.SettingsLanguage), LocaleController.getCurrentLanguageName()));'
if src.count(row_needle) != 1:
    raise SystemExit("Settings language row anchor changed; refusing unsafe patch")
src = src.replace(row_needle, row_needle + '\n        items.add(SettingCell.Factory.of(28, 0xFF4B75E8, 0xFF7655C9, R.drawable.settings_privacy, "NOVA Privacy Center", "Privacy controls"));', 1)
click_needle = "            case 10:\n                presentSettingFragment(new LanguageSelectActivity());\n                break;"
if src.count(click_needle) != 1:
    raise SystemExit("Settings click handler anchor changed; refusing unsafe patch")
src = src.replace(click_needle, click_needle + '\n            case 28:\n                getParentActivity().startActivity(new android.content.Intent(getParentActivity(), NovaPrivacyActivity.class));\n                break;', 1)
settings.write_text(src, encoding="utf-8")
