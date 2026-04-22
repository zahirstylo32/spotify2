# Spotify 2 🎵

Reproductor de música de escritorio construido con **Tkinter + pygame + mutagen**.

---

## Estructura del proyecto

```
spotify2/
├── main.py          ← Entry point
├── interfaz.py      ← UI completa (Tkinter)
├── player.py        ← Motor de audio (pygame.mixer)
├── queue.py         ← Cola de reproducción (shuffle / loop)
├── database.py      ← Capa de datos (SQLite)
├── metadata.py      ← Lectura de metadatos (mutagen)
├── requirements.txt
└── README.md
```

La base de datos `spotify2.db` se crea automáticamente en el directorio de ejecución.

---

## Instalación

```bash
# Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate          # Linux/macOS
venv\Scripts\activate             # Windows

# Instalar dependencias
pip install -r requirements.txt
```

> **Tkinter** viene incluido con Python en Windows y macOS.
> En Linux puede que necesites: `sudo apt install python3-tk`

---

## Ejecutar

```bash
python main.py
```

---

## Funcionalidades

### Reproducción
| Acción | Cómo |
|---|---|
| Reproducir canción | Doble clic en la lista |
| Play / Pausa | Botón ▶ / ⏸ en la barra inferior |
| Siguiente / Anterior | Botones ⏭ ⏮ |
| Volumen | Slider 🔊 |
| Saltar posición | Arrastrar la barra de progreso |

### Modos
| Botón | Modo |
|---|---|
| ⇄ (azul) | Shuffle activado |
| ↺ (gris) | Sin repetición |
| ↺ (azul) | Repetir toda la lista |
| ↻¹ (azul) | Repetir canción |

### Biblioteca
- **Agregar carpeta** → importa todos los MP3/FLAC/OGG/WAV/M4A de forma recursiva.
- Los metadatos (título, artista, álbum, género, carátula) se leen automáticamente.
- **Buscar** por título, artista, álbum o género con el campo de búsqueda.
- **Ordenar** columnas haciendo clic en el encabezado.

### Playlists
- Crear playlist con el botón **"＋ Nueva playlist"**.
- Agregar canciones: clic derecho sobre una canción → *Agregar a playlist*.
- Ver playlist: doble clic en la lista lateral.
- Renombrar / eliminar: clic derecho sobre la playlist.

---

## Formatos soportados
`.mp3` · `.flac` · `.ogg` · `.wav` · `.m4a` · `.aac`
