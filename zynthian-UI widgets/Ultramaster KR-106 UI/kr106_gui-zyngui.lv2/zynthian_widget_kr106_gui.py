#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ultramaster KR-106 UI v0.5.2 - widget for the original LV2 synthesizer.

LV2 UI extension for the already installed original plugin. Does not manipulate DSP.
GPL-3.0-or-later. Uses the zynthian_widget_base integration point.
"""
import logging
import math
import re
import tkinter as tk
import tkinter.font as tkfont

from zyngui import zynthian_widget_base

MULTI_INSTANCE = True
PLUGIN_URI = "https://kayrock.org/kr106"
WIDGET_VERSION = "0.5.2-tomita-original-r1"

# JUCE ParameterID p0..p55; indices from the original Source/PluginProcessor.h.
# Resolve by URI/symbol first, then by unique displayed name (no DSP changes).
PARAMS = [
    "Bender DCO", "Bender VCF", "Arp Rate", "LFO Rate", "LFO Delay",
    "DCO LFO", "DCO PWM", "DCO Sub", "DCO Noise", "HPF",
    "VCF Freq", "VCF Res", "VCF Env", "VCF LFO", "VCF Kbd",
    "Volume", "Attack", "Decay", "Sustain", "Release",
    "Transpose", "Hold", "Arpeggio", "Pulse", "Saw", "Sub Sw",
    "Chorus Off", "Chorus I", "Chorus II", "Octave", "Arp Mode",
    "Arp Range", "LFO Mode", "PWM Mode", "VCF Env Inv", "VCA Mode",
    "Bender", "Tuning", "Power", "Porta Mode", "Porta Rate",
    "Transpose Offset", "Bender LFO", "ADSR Mode", "Master Volume",
    "Voices", "VCF Oversample", "Ignore Velocity", "Arp Limit Kbd",
    "Arp Sync Host", "LFO Sync Host", "Mono Retrigger", "Send MIDI SysEx",
    "Arp Quantize", "LFO Quantize", "Oscillator Mode"
]
assert len(PARAMS) == 56

# Four pages, all 56 host parameters covered.
# Section entries are (section title, control indices); section widths weighted
# by number of controls so touch targets remain useful on a 5-inch display.
PAGES = [
    ("SYNTH", [
        ("LFO", [3, 4, 32]),
        ("DCO", [5, 6, 7, 8, 23, 24, 25, 29, 33]),
        ("HPF", [9]),
        ("VCF", [10, 11, 12, 13, 14, 34]),
    ]),
    ("ENVELOPE / CHORUS", [
        ("VCA", [15, 35]),
        ("ENVELOPE", [16, 17, 18, 19, 43]),
        ("CHORUS", [26, 27, 28]),
        ("MASTER", [44, 37]),
    ]),
    ("PERFORMANCE", [
        ("ARPEGGIATOR", [22, 21, 49, 30, 31, 53, 2]),
        ("PORTAMENTO", [39, 40, 41]),
        ("BENDER", [0, 1, 36, 42, 51]),
    ]),
    ("SETTINGS", [
        ("VOICE ENGINE", [45, 46, 55, 47]),
        ("HOST / MIDI", [48, 50, 52, 54]),
        ("PLAY", [20, 38]),
    ]),
]
ALL_PAGE_PARAMS = [idx for _, sections in PAGES for _, indices in sections for idx in indices]
assert len(ALL_PAGE_PARAMS) == len(PARAMS) and sorted(ALL_PAGE_PARAMS) == list(range(len(PARAMS)))

# A touch anywhere on a control selects its entire fixed hardware encoder group.
# Order in every tuple maps to Zynthian E1, E2, E3, E4 respectively.
# Groups do NOT cross pages, and no group contains more than four parameters.
ENCODER_GROUPS = [
    (3, 4, 32),                # LFO: RATE, DELAY, MODE
    (5, 6, 7, 8),             # DCO: LFO, PWM, SUB, NOISE
    (23, 24, 25),             # DCO: PULSE, SAW, SUB
    (29, 33),                 # DCO: OCT, PWM SRC
    (9,),                     # HPF
    (10, 11, 12, 34),         # VCF: FREQ, RES, ENV, ENV POL
    (13, 14),                 # VCF: LFO, KBD
    (15, 35),                 # VCA: LEVEL, MODE
    (16, 17, 18, 19),         # ENVELOPE: ADSR
    (43,),                    # ENVELOPE: TYPE
    (26, 27, 28),             # CHORUS: OFF, I, II (I+II independent)
    (44, 37),                 # MASTER: VOLUME, TUNE
    (22, 21, 49, 30),          # ARPEGGIATOR: ON/OFF, HOLD, SYNC, MODE
    (31, 53, 2),              # ARPEGGIATOR: RANGE, ARP DIV, RATE
    (39, 40, 41),             # PORTAMENTO: MODE, RATE, OFFSET
    (0, 1, 36, 42),           # BENDER: DCO, VCF, BEND, LFO
    (51,),                    # MONO RETRIG (visually under BENDER)
    (20, 38),                 # PLAY: TRANS, POWER
    (45, 46, 55, 47),         # VOICE ENGINE
    (48, 50, 52, 54),         # HOST/MIDI
]
GROUP_BY_PARAM = {idx: group for group in ENCODER_GROUPS for idx in group}
# Fixed encoder groups in visual page order for LEFT/RIGHT navigation (no ALT).
# Reuse the exact same group tuples as touchscreen selection; no new mapping.
PAGE_ENCODER_GROUPS = tuple(
    tuple(dict.fromkeys(
        GROUP_BY_PARAM[idx]
        for _label, indices in sections for idx in indices
    ))
    for _page_label, sections in PAGES
)
assert tuple(len(groups) for groups in PAGE_ENCODER_GROUPS) == (7, 5, 5, 3)
assert sum(map(len, PAGE_ENCODER_GROUPS)) == len(ENCODER_GROUPS)

assert len(GROUP_BY_PARAM) == len(PARAMS)
assert set(GROUP_BY_PARAM) == set(range(len(PARAMS)))
assert all(1 <= len(group) <= 4 for group in ENCODER_GROUPS)
assert all(
    sum(idx in indices for _, sections in PAGES for _, indices in sections) == 1
    for group in ENCODER_GROUPS for idx in group
)
assert all(
    len({page for page, (_, sections) in enumerate(PAGES)
         for _, indices in sections for idx in group if idx in indices}) == 1
    for group in ENCODER_GROUPS
)

# Continuous slider controls (others use 2+ position switch-type controls).
CONTINUOUS = {0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14,
              15, 16, 17, 18, 19, 36, 37, 40, 41, 42, 44}
TOGGLES = {20, 21, 22, 23, 24, 25, 26, 27, 28, 38, 47, 48, 49, 50, 51, 52}
# Explicit values avoid invalid intermediate selections in non-contiguous enums.
OPTIONS = {
    9: [0, 1, 2, 3],
    29: [0, 1, 2], 30: [0, 1, 2], 31: [0, 1, 2], 32: [0, 1],
    33: [0, 1, 2], 34: [0, 1], 35: [0, 1], 39: [0, 1, 2],
    43: [0, 1], 45: [6, 8, 10], 46: [1, 2, 4],
    53: list(range(9)), 54: list(range(13)), 55: [0, 1],
}
SWITCH_LABELS = {
    9: ["BOOST", "FLAT", "236 Hz", "754 Hz"],
    29: ["16'", "8'", "4'"], 30: ["UP", "UP/DN", "DOWN"],
    31: ["1 OCT", "2 OCT", "3 OCT"], 32: ["AUTO", "MAN"],
    33: ["LFO", "MAN", "ENV"], 34: ["NORM", "INV"],
    35: ["ENV", "GATE"], 39: ["OFF", "POLY I", "POLY II"],
    43: ["J60", "J106"], 45: ["6", "8", "10"],
    46: ["OFF", "2x", "4x"], 55: ["WAVE", "BLEP"],
    53: ["4 BEATS", "2 BEATS", "1/4", "1/4T", "1/8", "1/8T", "1/16", "1/16T", "1/32"],
}
SHORT_LABELS = {
    0: "DCO", 1: "VCF", 2: "RATE", 3: "RATE", 4: "DELAY", 5: "LFO",
    6: "PWM", 7: "SUB", 8: "NOISE", 9: "HPF", 10: "FREQ", 11: "RES",
    12: "ENV", 13: "LFO", 14: "KBD", 15: "LEVEL", 16: "ATTACK",
    17: "DECAY", 18: "SUSTAIN", 19: "RELEASE", 20: "TRANS",
    21: "HOLD", 22: "ON/OFF", 23: "PULSE", 24: "SAW", 25: "SUB",
    26: "OFF", 27: "I", 28: "II", 29: "OCT", 30: "MODE",
    31: "RANGE", 32: "MODE", 33: "PWM SRC", 34: "ENV POL",
    35: "MODE", 36: "BEND", 37: "TUNE", 38: "POWER",
    39: "MODE", 40: "RATE", 41: "OFFSET", 42: "LFO", 43: "TYPE",
    44: "VOLUME", 45: "VOICES", 46: "OVERSAMP", 47: "IGNORE VEL",
    48: "ARP LIMIT", 49: "SYNC", 50: "LFO SYNC", 51: "MONO RETRIG",
    52: "MIDI SYSEX", 53: "ARP DIV", 54: "LFO DIV", 55: "OSC MODEL",
}

C = {
    "background": "#111114", "panel": "#303034", "panel_alt": "#25252a",
    "panel_border": "#494950", "blue": "#162ed0", "red": "#bf1217",
    "orange": "#e6a04e", "text": "#eeeeef", "muted": "#b6b5bb",
    "fader": "#0e0e11", "rail": "#67676d", "handle": "#e2e0dc",
    "inactive": "#46464b", "green": "#91d7aa", "yellow": "#f2dd55",
    "led": "#f34c48", "white": "#d2d3d7", "footer": "#1b1b20",
    "selected_panel": "#3b3b41", "divider": "#bdbdc3"
}


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def norm(name):
    return "".join(x for x in name.lower() if x.isalnum())


def parameter_id(symbol):
    """Resolve numeric JUCE parameter identities of the ORIGINAL KR-106 only.

    Zynthian/lilv can surface a full URI, an underscored URI symbol, or
    the short pNN name. The processor URI is checked by resolve_controls()
    before this function is used. Never accept custom-fork symbols.
    """
    value = str(symbol or "").strip().lower()
    if "nicksynth" in value:
        return None
    match = re.search(r"(?:^|[_:#/])p([0-9]+)$", value)
    if not match:
        return None
    prefix = value[:match.start()]
    if prefix and "kr106" not in prefix and "kayrock" not in prefix:
        return None
    index = int(match.group(1))
    return index if 0 <= index < len(PARAMS) else None


def resolve_controls(processor):
    """Bind to the ORIGINAL KR-106 already running in Zynthian Tomita.

    Only the official https://kayrock.org/kr106 engine is accepted. Numeric
    JUCE IDs are preferred, followed by unique display names. Names may vary
    between upstream releases; missing and ambiguous controls stay disabled.
    Never instantiate, replace or reconfigure any audio plugin.
    """
    engine = processor.engine
    uri = getattr(engine, "plugin_url", PLUGIN_URI)
    if str(uri) != PLUGIN_URI:
        logging.error("KR-106 ORIGINAL widget: unexpected plugin URI: %s", uri)
        return {}
    sources = [getattr(processor, "controllers_dict", {}) or {},
               getattr(engine, "lv2_zctrl_dict", {}) or {}]
    resolved = {}
    ambiguous = set()
    name_candidates = {}
    for source in sources:
        if not hasattr(source, "items"):
            continue
        candidates = {}
        source_names = {}
        for key, control in source.items():
            if not callable(getattr(control, "set_value", None)):
                continue
            identities = {parameter_id(identity) for identity in
                          (key, getattr(control, "symbol", None),
                           getattr(control, "graph_path", None))}
            identities.discard(None)
            if len(identities) > 1:
                ambiguous.update(identities.difference(resolved))
                continue
            if identities:
                index = identities.pop()
                candidates.setdefault(index, {})[id(control)] = control
            name = norm(str(getattr(control, "name", "")))
            source_names.setdefault(name, {})[id(control)] = control
        # Do not overwrite an earlier source's display-name candidates.
        for name, objects in source_names.items():
            name_candidates.setdefault(name, objects)
        for index, objects in candidates.items():
            if index in resolved:
                continue
            if len(objects) == 1 and index not in ambiguous:
                resolved[index] = next(iter(objects.values()))
            else:
                ambiguous.add(index)
    for index in ambiguous:
        resolved.pop(index, None)
    used = {id(control) for control in resolved.values()}
    for index, name in enumerate(PARAMS):
        if index in resolved or index in ambiguous:
            continue
        candidates = name_candidates.get(norm(name), {})
        if len(candidates) == 1:
            control = next(iter(candidates.values()))
            if id(control) not in used:
                resolved[index] = control
                used.add(id(control))
    return resolved


class zynthian_widget_kr106_gui(zynthian_widget_base.zynthian_widget_base):
    """Custom GUI with full main-frame canvas, Zynthian parameter objects and encoders."""

    def __init__(self, parent):
        super().__init__(parent)
        self._destroyed = False
        self._pending_jobs = {}
        self.processor = None
        self.page = 0
        self.selection = 0
        self.active_group = ENCODER_GROUPS[0]
        self.controls = {}
        self.missing = []
        self.hitboxes = []
        self.visible_indices = []
        self.pointer_slider = None
        self.dynamic_items = {}
        self.cache = None
        self.control_specs = {}
        self.highlight_items = {}
        self.value_cache = {}
        self._record_hits = True
        self._drawing_full = False
        self._canvas_scale = (1.0, 1.0)
        self._size_cache = None
        # The native controller page remains editable for Zynthian MIDI Learn.
        # BACK / other Zynthian screens handle navigation; no additional
        # return button is placed over Zynthian's own controls.
        self.native_mode = False
        self._native_pending = False
        # Leaving the *whole control view* (not changing a controller page)
        # resets native mode. Re-entering the view shows our custom panel.
        self._unmap_binding = parent.main_frame.bind(
            "<Unmap>", self._on_control_view_unmap, add="+")
        # Tomita's normal widget slot is beside the four native controllers.
        # Preserve the approved full-width KR-106 panel with an overlay on
        # the SAME main_frame. destroy() explicitly owns this sibling canvas.
        self.overlay = tk.Canvas(parent.main_frame, bg=C["background"],
                                 bd=0, relief="flat", highlightthickness=0,
                                 takefocus=0)
        self.overlay.bind("<Configure>", self._on_resize)
        self.overlay.bind("<ButtonPress-1>", self._on_press)
        self.overlay.bind("<B1-Motion>", self._on_drag)
        self.overlay.bind("<ButtonRelease-1>", self._on_release)
        # A placeholder in the normal widget grid slot.
        self.widget_canvas = tk.Canvas(self, width=1, height=1,
                                       bd=0, highlightthickness=0)
        self.widget_canvas.pack(fill="both", expand=True)

    def set_processor(self, processor):
        same_processor = processor is self.processor
        super().set_processor(processor)
        if not same_processor:
            self.native_mode = False
            self._native_pending = False
        self.controls = resolve_controls(processor)
        self.missing = [i for i in range(len(PARAMS)) if i not in self.controls]
        if self.missing:
            logging.warning("KR-106 ORIGINAL widget: %d unmatched original parameters: %s",
                            len(self.missing), self.missing)
        if not same_processor:
            self.page = 0
            self.selection = 0
            self.active_group = ENCODER_GROUPS[0]
        self.cache = None
        self.value_cache = {}
        self._draw()

    def show(self):
        if self._destroyed:
            return
        super().show()
        if self.native_mode:
            # show_widget() is scheduled by Zynthian when the user selects a
            # different native control page. Keep the native controls visible
            # instead of letting it re-cover them with the custom canvas.
            self.overlay.place_forget()
            if not self._native_pending:
                self._native_pending = True
                self._queue_idle(self._restore_native_after_page_change)
            return
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        # Canvas.lift() means raise an item, not the canvas window.
        self.overlay.tk.call("raise", self.overlay._w)
        self._draw()

    def hide(self):
        if self._destroyed:
            return
        self.overlay.place_forget()
        self.pointer_slider = None
        self._cancel_pending_jobs()
        super().hide()

    def _queue_idle(self, callback, *args):
        """Track every deferred callback so a module reload can cancel it."""
        if self._destroyed:
            return None
        token = object()
        self._pending_jobs[token] = None

        def run():
            self._pending_jobs.pop(token, None)
            if not self._destroyed:
                callback(*args)

        try:
            after_id = self.after_idle(run)
        except Exception:
            self._pending_jobs.pop(token, None)
            raise
        # A CUIA may come from another thread: the Tk loop can run the callback
        # before after_idle() has returned to its caller.
        if token in self._pending_jobs:
            self._pending_jobs[token] = after_id
        return after_id

    def _cancel_pending_jobs(self):
        for after_id in list(self._pending_jobs.values()):
            if after_id is not None:
                try:
                    self.after_cancel(after_id)
                except tk.TclError:
                    pass
        self._pending_jobs.clear()
        self._native_pending = False

    def destroy(self):
        """Release owned objects outside this Frame before Tomita reloads it."""
        if self._destroyed:
            return
        self._destroyed = True
        self._cancel_pending_jobs()
        self.pointer_slider = None
        if self._unmap_binding:
            try:
                self.zyngui_control.main_frame.unbind("<Unmap>", self._unmap_binding)
            except tk.TclError:
                pass
            self._unmap_binding = None
        try:
            self.overlay.destroy()
        except tk.TclError:
            pass
        self.controls.clear()
        super().destroy()

    def _enter_native_controls(self):
        """Show the real ZYN control pages in active mode for MIDI Learn.

        set_mode_select() is deliberately NOT used: Zynthian sets mode='select'
        and disables its four native controllers in that method.
        """
        ctrl_ui = self.zyngui_control
        if getattr(ctrl_ui, 'mode', 'control') != 'control':
            logging.warning('KR-106: cannot enter native controls outside control mode')
            return
        self.native_mode = True
        self._show_native_controls()

    def _show_native_controls(self):
        ctrl_ui = self.zyngui_control
        # hide_widgets restores the native list and clears current_widget, so
        # zynpot_cb and MIDI learn are routed to native zgui_controllers.
        ctrl_ui.hide_widgets()
        for zgui_ctrl in getattr(ctrl_ui, 'zgui_controllers', ()):
            zgui_ctrl.enable(True)

    def _restore_native_after_page_change(self):
        self._native_pending = False
        if not self.native_mode:
            return
        # Native screen selection can schedule display_widget() (including a
        # built-in envelope widget). Hide it only once, after it was displayed,
        # so the ZYN native zctrl page remains active and usable.
        ctrl_ui = self.zyngui_control
        if getattr(ctrl_ui, 'mode', None) != 'control':
            return
        # The queued request belongs to one processor. A rapid instrument
        # change must never hide the replacement instrument's widget.
        try:
            if ctrl_ui.get_current_processor() is not self.processor:
                return
        except AttributeError:
            return
        if getattr(ctrl_ui, 'current_widget', None) is not None:
            self._show_native_controls()

    def _on_control_view_unmap(self, event):
        """Clear native-only state when navigating away from Control View.

        The parent frame remains mapped during ordinary native page changes;
        this callback is invoked only when the entire view is unmapped.
        """
        if not self._destroyed and event.widget is self.zyngui_control.main_frame:
            self.native_mode = False
            self._cancel_pending_jobs()

    def hide_on_select_mode(self):
        return True

    def refresh_gui(self):
        """ZYN UI polling: repaint ONLY controls whose values actually changed.

        No canvas.delete('all') on normal encoder / MIDI / automation changes.
        Tomita owns update() -> get_monitors() -> refresh_gui(). Hidden widgets
        do no work; native pages may show Tomita's own envelope/filter widget.
        """
        if self._destroyed:
            return
        if self.native_mode:
            ctrl_ui = self.zyngui_control
            try:
                same_proc = ctrl_ui.get_current_processor() is self.processor
            except (AttributeError, TypeError):
                same_proc = True
            if (same_proc and getattr(ctrl_ui, 'mode', None) == 'control'
                    and getattr(ctrl_ui, 'current_widget', None) is not None
                    and not self._native_pending):
                self._native_pending = True
                self._queue_idle(self._restore_native_after_page_change)
            return
        if not (self.shown and self.zyngui_control.shown):
            return
        if self.pointer_slider is None:
            self._refresh_changed_controls()

    def zynpot_cb(self, i, dval):
        if self.native_mode or not self.shown or i not in (0, 1, 2, 3):
            return False
        if i >= len(self.active_group):
            return True  # Unassigned encoder on groups with fewer than 4 controls.
        idx = self.active_group[i]
        zctrl = self.controls.get(idx)
        if zctrl is None or not dval:
            return True
        try:
            if idx in CONTINUOUS:
                zctrl.nudge(dval)
            elif idx in (26, 27, 28):
                self._chorus_encoder(idx, dval)
            elif idx in TOGGLES:
                # Turning right means ON; turning left means OFF (no per-tick
                # flip-flopping). Chorus is handled independently above.
                lo, hi = self._limits(idx)
                zctrl.set_value(hi if dval > 0 else lo)
            else:
                self._step_choice(idx, 1 if dval > 0 else -1)
            self._refresh_changed_controls()
        except Exception:
            logging.exception("KR-106 GUI encoder change failed: %s", idx)
        return True

    # Tomita routes hardware arrow CUIAs through
    # zynthian_gui_control.callable_ui_action -> current_widget.cuia_arrow_*.
    # These handlers intentionally do not alter the native Zynthian core files.
    def _custom_nav_visible(self):
        ctrl = self.zyngui_control
        return (not self._destroyed and self.shown and getattr(ctrl, "shown", False)
                and not self.native_mode
                and getattr(ctrl, "mode", None) == "control"
                and getattr(ctrl, "current_widget", None) is self)

    def _handle_hardware_arrow(self, direction):
        if not self._custom_nav_visible():
            # Native Z controls (Z / MIDI Learn) retain the normal arrows.
            return False
        # The four physical arrows always navigate inside our own widget.
        # No ALT modifier is needed. While the native Zynthian control screen
        # is visible, the guard above returns False so Zynthian retains its
        # normal arrow handling and MIDI Learn workflow.
        # CUIA callbacks may run in Zynthian's CUIA thread: never touch
        # Tk/Canvas there. Queue geometry/selection work on the Tk loop.
        try:
            self._queue_idle(self._apply_hardware_arrow, direction)
        except Exception:
            logging.exception("KR-106 GUI: failed to queue hardware arrow %s", direction)
        return True

    def _apply_hardware_arrow(self, direction):
        # A queued action must not operate on a hidden / switched processor.
        if not self._custom_nav_visible():
            return
        if direction in ("up", "down"):
            # DOWN -> next page; UP -> previous page.
            # Circular over four pages.
            step = -1 if direction == "up" else 1
            self._set_page((self.page + step) % len(PAGES))
        elif direction in ("left", "right"):
            # LEFT/RIGHT -> previous/next encoder group in the CURRENT page.
            # No DSP parameter is modified by navigation.
            groups = PAGE_ENCODER_GROUPS[self.page]
            if not groups:
                return
            try:
                position = groups.index(self.active_group)
            except ValueError:
                position = 0
            step = -1 if direction == "left" else 1
            self._select(groups[(position + step) % len(groups)][0])

    def cuia_arrow_left(self, params=None):
        return self._handle_hardware_arrow("left")

    def cuia_arrow_right(self, params=None):
        return self._handle_hardware_arrow("right")

    def cuia_arrow_up(self, params=None):
        return self._handle_hardware_arrow("up")

    def cuia_arrow_down(self, params=None):
        return self._handle_hardware_arrow("down")

    # CUIA aliases map to physical left/right on supported hardware profiles.
    cuia_arrow_prev = cuia_arrow_left
    cuia_arrow_next = cuia_arrow_right

    def _on_resize(self, event):
        if self._destroyed:
            return
        size = (event.width, event.height)
        if size != self._size_cache:
            self._size_cache = size
            self._draw()

    def _value(self, idx):
        zctrl = self.controls.get(idx)
        try:
            return float(zctrl.get_value()) if zctrl is not None else None
        except Exception:
            return None

    def _limits(self, idx):
        z = self.controls.get(idx)
        if z is None:
            return (0.0, 1.0)
        try:
            lo, hi = float(z.value_min), float(z.value_max)
            if hi > lo:
                return lo, hi
        except (TypeError, ValueError):
            pass
        return (0.0, 1.0)

    def _page_items(self):
        return [i for _, ids in PAGES[self.page][1] for i in ids]

    def _set_page(self, page):
        page = int(clamp(page, 0, len(PAGES) - 1))
        if self.page == page and self.control_specs:
            return
        self.page = page
        items = self._page_items()
        self.active_group = GROUP_BY_PARAM[items[0]] if items else ()
        self.selection = items[0] if items else 0
        self._draw()  # Full rebuild ONLY when the page changes.

    def _select(self, idx):
        group = GROUP_BY_PARAM.get(idx)
        if group is None:
            return
        self.selection = idx
        if group != self.active_group:
            self.active_group = group
            self._paint_group_selection()  # Only recolor pre-existing rectangles.

    def _step_choice(self, idx, direction):
        zctrl = self.controls.get(idx)
        current = self._value(idx)
        if zctrl is None or current is None:
            return
        values = OPTIONS.get(idx)
        if not values:
            lo, hi = self._limits(idx)
            values = list(range(int(lo), int(hi) + 1))
        if not values:
            return
        nearest = min(range(len(values)), key=lambda n: abs(values[n] - current))
        # ENV POL is NORM=0 (top) and INV=1 (bottom). Invert the
        # encoder step here so a clockwise turn still raises the lever.
        if idx == 34:
            direction = -direction
        dest = int(clamp(nearest + direction, 0, len(values) - 1))
        zctrl.set_value(values[dest])

    def _set_binary(self, idx, state):
        z = self.controls.get(idx)
        if z is None:
            return
        lo, hi = self._limits(idx)
        z.set_value(hi if state else lo)

    def _chorus_encoder(self, idx, dval):
        # OFF is an exclusive bypass button; I and II are independent and
        # can be enabled simultaneously as in the original KR-106.
        on = dval > 0
        if idx == 26:
            if on:
                self._set_binary(27, False)
                self._set_binary(28, False)
            self._set_binary(26, on)
        else:
            self._set_binary(idx, on)
            one_on = (self._value(27) or 0) > self._limits(27)[0]
            two_on = (self._value(28) or 0) > self._limits(28)[0]
            self._set_binary(26, not (one_on or two_on))

    def _switch(self, idx, direction=1):
        z = self.controls.get(idx)
        if z is None:
            return
        cur = self._value(idx)
        if cur is None:
            return
        if idx in (26, 27, 28):
            if idx == 26:
                self._chorus_encoder(26, 1)
            else:
                on = cur <= self._limits(idx)[0]
                self._chorus_encoder(idx, 1 if on else -1)
        elif idx in TOGGLES:
            lo, hi = self._limits(idx)
            z.set_value(lo if cur >= (lo + hi) / 2 else hi)
        elif idx == 34:
            # Touch on armed ENV POL toggles NORM / INV without changing
            # the semantics of the LV2 parameter or the preset state.
            self._set_binary(34, cur <= self._limits(34)[0])
        elif idx in OPTIONS and len(OPTIONS[idx]) == 2:
            # Two-position source/voice/model selectors must toggle both
            # ways on repeated taps, never get stuck in the upper position.
            choices = OPTIONS[idx]
            nearest = min(range(2), key=lambda j: abs(choices[j] - cur))
            z.set_value(choices[1 - nearest])
        else:
            self._step_choice(idx, direction)
        self._select(idx)
        self._refresh_changed_controls()

    def _slider_to_value(self, idx, y, top, bottom):
        z = self.controls.get(idx)
        if z is None:
            return
        lo, hi = self._limits(idx)
        val = lo + clamp((bottom - y) / max(1, bottom-top), 0, 1) * (hi - lo)
        try:
            if getattr(z, "is_integer", False):
                val = round(val)
            current = self._value(idx)
            if current is not None and abs(current - val) < max(1e-8, (hi - lo) / 2000):
                return
            z.set_value(val)
        except Exception:
            logging.exception("KR-106 GUI slider failed: %d", idx)
        self._select(idx)
        self._refresh_changed_controls()

    def _hit(self, x, y):
        for x0, y0, x1, y1, kind, val, extra in reversed(self.hitboxes):
            if x0 <= x <= x1 and y0 <= y <= y1:
                return kind, val, extra
        return None

    def _on_press(self, event):
        sx = max(1, self.overlay.winfo_width()) / 800.0
        sy = max(1, self.overlay.winfo_height()) / 420.0
        hit = self._hit(event.x / sx, event.y / sy)
        self.pointer_slider = None
        if not hit:
            return
        kind, val, extra = hit
        if kind in ("slider", "switch"):
            # First tap only arms the selected hardware encoder GROUP.
            # No value changes even if a finger drags without lifting.
            if GROUP_BY_PARAM[val] != self.active_group:
                self._select(val)
                return
            if kind == "slider":
                self.pointer_slider = (val, extra)
                self._slider_to_value(val, event.y / sy, extra[0], extra[1])
            else:
                self._switch(val)
        elif kind == "page":
            self._set_page(val)
        elif kind == "native":
            try:
                self._enter_native_controls()
            except Exception:
                logging.exception("KR-106 GUI failed to open active ZYN controls")

    def _on_drag(self, event):
        if not self.pointer_slider:
            return
        sy = max(1, self.overlay.winfo_height()) / 420.0
        idx, bounds = self.pointer_slider
        self._slider_to_value(idx, event.y / sy, bounds[0], bounds[1])

    def _on_release(self, _event):
        self.pointer_slider = None

    def _text(self, x, y, content, color="text", size=11, weight="normal", anchor="center"):
        return self.overlay.create_text(x, y, text=content, fill=C.get(color, color),
                                        font=("DejaVu Sans", max(7, size), weight),
                                        anchor=anchor)

    def _header_font_size(self, label, requested, available_width, available_height):
        """Fit the two large titles using actual Tk font metrics, not scale().

        Canvas.scale() changes text positions but DOES NOT change font sizes.
        Touch Navigation can narrow the usable canvas on Zynthian Tomita.
        This method is used only for ULTRAMASTER and KR-106; the GUI release
        label deliberately retains its approved nine-point font.
        """
        for point_size in range(requested, 4, -1):
            font = tkfont.Font(root=self.overlay, family="DejaVu Sans",
                               size=point_size, weight="bold")
            if (font.measure(label) + 3 <= available_width and
                    font.metrics("linespace") <= available_height):
                return point_size
        return 5

    def _draw_responsive_header(self, width, height):
        """Draw text AFTER geometry scaling so font widths are pixel-accurate.

        ULTRAMASTER and KR-106 shrink independently only when their allotted
        space would cause an overlap. Keep 'GUI 0.5.2' at 9 pt, right-aligned
        immediately to the left of the existing Z button.
        """
        sx, sy = width / 800.0, height / 420.0
        y = 28 * sy
        first_x = 11 * sx
        second_x = 177 * sx
        # Physical pixel padding is intentional: it works at any x scale.
        z_button_left = 433 * sx
        gui_right = z_button_left - 7
        gui_label = "GUI 0.5.2"
        gui_font = ("DejaVu Sans", 9, "normal")
        gui_metrics = tkfont.Font(root=self.overlay, family="DejaVu Sans",
                                  size=9, weight="normal")
        gui_left = gui_right - gui_metrics.measure(gui_label)
        gap = 3  # Match the original full-width typography until overlap is imminent
        # Avoid shrinking either large title unnecessarily on the usual
        # 800x420 screen, but guarantee separate columns on narrower layouts.
        max_lineheight = max(8, min(38 * sy, 38))
        brand_size = self._header_font_size(
            "ULTRAMASTER", 14, second_x - gap - first_x, max_lineheight)
        model_size = self._header_font_size(
            "KR-106", 19, gui_left - gap - second_x, max_lineheight)
        self.overlay.create_text(first_x, y, text="ULTRAMASTER",
                                 fill=C["text"], anchor="w",
                                 font=("DejaVu Sans", brand_size, "bold"),
                                 tags=("kr106-header", "kr106-brand"))
        self.overlay.create_text(second_x, y, text="KR-106",
                                 fill=C["orange"], anchor="w",
                                 font=("DejaVu Sans", model_size, "bold"),
                                 tags=("kr106-header", "kr106-model"))
        self.overlay.create_text(gui_right, y, text=gui_label,
                                 fill=C["muted"], anchor="e",
                                 font=gui_font,
                                 tags=("kr106-header", "kr106-version"))

    def _rect(self, x0, y0, x1, y1, fill="panel", outline="", width=1):
        return self.overlay.create_rectangle(x0, y0, x1, y1, fill=C.get(fill, fill),
                                             outline=C.get(outline, outline) if outline else "",
                                             width=width)

    def _hitbox(self, x0, y0, x1, y1, kind, val, extra=None):
        if self._record_hits:
            self.hitboxes.append((x0, y0, x1, y1, kind, val, extra))

    # Source-inspired panel controls. Coordinates are virtual 800 x 420 and
    # are mapped back to Zynthian controller objects (no modification to DSP).
    BAND_COLORS = {
        "LFO": "red", "ARPEGGIATOR": "blue", "CHORUS": "blue",
        "DCO": "red", "HPF": "red", "VCF": "red", "VCA": "red",
        "ENVELOPE": "red", "VOICE ENGINE": "red",
        "MASTER": "white", "PLAY": "white", "PORTAMENTO": "white",
        "BENDER": "white", "HOST / MIDI": "blue", "PLAY MODE": "blue",
    }
    # Yellow / amber caps echo the original Juno panel. Other selectors are
    # compact metal rockers and not browser-style toggles.
    # Display all binary KR-106 options as illuminated physical buttons.
    # v0.4.6 had these indexes in TOGGLES but omitted them here, so the
    # graphic wrongly fell back to a two-position lever.
    HARDWARE_BUTTONS = {20, 21, 22, 23, 24, 25, 26, 27, 28, 38,
                        47, 48, 49, 50, 51, 52}

    def _slider_label(self, idx, v, lo, hi):
        if v is None:
            return "N/A"
        if idx == 41:
            return "%+d" % round(v)
        if idx in (0, 1, 36, 37, 42):
            return "%.2f" % v
        t = clamp((v - lo) / (hi - lo), 0, 1) if hi > lo else 0.5
        return "%d%%" % round(t * 100)

    def _slider_y(self, idx, top, bottom):
        v = self._value(idx)
        lo, hi = self._limits(idx)
        t = clamp((v - lo) / (hi - lo), 0, 1) if v is not None and hi > lo else .5
        return bottom - (bottom - top) * t

    def _draw_slider(self, idx, x, w, top=125, bottom=281, value_y=309):
        mid = x + w / 2
        present = idx in self.controls
        name = SHORT_LABELS.get(idx, PARAMS[idx]).upper()
        self._text(mid, 108, name, "text", 9, "bold")
        self._rect(mid-5.5, top-4, mid+5.5, bottom+4, "fader", "#56565b")
        self.overlay.create_line(mid, top, mid, bottom, fill=C["rail"], width=2)
        for step in range(9):
            ty = top + (bottom - top) * step / 8
            self.overlay.create_line(mid - 17, ty, mid - 10, ty, fill="#8d8c90")
            self.overlay.create_line(mid + 10, ty, mid + 17, ty, fill="#8d8c90")
        py = self._slider_y(idx, top, bottom)
        # 10 percent wider + taller than the previous 28x12 fader caps.
        cap = self._rect(mid-15.5, py-6.6, mid+15.5, py+6.6,
                         "handle" if present else "inactive", "#b0b0b0")
        # Wider, darker recessed line on the fader cap.
        stripe = self._rect(mid-15.5, py-2.2, mid+15.5, py+2.2, "#77777b")
        shine = self.overlay.create_line(mid-13, py-5, mid+13, py-5, fill="#f8f8fa")
        v = self._value(idx)
        lo,hi = self._limits(idx)
        value = self._text(mid, value_y, self._slider_label(idx,v,lo,hi), "muted", 9,"bold")
        self.dynamic_items[idx] = {"kind":"slider", "mid":mid, "top":top,
                                   "bottom":bottom,"cap":cap,"stripe":stripe,
                                   "shine":shine,"value":value}
        self._hitbox(x, 102, x+w, value_y+10, "slider", idx, (top,bottom))

    def _switch_label(self, idx):
        val = self._value(idx)
        if val is None:
            return "N/A"
        if idx in SWITCH_LABELS:
            choices = OPTIONS.get(idx, [])
            if choices:
                best = min(range(len(choices)), key=lambda i: abs(val - choices[i]))
                labels = SWITCH_LABELS[idx]
                if best < len(labels):
                    return labels[best]
        if idx in TOGGLES:
            return "ON" if val > self._limits(idx)[0] else "OFF"
        if float(val).is_integer():
            return str(int(val))
        return "%.2f" % val

    def _draw_push_button(self, idx, x, y, w, h):
        val = self._value(idx)
        active = val is not None and val > self._limits(idx)[0]
        chorus = idx in (26, 27, 28)
        # CHORUS: +25% larger caps, labels to their LEFT, LEDs on right.
        if chorus:
            capw, caph = 45, 34
            cx = x + w * .66
            cy = y + h * .50
            self._text(x + 8, cy, SHORT_LABELS[idx], "text", 11, "bold", "w")
        else:
            capw = min(36, max(20, w * .40))
            caph = min(27, max(14, h * .40))
            cx = x + w / 2
            cy = y + h * (.63 if h >= 45 else .66)
            self._text(cx, y + (10 if h >= 45 else 8),
                       SHORT_LABELS.get(idx, PARAMS[idx]), "text", 8, "bold")
        self._rect(cx-capw/2-3, cy-caph/2-3, cx+capw/2+3, cy+caph/2+3,
                   "#101015")
        face_color = ("#ad4447" if active else "#303038") if idx == 38 else (
            C["yellow"] if active else "#8a895d")
        face = self._rect(cx-capw/2, cy-caph/2, cx+capw/2, cy+caph/2,
                          face_color, "#b5b4ac")
        shine = self.overlay.create_line(cx-capw/2+2, cy-caph/2+2,
                                         cx+capw/2-2, cy-caph/2+2,
                                         fill="#f5edab" if active else "#9e9c86")
        led = None
        if idx in (20, 21, 22, 23, 24, 25, 26, 27, 28,
                   47, 48, 49, 50, 51, 52):
            ledx = min(x + w - 6, cx + capw/2 + 7)
            led = self.overlay.create_oval(ledx-3, cy-3, ledx+3, cy+3,
                     fill=C["led"] if active else "#412329", outline="#121216")
        self.dynamic_items[idx] = {"kind": "button", "face": face,
                                   "shine": shine, "led": led}
        self._hitbox(x, y, x+w, y+h, "switch", idx)

    def _choice_values(self, idx):
        values = OPTIONS.get(idx)
        if values is None:
            if idx in TOGGLES:
                return [0,1]
            lo,hi = self._limits(idx)
            return list(range(int(lo),int(hi)+1)) or [0]
        return values

    def _choice_labels(self, idx, values):
        labels = SWITCH_LABELS.get(idx)
        if labels is not None and len(labels) == len(values):
            return labels
        if idx in TOGGLES:
            return ["OFF", "ON"]
        z = self.controls.get(idx)
        candidates = getattr(z,'labels',None)
        if isinstance(candidates,(list,tuple)) and len(candidates)==len(values):
            return [str(v) for v in candidates]
        return [str(v) for v in values]

    def _draw_rocker(self, idx, x, y, w, h, tall=False):
        """Original-style narrow levers; positions are explicit and stable.

        Inverted ENV POL: the underlying LV2 value 0 remains NORM, but
        NORM is drawn at TOP and INV at BOTTOM as on the source hardware.
        """
        label = SHORT_LABELS.get(idx, PARAMS[idx]).upper()
        v = self._value(idx)
        values = self._choice_values(idx)
        nearest = min(range(len(values)), key=lambda j:
                      abs(values[j]-(v if v is not None else values[0])))
        if idx == 53:
            # ARP DIV: nine positions in a tall selector with *all* labels
            # visible. The short v0.4.6 selector overlapped its text.
            self._text(x+w/2, y+10, label, "text", 8, "bold")
            cx=x+22
            y0, y1 = y+30, y+h-15
            self._rect(cx-4,y0-3,cx+4,y1+3,"#09090b","#59595e")
            labels=self._choice_labels(idx,values)
            for j,name in enumerate(labels):
                py=y1-(y1-y0)*j/max(1,len(labels)-1)
                self.overlay.create_line(cx+7,py,cx+12,py,fill="#818188",width=1)
                self._text(x+43,py,name,"muted",8,"normal","w")
            py=y1-(y1-y0)*nearest/max(1,len(values)-1)
            cap=self._rect(cx-7,py-9,cx+7,py+9,"#242428","#a4a4a9")
            shine=self.overlay.create_line(cx-2,py-7,cx-2,py-3,
                                           fill="#f0f0f2",width=3)
            side=self.overlay.create_line(cx+2,py-6,cx+2,py+5,
                                          fill="#34343a",width=2)
            self.dynamic_items[idx]={"kind":"rocker","cap":cap,
                "shine":shine,"side":side,"cx":cx,"top":y0,
                "bottom":y1,"values":values,"reverse_visual":False}
        elif idx == 54:
            # LFO DIV: use virtually the FULL section width for all thirteen
            # positions. A moving numeric/name readout replaces the overlapping
            # thirteen text labels of the original narrow horizontal rocker.
            self._text(x+w/2,y+14,label,"text",8,"bold")
            cy=y+h*.52
            x0,x1=x+19,x+w-19
            self._rect(x0,cy-4,x1,cy+4,"fader","#5b5b60")
            for j in range(len(values)):
                xx=x0+(x1-x0)*j/max(1,len(values)-1)
                self.overlay.create_line(xx,cy-12,xx,cy-7,fill="#92929a",width=1)
            px=x0+(x1-x0)*nearest/max(1,len(values)-1)
            cap=self._rect(px-6,cy-12,px+6,cy+12,"#242428","#8b8b91")
            shine=self.overlay.create_line(px-2,cy-8,px-2,cy-2,
                                           fill="#f5f5f7",width=3)
            labels=self._choice_labels(idx,values)
            current=self._text(x+w/2,y+h-17,labels[nearest],"muted",9,"bold")
            self.dynamic_items[idx]={"kind":"horizontal", "cap":cap,
                "shine":shine,"x0":x0,"x1":x1,"cy":cy,
                "values":values,"value_text":current,"labels":labels}
        elif idx in (29, 32, 33, 34, 35, 39, 43):
            # Horizontal levers for OCT, LFO MODE, PWM SRC, ENV POL,
            # VCA MODE, PORTAMENTO MODE and ENVELOPE TYPE. Values run
            # left-to-right in ascending LV2 order; no changes to DSP.

            cy = y + h * .46
            span = min(w-30, 110) if idx != 29 else w - max(32,w*.40)
            span = max(25, span)
            x0, x1 = x+w/2-span/2, x+w/2+span/2
            self._text(x+w/2,y+9,label,"text",8,"bold")
            self._rect(x0, cy-4, x1, cy+4, "fader", "#5b5b60")
            px=x0+(x1-x0)*nearest/max(1,len(values)-1)
            cap=self._rect(px-6,cy-11,px+6,cy+11,"#242428","#8b8b91")
            shine=self.overlay.create_line(px-2,cy-8,px-2,cy-2,
                                           fill="#f5f5f7",width=3)
            labels=self._choice_labels(idx,values)
            for j,name in enumerate(labels):
                xx=x0+(x1-x0)*j/max(1,len(values)-1)
                self._text(xx,y+h-9,name,"muted",8)
            self.dynamic_items[idx]={"kind":"horizontal", "cap":cap,
                  "shine":shine,"x0":x0,"x1":x1,"cy":cy,"values":values}
        elif idx==9:
            # HPF has a full-sized centered four-position slider and one
            # dynamic value label, not four crowded position labels.
            cx=x+w/2
            y0,y1=y+52,y+h-45
            self._text(cx,y+22,"HPF","text",8,"bold")
            self._rect(cx-5,y0,cx+5,y1,"fader","#56565b")
            for j in range(len(values)):
                pos=y1-(y1-y0)*j/max(1,len(values)-1)
                self.overlay.create_line(cx-14,pos,cx-9,pos,fill="#88888e")
            py=y1-(y1-y0)*nearest/max(1,len(values)-1)
            cap=self._rect(cx-11,py-6,cx+11,py+6,"handle","#aeabb0")
            shine=self.overlay.create_line(cx-9,py-3,cx+9,py-3,fill="#f8f8f9")
            value_text=self._text(cx,y+h-19,self._switch_label(idx),
                                  "muted",8,"bold")
            self.dynamic_items[idx]={"kind":"hpf", "cap":cap,
                  "shine":shine,"cx":cx,"y0":y0,"y1":y1,
                  "values":values,"value_text":value_text}
        else:
            # Narrow black lever with a light metal glint at its top. Labels
            # are placed BESIDE the lever and do not overlap its travel.
            is_vcf_pol = idx==34
            cx=x+(26 if is_vcf_pol else min(15,max(11,w*.17)))
            track_top=y+(24 if h>=52 else 16)
            track_bottom=y+h-(12 if h>=52 else 7)
            if track_bottom-track_top<9:
                track_bottom=track_top+9
            self._text(x+(w/2 if is_vcf_pol else 3),y+8,label,
                       "text",8 if w>=79 else 7,"bold",
                       "center" if is_vcf_pol else "w")
            self._rect(cx-4,track_top-5,cx+4,track_bottom+5,
                       "#09090b","#57575c")
            labels=self._choice_labels(idx,values)
            text_x = x+44 if is_vcf_pol else cx+13
            label_size=8 if w>=86 and len(values)<=4 else 7
            for j,name in enumerate(labels):
                # Normally increasing LV2 values move UP. ENV POL is the
                # physical exception: NORM=0 is TOP, INV=1 is BOTTOM.
                ratio=j/max(1,len(values)-1)
                py=(track_top+(track_bottom-track_top)*ratio if is_vcf_pol
                    else track_bottom-(track_bottom-track_top)*ratio)
                self._text(text_x,py,str(name)[:14],"muted",label_size,
                           "normal","w")
            py=(track_top+(track_bottom-track_top)*nearest/max(1,len(values)-1)
                if is_vcf_pol else track_bottom-(track_bottom-track_top)*nearest/max(1,len(values)-1))
            cap=self._rect(cx-6,py-10,cx+6,py+10,
                           "#202025","#898991")
            shine=self.overlay.create_line(cx-2,py-8,cx-2,py-2,
                                           fill="#ececef",width=3)
            side=self.overlay.create_line(cx+2,py-7,cx+2,py+6,
                                          fill="#34343a",width=2)
            self.dynamic_items[idx]={"kind":"rocker", "cap":cap,
                 "shine":shine,"side":side,"cx":cx,"top":track_top,
                 "bottom":track_bottom,"values":values,
                 "reverse_visual":is_vcf_pol}
        self._hitbox(x,y,x+w,y+h,"switch",idx)

    def _draw_switch(self, idx, x, y, w, h=35, tall=False):
        if idx in self.HARDWARE_BUTTONS:
            self._draw_push_button(idx, x, y, w, h)
        else:
            self._draw_rocker(idx, x, y, w, h, tall=tall)

    def _register_control(self, idx, kind, args, highlight):
        """Register geometry once per page; immutable hit targets/active overlay."""
        self.control_specs[idx] = (kind, args)
        xa, ya, xb, yb = highlight
        item = self._rect(xa, ya, xb, yb, "panel")
        self.highlight_items[idx] = item
        self._render_control(idx)

    def _render_control(self, idx, redraw=False):
        spec = self.control_specs.get(idx)
        if spec is None:
            return
        kind, args = spec
        tag = "krparam-%d" % idx
        if redraw:
            self.overlay.delete(tag)
        # All created items (incl. text, LED and fader cap) get the same tag,
        # so refreshing a control never clears the entire canvas/page.
        start_id = self.overlay.find_all()[-1] if self.overlay.find_all() else 0
        old = self._record_hits
        self._record_hits = not redraw
        try:
            if kind == "slider":
                self._draw_slider(idx, *args)
            else:
                self._draw_switch(idx, *args)
        finally:
            self._record_hits = old
        for item in self.overlay.find_all():
            if item > start_id:
                self.overlay.addtag_withtag(tag, item)
        if redraw:
            sx, sy = self._canvas_scale
            self.overlay.scale(tag, 0, 0, sx, sy)

    def _paint_group_selection(self):
        active = set(self.active_group)
        for idx, rect in self.highlight_items.items():
            self.overlay.itemconfigure(rect, fill=C["selected_panel"]
                                       if idx in active else C["panel"])

    def _scaled_coords(self, item, *coords):
        sx,sy=self._canvas_scale
        return self.overlay.coords(item,*[
            v*(sx if n%2==0 else sy) for n,v in enumerate(coords)])

    def _update_control(self, idx):
        data=self.dynamic_items.get(idx)
        if not data:
            return
        kind=data['kind']
        v=self._value(idx)
        if kind=='slider':
            mid=data['mid']; py=self._slider_y(idx,data['top'],data['bottom'])
            self._scaled_coords(data['cap'],mid-15.5,py-6.6,mid+15.5,py+6.6)
            self._scaled_coords(data['stripe'],mid-15.5,py-2.2,mid+15.5,py+2.2)
            self._scaled_coords(data['shine'],mid-13,py-5,mid+13,py-5)
            lo,hi=self._limits(idx)
            self.overlay.itemconfigure(data['value'],text=self._slider_label(idx,v,lo,hi))
        elif kind=='button':
            active=v is not None and v>self._limits(idx)[0]
            color=("#ad4447" if active else "#303038") if idx==38 else (
                   C['yellow'] if active else "#8a895d")
            self.overlay.itemconfigure(data['face'],fill=color)
            self.overlay.itemconfigure(data['shine'],
                fill="#f5edab" if active else "#9e9c86")
            if data['led'] is not None:
                self.overlay.itemconfigure(data['led'],
                    fill=C['led'] if active else "#412329")
        elif kind in ('rocker','hpf','horizontal'):
            vals=data['values']
            j=min(range(len(vals)),key=lambda n:
                  abs(vals[n]-(v if v is not None else vals[0])))
            if kind=='horizontal':
                px=data['x0']+(data['x1']-data['x0'])*j/max(1,len(vals)-1)
                cy=data['cy']
                self._scaled_coords(data['cap'],px-6,cy-11,px+6,cy+11)
                self._scaled_coords(data['shine'],px-2,cy-8,px-2,cy-2)
                if 'value_text' in data:
                    self.overlay.itemconfigure(data['value_text'],
                                               text=data['labels'][j])
            elif kind=='hpf':
                py=data['y1']-(data['y1']-data['y0'])*j/max(1,len(vals)-1)
                cx=data['cx']
                self._scaled_coords(data['cap'],cx-11,py-6,cx+11,py+6)
                self._scaled_coords(data['shine'],cx-9,py-3,cx+9,py-3)
                self.overlay.itemconfigure(data['value_text'],
                                           text=self._switch_label(idx))
            else:
                ratio=j/max(1,len(vals)-1)
                py=(data['top']+(data['bottom']-data['top'])*ratio
                    if data.get('reverse_visual') else
                    data['bottom']-(data['bottom']-data['top'])*ratio)
                cx=data['cx']
                self._scaled_coords(data['cap'],cx-6,py-10,cx+6,py+10)
                self._scaled_coords(data['shine'],cx-2,py-8,cx-2,py-2)
                self._scaled_coords(data['side'],cx+2,py-7,cx+2,py+6)

    def _refresh_changed_controls(self):
        if not self.control_specs:
            return
        for idx in self.visible_indices:
            val=self._value(idx)
            if self.value_cache.get(idx)!=val:
                self.value_cache[idx]=val
                # No deletion or re-creation of canvas objects during drag,
                # automation, or encoder input. Only coords / text / fill change.
                self._update_control(idx)

    def _add_slider(self,idx,x,w,top,bottom,value_y,highlight_top=96,highlight_bottom=None):
        hb=value_y+13 if highlight_bottom is None else highlight_bottom
        self._register_control(idx,'slider',(x,w,top,bottom,value_y),
                               (x+1,highlight_top,x+w-1,hb))

    def _add_switch(self,idx,x,y,w,h,highlight=None):
        self._register_control(idx,'switch',(x,y,w,h),
                   highlight if highlight else (x+1,y-1,x+w-1,y+h+1))

    def _draw_lfo(self,x,w):
        fw=(w-10)/2
        for j,idx in enumerate((3,4)):
            self._add_slider(idx,x+5+j*fw,fw,128,284,310,highlight_bottom=330)
        self._add_switch(32,x+5,335,w-10,71)

    def _draw_dco(self,x,w):
        fw=(w-12)/4
        for j,idx in enumerate((5,6,7,8)):
            self._add_slider(idx,x+6+j*fw,fw,128,261,285,
                             highlight_bottom=298)
        # Move the three yellow buttons to the right, like the source hardware.
        gap=4
        bw=(w-45-2*gap)/3
        for j,idx in enumerate((23,24,25)):
            self._add_switch(idx,x+37+j*(bw+gap),296,bw,55)
        # Inverted compared with v0.3: PWM SRC left, OCT right.
        self._add_switch(33,x+14,350,135,58)
        self._add_switch(29,x+160,350,w-172,58)

    def _draw_hpf(self,x,w):
        self._add_switch(9,x+3,109,w-6,298,
                         (x+3,96,x+w-3,409))

    def _draw_vcf(self,x,w):
        fw=(w-10)/5
        for j,idx in enumerate((10,11,12,13,14)):
            self._add_slider(idx,x+5+j*fw,fw,128,286,311,
                             highlight_bottom=331)
        # ENV POL directly below ENV, not at the section's far left.
        env_mid=x+5+fw*2.5
        swx=env_mid-49
        self._add_switch(34,swx,337,98,70)

    def _draw_chorus(self,x,w):
        # Vertical OFF / I / II, independent buttons like physical Juno.
        gap=7; h=90; start=111
        for j,idx in enumerate((26,27,28)):
            self._add_switch(idx,x+14,start+j*(h+gap),w-28,h)

    def _draw_arpeggiator(self,x,w):
        """Grouped as requested: ON/OFF, HOLD, SYNC, MODE then RANGE, ARP DIV, RATE.

        Left block carries the four-mode controls. Right block groups the three
        rate/range-related controls, with ARP DIV kept long for readability.
        """
        left_w=105
        left_x=x+7
        rate_w=82
        rate_x=x+w-rate_w-7
        mid_x=left_x+left_w+9
        mid_w=rate_x-mid_x-10
        # LEFT GROUP: ON/OFF, HOLD, SYNC, MODE.
        for idx, top in ((22,104),(21,162),(49,220)):
            self._add_switch(idx,left_x,top,left_w,50)
        self._add_switch(30,left_x,278,left_w,118)
        # RIGHT GROUP: RANGE, ARP DIV, RATE.
        self._add_switch(31,mid_x,109,mid_w,74)
        self._add_switch(53,mid_x,188,mid_w,214)
        self._add_slider(2,rate_x,rate_w,119,354,387,
                         highlight_bottom=407)

    def _draw_host_midi(self,x,w):
        # Three yellow buttons on top, horizontal LFO DIV below.
        gap=6
        cw=(w-20-2*gap)/3
        for j,idx in enumerate((48,50,52)):
            self._add_switch(idx,x+6+j*(cw+gap),126,cw,118)
        self._add_switch(54,x+6,260,w-12,138)

    def _draw_voice_engine(self,x,w):
        # Three slightly shorter selectors plus IGNORE VEL as a yellow button.
        margin=8
        gap=8
        cw=(w-2*margin-2*gap)/3
        top_y=118
        top_h=120
        for j,idx in enumerate((45,46,55)):
            self._add_switch(idx,x+margin+j*(cw+gap),top_y,cw,top_h)
        self._add_switch(47,x+margin,272,w-2*margin,92)

    def _draw_bender(self,x,w):
        fw=(w-10)/4
        for j,idx in enumerate((0,1,36,42)):
            self._add_slider(idx,x+5+j*fw,fw,127,278,302,highlight_bottom=322)
        self._add_switch(51,x+18,332,w-36,64)

    def _draw_set_play_stack(self,x,w):
        """PLAY occupies the last column of page 4 SET in v0.4.6."""
        self._rect(x,58,x+w,420,'panel')
        inset=4
        self._rect(x+inset,58,x+w-inset,89,'white')
        self._text(x+w/2,74,'PLAY','#111114',10,'bold')
        bw=(w-19)/2
        self._add_switch(20,x+6,150,bw,120)
        self._add_switch(38,x+13+bw,150,bw,120)
        self._rect(x+inset,415,x+w-inset,419,'white')

    def _draw_section(self,label,indices,x,width):
        x0,x1=x,x+width
        band=self.BAND_COLORS.get(label,'white')
        # WIDER dark-panel gaps only across the COLORED HEADER and FOOTER.
        # In the body a narrow light-grey divider is added in _draw().
        self._rect(x0,58,x1,420,'panel')
        band_inset=4
        self._rect(x0+band_inset,58,x1-band_inset,89,band)
        self._text((x0+x1)/2,74,label,
                  '#111114' if band=='white' else 'text',10,'bold')
        self._rect(x0+band_inset,415,x1-band_inset,419,band)
        special={'LFO':self._draw_lfo,'DCO':self._draw_dco,
                 'HPF':self._draw_hpf,'VCF':self._draw_vcf,
                 'CHORUS':self._draw_chorus,
                 'ARPEGGIATOR':self._draw_arpeggiator,
                 'HOST / MIDI':self._draw_host_midi,
                 'VOICE ENGINE':self._draw_voice_engine,
                 'BENDER':self._draw_bender}
        if label in special:
            special[label](x0,width)
            return
        sliders=[idx for idx in indices if idx in CONTINUOUS]
        switches=[idx for idx in indices if idx not in CONTINUOUS]
        if sliders:
            if len(switches)>=4:
                fader_bottom,value_y,switch_y,rows,switch_h=248,271,284,2,55
            else:
                fader_bottom,value_y,switch_y,rows,switch_h=287,311,334,1,72
            fw=(width-12)/len(sliders)
            for j,idx in enumerate(sliders):
                self._add_slider(idx,x0+6+fw*j,fw,127,fader_bottom,value_y,
                                 highlight_bottom=switch_y-5 if switches else 407)
            if switches:
                cols=int(math.ceil(len(switches)/rows))
                gap=4
                bw=(width-12-(cols-1)*gap)/cols
                for j,idx in enumerate(switches):
                    row,col=divmod(j,cols)
                    self._add_switch(idx,x0+6+col*(bw+gap),
                                     switch_y+row*(switch_h+4),bw,switch_h)
        elif switches:
            if len(switches)==1:
                self._add_switch(switches[0],x0+6,109,width-12,297)
            else:
                cols=min(3,len(switches)) if width>260 else (2 if width>145 else 1)
                rows=int(math.ceil(len(switches)/cols))
                gap=6
                bw=(width-14-(cols-1)*gap)/cols
                bh=min(91,(284-(rows-1)*gap)/rows)
                total_h=rows*bh+(rows-1)*gap
                sy=108+(295-total_h)/2
                for j,idx in enumerate(switches):
                    row,col=divmod(j,cols)
                    self._add_switch(idx,x0+7+col*(bw+gap),
                                     sy+row*(bh+gap),bw,bh)
        else:
            self._text((x0+x1)/2,220,'NO PARAMETERS','muted',9)

    def _draw(self):
        if not hasattr(self, "overlay"):
            return
        canvas = self.overlay
        w,h = canvas.winfo_width(),canvas.winfo_height()
        if w<50 or h<50:
            return
        canvas.delete("all")  # Only page change, show and true resize.
        sx, sy = w/800.0, h/420.0
        self._canvas_scale=(sx,sy)
        self.hitboxes=[]
        self.control_specs={}
        self.highlight_items={}
        self.dynamic_items={}
        self.value_cache={}
        self._record_hits=True
        self.visible_indices=self._page_items()
        self._rect(0,0,800,420,"background")
        self._rect(0,0,800,3,"red")
        # Header text is created after canvas.scale() below: Tk does not
        # scale font sizes when coordinates are scaled.
        # Z opens active native controllers for MIDI Learn (never select mode).
        self._rect(433,13,463,44,"panel_alt","panel_border")
        self._text(448,28,"Z","text",13,"bold")
        self._hitbox(433,13,463,44,"native",None)
        tabs=["1 SYNTH","2 ENV","3 PLAY","4 SET"]
        for p,label in enumerate(tabs):
            x=473+p*81
            active=p==self.page
            self._rect(x,11,x+77,46,"red" if active else "panel_alt",
                       "#aaaaaa" if active else "panel_border")
            self._text(x+38.5,28.5,label,"text",9,"bold")
            self._hitbox(x,11,x+77,46,"page",p)
        sections=PAGES[self.page][1]
        boundaries=[]
        if self.page==3:
            # 4 SET: VOICE ENGINE | HOST/MIDI | PLAY.
            # Keep PLAY in a dedicated right column for comfortable touch use.
            for (label,indices),x,width in zip(sections[:2],(0,305),(305,305)):
                self._draw_section(label,indices,x,width)
            self._draw_set_play_stack(610,190)
            boundaries=[305,610]
        else:
            if self.page==0:
                widths=[130,314,76,280]
            elif self.page==2:
                # PLAY remains in SET, while BENDER carries MONO RETRIG below the sliders.
                widths=[375,175,250]
            else:
                counts=[sum(idx in CONTINUOUS for idx in ids) for _,ids in sections]
                weights=[max(1.5,c+0.55*(len(ids)-c)+0.5)
                         for c,(_,ids) in zip(counts,sections)]
                widths=[800*v/sum(weights) for v in weights]
            x=0
            for (label,indices),width in zip(sections,widths):
                self._draw_section(label,indices,x,width)
                x+=width
                boundaries.append(x)
            boundaries.pop()
        # Thin silver BODY dividers. Wide dark gaps only break the header
        # and footer bands; never a thick vertical strip in the body.
        for divider_x in boundaries:
            canvas.create_line(divider_x,91,divider_x,412,
                               fill=C["divider"],width=2)
        for idx in self.visible_indices:
            self.value_cache[idx]=self._value(idx)
        self._paint_group_selection()
        canvas.scale("all",0,0,sx,sy)
        self._draw_responsive_header(w, h)


# Tomita loads the class by the exact module stem: zynthian_widget_kr106_gui.
