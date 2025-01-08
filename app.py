from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import mimetypes

app = Flask(__name__)

# Route to fetch video details (thumbnail, title, available streams)
@app.route('/get_video_details')
def get_video_details():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        title, thumbnail_url, streams = get_video_details_from_yt_dlp(url)
        if thumbnail_url:
            return jsonify({"thumbnail_url": thumbnail_url, "title": title, "streams": streams})
        else:
            return jsonify({"error": "Unable to fetch video details"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Function to get video details using yt-dlp
def get_video_details_from_yt_dlp(url):
    try:
        with yt_dlp.YoutubeDL() as ydl:
            # Extract video information (without downloading)
            info_dict = ydl.extract_info(url, download=False)
            title = info_dict.get('title', '')
            thumbnail_url = info_dict.get('thumbnail', '')
            streams = info_dict.get('formats', [])
            # Return the title, thumbnail URL, and available streams
            return title, thumbnail_url, streams
    except Exception as e:
        raise Exception(f"Error: {str(e)}")

# Route to display the main page (index.html)
@app.route('/')
def index():
    return render_template('index.html')  # This renders index.html when you visit the root URL

# Route to handle downloading video or audio
@app.route('/download', methods=['POST'])
def download():
    url = request.json.get('url')
    quality = request.json.get('quality')
    download_type = request.json.get('download_type')

    save_path = './downloads'

    # Create the download directory if it doesn't exist
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    # Set up yt-dlp options for downloading
    ydl_opts = {
        'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),  # Set the output file template
        'format': quality,  # Select the quality format from user input
        'noplaylist': True,  # Ensure only the selected video is downloaded, not the entire playlist
        'quiet': False,  # Enable quiet to reduce verbosity in logs
    }

    # Audio download fix: Ensure audio is downloaded in the correct format
    if download_type == 'audio':
        ydl_opts['format'] = 'bestaudio/best'  # Download best audio format
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegAudioConvertor',
            'preferredcodec': 'mp3',  # Convert audio to mp3 (or change to m4a, etc.)
            'preferredquality': '192',  # Set audio quality
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)  # Download the video/audio

            # Prepare the file path to send back to the user
            filename = ydl.prepare_filename(info_dict)

            # Get file extension and determine MIME type
            file_ext = filename.split('.')[-1]
            mime_type, _ = mimetypes.guess_type(filename)

            # Use the video title as the file name and add the correct extension
            video_title = info_dict['title']
            if download_type == 'audio':
                # If it's audio, we use the mp3 extension
                download_name = f"{video_title}.mp3"
            else:
                # If it's a video, we use mp4 or appropriate extension
                download_name = f"{video_title}.mp4"

            # Send the correct file with MIME type and proper name
            return send_file(filename, as_attachment=True, download_name=download_name, mimetype=mime_type)

    except Exception as e:
        return jsonify({"error": f"Error while downloading: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
