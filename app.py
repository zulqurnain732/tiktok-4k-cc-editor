import streamlit as st
import yt_dlp
import subprocess
import os
import uuid
import re
import imageio_ffmpeg

st.set_page_config(page_title="4K CC TikTok Editor", page_icon="🎬")
st.title("🎬 TikTok 4K CC Auto-Editor")
st.write("TikTok video ka link paste karein — automatic 4K CC & High-Sharpen edit hokar download ke liye tayyar ho jayegi.")

raw_input = st.text_input("TikTok Video Link yahan paste karein:")

# Fixed 4K CC & New Sharpen Preset Values (Locked - Koi change nahi kar sakta)
SHARPEN_STRENGTH = 2.2
SATURATION = 1.38
CONTRAST = 1.18
BRIGHTNESS = 0.02

def extract_url(text):
    match = re.search(r'(https?://[^\s]+)', text)
    return match.group(1) if match else None

if st.button("Edit & Prepare Download"):
    tiktok_url = extract_url(raw_input)
    
    if not tiktok_url:
        st.error("Sahi TikTok link paste karein!")
    else:
        job_id = str(uuid.uuid4())[:8]
        raw_video = f"raw_{job_id}.mp4"
        edited_video = f"4K_CC_{job_id}.mp4"
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

        try:
            with st.spinner("1/2: TikTok video download ho rahi hai..."):
                ydl_opts = {
                    'outtmpl': raw_video,
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'quiet': True,
                    'no_warnings': True
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([tiktok_url])

            with st.spinner("2/2: 4K CC & High-Sharpen preset apply ho raha hai..."):
                vf_filter = (
                    f"unsharp=5:5:{SHARPEN_STRENGTH}:5:5:0.0,"
                    f"eq=contrast={CONTRAST}:saturation={SATURATION}:brightness={BRIGHTNESS},"
                    f"scale=iw*1.5:ih*1.5:flags=lanczos"
                )
                
                cmd = [
                    ffmpeg_exe, "-y", "-i", raw_video,
                    "-vf", vf_filter,
                    "-r", "60",
                    "-c:v", "libx264", "-crf", "18", "-preset", "fast",
                    "-c:a", "aac", "-b:a", "192k",
                    edited_video
                ]
                subprocess.run(cmd, check=True)

            st.success("Video 4K CC mein edit ho gayi hai!")
            
            with open(edited_video, "rb") as file:
                st.download_button(
                    label="⬇️ Download 4K CC Video",
                    data=file,
                    file_name=f"4K_CC_{job_id}.mp4",
                    mime="video/mp4"
                )

        except Exception as e:
            st.error(f"Error aaya hai: {e}")
        finally:
            if os.path.exists(raw_video):
                os.remove(raw_video)
