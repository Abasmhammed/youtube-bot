import os
import subprocess
import random
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("stream.log"),  # ✅ تم التصحيح
        logging.StreamHandler()
    ]
)

# YouTube RTMP URL
STREAM_URL = "rtmp://a.rtmp.youtube.com/live2/"
STREAM_KEY = os.getenv("YOUTUBE_STREAM_KEY")
VIDEO_FOLDER = "videos"

def get_videos():
    supported_extensions = ('.mp4', '.mkv', '.mov', '.avi')
    if not os.path.exists(VIDEO_FOLDER):
        os.makedirs(VIDEO_FOLDER)
    videos = [os.path.join(VIDEO_FOLDER, f) for f in os.listdir(VIDEO_FOLDER) 
              if f.lower().endswith(supported_extensions)]
    return videos

def stream_video(video_path):
    if not STREAM_KEY:
        logging.error("YOUTUBE_STREAM_KEY not found in environment variables.")
        return False

    full_url = f"{STREAM_URL}{STREAM_KEY}"
    
    command = [
        'ffmpeg',
        '-re', 
        '-i', video_path,
        '-c:v', 'libx264',
        '-preset', 'veryfast',
        '-maxrate', '3000k',
        '-bufsize', '6000k',
        '-pix_fmt', 'yuv420p',
        '-g', '50', 
        '-c:a', 'aac',
        '-b:a', '128k',
        '-ar', '44100',
        '-f', 'flv',
        full_url
    ]

    logging.info(f"Streaming: {video_path}")
    try:
        process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            universal_newlines=True
        )
        for line in process.stdout:
            pass
        process.wait()
        return process.returncode == 0
    except Exception as e:
        logging.error(f"Unexpected error during streaming: {e}")
        return False

def main():
    logging.info("Motivational 24/7 Live Stream Bot Started...")
    while True:
        videos = get_videos()
        if not videos:
            logging.warning(f"No videos found in '{VIDEO_FOLDER}' folder. Waiting 30 seconds...")
            time.sleep(30)
            continue
        
        random.shuffle(videos)
        
        for video in videos:
            success = stream_video(video)
            if not success:
                logging.error("Stream interrupted, retrying in 10 seconds...")
                time.sleep(10)
                break
            time.sleep(2)

if __name__ == "__main__":
    main()
