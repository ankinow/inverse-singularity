import asyncio, hmac, logging, os, shutil, subprocess, tempfile
from pathlib import Path
from urllib.parse import urlparse
from typing import Literal

import imageio_ffmpeg
import yt_dlp
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from starlette.concurrency import run_in_threadpool

logging.basicConfig(level=os.getenv("LOG_LEVEL","INFO").upper(),
                    format="%(asctime)s %(levelname)s %(name)s %(message)s")
log=logging.getLogger("audio-clipper")

MAX_CLIP_SECONDS=float(os.getenv("MAX_CLIP_SECONDS","60"))
MAX_OFFSET_SECONDS=float(os.getenv("MAX_OFFSET_SECONDS","21600"))
PROCESS_TIMEOUT_SECONDS=int(os.getenv("PROCESS_TIMEOUT_SECONDS","120"))
MAX_CONCURRENT_JOBS=max(1,int(os.getenv("MAX_CONCURRENT_JOBS","1")))
API_KEY=os.getenv("API_KEY","").strip()
ALLOWED_HOSTS={h.strip().lower().lstrip(".") for h in os.getenv(
    "ALLOWED_HOSTS","youtube.com,youtu.be").split(",") if h.strip()}
FFMPEG=os.getenv("FFMPEG_BINARY","").strip() or imageio_ffmpeg.get_ffmpeg_exe()
JOBS=asyncio.Semaphore(MAX_CONCURRENT_JOBS)

app=FastAPI(title="Render Audio Clipper", version="1.1.0")

def auth(x_api_key: str|None=Header(default=None)):
    if API_KEY and (not x_api_key or not hmac.compare_digest(x_api_key,API_KEY)):
        raise HTTPException(401,"invalid API key")

def validate_url(raw:str)->str:
    try: p=urlparse(raw)
    except Exception as e: raise HTTPException(400,"invalid URL") from e
    if p.scheme not in {"http","https"} or not p.hostname:
        raise HTTPException(400,"only http/https URLs are accepted")
    host=p.hostname.rstrip(".").lower()
    if not any(host==base or host.endswith("."+base) for base in ALLOWED_HOSTS):
        raise HTTPException(400,f"host not allowed: {host}")
    return raw

def ydl_base(getcomments=False):
    opts={
      "quiet":True,"no_warnings":True,"noplaylist":True,"skip_download":True,
      "socket_timeout":30,"retries":2,"fragment_retries":2,
    }
    if getcomments:
        opts.update({
          "getcomments":True,
          "extractor_args":{"youtube":{"max_comments":["500"]}},
        })
    else:
        opts["format"]="bestaudio/best"
    return opts

def extract(url:str,getcomments=False):
    with yt_dlp.YoutubeDL(ydl_base(getcomments)) as ydl:
        info=ydl.extract_info(url,download=False)
    if not isinstance(info,dict): raise RuntimeError("no metadata returned")
    return info

def select_media(info:dict)->dict:
    rd=info.get("requested_downloads")
    if isinstance(rd,list) and rd: return rd[0]
    rf=info.get("requested_formats")
    if isinstance(rf,list):
        audio=[f for f in rf if f.get("acodec") not in {None,"none"}]
        if audio: return audio[0]
    return info

def header_blob(media:dict,info:dict)->str:
    headers=media.get("http_headers") or info.get("http_headers") or {}
    out=[]
    if isinstance(headers,dict):
        for k,v in headers.items():
            k,v=str(k),str(v)
            if any(c in k+v for c in "\r\n"): continue
            if k.lower() in {"host","content-length"}: continue
            out.append(f"{k}: {v}")
    return "\r\n".join(out)+("\r\n" if out else "")

def make_clip(url:str,start:float,duration:float,fmt:str):
    if duration<=0 or duration>MAX_CLIP_SECONDS:
        raise HTTPException(400,f"duration must be >0 and <= {MAX_CLIP_SECONDS:g}")
    if start<0 or start>MAX_OFFSET_SECONDS:
        raise HTTPException(400,f"start must be between 0 and {MAX_OFFSET_SECONDS:g}")
    info=extract(validate_url(url),False)
    media=select_media(info)
    stream=media.get("url")
    if not stream: raise RuntimeError("no playable audio URL")
    tmp=Path(tempfile.mkdtemp(prefix="clipper-"))
    out=tmp/f"clip.{fmt}"
    cmd=[FFMPEG,"-nostdin","-hide_banner","-loglevel","error"]
    hb=header_blob(media,info)
    if hb: cmd+=["-headers",hb]
    cmd+=["-ss",f"{start:.3f}","-i",str(stream),"-t",f"{duration:.3f}",
          "-vn","-map_metadata","-1"]
    if fmt=="mp3": cmd+=["-c:a","libmp3lame","-b:a","160k"]
    else: cmd+=["-c:a","pcm_s16le","-ar","44100","-ac","2"]
    cmd+=["-y",str(out)]
    try:
        subprocess.run(cmd,check=True,timeout=PROCESS_TIMEOUT_SECONDS,
                       stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
    except subprocess.CalledProcessError as e:
        shutil.rmtree(tmp,ignore_errors=True)
        raise RuntimeError((e.stderr or "ffmpeg failed")[-1200:])
    except subprocess.TimeoutExpired as e:
        shutil.rmtree(tmp,ignore_errors=True)
        raise RuntimeError("ffmpeg timed out") from e
    if not out.exists() or out.stat().st_size==0:
        shutil.rmtree(tmp,ignore_errors=True)
        raise RuntimeError("empty clip")
    return tmp,out,info

@app.get("/health")
def health():
    return {"ok":True,"service":"render-audio-clipper","ffmpeg":Path(FFMPEG).name,
            "max_clip_seconds":MAX_CLIP_SECONDS,"auth_enabled":bool(API_KEY),
            "allowed_hosts":sorted(ALLOWED_HOSTS)}

@app.get("/probe", dependencies=[Depends(auth)])
async def probe(url:str=Query(...)):
    try:
        async with JOBS: info=await run_in_threadpool(extract,validate_url(url),False)
        return {k:info.get(k) for k in ("id","title","uploader","duration","webpage_url","extractor_key")}
    except HTTPException: raise
    except Exception as e:
        log.exception("probe failed"); raise HTTPException(502,str(e)[:1000])

@app.get("/comments", dependencies=[Depends(auth)])
async def comments(url:str=Query(...), comment_id:str|None=Query(default=None)):
    try:
        async with JOBS: info=await run_in_threadpool(extract,validate_url(url),True)
        rows=info.get("comments") or []
        slim=[{"id":c.get("id"),"parent":c.get("parent"),"author":c.get("author"),
               "text":c.get("text"),"timestamp":c.get("timestamp"),
               "like_count":c.get("like_count")}
              for c in rows if isinstance(c,dict)]
        if comment_id:
            exact=[c for c in slim if c.get("id")==comment_id or c.get("parent")==comment_id]
            if exact: return {"matched":True,"count":len(exact),"comments":exact}
            base=comment_id.split(".")[0]
            related=[c for c in slim if str(c.get("id","")).startswith(base) or
                     str(c.get("parent","")).startswith(base)]
            return {"matched":bool(related),"count":len(related),"comments":related,
                    "searched_total":len(slim)}
        return {"count":len(slim),"comments":slim[:200]}
    except HTTPException: raise
    except Exception as e:
        log.exception("comments failed"); raise HTTPException(502,str(e)[:1000])

@app.get("/clip", dependencies=[Depends(auth)])
async def clip(url:str=Query(...), start:float=Query(0,ge=0),
               duration:float=Query(30,gt=0), format:Literal["mp3","wav"]=Query("mp3")):
    tmp=None
    try:
        async with JOBS:
            tmp,out,info=await run_in_threadpool(make_clip,validate_url(url),start,duration,format)
        media="audio/mpeg" if format=="mp3" else "audio/wav"
        name=f"{info.get('id') or 'clip'}-{start:g}s-{duration:g}s.{format}"
        return FileResponse(out,media_type=media,filename=name,
            headers={"Cache-Control":"no-store","X-Clip-Start":str(start),"X-Clip-Duration":str(duration)},
            background=BackgroundTask(shutil.rmtree,tmp,ignore_errors=True))
    except HTTPException:
        if tmp: shutil.rmtree(tmp,ignore_errors=True)
        raise
    except Exception as e:
        if tmp: shutil.rmtree(tmp,ignore_errors=True)
        log.exception("clip failed"); raise HTTPException(502,str(e)[:1000])


TARGET_URL=os.getenv("TARGET_URL","").strip()
TARGET_COMMENT_ID=os.getenv("TARGET_COMMENT_ID","").strip()

async def _startup_target_lookup():
    if not TARGET_URL:
        return
    await asyncio.sleep(2)
    try:
        log.info("target lookup begin url=%s comment_id=%s", TARGET_URL, TARGET_COMMENT_ID or "-")
        info=await run_in_threadpool(extract, validate_url(TARGET_URL), True)
        rows=info.get("comments") or []
        slim=[{"id":c.get("id"),"parent":c.get("parent"),"author":c.get("author"),
               "text":c.get("text"),"timestamp":c.get("timestamp"),
               "like_count":c.get("like_count")}
              for c in rows if isinstance(c,dict)]
        matches=[]
        if TARGET_COMMENT_ID:
            base=TARGET_COMMENT_ID.split(".")[0]
            matches=[c for c in slim if c.get("id")==TARGET_COMMENT_ID
                     or c.get("parent")==TARGET_COMMENT_ID
                     or str(c.get("id","")).startswith(base)
                     or str(c.get("parent","")).startswith(base)]
        log.info("TARGET_COMMENTS total=%s matches=%s", len(slim), matches[:20])
    except Exception:
        log.exception("target lookup failed")

@app.on_event("startup")
async def startup_target_lookup():
    asyncio.create_task(_startup_target_lookup())
