import os
import time
import base64
import json
import logging
import requests
from io import BytesIO
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv
from tqdm import tqdm
from openai import OpenAI  # Local vLLM エンジン用

# --- ログ設定 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
load_dotenv()

# --- 設定変数 (Vast.ai 用に最適化) ---
IMMICH_URL = os.getenv("IMMICH_URL", "").rstrip("/")
IMMICH_API_KEY = os.getenv("IMMICH_API_KEY", "")
# Local vLLM サーバーへの接続設定 (通常 localhost:8000)
LOCAL_AI_URL = "http://localhost:8000/v1"
client = OpenAI(api_key="none", base_url=LOCAL_AI_URL)

TAG_PREFIX = os.getenv("TAG_PREFIX", "AI_")
HEADERS = {"Accept": "application/json", "x-api-key": IMMICH_API_KEY}

# --- 分類リスト付きシステムプロンプト (成功コードから移植) ---
SYSTEM_PROMPT = """
この画像に写っている人物について、以下の項目を厳密なJSON形式のみで出力してください。
漢字は必ず日本語の漢字を使用してください。

【分類リスト】
- swimsuit_type: ビキニ, 三角ビキニ, ホルターネックビキニ, マイクロビキニ, ハイレグビキニ, モノキニ, ハイレグモノキニ, スリングショット, 眼帯ビキニ, Tバックビキニ, ブラジリアン, スクール水着, 競泳水着, ワンピース, その他
- underwear_type: 三角ブラ, マイクロブラ, ワイヤーブラ, レースブラ, オープンブラ, Tバック, Gストリング, 紐パン, キャミソール, ベビードール, テディ, ガーターベルト, その他
- outfit: 制服, 和服, 着物, ドレス, コスプレ, スポーツウェア, カジュアル, その他
- accessory: 眼鏡, 帽子, 猫耳, 花冠, 複数人, その他
- pose: 立ちポーズ, 胸寄せポーズ, 見返り美人, 振り向きポーズ, 脇見せポーズ, 膝立ち開脚, 膝抱えポーズ, 膝抱え座り, 椅子に片足乗せ, 正座崩しカーブ, 肩すくめ胸寄せ, 頭上両手上げ, 寝そべり, 四つん這い, しゃがみ, 腰掛け, 髪かきあげ, ピース, 前屈みヒップ強調, うつ伏せヒップ強調, 仰向け片脚上げ, M字開脚, 女豹のポーズ, その他

【出力JSONフォーマット】
{
  "analysis": "1〜2文で詳細分析",
  "swimsuit": bool,
  "swimsuit_type": リストから選択,
  "underwear": bool,
  "underwear_type": リストから選択,
  "outfit": リストから選択,
  "accessory": [リストから選択],
  "nude": bool,
  "pose": リストから選択
}
"""

def analyze_image_local(base64_image: str) -> Tuple[List[str], Dict]:
    """Vast.ai ローカルの Qwen2.5-VL モデルで解析"""
    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-VL-7B-Instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": SYSTEM_PROMPT},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ],
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        output_text = response.choices[0].message.content
        return parse_ai_output(output_text)
    except Exception as e:
        logger.error(f"AI解析エラー: {e}")
        return None, None

def parse_ai_output(output_text: str) -> Tuple[List[str], Dict]:
    """成功コードのパースロジックを継承"""
    try:
        data = json.loads(output_text)
        tags = []
        def is_true(v): return v is True or str(v).strip().lower() == "true"

        if is_true(data.get("swimsuit")):
            tags.append("水着")
            v = data.get("swimsuit_type")
            if v and v not in ["none", "その他"]: tags.append(f"水着/{v}")
        if is_true(data.get("underwear")):
            tags.append("下着")
            v = data.get("underwear_type")
            if v and v not in ["none", "その他"]: tags.append(f"下着/{v}")
        
        outfit = data.get("outfit")
        if outfit and outfit not in ["none", "その他"]: tags.append(f"衣装/{outfit}")

        acc = data.get("accessory", [])
        if isinstance(acc, str): acc = [acc]
        for a in acc:
            if a and a not in ["none", "その他"]: tags.append(f"特徴/{a}")
                
        if is_true(data.get("nude")): tags.append("ヌード")
        
        pose = data.get("pose")
        if pose and pose not in ["none", "その他"]: tags.append(f"ポーズ/{pose}")

        return [f"{TAG_PREFIX}{t}" for t in tags], data
    except: return None, None

def ensure_tag_path(path: str, existing_tags: Dict[str, str]) -> str:
    """階層タグの作成/取得"""
    if path in existing_tags: return existing_tags[path]
    parts = path.split("/")
    tag_name, parent_id = parts[-1], None
    if len(parts) > 1: parent_id = ensure_tag_path("/".join(parts[:-1]), existing_tags)
    try:
        r = requests.post(f"{IMMICH_URL}/tags", json={"name": tag_name, "type": "custom", "parentId": parent_id}, headers=HEADERS)
        tid = r.json()["id"]
        existing_tags[path] = tid
        return tid
    except: return None

def main():
    # 既存タグの取得
    try:
        r_tags = requests.get(f"{IMMICH_URL}/tags", headers=HEADERS)
        existing_tags = {t.get("name"): t["id"] for t in r_tags.json()}
    except Exception as e:
        logger.error(f"Immich接続失敗: {e}")
        return

    logger.info("=== Vast.ai Qwen-Tagger 起動 ===")
    
    page = 1
    while True:
        # 成功コードと同じ「検索」エンドポイントを使用 (404回避策)
        r = requests.post(f"{IMMICH_URL}/search/metadata", headers=HEADERS, json={"page": page, "size": 100, "type": "IMAGE"})
        assets = r.json().get("assets", {}).get("items", [])
        if not assets: break

        for asset in tqdm(assets, desc=f"Processing Page {page}"):
            aid = asset["id"]
            # 既にAIタグがあるか簡易チェック（重複防止）
            has_ai_tag = any(t.get("name", "").startswith(TAG_PREFIX) for t in asset.get("tags", []))
            if has_ai_tag: continue

            try:
                # サムネイル取得
                r_thumb = requests.get(f"{IMMICH_URL}/assets/{aid}/thumbnail?size=preview", headers=HEADERS)
                base64_img = base64.b64encode(r_thumb.content).decode('utf-8')
                
                # AI解析 (Local Qwen)
                tags, _ = analyze_image_local(base64_img)
                
                if tags:
                    tags.append(f"{TAG_PREFIX}判定済み")
                    tids = [ensure_tag_path(t, existing_tags) for t in tags]
                    # タグ付与
                    valid_ids = [tid for tid in tids if tid]
                    if valid_ids:
                        requests.put(f"{IMMICH_URL}/tags/assets", json={"tagIds": valid_ids, "assetIds": [aid]}, headers=HEADERS)
                        logger.info(f"✅ Tagged: {asset.get('originalFileName', aid)} -> {tags}")
            except Exception as e:
                logger.warning(f"解析失敗 Asset {aid}: {e}")

        page += 1

if __name__ == "__main__":
    main()