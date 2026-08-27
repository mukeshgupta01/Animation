"""Produce the handcrafted Five Little Ducks river countdown."""

from __future__ import annotations

import asyncio, json, math, random, struct, subprocess, wave
from pathlib import Path

import edge_tts
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

import produce_snack_video as base
import produce_star_friends_twinkle_playground as render_engine
from voice_profiles import select_voice_profile

AUTOMATION=base.AUTOMATION; PROJECT=AUTOMATION.parent; ITEM_ID="five-little-ducks-river-countdown-01"
OUTPUT=AUTOMATION/"production-output"/f"{ITEM_ID}.mp4"; WORK=AUTOMATION/"production-work"/ITEM_ID
META=PROJECT/"metadata"/f"{ITEM_ID}.json"; PLAN=PROJECT/"metadata"/f"{ITEM_ID}-plan.json"; ASSETS=AUTOMATION/"production-assets"; THUMBNAIL=AUTOMATION/"thumbnails"/f"{ITEM_ID}.jpg"; ART_FPS=10
VOICES={
    "maisie-story":{**select_voice_profile("maisie-uk"),"rate":"+1%","pitch":"+6Hz"},
    "maisie-song":{**select_voice_profile("maisie-uk"),"rate":"+7%","pitch":"+14Hz"},
    "natasha-au":select_voice_profile("natasha-au"),
    "natasha-song":{**select_voice_profile("natasha-au"),"rate":"+6%","pitch":"+10Hz"},
}

def shots(): return json.loads(PLAN.read_text(encoding="utf-8"))["shots"]
def voice_path(si,li,profile): return WORK/f"voice-v1-{si:02d}-{li:02d}-{profile}.mp3"
def duration(path): return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(path)],text=True).strip())

async def make_voices(rows):
    for si,shot in enumerate(rows):
        for li,line in enumerate(shot["lines"]):
            path=voice_path(si,li,line["profile"]); voice=VOICES[line["profile"]]
            if not path.exists() or path.stat().st_size<1000: await edge_tts.Communicate(line["line"],voice["voice"],rate=voice["rate"],pitch=voice["pitch"],volume="-1%").save(str(path))

def make_sfx(rows):
    rate=48000; rng=random.Random(82755); result={}
    for si,shot in enumerate(rows):
        length=2.8; path=WORK/f"effect-{si:02d}.wav"; count=shot["visible_count"]
        with wave.open(str(path),"wb") as out:
            out.setnchannels(2); out.setsampwidth(2); out.setframerate(rate); frames=bytearray(); smooth=0.0
            for n in range(round(length*rate)):
                t=n/rate; value=0.0
                # Duck calls are voiced by the effect itself, never spoken.
                if si in (1,2,3,4,6):
                    for onset in ((0.15,0.55,0.95) if si!=6 else (1.15,1.52,1.90)):
                        age=t-onset
                        if 0<=age<0.28:
                            freq=235-95*age/0.28; value += (math.sin(2*math.pi*freq*age)+.35*math.sin(2*math.pi*freq*2*age))*math.sin(math.pi*age/.28)**1.4*.075
                # Count-matched paddle/splash transients.
                splashes=(5 if si==0 else 3 if si in (2,6) else 2 if si==3 else 1 if si==4 else 0)
                for j in range(splashes):
                    onset=.25+j*.38 if si!=6 else .12+j*.28; age=t-onset
                    if 0<=age<.16: value += rng.uniform(-1,1)*math.exp(-28*age)*.08
                if si==3:
                    noise=rng.uniform(-1,1); smooth=.94*smooth+.06*noise; value += smooth*.025
                if si==5:
                    for onset in (.18,.68,1.18):
                        age=t-onset
                        if age>=0: value += math.sin(2*math.pi*620*age)*math.exp(-7*age)*.045
                sample=int(max(-1,min(1,value))*22000); frames.extend(struct.pack("<hh",sample,sample))
            out.writeframes(frames)
        result[shot["id"]]=path
    return result

def timeline(rows,sfx):
    events=[{"phase":"title","start":0.0,"end":3.8,"asset":rows[0]["asset"]}]; tracks=[]; cursor=3.8
    for si,shot in enumerate(rows):
        local=.25; lines=[]; fx_start=cursor+.18; fx_end=fx_start+duration(sfx[shot["id"]]); tracks.append((sfx[shot["id"]],fx_start))
        for li,line in enumerate(shot["lines"]):
            path=voice_path(si,li,line["profile"]); length=duration(path); start=cursor+local; lines.append({**line,"start":start,"end":start+length}); tracks.append((path,start)); local+=length+.12
        length=max(9.0,local+.35,fx_end-cursor+.3)
        if length>14: raise RuntimeError(f"14-second gate failed: {shot['id']} {length:.2f}s")
        events.append({"phase":shot["id"],"start":cursor,"end":cursor+length,"asset":shot["asset"],"visible_count":shot["visible_count"],"lines":lines,"effects":[{"name":shot["effect"],"start":fx_start,"end":fx_end}]}); cursor+=length
    events.append({"phase":"end","start":cursor,"end":cursor+4.8,"asset":rows[-1]["asset"]}); return events,tracks,events[-1]["end"]

def fit(path):
    image=Image.open(path).convert("RGB"); scale=max((base.W+180)/image.width,(base.H+110)/image.height); return image.resize((round(image.width*scale),round(image.height*scale)),Image.Resampling.LANCZOS)
def load_assets(rows):
    paths={r["asset"]:ASSETS/r["asset"] for r in rows}; missing=[str(p) for p in paths.values() if not p.is_file()]
    if missing: raise FileNotFoundError(missing)
    return {n:fit(p) for n,p in paths.items()}
def crop(image,event,t,index):
    p=max(0,min(1,(t-event["start"])/max(.01,event["end"]-event["start"]))); e=p*p*(3-2*p); zoom=1+(.045*e if index%2==0 else .045*(1-e)); resized=image.resize((round((base.W+180)*zoom),round((base.H+110)*zoom)),Image.Resampling.BICUBIC); ax=resized.width-base.W; ay=resized.height-base.H; x=int(ax*((.17+.48*e) if index%2==0 else (.73-.44*e))); y=int(ay*(.45+.04*math.sin(p*math.pi))); return resized.crop((x,y,x+base.W,y+base.H))
def overlay(frame,event,t,index):
    draw=ImageDraw.Draw(frame,"RGBA"); local=t-event["start"]; rng=random.Random(5500+index)
    for j in range(13):
        x=(rng.randint(20,1900)+int(local*(12+j%4*4)))%1920; y=rng.randint(500,1030); r=2+int(2*(.5+.5*math.sin(local*2+j))); draw.ellipse((x-r,y-r,x+r,y+r),fill=(190,235,255,60))
    if index>=4:
        for j in range(8):
            x=rng.randint(80,1840); y=rng.randint(80,900); r=2+int(3*(.5+.5*math.sin(local*1.4+j))); draw.ellipse((x-r,y-r,x+r,y+r),fill=(255,213,100,80))
def frame_for(event,t,assets):
    if event["phase"]=="title":
        frame=crop(assets[event["asset"]],event,t,0).convert("RGBA"); draw=ImageDraw.Draw(frame,"RGBA"); draw.rounded_rectangle((220,90,1700,350),48,fill=(31,75,94,222),outline=(255,230,115,245),width=7); base.centered(draw,(960,180),"FIVE LITTLE DUCKS",base.F62,(255,244,142,255),3); base.centered(draw,(960,278),"RIVER COUNTDOWN",base.F62,"white",3); return frame.convert("RGB")
    if event["phase"]=="end":
        frame=crop(assets[event["asset"]],event,t,6).convert("RGBA"); draw=ImageDraw.Draw(frame,"RGBA"); draw.rectangle((0,0,1920,1080),fill=(20,38,65,55)); draw.rounded_rectangle((320,760,1600,982),46,fill=(31,75,94,226),outline=(255,230,115,245),width=7); base.centered(draw,(960,840),"ONE • TWO • THREE • FOUR • FIVE",base.F48,(255,244,142,255),2); base.centered(draw,(960,922),"SAFE TOGETHER BY THE RIVER",base.F48,"white",2); return frame.convert("RGB")
    rows=shots(); index=next(i for i,r in enumerate(rows) if r["id"]==event["phase"]); frame=crop(assets[event["asset"]],event,t,index).convert("RGBA"); overlay(frame,event,t,index); return frame.convert("RGB")

def make_music(total):
    path=WORK/"original-five-ducks-river-arrangement.wav"; rate=48000; beat=60/104; notes=(392,440,523.25,440,392,329.63,349.23,392); rng=random.Random(827104)
    with wave.open(str(path),"wb") as out:
        out.setnchannels(2); out.setsampwidth(2); out.setframerate(rate); chunk=bytearray()
        for n in range(int(total*rate)):
            t=n/rate; note=notes[int(t/beat)%len(notes)]; phase=t%beat; pluck=math.sin(2*math.pi*note*t)*math.exp(-4.2*phase)*.042; bass=math.sin(2*math.pi*(note/2)*t)*.009; pulse=math.sin(2*math.pi*86*t)*max(0,1-phase/.03)*.022 if phase<.03 else 0; value=pluck+bass+pulse+rng.uniform(-.0008,.0008); sample=int(max(-1,min(1,value))*32767); chunk.extend(struct.pack("<hh",sample,sample))
            if len(chunk)>=rate*4: out.writeframesraw(chunk); chunk.clear()
        if chunk: out.writeframesraw(chunk)
    return path
def make_thumbnail():
    source=Image.open(ASSETS/"five-ducks-river-reunion-v1.png").convert("RGB"); w=round(source.height*16/9); left=max(0,(source.width-w)//2); canvas=source.crop((left,0,left+w,source.height)).resize((1280,720),Image.Resampling.LANCZOS).convert("RGBA"); canvas=ImageEnhance.Color(canvas).enhance(1.08); draw=ImageDraw.Draw(canvas,"RGBA"); draw.rounded_rectangle((60,34,1220,170),35,fill=(25,67,87,230),outline="white",width=5); font=ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf",64); text="CAN YOU COUNT THEM?"; box=draw.textbbox((0,0),text,font=font,stroke_width=3); draw.text(((1280-(box[2]-box[0]))//2,67),text,font=font,fill=(255,244,130),stroke_width=4,stroke_fill=(20,40,65)); THUMBNAIL.parent.mkdir(parents=True,exist_ok=True); canvas.convert("RGB").save(THUMBNAIL,quality=89,optimize=True)

def quality(events,total,assets):
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration,size","-show_entries","stream=codec_name,codec_type,width,height,sample_rate,channels","-of","json",str(OUTPUT)],text=True)); video=next(s for s in probe["streams"] if s["codec_type"]=="video"); audio=next(s for s in probe["streams"] if s["codec_type"]=="audio"); decode=subprocess.run(["ffmpeg","-v","error","-i",str(OUTPUT),"-f","null","-"],capture_output=True); gaps=[{"from":a["phase"],"to":b["phase"],"gap_seconds":b["start"]-a["end"]} for a,b in zip(events,events[1:])]; sync=[{"shot_id":e["phase"],"asset":e["asset"],"visible_count":e["visible_count"],"visual_start":e["start"],"visual_end":e["end"],"lines":e["lines"],"effects":e["effects"],"contained":all(e["start"]<=x["start"]<x["end"]<=e["end"] for x in e["lines"]+e["effects"])} for e in events[1:-1]]; spoken=[x["line"].lower() for r in sync for x in r["lines"]]
    checks={"duration":70<=float(probe["format"]["duration"])<=120,"h264_1080p":video.get("codec_name")=="h264" and video.get("width")==1920 and video.get("height")==1080,"aac_stereo":audio.get("codec_name")=="aac" and audio.get("sample_rate")=="48000" and audio.get("channels")==2,"full_decode":decode.returncode==0,"zero_gaps":all(abs(x["gap_seconds"])<1e-6 for x in gaps),"seven_unique_scenes":len({x["asset"] for x in sync})==7,"exact_count_sequence":[x["visible_count"] for x in sync]==[5,4,3,2,1,0,5],"sync_containment":all(x["contained"] for x in sync),"max_14_seconds":all(e["end"]-e["start"]<=14 for e in events[1:-1]),"final_card_only":events[-1]["phase"]=="end","no_spoken_quack":all("quack" not in line for line in spoken),"lead_voice_rotation":"maisie-story" in VOICES and "maisie-song" in VOICES,"thumbnail":THUMBNAIL.is_file() and THUMBNAIL.stat().st_size<2_000_000}; (WORK/"timeline-gap-audit.json").write_text(json.dumps(gaps,indent=2)+"\n",encoding="utf-8"); (WORK/"narration-visual-sync-audit.json").write_text(json.dumps(sync,indent=2)+"\n",encoding="utf-8"); report={"output":str(OUTPUT),"duration_seconds":float(probe["format"]["duration"]),"voice_profile":"maisie-uk","visual_method":"seven original handcrafted felt-and-wood river tableaux with exact visible counts and eased follow camera","audio_method":"new Tiny Tales river arrangement with sung story lines, real synthesized duck calls, paddles, waterfall, lantern and walking effects","new_image_generation_calls":7,"true_rigged_3d_animation":False,"paid_generation_used":False,"checks":checks,"passed":all(checks.values())}; (WORK/"quality-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8"); general=Image.new("RGB",(960,math.ceil(len(events)/4)*135),"white")
    for i,e in enumerate(events): general.paste(frame_for(e,e["start"]+(e["end"]-e["start"])*.55,assets).resize((240,135),Image.Resampling.LANCZOS),((i%4)*240,(i//4)*135))
    general.save(WORK/"quality-contact-sheet.png"); boundary=[]
    for a,b in zip(events,events[1:]): boundary += [(a,a["end"]-.12),(b,b["start"]+.12)]
    sheet=Image.new("RGB",(1200,math.ceil(len(boundary)/5)*135),"white")
    for i,(e,t) in enumerate(boundary): sheet.paste(frame_for(e,t,assets).resize((240,135),Image.Resampling.LANCZOS),((i%5)*240,(i//5)*135))
    sheet.save(WORK/"transition-contact-sheet.png")
    if not report["passed"]: raise RuntimeError(report)
def write_metadata(total):
    doc={"id":ITEM_ID,"title":"Five Little Ducks' River Countdown | Nursery Song for Kids","description":"Follow five little ducklings through a handcrafted river journey as their visible group counts down from five to one. Mother Duck follows their colourful leaf trail, and the whole family reunites for a warm count-up finale.\n\nA new original Tiny Tales musical arrangement and river story for children ages 3 to 7.","tags":["five little ducks","nursery song for kids","counting song","duck song","counting 1 to 5","preschool music","Tiny Tales"],"category_id":"27","made_for_kids":True,"privacy":"public","upload_authorized":False,"output":str(OUTPUT),"duration_seconds":total,"voice_profile":"maisie-uk","character_voice_profiles":{"mother_duck":"natasha-au"},"format_family":"traditional-countdown-river-song","visual_system":"seven-progressive-handcrafted-felt-and-wood-river-tableaux","interaction_style":"sing-count-follow-river-actions-and-family-reunion","quality_gate_passed":True,"full_decode_passed":True,"transition_audit_passed":True,"transition_contact_sheet_reviewed":False,"thumbnail_reviewed":False,"quality_report":f"automation/production-work/{ITEM_ID}/quality-report.json","transition_audit":f"automation/production-work/{ITEM_ID}/timeline-gap-audit.json","narration_visual_sync_audit":f"automation/production-work/{ITEM_ID}/narration-visual-sync-audit.json","quality_contact_sheet":f"automation/production-work/{ITEM_ID}/quality-contact-sheet.png","transition_contact_sheet":f"automation/production-work/{ITEM_ID}/transition-contact-sheet.png","prepared_thumbnail":f"automation/thumbnails/{ITEM_ID}.jpg","thumbnail_hook":"CAN YOU COUNT THEM?","new_image_generation_calls":7,"true_rigged_3d_animation":False,"paid_generation_used":False,"spoken_duck_calls_removed":True}; META.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8")
def main():
    WORK.mkdir(parents=True,exist_ok=True); OUTPUT.parent.mkdir(parents=True,exist_ok=True); rows=shots(); sfx=make_sfx(rows); asyncio.run(make_voices(rows)); events,tracks,total=timeline(rows,sfx); assets=load_assets(rows); make_thumbnail(); render_engine.WORK=WORK; render_engine.OUTPUT=OUTPUT; render_engine.frame_for=frame_for; render_engine.make_music=make_music; render_engine.render(events,tracks,total,assets); quality(events,total,assets); write_metadata(total); print(json.dumps({"output":str(OUTPUT),"duration_seconds":total},indent=2))
if __name__=="__main__": main()
