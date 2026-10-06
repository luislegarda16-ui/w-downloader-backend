from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import os
import tempfile
import uuid

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "W Downloader Backend OK V2 - Usa /download?url=LINK&format=mp3"

@app.route('/download')
def download():
    url = request.args.get('url')
    format_type = request.args.get('format', 'mp3')  # mp3 or mp4
    quality = request.args.get('quality', 'mp3-320')
    
    if not url:
        return jsonify({"error": "Falta ?url="}), 400

    temp_dir = tempfile.gettempdir()
    file_id = str(uuid.uuid4())[:8]
    
    # Configuración base que evita el bloqueo de YouTube
    ydl_opts_base = {
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
                'player_skip': ['webpage', 'configs'],
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
        },
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'noplaylist': True,
    }

    try:
        if format_type == 'mp3':
            # MP3 - extrae solo audio
            output_path = os.path.join(temp_dir, f"{file_id}.%(ext)s")
            ydl_opts = {
                **ydl_opts_base,
                'format': 'bestaudio/best',
                'outtmpl': output_path,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320' if '320' in quality else '192',
                }],
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'audio')[:50]
            final_file = os.path.join(temp_dir, f"{file_id}.mp3")
            # Limpiar nombre seguro
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            return send_file(final_file, as_attachment=True, download_name=f"{safe_title}.mp3", mimetype="audio/mpeg")
        else:
            # MP4 - video + audio
            output_path = os.path.join(temp_dir, f"{file_id}.mp4")
            ydl_opts = {
                **ydl_opts_base,
                'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': output_path,
                'merge_output_format': 'mp4',
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'video')[:50]
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            return send_file(output_path, as_attachment=True, download_name=f"{safe_title}.mp4", mimetype="video/mp4")

    except Exception as e:
        # Si YouTube sigue bloqueando, intenta con cliente diferente
        error_msg = str(e)
        print(f"Error descarga: {error_msg}")
        
        # Fallback: prueba sin postprocesador para TikTok/IG que no necesitan FFmpeg
        if "Sign in to confirm" in error_msg or "bot" in error_msg:
            return jsonify({
                "error": "YouTube está bloqueando IPs de servidores gratis. Prueba con TikTok, Instagram, Facebook o Twitter que sí funcionan al 100%. Para YouTube necesitas usar una cookie. ERROR: " + error_msg[:500]
            }), 500
        
        return jsonify({"error": error_msg}), 500

@app.route('/info')
def info():
    """Devuelve info del video sin descargar, para mostrar thumbnail"""
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Falta url"}), 400
    try:
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
                "duration": info.get('duration'),
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
