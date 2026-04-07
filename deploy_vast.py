import os
import subprocess
import sys
from dotenv import load_dotenv

# .env ファイルから環境変数を読み込む
load_dotenv()

def get_env_or_error(key):
    value = os.getenv(key)
    if not value:
        raise ValueError(f"❌ .env ファイルに {key} が設定されていません。")
    return value

def deploy():
    # 1. vastai.exe の絶対パス
    vastai_exe = r"C:\Users\n-tra\AppData\Local\Python\pythoncore-3.14-64\Scripts\vastai.exe"
    
    # 2. 起動時に実行するスクリプトの内容 (onstart.sh)
    # 改行コードを Linux 形式 (\n) に固定し、文字コードエラーを防ぐために ASCII 範囲内で記述します
    tagger_url = "https://raw.githubusercontent.com/hnaka488-maker/immich_auto_taggar/refs/heads/main/tagger_script.py"
    
    onstart_content = f"""#!/bin/bash
# 1. ワークスペースのパスを特定 (vllm-workspace か workspace)
W_DIR=$(ls -d /vllm-workspace /workspace 2>/dev/null | head -n 1)
MODEL_PATH="$W_DIR/model/Qwen2.5-VL-7B-Instruct"

# 2. 必要なツールの準備
apt-get update && apt-get install -y wget nano

# 3. 最新スクリプト取得 (GitHubから)
wget -O /app/tagger_script.py {tagger_url}

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
"""

    # onstart.sh を UTF-8 (BOMなし) で保存
    with open("onstart.sh", "w", encoding="utf-8", newline='\n') as f:
        f.write(onstart_content)

    try:
        model_url = get_env_or_error("MODEL_URL")
        docker_image = get_env_or_error("DOCKER_IMAGE")
        immich_url = get_env_or_error("IMMICH_URL")
        immich_api_key = get_env_or_error("IMMICH_API_KEY")

        print("🔍 最安の RTX 4090 / A6000 (Verified) を探しています...")
        search_cmd = f'{vastai_exe} search offers "gpu_name=RTX_4090 num_gpus=1 verified=true" -o "price_per_gpu"'
        
        offers_output = subprocess.check_output(search_cmd, shell=True).decode('utf-8').strip()
        lines = [line for line in offers_output.split('\n') if line.strip()]
        
        if len(lines) < 2:
            print("❌ 条件に合う GPU が見つかりませんでした。")
            return

        first_offer = lines[1].split()[0]
        print(f"✅ 最安の Offer ID {first_offer} を確保しました。")

        # 🚀 インスタンス作成
        # --onstart にはファイル名 "onstart.sh" を指定します
        # --- deploy_vast.py の launch_cmd 部分 ---
        env_vars = f'AZURE_SAS_URL={model_url} IMMICH_URL={immich_url} IMMICH_API_KEY={immich_api_key}'

        launch_cmd = (
            f'{vastai_exe} create instance {first_offer} '
            f'--image {docker_image} '
            f'--env "{env_vars}" '  # クォートをシンプルに
            f'--onstart onstart.sh '
            f'--disk 60'
        )
        
        print("🚀 Vast.ai にデプロイ命令を送信中...")
        # Windowsのcp932エラーを避けるため、出力を無視するか適切に処理します
        result = subprocess.run(launch_cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            print("-" * 50)
            print("✨ デプロイ命令の送信が完了しました！")
            print("Vast.ai コンソールで 'Running' になるまで数分待機してください。")
            print("-" * 50)
        else:
            print(f"⚠️ エラーが発生しました:\n{result.stderr}")

    except Exception as e:
        print(f"⚠️ 実行エラー: {e}")

if __name__ == "__main__":
    deploy()