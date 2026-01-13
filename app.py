import streamlit as st
from PIL import Image
import io

st.title("画像軽量化ツール 🐼")
st.write("用途に合わせて「PNG圧縮」「WebP変換」「JPEG変換」を選べます。")

# 設定エリア
with st.container():
    st.subheader("設定")
    # 変換モードの選択（3つに増えました）
    mode = st.radio(
        "変換モードを選択してください",
        (
            "PNGのまま圧縮 (画質キープ)",
            "WebPに変換 (超軽量・推奨)",
            "JPEGに変換 (写真向け・背景透過なし)"
        )
    )

    # 共通：リサイズオプション
    resize_ratio = st.slider("画像の大きさ（縮尺）", 10, 100, 100, help="100%なら元の大きさのままです。小さくするとさらに軽くなります。")

# 画像アップロード
uploaded_file = st.file_uploader("PNG画像をアップロード", type=["png"])

if uploaded_file is not None:
    # 画像を開く
    image = Image.open(uploaded_file)
    original_size = uploaded_file.size / 1024
    
    # 元画像を表示
    st.image(image, caption="元の画像", use_container_width=True)
    st.write(f"元のサイズ: {original_size:.2f} KB")

    # 変換実行ボタン
    if st.button("変換・圧縮を実行"):
        # バッファ（保存場所）の準備
        img_buffer = io.BytesIO()

        # 1. リサイズ処理
        if resize_ratio < 100:
            width, height = image.size
            new_width = int(width * resize_ratio / 100)
            new_height = int(height * resize_ratio / 100)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 2. モードごとの変換処理
        if mode == "PNGのまま圧縮 (画質キープ)":
            # 減色処理 (256色)
            img_converted = image.quantize(colors=256, method=2)
            img_converted.save(img_buffer, format="PNG", optimize=True)
            file_ext = "png"
            mime_type = "image/png"

        elif mode == "WebPに変換 (超軽量・推奨)":
            # WebP変換 (画質80)
            image.save(img_buffer, format="WEBP", quality=80)
            file_ext = "webp"
            mime_type = "image/webp"
        
        else: # JPEGに変換
            # JPEGは透明を持てないので、背景を「白」にする処理が必要
            if image.mode in ('RGBA', 'LA'):
                # 白い背景を作成
                background = Image.new('RGB', image.size, (255, 255, 255))
                # その上に画像を貼り付け（透明部分が白になる）
                background.paste(image, mask=image.split()[-1]) # アルファチャンネルをマスクとして使用
                save_image = background
            else:
                save_image = image.convert("RGB")
            
            # JPEG保存 (画質85)
            save_image.save(img_buffer, format="JPEG", quality=85)
            file_ext = "jpg"
            mime_type = "image/jpeg"

        # 変換後のデータ取得
        img_data = img_buffer.getvalue()
        converted_size = len(img_data) / 1024
        reduction_rate = 100 - (converted_size / original_size * 100)

        # 結果表示
        st.success(f"完了！ 約 {reduction_rate:.1f}% 軽くなりました 🎉")
        st.write(f"変換後のサイズ: {converted_size:.2f} KB")
        
        # ダウンロードボタン
        st.download_button(
            label=f"画像をダウンロード (. {file_ext})",
            data=img_data,
            file_name=f"compressed_image.{file_ext}",
            mime=mime_type
        )