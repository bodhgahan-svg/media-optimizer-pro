import os
import subprocess
import tempfile
import static_ffmpeg
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# FFmpeg पाथ ऑटो-सेट करें
static_ffmpeg.add_paths()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "Server is running with FFmpeg!"}

@app.post("/process-media/")
async def process_media(
    file: UploadFile = File(...),
    mode: str = Form("compress"),
    resolution: str = Form("original"),
    quality: str = Form("85")
):
    try:
        suffix = os.path.splitext(file.filename)[1].lower()
        if not suffix:
            suffix = ".mp4"

        # टेम्परेरी इनपुट फ़ाइल बनाएं
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_in:
            content = await file.read()
            tmp_in.write(content)
            in_path = tmp_in.name

        out_path = in_path + "_processed" + suffix

        # रेजोल्यूशन सेटिंग्स (4K/1080p/Original)
        vf_filter = ""
        if resolution == "4k":
            vf_filter = "scale=3840:2160:force_original_aspect_ratio=decrease,pad=3840:2160:(ow-iw)/2:(oh-ih)/2"
        elif resolution == "1080":
            vf_filter = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2"

        is_video = suffix in ['.mp4', '.mkv', '.avi', '.mov', '.webm', '.3gp']

        cmd = ["ffmpeg", "-y", "-i", in_path]

        if is_video:
            if vf_filter:
                cmd.extend(["-vf", vf_filter])
            # क्वालिटी (CRF) कैलकुलेशन
            q_val = int(quality)
            crf = int(35 - ((q_val - 40) * (35 - 18) / 58))
            cmd.extend(["-c:v", "libx264", "-crf", str(crf), "-preset", "ultrafast", "-c:a", "copy", out_path])
        else:
            if vf_filter:
                cmd.extend(["-vf", vf_filter])
            cmd.extend([out_path])

        # FFmpeg कमांड चलाएं
        subprocess.run(cmd, check=True)

        return FileResponse(out_path, filename=f"optimized_{file.filename}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
