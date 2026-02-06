#!/usr/bin/env python3
"""
Material You Theme Installer — GUI
====================================
GTK4 + libadwaita with Material 3 Expressive design.
Adaptive layout, dynamic color picker, spring animations.
"""

import colorsys
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, Gdk, Pango

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from material_you_installer import (
    SystemDetector, SystemInfo, BackupManager, InstallerStep,
    ALL_STEPS, BACKUP_BASE, Status, ComponentResult, VERSION,
    THEME_DIR,
)

# Path for tracking the currently installed palette
PALETTE_STATE_FILE = Path.home() / ".local" / "share" / "material-you-orange" / "palette.json"


# ─── Color Palettes ─────────────────────────────────────────────────────────

PALETTES = {
    "Orange": {
        "seed":                   "#ffb86c",
        "primary":                "#ffb86c",
        "on_primary":             "#1a1110",
        "primary_container":      "#5c3a1a",
        "on_primary_container":   "#ffdcbe",
        "secondary":              "#e4bfa8",
        "secondary_container":    "#3d2e20",
        "tertiary":               "#b2dfdb",
        "tertiary_container":     "#1e3533",
        "error":                  "#ffb4ab",
        "error_container":        "#93000a",
        "surface":                "#1a1110",
        "surface_cont_lowest":    "#140e0c",
        "surface_cont_low":       "#1e1514",
        "surface_cont":           "#231918",
        "surface_cont_high":      "#2d2220",
        "surface_cont_highest":   "#3d312e",
        "on_surface":             "#efe0db",
        "on_surface_var":         "#d5c4bc",
        "outline":                "#9e8e86",
        "outline_var":            "#51443e",
        "success":                "#a8c77a",
        "warning":                "#ffc888",
    },
    "Blue": {
        "seed":                   "#82b1ff",
        "primary":                "#82b1ff",
        "on_primary":             "#0d1a2e",
        "primary_container":      "#1a3a5c",
        "on_primary_container":   "#c4dcff",
        "secondary":              "#a8c4e4",
        "secondary_container":    "#20303d",
        "tertiary":               "#d4bfdb",
        "tertiary_container":     "#331e35",
        "error":                  "#ffb4ab",
        "error_container":        "#93000a",
        "surface":                "#101418",
        "surface_cont_lowest":    "#0b0f12",
        "surface_cont_low":       "#141a1e",
        "surface_cont":           "#181e23",
        "surface_cont_high":      "#20282d",
        "surface_cont_highest":   "#2e373d",
        "on_surface":             "#dbe3ef",
        "on_surface_var":         "#bcc6d5",
        "outline":                "#86919e",
        "outline_var":            "#3e4851",
        "success":                "#a8c77a",
        "warning":                "#ffc888",
    },
    "Green": {
        "seed":                   "#a8c77a",
        "primary":                "#a8c77a",
        "on_primary":             "#142010",
        "primary_container":      "#2a3d1a",
        "on_primary_container":   "#d0e8b0",
        "secondary":              "#bcc8a8",
        "secondary_container":    "#2d3520",
        "tertiary":               "#a8c4c0",
        "tertiary_container":     "#1e3330",
        "error":                  "#ffb4ab",
        "error_container":        "#93000a",
        "surface":                "#121410",
        "surface_cont_lowest":    "#0d0f0b",
        "surface_cont_low":       "#161a14",
        "surface_cont":           "#1a1e18",
        "surface_cont_high":      "#232820",
        "surface_cont_highest":   "#31382e",
        "on_surface":             "#e0e8db",
        "on_surface_var":         "#c4ccbc",
        "outline":                "#8e9686",
        "outline_var":            "#444e3e",
        "success":                "#a8c77a",
        "warning":                "#ffc888",
    },
    "Purple": {
        "seed":                   "#ce93d8",
        "primary":                "#ce93d8",
        "on_primary":             "#201025",
        "primary_container":      "#3d1a4a",
        "on_primary_container":   "#ecc4f2",
        "secondary":              "#d4b8d8",
        "secondary_container":    "#352a38",
        "tertiary":               "#c8c0a8",
        "tertiary_container":     "#33301e",
        "error":                  "#ffb4ab",
        "error_container":        "#93000a",
        "surface":                "#161214",
        "surface_cont_lowest":    "#100d0f",
        "surface_cont_low":       "#1a1618",
        "surface_cont":           "#1e1a1d",
        "surface_cont_high":      "#282325",
        "surface_cont_highest":   "#383234",
        "on_surface":             "#ece0ee",
        "on_surface_var":         "#d2c4d4",
        "outline":                "#9c8e9e",
        "outline_var":            "#4e424f",
        "success":                "#a8c77a",
        "warning":                "#ffc888",
    },
    "Red": {
        "seed":                   "#ff897d",
        "primary":                "#ff897d",
        "on_primary":             "#2e0e0a",
        "primary_container":      "#5c1a1a",
        "on_primary_container":   "#ffc4be",
        "secondary":              "#e4b8a8",
        "secondary_container":    "#3d2820",
        "tertiary":               "#b2c8c4",
        "tertiary_container":     "#1e3330",
        "error":                  "#ffb4ab",
        "error_container":        "#93000a",
        "surface":                "#1a1010",
        "surface_cont_lowest":    "#140c0c",
        "surface_cont_low":       "#1e1414",
        "surface_cont":           "#231818",
        "surface_cont_high":      "#2d2020",
        "surface_cont_highest":   "#3d302e",
        "on_surface":             "#efe0db",
        "on_surface_var":         "#d5c0bc",
        "outline":                "#9e8686",
        "outline_var":            "#51403e",
        "success":                "#a8c77a",
        "warning":                "#ffc888",
    },
    "Teal": {
        "seed":                   "#80cbc4",
        "primary":                "#80cbc4",
        "on_primary":             "#0a2420",
        "primary_container":      "#1a3d3a",
        "on_primary_container":   "#b8e8e4",
        "secondary":              "#a8c8c4",
        "secondary_container":    "#203533",
        "tertiary":               "#c0b8d4",
        "tertiary_container":     "#2a2638",
        "error":                  "#ffb4ab",
        "error_container":        "#93000a",
        "surface":                "#101614",
        "surface_cont_lowest":    "#0b100f",
        "surface_cont_low":       "#141a18",
        "surface_cont":           "#181e1d",
        "surface_cont_high":      "#202826",
        "surface_cont_highest":   "#2e3836",
        "on_surface":             "#dbe8e6",
        "on_surface_var":         "#bcccc8",
        "outline":                "#869694",
        "outline_var":            "#3e4e4b",
        "success":                "#a8c77a",
        "warning":                "#ffc888",
    },
    "Pink": {
        "seed":                   "#f48fb1",
        "primary":                "#f48fb1",
        "on_primary":             "#2e0e1a",
        "primary_container":      "#5c1a3a",
        "on_primary_container":   "#ffc4d8",
        "secondary":              "#e4b0c0",
        "secondary_container":    "#3d2030",
        "tertiary":               "#b2c8a8",
        "tertiary_container":     "#1e3320",
        "error":                  "#ffb4ab",
        "error_container":        "#93000a",
        "surface":                "#1a1014",
        "surface_cont_lowest":    "#140c10",
        "surface_cont_low":       "#1e1418",
        "surface_cont":           "#23181d",
        "surface_cont_high":      "#2d2025",
        "surface_cont_highest":   "#3d2e34",
        "on_surface":             "#efe0e6",
        "on_surface_var":         "#d5c0ca",
        "outline":                "#9e868e",
        "outline_var":            "#51404a",
        "success":                "#a8c77a",
        "warning":                "#ffc888",
    },
    "Yellow": {
        "seed":                   "#fff176",
        "primary":                "#fff176",
        "on_primary":             "#2e2a0a",
        "primary_container":      "#4a4a1a",
        "on_primary_container":   "#fff8b8",
        "secondary":              "#e4dca8",
        "secondary_container":    "#3d3820",
        "tertiary":               "#b8c8d4",
        "tertiary_container":     "#202a33",
        "error":                  "#ffb4ab",
        "error_container":        "#93000a",
        "surface":                "#181610",
        "surface_cont_lowest":    "#12110b",
        "surface_cont_low":       "#1c1a14",
        "surface_cont":           "#201e18",
        "surface_cont_high":      "#2a2820",
        "surface_cont_highest":   "#3a382e",
        "on_surface":             "#efe8db",
        "on_surface_var":         "#d5d0bc",
        "outline":                "#9e9886",
        "outline_var":            "#514c3e",
        "success":                "#a8c77a",
        "warning":                "#ffc888",
    },
}


def build_css(p: dict) -> str:
    """Generate the full CSS string from a palette dict."""
    return f"""
/* ===== Material You — Dynamic Theme ===== */

/* ── Window ── */
window.material-you-installer {{
    background-color: {p["surface"]};
}}

/* ── Navigation pages ── */
.page-surface {{
    background-color: {p["surface"]};
}}

/* ── HeaderBar ── */
.header-transparent {{
    background-color: transparent;
    border-bottom: none;
}}

.header-surface {{
    background-color: {p["surface_cont_low"]};
    border-bottom: 1px solid {p["outline_var"]};
}}

/* ── Primary Container (hero area) ── */
.primary-container {{
    background-color: {p["primary_container"]};
    border-radius: 28px;
    padding: 36px 28px 28px 28px;
}}

.on-primary-container {{
    color: {p["on_primary_container"]};
}}

/* ── Typography ── */
.display-medium {{
    font-size: 40px;
    font-weight: 800;
    letter-spacing: -0.5px;
    color: {p["on_primary_container"]};
}}

.headline-small {{
    font-size: 22px;
    font-weight: 600;
    color: {p["on_surface"]};
}}

.title-large {{
    font-size: 20px;
    font-weight: 600;
    color: {p["on_surface"]};
}}

.title-medium {{
    font-size: 16px;
    font-weight: 500;
    letter-spacing: 0.15px;
    color: {p["on_surface"]};
}}

.title-small {{
    font-size: 14px;
    font-weight: 500;
    letter-spacing: 0.1px;
    color: {p["on_surface"]};
}}

.body-large {{
    font-size: 16px;
    font-weight: 400;
    letter-spacing: 0.5px;
    color: {p["on_surface_var"]};
}}

.body-medium {{
    font-size: 14px;
    font-weight: 400;
    letter-spacing: 0.25px;
    color: {p["on_surface_var"]};
}}

.body-small {{
    font-size: 12px;
    font-weight: 400;
    letter-spacing: 0.4px;
    color: {p["outline"]};
}}

.label-large {{
    font-size: 14px;
    font-weight: 500;
    letter-spacing: 0.1px;
    color: {p["primary"]};
}}

.label-medium {{
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.5px;
    color: {p["outline"]};
}}

.label-small {{
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.5px;
    color: {p["outline"]};
}}

/* ── Surface Cards ── */
.surface-container {{
    background-color: {p["surface_cont"]};
    border-radius: 16px;
}}

.surface-container-low {{
    background-color: {p["surface_cont_low"]};
    border-radius: 16px;
}}

.surface-container-high {{
    background-color: {p["surface_cont_high"]};
    border-radius: 16px;
}}

.surface-container-highest {{
    background-color: {p["surface_cont_highest"]};
    border-radius: 12px;
}}

/* ── Filled Button (Primary) ── */
.filled-button {{
    background-color: {p["primary"]};
    color: {p["on_primary"]};
    font-weight: 600;
    font-size: 14px;
    letter-spacing: 0.1px;
    border-radius: 20px;
    padding: 12px 24px;
    min-height: 20px;
    border: none;
    transition: opacity 200ms ease-in-out;
}}

.filled-button:hover {{
    opacity: 0.92;
}}

.filled-button:active {{
    opacity: 0.82;
}}

/* ── Filled Tonal Button ── */
.tonal-button {{
    background-color: {p["secondary_container"]};
    color: {p["secondary"]};
    font-weight: 600;
    font-size: 14px;
    letter-spacing: 0.1px;
    border-radius: 20px;
    padding: 10px 24px;
    min-height: 20px;
    border: none;
    transition: opacity 200ms ease-in-out;
}}

.tonal-button:hover {{
    opacity: 0.88;
}}

/* ── Outlined Button ── */
.outlined-button {{
    background-color: transparent;
    color: {p["primary"]};
    font-weight: 600;
    font-size: 14px;
    border-radius: 20px;
    padding: 10px 24px;
    min-height: 20px;
    border: 1px solid {p["outline"]};
    transition: background-color 200ms ease-in-out;
}}

.outlined-button:hover {{
    background-color: {p["surface_cont_high"]};
}}

/* ── Text Button ── */
.text-button-primary {{
    color: {p["primary"]};
    font-weight: 600;
    font-size: 14px;
    letter-spacing: 0.1px;
    padding: 10px 12px;
    border-radius: 20px;
    background-color: transparent;
    border: none;
    transition: background-color 200ms ease-in-out;
}}

.text-button-primary:hover {{
    background-color: {p["surface_cont_high"]};
}}

/* ── FAB (Floating Action Button) ── */
.fab-primary {{
    background-color: {p["primary_container"]};
    color: {p["on_primary_container"]};
    font-weight: 600;
    font-size: 15px;
    letter-spacing: 0.1px;
    border-radius: 16px;
    padding: 16px 20px;
    min-height: 24px;
    border: none;
    transition: opacity 200ms ease-in-out;
}}

.fab-primary:hover {{
    opacity: 0.92;
}}

/* ── Extended FAB ── */
.fab-extended {{
    background-color: {p["primary_container"]};
    color: {p["on_primary_container"]};
    font-weight: 600;
    font-size: 15px;
    letter-spacing: 0.1px;
    border-radius: 16px;
    padding: 16px 28px;
    min-height: 24px;
    border: none;
    transition: opacity 200ms ease-in-out;
}}

.fab-extended:hover {{
    opacity: 0.92;
}}

/* ── Hero Pill Button (large) ── */
.hero-pill {{
    background: {p["primary"]};
    color: {p["on_primary"]};
    font-weight: 700;
    font-size: 17px;
    letter-spacing: 0.1px;
    border-radius: 100px;
    padding: 18px 48px;
    min-height: 28px;
    border: none;
    transition: opacity 200ms ease-in-out;
}}

.hero-pill:hover {{
    opacity: 0.90;
}}

.hero-pill:active {{
    opacity: 0.80;
}}

/* ── Switch ── */
switch {{
    background-color: {p["outline_var"]};
    border-radius: 16px;
    transition: background-color 200ms ease-in-out;
}}

switch:checked {{
    background-color: {p["primary"]};
}}

switch slider {{
    background-color: {p["outline"]};
    border-radius: 14px;
    transition: all 200ms ease-in-out;
}}

switch:checked slider {{
    background-color: {p["on_primary"]};
}}

/* ── Progress Bar ── */
progressbar trough {{
    background-color: {p["surface_cont_high"]};
    border-radius: 4px;
    min-height: 4px;
}}

progressbar progress {{
    background-color: {p["primary"]};
    border-radius: 4px;
    min-height: 4px;
    transition: all 300ms ease-in-out;
}}

/* ── List / PreferencesGroup ── */
.m3-group {{
    background-color: {p["surface_cont_low"]};
    border-radius: 20px;
    margin: 4px 16px;
    padding: 4px 0;
}}

.m3-group > header {{
    padding: 16px 16px 8px 16px;
}}

/* Rows inside groups */
.m3-row {{
    padding: 12px 16px;
    margin: 0 4px;
    border-radius: 14px;
    transition: background-color 150ms ease-in-out;
}}

.m3-row:hover {{
    background-color: {p["surface_cont"]};
}}

/* ── Status Colors ── */
.color-primary {{
    color: {p["primary"]};
}}

.color-on-surface {{
    color: {p["on_surface"]};
}}

.color-on-surface-var {{
    color: {p["on_surface_var"]};
}}

.color-outline {{
    color: {p["outline"]};
}}

.color-success {{
    color: {p["success"]};
}}

.color-error {{
    color: {p["error"]};
}}

.color-warning {{
    color: {p["warning"]};
}}

/* ── Icon in Primary Container ── */
.icon-primary-container {{
    background-color: {p["surface_cont_high"]};
    border-radius: 14px;
    padding: 10px;
}}

/* ── Chip / Badge ── */
.chip-filled {{
    background-color: {p["secondary_container"]};
    color: {p["secondary"]};
    border-radius: 8px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 600;
}}

.chip-error {{
    background-color: {p["error_container"]};
    color: {p["error"]};
    border-radius: 8px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}}

/* ── Divider ── */
.divider {{
    background-color: {p["outline_var"]};
    min-height: 1px;
    margin: 0 16px;
}}

/* ── Scrollbar ── */
scrollbar slider {{
    background-color: {p["outline_var"]};
    border-radius: 100px;
    min-width: 4px;
}}

scrollbar slider:hover {{
    background-color: {p["outline"]};
}}

/* ── Toast ── */
toast {{
    background: {p["surface_cont_highest"]};
    color: {p["on_surface"]};
    border-radius: 16px;
}}

toast button {{
    background: transparent;
    color: {p["primary"]};
    font-weight: 600;
}}

/* ── Info Card ── */
.info-card {{
    background-color: {p["surface_cont_low"]};
    border-radius: 16px;
    padding: 16px;
    margin: 4px 16px;
}}

/* ── Result Row ── */
.result-row-success {{
    background-color: {p["surface_cont_low"]};
    border-radius: 14px;
    padding: 12px 16px;
    margin: 2px 16px;
}}

.result-row-fail {{
    background-color: rgba(147, 0, 10, 0.12);
    border-radius: 14px;
    padding: 12px 16px;
    margin: 2px 16px;
}}

.result-row-skip {{
    background-color: {p["surface_cont_low"]};
    border-radius: 14px;
    padding: 12px 16px;
    margin: 2px 16px;
    opacity: 0.7;
}}

/* ── Status Page icons ── */
.success-large-icon {{
    color: {p["success"]};
    font-size: 64px;
    font-weight: 200;
}}

.warning-large-icon {{
    color: {p["warning"]};
    font-size: 64px;
    font-weight: 200;
}}

/* ── Pulsing dot ── */
@keyframes m3-pulse {{
    0%   {{ opacity: 0.4; }}
    50%  {{ opacity: 1.0; }}
    100% {{ opacity: 0.4; }}
}}

.pulse {{
    animation: m3-pulse 1.2s ease-in-out infinite;
}}

/* ── Counter Pill ── */
.counter-pill {{
    background-color: {p["primary_container"]};
    color: {p["on_primary_container"]};
    border-radius: 100px;
    padding: 6px 16px;
    font-size: 13px;
    font-weight: 600;
}}

/* ── Bottom Bar ── */
.bottom-bar {{
    background-color: {p["surface_cont"]};
    padding: 12px 16px;
    border-top: 1px solid {p["outline_var"]};
}}

/* ── Note Banner ── */
.note-banner {{
    background-color: {p["surface_cont_high"]};
    border-radius: 12px;
    padding: 12px 16px;
    margin: 8px 16px;
}}

/* ── Color Circle ── */
.color-circle {{
    border-radius: 9999px;
    min-width: 56px;
    min-height: 56px;
    border: 3px solid transparent;
    transition: all 200ms ease-in-out;
}}

.color-circle:hover {{
    opacity: 0.85;
}}

.color-circle-selected {{
    border-color: {p["on_surface"]};
}}

/* ── Swatch Preview ── */
.swatch {{
    border-radius: 12px;
    min-height: 40px;
    min-width: 60px;
}}

/* ── Expanded layout helpers ── */
.expanded-pane {{
    padding: 24px;
}}

.compact-only {{}}
.expanded-only {{}}

/* ── Bottom Navigation Bar (Material 3) ── */
.bottom-nav-bar {{
    background-color: {p["surface_cont"]};
    padding: 4px 0;
}}

.nav-item,
.nav-item:hover,
.nav-item:active,
.nav-item:focus {{
    background: none;
    box-shadow: none;
    border: none;
    outline: none;
    padding: 0;
    margin: 0;
    min-height: 0;
    min-width: 0;
}}

.nav-pill-bg {{
    border-radius: 14px;
    padding: 4px 18px;
    transition: background-color 200ms ease-in-out;
}}

.nav-pill-active {{
    background-color: {p["secondary_container"]};
}}

.nav-icon {{
    color: {p["on_surface_var"]};
}}

.nav-icon-active {{
    color: {p["on_surface"]};
}}

.nav-label {{
    font-size: 12px;
    font-weight: 500;
    color: {p["on_surface_var"]};
    margin-top: 1px;
}}

.nav-label-active {{
    font-weight: 700;
    color: {p["on_surface"]};
}}

/* ── System Carousel Card ── */
.sys-carousel-card {{
    background-color: {p["surface_cont_low"]};
    border-radius: 12px;
    padding: 10px 12px;
}}

/* ── Clickable row ── */
.clickable-row {{
    transition: background-color 150ms ease-in-out;
}}

.clickable-row:hover {{
    background-color: {p["surface_cont"]};
}}
"""


# ─── Palette State Helpers ──────────────────────────────────────────────────

def load_installed_palette() -> str | None:
    """Read the name of the currently installed palette from state file."""
    if PALETTE_STATE_FILE.exists():
        try:
            data = json.loads(PALETTE_STATE_FILE.read_text())
            return data.get("palette")
        except (json.JSONDecodeError, OSError):
            pass
    return None


def save_installed_palette(name: str) -> None:
    """Write the currently installed palette name to state file."""
    PALETTE_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    PALETTE_STATE_FILE.write_text(json.dumps({"palette": name}))


# ─── HSL Color Helpers ─────────────────────────────────────────────────────

# Colors that must NEVER be hue-shifted (standard GNOME / semantic colors)
PROTECTED_COLORS = {
    # GNOME blues
    "#3584e4", "#1c71d8", "#1a5fb4", "#99c1f1", "#62a0ea",
    # GNOME greens
    "#33d17a", "#2ec27e", "#26a269", "#57e389", "#8ff0a4", "#8cd48c", "#1b5e20",
    # GNOME yellows
    "#f9f06b", "#f8e45c", "#f6d32d", "#f5c211", "#e5a50a",
    # GNOME reds
    "#f66151", "#ed333b", "#e01b24", "#c01c28", "#a51d2d",
    # GNOME purples
    "#dc8add", "#c061cb", "#9141ac", "#813d9c", "#613583",
    "#e4dfff", "#c8bfff", "#2f2d5e", "#464490",
    # Pure neutrals
    "#ffffff", "#f6f5f4", "#deddda", "#c0bfbc", "#9a9996",
    "#77767b", "#5e5c64", "#3d3846", "#241f31", "#000000",
    # Error (constant across all palettes)
    "#93000a", "#a5000c", "#ffb4ab",
    # Success / warning (constant across all palettes)
    "#a8c77a", "#ffc888",
}


def hex_to_hsl(hex_color: str) -> tuple[float, float, float]:
    """Convert #rrggbb to (H, S, L). H is 0-360, S and L are 0-1."""
    r = int(hex_color[1:3], 16) / 255
    g = int(hex_color[3:5], 16) / 255
    b = int(hex_color[5:7], 16) / 255
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return (h * 360, s, l)


def hsl_to_hex(h: float, s: float, l: float) -> str:
    """Convert (H, S, L) to #rrggbb."""
    r, g, b = colorsys.hls_to_rgb(h / 360, l, s)
    ri = max(0, min(255, int(r * 255 + 0.5)))
    gi = max(0, min(255, int(g * 255 + 0.5)))
    bi = max(0, min(255, int(b * 255 + 0.5)))
    return f"#{ri:02x}{gi:02x}{bi:02x}"


def build_full_color_map(old_palette: dict, new_palette: dict,
                         css_files: list[Path]) -> dict[str, str]:
    """Build hex→hex map covering palette tokens + hue-shifted intermediate colors."""
    mapping: dict[str, str] = {}

    # 1. Direct palette token mappings
    for key in old_palette:
        old_hex = old_palette[key].lower()
        new_hex = new_palette[key].lower()
        if old_hex != new_hex:
            mapping[old_hex] = new_hex

    # 2. Compute hue shift between primaries
    old_hue, _, _ = hex_to_hsl(old_palette["primary"])
    new_hue, _, _ = hex_to_hsl(new_palette["primary"])
    hue_shift = new_hue - old_hue

    if abs(hue_shift) < 0.5:
        return mapping  # same hue, nothing extra to shift

    # 3. Collect all hex colors from the CSS files
    all_hexes: set[str] = set()
    for path in css_files:
        if path.exists():
            try:
                text = path.read_text()
                all_hexes.update(h.lower() for h in re.findall(r'#[0-9a-fA-F]{6}\b', text))
            except OSError:
                pass

    # 4. For each hex not already mapped, hue-shift if it's theme-specific
    target_values = set(mapping.values())
    for hex_color in all_hexes:
        if hex_color in mapping or hex_color in PROTECTED_COLORS or hex_color in target_values:
            continue
        h, s, l = hex_to_hsl(hex_color)
        # Only shift colors within ±35° of old primary hue with saturation > 0.05
        hue_dist = abs(h - old_hue)
        if hue_dist > 180:
            hue_dist = 360 - hue_dist
        if hue_dist <= 35 and s > 0.05:
            new_h = (h + hue_shift) % 360
            new_hex = hsl_to_hex(new_h, s, l)
            if new_hex != hex_color:
                mapping[hex_color] = new_hex

    return mapping


def recolor_file(path: Path, color_map: dict[str, str]) -> bool:
    """Replace hex colors in a text file using single-pass regex. Returns True if changed."""
    try:
        text = path.read_text()
    except OSError:
        return False
    if not color_map:
        return False

    # Build a regex matching all old hex values (case insensitive)
    pattern = re.compile(
        '(' + '|'.join(re.escape(v) for v in color_map) + ')',
        re.IGNORECASE,
    )

    def _replacer(m: re.Match) -> str:
        matched = m.group(0).lower()
        new = color_map.get(matched, m.group(0))
        # Preserve uppercase if original was uppercase
        if m.group(0)[1:].isupper():
            return '#' + new[1:].upper()
        return new

    new_text = pattern.sub(_replacer, text)
    if new_text != text:
        try:
            path.write_text(new_text)
            return True
        except OSError:
            return False
    return False


# ─── Component metadata ─────────────────────────────────────────────────────

COMPONENT_META = {
    1:  ("color-profile-symbolic",             "GNOME Shell CSS",                     "Theme"),
    2:  ("preferences-desktop-appearance-symbolic", "GTK4 application styling",        "Theme"),
    3:  ("preferences-desktop-appearance-symbolic", "GTK3 legacy app styling",         "Theme"),
    4:  ("utilities-terminal-symbolic",        "Terminal color palette",               "Theme"),
    5:  ("preferences-system-details-symbolic","System info display config",           "Theme"),
    6:  ("view-reveal-symbolic",               "Window open/close effects",            "Theme"),
    7:  ("preferences-desktop-wallpaper-symbolic", "Desktop & lock screen wallpaper",  "Theme"),
    8:  ("font-x-generic-symbolic",            "Inter, Fira Code, Noto Serif",        "Assets"),
    9:  ("folder-symbolic",                    "Papirus Dark icon pack",               "Assets"),
    10: ("input-mouse-symbolic",               "Bibata Modern Classic",                "Assets"),
    11: ("application-x-addon-symbolic",       "12 GNOME Shell extensions",            "Extensions & Config"),
    12: ("emblem-system-symbolic",             "57 dconf keys",                        "Extensions & Config"),
    13: ("system-run-symbolic",                "Global Flatpak theme override",        "Flatpak"),
    14: ("emblem-symbolic-link-symbolic",       "GTK CSS symlinks for all apps",       "Flatpak"),
    15: ("web-browser-symbolic",               "userChrome + userContent CSS",         "Apps"),
    16: ("system-lock-screen-symbolic",        "Login screen theme",                   "System"),
    17: ("applications-system-symbolic",       "Desktop icons CSS fix",                "System"),
    18: ("system-software-install-symbolic",  "rEFInd boot manager",                  "System"),
    19: ("color-profile-symbolic",            "Material You rEFInd theme",            "System"),
}

# Map palette name → GNOME accent-color dconf value
ACCENT_COLOR_MAP = {
    "Orange": "orange",
    "Blue":   "blue",
    "Green":  "green",
    "Purple": "purple",
    "Red":    "red",
    "Teal":   "teal",
    "Pink":   "pink",
    "Yellow": "yellow",
}

# Map palette name → papirus-folders color name
PAPIRUS_FOLDER_MAP = {
    "Orange":  "orange",
    "Blue":    "blue",
    "Green":   "green",
    "Purple":  "violet",
    "Red":     "red",
    "Teal":    "teal",
    "Pink":    "pink",
    "Yellow":  "yellow",
}

COMPONENT_DESCRIPTIONS = {
    1:  "Installs the Material You CSS for GNOME Shell: top bar, quick settings, notifications, OSD, overview, calendar and lock screen.",
    2:  "Custom GTK4/libadwaita stylesheet for Nautilus, Settings, Text Editor, and all modern GNOME apps.",
    3:  "Custom GTK3 stylesheet for legacy apps that haven't migrated to GTK4 yet (Firefox UI, older GNOME apps).",
    4:  "Material You color palette for the Ptyxis terminal: 16 ANSI colors plus foreground, background and cursor.",
    5:  "Themed system info layout for Fastfetch with Material You colors, custom ASCII art and module order.",
    6:  "Burn My Windows animation profile with fire/glow colors matched to the Material You palette.",
    7:  "Sets the desktop wallpaper and lock screen background to the Material You dark gradient image.",
    8:  "Downloads and installs three font families: Inter (UI), Fira Code (monospace) and Noto Serif (documents).",
    9:  "Installs the Papirus Dark flat icon pack with consistent symbolic and full-color icons.",
    10: "Installs the Bibata Modern Classic cursor theme with smooth animations and HiDPI support.",
    11: "Installs 12 GNOME Shell extensions: Blur My Shell, Logo Menu, Hot Edge, Caffeine, Magic Lamp, and more.",
    12: "Applies 57 dconf keys: accent color, fonts, cursor theme, icon theme, night light, wallpaper paths and extension settings.",
    13: "Writes a global Flatpak override so sandboxed apps can read the GTK theme, icons and cursor.",
    14: "Creates gtk.css symlinks inside each Flatpak app's config directory for full theme coverage.",
    15: "Installs userChrome.css and userContent.css for a fully dark Material You Firefox interface.",
    16: "Configures the GDM login screen: Material You dconf profile, Inter font and Bibata cursor. Requires sudo.",
    17: "Patches the DING desktop icons extension CSS priority from 600 to 900 to prevent theme conflicts.",
    18: "Installs the rEFInd EFI boot manager from the local RPM package and runs refind-install. Requires sudo.",
    19: "Deploys the Material You boot theme to the ESP partition: background, circular selection icons and OS logos.",
}


# ─── Application ─────────────────────────────────────────────────────────────

class MaterialYouApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="com.material-you-orange.installer",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self.css_provider = None
        self.current_palette_name = "Orange"

    def do_activate(self):
        win = InstallerWindow(application=self)
        win.present()

    def do_startup(self):
        Adw.Application.do_startup(self)
        self.get_style_manager().set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        self.css_provider = Gtk.CssProvider()
        self.css_provider.load_from_string(build_css(PALETTES["Orange"]))
        # Use USER+1 to override the global ~/.config/gtk-4.0/gtk.css
        # which is loaded at PRIORITY_USER and sets toast bg to inverse_surface
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER + 1,
        )

    def reload_css(self, palette_name: str):
        self.current_palette_name = palette_name
        p = PALETTES[palette_name]
        self.css_provider.load_from_string(build_css(p))


# ─── Main Window ─────────────────────────────────────────────────────────────

class InstallerWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Material Gnome")
        self.set_default_size(480, 800)
        self.set_icon_name("com.material-you-orange.installer")
        self.add_css_class("material-you-installer")

        self.sys_info: SystemInfo | None = None
        self.selected: dict[int, bool] = {s.number: True for s in ALL_STEPS}
        self.results: list[ComponentResult] = []
        self.switches: dict[int, Gtk.Switch] = {}
        self.progress_rows: dict[int, dict] = {}

        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.toast_overlay.set_child(main_box)

        self.nav = Adw.NavigationView()
        self.nav.set_vexpand(True)
        main_box.append(self.nav)

        self.bottom_nav = self._build_bottom_nav()
        main_box.append(self.bottom_nav)
        self.bottom_nav.set_visible(False)
        self._is_expanded = False

        win_bp = Adw.Breakpoint()
        win_bp.set_condition(Adw.BreakpointCondition.parse("min-width: 700px"))
        win_bp.connect("apply", self._on_window_expand)
        win_bp.connect("unapply", self._on_window_compact)
        self.add_breakpoint(win_bp)

        self.nav.connect("notify::visible-page", self._on_visible_page_changed)

        self._show_loading()
        threading.Thread(target=self._detect, daemon=True).start()

    def _get_app(self) -> MaterialYouApp:
        return self.get_application()

    def _get_palette(self) -> dict:
        return PALETTES[self._get_app().current_palette_name]

    # ── Loading ──────────────────────────────────────────────────────────

    def _show_loading(self):
        page = Adw.StatusPage()
        page.set_title("Material Gnome")
        page.set_description("Detecting system...")
        page.set_icon_name("emblem-system-symbolic")
        page.add_css_class("page-surface")
        nav_page = Adw.NavigationPage(title="Loading", child=page)
        self.nav.push(nav_page)

    def _detect(self):
        info = SystemDetector().detect()
        GLib.idle_add(self._on_detected, info)

    def _on_detected(self, info: SystemInfo):
        self.sys_info = info
        self.nav.replace([self._build_welcome()])

    # ── PAGE 1: Welcome ──────────────────────────────────────────────────

    def _build_welcome(self) -> Adw.NavigationPage:
        bp_page = Adw.BreakpointBin()
        bp_page.set_size_request(360, 400)

        # === Compact layout (single column, scrollable) ===
        compact = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        toolbar_c = Adw.ToolbarView()
        hbar_c = Adw.HeaderBar()
        hbar_c.add_css_class("header-transparent")
        hbar_c.set_show_title(False)
        toolbar_c.add_top_bar(hbar_c)

        scroll_c = Gtk.ScrolledWindow(vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER)
        clamp_c = Adw.Clamp(maximum_size=600, tightening_threshold=400)
        content_c = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        clamp_c.set_child(content_c)
        scroll_c.set_child(clamp_c)
        toolbar_c.set_content(scroll_c)

        # Hero
        hero_c = self._make_hero()
        hero_c.set_margin_start(16)
        hero_c.set_margin_end(16)
        hero_c.set_margin_top(8)
        content_c.append(hero_c)
        content_c.append(self._spacer(16))

        # System info (3x2 grid)
        sys_grid_c = self._make_sys_grid()
        sys_grid_c.set_margin_start(16)
        sys_grid_c.set_margin_end(16)
        content_c.append(sys_grid_c)
        content_c.append(self._spacer(8))

        # Features
        inc_group_c = self._make_features_group()
        content_c.append(inc_group_c)
        content_c.append(self._spacer(24))

        # Button
        btn_c = Gtk.Button(label="Get Started")
        btn_c.add_css_class("hero-pill")
        btn_c.set_halign(Gtk.Align.CENTER)
        btn_c.connect("clicked", lambda b: self.nav.push(self._build_color_picker()))
        content_c.append(btn_c)
        content_c.append(self._spacer(32))

        compact.append(toolbar_c)

        # === Expanded layout (two columns) ===
        expanded = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        toolbar_e = Adw.ToolbarView()
        hbar_e = Adw.HeaderBar()
        hbar_e.add_css_class("header-transparent")
        hbar_e.set_show_title(False)
        toolbar_e.add_top_bar(hbar_e)

        two_col = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0,
                          vexpand=True, hexpand=True)

        # Left pane: hero + system carousel + button
        left_scroll = Gtk.ScrolledWindow(vexpand=True, hexpand=True,
                                         hscrollbar_policy=Gtk.PolicyType.NEVER)
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0,
                       hexpand=True, vexpand=True, valign=Gtk.Align.CENTER)
        left.add_css_class("expanded-pane")

        hero_e = self._make_hero()
        left.append(hero_e)
        left.append(self._spacer(16))

        sys_grid_e = self._make_sys_grid()
        left.append(sys_grid_e)
        left.append(self._spacer(24))

        btn_e = Gtk.Button(label="Get Started")
        btn_e.add_css_class("hero-pill")
        btn_e.set_halign(Gtk.Align.CENTER)
        btn_e.connect("clicked", lambda b: self.nav.push(self._build_color_picker()))
        left.append(btn_e)

        left_scroll.set_child(left)
        two_col.append(left_scroll)

        # Right pane: features
        right_scroll = Gtk.ScrolledWindow(vexpand=True, hexpand=True,
                                          hscrollbar_policy=Gtk.PolicyType.NEVER)
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0,
                        vexpand=True, valign=Gtk.Align.CENTER)
        right.add_css_class("expanded-pane")

        inc_group_e = self._make_features_group()
        right.append(inc_group_e)
        right.append(self._spacer(24))

        right_scroll.set_child(right)
        two_col.append(right_scroll)

        toolbar_e.set_content(two_col)
        expanded.append(toolbar_e)

        stack = Gtk.Stack()
        self._setup_breakpoint(bp_page, compact, expanded, stack)

        return Adw.NavigationPage(title="Welcome", tag="welcome", child=bp_page)

    def _make_hero(self) -> Gtk.Box:
        hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        hero.add_css_class("primary-container")

        lbl_m = Gtk.Label(label="Material")
        lbl_m.add_css_class("display-medium")
        lbl_m.set_halign(Gtk.Align.START)
        hero.append(lbl_m)

        lbl_o = Gtk.Label(label="Gnome")
        lbl_o.add_css_class("display-medium")
        lbl_o.set_halign(Gtk.Align.START)
        hero.append(lbl_o)

        lbl_sub = Gtk.Label(label="Install Material You on your PC")
        lbl_sub.add_css_class("body-medium")
        lbl_sub.add_css_class("on-primary-container")
        lbl_sub.set_halign(Gtk.Align.START)
        lbl_sub.set_margin_top(8)
        hero.append(lbl_sub)

        lbl_v = Gtk.Label(label=f"v{VERSION}")
        lbl_v.add_css_class("label-small")
        lbl_v.add_css_class("on-primary-container")
        lbl_v.set_halign(Gtk.Align.START)
        lbl_v.set_margin_top(4)
        hero.append(lbl_v)

        return hero

    def _make_sys_group(self) -> Adw.PreferencesGroup:
        sys_group = Adw.PreferencesGroup(title="System")
        sys_group.set_margin_start(16)
        sys_group.set_margin_end(16)

        info = self.sys_info
        sys_rows = [
            ("computer-symbolic",               "Distribution", info.distro_name.split("(")[0].strip() if info.distro_name else "Unknown"),
            ("desktop-symbolic",                 "GNOME Shell",  info.gnome_version or "Not detected"),
            ("video-display-symbolic",           "Display",      "Wayland" if info.is_wayland else "X11"),
            ("drive-harddisk-symbolic",          "System Type",  "Immutable" if info.is_immutable else "Mutable"),
            ("package-x-generic-symbolic",       "Packages",     info.pkg_manager.value.upper()),
            ("system-software-install-symbolic", "Flatpak",      "Available" if info.has_flatpak else "Not found"),
        ]

        for icon_name, title, value in sys_rows:
            row = Adw.ActionRow(title=title, subtitle=value)
            icon = Gtk.Image.new_from_icon_name(icon_name)
            icon.set_pixel_size(20)
            icon.add_css_class("color-primary")
            row.add_prefix(icon)
            sys_group.add(row)

        return sys_group

    def _make_sys_grid(self) -> Gtk.Box:
        """Two-row grid of system info cards (3 per row)."""
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

        title = Gtk.Label(label="System")
        title.add_css_class("title-medium")
        title.set_halign(Gtk.Align.START)
        title.set_margin_start(4)
        outer.append(title)

        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)
        grid.set_column_homogeneous(True)

        info = self.sys_info
        items = [
            ("computer-symbolic",               "Distribution",
             info.distro_name.split("(")[0].strip() if info.distro_name else "Unknown"),
            ("desktop-symbolic",                 "GNOME Shell",
             info.gnome_version or "Not detected"),
            ("video-display-symbolic",           "Display",
             "Wayland" if info.is_wayland else "X11"),
            ("drive-harddisk-symbolic",          "System Type",
             "Immutable" if info.is_immutable else "Mutable"),
            ("package-x-generic-symbolic",       "Packages",
             info.pkg_manager.value.upper()),
            ("system-software-install-symbolic", "Flatpak",
             "Available" if info.has_flatpak else "Not found"),
        ]

        for i, (icon_name, title_text, value_text) in enumerate(items):
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            card.add_css_class("sys-carousel-card")
            card.set_hexpand(True)

            icon = Gtk.Image.new_from_icon_name(icon_name)
            icon.set_pixel_size(16)
            icon.add_css_class("color-primary")
            icon.set_halign(Gtk.Align.START)
            card.append(icon)

            lbl_t = Gtk.Label(label=title_text)
            lbl_t.add_css_class("label-small")
            lbl_t.set_halign(Gtk.Align.START)
            lbl_t.set_ellipsize(Pango.EllipsizeMode.END)
            card.append(lbl_t)

            lbl_v = Gtk.Label(label=value_text)
            lbl_v.add_css_class("body-small")
            lbl_v.set_halign(Gtk.Align.START)
            lbl_v.set_ellipsize(Pango.EllipsizeMode.END)
            card.append(lbl_v)

            grid.attach(card, i % 3, i // 3, 1, 1)

        outer.append(grid)
        return outer

    def _make_features_group(self) -> Adw.PreferencesGroup:
        inc_group = Adw.PreferencesGroup(title="What's Included")
        inc_group.set_margin_start(16)
        inc_group.set_margin_end(16)

        features = [
            ("color-profile-symbolic",       "GNOME Shell + GTK Theme",   "Complete dark theme with dynamic accents"),
            ("font-x-generic-symbolic",      "Fonts",                      "Inter, Fira Code, Noto Serif"),
            ("application-x-addon-symbolic", "12 GNOME Extensions",        "Pre-configured and enabled"),
            ("web-browser-symbolic",         "Firefox Theme",              "Custom CSS for dark UI"),
            ("emblem-system-symbolic",       "57 System Settings",         "dconf, Flatpak, night light, cursors"),
            ("document-save-symbolic",       "Backup and Restore",         "Full undo with timestamped backups"),
        ]

        for icon_name, title, desc in features:
            row = Adw.ActionRow(title=title, subtitle=desc)
            icon = Gtk.Image.new_from_icon_name(icon_name)
            icon.set_pixel_size(20)
            icon.add_css_class("color-primary")
            row.add_prefix(icon)
            inc_group.add(row)

        return inc_group

    # ── PAGE 2: Color Picker ─────────────────────────────────────────────

    def _build_color_picker(self) -> Adw.NavigationPage:
        bp_page = Adw.BreakpointBin()
        bp_page.set_size_request(360, 400)

        # State for circle widgets
        self._color_circles: dict[str, Gtk.Button] = {}
        self._color_checks: dict[str, Gtk.Image] = {}
        self._preview_swatches: list[tuple[Gtk.Box, str]] = []  # (widget, token_key)
        self._preview_labels: list[tuple[Gtk.Label, str]] = []

        # === Compact layout ===
        compact = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        toolbar_c = Adw.ToolbarView()
        hbar_c = Adw.HeaderBar()
        hbar_c.add_css_class("header-surface")
        hbar_c.set_title_widget(Gtk.Label(label="Choose Color", css_classes=["title-medium"]))
        toolbar_c.add_top_bar(hbar_c)

        scroll_c = Gtk.ScrolledWindow(vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER)
        clamp_c = Adw.Clamp(maximum_size=600, tightening_threshold=400)
        content_c = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        clamp_c.set_child(content_c)
        scroll_c.set_child(clamp_c)
        toolbar_c.set_content(scroll_c)

        content_c.append(self._spacer(24))
        grid_c = self._make_color_grid("compact")
        grid_c.set_halign(Gtk.Align.CENTER)
        content_c.append(grid_c)
        content_c.append(self._spacer(24))

        preview_c = self._make_preview_card("compact")
        preview_c.set_margin_start(16)
        preview_c.set_margin_end(16)
        content_c.append(preview_c)
        content_c.append(self._spacer(24))

        btn_row_c = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12,
                            halign=Gtk.Align.CENTER)
        aggiorna_c = Gtk.Button(label="Aggiorna")
        aggiorna_c.add_css_class("tonal-button")
        aggiorna_c.set_size_request(140, -1)
        aggiorna_c.connect("clicked", self._on_aggiorna)
        btn_row_c.append(aggiorna_c)

        btn_c = Gtk.Button(label="Continue")
        btn_c.add_css_class("fab-extended")
        btn_c.set_size_request(180, -1)
        btn_c.connect("clicked", lambda b: self.nav.push(self._build_components()))
        btn_row_c.append(btn_c)
        content_c.append(btn_row_c)
        content_c.append(self._spacer(32))

        compact.append(toolbar_c)

        # === Expanded layout ===
        expanded = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        toolbar_e = Adw.ToolbarView()
        hbar_e = Adw.HeaderBar()
        hbar_e.add_css_class("header-surface")
        hbar_e.set_title_widget(Gtk.Label(label="Choose Color", css_classes=["title-medium"]))
        toolbar_e.add_top_bar(hbar_e)

        two_col = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0,
                          vexpand=True, hexpand=True)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16,
                       hexpand=True, vexpand=True, valign=Gtk.Align.CENTER,
                       halign=Gtk.Align.CENTER)
        left.add_css_class("expanded-pane")

        title_l = Gtk.Label(label="Pick your accent color")
        title_l.add_css_class("headline-small")
        left.append(title_l)

        grid_e = self._make_color_grid("expanded")
        grid_e.set_halign(Gtk.Align.CENTER)
        left.append(grid_e)

        two_col.append(left)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0,
                        hexpand=True, vexpand=True)
        right.add_css_class("expanded-pane")

        preview_e = self._make_preview_card("expanded")
        preview_e.set_valign(Gtk.Align.CENTER)
        preview_e.set_vexpand(True)
        right.append(preview_e)

        btn_row_e = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12,
                            halign=Gtk.Align.END)
        btn_row_e.set_margin_bottom(24)
        btn_row_e.set_margin_end(8)

        aggiorna_e = Gtk.Button(label="Aggiorna")
        aggiorna_e.add_css_class("tonal-button")
        aggiorna_e.set_size_request(140, -1)
        aggiorna_e.connect("clicked", self._on_aggiorna)
        btn_row_e.append(aggiorna_e)

        btn_e = Gtk.Button(label="Continue")
        btn_e.add_css_class("fab-extended")
        btn_e.set_size_request(180, -1)
        btn_e.connect("clicked", lambda b: self.nav.push(self._build_components()))
        btn_row_e.append(btn_e)
        right.append(btn_row_e)

        two_col.append(right)

        toolbar_e.set_content(two_col)
        expanded.append(toolbar_e)

        stack = Gtk.Stack()
        self._setup_breakpoint(bp_page, compact, expanded, stack)

        # Initial selection state
        self._update_color_selection(self._get_app().current_palette_name)

        return Adw.NavigationPage(title="Color", tag="color", child=bp_page)

    def _make_color_grid(self, variant: str) -> Gtk.Grid:
        grid = Gtk.Grid()
        grid.set_row_spacing(12)
        grid.set_column_spacing(12)

        palette_names = list(PALETTES.keys())
        for i, name in enumerate(palette_names):
            p = PALETTES[name]
            col = i % 4
            row = i // 4

            overlay = Gtk.Overlay()

            btn = Gtk.Button()
            btn.set_size_request(64, 64)
            btn.add_css_class("color-circle")
            btn.add_css_class("flat")

            # Set background color inline via a dedicated per-circle CSS
            # Must use `background` shorthand to override button.flat's `background: none`
            circle_css = Gtk.CssProvider()
            circle_css.load_from_string(
                f".color-circle-{name.lower()}-{variant} {{ background: {p['primary']}; }}"
            )
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(), circle_css,
                Gtk.STYLE_PROVIDER_PRIORITY_USER,
            )
            btn.add_css_class(f"color-circle-{name.lower()}-{variant}")

            btn.connect("clicked", self._on_color_selected, name)
            overlay.set_child(btn)

            check = Gtk.Image.new_from_icon_name("emblem-ok-symbolic")
            check.set_pixel_size(24)
            check.set_halign(Gtk.Align.CENTER)
            check.set_valign(Gtk.Align.CENTER)
            check.set_visible(False)
            check.set_can_target(False)
            overlay.add_overlay(check)

            # Label below
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4,
                          halign=Gtk.Align.CENTER)
            box.append(overlay)
            lbl = Gtk.Label(label=name)
            lbl.add_css_class("label-small")
            box.append(lbl)

            grid.attach(box, col, row, 1, 1)

            key = f"{name}_{variant}"
            self._color_circles[key] = btn
            self._color_checks[key] = check

        return grid

    def _make_preview_card(self, variant: str) -> Gtk.Box:
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.add_css_class("surface-container")
        card.set_margin_top(8)
        card.set_margin_bottom(8)
        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        inner.set_margin_top(20)
        inner.set_margin_bottom(20)
        inner.set_margin_start(20)
        inner.set_margin_end(20)

        title = Gtk.Label(label="Preview")
        title.add_css_class("title-medium")
        title.set_halign(Gtk.Align.START)
        inner.append(title)

        p = self._get_palette()
        swatches_data = [
            ("Primary",            "primary"),
            ("Primary Container",  "primary_container"),
            ("Surface",            "surface"),
            ("Surface Container",  "surface_cont_high"),
        ]

        for label_text, token_key in swatches_data:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12,
                          valign=Gtk.Align.CENTER)

            swatch = Gtk.Box()
            swatch.add_css_class("swatch")
            swatch.set_size_request(48, 36)

            # Per-swatch CSS
            swatch_id = f"swatch-{token_key}-{variant}"
            swatch_css = Gtk.CssProvider()
            swatch_css.load_from_string(
                f".{swatch_id} {{ background-color: {p[token_key]}; border-radius: 12px; }}"
            )
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(), swatch_css,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 2,
            )
            swatch.add_css_class(swatch_id)
            row.append(swatch)

            lbl = Gtk.Label(label=label_text)
            lbl.add_css_class("body-medium")
            row.append(lbl)

            hex_lbl = Gtk.Label(label=p[token_key].upper())
            hex_lbl.add_css_class("label-medium")
            hex_lbl.set_hexpand(True)
            hex_lbl.set_halign(Gtk.Align.END)
            row.append(hex_lbl)

            inner.append(row)
            self._preview_swatches.append((swatch, token_key, swatch_id, swatch_css, variant))
            self._preview_labels.append((hex_lbl, token_key))

        card.append(inner)
        return card

    def _on_color_selected(self, btn, palette_name: str):
        self._get_app().reload_css(palette_name)
        self._update_color_selection(palette_name)
        self._update_preview_swatches(palette_name)
        self.toast_overlay.add_toast(Adw.Toast(title=f"{palette_name} theme applied"))

    def _update_color_selection(self, selected_name: str):
        for key, btn in self._color_circles.items():
            name = key.rsplit("_", 1)[0]
            check = self._color_checks[key]
            if name == selected_name:
                btn.add_css_class("color-circle-selected")
                check.set_visible(True)
            else:
                btn.remove_css_class("color-circle-selected")
                check.set_visible(False)

    def _update_preview_swatches(self, palette_name: str):
        p = PALETTES[palette_name]
        for swatch_widget, token_key, swatch_id, swatch_css, variant in self._preview_swatches:
            swatch_css.load_from_string(
                f".{swatch_id} {{ background-color: {p[token_key]}; border-radius: 12px; }}"
            )
        for hex_lbl, token_key in self._preview_labels:
            hex_lbl.set_label(p[token_key].upper())

    def _on_aggiorna(self, btn):
        """Recolor all installed theme files from the old palette to the new one."""
        new_name = self._get_app().current_palette_name
        old_name = load_installed_palette()

        if not old_name:
            self.toast_overlay.add_toast(
                Adw.Toast(title="Nessuna installazione trovata — installa prima il tema"))
            return

        if old_name == new_name:
            self.toast_overlay.add_toast(
                Adw.Toast(title=f"Il tema è già {new_name}"))
            return

        old_palette = PALETTES.get(old_name)
        new_palette = PALETTES.get(new_name)
        if not old_palette or not new_palette:
            self.toast_overlay.add_toast(Adw.Toast(title="Palette non trovata"))
            return

        # Run recolor in a thread to avoid blocking UI
        btn.set_sensitive(False)
        threading.Thread(target=self._run_aggiorna,
                         args=(old_palette, new_palette, new_name, btn),
                         daemon=True).start()

    def _run_aggiorna(self, old_palette: dict, new_palette: dict,
                      new_name: str, btn: Gtk.Button):
        """Background thread: recolor CSS files, update dconf, reload shell theme."""
        home = Path.home()
        changed = 0

        # ── 1. Recolor all CSS / config files ──────────────────────────
        targets = [
            home / ".themes" / "Material-You-Orange" / "gnome-shell" / "gnome-shell.css",
            home / ".config" / "gtk-4.0" / "gtk.css",
            home / ".config" / "gtk-3.0" / "gtk.css",
            home / ".local" / "share" / "org.gnome.Ptyxis" / "palettes" / "material-you-orange.palette",
            home / ".config" / "fastfetch" / "config.jsonc",
            home / ".config" / "burn-my-windows" / "profiles" / "material-you-orange.conf",
        ]

        # Firefox profiles
        for ff_base in [
            home / ".var" / "app" / "org.mozilla.firefox" / "config" / "mozilla" / "firefox",
            home / ".mozilla" / "firefox",
        ]:
            if ff_base.exists():
                for d in ff_base.iterdir():
                    if d.is_dir():
                        for css_name in ["userChrome.css", "userContent.css"]:
                            css_path = d / "chrome" / css_name
                            if css_path.exists():
                                targets.append(css_path)

        existing = [p for p in targets if p.exists()]

        # Build full color map: palette tokens + hue-shifted intermediate colors
        color_map = build_full_color_map(old_palette, new_palette, existing)

        for path in existing:
            if recolor_file(path, color_map):
                changed += 1

        # ── 2. Update dconf accent-color ───────────────────────────────
        accent = ACCENT_COLOR_MAP.get(new_name, "orange")
        subprocess.run(
            ["dconf", "write", "/org/gnome/desktop/interface/accent-color",
             f"'{accent}'"],
            capture_output=True, timeout=10,
        )

        # ── 3. Reload GNOME Shell theme (toggle user-theme off/on) ─────
        subprocess.run(
            ["dconf", "write",
             "/org/gnome/shell/extensions/user-theme/name", "''"],
            capture_output=True, timeout=5,
        )
        time.sleep(0.4)
        subprocess.run(
            ["dconf", "write",
             "/org/gnome/shell/extensions/user-theme/name",
             "'Material-You-Orange'"],
            capture_output=True, timeout=5,
        )

        # ── 3b. Force GTK apps to reload CSS (toggle gtk-theme) ───────
        subprocess.run(
            ["dconf", "write",
             "/org/gnome/desktop/interface/gtk-theme", "'Adwaita'"],
            capture_output=True, timeout=5,
        )
        time.sleep(0.3)
        subprocess.run(
            ["dconf", "write",
             "/org/gnome/desktop/interface/gtk-theme", "'Marble-red-dark'"],
            capture_output=True, timeout=5,
        )

        # ── 3c. Reload Ptyxis terminal palette ────────────────────────
        ptyxis_profiles = subprocess.run(
            ["dconf", "read",
             "/org/gnome/Ptyxis/profile-uuids"],
            capture_output=True, text=True, timeout=5,
        )
        if ptyxis_profiles.returncode == 0 and ptyxis_profiles.stdout.strip():
            # Parse the profile UUIDs from GVariant array
            raw = ptyxis_profiles.stdout.strip().strip("[]")
            for uid in raw.replace("'", "").split(","):
                uid = uid.strip()
                if not uid:
                    continue
                pal_key = f"/org/gnome/Ptyxis/Profiles/{uid}/palette"
                # Toggle palette off/on to force reload
                subprocess.run(
                    ["dconf", "write", pal_key, "''"],
                    capture_output=True, timeout=5,
                )
                time.sleep(0.2)
                subprocess.run(
                    ["dconf", "write", pal_key,
                     "'material-you-orange'"],
                    capture_output=True, timeout=5,
                )

        # ── 4. Papirus folder colors (re-symlink folder icons) ────────
        self._relink_papirus_folders(home, new_name)

        # ── 5. Flatpak: re-symlink (same files, triggers mtime change) ─
        gtk4_src = home / ".config" / "gtk-4.0" / "gtk.css"
        gtk3_src = home / ".config" / "gtk-3.0" / "gtk.css"
        flatpak_base = home / ".var" / "app"
        if flatpak_base.exists():
            for app_dir in flatpak_base.iterdir():
                for ver, src in [("gtk-4.0", gtk4_src), ("gtk-3.0", gtk3_src)]:
                    link = app_dir / "config" / ver / "gtk.css"
                    if link.is_symlink():
                        # Touch the symlink target to bust caches
                        try:
                            link.touch()
                        except OSError:
                            pass

        save_installed_palette(new_name)

        GLib.idle_add(self._aggiorna_done, changed, new_name, btn)

    @staticmethod
    def _relink_papirus_folders(home: Path, new_name: str):
        """Swap Papirus-Dark folder symlinks from current color to new_name."""
        new_color = PAPIRUS_FOLDER_MAP.get(new_name, "orange")
        icons_base = home / ".local" / "share" / "icons" / "Papirus-Dark"
        if not icons_base.exists():
            return

        for size_dir in icons_base.iterdir():
            places = size_dir / "places"
            if not places.is_dir():
                continue
            for link in places.iterdir():
                if not link.is_symlink():
                    continue
                target = os.readlink(link)
                # Match symlinks like folder-orange.svg, folder-orange-documents.svg
                # Also match the base: folder.svg → folder-orange.svg
                for color in PAPIRUS_FOLDER_MAP.values():
                    old_prefix = f"folder-{color}"
                    new_prefix = f"folder-{new_color}"
                    if target.startswith(old_prefix):
                        new_target = new_prefix + target[len(old_prefix):]
                        # Only relink if target exists
                        new_target_path = places / new_target
                        if new_target_path.exists() or new_target_path.is_symlink():
                            link.unlink()
                            link.symlink_to(new_target)
                        break

        # Update icon cache
        subprocess.run(
            ["gtk-update-icon-cache", "-f", str(icons_base)],
            capture_output=True, timeout=30,
        )

    def _aggiorna_done(self, changed: int, new_name: str, btn: Gtk.Button):
        btn.set_sensitive(True)
        if changed > 0:
            self.toast_overlay.add_toast(
                Adw.Toast(title=f"Aggiornati {changed} file a {new_name}"))
        else:
            self.toast_overlay.add_toast(
                Adw.Toast(title=f"Palette aggiornata a {new_name} (nessun file modificato)"))

    # ── PAGE 3: Components ───────────────────────────────────────────────

    def _build_components(self) -> Adw.NavigationPage:
        bp_page = Adw.BreakpointBin()
        bp_page.set_size_request(360, 400)

        # Primary switches (compact) + mirrors (expanded)
        self.switches = {}
        self._exp_switches: dict[int, Adw.ExpanderRow] = {}
        self._syncing = False
        self._count_pills: list[Gtk.Label] = []

        # Build groups data
        groups: dict[str, list[InstallerStep]] = {}
        for step in ALL_STEPS:
            meta = COMPONENT_META.get(step.number, ("", "", "Other"))
            group = meta[2]
            groups.setdefault(group, []).append(step)

        group_names = list(groups.keys())
        mid = (len(group_names) + 1) // 2

        # === Compact layout ===
        compact = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        toolbar_c = Adw.ToolbarView()
        hbar_c = self._make_components_header()
        toolbar_c.add_top_bar(hbar_c)

        scroll_c = Gtk.ScrolledWindow(vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER)
        clamp_c = Adw.Clamp(maximum_size=600, tightening_threshold=400)
        box_c = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        clamp_c.set_child(box_c)
        scroll_c.set_child(clamp_c)

        for group_name in group_names:
            steps = groups[group_name]
            expander = self._make_component_expander(group_name, steps, is_expanded_layout=False)
            expander.set_margin_start(16)
            expander.set_margin_end(16)
            expander.set_margin_top(4)
            box_c.append(expander)

        box_c.append(self._spacer(8))
        box_c.append(self._make_install_bottom())
        box_c.append(self._spacer(16))

        toolbar_c.set_content(scroll_c)
        compact.append(toolbar_c)

        # === Expanded layout ===
        expanded = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        toolbar_e = Adw.ToolbarView()
        hbar_e = self._make_components_header()
        toolbar_e.add_top_bar(hbar_e)

        scroll_e = Gtk.ScrolledWindow(vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER)
        two_col = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0,
                          vexpand=True, hexpand=True)

        left_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0,
                           hexpand=True, valign=Gtk.Align.START)
        left_col.add_css_class("expanded-pane")
        right_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0,
                            hexpand=True, valign=Gtk.Align.START)
        right_col.add_css_class("expanded-pane")

        for i, group_name in enumerate(group_names):
            steps = groups[group_name]
            expander = self._make_component_expander(group_name, steps, is_expanded_layout=True)
            expander.set_margin_top(4)
            if i < mid:
                expander.set_margin_end(8)
                left_col.append(expander)
            else:
                expander.set_margin_start(8)
                right_col.append(expander)

        two_col.append(left_col)
        two_col.append(right_col)
        scroll_e.set_child(two_col)

        bottom_e = self._make_install_bottom()
        bottom_e.set_margin_bottom(16)

        inner_e = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        inner_e.append(scroll_e)
        inner_e.append(bottom_e)

        toolbar_e.set_content(inner_e)
        expanded.append(toolbar_e)

        stack = Gtk.Stack()
        self._setup_breakpoint(bp_page, compact, expanded, stack)

        return Adw.NavigationPage(title="Components", tag="components", child=bp_page)

    def _make_components_header(self) -> Adw.HeaderBar:
        hbar = Adw.HeaderBar()
        hbar.add_css_class("header-surface")
        hbar.set_title_widget(Gtk.Label(label="Select Components", css_classes=["title-medium"]))

        all_btn = Gtk.Button(label="All")
        all_btn.add_css_class("text-button-primary")
        all_btn.add_css_class("flat")
        all_btn.connect("clicked", lambda b: self._toggle_all(True))

        none_btn = Gtk.Button(label="None")
        none_btn.add_css_class("flat")
        none_btn.connect("clicked", lambda b: self._toggle_all(False))

        hbar.pack_start(all_btn)
        hbar.pack_end(none_btn)
        return hbar

    def _make_component_expander(self, group_name: str, steps: list[InstallerStep],
                                  is_expanded_layout: bool = False) -> Adw.PreferencesGroup:
        group = Adw.PreferencesGroup(title=group_name)

        for step in steps:
            meta = COMPONENT_META.get(step.number, ("application-x-executable-symbolic", "", ""))
            icon_name, desc, _ = meta

            row = Adw.ExpanderRow(title=step.name, subtitle=desc)
            row.set_show_enable_switch(True)
            row.set_enable_expansion(self.selected.get(step.number, True))

            icon = Gtk.Image.new_from_icon_name(icon_name)
            icon.set_pixel_size(20)
            icon.add_css_class("color-primary")
            row.add_prefix(icon)

            if step.requires_sudo:
                badge = Gtk.Label(label="sudo")
                badge.add_css_class("chip-error")
                badge.set_valign(Gtk.Align.CENTER)
                row.add_suffix(badge)

            # Show checkmark if already installed
            if self.sys_info and step.is_installed(self.sys_info):
                check_icon = Gtk.Image.new_from_icon_name("emblem-ok-symbolic")
                check_icon.set_pixel_size(16)
                check_icon.add_css_class("color-success")
                check_icon.set_valign(Gtk.Align.CENTER)
                row.add_suffix(check_icon)

            # Detail sub-row inside expander
            comp_desc = COMPONENT_DESCRIPTIONS.get(step.number, "")
            detail = Adw.ActionRow(title=comp_desc)
            detail.set_title_lines(3)
            detail_icon = Gtk.Image.new_from_icon_name("dialog-information-symbolic")
            detail_icon.set_pixel_size(16)
            detail_icon.add_css_class("color-outline")
            detail.add_prefix(detail_icon)
            row.add_row(detail)

            row.connect("notify::enable-expansion", self._on_expander_toggled,
                        step.number, is_expanded_layout)

            if is_expanded_layout:
                self._exp_switches[step.number] = row
            else:
                self.switches[step.number] = row

            group.add(row)

        return group

    def _make_install_bottom(self) -> Gtk.Box:
        bottom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12,
                         halign=Gtk.Align.CENTER)
        bottom.set_margin_top(8)
        bottom.set_margin_bottom(24)

        pill = Gtk.Label()
        pill.add_css_class("counter-pill")
        self._count_pills.append(pill)
        self._update_count()
        bottom.append(pill)

        install_btn = Gtk.Button()
        install_btn.add_css_class("fab-extended")
        install_btn.set_size_request(180, -1)
        btn_content = Adw.ButtonContent(label="Install", icon_name="emblem-ok-symbolic")
        install_btn.set_child(btn_content)
        install_btn.connect("clicked", self._on_install)
        bottom.append(install_btn)

        return bottom

    def _on_expander_toggled(self, row, pspec, number, is_expanded_layout):
        if self._syncing:
            return
        self._syncing = True
        state = row.get_enable_expansion()
        self.selected[number] = state
        # Sync the other layout's row
        mirror = self._exp_switches if not is_expanded_layout else self.switches
        if number in mirror:
            mirror[number].set_enable_expansion(state)
        self._update_count()
        self._syncing = False

    def _toggle_all(self, state: bool):
        self._syncing = True
        for num, row in self.switches.items():
            row.set_enable_expansion(state)
            self.selected[num] = state
        for num, row in self._exp_switches.items():
            row.set_enable_expansion(state)
        self._syncing = False
        self._update_count()

    def _update_count(self):
        n = sum(1 for v in self.selected.values() if v)
        for pill in getattr(self, '_count_pills', []):
            pill.set_label(f"{n} of {len(ALL_STEPS)}")

    def _on_install(self, btn):
        steps = [s for s in ALL_STEPS if self.selected.get(s.number)]
        if not steps:
            self.toast_overlay.add_toast(Adw.Toast(title="Select at least one component"))
            return
        self.nav.push(self._build_progress(steps))
        threading.Thread(target=self._run_install, args=(steps,), daemon=True).start()

    # ── PAGE 4: Progress ─────────────────────────────────────────────────

    def _build_progress(self, steps: list[InstallerStep]) -> Adw.NavigationPage:
        self.progress_rows = {}

        bp_page = Adw.BreakpointBin()
        bp_page.set_size_request(360, 400)

        # Progress card (shared data — we create two instances)
        # We'll use instance variables that both layouts reference

        # === Compact layout ===
        compact = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        toolbar_c = Adw.ToolbarView()
        hbar_c = Adw.HeaderBar()
        hbar_c.add_css_class("header-surface")
        hbar_c.set_show_back_button(False)
        hbar_c.set_title_widget(Gtk.Label(label="Installing", css_classes=["title-medium"]))
        toolbar_c.add_top_bar(hbar_c)

        scroll_c = Gtk.ScrolledWindow(vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER)
        clamp_c = Adw.Clamp(maximum_size=600, tightening_threshold=400)
        box_c = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        clamp_c.set_child(box_c)
        scroll_c.set_child(clamp_c)
        toolbar_c.set_content(scroll_c)

        # Progress card
        card_c = self._make_progress_card(steps)
        card_c.set_margin_top(16)
        box_c.append(card_c)
        box_c.append(self._spacer(8))

        # Component rows
        group_c = self._make_progress_group(steps)
        box_c.append(group_c)
        box_c.append(self._spacer(24))

        compact.append(toolbar_c)

        # === Expanded layout ===
        expanded = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        toolbar_e = Adw.ToolbarView()
        hbar_e = Adw.HeaderBar()
        hbar_e.add_css_class("header-surface")
        hbar_e.set_show_back_button(False)
        hbar_e.set_title_widget(Gtk.Label(label="Installing", css_classes=["title-medium"]))
        toolbar_e.add_top_bar(hbar_e)

        two_col = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0,
                          vexpand=True, hexpand=True)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0,
                       hexpand=True, vexpand=True, valign=Gtk.Align.CENTER)
        left.add_css_class("expanded-pane")

        # Reuse same widgets — progress card and group are in compact.
        # For expanded, we just show a summary card.
        exp_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        exp_card.add_css_class("surface-container")
        exp_card_inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        exp_card_inner.set_margin_top(24)
        exp_card_inner.set_margin_bottom(24)
        exp_card_inner.set_margin_start(24)
        exp_card_inner.set_margin_end(24)

        self._exp_progress_icon = Gtk.Image.new_from_icon_name("emblem-system-symbolic")
        self._exp_progress_icon.set_pixel_size(48)
        self._exp_progress_icon.add_css_class("color-primary")
        self._exp_progress_icon.add_css_class("pulse")
        exp_card_inner.append(self._exp_progress_icon)

        self._exp_progress_title = Gtk.Label(label="Preparing...")
        self._exp_progress_title.add_css_class("headline-small")
        exp_card_inner.append(self._exp_progress_title)

        self._exp_progress_bar = Gtk.ProgressBar()
        self._exp_progress_bar.set_fraction(0)
        self._exp_progress_bar.set_margin_top(8)
        exp_card_inner.append(self._exp_progress_bar)

        self._exp_progress_count = Gtk.Label(label=f"0 / {len(steps)}")
        self._exp_progress_count.add_css_class("label-medium")
        exp_card_inner.append(self._exp_progress_count)

        exp_card.append(exp_card_inner)
        left.append(exp_card)
        two_col.append(left)

        right_scroll = Gtk.ScrolledWindow(vexpand=True, hexpand=True,
                                          hscrollbar_policy=Gtk.PolicyType.NEVER)
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0,
                        vexpand=True, valign=Gtk.Align.START)
        right.add_css_class("expanded-pane")

        group_e = self._make_progress_group_expanded(steps)
        right.append(group_e)
        right.append(self._spacer(24))
        right_scroll.set_child(right)
        two_col.append(right_scroll)

        toolbar_e.set_content(two_col)
        expanded.append(toolbar_e)

        stack = Gtk.Stack()
        self._setup_breakpoint(bp_page, compact, expanded, stack)

        self._total_steps = len(steps)
        return Adw.NavigationPage(title="Installing", tag="progress", child=bp_page)

    def _make_progress_card(self, steps: list[InstallerStep]) -> Gtk.Box:
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.add_css_class("info-card")

        self.progress_title = Gtk.Label(label="Preparing...")
        self.progress_title.add_css_class("title-medium")
        self.progress_title.set_halign(Gtk.Align.START)
        card.append(self.progress_title)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_fraction(0)
        self.progress_bar.set_margin_top(4)
        card.append(self.progress_bar)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.progress_count = Gtk.Label(label=f"0 / {len(steps)}")
        self.progress_count.add_css_class("label-medium")
        self.progress_count.set_halign(Gtk.Align.START)
        self.progress_count.set_hexpand(True)
        hbox.append(self.progress_count)

        self.progress_pct = Gtk.Label(label="0%")
        self.progress_pct.add_css_class("label-large")
        hbox.append(self.progress_pct)

        card.append(hbox)
        return card

    def _make_progress_group(self, steps: list[InstallerStep]) -> Adw.PreferencesGroup:
        group = Adw.PreferencesGroup(title="Components")
        group.set_margin_start(16)
        group.set_margin_end(16)

        for step in steps:
            meta = COMPONENT_META.get(step.number, ("application-x-executable-symbolic", "", ""))
            icon_name = meta[0]

            row = Adw.ActionRow(title=step.name, subtitle="Waiting")
            prefix_icon = Gtk.Image.new_from_icon_name(icon_name)
            prefix_icon.set_pixel_size(20)
            prefix_icon.add_css_class("color-outline")
            row.add_prefix(prefix_icon)

            status_icon = Gtk.Image.new_from_icon_name("content-loading-symbolic")
            status_icon.set_pixel_size(16)
            status_icon.add_css_class("color-outline")
            row.add_suffix(status_icon)

            self.progress_rows[step.number] = {
                "row": row,
                "prefix": prefix_icon,
                "suffix": status_icon,
                "exp_rows": [],  # will be populated by expanded group
            }
            group.add(row)

        return group

    def _make_progress_group_expanded(self, steps: list[InstallerStep]) -> Adw.PreferencesGroup:
        group = Adw.PreferencesGroup(title="Components")

        for step in steps:
            meta = COMPONENT_META.get(step.number, ("application-x-executable-symbolic", "", ""))
            icon_name = meta[0]

            row = Adw.ActionRow(title=step.name, subtitle="Waiting")
            prefix_icon = Gtk.Image.new_from_icon_name(icon_name)
            prefix_icon.set_pixel_size(20)
            prefix_icon.add_css_class("color-outline")
            row.add_prefix(prefix_icon)

            status_icon = Gtk.Image.new_from_icon_name("content-loading-symbolic")
            status_icon.set_pixel_size(16)
            status_icon.add_css_class("color-outline")
            row.add_suffix(status_icon)

            if step.number in self.progress_rows:
                self.progress_rows[step.number]["exp_rows"].append({
                    "row": row, "prefix": prefix_icon, "suffix": status_icon,
                })

            group.add(row)

        return group

    def _run_install(self, steps: list[InstallerStep]):
        backup = BackupManager(dry_run=False)
        backup.init()
        self.results = []

        for i, step in enumerate(steps):
            GLib.idle_add(self._mark_running, step, i, len(steps))
            try:
                result = step.install(self.sys_info, backup, dry_run=False)
            except Exception as e:
                result = ComponentResult(step.number, step.name, Status.FAILED, str(e))
            self.results.append(result)
            GLib.idle_add(self._mark_done, step, result, i + 1, len(steps))
            time.sleep(0.1)

        backup.save_manifest()
        self.backup_dir = backup.backup_dir
        # Save the installed palette name for future recolor operations
        save_installed_palette(self._get_app().current_palette_name)
        GLib.idle_add(self._goto_results)

    def _mark_running(self, step, idx, total):
        self.progress_title.set_label(step.name)
        if hasattr(self, '_exp_progress_title'):
            self._exp_progress_title.set_label(step.name)

        if step.number in self.progress_rows:
            rd = self.progress_rows[step.number]
            for d in [rd] + rd.get("exp_rows", []):
                d["row"].set_subtitle("Installing...")
                d["prefix"].remove_css_class("color-outline")
                d["prefix"].add_css_class("color-primary")
                d["suffix"].set_from_icon_name("content-loading-symbolic")
                d["suffix"].remove_css_class("color-outline")
                d["suffix"].add_css_class("color-primary")
                d["suffix"].add_css_class("pulse")

    def _mark_done(self, step, result: ComponentResult, done, total):
        frac = done / total
        self.progress_bar.set_fraction(frac)
        self.progress_count.set_label(f"{done} / {total}")
        self.progress_pct.set_label(f"{int(frac * 100)}%")

        if hasattr(self, '_exp_progress_bar'):
            self._exp_progress_bar.set_fraction(frac)
            self._exp_progress_count.set_label(f"{done} / {total}")

        if step.number in self.progress_rows:
            rd = self.progress_rows[step.number]
            for d in [rd] + rd.get("exp_rows", []):
                d["suffix"].remove_css_class("pulse")
                d["suffix"].remove_css_class("color-primary")
                d["suffix"].remove_css_class("color-outline")
                d["prefix"].remove_css_class("color-outline")

                if result.status == Status.SUCCESS:
                    d["row"].set_subtitle(result.message)
                    d["suffix"].set_from_icon_name("emblem-ok-symbolic")
                    d["suffix"].add_css_class("color-success")
                    d["prefix"].add_css_class("color-success")
                elif result.status == Status.SKIPPED:
                    d["row"].set_subtitle(result.message)
                    d["suffix"].set_from_icon_name("process-stop-symbolic")
                    d["suffix"].add_css_class("color-warning")
                    d["prefix"].add_css_class("color-warning")
                else:
                    d["row"].set_subtitle(result.message)
                    d["suffix"].set_from_icon_name("dialog-error-symbolic")
                    d["suffix"].add_css_class("color-error")
                    d["prefix"].add_css_class("color-error")

        if done == total:
            self.progress_title.set_label("Complete")
            if hasattr(self, '_exp_progress_title'):
                self._exp_progress_title.set_label("Complete")
                self._exp_progress_icon.remove_css_class("pulse")
                self._exp_progress_icon.set_from_icon_name("emblem-ok-symbolic")
                self._exp_progress_icon.add_css_class("color-success")

    def _goto_results(self):
        self.nav.push(self._build_results())

    # ── PAGE 5: Results ──────────────────────────────────────────────────

    def _build_results(self) -> Adw.NavigationPage:
        bp_page = Adw.BreakpointBin()
        bp_page.set_size_request(360, 400)

        ok = sum(1 for r in self.results if r.status == Status.SUCCESS)
        skip = sum(1 for r in self.results if r.status == Status.SKIPPED)
        fail = sum(1 for r in self.results if r.status == Status.FAILED)

        # === Compact layout ===
        compact = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        toolbar_c = Adw.ToolbarView()
        hbar_c = Adw.HeaderBar()
        hbar_c.add_css_class("header-surface")
        hbar_c.set_show_back_button(False)
        hbar_c.set_title_widget(Gtk.Label(label="Complete", css_classes=["title-medium"]))
        toolbar_c.add_top_bar(hbar_c)

        scroll_c = Gtk.ScrolledWindow(vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER)
        clamp_c = Adw.Clamp(maximum_size=600, tightening_threshold=400)
        box_c = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        clamp_c.set_child(box_c)
        scroll_c.set_child(clamp_c)
        toolbar_c.set_content(scroll_c)

        box_c.append(self._spacer(32))
        box_c.append(self._make_result_summary(ok, skip, fail))
        box_c.append(self._spacer(20))

        details_c = self._make_result_details()
        details_c.set_margin_start(16)
        details_c.set_margin_end(16)
        box_c.append(details_c)

        box_c.append(self._spacer(8))
        box_c.append(self._make_result_notes())
        box_c.append(self._spacer(24))
        box_c.append(self._make_result_buttons())
        box_c.append(self._spacer(32))

        compact.append(toolbar_c)

        # === Expanded layout ===
        expanded = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        toolbar_e = Adw.ToolbarView()
        hbar_e = Adw.HeaderBar()
        hbar_e.add_css_class("header-surface")
        hbar_e.set_show_back_button(False)
        hbar_e.set_title_widget(Gtk.Label(label="Complete", css_classes=["title-medium"]))
        toolbar_e.add_top_bar(hbar_e)

        two_col = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0,
                          vexpand=True, hexpand=True)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0,
                       hexpand=True, vexpand=True, valign=Gtk.Align.CENTER,
                       halign=Gtk.Align.CENTER)
        left.add_css_class("expanded-pane")
        left.append(self._make_result_summary(ok, skip, fail))
        left.append(self._spacer(24))
        left.append(self._make_result_buttons())

        two_col.append(left)

        right_scroll = Gtk.ScrolledWindow(vexpand=True, hexpand=True,
                                          hscrollbar_policy=Gtk.PolicyType.NEVER)
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0,
                        vexpand=True, valign=Gtk.Align.START)
        right.add_css_class("expanded-pane")

        details_e = self._make_result_details()
        right.append(details_e)
        right.append(self._spacer(8))
        right.append(self._make_result_notes())
        right.append(self._spacer(24))

        right_scroll.set_child(right)
        two_col.append(right_scroll)

        toolbar_e.set_content(two_col)
        expanded.append(toolbar_e)

        stack = Gtk.Stack()
        self._setup_breakpoint(bp_page, compact, expanded, stack)

        return Adw.NavigationPage(title="Results", tag="results", child=bp_page)

    def _make_result_summary(self, ok: int, skip: int, fail: int) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0,
                      halign=Gtk.Align.CENTER)

        icon_box = Gtk.Box(halign=Gtk.Align.CENTER)
        if fail == 0:
            status_icon = Gtk.Image.new_from_icon_name("emblem-ok-symbolic")
            status_icon.set_pixel_size(72)
            status_icon.add_css_class("color-success")
            icon_box.append(status_icon)
            box.append(icon_box)

            box.append(self._spacer(16))
            t = Gtk.Label(label="All Done", halign=Gtk.Align.CENTER)
            t.add_css_class("headline-small")
            box.append(t)

            s = Gtk.Label(label=f"{ok} installed, {skip} skipped", halign=Gtk.Align.CENTER)
            s.add_css_class("body-medium")
            s.set_margin_top(4)
            box.append(s)
        else:
            status_icon = Gtk.Image.new_from_icon_name("dialog-warning-symbolic")
            status_icon.set_pixel_size(72)
            status_icon.add_css_class("color-warning")
            icon_box.append(status_icon)
            box.append(icon_box)

            box.append(self._spacer(16))
            t = Gtk.Label(label="Completed with Issues", halign=Gtk.Align.CENTER)
            t.add_css_class("headline-small")
            box.append(t)

            s = Gtk.Label(label=f"{ok} ok, {skip} skipped, {fail} failed",
                         halign=Gtk.Align.CENTER)
            s.add_css_class("body-medium")
            s.set_margin_top(4)
            box.append(s)

        # Color name badge
        palette_name = self._get_app().current_palette_name
        badge = Gtk.Label(label=f"{palette_name} theme")
        badge.add_css_class("chip-filled")
        badge.set_halign(Gtk.Align.CENTER)
        badge.set_margin_top(12)
        box.append(badge)

        return box

    def _make_result_details(self) -> Adw.PreferencesGroup:
        group = Adw.PreferencesGroup(title="Details")

        for r in self.results:
            meta = COMPONENT_META.get(r.number, ("application-x-executable-symbolic", "", ""))
            icon_name = meta[0]

            row = Adw.ActionRow(title=r.name, subtitle=r.message)
            row.set_activatable(True)
            row.add_css_class("clickable-row")
            row.connect("activated", self._on_result_row_clicked, r)

            prefix = Gtk.Image.new_from_icon_name(icon_name)
            prefix.set_pixel_size(20)
            row.add_prefix(prefix)

            if r.status == Status.SUCCESS:
                suffix = Gtk.Image.new_from_icon_name("emblem-ok-symbolic")
                suffix.add_css_class("color-success")
                prefix.add_css_class("color-success")
            elif r.status == Status.SKIPPED:
                suffix = Gtk.Image.new_from_icon_name("process-stop-symbolic")
                suffix.add_css_class("color-warning")
                prefix.add_css_class("color-warning")
            else:
                suffix = Gtk.Image.new_from_icon_name("dialog-error-symbolic")
                suffix.add_css_class("color-error")
                prefix.add_css_class("color-error")

            suffix.set_pixel_size(16)
            row.add_suffix(suffix)

            # Copy icon hint
            copy_icon = Gtk.Image.new_from_icon_name("edit-copy-symbolic")
            copy_icon.set_pixel_size(14)
            copy_icon.add_css_class("color-outline")
            row.add_suffix(copy_icon)

            group.add(row)

        return group

    def _on_result_row_clicked(self, row, result: ComponentResult):
        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.set(result.message)
        self.toast_overlay.add_toast(Adw.Toast(title=f"Copied: {result.message}"))

    def _make_result_notes(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

        note = Adw.ActionRow(title="Log out and back in for full effect")
        note.add_css_class("note-banner")
        note_icon = Gtk.Image.new_from_icon_name("dialog-information-symbolic")
        note_icon.set_pixel_size(20)
        note_icon.add_css_class("color-primary")
        note.add_prefix(note_icon)
        note.set_margin_start(16)
        note.set_margin_end(16)
        box.append(note)

        if hasattr(self, 'backup_dir'):
            brow = Adw.ActionRow(title="Backup saved", subtitle=str(self.backup_dir))
            brow.set_subtitle_selectable(True)
            brow.set_margin_start(16)
            brow.set_margin_end(16)
            b_icon = Gtk.Image.new_from_icon_name("document-save-symbolic")
            b_icon.set_pixel_size(20)
            b_icon.add_css_class("color-primary")
            brow.add_prefix(b_icon)
            brow.add_css_class("note-banner")
            box.append(brow)

        return box

    def _make_result_buttons(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12,
                      halign=Gtk.Align.CENTER)

        logout_btn = Gtk.Button()
        logout_btn.add_css_class("tonal-button")
        logout_content = Adw.ButtonContent(label="Log Out", icon_name="system-log-out-symbolic")
        logout_btn.set_child(logout_content)
        logout_btn.connect("clicked", self._on_logout)
        box.append(logout_btn)

        done = Gtk.Button(label="Done")
        done.add_css_class("fab-extended")
        done.set_size_request(140, -1)
        done.connect("clicked", lambda b: self.close())
        box.append(done)

        return box

    def _on_logout(self, btn):
        try:
            subprocess.Popen(["gnome-session-quit", "--logout", "--no-prompt"])
        except FileNotFoundError:
            self.toast_overlay.add_toast(Adw.Toast(title="Could not find gnome-session-quit"))

    # ── Bottom Navigation Bar ─────────────────────────────────────────────

    def _build_bottom_nav(self) -> Gtk.Box:
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0,
                      valign=Gtk.Align.CENTER)
        bar.add_css_class("bottom-nav-bar")
        bar.set_hexpand(True)

        self._nav_items: list[dict] = []
        items = [
            ("go-home-symbolic", "Home", "welcome"),
            ("color-select-symbolic", "Color", "color"),
            ("view-list-symbolic", "Components", "components"),
        ]

        for i, (icon_name, label_text, tag) in enumerate(items):
            btn = Gtk.Button()
            btn.add_css_class("flat")
            btn.add_css_class("nav-item")
            btn.set_hexpand(True)
            btn.set_valign(Gtk.Align.CENTER)

            inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0,
                            halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER)

            pill = Gtk.Box(halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER)
            pill.add_css_class("nav-pill-bg")

            icon = Gtk.Image.new_from_icon_name(icon_name)
            icon.set_pixel_size(22)
            icon.add_css_class("nav-icon")
            pill.append(icon)

            inner.append(pill)

            lbl = Gtk.Label(label=label_text)
            lbl.add_css_class("nav-label")
            inner.append(lbl)

            btn.set_child(inner)
            btn.connect("clicked", self._on_nav_clicked, i)
            bar.append(btn)

            self._nav_items.append({
                "pill": pill, "icon": icon, "label": lbl, "tag": tag,
            })

        return bar

    def _on_nav_clicked(self, btn, index):
        # Skip if already on this page
        page = self.nav.get_visible_page()
        if page:
            tag_map = {0: "welcome", 1: "color", 2: "components"}
            if (page.get_tag() or "") == tag_map.get(index):
                return
        pages = []
        if index >= 0:
            pages.append(self._build_welcome())
        if index >= 1:
            pages.append(self._build_color_picker())
        if index >= 2:
            pages.append(self._build_components())
        if pages:
            self.nav.replace(pages)

    def _on_window_expand(self, bp):
        self._is_expanded = True
        self.bottom_nav.set_visible(False)

    def _on_window_compact(self, bp):
        self._is_expanded = False
        page = self.nav.get_visible_page()
        if page:
            tag = page.get_tag() or ""
            if tag in ("welcome", "color", "components"):
                self.bottom_nav.set_visible(True)

    def _on_visible_page_changed(self, nav_view, pspec):
        page = nav_view.get_visible_page()
        if page is None:
            return
        tag = page.get_tag() or ""
        tag_to_index = {"welcome": 0, "color": 1, "components": 2}

        if tag not in tag_to_index or self._is_expanded:
            self.bottom_nav.set_visible(False)
            return

        self.bottom_nav.set_visible(True)
        self._update_bottom_nav(tag_to_index[tag])

    def _update_bottom_nav(self, active_index: int):
        for i, item in enumerate(self._nav_items):
            if i == active_index:
                item["pill"].add_css_class("nav-pill-active")
                item["icon"].add_css_class("nav-icon-active")
                item["label"].add_css_class("nav-label-active")
            else:
                item["pill"].remove_css_class("nav-pill-active")
                item["icon"].remove_css_class("nav-icon-active")
                item["label"].remove_css_class("nav-label-active")

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _setup_breakpoint(bp_page, compact, expanded, stack):
        """Wire up a 700px breakpoint that toggles compact/expanded visibility."""
        expanded.set_visible(False)
        stack.add_named(compact, "compact")
        stack.add_named(expanded, "expanded")
        stack.set_visible_child_name("compact")
        bp_page.set_child(stack)

        bp = Adw.Breakpoint()
        bp.set_condition(Adw.BreakpointCondition.parse("min-width: 700px"))

        def _apply(b):
            expanded.set_visible(True)
            stack.set_visible_child_name("expanded")
            compact.set_visible(False)

        def _unapply(b):
            compact.set_visible(True)
            stack.set_visible_child_name("compact")
            expanded.set_visible(False)

        bp.connect("apply", _apply)
        bp.connect("unapply", _unapply)
        bp_page.add_breakpoint(bp)

    @staticmethod
    def _spacer(h: int) -> Gtk.Box:
        s = Gtk.Box()
        s.set_size_request(-1, h)
        return s


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    app = MaterialYouApp()
    app.run(sys.argv)

if __name__ == "__main__":
    main()
