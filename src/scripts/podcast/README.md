# 播客生成器

這個目錄包含了播客生成器的 Python 腳本和相關配置。

## 安裝依賴

```bash
pip install -r requirements.txt
```

## 注意事項

1. 需要安裝 ffmpeg 用於音頻處理：
   ```bash
   brew install ffmpeg
   ```

2. 配置文件位於 `config/config.yaml`，請確保已正確設置：
   - appid
   - token
   - cluster
   - voice_types
   - host

## 使用方法

1. 確保所有依賴已安裝
2. 檢查配置文件是否正確
3. 運行 Python 腳本：
   ```bash
   python podcast_generator.py
   ``` 