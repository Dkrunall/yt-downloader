from flask import Flask, request, jsonify, send_file, Response
import yt_dlp as ytdl
import os

app = Flask(__name__)

# Path to the cookies file
COOKIES_FILE = "cookies.txt"

# Ensure cookies.txt is available
if not os.path.exists(COOKIES_FILE):
    raise FileNotFoundError("The cookies.txt file is missing. Please export it from your browser.")

# Route to fetch video details
@app.route('/get_video_details', methods=['GET'])
def get_video_details():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        ydl_opts = {
            'cookiefile': COOKIES_FILE
        }
        with ytdl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                "title": info.get("title"),
                "thumbnail_url": info.get("thumbnail"),
                "duration": info.get("duration"),
                "uploader": info.get("uploader"),
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to download video or audio
@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    quality = data.get('quality', 'best')
    download_type = data.get('download_type', 'video')

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    # Output filename
    output_file = "downloads/%(title)s.%(ext)s"
    ydl_opts = {
        'format': 'bestaudio/best' if download_type == 'audio' else quality,
        'outtmpl': output_file,
        'noplaylist': True,
        'cookiefile': COOKIES_FILE,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if download_type == 'audio' else [],
    }

    try:
        with ytdl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            if download_type == 'audio':
                filename = filename.replace(".webm", ".mp3").replace(".m4a", ".mp3")

            return send_file(
                filename,
                as_attachment=True,
                download_name=os.path.basename(filename),
                mimetype="application/octet-stream"
            )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Basic health check route
@app.route('/')
def home():
    return jsonify({"message": "YouTube Downloader API is running!"})

# Ensure downloads directory exists
if __name__ == "__main__":
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    app.run(debug=True)
