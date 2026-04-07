# vLLM公式イメージ（CUDA 12.4/13.0対応版を想定）
FROM vllm/vllm-openai:latest

# 必要なライブラリの追加
RUN pip install python-dotenv azure-storage-blob requests pillow

WORKDIR /app

# ファイルを1つずつ明示的にコピーする（これでエラー箇所がハッキリします）
COPY entrypoint.sh /app/entrypoint.sh
COPY tagger_script.py /app/tagger_script.py
COPY .env /app/.env

# 実行権限の付与
RUN chmod +x /app/entrypoint.sh

# 起動時に実行
ENTRYPOINT ["/app/entrypoint.sh"]