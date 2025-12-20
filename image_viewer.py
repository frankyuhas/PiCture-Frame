"""
E-Ink Image Viewer for Raspberry Pi with 7.3inch E-Ink Spectra 6 (E6)
----------------------------------------------------------------------
• Waveshare 7.3inch E-Ink ACeP display (800x480)
• 7-color display support
• Uses gpiozero as recommended by Waveshare
• Instant detection of new/deleted images using inotify
• Maintains aspect ratio (no stretching)
"""

import os
import sys
import time
import threading
from PIL import Image
from inotify_simple import INotify, flags

# Import Waveshare E-Paper library
try:
    # The library should be installed in the system path
    from waveshare_epd import epd7in3e
except ImportError:
    print("=" * 60)
    print("ERROR: Waveshare E-Paper library not found!")
    print("=" * 60)
    print("Install instructions:")
    print("1. cd ~")
    print("2. git clone https://github.com/waveshare/e-Paper.git")
    print("3. cd e-Paper/RaspberryPi_JetsonNano/python/")
    print("4. sudo python3 setup.py install")
    print("=" * 60)
    sys.exit(1)

# ==========================
# USER SETTINGS
# ==========================

IMAGE_FOLDER = "/home/pictureframe/images"
DISPLAY_TIME = 30  # seconds per image (E-Ink is slow to refresh, ~15-30s)
SLEEP_BETWEEN_IMAGES = True  # Put display to sleep to save power

# ==========================
# GLOBAL STATE
# ==========================

image_list_lock = threading.Lock()
image_files = []
list_updated = threading.Event()
epd = None

# ==========================
# E-INK HELPER FUNCTIONS
# ==========================

def init_display():
    """
    Initialize the E-Ink display
    """
    global epd
    print("Initializing E-Ink display...")
    print("This may take 15-30 seconds...")
    
    try:
        epd = epd7in3e.EPD()
        print("  - Calling epd.init()...")
        epd.init()
        
        print("  - Clearing display...")
        epd.Clear()
        
        print(f"✓ E-Ink display ready: {epd.width}x{epd.height} pixels")
        print(f"  Colors: Black, White, Red, Yellow, Blue, Green, Orange")
        return epd
    except Exception as e:
        print(f"❌ Failed to initialize display: {e}")
        print("\nTroubleshooting:")
        print("1. Check SPI is enabled: sudo raspi-config -> Interface Options -> SPI")
        print("2. Check wiring connections")
        print("3. Try running with sudo")
        return None


def fit_image_to_screen(image, screen_width, screen_height):
    """
    Resize image to fit screen while maintaining aspect ratio
    Centers the image on a white background (better for E-Ink)
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
    
    # Create white background (better for E-Ink than black)
    final_image = Image.new("RGB", (screen_width, screen_height), (255, 255, 255))
    
    # Calculate position to center the image
    x_offset = (screen_width - new_width) // 2
    y_offset = (screen_height - new_height) // 2
    
    # Paste resized image onto white background
    final_image.paste(resized_image, (x_offset, y_offset))
    
    return final_image


def display_image_on_eink(image):
    """
    Display image on E-Ink screen
    Note: This takes 15-30 seconds due to E-Ink refresh time
    """
    global epd
    
    if epd is None:
        print("❌ E-Ink display not initialized")
        return False
    
    try:
        print("  → Converting image for E-Ink display...")
        
        # The 7.3e supports landscape by default (800x480)
        # If your display appears rotated, uncomment one of these:
        # image = image.rotate(90, expand=True)
        # image = image.rotate(180, expand=True)
        # image = image.rotate(270, expand=True)
        
        # Get the image buffer
        buffer = epd.getbuffer(image)
        
        print("  → Refreshing E-Ink (this takes ~15-30 seconds)...")
        start_time = time.time()
        
        # Display the image
        epd.display(buffer)
        
        elapsed = time.time() - start_time
        print(f"  ✓ Display refreshed in {elapsed:.1f} seconds")
        
        # Optional: Put display to sleep to save power
        if SLEEP_BETWEEN_IMAGES:
            print("  → Putting display to sleep mode...")
            epd.sleep()
        
        return True
        
    except Exception as e:
        print(f"❌ Error displaying image: {e}")
        return False


# ==========================
# IMAGE LIST MANAGEMENT
# ==========================

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
            print(f"\n📁 Image list updated: {len(image_files)} image(s)")


def file_watcher():
    """
    Watch the image folder for changes using inotify
    Runs in a separate thread
    """
    print(f"👁️  Watching folder for changes: {IMAGE_FOLDER}")
    
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
    global image_files, epd
    
    print("=" * 60)
    print("E-Ink Picture Frame Viewer")
    print("=" * 60)
    
    # Initialize E-Ink display
    epd = init_display()
    if epd is None:
        print("\n❌ Failed to initialize display. Exiting.")
        print("Make sure to run with: sudo python3 image_viewer.py")
        return

    print(f"\n📂 Image folder: {IMAGE_FOLDER}")
    print(f"⏱️  Display time: {DISPLAY_TIME} seconds per image")
    print(f"🔔 Instant file detection: Enabled")
    print("=" * 60)

    # Ensure image folder exists
    os.makedirs(IMAGE_FOLDER, exist_ok=True)

    # Initial image list
    update_image_list()

    # Start file watcher thread
    watcher_thread = threading.Thread(target=file_watcher, daemon=True)
    watcher_thread.start()

    current_index = 0
    last_display_time = 0

    # Main display loop
    print("\nStarting slideshow...\n")
    
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
            print("⏳ No images found. Waiting for uploads...")
            time.sleep(5)
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
                time.sleep(1)
                continue

            print(f"\n📸 [{current_index + 1}/{len(current_files)}] {filename}")

            # Wake display if it was sleeping
            if SLEEP_BETWEEN_IMAGES:
                print("  → Waking display...")
                epd.init()

            # Open and process image
            print("  → Loading image...")
            image = Image.open(image_path).convert("RGB")
            
            # Fit image to screen while maintaining aspect ratio
            print("  → Fitting to screen...")
            image = fit_image_to_screen(image, epd.width, epd.height)
            
            # Display on E-Ink
            if display_image_on_eink(image):
                last_display_time = current_time
                current_index += 1
                print(f"  ✓ Next image in {DISPLAY_TIME} seconds\n")
            else:
                print("  ✗ Failed to display, retrying in 5 seconds...")
                time.sleep(5)

        except FileNotFoundError:
            print(f"⚠️  Image not found (deleted during display): {filename}")
            update_image_list()
            continue
            
        except Exception as e:
            print(f"❌ Error with {filename}: {e}")
            current_index += 1
            time.sleep(5)
            continue


# ==========================
# ENTRY POINT
# ==========================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("Shutting down...")
        print("=" * 60)
        if epd is not None:
            try:
                print("Putting display to sleep...")
                epd.sleep()
                print("✓ Display sleep mode activated")
            except Exception as e:
                print(f"Note: {e}")
        print("✓ Exited cleanly\n")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        if epd is not None:
            try:
                epd.sleep()
            except:
                pass
