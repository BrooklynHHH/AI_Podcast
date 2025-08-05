# coding=utf-8

"""
新版：基於火山引擎 WebSocket v3 協議的雙人播客自動生成
"""

import asyncio
import websockets
import uuid
import json
import os
import wave
from datetime import datetime
import gzip # Added for gzip compression
from pydub import AudioSegment
import numpy as np # Added for improved PCM handling
import aiofiles # Added for async file writing

# 目錄結構
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TEXT_DIR = os.path.join(BASE_DIR, "text")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
if not os.path.exists(TEXT_DIR):
    os.makedirs(TEXT_DIR)

# API參數
APP_ID = "3629151115"
TOKEN = "uGFwSN8p4R7u6MJiuDcj3Pi3zS7hM8Oy"
RESOURCE_ID = "volc.service_type.10050"
APP_KEY = "aGjiRDfUWi"
API_URL = "wss://openspeech.bytedance.com/api/v3/sami/podcasttts"

# Header常量
PROTOCOL_VERSION = 1
DEFAULT_HEADER_SIZE = 2
NO_SERIALIZATION = 1  # JSON
COMPRESSION_NO = 0
COMPRESSION_GZIP = 1

# 事件碼
EVENT_SessionStarted = 150
EVENT_SessionFinished = 152
EVENT_PodcastSpeaker = 360
EVENT_PodcastTTSResponse = 361
EVENT_PodcastTTSRoundEnd = 362
EVENT_FinishConnection = 2
EVENT_ConnectionFinished = 52

# 音頻配置
AUDIO_FORMAT = "pcm"  # 使用PCM格式，轉換為WAV
SAMPLE_RATE = 24000
SPEECH_RATE = 0

# Header類
class Header:
    def __init__(self,
                 protocol_version=PROTOCOL_VERSION,
                 header_size=DEFAULT_HEADER_SIZE,
                 message_type: int = 0,
                 message_type_specific_flags: int = 0,
                 serial_method: int = NO_SERIALIZATION,
                 compression_type: int = COMPRESSION_NO,
                 reserved_data=0):
        self.protocol_version = protocol_version
        self.header_size = header_size
        self.message_type = message_type
        self.message_type_specific_flags = message_type_specific_flags
        self.serial_method = serial_method
        self.compression_type = compression_type
        self.reserved_data = reserved_data

    def as_bytes(self) -> bytes:
        return bytes([
            (self.protocol_version << 4) | self.header_size,
            (self.message_type << 4) | self.message_type_specific_flags,
            (self.serial_method << 4) | self.compression_type,
            self.reserved_data
        ])

# 將PCM數據寫入WAV文件（參考官方示例）
async def pcm2wav(audio_data, audio_path, sr=SAMPLE_RATE):
    def write_wav_file(audio_data):
        with wave.open(audio_path, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sr)
            wav_file.writeframes(audio_data)
    await asyncio.to_thread(write_wav_file, audio_data)

# 改進的PCM到WAV轉換，支援多種數據類型（參考官方示例）
async def pcm2wav_improved(audio_data, audio_path, sr=SAMPLE_RATE, dtype=np.int16):
    def write_wav_file(audio_data):
        if dtype == np.float32:
            # 將字節數據轉換為 32 位浮點數數組
            float_samples = np.frombuffer(audio_data, dtype=np.float32)
            num_frames = len(float_samples) // 1
            # 轉換為 16 位整數 (-32768 到 32767)
            target_dtype = np.int16
            max_value = 32767
            int_samples = (float_samples * max_value).clip(-max_value, max_value).astype(target_dtype)
            audio_data = int_samples.tobytes()
        elif dtype == np.int16:
            # 直接使用int16數據
            pass
        else:
            # 其他數據類型轉換為int16
            samples = np.frombuffer(audio_data, dtype=dtype)
            int_samples = samples.astype(np.int16)
            audio_data = int_samples.tobytes()
        
        with wave.open(audio_path, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sr)
            wav_file.setnframes(len(audio_data) // 2)  # 16位 = 2字節
            wav_file.setcomptype('NONE', 'not compressed')  # 不使用壓縮
            wav_file.writeframes(audio_data)
    await asyncio.to_thread(write_wav_file, audio_data)

# 直接寫入音頻文件（支援MP3等格式）
async def write_audio_file(audio_data, audio_path):
    async with aiofiles.open(audio_path, 'wb') as f:
        await f.write(audio_data)

# 發送事件封裝，header_size=1，optional=event code
async def send_event(ws, event_code: int, payload: bytes | None = None, serial_method: int = 1, compression_type: int = 0):
    MSG_FLAG_WITH_EVENT = 0b0100  # optional 中帶 event 編號
    header = Header(
        message_type=1,
        header_size=1,
        message_type_specific_flags=MSG_FLAG_WITH_EVENT,
        serial_method=serial_method,
        compression_type=compression_type
    ).as_bytes()
    frame = bytearray(header)
    frame.extend(event_code.to_bytes(4, "big", signed=False))
    if payload is None:
        frame.extend((0).to_bytes(4, "big", signed=True))
    else:
        frame.extend(len(payload).to_bytes(4, "big", signed=True))
        frame.extend(payload)
    await ws.send(frame)

def parse_frame(res):
    msg_type  = (res[1] >> 4) & 0x0F
    flags     =  res[1] & 0x0F
    serial    = (res[2] >> 4) & 0x0F
    compress  =  res[2] & 0x0F
    offset = 4
    event = None
    session_id = None
    payload = None
    seq_number = None
    if flags == 0b0100:
        event = int.from_bytes(res[offset:offset+4], "big")
        offset += 4
        if msg_type in [9, 1] and len(res) > offset+4:
            try:
                sid_len = int.from_bytes(res[offset:offset+4], "big")
                offset += 4
                session_id = res[offset:offset+sid_len].decode("utf-8")
                offset += sid_len
            except Exception:
                pass
    if msg_type == 0b1011 and flags != 0:
        seq_number = int.from_bytes(res[offset:offset+4], "big", signed=True)
        offset += 4
    if len(res) < offset + 4:
        return msg_type, flags, event, session_id, serial, compress, b"", seq_number
    payload_size = int.from_bytes(res[offset:offset+4], "big", signed=True)
    offset += 4
    payload = res[offset:offset+max(payload_size,0)]
    return msg_type, flags, event, session_id, serial, compress, payload, seq_number

def save_text_file(all_text_content, text_filename):
    import os
    from datetime import datetime
    if not text_filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        text_filename = f"podcast_text_{timestamp}_{str(uuid.uuid4())[:8]}.txt"
    text_path = os.path.join(TEXT_DIR, text_filename)
    try:
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(all_text_content))
        print(f"[SUCCESS] 播客文本已保存: {text_path}，內容段落數: {len(all_text_content)}")
    except Exception as e:
        print(f"[ERROR] 保存文本文件失敗: {e}")
    return text_path

# 主播客生成函數
async def generate_podcast(text, output_filename=None):
    if output_filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"podcast_{timestamp}_{str(uuid.uuid4())[:8]}.wav"  # 固定使用WAV格式
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    all_rounds = []
    session_id_for_file = None
    
    # 文本收集相關變量
    all_text_content = []
    text_filename = None
    ws_header = {
        "X-Api-App-Id": APP_ID,
        "X-Api-Access-Key": TOKEN,
        "X-Api-Resource-Id": RESOURCE_ID,
        "X-Api-App-Key": APP_KEY,
        "X-Api-Request-Id": str(uuid.uuid4())
    }
    start_session_payload = {
        "input_id": str(uuid.uuid4()),
        "input_text": text,
        "scene": "deep_research",
        "action": 0,
        "use_head_music": False,
        "audio_config": {
            "format": AUDIO_FORMAT,
            "sample_rate": SAMPLE_RATE,
            "speech_rate": SPEECH_RATE
        }
    }
    payload_sess = json.dumps(start_session_payload).encode("utf-8")
    print(f"[INFO] 連接API...")
    session_id = None
    try:
        async with websockets.connect(API_URL, additional_headers=ws_header, ping_interval=None) as ws:
            payload_conn = json.dumps({
                "app_id": APP_ID,
                "access_key": TOKEN,
                "resource_id": RESOURCE_ID,
                "app_key": APP_KEY
            }).encode("utf-8")
            await send_event(ws, 1, payload_conn, serial_method=1, compression_type=0)
            while True:
                res = await ws.recv()
                header_bytes = res[:4]
                optional_event = int.from_bytes(res[4:8], "big")
                payload_size = int.from_bytes(res[8:12], "big", signed=True)
                payload = res[12:12+max(payload_size,0)]
                if optional_event == 50:
                    print("[INFO] ConnectionStarted (50) 收到")
                    break
                elif optional_event == 0xf:
                    print("[ERROR] 連接失敗，服務返回錯誤")
                    return None
            session_id = uuid.uuid4().hex
            start_session_payload = {
                "input_id": session_id,
                "input_text": text,
                "scene": "deep_research",
                "action": 0,
                "use_head_music": False,
                "audio_config": {
                    "format": AUDIO_FORMAT,
                    "sample_rate": SAMPLE_RATE,
                    "speech_rate": SPEECH_RATE
                }
            }
            payload_gzip = gzip.compress(json.dumps(start_session_payload).encode("utf-8"))
            session_id_bytes = session_id.encode("utf-8")
            header_ss = Header(
                message_type=1,
                header_size=1,
                message_type_specific_flags=0b0100,
                serial_method=1,
                compression_type=1
            ).as_bytes()
            frame_ss = bytearray(header_ss)
            frame_ss.extend((100).to_bytes(4, 'big'))
            frame_ss.extend(len(session_id_bytes).to_bytes(4, 'big'))
            frame_ss.extend(session_id_bytes)
            frame_ss.extend(len(payload_gzip).to_bytes(4, 'big', signed=True))
            frame_ss.extend(payload_gzip)
            await ws.send(frame_ss)
            print("[INFO] StartSession 已發送，等待播客數據...")
            round_audio = []
            current_round_id = None
            current_speaker = None
            idx = 0
            session_id_for_file = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(uuid.uuid4())[:8]
            last_audio_time = asyncio.get_event_loop().time()
            timeout_seconds = 10
            while True:
                try:
                    res = await asyncio.wait_for(ws.recv(), timeout=timeout_seconds)
                except asyncio.TimeoutError:
                    print(f"[TIMEOUT] {timeout_seconds}秒內無新數據，觸發超時合併...")
                    break
                except Exception as e:
                    print(f"[ERROR] 接收數據時出錯: {e}")
                    break
                msg_type, flags, event, session_id, serial, compress, payload, seq_num = parse_frame(res)
                if event == 360:
                    try:
                        payload_dec = gzip.decompress(payload) if compress == 1 else payload
                        resp = json.loads(payload_dec.decode('utf-8'))
                        current_round_id = resp.get('round_id')
                        current_speaker = resp.get('speaker')
                        text_content = resp.get('text', '')
                        if current_round_id == -1 and not current_speaker:
                            current_speaker = "head_music"
                            print("[EVENT] 360 開頭音樂開始")
                        else:
                            print(f"[EVENT] 360 新輪次: round_id={current_round_id}, speaker={current_speaker}")
                            if text_content:
                                print(f"[TEXT] 對話內容: {text_content[:100]}...")
                                all_text_content.append(f"[{current_speaker}]: {text_content}")
                                print(f"[DEBUG] 當前文本收集數量: {len(all_text_content)}")
                                if text_filename is None:
                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    text_filename = f"podcast_text_{timestamp}_{str(uuid.uuid4())[:8]}.txt"
                    except Exception as e:
                        print(f"[ERROR] 解析360失敗: {e}")
                        current_round_id = None
                        current_speaker = None
                    round_audio = []
                elif msg_type == 0b1011:
                    if flags != 0 and payload:
                        round_audio.append(payload)
                        last_audio_time = asyncio.get_event_loop().time()
                        print(f"[AUDIO] 片段 seq={seq_num}, bytes={len(payload)}, round_total={sum(len(x) for x in round_audio)}")
                    elif flags == 0:
                        print(f"[ACK] 音頻確認幀 seq={seq_num}")
                elif event == 361:
                    try:
                        payload_dec = gzip.decompress(payload) if compress == 1 else payload
                        resp = json.loads(payload_dec.decode('utf-8'))
                        print(f"[EVENT] 361 音頻響應: {resp}")
                    except Exception as e:
                        print(f"[DEBUG] 事件361 payload無法解析: {payload[:32]}, error: {e}")
                elif event == 362:
                    print(f"[EVENT] 362 輪次結束: round_id={current_round_id}, speaker={current_speaker}")
                    print(f"[AUDIO] 累積音頻: {len(round_audio)}片段, {sum(len(x) for x in round_audio)} bytes")
                    if current_round_id is not None and current_speaker is not None and round_audio:
                        if current_round_id == -1:
                            filename = os.path.join(OUTPUT_DIR, f"round_{session_id_for_file}_{idx}_head_music.wav")
                        else:
                            filename = os.path.join(OUTPUT_DIR, f"round_{session_id_for_file}_{idx}_{current_round_id}_{current_speaker}.wav")
                        # 將PCM數據轉換為WAV格式
                        try:
                            await pcm2wav_improved(b''.join(round_audio), filename, sr=SAMPLE_RATE, dtype=np.int16)
                            all_rounds.append(filename)
                            print(f"[INFO] 保存輪次音頻: {filename}，總長度: {sum(len(x) for x in round_audio)}")
                            if os.path.exists(filename):
                                print(f"[DEBUG] 文件已寫入: {filename}，文件大小: {os.path.getsize(filename)} bytes")
                            else:
                                print(f"[ERROR] 文件寫入失敗: {filename}")
                            idx += 1
                        except Exception as e:
                            print(f"[ERROR] 轉換音頻時出錯: {e}")
                            continue
                    else:
                        print(f"[WARN] 362時 round_audio為空或 round_id/speaker缺失，current_round_id={current_round_id}, current_speaker={current_speaker}, round_audio_len={len(round_audio)}")
                    round_audio = []
                elif event == 152:
                    print(f"[EVENT] 152 會話結束，開始合併所有輪次音頻...")
                    
                    # 保存文本文件
                    save_text_file(all_text_content, text_filename)
                    
                    for fname in all_rounds:
                        if not os.path.exists(fname) or os.path.getsize(fname) < 1000:
                            print(f"[ERROR] 分段文件異常: {fname}，文件大小: {os.path.getsize(fname) if os.path.exists(fname) else '不存在'}")
                    # 使用pydub合併WAV文件
                    combined = AudioSegment.empty()
                    for fname in all_rounds:
                        if os.path.exists(fname):
                            combined += AudioSegment.from_wav(fname)
                    if len(combined) > 0:
                        combined.export(output_path, format="wav")
                    else:
                        print("[ERROR] 無可用分段可合併")
                    print(f"[SUCCESS] 播客音頻已保存: {output_path}")
                    break
                elif event == 52:
                    print("[EVENT] 52 ConnectionFinished，伺服端關閉連線，嘗試合併目前所有輪次...")
                    break
                elif event is not None:
                    try:
                        payload_dec = gzip.decompress(payload) if compress == 1 else payload
                        resp = json.loads(payload_dec.decode('utf-8'))
                        print(f"[EVENT] {event} 收到: {resp}")
                    except Exception as e:
                        print(f"[DEBUG] 事件{event} payload無法解析: {payload[:32]}, error: {e}")
                current_time = asyncio.get_event_loop().time()
                if (current_time - last_audio_time > 5 and all_rounds and not os.path.exists(output_path)):
                    print(f"[AUTO-MERGE] 5秒無新音頻，自動觸發合併，共{len(all_rounds)}段")
                    break
            return output_path
    except websockets.exceptions.ConnectionClosedOK:
        print("[INFO] WebSocket 已正常關閉")
    except Exception as e:
        print(f"[ERROR] 連接或處理過程出錯: {e}")
    finally:
        print(f"[DEBUG] finally: all_text_content長度={len(all_text_content)}, text_filename={text_filename}")
        save_text_file(all_text_content, text_filename)
        try:
            # 備援保存文本文件
            if all_rounds and (not os.path.exists(output_path)):
                print("[FALLBACK] 觸發備援合併，共", len(all_rounds), "段")
                for fname in all_rounds:
                    if not os.path.exists(fname):
                        print("[WARN] 缺少分段文件", fname)
                # 使用pydub合併WAV文件
                combined = AudioSegment.empty()
                for fname in all_rounds:
                    if os.path.exists(fname):
                        combined += AudioSegment.from_wav(fname)
                if len(combined) > 0:
                    combined.export(output_path, format="wav")
                    print(f"[SUCCESS] 備援合併完成: {output_path}")
                else:
                    print("[ERROR] 無可用分段可合併")
        except Exception as e_merge:
            print("[ERROR] 備援合併失敗:", e_merge)
    return None

# 導出generate_podcast_from_string作為雙人播客主入口，返回文件名
async def generate_podcast_from_string(text, output_filename=None):
    result = await generate_podcast(text, output_filename)
    if result is None:
        return None
    return os.path.basename(result)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        text = sys.argv[1]
        asyncio.run(generate_podcast(text))
    else:
        print("請提供播客主題文本作為參數") 