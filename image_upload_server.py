"""
Simple Local Image Upload Web Server for Raspberry Pi
-----------------------------------------------------
• Runs on Pi OS Lite (no desktop)
• Local network access only
• Upload images via browser
• Saves files to image folder
"""

from flask import Flask, request, render_template, redirect, url_for, send_from_directory, abort
import os


# Absolute path to your project folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# ==========================
# USER SETTINGS
# ==========================

IMAGE_FOLDER = os.path.join(BASE_DIR, "static/images")
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp"}
PORT = 8080   # Web page will be http://pi-ip:8080

# ==========================
# BASIC SETUP
# ==========================

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

app.config["UPLOAD_FOLDER"] = IMAGE_FOLDER

# Ensure image folder exists
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# ==========================
# HELPER FUNCTIONS
# ==========================

def allowed_file(filename):
    """
    Check if file has an allowed image extension
    """
    ext = os.path.splitext(filename.lower())[1]
    return ext in ALLOWED_EXTENSIONS
    
def get_images():
    """Return a sorted list of image filenames in IMAGE_FOLDER"""
    return sorted(
        f for f in os.listdir(IMAGE_FOLDER)
        if allowed_file(f)
    )

# ==========================
# ROUTES
# ==========================

@app.route("/", methods=["GET"])
def index():
    images = get_images()
    return render_template("index.html", images=images)

@app.route("/upload", methods=["POST"])
@app.route("/upload", methods=["POST"])
def upload():
    files = request.files.getlist("file")  # support multiple files
    for file in files:
        if file.filename and allowed_file(file.filename):
            filename = os.path.basename(file.filename)
            file.save(os.path.join(IMAGE_FOLDER, filename))
    return redirect(url_for("index"))


# ==========================
# ENTRY POINT
# ==========================

if __name__ == "__main__":
    # Bind to all interfaces so LAN devices can access it
    app.run(host="0.0.0.0", port=PORT)








