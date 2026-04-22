"""
metadata.py — Lectura de metadatos con mutagen.
Extrae título, artista, álbum, género, duración y carátula.
"""

import os
from mutagen import File as MutagenFile
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.id3 import ID3NoHeaderError

SUPPORTED_EXT = {".mp3", ".flac", ".ogg", ".wav", ".m4a", ".aac"}


def _get_tag(tags, *keys, default=""):
    """Intenta varios nombres de tag y retorna el primero encontrado."""
    for k in keys:
        val = tags.get(k)
        if val:
            return str(val[0]) if isinstance(val, list) else str(val)
    return default


def read_metadata(path: str) -> dict:
    """
    Retorna un dict con:
        titulo, artista, album, genero, duracion (float seg), caratula (bytes|None)
    """
    result = {
        "titulo":   os.path.splitext(os.path.basename(path))[0],
        "artista":  "",
        "album":    "",
        "genero":   "",
        "duracion": 0.0,
        "caratula": None,
    }

    try:
        audio = MutagenFile(path, easy=False)
        if audio is None:
            return result

        # ── Duración ──────────────────────────────────────────────────────────
        if hasattr(audio, "info") and hasattr(audio.info, "length"):
            result["duracion"] = float(audio.info.length)

        tags = audio.tags or {}

        ext = os.path.splitext(path)[1].lower()

        # ── MP3 (ID3) ─────────────────────────────────────────────────────────
        if ext == ".mp3":
            result["titulo"]  = _get_tag(tags, "TIT2", default=result["titulo"])
            result["artista"] = _get_tag(tags, "TPE1", "TPE2")
            result["album"]   = _get_tag(tags, "TALB")
            result["genero"]  = _get_tag(tags, "TCON")
            # Carátula APIC
            for key in tags:
                if key.startswith("APIC"):
                    result["caratula"] = tags[key].data
                    break

        # ── M4A / AAC (MP4 tags) ──────────────────────────────────────────────
        elif ext in {".m4a", ".aac"}:
            result["titulo"]  = _get_tag(tags, "\xa9nam", default=result["titulo"])
            result["artista"] = _get_tag(tags, "\xa9ART", "aART")
            result["album"]   = _get_tag(tags, "\xa9alb")
            result["genero"]  = _get_tag(tags, "\xa9gen")
            covr = tags.get("covr")
            if covr:
                result["caratula"] = bytes(covr[0])

        # ── FLAC / OGG (VorbisComment) ────────────────────────────────────────
        else:
            result["titulo"]  = _get_tag(tags, "title",  "TITLE",  default=result["titulo"])
            result["artista"] = _get_tag(tags, "artist", "ARTIST")
            result["album"]   = _get_tag(tags, "album",  "ALBUM")
            result["genero"]  = _get_tag(tags, "genre",  "GENRE")
            # FLAC pictures
            if isinstance(audio, FLAC) and audio.pictures:
                result["caratula"] = audio.pictures[0].data

    except Exception:
        pass   # Si falla, devuelve los defaults

    return result


def get_supported_files(folder: str) -> list[str]:
    """Devuelve todos los archivos de audio soportados en folder (recursivo)."""
    found = []
    for root, _, files in os.walk(folder):
        for f in files:
            if os.path.splitext(f)[1].lower() in SUPPORTED_EXT:
                found.append(os.path.join(root, f))
    return sorted(found)
