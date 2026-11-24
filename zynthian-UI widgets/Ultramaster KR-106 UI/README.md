# Ultramaster KR-106 UI v0.5.2

Custom touchscreen control widget for the **original Ultramaster KR-106 LV2 synthesizer** on Zynthian **Tomita**.

**Only the GUI is provided.** It uses the official LV2 widget extension (`zyngui:widget`, API v1), targets plugin URI `https://kayrock.org/kr106`, and does not install or replace an audio engine.

## Features

- Four pages: SYNTH, ENV, PLAY and SET.
- Twenty encoder groups and 56 controller positions.
- Touchscreen sliders, switches, chorus and arpeggiator controls.
- Left/right changes encoder group and up/down changes page; **ALT is not required**.
- Z for the Zynthian native controls and MIDI Learn.
- First tap on another group only selects that group.
- Responsive header: ULTRAMASTER and KR-106 shrink only when required, while `GUI 0.5.1` remains beside the Z button.
- Automatic reload cleanup for Tomita.

## Install using the standard LV2 widget mechanism

Copy the **`kr106_gui-zyngui.lv2`** directory into `/zynthian/zynthian-plugins/lv2-widgets/`. With this repository checked out on the Zynthian, run from its root:

```bash
source /zynthian/config/zynthian_envars.sh
mkdir -p /zynthian/zynthian-plugins/lv2-widgets
cp -a "zynthian-UI widgets/Ultramaster KR-106 UI/kr106_gui-zyngui.lv2" /zynthian/zynthian-plugins/lv2-widgets/
touch /zynthian/config/lv2.stamp
```

When updating, first back up the installed `kr106_gui-zyngui.lv2` directory. After copying, exit the KR-106 control view and reopen it. No audio plugin installation is necessary.

## Validate on Tomita

```bash
source /zynthian/config/zynthian_envars.sh
lv2ls | grep -F 'https://kayrock.org/kr106'
python3 /zynthian/zynthian-ui/.claude/skills/zynthian-lv2-plugin/scripts/lv2_ports.py widget https://kayrock.org/kr106
```

The widget detection should show an API v1 widget path within `lv2-widgets/kr106_gui-zyngui.lv2`.

## Distribution

Project-specific release tag: **`ultramaster-kr106-ui-v0.5.2`**. Future widgets in this repository should have their own tag prefixes and their own project folders.

Consult [CHANGELOG.md](CHANGELOG.md), [RELEASE_NOTES.md](RELEASE_NOTES.md), and the detailed [bundle notes](kr106_gui-zyngui.lv2/README.md).

Community widget licensed under GPL-3.0. Not an official Zynthian or Ultramaster release.
