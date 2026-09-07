import os
import glob
from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_DIR = os.path.join(BASE_DIR, "assets", "history")

def optimize_images():
    png_files = glob.glob(os.path.join(HISTORY_DIR, "*.png"))
    total_files = len(png_files)
    
    if not png_files:
        print("No PNG files found in assets/history!")
        return

    print(f"Found {total_files} PNG images. Converting to WebP...")
    
    saved_bytes = 0

    for i, png_path in enumerate(png_files, 1):
        filename = os.path.basename(png_path)
        webp_filename = os.path.splitext(filename)[0] + ".webp"
        webp_path = os.path.join(HISTORY_DIR, webp_filename)

        original_size = os.path.getsize(png_path)

        with Image.open(png_path) as img:
            # Save as WebP with 80% quality (sharp text, ~70% smaller file size)
            img.save(webp_path, "WEBP", quality=80, method=6)

        new_size = os.path.getsize(webp_path)
        saved_bytes += (original_size - new_size)

        # Delete original PNG to free space
        os.remove(png_path)

        print(f"[{i}/{total_files}] Converted: {filename} -> {webp_filename} ({(1 - new_size/original_size)*100:.1f}% reduction)")

    print("-" * 50)
    print(f"Done! Saved approximately {saved_bytes / (1024 * 1024):.2f} MB across {total_files} files.")

if __name__ == "__main__":
    optimize_images()