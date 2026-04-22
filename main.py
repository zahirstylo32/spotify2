"""
main.py — Entry point de Spotify 2.
"""

import tkinter as tk
from interfaz import App

if __name__ == "__main__":
    ventana = tk.Tk()
    app = App(ventana)
    ventana.protocol("WM_DELETE_WINDOW", app.on_close)
    ventana.mainloop()