import tkinter as tk
from tkinter import ttk
from tkinter import *
from PIL import Image, ImageTk 

def ventanas_en_pantalla(ventana):
    label = ttk.Label(ventana, text="Hola Mundo", font=("Arial", 12))
    label.pack(pady=20)

