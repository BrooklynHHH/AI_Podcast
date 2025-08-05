# coding=utf-8

'''
需要Python 3.6或更新版本

安装依賴:
pip install asyncio
pip install websockets
pip install pydub
pip install pyyaml

注意: 如果要合併音頻，需要安裝 ffmpeg 用於音頻處理
brew install ffmpeg
'''

import asyncio
import websockets
import uuid
import json
import gzip
import copy
import os
import yaml
from datetime import datetime
from pydub import AudioSegment

# 目錄結構
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "temp")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
CONFIG_DIR = os.path.join(BASE_DIR, "config")

# 確保目錄存在
for directory in [TEMP_DIR, OUTPUT_DIR, CONFIG_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# 生成唯一的輸出文件名
def generate_unique_filename(base_name="podcast"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]  # 使用UUID的前8位作為唯一標識
    return f"{base_name}_{timestamp}_{unique_id}.mp3"

# 加載配置文件
def load_config():
    config_path = os.path.join(CONFIG_DIR, "double_config.yaml")
    if not os.path.exists(config_path):
        # 創建默認配置
        default_config = {
                    "appid": "YOUR_APP_ID",
        "token": "YOUR_TOKEN",
            "cluster": "volcano_tts",
            "voice_types": {
                "male": "zh_male_wennuanahu_moon_bigtts",
                "female": "zh_female_tianmeitaozi_mars_bigtts"
            },
            "host": "openspeech.bytedance.com"
        }
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(default_config, f, allow_unicode=True)
        return default_config
    
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# 加載配置
config = load_config()
appid = config["appid"]
token = config["token"]
cluster = config["cluster"]
male_voice_type = config["voice_types"]["male"]
female_voice_type = config["voice_types"]["female"]
host = config["host"]
api_url = f"wss://{host}/api/v1/tts/ws_binary"

# 二進制協議頭部
default_header = bytearray(b'\x11\x10\x11\x00')

# 請求模板
request_json = {
    "app": {
        "appid": appid,
        "token": token,
        "cluster": cluster
    },
    "user": {
        "uid": "388808087185088"
    },
    "audio": {
        "voice_type": "",  # 將在具體請求中設置
        "encoding": "mp3",
        "speed_ratio": 1.0,
        "volume_ratio": 1.0,
        "pitch_ratio": 1.0,
    },
    "request": {
        "reqid": "",  # 將在具體請求中設置
        "text": "",  # 將在具體請求中設置
        "text_type": "plain",
        "operation": "submit"
    }
}

# 解析二進製響應
def parse_response(res, file):
    # 提取協議頭部信息
    protocol_version = res[0] >> 4
    header_size = res[0] & 0x0f
    message_type = res[1] >> 4
    message_type_specific_flags = res[1] & 0x0f
    serialization_method = res[2] >> 4
    message_compression = res[2] & 0x0f
    payload = res[header_size*4:]
    
    if message_type == 0xb:  # audio-only server response
        if message_type_specific_flags == 0:  # no sequence number as ACK
            return False
        else:
            sequence_number = int.from_bytes(payload[:4], "big", signed=True)
            payload_size = int.from_bytes(payload[4:8], "big", signed=False)
            payload = payload[8:]
            file.write(payload)
            if sequence_number < 0:
                return True
            else:
                return False
    elif message_type == 0xf:  # 錯誤消息
        code = int.from_bytes(payload[:4], "big", signed=False)
        msg_size = int.from_bytes(payload[4:8], "big", signed=False)
        error_msg = payload[8:]
        if message_compression == 1:
            error_msg = gzip.decompress(error_msg)
        error_msg = str(error_msg, "utf-8")
        print(f"錯誤碼: {code}")
        print(f"錯誤信息: {error_msg}")
        return True
    else:
        return True

# 生成音頻的核心函數
async def generate_audio(text, voice_type, output_file):
    submit_request_json = copy.deepcopy(request_json)
    submit_request_json["audio"]["voice_type"] = voice_type
    submit_request_json["request"]["reqid"] = str(uuid.uuid4())
    submit_request_json["request"]["text"] = text
    
    # 壓縮請求負載
    payload_bytes = str.encode(json.dumps(submit_request_json))
    payload_bytes = gzip.compress(payload_bytes)
    
    # 構造完整請求
    full_client_request = bytearray(default_header)
    full_client_request.extend((len(payload_bytes)).to_bytes(4, 'big'))  # payload size(4 bytes)
    full_client_request.extend(payload_bytes)  # payload
    
    print(f"正在生成音頻: {text}")
    
    # 打開文件準備寫入
    file_to_save = open(output_file, "wb")
    
    # 建立WebSocket連接並發送請求
    header = {"Authorization": f"Bearer; {token}"}
    try:
        # 修改 WebSocket 連接方式
        ws = await websockets.connect(api_url, extra_headers=header, ping_interval=None)
        await ws.send(full_client_request)
        while True:
            res = await ws.recv()
            done = parse_response(res, file_to_save)
            if done:
                file_to_save.close()
                await ws.close()
                break
        print(f"音頻生成完成: {output_file}")
        return True
    except Exception as e:
        print(f"生成音頻時出錯: {e}")
        file_to_save.close()
        return False

def is_valid_mp3(file_path):
    try:
        audio = AudioSegment.from_mp3(file_path)
        return len(audio) > 0
    except Exception as e:
        print(f"警告: {file_path} 不是有效的mp3文件，將跳過。錯誤信息: {e}")
        return False

def combine_audio_files(file_list, output_file, gap_ms=500):
    combined = AudioSegment.empty()
    gap = AudioSegment.silent(duration=gap_ms)
    for file in file_list:
        if os.path.exists(file) and is_valid_mp3(file):
            audio = AudioSegment.from_mp3(file)
            combined += audio
            combined += gap
        else:
            print(f"跳過無效或不存在的文件: {file}")
    if len(combined) > 0:
        combined.export(output_file, format="mp3")
        print(f"播客音頻已生成：{output_file}")
    else:
        print("沒有有效的音頻片段可合併，未生成播客文件。")

# 修改生成對話的主函數
async def generate_dialogue_no_merge(dialogue, session_id=None):
    if session_id is None:
        session_id = str(uuid.uuid4())[:8]
    
    # 為本次會話創建臨時目錄
    session_dir = os.path.join(TEMP_DIR, f"session_{session_id}")
    if not os.path.exists(session_dir):
        os.makedirs(session_dir)
    
    generated_files = []
    
    # 為每段對話生成音頻
    for idx, item in enumerate(dialogue):
        role = "female" if item["role"] == "female" else "male"
        output_file = os.path.join(session_dir, f"{idx+1}_{role}.mp3")
        voice_type = female_voice_type if item["role"] == "female" else male_voice_type
        
        success = await generate_audio(item["text"], voice_type, output_file)
        if success:
            generated_files.append(output_file)
    
    print(f"\n成功生成 {len(generated_files)} 個音頻文件在 {session_dir} 目錄下:")
    for file in generated_files:
        print(f" - {file}")
    
    return len(generated_files) > 0, session_dir

# 修改主流程函數，使其可以接收外部輸入
async def generate_podcast_from_string(dialogue_str, output_filename=None):
    # 生成會話ID
    session_id = str(uuid.uuid4())[:8]
    
    # 創建本次會話的臨時目錄
    session_dir = os.path.join(TEMP_DIR, f"session_{session_id}")
    if not os.path.exists(session_dir):
        os.makedirs(session_dir)
    
    # 生成唯一的輸出文件名
    if output_filename is None:
        output_filename = generate_unique_filename()
    
    output_file = os.path.join(OUTPUT_DIR, output_filename)
    
    lines = [line.strip() for line in dialogue_str.strip().split('\n') if line.strip()]
    temp_files = []
    
    for idx, line in enumerate(lines):
        voice_type = male_voice_type if idx % 2 == 0 else female_voice_type
        temp_file = os.path.join(session_dir, f"temp_line_{idx+1}.mp3")
        print(f"生成第{idx+1}段音頻: {line} ({'男' if voice_type==male_voice_type else '女'})")
        success = await generate_audio(line, voice_type, temp_file)
        if success and os.path.exists(temp_file):
            temp_files.append(temp_file)
        else:
            print(f"第{idx+1}段音頻生成失敗，將跳過。內容: {line}")
    
    print("合併所有音頻段...")
    combine_audio_files(temp_files, output_file)
    
    # 清理臨時文件
    for file in temp_files:
        if os.path.exists(file):
            os.remove(file)
    
    # 刪除臨時目錄
    try:
        os.rmdir(session_dir)
    except OSError:
        print(f"警告：無法刪除臨時目錄 {session_dir}")
    
    return output_file

# 如果直接運行此腳本
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # 從命令行參數讀取文本
        dialogue_str = sys.argv[1]
        output_file = asyncio.run(generate_podcast_from_string(dialogue_str))
        print(f"\n最終播客文件已生成：{output_file}")
    else:
        print("請提供播客文本作為參數") 