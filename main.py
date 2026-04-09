import tkinter as tk
from tkinter import messagebox, ttk
from tkinter import *
from PIL import Image, ImageTk

ventana = tk.Tk()
ventana.title("Spotify 2")
ventana.geometry("1920x1080")
ventana.configure(bg="#0077b6")

def imagenes(type):
    nombre = f"assets/{type}.png"
    img = Image.open(nombre)
    img = img.resize((50, 50))  
    img_tk = ImageTk.PhotoImage(img)
    return img_tk

img_play = imagenes("play")
img_pause = imagenes("pause")
img_atrasar = imagenes("atrasar")
img_adelantar = imagenes("adelantar")

boton_play = tk.Button(
    ventana,
    image=img_play,
    bg="#0077b6",
    activebackground="#0077b6",
    borderwidth=0,
    highlightthickness=0)

boton_play.place(x=670, y=500)

boton_adelantar = tk.Button(
    ventana,
    image=img_adelantar,
    bg="#0077b6",
    activebackground="#0077b6",
    borderwidth=0,
    highlightthickness=0)

boton_adelantar.place(x=770, y=500)

boton_atrasar = tk.Button(
    ventana,
    image=img_atrasar,
    bg="#0077b6",
    activebackground="#0077b6",
    borderwidth=0,
    highlightthickness=0)

boton_atrasar.place(x=570, y=500)

ventana.mainloop()