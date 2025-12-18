"""
Framebuffer Image Viewer for Raspberry Pi OS Lite (64-bit, Debian Trixie)
------------------------------------------------------------------------
• No desktop environment required
• Writes directly to /dev/fb0
• Ideal base for HDMI now, E-Ink later
• Designed for Pi Zero 2 W
• Handles deleted images gracefully
"""

import os
import sys
import time
import struct
from PIL import Image

# ==========================
# USER SETTINGS
# ==========================

IMAGE_FOLDER = "/home/pictureframe/images"
DISPLAY_TIME = 5  # seconds per image
FRAMEBUFFER = "/dev/fb0"
RESCAN_INTERVAL = 30  # seconds - how often to refresh the image list

# ==========================
# HELPER FUNCTIONS
# ==========================

def get_screen_resolution():
    """
    Reads screen resolution from framebuffer
    """
    with open("/sys/class/graphics/fb0/virtual_size", "r") as f:
        width, height = f.read().strip().split(",")
    return int(width), int(height)


def fit_image_to_screen(image, screen_width, screen_height):
    """
    Resize image to fit screen while maintaining aspect ratio
    Centers the image on a black background
    """
    # Calculate scaling to fit within screen
    img_ratio = image.width / image.height
    screen_ratio = screen_width / screen_height
    
    if img_ratio > screen_ratio:
        # Image is wider - fit to width
        new_width = screen_width
        new_height = int(screen_width / img_ratio)
    else:
        # Image is taller - fit to height
        new_height = screen_height
        new_width = int(screen_height * img_ratio)
    
    # Resize image maintaining aspect ratio
    resized_image = image.resize((new_width, new_height), Image.LANCZOS)
    
    # Create black background
    final_image = Image.new("RGB", (screen_width, screen_height), (0, 0, 0))
    
    # Calculate position to center the image
    x_offset = (screen_width - new_width) // 2
    y_offset = (screen_height - new_height) // 2
    
    # Paste resized image onto black background
    final_image.paste(resized_image, (x_offset, y_offset))
    
    return final_image


def show_image_on_framebuffer(image):
    """
    Converts and writes an image directly to the framebuffer
    Assumes RGB565 (most Pi HDMI setups)
    """
    with open(FRAMEBUFFER, "wb") as fb:
        pixels = image.load()
        for y in range(image.height):
            for x in range(image.width):
                r, g, b = pixels[x, y]

                # Convert RGB888 → RGB565
                rgb565 = (
                    ((r & 0xF8) << 8) |
                    ((g & 0xFC) << 3) |
                    (b >> 3)
                )

                fb.write(struct.pack("<H", rgb565))


def get_image_list():
    """
    Get current list of valid image files
    """
    try:
        image_files = [
            f for f in os.listdir(IMAGE_FOLDER)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"))
        ]
        return sorted(image_files)
    except Exception as e:
        print(f"Error reading image folder: {e}")
        return []


# ==========================
# MAIN PROGRAM
# ==========================

def hide_cursor():
    """
    Hide the blinking cursor in the terminal using ANSI escape codes
    """
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()


def show_cursor():
    """
    Show the cursor again (for clean exit)
    """
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()


def main():
    # Hide cursor at startup
    hide_cursor()
    
    # Get screen resolution
    screen_width, screen_height = get_screen_resolution()

    print(f"Framebuffer resolution: {screen_width}x{screen_height}")
    print(f"Image folder: {IMAGE_FOLDER}")
    print(f"Rescanning for new images every {RESCAN_INTERVAL} seconds")
    print("-" * 50)

    last_rescan_time = 0
    image_files = []
    current_index = 0

    # Main display loop
    while True:
        current_time = time.time()
        
        # Rescan for images periodically or if list is empty
        if not image_files or (current_time - last_rescan_time) >= RESCAN_INTERVAL:
            print("Scanning for images...")
            image_files = get_image_list()
            last_rescan_time = current_time
            current_index = 0
            
            if not image_files:
                print("No images found. Waiting...")
                time.sleep(5)
                continue
            
            print(f"Found {len(image_files)} image(s)")

        # Get next image (wrap around if needed)
        if current_index >= len(image_files):
            current_index = 0

        filename = image_files[current_index]
        image_path = os.path.join(IMAGE_FOLDER, filename)

        try:
            # Check if file still exists
            if not os.path.exists(image_path):
                print(f"⚠️  Image deleted: {filename}")
                # Remove from list and rescan on next iteration
                image_files.pop(current_index)
                continue

            print(f"Displaying [{current_index + 1}/{len(image_files)}]: {filename}")

            # Open and process image
            image = Image.open(image_path).convert("RGB")
            
            # Fit image to screen while maintaining aspect ratio
            image = fit_image_to_screen(image, screen_width, screen_height)
            
            # Display on framebuffer
            show_image_on_framebuffer(image)
            
            # Move to next image
            current_index += 1
            
            # Wait before next image
            time.sleep(DISPLAY_TIME)

        except FileNotFoundError:
            print(f"⚠️  Image not found (deleted during display): {filename}")
            # Remove from list and continue
            image_files.pop(current_index)
            continue
            
        except Exception as e:
            print(f"❌ Error displaying {filename}: {e}")
            # Skip this image and move to next
            current_index += 1
            time.sleep(1)
            continue


# ==========================
# ENTRY POINT
# ==========================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting cleanly")
        show_cursor()
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        show_cursor()
    finally:
        show_cursor()
