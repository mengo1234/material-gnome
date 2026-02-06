<p align="center">
  <img src="screenshots/banner.svg" width="900" alt="Material Gnome">
</p>

<p align="center">
  <a href="#quick-start"><img src="https://img.shields.io/badge/-Download-ffb86c?style=for-the-badge&logoColor=1a1110" alt="Download"></a>&nbsp;
  <img src="https://img.shields.io/badge/GNOME-45%2B-4a86cf?style=for-the-badge&logo=gnome&logoColor=white" alt="GNOME 45+">&nbsp;
  <img src="https://img.shields.io/badge/GTK4-libadwaita-ffb86c?style=for-the-badge" alt="GTK4">&nbsp;
  <img src="https://img.shields.io/badge/License-MIT-9e8e86?style=for-the-badge" alt="MIT">
</p>

---

<br>

### Your desktop deserves better than default Adwaita.

Material Gnome is a full-system Material You dark theme for GNOME. It replaces the look of every surface you interact with daily -- the top bar, the app grid, Nautilus, Settings, Firefox, your terminal, even the boot screen -- with a cohesive, warm, Material Design 3 aesthetic.

The project ships as a **native GTK4 / libadwaita installer** with an adaptive layout that feels at home on both a laptop and a widescreen monitor. Pick one of **8 accent colors**, toggle the **19 components** you want, hit install, and walk away. Everything is backed up automatically. Nothing is irreversible.

Need to change your mind later? Open the installer, pick a new color, press **Aggiorna**, and watch your entire desktop -- CSS files, Papirus folder icons, terminal palette, GNOME accent color, running GTK apps -- shift hue in real time. No logout. No restart.

Built and tested on **Bazzite / Fedora Silverblue** (GNOME 49.1, Wayland, immutable root), but works on any distribution running GNOME 45 or later.

<br>

<p align="center">
  <img src="screenshots/features.svg" width="900" alt="Feature highlights">
</p>

<br>

---

<br>

<p align="center">
  <img src="screenshots/welcome-expanded.png" width="780" alt="Material Gnome — Home">
</p>

<p align="center">
  <sub>Home screen -- system detection, feature overview, and the hero card. Adaptive two-column layout.</sub>
</p>

<br>

<p align="center">
  <img src="screenshots/colors.png" width="780" alt="Material Gnome — Color Picker">
</p>

<p align="center">
  <sub>Color picker -- 8 Material You palettes with live preview of primary, container, and surface tokens.</sub>
</p>

<br>

<p align="center">
  <img src="screenshots/welcome.png" width="300" alt="Material Gnome — Compact">
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="screenshots/components.png" width="300" alt="Material Gnome — Components">
</p>

<p align="center">
  <sub>Compact layout with bottom navigation and component selection with per-step install detection.</sub>
</p>

<br>

---

<br>

## What gets installed

| | Component | What it does |
|:---:|---|---|
| <img src="https://img.shields.io/badge/%20-5c3a1a?style=flat-square" width="8"> | **GNOME Shell** | Top bar, quick settings, notifications, OSD, overview, calendar, lock screen |
| <img src="https://img.shields.io/badge/%20-5c3a1a?style=flat-square" width="8"> | **GTK4 / libadwaita** | Nautilus, Settings, Text Editor, and every modern GNOME app |
| <img src="https://img.shields.io/badge/%20-5c3a1a?style=flat-square" width="8"> | **GTK3** | Legacy application styling |
| <img src="https://img.shields.io/badge/%20-5c3a1a?style=flat-square" width="8"> | **Ptyxis Terminal** | Palette with matched background, cursor, selection, and ANSI colors |
| <img src="https://img.shields.io/badge/%20-5c3a1a?style=flat-square" width="8"> | **Fastfetch** | Styled terminal system info display |
| <img src="https://img.shields.io/badge/%20-5c3a1a?style=flat-square" width="8"> | **Burn My Windows** | Window close animation profile |
| <img src="https://img.shields.io/badge/%20-5c3a1a?style=flat-square" width="8"> | **Wallpaper** | Dark lockscreen wallpaper |
| <img src="https://img.shields.io/badge/%20-5c3a1a?style=flat-square" width="8"> | **Fonts** | Inter, Fira Code, Noto Serif |
| <img src="https://img.shields.io/badge/%20-5c3a1a?style=flat-square" width="8"> | **Papirus Icons** | Papirus-Dark with accent-colored folders |
| <img src="https://img.shields.io/badge/%20-5c3a1a?style=flat-square" width="8"> | **Bibata Cursors** | Bibata Modern Classic cursor theme |
| <img src="https://img.shields.io/badge/%20-5c3a1a?style=flat-square" width="8"> | **12 Extensions** | Logo Menu, Blur, AppIndicator, Tiling, Compiz effects, and more |
| <img src="https://img.shields.io/badge/%20-5c3a1a?style=flat-square" width="8"> | **57 dconf Settings** | Accent color, Flatpak overrides, night light, keybindings |
| <img src="https://img.shields.io/badge/%20-5c3a1a?style=flat-square" width="8"> | **Flatpak Overrides** | Global GTK theme override for sandboxed apps |
| <img src="https://img.shields.io/badge/%20-5c3a1a?style=flat-square" width="8"> | **Flatpak Symlinks** | Per-app CSS symlinks for theme consistency |
| <img src="https://img.shields.io/badge/%20-5c3a1a?style=flat-square" width="8"> | **Firefox** | Custom `userChrome.css` and `userContent.css` |
| <img src="https://img.shields.io/badge/%20-5c3a1a?style=flat-square" width="8"> | **GDM** | Login screen with matching colors and font |
| <img src="https://img.shields.io/badge/%20-5c3a1a?style=flat-square" width="8"> | **DING** | Desktop icons priority fix |
| <img src="https://img.shields.io/badge/%20-5c3a1a?style=flat-square" width="8"> | **rEFInd** | Boot manager theme |
| <img src="https://img.shields.io/badge/%20-5c3a1a?style=flat-square" width="8"> | **rEFInd Theme** | Background, selection icons, and OS logos for the boot screen |

<br>

## Accent colors

Pick once, change anytime. The **Aggiorna** engine uses HSL hue-shifting to remap every color in every CSS file -- not just the 24 palette tokens, but all derived and intermediate shades. Papirus folder symlinks, dconf accent keys, and terminal palettes are updated in the same pass.

<p align="center">
<img src="https://img.shields.io/badge/%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B-ffb86c?style=flat-square&logoColor=white" height="32" alt="Orange">&nbsp;
<img src="https://img.shields.io/badge/%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B-82b1ff?style=flat-square" height="32" alt="Blue">&nbsp;
<img src="https://img.shields.io/badge/%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B-a8c77a?style=flat-square" height="32" alt="Green">&nbsp;
<img src="https://img.shields.io/badge/%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B-ce93d8?style=flat-square" height="32" alt="Purple">&nbsp;
<img src="https://img.shields.io/badge/%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B-ef9a9a?style=flat-square" height="32" alt="Red">&nbsp;
<img src="https://img.shields.io/badge/%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B-80cbc4?style=flat-square" height="32" alt="Teal">&nbsp;
<img src="https://img.shields.io/badge/%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B-f48fb1?style=flat-square" height="32" alt="Pink">&nbsp;
<img src="https://img.shields.io/badge/%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B-fff176?style=flat-square" height="32" alt="Yellow">
</p>

<p align="center">
  <sub>Orange &nbsp;&middot;&nbsp; Blue &nbsp;&middot;&nbsp; Green &nbsp;&middot;&nbsp; Purple &nbsp;&middot;&nbsp; Red &nbsp;&middot;&nbsp; Teal &nbsp;&middot;&nbsp; Pink &nbsp;&middot;&nbsp; Yellow</sub>
</p>

<br>

---

<br>

## Quick start

```bash
git clone https://github.com/mengo1234/material-gnome.git
cd material-gnome
python3 material-you-installer-gui.py
```

Or run the TUI installer in any terminal:

```bash
python3 material_you_installer.py
```

<br>

## Requirements

| | |
|---|---|
| **Desktop** | GNOME 45+ (tested on 49.1) |
| **Python** | 3.10+ |
| **GUI deps** | `gtk4`, `libadwaita` |
| **Elevated** | `sudo` for GDM, rEFInd, Plymouth, DING |

<br>

## How it works

```
theme/
  gnome-shell/   ->  ~/.themes/Material-You-Orange/gnome-shell/
  gtk-4.0/       ->  ~/.config/gtk-4.0/
  gtk-3.0/       ->  ~/.config/gtk-3.0/
  firefox/       ->  ~/.mozilla/firefox/<profile>/chrome/
  ptyxis/        ->  ~/.local/share/org.gnome.Ptyxis/palettes/
  fastfetch/     ->  ~/.config/fastfetch/
  wallpaper/     ->  lockscreen background
  gdm/           ->  /etc/dconf/db/gdm.d/
  refind/        ->  /boot/efi/EFI/refind/
```

Already-installed components show a checkmark. Every step creates a timestamped backup before touching anything. On immutable distros (Bazzite, Silverblue, Kinoite) the installer uses `/etc` overlays automatically.

<br>

## Uninstall

```bash
python3 material_you_installer.py
# Select "Restore" to roll back individual components or everything at once
```

Backups live in `~/.local/share/material-you-orange/backups/`.

<br>

## Project structure

```
material-you-installer-gui.py    GTK4 / libadwaita GUI application
material_you_installer.py        TUI installer and core step engine
material-you-installer.py        Legacy TUI entry point
theme/                           Pre-built CSS, configs, and assets
screenshots/                     App screenshots and visual assets
```

<br>

---

<p align="center">
  <sub>MIT License</sub>
</p>
