import tkinter as tk
from PIL import Image, ImageTk

# ── Image loader ──────────────────────────────────────────────────────────────
def cargar_imagen(tipo, size=(40, 40)):
    img = Image.open(f"assets/{tipo}.png")
    img = img.resize(size)
    return ImageTk.PhotoImage(img)

# ── Button factory ────────────────────────────────────────────────────────────
def crear_botones(ventana):
    """Crea y retorna los botones de reproducción. Recibe la ventana como parámetro."""

    # Load images (kept alive as attributes to prevent garbage collection)
    imgs = {
        "play":      cargar_imagen("play"),
        "pause":     cargar_imagen("pause"),
        "atrasar":   cargar_imagen("atrasar"),
        "adelantar": cargar_imagen("adelantar"),
    }

    stylo_boton = dict(
        bg="#0077b6",
        activebackground="#0077b6",
        borderwidth=0,
        highlightthickness=0,
    )

    boton_atrasar   = tk.Button(ventana, image=imgs["atrasar"],   **stylo_boton)
    boton_play      = tk.Button(ventana, image=imgs["play"],      **stylo_boton)
    boton_adelantar = tk.Button(ventana, image=imgs["adelantar"], **stylo_boton)

    # Prevent garbage collection of PhotoImage objects
    for btn, key in zip([boton_atrasar, boton_play, boton_adelantar],
                        ["atrasar", "play", "adelantar"]):
        btn.image = imgs[key]

    return boton_play, boton_adelantar, boton_atrasar, imgs