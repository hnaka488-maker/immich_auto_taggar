#!/bin/bash
# 1. ツールのインストール
apt-get update && apt-get install -y wget nano

# 2. GitHubから最新スクリプトをダウンロード
wget -O /app/tagger_script.py https://raw.githubusercontent.com/hnaka488-maker/immich_auto_taggar/refs/heads/main/tagger_script.py

# 3. AIエンジン (vLLM) をバックグラウンドで起動
python3 -m vllm.entrypoints.openai.api_server --model /workspace/model/Qwen2.5-VL-7B-Instruct --trust-remote-code --max-model-len 4096 --gpu-memory-utilization 0.9 > /app/engine.log 2>&1 &

# 4. 起動を待ってから解析実行
sleep 120
python3 /app/tagger_script.py