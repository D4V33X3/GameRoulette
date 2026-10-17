import json, math, random, re, threading, time, tkinter as tk, os, glob
from html.parser import HTMLParser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk, colorchooser, simpledialog
from urllib.parse import quote, unquote
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = ImageTk = None

EXTS = {".iso",".bin",".cue",".chd",".cso",".pbp",".gcm",".gcz",".rvz",".wad",".wbfs",".wud",".nsp",".xci",".3ds",".cia",".nds",".gba",".gbc",".gb",".z64",".n64",".v64",".nes",".sfc",".smc",".md",".gen",".sms",".gg",".a26",".a78",".zip",".7z",".rar",".elf",".dol",".pkg"}
IMG = {".png",".jpg",".jpeg",".webp",".bmp",".gif"}
BASE = "https://thumbnails.libretro.com"
PS2_COVER_URL = "https://raw.githubusercontent.com/xlenore/ps2-covers/main/covers/3d/{serial}.png"
PS2_CACHE_PATHS = [Path(r"G:\PCSX2\cache\gamelist.cache"), Path(__file__).with_name("gamelist.cache")]
SYSTEMS = [
 "Auto-detect (best effort)", "Sony - PlayStation 2", "Sony - PlayStation",
 "Sony - PlayStation Portable", "Nintendo - GameCube", "Nintendo - Wii",
 "Nintendo - Nintendo 64", "Nintendo - Nintendo DS", "Nintendo - Game Boy Advance",
 "Nintendo - Game Boy Color", "Nintendo - Game Boy", "Nintendo - Nintendo Entertainment System",
 "Nintendo - Super Nintendo Entertainment System", "Nintendo - Nintendo 3DS",
 "Sega - Mega Drive - Genesis", "Sega - Saturn", "Sega - Dreamcast", "Microsoft - Xbox", "Atari - 2600"
]
AUTO = {".cso":"Sony - PlayStation Portable",".pbp":"Sony - PlayStation Portable",
 ".gcm":"Nintendo - GameCube",".gcz":"Nintendo - GameCube",".rvz":"Nintendo - Wii",
 ".wbfs":"Nintendo - Wii",".nds":"Nintendo - Nintendo DS",".gba":"Nintendo - Game Boy Advance",
 ".gbc":"Nintendo - Game Boy Color",".gb":"Nintendo - Game Boy",".z64":"Nintendo - Nintendo 64",
 ".n64":"Nintendo - Nintendo 64",".v64":"Nintendo - Nintendo 64",".nes":"Nintendo - Nintendo Entertainment System",
 ".sfc":"Nintendo - Super Nintendo Entertainment System",".smc":"Nintendo - Super Nintendo Entertainment System",
 ".md":"Sega - Mega Drive - Genesis",".gen":"Sega - Mega Drive - Genesis",".3ds":"Nintendo - Nintendo 3DS"}

def norm(s):
    s = Path(s).stem
    s = re.sub(r"(?i)[\s._-]*(disc|disk|cd)[\s._-]*[0-9]+$", "", s)
    return re.sub(r"[^a-z0-9]", "", s.casefold())


def load_ps2_serial_database():
    """Parse PCSX2 GLCE cache entries into normalized ROM-name -> serial mappings."""
    db = {}
    pattern = re.compile(rb"([^\x00\r\n]+\.(?:iso|bin|chd|cue|elf|cso|gz))\n\x00{3}([A-Z]{4}-\d{5})", re.I)
    for cache_path in PS2_CACHE_PATHS:
        try:
            data = cache_path.read_bytes()
        except OSError:
            continue
        for raw_path, raw_serial in pattern.findall(data):
            path_text = raw_path.decode("utf-8", "ignore")
            serial = raw_serial.decode("ascii", "ignore").upper()
            name = Path(path_text.replace("\\", "/")).name
            db.setdefault(norm(name), serial)
            db.setdefault(norm(Path(name).stem), serial)
        if db:
            break
    return db

def base_norm(s):
    return norm(re.sub(r"\s*[\(\[].*$", "", Path(s).stem))

class Game:
    def __init__(self, path, title=None, source="ROM"):
        self.path = Path(path); self._title = title; self.source = source
    @property
    def title(self):
        if self._title: return self._title
        s = re.sub(r"(?i)[\s._-]*(disc|disk|cd)[\s._-]*[0-9]+$", "", self.path.stem)
        return re.sub(r"\s+", " ", s.replace("_"," ").replace("."," ")).strip() or self.path.stem

def scan_games(folders):
    """Scan ROMs and treat a CUE/BIN pair as one disc/game.

    When a .cue file and one or more .bin files share the same directory and
    stem, keep the .cue entry and skip the matching .bin file(s). Standalone
    BIN files remain eligible games.
    """
    paths = {}
    for folder in folders:
        try:
            for p in Path(folder).rglob("*"):
                if p.is_file() and p.suffix.casefold() in EXTS:
                    resolved = p.resolve()
                    paths[str(resolved).casefold()] = resolved
        except (OSError, PermissionError):
            pass

    cue_stems = {
        (p.parent.as_posix().casefold(), p.stem.casefold())
        for p in paths.values() if p.suffix.casefold() == ".cue"
    }
    found = {}
    for p in paths.values():
        if p.suffix.casefold() == ".bin" and (p.parent.as_posix().casefold(), p.stem.casefold()) in cue_stems:
            continue
        found[str(p).casefold()] = Game(p)
    return sorted(found.values(), key=lambda g: g.title.casefold())

def launcher_games(selected):
    """Find installed games from selected launchers only; never runs automatically."""
    found=[]; home=Path.home(); local=Path(os.environ.get("LOCALAPPDATA", home/"AppData"/"Local")); program=Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData"))
    def add(title, path, source):
        title=(title or "").strip()
        if title and path and title.casefold() not in {g.title.casefold() for g in found}:
            found.append(Game(path, title=title, source=source))
    # Steam: installed appmanifest files in each configured Steam library.
    if "Steam" in selected:
        roots=[]
        for candidate in [Path(r"C:\Program Files (x86)\Steam"),Path(r"C:\Program Files\Steam"),Path(os.environ.get("ProgramFiles(x86)",r"C:\Program Files (x86)"))/"Steam"]:
            if candidate.exists() and candidate not in roots: roots.append(candidate)
        for root in list(roots):
            vdf=root/"steamapps"/"libraryfolders.vdf"
            try:
                text=vdf.read_text(encoding="utf-8",errors="ignore")
                for lib in re.findall(r'"path"\s*"([^"]+)"',text):
                    q=Path(lib.replace("\\\\","\\"))
                    if q.exists() and q not in roots: roots.append(q)
            except OSError: pass
        for root in roots:
            for mf in (root/"steamapps").glob("appmanifest_*.acf"):
                try:
                    txt=mf.read_text(encoding="utf-8",errors="ignore")
                    name=re.search(r'"name"\s*"([^"]+)"',txt)
                    if name: add(name.group(1),mf,"Steam")
                except OSError: pass
    # Epic Games: installed manifests in Epic's Launcher data folder.
    if "Epic Games" in selected:
        manifests=local/"EpicGamesLauncher"/"Data"/"Manifests"
        if manifests.exists():
            for mf in manifests.glob("*.item"):
                try:
                    data=json.loads(mf.read_text(encoding="utf-8")); title=data.get("DisplayName")
                    if title and data.get("InstallLocation"): add(title, data.get("LaunchExecutable") and (Path(data["InstallLocation"])/data["LaunchExecutable"]) or mf,"Epic Games")
                except (OSError,ValueError): pass
    # GOG Galaxy: installed game folders are often represented by Start Menu shortcuts.
    shortcut_roots=[program/"Microsoft"/"Windows"/"Start Menu"/"Programs",local/"Microsoft"/"Windows"/"Start Menu"/"Programs",home/"Desktop"]
    if "GOG Galaxy" in selected or "Ubisoft Connect" in selected or "EA app" in selected or "Xbox app" in selected:
        wanted={"GOG Galaxy":"GOG.com","Ubisoft Connect":"Ubisoft","EA app":"EA Games","Xbox app":"Xbox Games"}
        for root in shortcut_roots:
            for lnk in root.rglob("*.lnk") if root.exists() else []:
                low=str(lnk).casefold()
                for launcher, marker in wanted.items():
                    if launcher in selected and marker.casefold() in low:
                        add(lnk.stem,lnk,launcher)
    return sorted(found,key=lambda g:g.title.casefold())

def steam_owned_games(api_key, steam_id):
    """Fetch games from a public Steam profile using the official Steam Web API."""
    from urllib.parse import urlencode
    query = urlencode({
        "key": api_key.strip(),
        "steamid": steam_id.strip(),
        "include_appinfo": 1,
        "include_played_free_games": 1,
        "format": "json",
    })
    url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?" + query
    req = Request(url, headers={"User-Agent": "GameRoulette/1.0"})
    with urlopen(req, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    games = payload.get("response", {}).get("games", [])
    if not games:
        raise ValueError("Steam returned no games. Make sure the profile's Game details privacy is Public and the Steam ID/API key are correct.")
    return [Game(Path("Steam library (not installed)"), title=item.get("name", "").strip(), source="Steam library (not installed)")
            for item in games if item.get("name", "").strip()]


def local_covers(folder):
    out = {}
    if not folder: return out
    try:
        for p in sorted(Path(folder).rglob("*"), key=lambda p:str(p).casefold()):
            if p.is_file() and p.suffix.casefold() in IMG: out.setdefault(norm(p.name), p)
    except (OSError, PermissionError): pass
    return out

def serial_keys(text):
    """Return normalized PS2 serial variants found in a filename or title."""
    stem = Path(text).stem.upper()
    found = []
    # Common PS2 serials: SLUS-12345, SLES_123.45, SCUS-97490, etc.
    for m in re.finditer(r"\b(SLUS|SLES|SCUS|SCES|SLPS|SCAJ|SLPM|SLAJ|SCPS|PAPX|PCPX|TCPS|TCUS)[-_ ]?([0-9]{3})[-_. ]?([0-9]{2,3})\b", stem):
        prefix, a, b = m.groups()
        digits = a + b
        found.extend([prefix + digits, prefix + "-" + digits, prefix + "_" + digits])
    return list(dict.fromkeys(norm(x) for x in found))

def find_cover(game, covers):
    # Prefer exact serial matches, then exact title matches only. Fuzzy matching
    # is deliberately avoided here so unrelated games never share a cover.
    for key in serial_keys(game.path.name) + serial_keys(game.title):
        if key in covers: return covers[key]
    for k in (norm(game.path.name), norm(game.title), base_norm(game.title)):
        if k in covers: return covers[k]
    return None

class Links(HTMLParser):
    def __init__(self): super().__init__(); self.items=[]
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            h=dict(attrs).get("href")
            if h: self.items.append(unquote(h.rsplit("/",1)[-1]))

class CoverDownloader:
    def __init__(self):
        self.cache = Path.home()/".rom_roulette"/"online_covers"
        self.listings={}
        self.ps2_serials=load_ps2_serial_database()
    def get(self,url):
        req=Request(url,headers={"User-Agent":"ROM-Roulette/0.2"})
        with urlopen(req,timeout=8) as r: return r.read()
    def download_launcher_cover(self, game):
        """Best-effort cover lookup for imported PC launcher titles.

        Uses the public Steam Store search endpoint to resolve a title to an
        app ID, then downloads Steam's portrait library artwork. Results are
        cached locally and no launcher account credentials are accessed.
        """
        folder = self.cache / "launcher_games"
        folder.mkdir(parents=True, exist_ok=True)
        key = norm(game.title)
        cached = folder / (key + ".jpg")
        if cached.exists() and cached.stat().st_size > 1000:
            return cached
        try:
            from urllib.parse import urlencode
            search_url = "https://store.steampowered.com/api/storesearch/?" + urlencode({"term": game.title, "l": "english", "cc": "GB"})
            payload = json.loads(self.get(search_url).decode("utf-8", "replace"))
            items = payload.get("items", [])
            wanted = norm(game.title)
            exact = [it for it in items if norm(it.get("name", "")) == wanted]
            # Only accept exact normalized title matches to avoid assigning an
            # unrelated game's artwork to another launcher entry.
            match = exact[0] if exact else None
            if not match:
                return None
            appid = int(match["id"])
            urls = [f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/library_600x900.jpg",
                    f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/header.jpg"]
            for url in urls:
                try:
                    data = self.get(url)
                    if len(data) > 1000 and data[:3] == b"\xff\xd8\xff":
                        cached.write_bytes(data)
                        return cached
                    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) > 1000:
                        png = folder / (key + ".png")
                        png.write_bytes(data)
                        return png
                except Exception:
                    continue
        except Exception:
            return None
        return None

    def download(self,game,system):
        if not system: return None
        # PS2 artwork must be looked up by the serial from PCSX2's gamelist.cache,
        # not by fuzzy title matching. This avoids duplicated wrong covers.
        if system == "Sony - PlayStation 2":
            serial = None
            for key in (norm(game.path.name), norm(game.title), norm(game.path.stem)):
                if key in self.ps2_serials:
                    serial = self.ps2_serials[key]; break
            if serial:
                folder=self.cache/"xlenore_ps2_3d"
                folder.mkdir(parents=True,exist_ok=True)
                cached=folder/(serial+".png")
                if cached.exists() and cached.stat().st_size > 100: return cached
                try:
                    data=self.get(PS2_COVER_URL.format(serial=quote(serial,safe="")))
                    if data.startswith(b"\x89PNG\r\n\x1a\n"):
                        cached.write_bytes(data); return cached
                except Exception:
                    pass
        folder=self.cache/re.sub(r"[^a-zA-Z0-9_-]+","_",system)
        folder.mkdir(parents=True,exist_ok=True)
        for p in folder.glob("*.png"):
            if norm(p.name) in {norm(game.path.name),norm(game.title),base_norm(game.title)}: return p
        try:
            if system not in self.listings:
                url=f"{BASE}/{quote(system,safe='')}/Named_Boxarts/"
                parser=Links(); parser.feed(self.get(url).decode("utf8","replace"))
                self.listings[system]=[x for x in parser.items if x.lower().endswith(".png")]
            names=self.listings[system]
        except Exception: return None
        keys={norm(n):n for n in names}
        match=keys.get(norm(game.path.name)) or keys.get(norm(game.title)) or keys.get(base_norm(game.title))
        if not match:
            options=[n for n in names if base_norm(n)==base_norm(game.title)]
            if len(options)==1: match=options[0]
        if not match: return None
        try:
            data=self.get(f"{BASE}/{quote(system,safe='')}/Named_Boxarts/{quote(match,safe='')}")
            if not data.startswith(b"\x89PNG\r\n\x1a\n"): return None
            p=folder/match; p.write_bytes(data); return p
        except Exception: return None


from PySide6.QtCore import Qt, QTimer, QRectF, QPointF, Signal, QObject
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QFont, QPixmap, QRadialGradient, QIcon
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton,
    QListWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFileDialog, QComboBox, QColorDialog,
    QSlider, QDialog, QDialogButtonBox, QProgressBar, QMessageBox, QGraphicsDropShadowEffect, QStyle, QSizePolicy, QCheckBox, QLineEdit)
import sys

class Signals(QObject):
    status = Signal(str)
    finished = Signal(int, int)

class Wheel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.games=[]; self.covers={}; self.angle=0; self.glow='#36c5ff'; self.winner_index=-1
        self.setMinimumSize(480,480); self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    def paintEvent(self, event):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing); p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        side=min(self.width(),self.height())-40; r=side/2; cx=self.width()/2; cy=self.height()/2; rect=QRectF(cx-r,cy-r,2*r,2*r)
        glow=QColor(self.glow); glow.setAlpha(210)
        p.setPen(QPen(glow,3)); p.setBrush(QColor(19,31,52,230)); p.drawEllipse(rect)
        if not self.games:
            p.setPen(QColor('#f3f7ff')); p.setFont(QFont('Segoe UI',16,QFont.Weight.Bold)); p.drawText(rect,Qt.AlignmentFlag.AlignCenter,'ADD ROM FOLDERS'); return
        step=360/len(self.games); colors=['#174d7a','#17335c','#12616b','#354278','#5c3d70','#205c56','#4b4f70','#6c4c32']
        for i,g in enumerate(self.games):
            start=90-(i+1)*step+self.angle
            p.setPen(QPen(QColor(5,10,22),2)); p.setBrush(QColor(colors[i%len(colors)])); p.drawPie(rect,int(start*16),int(step*16))
            mid=math.radians(start+step/2); rr=r*.68; x=cx+math.cos(mid)*rr; y=cy-math.sin(mid)*rr
            cp=find_cover(g,self.covers)
            if cp:
                pix=QPixmap(str(cp))
                if not pix.isNull():
                    tw=max(18,min(58,int(2*r*math.sin(math.radians(min(step,45))/2)*.8))); th=max(24,min(76,int(tw*1.3)))
                    pix=pix.scaled(tw,th,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
                    p.drawPixmap(int(x-pix.width()/2),int(y-pix.height()/2),pix); continue
            label=g.title; maxc=max(5,min(13,int(32/max(step,1))))
            if len(label)>maxc: label=label[:maxc-1]+'…'
            p.setPen(QColor('#eef6ff')); p.setFont(QFont('Segoe UI',max(7,min(10,int(step/3))),QFont.Weight.Bold)); p.drawText(QRectF(x-35,y-15,70,30),Qt.AlignmentFlag.AlignCenter,label)
        # center cap and pointer
        p.setPen(QPen(QColor(self.glow),4)); p.setBrush(QColor(7,13,27,245)); p.drawEllipse(QPointF(cx,cy),r*.16,r*.16)
        p.setPen(QColor('#ffd166')); p.setFont(QFont('Segoe UI',13,QFont.Weight.Black)); p.drawText(QRectF(cx-r*.16,cy-r*.1,2*r*.16,2*r*.1),Qt.AlignmentFlag.AlignCenter,'SPIN')
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor('#ffd166')); p.drawPolygon([QPointF(cx-17,cy-r-19),QPointF(cx+17,cy-r-19),QPointF(cx,cy-r+17)])

class GlassDialog(QDialog):
    def __init__(self,color,strength,parent=None):
        super().__init__(parent); self.setWindowTitle('Glass & Glow'); self.setModal(True); self.color=color; self.strength=strength
        self.setStyleSheet('QDialog{background:#0b1222;color:#eef5ff;} QLabel{color:#eef5ff;} QPushButton{background:#1a2b45;color:#eef5ff;border:1px solid #405675;border-radius:8px;padding:8px;}')
        l=QVBoxLayout(self); l.addWidget(QLabel('Choose your accent glow colour'))
        self.pick=QPushButton('Choose colour  '+color); self.pick.clicked.connect(self.choose); l.addWidget(self.pick)
        l.addWidget(QLabel('Glow intensity'))
        self.slider=QSlider(Qt.Orientation.Horizontal); self.slider.setRange(1,5); self.slider.setValue(strength); l.addWidget(self.slider)
        self.preview=QLabel('LIVE STYLE PREVIEW'); self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter); self.preview.setMinimumHeight(70); l.addWidget(self.preview)
        self.slider.valueChanged.connect(self.update_preview); self.update_preview()
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel); buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); l.addWidget(buttons)
    def choose(self):
        c=QColorDialog.getColor(QColor(self.color),self,'Glow colour')
        if c.isValid(): self.color=c.name(); self.pick.setText('Choose colour  '+self.color); self.update_preview()
    def update_preview(self): self.preview.setStyleSheet(f'background:rgba(28,47,72,190);border: {self.slider.value()}px solid {self.color};border-radius:14px;padding:12px;')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle('Game Roulette'); self.setWindowIcon(QIcon(str(Path(__file__).with_name('game_roulette_icon.png')))); self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window); self.resize(1400,900); self.setMinimumSize(1050,700); self._drag_pos=None
        self.settings_path=Path.home()/'.rom_roulette'/'settings.json'; self.glow_color='#36c5ff'; self.glow_strength=3; self.theme_name='Midnight Glass'
        try:
            cfg=json.loads(self.settings_path.read_text()); self.glow_color=cfg.get('glow_color',self.glow_color); self.glow_strength=int(cfg.get('glow_strength',3)); self.theme_name=cfg.get('theme_name','Midnight Glass')
        except Exception: pass
        self.folders=[]; self.coverfolder=None; self.pcsx2folder=Path(r'G:\PCSX2\covers'); self.games=[]; self.covers={}; self.winner=None; self.busy=False; self.angle=0; self.downloader=CoverDownloader(); self.signals=Signals(); self.signals.status.connect(self.set_status); self.signals.finished.connect(self.finish_download)
        self.build(); self.apply_theme()
    def toggle_maximize(self):
        if self.isMaximized(): self.showNormal(); self.maxbtn.setText('□')
        else: self.showMaximized(); self.maxbtn.setText('❐')
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() <= 44 and not self.isMaximized():
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft(); event.accept(); return
        super().mousePressEvent(event)
    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton and not self.isMaximized():
            self.move(event.globalPosition().toPoint() - self._drag_pos); event.accept(); return
        super().mouseMoveEvent(event)
    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)
    def panel(self):
        f=QFrame(); f.setObjectName('glassPanel'); f.setFrameShape(QFrame.Shape.NoFrame); return f
    def build(self):
        root=QWidget(); root.setObjectName('root'); self.setCentralWidget(root); outer=QVBoxLayout(root); outer.setContentsMargins(1,1,1,1); outer.setSpacing(0)
        titlebar=QFrame(); titlebar.setObjectName('titleBar'); titlebar.setFixedHeight(42); tb=QHBoxLayout(titlebar); tb.setContentsMargins(14,0,8,0); tb.setSpacing(8)
        appmark=QLabel('◈'); appmark.setObjectName('titleMark'); tb.addWidget(appmark); wintitle=QLabel('GAME ROULETTE  /  GLASS EDITION'); wintitle.setObjectName('windowTitle'); tb.addWidget(wintitle); tb.addStretch()
        self.minbtn=QPushButton('—'); self.minbtn.setObjectName('windowControl'); self.minbtn.setFixedSize(42,30); self.minbtn.clicked.connect(self.showMinimized); tb.addWidget(self.minbtn)
        self.maxbtn=QPushButton('□'); self.maxbtn.setObjectName('windowControl'); self.maxbtn.setFixedSize(42,30); self.maxbtn.clicked.connect(self.toggle_maximize); tb.addWidget(self.maxbtn)
        self.closebtn=QPushButton('×'); self.closebtn.setObjectName('windowClose'); self.closebtn.setFixedSize(42,30); self.closebtn.clicked.connect(self.close); tb.addWidget(self.closebtn); outer.addWidget(titlebar)
        contentroot=QWidget(); contentroot.setObjectName('contentRoot'); outer.addWidget(contentroot,1); outer=QVBoxLayout(contentroot); outer.setContentsMargins(25,20,25,16); outer.setSpacing(15)
        header=QHBoxLayout(); brand=QVBoxLayout(); title=QLabel('GAME ROULETTE'); title.setObjectName('hero'); brand.addWidget(title); sub=QLabel('YOUR LIBRARY. ONE SPIN. ONTO THE NEXT ADVENTURE.'); sub.setObjectName('subtitle'); brand.addWidget(sub); header.addLayout(brand); header.addStretch(); outer.addLayout(header)
        toolbar=self.panel(); row=QHBoxLayout(toolbar); row.setContentsMargins(14,12,14,12); row.setSpacing(9)
        for text,fn in [('＋ Add ROM Folder',self.add_folder),('Import Launcher Games…',self.import_launchers),('Choose Local Covers',self.choose_covers),('Scan Library',self.scan)]:
            b=QPushButton(text); b.clicked.connect(fn); row.addWidget(b)
        row.addWidget(QLabel('Theme:')); self.theme=QComboBox(); self.theme.addItems(['Midnight Glass','Arctic Glass','Emerald Glass','Violet Glass','Sunset Glass','Rose Gold']); self.theme.setCurrentText(self.theme_name); self.theme.currentTextChanged.connect(self.change_theme); row.addWidget(self.theme); row.addWidget(QLabel('Online system:')); self.system=QComboBox(); self.system.addItems(SYSTEMS); row.addWidget(self.system,1); outer.addWidget(toolbar)
        self.status=QLabel('Choose ROM folders, then scan. Online covers need an internet connection.'); self.status.setObjectName('status'); outer.addWidget(self.status)
        content=QHBoxLayout(); content.setSpacing(16); outer.addLayout(content,1)
        wheelpanel=self.panel(); wl=QVBoxLayout(wheelpanel); wh=QLabel('✦  THE GAME WHEEL  ✦'); wh.setObjectName('sectionTitle'); wh.setAlignment(Qt.AlignmentFlag.AlignCenter); wl.addWidget(wh); self.wheel=Wheel(); wl.addWidget(self.wheel,1); content.addWidget(wheelpanel,7)
        side=QVBoxLayout(); content.addLayout(side,3)
        winner=self.panel(); v=QVBoxLayout(winner); v.addWidget(QLabel('YOUR NEXT GAME',objectName='sectionTitle'))
        self.cover=QLabel('COVER ART'); self.cover.setObjectName('cover'); self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter); self.cover.setMinimumHeight(190); v.addWidget(self.cover)
        self.wtitle=QLabel('Spin to pick a game'); self.wtitle.setWordWrap(True); self.wtitle.setObjectName('winnerTitle'); v.addWidget(self.wtitle)
        self.wpath=QLabel('Winner appears here'); self.wpath.setWordWrap(True); self.wpath.setObjectName('muted'); v.addWidget(self.wpath)
        self.spinbtn=QPushButton('▶  SPIN THE WHEEL'); self.spinbtn.setObjectName('spin'); self.spinbtn.clicked.connect(self.spin); v.addWidget(self.spinbtn); self.showbtn=QPushButton('Show Game File Location'); self.showbtn.setEnabled(False); self.showbtn.clicked.connect(self.show_location); v.addWidget(self.showbtn); side.addWidget(winner)
        lib=self.panel(); lv=QVBoxLayout(lib); lv.addWidget(QLabel('YOUR GAME LIBRARY',objectName='sectionTitle')); self.list=QListWidget(); self.list.currentRowChanged.connect(self.select_game); lv.addWidget(self.list,1); self.removebtn=QPushButton('✕ Remove Selected Game'); self.removebtn.setEnabled(False); self.removebtn.clicked.connect(self.remove_selected_game); lv.addWidget(self.removebtn); self.removeallbtn=QPushButton('⌫ Remove All Games'); self.removeallbtn.setEnabled(False); self.removeallbtn.clicked.connect(self.remove_all_games); lv.addWidget(self.removeallbtn); side.addWidget(lib,1)
        foot=QLabel('LOCAL + ONLINE BOX ART   •   CUE/BIN PAIR DEDUPLICATION   •   YOU LAUNCH THE WINNER'); foot.setAlignment(Qt.AlignmentFlag.AlignCenter); foot.setObjectName('footer'); outer.addWidget(foot)
    def change_theme(self, name):
        presets={'Midnight Glass':'#36c5ff','Arctic Glass':'#8deaff','Emerald Glass':'#35e6a1','Violet Glass':'#b58aff','Sunset Glass':'#ff9a62','Rose Gold':'#ff7eb6'}
        self.theme_name=name
        # Theme presets set the accent; the custom glow picker can still override it.
        self.glow_color=presets.get(name, self.glow_color)
        self.apply_theme()
        try:
            self.settings_path.parent.mkdir(parents=True,exist_ok=True); self.settings_path.write_text(json.dumps({'glow_color':self.glow_color,'glow_strength':self.glow_strength,'theme_name':self.theme_name},indent=2))
        except OSError: pass
        self.set_status(f'Theme changed to {name}.')
    def apply_theme(self):
        c=self.glow_color; strength=self.glow_strength
        # translucent alpha surfaces and soft halo via Qt drop shadows; true acrylic blur is OS-managed and optional.
        self.setStyleSheet(f"""
        QMainWindow{{background:transparent;color:#eef5ff;font-family:'Segoe UI';font-size:10pt;}} QWidget#root{{background:rgba(7,13,25,246);border:1px solid rgba(220,240,255,100);border-radius:16px;}} QWidget#contentRoot{{background:qradialgradient(cx:0.2,cy:0.0,radius:1.2,fx:0.2,fy:0.0,stop:0 rgba(28,48,76,248),stop:0.55 rgba(10,18,34,250),stop:1 rgba(6,10,19,252));border-bottom-left-radius:15px;border-bottom-right-radius:15px;}} QFrame#titleBar{{background:rgba(32,50,75,220);border-bottom:1px solid rgba(230,245,255,95);border-top-left-radius:15px;border-top-right-radius:15px;}} QLabel#titleMark{{color:{c};font-size:17pt;font-weight:900;}} QLabel#windowTitle{{color:#e9f4ff;font-size:9pt;font-weight:700;letter-spacing:1px;}} QPushButton#windowControl{{background:rgba(255,255,255,18);border:1px solid rgba(255,255,255,38);border-radius:6px;padding:0;font-size:12pt;}} QPushButton#windowControl:hover{{background:rgba(255,255,255,55);border:1px solid {c};}} QPushButton#windowClose:hover{{background:#c93651;color:white;border:1px solid #ff8294;border-radius:6px;padding:0;font-size:15pt;}}
        QFrame#glassPanel{{background:rgba(25,42,66,150);border:1px solid rgba(220,240,255,105);border-top:1px solid rgba(255,255,255,150);border-radius:18px;}}
        QLabel#hero{{font-size:31pt;font-weight:900;letter-spacing:2px;color:#f4f8ff;}} QLabel#subtitle{{font-size:9pt;font-weight:700;color:#9eb5d4;letter-spacing:1px;}}
        QLabel#badge{{background:rgba(45,67,96,145);border:1px solid rgba(255,255,255,100);border-radius:12px;padding:12px;color:#ffd166;font-weight:700;}}
        QLabel#sectionTitle{{font-size:12pt;font-weight:800;color:#f4f8ff;padding:8px;}} QLabel#status{{color:#a8bbd7;padding:3px;}} QLabel#footer{{color:#7188a8;font-size:8pt;font-weight:700;}}
        QPushButton{{background:rgba(43,64,91,190);color:#edf5ff;border:1px solid rgba(210,230,255,105);border-radius:9px;padding:10px 12px;font-weight:600;}}
        QPushButton:hover{{background:rgba(61,91,126,220);border:1px solid {c};}} QPushButton:pressed{{background:{c};color:#06101d;}}
        QPushButton#spin{{background:{c};color:#07111e;border:1px solid rgba(255,255,255,170);font-size:13pt;font-weight:900;padding:14px;border-radius:12px;}}
        QPushButton#spin:hover{{background:#f5fbff;color:#07111e;}} QPushButton:disabled{{color:#61728b;background:rgba(30,43,62,140);}}
        QComboBox{{background:rgba(16,28,45,210);color:#edf5ff;border:1px solid rgba(220,240,255,110);border-radius:8px;padding:8px;}} QComboBox QAbstractItemView{{background:#13233a;color:#edf5ff;selection-background-color:{c};}}
        QListWidget{{background:rgba(7,14,27,170);color:#eaf2ff;border:1px solid rgba(220,240,255,65);border-radius:10px;padding:6px;}} QListWidget::item{{padding:8px;border-radius:6px;}} QListWidget::item:selected{{background:{c};color:#07111e;}}
        QLabel#cover{{background:rgba(7,14,27,150);border:1px solid {c};border-radius:12px;color:#8ca6c8;}} QLabel#winnerTitle{{font-size:14pt;font-weight:800;color:#f4f8ff;}} QLabel#muted{{color:#9bb0ce;font-size:9pt;}}
        """)
        for w in self.findChildren(QFrame):
            if w.objectName()=='glassPanel':
                effect=QGraphicsDropShadowEffect(self); effect.setBlurRadius(8+strength*7); effect.setOffset(0,2); shadow=QColor(c); shadow.setAlpha(45+strength*18); effect.setColor(shadow); w.setGraphicsEffect(effect)
        self.wheel.glow=c; self.wheel.update()
    def customise_glow(self):
        d=GlassDialog(self.glow_color,self.glow_strength,self)
        if d.exec():
            self.glow_color=d.color; self.glow_strength=d.slider.value(); self.apply_theme()
            try: self.settings_path.parent.mkdir(parents=True,exist_ok=True); self.settings_path.write_text(json.dumps({'glow_color':self.glow_color,'glow_strength':self.glow_strength,'theme_name':self.theme_name},indent=2))
            except OSError: pass
            self.set_status(f'Glass theme updated • glow {self.glow_color.upper()} • strength {self.glow_strength}/5')
    def set_status(self,s): self.status.setText(s)
    def add_folder(self):
        p=QFileDialog.getExistingDirectory(self,'Choose ROM folder')
        if p and Path(p) not in self.folders: self.folders.append(Path(p)); self.set_status(f'{len(self.folders)} ROM folder(s) selected.')
    def import_launchers(self):
        # Explicit opt-in only: no launcher or online account is accessed automatically.
        d=QDialog(self); d.setWindowTitle('Import games from launchers'); d.setMinimumWidth(440)
        lay=QVBoxLayout(d)
        lay.addWidget(QLabel('Choose which launchers to check. Installed games are detected locally. To include uninstalled games, Steam supports importing a public profile using your Steam Web API key.'))
        checks={}
        for name in ['Steam','Epic Games','GOG Galaxy','Ubisoft Connect','EA app','Xbox app']:
            cb=QCheckBox(name); cb.setChecked(name in ('Steam','Epic Games')); checks[name]=cb; lay.addWidget(cb)
        cloud=QCheckBox('Include games in my Steam account even if not installed')
        lay.addWidget(cloud)
        lay.addWidget(QLabel('Steam Web API key (required for online Steam library):'))
        api_key=QLineEdit(); api_key.setPlaceholderText('Paste your Steam Web API key'); api_key.setEchoMode(QLineEdit.EchoMode.Password); lay.addWidget(api_key)
        lay.addWidget(QLabel('SteamID64 (17-digit Steam ID; profile Game details must be Public):'))
        steam_id=QLineEdit(); steam_id.setPlaceholderText('e.g. 7656119…'); lay.addWidget(steam_id)
        help_label=QLabel('Get an API key at steamcommunity.com/dev/apikey. Your key is used for this request only and is not saved by Game Roulette.')
        help_label.setWordWrap(True); help_label.setObjectName('muted'); lay.addWidget(help_label)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel); buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Import selected'); buttons.accepted.connect(d.accept); buttons.rejected.connect(d.reject); lay.addWidget(buttons)
        if d.exec()!=QDialog.DialogCode.Accepted: return
        selected=[name for name,cb in checks.items() if cb.isChecked()]
        if not selected: QMessageBox.information(self,'No launchers selected','Choose at least one launcher to import.'); return
        found=launcher_games(selected)
        if cloud.isChecked():
            if not api_key.text().strip() or not re.fullmatch(r'\d{17}', steam_id.text().strip()):
                QMessageBox.warning(self,'Steam details needed','Enter a Steam Web API key and your 17-digit SteamID64 to import your online Steam library.')
                return
            try:
                found.extend(steam_owned_games(api_key.text(), steam_id.text()))
            except Exception as exc:
                QMessageBox.warning(self,'Steam library could not be loaded',f'{exc}\n\nCheck your API key, SteamID64, internet connection, and that Game details are public.')
                return
        # Merge by normalized title so installed and uninstalled copies don't duplicate.
        existing={g.title.casefold() for g in self.games}; added=[]
        for g in found:
            if g.title.casefold() not in existing:
                added.append(g); existing.add(g.title.casefold())
        self.games.extend(added); self.games.sort(key=lambda g:g.title.casefold()); self.refresh(); self.draw()
        if added:
            self.busy=True; self.spinbtn.setEnabled(False)
            self.set_status(f'Imported {len(added)} games. Looking for cover art online…')
            threading.Thread(target=self.download_launcher_covers, args=(added,), daemon=True).start()
        else:
            self.set_status(f'Launcher import complete: no new games added from {", ".join(selected)}.')
        if not found: QMessageBox.information(self,'No games found','No games were found for the selected launchers. Other launchers currently show locally detected/installed games only; online account-library imports are not available for them in this version.')

    def download_launcher_covers(self, games):
        good=bad=0
        for i,g in enumerate(games,1):
            if find_cover(g,self.covers):
                good+=1
            else:
                p=self.downloader.download_launcher_cover(g)
                if p:
                    self.covers[norm(p.name)]=p
                    self.covers[norm(g.title)]=p
                    self.covers[norm(g.path.name)]=p
                    good+=1
                else:
                    bad+=1
            if i % 3 == 0 or i == len(games):
                self.signals.status.emit(f'Finding launcher covers… {i}/{len(games)} • {good} found • {bad} not found')
        self.signals.finished.emit(good,bad)
    def choose_covers(self):
        p=QFileDialog.getExistingDirectory(self,'Choose local cover folder')
        if p: self.coverfolder=Path(p); self.set_status('Local covers folder selected.')
    def scan(self):
        if self.busy:return
        if not self.folders: QMessageBox.information(self,'Choose folders','Click Add ROM Folder first.'); return
        self.games=scan_games(self.folders); self.covers=local_covers(self.coverfolder)
        for key,path in local_covers(self.pcsx2folder).items(): self.covers.setdefault(key,path)
        self.refresh(); self.draw()
        if not self.games: QMessageBox.warning(self,'No games','No supported game files found.'); return
        local=sum(find_cover(g,self.covers) is not None for g in self.games); self.set_status(f'Found {len(self.games)} games, {local} local covers. Searching online for the rest…'); self.busy=True; self.spinbtn.setEnabled(False)
        threading.Thread(target=self.download_missing,daemon=True).start()
    def download_missing(self):
        system=None if self.system.currentText()==SYSTEMS[0] else self.system.currentText(); good=bad=0
        for i,g in enumerate(self.games,1):
            if find_cover(g,self.covers): good+=1
            else:
                sysname=system or AUTO.get(g.path.suffix.casefold()); p=self.downloader.download(g,sysname)
                if p: self.covers[norm(p.name)]=p; self.covers[norm(g.path.name)]=p; self.covers[norm(g.title)]=p; good+=1
                else: bad+=1
            if i%4==0 or i==len(self.games): self.signals.status.emit(f'Searching online covers… {i}/{len(self.games)} • {good} found • {bad} missing')
        self.signals.finished.emit(good,bad)
    def finish_download(self,good,bad):
        self.busy=False; self.refresh(); self.draw(); self.spinbtn.setEnabled(bool(self.games)); self.set_status(f'{len(self.games)} games • {good} covers available • {bad} missing. Covers are cached on this PC.')
    def refresh(self):
        self.list.blockSignals(True); self.list.clear()
        for g in self.games: self.list.addItem(('▣ ' if find_cover(g,self.covers) else '• ')+g.title)
        self.list.blockSignals(False); self.removebtn.setEnabled(False); self.removeallbtn.setEnabled(bool(self.games) and not self.busy); self.spinbtn.setEnabled(bool(self.games) and not self.busy)
    def draw(self): self.wheel.games=self.games; self.wheel.covers=self.covers; self.wheel.angle=self.angle; self.wheel.glow=self.glow_color; self.wheel.update()
    def select_game(self,index):
        if 0<=index<len(self.games) and not self.busy: self.show_game(self.games[index]); self.showbtn.setEnabled(True); self.removebtn.setEnabled(True)
    def remove_selected_game(self):
        idx=self.list.currentRow()
        if self.busy or idx<0:return
        g=self.games.pop(idx); self.winner=None; self.cover.setPixmap(QPixmap()); self.cover.setText('COVER ART'); self.wtitle.setText('Spin to pick a game' if self.games else 'No games on the wheel'); self.wpath.setText('Winner appears here'); self.refresh(); self.draw(); self.set_status(f'Removed {g.title} from this session. ROM file not deleted.')
    def remove_all_games(self):
        if self.busy or not self.games: return
        answer=QMessageBox.question(self,'Remove all games?',f'Remove all {len(self.games)} games from the current Game Roulette list?\n\nYour ROM files and installed games will not be deleted.',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes: return
        count=len(self.games); self.games.clear(); self.winner=None
        self.cover.setPixmap(QPixmap()); self.cover.setText('COVER ART')
        self.wtitle.setText('No games on the wheel'); self.wpath.setText('Winner appears here'); self.showbtn.setEnabled(False)
        self.refresh(); self.draw(); self.set_status(f'Removed all {count} games from this session. Files were not deleted.')
    def show_game(self,g):
        self.winner=g; p=find_cover(g,self.covers); self.cover.setPixmap(QPixmap(str(p)).scaled(210,210,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation) if p else QPixmap()); self.cover.setText('' if p else 'NO COVER FOUND'); self.wtitle.setText(g.title); self.wpath.setText((f'{g.source} • ' if getattr(g,'source','ROM') != 'ROM' else '') + str(g.path))
    def spin(self):
        if self.busy or not self.games:return
        self.spinbtn.setEnabled(False); self.chosen=random.randrange(len(self.games)); self.start_angle=self.angle; step=360/len(self.games); dest=((self.chosen+.5)*step)%360; delta=(dest-self.start_angle%360)%360; self.target=self.start_angle+random.randint(5,8)*360+delta; self.t0=time.monotonic(); self.timer=QTimer(self); self.timer.timeout.connect(self.animate); self.timer.start(16)
    def animate(self):
        t=min(1,(time.monotonic()-self.t0)/4.1); e=1-(1-t)**4; self.angle=self.start_angle+(self.target-self.start_angle)*e; self.draw()
        if t>=1:
            self.timer.stop(); self.angle=self.target; self.draw(); self.spinbtn.setEnabled(True); self.spinbtn.setText('▶  SPIN AGAIN'); self.list.setCurrentRow(self.chosen); self.show_game(self.games[self.chosen]); self.showbtn.setEnabled(True); self.set_status('Winner picked! Open it manually in your emulator.')
    def show_location(self):
        if self.winner: QMessageBox.information(self,'Game file location',f'{self.winner.title}\nSource: {getattr(self.winner, "source", "ROM")}\n\n{self.winner.path}\n\nOpen it manually in its launcher.')

def main():
    app=QApplication(sys.argv); app.setWindowIcon(QIcon(str(Path(__file__).with_name('game_roulette_icon.png')))); app.setStyle('Fusion'); app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True); w=MainWindow(); w.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True); w.show(); sys.exit(app.exec())
if __name__=='__main__': main()
