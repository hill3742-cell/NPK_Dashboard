import os
import shutil
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, simpledialog

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET_DIR = os.path.join(BASE_DIR, "assets", "weekly")
os.makedirs(TARGET_DIR, exist_ok=True)

root = tk.Tk()
root.withdraw()

current_year = datetime.now().year
year = simpledialog.askinteger("Preview Setup", "Enter Season Year:", initialvalue=current_year, minvalue=2010, maxvalue=2050)
if not year:
    exit()

week = simpledialog.askinteger("Preview Setup", "Enter Week Number (1-18):", initialvalue=1, minvalue=1, maxvalue=18)
if not week:
    exit()

file_path = filedialog.askopenfilename(
    title=f"Select Preview File for {year} Week {week}",
    filetypes=[
        ("Supported Files", "*.png;*.jpg;*.jpeg;*.webp;*.txt;*.pdf"),
        ("Images", "*.png;*.jpg;*.jpeg;*.webp"),
        ("Text Files", "*.txt"),
        ("PDF Files", "*.pdf"),
        ("All Files", "*.*")
    ]
)

if not file_path:
    exit()

ext = os.path.splitext(file_path)[1].lower()

if ext == ".pdf":
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap(dpi=150)
            suffix = f"_p{page_num + 1}" if len(doc) > 1 else ""
            out_name = f"{year}_W{week}_preview{suffix}.png"
            pix.save(os.path.join(TARGET_DIR, out_name))
        messagebox.showinfo("Success", f"Preview PDF converted to image(s) in assets/weekly/ as {year}_W{week}_preview.png")
    except ImportError:
        messagebox.showerror("PyMuPDF Required", "To convert PDFs directly, install fitz: pip install pymupdf\nOr select an exported PNG/JPG.")
else:
    target_filename = f"{year}_W{week}_preview{ext}"
    target_path = os.path.join(TARGET_DIR, target_filename)
    shutil.copyfile(file_path, target_path)
    messagebox.showinfo("Success", f"Saved successfully:\n{target_path}")