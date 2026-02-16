
# FotoTool FINAL 1.0 – Statuslayout getrennt (links Info, unten Progressbar mit Prozent)


import queue
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
import sys
import subprocess
import threading
import time
import json
import shutil
import requests
from datetime import datetime
from tkinter import PhotoImage
from PIL import Image, ImageTk
from tag_manager import TagManager
print(sys.executable)



# ------------------------------------------------------------
# Portabler ExifTool-Pfad
# ------------------------------------------------------------
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _norm(p: str) -> str:
    return os.path.normcase(os.path.normpath(p))


def resource_path(rel_path: str):
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = BASE_DIR
    return os.path.join(base, rel_path)

EXIFTOOL_PATH = resource_path("tools/exiftool.exe")


COLORS = {
    "bg":     "#0d0e0e",  # App-Hintergrund (bleibt)
    "panel":  "#14161B",  # Cards/Header/Sidebar (etwas heller als bg)
    "accent": "#4b5563",  # Akzent = Blau (modern, weniger „Gamification“)
    "text":   "#e5e7eb",
    "muted":  "#9ca3af",
    "hover":  "#1f2937",
    "active": "#161b23",


}
    

MONTH_NAMES = {
    "01": "Januar", "02": "Februar", "03": "März",
    "04": "April", "05": "Mai", "06": "Juni",
    "07": "Juli", "08": "August", "09": "September",
    "10": "Oktober", "11": "November", "12": "Dezember",
}

from datetime import date, timedelta

def easter_date(year):
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451

    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1

    return date(year, month, day)


GERMAN_FIXED_HOLIDAYS = {
    (1, 1): "Neujahr",
    (5, 1): "Tag der Arbeit",
    (10, 3): "Tag der Deutschen Einheit",
    (12, 25): "1. Weihnachtstag",
    (12, 26): "2. Weihnachtstag",
}

def holiday_name_de(d: date) -> str | None:
    # feste Feiertage
    name = GERMAN_FIXED_HOLIDAYS.get((d.month, d.day))
    if name:
        return name

    # bewegliche Feiertage
    easter = easter_date(d.year)

    movable = {
        easter - timedelta(days=2): "Karfreitag",
        easter + timedelta(days=1): "Ostermontag",
        easter + timedelta(days=39): "Christi Himmelfahrt",
        easter + timedelta(days=50): "Pfingstmontag",
    }

    return movable.get(d)


# ------------------------------------------------------------
# Tooltip Helper
# ------------------------------------------------------------
class Tooltip:
    def __init__(self, widget, text, delay=400):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tipwindow = None
        self._after_id = None

        
        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._hide)
        widget.bind("<ButtonPress>", self._hide)

    def _schedule(self, event=None):
        self._after_id = self.widget.after(self.delay, self._show)

    def _show(self):
        if self.tipwindow or not self.text:
            return

        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8

        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.configure(bg="#111827")

        label = tk.Label(
            tw,
            text=self.text,
            justify="left",
            bg="#111827",
            fg="#e5e7eb",
            relief="flat",
            padx=8,
            pady=6,
            font=("Segoe UI", 9)
        )
        label.pack()

    def _hide(self, event=None):
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None





class FotoToolFinal20(tk.Tk):

    def _stop_sort(self):
        self.stop_flag = True



    def step_title(self, parent, text):
        row = tk.Frame(parent, bg=parent["bg"])
        row.pack(fill="x", pady=(10, 4), anchor="w")

        tk.Frame(row, bg=COLORS["accent"], width=4, height=18).pack(side="left", padx=(0, 10))
        tk.Label(
            row,
            text=text,
            fg=COLORS["text"],
            bg=row["bg"],
            font=("Segoe UI", 11, "bold"),
        ).pack(side="left")
        return row


    def _page_header(self, parent, title):
        header = tk.Frame(parent, bg=COLORS["panel"], padx=20, pady=16)
        header.pack(fill="x", pady=(0, 12))

        title_lbl = tk.Label(
            header,
            text=title,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Segoe UI", 14, "bold"),
        )
        title_lbl.grid(row=0, column=0, sticky="w")

        header.grid_columnconfigure(0, weight=1)

        return header

            

    def _update_holiday_preview(self, *args):
        example_date = datetime(2024, 3, 31).date()
        holiday = holiday_name_de(example_date)

        if self.holiday_name_var.get() and holiday:
            self.holiday_preview_text.set(
                f"Beispiel: 2024-03-31_{holiday}"
            )
        else:
            self.holiday_preview_text.set(
                "Beispiel: 2024-03-31_Alltag"
            )


    def _learn_import_tags(self):
        import_path = self.import_var.get()

        if not import_path or not os.path.isdir(import_path):
            messagebox.showerror("Fehler", "Bitte gültigen Import-Ordner wählen.")
            return

        def worker():
            try:
                learned = self.tags.scan_import_structure(import_path)

                self.ui(
                    self._show_center_message,
                    "Import gelernt",
                    f"{learned} Dateien mit Struktur-Tags gespeichert."
                )

            except Exception as e:
                self.ui(messagebox.showerror, "Fehler", str(e))

        threading.Thread(target=worker, daemon=True).start()


    def _run_sort_simulation(self):
        if not os.path.isdir(self.import_var.get()):
            messagebox.showerror("Fehler", "Bitte gültigen Import-Ordner wählen.")
            return

        if not os.path.isdir(self.archiv_var.get()):
            messagebox.showerror("Fehler", "Bitte gültiges Archiv wählen.")
            return

        self.ui(self.status_text.set, "Simulation läuft…")
        self.ui(self.detail_text.set, "")
        self.ui(self.percent_text.set, "")

        def worker():
            try:
                files = []
                for root, _, fns in os.walk(self.import_var.get()):
                    for f in fns:
                        files.append(os.path.join(root, f))

                total = len(files)

                count_sorted = 0
                count_unsorted = 0
                count_holidays = 0
                count_whatsapp = 0
                count_screenshot = 0
                count_videos = 0
                count_tag_candidates = 0

                tag_preview = []


                # EXIF einmal laden (wie im echten Sortieren)
                exif_data = self._load_exif_batch(self.import_var.get())
                exif_map = {_norm(i["SourceFile"]): i for i in exif_data if "SourceFile" in i}

                for idx, file in enumerate(files, start=1):

                    name_lower = os.path.basename(file).lower()
                    ext = os.path.splitext(file)[1].lower()
                    is_video = ext in [".mp4", ".mov", ".avi", ".mkv", ".3gp"]

                    meta = exif_map.get(_norm(file), {})
                    has_exif = bool(meta.get("DateTimeOriginal"))
                    tags = self.tags.tags_for_file(file)

                    # Kandidat: Tags vorhanden, aber keine EXIF-Datum/Details (deine Regel später)
                    if tags and not has_exif:
                        count_tag_candidates += 1

                        if len(tag_preview) < 20:
                            tag_preview.append(
                                f"{os.path.basename(file)}  ->  {', '.join(tags)}"
                            )

                        self.ui(self.detail_text.set, f"{os.path.basename(file)}  •  Tags: {tags}")




                    year, month, month_name = self._get_year_month(
                        file, meta, is_video,
                        self.mode_var.get() == "filedate",
                        self.mode_var.get() == "hybrid"
                    )

                    # gleiche Klassifikation wie echtes Sortieren
                    category = self._classify_photo(
                        file,
                        name_lower,
                        year,
                        month_name,
                        has_exif,
                        self.mode_var.get() == "filedate",
                        self.mode_var.get() == "hybrid",
                        self.mode_var.get() == "events_time_gps",
                        {}
                    )

                    if is_video:
                        count_videos += 1
                    elif category == "whatsapp":
                        count_whatsapp += 1
                    elif category == "screenshot":
                        count_screenshot += 1
                    elif category == "date" or category == "event":
                        count_sorted += 1
                    else:
                        count_unsorted += 1

                    percent = int(idx / total * 100) if total else 0
                    self.ui(self.progress_val.set, percent)
                    self.ui(self.percent_text.set, f"{percent} %") if 0 < percent < 100 else self.ui(self.percent_text.set, "")


                preview_text = "\n".join(tag_preview) if tag_preview else "- (keine)"

                summary = "\n".join([
                    "Simulation abgeschlossen.",
                    "",
                    f"Einsortiert: {count_sorted}",
                    f"WhatsApp-Screenshots: {count_screenshot}",
                    f"Unsortiert: {count_unsorted}",
                    f"Videos: {count_videos}",
                    "",
                    f"Tag-Kandidaten (würden Tags bekommen): {count_tag_candidates}",
                    "",
                    "Beispiele (max 20):",
                    preview_text
                ])



                self.ui(self.status_text.set, "Simulation fertig")
                self.ui(self._show_center_message, "Simulation", summary)

            except Exception as e:
                self.ui(messagebox.showerror, "Fehler", str(e))
                self.ui(self.status_text.set, "Simulation fehlgeschlagen")

        threading.Thread(target=worker, daemon=True).start()

    
    
    # ------------------------------------------------------------
    # ------------------------------------------------------------
    # Zentrale UI-Queue – ALLE Thread->UI Updates laufen hier durch
    # ------------------------------------------------------------
    def ui(self, fn, *args, **kwargs):
        """Thread-safe Aufruf von UI-Funktionen."""
        self._ui_queue.put((fn, args, kwargs))


    def _process_ui_queue(self):
        """Wird nur im Tk-Hauptthread ausgeführt."""
        try:
            while True:
                fn, args, kwargs = self._ui_queue.get_nowait()
                try:
                    fn(*args, **kwargs)
                except Exception as e:
                    # UI-Fehler dürfen die App niemals crashen
                    print("UI-Dispatch-Fehler:", e)
        except queue.Empty:
            pass

        # 60 FPS reichen völlig → 16 ms
        self.after(16, self._process_ui_queue)


    def _show_center_message(self, title, text):
        win = tk.Toplevel(self)
        win.title(title)
        win.transient(self)
        win.grab_set()

        tk.Label(win, text=text, padx=20, pady=20).pack()

        tk.Button(win, text="OK", command=win.destroy, width=10).pack(pady=(0, 15))

        # Fenstergröße berechnen
        win.update_idletasks()

        w = win.winfo_width()
        h = win.winfo_height()

        x = self.winfo_x() + (self.winfo_width() // 2) - (w // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (h // 2)

        win.geometry(f"{w}x{h}+{x}+{y}")


    def __init__(self):
        super().__init__()
        

        import queue

        style = ttk.Style()
        style.theme_use("default")

        style.configure(
            "TProgressbar",
            troughcolor=COLORS["panel"],
            background=COLORS["accent"],
            bordercolor=COLORS["panel"],
            lightcolor=COLORS["accent"],
            darkcolor=COLORS["accent"],
        )
        style.configure(
            "Vertical.TScrollbar",
            background=COLORS["panel"],
            troughcolor=COLORS["bg"],
            bordercolor=COLORS["panel"],
        )


        
        self._ui_queue = queue.Queue()
        self._process_ui_queue()
        self._gps_cache = {}



        self.dup_result = tk.StringVar(value="Noch kein Scan durchgeführt.")
        # ---------------- Logs-Ordner vorbereiten ----------------
        appdata = os.getenv("LOCALAPPDATA")
        self.app_dir = os.path.join(appdata, "FotoTool")
        os.makedirs(self.app_dir, exist_ok=True)

        self.tags = TagManager(self.app_dir)   # <-- statt BASE_DIR

        self.logs_dir = os.path.join(appdata, "FotoTool", "logs")
        os.makedirs(self.logs_dir, exist_ok=True)

        # Thumbnail-Cache Ordner
        self.thumb_cache_dir = os.path.join(appdata, "FotoTool", "thumbcache")
        os.makedirs(self.thumb_cache_dir, exist_ok=True)


        self.tip_text = tk.StringVar(value="")
        self.percent_text = tk.StringVar(value="")
        


        self.current_log_path = None

        def _start_log(prefix):
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self.current_log_path = os.path.join(self.logs_dir, f"{prefix}_{ts}.txt")
            with open(self.current_log_path, "w", encoding="utf-8") as f:
                f.write(f"Log gestartet: {ts}")

        def _log_line(text):
            if not self.current_log_path:
                return
            with open(self.current_log_path, "a", encoding="utf-8") as f:
                f.write(text + "\n")


        self._start_log = _start_log
        self._log_line = _log_line

        self.nav_buttons = {}
        self.active_page = None

        self.ui_style = {

            "pad": 14,
            "radius_pad": 18,   # nur optisch (Padding)
            "entry_bg": COLORS["bg"],
            "card_bg": COLORS["panel"],
            "btn_bg": COLORS["panel"],
        }


        self.title("FotoTool 1.0 – by Heinz")
        self.geometry("1100x1100")
        self.minsize(1100, 1100)
        self.configure(bg=COLORS["bg"])
        # App-Icon (Fenster)
        ICON_APP = resource_path("icons/app.ico")
        try:
            self.iconbitmap(resource_path("icons/app.ico"))
        except Exception:
            pass

        # Icons laden (müssen als Referenz am Objekt bleiben, sonst verschwinden sie)
        self.ICONS = {}

        for k in ["sort","unsorted","duplicate","logs","license","help",
          "start","stop","undo","folder","apply"]:

            try:
                img = Image.open(resource_path(f"icons/{k}.png"))


                # Sidebar-Icons
                if k in ["sort","unsorted","duplicate"]:
                    img = img.resize((80, 80), Image.LANCZOS)

                if k in ["logs","license","help"]:
                    img = img.resize((28, 28), Image.LANCZOS)

                # Button-Icons
                if k in ["start","stop","undo","folder"]:
                    img = img.resize((42, 42), Image.LANCZOS)

                if k == "apply":
                    img = img.resize((64, 64), Image.LANCZOS)

                self.ICONS[k] = ImageTk.PhotoImage(img)

            except Exception:
                self.ICONS[k] = None



        self.stop_flag = False
        self._last_sort_ops = []   # speichert move UND copy
        self._last_dup_ops = []
        self.dup_trash_dir = os.path.join(self.app_dir, "dup_trash")
        os.makedirs(self.dup_trash_dir, exist_ok=True)


        self.progress_val = tk.DoubleVar(value=0)
        self.status_text = tk.StringVar(value="Bereit")
        self.detail_text = tk.StringVar(value="")
        
        container = tk.Frame(self, bg=COLORS["bg"])
        container.pack(fill="both", expand=True)

       # Sidebar
        self.sidebar = tk.Frame(container, bg=COLORS["panel"], width=120)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # ---- oberer Spacer ----
        self.sidebar_top_spacer = tk.Frame(self.sidebar, bg=COLORS["panel"])
        self.sidebar_top_spacer.pack(side="top", fill="both", expand=True)

        # ---- mittlere Navigation (3 Icons) ----
        self.nav_frame = tk.Frame(self.sidebar, bg=COLORS["panel"])
        self.nav_frame.pack(side="top")

        # ---- unterer Spacer ----
        self.sidebar_bottom_spacer = tk.Frame(self.sidebar, bg=COLORS["panel"])
        self.sidebar_bottom_spacer.pack(side="top", fill="both", expand=True)



        # ---- Footer ganz unten ----
        self.nav_footer = tk.Frame(self.sidebar, bg=COLORS["panel"])
        self.nav_footer.pack(side="bottom", pady=20)

               

        # Main
        self.main = tk.Frame(container, bg=COLORS["bg"])
        self.main.pack(side="left", fill="both", expand=True)

       
        # Bereich nur für Seiten
        self.page_area = tk.Frame(self.main, bg=COLORS["bg"])
        self.page_area.pack(side="top", fill="both", expand=True)



        self.pages = {}

        # Navigation links erzeugen
        # Hauptnavigation oben
        self._nav("Sortieren", "sort", top=True)
        self._nav("Unsortiert", "uns", top=True)
        self._nav("Duplikate", "dup", top=True)

        # ---- Thumbnail mittig unter Hauptnavigation ----
        self.thumb_frame = tk.Frame(self.sidebar, bg=COLORS["panel"])
        self.thumb_frame.pack(in_=self.nav_frame, pady=(12, 12))

        self.thumb_label = tk.Label(
            self.thumb_frame,
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            text="",
            justify="center"
        )
        self.thumb_label.pack()


        # Sekundär unten
        self._nav("Logs", "logs", top=False)
        self._nav("Lizenzen", "lic", top=False)
        self._nav("Hilfe", "help", top=False)




        self.pages["sort"] = self._page_sort(self.page_area)
        self.pages["uns"]  = self._page_unsorted(self.page_area)
        self.pages["dup"]  = self._page_duplicates(self.page_area)
        self.pages["logs"] = self._page_logs(self.page_area)
        self.pages["lic"]  = self._page_licenses(self.page_area)
        self.pages["help"] = self._page_help(self.page_area)



        self._progressbar_bottom()

        self.show("sort")

    # ------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------
    def _nav(self, title, key, top=True):
        icon_map = {
            "sort": "sort",
            "uns": "unsorted",
            "dup": "duplicate",
            "logs": "logs",
            "lic": "license",
            "help": "help",

        }

        img = self.ICONS.get(icon_map.get(key))

        # kleinere Icons für Footer
        size = 80 if top else 34

        btn = tk.Button(
            self.nav_frame if top else self.nav_footer,
            image=img,
            text="",
            width=size,
            height=size,
            command=lambda k=key: self.show(k),
            bg=COLORS["panel"],
            relief="flat",
            bd=0,
            highlightthickness=0,
            activebackground=COLORS["panel"],
        )
        if top:
            btn.pack(pady=18)
        else:
            btn.pack(pady=8)


        btn.bind("<Enter>", lambda e, b=btn: self._on_hover(b))
        btn.bind("<Leave>", lambda e, b=btn, k=key: self._on_leave(b, k))

        self.nav_buttons[key] = btn


    def _on_hover(self, btn):
        if btn != self.nav_buttons.get(self.active_page):
            btn.configure(bg=COLORS["hover"], cursor="hand2")


    def _on_leave(self, btn, key):
        if key != self.active_page:
            btn.configure(bg=COLORS["panel"])


    def show(self, key):
        for p in self.pages.values():
            p.pack_forget()

        self.pages[key].pack(fill="both", expand=True)




        # ----- Seitenabhängiger Tipp -----
        if key == "sort":
            self.tip_text.set("Tipp: EXIF ist am genauesten – Dateidatum sortiert jede Datei.")
        elif key == "uns":
            self.tip_text.set("Tipp: Erst Analyse starten, dann Zielordner anwenden.")
        elif key == "dup":
            self.tip_text.set("Tipp: Große Archive zuerst prüfen – spart Zeit.")
        elif key == "logs":
            self.tip_text.set("Tipp: Logs helfen beim Finden von Fehlern.")
        elif key == "lic":
            self.tip_text.set("Open-Source-Lizenzen der verwendeten Tools.")
        elif key == "help":
            self.tip_text.set("Bedienhilfe und Erklärung aller Funktionen.")



        # alte aktive Farbe zurücksetzen
        if self.active_page and self.active_page in self.nav_buttons:
            self.nav_buttons[self.active_page].configure(bg=COLORS["panel"])

        # neue aktiv markieren
        if key in self.nav_buttons:
            self.nav_buttons[key].configure(
                bg=COLORS["active"],
                relief="flat",
                bd=0,
                highlightthickness=2,
                highlightbackground=COLORS["accent"]
            )


        self.active_page = key


    
    # ------------------------------------------------------------
    # Progressbar ganz unten – nur unter Hauptbereich, mit Prozent mittig
    # ------------------------------------------------------------

    def _progressbar_bottom(self):
        # Untere Leiste nur für Progress – volle Breite des Hauptbereichs
        bar = tk.Frame(self.main, bg=COLORS["panel"], height=64)
        bar.pack(side="bottom", fill="x")

        # Statuszeilen über dem Progressbar (lesbar, immer im Main)
      
        topline = tk.Frame(bar, bg=COLORS["panel"])
        topline.pack(fill="x")

        # Status links
        tk.Label(
            topline,
            textvariable=self.status_text,
            fg=COLORS["text"],
            bg=COLORS["panel"],
            anchor="w",
        ).pack(side="left", padx=12)

        # Spacer füllt die Mitte
        spacer = tk.Frame(topline, bg=COLORS["panel"])
        spacer.pack(side="left", expand=True, fill="x")

        # Prozent mittig im Spacer
        tk.Label(
            spacer,
            textvariable=self.percent_text,
            fg=COLORS["text"],
            bg=COLORS["panel"],
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="center")

        # Tipp rechts
        tk.Label(
            topline,
            textvariable=self.tip_text,
            fg=COLORS["muted"],
            bg=COLORS["panel"],
            anchor="e",
        ).pack(side="right", padx=12)






        # Progressbar bewusst höher, damit Prozent mittig sitzen kann
        self.progress = ttk.Progressbar(
            bar,
            variable=self.progress_val,
            maximum=100,
            style="accent.Horizontal.TProgressbar",
        )
        self.progress.pack(fill="x", padx=12, pady=14)

        
        

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------

    # ------------------------------------------------------------
    # Thumbnail in der Sidebar anzeigen
    # ------------------------------------------------------------
    
    def _write_tags_to_file(self, filepath: str, tags: list[str]) -> bool:
        """
        Schreibt Tags in XMP:Subject und IPTC:Keywords.
        Return True wenn ExifTool sauber durchläuft.
        """
        if not tags:
            return False

        # ExifTool erwartet entweder wiederholte Felder oder -sep.
        # Wir nehmen -sep ", " und setzen beide Felder.
        tag_str = ", ".join(tags)

        try:
            result = subprocess.run(
                [
                    EXIFTOOL_PATH,
                    "-overwrite_original",
                    f"-XMP:Subject={tag_str}",
                    f"-IPTC:Keywords={tag_str}",
                    "-sep", ", ",
                    filepath,
                ],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return result.returncode == 0
        except Exception:
            return False

    
    
    def show_thumbnail(self, path):
        try:
            # eindeutiger Dateiname im Cache
            import hashlib
            key = hashlib.md5(path.encode("utf-8")).hexdigest()
            cache_file = os.path.join(self.thumb_cache_dir, key + ".png")

            # ---------- aus Cache laden ----------
            if os.path.exists(cache_file):
                img = Image.open(cache_file)

            # ---------- neu erzeugen ----------
            else:
                img = Image.open(path)
                img.thumbnail((96, 96))
                img.save(cache_file, "PNG")

            photo = ImageTk.PhotoImage(img)

            # Referenz speichern (wichtig für Tkinter)
            self._thumb_img = photo

            self.thumb_label.configure(image=photo, text="")

            # Cache gelegentlich aufräumen
            self._cleanup_thumb_cache()


        except Exception:
            self.thumb_label.configure(image="", text="Keine Vorschau")

        # ------------------------------------------------------------
    # Thumbnail-Cache auf Maximalgröße begrenzen
    # ------------------------------------------------------------
    def _cleanup_thumb_cache(self, max_size_mb=500):
        try:
            max_bytes = max_size_mb * 1024 * 1024

            files = []
            total_size = 0

            for name in os.listdir(self.thumb_cache_dir):
                path = os.path.join(self.thumb_cache_dir, name)
                if os.path.isfile(path):
                    size = os.path.getsize(path)
                    mtime = os.path.getmtime(path)
                    files.append((path, size, mtime))
                    total_size += size

            # Wenn unter Limit → nichts tun
            if total_size <= max_bytes:
                return

            # Nach Alter sortieren (älteste zuerst löschen)
            files.sort(key=lambda x: x[2])

            for path, size, _ in files:
                os.remove(path)
                total_size -= size
                if total_size <= max_bytes:
                    break

        except Exception:
            pass

        # ------------------------------------------------------------
    # Thumbnails im Hintergrund erzeugen (Preload)
    # ------------------------------------------------------------
    def _preload_thumbnails(self, file_list, limit=200):
        
        def worker():
            import hashlib

            count = 0
            for path in file_list:
                if count >= limit:
                    break

                try:
                    key = hashlib.md5(path.encode("utf-8")).hexdigest()
                    cache_file = os.path.join(self.thumb_cache_dir, key + ".png")

                    # Nur erzeugen, wenn noch nicht im Cache
                    if not os.path.exists(cache_file):
                        img = Image.open(path)
                        img.thumbnail((96, 96))
                        img.save(cache_file, "PNG")

                    count += 1

                except Exception:
                    pass

        threading.Thread(target=worker, daemon=True).start()

    def _gps_to_place(self, lat, lon):
        try:
            if lat is None or lon is None:
                return "Unbekannt"

            key = f"{round(lat, 4)}_{round(lon, 4)}"

            if key in self._gps_cache:
                return self._gps_cache[key]

            import requests

            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                "lat": lat,
                "lon": lon,
                "format": "json",
                "zoom": 10,
                "addressdetails": 1,
            }

            headers = {"User-Agent": "FotoTool/2.0"}

            r = requests.get(url, params=params, headers=headers, timeout=2)

            if r.status_code != 200:
                return "Unbekannt"

            data = r.json()
            address = data.get("address", {})

            city = (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("county")
            )
            country = address.get("country")

            if city and country:
                result = f"{country}_{city}"
            elif city:
                result = city
            elif country:
                result = country
            else:
                result = "Unbekannt"

            self._gps_cache[key] = result
            return result

        except Exception:
            return "Unbekannt"


    def _ensure_event_cover(self, event_dir, image_path):
        """
        Erstellt ein Coverbild im Eventordner,
        falls noch keines existiert.
        """
        try:
            cover_path = os.path.join(event_dir, "cover.jpg")

            # Wenn schon vorhanden → nichts tun
            if os.path.exists(cover_path):
                return

            from PIL import Image

            img = Image.open(image_path)

            # Nur echte Bilder verwenden
            if img.format not in ("JPEG", "JPG", "PNG"):
                return

            # Auf 800px Breite skalieren
            w, h = img.size
            if w > 800:
                new_h = int(h * (800 / w))
                img = img.resize((800, new_h), Image.LANCZOS)

            img.convert("RGB").save(cover_path, "JPEG", quality=85)

        except Exception:
            pass


    def _update_structure_preview(self, *args):
        mode = getattr(self, "mode_var", tk.StringVar(value="exif")).get()
        structure = getattr(self, "structure_var", tk.StringVar(value="time_first")).get()
        gps_fallback = getattr(self, "gps_fallback_var", tk.BooleanVar(value=False)).get()

        preview = "Archiv → Jahr → Monat"

        # Beispielwerte für Vorschau
        place = "Italien_Rom"
        year = "2024"
        month = "März"
        date = "2024-03-12"

        # -----------------------------
        # Normale Modi
        # -----------------------------
        if mode == "exif":
            preview = (
                f"Fotos mit Aufnahmedatum → Archiv → {year} → {month}\n"
                f"(ohne Aufnahmedatum → Archiv → Unsortiert)"
            )

        elif mode == "filedate":
            preview = f"Archiv → {year} → {month}"

        elif mode == "hybrid":
            preview = (
                f"Fotos → Archiv → {year} → {month}\n"
                f"WhatsApp & Screenshots → Archiv → WhatsApp-Screenshots → {year} → {month}"
            )

        

        
        elif mode == "events_time_gps":
            if structure == "time_first":
                preview = f"Archiv → {year} → {month} → {date}_{place}"
            elif structure == "place_first":
                preview = f"Archiv → {place} → {year} → {month}"
            elif structure == "place_event":
                preview = f"Archiv → {place} → {date}_{place}"

            preview += "\nScreenshots/PNG → Archiv → WhatsApp-Screenshots → Jahr → Monat"


                            


        self.preview_text.set(preview)

    def _update_structure_visibility(self, *args):
        mode = self.mode_var.get()

        # Ordnerstruktur nur bei Events sichtbar
        if mode == "events_time_gps":
            self.structure_frame.pack(anchor="nw", fill="x")
            self.event_opts_frame.pack(anchor="w", padx=22, pady=(6, 0))
        else:
            self.structure_frame.pack_forget()
            self.event_opts_frame.pack_forget()



    def _build_event_name(
        self,
        event_id,
        has_real_gps,
        lat,
        lon,
        event_start_date,
        event_end_date,
        event_place_cache,
        file_path=None,          # ← NEU: damit wir Tags lesen können
    ):
        """
        Erzeugt stabilen, menschenlesbaren Eventnamen
        mit Priorität:
        Import-Tag > Feiertag > GPS-Ort > Alltag
        """

        try:
            d0 = event_start_date.get(event_id)
            d1 = event_end_date.get(event_id)

            if not d0:
                return f"Event-{event_id}"

            # ---------------- Datumsbereich ----------------
            if d1 and d1 != d0:
                date_str = f"{d0.strftime('%Y-%m-%d')}_bis_{d1.strftime('%Y-%m-%d')}"
            else:
                date_str = d0.strftime("%Y-%m-%d")

            # ---------------- Import-Tags prüfen ----------------
            event_title = None
            if file_path:
                tags = self.tags.tags_for_file(file_path)
                if tags:
                    event_title = tags[0]  # erster Tag = Ordnername

            # ---------------- Feiertag ----------------
            hname = holiday_name_de(d0) if self.holiday_name_var.get() else None

            # ---------------- GPS-Ort ----------------
            place = None
            if has_real_gps:
                if event_id in event_place_cache:
                    place = event_place_cache[event_id]
                else:
                    place = self._gps_to_place(lat, lon)
                    event_place_cache[event_id] = place

                if place == "Unbekannt":
                    place = None

            # =====================================================
            # ENTSCHEIDUNGSLOGIK (deine gewünschte Priorität)
            # =====================================================

            # 1) Wenn GPS vorhanden → Import-Tag ignorieren
            if has_real_gps:
                event_title = None

            # Import-Tag ohne GPS → Eventname übernehmen
            if event_title and not has_real_gps:
                return f"{date_str}_{event_title}"

            # 2) Feiertag + Ort
            if hname and place:
                return f"{date_str}_{hname}_{place}"

            # 3) Nur Feiertag
            if hname:
                return f"{date_str}_{hname}"

            # 4) Nur Ort
            if place:
                return f"{date_str}_{place}"

            # 5) Alltag
            return f"{date_str}_Alltag"

        except Exception:
            return f"Event-{event_id}"




    def _pick_dir(self, var):
        d = filedialog.askdirectory()
        if d:
            var.set(d)

    def _create_info_card(self, parent, title, text, example=None):
        card = tk.Frame(parent, bg=COLORS["panel"], padx=12, pady=10)

        tk.Label(
            card,
            text=title,
            fg=COLORS["text"],
            bg=COLORS["panel"],
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        ).pack(anchor="w")

        tk.Label(
            card,
            text=text,
            fg=COLORS["muted"],
            bg=COLORS["panel"],
            justify="left",
            wraplength=320,
        ).pack(anchor="w", pady=(4, 0))

        if example:
            tk.Label(
                card,
                text=f"Beispiel: {example}",
                fg=COLORS["text"],
                bg=COLORS["panel"],
                font=("Segoe UI", 9, "italic"),
            ).pack(anchor="w", pady=(6, 0))

        return card
    
    
    def _standard_footer(
        self,
        parent,
        start_cmd,
        stop_cmd=None,
        third_cmd=None,
        third_icon="undo",
        show_top_buttons=False,
        start_tooltip="Startet die Aktion.",
        analyse_cmd=None,
        preview_cmd=None,
    ):
        footer = tk.Frame(parent, bg=COLORS["bg"], padx=12, pady=12)

        # ---------- OBERE REIHE ----------
        if show_top_buttons:
            top_row = tk.Frame(footer, bg=COLORS["bg"])
            top_row.pack(fill="x", pady=(0, 8))

            for i in range(2):
                top_row.grid_columnconfigure(i, weight=1)

            analyse_btn = tk.Button(
                top_row,
                text="Ordnerstruktur analysieren",
                command=analyse_cmd if analyse_cmd else (lambda: None),
                bg=COLORS["panel"],
                fg=COLORS["text"],
                relief="flat",
                bd=0,
                height=2,
                state=("normal" if analyse_cmd else "disabled"),
            )
            analyse_btn.grid(row=0, column=0, sticky="ew", padx=6)

            preview_btn = tk.Button(
                top_row,
                text="Vorschau anzeigen",
                command=preview_cmd if preview_cmd else (lambda: None),
                bg=COLORS["panel"],
                fg=COLORS["text"],
                relief="flat",
                bd=0,
                height=2,
                state=("normal" if preview_cmd else "disabled"),
            )
            preview_btn.grid(row=0, column=1, sticky="ew", padx=6)

        # ---------- UNTERE REIHE ----------
        bottom_row = tk.Frame(footer, bg=COLORS["bg"])
        bottom_row.pack(fill="x")

        for i in range(3):
            bottom_row.grid_columnconfigure(i, weight=1)

        start_btn = tk.Button(
            bottom_row,
            image=self.ICONS.get("start"),
            command=start_cmd,
            bg=COLORS["accent"],
            relief="flat",
            bd=0,
            height=56,
        )
        start_btn.grid(row=0, column=0, sticky="ew", padx=6)

        stop_btn = tk.Button(
            bottom_row,
            image=self.ICONS.get("stop"),
            command=stop_cmd if stop_cmd else (lambda: None),
            bg=COLORS["panel"],
            relief="flat",
            bd=0,
            height=56,
            state=("normal" if stop_cmd else "disabled"),
        )
        stop_btn.grid(row=0, column=1, sticky="ew", padx=6)

        undo_btn = tk.Button(
            bottom_row,
            image=self.ICONS.get(third_icon),
            command=third_cmd if third_cmd else (lambda: None),
            bg=COLORS["panel"],
            relief="flat",
            bd=0,
            height=56,
            state=("normal" if third_cmd else "disabled"),
        )
        undo_btn.grid(row=0, column=2, sticky="ew", padx=6)

        return footer


                



    def rounded_card(self, parent, radius=18, bg="#111827", height=140):
        canvas = tk.Canvas(parent, bg=COLORS["bg"], highlightthickness=0, height=height)
        canvas.pack(fill="x", pady=12)

        inner = tk.Frame(canvas, bg=bg)
        win_id = canvas.create_window(0, 0, anchor="nw", window=inner)

        def redraw(event=None):
            w = canvas.winfo_width()
            h = height
            canvas.delete("bg")

            canvas.create_rectangle(radius, 0, w - radius, h, fill=bg, outline=bg, tags="bg")
            canvas.create_rectangle(0, radius, w, h - radius, fill=bg, outline=bg, tags="bg")

            canvas.create_oval(0, 0, radius * 2, radius * 2, fill=bg, outline=bg, tags="bg")
            canvas.create_oval(w - radius * 2, 0, w, radius * 2, fill=bg, outline=bg, tags="bg")
            canvas.create_oval(0, h - radius * 2, radius * 2, h, fill=bg, outline=bg, tags="bg")
            canvas.create_oval(w - radius * 2, h - radius * 2, w, h, fill=bg, outline=bg, tags="bg")

            canvas.itemconfigure(win_id, width=w, height=h)

        canvas.bind("<Configure>", redraw)
        redraw()

        return canvas, inner




       

    # ------------------------------------------------------------
    # SORTIEREN
    # ------------------------------------------------------------

    def _load_exif_batch(self, folder):
        try:
            result = subprocess.run(
                [
                    EXIFTOOL_PATH,
                    "-json",
                    "-r",
                    "-FileName",
                    "-DateTimeOriginal",
                    "-GPSLatitude",
                    "-GPSLongitude",
                    "-n",
                    folder,
                ],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )


            return json.loads(result.stdout)

        except Exception:
            return []

    def _get_best_datetime(self, file, meta):
        """
        Bestimmt die echte Aufnahmezeit:
        EXIF → Dateiname → Dateisystem
        """
        import re
        from datetime import datetime
        import os

        # 1) EXIF
        date_str = meta.get("DateTimeOriginal")
        if date_str:
            try:
                return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
            except Exception:
                pass

        # 2) Datum im Dateinamen
        name = os.path.basename(file)
        m = re.search(r"(20\d{2})[-_]?([01]\d)[-_]?([0-3]\d)", name)
        if m:
            try:
                y, mo, d = m.groups()
                return datetime(int(y), int(mo), int(d))
            except Exception:
                pass

        # 3) Dateisystem-Fallback
        try:
            return datetime.fromtimestamp(os.path.getmtime(file))
        except Exception:
            return None

    def _get_year_month(self, file, meta, is_video, use_filedate, use_hybrid):
        """
        Liefert (year, month, month_name) oder (None, None, None),
        wenn kein Datum bestimmbar ist.
        """

        # 1) Videos → Dateisystemdatum
        if is_video:
            try:
                ts = os.path.getmtime(file)
                t = time.localtime(ts)
                year = str(t.tm_year)
                month = f"{t.tm_mon:02d}"
                return year, month, MONTH_NAMES.get(month, month)
            except Exception:
                return None, None, None

        # 2) EXIF
        date_str = meta.get("DateTimeOriginal")
        if date_str:
            try:
                year, month = date_str.split(" ")[0].split(":")[:2]
                return year, month, MONTH_NAMES.get(month, month)
            except Exception:
                pass

        # 3) Filedate-Fallback (nur wenn erlaubt)
        if use_filedate or use_hybrid:
            try:
                ts = os.path.getmtime(file)
                t = time.localtime(ts)
                year = str(t.tm_year)
                month = f"{t.tm_mon:02d}"
                return year, month, MONTH_NAMES.get(month, month)
            except Exception:
                pass

        # Fallback aus Archiv-Lernen
        year_l, month_l = self.tags.learned_date_for_file(file)
        if year_l:
            month_l = month_l if month_l else "01"
            return year_l, month_l, MONTH_NAMES.get(month_l, month_l)



        # 4) Kein Datum
        return None, None, None

    def _classify_photo(
        self,
        file,
        name_lower,
        year,
        month_name,
        has_exif,
        use_filedate,
        use_hybrid,
        use_events,
        event_map,
    ):
        """
        Bestimmt nur die Kategorie eines Fotos.
        Rückgabe:
        "whatsapp", "screenshot", "event", "date", "unsorted"
        """

        # ---------------------------------
        # 1) WhatsApp / Screenshot
        # ---------------------------------
        if "whatsapp" in name_lower:
            return "whatsapp"

        if "screenshot" in name_lower or "bildschirmfoto" in name_lower:
            return "screenshot"

        # ---------------------------------
        # 2) Event
        # ---------------------------------
        if use_events and _norm(file) in event_map:
            return "event"

        # ---------------------------------
        # 3) Normales Datum
        # ---------------------------------
        if year and month_name and (has_exif or use_filedate or use_hybrid):
            return "date"

        # ---------------------------------
        # 4) Kein Datum
        # ---------------------------------
        return "unsorted"



    def _run_sort(self):

        # Sicherheitsabfrage bei Verschieben
        if self.move_mode.get() == "move":
            ok = messagebox.askyesno(
                "Warnung: Verschieben aktiv",
                "Du hast „Verschieben“ gewählt.\n\n"
                "Dateien werden aus dem Import-Ordner entfernt "
                "und ins Archiv verschoben.\n\n"
                "Rückgängig ist nur möglich, solange das Programm geöffnet ist.\n\n"
                "Trotzdem fortfahren?"
            )

            if not ok:
                return


        print("IMPORT:", self.import_var.get())
        print("ARCHIV:", self.archiv_var.get())

        self._start_log("sort")
        if not os.path.isfile(EXIFTOOL_PATH):
            messagebox.showerror("Fehler", f"ExifTool nicht gefunden:\n{EXIFTOOL_PATH}")
            return


        
        self._last_sort_moves = []
        self.stop_flag = False
        self.progress_val.set(0)
        self.ui(self.percent_text.set,"")
        self.ui(self.status_text.set, "Starte Import…")
        self.ui(self.detail_text.set,"")

        def worker():
            try:
                
                # --------------------------------------------------
                # Import-Ordnerstruktur automatisch lernen (falls nötig)
                # --------------------------------------------------
                try:
                    import_path = self.import_var.get()

                    if import_path and os.path.isdir(import_path):
                        # Prüfen, ob schon Tags existieren
                        learned_any = False

                        for root, _, files in os.walk(import_path):
                            for f in files:
                                if self.tags.tags_for_file(os.path.join(root, f)):
                                    learned_any = True
                                    break
                            if learned_any:
                                break

                        # Wenn noch keine Tags vorhanden → automatisch analysieren
                        self.tags.scan_import_structure(import_path)


                except Exception:
                    pass



                # --------------------------------------------------
                # Sortiermodus einmal global bestimmen
                # --------------------------------------------------
                mode = self.mode_var.get()

                use_filedate = mode == "filedate"
                use_hybrid = mode == "hybrid"
                use_events = mode == "events_time_gps"




                # Verlauf geladener Ordner (für "bereits sortiert")
                history_file = os.path.join(
                    os.getenv("LOCALAPPDATA"),
                    "FotoTool",
                    "sorted_history.json"
                )

                try:
                    with open(history_file, "r", encoding="utf-8") as f:
                        # Pfade + Zeitstempel laden
                        sorted_history = {os.path.normpath(k): v for k, v in json.load(f).items()}
                except Exception:
                    sorted_history = {}

                current_import_root = os.path.normpath(self.import_var.get())

                files = []
                for root, _, fns in os.walk(self.import_var.get()):
                    root_norm = os.path.normpath(root)

                    # -------------------------------
                    # Bereits sortierte Ordner überspringen
                    # -------------------------------
                    if self.remember_var.get():
                        last_sorted = sorted_history.get(root_norm)

                        if last_sorted:
                            try:
                                current_mtime = os.path.getmtime(root_norm)

                                # Wenn sich nichts geändert hat → überspringen
                                if current_mtime <= last_sorted:
                                    continue
                            except Exception:
                                pass

                    for f in fns:
                        files.append(os.path.join(root, f))



                # ---------------- Batch-EXIF laden ----------------
                self.ui(self.status_text.set,"Lese EXIF-Daten…")

                exif_data = self._load_exif_batch(self.import_var.get())

                # Map: Datei → Metadaten (Pfade normieren!)
                
                exif_map = {_norm(item["SourceFile"]): item for item in exif_data if "SourceFile" in item}



                # --------------------------------------------------
                # Events nach Zeit vorbereiten
                # --------------------------------------------------
                event_map = {}
                event_start_date = {}
                event_end_date = {}
                event_place_cache = {}

                if use_events:
                    files_sorted = sorted(
                        files,
                        key=lambda p: self._get_best_datetime(p, exif_map.get(_norm(p), {})) or datetime.min
                    )

                    last_time = None
                    event_id = 0

                    for path in files_sorted:
                        try:
                            best_dt = self._get_best_datetime(path, exif_map.get(_norm(path), {}))
                            if not best_dt:
                                # keine Zeit -> NICHT skippen, sondern später trotzdem Event bekommen
                                continue

                            ts = best_dt.timestamp()

                            gap_seconds = self.event_gap_hours.get() * 3600

                            if last_time is None or (ts - last_time > gap_seconds):

                                event_id += 1
                                event_start_date[event_id] = best_dt.date()
                                event_end_date[event_id] = best_dt.date()
                            else:
                                event_end_date[event_id] = best_dt.date()

                            event_map[_norm(path)] = event_id
                            last_time = ts

                        except Exception:
                            continue

                    # -----------------------------
                    # Sicherheitsnetz (WICHTIG: HIER!)
                    # -----------------------------
                    if event_id == 0:
                        event_id = 1
                        event_start_date[event_id] = datetime.now().date()
                        event_end_date[event_id] = datetime.now().date()

                    for p in files:
                        if _norm(p) not in event_map:
                            event_map[_norm(p)] = event_id




                        
                                            

                        
                    
                

                # Zähler für Abschlussbericht
                count_sorted = 0
                count_unsorted = 0
                count_holidays = 0
                count_whatsapp = 0
                count_screenshot = 0
                count_videos = 0
                start_time = time.time()
                total = len(files)


                for idx, file in enumerate(files, start=1):
                    if self.stop_flag:
                        self.ui(self.status_text.set,"Abgebrochen")
                        return

                    # Dateityp bestimmen
                    name_lower = os.path.basename(file).lower()
                    ext = os.path.splitext(file)[1].lower()
                    is_png = ext == ".png"
                    is_video = ext in [".mp4", ".mov", ".avi", ".mkv", ".3gp"]

                    # ---------------- EXIF aus Batch holen ----------------
                    meta = exif_map.get(_norm(file), {})

                    date_str = meta.get("DateTimeOriginal")
                    lat = meta.get("GPSLatitude")
                    lon = meta.get("GPSLongitude")
                    
                    self._log_line(f"GPS CHECK: {file} | lat={lat} lon={lon} | meta_keys={list(meta.keys())[:8]}")
                    
                    
                    has_exif = bool(date_str)


                    year, month, month_name = self._get_year_month(
                        file,
                        meta,
                        is_video,
                        use_filedate,
                        use_hybrid
                    )

                    # ---------------------------------------------
                    # PNG → nur in Hybrid oder Event als Screenshot
                    # ---------------------------------------------
                    if not is_video and is_png and (use_hybrid or use_events) and year and month_name:
                        target_dir = os.path.join(
                            self.archiv_var.get(),
                            "WhatsApp-Screenshots",
                            year,
                            month_name
                        )

                        count_screenshot += 1
                        exif_flag = "PNG → WhatsApp/Screenshots"
                        
                        # Datei sofort kopieren und nächsten Loop starten
                        base = os.path.basename(file)
                        dest = os.path.join(target_dir, base)
                        os.makedirs(target_dir, exist_ok=True)
                        shutil.copy2(file, dest)

                        continue



                    # WhatsApp / Screenshot erkennen (nur Fotos)
                    is_whatsapp = "whatsapp" in name_lower
                    is_screenshot = ("screenshot" in name_lower) or ("bildschirmfoto" in name_lower)

                    # -------------------------
                    # 0) Videos separat behandeln
                    # -------------------------
                    if is_video:
                        count_videos += 1

                        if year and month_name:
                            target_dir = os.path.join(self.archiv_var.get(), "Videos", year, month_name)
                            exif_flag = "Video"
                        else:
                            target_dir = os.path.join(self.archiv_var.get(), "Videos", "Unsortiert")
                            exif_flag = "Video (kein Datum)"

                    # -------------------------
                    # 1) Fotos / Bilder (NEU – saubere Entscheidungslogik)
                    # -------------------------
                    else:
                        category = self._classify_photo(
                            file,
                            name_lower,
                            year,
                            month_name,
                            has_exif,
                            use_filedate,
                            use_hybrid,
                            use_events,
                            event_map,
                        )

                        target_dir = None
                        exif_flag = ""

                        # ---------------------------------------------
                        # 1a) WhatsApp / Screenshots
                        # ---------------------------------------------
                        if (use_filedate or use_hybrid) and year and month_name:

                            if category == "whatsapp":
                                target_dir = os.path.join(self.archiv_var.get(), "WhatsApp", year, month_name)
                                count_whatsapp += 1
                                exif_flag = "WhatsApp"

                            elif category == "screenshot":
                                target_dir = os.path.join(self.archiv_var.get(), "Screenshots", year, month_name)
                                count_screenshot += 1
                                exif_flag = "Screenshot"

                        # ---------------------------------------------
                        # 1b) Event-Modus
                        # ---------------------------------------------
                        if target_dir is None and category == "event":

                            event_id = event_map[_norm(file)]
                            d0 = event_start_date.get(event_id)

                            if d0:
                                date_str = d0.strftime("%Y-%m-%d")
                                year = str(d0.year)
                                month = f"{d0.month:02d}"
                                month_name = MONTH_NAMES.get(month, month)
                            else:
                                date_str = "Unbekannt"

                            has_real_gps = lat is not None and lon is not None

                            event_name = self._build_event_name(
                                event_id,
                                has_real_gps,
                                lat,
                                lon,
                                event_start_date,
                                event_end_date,
                                event_place_cache,
                                file_path=file   # ← NEU
                            )
                            hname = holiday_name_de(d0) if d0 else None
                            if hname and hname in event_name:
                                count_holidays += 1


                            structure = self.structure_var.get()

                            # -------- KEIN GPS → Alltag --------
                            if not has_real_gps:

                                if not d0:
                                    target_dir = os.path.join(self.archiv_var.get(), "Unsortiert")
                                    count_unsorted += 1
                                    exif_flag = "kein Datum"

                                else:
                                    # Event ohne GPS → unter Alltag-Überordner einsortieren
                                    target_dir = os.path.join(
                                        self.archiv_var.get(),
                                        "Alltag (kein Ort-GPS)",
                                        year,
                                        month_name,
                                        event_name
                                    )
                                    count_sorted += 1
                                    exif_flag = "Event (ohne GPS)"


                            # -------- MIT GPS --------
                            else:

                                if structure == "time_first":
                                    target_dir = os.path.join(self.archiv_var.get(), year, month_name, event_name)

                                elif structure == "place_first":

                                    place = self._gps_to_place(lat, lon)

                                    if "_" in place:
                                        country, city = place.split("_", 1)
                                    else:
                                        country = place
                                        city = "Unbekannt"

                                    target_dir = os.path.join(
                                        self.archiv_var.get(),
                                        country,
                                        city,
                                        year,
                                        month_name
                                    )

                                elif structure == "place_event":
                                    parts = event_name.split("_")

                                    # Ort steht meist am Ende des Namens
                                    place = parts[-1] if len(parts) > 1 else "Unbekannt"

                                    target_dir = os.path.join(self.archiv_var.get(), place, event_name)

                                else:
                                    target_dir = os.path.join(self.archiv_var.get(), year, month_name, event_name)

                                count_sorted += 1
                                exif_flag = "Event (Zeit+Ort)"

                        # ---------------------------------------------
                        # 1c) Normale Datumssortierung
                        # ---------------------------------------------
                        if target_dir is None and category == "date":
                            target_dir = os.path.join(self.archiv_var.get(), year, month_name)
                            count_sorted += 1
                            exif_flag = "Datum ✓"

                        # ---------------------------------------------
                        # 1d) Kein Datum → Unsortiert
                        # ---------------------------------------------
                        if target_dir is None:
                            target_dir = os.path.join(self.archiv_var.get(), "Unsortiert")
                            count_unsorted += 1
                            exif_flag = "kein Datum"


                    # Datei kopieren ohne Überschreiben
                    base = os.path.basename(file)
                    name, extension = os.path.splitext(base)
                    dest = os.path.join(target_dir, base)
                    counter = 1

                    while os.path.exists(dest):
                        dest = os.path.join(target_dir, f"{name}_{counter}{extension}")
                        counter += 1

                    try:
                        os.makedirs(target_dir, exist_ok=True)
                            


                        if self.move_mode.get() == "move":
                            shutil.move(file, dest)
                            self._last_sort_ops.append(("move", dest, file))
                            self._log_line(f"MOVE: {file} -> {dest}")
                        else:
                            shutil.copy2(file, dest)
                            self._last_sort_ops.append(("copy", dest, file))
                            self._log_line(f"COPY: {file} -> {dest}")

                    except Exception as e:
                        self._log_line(f"FEHLER beim Kopieren: {file} -> {dest} | {e}")

                    


                    # Coverbild für Event erzeugen
                    if use_events:
                        try:
                            self._ensure_event_cover(target_dir, dest)
                        except Exception:
                            pass


                    # Statusanzeige
                    self.ui(self.detail_text.set, f"{os.path.basename(file)}  •  {exif_flag}")

                    elapsed = time.time() - start_time
                    avg = elapsed / idx if idx else 0
                    remaining = int(avg * (total - idx))
                    mins, secs = divmod(remaining, 60)

                    self.ui(self.status_text.set,f"Sortiere {idx}/{total} – Restzeit {mins:02d}:{secs:02d}")

                    percent = int(idx / total * 100) if total else 0
                    self.ui(self.progress_val.set, percent)

                    if 0 < percent < 100:
                        self.ui(self.percent_text.set,f"{percent} %")
                        
                    else:
                        self.ui(self.percent_text.set,"")
                        

                    

                self.ui(self.detail_text.set,"")
                self.ui(self.status_text.set,"Import abgeschlossen")
                self.ui(self.percent_text.set,"")
                
                # Abschlussbericht
                lines = [
                    "Sortieren abgeschlossen.",
                    "",
                    f"Fotos/Videos einsortiert: {count_sorted}",
                    f"Feiertags-Events: {count_holidays}",
                    f"WhatsApp-Screenshots: {count_screenshot}",
                    f"Unsortiert: {count_unsorted}",
                    f"Videos: {count_videos}",
                ]
                lines.append("")
                


                summary = "\n".join(lines)
                self.ui(self._show_center_message, "Fertig", summary)





                # aktuellen Import-Ordner als verarbeitet merken
                if self.remember_var.get():
                    try:
                        for root, _, _ in os.walk(self.import_var.get()):
                            root_norm = os.path.normpath(root)
                            try:
                                sorted_history[root_norm] = os.path.getmtime(root_norm)
                            except Exception:
                                pass

                        with open(history_file, "w", encoding="utf-8") as f:
                            json.dump(sorted_history, f, indent=2)
                    except Exception:
                        pass

                self._log_line("--- Zusammenfassung ---")
                for line in lines:
                    self._log_line(line)

                
            except Exception as e:
                messagebox.showerror("Fehler", str(e))
                self.ui(self.status_text.set,"Fehler")

        threading.Thread(target=worker, daemon=True).start()

    def _undo_last_dup(self):
        if not self._last_dup_ops:
            messagebox.showinfo("Undo", "Keine Löschaktion vorhanden.")
            return

        restored = 0

        for trash_path, original_path in reversed(self._last_dup_ops):
            try:
                os.makedirs(os.path.dirname(original_path), exist_ok=True)
                shutil.move(trash_path, original_path)
                restored += 1
            except Exception:
                pass

        self._last_dup_ops.clear()

        messagebox.showinfo("Undo", f"{restored} Dateien wiederhergestellt.")


    def _undo_last_sort(self):
        ops = getattr(self, "_last_sort_ops", [])

        if not ops:
            messagebox.showinfo("Undo", "Keine Sortierung zum Rückgängig machen.")
            return

        restored = 0
        deleted = 0
        failed = 0

        for op, dest, src in reversed(ops):
            try:
                if op == "move":
                    os.makedirs(os.path.dirname(src), exist_ok=True)
                    if os.path.exists(dest):
                        shutil.move(dest, src)
                        restored += 1

                elif op == "copy":
                    if os.path.exists(dest):
                        os.remove(dest)
                        deleted += 1

            except Exception:
                failed += 1

        ops.clear()

        messagebox.showinfo(
            "Undo",
            f"Zurück: {restored} verschoben, {deleted} Kopien gelöscht. Fehler: {failed}"
        )



    def _page_sort(self, parent):
        p = tk.Frame(parent, bg=COLORS["bg"])
        p.pack_propagate(False)

        # ---------- HEADER ----------
        header = tk.Frame(p, bg=COLORS["panel"], padx=20, pady=16)
        header.pack(fill="x")
        header.grid_columnconfigure(0, weight=1)  # linker Bereich dehnt sich
        header.grid_columnconfigure(1, weight=0)

        # ---------- SCROLL-CONTAINER ----------
        scroll_container = tk.Frame(p, bg=COLORS["bg"])
        scroll_container.pack(fill="both", expand=True)

        canvas = tk.Canvas(scroll_container, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        content_outer = tk.Frame(canvas, bg=COLORS["bg"])
        content_window = canvas.create_window((0, 0), window=content_outer, anchor="nw")

        content = tk.Frame(content_outer, bg=COLORS["bg"])
        content.pack(fill="both", expand=True, padx=20)


        def _resize_content(event):
            canvas.itemconfig(content_window, width=event.width)

        canvas.bind("<Configure>", _resize_content)
        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=scrollbar.set)






        

        # Linke Seite: Titel + Untertitel
        left = tk.Frame(header, bg=COLORS["panel"])

        left.grid(row=0, column=0, sticky="nw")

        tk.Label(
            left,
            text="Import ins Archiv",
            fg=COLORS["text"],
            bg=COLORS["panel"],
            font=("Segoe UI", 22, "bold"),
        ).pack(anchor="w")

        tk.Label(
            left,
            text="Wähle Quelle und Ziel. Danach sortiert FotoTool automatisch nach Jahr/Monat.",
            fg=COLORS["muted"],
            bg=COLORS["panel"],
        ).pack(anchor="w", pady=(6, 0))

        # Rechte Seite: Info-Karte
        info = self._create_info_card(
            header,
            "Fotos ins Archiv importieren",
            "Wähle einen Import-Ordner und ein Ziel-Archiv. "
            "FotoTool sortiert Bilder und Videos automatisch nach Jahr und Monat.",
            "Handy/DCIM → Archiv/2024/03",
        )
        info.grid(row=0, column=1, sticky="ne", padx=(40, 40))



        # State
        self.import_var = tk.StringVar()
        self.archiv_var = tk.StringVar()
        self.mode_var = tk.StringVar(value="exif")
        self.move_mode = tk.StringVar(value="copy")
        self.remember_var = tk.BooleanVar(value=True)
        self.preview_text = tk.StringVar(value="")



        # ---------- Schritt 1 ----------

        self.step_title(content, "1. Quelle & Ziel wählen")


        # ---------- Card 1: Pfade ----------
        
        
        card_paths = tk.Label(content, bg=COLORS["panel"], padx=16, pady=14)
        card_paths.pack(fill="x")

        card_paths.grid_columnconfigure(0, weight=0)  # Label
        card_paths.grid_columnconfigure(1, weight=1)  # Entry
        card_paths.grid_columnconfigure(2, weight=0)  # Button

        def field_row(r, label, var, icon_key="folder"):
            tk.Label(
                card_paths,
                text=label,
                fg=COLORS["muted"],
                bg=COLORS["panel"],
                font=("Segoe UI", 10),
            ).grid(row=r, column=0, sticky="w", pady=10)

            e = tk.Entry(
                card_paths,
                textvariable=var,
                bg=COLORS["panel"],
                fg=COLORS["text"],
                insertbackground=COLORS["text"],
                relief="flat",
                highlightthickness=1,
                highlightbackground=COLORS["hover"],
                highlightcolor=COLORS["hover"],
            )
            e.grid(row=r, column=1, sticky="ew", padx=(14, 10), pady=10, ipady=6)

            tk.Button(
                card_paths,
                image=self.ICONS.get(icon_key),
                text="",
                width=42,
                height=34,
                command=lambda v=var: self._pick_dir(v),
                bg=COLORS["panel"],
                activebackground="#111b33",
                relief="flat",
                bd=0,
                highlightthickness=0,
            ).grid(row=r, column=2, sticky="e", pady=10)

        field_row(0, "Import-Ordner", self.import_var, "folder")
        field_row(1, "Archiv", self.archiv_var, "folder")

        # ---------- Schritt 2 ----------
        self.step_title(content, "2. Sortierart festlegen")

        

        # ---------- Card 2: Optionen ----------
        card_opts = tk.Label(content, bg=COLORS["panel"], padx=16, pady=14)
        card_opts.pack(fill="x", pady=(14, 0))

        


        # Drei-Spalten-Layout für Optionen
       
        opts_grid = tk.Frame(card_opts, bg=COLORS["panel"])
        opts_grid.pack(fill="x")

        # 3 gleich breite Spalten
        opts_grid.grid_columnconfigure(0, weight=1)
        opts_grid.grid_columnconfigure(1, weight=1)
        opts_grid.grid_columnconfigure(2, weight=1)

        left_col = tk.Frame(opts_grid, bg=COLORS["panel"])
        mid_col = tk.Frame(opts_grid, bg=COLORS["panel"])
        right_col = tk.Frame(opts_grid, bg=COLORS["panel"])

        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        mid_col.grid(row=0, column=1, sticky="nsew", padx=(0, 15))
        right_col.grid(row=0, column=2, sticky="nsew")




               
       
        
        
        # ---------------- Sortiermodus (LINKS) ----------------
        tk.Label(
            left_col,
            text="Sortiermodus",
            fg=COLORS["text"],
            bg=COLORS["panel"],
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", pady=(0, 6))


        def seg_rb(parent, text, value):
            return tk.Radiobutton(
                parent,
                text=text,
                variable=self.mode_var,
                value=value,
                bg=COLORS["panel"],
                fg=COLORS["text"],
               selectcolor=COLORS["panel"],
                activebackground=COLORS["panel"],
                activeforeground=COLORS["text"],
                padx=10,
                pady=4,
            )


        seg_rb(left_col, "Originales Aufnahmedatum (aus Kamera)", "exif").pack(anchor="w")
        seg_rb(left_col, "Dateidatum (aus Datei)", "filedate").pack(anchor="w")
        seg_rb(left_col, "Automatisch (inkl. WhatsApp & Screenshots)", "hybrid").pack(anchor="w")
        seg_rb(left_col, "Events nach Zeit + Ort", "events_time_gps").pack(anchor="w")




        # --------------------------------------------------
        # Event-Optionen (nur sichtbar im Event-Modus)
        # --------------------------------------------------
        self.event_opts_frame = tk.Frame(left_col, bg=COLORS["panel"])
        self.event_opts_frame.pack(anchor="w", padx=22, pady=(6, 0))

        self.holiday_name_var = tk.BooleanVar(value=True)
        self.holiday_name_var.trace_add("write", self._update_holiday_preview)


        tk.Checkbutton(
            self.event_opts_frame,
            text="Event automatisch nach Feiertag benennen",
            variable=self.holiday_name_var,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            selectcolor=COLORS["panel"],
            activebackground=COLORS["panel"],
            activeforeground=COLORS["text"],
        ).pack(anchor="w")

        self.holiday_preview_text = tk.StringVar()
        self._update_holiday_preview()

        tk.Label(
            self.event_opts_frame,
            textvariable=self.holiday_preview_text,
            fg=COLORS["muted"],
            bg=COLORS["panel"],
            font=("Segoe UI", 9, "italic"),
        ).pack(anchor="w", pady=(2, 6))


        # ---- Zeitabstand Spinbox ----
        self.event_gap_hours = tk.IntVar(value=6)

        gap_frame = tk.Frame(self.event_opts_frame, bg=COLORS["panel"])
        gap_frame.pack(anchor="w", pady=(4, 0))

        tk.Label(
            gap_frame,
            text="Neues Event nach Abstand (Stunden):",
            fg=COLORS["muted"],
            bg=COLORS["panel"],
        ).pack(side="left")

        tk.Spinbox(
            gap_frame,
            from_=1,
            to=168,
            width=4,
            textvariable=self.event_gap_hours,
        ).pack(side="left", padx=(6, 0))



        


             
                                            
        
           
        # --------------------------------------------------
        # Ordnerstruktur (nur für Event-Modi sichtbar)
        # --------------------------------------------------
        self.structure_frame = tk.Frame(right_col, bg=COLORS["panel"])
        self.structure_frame.pack(anchor="nw", fill="x")

        tk.Label(
            self.structure_frame,
            text="Ordnerstruktur",
            fg=COLORS["text"],
            bg=COLORS["panel"],
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", pady=(0, 4))

        if not hasattr(self, "structure_var"):
            self.structure_var = tk.StringVar(value="time_first")


        def struct_rb(text, value):
            return tk.Radiobutton(
                self.structure_frame,
                text=text,
                variable=self.structure_var,
                value=value,
                bg=COLORS["panel"],
                fg=COLORS["text"],
                selectcolor=COLORS["bg"],
                activebackground=COLORS["panel"],
                activeforeground=COLORS["text"],
                padx=10,
                pady=4,
            )

        struct_rb("Zeit → Ort (Jahr/Monat/Event)", "time_first").pack(anchor="w")
        struct_rb("Ort → Zeit (Ort/Jahr/Monat)", "place_first").pack(anchor="w")
        struct_rb("Nur Ort-Events (Ort/Eventdatum)", "place_event").pack(anchor="w")
        
        tk.Label(
            mid_col,
            text="Optionen",
            fg=COLORS["text"],
            bg=COLORS["panel"],
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", pady=(18, 6))
        tk.Checkbutton(
            mid_col,
            text="Bereits sortierte Ordner überspringen",
            variable=self.remember_var,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            selectcolor=COLORS["bg"],
            activebackground=COLORS["panel"],
            activeforeground=COLORS["text"],
        ).pack(anchor="w")

        
        move_frame = tk.Frame(mid_col, bg=COLORS["panel"])
        move_frame.pack(anchor="w", pady=(10, 0))

        tk.Radiobutton(
            move_frame,
            text="Kopieren",
            variable=self.move_mode,
            value="copy",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            selectcolor=COLORS["bg"],
            activebackground=COLORS["panel"],
            activeforeground=COLORS["text"],
        ).pack(side="left", padx=(0, 14))

        tk.Radiobutton(
            move_frame,
            text="Verschieben",
            variable=self.move_mode,
            value="move",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            selectcolor=COLORS["bg"],
            activebackground=COLORS["panel"],
            activeforeground=COLORS["text"],
        ).pack(side="left")


        


       
        # ----- MITTIG: Vorschau-Box -----
           # ---------- Schritt 2 ----------
        self.step_title(content, "3. Vorschau prüfen")

        # ---------- Card ----------
        card_preview = tk.Frame(content, bg=COLORS["panel"], padx=16, pady=14)
        card_preview.pack(fill="x", pady=(14, 0))

        # Container für mittige Ausrichtung
        pv_container = tk.Frame(card_preview, bg=COLORS["panel"])
        pv_container.pack(fill="x")

        pv_container.grid_columnconfigure(0, weight=1)

        # Vorschau-Box (dunkel hervorgehoben)
        preview_box = tk.Frame(pv_container, bg=COLORS["panel"], padx=24, pady=18)
        preview_box.grid(row=0, column=0)

        # Titel
        tk.Label(
            preview_box,
            text="Vorschau",
            fg=COLORS["muted"],
            bg=COLORS["panel"],
            font=("Segoe UI", 9)
        ).pack(anchor="center")

        # Vorschautext
        tk.Label(
            preview_box,
            textvariable=self.preview_text,
            fg=COLORS["text"],
            bg=COLORS["panel"],
            font=("Segoe UI", 13, "bold"),
            justify="center"
        ).pack(anchor="center", pady=(8, 0))


                



        # ---------- Footer Buttons ----------
        

        # ---------- Schritt 4 ----------
        self.step_title(content, "4. Aktion ausführen")



        
        footer = self._standard_footer(
            p,
            start_cmd=self._run_sort,
            stop_cmd=self._stop_sort,
            third_cmd=self._undo_last_sort,
            analyse_cmd=self._learn_import_tags,
            preview_cmd=self._run_sort_simulation,
        )
        footer.pack(fill="x", side="bottom")
        





                
              

        
        self.mode_var.trace_add("write", self._update_structure_preview)
        self.structure_var.trace_add("write", self._update_structure_preview)
        self.mode_var.trace_add("write", self._update_structure_visibility)

        self._update_structure_preview()
        self._update_structure_visibility()





        return p


    # ------------------------------------------------------------
    # DUPLIKATE (CZKAWKA)
    # ------------------------------------------------------------

    def _page_duplicates(self, parent):
        p = tk.Frame(parent, bg=COLORS["bg"])
        p.pack_propagate(False)

        # ---------- HEADER ----------
        header = tk.Frame(p, bg=COLORS["panel"], padx=20, pady=16)
        header.pack(fill="x")
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        left = tk.Frame(header, bg=COLORS["panel"])
        left.grid(row=0, column=0, sticky="nw")

        tk.Label(
            left,
            text="Duplikate finden",
            fg=COLORS["text"],
            bg=COLORS["panel"],
            font=("Segoe UI", 22, "bold"),
        ).pack(anchor="w")

        tk.Label(
            left,
            text="Durchsucht einen Ordner nach identischen Dateien mit Czkawka.",
            fg=COLORS["muted"],
            bg=COLORS["panel"],
        ).pack(anchor="w", pady=(6, 0))

        info = self._create_info_card(
            header,
            "Doppelte Dateien finden",
            "Durchsucht einen Ordner nach identischen Bildern oder Videos. "
            "So kannst du Speicherplatz sparen und dein Archiv bereinigen.",
            "Archiv → 120 Duplikate erkannt",
        )
        info.grid(row=0, column=1, sticky="ne", padx=(40, 0))

        # ---------- CONTENT ----------
        content = tk.Frame(p, bg=COLORS["bg"])
        content.pack(fill="both", expand=True)



        # ---------- State ----------
        self.dup_folder_var = tk.StringVar()
        self.dup_mode = tk.StringVar(value="images")  # images oder all

        # ---------- Schritt 1 ----------
        self.step_title(content, "1. Ordner wählen")

        card = tk.Frame(content, bg=COLORS["panel"], padx=16, pady=14)
        card.pack(fill="x", padx=20)   # wichtig: gleicher left/right Abstand wie Header

        card.grid_columnconfigure(0, weight=0)
        card.grid_columnconfigure(1, weight=1)
        card.grid_columnconfigure(2, weight=0)

        tk.Label(card, text="Zu prüfen", fg=COLORS["muted"], bg=COLORS["panel"]).grid(
            row=0, column=0, sticky="w", pady=10
        )

        entry = tk.Entry(
            card,
            textvariable=self.dup_folder_var,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLORS["hover"],
            highlightcolor=COLORS["hover"],
        )
        entry.grid(row=0, column=1, sticky="ew", padx=(14, 10), pady=10, ipady=6)

        tk.Button(
            card,
            image=self.ICONS.get("folder"),
            text="",
            width=42,
            height=34,
            command=lambda: self._pick_dir(self.dup_folder_var),
            bg=COLORS["panel"],
            activebackground="#111b33",
            relief="flat",
            bd=0,
            highlightthickness=0,
        ).grid(row=0, column=2, sticky="e", pady=10)


        # ---------- Schritt 2 ----------
        self.step_title(content, "2. Suchtyp festlegen")

        opts_container = tk.Frame(content, bg=COLORS["bg"])
        opts_container.pack(fill="x", padx=20)

        opts = tk.Frame(opts_container, bg=COLORS["panel"], padx=16, pady=14)
        opts.pack(fill="x", pady=(8, 0))


        tk.Label(
            opts,
            text="Suchtyp",
            fg=COLORS["text"],
            bg=COLORS["panel"],
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w")

        tk.Radiobutton(
            opts, text="Nur Bilder",
            variable=self.dup_mode, value="images",
            bg=COLORS["panel"], fg=COLORS["text"],
            selectcolor=COLORS["bg"],
        ).pack(anchor="w")

        tk.Radiobutton(
            opts, text="Alle Dateien",
            variable=self.dup_mode, value="all",
            bg=COLORS["panel"], fg=COLORS["text"],
            selectcolor=COLORS["bg"],
        ).pack(anchor="w", pady=(0, 10))

        # ---------- Schritt 3 ----------
        self.step_title(content, "3. Scan starten")

        card_action = tk.Frame(content, bg=COLORS["panel"], padx=16, pady=14)
        card_action.pack(fill="x", pady=(8, 0))

        scan_btn = tk.Button(
            card_action,
            text="Duplikate finden",
            command=self._run_czkawka,
            bg=COLORS["accent"],
            fg="white",
            relief="flat",
            bd=0,
            height=3,
            font=("Segoe UI", 12, "bold"),
        )
        scan_btn.pack(fill="x")
        Tooltip(scan_btn, "Startet den Scan mit den oben gewählten Optionen.")

        # ---------- Ergebnisbereich (immer sichtbar) ----------
        self.dup_result_frame = tk.Frame(content, bg=COLORS["bg"])
        self.dup_result_frame.pack(fill="both", expand=True, pady=(14, 0))

        # ---------- Footer (immer sichtbar) ----------
        self.dup_footer = tk.Frame(p, bg=COLORS["bg"])
        self.dup_footer.pack(fill="x", side="bottom")



        self.dup_footer_inner = self._standard_footer(
            self.dup_footer,
            start_cmd=self._delete_duplicates,
            stop_cmd=None,
            third_cmd=self._undo_last_dup,
            third_icon="undo",
            show_top_buttons=False,
            start_tooltip="Löscht Duplikate gemäß gewählter Strategie."
        )

        self.dup_footer_inner.pack(fill="x", pady=(10, 0))

        # Treeview/Preview UI einmalig vorbereiten
        
        
        self._build_dup_results_ui()
        return p



    def _build_dup_results_ui(self):
        """Erstellt Treeview + Scrollbar im Ergebnisbereich (einmalig)."""

        for w in self.dup_result_frame.winfo_children():
            w.destroy()

        # Schritt-Titel
        self.step_title(self.dup_result_frame, "4. Ergebnis & Vorschau")

        # ---------- Aktionsleiste ----------
        action_bar = tk.Frame(
            self.dup_result_frame,
            bg=COLORS["panel"],
            padx=10,
            pady=10
        )
        self._dup_action_bar = action_bar  # wird später je nach Ergebnis ein/ausgeblendet
        self._dup_action_bar.pack(fill="x", pady=(10, 0))

        tk.Label(
            action_bar,
            text="Aktion für Duplikate:",
            fg=COLORS["text"],
            bg=COLORS["panel"],
            font=("Segoe UI", 11, "bold"),
        ).pack(side="left", padx=(0, 10))

        self.dup_delete = tk.StringVar(value="newest")

        tk.Radiobutton(
            action_bar,
            text="Behalte neueste",
            variable=self.dup_delete,
            value="newest",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            selectcolor=COLORS["bg"],
        ).pack(side="left", padx=6)

        tk.Radiobutton(
            action_bar,
            text="Behalte älteste",
            variable=self.dup_delete,
            value="oldest",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            selectcolor=COLORS["bg"],
        ).pack(side="left", padx=6)

        # ---------- Vorschau/Tree ----------
        preview_panel = tk.Frame(
            self.dup_result_frame,
            bg=COLORS["panel"],
            padx=10,
            pady=10
        )
        preview_panel.pack(fill="both", expand=True)

        table_frame = tk.Frame(preview_panel, bg=COLORS["panel"])
        table_frame.pack(fill="both", expand=True)

        scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical")
        scrollbar_y.pack(side="right", fill="y")

        self.dup_tree = ttk.Treeview(
            table_frame,
            columns=("size", "path"),
            show="tree headings",
            yscrollcommand=scrollbar_y.set
        )

        self.dup_tree.heading("#0", text="Datei / Gruppe")
        self.dup_tree.heading("size", text="Größe")

        self.dup_tree.column("#0", width=700)
        self.dup_tree.column("size", width=120, anchor="e")

        # "path" ist unsichtbar, nur als Datenspeicher
        self.dup_tree.column("path", width=0, stretch=False)

        self.dup_tree.pack(side="left", fill="both", expand=True)
        scrollbar_y.config(command=self.dup_tree.yview)

        def _on_dup_select(event):
            sel = self.dup_tree.selection()
            if not sel:
                return

            item = sel[0]
            parent = self.dup_tree.parent(item)

            if parent == "":
                return  # Gruppe → kein Thumbnail

            path = self.dup_tree.item(item, "values")[1]  # (size, path)
            if path and os.path.isfile(path):
                self.show_thumbnail(path)

        self.dup_tree.bind("<<TreeviewSelect>>", _on_dup_select)



    def _run_czkawka(self):
        self._start_log("duplikate")
        folder = self.dup_folder_var.get()

        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Fehler", "Bitte gültigen Ordner wählen.")
            return

        CZKAWKA_PATH = resource_path("tools/czkawka_cli.exe")

        if not os.path.isfile(CZKAWKA_PATH):
            messagebox.showerror("Fehler", f"Czkawka nicht gefunden:\n{CZKAWKA_PATH}")
            return

        self.ui(self.status_text.set, "Suche Duplikate…")
        self.ui(self.detail_text.set,os.path.basename(folder))

        # Tabelle leeren
        for i in self.dup_tree.get_children():
            self.dup_tree.delete(i)

        total_files = 0
        for root, _, files in os.walk(folder):
            total_files += len(files)

        self._czkawka_total = max(total_files, 1)


        def worker():

            start_time = time.time()
            self._czkawka_running = True

            def start_status_timer():
                def update_status():
                    if not self._czkawka_running:
                        return

                    result_file = os.path.join(self.app_dir, "czkawka_result.json")

                    processed = 0
                    if os.path.isfile(result_file):
                        try:
                            with open(result_file, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            for size_group in data.values():
                                for dup_group in size_group:
                                    processed += len(dup_group)
                        except Exception:
                            pass

                    total = getattr(self, "_czkawka_total", 1)
                    percent = int((processed / total) * 100) if total else 0

                    self.progress_val.set(min(percent, 99))
                    self.percent_text.set(f"{percent} %")

                    self.status_text.set(f"Suche Duplikate… {percent} %")

                    self._czkawka_timer = self.after(1000, update_status)

                update_status()


            self.ui(start_status_timer)


                        



            try:
                result_file = os.path.join(self.app_dir, "czkawka_result.json")

                args = [
                    CZKAWKA_PATH,
                    "dup",
                    "-d", folder,
                    "-s", "HASH",
                    "-p", result_file
                ]

                if self.dup_mode.get() == "images":
                    args += ["-x", "IMAGE"]

                # Scan vollständig ausführen
                self._czkawka_proc = subprocess.Popen(
                    args,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                self._czkawka_proc.wait()
                self._czkawka_running = False


                # Prüfen ob Ergebnis existiert
                if not os.path.isfile(result_file):
                    self._czkawka_running = False
                    self.after(0, lambda: self.ui(self.status_text.set,"Keine Duplikate gefunden"))
                    return

                # JSON laden
                with open(result_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                def fill_tree():

                    # --- Sicherstellen dass Tree existiert ---
                    if not hasattr(self, "dup_tree"):
                        messagebox.showerror("Fehler", "Duplikat-UI nicht initialisiert.")
                        return

                    # --- Variablen initialisieren ---
                    group_counter = 0
                    count = 0
                    paths_for_preload = []

                    # --- Tree leeren ---
                    for i in self.dup_tree.get_children():
                        self.dup_tree.delete(i)

                    # --- Daten durchlaufen ---
                    for size_group in data.values():
                        for dup_group in size_group:

                            if len(dup_group) < 2:
                                continue

                            group_counter += 1

                            size_value = dup_group[0].get("size", 0)
                            size_mb = round(int(size_value) / 1024 / 1024, 2)

                            group_title = f"{len(dup_group)}× Duplikat-Gruppe #{group_counter} ({size_mb} MB)"

                            parent_id = self.dup_tree.insert(
                                "",
                                "end",
                                text=group_title,
                                values=(f"{size_mb} MB", "")
                            )

                            for item in dup_group:
                                pth = item.get("path", "")
                                sz  = item.get("size", 0)

                                self.dup_tree.insert(
                                    parent_id,
                                    "end",
                                    text=os.path.basename(pth),
                                    values=(round(int(sz) / 1024 / 1024, 2), pth)
                                )

                                if pth:
                                    paths_for_preload.append(pth)

                                count += 1

                    
                    # --- Status ---
                    if group_counter == 0:
                        self.status_text.set("Keine Duplikate gefunden")
                        self.dup_result.set("Keine Duplikate gefunden.")
                    else:
                        self.status_text.set(f"{count} Dateien in Duplikaten gefunden")
                        self.dup_result.set(f"{count} Dateien gehören zu Duplikat-Gruppen.")

                    self.detail_text.set("")
                    self.progress_val.set(100)
                    self.percent_text.set("100 %")

                    # --- Thumbnails ---
                    if paths_for_preload:
                        self._preload_thumbnails(paths_for_preload, limit=200)

                                    # UI-Update ausführen
                self.ui(fill_tree)

            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Fehler", str(e)))
                self.after(0, lambda: self.ui(self.status_text.set, "Fehler bei Duplikat-Scan"))

        threading.Thread(target=worker, daemon=True).start()


    def _stop_czkawka(self):
        self._czkawka_running = False

        if hasattr(self, "_czkawka_timer"):
            try:
                self.after_cancel(self._czkawka_timer)
            except Exception:
                pass

        if hasattr(self, "_czkawka_proc") and self._czkawka_proc:
            try:
                self._czkawka_proc.terminate()
            except Exception:
                pass

        self.ui(self.status_text.set,"Duplikat-Scan abgebrochen")


    def _safe_mtime(self, path: str) -> float:
        try:
            return os.path.getmtime(path)
        except Exception:
            return 0.0


    def _delete_duplicates(self):
        folder = self.dup_folder_var.get()
        result_file = os.path.join(self.app_dir, "czkawka_result.json")

        if not os.path.isfile(result_file):
            messagebox.showerror("Fehler", "Keine Ergebnisdatei gefunden. Erst scannen.")
            return

        mode = self.dup_delete.get()
        if mode == "none":
            messagebox.showinfo("Hinweis", "Keine Lösch-Aktion gewählt.")
            return

        if not messagebox.askyesno("Sicher?", "Wirklich Duplikate löschen?"):
            return

        try:
            with open(result_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            deleted = 0

            for groups in data.values():
                for group in groups:

                    # nach Datum sortieren
                    group.sort(key=lambda x: self._safe_mtime(x.get("path", "")))



                    if mode == "newest":
                        to_delete = group[:-1]   # alles außer neueste
                    elif mode == "oldest":
                        to_delete = group[1:]    # alles außer älteste
                    else:
                        continue

                    for fileinfo in to_delete:
                        try:
                            src = fileinfo["path"]
                            filename = os.path.basename(src)
                            trash_path = os.path.join(self.dup_trash_dir, filename)

                            counter = 1
                            name, ext = os.path.splitext(filename)
                            while os.path.exists(trash_path):
                                trash_path = os.path.join(self.dup_trash_dir, f"{name}_{counter}{ext}")
                                counter += 1

                            shutil.move(src, trash_path)
                            self._last_dup_ops.append((trash_path, src))
                            deleted += 1

                            self._log_line(f"DELETE: {fileinfo['path']}")
                        except Exception:
                            pass
                    
            self._run_czkawka()
            messagebox.showinfo("Fertig", f"{deleted} Dateien gelöscht.")
            self.ui(self.status_text.set,"Duplikate bereinigt")

        except Exception as e:
            messagebox.showerror("Fehler", str(e))

            

    
# ------------------------------------------------------------
    # UNSORTIERT ANALYSE
    # ------------------------------------------------------------

    def _page_unsorted(self, parent):
        p = tk.Frame(parent, bg=COLORS["bg"])
        p.pack_propagate(False)

        # ---------- HEADER ----------
        header = tk.Frame(p, bg=COLORS["panel"], padx=20, pady=16)
        header.pack(fill="x")
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        left = tk.Frame(header, bg=COLORS["panel"])
        left.grid(row=0, column=0, sticky="nw")

        tk.Label(
            left,
            text="Unsortierte Dateien",
            fg=COLORS["text"],
            bg=COLORS["panel"],
            font=("Segoe UI", 22, "bold"),
        ).pack(anchor="w")

        tk.Label(
            left,
            text="Analysiert Dateien ohne klares Datum und schlägt Zielordner vor.",
            fg=COLORS["muted"],
            bg=COLORS["panel"],
        ).pack(anchor="w", pady=(6, 0))

        info = self._create_info_card(
            header,
            "Unsortierte Dateien prüfen",
            "Analysiert Dateien ohne klares Datum und schlägt passende Zielordner vor.",
            "Unsortiert → Archiv/2023/11",
        )
        info.grid(row=0, column=1, sticky="ne", padx=(40, 0))


        # ---------- SCROLL-CONTAINER ----------
        scroll_container = tk.Frame(p, bg=COLORS["bg"])
        scroll_container.pack(fill="both", expand=True)
        # ---------- FESTER ERGEBNISBEREICH ----------
        result_area = tk.Frame(p, bg=COLORS["bg"])
        result_area.pack(fill="both", expand=False)


        canvas = tk.Canvas(scroll_container, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        content_outer = tk.Frame(canvas, bg=COLORS["bg"])
        content_window = canvas.create_window((0, 0), window=content_outer, anchor="nw")

        content = tk.Frame(content_outer, bg=COLORS["bg"])
        content.pack(fill="both", expand=True, padx=20)

        def _resize_content(event):
            canvas.itemconfig(content_window, width=event.width)

        canvas.bind("<Configure>", _resize_content)
        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=scrollbar.set)


        # ---------- STATE ----------
        self.unsorted_var = tk.StringVar()

        if not hasattr(self, "archiv_var"):
            self.archiv_var = tk.StringVar()


        # ---------- Schritt 1 ----------
        self.step_title(content, "1. Ordner wählen")

        card_paths = tk.Frame(content, bg=COLORS["panel"], padx=16, pady=14)
        card_paths.pack(fill="x")

        card_paths.grid_columnconfigure(0, weight=0)
        card_paths.grid_columnconfigure(1, weight=1)
        card_paths.grid_columnconfigure(2, weight=0)

        def field_row(r, label, var, icon_key="folder"):
            tk.Label(card_paths, text=label, fg=COLORS["muted"], bg=COLORS["panel"]).grid(
                row=r, column=0, sticky="w", pady=10
            )

            e = tk.Entry(
                card_paths,
                textvariable=var,
                bg=COLORS["panel"],
                fg=COLORS["text"],
                insertbackground=COLORS["text"],
                relief="flat",
                highlightthickness=1,
                highlightbackground=COLORS["hover"],
                highlightcolor=COLORS["hover"],
            )
            e.grid(row=r, column=1, sticky="ew", padx=(14, 10), pady=10, ipady=6)

            tk.Button(
                card_paths,
                image=self.ICONS.get(icon_key),
                command=lambda v=var: self._pick_dir(v),
                bg=COLORS["panel"],
                relief="flat",
                bd=0,
                highlightthickness=0,
            ).grid(row=r, column=2, sticky="e", pady=10)

        field_row(0, "Unsortiert-Ordner", self.unsorted_var)
        field_row(1, "Archiv", self.archiv_var)


        # ---------- Schritt 2 ----------
        self.step_title(content, "2. Analyse starten")

        card_action = tk.Frame(content, bg=COLORS["panel"], padx=16, pady=14)
        card_action.pack(fill="x", pady=(14, 0))

        start_btn = tk.Button(
            card_action,
            text="Analyse starten",
            command=self._run_unsorted_analysis,
            bg=COLORS["accent"],
            fg="white",
            relief="flat",
            bd=0,
            height=3,
            font=("Segoe UI", 12, "bold"),
        )
        start_btn.pack(fill="x")

        Tooltip(start_btn, "Durchsucht den Unsortiert-Ordner und analysiert mögliche Zielordner.")


        # ---------- Schritt 3 ----------
        self.step_title(result_area, "3. Ergebnis")

        self.unsorted_result_box = tk.Text(
            result_area,
            height=4,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            relief="flat",
            highlightthickness=0,
        )
        self.unsorted_result_box.pack(fill="x", padx=20, pady=(8, 6))


        self.unsorted_result_box.insert("1.0", "Noch keine Analyse durchgeführt.")
        self.unsorted_result_box.configure(state="disabled")


        # ---------- FOOTER ----------
        

        return p


    def _preview_unsorted(self):
        folder = self.unsorted_var.get()
        archiv = self.archiv_var.get() if hasattr(self, "archiv_var") else ""

        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Fehler", "Bitte gültigen Unsortiert-Ordner wählen.")
            return

        if not archiv or not os.path.isdir(archiv):
            messagebox.showerror("Fehler", "Bitte gültiges Archiv im Sortieren-Tab wählen.")
            return

        if hasattr(self, "_unsorted_preview_frame") and self._unsorted_preview_frame.winfo_exists():
            self._unsorted_preview_frame.destroy()

        preview_frame = tk.Frame(self.pages["uns"], bg=COLORS["panel"])
        preview_frame.pack(fill="both", expand=True, pady=(16, 0))
        self._unsorted_preview_frame = preview_frame

        
        # ---------- TABELLE ----------
        
        style = ttk.Style()
        style.theme_use("default")

        style.configure("Treeview", font=("Segoe UI Emoji", 10))


        style.configure("Treeview.Heading",
            background=COLORS["panel"],
            foreground=COLORS["text"],
            relief="flat"
        )

        style.map("Treeview.Heading",
            background=[("active", COLORS["hover"])]
        )

        # Container für Tree + Scrollbar
        table_frame = tk.Frame(preview_frame, bg=COLORS["panel"])
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)


       # ---------- Tree + Scrollbar Container ----------
        tree = ttk.Treeview(
            table_frame,
            columns=("del", "namechk", "filechk", "nonechk", "file", "target", "year", "month", "unsure"),
            show="headings"
        )


        tree.tag_configure("name_date", background="#163d2b")
        tree.tag_configure("file_date", background="#3a2e12")
        tree.tag_configure("no_date", background="#3d1f1f")

        self._preview_tree = tree

        def toggle_checkbox(event):
            item = tree.identify_row(event.y)
            col = tree.identify_column(event.x)

            if not item:
                return

            # Checkbox-Spalten sind #2, #3, #4
            col_map = {"#2": 1, "#3": 2, "#4": 3}
            if col not in col_map:
                return

            vals = list(tree.item(item, "values"))
            idx = col_map[col]

            # Wenn die angeklickte Checkbox schon aktiv ist → alles abwählen
            if vals[idx] == "☑":
                vals[1] = vals[2] = vals[3] = "☐"

            else:
                # sonst nur diese aktivieren
                vals[1] = vals[2] = vals[3] = "☐"
                vals[idx] = "☑"

            tree.item(item, values=vals)







        def select_column(col_index):
            # col_index: 0=namechk, 1=filechk, 2=nonechk
            tag_map = {0: "name_date", 1: "file_date", 2: "no_date"}
            wanted_tag = tag_map[col_index]

            check_pos = col_index + 1  # weil Checkboxen in values[1..3] liegen

            # Prüfen: sind alle passenden schon aktiv?
            all_active = True
            for item in tree.get_children():
                tags = tree.item(item, "tags")
                vals = tree.item(item, "values")
                if wanted_tag in tags and vals[check_pos] != "☑":
                    all_active = False
                    break

            for item in tree.get_children():
                vals = list(tree.item(item, "values"))
                tags = tree.item(item, "tags")

                # nur Checkboxen resetten
                vals[1] = vals[2] = vals[3] = "☐"

                # zweiter Klick: alles leer lassen, sonst passende setzen
                if not all_active and wanted_tag in tags:
                    vals[check_pos] = "☑"

                tree.item(item, values=vals)







        tree.heading("del", text="")  # Kopf leer, weil Emoji in den Zeilen steht
        tree.heading("namechk", text="Datum im Namen", command=lambda: select_column(0))
        tree.heading("filechk", text="Dateidatum", command=lambda: select_column(1))
        tree.heading("nonechk", text="Kein Datum", command=lambda: select_column(2))


        tree.column("del", width=45, anchor="center", stretch=False)
        tree.column("namechk", width=60, anchor="center")
        tree.column("filechk", width=60, anchor="center")
        tree.column("nonechk", width=60, anchor="center")

        tree.heading("file", text="Datei")
        tree.heading("target", text="Zielordner")

        tree.column("year", width=0, stretch=False)
        tree.column("month", width=0, stretch=False)
        tree.column("unsure", width=0, stretch=False)

        # Vertikale Scrollbar
        scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical")
        scrollbar_y.pack(side="right", fill="y")

        tree.pack(side="left", fill="both", expand=True)

        def _on_unsorted_select(event):
            sel = tree.selection()
            if not sel:
                return

            # Dateiname steht in Spalte 3
            filename = tree.item(sel[0], "values")[4]

            # echten Pfad im Unsortiert-Ordner suchen
            for root, _, files in os.walk(self.unsorted_var.get()):
                if filename in files:
                    self.show_thumbnail(os.path.join(root, filename))
                    break

        tree.bind("<<TreeviewSelect>>", _on_unsorted_select)


        scrollbar_y.config(command=tree.yview)
        tree.configure(yscrollcommand=scrollbar_y.set)

                                    

        # ---------- DATEIEN LADEN ----------
        for root, _, files in os.walk(folder):
            for f in files[:500]:
                src = os.path.join(root, f)

                try:
                    ts = os.path.getmtime(src)
                    t = time.localtime(ts)
                    year = str(t.tm_year)
                    month = f"{t.tm_mon:02d}"
                    unsure = "1"
                    target = f"{year}/{month} (unsicher)"
                except Exception:
                    year, month, unsure, target = "?", "?", "1", "Unbekannt"

                name_lower = f.lower()
                has_name_date = ("20" in name_lower and any(c.isdigit() for c in name_lower))

                # Tag bestimmen für Farbe
                if year == "?" or month == "?":
                    tag = "no_date"
                    namechk, filechk, nonechk = "☐", "☐", "☑"
                elif has_name_date:
                    tag = "name_date"
                    namechk, filechk, nonechk = "☑", "☐", "☐"
                else:
                    tag = "file_date"
                    namechk, filechk, nonechk = "☐", "☑", "☐"

                tree.insert(
                    "", "end",
                    values=("🗑", namechk, filechk, nonechk, f, target, year, month, unsure),
                    tags=(tag,)
                )




        
        def on_tree_click(event):
            item = tree.identify_row(event.y)
            col = tree.identify_column(event.x)

            if not item:
                return

            # Papierkorb ist Spalte #1
            if col == "#1":
                vals = tree.item(item, "values")
                filename = vals[4]  # file-Spalte

                src = None
                for root, _, files in os.walk(self.unsorted_var.get()):
                    if filename in files:
                        src = os.path.join(root, filename)
                        break

                if not src:
                    return

                if messagebox.askyesno("Löschen?", f"{filename} wirklich löschen?"):
                    try:
                        os.remove(src)
                        tree.delete(item)
                    except Exception as e:
                        messagebox.showerror("Fehler", str(e))
                return

            # sonst Checkbox
            toggle_checkbox(event)

        tree.bind("<Button-1>", on_tree_click)




        # ---------- BUTTONLEISTE ----------
       
        control = tk.Frame(preview_frame, bg=COLORS["panel"])
        control.pack(fill="x", padx=10, pady=(0, 10))

        target_var = tk.StringVar(value="Jahr/Monat (unsicher)")

        style = ttk.Style()
        style.configure("Tall.TCombobox", padding=(6, 10))  


        dropdown = ttk.Combobox(control, textvariable=target_var, state="readonly", style="Tall.TCombobox")
        dropdown["values"] = [
            "Jahr/Monat",
            "Jahr/Monat (unsicher)",
            "WhatsApp/Jahr/Monat",
            "Screenshots/Jahr/Monat",
        ]
        dropdown.pack(side="left")

        Tooltip(dropdown, "Wählt den Zieltyp für die markierten Dateien.")



        self._unsorted_stop = False
        self._last_moves = []

        def apply_target():
            for item in tree.get_children():
                vals = list(tree.item(item, "values"))

                # Nur wenn Checkbox aktiv
                if "☑" not in vals[1:4]:
                    continue

                choice = target_var.get()

                if choice.startswith("WhatsApp"):
                    vals[5] = f"WhatsApp/{vals[6]}/{vals[7]}"
                    vals[8] = "0"

                elif choice.startswith("Screenshots"):
                    vals[5] = f"Screenshots/{vals[6]}/{vals[7]}"
                    vals[8] = "0"

                elif "unsicher" in choice:
                    vals[5] = f"{vals[6]}/{vals[7]} (unsicher)"
                    vals[8] = "1"

                else:
                    vals[5] = f"{vals[6]}/{vals[7]}"
                    vals[8] = "0"

                tree.item(item, values=vals)


        def start_move():
            self._unsorted_stop = False
            archiv_path = self.archiv_var.get()

            def worker():
                for item in list(tree.get_children()):
                    if self._unsorted_stop:
                        break

                    vals = tree.item(item, "values")
                    if "☑" not in vals[1:4]:
                        continue

                    filename, target, year, month, unsure = vals[4], vals[5], vals[6], vals[7], vals[8]

                    src = None
                    for root, _, files in os.walk(self.unsorted_var.get()):
                        if filename in files:
                            src = os.path.join(root, filename)
                            break

                    if not src:
                        continue

                    month_name = MONTH_NAMES.get(month, month)

                    if target.startswith("WhatsApp"):
                        target_dir = os.path.join(archiv_path, "WhatsApp", year, month_name)
                    elif target.startswith("Screenshots"):
                        target_dir = os.path.join(archiv_path, "Screenshots", year, month_name)
                    elif unsure == "1":
                        target_dir = os.path.join(archiv_path, f"{year}_unsicher", month_name)
                    else:
                        target_dir = os.path.join(archiv_path, year, month_name)



                    os.makedirs(target_dir, exist_ok=True)

                    dest = os.path.join(target_dir, filename)
                    counter = 1
                    name, ext = os.path.splitext(filename)

                    while os.path.exists(dest):
                        dest = os.path.join(target_dir, f"{name}_{counter}{ext}")
                        counter += 1

                    shutil.move(src, dest)
                    self._last_moves.append((dest, src))

                    self.after(0, lambda i=item: tree.delete(i))

            threading.Thread(target=worker, daemon=True).start()

        def stop_move():
            self._unsorted_stop = True
    


        def undo_last():
            for dest, src in reversed(self._last_moves):
                try:
                    os.makedirs(os.path.dirname(src), exist_ok=True)
                    shutil.move(dest, src)
                except Exception:
                    pass
            self._last_moves.clear()

        btnbar = tk.Frame(control, bg=COLORS["panel"])
        btnbar.pack(fill="x", pady=(8, 0))

        for i in range(4):
            btnbar.grid_columnconfigure(i, weight=1)

        apply_btn = tk.Button(
            btnbar,
            image=self.ICONS.get("apply"),
            command=apply_target,
            bg=COLORS["bg"],
            relief="flat",
            bd=0,
            height=44
        )
        apply_btn.grid(row=0, column=0, sticky="ew", padx=4)

        Tooltip(apply_btn, "Übernimmt das gewählte Ziel für markierte Dateien.")


        start_move_btn = tk.Button(
            btnbar,
            image=self.ICONS.get("start"),
            command=start_move,
            bg=COLORS["accent"],
            relief="flat",
            bd=0,
            height=44
        )
        start_move_btn.grid(row=0, column=1, sticky="ew", padx=4)

        Tooltip(start_move_btn, "Verschiebt die markierten Dateien ins Archiv.")

        stop_btn = tk.Button(
            btnbar,
            image=self.ICONS.get("stop"),
            command=stop_move,
            bg=COLORS["panel"],
            relief="flat",
            bd=0,
            height=44
        )
        stop_btn.grid(row=0, column=2, sticky="ew", padx=4)

        Tooltip(stop_btn, "Bricht den aktuellen Verschiebevorgang ab.")
        
        
        undo_btn = tk.Button(
            btnbar,
            image=self.ICONS.get("undo"),
            command=undo_last,
            bg=COLORS["bg"],
            relief="flat",
            bd=0,
            height=44
        )
        undo_btn.grid(row=0, column=3, sticky="ew", padx=4)

        Tooltip(undo_btn, "Macht die letzte Verschiebung rückgängig.")


    def _apply_unsorted(self):
        if not hasattr(self, "_preview_tree") or not self._preview_tree.winfo_exists():
            messagebox.showerror("Fehler", "Bitte zuerst die Vorschau öffnen.")
            return

        tree = self._preview_tree
        archiv = self.archiv_var.get()

        moved = []
        remaining = []

        for item in tree.get_children():
            check, filename, target = tree.item(item, "values")
            if check != "☑":
                continue

            src = None
            for root, _, files in os.walk(self.unsorted_var.get()):
                if filename in files:
                    src = os.path.join(root, filename)
                    break

            if not src:
                remaining.append(filename)
                continue

            try:
                year, month = target.split("/")
                month_name = MONTH_NAMES.get(month, month)

                target_dir = os.path.join(archiv, year, month)
                os.makedirs(target_dir, exist_ok=True)

                dest = os.path.join(target_dir, filename)
                counter = 1
                name, ext = os.path.splitext(filename)

                while os.path.exists(dest):
                    dest = os.path.join(target_dir, f"{name}_{counter}{ext}")
                    counter += 1

                shutil.move(src, dest)
                moved.append(filename)
            except Exception:
                remaining.append(filename)

        # Ergebnisliste
        win = tk.Toplevel(self)
        win.title("Unsortiert verarbeitet")
        win.geometry("500x400")

        lb = tk.Listbox(win)
        lb.pack(fill="both", expand=True, padx=10, pady=10)

        for f in moved:
            lb.insert("end", f"✔ {f}")

        if remaining:
            lb.insert("end", "--- Fehler ---")
            for f in remaining:
                lb.insert("end", f"✖ {f}")

    def _run_unsorted_analysis(self):
        self._unsorted_stop = False
        self._start_log("unsortiert")

        folder = self.unsorted_var.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Fehler", "Bitte gültigen Unsortiert-Ordner wählen.")
            return

        archiv = self.archiv_var.get()
        if not archiv or not os.path.isdir(archiv):
            messagebox.showerror("Fehler", "Bitte gültigen Archiv-Ordner wählen.")
            return


        def worker():
            try:
                all_files = []
                for root, _, files in os.walk(folder):
                    for f in files:
                        all_files.append(os.path.join(root, f))

                total = len(all_files)
                with_name_date = 0
                with_file_date = 0
                unknown = 0

                start_time = time.time()

                for idx, path in enumerate(all_files, start=1):
                    if self._unsorted_stop:
                        self.ui(self.status_text.set, "Analyse abgebrochen")
                        self.ui(self.detail_text.set, "")
                        return

                    f = os.path.basename(path)
                    name = f.lower()

                    elapsed = time.time() - start_time
                    avg = elapsed / idx if idx else 0
                    remaining = int(avg * (total - idx))
                    mins, secs = divmod(remaining, 60)

                    self.ui(self.status_text.set, f"Analysiere Unsortiert – Datei {idx}/{total} – Restzeit {mins:02d}:{secs:02d}")
                    self.ui(self.detail_text.set, f)

                    if any(char.isdigit() for char in name) and "20" in name:
                        with_name_date += 1
                    else:
                        try:
                            os.path.getmtime(path)
                            with_file_date += 1
                        except Exception:
                            unknown += 1

                # Ergebnistext in UI schreiben (thread-safe)
                def update_box():
                    self.unsorted_result_box.configure(state="normal")
                    self.unsorted_result_box.delete("1.0", "end")

                    self.unsorted_result_box.insert("end", f"Dateien gesamt: {total}\n")
                    self.unsorted_result_box.insert("end", "● Datum im Namen erkannt: ")
                    self.unsorted_result_box.insert("end", f"{with_name_date}\n", "name")
                    self.unsorted_result_box.insert("end", "● Nur Dateidatum vorhanden: ")
                    self.unsorted_result_box.insert("end", f"{with_file_date}\n", "file")
                    self.unsorted_result_box.insert("end", "● Kein Hinweis auf Datum: ")
                    self.unsorted_result_box.insert("end", f"{unknown}", "none")

                    self.unsorted_result_box.tag_config("name", foreground="#22c55e")
                    self.unsorted_result_box.tag_config("file", foreground="#eab308")
                    self.unsorted_result_box.tag_config("none", foreground="#ef4444")
                    self.unsorted_result_box.configure(state="disabled")

                self.ui(self.status_text.set, "Analyse abgeschlossen")
                self.ui(self.detail_text.set, "")
                self.ui(update_box)

                # Vorschau öffnen (UI-thread)
                self.ui(lambda: self.after(100, self._preview_unsorted))

            except Exception as e:
                self.ui(messagebox.showerror, "Fehler", str(e))
                self.ui(self.status_text.set, "Fehler")
                self.ui(self.detail_text.set, "")

        threading.Thread(target=worker, daemon=True).start()



    # ------------------------------------------------------------
    # LOGS
    # ------------------------------------------------------------

    def _page_logs(self, parent):
        p = tk.Frame(parent, bg=COLORS["bg"])
        p.pack_propagate(False)

        # ---------- HEADER ----------
        header = tk.Frame(p, bg=COLORS["panel"], padx=20, pady=16)
        header.pack(fill="x")
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        left = tk.Frame(header, bg=COLORS["panel"])
        left.grid(row=0, column=0, sticky="nw")

        tk.Label(
            left,
            text="Logs",
            fg=COLORS["text"],
            bg=COLORS["panel"],
            font=("Segoe UI", 22, "bold"),
        ).pack(anchor="w")

        tk.Label(
            left,
            text="Zeigt die letzten Aktionen des FotoTools an.",
            fg=COLORS["muted"],
            bg=COLORS["panel"],
        ).pack(anchor="w", pady=(6, 0))

        info = self._create_info_card(
            header,
            "Protokolle anzeigen",
            "Hier findest du alle Aktionen, Fehler und Abläufe des Programms.",
            "sort_2026-02-12_18-33.txt",
        )
        info.grid(row=0, column=1, sticky="ne", padx=(40, 0))

        # ---------- SCROLL-CONTAINER ----------
        scroll_container = tk.Frame(p, bg=COLORS["bg"])
        scroll_container.pack(fill="both", expand=True)

        canvas = tk.Canvas(scroll_container, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        content_outer = tk.Frame(canvas, bg=COLORS["bg"])
        content_window = canvas.create_window((0, 0), window=content_outer, anchor="nw")

        content = tk.Frame(content_outer, bg=COLORS["bg"])
        content.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        def _on_canvas_configure(event):
            # WICHTIG: Breite UND Höhe an Viewport anpassen
            canvas.itemconfig(content_window, width=event.width, height=event.height)

        canvas.bind("<Configure>", _on_canvas_configure)

        content_outer.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.configure(yscrollcommand=scrollbar.set)


        # ---------- LISTE ----------
        self.step_title(content, "1. Logdatei auswählen")

        self.log_list = tk.Listbox(content, height=8, bg=COLORS["panel"], fg=COLORS["text"])
        self.log_list.pack(fill="x")

        # ---------- INHALT ----------
        self.step_title(content, "2. Inhalt anzeigen")

        self.log_text = tk.Text(
            content,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            wrap="word",
            relief="flat"
        )
        
        self.log_text.pack(fill="both", expand=True, pady=(8, 20))




        # ---------- BUTTONS ----------
        btn_frame = tk.Frame(content, bg=COLORS["bg"])
        btn_frame.pack(anchor="w", pady=12)

        tk.Button(btn_frame, text="Liste aktualisieren", command=self._refresh_log_list,
                bg=COLORS["accent"], fg="white").pack(side="left")

        tk.Button(btn_frame, text="Log anzeigen", command=self._open_selected_log,
                bg=COLORS["panel"], fg=COLORS["text"]).pack(side="left", padx=8)

        tk.Button(btn_frame, text="Logs löschen", command=self._clear_logs,
                bg=COLORS["panel"], fg=COLORS["text"]).pack(side="left", padx=8)

        return p


    def _refresh_log_list(self):
        self.log_list.delete(0, "end")
        for name in sorted(os.listdir(self.logs_dir)):
            if name.endswith(".txt"):
                self.log_list.insert("end", name)

    def _open_selected_log(self):
        sel = self.log_list.curselection()
        if not sel:
            return
        name = self.log_list.get(sel[0])
        path = os.path.join(self.logs_dir, name)

        self.log_text.delete("1.0", "end")
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.log_text.insert("1.0", f.read())
        except Exception as e:
            self.log_text.insert("end", f"Fehler beim Laden: {e}")

    def _load_logs(self):
        log_file = os.path.join(BASE_DIR, "fototool.log")
        self.log_text.delete("1.0", "end")

        if not os.path.isfile(log_file):
            self.log_text.insert("end", "Noch keine Logs vorhanden.")
            return

        try:
            with open(log_file, "r", encoding="utf-8") as f:
                self.log_text.insert("end", f.read())
        except Exception as e:
            self.log_text.insert("end", f"Fehler beim Laden der Logs: {e}")

    def _clear_logs(self):
        for name in os.listdir(self.logs_dir):
            try:
                os.remove(os.path.join(self.logs_dir, name))
            except Exception:
                pass
        self.log_list.delete(0, "end")
        self.log_text.delete("1.0", "end")

    def _clear_logs_old(self):
        log_file = os.path.join(BASE_DIR, "fototool.log")
        try:
            if os.path.isfile(log_file):
                os.remove(log_file)
            self.log_text.delete("1.0", "end")
            self.log_text.insert("end", "Logs gelöscht.")
        except Exception as e:
            messagebox.showerror("Fehler", str(e))




    # ------------------------------------------------------------
    # LIZENZEN
    # ------------------------------------------------------------

    def _page_licenses(self, parent):
        p = tk.Frame(parent, bg=COLORS["bg"])
        p.pack_propagate(False)

        # ---------- HEADER ----------
        header = tk.Frame(p, bg=COLORS["panel"], padx=20, pady=16)
        header.pack(fill="x")
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        left = tk.Frame(header, bg=COLORS["panel"])
        left.grid(row=0, column=0, sticky="nw")

        tk.Label(
            left,
            text="Lizenzen",
            fg=COLORS["text"],
            bg=COLORS["panel"],
            font=("Segoe UI", 22, "bold"),
        ).pack(anchor="w")

        tk.Label(
            left,
            text="Open-Source-Software und deren Lizenzbedingungen.",
            fg=COLORS["muted"],
            bg=COLORS["panel"],
        ).pack(anchor="w", pady=(6, 0))

        info = self._create_info_card(
            header,
            "Open-Source-Komponenten",
            "FotoTool nutzt externe Bibliotheken. "
            "Hier findest du die vollständigen Lizenztexte.",
            "ExifTool · Czkawka · Pillow",
        )
        info.grid(row=0, column=1, sticky="ne", padx=(40, 0))


        # ---------- SCROLL-CONTAINER ----------
        scroll_container = tk.Frame(p, bg=COLORS["bg"])
        scroll_container.pack(fill="both", expand=True)

        canvas = tk.Canvas(scroll_container, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        content_outer = tk.Frame(canvas, bg=COLORS["bg"])
        content_window = canvas.create_window((0, 0), window=content_outer, anchor="nw")

        content = tk.Frame(content_outer, bg=COLORS["bg"])
        content.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        def _on_canvas_configure(event):
            # WICHTIG: Breite UND Höhe an Viewport anpassen
            canvas.itemconfig(content_window, width=event.width, height=event.height)

        canvas.bind("<Configure>", _on_canvas_configure)

        content_outer.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.configure(yscrollcommand=scrollbar.set)



        # ---------- SCHRITT ----------
        self.step_title(content, "Lizenztexte")

        container = tk.Frame(content, bg=COLORS["bg"])
        container.pack(fill="both", expand=True, pady=(8, 0))

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        text = tk.Text(
            container,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            wrap="word",
            relief="flat",
            padx=12,
            pady=12,
        )
        text.grid(row=0, column=0, sticky="nsew")



        LICENSE_DIR = resource_path("licenses")

        contents = []

        if os.path.isdir(LICENSE_DIR):
            for name in sorted(os.listdir(LICENSE_DIR)):
                path = os.path.join(LICENSE_DIR, name)
                if os.path.isfile(path):
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            contents.append(f"===== {name} =====\n" + f.read() + "\n\n")
                    except Exception as e:
                        contents.append(f"Fehler beim Laden von {name}: {e}\n\n")
        else:
            contents.append("licenses-Ordner nicht gefunden.")

        text.insert("1.0", "".join(contents))
        text.configure(state="disabled")

        return p

        # ------------------------------------------------------------
    # HILFE
    # ------------------------------------------------------------
    def _page_help(self, parent):
        p = tk.Frame(parent, bg=COLORS["bg"])
        p.pack_propagate(False)

        # ---------- HEADER ----------
        header = tk.Frame(p, bg=COLORS["panel"], padx=20, pady=16)
        header.pack(fill="x")
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        left = tk.Frame(header, bg=COLORS["panel"])
        left.grid(row=0, column=0, sticky="nw")

        tk.Label(
            left,
            text="Hilfe & Bedienung",
            fg=COLORS["text"],
            bg=COLORS["panel"],
            font=("Segoe UI", 22, "bold"),
        ).pack(anchor="w")

        tk.Label(
            left,
            text="Kurze Erklärung aller Bereiche im FotoTool.",
            fg=COLORS["muted"],
            bg=COLORS["panel"],
        ).pack(anchor="w", pady=(6, 0))

        info = self._create_info_card(
            header,
            "Bedienhilfe",
            "Hier findest du eine Übersicht über alle Funktionen "
            "und Hinweise zur Nutzung von FotoTool.",
            "Sortieren · Unsortiert · Duplikate",
        )
        info.grid(row=0, column=1, sticky="ne", padx=(40, 0))


        # ---------- SCROLL-CONTAINER ----------
        scroll_container = tk.Frame(p, bg=COLORS["bg"])
        scroll_container.pack(fill="both", expand=True)

        canvas = tk.Canvas(scroll_container, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        content_outer = tk.Frame(canvas, bg=COLORS["bg"])
        content_window = canvas.create_window((0, 0), window=content_outer, anchor="nw")

        content = tk.Frame(content_outer, bg=COLORS["bg"])
        content.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        def _on_canvas_configure(event):
            # WICHTIG: Breite UND Höhe an Viewport anpassen
            canvas.itemconfig(content_window, width=event.width, height=event.height)

        canvas.bind("<Configure>", _on_canvas_configure)

        content_outer.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.configure(yscrollcommand=scrollbar.set)



        # ---------- INHALT ----------
        self.step_title(content, "Übersicht")

        text = tk.Text(
            content,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            wrap="word",
            relief="flat",
            padx=12,
            pady=12,
        )
        text.pack(fill="both", expand=True, pady=(8, 20))


        help_text = """
    SORTIEREN
    ---------
    Import-Ordner wählen → Ziel-Archiv wählen → Start drücken.
    Fotos werden nach Datum, WhatsApp, Screenshots oder Events sortiert.

    UNSORTIERT
    ----------
    Analysiert Dateien ohne klares Datum.
    Danach kannst du Zielordner auswählen und Dateien verschieben.

    DUPLIKATE
    ---------
    Durchsucht einen Ordner nach identischen Dateien.

    LOGS
    ----
    Zeigt alle Aktionen des Programms an.


    TIPPS
    -----
    • Erst Simulation testen, dann echten Import starten.
    • Große Archive lieber in mehreren Schritten sortieren.


    IMPRESSUM
    ---------
    Andreas Heinig 
    E-Mail: andreasheinig@icloud.com

    Private, nicht-kommerzielle Software zur lokalen Foto-Organisation.
    """

        text.insert("1.0", help_text.strip())
        text.configure(state="disabled")

        return p



    

    # ------------------------------------------------------------
    # Platzhalterseiten
    # ------------------------------------------------------------

    def _simple_page(self, title, text):
        p = tk.Frame(self.main, bg=COLORS["bg"])
        p.pack_propagate(False)

        tk.Label(p, text=title, fg=COLORS["text"], bg=COLORS["bg"], font=("Segoe UI", 22, "bold")).pack(anchor="w")
        tk.Label(p, text=text, fg=COLORS["muted"], bg=COLORS["bg"], justify="left").pack(anchor="w", pady=(6, 0))
        return p


if __name__ == "__main__":
    app = FotoToolFinal20()   
    app.mainloop()
