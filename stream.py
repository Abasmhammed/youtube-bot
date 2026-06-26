import os
import subprocess
import random
import time
import logging
import asyncio
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import edge_tts

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("stream.log"),
        logging.StreamHandler()
    ]
)

# YouTube RTMP URL
STREAM_URL = "rtmp://a.rtmp.youtube.com/live2/"
STREAM_KEY = os.getenv("YOUTUBE_STREAM_KEY")
VIDEO_FOLDER = "videos"

W, H = 1080, 1920
FPS  = 30

# ── Built-in motivational stories ──────────────────────────
STORIES = [
    {
        "title": "FROM ZERO TO MILLIONS",
        "lines": [
            "At age 23, he had nothing.",
            "No money. No job. No hope.",
            "He slept in his car for 6 months.",
            "Every morning he woke up and said:",
            '"Today I will not give up."',
            "He learned coding from free YouTube videos.",
            "He built an app in 90 days.",
            "First month: $12 revenue.",
            "He kept going.",
            "Month 6: $4,000.",
            "Month 12: $40,000.",
            "Year 3: $2.1 Million.",
            "The car he slept in?",
            "He bought the lot it was parked on.",
            "Your only competition is who",
            "you were yesterday.",
        ],
        "color": ("#FFD700", "#FF6B00"),
        "bg":    ("#0a0a0a", "#1a0a00"),
    },
    {
        "title": "THE 5AM DECISION",
        "lines": [
            "She was exhausted.",
            "Working 2 jobs. Raising 2 kids alone.",
            "No time. No energy. No money.",
            "One night she made a decision.",
            "5AM. Every single day.",
            "One hour just for her dreams.",
            "Day 1 was hard.",
            "Day 30 was a habit.",
            "Day 90 changed everything.",
            "She launched her business.",
            "First client came in week 2.",
            "She quit job #1 in month 4.",
            "She quit job #2 in month 8.",
            "Now she works for herself.",
            "One decision at 5AM",
            "rewrote her entire life.",
        ],
        "color": ("#00FFCC", "#0088FF"),
        "bg":    ("#000a1a", "#000a10"),
    },
    {
        "title": "THEY ALL SAID NO",
        "lines": [
            "27 investors said no.",
            "His family said stop dreaming.",
            "His friends stopped calling.",
            "He was $80,000 in debt.",
            "But he had one thing:",
            "An idea he believed in.",
            "He pitched investor #28.",
            "They said: maybe.",
            "He worked harder.",
            "Investor #28 became a yes.",
            "$500,000 funding secured.",
            "18 months later:",
            "His company hit $10M revenue.",
            "The 27 who said no?",
            "They read about him",
            "in Forbes Magazine.",
        ],
        "color": ("#FF4488", "#FF0000"),
        "bg":    ("#0a0010", "#1a0008"),
    },
    {
        "title": "THE LAST $47",
        "lines": [
            "He had $47 left in his account.",
            "Rent was due in 3 days.",
            "He could panic.",
            "Instead, he got to work.",
            "He offered a service on Fiverr.",
            "Graphic design. $5 per logo.",
            "First order came in 2 hours.",
            "He worked through the night.",
            "Made $120 by morning.",
            "He reinvested every dollar.",
            "Hired help. Scaled up.",
            "6 months later: $15,000/month.",
            "A year later: his own agency.",
            "$47 was not his end.",
            "It was his beginning.",
            "What is YOUR $47 moment?",
        ],
        "color": ("#FFFFFF", "#AAAAFF"),
        "bg":    ("#050510", "#0a0520"),
    },
    {
        "title": "99 DAYS OF REJECTION",
        "lines": [
            "He applied to 100 companies.",
            "Got rejected 99 times.",
            "Each rejection hit hard.",
            "But he studied every no.",
            "Improved his resume.",
            "Practiced his pitch.",
            "Sharpened his skills.",
            "Company #100 called back.",
            "Then flew him out.",
            "Then made an offer.",
            "$120,000 salary.",
            "Remote work. Dream role.",
            "He later said:",
            "The 99 rejections taught me",
            "more than any school ever did.",
            "Rejection is redirection.",
        ],
        "color": ("#FF9900", "#FFFF00"),
        "bg":    ("#0a0800", "#150f00"),
    },
]

QUOTES = [
    "Success is rented, not owned. Rent is due every day.",
    "The secret of getting ahead is getting started.",
    "Don't wait for the right moment. Create it.",
    "Pain is temporary. Quitting lasts forever.",
    "Your future self is watching you right now.",
    "Work in silence. Let success make the noise.",
    "Every expert was once a beginner.",
    "Rich people have big libraries. Poor people have big TVs.",
    "Discipline is choosing what you want most over what you want now.",
]

# ── Helpers ─────────────────────────────────────────────────
def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def get_font(size):
    for p in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def make_bg(top, bot):
    img = Image.new("RGB", (W, H))
    d   = ImageDraw.Draw(img)
    t   = hex_rgb(top)
    b   = hex_rgb(bot)
    for y in range(H):
        r  = t[0] + (b[0] - t[0]) * y // H
        g  = t[1] + (b[1] - t[1]) * y // H
        bv = t[2] + (b[2] - t[2]) * y // H
        d.line([(0, y), (W, y)], fill=(r, g, bv))
    return img

def draw_frame(story, line_idx, progress, frame_num):
    bg_top, bg_bot = story["bg"]
    c1, c2         = story["color"]
    img = make_bg(bg_top, bg_bot)
    d   = ImageDraw.Draw(img)

    # Top/bottom accent bars
    d.rectangle([0, 0, W, 8],       fill=hex_rgb(c1))
    d.rectangle([0, H-8, W, H],     fill=hex_rgb(c2))

    # Particles
    rng = random.Random(frame_num // 3)
    for _ in range(30):
        px = rng.randint(0, W)
        py = rng.randint(0, H)
        pr = rng.randint(1, 5)
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        od.ellipse([px, py, px+pr, py+pr], fill=hex_rgb(c1) + (rng.randint(15, 60),))
        img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
        d   = ImageDraw.Draw(img)

    # Title
    font_title = get_font(54)
    bbox = d.textbbox((0, 0), story["title"], font=font_title)
    tx   = (W - (bbox[2] - bbox[0])) // 2
    d.text((tx+3, 103), story["title"], font=font_title, fill=(0, 0, 0))
    d.text((tx,   100), story["title"], font=font_title, fill=hex_rgb(c1))

    # Story lines
    font_cur = get_font(64)
    font_old = get_font(52)
    lines    = story["lines"]
    visible  = lines[:line_idx + 1]
    start_y  = H // 2 - len(visible) * 48

    for i, line in enumerate(visible):
        for part in textwrap.fill(line, width=20).split("\n"):
            bbox2 = d.textbbox((0, 0), part, font=font_cur)
            px    = (W - (bbox2[2] - bbox2[0])) // 2
            if i == len(visible) - 1:
                d.text((px+3, start_y+3), part, font=font_cur, fill=(0, 0, 0))
                d.text((px,   start_y),   part, font=font_cur, fill=hex_rgb(c1))
            else:
                d.text((px, start_y), part, font=font_old, fill=(180, 180, 180))
            start_y += 82

    # Progress dots
    dot_r   = 10
    spacing = 28
    sx      = (W - len(lines) * spacing) // 2
    for i in range(len(lines)):
        cx = sx + i * spacing + dot_r
        cy = H - 80
        fill = hex_rgb(c1) if i <= line_idx else (50, 50, 50)
        d.ellipse([cx-dot_r, cy-dot_r, cx+dot_r, cy+dot_r], fill=fill)

    return img

# ── TTS ─────────────────────────────────────────────────────
async def _tts(text, path):
    voice = random.choice([
        "en-US-GuyNeural", "en-US-AriaNeural",
        "en-GB-RyanNeural", "en-AU-WilliamNeural",
    ])
    await edge_tts.Communicate(text, voice).save(path)

# ── Generate one video ───────────────────────────────────────
def generate_video(story):
    frames_dir = Path("tmp_frames")
    frames_dir.mkdir(exist_ok=True)
    for f in frames_dir.glob("*.png"):
        f.unlink()

    frame_idx = 0
    secs_per_line = 3

    for li, line in enumerate(story["lines"]):
        for f in range(secs_per_line * FPS):
            draw_frame(story, li, f / (secs_per_line * FPS), frame_idx).save(
                frames_dir / f"f{frame_idx:06d}.png"
            )
            frame_idx += 1

    # Quote ending
    quote_story = {**story, "title": "REMEMBER THIS", "lines": [random.choice(QUOTES)]}
    for f in range(5 * FPS):
        draw_frame(quote_story, 0, 1.0, frame_idx).save(
            frames_dir / f"f{frame_idx:06d}.png"
        )
        frame_idx += 1

    # Audio
    script     = " ".join(story["lines"]) + " " + random.choice(QUOTES)
    audio_path = "tmp_audio.mp3"
    asyncio.run(_tts(script, audio_path))

    # Encode
    safe    = story["title"].replace(" ", "_")
    out     = os.path.join(VIDEO_FOLDER, f"{safe}.mp4")
    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(frames_dir / "f%06d.png"),
        "-i", audio_path,
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart",
        out,
    ], check=True)
    logging.info(f"Video created: {out}")
    return out

def generate_all_videos():
    os.makedirs(VIDEO_FOLDER, exist_ok=True)
    for story in STORIES:
        safe = story["title"].replace(" ", "_")
        path = os.path.join(VIDEO_FOLDER, f"{safe}.mp4")
        if not os.path.exists(path):
            logging.info(f"Generating: {story['title']}")
            generate_video(story)
        else:
            logging.info(f"Already exists: {path}")

# ── Original stream functions (unchanged) ───────────────────
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
    command  = [
        'ffmpeg', '-re',
        '-i', video_path,
        '-c:v', 'libx264', '-preset', 'veryfast',
        '-maxrate', '3000k', '-bufsize', '6000k',
        '-pix_fmt', 'yuv420p', '-g', '50',
        '-c:a', 'aac', '-b:a', '128k', '-ar', '44100',
        '-f', 'flv', full_url,
    ]
    logging.info(f"Streaming: {video_path}")
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
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

    # Generate videos first if folder is empty
    generate_all_videos()

    while True:
        videos = get_videos()
        if not videos:
            logging.warning(f"No videos found in '{VIDEO_FOLDER}'. Waiting 30 seconds...")
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
