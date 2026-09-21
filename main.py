import os
import subprocess
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn

app = FastAPI(title="Pro Media Optimizer Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_ffmpeg(command):
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise Exception(f"FFmpeg Error: {e.stderr.decode('utf-8', errors='ignore')}")

@app.post("/process-media/")
async def process_media(
    file: UploadFile = File(...),
    mode: str = Form(...),
    resolution: str = Form(...),
    quality: int = Form(...)
):
    input_path = os.path.join(UPLOAD_DIR, file.filename)
    filename_without_ext = os.path.splitext(file.filename)[0]
    
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    is_video = file.content_type.startswith("video")
    
    if is_video:
        output_filename = f"{filename_without_ext}_pro.mp4"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        cmd = ["ffmpeg", "-y", "-i", input_path]
        
        scale_filter = ""
        if resolution == "4k":
            scale_filter = "scale=3840:-2:flags=lanczos"
        elif resolution == "1080":
            scale_filter = "scale=1920:-2:flags=lanczos"
            
        if scale_filter:
            cmd.extend(["-vf", scale_filter])

        crf = int(32 - ((quality / 100) * 14))
        
        cmd.extend([
            "-c:v", "libx264",
            "-preset", "faster",
            "-crf", str(crf),
            "-c:a", "aac",
            "-b:a", "128k",
            output_path
        ])
        
    else:
        output_filename = f"{filename_without_ext}_pro.webp"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        cmd = ["ffmpeg", "-y", "-i", input_path]
        
        if resolution == "4k":
            cmd.extend(["-vf", "scale=3840:-2:flags=lanczos"])
        elif resolution == "1080":
            cmd.extend(["-vf", "scale=1920:-2:flags=lanczos"])
            
        cmd.extend([
            "-quality", str(quality),
            output_path
        ])

    try:
        run_ffmpeg(cmd)
        os.remove(input_path)
        return FileResponse(path=output_path, filename=output_filename, media_type='application/octet-stream')
    except Exception as e:
        if os.path.exists(input_path): os.remove(input_path)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
