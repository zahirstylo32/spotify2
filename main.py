import tkinter as tk
from tkinter import messagebox, ttk
from tkinter import *
from PIL import Image, ImageTk

ventana = tk.Tk()
ventana.title("Spotify 2")
ventana.geometry("1920x1080")
ventana.configure(bg="#4E4D4D")

img = Image.open("assets/play.png")
img = img.resize((50, 50))  
img_tk = ImageTk.PhotoImage(img)

boton_play = Button(ventana, image=img_tk, bg="white", activebackground= "white", borderwidth= 0, highlightthickness= 0 )
boton_play.place(x=670, y=500)



ventana.mainloop()