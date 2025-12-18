"""
Simple Image Viewer for Raspberry Pi
------------------------------------
• Displays images from a folder
• Fullscreen HDMI output
• Cycles images every few seconds
• Written for Raspberry Pi OS 64-bit
• Easy to adapt for E-Ink displays later
"""

import os
import time
import pygame
from PIL import Image

# ==========================
# USER SETTINGS
# ==========================

# Folder where images are stored
IMAGE_FOLDER = "/home/pi/images"

# Time (in seconds) each image is displayed
DISPLAY_TIME = 5

# ==========================
# INITIAL SETUP
# ==========================

# Initialize pygame
pygame.init()

# Get screen size automatically
screen_info = pygame.display.Info()
SCREEN_WIDTH = screen_info.current_w
SCREEN_HEIGHT = screen_info.current_h

# Create fullscreen window
screen = pygame.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT),
    pygame.FULLSCREEN
)

# Hide mouse cursor
pygame.mouse.set_visible(False)

# ==========================
# LOAD IMAGE LIST
# ==========================

# Get all image files in the folder
image_files = [
    f for f in os.listdir(IMAGE_FOLDER)
    if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp"))
]

# Sort images alphabetically
image_files.sort()

# If no images are found, stop the program
if not image_files:
    print("No images found in", IMAGE_FOLDER)
    pygame.quit()
    exit()

# ==========================
# MAIN LOOP
# ==========================

running = True
image_index = 0

while running:
    # Handle quit events (keyboard / ctrl+c)
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            running = False
        if event.type == pygame.QUIT:
            running = False

    # Load image using Pillow
    image_path = os.path.join(IMAGE_FOLDER, image_files[image_index])
    image = Image.open(image_path)

    # Resize image to fit screen
    image = image.resize((SCREEN_WIDTH, SCREEN_HEIGHT))

    # Convert Pillow image to pygame format
    image_surface = pygame.image.fromstring(
        image.tobytes(),
        image.size,
        image.mode
    )

    # Draw image to screen
    screen.blit(image_surface, (0, 0))
    pygame.display.flip()

    # Wait before showing next image
    time.sleep(DISPLAY_TIME)

    # Move to next image
    image_index = (image_index + 1) % len(image_files)

# ==========================
# CLEAN EXIT
# ==========================

pygame.quit()
