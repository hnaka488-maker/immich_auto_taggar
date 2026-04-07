from huggingface_hub import snapshot_download
import os

# 保存先のディレクトリ名
target_dir = "Qwen2.5-VL-7B-Instruct"

print(f"🚀 ダウンロードを開始します: {target_dir}")

# モデルのダウンロード実行
snapshot_download(
    repo_id="Qwen/Qwen2.5-VL-7B-Instruct",
    local_dir=target_dir,
    local_dir_use_symlinks=False,  # 本物のファイルをダウンロード
    revision="main"                 # 最新版を指定
)

print(f"✅ ダウンロードが完了しました！場所: {os.path.abspath(target_dir)}")