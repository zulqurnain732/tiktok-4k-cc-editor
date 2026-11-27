import streamlit as st
import yt_dlp
import requests
import subprocess
import os
import uuid
import re
import imageio_ffmpeg

st.set_page_config(page_title="4K CC TikTok Editor", page_icon="🎬")
st.title("🎬 TikTok 4K CC Auto-Editor")
st.write("TikTok video ka link paste karein — automatic 4K CC & High-Sharpen edit hokar download ke liye tayyar ho jayegi.")

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

def download_tiktok_video(url, output_path):
    # Method 1: TikWM API (Bina watermark HD video ke liye sabse reliable)
    try:
        api_url = "https://www.tikwm.com/api/"
        resp = requests.post(api_url, data={"url": url, "hd": 1}, timeout=20).json()
        if resp.get("code") == 0 and resp.get("data"):
            video_url = resp["data"].get("hdplay") or resp["data"].get("play")
            if video_url:
                if not video_url.startswith("http"):
                    video_url = "https://www.tikwm.com" + video_url
                vid_data = requests.get(video_url, timeout=30)
                if vid_data.status_code == 200 and len(vid_data.content) > 50000:
                    with open(output_path, "wb") as f:
                        f.write(vid_data.content)
                    return True
    except Exception:
        pass

    # Method 2: yt-dlp fallback
    try:
        ydl_opts = {
            'outtmpl': output_path,
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        if os.path.exists(output_path) and os.path.getsize(output_path) > 50000:
            return True
    except Exception:
        pass

    return False

if st.button("Edit & Prepare Download"):
    tiktok_url = extract_url(raw_input)
    
    if not tiktok_url:
        st.error("Sahi TikTok link paste karein!")
    else:
        st.session_state.video_bytes = None
        
        job_id = str(uuid.uuid4())[:8]
        raw_video = f"raw_{job_id}.mp4"
        edited_video = f"4K_CC_{job_id}.mp4"
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

        try:
            with st.spinner("1/2: TikTok HD video download ho rahi hai..."):
                success = download_tiktok_video(tiktok_url, raw_video)
                if not success:
                    st.error("TikTok video download nahi ho saki. Link check karein ya public video ka link dein.")
                    st.stop()

            with st.spinner("2/2: 4K CC & High-Sharpen preset apply ho raha hai (thoda intezar karein)..."):
                vf_filter = (
                    f"unsharp=5:5:{SHARPEN_STRENGTH}:5:5:0.0,"
                    f"eq=contrast={CONTRAST}:saturation={SATURATION}:brightness={BRIGHTNESS},"
                    f"scale=trunc(iw*1.5/2)*2:trunc(ih*1.5/2)*2:flags=lanczos"
                )
                
                cmd = [
                    ffmpeg_exe, "-y", "-i", raw_video,
                    "-vf", vf_filter,
                    "-r", "60",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "18", "-preset", "fast",
                    "-movflags", "+faststart",
                    "-c:a", "aac", "-b:a", "192k",
                    edited_video
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    st.error(f"Video processing error: {result.stderr[-300:]}")
                    st.stop()

            if os.path.exists(edited_video) and os.path.getsize(edited_video) > 50000:
                with open(edited_video, "rb") as f:
                    st.session_state.video_bytes = f.read()
                st.session_state.video_filename = f"4K_CC_{job_id}.mp4"
            else:
                st.error("Edited video empty bani hai, dobara koshish karein.")

        except Exception as e:
            st.error(f"Error aaya hai: {e}")
        finally:
            if os.path.exists(raw_video):
                os.remove(raw_video)
            if os.path.exists(edited_video):
                os.remove(edited_video)

if st.session_state.video_bytes is not None:
    st.success("Video 4K CC mein edit ho gayi hai!")
    st.video(st.session_state.video_bytes)
    st.download_button(
        label="⬇️ Download 4K CC Video",
        data=st.session_state.video_bytes,
        file_name=st.session_state.video_filename,
        mime="video/mp4"
    )
