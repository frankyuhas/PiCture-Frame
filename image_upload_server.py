"""
Enhanced Local Image Upload Web Server for Raspberry Pi
--------------------------------------------------------
• Modern, responsive UI with drag-and-drop
• Image gallery with thumbnails
• Progress feedback and animations
• Mobile-friendly design
"""

from flask import Flask, request, redirect, url_for, jsonify, render_template_string
import os
from datetime import datetime

# ==========================
# USER SETTINGS
# ==========================

IMAGE_FOLDER = "/home/pictureframe/images"
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
PORT = 8080
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# ==========================
# BASIC SETUP
# ==========================

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = IMAGE_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE

os.makedirs(IMAGE_FOLDER, exist_ok=True)

# ==========================
# HELPER FUNCTIONS
# ==========================

def allowed_file(filename):
    ext = os.path.splitext(filename.lower())[1]
    return ext in ALLOWED_EXTENSIONS

def get_uploaded_images():
    """Get list of uploaded images with metadata"""
    images = []
    if os.path.exists(IMAGE_FOLDER):
        for filename in os.listdir(IMAGE_FOLDER):
            if allowed_file(filename):
                filepath = os.path.join(IMAGE_FOLDER, filename)
                stat = os.stat(filepath)
                images.append({
                    "name": filename,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                })
    return sorted(images, key=lambda x: x["modified"], reverse=True)

# ==========================
# HTML TEMPLATE
# ==========================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pi Image Upload</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }

        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }

        .upload-section {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            margin-bottom: 30px;
        }

        .upload-zone {
            border: 3px dashed #667eea;
            border-radius: 15px;
            padding: 60px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            background: #f8f9ff;
        }

        .upload-zone:hover {
            border-color: #764ba2;
            background: #f0f2ff;
            transform: translateY(-2px);
        }

        .upload-zone.drag-over {
            border-color: #4CAF50;
            background: #e8f5e9;
            transform: scale(1.02);
        }

        .upload-icon {
            font-size: 4em;
            margin-bottom: 20px;
        }

        .upload-zone h3 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.5em;
        }

        .upload-zone p {
            color: #666;
            font-size: 0.95em;
        }

        #file-input {
            display: none;
        }

        .file-info {
            margin-top: 20px;
            padding: 15px;
            background: #e3f2fd;
            border-radius: 10px;
            display: none;
        }

        .file-info.show {
            display: block;
        }

        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e0e0e0;
            border-radius: 10px;
            margin-top: 15px;
            overflow: hidden;
            display: none;
        }

        .progress-bar.show {
            display: block;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            width: 0%;
            transition: width 0.3s ease;
            border-radius: 10px;
        }

        .upload-btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 1.1em;
            border-radius: 10px;
            cursor: pointer;
            margin-top: 20px;
            transition: all 0.3s ease;
            display: none;
        }

        .upload-btn.show {
            display: inline-block;
        }

        .upload-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }

        .upload-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .message {
            padding: 15px 20px;
            border-radius: 10px;
            margin-top: 20px;
            display: none;
            animation: slideIn 0.3s ease;
        }

        .message.show {
            display: block;
        }

        .message.success {
            background: #4CAF50;
            color: white;
        }

        .message.error {
            background: #f44336;
            color: white;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .gallery-section {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }

        .gallery-section h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8em;
        }

        .image-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        .image-card {
            background: #f8f9ff;
            border-radius: 12px;
            padding: 15px;
            transition: all 0.3s ease;
            border: 2px solid transparent;
        }

        .image-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.2);
            border-color: #667eea;
        }

        .image-thumbnail {
            width: 100%;
            height: 150px;
            object-fit: cover;
            border-radius: 8px;
            background: #e0e0e0;
        }

        .image-info {
            margin-top: 10px;
        }

        .image-name {
            font-weight: 600;
            color: #333;
            font-size: 0.9em;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .image-meta {
            font-size: 0.8em;
            color: #666;
            margin-top: 5px;
        }

        .empty-gallery {
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }

        .empty-gallery-icon {
            font-size: 4em;
            margin-bottom: 15px;
            opacity: 0.3;
        }

        @media (max-width: 768px) {
            .header h1 {
                font-size: 2em;
            }

            .upload-section, .gallery-section {
                padding: 25px;
            }

            .image-grid {
                grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
                gap: 15px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖼️ Pi Image Upload</h1>
            <p>Drag & drop or click to upload images</p>
        </div>

        <div class="upload-section">
            <div class="upload-zone" id="upload-zone">
                <div class="upload-icon">📤</div>
                <h3>Drop images here</h3>
                <p>or click to browse</p>
                <p style="margin-top: 10px; font-size: 0.85em; color: #999;">
                    Supported: PNG, JPG, JPEG, BMP, GIF, WebP (Max 16MB)
                </p>
            </div>
            <input type="file" id="file-input" accept="image/*" multiple>
            
            <div class="file-info" id="file-info"></div>
            <div class="progress-bar" id="progress-bar">
                <div class="progress-fill" id="progress-fill"></div>
            </div>
            <button class="upload-btn" id="upload-btn">Upload Images</button>
            <div class="message" id="message"></div>
        </div>

        <div class="gallery-section">
            <h2>📁 Uploaded Images ({{ image_count }})</h2>
            {% if images %}
            <div class="image-grid">
                {% for image in images %}
                <div class="image-card">
                    <img src="/images/{{ image.name }}" alt="{{ image.name }}" class="image-thumbnail">
                    <div class="image-info">
                        <div class="image-name" title="{{ image.name }}">{{ image.name }}</div>
                        <div class="image-meta">
                            {{ "%.1f"|format(image.size / 1024) }} KB • {{ image.modified }}
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
            {% else %}
            <div class="empty-gallery">
                <div class="empty-gallery-icon">📭</div>
                <p>No images uploaded yet. Start by uploading your first image!</p>
            </div>
            {% endif %}
        </div>
    </div>

    <script>
        const uploadZone = document.getElementById("upload-zone");
        const fileInput = document.getElementById("file-input");
        const fileInfo = document.getElementById("file-info");
        const uploadBtn = document.getElementById("upload-btn");
        const progressBar = document.getElementById("progress-bar");
        const progressFill = document.getElementById("progress-fill");
        const message = document.getElementById("message");

        let selectedFiles = [];

        // Click to select files
        uploadZone.addEventListener("click", () => fileInput.click());

        // Drag and drop handlers
        uploadZone.addEventListener("dragover", (e) => {
            e.preventDefault();
            uploadZone.classList.add("drag-over");
        });

        uploadZone.addEventListener("dragleave", () => {
            uploadZone.classList.remove("drag-over");
        });

        uploadZone.addEventListener("drop", (e) => {
            e.preventDefault();
            uploadZone.classList.remove("drag-over");
            handleFiles(e.dataTransfer.files);
        });

        // File input change
        fileInput.addEventListener("change", (e) => {
            handleFiles(e.target.files);
        });

        function handleFiles(files) {
            selectedFiles = Array.from(files);
            if (selectedFiles.length === 0) return;

            let infoHTML = `<strong>${selectedFiles.length} file(s) selected:</strong><br>`;
            selectedFiles.forEach(file => {
                infoHTML += `📄 ${file.name} (${(file.size / 1024).toFixed(1)} KB)<br>`;
            });

            fileInfo.innerHTML = infoHTML;
            fileInfo.classList.add("show");
            uploadBtn.classList.add("show");
            message.classList.remove("show");
        }

        uploadBtn.addEventListener("click", async () => {
            if (selectedFiles.length === 0) return;

            uploadBtn.disabled = true;
            progressBar.classList.add("show");
            message.classList.remove("show");

            const formData = new FormData();
            selectedFiles.forEach(file => {
                formData.append("files", file);
            });

            try {
                // Simulate progress
                let progress = 0;
                const progressInterval = setInterval(() => {
                    progress += 10;
                    progressFill.style.width = Math.min(progress, 90) + "%";
                }, 100);

                const response = await fetch("/upload", {
                    method: "POST",
                    body: formData
                });

                clearInterval(progressInterval);
                progressFill.style.width = "100%";

                const result = await response.json();

                if (response.ok) {
                    showMessage("success", `✓ Successfully uploaded ${result.uploaded} image(s)!`);
                    setTimeout(() => location.reload(), 1500);
                } else {
                    showMessage("error", `✗ Error: ${result.error || "Upload failed"}`);
                }
            } catch (error) {
                showMessage("error", `✗ Error: ${error.message}`);
            } finally {
                uploadBtn.disabled = false;
                setTimeout(() => {
                    progressBar.classList.remove("show");
                    progressFill.style.width = "0%";
                }, 2000);
            }
        });

        function showMessage(type, text) {
            message.className = `message ${type} show`;
            message.textContent = text;
        }
    </script>
</body>
</html>
"""

# ==========================
# ROUTES
# ==========================

@app.route("/", methods=["GET"])
def index():
    images = get_uploaded_images()
    return render_template_string(HTML_TEMPLATE, images=images, image_count=len(images))

@app.route("/upload", methods=["POST"])
def upload():
    """Handle multiple file uploads with JSON response"""
    if "files" not in request.files:
        return jsonify({"error": "No files provided"}), 400

    files = request.files.getlist("files")
    uploaded = 0
    errors = []

    for file in files:
        if file.filename == "":
            continue

        if not allowed_file(file.filename):
            errors.append(f"{file.filename}: Invalid file type")
            continue

        try:
            filename = os.path.basename(file.filename)
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(save_path)
            uploaded += 1
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")

    if uploaded > 0:
        return jsonify({
            "uploaded": uploaded,
            "errors": errors
        }), 200
    else:
        return jsonify({
            "error": "No files uploaded",
            "details": errors
        }), 400

@app.route("/images/<filename>")
def serve_image(filename):
    """Serve uploaded images"""
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/api/images", methods=["GET"])
def api_images():
    """API endpoint to get list of images"""
    images = get_uploaded_images()
    return jsonify({"images": images, "count": len(images)})

# ==========================
# ENTRY POINT
# ==========================

if __name__ == "__main__":
    print(f"\n{'='*50}")
    print(f"🖼️  Pi Image Upload Server Starting...")
    print(f"{'='*50}")
    print(f"📁 Upload folder: {IMAGE_FOLDER}")
    print(f"🌐 Access from browser: http://<pi-ip>:{PORT}")
    print(f"{'='*50}\n")
    
    app.run(host="0.0.0.0", port=PORT, debug=False)
