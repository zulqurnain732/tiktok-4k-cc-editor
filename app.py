import streamlit as st
import yt_dlp
import subprocess
import os
import uuid

st.set_page_config(page_title="4K CC TikTok Editor", page_icon="🎬")
st.title("🎬 TikTok 4K CC Auto-Editor")
st.write("TikTok video ka link paste karein aur 4K Sharpen + Color Graded video download karein.")

tiktok_url = st.text_input("TikTok Video Link yahan paste karein:")

# CC Intensity sliders (Nova Editor ke Adjust option ki tarah)
sharpen_strength = st.slider("Sharpen Quality (New Sharpen Effect)", 1.0, 3.0, 2.0)
saturation = st.slider("Color Vibrance (CC)", 1.0, 1.8, 1.35)
contrast = st.slider("Contrast", 1.0, 1.5, 1.15)

if st.button("Edit & Prepare Download"):
    if not tiktok_url:
        st.error("Pehle TikTok ka link dalein!")
    else:
        job_id = str(uuid.uuid4())[:8]
        raw_video = f"raw_{job_id}.mp4"
        edited_video = f"4K_CC_{job_id}.mp4"

        try:
            with st.spinner("1/2: TikTok video download ho rahi hai..."):
                ydl_opts = {
                    'outtmpl': raw_video,
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'quiet': True
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([tiktok_url])

            with st.spinner("2/2: 4K CC & Sharpen filter apply ho raha hai..."):
                # FFmpeg filter jo Nova Editor ke 'New Sharpen' aur '4K CC' jaisa look deta hai
                vf_filter = (
                    f"unsharp=5:5:{sharpen_strength}:5:5:0.0,"
                    f"eq=contrast={contrast}:saturation={saturation}:brightness=0.02,"
                    f"scale=iw*1.5:ih*1.5:flags=lanczos"
                )
                
                cmd = [
                    "ffmpeg", "-y", "-i", raw_video,
                    "-vf", vf_filter,
                    "-r", "60", # Smooth 60 FPS
                    "-c:v", "libx264", "-crf", "18", "-preset", "fast",
                    "-c:a", "copy",
                    edited_video
                ]
                subprocess.run(cmd, check=True)

            st.success("Video edit ho gayi hai!")
            
            with open(edited_video, "rb") as file:
                st.download_button(
                    label="⬇️ Download 4K CC Video",
                    data=file,
                    file_name=f"Edited_4K_CC_{job_id}.mp4",
                    mime="video/mp4"
                )

        except Exception as e:
            st.error(f"Error aaya hai: {e}")
        finally:
            if os.path.exists(raw_video):
                os.remove(raw_video)
