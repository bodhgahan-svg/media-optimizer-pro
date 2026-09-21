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
    return {"status": "Server is running with High-Quality 4K FFmpeg Engine!"}

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

        # इनपुट टेम्परेरी फ़ाइल
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_in:
            content = await file.read()
            tmp_in.write(content)
            in_path = tmp_in.name

        out_path = in_path + "_4k_processed" + suffix
        is_video = suffix in ['.mp4', '.mkv', '.avi', '.mov', '.webm', '.3gp']

        # उच्च गुणवत्ता वाली स्केलिंग + शार्पनिंग फ़िल्टर (बिना काली पट्टियों के)
        filters = []
        if resolution == "4k":
            # Lanczos स्केलिंग + unsharp फ़िल्टर (4K क्लैरिटी के लिए)
            filters.append("scale='if(gt(iw,ih),3840,-2)':'if(gt(iw,ih),-2,2160)':flags=lanczos")
            filters.append("unsharp=5:5:1.5:5:5:0.0")
        elif resolution == "1080":
            filters.append("scale='if(gt(iw,ih),1920,-2)':'if(gt(iw,ih),-2,1080)':flags=lanczos")
            filters.append("unsharp=3:3:1.0:3:3:0.0")

        vf_str = ",".join(filters) if filters else ""

        cmd = ["ffmpeg", "-y", "-i", in_path]

        if is_video:
            if vf_str:
                cmd.extend(["-vf", vf_str])
            
            # क्वालिटी (CRF) कैलकुलेशन
            q_val = int(quality)
            crf = int(32 - ((q_val - 40) * (32 - 15) / 58))
            cmd.extend(["-c:v", "libx264", "-crf", str(crf), "-preset", "medium", "-c:a", "copy", out_path])
        else:
            # फोटो के लिए (हाई-क्वालिटी आउटपुट + 4K स्केलिंग)
            if vf_str:
                cmd.extend(["-vf", vf_str])
            cmd.extend(["-q:v", "2", out_path])

        # FFmpeg कमांड एग्जीक्यूट करें
        subprocess.run(cmd, check=True)

        return FileResponse(out_path, filename=f"4K_optimized_{file.filename}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
