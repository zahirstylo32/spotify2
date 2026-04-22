"""
interfaz.py — Interfaz gráfica principal con Tkinter.

Paleta: fondo casi negro #0d0d0d, acento azul eléctrico #1e90ff,
texto blanco hueso, sidebar carbón #1a1a2e.
Tipografía: Segoe UI / TkDefaultFont en distintos pesos.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import io
import threading

from PIL import Image, ImageTk, ImageDraw

import database as db
import metadata as meta
from player import Player
from playqueue import Queue, LOOP_NONE, LOOP_ONE

# ── Paleta ────────────────────────────────────────────────────────────────────
BG       = "#0d0d0d"
SIDEBAR  = "#111122"
CARD     = "#1a1a2e"
ACCENT   = "#1e90ff"
ACCENT2  = "#0055cc"
TEXT     = "#e8e8f0"
SUBTEXT  = "#7070a0"
HOVER    = "#22223a"
SEL      = "#1e3a6e"
DANGER   = "#e05555"

FONT_TITLE  = ("Segoe UI", 22, "bold")
FONT_ARTIST = ("Segoe UI", 12)
FONT_LABEL  = ("Segoe UI", 10)
FONT_SMALL  = ("Segoe UI", 9)
FONT_BTN    = ("Segoe UI", 14)
FONT_MONO   = ("Consolas", 9)

COVER_SIZE   = 180
LIST_ROW_H   = 36
BTN_IMG_SIZE = (36, 36)   # tamaño al que se redimensionan los íconos de control


def _load_asset(nombre: str, size: tuple = BTN_IMG_SIZE) -> "ImageTk.PhotoImage | None":
    """
    Carga assets/<nombre>.png redimensionado a `size`.
    Devuelve None si el archivo no existe, para que el botón use texto como fallback.
    """
    path = os.path.join("assets", f"{nombre}.png")
    if not os.path.isfile(path):
        return None
    try:
        img = Image.open(path).convert("RGBA").resize(size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


def fmt_time(secs: float) -> str:
    secs = max(0, int(secs))
    return f"{secs // 60}:{secs % 60:02d}"


def make_round_image(img: Image.Image, size: int) -> ImageTk.PhotoImage:
    img = img.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    result = Image.new("RGBA", (size, size))
    result.paste(img, mask=mask)
    return ImageTk.PhotoImage(result)


def placeholder_cover(size: int) -> ImageTk.PhotoImage:
    img = Image.new("RGB", (size, size), color="#1a1a2e")
    draw = ImageDraw.Draw(img)
    draw.ellipse((size // 4, size // 4, 3 * size // 4, 3 * size // 4),
                 fill="#1e90ff", outline="#0055cc", width=2)
    note_x, note_y = size // 2 - 8, size // 2 - 10
    draw.rectangle([note_x, note_y, note_x + 4, note_y + 18], fill="#0d0d0d")
    draw.rectangle([note_x + 4, note_y, note_x + 14, note_y + 4], fill="#0d0d0d")
    return make_round_image(img, size)


# ─────────────────────────────────────────────────────────────────────────────
class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Spotify 2")
        root.geometry("1200x720")
        root.minsize(900, 600)
        root.configure(bg=BG)

        db.init_db()

        self.player = Player(on_song_end=self._on_song_end, on_tick=self._on_tick)
        self.queue  = Queue()

        self._current_song: dict | None = None
        self._dragging_progress = False
        self._cover_photo = None
        self._active_playlist_id: int | None = None
        self._view = "library"   # "library" | "playlist"

        # ── Cargar imágenes de assets/ ──────────────────────────────────────
        self._imgs: dict = {}
        self._load_btn_images()

        self._build_ui()
        self._load_library()

    # ══════════════════════════════════════════════════════════════════════════
    # UI BUILD
    # ══════════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)

        self._build_sidebar()
        self._build_main()
        self._build_player_bar()

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self):
        side = tk.Frame(self.root, bg=SIDEBAR, width=220)
        side.grid(row=0, column=0, sticky="nsew")
        side.grid_propagate(False)

        # Logo
        tk.Label(side, text="♫  Spotify 2", bg=SIDEBAR, fg=ACCENT,
                 font=("Segoe UI", 16, "bold"), pady=18).pack(fill="x", padx=16)

        tk.Frame(side, bg="#222244", height=1).pack(fill="x", padx=12, pady=4)

        # Library button
        self._btn_library = self._sidebar_btn(side, "🎵  Biblioteca", self._show_library)
        self._btn_library.pack(fill="x", padx=8, pady=2)

        tk.Label(side, text="PLAYLISTS", bg=SIDEBAR, fg=SUBTEXT,
                 font=("Segoe UI", 8, "bold"), padx=16, pady=8).pack(fill="x")

        # Playlist list
        pl_frame = tk.Frame(side, bg=SIDEBAR)
        pl_frame.pack(fill="both", expand=True, padx=4)

        self._pl_listbox = tk.Listbox(
            pl_frame, bg=SIDEBAR, fg=TEXT, font=FONT_LABEL,
            selectbackground=SEL, selectforeground=TEXT,
            relief="flat", bd=0, activestyle="none",
            highlightthickness=0
        )
        self._pl_listbox.pack(fill="both", expand=True)
        self._pl_listbox.bind("<Double-Button-1>", self._on_playlist_double)
        self._pl_listbox.bind("<Button-3>", self._playlist_context_menu)

        # New playlist btn
        tk.Button(side, text="＋  Nueva playlist",
                  bg=SIDEBAR, fg=ACCENT, font=FONT_LABEL,
                  relief="flat", bd=0, cursor="hand2",
                  activebackground=HOVER, activeforeground=ACCENT,
                  command=self._nueva_playlist).pack(fill="x", padx=12, pady=8)

        self._refresh_playlists()

    def _sidebar_btn(self, parent, text, cmd):
        btn = tk.Button(parent, text=text, bg=SIDEBAR, fg=TEXT,
                        font=FONT_LABEL, relief="flat", bd=0, anchor="w",
                        padx=12, pady=6, cursor="hand2",
                        activebackground=HOVER, activeforeground=ACCENT,
                        command=cmd)
        return btn

    # ── Main area ─────────────────────────────────────────────────────────────

    def _build_main(self):
        main = tk.Frame(self.root, bg=BG)
        main.grid(row=0, column=1, sticky="nsew")
        main.rowconfigure(1, weight=1)
        main.columnconfigure(0, weight=1)

        # ── Toolbar ───────────────────────────────────────────────────────────
        toolbar = tk.Frame(main, bg=BG, pady=10)
        toolbar.grid(row=0, column=0, sticky="ew", padx=16)

        self._lbl_view_title = tk.Label(toolbar, text="Biblioteca", bg=BG, fg=TEXT,
                                        font=FONT_TITLE)
        self._lbl_view_title.pack(side="left")

        # Search
        search_frame = tk.Frame(toolbar, bg="#1a1a2e", padx=8, pady=4)
        search_frame.pack(side="right", padx=(0, 8))

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._on_search())

        tk.Label(search_frame, text="🔍", bg="#1a1a2e", fg=SUBTEXT,
                 font=FONT_LABEL).pack(side="left")
        self._search_entry = tk.Entry(search_frame, textvariable=self._search_var,
                                      bg="#1a1a2e", fg=TEXT, insertbackground=TEXT,
                                      relief="flat", font=FONT_LABEL, width=22)
        self._search_entry.pack(side="left")

        # Sort / Campo de búsqueda
        self._sort_var = tk.StringVar(value="titulo")
        sort_options = ["titulo", "artista", "album", "genero"]
        sort_menu = ttk.Combobox(toolbar, textvariable=self._sort_var,
                                 values=sort_options, state="readonly",
                                 width=8, font=FONT_LABEL)
        sort_menu.pack(side="right", padx=4)
        sort_menu.bind("<<ComboboxSelected>>", lambda *_: self._on_search())
        tk.Label(toolbar, text="Ordenar:", bg=BG, fg=SUBTEXT,
                 font=FONT_LABEL).pack(side="right")

        # Add folder
        tk.Button(toolbar, text="📁  Agregar carpeta",
                  bg=ACCENT2, fg=TEXT, font=FONT_LABEL,
                  relief="flat", bd=0, padx=10, pady=4, cursor="hand2",
                  activebackground=ACCENT, activeforeground=TEXT,
                  command=self._add_folder).pack(side="right", padx=(0, 12))

        # ── Song list ─────────────────────────────────────────────────────────
        list_container = tk.Frame(main, bg=BG)
        list_container.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 4))
        list_container.rowconfigure(0, weight=1)
        list_container.columnconfigure(0, weight=1)

        # Header
        header = tk.Frame(list_container, bg=CARD)
        header.grid(row=0, column=0, sticky="ew", padx=4, pady=(0, 2))
        for col, (text, w) in enumerate([("#", 4), ("Título", 35),
                                          ("Artista", 22), ("Álbum", 22),
                                          ("Género", 12), ("Duración", 7)]):
            tk.Label(header, text=text, bg=CARD, fg=SUBTEXT,
                     font=("Segoe UI", 9, "bold"),
                     width=w, anchor="w", padx=4, pady=6).grid(
                row=0, column=col, sticky="w")

        # Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.Treeview",
                        background=BG, foreground=TEXT,
                        fieldbackground=BG, rowheight=LIST_ROW_H,
                        borderwidth=0, font=FONT_LABEL)
        style.configure("Custom.Treeview.Heading",
                        background=CARD, foreground=SUBTEXT,
                        borderwidth=0, font=("Segoe UI", 9, "bold"))
        style.map("Custom.Treeview",
                  background=[("selected", SEL)],
                  foreground=[("selected", TEXT)])

        cols = ("num", "titulo", "artista", "album", "genero", "duracion")
        self._tree = ttk.Treeview(list_container, columns=cols,
                                   show="headings", style="Custom.Treeview",
                                   selectmode="browse")
        for col, (text, w) in zip(cols, [
            ("#", 40), ("Título", 280), ("Artista", 160),
            ("Álbum", 160), ("Género", 90), ("Duración", 70)
        ]):
            self._tree.heading(col, text=text,
                               command=lambda c=col: self._sort_by_col(c))
            self._tree.column(col, width=w, minwidth=30, anchor="w")

        vsb = ttk.Scrollbar(list_container, orient="vertical",
                             command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)

        self._tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        list_container.rowconfigure(1, weight=1)

        self._tree.bind("<Double-Button-1>", self._on_tree_double)
        self._tree.bind("<Button-3>",        self._tree_context_menu)

    # ── Player bar ────────────────────────────────────────────────────────────

    def _load_btn_images(self):
        """
        Carga todas las imágenes de assets/.
        Las que no existan quedan como None y el botón usará texto.
        Imágenes con imagen propia (tus archivos): play, pause, atrasar, adelantar.
        Imágenes opcionales: shuffle, loop_none, loop_all, loop_one.
        """
        for nombre in ("play", "pause", "atrasar", "adelantar",
                       "shuffle", "loop_none", "loop_one"):
            self._imgs[nombre] = _load_asset(nombre)

    def _make_ctrl_btn(self, parent, img_key: str, text_fallback: str,
                       command, fg=None, font=None, **extra) -> tk.Button:
        """
        Crea un botón de control usando imagen si existe, texto si no.
        `img_key` es la clave en self._imgs.
        """
        img = self._imgs.get(img_key)
        kw = dict(bg=CARD, activebackground=CARD, relief="flat", bd=0,
                  cursor="hand2", command=command)
        if fg:
            kw["activeforeground"] = fg
        if img:
            kw["image"] = img
            kw["text"]  = ""
        else:
            kw["text"] = text_fallback
            kw["font"] = font or FONT_BTN
            if fg:
                kw["fg"] = fg
        kw.update(extra)
        btn = tk.Button(parent, **kw)
        if img:
            btn.image = img   # evitar garbage collection
        return btn

    def _build_player_bar(self):
        bar = tk.Frame(self.root, bg=CARD, height=100)
        bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        bar.grid_propagate(False)
        bar.columnconfigure(1, weight=1)

        # ── Cover + info ──────────────────────────────────────────────────────
        info_frame = tk.Frame(bar, bg=CARD)
        info_frame.grid(row=0, column=0, sticky="w", padx=16, pady=8)

        self._cover_label = tk.Label(info_frame, bg=CARD)
        self._cover_label.grid(row=0, column=0, rowspan=2, padx=(0, 12))
        self._set_cover(None)

        self._lbl_title  = tk.Label(info_frame, text="Sin canción",
                                    bg=CARD, fg=TEXT, font=("Segoe UI", 11, "bold"),
                                    anchor="w", width=22)
        self._lbl_title.grid(row=0, column=1, sticky="w")
        self._lbl_artist = tk.Label(info_frame, text="—",
                                    bg=CARD, fg=SUBTEXT, font=FONT_LABEL,
                                    anchor="w", width=22)
        self._lbl_artist.grid(row=1, column=1, sticky="w")

        # ── Controls center ───────────────────────────────────────────────────
        ctrl = tk.Frame(bar, bg=CARD)
        ctrl.grid(row=0, column=1, sticky="nsew", padx=16)
        ctrl.columnconfigure(0, weight=1)

        btn_row = tk.Frame(ctrl, bg=CARD)
        btn_row.grid(row=0, column=0, pady=(10, 4))

        # Shuffle — usa assets/shuffle.png si existe, si no texto "⇄"
        self._btn_shuffle = self._make_ctrl_btn(
            btn_row, "shuffle", "⇄", self._toggle_shuffle, fg=SUBTEXT)
        self._btn_shuffle.pack(side="left", padx=6)

        # Atrasar — usa assets/atrasar.png
        self._btn_prev = self._make_ctrl_btn(
            btn_row, "atrasar", "⏮", self._prev, fg=TEXT)
        self._btn_prev.pack(side="left", padx=6)

        # Play/Pause — usa assets/play.png por defecto, cambia a pause al reproducir
        self._btn_play = self._make_ctrl_btn(
            btn_row, "play", "▶", self._toggle_play,
            fg=ACCENT, font=("Segoe UI", 20, "bold"))
        self._btn_play.pack(side="left", padx=8)

        # Adelantar — usa assets/adelantar.png
        self._btn_next = self._make_ctrl_btn(
            btn_row, "adelantar", "⏭", self._next, fg=TEXT)
        self._btn_next.pack(side="left", padx=6)

        # Loop — usa assets/loop_none.png si existe, si no texto "↺"
        self._btn_loop = self._make_ctrl_btn(
            btn_row, "loop_none", "↺", self._cycle_loop, fg=SUBTEXT)
        self._btn_loop.pack(side="left", padx=6)

        # Progress
        prog_row = tk.Frame(ctrl, bg=CARD)
        prog_row.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 8))

        self._lbl_cur  = tk.Label(prog_row, text="0:00", bg=CARD, fg=SUBTEXT,
                                  font=FONT_SMALL, width=5)
        self._lbl_cur.pack(side="left")

        self._progress_var = tk.DoubleVar(value=0)
        self._progress_bar = ttk.Scale(prog_row, from_=0, to=100,
                                       variable=self._progress_var,
                                       orient="horizontal",
                                       command=self._on_progress_move)
        style = ttk.Style()
        style.configure("Horizontal.TScale", background=CARD,
                        troughcolor="#2a2a4a", sliderlength=12)
        self._progress_bar.pack(side="left", fill="x", expand=True, padx=6)
        self._progress_bar.bind("<ButtonPress-1>",   lambda e: self._start_drag())
        self._progress_bar.bind("<ButtonRelease-1>", lambda e: self._end_drag())

        self._lbl_dur  = tk.Label(prog_row, text="0:00", bg=CARD, fg=SUBTEXT,
                                  font=FONT_SMALL, width=5)
        self._lbl_dur.pack(side="left")

        # ── Volume ────────────────────────────────────────────────────────────
        vol_frame = tk.Frame(bar, bg=CARD)
        vol_frame.grid(row=0, column=2, sticky="e", padx=20, pady=8)

        tk.Label(vol_frame, text="🔊", bg=CARD, fg=SUBTEXT,
                 font=FONT_LABEL).pack(side="left")
        self._vol_var = tk.DoubleVar(value=70)
        vol_scale = ttk.Scale(vol_frame, from_=0, to=100,
                              variable=self._vol_var, orient="horizontal",
                              command=self._on_volume_change)
        vol_scale.pack(side="left", padx=4)
        self._lbl_vol = tk.Label(vol_frame, text="70%", bg=CARD, fg=SUBTEXT,
                                 font=FONT_SMALL, width=4)
        self._lbl_vol.pack(side="left")

    # ══════════════════════════════════════════════════════════════════════════
    # DATA / LIBRARY
    # ══════════════════════════════════════════════════════════════════════════

    def _load_library(self):
        songs = db.get_all_canciones(self._sort_var.get())
        self._populate_tree(songs)

    def _populate_tree(self, songs: list[dict]):
        self._tree.delete(*self._tree.get_children())
        for i, s in enumerate(songs, 1):
            self._tree.insert("", "end", iid=str(s["id"]),
                              values=(i, s["titulo"], s["artista"],
                                      s["album"], s["genero"],
                                      fmt_time(s["duracion"])))

    def _add_folder(self):
        folder = filedialog.askdirectory(title="Seleccionar carpeta de música")
        if not folder:
            return
        files = meta.get_supported_files(folder)
        if not files:
            messagebox.showinfo("Sin archivos",
                                "No se encontraron archivos de audio en esa carpeta.")
            return

        def task():
            for path in files:
                m = meta.read_metadata(path)
                db.upsert_cancion(path, m["titulo"], m["artista"], m["album"],
                                  m["genero"], m["duracion"], m["caratula"])
            self.root.after(0, self._load_library)
            self.root.after(0, lambda: messagebox.showinfo(
                "Listo", f"Se importaron {len(files)} archivos."))

        threading.Thread(target=task, daemon=True).start()

    def _on_search(self):
        q = self._search_var.get().strip()
        campo = self._sort_var.get()
        if self._view == "playlist" and self._active_playlist_id:
            songs = db.get_canciones_de_playlist(self._active_playlist_id)
            if q:
                songs = [s for s in songs if q.lower() in s.get(campo, "").lower()]
        else:
            if q:
                songs = db.buscar_canciones(q, campo)
            else:
                songs = db.get_all_canciones(campo)
        self._populate_tree(songs)

    def _sort_by_col(self, col):
        map_ = {"titulo": "titulo", "artista": "artista",
                "album": "album", "genero": "genero"}
        if col in map_:
            self._sort_var.set(map_[col])
            self._on_search()

    # ══════════════════════════════════════════════════════════════════════════
    # VIEWS
    # ══════════════════════════════════════════════════════════════════════════

    def _show_library(self):
        self._view = "library"
        self._active_playlist_id = None
        self._lbl_view_title.config(text="Biblioteca")
        self._load_library()

    def _show_playlist(self, pid: int):
        pl = db.get_playlist_by_id(pid)
        if not pl:
            return
        self._view = "playlist"
        self._active_playlist_id = pid
        self._lbl_view_title.config(text=f"▶ {pl['nombre']}")
        songs = db.get_canciones_de_playlist(pid)
        self._populate_tree(songs)

    # ══════════════════════════════════════════════════════════════════════════
    # PLAYLISTS
    # ══════════════════════════════════════════════════════════════════════════

    def _refresh_playlists(self):
        self._pl_listbox.delete(0, "end")
        self._playlists = db.get_all_playlists()
        for pl in self._playlists:
            self._pl_listbox.insert("end", f"  {pl['nombre']}")

    def _nueva_playlist(self):
        nombre = simpledialog.askstring("Nueva playlist", "Nombre:",
                                        parent=self.root)
        if nombre and nombre.strip():
            db.crear_playlist(nombre.strip())
            self._refresh_playlists()

    def _on_playlist_double(self, event):
        sel = self._pl_listbox.curselection()
        if not sel:
            return
        pl = self._playlists[sel[0]]
        self._show_playlist(pl["id"])

    def _playlist_context_menu(self, event):
        idx = self._pl_listbox.nearest(event.y)
        if idx < 0 or idx >= len(self._playlists):
            return
        pl = self._playlists[idx]
        menu = tk.Menu(self.root, tearoff=0, bg=CARD, fg=TEXT,
                       activebackground=SEL, activeforeground=TEXT,
                       relief="flat")
        menu.add_command(label="Renombrar",
                         command=lambda: self._renombrar_playlist(pl["id"]))
        menu.add_command(label="Eliminar",
                         command=lambda: self._eliminar_playlist(pl["id"]))
        menu.tk_popup(event.x_root, event.y_root)

    def _renombrar_playlist(self, pid):
        nuevo = simpledialog.askstring("Renombrar", "Nuevo nombre:", parent=self.root)
        if nuevo and nuevo.strip():
            db.renombrar_playlist(pid, nuevo.strip())
            self._refresh_playlists()
            if self._active_playlist_id == pid:
                self._show_playlist(pid)

    def _eliminar_playlist(self, pid):
        if messagebox.askyesno("Eliminar", "¿Eliminar esta playlist?"):
            db.eliminar_playlist(pid)
            self._refresh_playlists()
            if self._active_playlist_id == pid:
                self._show_library()

    # ══════════════════════════════════════════════════════════════════════════
    # TREE INTERACTIONS
    # ══════════════════════════════════════════════════════════════════════════

    def _on_tree_double(self, event):
        item = self._tree.focus()
        if not item:
            return
        song_id = int(item)
        # Cargar toda la lista visible como cola
        visible_ids = [int(i) for i in self._tree.get_children()]
        songs = [db.get_cancion_by_id(i) for i in visible_ids]
        songs = [s for s in songs if s]
        start = next((i for i, s in enumerate(songs) if s["id"] == song_id), 0)
        self.queue.set_songs(songs, start)
        self._play_current()

    def _tree_context_menu(self, event):
        item = self._tree.identify_row(event.y)
        if not item:
            return
        self._tree.selection_set(item)
        song_id = int(item)

        menu = tk.Menu(self.root, tearoff=0, bg=CARD, fg=TEXT,
                       activebackground=SEL, activeforeground=TEXT,
                       relief="flat")
        menu.add_command(label="▶ Reproducir",
                         command=lambda: self._play_song_by_id(song_id))

        # Submenú: agregar a playlist
        playlists = db.get_all_playlists()
        if playlists:
            sub = tk.Menu(menu, tearoff=0, bg=CARD, fg=TEXT,
                          activebackground=SEL, activeforeground=TEXT,
                          relief="flat")
            for pl in playlists:
                sub.add_command(
                    label=pl["nombre"],
                    command=lambda pid=pl["id"]: db.agregar_a_playlist(pid, song_id)
                )
            menu.add_cascade(label="Agregar a playlist →", menu=sub)

        # Si estamos viendo una playlist, ofrecer quitar
        if self._view == "playlist" and self._active_playlist_id:
            pid = self._active_playlist_id
            menu.add_command(
                label="Quitar de playlist",
                command=lambda: self._quitar_de_playlist(pid, song_id)
            )

        menu.tk_popup(event.x_root, event.y_root)

    def _quitar_de_playlist(self, pid, song_id):
        db.quitar_de_playlist(pid, song_id)
        self._show_playlist(pid)

    def _play_song_by_id(self, song_id: int):
        visible_ids = [int(i) for i in self._tree.get_children()]
        songs = [db.get_cancion_by_id(i) for i in visible_ids]
        songs = [s for s in songs if s]
        start = next((i for i, s in enumerate(songs) if s["id"] == song_id), 0)
        self.queue.set_songs(songs, start)
        self._play_current()

    # ══════════════════════════════════════════════════════════════════════════
    # PLAYBACK
    # ══════════════════════════════════════════════════════════════════════════

    def _play_current(self):
        song = self.queue.current()
        if not song:
            return
        if not os.path.exists(song["path"]):
            messagebox.showerror("Error", f"No se encontró el archivo:\n{song['path']}")
            return
        self._current_song = song
        self.player.load(song["path"], song["duracion"])
        self.player.play()
        self._update_now_playing(song)
        self._highlight_tree(song["id"])

    def _toggle_play(self):
        if not self._current_song:
            return
        if self.player.is_playing:
            self.player.pause()
            self._set_play_btn_state("pause")   # muestra ícono "play" (para reanudar)
        elif self.player.is_paused:
            self.player.play()
            self._set_play_btn_state("play")    # muestra ícono "pause" (está sonando)
        else:
            self.player.play()
            self._set_play_btn_state("play")

    def _set_play_btn_state(self, state: str):
        """
        state="play"  → el botón muestra pausa (la canción está sonando).
        state="pause" → el botón muestra play  (la canción está pausada/detenida).
        Usa imágenes si existen, texto si no.
        """
        if state == "play":
            img = self._imgs.get("pause")
            txt = "⏸"
            fg  = ACCENT
        else:
            img = self._imgs.get("play")
            txt = "▶"
            fg  = ACCENT

        if img:
            self._btn_play.config(image=img, text="")
            self._btn_play.image = img
        else:
            self._btn_play.config(text=txt, fg=fg, image="")

    def _next(self):
        song = self.queue.next()
        if song:
            self._current_song = song
            self.player.load(song["path"], song["duracion"])
            self.player.play()
            self._update_now_playing(song)
            self._highlight_tree(song["id"])

    def _prev(self):
        # Si la canción lleva más de 3 s, reiniciarla
        if self.player.position() > 3:
            self.player.seek(0)
            return
        song = self.queue.prev()
        if song:
            self._current_song = song
            self.player.load(song["path"], song["duracion"])
            self.player.play()
            self._update_now_playing(song)
            self._highlight_tree(song["id"])

    def _on_song_end(self):
        """Callback del player cuando termina una canción."""
        self.root.after(0, self._next)

    # ── Shuffle / Loop ────────────────────────────────────────────────────────

    def _toggle_shuffle(self):
        active = self.queue.toggle_shuffle()
        img = self._imgs.get("shuffle")
        if img:
            # Con imagen: resaltamos con un fondo diferente
            self._btn_shuffle.config(
                bg=SEL if active else CARD,
                activebackground=SEL if active else CARD)
        else:
            self._btn_shuffle.config(fg=ACCENT if active else SUBTEXT)

    def _cycle_loop(self):
        mode = self.queue.cycle_loop()
        # Solo LOOP_NONE y LOOP_ONE
        mode_map = {
            LOOP_NONE: ("loop_none", "↺",  SUBTEXT, CARD),
            LOOP_ONE:  ("loop_one",  "↻¹", ACCENT,  SEL),
        }
        img_key, txt, fg, bg_active = mode_map[mode]
        img = self._imgs.get(img_key)
        if img:
            self._btn_loop.config(image=img, text="",
                                  bg=bg_active, activebackground=bg_active)
            self._btn_loop.image = img
        else:
            self._btn_loop.config(text=txt, fg=fg,
                                  bg=CARD, activebackground=CARD, image="")

    # ── Volume ────────────────────────────────────────────────────────────────

    def _on_volume_change(self, val):
        v = float(val) / 100
        self.player.set_volume(v)
        self._lbl_vol.config(text=f"{int(float(val))}%")

    # ── Progress bar ──────────────────────────────────────────────────────────

    def _start_drag(self):
        self._dragging_progress = True

    def _end_drag(self):
        if self._dragging_progress and self._current_song:
            dur = self._current_song["duracion"]
            pos = (self._progress_var.get() / 100) * dur
            self.player.seek(pos)
        self._dragging_progress = False

    def _on_progress_move(self, val):
        if self._dragging_progress and self._current_song:
            dur = self._current_song["duracion"]
            pos = (float(val) / 100) * dur
            self._lbl_cur.config(text=fmt_time(pos))

    def _on_tick(self, pos: float, dur: float):
        """Llamado cada ~200 ms desde el hilo del player."""
        if self._dragging_progress:
            return
        self.root.after(0, self._update_progress, pos, dur)

    def _update_progress(self, pos: float, dur: float):
        if dur > 0:
            pct = (pos / dur) * 100
            self._progress_var.set(pct)
        self._lbl_cur.config(text=fmt_time(pos))
        self._lbl_dur.config(text=fmt_time(dur))
        self._set_play_btn_state("play" if self.player.is_playing else "pause")

    # ── Now playing info ──────────────────────────────────────────────────────

    def _update_now_playing(self, song: dict):
        self._lbl_title.config(text=song["titulo"][:28])
        self._lbl_artist.config(text=song["artista"] or "—")
        self._lbl_dur.config(text=fmt_time(song["duracion"]))
        self._set_play_btn_state("play")
        self._set_cover(song.get("caratula"))

    def _set_cover(self, data: bytes | None):
        try:
            if data:
                img = Image.open(io.BytesIO(data))
            else:
                img = None
            photo = make_round_image(img, 52) if img else placeholder_cover(52)
        except Exception:
            photo = placeholder_cover(52)
        self._cover_photo = photo
        self._cover_label.config(image=photo)

    def _highlight_tree(self, song_id: int):
        item = str(song_id)
        if self._tree.exists(item):
            self._tree.selection_set(item)
            self._tree.see(item)

    # ── Stop ──────────────────────────────────────────────────────────────────

    def stop(self):
        self.player.stop()
        self._set_play_btn_state("pause")
        self._progress_var.set(0)
        self._lbl_cur.config(text="0:00")

    def on_close(self):
        self.player.destroy()
        self.root.destroy()
