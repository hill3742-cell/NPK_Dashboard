import fitz  # PyMuPDF
import glob

# Find all the individual yearly PDFs in your folder
pdf_files = glob.glob("No Pain Keeper League - * Season History.pdf")

if not pdf_files:
    print("No yearly PDF files found to convert.")

for pdf_path in pdf_files:
    # Extract just the year from the file name
    year = pdf_path.split(" - ")[1].split(" ")[0]
    
    # Open the PDF file
    doc = fitz.open(pdf_path)
    
    # Loop through every page in the PDF
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        
        # Render the page to a high-resolution image (200 DPI)
        pix = page.get_pixmap(dpi=200)
        
        # Save the image with the year and page number
        output_name = f"{year}_season_history_page_{page_num + 1}.png"
        pix.save(output_name)
        
        print(f"Converted {year} Page {page_num + 1} -> {output_name}")