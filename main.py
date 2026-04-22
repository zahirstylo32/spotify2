import tkinter as tk
from interfaz import crear_botones

# ── Main window ───────────────────────────────────────────────────────────────
ventana = tk.Tk()
ventana.title("Spotify 2")
ventana.geometry("1920x1080")
ventana.configure(bg="#0077b6")

# ── Buttons (ventana is passed in — no circular import) ───────────────────────
boton_play, boton_adelantar, boton_atrasar, imgs = crear_botones(ventana)

boton_atrasar.place(  x=570, y=500)
boton_play.place(     x=670, y=500)
boton_adelantar.place(x=770, y=500)

ventana.mainloop()