from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import asyncio
from podcast_generator import generate_podcast_from_string
from single_podcast_generator import generate_single_podcast
import os
import logging

# 配置日誌
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# 定義播客音頻的輸出目錄
PODCAST_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
logger.info(f"[Flask Server] 音頻輸出目錄: {PODCAST_OUTPUT_DIR}")

# 確保輸出目錄存在
os.makedirs(PODCAST_OUTPUT_DIR, exist_ok=True)

@app.route('/generate-podcast', methods=['POST'])
def generate_podcast():
    try:
        data = request.get_json()
        text = data.get('text')
        podcast_type = data.get('type', 'single')  # 預設為 single
        
        logger.info(f"[Flask Server] 接收到請求: text='{text[:50]}...', type='{podcast_type}'")
        
        if not text:
            return jsonify({'error': '請提供播客文本'}), 400
        
        # 根據類型選擇不同的生成器
        if podcast_type == 'single':
            logger.info("[Flask Server] 選擇單人播客生成器")
            audio_file = asyncio.run(generate_single_podcast(text))
        else:
            logger.info("[Flask Server] 選擇雙人播客生成器")
            audio_file = asyncio.run(generate_podcast_from_string(text))
        
        audio_path = os.path.join(PODCAST_OUTPUT_DIR, audio_file)
        
        if os.path.exists(audio_path):
            logger.info(f"[Flask Server] 生成成功，文件名: {audio_file}")
            return jsonify({
                'success': True,
                'audio_file': audio_file,
                'podcast_type': podcast_type
            })
        else:
            logger.error(f"[Flask Server] 錯誤: 音頻文件未找到: {audio_file}")
            return jsonify({
                'success': False,
                'error': f'音頻文件未找到: {audio_file}'
            }), 500
    except Exception as e:
        logger.error(f"[Flask Server] 錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 修正音頻文件的路由
@app.route('/audio/<path:filename>')
def serve_audio(filename):
    logger.info(f"[Flask Server] 嘗試提供音頻文件: {filename}")
    try:
        # 從完整路徑中提取文件名
        filename = os.path.basename(filename)
        logger.info(f"[Flask Server] 從目錄 {PODCAST_OUTPUT_DIR} 提供文件 {filename}")
        return send_from_directory(PODCAST_OUTPUT_DIR, filename, mimetype='audio/mpeg')
    except Exception as e:
        logger.error(f"[Flask Server] 提供音頻文件時出錯: {str(e)}")
        return jsonify({'error': '文件不存在'}), 404

if __name__ == '__main__':
    app.run(port=5001, debug=True)  # 添加 debug=True 以便查看詳細錯誤信息 