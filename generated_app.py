import streamlit as st
import os
import base64
from PIL import Image
import io
from openai import OpenAI

# ページ設定
st.set_page_config(
    page_title="食材から簡単料理提案",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# カスタムCSSでモダンなUI（ダークモード対応）
st.markdown("""
<style>
    .main {
        background-color: var(--background-color);
        color: var(--text-color);
    }
    .stButton button {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        background-color: #45a049;
        transform: scale(1.02);
    }
    .recipe-card {
        background-color: var(--secondary-background-color);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-top: 1rem;
    }
    @media (max-width: 768px) {
        .stButton button {
            width: 100%;
        }
    }
</style>
""", unsafe_allow_html=True)

st.title("🍳 食材から簡単料理提案")
st.markdown("スマホのカメラで食材の写真を撮るか、画像をアップロードしてください。AIが簡単レシピを提案します。")

# セッション状態の初期化
if "recipe" not in st.session_state:
    st.session_state.recipe = None
if "show_recipe" not in st.session_state:
    st.session_state.show_recipe = False

# 画像入力方法の選択
input_method = st.radio("画像の入力方法を選択", ("カメラで撮影", "ファイルをアップロード"), horizontal=True)

image = None
if input_method == "カメラで撮影":
    image = st.camera_input("食材の写真を撮影してください")
else:
    uploaded_file = st.file_uploader("食材の画像をアップロード", type=["jpg", "jpeg", "png", "webp"])
    if uploaded_file is not None:
        image = uploaded_file

# 人数と追加食材の入力
col1, col2 = st.columns(2)
with col1:
    servings = st.selectbox("何人前の料理にしますか？", options=[1, 2, 3, 4, 5, 6], index=1)
with col2:
    extra_ingredients = st.text_input("追加で可能な食材（例：玉子、豆腐、乾麺）", placeholder="カンマ区切りで入力")

# レシピ生成ボタン
if st.button("レシピを提案", type="primary", use_container_width=True):
    if image is None:
        st.warning("画像が選択されていません。カメラで撮影するか、画像をアップロードしてください。")
    else:
        try:
            # 画像をPILで開く
            img = Image.open(image)
            # RGBに変換（必要に応じて）
            if img.mode != "RGB":
                img = img.convert("RGB")
            # 画像をbase64エンコード
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

            # DeepSeek APIクライアントの初期化
            api_key = os.environ.get("DEEPSEEK_API_KEY")
            if not api_key:
                st.error("DEEPSEEK_API_KEYが設定されていません。環境変数を確認してください。")
                st.stop()

            client = OpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com/v1"
            )

            # プロンプトの構築
            prompt = f"""
            この画像に写っている食材を使って、{servings}人前の簡単料理のレシピを提案してください。
            追加で利用可能な食材: {extra_ingredients if extra_ingredients else 'なし'}
            以下の形式で出力してください：
            - 料理名
            - 材料（分量付き）
            - 作り方（簡単な手順）
            - 調理時間の目安
            簡単で家庭で作りやすいレシピにしてください。
            """

            # APIリクエスト
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.7
            )

            recipe = response.choices[0].message.content
            st.session_state.recipe = recipe
            st.session_state.show_recipe = True

        except Exception as e:
            st.error(f"画像の処理またはレシピ生成中にエラーが発生しました: {str(e)}")
            st.info("画像が正しく読み込めるか確認し、もう一度お試しください。")
            st.session_state.show_recipe = False

# レシピの表示
if st.session_state.show_recipe and st.session_state.recipe:
    st.markdown("---")
    st.subheader("🍽️ 提案されたレシピ")
    st.markdown(f"<div class='recipe-card'>{st.session_state.recipe}</div>", unsafe_allow_html=True)
