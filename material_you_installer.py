#!/usr/bin/env python3
"""
Material You Orange Dark Theme Installer
=========================================
TUI installer for GNOME 49+ that replicates the complete Material You Orange
dark theme setup across compatible Linux distributions.

Supports: Bazzite, Fedora Silverblue, Fedora, Ubuntu, Arch
Requires: Python 3.10+, rich (pre-installed on Fedora/Bazzite)
"""

import argparse
import datetime
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import urllib.request
import zipfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn, TaskProgressColumn
    from rich.table import Table
    from rich.text import Text
    from rich.prompt import Confirm, Prompt
    from rich.theme import Theme
    from rich import box
except ImportError:
    print("\n[ERROR] 'rich' library is required but not installed.")
    print("Install it with:  pip install rich")
    print("Or on Fedora:     sudo dnf install python3-rich")
    sys.exit(1)

# ─── Constants ───────────────────────────────────────────────────────────────

VERSION = "1.0.0"
SCRIPT_DIR = Path(__file__).resolve().parent
THEME_DIR = SCRIPT_DIR / "theme"
BACKUP_BASE = Path.home() / ".local" / "share" / "material-you-orange" / "backups"

# Color palette
COLORS = {
    "primary": "#ffb86c",
    "on_primary": "#1a1110",
    "surface": "#1a1110",
    "surface_container": "#1e1514",
    "surface_container_high": "#2d2220",
    "surface_container_highest": "#3d312e",
    "on_surface": "#efe0db",
    "on_surface_variant": "#d5c4bc",
    "outline": "#9e8e86",
    "outline_variant": "#51443e",
    "error": "#ffb4ab",
    "secondary": "#e4bfa8",
}

RICH_THEME = Theme({
    "info": "bold #ffb86c",
    "success": "bold #a8c77a",
    "warning": "bold #ffc888",
    "error": "bold #ffb4ab",
    "muted": "#9e8e86",
    "accent": "#ffb86c",
})

console = Console(theme=RICH_THEME)

# GNOME Extensions to install
EXTENSIONS = [
    ("logomenu@aryan_k", "Logo Menu"),
    ("appindicatorsupport@rgcjonas.gmail.com", "AppIndicator Support"),
    ("user-theme@gnome-shell-extensions.gcampax.github.com", "User Themes"),
    ("gsconnect@andyholmes.github.io", "GSConnect"),
    ("blur-my-shell@aunetx", "Blur My Shell"),
    ("hotedge@jonathan.jdoda.ca", "Hot Edge"),
    ("caffeine@patapon.info", "Caffeine"),
    ("add-to-steam@pupper.space", "Add to Steam"),
    ("restartto@tiagoporsch.github.io", "Restart To"),
    ("block-caribou-36@lxylxy123456.ercli.dev", "Block Caribou"),
    ("compiz-alike-magic-lamp-effect@hermes83.github.com", "Magic Lamp Effect"),
    ("burn-my-windows@schneegans.github.com", "Burn My Windows"),
]

# Font download URLs
FONT_URLS = {
    "Inter": "https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip",
    "FiraCode": "https://github.com/tonsky/FiraCode/releases/download/6.2/Fira_Code_v6.2.zip",
    "NotoSerif": "https://github.com/notofonts/notofonts.github.io/raw/main/fonts/NotoSerif/googlefonts/variable-ttf/NotoSerif%5Bwdth%2Cwght%5D.ttf",
}

# Papirus icon theme
PAPIRUS_URL = "https://github.com/PapirusDevelopmentTeam/papirus-icon-theme/archive/refs/heads/master.zip"

# Bibata cursor
BIBATA_URL = "https://github.com/ful1e5/Bibata_Cursor/releases/download/v2.0.7/Bibata-Modern-Classic.tar.xz"


# ─── Enums ───────────────────────────────────────────────────────────────────

class Status(Enum):
    SUCCESS = "success"
    SKIPPED = "skipped"
    FAILED = "failed"
    PENDING = "pending"


class Distro(Enum):
    BAZZITE = "bazzite"
    SILVERBLUE = "silverblue"
    FEDORA = "fedora"
    UBUNTU = "ubuntu"
    ARCH = "arch"
    UNKNOWN = "unknown"


class PkgManager(Enum):
    DNF = "dnf"
    APT = "apt"
    PACMAN = "pacman"
    RPM_OSTREE = "rpm-ostree"
    NONE = "none"


# ─── Data Classes ────────────────────────────────────────────────────────────

@dataclass
class SystemInfo:
    distro: Distro = Distro.UNKNOWN
    distro_name: str = ""
    gnome_version: str = ""
    pkg_manager: PkgManager = PkgManager.NONE
    is_immutable: bool = False
    is_wayland: bool = False
    home: Path = field(default_factory=Path.home)
    has_flatpak: bool = False


@dataclass
class ComponentResult:
    number: int
    name: str
    status: Status = Status.PENDING
    message: str = ""


# ─── Utility Functions ───────────────────────────────────────────────────────

def run(cmd: list[str] | str, check: bool = False, capture: bool = True,
        shell: bool = False, timeout: int = 120, **kwargs) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    if isinstance(cmd, str):
        shell = True
    return subprocess.run(
        cmd, capture_output=capture, text=True, shell=shell,
        check=check, timeout=timeout, **kwargs
    )


def run_ok(cmd: list[str] | str, **kwargs) -> bool:
    """Run a command and return True if it succeeded."""
    try:
        r = run(cmd, **kwargs)
        return r.returncode == 0
    except (subprocess.SubprocessError, OSError):
        return False


def run_output(cmd: list[str] | str, **kwargs) -> str:
    """Run a command and return its stdout, stripped."""
    try:
        r = run(cmd, **kwargs)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (subprocess.SubprocessError, OSError):
        return ""


def ensure_dir(path: Path) -> None:
    """Create directory and parents if they don't exist."""
    path.mkdir(parents=True, exist_ok=True)


def copy_file(src: Path, dst: Path) -> None:
    """Copy a file, creating parent directories as needed."""
    ensure_dir(dst.parent)
    shutil.copy2(src, dst)


def download_file(url: str, dest: Path, desc: str = "") -> bool:
    """Download a file from URL to dest path."""
    try:
        ensure_dir(dest.parent)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as f:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            block = 8192
            while True:
                chunk = resp.read(block)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
        return True
    except Exception as e:
        console.print(f"  [error]Download failed: {e}[/]")
        return False


def dconf_read(key: str) -> str:
    """Read a single dconf value."""
    return run_output(["dconf", "read", key])


def dconf_write(key: str, value: str) -> bool:
    """Write a single dconf value."""
    return run_ok(["dconf", "write", key, value])


def dconf_dump(path: str) -> str:
    """Dump dconf at a given path."""
    return run_output(["dconf", "dump", path])


def dconf_load(path: str, data: str) -> bool:
    """Load dconf data at a given path."""
    try:
        r = subprocess.run(
            ["dconf", "load", path], input=data, text=True,
            capture_output=True, timeout=30
        )
        return r.returncode == 0
    except (subprocess.SubprocessError, OSError):
        return False


# ─── Banner ──────────────────────────────────────────────────────────────────

BANNER_TEXT = r"""
 __  __       _            _       _  __   __
|  \/  | __ _| |_ ___ _ __(_) __ _| | \ \ / /__  _   _
| |\/| |/ _` | __/ _ \ '__| |/ _` | |  \ V / _ \| | | |
| |  | | (_| | ||  __/ |  | | (_| | |   | | (_) | |_| |
|_|  |_|\__,_|\__\___|_|  |_|\__,_|_|   |_|\___/ \__,_|
  ___                              ____             _
 / _ \ _ __ __ _ _ __   __ _  ___|  _ \  __ _ _ __| | __
| | | | '__/ _` | '_ \ / _` |/ _ \ | | |/ _` | '__| |/ /
| |_| | | | (_| | | | | (_| |  __/ |_| | (_| | |  |   <
 \___/|_|  \__,_|_| |_|\__, |\___|____/ \__,_|_|  |_|\_\
                        |___/
"""


def print_banner() -> None:
    """Print ASCII art banner with orange gradient."""
    lines = BANNER_TEXT.strip().split("\n")
    # Gradient from #ffb86c (warm orange) to #e65100 (deep orange)
    gradient = [
        "#ffb86c", "#ffad5e", "#ffa250", "#ff9742", "#ff8c34",
        "#ff8126", "#ff7618", "#ff6b0a", "#f06000", "#e65100",
    ]
    text = Text()
    for i, line in enumerate(lines):
        color = gradient[i % len(gradient)]
        text.append(line + "\n", style=color)
    console.print(text)
    console.print(
        f"  [muted]v{VERSION} — Material You Orange Dark Theme Installer[/]\n"
    )


# ─── SystemDetector ──────────────────────────────────────────────────────────

class SystemDetector:
    """Detects system configuration for multi-distro support."""

    def detect(self) -> SystemInfo:
        info = SystemInfo()
        info.home = Path.home()
        self._detect_distro(info)
        self._detect_gnome(info)
        self._detect_wayland(info)
        self._detect_flatpak(info)
        return info

    def _detect_distro(self, info: SystemInfo) -> None:
        os_release = {}
        for path in ["/etc/os-release", "/usr/lib/os-release"]:
            if os.path.exists(path):
                with open(path) as f:
                    for line in f:
                        if "=" in line:
                            k, v = line.strip().split("=", 1)
                            os_release[k] = v.strip('"')
                break

        name = os_release.get("ID", "").lower()
        pretty = os_release.get("PRETTY_NAME", "Unknown Linux")
        variant = os_release.get("VARIANT_ID", "").lower()
        info.distro_name = pretty

        if "bazzite" in name or "bazzite" in variant or "bazzite" in pretty.lower():
            info.distro = Distro.BAZZITE
            info.is_immutable = True
            info.pkg_manager = PkgManager.RPM_OSTREE
        elif "silverblue" in variant or "kinoite" in variant:
            info.distro = Distro.SILVERBLUE
            info.is_immutable = True
            info.pkg_manager = PkgManager.RPM_OSTREE
        elif "fedora" in name:
            info.distro = Distro.FEDORA
            info.pkg_manager = PkgManager.DNF
        elif "ubuntu" in name or "pop" in name or "mint" in name:
            info.distro = Distro.UBUNTU
            info.pkg_manager = PkgManager.APT
        elif "arch" in name or "manjaro" in name or "endeavouros" in name:
            info.distro = Distro.ARCH
            info.pkg_manager = PkgManager.PACMAN
        else:
            info.distro = Distro.UNKNOWN
            # Try to guess pkg manager
            if shutil.which("dnf"):
                info.pkg_manager = PkgManager.DNF
            elif shutil.which("apt"):
                info.pkg_manager = PkgManager.APT
            elif shutil.which("pacman"):
                info.pkg_manager = PkgManager.PACMAN

    def _detect_gnome(self, info: SystemInfo) -> None:
        ver = run_output("gnome-shell --version")
        if ver:
            # "GNOME Shell 49.1" -> "49.1"
            parts = ver.split()
            if len(parts) >= 3:
                info.gnome_version = parts[-1]

    def _detect_wayland(self, info: SystemInfo) -> None:
        session = os.environ.get("XDG_SESSION_TYPE", "")
        info.is_wayland = session == "wayland"

    def _detect_flatpak(self, info: SystemInfo) -> None:
        info.has_flatpak = shutil.which("flatpak") is not None

    def print_info(self, info: SystemInfo) -> None:
        table = Table(box=box.ROUNDED, border_style="accent", show_header=False, padding=(0, 2))
        table.add_column("Property", style="muted")
        table.add_column("Value", style="bold")
        table.add_row("Distribution", info.distro_name)
        table.add_row("GNOME Shell", info.gnome_version or "not detected")
        table.add_row("Display Server", "Wayland" if info.is_wayland else "X11")
        table.add_row("Immutable OS", "Yes" if info.is_immutable else "No")
        table.add_row("Package Manager", info.pkg_manager.value)
        table.add_row("Flatpak", "Available" if info.has_flatpak else "Not found")
        table.add_row("Home Directory", str(info.home))
        console.print(Panel(table, title="[accent]System Detection[/]", border_style="accent"))
        console.print()


# ─── BackupManager ───────────────────────────────────────────────────────────

class BackupManager:
    """Manages timestamped backups for safe theme installation."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = BACKUP_BASE / self.timestamp
        self.manifest: dict = {"timestamp": self.timestamp, "files": [], "dconf": []}

    def init(self) -> None:
        if not self.dry_run:
            ensure_dir(self.backup_dir)

    def backup_file(self, path: Path) -> bool:
        """Backup a file if it exists. Returns True if backed up."""
        if not path.exists():
            return False
        rel = str(path).replace(str(Path.home()), "~")
        dest = self.backup_dir / "files" / rel.lstrip("~/")
        if self.dry_run:
            console.print(f"  [muted]Would backup: {rel}[/]")
            return True
        ensure_dir(dest.parent)
        shutil.copy2(path, dest)
        self.manifest["files"].append({
            "original": str(path),
            "backup": str(dest),
        })
        return True

    def backup_dconf(self, path: str) -> bool:
        """Backup a dconf path. Returns True if backed up."""
        data = dconf_dump(path)
        if not data:
            return False
        if self.dry_run:
            console.print(f"  [muted]Would backup dconf: {path}[/]")
            return True
        dest = self.backup_dir / "dconf" / path.strip("/").replace("/", "_")
        ensure_dir(dest.parent)
        dest.write_text(data)
        self.manifest["dconf"].append({
            "path": path,
            "backup": str(dest),
        })
        return True

    def save_manifest(self) -> None:
        if self.dry_run:
            return
        manifest_path = self.backup_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(self.manifest, f, indent=2)

    @staticmethod
    def list_backups() -> list[Path]:
        """Return list of backup directories, newest first."""
        if not BACKUP_BASE.exists():
            return []
        dirs = sorted(BACKUP_BASE.iterdir(), reverse=True)
        return [d for d in dirs if d.is_dir() and (d / "manifest.json").exists()]

    @staticmethod
    def restore(backup_dir: Path) -> bool:
        """Restore files and dconf from a backup."""
        manifest_path = backup_dir / "manifest.json"
        if not manifest_path.exists():
            console.print("[error]No manifest.json found in backup[/]")
            return False

        with open(manifest_path) as f:
            manifest = json.load(f)

        console.print(f"\n[info]Restoring from backup: {manifest['timestamp']}[/]\n")

        # Restore files
        for entry in manifest.get("files", []):
            src = Path(entry["backup"])
            dst = Path(entry["original"])
            if src.exists():
                ensure_dir(dst.parent)
                shutil.copy2(src, dst)
                console.print(f"  [success]Restored:[/] {dst}")
            else:
                console.print(f"  [warning]Backup file missing:[/] {src}")

        # Restore dconf
        for entry in manifest.get("dconf", []):
            src = Path(entry["backup"])
            path = entry["path"]
            if src.exists():
                data = src.read_text()
                # Reset the path first, then load
                run(["dconf", "reset", "-f", path])
                if dconf_load(path, data):
                    console.print(f"  [success]Restored dconf:[/] {path}")
                else:
                    console.print(f"  [error]Failed to restore dconf:[/] {path}")
            else:
                console.print(f"  [warning]Backup file missing:[/] {src}")

        return True


# ─── Base Installer Step ─────────────────────────────────────────────────────

class InstallerStep(ABC):
    """Base class for all installation steps."""

    def __init__(self, number: int, name: str, requires_sudo: bool = False):
        self.number = number
        self.name = name
        self.requires_sudo = requires_sudo

    @abstractmethod
    def install(self, sys_info: SystemInfo, backup: BackupManager, dry_run: bool) -> ComponentResult:
        pass

    def uninstall(self, sys_info: SystemInfo) -> bool:
        """Override for components that need custom uninstall logic."""
        return True

    def is_installed(self, sys_info: SystemInfo) -> bool:
        """Check if this component is already installed."""
        return False

    def verify(self, sys_info: SystemInfo) -> bool:
        """Override to add verification after install."""
        return True


# ─── Step 1: GNOME Shell Theme ──────────────────────────────────────────────

class GnomeShellInstaller(InstallerStep):
    def __init__(self):
        super().__init__(1, "GNOME Shell Theme")

    def is_installed(self, sys_info: SystemInfo) -> bool:
        return (sys_info.home / ".themes" / "Material-You-Orange" / "gnome-shell" / "gnome-shell.css").exists()

    def install(self, sys_info: SystemInfo, backup: BackupManager, dry_run: bool) -> ComponentResult:
        src = THEME_DIR / "gnome-shell" / "gnome-shell.css"
        dst = sys_info.home / ".themes" / "Material-You-Orange" / "gnome-shell" / "gnome-shell.css"

        if not src.exists():
            return ComponentResult(self.number, self.name, Status.FAILED, "Source gnome-shell.css not found")

        backup.backup_file(dst)

        if dry_run:
            return ComponentResult(self.number, self.name, Status.SUCCESS, f"Would copy to {dst}")

        copy_file(src, dst)
        return ComponentResult(self.number, self.name, Status.SUCCESS, "Installed")

    def verify(self, sys_info: SystemInfo) -> bool:
        dst = sys_info.home / ".themes" / "Material-You-Orange" / "gnome-shell" / "gnome-shell.css"
        return dst.exists()


# ─── Step 2: GTK4 Theme ─────────────────────────────────────────────────────

class Gtk4Installer(InstallerStep):
    def __init__(self):
        super().__init__(2, "GTK4 Theme")

    def is_installed(self, sys_info: SystemInfo) -> bool:
        return (sys_info.home / ".config" / "gtk-4.0" / "gtk.css").exists()

    def install(self, sys_info: SystemInfo, backup: BackupManager, dry_run: bool) -> ComponentResult:
        src = THEME_DIR / "gtk-4.0" / "gtk.css"
        dst = sys_info.home / ".config" / "gtk-4.0" / "gtk.css"

        if not src.exists():
            return ComponentResult(self.number, self.name, Status.FAILED, "Source gtk-4.0/gtk.css not found")

        backup.backup_file(dst)

        if dry_run:
            return ComponentResult(self.number, self.name, Status.SUCCESS, f"Would copy to {dst}")

        copy_file(src, dst)
        return ComponentResult(self.number, self.name, Status.SUCCESS, "Installed")


# ─── Step 3: GTK3 Theme ─────────────────────────────────────────────────────

class Gtk3Installer(InstallerStep):
    def __init__(self):
        super().__init__(3, "GTK3 Theme")

    def is_installed(self, sys_info: SystemInfo) -> bool:
        return (sys_info.home / ".config" / "gtk-3.0" / "gtk.css").exists()

    def install(self, sys_info: SystemInfo, backup: BackupManager, dry_run: bool) -> ComponentResult:
        src = THEME_DIR / "gtk-3.0" / "gtk.css"
        dst = sys_info.home / ".config" / "gtk-3.0" / "gtk.css"

        if not src.exists():
            return ComponentResult(self.number, self.name, Status.FAILED, "Source gtk-3.0/gtk.css not found")

        backup.backup_file(dst)

        if dry_run:
            return ComponentResult(self.number, self.name, Status.SUCCESS, f"Would copy to {dst}")

        copy_file(src, dst)
        return ComponentResult(self.number, self.name, Status.SUCCESS, "Installed")


# ─── Step 4: Ptyxis Palette ─────────────────────────────────────────────────

class PtyxisInstaller(InstallerStep):
    def __init__(self):
        super().__init__(4, "Ptyxis Palette")

    def is_installed(self, sys_info: SystemInfo) -> bool:
        return (sys_info.home / ".local" / "share" / "org.gnome.Ptyxis" / "palettes" / "material-you-orange.palette").exists()

    def install(self, sys_info: SystemInfo, backup: BackupManager, dry_run: bool) -> ComponentResult:
        src = THEME_DIR / "ptyxis" / "material-you-orange.palette"
        dst = sys_info.home / ".local" / "share" / "org.gnome.Ptyxis" / "palettes" / "material-you-orange.palette"

        if not src.exists():
            return ComponentResult(self.number, self.name, Status.FAILED, "Source palette not found")

        backup.backup_file(dst)

        if dry_run:
            return ComponentResult(self.number, self.name, Status.SUCCESS, f"Would copy to {dst}")

        copy_file(src, dst)
        return ComponentResult(self.number, self.name, Status.SUCCESS, "Installed")


# ─── Step 5: Fastfetch Config ───────────────────────────────────────────────

class FastfetchInstaller(InstallerStep):
    def __init__(self):
        super().__init__(5, "Fastfetch Config")

    def is_installed(self, sys_info: SystemInfo) -> bool:
        cfg = sys_info.home / ".config" / "fastfetch" / "config.jsonc"
        logo = sys_info.home / ".config" / "fastfetch" / "material-logo.txt"
        return cfg.exists() and logo.exists()

    def install(self, sys_info: SystemInfo, backup: BackupManager, dry_run: bool) -> ComponentResult:
        src_cfg = THEME_DIR / "fastfetch" / "config.jsonc"
        src_logo = THEME_DIR / "fastfetch" / "material-logo.txt"
        dst_dir = sys_info.home / ".config" / "fastfetch"
        dst_cfg = dst_dir / "config.jsonc"
        dst_logo = dst_dir / "material-logo.txt"

        if not src_cfg.exists():
            return ComponentResult(self.number, self.name, Status.FAILED, "Source config.jsonc not found")

        backup.backup_file(dst_cfg)
        backup.backup_file(dst_logo)

        if dry_run:
            return ComponentResult(self.number, self.name, Status.SUCCESS, f"Would copy to {dst_dir}")

        copy_file(src_cfg, dst_cfg)
        if src_logo.exists():
            copy_file(src_logo, dst_logo)

        # Disable Bazzite motd and add Material Terminal greeting to .bashrc
        motd_flag = sys_info.home / ".config" / "no-show-user-motd"
        if not motd_flag.exists():
            motd_flag.touch()

        bashrc = sys_info.home / ".bashrc"
        marker = "# Material Gnome Terminal"
        if bashrc.exists():
            content = bashrc.read_text()
            if marker not in content:
                greeting = (
                    "\n"
                    f"{marker}\n"
                    "if [[ $- == *i* ]] && [[ ! -v MATERIAL_TERMINAL ]]; then\n"
                    "    export MATERIAL_TERMINAL=1\n"
                    "    printf '\\n'\n"
                    "    /usr/bin/fastfetch -c ~/.config/fastfetch/config.jsonc\n"
                    "    printf '\\n'\n"
                    "fi\n"
                )
                backup.backup_file(bashrc)
                with open(bashrc, "a") as f:
                    f.write(greeting)

        return ComponentResult(self.number, self.name, Status.SUCCESS, "Installed")


# ─── Step 6: Burn My Windows ────────────────────────────────────────────────

class BurnMyWindowsInstaller(InstallerStep):
    def __init__(self):
        super().__init__(6, "Burn My Windows")

    def is_installed(self, sys_info: SystemInfo) -> bool:
        return (sys_info.home / ".config" / "burn-my-windows" / "profiles" / "material-you-orange.conf").exists()

    def install(self, sys_info: SystemInfo, backup: BackupManager, dry_run: bool) -> ComponentResult:
        src = THEME_DIR / "burn-my-windows" / "material-you-orange.conf"
        profiles_dir = sys_info.home / ".config" / "burn-my-windows" / "profiles"
        dst = profiles_dir / "material-you-orange.conf"

        if not src.exists():
            return ComponentResult(self.number, self.name, Status.FAILED, "Source BMW profile not found")

        # Backup existing profiles
        if profiles_dir.exists():
            for f in profiles_dir.iterdir():
                backup.backup_file(f)

        if dry_run:
            return ComponentResult(self.number, self.name, Status.SUCCESS, f"Would copy to {dst}")

        copy_file(src, dst)
        return ComponentResult(self.number, self.name, Status.SUCCESS, "Installed")


# ─── Step 7: Wallpaper ──────────────────────────────────────────────────────

class WallpaperInstaller(InstallerStep):
    def __init__(self):
        super().__init__(7, "Wallpaper")

    def is_installed(self, sys_info: SystemInfo) -> bool:
        return (sys_info.home / ".local" / "share" / "backgrounds" / "lockscreen.png").exists()

    def install(self, sys_info: SystemInfo, backup: BackupManager, dry_run: bool) -> ComponentResult:
        src = THEME_DIR / "wallpaper" / "lockscreen.png"
        dst = sys_info.home / ".local" / "share" / "backgrounds" / "lockscreen.png"

        if not src.exists():
            return ComponentResult(self.number, self.name, Status.FAILED, "Source wallpaper not found")

        backup.backup_file(dst)

        if dry_run:
            return ComponentResult(self.number, self.name, Status.SUCCESS, f"Would copy to {dst}")

        copy_file(src, dst)
        return ComponentResult(self.number, self.name, Status.SUCCESS, "Installed")


# ─── Step 8: Fonts ──────────────────────────────────────────────────────────

class FontsInstaller(InstallerStep):
    def __init__(self):
        super().__init__(8, "Fonts (Inter, Fira Code, Noto Serif)")

    def is_installed(self, sys_info: SystemInfo) -> bool:
        fonts_dir = sys_info.home / ".local" / "share" / "fonts"
        return self._font_installed(fonts_dir, "Inter")

    def install(self, sys_info: SystemInfo, backup: BackupManager, dry_run: bool) -> ComponentResult:
        fonts_dir = sys_info.home / ".local" / "share" / "fonts"

        if dry_run:
            return ComponentResult(self.number, self.name, Status.SUCCESS, "Would download and install fonts")

        ensure_dir(fonts_dir)
        results = []

        # Inter
        if not self._font_installed(fonts_dir, "Inter"):
            ok = self._install_inter(fonts_dir)
            results.append(("Inter", ok))
        else:
            results.append(("Inter", True))

        # Fira Code
        if not self._font_installed(fonts_dir, "FiraCode"):
            ok = self._install_firacode(fonts_dir)
            results.append(("Fira Code", ok))
        else:
            results.append(("Fira Code", True))

        # Noto Serif
        if not self._font_installed(fonts_dir, "NotoSerif"):
            ok = self._install_notoserif(fonts_dir)
            results.append(("Noto Serif", ok))
        else:
            results.append(("Noto Serif", True))

        # Refresh font cache
        run(["fc-cache", "-f"], timeout=60)

        failed = [name for name, ok in results if not ok]
        if failed:
            return ComponentResult(self.number, self.name, Status.FAILED, f"Failed: {', '.join(failed)}")
        return ComponentResult(self.number, self.name, Status.SUCCESS, "All fonts installed")

    def _font_installed(self, fonts_dir: Path, prefix: str) -> bool:
        """Check if font files with given prefix exist."""
        for f in fonts_dir.iterdir() if fonts_dir.exists() else []:
            if f.name.startswith(prefix) and f.suffix in (".ttf", ".otf"):
                return True
        # Also check system fonts
        result = run_output(f"fc-list | grep -i '{prefix}'")
        return bool(result)

    def _install_inter(self, fonts_dir: Path) -> bool:
        console.print("  Downloading Inter font...")
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = Path(tmp) / "inter.zip"
            if not download_file(FONT_URLS["Inter"], zip_path):
                return False
            try:
                with zipfile.ZipFile(zip_path) as zf:
                    for name in zf.namelist():
                        if name.endswith(".ttf") and "InterVariable" in name:
                            data = zf.read(name)
                            dest = fonts_dir / Path(name).name
                            dest.write_bytes(data)
                return True
            except Exception as e:
                console.print(f"  [error]Error extracting Inter: {e}[/]")
                return False

    def _install_firacode(self, fonts_dir: Path) -> bool:
        console.print("  Downloading Fira Code font...")
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = Path(tmp) / "firacode.zip"
            if not download_file(FONT_URLS["FiraCode"], zip_path):
                return False
            try:
                with zipfile.ZipFile(zip_path) as zf:
                    for name in zf.namelist():
                        if name.endswith(".ttf") and "/ttf/" in name:
                            data = zf.read(name)
                            dest = fonts_dir / Path(name).name
                            dest.write_bytes(data)
                return True
            except Exception as e:
                console.print(f"  [error]Error extracting Fira Code: {e}[/]")
                return False

    def _install_notoserif(self, fonts_dir: Path) -> bool:
        console.print("  Downloading Noto Serif font...")
        dest = fonts_dir / "NotoSerif-Variable.ttf"
        return download_file(FONT_URLS["NotoSerif"], dest)


# ─── Step 9: Papirus Icons ──────────────────────────────────────────────────

class PapirusInstaller(InstallerStep):
    def __init__(self):
        super().__init__(9, "Papirus Icons")

    def is_installed(self, sys_info: SystemInfo) -> bool:
        return (sys_info.home / ".local" / "share" / "icons" / "Papirus-Dark").exists() or self._system_installed()

    def install(self, sys_info: SystemInfo, backup: BackupManager, dry_run: bool) -> ComponentResult:
        icons_dir = sys_info.home / ".local" / "share" / "icons"

        # Check if already installed
        if (icons_dir / "Papirus-Dark").exists() or self._system_installed():
            return ComponentResult(self.number, self.name, Status.SUCCESS, "Already installed")

        if dry_run:
            return ComponentResult(self.number, self.name, Status.SUCCESS, "Would install Papirus icons")

        # Try package manager first (non-immutable systems)
        if not sys_info.is_immutable:
            if self._install_via_pkg(sys_info):
                return ComponentResult(self.number, self.name, Status.SUCCESS, "Installed via package manager")

        # Fall back to manual download
        console.print("  Downloading Papirus icon theme (this may take a moment)...")
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = Path(tmp) / "papirus.zip"
            if not download_file(PAPIRUS_URL, zip_path):
                return ComponentResult(self.number, self.name, Status.FAILED, "Download failed")
            try:
                with zipfile.ZipFile(zip_path) as zf:
                    zf.extractall(tmp)
                # Find extracted directory
                extracted = Path(tmp) / "papirus-icon-theme-master"
                if not extracted.exists():
                    return ComponentResult(self.number, self.name, Status.FAILED, "Extraction failed")
                # Copy Papirus and Papirus-Dark
                for theme_name in ["Papirus", "Papirus-Dark"]:
                    src = extracted / theme_name
                    if src.exists():
                        dst = icons_dir / theme_name
                        if dst.exists():
                            shutil.rmtree(dst)
                        shutil.copytree(src, dst)
                # Update icon cache
                run(["gtk-update-icon-cache", str(icons_dir / "Papirus-Dark")], timeout=60)
                return ComponentResult(self.number, self.name, Status.SUCCESS, "Installed from GitHub")
            except Exception as e:
                return ComponentResult(self.number, self.name, Status.FAILED, f"Error: {e}")

    def _system_installed(self) -> bool:
        return Path("/usr/share/icons/Papirus-Dark").exists()

    def _install_via_pkg(self, sys_info: SystemInfo) -> bool:
        pkg_name = {
            PkgManager.DNF: "papirus-icon-theme",
            PkgManager.APT: "papirus-icon-theme",
            PkgManager.PACMAN: "papirus-icon-theme",
        }.get(sys_info.pkg_manager)
        if not pkg_name:
            return False
        cmd = {
            PkgManager.DNF: ["sudo", "dnf", "install", "-y", pkg_name],
            PkgManager.APT: ["sudo", "apt", "install", "-y", pkg_name],
            PkgManager.PACMAN: ["sudo", "pacman", "-S", "--noconfirm", pkg_name],
        }.get(sys_info.pkg_manager)
        if cmd:
            return run_ok(cmd, timeout=300)
        return False


# ─── Step 10: Bibata Cursor ─────────────────────────────────────────────────

class BibataInstaller(InstallerStep):
    def __init__(self):
        super().__init__(10, "Bibata Cursor")

    def is_installed(self, sys_info: SystemInfo) -> bool:
        return (sys_info.home / ".local" / "share" / "icons" / "Bibata-Modern-Classic").exists()

    def install(self, sys_info: SystemInfo, backup: BackupManager, dry_run: bool) -> ComponentResult:
        icons_dir = sys_info.home / ".local" / "share" / "icons"
        cursor_dir = icons_dir / "Bibata-Modern-Classic"

        if cursor_dir.exists():
            return ComponentResult(self.number, self.name, Status.SUCCESS, "Already installed")

        if dry_run:
            return ComponentResult(self.number, self.name, Status.SUCCESS, "Would install Bibata cursor")

        console.print("  Downloading Bibata cursor theme...")
        with tempfile.TemporaryDirectory() as tmp:
            tar_path = Path(tmp) / "bibata.tar.xz"
            if not download_file(BIBATA_URL, tar_path):
                return ComponentResult(self.number, self.name, Status.FAILED, "Download failed")
            try:
                r = run(["tar", "xf", str(tar_path), "-C", tmp])
                if r.returncode != 0:
                    return ComponentResult(self.number, self.name, Status.FAILED, "Extraction failed")
                src = Path(tmp) / "Bibata-Modern-Classic"
                if src.exists():
                    ensure_dir(icons_dir)
                    if cursor_dir.exists():
                        shutil.rmtree(cursor_dir)
                    shutil.copytree(src, cursor_dir)
                    return ComponentResult(self.number, self.name, Status.SUCCESS, "Installed")
                return ComponentResult(self.number, self.name, Status.FAILED, "Cursor theme not found in archive")
            except Exception as e:
                return ComponentResult(self.number, self.name, Status.FAILED, f"Error: {e}")


# ─── Step 11: GNOME Extensions ──────────────────────────────────────────────

class GnomeExtensionsInstaller(InstallerStep):
    def __init__(self):
        super().__init__(11, "GNOME Extensions")

    def is_installed(self, sys_info: SystemInfo) -> bool:
        ext_dir = sys_info.home / ".local" / "share" / "gnome-shell" / "extensions"
        sys_ext = Path("/usr/share/gnome-shell/extensions")
        count = sum(1 for uuid, _ in EXTENSIONS
                    if (ext_dir / uuid).exists() or (sys_ext / uuid).exists())
        return count >= len(EXTENSIONS) // 2

    def install(self, sys_info: SystemInfo, backup: BackupManager, dry_run: bool) -> ComponentResult:
        if not sys_info.gnome_version:
            return ComponentResult(self.number, self.name, Status.FAILED, "GNOME not detected")

        if dry_run:
            ext_list = ", ".join(name for _, name in EXTENSIONS)
            return ComponentResult(self.number, self.name, Status.SUCCESS, f"Would install: {ext_list}")

        # Backup current extension list
        backup.backup_dconf("/org/gnome/shell/enabled-extensions")

        installed = []
        failed = []
        already = []

        for uuid, name in EXTENSIONS:
            status = self._install_extension(uuid, name, sys_info)
            if status == "installed":
                installed.append(name)
            elif status == "already":
                already.append(name)
            else:
                failed.append(name)

        # Enable all extensions
        self._enable_extensions(sys_info)

        parts = []
        if installed:
            parts.append(f"{len(installed)} installed")
        if already:
            parts.append(f"{len(already)} already present")
        if failed:
            parts.append(f"{len(failed)} failed")

        status = Status.SUCCESS if not failed else Status.FAILED
        return ComponentResult(self.number, self.name, status, ", ".join(parts))

    def _install_extension(self, uuid: str, name: str, sys_info: SystemInfo) -> str:
        """Install a single extension. Returns 'installed', 'already', or 'failed'."""
        # Check if already installed
        ext_dir = sys_info.home / ".local" / "share" / "gnome-shell" / "extensions" / uuid
        sys_ext_dir = Path("/usr/share/gnome-shell/extensions") / uuid
        if ext_dir.exists() or sys_ext_dir.exists():
            return "already"

        console.print(f"  Installing {name}...")

        # Use gnome-extensions install from extensions.gnome.org
        shell_ver = sys_info.gnome_version.split(".")[0]  # e.g. "49"

        # Query the extension info from GNOME extensions API
        try:
            api_url = f"https://extensions.gnome.org/extension-info/?uuid={uuid}&shell_version={shell_ver}"
            req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                info = json.loads(resp.read())
            pk = info.get("pk")
            version_tag = None
            # Find the right version
            shell_versions = info.get("shell_version_map", {})
            if shell_ver in shell_versions:
                version_tag = shell_versions[shell_ver].get("version")
            elif "all" in shell_versions:
                version_tag = shell_versions["all"].get("version")
            else:
                # Try any available version
                for ver_key, ver_info in shell_versions.items():
                    version_tag = ver_info.get("version")
                    break

            if not version_tag or not pk:
                console.print(f"  [warning]No compatible version for {name}[/]")
                return "failed"

            # Download the extension zip
            dl_url = f"https://extensions.gnome.org/download-extension/{uuid}.shell-extension.zip?version_tag={version_tag}"
            with tempfile.TemporaryDirectory() as tmp:
                zip_path = Path(tmp) / "ext.zip"
                if not download_file(dl_url, zip_path):
                    return "failed"
                # Install using gnome-extensions
                r = run(["gnome-extensions", "install", "--force", str(zip_path)], timeout=30)
                if r.returncode == 0:
                    return "installed"
                else:
                    # Manual install fallback
                    ext_dest = sys_info.home / ".local" / "share" / "gnome-shell" / "extensions" / uuid
                    ensure_dir(ext_dest)
                    with zipfile.ZipFile(zip_path) as zf:
                        zf.extractall(ext_dest)
                    return "installed"
        except Exception as e:
            console.print(f"  [warning]Failed to install {name}: {e}[/]")
            return "failed"

    def _enable_extensions(self, sys_info: SystemInfo) -> None:
        """Enable all required extensions via dconf."""
        uuids = [uuid for uuid, _ in EXTENSIONS]
        # Also add ding and lockscreen-extension
        uuids.extend(["ding@rastersoft.com", "lockscreen-extension@pratap.fastmail.fm"])
        # Format as GVariant array
        arr = "[" + ", ".join(f"'{u}'" for u in uuids) + "]"
        dconf_write("/org/gnome/shell/enabled-extensions", arr)
        dconf_write("/org/gnome/shell/disable-user-extensions", "false")


# ─── Step 12: dconf Settings ────────────────────────────────────────────────

class DconfSettingsInstaller(InstallerStep):
    def __init__(self):
        super().__init__(12, "dconf Settings")

    def is_installed(self, sys_info: SystemInfo) -> bool:
        val = run_output(["dconf", "read", "/org/gnome/desktop/interface/accent-color"])
        return bool(val)

    def install(self, sys_info: SystemInfo, backup: BackupManager, dry_run: bool) -> ComponentResult:
        if dry_run:
            return ComponentResult(self.number, self.name, Status.SUCCESS, "Would apply all dconf settings")

        # Backup relevant dconf paths
        for path in ["/org/gnome/desktop/", "/org/gnome/shell/", "/org/gnome/mutter/",
                      "/org/gnome/settings-daemon/"]:
            backup.backup_dconf(path)

        failed = []

        # Desktop interface
        settings = {
            "/org/gnome/desktop/interface/accent-color": "'orange'",
            "/org/gnome/desktop/interface/color-scheme": "'prefer-dark'",
            "/org/gnome/desktop/interface/cursor-theme": "'Bibata-Modern-Classic'",
            "/org/gnome/desktop/interface/icon-theme": "'Papirus-Dark'",
            "/org/gnome/desktop/interface/gtk-theme": "'Marble-red-dark'",
            "/org/gnome/desktop/interface/font-name": "'Inter 11'",
            "/org/gnome/desktop/interface/document-font-name": "'Noto Serif 11'",
            "/org/gnome/desktop/interface/show-battery-percentage": "true",
            "/org/gnome/desktop/wm/preferences/titlebar-font": "'Inter Semi-Bold 11'",
            # Background
            "/org/gnome/desktop/background/picture-uri": f"'file://{sys_info.home}/.local/share/backgrounds/lockscreen.png'",
            "/org/gnome/desktop/background/picture-uri-dark": f"'file://{sys_info.home}/.local/share/backgrounds/lockscreen.png'",
            "/org/gnome/desktop/background/picture-options": "'zoom'",
            "/org/gnome/desktop/background/primary-color": "'#000000000000'",
            "/org/gnome/desktop/background/color-shading-type": "'solid'",
            # Screensaver
            "/org/gnome/desktop/screensaver/picture-uri": f"'file://{sys_info.home}/.local/share/backgrounds/lockscreen.png'",
            "/org/gnome/desktop/screensaver/picture-options": "'zoom'",
            "/org/gnome/desktop/screensaver/primary-color": "'#000000000000'",
            "/org/gnome/desktop/screensaver/color-shading-type": "'solid'",
            # Night light
            "/org/gnome/settings-daemon/plugins/color/night-light-enabled": "true",
            "/org/gnome/settings-daemon/plugins/color/night-light-schedule-automatic": "false",
            "/org/gnome/settings-daemon/plugins/color/night-light-temperature": "uint32 3200",
            # Mutter
            "/org/gnome/mutter/edge-tiling": "true",
            # Mouse
            "/org/gnome/desktop/peripherals/mouse/accel-profile": "'flat'",
            # Sound
            "/org/gnome/desktop/sound/theme-name": "'freedesktop'",
            # A11y
            "/org/gnome/desktop/a11y/interface/high-contrast": "false",
        }

        # Extension-specific settings
        ext_settings = {
            # User Theme
            "/org/gnome/shell/extensions/user-theme/name": "'Material-You-Orange'",
            # Logo Menu
            "/org/gnome/shell/extensions/Logo-menu/hide-forcequit": "true",
            "/org/gnome/shell/extensions/Logo-menu/hide-icon-shadow": "false",
            "/org/gnome/shell/extensions/Logo-menu/menu-button-icon-image": "21",
            "/org/gnome/shell/extensions/Logo-menu/menu-button-icon-size": "19",
            "/org/gnome/shell/extensions/Logo-menu/menu-button-terminal": "'ptyxis --new-window'",
            "/org/gnome/shell/extensions/Logo-menu/show-activities-button": "true",
            "/org/gnome/shell/extensions/Logo-menu/symbolic-icon": "true",
            # Blur My Shell
            "/org/gnome/shell/extensions/blur-my-shell/settings-version": "2",
            "/org/gnome/shell/extensions/blur-my-shell/appfolder/brightness": "0.6",
            "/org/gnome/shell/extensions/blur-my-shell/appfolder/sigma": "30",
            "/org/gnome/shell/extensions/blur-my-shell/dash-to-dock/blur": "true",
            "/org/gnome/shell/extensions/blur-my-shell/dash-to-dock/brightness": "0.6",
            "/org/gnome/shell/extensions/blur-my-shell/dash-to-dock/sigma": "30",
            "/org/gnome/shell/extensions/blur-my-shell/dash-to-dock/static-blur": "true",
            "/org/gnome/shell/extensions/blur-my-shell/dash-to-dock/style-dash-to-dock": "0",
            "/org/gnome/shell/extensions/blur-my-shell/overview/blur": "true",
            "/org/gnome/shell/extensions/blur-my-shell/panel/blur": "false",
            "/org/gnome/shell/extensions/blur-my-shell/panel/brightness": "0.6",
            "/org/gnome/shell/extensions/blur-my-shell/panel/override-background": "true",
            "/org/gnome/shell/extensions/blur-my-shell/panel/sigma": "30",
            "/org/gnome/shell/extensions/blur-my-shell/panel/static-blur": "false",
            "/org/gnome/shell/extensions/blur-my-shell/panel/style-panel": "0",
            # Burn My Windows
            "/org/gnome/shell/extensions/burn-my-windows/active-profile": f"'{sys_info.home}/.config/burn-my-windows/profiles/material-you-orange.conf'",
            # Caffeine
            "/org/gnome/shell/extensions/caffeine/user-enabled": "true",
            # DING
            "/org/gnome/shell/extensions/ding/show-home": "false",
            "/org/gnome/shell/extensions/ding/show-trash": "true",
            "/org/gnome/shell/extensions/ding/icon-size": "'standard'",
            # Magic Lamp
            "/org/gnome/shell/extensions/ncom/github/hermes83/compiz-alike-magic-lamp-effect/duration": "300.0",
            "/org/gnome/shell/extensions/ncom/github/hermes83/compiz-alike-magic-lamp-effect/x-tiles": "15.0",
            "/org/gnome/shell/extensions/ncom/github/hermes83/compiz-alike-magic-lamp-effect/y-tiles": "20.0",
            # AppIndicator
            "/org/gnome/shell/extensions/appindicator/legacy-tray-enabled": "true",
        }

        all_settings = {**settings, **ext_settings}

        for key, value in all_settings.items():
            if not dconf_write(key, value):
                failed.append(key.split("/")[-1])

        if failed:
            return ComponentResult(self.number, self.name, Status.FAILED, f"Failed keys: {', '.join(failed[:5])}")
        return ComponentResult(self.number, self.name, Status.SUCCESS, f"Applied {len(all_settings)} settings")


# ─── Step 13: Flatpak Overrides ─────────────────────────────────────────────

class FlatpakOverridesInstaller(InstallerStep):
    def __init__(self):
        super().__init__(13, "Flatpak Overrides")

    def is_installed(self, sys_info: SystemInfo) -> bool:
        return (sys_info.home / ".local" / "share" / "flatpak" / "overrides" / "global").exists()

    def install(self, sys_info: SystemInfo, backup: BackupManager, dry_run: bool) -> ComponentResult:
        if not sys_info.has_flatpak:
            return ComponentResult(self.number, self.name, Status.SKIPPED, "Flatpak not available")

        overrides_dir = sys_info.home / ".local" / "share" / "flatpak" / "overrides"

        global_override = textwrap.dedent("""\
            [Context]
            filesystems=xdg-config/gtk-3.0:ro;xdg-config/gtk-4.0:ro;~/.local/share/icons:ro;~/.icons:ro;~/.themes:ro

            [Environment]
            GTK_THEME=Marble-red-dark
            ICON_THEME=Papirus-Dark
            QT_QPA_PLATFORMTHEME=gtk3
            QT_STYLE_OVERRIDE=adwaita-dark
        """)

        if dry_run:
            return ComponentResult(self.number, self.name, Status.SUCCESS, "Would write global Flatpak override")

        global_file = overrides_dir / "global"
        backup.backup_file(global_file)
        ensure_dir(overrides_dir)
        global_file.write_text(global_override)

        return ComponentResult(self.number, self.name, Status.SUCCESS, "Global override written")


# ─── Step 14: Flatpak GTK Symlinks ──────────────────────────────────────────

class FlatpakSymlinksInstaller(InstallerStep):
    def __init__(self):
        super().__init__(14, "Flatpak GTK Symlinks")

    def is_installed(self, sys_info: SystemInfo) -> bool:
        flatpak_base = sys_info.home / ".var" / "app"
        if not flatpak_base.exists():
            return False
        for app_dir in flatpak_base.iterdir():
            css = app_dir / "config" / "gtk-4.0" / "gtk.css"
            if css.is_symlink():
                return True
        return False

    def install(self, sys_info: SystemInfo, backup: BackupManager, dry_run: bool) -> ComponentResult:
        if not sys_info.has_flatpak:
            return ComponentResult(self.number, self.name, Status.SKIPPED, "Flatpak not available")

        # Get list of installed Flatpak apps
        result = run_output("flatpak list --app --columns=application")
        if not result:
            return ComponentResult(self.number, self.name, Status.SKIPPED, "No Flatpak apps found")

        apps = [line.strip() for line in result.split("\n") if line.strip()]
        flatpak_base = sys_info.home / ".var" / "app"

        gtk4_src = sys_info.home / ".config" / "gtk-4.0" / "gtk.css"
        gtk3_src = sys_info.home / ".config" / "gtk-3.0" / "gtk.css"

        if dry_run:
            return ComponentResult(self.number, self.name, Status.SUCCESS, f"Would create symlinks for {len(apps)} apps")

        count = 0
        for app_id in apps:
            app_dir = flatpak_base / app_id
            for version, src in [("gtk-4.0", gtk4_src), ("gtk-3.0", gtk3_src)]:
                config_dir = app_dir / "config" / version
                dst = config_dir / "gtk.css"
                ensure_dir(config_dir)
                # Remove existing file/symlink
                if dst.exists() or dst.is_symlink():
                    dst.unlink()
                try:
                    dst.symlink_to(src)
                    count += 1
                except OSError:
                    pass

        return ComponentResult(self.number, self.name, Status.SUCCESS, f"Created {count} symlinks for {len(apps)} apps")


# ─── Step 15: Firefox Theme ─────────────────────────────────────────────────

class FirefoxInstaller(InstallerStep):
    def __init__(self):
        super().__init__(15, "Firefox Theme")

    def is_installed(self, sys_info: SystemInfo) -> bool:
        for ff_dir in [
            sys_info.home / ".var" / "app" / "org.mozilla.firefox" / "config" / "mozilla" / "firefox",
            sys_info.home / ".mozilla" / "firefox",
        ]:
            if not ff_dir.exists():
                continue
            for d in ff_dir.iterdir():
                if d.is_dir() and (d / "chrome" / "userChrome.css").exists():
                    return True
        return False

    def install(self, sys_info: SystemInfo, backup: BackupManager, dry_run: bool) -> ComponentResult:
        chrome_src = THEME_DIR / "firefox" / "userChrome.css"
        content_src = THEME_DIR / "firefox" / "userContent.css"

        if not chrome_src.exists() or not content_src.exists():
            return ComponentResult(self.number, self.name, Status.FAILED, "Source Firefox CSS not found")

        # Find Firefox profile directories
        profiles = self._find_profiles(sys_info)
        if not profiles:
            return ComponentResult(self.number, self.name, Status.SKIPPED, "No Firefox profiles found")

        if dry_run:
            return ComponentResult(self.number, self.name, Status.SUCCESS, f"Would install to {len(profiles)} profile(s)")

        for profile_dir in profiles:
            chrome_dir = profile_dir / "chrome"
            ensure_dir(chrome_dir)

            backup.backup_file(chrome_dir / "userChrome.css")
            backup.backup_file(chrome_dir / "userContent.css")

            copy_file(chrome_src, chrome_dir / "userChrome.css")
            copy_file(content_src, chrome_dir / "userContent.css")

            # Configure user.js for toolkit.legacyUserProfileCustomizations
            user_js = profile_dir / "user.js"
            backup.backup_file(user_js)
            self._write_user_js(user_js)

        return ComponentResult(self.number, self.name, Status.SUCCESS, f"Installed to {len(profiles)} profile(s)")

    def _find_profiles(self, sys_info: SystemInfo) -> list[Path]:
        """Find Firefox profile directories (native and Flatpak)."""
        profiles = []

        # Flatpak Firefox
        flatpak_ff = sys_info.home / ".var" / "app" / "org.mozilla.firefox" / "config" / "mozilla" / "firefox"
        # Native Firefox
        native_ff = sys_info.home / ".mozilla" / "firefox"

        for ff_dir in [flatpak_ff, native_ff]:
            if not ff_dir.exists():
                continue
            profiles_ini = ff_dir / "profiles.ini"
            if profiles_ini.exists():
                # Parse profiles.ini to find profile paths
                import configparser
                config = configparser.ConfigParser()
                config.read(profiles_ini)
                for section in config.sections():
                    if section.startswith("Profile") or section.startswith("Install"):
                        path = config.get(section, "Path", fallback=None)
                        is_relative = config.get(section, "IsRelative", fallback="1")
                        if path:
                            if is_relative == "1":
                                full_path = ff_dir / path
                            else:
                                full_path = Path(path)
                            if full_path.exists():
                                profiles.append(full_path)
            else:
                # Fallback: look for *.default* directories
                for d in ff_dir.iterdir():
                    if d.is_dir() and "default" in d.name:
                        profiles.append(d)

        # Deduplicate
        seen = set()
        unique = []
        for p in profiles:
            rp = p.resolve()
            if rp not in seen:
                seen.add(rp)
                unique.append(p)
        return unique

    def _write_user_js(self, path: Path) -> None:
        """Ensure user.js enables custom CSS loading."""
        existing = ""
        if path.exists():
            existing = path.read_text()

        pref = 'user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);'
        if pref not in existing:
            with open(path, "a") as f:
                if existing and not existing.endswith("\n"):
                    f.write("\n")
                f.write(f"\n// Material You Orange - enable custom CSS\n{pref}\n")


# ─── Step 16: GDM Theme ─────────────────────────────────────────────────────

class GdmInstaller(InstallerStep):
    def __init__(self):
        super().__init__(16, "GDM Theme", requires_sudo=True)

    def is_installed(self, sys_info: SystemInfo) -> bool:
        return Path("/etc/dconf/db/gdm.d/01-material-you").exists()

    def install(self, sys_info: SystemInfo, backup: BackupManager, dry_run: bool) -> ComponentResult:
        gdm_src = THEME_DIR / "gdm" / "01-material-you"
        if not gdm_src.exists():
            return ComponentResult(self.number, self.name, Status.FAILED, "Source GDM dconf not found")

        if dry_run:
            return ComponentResult(self.number, self.name, Status.SUCCESS, "Would configure GDM theme (requires sudo)")

        results = []

        # 1. Write GDM dconf profile
        gdm_dconf_dir = Path("/etc/dconf/db/gdm.d")
        gdm_dest = gdm_dconf_dir / "01-material-you"
        r = run(["sudo", "mkdir", "-p", str(gdm_dconf_dir)])
        r = run(["sudo", "cp", str(gdm_src), str(gdm_dest)])
        if r.returncode == 0:
            results.append("dconf")
        else:
            results.append("!dconf")

        # 2. Copy Inter font for GDM
        inter_font = None
        # Look for Inter in user fonts
        user_fonts = sys_info.home / ".local" / "share" / "fonts"
        if user_fonts.exists():
            for f in user_fonts.iterdir():
                if f.name.startswith("Inter") and f.suffix in (".ttf", ".otf"):
                    inter_font = f
                    break
        if inter_font:
            gdm_font_dir = Path("/etc/fonts/local-fonts")
            r = run(["sudo", "mkdir", "-p", str(gdm_font_dir)])
            r = run(["sudo", "cp", str(inter_font), str(gdm_font_dir / inter_font.name)])
            if r.returncode == 0:
                results.append("font")

        # 3. Symlink Bibata cursor for GDM
        cursor_src = sys_info.home / ".local" / "share" / "icons" / "Bibata-Modern-Classic"
        if cursor_src.exists():
            cursor_dest = Path("/usr/local/share/icons/Bibata-Modern-Classic")
            run(["sudo", "mkdir", "-p", "/usr/local/share/icons"])
            # Remove existing if it's a symlink
            run(["sudo", "rm", "-rf", str(cursor_dest)])
            r = run(["sudo", "cp", "-r", str(cursor_src), str(cursor_dest)])
            if r.returncode == 0:
                results.append("cursor")

        # 4. Rebuild GDM dconf database
        r = run(["sudo", "dconf", "update"])
        if r.returncode == 0:
            results.append("db-updated")

        ok_items = [r for r in results if not r.startswith("!")]
        return ComponentResult(self.number, self.name, Status.SUCCESS, f"Configured: {', '.join(ok_items)}")


# ─── Step 17: DING Fix ──────────────────────────────────────────────────────

class DingFixInstaller(InstallerStep):
    def __init__(self):
        super().__init__(17, "DING Desktop Icons Fix")

    def is_installed(self, sys_info: SystemInfo) -> bool:
        for p in [
            sys_info.home / ".local" / "share" / "gnome-shell" / "extensions" / "ding@rastersoft.com" / "app" / "desktopManager.js",
            Path("/usr/share/gnome-shell/extensions/ding@rastersoft.com/app/desktopManager.js"),
        ]:
            if p.exists():
                try:
                    return "priority: 900" in p.read_text()
                except OSError:
                    pass
        return False

    def install(self, sys_info: SystemInfo, backup: BackupManager, dry_run: bool) -> ComponentResult:
        # Find DING's desktopManager.js
        ding_paths = [
            sys_info.home / ".local" / "share" / "gnome-shell" / "extensions" / "ding@rastersoft.com" / "app" / "desktopManager.js",
            Path("/usr/share/gnome-shell/extensions/ding@rastersoft.com/app/desktopManager.js"),
        ]

        target = None
        for p in ding_paths:
            if p.exists():
                target = p
                break

        if not target:
            return ComponentResult(self.number, self.name, Status.SKIPPED, "DING extension not found")

        if dry_run:
            return ComponentResult(self.number, self.name, Status.SUCCESS, f"Would patch {target}")

        backup.backup_file(target)

        content = target.read_text()
        # Look for CSS priority 600 and change to 900
        if "priority: 600" in content:
            new_content = content.replace("priority: 600", "priority: 900")
            # If it's in a system path, need sudo
            if str(target).startswith("/usr/"):
                with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as tmp:
                    tmp.write(new_content)
                    tmp_path = tmp.name
                r = run(["sudo", "cp", tmp_path, str(target)])
                os.unlink(tmp_path)
                if r.returncode != 0:
                    return ComponentResult(self.number, self.name, Status.FAILED, "Failed to write (sudo)")
            else:
                target.write_text(new_content)
            return ComponentResult(self.number, self.name, Status.SUCCESS, "Patched priority 600 -> 900")
        elif "priority: 900" in content:
            return ComponentResult(self.number, self.name, Status.SUCCESS, "Already patched")
        else:
            return ComponentResult(self.number, self.name, Status.SKIPPED, "Priority pattern not found")


# ─── Step 18: rEFInd Boot Manager ────────────────────────────────────────────

class RefindInstaller(InstallerStep):
    def __init__(self):
        super().__init__(18, "rEFInd Boot Manager", requires_sudo=True)

    def is_installed(self, sys_info: SystemInfo) -> bool:
        return run_ok(["rpm", "-q", "refind"])

    def install(self, sys_info: SystemInfo, backup: BackupManager, dry_run: bool) -> ComponentResult:
        # Check if already installed
        if run_ok(["rpm", "-q", "refind"]):
            return ComponentResult(self.number, self.name, Status.SUCCESS, "Already installed")

        rpm_path = sys_info.home / "refind-0.14.2-1.x86_64.rpm"
        if not rpm_path.exists():
            return ComponentResult(self.number, self.name, Status.FAILED, f"RPM not found: {rpm_path}")

        if dry_run:
            return ComponentResult(self.number, self.name, Status.SUCCESS, "Would install rEFInd via rpm-ostree")

        # Install via rpm-ostree on immutable systems, rpm on mutable
        if sys_info.is_immutable:
            r = run(["sudo", "rpm-ostree", "install", str(rpm_path)], timeout=300)
        else:
            r = run(["sudo", "rpm", "-ivh", str(rpm_path)], timeout=120)

        if r.returncode != 0:
            return ComponentResult(self.number, self.name, Status.FAILED,
                                   f"Install failed: {r.stderr.strip()[:100]}")

        # Run refind-install
        r = run(["sudo", "refind-install"], timeout=120)
        if r.returncode != 0:
            return ComponentResult(self.number, self.name, Status.FAILED,
                                   f"refind-install failed: {r.stderr.strip()[:100]}")

        return ComponentResult(self.number, self.name, Status.SUCCESS, "Installed and configured")


# ─── Step 19: rEFInd Theme ──────────────────────────────────────────────────

class RefindThemeInstaller(InstallerStep):
    def __init__(self):
        super().__init__(19, "rEFInd Material You Theme", requires_sudo=True)

    def is_installed(self, sys_info: SystemInfo) -> bool:
        return Path("/boot/efi/EFI/refind/themes/material-you/theme.conf").exists()

    def install(self, sys_info: SystemInfo, backup: BackupManager, dry_run: bool) -> ComponentResult:
        src_dir = THEME_DIR / "refind"
        if not src_dir.exists():
            return ComponentResult(self.number, self.name, Status.FAILED, "Source theme/refind/ not found")

        refind_dir = Path("/boot/efi/EFI/refind")
        theme_dest = refind_dir / "themes" / "material-you"
        refind_conf = refind_dir / "refind.conf"

        if not refind_conf.exists():
            return ComponentResult(self.number, self.name, Status.FAILED, "refind.conf not found — is rEFInd installed?")

        if dry_run:
            return ComponentResult(self.number, self.name, Status.SUCCESS, f"Would deploy theme to {theme_dest}")

        # Backup existing theme if present
        if theme_dest.exists():
            backup_target = backup.backup_dir / "files" / "boot" / "efi" / "EFI" / "refind" / "themes" / "material-you"
            if not backup.dry_run:
                ensure_dir(backup_target.parent)
                run(["sudo", "cp", "-r", str(theme_dest), str(backup_target)])

        # Create theme directory and copy files
        run(["sudo", "mkdir", "-p", str(theme_dest / "icons")])

        for item in ["background.png", "theme.conf", "selection_big.png", "selection_small.png"]:
            src = src_dir / item
            if src.exists():
                r = run(["sudo", "cp", str(src), str(theme_dest / item)])
                if r.returncode != 0:
                    return ComponentResult(self.number, self.name, Status.FAILED, f"Failed to copy {item}")

        # Copy icons
        icons_src = src_dir / "icons"
        if icons_src.exists():
            for icon in icons_src.iterdir():
                run(["sudo", "cp", str(icon), str(theme_dest / "icons" / icon.name)])

        # Add include line to refind.conf if not already present
        conf_content = run_output(["sudo", "cat", str(refind_conf)])
        include_line = "include themes/material-you/theme.conf"
        if include_line not in conf_content:
            r = run(f'echo "\n{include_line}" | sudo tee -a {refind_conf}', timeout=10)
            if r.returncode != 0:
                return ComponentResult(self.number, self.name, Status.FAILED, "Failed to update refind.conf")

        return ComponentResult(self.number, self.name, Status.SUCCESS, "Theme deployed")


# ─── Component Registry ─────────────────────────────────────────────────────

ALL_STEPS: list[InstallerStep] = [
    GnomeShellInstaller(),    # 1
    Gtk4Installer(),          # 2
    Gtk3Installer(),          # 3
    PtyxisInstaller(),        # 4
    FastfetchInstaller(),     # 5
    BurnMyWindowsInstaller(), # 6
    WallpaperInstaller(),     # 7
    FontsInstaller(),         # 8
    PapirusInstaller(),       # 9
    BibataInstaller(),        # 10
    GnomeExtensionsInstaller(), # 11
    DconfSettingsInstaller(),   # 12
    FlatpakOverridesInstaller(), # 13
    FlatpakSymlinksInstaller(),  # 14
    FirefoxInstaller(),          # 15
    GdmInstaller(),              # 16
    DingFixInstaller(),          # 17
    RefindInstaller(),           # 18
    RefindThemeInstaller(),      # 19
]


# ─── ThemeInstaller (Main Orchestrator) ──────────────────────────────────────

class ThemeInstaller:
    """Main TUI orchestrator for the theme installation."""

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.sys_info: Optional[SystemInfo] = None
        self.backup: Optional[BackupManager] = None
        self.results: list[ComponentResult] = []

    def run(self) -> int:
        """Main entry point. Returns exit code."""
        print_banner()

        # Handle uninstall mode
        if self.args.uninstall:
            return self._run_uninstall()

        # Handle refresh-symlinks mode
        if self.args.refresh_symlinks:
            return self._run_refresh_symlinks()

        # Detect system
        detector = SystemDetector()
        self.sys_info = detector.detect()
        detector.print_info(self.sys_info)

        # Check GNOME version
        if self.sys_info.gnome_version:
            major = int(self.sys_info.gnome_version.split(".")[0])
            if major < 45:
                console.print("[warning]Warning: This theme is designed for GNOME 45+. "
                              f"You have GNOME {self.sys_info.gnome_version}.[/]")
                if not self.args.non_interactive:
                    if not Confirm.ask("Continue anyway?", default=False):
                        return 0

        # Select components
        steps = self._select_components()
        if not steps:
            console.print("[muted]No components selected. Exiting.[/]")
            return 0

        # Confirm
        if not self.args.non_interactive and not self.args.dry_run:
            self._show_selection(steps)
            if not Confirm.ask("\n[accent]Proceed with installation?[/]", default=True):
                console.print("[muted]Cancelled.[/]")
                return 0

        # Initialize backup
        if not self.args.no_backup:
            self.backup = BackupManager(dry_run=self.args.dry_run)
            self.backup.init()
            if not self.args.dry_run:
                console.print(f"[info]Backup directory:[/] {self.backup.backup_dir}\n")
        else:
            self.backup = BackupManager(dry_run=True)  # no-op backup

        # Install
        self._install_steps(steps)

        # Save manifest
        if not self.args.no_backup:
            self.backup.save_manifest()

        # Show results
        self._show_results()

        return 0 if all(r.status in (Status.SUCCESS, Status.SKIPPED) for r in self.results) else 1

    def _select_components(self) -> list[InstallerStep]:
        """Select which components to install."""
        # If specific components requested
        if self.args.components:
            nums = set()
            for part in self.args.components.split(","):
                part = part.strip()
                if "-" in part:
                    start, end = part.split("-", 1)
                    nums.update(range(int(start), int(end) + 1))
                else:
                    nums.add(int(part))
            return [s for s in ALL_STEPS if s.number in nums]

        # Non-interactive: all components
        if self.args.non_interactive:
            return list(ALL_STEPS)

        # Interactive checklist
        return self._interactive_select()

    def _interactive_select(self) -> list[InstallerStep]:
        """Show interactive component selection."""
        console.print(Panel(
            "[accent]Select components to install[/]\n"
            "[muted]Enter component numbers separated by commas, ranges (1-7), or 'all'[/]",
            border_style="accent"
        ))
        console.print()

        table = Table(box=box.SIMPLE, padding=(0, 2), show_header=True, header_style="bold")
        table.add_column("#", style="accent", width=3)
        table.add_column("Component", style="bold")
        table.add_column("Sudo", style="muted", width=6)

        for step in ALL_STEPS:
            sudo_mark = "[warning]Yes[/]" if step.requires_sudo else "No"
            table.add_row(str(step.number), step.name, sudo_mark)

        console.print(table)
        console.print()

        while True:
            answer = Prompt.ask(
                "[accent]Components[/]",
                default="all"
            ).strip().lower()

            if answer in ("all", "a", "*"):
                return list(ALL_STEPS)

            if answer in ("q", "quit", "exit", "none"):
                return []

            try:
                nums = set()
                for part in answer.split(","):
                    part = part.strip()
                    if "-" in part:
                        start, end = part.split("-", 1)
                        nums.update(range(int(start), int(end) + 1))
                    else:
                        nums.add(int(part))
                selected = [s for s in ALL_STEPS if s.number in nums]
                if selected:
                    return selected
                console.print("[error]No valid components selected.[/]")
            except ValueError:
                console.print("[error]Invalid input. Use numbers, ranges (1-7), 'all', or 'quit'.[/]")

    def _show_selection(self, steps: list[InstallerStep]) -> None:
        """Display selected components."""
        console.print(Panel(
            "\n".join(f"  [accent]{s.number:2d}.[/] {s.name}" for s in steps),
            title="[accent]Selected Components[/]",
            border_style="accent"
        ))

    def _install_steps(self, steps: list[InstallerStep]) -> None:
        """Install all selected steps with progress display."""
        console.print()
        prefix = "[muted]DRY RUN:[/] " if self.args.dry_run else ""

        with Progress(
            SpinnerColumn(style="accent"),
            TextColumn("[bold]{task.description}"),
            BarColumn(complete_style="accent", finished_style="success"),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            overall = progress.add_task(f"{prefix}Installing theme", total=len(steps))

            for step in steps:
                progress.update(overall, description=f"{prefix}[{step.number}/{len(ALL_STEPS)}] {step.name}")

                result = self._install_single(step)
                self.results.append(result)

                # Show inline result
                icon = {
                    Status.SUCCESS: "[success]✓[/]",
                    Status.SKIPPED: "[warning]○[/]",
                    Status.FAILED: "[error]✗[/]",
                }[result.status]
                progress.console.print(f"  {icon} {step.name}: {result.message}")

                progress.advance(overall)

    def _install_single(self, step: InstallerStep) -> ComponentResult:
        """Install a single step with error handling."""
        try:
            result = step.install(self.sys_info, self.backup, self.args.dry_run)
            return result
        except KeyboardInterrupt:
            return ComponentResult(step.number, step.name, Status.FAILED, "Interrupted")
        except Exception as e:
            if self.args.non_interactive:
                return ComponentResult(step.number, step.name, Status.FAILED, str(e))

            # Interactive error handling
            console.print(f"\n  [error]Error in {step.name}: {e}[/]")
            while True:
                choice = Prompt.ask(
                    "  [R]etry / [S]kip / [A]bort",
                    choices=["r", "s", "a"],
                    default="s"
                ).lower()
                if choice == "r":
                    try:
                        return step.install(self.sys_info, self.backup, self.args.dry_run)
                    except Exception as e2:
                        console.print(f"  [error]Retry failed: {e2}[/]")
                        continue
                elif choice == "s":
                    return ComponentResult(step.number, step.name, Status.SKIPPED, "Skipped by user")
                else:  # abort
                    raise KeyboardInterrupt("Aborted by user")

    def _show_results(self) -> None:
        """Show final results table."""
        console.print()
        table = Table(
            title="Installation Results",
            box=box.ROUNDED,
            border_style="accent",
            title_style="bold accent",
        )
        table.add_column("#", style="muted", width=3)
        table.add_column("Component", style="bold")
        table.add_column("Status", width=10)
        table.add_column("Details", style="muted")

        for r in self.results:
            status_style = {
                Status.SUCCESS: "[success]SUCCESS[/]",
                Status.SKIPPED: "[warning]SKIPPED[/]",
                Status.FAILED: "[error]FAILED[/]",
                Status.PENDING: "[muted]PENDING[/]",
            }[r.status]
            table.add_row(str(r.number), r.name, status_style, r.message)

        console.print(table)

        # Summary
        success = sum(1 for r in self.results if r.status == Status.SUCCESS)
        skipped = sum(1 for r in self.results if r.status == Status.SKIPPED)
        failed = sum(1 for r in self.results if r.status == Status.FAILED)

        console.print()
        if failed == 0:
            console.print("[success]All components installed successfully![/]")
        else:
            console.print(f"[info]{success} succeeded[/], [warning]{skipped} skipped[/], [error]{failed} failed[/]")

        if not self.args.dry_run and self.backup and not self.args.no_backup:
            console.print(f"\n[muted]Backup saved to: {self.backup.backup_dir}[/]")
            console.print("[muted]To restore: python3 material-you-installer.py --uninstall[/]")

        # Hint about logout
        if not self.args.dry_run and any(r.status == Status.SUCCESS for r in self.results):
            console.print("\n[warning]Note:[/] Some changes require logging out and back in to take effect.")

    def _run_uninstall(self) -> int:
        """Handle uninstall mode."""
        backups = BackupManager.list_backups()
        if not backups:
            console.print("[error]No backups found.[/]")
            return 1

        console.print(Panel("[accent]Available Backups[/]", border_style="accent"))
        for i, b in enumerate(backups, 1):
            ts = b.name
            manifest = json.loads((b / "manifest.json").read_text())
            n_files = len(manifest.get("files", []))
            n_dconf = len(manifest.get("dconf", []))
            console.print(f"  [accent]{i}.[/] {ts} ({n_files} files, {n_dconf} dconf paths)")

        console.print()
        choice = Prompt.ask("Select backup to restore", default="1")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(backups):
                if BackupManager.restore(backups[idx]):
                    console.print("\n[success]Restore complete![/]")
                    console.print("[warning]Note:[/] Log out and back in for all changes to take effect.")
                    return 0
                return 1
            console.print("[error]Invalid selection.[/]")
            return 1
        except (ValueError, IndexError):
            console.print("[error]Invalid selection.[/]")
            return 1

    def _run_refresh_symlinks(self) -> int:
        """Refresh Flatpak GTK symlinks for new apps."""
        detector = SystemDetector()
        self.sys_info = detector.detect()

        if not self.sys_info.has_flatpak:
            console.print("[error]Flatpak not available.[/]")
            return 1

        step = FlatpakSymlinksInstaller()
        backup = BackupManager(dry_run=True)  # no-op
        result = step.install(self.sys_info, backup, dry_run=False)
        console.print(f"[info]{result.message}[/]")
        return 0


# ─── Argument Parser ─────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Material You Orange Dark Theme Installer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              %(prog)s                          Interactive full install
              %(prog)s --dry-run                Show what would be done
              %(prog)s --components 1-7         Install only file-copy steps
              %(prog)s --components 8,9,10      Install only fonts/icons/cursor
              %(prog)s --non-interactive        Install everything without prompts
              %(prog)s --uninstall              Restore from backup
              %(prog)s --refresh-symlinks       Update Flatpak symlinks for new apps
        """),
    )
    parser.add_argument("--uninstall", action="store_true",
                        help="Restore from a previous backup")
    parser.add_argument("--non-interactive", action="store_true",
                        help="Install all components without prompts")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be done without making changes")
    parser.add_argument("--components",
                        help="Comma-separated list of component numbers (e.g. 1,2,3 or 1-7)")
    parser.add_argument("--no-backup", action="store_true",
                        help="Skip backup (not recommended)")
    parser.add_argument("--refresh-symlinks", action="store_true",
                        help="Recreate Flatpak GTK symlinks for new apps")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    return parser


# ─── Main ────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        installer = ThemeInstaller(args)
        return installer.run()
    except KeyboardInterrupt:
        console.print("\n[warning]Interrupted.[/]")
        return 130


if __name__ == "__main__":
    sys.exit(main())
