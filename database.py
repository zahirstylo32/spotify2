"""
database.py — Capa de datos (SQLite)
Maneja canciones, playlists y relaciones entre ellas.
"""
 
import sqlite3
import os
 
DB_PATH = "spotify2.db"
 
 
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
 
 
def init_db():
    """Crea las tablas si no existen."""
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS canciones (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                path      TEXT    UNIQUE NOT NULL,
                titulo    TEXT    NOT NULL,
                artista   TEXT    DEFAULT '',
                album     TEXT    DEFAULT '',
                genero    TEXT    DEFAULT '',
                duracion  REAL    DEFAULT 0,
                caratula  BLOB
            );
 
            CREATE TABLE IF NOT EXISTS playlists (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT    UNIQUE NOT NULL
            );
 
            CREATE TABLE IF NOT EXISTS playlist_canciones (
                playlist_id  INTEGER REFERENCES playlists(id)  ON DELETE CASCADE,
                cancion_id   INTEGER REFERENCES canciones(id)  ON DELETE CASCADE,
                posicion     INTEGER DEFAULT 0,
                PRIMARY KEY (playlist_id, cancion_id)
            );
        """)
 
 
# ── Canciones ─────────────────────────────────────────────────────────────────
 
def upsert_cancion(path, titulo, artista="", album="", genero="", duracion=0.0, caratula=None):
    """
    Inserta o actualiza una canción.
    Detecta duplicados por PATH o por combinación TITULO+ARTISTA,
    así evita dobles entradas cuando el archivo viene de una ruta diferente.
    """
    with get_conn() as conn:
        # 1. ¿Ya existe con el mismo path?
        existente = conn.execute(
            "SELECT id FROM canciones WHERE path = ?", (path,)
        ).fetchone()
 
        if existente:
            # Actualizar datos pero conservar el path
            conn.execute("""
                UPDATE canciones SET
                    titulo   = ?,
                    artista  = ?,
                    album    = ?,
                    genero   = ?,
                    duracion = ?,
                    caratula = COALESCE(?, caratula)
                WHERE path = ?
            """, (titulo, artista, album, genero, duracion, caratula, path))
            return get_cancion_by_path(path)
 
        # 2. ¿Existe otra entrada con mismo título Y artista (vino de otra ruta)?
        duplicado = conn.execute("""
            SELECT id, path FROM canciones
            WHERE titulo = ? COLLATE NOCASE
              AND artista = ? COLLATE NOCASE
        """, (titulo, artista)).fetchone()
 
        if duplicado:
            # Actualizar el path al nuevo y refrescar metadatos
            conn.execute("""
                UPDATE canciones SET
                    path     = ?,
                    album    = ?,
                    genero   = ?,
                    duracion = ?,
                    caratula = COALESCE(?, caratula)
                WHERE id = ?
            """, (path, album, genero, duracion, caratula, duplicado["id"]))
            return get_cancion_by_path(path)
 
        # 3. Es una canción nueva — insertar normalmente
        conn.execute("""
            INSERT INTO canciones (path, titulo, artista, album, genero, duracion, caratula)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (path, titulo, artista, album, genero, duracion, caratula))
 
    return get_cancion_by_path(path)
 
 
def get_all_canciones(order_by="titulo"):
    cols = {"titulo", "artista", "album", "genero"}
    col = order_by if order_by in cols else "titulo"
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            f"SELECT * FROM canciones ORDER BY {col} COLLATE NOCASE"
        )]
 
 
def get_cancion_by_path(path):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM canciones WHERE path=?", (path,)).fetchone()
        return dict(row) if row else None
 
 
def get_cancion_by_id(cid):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM canciones WHERE id=?", (cid,)).fetchone()
        return dict(row) if row else None
 
 
def buscar_canciones(query, campo="titulo"):
    cols = {"titulo", "artista", "album", "genero"}
    col = campo if campo in cols else "titulo"
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            f"SELECT * FROM canciones WHERE {col} LIKE ? COLLATE NOCASE ORDER BY {col} COLLATE NOCASE",
            (f"%{query}%",)
        )]
 
 
# ── Playlists ─────────────────────────────────────────────────────────────────
 
def crear_playlist(nombre):
    with get_conn() as conn:
        conn.execute("INSERT OR IGNORE INTO playlists (nombre) VALUES (?)", (nombre,))
    return get_playlist_by_name(nombre)
 
 
def get_all_playlists():
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM playlists ORDER BY nombre COLLATE NOCASE")]
 
 
def get_playlist_by_name(nombre):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM playlists WHERE nombre=?", (nombre,)).fetchone()
        return dict(row) if row else None
 
 
def get_playlist_by_id(pid):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM playlists WHERE id=?", (pid,)).fetchone()
        return dict(row) if row else None
 
 
def renombrar_playlist(pid, nuevo_nombre):
    with get_conn() as conn:
        conn.execute("UPDATE playlists SET nombre=? WHERE id=?", (nuevo_nombre, pid))
 
 
def eliminar_playlist(pid):
    with get_conn() as conn:
        conn.execute("DELETE FROM playlists WHERE id=?", (pid,))
 
 
def agregar_a_playlist(playlist_id, cancion_id):
    with get_conn() as conn:
        pos = conn.execute(
            "SELECT COALESCE(MAX(posicion)+1, 0) FROM playlist_canciones WHERE playlist_id=?",
            (playlist_id,)
        ).fetchone()[0]
        conn.execute(
            "INSERT OR IGNORE INTO playlist_canciones (playlist_id, cancion_id, posicion) VALUES (?,?,?)",
            (playlist_id, cancion_id, pos)
        )
 
 
def quitar_de_playlist(playlist_id, cancion_id):
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM playlist_canciones WHERE playlist_id=? AND cancion_id=?",
            (playlist_id, cancion_id)
        )
 
 
def get_canciones_de_playlist(playlist_id):
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("""
            SELECT c.* FROM canciones c
            JOIN playlist_canciones pc ON pc.cancion_id = c.id
            WHERE pc.playlist_id = ?
            ORDER BY pc.posicion
        """, (playlist_id,))]
 