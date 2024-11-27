import subprocess
import json
import io
import time
import logging
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins, modify as needed
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Get the absolute path to the ffmpeg.exe in the same directory as this script
current_dir = Path(__file__).parent
ffmpeg_path = "ffmpeg"

# Custom User-Agent string to mimic a browser request
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

@app.get("/download-audio/")
async def download_audio(url: str):
    mainstart = time.time()
    logger.info(f"Downloading audio from: {url}")

    try:
        # Step 1: Use yt-dlp to get video info and check audio format
        info_command = [
            "yt-dlp", "-j", "--skip-download", "--no-check-certificate", "--geo-bypass",
            "--user-agent", USER_AGENT, url  # Output metadata in JSON format, no SSL check, bypass region block
        ]
        logger.debug(f"Running command: {' '.join(info_command)}")
        result = subprocess.run(info_command, capture_output=True, text=True, check=True)

        # Parse the JSON output safely
        metadata = json.loads(result.stdout)  # Parse JSON string to Python dictionary

        ext = metadata.get("ext", "")  # Get the file extension (audio/video format)
        title = metadata.get("title", "audio_file")  # Extract the video title or set a default
        logger.info(f"File extension: {ext}")
        logger.info(f"Title: {title}")

        # Step 2: Handle audio download and conversion
        if ext == "mp3":
            # Directly download the MP3 file if it is already in MP3 format
            yt_dlp_command = [
                "yt-dlp",
                "--format", "bestaudio/best",  # Best available audio
                "--output", "-",  # Output to stdout (in memory)
                "--no-check-certificate",  # Disable certificate check
                "--geo-bypass",  # Bypass geo-blocks
                "--user-agent", USER_AGENT,  # Use the browser-like User-Agent
                url
            ]
            logger.info("Downloading MP3")
            result = subprocess.run(yt_dlp_command, capture_output=True, check=True)

            # Return the result as a streaming response with a dynamic filename
            logger.debug("Returning MP3 file as response.")
            return StreamingResponse(io.BytesIO(result.stdout), media_type="audio/mpeg",
                                     headers={"Content-Disposition": f"attachment; filename={title}.mp3"})

        elif ext in ["webm", "m4a", "flac", "ogg"]:
            # Handle known audio formats that yt-dlp can extract
            yt_dlp_command = [
                "yt-dlp",
                "--extract-audio",  # Extract audio only
                "--audio-format", "best",  # Let yt-dlp decide the best format
                "--output", "-",  # Output to stdout (in memory)
                "--no-check-certificate",  # Disable certificate check
                "--geo-bypass",  # Bypass geo-blocks
                "--user-agent", USER_AGENT,  # Use the browser-like User-Agent
                url
            ]
            logger.info(f"Downloading audio in format: {ext}")
            start_time = time.time()
            result = subprocess.run(yt_dlp_command, capture_output=True, check=True)
            end_time = time.time()

            elapsed_time = end_time - start_time
            logger.info(f"Download ran for {elapsed_time} seconds.")

            # Convert to MP3 if the format isn't MP3
            if ext != "mp3":
                ffmpeg_command = [
                    str(ffmpeg_path), '-i', 'pipe:0',  # Read from stdin
                    '-c:a', 'libmp3lame', '-b:a', '192k',  # Encode with MP3 codec, 192kbps
                    '-f', 'mp3', 'pipe:1'  # Write to stdout
                ]
                logger.info("Converting to MP3")
                start_time = time.time()
                try:
                    ffmpeg_process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except Exception as e:
                    logger.error("Error starting ffmpeg process")
                    raise e

                try:
                    mp3_data, stderr = ffmpeg_process.communicate(input=result.stdout)
                    if stderr:
                        logger.error(f"FFmpeg stderr: {stderr.decode()}")
                except Exception as e:
                    logger.error("Error during ffmpeg communicate")
                    raise e

                end_time = time.time()
                elapsed_time = end_time - start_time
                logger.info(f"Conversion ran for {elapsed_time} seconds.")

                mainend = time.time()
                main_elapsed_time = mainend - mainstart
                logger.info(f"Total time: {main_elapsed_time} seconds.")

                # Return the MP3 data as a streaming response with a dynamic filename
                logger.debug(f"Returning converted MP3 as response.")
                return StreamingResponse(io.BytesIO(mp3_data), media_type="audio/mpeg",
                                         headers={"Content-Disposition": f"attachment; filename={title}.mp3"})

        else:
            error_message = f"Unsupported audio format: {ext}"
            logger.error(error_message)
            return {"error": error_message}

    except subprocess.CalledProcessError as e:
        logger.error(f"yt-dlp subprocess error: {e.stderr}")
        return {"error": f"An error occurred: {e.stderr}"}
    except Exception as e:
        logger.error(f"General error: {str(e)}")
        return {"error": str(e)}
