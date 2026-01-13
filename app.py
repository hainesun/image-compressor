import streamlit as st
from PIL import Image
import io
import zipfile

st.title("画像軽量化ツール 🐼")
st.write("画質優先か、圧縮率優先かを選んで一括変換できます。")

# --- サイドバー設定 ---
with st.container():
    st.subheader("設定")
    
    # 変換モード
    mode = st.radio(
        "変換モード",
        (
            "PNG (画質・圧縮バランス選択)",
            "WebPに変換 (超軽量・推奨)",
            "JPEGに変換 (写真向け・背景透過なし)"
        )
    )

    # PNGの場合だけ、詳細設定を表示
    png_quality_mode = "圧縮優先 (256色・超軽量)" # 初期値
    if mode == "PNG (画質・圧縮バランス選択)":
        png_quality_mode = st.radio(
            "PNGの処理方法",
            (
                "画質優先 (色を減らさない・サイズ大)",
                "圧縮優先 (256色に減色・サイズ小)"
            ),
            help="「画質優先」は見た目が変わりませんが、サイズはあまり減りません。「圧縮優先」は劇的に軽くなりますが、少しザラザラします。"
        )

    # リサイズ
    resize_ratio = st.slider("画像の大きさ（縮尺）", 10, 100, 100, help="小さくすると画質を保ったまま軽くなります。")

# --- 画像アップロード ---
uploaded_files = st.file_uploader(
    "画像をアップロード（複数選択可）", 
    type=["png", "jpg", "jpeg"], # 入力はJPGも許可しておきました
    accept_multiple_files=True
)

if uploaded_files:
    st.write(f"📂 **{len(uploaded_files)} 枚** の画像を読み込みました")
    
    # 実行ボタン
    if st.button("一括変換を実行"):
        
        # ZIPファイルを作るための箱を準備
        zip_buffer = io.BytesIO()
        
        # プログレスバー
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            
            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"処理中: {uploaded_file.name} ...")
                
                # 画像を開く
                image = Image.open(uploaded_file)
                
                # 1. リサイズ処理
                if resize_ratio < 100:
                    width, height = image.size
                    new_width = int(width * resize_ratio / 100)
                    new_height = int(height * resize_ratio / 100)
                    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # 保存用バッファ
                img_byte_arr = io.BytesIO()
                file_name_body = uploaded_file.name.rsplit('.', 1)[0]
                
                # 2. モードごとの変換処理
                if mode == "PNG (画質・圧縮バランス選択)":
                    if png_quality_mode == "画質優先 (色を減らさない・サイズ大)":
                        # 色を減らさず、optimizeフラグだけで圧縮（一番きれい）
                        # compress_level=9 (最大圧縮) をかけて時間をかけて縮める
                        image.save(img_byte_arr, format="PNG", optimize=True, compress_level=9)
                    else:
                        # 以前のやり方（減色）
                        image = image.quantize(colors=256, method=2)
                        image.save(img_byte_arr, format="PNG", optimize=True)
                    
                    save_name = f"{file_name_body}_opt.png"
                    
                elif mode == "WebPに変換 (超軽量・推奨)":
                    image.save(img_byte_arr, format="WEBP", quality=80)
                    save_name = f"{file_name_body}.webp"
                    
                else: # JPEG
                    if image.mode in ('RGBA', 'LA'):
                        background = Image.new('RGB', image.size, (255, 255, 255))
                        background.paste(image, mask=image.split()[-1])
                        image = background
                    else:
                        image = image.convert("RGB")
                    
                    image.save(img_byte_arr, format="JPEG", quality=85)
                    save_name = f"{file_name_body}.jpg"

                # ZIPに追加
                zf.writestr(save_name, img_byte_arr.getvalue())
                
                progress_bar.progress((i + 1) / len(uploaded_files))

        status_text.text("すべての処理が完了しました！")
        
        # ZIPダウンロード
        st.download_button(
            label="📦 まとめてダウンロード (ZIP)",
            data=zip_buffer.getvalue(),
            file_name="compressed_images.zip",
            mime="application/zip"
        )
