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

# Session state initialize karein taake download dabane par file gayab na ho
if "video_bytes" not in st.session_state:
    st.session_state.video_bytes = None
if "video_filename" not in st.session_state:
    st.session_state.video_filename = None

raw_input = st.text_input("TikTok Video Link yahan paste karein:")

# Fixed 4K CC & New Sharpen Preset Values (Locked)
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
        # Purani video clear karein
        st.session_state.video_bytes = None
        
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
                    "-movflags", "+faststart",
                    "-c:a", "aac", "-b:a", "192k",
                    edited_video
                ]
                subprocess.run(cmd, check=True)

            # Video file ko memory (bytes) mein save karein
            if os.path.exists(edited_video) and os.path.getsize(edited_video) > 0:
                with open(edited_video, "rb") as f:
                    st.session_state.video_bytes = f.read()
                st.session_state.video_filename = f"4K_CC_{job_id}.mp4"
            else:
                st.error("Video file sahi se ban nahi saki, dobara koshish karein.")

        except Exception as e:
            st.error(f"Error aaya hai: {e}")
        finally:
            if os.path.exists(raw_video):
                os.remove(raw_video)
            if os.path.exists(edited_video):
                os.remove(edited_video)

# Agar video tayyar hai to preview aur download button dikhayein
if st.session_state.video_bytes is not None:
    st.success("Video 4K CC mein edit ho gayi hai!")
    st.video(st.session_state.video_bytes)
    st.download_button(
        label="⬇️ Download 4K CC Video",
        data=st.session_state.video_bytes,
        file_name=st.session_state.video_filename,
        mime="video/mp4"
    )
