#!/bin/bash
set -e

echo "--- 🚀 Cloud Instance Startup ---"

# 1. モデル保存用ディレクトリの作成
MODEL_DIR="/workspace/model/Qwen2.5-VL-7B-Instruct"
mkdir -p $MODEL_DIR

# 2. Azure Blobからモデルをダウンロード (SASトークンを使用)
# ※AZURE_SAS_URL は Vast.ai 起動時の環境変数として渡します
if [ -z "$AZURE_SAS_URL" ]; then
    echo "❌ Error: AZURE_SAS_URL is not set."
    exit 1
fi

echo "📦 Downloading model from Azure..."
# モデルが巨大なため、高速なcurlを使用（.tar.gzなどのアーカイブ形式を推奨）
curl -L "$AZURE_SAS_URL" -o /workspace/model.tar.gz
tar -xzvf /workspace/model.tar.gz -C $MODEL_DIR --strip-components=1
rm /workspace/model.tar.gz

echo "✅ Model ready. Starting Tagger Script..."

# 3. Pythonスクリプトの実行
python3 /app/tagger_script.py