import tkinter as tk
from .ui import PixelArtSchematicApp

def main():
    root = tk.Tk()
    app = PixelArtSchematicApp(root)
    app.pack(expand=True, fill="both")
    root.mainloop()
