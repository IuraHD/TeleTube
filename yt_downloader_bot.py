# yt_downloader_bot.py

import logging
import os
import tempfile
import threading
import math
import time
import io
import sys
from pathlib import Path

# Check Python version first
if sys.version_info < (3, 11):
    print(f"❌ Python version error!")
    print(f"Required: Python 3.11.0")
    print(f"Found:    Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print(f"")
    print(f"📥 Please install Python 3.11.0:")
    print(f"   Download from: https://www.python.org/downloads/release/python-3110/")
    print(f"   Make sure to check 'Add Python to PATH' during installation")
    sys.exit(1)

# Third-party imports with error handling
try:
    from dotenv import load_dotenv
    from telegram import (
        Update,
        InlineKeyboardButton,
        InlineKeyboardMarkup,
        ParseMode,
    )
    from telegram.ext import (
        Updater,
        CommandHandler,
        MessageHandler,
        Filters,
        CallbackQueryHandler,
        CallbackContext,
    )
    from telegram.utils.request import Request
    from yt_dlp import YoutubeDL
except ImportError as e:
    print(f"❌ Missing required package: {e}")
    print("📦 Install required packages with:")
    print("   pip install python-telegram-bot==13.15 yt-dlp python-dotenv")
    sys.exit(1)
from yt_dlp import YoutubeDL

# Load environment variables from .env file
load_dotenv(override=True)  # Force reload environment variables from .env

# ————— CONFIG —————
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'your_bot_token_here')

# GPU Acceleration Settings
USE_GPU_ACCELERATION = True  # Enable NVIDIA GPU acceleration (NVENC)
GPU_ENCODER = "h264_nvenc"   # Options: h264_nvenc, h264_amf (AMD), h264_qsv (Intel)

# Speed vs Quality Settings
PRIORITIZE_SPEED = True      # Skip re-encoding when possible for faster processing
MAX_CONCURRENT_DOWNLOADS = 4 # Number of parallel fragment downloads

# Local Bot API Server configuration
# Set to True when using Local Bot API Server, False for standard API
USE_LOCAL_API = os.getenv('USE_LOCAL_API', 'true').lower() == 'true'  # Read from .env file
LOCAL_API_SERVER = os.getenv('LOCAL_API_SERVER', 'http://localhost:8081')  # Read from .env file

# File size limits based on API type - 1.8GB max before splitting
if USE_LOCAL_API:
    TG_MAX_FILESIZE = 2 * 1024**3  # 2 GB for Local API
    VIDEO_SIZE_LIMIT = 1.8 * 1024**3  # 1.8GB threshold for splitting
    CHUNK_SIZE = 1 * 1024**3  # 1GB chunks for local API
else:
    TG_MAX_FILESIZE = 50 * 1024**2  # 50 MB for Standard API
    VIDEO_SIZE_LIMIT = 45 * 1024**2  # 45MB threshold for splitting
    CHUNK_SIZE = 40 * 1024**2  # 40MB chunks for standard API

# ————— LOGGING —————
# Clean console output - only show important messages
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,  # Changed from DEBUG to INFO for cleaner output
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')  # Log debug info to file
    ]
)
logger = logging.getLogger(__name__)

# Set specific loggers to WARNING to reduce noise
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('apscheduler').setLevel(logging.WARNING)

# User activity logger for tracking video downloads
user_activity_logger = logging.getLogger('user_activity')
user_activity_handler = logging.FileHandler('user_activity.log', encoding='utf-8')
user_activity_formatter = logging.Formatter('%(asctime)s - %(message)s')
user_activity_handler.setFormatter(user_activity_formatter)
user_activity_logger.addHandler(user_activity_handler)
user_activity_logger.setLevel(logging.INFO)
user_activity_logger.propagate = False  # Don't send to parent logger


def log_user_activity(user_id, username, first_name, action, video_url=None, video_title=None):
    """Log user activity to dedicated user activity log file."""
    # Format username safely
    username_str = f"@{username}" if username else "No username"
    
    # Create simple log entry with just user ID, name, and link
    if action == "VIDEO_REQUEST" and video_url:
        # Clean the URL for logging (remove any sensitive parameters if needed)
        clean_url = video_url.split('&')[0] if video_url else "Unknown URL"
        log_message = f"ID: {user_id} | Name: {first_name} | Username: {username_str} | Link: {clean_url}"
        
        # Log to user activity file
        user_activity_logger.info(log_message)


# session store: chat_id → {url, info, choices, cancel_flag, status_msg_id}
_sessions = {}

# yt-dlp metadata-only
YDL_OPTS_INFO = {
    'format': 'best',
    'noplaylist': True,
    'quiet': True,
    'skip_download': True,
    'ffmpeg_location': os.path.join(os.getcwd(), 'ffmpeg', 'ffmpeg.exe'),
}


def get_ios_safe_emoji(standard_emoji, safe_alternative):
    """Return iOS-safe emoji alternative if iOS_SAFE_MODE is enabled."""
    # For now, always return the standard emoji since iOS_SAFE_MODE is not defined
    return standard_emoji


def get_aspect_ratio_info(width, height):
    """Determine aspect ratio and return display info."""
    if not width or not height:
        return "Unknown", "📐"
    
    # Calculate aspect ratio
    ratio = width / height
    
    # Common aspect ratios with tolerances
    if abs(ratio - 16/9) < 0.1:
        return "16:9 (Widescreen)", "📺"
    elif abs(ratio - 4/3) < 0.1:
        return "4:3 (Standard)", "📱"
    elif abs(ratio - 1/1) < 0.1:
        return "1:1 (Square)", "⬜"
    elif abs(ratio - 21/9) < 0.1:
        return "21:9 (Ultrawide)", "📽️"
    elif abs(ratio - 9/16) < 0.1:
        return "9:16 (Vertical)", "📲"
    elif ratio > 2:
        return f"{ratio:.1f}:1 (Wide)", "📐"
    elif ratio < 0.7:
        return f"1:{1/ratio:.1f} (Tall)", "📐"
    else:
        return f"{ratio:.1f}:1", "📐"


def get_gpu_encoder_settings():
    """Get GPU encoder settings based on available hardware."""
    if not USE_GPU_ACCELERATION:
        return None
    
    # Try to detect available GPU encoders
    encoders = {
        'nvidia': 'h264_nvenc',    # NVIDIA NVENC
        'amd': 'h264_amf',         # AMD AMF
        'intel': 'h264_qsv'        # Intel Quick Sync
    }
    
    # For now, return NVIDIA settings (most common)
    # This could be enhanced to auto-detect hardware
    return {
        'video_codec': GPU_ENCODER,
        'preset': 'fast',          # fast, medium, slow
        'cq': '23',               # Constant Quality (lower = better quality)
        'gpu_args': [
            '-c:v', GPU_ENCODER,
            '-preset', 'fast',
            '-cq', '23',
            '-profile:v', 'main',
            '-level:v', '4.0',
            '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart'
        ]
    }


def build_quality_keyboard(choices, audio_streams):
    """Build the quality selection keyboard with consistent formatting."""
    # Find best audio for size calculation
    best_audio = sorted(audio_streams, key=lambda x: (x.get('abr') or 0), reverse=True)[0] if audio_streams else None
    
    keyboard = []
    for idx, f in enumerate(choices):
        h = f.get('height') or 0
        w = f.get('width') or 0
        
        # Quality indicator
        if h >= 2160:
            quality_emoji = "🌟"  # 4K
        elif h >= 1440:
            quality_emoji = "💎"  # 2K
        elif h >= 1080:
            quality_emoji = "✨"  # Full HD
        elif h >= 720:
            quality_emoji = "⭐"  # HD
        else:
            quality_emoji = "📱"  # SD
            
        # Get aspect ratio info
        aspect_name, aspect_emoji = get_aspect_ratio_info(w, h)
        
        # Size information with better estimation
        size = f.get('filesize')
        estimated_size = size
        
        # For adaptive streams, add the size of the best audio to give a more accurate estimate
        is_progressive = f.get('acodec') and f.get('acodec') != 'none'
        if not is_progressive and best_audio and best_audio.get('filesize'):
            if size:
                estimated_size = size + best_audio.get('filesize')
            else:
                # Estimate based on duration and bitrate if no file size available
                duration = f.get('duration') or 0
                video_bitrate = f.get('vbr') or f.get('tbr') or 0
                audio_bitrate = best_audio.get('abr') or 128
                if duration and video_bitrate:
                    estimated_size = int((video_bitrate + audio_bitrate) * duration * 1000 / 8)  # Convert to bytes
        elif not size and not is_progressive:
            # Fallback estimation for adaptive streams without size info
            duration = f.get('duration') or 0
            video_bitrate = f.get('vbr') or f.get('tbr') or 0
            if duration and video_bitrate:
                estimated_size = int((video_bitrate + 128) * duration * 1000 / 8)  # Assume 128k audio

        # Show resolution and size - simplified for parsing safety
        if estimated_size:
            size_mb = estimated_size / (1024**2)
            if size_mb >= 1024:
                size_text = f" • {size_mb/1024:.1f}GB"
            else:
                size_text = f" • {size_mb:.0f}MB"
        else:
            size_text = " • Size unknown"
        
        # Get codec information for better quality indication
        vcodec = f.get('vcodec', '').lower()
        codec_info = ""
        if 'avc1' in vcodec or 'h264' in vcodec:
            codec_info = " H.264"
        elif 'vp9' in vcodec:
            codec_info = " VP9"
        elif 'av01' in vcodec:
            codec_info = " AV1"
        
        # Simple button text without complex aspect ratio strings
        button_text = f"{quality_emoji} {h}p{codec_info}{size_text}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=str(idx))])
    
    return keyboard


def clean_title(text):
    """Clean title by removing slashes, dashes and other unwanted characters for safe display."""
    if not text:
        return ""
    # Remove forward and backward slashes, dashes and other problematic characters
    text = text.replace('/', '').replace('\\', '').replace('-', '')
    # Remove other potentially problematic characters for clean display
    text = text.replace('|', '').replace('[', '').replace(']', '')
    # Clean up extra spaces
    text = ' '.join(text.split())
    return text


def safe_caption(text):
    """Create a safe caption for Telegram uploads by cleaning and escaping."""
    if not text:
        return ""
    # First clean the title
    clean_text = clean_title(text)
    # For captions, we don't use markdown formatting to avoid escaping issues
    # Just return clean text without any markdown
    return clean_text


def escape_markdown(text):
    """Escape markdown special characters in text."""
    if not text:
        return ""
    # More comprehensive markdown escaping
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!', '\\']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text


def upload_with_progress(bot, chat_id, file_path, upload_type='video', caption=None, 
                        progress_callback=None, timeout=None, session=None, status_msg_id=None, **kwargs):
    """Upload file with simulated progress tracking."""
    
    file_size = os.path.getsize(file_path)
    file_size_mb = file_size / (1024**2)
    
    # Simulate upload progress with realistic timing
    def simulate_upload_progress():
        """Simulate realistic upload progress based on file size."""
        # Estimate upload time based on file size (assuming ~1-5 MB/s upload speed)
        estimated_time = max(5, file_size_mb / 2)  # At least 5 seconds, ~2 MB/s avg
        
        progress_steps = [5, 10, 15, 25, 35, 45, 55, 65, 75, 85, 90, 95]
        step_interval = estimated_time / len(progress_steps)
        
        for i, progress in enumerate(progress_steps):
            if session and session.get('cancel', False):
                return
                
            # Calculate timing - slower start, faster in middle, slower at end
            if i < 3:  # First 3 steps slower (connection setup)
                delay = step_interval * 1.5
            elif i > len(progress_steps) - 3:  # Last 3 steps slower (finalizing)
                delay = step_interval * 1.3
            else:  # Middle steps faster
                delay = step_interval * 0.8
            
            time.sleep(delay)
            
            if progress_callback:
                bytes_uploaded = int((progress / 100) * file_size)
                progress_callback(bytes_uploaded, file_size, progress)
    
    # Start progress simulation in a separate thread
    if progress_callback:
        progress_thread = threading.Thread(target=simulate_upload_progress)
        progress_thread.daemon = True
        progress_thread.start()
    
    try:
        # Perform actual upload
        with open(file_path, 'rb') as f:
            if upload_type == 'video':
                # Get video metadata for enhanced upload
                width = kwargs.get('width')
                height = kwargs.get('height') 
                duration = kwargs.get('duration')
                
                result = bot.send_video(
                    chat_id=chat_id,
                    video=f,
                    width=width,
                    height=height,
                    duration=duration,
                    caption=caption,
                    supports_streaming=True,
                    timeout=timeout
                )
            elif upload_type == 'document':
                result = bot.send_document(
                    chat_id=chat_id,
                    document=f,
                    caption=caption,
                    timeout=timeout
                )
            else:
                raise ValueError(f"Unsupported upload type: {upload_type}")
        
        # Show 100% completion
        if progress_callback:
            progress_callback(file_size, file_size, 100)
            
        return result
        
    except Exception as e:
        # Stop progress thread on error
        if session:
            session['cancel'] = True
        raise e


def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    username = update.effective_user.username or "No username"
    first_name = update.effective_user.first_name or "Unknown"
    
    # Store user info in context for later use
    context.user_data['user_info'] = {
        'username': username,
        'first_name': first_name,
        'chat_id': chat_id
    }
    
    # Console log for user action
    print(f"🔥 USER ACTION: {first_name} (@{username}) [ID: {chat_id}] started the bot")
    logger.info(f"User {first_name} (@{username}) [ID: {chat_id}] started the bot")
    
    # Calculate file size limit text based on current API mode
    file_limit = TG_MAX_FILESIZE / (1024**2 if not USE_LOCAL_API else 1024**3)
    limit_unit = 'MB' if not USE_LOCAL_API else 'GB'
    api_mode_text = '🏠 Local Bot API (2GB support)' if USE_LOCAL_API else '☁️ Standard Bot API (50MB limit)'
    size_threshold = "1.8GB" if USE_LOCAL_API else "45MB"
    
    # Get GPU status for welcome message
    gpu_status = "⚡ GPU acceleration" if USE_GPU_ACCELERATION else "🔄 CPU processing"
    
    welcome_text = f"""🎬 **YouTube Video Downloader**

📋 **How to use:**
1️⃣ Send me any YouTube link
2️⃣ Choose quality (up to 4K!)
3️⃣ Download & enjoy! 

� **Just paste a YouTube link to start!**"""
    update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)


def handle_link(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    username = update.effective_user.username or "No username"
    first_name = update.effective_user.first_name or "Unknown"
    url = update.message.text.strip()
    
    # Store user info in context for later use
    context.user_data['user_info'] = {
        'username': username,
        'first_name': first_name,
        'chat_id': chat_id
    }
    
    # Console log for user action
    print(f"🔗 USER ACTION: {first_name} (@{username}) [ID: {chat_id}] sent YouTube URL: {url[:50]}{'...' if len(url) > 50 else ''}")
    logger.info(f"User {first_name} (@{username}) [ID: {chat_id}] sent URL: {url}")

    # Log video request to user activity file
    log_user_activity(chat_id, username, first_name, "VIDEO_REQUEST", video_url=url)
    
    if not url.startswith(("http://", "https://")):
        return update.message.reply_text(
            "❌ **Invalid URL**\n\n"
            "Please send me a valid YouTube link that starts with `http://` or `https://`\n\n"
            "Example: `https://www.youtube.com/watch?v=...`",
            parse_mode=ParseMode.MARKDOWN
        )

    # Send "processing" message first
    print(f"📊 STATUS: {first_name} (@{username}) - Analyzing video metadata...")
    processing_msg = update.message.reply_text("🔍 **Getting video info...**", parse_mode=ParseMode.MARKDOWN)
    
    try:
        with YoutubeDL(YDL_OPTS_INFO) as ydl:
            info = ydl.extract_info(url, download=False)
        title = info.get('title', 'video')
        duration = info.get('duration', 0)
        uploader = info.get('uploader', 'Unknown')
        print(f"✅ SUCCESS: {first_name} (@{username}) - Video metadata fetched: '{title[:30]}{'...' if len(title) > 30 else ''}' by {uploader}")
        logger.debug("Fetched metadata: %s", title)
    except Exception:
        print(f"❌ ERROR: {first_name} (@{username}) - Failed to fetch video info for: {url[:50]}{'...' if len(url) > 50 else ''}")
        logger.exception("Failed to extract info")
        processing_msg.edit_text(
            "❌ **Can't get video info**\n\nPlease check the link and try again.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # Filter for video streams with iOS compatibility priority
    video_streams = [
        f for f in info['formats']
        if f.get('vcodec') != 'none'  # has video
           and f.get('height')  # has resolution
           and f.get('ext') in ['mp4', 'webm']  # supported video formats
    ]
    
    # Prioritize H.264 codec and specific profiles for Telegram + iOS compatibility
    # Look for H.264 Main/Baseline profiles which are most compatible
    # Also prioritize progressive (single-file) streams for better Telegram streaming
    telegram_compatible_streams = []
    h264_progressive_streams = []
    h264_adaptive_streams = []
    other_progressive_streams = []
    other_adaptive_streams = []
    
    for f in video_streams:
        vcodec = f.get('vcodec', '').lower()
        is_progressive = f.get('acodec') != 'none'  # Has both video and audio
        
        if 'avc1' in vcodec or 'h264' in vcodec:
            # Check for Telegram/iOS-friendly profiles (best compatibility)
            if ('main' in vcodec or 'baseline' in vcodec or 
                'avc1.42' in vcodec or 'avc1.4d' in vcodec):
                if is_progressive:
                    telegram_compatible_streams.append(f)
                else:
                    h264_adaptive_streams.append(f)
            else:
                if is_progressive:
                    h264_progressive_streams.append(f)
                else:
                    h264_adaptive_streams.append(f)
        else:
            if is_progressive:
                other_progressive_streams.append(f)
            else:
                other_adaptive_streams.append(f)
    
    # Reorder streams for optimal Telegram compatibility:
    # 1. Telegram-compatible H.264 progressive (best for streaming)
    # 2. Other H.264 progressive 
    # 3. H.264 adaptive (requires merging but good codec)
    # 4. Other progressive formats
    # 5. Other adaptive formats (fallback)
    video_streams = (telegram_compatible_streams + h264_progressive_streams + 
                    h264_adaptive_streams + other_progressive_streams + other_adaptive_streams)
    
    # Add audio-only streams to calculate total size for adaptive formats
    audio_streams = [f for f in info['formats'] if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
    best_audio = sorted(audio_streams, key=lambda x: (x.get('abr') or 0), reverse=True)[0] if audio_streams else None

    if not video_streams:
        print(f"❌ ERROR: {first_name} (@{username}) - No video streams found for: {title[:30]}{'...' if len(title) > 30 else ''}")
        processing_msg.edit_text(
            "❌ **No video found**\n\nTry a different video.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # group by resolution and pick best quality for each (prioritize H.264 and no re-encoding needed)
    unique = {}
    for f in video_streams:
        h = f.get('height')
        if h not in unique:
            unique[h] = f
        else:
            # prefer higher quality with these priorities:
            # 1. H.264 codec (no conversion needed)
            # 2. Progressive streams (no merging needed)
            # 3. Higher resolution/bitrate
            # 4. Larger file size
            current = unique[h]
            
            # Check if current format is better
            current_vcodec = current.get('vcodec', '').lower()
            new_vcodec = f.get('vcodec', '').lower()
            
            current_is_h264 = 'avc1' in current_vcodec or 'h264' in current_vcodec
            new_is_h264 = 'avc1' in new_vcodec or 'h264' in new_vcodec
            
            current_is_progressive = current.get('acodec') and current.get('acodec') != 'none'
            new_is_progressive = f.get('acodec') and f.get('acodec') != 'none'
            
            # Prioritize H.264 streams
            if new_is_h264 and not current_is_h264:
                unique[h] = f
            elif current_is_h264 and not new_is_h264:
                continue  # Keep current
            # If both or neither are H.264, prioritize progressive
            elif new_is_progressive and not current_is_progressive:
                unique[h] = f
            elif current_is_progressive and not new_is_progressive:
                continue  # Keep current
            # If same codec and progressive status, prefer higher quality
            elif (f.get('width', 0) * f.get('height', 0) > current.get('width', 0) * current.get('height', 0) or
                  (f.get('vbr') or f.get('tbr') or 0) > (current.get('vbr') or current.get('tbr') or 0) or
                  (f.get('filesize') or 0) > (current.get('filesize') or 0)):
                unique[h] = f
    
    choices = sorted(unique.values(), key=lambda x: x.get('height') or 0, reverse=True)

    print(f"🎯 QUALITY OPTIONS: {first_name} (@{username}) - {len(choices)} quality options available for '{title[:30]}{'...' if len(title) > 30 else ''}'")

    _sessions[chat_id] = {
        'url': url,
        'info': info,
        'choices': choices,
        'cancel': False,
        'status_msg_id': None,
        'split_mode': False,
    }

    # build inline keyboard using the reusable function
    keyboard = build_quality_keyboard(choices, audio_streams)

    # Format duration
    if duration:
        mins, secs = divmod(duration, 60)
        hours, mins = divmod(mins, 60)
        if hours:
            duration_str = f"{hours:02d}:{mins:02d}:{secs:02d}"
        else:
            duration_str = f"{mins:02d}:{secs:02d}"
    else:
        duration_str = "Unknown"

    # Create video info message
    clean_full_title = clean_title(title)
    safe_title = escape_markdown(clean_full_title)
    safe_uploader = escape_markdown(uploader)
    
    video_info = f"""📺 **{safe_title}**

👤 {safe_uploader} • ⏱️ {duration_str}

🎯 **Choose quality:**"""

    processing_msg.edit_text(
        video_info,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )


def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    chat_id = query.message.chat.id
    username = query.from_user.username or "No username"
    first_name = query.from_user.first_name or "Unknown"
    data = query.data
    query.answer()

    # Cancel button pressed
    if data == 'cancel':
        print(f"🛑 USER ACTION: {first_name} (@{username}) [ID: {chat_id}] canceled download")
        session = _sessions.get(chat_id)
        if session:
            session['cancel'] = True
            try:
                context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=session['status_msg_id'],
                    text="❌ **Download Canceled**\n\nYour download has been stopped and files cleaned up.",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=None
                )
            except:
                context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ **Download Canceled**\n\nYour download has been stopped.",
                    parse_mode=ParseMode.MARKDOWN
                )
        return

    # Back button pressed (return to quality selection)
    if data == 'back':
        print(f"🔙 USER ACTION: {first_name} (@{username}) [ID: {chat_id}] went back to quality selection")
        session = _sessions.get(chat_id)
        if not session:
            return query.edit_message_text(
                "⏰ **Session expired**\n\nSend a YouTube link again.",
                parse_mode=ParseMode.MARKDOWN
            )
        
        # Rebuild quality selection using reusable function
        choices = session['choices']
        audio_streams = [f for f in session['info']['formats'] if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
        keyboard = build_quality_keyboard(choices, audio_streams)

        return query.edit_message_text(
            "🎯 **Choose your preferred quality:**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )

    # Split file option
    if data.startswith('split_'):
        idx = int(data.split('_')[1])
        print(f"📦 USER ACTION: {first_name} (@{username}) [ID: {chat_id}] chose to split large file")
        session = _sessions.get(chat_id)
        if not session:
            return query.edit_message_text(
                "⏰ **Session expired**\n\nSend a YouTube link again.",
                parse_mode=ParseMode.MARKDOWN
            )

        url = session['url']
        info = session['info']
        choice = session['choices'][idx]
        title = info.get('title', 'video')
        h = choice.get('height') or 0

        print(f"🚀 DOWNLOAD START: {first_name} (@{username}) [ID: {chat_id}] - {h}p quality (SPLIT MODE) for '{clean_title(title)[:30]}{'...' if len(clean_title(title)) > 30 else ''}'")

        # Remove the split selection keyboard from the original message  
        clean_full_title = clean_title(title)
        safe_title_display = escape_markdown(f"📺 {clean_full_title}")
        query.edit_message_text(
            f"✅ **{safe_title_display}**\n\n📺 **{h}p** quality selected (Split Mode)",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=None
        )

        # send initial status with Cancel button
        status = context.bot.send_message(
            chat_id=chat_id,
            text=f"🚀 **Starting Download (Split Mode)**\n\n📺 Quality: **{h}p**\n📦 Will be split into parts\n📊 Preparing download...",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]),
            parse_mode=ParseMode.MARKDOWN
        )
        session['status_msg_id'] = status.message_id
        session['split_mode'] = True

        # perform download in separate thread to avoid blocking
        threading.Thread(target=_download_and_send, args=(chat_id, choice, url, title, h, context, username, first_name)).start()
        return

    # Quality selection
    idx = int(data)
    print(f"🎯 USER ACTION: {first_name} (@{username}) [ID: {chat_id}] selected quality option #{idx}")
    session = _sessions.get(chat_id)
    if not session:
        return query.edit_message_text(
            "⏰ **Session expired**\n\nSend a YouTube link again.",
            parse_mode=ParseMode.MARKDOWN
        )

    url = session['url']
    info = session['info']
    choice = session['choices'][idx]
    title = info.get('title', 'video')
    h = choice.get('height') or 0
    
    # Recalculate size including audio for adaptive streams
    size = choice.get('filesize') or 0
    is_progressive = choice.get('acodec') and choice.get('acodec') != 'none'
    if not is_progressive:
        audio_streams = [f for f in info['formats'] if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
        best_audio = sorted(audio_streams, key=lambda x: (x.get('abr') or 0), reverse=True)[0] if audio_streams else None
        if best_audio and best_audio.get('filesize'):
            size += best_audio.get('filesize')

    # Check if file needs splitting (>1.8GB for Local API, >45MB for Standard API)
    video_size_limit = VIDEO_SIZE_LIMIT
    if size and size > video_size_limit:
        size_gb = size / (1024**3)
        num_parts = math.ceil(size / video_size_limit)
        
        limit_text = "1.8GB" if USE_LOCAL_API else "45MB"
        
        # Create keyboard with split option
        keyboard = [
            [InlineKeyboardButton(f"📦 Split into {num_parts} parts", callback_data=f"split_{idx}")],
            [InlineKeyboardButton("🔙 Choose different quality", callback_data="back")]
        ]
        
        return query.edit_message_text(
            f"⚠️ **Large File - Will Be Split**\n\n"
            f"📺 **{h}p** video is **{size_gb:.1f}GB**\n\n"
            f"📦 **Will split into {num_parts} parts**\n"
            f"💡 Each part under {limit_text}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )

    print(f"🚀 DOWNLOAD START: {first_name} (@{username}) [ID: {chat_id}] - {h}p quality for '{clean_title(title)[:30]}{'...' if len(clean_title(title)) > 30 else ''}'")

    # Remove the quality selection keyboard from the original message
    clean_full_title = clean_title(title)
    safe_title_display = escape_markdown(f"📺 {clean_full_title}")
    query.edit_message_text(
        f"✅ **{safe_title_display}**\n\n📺 **{h}p** quality selected",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=None
    )

    # send initial status with Cancel button
    status = context.bot.send_message(
        chat_id=chat_id,
        text=f"🚀 **Starting Download**\n\n📺 Quality: **{h}p**",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]),
        parse_mode=ParseMode.MARKDOWN
    )
    session['status_msg_id'] = status.message_id
    session['split_mode'] = False

    # perform download in separate thread to avoid blocking
    threading.Thread(target=_download_and_send, args=(chat_id, choice, url, title, h, context, username, first_name)).start()


def _download_and_send(chat_id, choice, url, title, h, context: CallbackContext, username="Unknown", first_name="Unknown"):
    print(f"📥 DOWNLOAD THREAD: {first_name} (@{username}) [ID: {chat_id}] - Starting download thread for {h}p quality")
    
    session = _sessions.get(chat_id)
    if not session:
        print(f"❌ ERROR: {first_name} (@{username}) [ID: {chat_id}] - Session not found")
        return
    
    # Get video info and audio streams from session
    info = session.get('info', {})
    audio_streams = [f for f in info.get('formats', []) if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
    best_audio = sorted(audio_streams, key=lambda x: (x.get('abr') or 0), reverse=True)[0] if audio_streams else None
    
    # Create a dedicated download directory to avoid temp folder pollution
    download_dir = os.path.join(os.getcwd(), 'downloads')
    os.makedirs(download_dir, exist_ok=True)
    
    # Clean any existing files in download directory
    for f in os.listdir(download_dir):
        file_path = os.path.join(download_dir, f)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.debug(f"Could not remove {file_path}: {e}")
    
    before = set(os.listdir(download_dir))

    def progress_hook(d):
        if session.get('cancel', False):
            print(f"🛑 DOWNLOAD CANCELED: {first_name} (@{username}) [ID: {chat_id}] - User canceled download")
            raise Exception("Download canceled by user")
        
        status = d.get('status', '')
        logger.debug(f"Progress hook called with status: {status}")
        
        if status == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            speed = d.get('speed', 0)
            
            if total > 0:
                pct = (downloaded / total) * 100
                # Log progress every 10% for major milestones
                if int(pct) % 20 == 0 and int(pct) > 0:
                    print(f"📊 DOWNLOAD PROGRESS: {first_name} (@{username}) [ID: {chat_id}] - {pct:.0f}% complete ({downloaded/(1024**2):.1f}MB/{total/(1024**2):.1f}MB)")
                
                # Create progress bar (iOS-compatible characters)
                bar_length = 20
                filled_length = int(bar_length * pct // 100)
                bar = "=" * filled_length + "-" * (bar_length - filled_length)
                
                # Speed formatting
                if speed:
                    if speed > 1024*1024:
                        speed_text = f"{speed/(1024*1024):.1f} MB/s"
                    elif speed > 1024:
                        speed_text = f"{speed/1024:.1f} KB/s"
                    else:
                        speed_text = f"{speed:.0f} B/s"
                else:
                    speed_text = "Unknown speed"
                
                try:
                    # Create animated progress bar for download
                    bar_length = 18
                    filled_length = int(bar_length * pct // 100)
                    
                    # Use different characters for a more dynamic look
                    if pct < 100:
                        bar = "█" * filled_length + "▓" + "░" * (bar_length - filled_length - 1)
                    else:
                        bar = "█" * bar_length
                    
                    progress_text = f"⬇️ **Downloading {h}p**\n\n" \
                                  f"📊 Progress: **{pct:.1f}%**\n" \
                                  f"📁 Downloaded: {downloaded/(1024**2):.1f}MB / {total/(1024**2):.1f}MB\n" \
                                  f"⬇️ `{bar}`\n" \
                                  f"🚀 Speed: {speed_text}"
                    
                    context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=session['status_msg_id'],
                        text=progress_text,
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]),
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception as e:
                    logger.debug(f"Failed to update progress: {e}")
                    pass
        elif status == 'finished':
            print(f"✅ DOWNLOAD COMPLETE: {first_name} (@{username}) [ID: {chat_id}] - Download finished, starting processing...")
            logger.debug("Download finished, starting processing...")
            try:
                completion_text = f"✅ **Download Complete!**\n\n📺 Quality: **{h}p**\n🔄 Processing file..."
                context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=session['status_msg_id'],
                    text=completion_text,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]),
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.debug(f"Failed to update completion status: {e}")
        elif status == 'error':
            print(f"❌ DOWNLOAD ERROR: {first_name} (@{username}) [ID: {chat_id}] - {d.get('error', 'Unknown error')}")
            logger.error(f"Download error: {d.get('error', 'Unknown error')}")
        else:
            logger.debug(f"Other status: {status} - {d}")

    # Check if the selected format is progressive (has audio) or needs merging
    is_progressive = choice.get('acodec') and choice['acodec'] != 'none'
    
    # Get video dimensions for aspect ratio preservation
    width = choice.get('width', 0)
    height = choice.get('height', 0)
    aspect_name, aspect_emoji = get_aspect_ratio_info(width, height)
    
    # Prefer formats that don't need post-processing
    vcodec = choice.get('vcodec', '').lower()
    needs_conversion = not ('avc1' in vcodec or 'h264' in vcodec or choice.get('ext') == 'mp4')
    
    # Get GPU encoder settings
    gpu_settings = get_gpu_encoder_settings()
    
    if is_progressive:
        format_string = f"{choice['format_id']}"
        merging_text = f"✅ Video has audio, no merging needed"
    else:
        # Prioritize iOS-compatible audio formats with exact quality matching
        best_audio_format = None
        if best_audio:
            best_audio_format = best_audio.get('format_id')
        
        if best_audio_format:
            format_string = f"{choice['format_id']}+{best_audio_format}"
        else:
            format_string = f"{choice['format_id']}+bestaudio[ext=m4a]/bestaudio[ext=aac]/bestaudio"
        merging_text = f"🎵 Merging video with high-quality audio..."

    # Build FFmpeg arguments optimized specifically for Telegram's video player
    # Based on official Telegram Bot API documentation requirements
    
    # Calculate proper dimensions and aspect ratio for Telegram
    if width and height:
        # Ensure dimensions are even numbers (required for H.264 encoding)
        if width % 2 != 0:
            width = width - 1
        if height % 2 != 0:
            height = height - 1
        
        # Telegram video specifications (from Bot API docs):
        # - MPEG4 format (MP4 container) 
        # - H.264 codec preferred for maximum compatibility
        # - supports_streaming=True for inline playback
        # - Preserves any aspect ratio (no restrictions in API)
        # - Optimized for mobile and desktop players
        
        # Advanced video filter chain for optimal Telegram playback
        # 1. Scale with aspect ratio preservation + even dimensions
        # 2. Set proper Sample Aspect Ratio (SAR) for pixel-perfect display
        # 3. Ensure color matrix for consistent playback across devices
        telegram_vf = (f'scale={width}:{height}:force_original_aspect_ratio=decrease:'
                      f'force_divisible_by=2,setsar=1:1,colormatrix=bt709:bt709')
    else:
        # Fallback for unknown dimensions - use adaptive HD resolution
        # 16:9 aspect ratio is most common and well-supported
        telegram_vf = ('scale=1280:720:force_original_aspect_ratio=decrease:'
                      'force_divisible_by=2,setsar=1:1,colormatrix=bt709:bt709')
        width, height = 1280, 720
    
    # Telegram-optimized encoding settings based on Bot API requirements
    if gpu_settings and (needs_conversion or not is_progressive):
        # GPU acceleration with Telegram streaming optimization
        ffmpeg_args = [
            # Video codec settings for maximum Telegram compatibility
            '-c:v', GPU_ENCODER,         # Hardware encoder (h264_nvenc/amf/qsv)
            '-preset', 'fast',           # Balanced speed/quality for streaming
            '-cq', '23',                 # Good quality for streaming (lower than 28 default)
            '-profile:v', 'main',        # H.264 Main profile (widely supported)
            '-level:v', '4.0',           # H.264 Level 4.0 (standard compatibility)
            
            # Audio codec settings optimized for Telegram
            '-c:a', 'aac',               # AAC audio (Telegram standard, iOS/Android compatible)
            '-b:a', '128k',              # Standard audio bitrate for good quality/size ratio
            '-ar', '44100',              # Standard sample rate (44.1kHz)
            '-ac', '2',                  # Stereo audio (most compatible)
            
            # Container and streaming optimization for Telegram player
            '-f', 'mp4',                 # MP4 container (MPEG4 format required by Telegram)
            '-movflags', '+faststart+rtphint',  # Enhanced streaming: metadata first + RTP hints
            '-fflags', '+genpts+igndts', # Generate timestamps + ignore DTS for better seeking
            
            # Pixel format and color settings for optimal display
            '-pix_fmt', 'yuv420p',       # YUV 4:2:0 (maximum compatibility across all devices)
            '-colorspace', 'bt709',      # Standard HD color space
            '-color_primaries', 'bt709', # Standard color primaries
            '-color_trc', 'bt709',       # Standard transfer characteristics
            '-color_range', 'tv',        # TV range (16-235) for better mobile compatibility
            
            # Video filters for Telegram player optimization
            '-vf', telegram_vf,
            
            # Container metadata for enhanced compatibility
            '-brand', 'mp42',            # MP4 version 2 brand (better compatibility)
            '-metadata:s:v:0', 'rotate=0',  # Ensure no rotation metadata
            '-metadata', 'creation_time=now',  # Add creation timestamp
            
            # Additional streaming optimizations
            '-avoid_negative_ts', 'make_zero',  # Avoid negative timestamps
            '-max_muxing_queue_size', '1024',   # Larger muxing queue for stability
        ]
        processing_method = f"⚡ GPU-accelerated ({GPU_ENCODER}) - Telegram player optimized"
    else:
        # CPU encoding with enhanced Telegram player optimization
        ffmpeg_args = [
            # Video codec settings for maximum Telegram compatibility  
            '-c:v', 'libx264',           # Software H.264 encoder
            '-preset', 'fast',           # Balanced preset for good speed/quality
            '-crf', '23',                # Constant Rate Factor for good quality
            '-profile:v', 'main',        # H.264 Main profile (best compatibility)
            '-level:v', '4.0',           # H.264 Level 4.0 (standard compatibility)
            '-tune', 'film',             # Optimize for film content (better for videos)
            
            # Audio codec settings optimized for Telegram
            '-c:a', 'aac',               # AAC audio codec (Telegram/mobile standard)
            '-b:a', '128k',              # Audio bitrate for good quality
            '-ar', '44100',              # Sample rate (44.1kHz standard)
            '-ac', '2',                  # Stereo audio channels
            
            # Container and streaming optimization for Telegram player
            '-f', 'mp4',                 # MP4 container format (required)
            '-movflags', '+faststart+rtphint',  # Enhanced streaming optimization
            '-fflags', '+genpts+igndts', # Generate timestamps for better seeking
            
            # Pixel format and color settings for optimal display
            '-pix_fmt', 'yuv420p',       # Standard pixel format (universal compatibility)
            '-colorspace', 'bt709',      # HD color space
            '-color_primaries', 'bt709', # Standard color primaries  
            '-color_trc', 'bt709',       # Standard transfer characteristics
            '-color_range', 'tv',        # TV range for mobile compatibility
            
            # Video filters for Telegram player optimization
            '-vf', telegram_vf,
            
            # Container metadata for enhanced compatibility
            '-brand', 'mp42',            # MP4 brand for better compatibility
            '-metadata:s:v:0', 'rotate=0',  # No rotation metadata
            '-metadata', 'creation_time=now',  # Creation timestamp
            
            # Additional optimizations for smooth playback
            '-avoid_negative_ts', 'make_zero',  # Clean timestamps
            '-max_muxing_queue_size', '1024',   # Stable muxing
            '-x264opts', 'keyint=50:min-keyint=25',  # Keyframe every 2 seconds for better seeking
        ]
        processing_method = f"🔄 CPU encoding - Telegram player optimized"

    ydl_opts = {
        'format': format_string,
        'outtmpl': os.path.join(download_dir, 'video.%(ext)s'),  # Simple filename to avoid issues
        'noplaylist': True,
        'quiet': True,  # Reduce yt-dlp output noise
        'no_warnings': False,  # Show warnings
        'progress_hooks': [progress_hook],
        'merge_output_format': 'mp4',  # ensure final output is MP4
        'restrictfilenames': True,  # Use only ASCII characters in filenames
        'windowsfilenames': True,  # Use Windows-safe filenames
        'ffmpeg_location': os.path.join(os.getcwd(), 'ffmpeg', 'ffmpeg.exe'),  # Use local ffmpeg
        # Remove post-processors that might cause file locking issues
        'writesubtitles': False,
        'writeautomaticsub': False,
        'writethumbnail': False,
        'overwrites': True,  # Overwrite existing files
        # Optimized post-processors for speed and quality with Telegram compatibility
        'postprocessors': [
            {
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            },
            {
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            }
        ] if (needs_conversion and not PRIORITIZE_SPEED) else [
            {
                'key': 'FFmpegMetadata', 
                'add_metadata': True,
            }
        ],
        # Optimized FFmpeg options for speed and quality preservation with Telegram compatibility
        'postprocessor_args': {
            'default': ffmpeg_args + [
                '-metadata:s:v:0', f'rotate=0',  # Ensure no rotation metadata
                '-metadata', f'creation_time=now',  # Add creation time
                '-metadata', f'title={clean_title(title)[:50]}',  # Add cleaned video title metadata
            ] if width and height else ffmpeg_args
        } if (needs_conversion or not is_progressive) and not PRIORITIZE_SPEED else {
            'default': [
                '-c', 'copy',  # Copy streams without re-encoding when possible
                '-metadata:s:v:0', f'rotate=0',  # Ensure no rotation metadata
                '-movflags', '+faststart+rtphint',  # Enhanced streaming for Telegram
                '-avoid_negative_ts', 'make_zero',  # Clean timestamps
            ]
        },
        # Additional speed optimizations for faster processing
        'concurrent_fragment_downloads': MAX_CONCURRENT_DOWNLOADS,  # Download fragments in parallel
        'buffersize': 32768,  # 32KB buffer size (increased for better performance)
        'http_chunk_size': 10485760,  # 10MB chunks for faster download
        
        # Telegram-optimized quality settings
        'format_selector': None,
        'extractaudio': False,
        'audioformat': 'aac',        # AAC is preferred by Telegram
        'embed_subs': False,
        'writesubtitles': False,
        'writeautomaticsub': False,
        
        # Metadata handling optimized for Telegram
        'add_metadata': True,
        'embed_thumbnail': False,    # Skip thumbnail embedding for faster processing
        'writeinfojson': False,      # Skip JSON metadata files for speed
        'ignoreerrors': False,       # Don't ignore errors
        
        # Network optimization for better download speed
        'socket_timeout': 30,        # 30 second socket timeout
        'retries': 3,               # Retry failed downloads 3 times
    }

    out_file = None
    try:
        # Log processing details
        vcodec = choice.get('vcodec', '').lower()
        codec_type = "H.264" if ('avc1' in vcodec or 'h264' in vcodec) else "Other"
        will_reencode = needs_conversion or not is_progressive
        aspect_ratio = width / height if width and height else 0
        
        print(f"🔄 PROCESSING: {first_name} (@{username}) [ID: {chat_id}] - Starting video processing:")
        print(f"   📹 Codec: {codec_type} | Re-encode: {'Yes' if will_reencode else 'No'} | Method: {'GPU' if gpu_settings else 'CPU'}")
        print(f"   📐 Dimensions: {width}x{height} | Aspect: {aspect_ratio:.2f} ({aspect_name}) | Progressive: {'Yes' if is_progressive else 'No'}")
        print(f"   📺 Telegram player optimization: Enhanced streaming + color matrix + SAR")
        print(f"   🎬 Processing method: {processing_method}")
        
        # Update status to show processing status with safer text
        processing_status = "🔄 **Processing Video**\n\n📺 Quality: **{h}p**\n� Optimizing for Telegram player\n⚡ Enhanced streaming support".format(h=h)
        
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=session['status_msg_id'],
            text=processing_status,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Add small delay to allow previous operations to complete
        time.sleep(2)
        
        logger.debug(f"Starting yt-dlp download with options: {ydl_opts}")
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Wait a moment for file operations to complete
        time.sleep(3)
        
        after = set(os.listdir(download_dir))
        new_files = after - before
        
        # Debug: Log what files we found
        logger.debug(f"Files before download: {before}")
        logger.debug(f"Files after download: {after}")
        logger.debug(f"New files after download: {new_files}")
        logger.debug(f"Looking for video files in: {download_dir}")
        
        # Find the correct output file. Look for any video files created during download
        video_files = []
        
        # First, check new files
        for f in new_files:
            file_path = os.path.join(download_dir, f)
            if (f.lower().endswith(('.mp4', '.webm', '.mkv', '.avi', '.flv', '.mov')) and 
                os.path.isfile(file_path) and os.path.getsize(file_path) > 1024):  # At least 1KB
                video_files.append(f)
                logger.debug(f"Found new video file: {f} ({os.path.getsize(file_path)} bytes)")
        
        # If no new files found, look for any video files in download directory that might be the download
        if not video_files:
            logger.debug("No new video files found, searching all download files...")
            all_files = os.listdir(download_dir)
            current_time = time.time()
            for f in all_files:
                file_path = os.path.join(download_dir, f)
                if (f.lower().endswith(('.mp4', '.webm', '.mkv', '.avi', '.flv', '.mov')) and 
                    os.path.isfile(file_path) and os.path.getsize(file_path) > 1024):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age < 600:  # Modified within 10 minutes
                        video_files.append(f)
                        logger.debug(f"Found recent video file: {f} ({os.path.getsize(file_path)} bytes, age: {file_age:.0f}s)")
        
        # Also check for partial files that might indicate download issues
        if not video_files:
            logger.debug("No video files found, checking for partial files...")
            for f in os.listdir(download_dir):
                if f.lower().endswith(('.part', '.tmp', '.temp')):
                    logger.debug(f"Found partial file: {f}")
        
        if not video_files:
            logger.error(f"Downloaded file not found!")
            logger.error(f"Files before: {sorted(list(before))}")
            logger.error(f"Files after: {sorted(list(after))}")
            logger.error(f"New files: {sorted(list(new_files))}")
            raise FileNotFoundError(f"Downloaded file not found. Expected video file was not created.")
        
        # Get the full path and size for each video file
        video_files_with_size = [(os.path.join(download_dir, f), os.path.getsize(os.path.join(download_dir, f))) for f in video_files]
        
        # The final video is usually the largest one
        out_file, file_size = max(video_files_with_size, key=lambda item: item[1])
        
        # Calculate size difference for optimization tracking
        original_size = choice.get('filesize', 0)
        if not is_progressive and best_audio and best_audio.get('filesize'):
            original_size += best_audio.get('filesize')
        
        size_mb = file_size / (1024**2)
        original_mb = original_size / (1024**2) if original_size else 0
        
        if original_size:
            size_diff = ((file_size - original_size) / original_size) * 100
            print(f"📁 FILE FOUND: {first_name} (@{username}) [ID: {chat_id}] - Output: {os.path.basename(out_file)} ({size_mb:.1f}MB)")
            print(f"   📊 Size change: {size_diff:+.1f}% from original ({original_mb:.1f}MB → {size_mb:.1f}MB)")
        else:
            print(f"📁 FILE FOUND: {first_name} (@{username}) [ID: {chat_id}] - Output: {os.path.basename(out_file)} ({size_mb:.1f}MB)")
        
        logger.debug(f"Selected output file: {out_file} ({file_size} bytes)")

        # Update status to show upload
        logger.debug(f"Starting upload phase for file: {out_file}")
        upload_text = f"📤 **Uploading to Telegram**\n\n📺 Quality: **{h}p**\n⏳ Please wait..."
        context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=session['status_msg_id'],
            text=upload_text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]),
            parse_mode=ParseMode.MARKDOWN
        )

        # Get file size for processing
        file_size = os.path.getsize(out_file)
        size_mb = file_size / (1024**2)
        logger.debug(f"File size: {file_size} bytes ({size_mb:.1f} MB)")

        # Check if we need to split the file based on API type
        video_size_limit = VIDEO_SIZE_LIMIT
        if session.get('split_mode', False) or file_size > video_size_limit:
            print(f"📦 SPLITTING: {first_name} (@{username}) [ID: {chat_id}] - File too large ({size_mb:.1f}MB), splitting into parts")
            # Split the file into appropriate chunks based on API type
            part_files = split_file(out_file, CHUNK_SIZE)
            
            for i, part_file in enumerate(part_files, 1):
                if session['cancel']:
                    break
                    
                # Update status for each part
                part_status = f"📤 **Uploading Part {i}/{len(part_files)}**\n\n📺 Quality: **{h}p**\n📦 Part {i} of {len(part_files)}"
                context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=session['status_msg_id'],
                    text=part_status,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]),
                    parse_mode=ParseMode.MARKDOWN
                )

                # Show upload progress updates
                part_size_mb = os.path.getsize(part_file) / (1024**2)
                
                print(f"📤 UPLOADING PART: {first_name} (@{username}) [ID: {chat_id}] - Part {i}/{len(part_files)} ({part_size_mb:.1f}MB)")
                
                # Progress tracking for part upload
                last_progress_update = [0]  # Use list for mutable reference
                
                def part_upload_progress(bytes_uploaded, total_bytes, progress_percent):
                    if session.get('cancel', False):
                        return
                    
                    # Update progress every 10% for parts
                    current_progress = int(progress_percent // 10) * 10
                    if current_progress > last_progress_update[0] and current_progress > 0:
                        last_progress_update[0] = current_progress
                        print(f"📊 UPLOAD PROGRESS: {first_name} (@{username}) [ID: {chat_id}] - Part {i}/{len(part_files)}: {progress_percent:.0f}% ({bytes_uploaded/(1024**2):.1f}MB/{total_bytes/(1024**2):.1f}MB)")
                    
                    # Create animated progress bar for user interface
                    bar_length = 18
                    filled_length = int(bar_length * progress_percent // 100)
                    
                    # Use different characters for a more dynamic look
                    if progress_percent < 100:
                        bar = "█" * filled_length + "▓" + "░" * (bar_length - filled_length - 1)
                    else:
                        bar = "█" * bar_length
                    
                    # Speed estimation based on progress
                    if progress_percent >= 15:
                        estimated_speed = (bytes_uploaded / 1024 / 1024) / (progress_percent / 100) * 0.1  # Rough estimate
                        speed_text = f"📡 ~{estimated_speed:.1f} MB/s"
                    else:
                        speed_text = "📡 Calculating speed..."
                    
                    try:
                        upload_progress = f"📤 **Uploading Part {i}/{len(part_files)}**\n\n" \
                                        f"📺 Quality: **{h}p**\n" \
                                        f"📦 Part {i} of {len(part_files)}\n" \
                                        f"📊 Progress: **{progress_percent:.1f}%**\n" \
                                        f"📁 Uploaded: {bytes_uploaded/(1024**2):.1f}MB / {total_bytes/(1024**2):.1f}MB\n" \
                                        f"⬆️ `{bar}`\n" \
                                        f"{speed_text}"
                        
                        context.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=session['status_msg_id'],
                            text=upload_progress,
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]),
                            parse_mode=ParseMode.MARKDOWN
                        )
                    except Exception as e:
                        logger.debug(f"Failed to update upload progress: {e}")
                
                # Upload part with progress tracking
                part_file_size = os.path.getsize(part_file)
                video_telegram_limit = TG_MAX_FILESIZE  # Use configured limit
                
                # Determine upload type for split parts (same logic as single files)
                if part_file_size <= video_telegram_limit:
                    print(f"📺 UPLOADING PART AS VIDEO: {first_name} (@{username}) [ID: {chat_id}] - Part {i}/{len(part_files)} with streaming support")
                    upload_with_progress(
                        bot=context.bot,
                        chat_id=chat_id,
                        file_path=part_file,
                        upload_type='video',
                        width=width,
                        height=height,
                        duration=info.get('duration'),
                        caption=safe_caption(f"📺 {clean_title(title)} (Part {i}/{len(part_files)})"),
                        progress_callback=part_upload_progress,
                        session=session,
                        status_msg_id=session['status_msg_id'],
                        timeout=300  # 5 minutes timeout for large files
                    )
                else:
                    size_limit_text = "2GB" if USE_LOCAL_API else "50MB"
                    print(f"📄 UPLOADING PART AS DOCUMENT: {first_name} (@{username}) [ID: {chat_id}] - Part {i}/{len(part_files)} too large for video (>{size_limit_text})")
                    upload_with_progress(
                        bot=context.bot,
                        chat_id=chat_id,
                        file_path=part_file,
                        upload_type='document',
                        caption=safe_caption(f"📺 {clean_title(title)} (Part {i}/{len(part_files)})"),
                        progress_callback=part_upload_progress,
                        session=session,
                        status_msg_id=session['status_msg_id'],
                        timeout=300  # 5 minutes timeout for large files
                    )
                
                # Clean up part file
                os.remove(part_file)
            
            # Send completion message for split files
            if not session['cancel']:
                print(f"🎉 UPLOAD COMPLETE: {first_name} (@{username}) [ID: {chat_id}] - All {len(part_files)} parts uploaded successfully!")
                clean_full_title = clean_title(title)
                safe_title_display = escape_markdown(f"📺 {clean_full_title}")
                context.bot.send_message(
                    chat_id=chat_id,
                    text=f"✅ **{safe_title_display}**\n📦 **{len(part_files)} parts uploaded**",
                    parse_mode=ParseMode.MARKDOWN
                )
        else:
            print(f"📤 UPLOADING: {first_name} (@{username}) [ID: {chat_id}] - Uploading single file ({size_mb:.1f}MB)")
            # Send as single file  
            safe_title_caption = safe_caption(f"📺 {clean_title(title)}")
            
            # Telegram limits based on API type
            video_telegram_limit = TG_MAX_FILESIZE  # Use configured limit
            file_size = os.path.getsize(out_file)
            
            # Progress tracking for single file upload
            last_progress_update = [0]  # Use list for mutable reference
            
            def single_upload_progress(bytes_uploaded, total_bytes, progress_percent):
                if session.get('cancel', False):
                    return
                
                # Update progress every 5% for single files  
                current_progress = int(progress_percent // 5) * 5
                if current_progress > last_progress_update[0] and current_progress > 0:
                    last_progress_update[0] = current_progress
                    print(f"📊 UPLOAD PROGRESS: {first_name} (@{username}) [ID: {chat_id}] - {progress_percent:.0f}% complete ({bytes_uploaded/(1024**2):.1f}MB/{total_bytes/(1024**2):.1f}MB)")
                
                # Create animated progress bar for user interface
                bar_length = 18
                filled_length = int(bar_length * progress_percent // 100)
                
                # Use different characters for a more dynamic look
                if progress_percent < 100:
                    bar = "█" * filled_length + "▓" + "░" * (bar_length - filled_length - 1)
                else:
                    bar = "█" * bar_length
                
                # Speed calculation (rough estimate)
                if progress_percent > 15:  # Only show speed after some progress
                    avg_speed = (bytes_uploaded/1024/1024) / max(1, progress_percent/100 * 10)  # Estimate based on time
                    speed_text = f"📡 ~{avg_speed:.1f} MB/s"
                else:
                    speed_text = "📡 Calculating speed..."
                
                try:
                    upload_type_text = "Video" if file_size <= video_telegram_limit else "Document"
                    upload_progress = f"📤 **Uploading {upload_type_text} to Telegram**\n\n" \
                                    f"📺 Quality: **{h}p**\n" \
                                    f"📁 Size: **{size_mb:.1f} MB**\n" \
                                    f"📊 Progress: **{progress_percent:.1f}%**\n" \
                                    f"📁 Uploaded: {bytes_uploaded/(1024**2):.1f}MB / {total_bytes/(1024**2):.1f}MB\n" \
                                    f"⬆️ `{bar}`\n" \
                                    f"{speed_text}"
                    
                    context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=session['status_msg_id'],
                        text=upload_progress,
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]),
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception as e:
                    logger.debug(f"Failed to update upload progress: {e}")
            
            # Determine upload type and upload with progress
            if file_size <= video_telegram_limit:
                print(f"📺 UPLOADING AS VIDEO: {first_name} (@{username}) [ID: {chat_id}] - With streaming support and metadata")
                # Upload as video with progress tracking
                upload_with_progress(
                    bot=context.bot,
                    chat_id=chat_id,
                    file_path=out_file,
                    upload_type='video',
                    width=width,
                    height=height,
                    duration=info.get('duration'),
                    caption=safe_title_caption,
                    progress_callback=single_upload_progress,
                    session=session,
                    status_msg_id=session['status_msg_id'],
                    timeout=300  # 5 minutes timeout for large files
                )
                print(f"🎉 UPLOAD COMPLETE: {first_name} (@{username}) [ID: {chat_id}] - Video uploaded successfully as streaming video!")
            else:
                size_limit_text = "2GB" if USE_LOCAL_API else "50MB"
                print(f"� UPLOADING AS DOCUMENT: {first_name} (@{username}) [ID: {chat_id}] - File too large for video upload (>{size_limit_text})")
                # Upload as document with progress tracking
                upload_with_progress(
                    bot=context.bot,
                    chat_id=chat_id,
                    file_path=out_file,
                    upload_type='document',
                    caption=safe_title_caption,
                    progress_callback=single_upload_progress,
                    session=session,
                    status_msg_id=session['status_msg_id'],
                    timeout=300  # 5 minutes timeout for large files
                )
                print(f"🎉 UPLOAD COMPLETE: {first_name} (@{username}) [ID: {chat_id}] - Large file uploaded successfully as document!")
        
        # Delete the status message
        try:
            context.bot.delete_message(chat_id=chat_id, message_id=session['status_msg_id'])
        except:
            pass
            
    except Exception as e:
        print(f"💥 DOWNLOAD FAILED: {first_name} (@{username}) [ID: {chat_id}] - Error: {str(e)[:100]}{'...' if len(str(e)) > 100 else ''}")
        logger.exception(f"Download thread for {chat_id} ended with error: {e}")
        # if not canceled, notify failure
        if not session.get('cancel', False):
            try:
                context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=session['status_msg_id'],
                    text=f"❌ **Download Failed**\n\n"
                         f"Error: `{str(e)[:100]}{'...' if len(str(e)) > 100 else ''}`\n\n"
                         "This could be due to:\n"
                         "• Network connection issues\n"
                         "• Video no longer available\n"
                         "• FFmpeg processing error\n"
                         "• File format compatibility issue\n\n"
                         "Please try again or choose a different quality.",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=None
                )
            except Exception as inner_e:
                logger.error(f"Failed to send error message: {inner_e}")
    finally:
        print(f"🧹 CLEANUP: {first_name} (@{username}) [ID: {chat_id}] - Cleaning up temporary files and session")
        # cleanup
        if out_file and os.path.exists(out_file):
            os.remove(out_file)
        
        # Clean up any remaining part files
        if out_file:
            base_name = os.path.splitext(out_file)[0]
            ext = os.path.splitext(out_file)[1]
            part_pattern = f"{base_name}_part*{ext}"
            
            import glob
            for part_file in glob.glob(part_pattern):
                if os.path.exists(part_file):
                    os.remove(part_file)
        
        _sessions.pop(chat_id, None)


def split_file(file_path, max_size_bytes):
    """Split a large file into smaller chunks."""
    file_size = os.path.getsize(file_path)
    if file_size <= max_size_bytes:
        return [file_path]  # No need to split
    
    base_name = os.path.splitext(file_path)[0]
    ext = os.path.splitext(file_path)[1]
    
    num_parts = math.ceil(file_size / max_size_bytes)
    chunk_size = file_size // num_parts
    
    part_files = []
    
    with open(file_path, 'rb') as f:
        for i in range(num_parts):
            part_filename = f"{base_name}_part{i+1:02d}{ext}"
            
            with open(part_filename, 'wb') as part_file:
                if i == num_parts - 1:  # Last part
                    part_file.write(f.read())  # Read remaining data
                else:
                    part_file.write(f.read(chunk_size))
            
            part_files.append(part_filename)
    
    return part_files


def error_handler(update: Update, context: CallbackContext):
    logger.exception("Unhandled exception in handler")


def main():
    """Main function to run the Telegram bot."""
    try:
        # Check if bot token is provided
        if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == 'your_bot_token_here':
            print("❌ ERROR: Bot token not found!")
            print("📝 Please set your TELEGRAM_BOT_TOKEN in:")
            print("   1. Environment variable: export TELEGRAM_BOT_TOKEN='your_token'")
            print("   2. .env file: TELEGRAM_BOT_TOKEN=your_token")
            print("   3. Directly in the script (not recommended)")
            sys.exit(1)
        
        # Check if required directories exist
        os.makedirs('downloads', exist_ok=True)
        
        # Configure request for local API if enabled
        if USE_LOCAL_API:
            print(f"🏠 Using Local Bot API Server: {LOCAL_API_SERVER}")
            updater = Updater(
                token=TELEGRAM_BOT_TOKEN, 
                base_url=f"{LOCAL_API_SERVER}/bot",
                use_context=True
            )
        else:
            print("☁️ Using Standard Telegram Bot API")
            updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
        
        # Get the dispatcher to register handlers
        dispatcher = updater.dispatcher
        
        # Register command and message handlers
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_link))
        dispatcher.add_handler(CallbackQueryHandler(button_handler))
        
        # Start the bot
        print("🤖 Starting Telegram Bot...")
        print(f"⚙️ GPU Acceleration: {'Enabled' if USE_GPU_ACCELERATION else 'Disabled'}")
        print(f"📁 File Size Limit: {TG_MAX_FILESIZE/(1024**3 if USE_LOCAL_API else 1024**2):.0f}{'GB' if USE_LOCAL_API else 'MB'}")
        print(f"✂️ Split Threshold: {VIDEO_SIZE_LIMIT/(1024**3 if USE_LOCAL_API else 1024**2):.1f}{'GB' if USE_LOCAL_API else 'MB'}")
        
        updater.start_polling()
        
        print("🚀 Bot is ready! Send YouTube links to start downloading.")
        print("="*60)
        print("📊 CONSOLE LOGGING ENABLED:")
        print("   🔥 User actions (start, link sending)")
        print("   🎯 Quality selections")
        print("   📥 Download progress (every 20%)")
        print("   📤 Upload progress (every 5-10%)")
        print("   ✅ Success/Error messages")
        print("="*60)
        print("💡 Press Ctrl+C to stop the bot")
        
        # Keep the bot running
        updater.idle()
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        logger.exception("Bot startup error")
        sys.exit(1)


if __name__ == "__main__":
    main()
