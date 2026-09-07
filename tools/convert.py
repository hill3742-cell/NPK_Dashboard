import os
import tkinter as tk
from tkinter import messagebox

try:
    import fitz  # PyMuPDF
except ImportError:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Missing PyMuPDF", "PyMuPDF is required. Run 'pip install pymupdf' in terminal.")
    exit()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET_DIR = os.path.join(BASE_DIR, "assets", "history")
os.makedirs(TARGET_DIR, exist_ok=True)

# Look for the PDF in the tools folder or the project root
pdf_name = "No Pain Keeper League - All Seasons History.pdf"
local_pdf = os.path.join(os.path.dirname(os.path.abspath(__file__)), pdf_name)
root_pdf = os.path.join(BASE_DIR, pdf_name)

pdf_path = local_pdf if os.path.exists(local_pdf) else (root_pdf if os.path.exists(root_pdf) else None)

root = tk.Tk()
root.withdraw()

if not pdf_path:
    messagebox.showerror("File Not Found", f"Could not find '{pdf_name}' in tools or root directory.")
    exit()

doc = fitz.open(pdf_path)
total_pages = len(doc)

# Pages map chronologically: Page 0 = 2011 up through latest season
start_year = 2011
for page_num in range(total_pages):
    season_year = start_year + page_num
    page = doc[page_num]
    pix = page.get_pixmap(dpi=150)
    out_file = os.path.join(TARGET_DIR, f"{season_year}_season_history.png")
    pix.save(out_file)

messagebox.showinfo("Conversion Complete", f"Successfully converted {total_pages} seasons to:\n{TARGET_DIR}")