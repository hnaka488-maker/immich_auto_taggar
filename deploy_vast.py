import os
import subprocess
from dotenv import load_dotenv

# .env ファイルから環境変数を読み込む
load_dotenv()

def get_env_or_error(key):
    """環境変数を取得し、未設定ならエラーを投げるヘルパー関数"""
    value = os.getenv(key)
    if not value:
        raise ValueError(f"❌ .env ファイルに {key} が設定されていません。確認してください。")
    return value

def deploy():
    # 1. vastai.exe の絶対パス（環境に合わせて調整済み）
    vastai_exe = r"C:\Users\n-tra\AppData\Local\Python\pythoncore-3.14-64\Scripts\vastai.exe"

    try:
        # 2. .env から設定を読み込む
        model_url = get_env_or_error("MODEL_URL")
        docker_image = get_env_or_error("DOCKER_IMAGE")
        immich_url = get_env_or_error("IMMICH_URL")
        immich_api_key = get_env_or_error("IMMICH_API_KEY")

        print("🔍 最安の RTX 4090 / A6000 (Verified) を探しています...")
        
        # 3. Vast.ai で利用可能な最安の GPU リストを取得
        search_cmd = f'{vastai_exe} search offers "gpu_name=RTX_4090 num_gpus=1 verified=true" -o "price_per_gpu"'
        
        # 検索の実行
        offers_output = subprocess.check_output(search_cmd, shell=True).decode('utf-8').strip()
        
        # 結果を行に分割
        lines = [line for line in offers_output.split('\n') if line.strip()]
        
        if len(lines) < 2:
            print("❌ 条件に合う GPU が見つかりませんでした。")
            return

        # 最安の Offer ID を取得
        first_offer = lines[1].split()[0]
        print(f"✅ 最安の Offer ID {first_offer} を確保しました。")

        # 4. インスタンスを作成（デプロイ開始）
        # 【修正ポイント A】MODEL_URL を AZURE_SAS_URL という名前に変更
        # 【修正ポイント B】--onstart オプションを追加して自動起動を設定
        # --- 修正後の launch_cmd 部分 ---
        # 先ほどコピーしたGitHubのRaw URLを入力してください
        tagger_raw_url = "https://raw.githubusercontent.com/hnaka488-maker/immich_auto_taggar/refs/heads/main/tagger_script.py"

        # --- 修正後の launch_cmd 部分 ---
        # --onstart に、直接コマンドではなく「ファイル名」を指定します
        launch_cmd = (
            f'{vastai_exe} create instance {first_offer} '
            f'--image {docker_image} '
            f'--env "AZURE_SAS_URL=\'{model_url}\' IMMICH_URL=\'{immich_url}\' IMMICH_API_KEY=\'{immich_api_key}\'" '
            f'--onstart onstart.sh '  # ここをファイル名に変更
            f'--disk 60'
        )
        
        print("🚀 Vast.ai にデプロイ命令を送信中...")
        subprocess.run(launch_cmd, shell=True)
        
        print("-" * 50)
        print("✨ 【全自動モード】デプロイ命令の送信が完了しました！")
        print("1. Vast.ai のコンソール（https://vast.ai/console/instances/）を開いてください。")
        print("2. Status が 'Running' になると、バックグラウンドで自動的にダウンロードと解析が始まります。")
        print("3. SSH でログインして操作する必要はありません。Immich にタグが付くのを待つだけです。")
        print("-" * 50)

    except subprocess.CalledProcessError as e:
        print(f"⚠️ vastai コマンドの実行中にエラーが発生しました: {e}")
    except Exception as e:
        print(f"⚠️ 予期しないエラーが発生しました: {e}")

if __name__ == "__main__":
    deploy()