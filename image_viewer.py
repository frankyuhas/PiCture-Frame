"""
Framebuffer Image Viewer for Raspberry Pi OS Lite (64-bit, Debian Trixie)
------------------------------------------------------------------------
• No desktop environment required
• Writes directly to /dev/fb0
• Instant detection of new/deleted images using inotify
• Handles deleted images gracefully
• Maintains aspect ratio (no stretching)
"""

import os
import sys
import time
import struct
import threading
from PIL import Image
from inotify_simple import INotify, flags

# ==========================
# USER SETTINGS
# ==========================

IMAGE_FOLDER = "/home/pictureframe/images"
DISPLAY_TIME = 5  # seconds per image
FRAMEBUFFER = "/dev/fb0"

# ==========================
# GLOBAL STATE
# ==========================

image_list_lock = threading.Lock()
image_files = []
list_updated = threading.Event()

# ==========================
# HELPER FUNCTIONS
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
        files = [
            f for f in os.listdir(IMAGE_FOLDER)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"))
        ]
        return sorted(files)
    except Exception as e:
        print(f"Error reading image folder: {e}")
        return []


def update_image_list():
    """
    Update the global image list thread-safely
    """
    global image_files
    new_list = get_image_list()
    
    with image_list_lock:
        if new_list != image_files:
            image_files = new_list
            list_updated.set()
            print(f"📁 Image list updated: {len(image_files)} image(s)")


def file_watcher():
    """
    Watch the image folder for changes using inotify
    Runs in a separate thread
    """
    print(f"👁️  Watching folder: {IMAGE_FOLDER}")
    
    inotify = INotify()
    watch_flags = flags.CREATE | flags.DELETE | flags.MOVED_TO | flags.MOVED_FROM | flags.CLOSE_WRITE
    inotify.add_watch(IMAGE_FOLDER, watch_flags)
    
    while True:
        try:
            events = inotify.read(timeout=1000)
            if events:
                # Give a short delay for file writes to complete
                time.sleep(0.1)
                update_image_list()
        except Exception as e:
            print(f"File watcher error: {e}")
            time.sleep(1)


# ==========================
# MAIN PROGRAM
# ==========================

def main():
    global image_files
    
    # Hide cursor at startup
    hide_cursor()
    
    # Get screen resolution
    screen_width, screen_height = get_screen_resolution()

    print(f"Framebuffer resolution: {screen_width}x{screen_height}")
    print(f"Image folder: {IMAGE_FOLDER}")
    print(f"Instant file detection enabled")
    print("-" * 50)

    # Initial image list
    update_image_list()

    # Start file watcher thread
    watcher_thread = threading.Thread(target=file_watcher, daemon=True)
    watcher_thread.start()

    current_index = 0
    last_display_time = 0

    # Main display loop
    while True:
        with image_list_lock:
            current_files = image_files.copy()
        
        # Check if list was updated
        if list_updated.is_set():
            list_updated.clear()
            # Reset index if we're beyond the new list length
            if current_index >= len(current_files):
                current_index = 0
        
        if not current_files:
            print("No images found. Waiting...")
            time.sleep(2)
            continue

        # Get next image (wrap around if needed)
        if current_index >= len(current_files):
            current_index = 0

        filename = current_files[current_index]
        image_path = os.path.join(IMAGE_FOLDER, filename)

        try:
            # Check if file still exists
            if not os.path.exists(image_path):
                print(f"⚠️  Image deleted: {filename}")
                update_image_list()
                continue

            # Only display if enough time has passed
            current_time = time.time()
            if current_time - last_display_time < DISPLAY_TIME:
                time.sleep(0.1)
                continue

            print(f"Displaying [{current_index + 1}/{len(current_files)}]: {filename}")

            # Open and process image
            image = Image.open(image_path).convert("RGB")
            
            # Fit image to screen while maintaining aspect ratio
            image = fit_image_to_screen(image, screen_width, screen_height)
            
            # Display on framebuffer
            show_image_on_framebuffer(image)
            
            # Update timing and move to next image
            last_display_time = current_time
            current_index += 1

        except FileNotFoundError:
            print(f"⚠️  Image not found (deleted during display): {filename}")
            update_image_list()
            continue
            
        except Exception as e:
            print(f"❌ Error displaying {filename}: {e}")
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
