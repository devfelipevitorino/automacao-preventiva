import tkinter as tk
from PIL import Image, ImageTk
import sys
import os
from aplicador import AplicadorPermissoes 

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS 
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def main():
    root = tk.Tk()

    ico_path = resource_path("icone.ico")
    png_path = resource_path("icone.png")

    try:
        root.iconbitmap(ico_path)
    except Exception as e:
        print(f"Erro ao carregar icone.ico: {e}")

    try:
        img = Image.open(png_path)
        photo = ImageTk.PhotoImage(img)
        root.iconphoto(True, photo)
        root._img_icon = photo  
    except Exception as e:
        print(f"Erro ao carregar icone.png: {e}")

    app = AplicadorPermissoes(root)
    root.mainloop()

if __name__ == "__main__":
    main()
