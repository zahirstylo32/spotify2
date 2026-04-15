import tkinter as tk
from tkinter import messagebox, ttk
from tkinter import *
from PIL import Image, ImageTk
from interfaz import boton_play, boton_adelantar, boton_atrasar

ventana = tk.Tk()
ventana.title("Spotify 2")
ventana.geometry("1920x1080")
ventana.configure(bg="#0077b6")



boton_play.place(x=670, y=500)
boton_adelantar.place(x=770, y=500)
boton_atrasar.place(x=570, y=500)

ventana.mainloop()