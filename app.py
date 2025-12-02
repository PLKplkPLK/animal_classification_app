from email import message
from shutil import ExecError
import sys
import threading

import torch
import tkinter as tk
from tkinter import filedialog, messagebox

from pipeline import run_megadetector, run_pipeline


# -------- Redirect print() to Text widget --------
class RedirectText:
    def __init__(self, widget):
        self.widget = widget

    def write(self, text):
        self.widget.insert(tk.END, text)
        self.widget.see(tk.END)
        self.widget.update_idletasks()

    def flush(self):
        pass

# -------- GUI Logic --------
def select_folder():
    folder = filedialog.askdirectory()
    folder_path.set(folder)

def run():
    folder = folder_path.get()
    if not folder:
        messagebox.showerror("Error", "Please select a folder")
        return

    try:
        batch = int(batch_size_var.get())
        workers = int(workers_var.get())
    except ValueError:
        messagebox.showerror("Error", "Batch size & workers must be numbers")
        return

    def task():
        try:
            run_megadetector(folder, batch, workers)
            run_pipeline(batch)
            messagebox.showinfo("Done", "Processing complete")
        except ExecError as error:
            messagebox.showerror("Batch size too big", str(error))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    threading.Thread(target=task).start()

# -------- App --------
root = tk.Tk()
root.title("Image Classifier")
root.geometry("650x500")

# GPU / CPU Status
device = "GPU" if torch.cuda.is_available() else "CPU"
tk.Label(root, text=f"Running on: {device}", fg="green").pack(pady=5)

# Folder selection
folder_path = tk.StringVar()
tk.Label(root, text="Image Directory").pack()
tk.Entry(root, textvariable=folder_path, width=60).pack()
tk.Button(root, text="Browse", command=select_folder).pack(pady=5)

# Parameters
params_frame = tk.Frame(root)
params_frame.pack(pady=10)

batch_size_var = tk.StringVar(value="10")
workers_var = tk.StringVar(value="1")

if device == "GPU":
    tk.Label(params_frame, text="Batch size:").grid(row=0, column=0)
    tk.Entry(params_frame, textvariable=batch_size_var, width=6).grid(row=0, column=1, padx=10)
else:
    tk.Label(params_frame, text="CPU workers:").grid(row=0, column=2)
    tk.Entry(params_frame, textvariable=workers_var, width=6).grid(row=0, column=3)

# Run button
tk.Button(root, text="Run Classification", command=run).pack(pady=10)

# Output console
output = tk.Text(root, height=15)
output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

sys.stdout = RedirectText(output)
sys.stderr = RedirectText(output)

root.mainloop()
