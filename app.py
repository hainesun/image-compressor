import streamlit as st
from PIL import Image
import io
import zipfile

st.title("画像軽量化ツール 🐼 (一括変換版)")
st.write("複数の画像をまとめて変換・圧縮し、ZIPでダウンロードできます。")

# --- サイドバー設定 ---
with st.container():
    st.subheader("設定")
    # 変換モード
    mode = st.radio(
        "変換モード",
        (
            "PNGのまま圧縮 (画質キープ)",
            "WebPに変換 (超軽量・推奨)",
            "JPEGに変換 (写真向け・背景透過なし)"
        )
    )
    # リサイズ
    resize_ratio = st.slider("画像の大きさ（縮尺）", 10, 100, 100, help="小さくするとさらに軽くなります。")

# --- 画像アップロード (accept_multiple_files=True に変更) ---
uploaded_files = st.file_uploader(
    "PNG画像をアップロード（複数選択可）", 
    type=["png"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.write(f"📂 **{len(uploaded_files)} 枚** の画像を読み込みました")
    
    # 実行ボタン
    if st.button("一括変換を実行"):
        
        # ZIPファイルを作るための箱を準備
        zip_buffer = io.BytesIO()
        
        # プログレスバー（進捗状況）を表示
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # ZIPファイル作成開始
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            
            for i, uploaded_file in enumerate(uploaded_files):
                # 進捗表示
                status_text.text(f"処理中: {uploaded_file.name} ...")
                
                # 画像を開く
                image = Image.open(uploaded_file)
                
                # 1. リサイズ処理
                if resize_ratio < 100:
                    width, height = image.size
                    new_width = int(width * resize_ratio / 100)
                    new_height = int(height * resize_ratio / 100)
                    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # 個別の画像データを保存するバッファ
                img_byte_arr = io.BytesIO()
                file_name_body = uploaded_file.name.rsplit('.', 1)[0]
                
                # 2. モードごとの変換処理
                if mode == "PNGのまま圧縮 (画質キープ)":
                    image = image.quantize(colors=256, method=2)
                    image.save(img_byte_arr, format="PNG", optimize=True)
                    save_name = f"{file_name_body}_compressed.png"
                    
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
                
                # プログレスバー更新
                progress_bar.progress((i + 1) / len(uploaded_files))

        status_text.text("すべての処理が完了しました！")
        
        # ZIPダウンロードボタン
        st.download_button(
            label="📦 まとめてダウンロード (ZIP)",
            data=zip_buffer.getvalue(),
            file_name="compressed_images.zip",
            mime="application/zip"
        )
