#!/usr/bin/env python3
"""
YouTube Live Bot - Advanced Streaming System
يقوم ببث الفيديوهات التحفيزية بشكل مستمر 24/7 على قناة يوتيوب
"""

import os
import subprocess
import random
import time
import logging
from pathlib import Path
from datetime import datetime

# إعداد السجلات (Logging)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('stream.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# إعدادات البث
STREAM_URL = "rtmp://a.rtmp.youtube.com/live2/"
STREAM_KEY = os.getenv("YOUTUBE_STREAM_KEY")
VIDEO_FOLDER = "videos"
RECONNECT_DELAY = 5  # ثوانٍ
MAX_RETRIES = 3

class YouTubeStreamer:
    """فئة للتعامل مع بث يوتيوب المباشر"""
    
    def __init__(self):
        self.stream_url = f"{STREAM_URL}{STREAM_KEY}"
        self.video_folder = Path(VIDEO_FOLDER)
        self.current_video = None
        self.retry_count = 0
        
    def get_videos(self):
        """الحصول على قائمة الفيديوهات المتاحة"""
        if not self.video_folder.exists():
            logger.warning(f"مجلد الفيديوهات غير موجود: {self.video_folder}")
            return []
        
        videos = list(self.video_folder.glob("*.mp4")) + \
                 list(self.video_folder.glob("*.mkv")) + \
                 list(self.video_folder.glob("*.mov"))
        
        logger.info(f"تم العثور على {len(videos)} فيديو")
        return videos
    
    def stream_video(self, video_path):
        """بث فيديو واحد إلى يوتيوب"""
        if not os.path.exists(video_path):
            logger.error(f"الفيديو غير موجود: {video_path}")
            return False
        
        self.current_video = video_path
        logger.info(f"جاري بث الفيديو: {os.path.basename(video_path)}")
        
        # أمر FFmpeg للبث
        command = [
            'ffmpeg',
            '-re',
            '-i', str(video_path),
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
            self.stream_url
        ]
        
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            logger.info(f"انتهى بث الفيديو: {os.path.basename(video_path)}")
            self.retry_count = 0
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"خطأ في البث: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"خطأ غير متوقع: {str(e)}")
            return False
    
    def run(self):
        """تشغيل البوت بشكل مستمر"""
        if not STREAM_KEY:
            logger.error("لم يتم العثور على مفتاح البث (YOUTUBE_STREAM_KEY)")
            return
        
        logger.info("🎬 بدء بوت البث المباشر على يوتيوب")
        logger.info(f"📁 مجلد الفيديوهات: {self.video_folder}")
        
        while True:
            try:
                videos = self.get_videos()
                
                if not videos:
                    logger.warning("لا توجد فيديوهات متاحة. جاري الانتظار...")
                    time.sleep(10)
                    continue
                
                # خلط الفيديوهات بشكل عشوائي
                random.shuffle(videos)
                
                logger.info(f"🔄 بدء دورة بث جديدة ({len(videos)} فيديو)")
                
                for video in videos:
                    if self.stream_video(str(video)):
                        logger.info(f"✅ تم بث الفيديو بنجاح")
                    else:
                        logger.warning(f"⚠️ فشل البث، جاري إعادة المحاولة...")
                        time.sleep(RECONNECT_DELAY)
                
                logger.info("🔁 انتهت الدورة، جاري بدء دورة جديدة...")
                
            except KeyboardInterrupt:
                logger.info("تم إيقاف البوت من قبل المستخدم")
                break
            except Exception as e:
                logger.error(f"خطأ في الحلقة الرئيسية: {str(e)}")
                time.sleep(RECONNECT_DELAY)

def main():
    """الدالة الرئيسية"""
    streamer = YouTubeStreamer()
    streamer.run()

if __name__ == "__main__":
    main()
