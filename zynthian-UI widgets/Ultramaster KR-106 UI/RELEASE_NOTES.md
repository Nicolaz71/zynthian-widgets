# Ultramaster KR-106 UI v0.5.1

First community release of the custom Zynthian Tomita Python/Tk widget for the **original Ultramaster KR-106** LV2 instrument.

**Highlights**: Four pages (SYNTH, ENV, PLAY, SET), 20 encoder groups, 56 control slots, hardware ALT navigation, native Zynthian controls/MIDI Learn, dynamic header fitting for Touch Navigation.

**Requirements**: Zynthian Tomita with ZynGUI LV2 widget API v1 and original KR-106 (`https://kayrock.org/kr106`) installed.

**What is included**: Widget LV2 extension only; no plugin audio engine, `.so` binary, preset packs, or patch to Zynthian core.

**Installation**: Copy `kr106_gui-zyngui.lv2` into `/zynthian/zynthian-plugins/lv2-widgets/`, touch `/zynthian/config/lv2.stamp`, reopen the control screen. Full instructions in README.md.

**Repository tag:** `ultramaster-kr106-ui-v0.5.1` (a widget-specific tag within the `zynthian-widgets` repository).
