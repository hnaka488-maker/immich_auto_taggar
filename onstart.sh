#!/bin/bash
# 1. ワークスペースのパスを特定 (vllm-workspace か workspace)
W_DIR=$(ls -d /vllm-workspace /workspace 2>/dev/null | head -n 1)
MODEL_PATH="$W_DIR/model/Qwen2.5-VL-7B-Instruct"

# 2. 必要なツールの準備
apt-get update && apt-get install -y wget nano

# 3. 最新スクリプト取得 (GitHubから)
wget -O /app/tagger_script.py https://raw.githubusercontent.com/hnaka488-maker/immich_auto_taggar/refs/heads/main/tagger_script.py

# 4. モデルのダウンロード完了を待機 (config.json の存在を確認)
echo "Waiting for model in $MODEL_PATH..."
until [ -f "$MODEL_PATH/config.json" ]; do
    sleep 30
    echo "Still waiting for model files..."
done

# 5. エンジン起動 (特定したパスを使用)
python3 -m vllm.entrypoints.openai.api_server --model "$MODEL_PATH" --trust-remote-code --max-model-len 4096 --gpu-memory-utilization 0.9 > /app/engine.log 2>&1 &

# 6. 待機して実行
sleep 120
python3 /app/tagger_script.py
