# tkinter_version_check.py
import sys, tkinter as tk

print("Python :", sys.version)
root = tk.Tk()
print("Tk patchlevel :", root.tk.call("info", "patchlevel"))
root.destroy()
