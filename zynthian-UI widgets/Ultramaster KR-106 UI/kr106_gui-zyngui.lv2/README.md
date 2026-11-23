# Ultramaster KR-106 ORIGINAL - Zynthian Tomita LV2 widget

VERSION: 0.5.1-tomita-original-r2 (adaptive header) (widget-only). Not an official catalog entry.

## Mandatory host dependency

- Existing original instrument: `https://kayrock.org/kr106`
- Zynthian Tomita with ZynGUI LV2 widget support (API version 1).
- This bundle does not contain audio binaries. It deliberately does not target
  the separate fork URI `urn:nicksynth:kr106-gui`.

## Standard installation from a ZIP copied to /root

```
mkdir -p /zynthian/zynthian-plugins/lv2-widgets
W=/zynthian/zynthian-plugins/lv2-widgets/kr106_gui-zyngui.lv2
if [ -d "$W" ] && [ ! -L "$W" ]; then
  mv "$W" "/root/kr106_gui-zyngui.backup.$(date +%Y%m%d_%H%M%S).lv2"
fi
unzip -o /root/KR106_Original_Tomita_Widget_v051_HeaderFix.zip   -d /zynthian/zynthian-plugins/lv2-widgets
touch /zynthian/config/lv2.stamp
```

Change away from and back to the KR-106 control view. No service restart,
no local installer, no audio plugin installation. Existing bundle under the
same path is replaced (it targeted the old custom fork).

Verify with Tomita's official script:
```
source /zynthian/config/zynthian_envars.sh
python3 /zynthian/zynthian-ui/.claude/skills/zynthian-lv2-plugin/scripts/lv2_ports.py \
  widget https://kayrock.org/kr106
```
The output must show api_version=1 and the fpath inside lv2-widgets.

## Actual controller mapping

The UI expects 56 JUCE parameters, IDs p0..p55, from the original project.
Each control is matched by the normalized LV2 property identity or by
its unique displayed parameter name. If the installed original has
fewer/different controls, the corresponding GUI slots remain disabled.
This is fail-safe: no writes to unrelated parameters. First test on hardware.

Read-only native control-port check:
```
PYTHONPATH=/zynthian/zynthian-ui python3 - <<'PYCODE'
from zyngine import zynthian_lv2
zynthian_lv2.init_lilv()
ports = zynthian_lv2.get_plugin_ports('https://kayrock.org/kr106')
print('Controlli del KR-106 originale:', len(ports))
for p in (ports.values() if hasattr(ports,'values') else ports):
 print(str(p['symbol']), '=>', str(p['name']))
PYCODE
```

## Header fix: r2 (same GUI 0.5.1 display version)

- "ULTRAMASTER" and "KR-106" retain their original fonts at full width.
- On narrower Tomita layouts, the two title fonts automatically shrink to
  avoid overlap. Canvas.scale() does not scale Tk font sizes.
- The right-aligned label reads **GUI 0.5.1**, without the letter v;
  its 9-point font remains unchanged, immediately to the left of Z.
- The resize changes only header text. Four pages, 20 encoder groups, touch,
  MIDI Learn, and the original plugin URI are unchanged.
- No DSP, LV2 processor parameters, Zynthian core files or service changes.

## Scope

Pure Python/Tk widget. Preserves v0.4.8 layout: four pages, all 20
encoder groups, MIDI Learn via Z, dynamic reload cleanup. No patch to
zynthian_engine_jalv.py; no chorus settings changes; no custom audio engine.
The portable ZIP is not yet published in the official Zynthian catalog.

## Restore previous external widget

If needed, restore the timestamped backup created during installation:
```
rm -rf /zynthian/zynthian-plugins/lv2-widgets/kr106_gui-zyngui.lv2
mv /root/kr106_gui-zyngui.backup.YYYYMMDD_HHMMSS.lv2   /zynthian/zynthian-plugins/lv2-widgets/kr106_gui-zyngui.lv2
touch /zynthian/config/lv2.stamp
```
Replace `YYYYMMDD_HHMMSS` with the actual backup timestamp.

GPL-3.0-or-later. Check upstream KR-106 parameter changes before release.
