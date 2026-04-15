import tkinter as tk
from tkinter import ttk
from tkinter import *
from PIL import Image, ImageTk 
from main import ventana

def ventanas_en_pantalla(ventana):
    label = ttk.Label(ventana, text="Hola Mundo", font=("Arial", 12))
    label.pack(pady=20)

def imagenes(type):
    nombre = f"assets/{type}.png"
    img = Image.open(nombre)
    img = img.resize((40, 40))  
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

boton_atrasar.place(x=570