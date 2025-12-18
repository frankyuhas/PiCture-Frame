"""
Framebuffer Image Viewer for Raspberry Pi OS Lite (64-bit, Debian Trixie)
------------------------------------------------------------------------
• No desktop environment required
• Writes directly to /dev/fb0
• Ideal base for HDMI now, E-Ink later
• Designed for Pi Zero 2 W
"""

import os
import time
import struct
from PIL import Image

# ==========================
# USER SETTINGS
# ==========================

IMAGE_FOLDER = "/home/pictureframe/images"
DISPLAY_TIME = 5  # seconds per image
FRAMEBUFFER = "/dev/fb0"

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


# ==========================
# MAIN PROGRAM
# ==========================

def main():
    # Get screen resolution
    screen_width, screen_height = get_screen_resolution()

    print(f"Framebuffer resolution: {screen_width}x{screen_height}")

    # Load image list
    image_files = [
        f for f in os.listdir(IMAGE_FOLDER)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp"))
    ]

    image_files.sort()

    if not image_files:
        print("No images found in", IMAGE_FOLDER)
        return

    # Main display loop
    while True:
        for filename in image_files:
            image_path = os.path.join(IMAGE_FOLDER, filename)
            print("Displaying:", image_path)

            # Open image
            image = Image.open(image_path).convert("RGB")

            # Resize to screen
            image = image.resize((screen_width, screen_height))

            # Display on framebuffer
            show_image_on_framebuffer(image)

            # Wait before next image
            time.sleep(DISPLAY_TIME)


# ==========================
# ENTRY POINT
# ==========================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting cleanly")

