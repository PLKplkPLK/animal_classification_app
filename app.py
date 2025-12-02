import sys
import threading
import gc
from shutil import ExecError

import torch
import tkinter as tk
from tkinter import filedialog, messagebox

from pipeline import run_megadetector, run_pipeline


# -------- Redirect print() to Text widget --------
class RedirectText:
    def __init__(self, widget):
        self.widget = widget

    def write(self, text: str):
        # Handle carriage-return updates (e.g. tqdm progress bars)
        if '\r' in text:
            segment = text.replace('\r', '')
            self.widget.delete("end-1l linestart", tk.END)
            self.widget.insert(tk.END, segment)
        # keep view scrolled to end and update UI
        try:
            self.widget.see(tk.END)
            self.widget.update_idletasks()
        except Exception:
            pass

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
        batch_md = int(batch_size_var_md.get())
        batch_df = int(batch_size_var_df.get())
        workers = int(workers_var.get())
    except ValueError:
        messagebox.showerror("Error", "Batch size & workers must be numbers")
        return

    def task():
        try:
            status_var.set("Running detector...")
            run_megadetector(folder, batch_md, workers)
            status_var.set("Running classifier...")
            run_pipeline(batch_df)
            messagebox.showinfo("Done", "Processing complete")
        except ExecError as error:
            messagebox.showerror("Detector batch too big", str(error))
        except Exception as e:
            if "CUDA out of memory" in str(e):
                messagebox.showerror(
                    "Classifier batch too big",
                    "Lower classifier batch size. Your GPU doesn't have this much memory."
                )
            else:
                messagebox.showerror("Unexpected error", str(e))
        finally:
            gc.collect()
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
            output.delete("1.0", tk.END)

    threading.Thread(target=task).start()

# -------- App --------
root = tk.Tk()
root.title("Image Classifier")
root.geometry("500x330")

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

batch_size_var_md = tk.StringVar(value="10")
batch_size_var_df = tk.StringVar(value="10")
workers_var = tk.StringVar(value="1")

if device == "GPU":
    tk.Label(params_frame, text="Batch size detector:").grid(row=0, column=0)
    tk.Entry(params_frame, textvariable=batch_size_var_md, width=6).grid(row=0, column=1, padx=10)
    tk.Label(params_frame, text="Batch size classifier:").grid(row=0, column=3)
    tk.Entry(params_frame, textvariable=batch_size_var_df, width=6).grid(row=0, column=4, padx=10)
else:
    tk.Label(params_frame, text="CPU workers:").grid(row=0, column=2)
    tk.Entry(params_frame, textvariable=workers_var, width=6).grid(row=0, column=3)

# Run button
tk.Button(root, text="Run Classification", command=run).pack(pady=10)

tk.Label(root, text="Currently:").pack()
status_var = tk.StringVar(value="waiting for your folder and classificaion start")
tk.Label(root, textvariable=status_var).pack()

# Output console
output = tk.Text(root, height=1)
output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

sys.stdout = RedirectText(output)
sys.stderr = RedirectText(output)

root.mainloop()
