import streamlit as st
from PIL import Image, ImageOps
import io
import zipfile

st.title("画像軽量化ツール 🐼 ")
st.write("「画質は綺麗に残したい、でも軽くしたい」という微調整が可能です。")

# --- サイドバー設定 ---
with st.container():
    st.subheader("設定")
    
    # 変換モード
    mode = st.radio(
        "変換モード",
        (
            "PNG (画質・圧縮バランス調整)",
            "WebPに変換 (超軽量・推奨)",
            "JPEGに変換 (写真向け・背景透過なし)"
        )
    )

    # PNGの場合のオプション
    png_reduce_colors = False # 初期値
    posterize_bits = 8 # 初期値（加工なし）

    if mode == "PNG (画質・圧縮バランス調整)":
        png_mode_select = st.radio(
            "PNGの処理タイプ",
            ("フルカラーのまま軽くする (推奨)", "256色に減色 (最強に軽い)")
        )
        
        if png_mode_select == "256色に減色 (最強に軽い)":
            png_reduce_colors = True
            st.info("ℹ️ 色数を256色に制限します。ロゴやアイコンには最適ですが、写真は少し荒れます。")
        else:
            png_reduce_colors = False
            # ポスタリゼーション（色深度）のスライダー
            st.info("ℹ️ 以下のスライダーを下げると、見た目をほぼ保ったままデータ量が減ります。")
            posterize_bits = st.slider(
                "色の滑らかさ (ビット数)", 
                min_value=4, max_value=8, value=6,
                help="8=無劣化(重い)。6=見た目変化なしで軽量化。4=少し荒いが軽い。"
            )

    # 共通リサイズ
    resize_ratio = st.slider("画像の大きさ（縮尺）", 10, 100, 100, help="小さくすると画質を保ったまま軽くなります。")

# --- 画像アップロード ---
uploaded_files = st.file_uploader(
    "画像をアップロード（複数可・ドラッグ&ドロップ）", 
    type=["png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.write(f"📂 **{len(uploaded_files)} 枚** の画像を読み込みました")
    
    if st.button("一括変換を実行"):
        
        zip_buffer = io.BytesIO()
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            
            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"処理中: {uploaded_file.name} ...")
                
                image = Image.open(uploaded_file)
                
                # 1. リサイズ
                if resize_ratio < 100:
                    width, height = image.size
                    new_width = int(width * resize_ratio / 100)
                    new_height = int(height * resize_ratio / 100)
                    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                img_byte_arr = io.BytesIO()
                file_name_body = uploaded_file.name.rsplit('.', 1)[0]
                
                # 2. モードごとの変換
                if mode == "PNG (画質・圧縮バランス調整)":
                    
                    if png_reduce_colors:
                        # 従来の減色処理 (256色)
                        image = image.quantize(colors=256, method=2)
                        image.save(img_byte_arr, format="PNG", optimize=True)
                    else:
                        # ★ここが新機能：ポスタリゼーション処理
                        # 画像がPモード(パレット)ならRGBに戻す
                        if image.mode == 'P':
                            image = image.convert('RGBA')
                        
                        # ビット数が8未満なら処理を実行
                        if posterize_bits < 8:
                            # アルファチャンネル(透明)があるとposterizeが失敗するので分離
                            if image.mode in ('RGBA', 'LA'):
                                # 透明部分を取り分ける
                                alpha = image.getchannel('A')
                                image = image.convert('RGB')
                                # RGB部分だけ色を少し間引く（見た目は変わらない）
                                image = ImageOps.posterize(image, posterize_bits)
                                # 透明部分を戻す
                                image.putalpha(alpha)
                            else:
                                image = image.convert('RGB')
                                image = ImageOps.posterize(image, posterize_bits)

                        # 保存 (optimize=Trueで圧縮)
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

                zf.writestr(save_name, img_byte_arr.getvalue())
                progress_bar.progress((i + 1) / len(uploaded_files))

        status_text.text("すべての処理が完了しました！")
        
        st.download_button(
            label="📦 まとめてダウンロード (ZIP)",
            data=zip_buffer.getvalue(),
            file_name="compressed_images.zip",
            mime="application/zip"
        )
