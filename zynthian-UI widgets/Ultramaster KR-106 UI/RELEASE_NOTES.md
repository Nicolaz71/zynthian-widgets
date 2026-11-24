# Ultramaster KR-106 UI v0.5.2

Hardware-tested update for Zynthian Tomita's LV2 widget API v1, targeting the **original** Ultramaster KR-106 (`https://kayrock.org/kr106`).

## Changes from 0.5.1

- Use **UP/DOWN** to navigate between the four interface pages.
- Use **LEFT/RIGHT** to navigate between encoder groups.
- ALT is not required; navigation wraps around.
- Touch controls, physical encoders and Z/native MIDI Learn remain unchanged.
- Responsive header and four pages (SYNTH, ENV, PLAY, SET) preserved.

## Install

Extract the attached ZIP under `/zynthian/zynthian-plugins/lv2-widgets/`, then touch `/zynthian/config/lv2.stamp` and reopen the controls. Back up the previous `kr106_gui-zyngui.lv2` bundle before replacing it.

This release contains **only** the Python/Tk LV2 widget. It does not contain an audio plugin, .so binaries, or changes to Zynthian's core.

GitHub release tag: `ultramaster-kr106-ui-v0.5.2`.
