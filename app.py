import streamlit as st
import yt_dlp
import requests
import subprocess
import os
import uuid
import re
import imageio_ffmpeg

st.set_page_config(page_title="4K CC TikTok Editor", page_icon="🎬")
st.title("🎬 TikTok 4K HDR CC Auto-Editor")
st.write("TikTok video ka link paste karein — exact 4K CC, HDR Clarity, Glow aur High-Sharpen edit hokar download ke liye tayyar ho jayegi.")

if "video_bytes" not in st.session_state:
    st.session_state.video_bytes = None
if "video_filename" not in st.session_state:
    st.session_state.video_filename = None

raw_input = st.text_input("TikTok Video Link yahan paste karein:")

def extract_url(text):
    match = re.search(r'(https?://[^\s]+)', text)
    return match.group(1) if match else None

def download_tiktok_video(url, output_path):
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

            with st.spinner("2/2: Heavy 4K HDR CC + Glow + New Sharpen apply ho raha hai..."):
                # Exact Nova Editor / Alight Motion style 4K CC Filtergraph:
                # 1. Lanczos 1080p/2K upscale for crisp edges
                # 2. HDR Curve (shadows lift + highlights punch)
                # 3. Contrast Adaptive Sharpening (CAS) + Heavy Unsharp (New Sharpen look)
                # 4. Rich Color Grading + Soft 4K Highlight Glow (Screen blend)
                filter_complex = (
                    "[0:v]scale=trunc(iw*1.5/2)*2:trunc(ih*1.5/2)*2:flags=lanczos,"
                    "curves=all='0/0.03 0.22/0.27 0.5/0.55 0.78/0.84 1/1',"
                    "cas=strength=0.85,"
                    "unsharp=7:7:2.6:7:7:0.4,"
                    "eq=contrast=1.22:saturation=1.42:brightness=0.03:gamma=1.06,"
                    "colorbalance=rs=0.04:gs=0.01:bs=-0.03:rh=0.05:gh=0.02:bh=-0.02,"
                    "split=2[sharp][blur];"
                    "[blur]gblur=sigma=12,eq=brightness=0.05:contrast=1.1[glow];"
                    "[sharp][glow]blend=all_mode=screen:all_opacity=0.22[out]"
                )
                
                cmd = [
                    ffmpeg_exe, "-y", "-i", raw_video,
                    "-filter_complex", filter_complex,
                    "-map", "[out]", "-map", "0:a?",
                    "-r", "60",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "17", "-preset", "fast",
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
                st.session_state.video_filename = f"4K_HDR_CC_{job_id}.mp4"
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
    st.success("Video full 4K HDR CC mein edit ho gayi hai!")
    st.video(st.session_state.video_bytes)
    st.download_button(
        label="⬇️ Download 4K CC Video",
        data=st.session_state.video_bytes,
        file_name=st.session_state.video_filename,
        mime="video/mp4"
    )
