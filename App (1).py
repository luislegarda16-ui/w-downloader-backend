
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import os, uuid

app = Flask(__name__)
CORS(app)  # permite que tu web de Cloudflare llame a este backend

@app.route('/')
def home():
    return "W Downloader Backend OK - Usa /download?url=LINK&format=mp3"

@app.route('/download')
def download():
    url = request.args.get('url')
    fmt = request.args.get('format','mp3')  # mp3 o mp4
    quality = request.args.get('quality','mp3-320')
    
    if not url:
        return jsonify({"error":"Falta url"}), 400

    tmp_id = str(uuid.uuid4())[:8]
    
    if 'mp3' in fmt:
        # Descarga solo audio y convierte a mp3
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'/tmp/{tmp_id}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320' if '320' in quality else '192',
            }],
            'quiet': True,
        }
    else:
        # Descarga video
        q = '1080' if '1080' in quality else '720'
        ydl_opts = {
            'format': f'bestvideo[height<={q}]+bestaudio/best[height<={q}]',
            'outtmpl': f'/tmp/{tmp_id}.%(ext)s',
            'merge_output_format': 'mp4',
            'quiet': True,
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # buscar archivo generado
            filename = ydl.prepare_filename(info)
            # si es mp3, yt-dlp cambia extension
            if 'mp3' in fmt:
                filename = os.path.splitext(filename)[0] + '.mp3'
            
            if os.path.exists(filename):
                return send_file(filename, as_attachment=True, download_name=f"W-Downloader-{tmp_id}.{ 'mp3' if 'mp3' in fmt else 'mp4'}")
            else:
                # buscar cualquier archivo con tmp_id
                for f in os.listdir('/tmp'):
                    if tmp_id in f:
                        return send_file(f'/tmp/{f}', as_attachment=True)
                return jsonify({"error":"No se pudo generar archivo"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
