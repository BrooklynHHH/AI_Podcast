import asyncio
import websockets
import uuid
import json
import gzip
import copy
import os
import yaml
from datetime import datetime

# 目錄結構
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEXT_DIR = os.path.join(BASE_DIR, "text")
CONFIG_DIR = os.path.join(BASE_DIR, "config")

# 確保目錄存在
for directory in [OUTPUT_DIR, TEXT_DIR, CONFIG_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# 生成唯一的輸出文件名
def generate_unique_filename(base_name="podcast"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"{base_name}_{timestamp}_{unique_id}.mp3"

# 加載配置文件
def load_config():
    config_path = os.path.join(CONFIG_DIR, "single_config.yaml")
    if not os.path.exists(config_path):
        default_config = {
            "appid": "3629151115",
            "token": "uGFwSN8p4R7u6MJiuDcj3Pi3zS7hM8Oy",
            "cluster": "volcano_tts",
            "voice_types": {
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
voice_type = config["voice_types"]["female"]
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
        "voice_type": "",
        "encoding": "mp3",
        "speed_ratio": 1.0,
        "volume_ratio": 1.0,
        "pitch_ratio": 1.0,
    },
    "request": {
        "reqid": "",
        "text": "",
        "text_type": "plain",
        "operation": "submit"
    }
}

# 解析二進製響應
def parse_response(res, file):
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
async def generate_audio(text, output_file):
    submit_request_json = copy.deepcopy(request_json)
    submit_request_json["audio"]["voice_type"] = voice_type
    submit_request_json["request"]["reqid"] = str(uuid.uuid4())
    submit_request_json["request"]["text"] = text
    
    # 壓縮請求負載
    payload_bytes = str.encode(json.dumps(submit_request_json))
    payload_bytes = gzip.compress(payload_bytes)
    
    # 構造完整請求
    full_client_request = bytearray(default_header)
    full_client_request.extend((len(payload_bytes)).to_bytes(4, 'big'))
    full_client_request.extend(payload_bytes)
    
    print(f"正在生成音頻: {text}")
    
    # 打開文件準備寫入
    file_to_save = open(output_file, "wb")
    
    # 建立WebSocket連接並發送請求
    header = {"Authorization": f"Bearer; {token}"}
    try:
        ws = await websockets.connect(api_url, additional_headers=header, ping_interval=None)
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

# 主流程函數
async def generate_single_podcast(text, output_filename=None):
    if output_filename is None:
        output_filename = generate_unique_filename()
    
    output_file = os.path.join(OUTPUT_DIR, output_filename)
    
    # 保存文本文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    text_filename = f"single_podcast_text_{timestamp}_{str(uuid.uuid4())[:8]}.txt"
    text_file = os.path.join(TEXT_DIR, text_filename)
    
    try:
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"播客文本已保存：{text_file}")
    except Exception as e:
        print(f"保存文本文件失敗: {e}")
    
    # 直接生成整個文本的音頻
    success = await generate_audio(text, output_file)
    
    if success:
        print(f"播客音頻已生成：{output_file}")
        return output_filename  # 返回文件名而不是完整路徑
    else:
        print("音頻生成失敗")
        return None

# 如果直接運行此腳本
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        text = sys.argv[1]
        output_file = asyncio.run(generate_single_podcast(text))
        if output_file:
            print(f"\n最終播客文件已生成：{output_file}")
    else:
        print("請提供播客文本作為參數") 