import asyncio
import json
import math
import struct
import subprocess
import wave
from pathlib import Path

import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance


ROOT=Path(__file__).resolve().parent
WORK=ROOT/"preschool-jokes-work"
W,H,ART_FPS,VIDEO_FPS=1280,720,8,24
VOICE="en-US-AnaNeural"
FONT_BOLD="C:/Windows/Fonts/arialbd.ttf"
FONT="C:/Windows/Fonts/arial.ttf"

JOKES=[
 {"image":"joke-01-monkey-key.png","question":"What kind of key opens a banana?","answer":"A MONKEY!","explain":"Listen carefully: mon-KEY! The word monkey ends with key, and a monkey opens a banana by peeling it.","word":"MON-KEY","highlight":"KEY"},
 {"image":"joke-02-dino-snore.png","question":"What do you call a sleeping dinosaur?","answer":"A DINO-SNORE!","explain":"Dino-snore sounds like dinosaur. This sleepy dinosaur is making a great big snore!","word":"DINO-SNORE","highlight":"SNORE"},
 {"image":"joke-03-chicken-slide.png","question":"Why did the chicken cross the playground?","answer":"TO GET TO THE OTHER SLIDE!","explain":"We usually hear, other side. But at a playground, the chicken wants the other slide!","word":"OTHER SLIDE","highlight":"SLIDE"},
 {"image":"joke-04-honeycomb.png","question":"What does a bee use to brush its hair?","answer":"A HONEYCOMB!","explain":"A honeycomb holds honey, and the word ends with comb. This bee uses it like a hair comb!","word":"HONEY-COMB","highlight":"COMB"},
 {"image":"joke-05-french-flies.png","question":"What do frogs like with their burgers?","answer":"FRENCH FLIES!","explain":"French fries are potato snacks. But this silly frog orders French flies, because frogs like little flies!","word":"FRENCH FLIES","highlight":"FLIES"},
 {"image":"joke-06-chili-dog.png","question":"What do you call a very cold dog?","answer":"A CHILI DOG!","explain":"This puppy feels chilly. Brrr! Chilly dog sounds just like chili dog.","word":"CHILLY DOG","highlight":"CHILLY"},
 {"image":"joke-07-moo-vies.png","question":"Where do cows go for entertainment?","answer":"TO THE MOO-VIES!","explain":"Movies are shown at a cinema. But a cow says moo, so this cow goes to the moo-vies!","word":"MOO-VIES","highlight":"MOO"},
 {"image":"joke-08-gummy-bear.png","question":"What do you call a bear with no teeth?","answer":"A GUMMY BEAR!","explain":"Without teeth, a bear would use its gums. And gummy bears are chewy little bear-shaped treats!","word":"GUMMY BEAR","highlight":"GUMMY"},
 {"image":"joke-09-funny-bunny.png","question":"What do you call a rabbit who tells jokes?","answer":"A FUNNY BUNNY!","explain":"Funny and bunny rhyme. This funny bunny loves making everyone laugh!","word":"FUNNY BUNNY","highlight":"FUNNY"},
]

for j in JOKES:
    j["art"]=Image.open(ROOT/j["image"]).convert("RGB").resize((W,H),Image.Resampling.LANCZOS)


def font(size,bold=True):return ImageFont.truetype(FONT_BOLD if bold else FONT,size)


def fit_font(draw,text,max_width,start=46,min_size=24):
    size=start
    while size>min_size and draw.textbbox((0,0),text,font=font(size))[2]>max_width:size-=2
    return font(size)


def center(draw,text,y,fnt,fill):
    bb=draw.textbbox((0,0),text,font=fnt);draw.text(((W-(bb[2]-bb[0]))/2,y),text,font=fnt,fill=fill)


def question_bg(t,part):
    colors=[((92,193,235),(255,224,104)),((130,211,142),(255,170,114)),((174,145,232),(113,207,224))]
    a,b=colors[part-1];im=Image.new("RGB",(W,H));d=ImageDraw.Draw(im,"RGBA")
    for y in range(H):
        q=y/(H-1);c=tuple(int(a[k]*(1-q)+b[k]*q) for k in range(3))
        d.line((0,y,W,y),fill=c)
    for i in range(22):
        x=(i*97+int(t*32))%(W+60)-30;y=90+(i*71+int(t*45))%540;r=8+(i%4)*3
        d.ellipse((x-r,y-r,x+r,y+r),fill=(255,255,255,65))
    return im


def panel(draw,box,outline=(255,176,44,255),fill=(255,252,237,246),width=5,radius=26):
    draw.rounded_rectangle(box,radius=radius,fill=fill,outline=outline,width=width)


def draw_title(frame,part,subtitle=None):
    d=ImageDraw.Draw(frame,"RGBA");panel(d,(245,20,1035,94))
    center(d,f"SILLY ANIMAL JOKES — PART {part}",36,font(34),(40,70,95,255))
    if subtitle:
        panel(d,(250,620,1030,690),outline=(70,167,216,255),width=4)
        center(d,subtitle,638,fit_font(d,subtitle,720,30),(38,68,92,255))


def draw_question(frame,part,num,text,t):
    d=ImageDraw.Draw(frame,"RGBA");draw_title(frame,part)
    panel(d,(80,150,1200,490),outline=(255,255,255,235),fill=(255,252,238,235),width=6,radius=38)
    center(d,f"JOKE {num}",185,font(32),(229,84,76,255))
    words=text.split();lines=[];line=""
    for w in words:
        test=(line+" "+w).strip()
        if d.textbbox((0,0),test,font=font(46))[2]>980 and line:lines.append(line);line=w
        else:line=test
    if line:lines.append(line)
    y=255-(len(lines)-1)*30
    for ln in lines:center(d,ln,y,font(46),(34,65,90,255));y+=66
    pulse=1+.08*math.sin(t*3);r=45*pulse
    d.ellipse((W/2-r,500-r,W/2+r,500+r),fill=(255,191,52,235),outline=(255,255,255,235),width=5)
    center(d,"?",465,font(60),(255,255,255,255))


def highlighted_word(draw,joke,y):
    word=joke["word"];hi=joke["highlight"]
    f=font(48);pre,sep,post=word.partition(hi)
    widths=[draw.textbbox((0,0),s,font=f)[2] for s in (pre,hi,post)]
    x=(W-sum(widths))/2
    if pre:draw.text((x,y),pre,font=f,fill=(38,69,95));x+=widths[0]
    draw.rounded_rectangle((x-8,y-4,x+widths[1]+8,y+60),radius=12,fill=(255,224,84,230))
    draw.text((x,y),hi,font=f,fill=(218,68,61));x+=widths[1]
    if post:draw.text((x,y),post,font=f,fill=(38,69,95))


def draw_reveal(frame,part,joke,phase,t):
    # Gentle living-camera movement plus sparkles; never crop the focal animal.
    scale=1.0+.018*math.sin(t*.65)
    if scale!=1:
        nw,nh=int(W*scale),int(H*scale);im=frame.resize((nw,nh),Image.Resampling.LANCZOS)
        frame.paste(im.crop(((nw-W)//2,(nh-H)//2,(nw+W)//2,(nh+H)//2)))
    frame.alpha_composite(Image.new("RGBA",(W,H),(0,0,0,22)))
    d=ImageDraw.Draw(frame,"RGBA")
    draw_title(frame,part)
    for i in range(14):
        a=i*.9+t*1.1;x=640+500*math.sin(a);y=155+400*((i*73+int(t*55))%400)/400
        rr=4+2*math.sin(t*4+i);d.ellipse((x-rr,y-rr,x+rr,y+rr),fill=(255,220,70,190))
    if phase=="answer":
        panel(d,(110,545,1170,680),outline=(255,92,82,255),fill=(255,250,233,246),width=6)
        center(d,joke["answer"],578,fit_font(d,joke["answer"],980,46),(218,67,61,255))
    else:
        panel(d,(160,530,1120,690),outline=(74,169,217,255),fill=(255,252,239,247),width=5)
        highlighted_word(d,joke,556)


def make_frame(part,jokes,t,timeline):
    event=next((e for e in timeline if e["start"]<=t<e["end"]),timeline[-1])
    kind=event["kind"]
    if kind in ("intro","question","pause","outro"):
        frame=question_bg(t,part).convert("RGBA")
        if kind=="intro":
            draw_title(frame,part)
            d=ImageDraw.Draw(frame,"RGBA");panel(d,(190,170,1090,535),outline=(255,255,255,240),fill=(255,252,235,235),width=7,radius=40)
            center(d,"3 GIGGLE-TASTIC JOKES!",235,font(46),(223,74,67,255));center(d,"Listen • Guess • Laugh",330,font(38),(41,88,119,255))
            center(d,"Are you ready?",415,font(42),(69,164,112,255))
        elif kind in ("question","pause"):
            draw_question(frame,part,event["joke_no"],event["joke"]["question"],t)
        else:
            draw_title(frame,part)
            d=ImageDraw.Draw(frame,"RGBA");panel(d,(180,175,1100,555),outline=(255,255,255,240),fill=(255,252,235,237),width=7,radius=40)
            center(d,"THANKS FOR GIGGLING!",240,font(48),(223,74,67,255))
            center(d,"Which joke was your favorite?",340,font(38),(38,75,101,255))
            if t>=event.get("subscribe_at",event["end"]):
                panel(d,(315,430,965,520),outline=(255,92,82,255),width=5)
                center(d,"LIKE & SUBSCRIBE",452,font(40),(218,67,61,255))
        return frame.convert("RGB")
    joke=event["joke"];frame=joke["art"].copy().convert("RGBA")
    phase="answer" if kind in ("answer","answer_gap") else "explain"
    draw_reveal(frame,part,joke,phase,t)
    return frame.convert("RGB")


def speech_path(name):return WORK/f"jokes-{name}.mp3"


async def make_voice_assets():
    WORK.mkdir(exist_ok=True);tasks=[]
    for p in range(1,4):
        tasks.append((f"p{p}-intro",f"Welcome to Silly Animal Jokes, Part {p}! Listen carefully, make your best guess, and get ready to giggle."))
        tasks.append((f"p{p}-outro","Thanks for giggling with us! Which joke was your favorite? Please like and subscribe for more silly jokes. See you next time!"))
    for i,j in enumerate(JOKES,1):
        tasks += [(f"j{i}-q",j["question"]),(f"j{i}-a",j["answer"]),(f"j{i}-e",j["explain"])]
    tasks.append(("laugh","Ha ha ha! Hee hee hee!"))
    for key,text in tasks:
        path=speech_path(key)
        if not path.exists():
            print("Voice:",key,flush=True)
            rate="+12%" if key=="laugh" else "-6%";pitch="+12Hz" if key=="laugh" else "+5Hz"
            await edge_tts.Communicate(text,VOICE,rate=rate,pitch=pitch,volume="-3%").save(str(path))


def probe(path):
    r=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","json",str(path)],capture_output=True,text=True,check=True)
    return float(json.loads(r.stdout)["format"]["duration"])


def build_part(part):
    jokes=JOKES[(part-1)*3:part*3];timeline=[];voices=[];cursor=.3
    def add(kind,dur,**kw):
        nonlocal cursor
        e={"kind":kind,"start":cursor,"end":cursor+dur,**kw};timeline.append(e);cursor=e["end"]
        return e
    ik=f"p{part}-intro";id=probe(speech_path(ik));add("intro",id+.5);voices.append((ik,.3,1.15))
    laugh_d=probe(speech_path("laugh"));aud=[]
    for n,j in enumerate(jokes,1):
        qi=(part-1)*3+n;qk=f"j{qi}-q";ak=f"j{qi}-a";ek=f"j{qi}-e"
        qd,ad,ed=probe(speech_path(qk)),probe(speech_path(ak)),probe(speech_path(ek))
        qe=add("question",qd,joke=j,joke_no=n);voices.append((qk,qe["start"],1.17))
        add("pause",4.5,joke=j,joke_no=n)
        ae=add("answer",ad,joke=j,joke_no=n);voices.append((ak,ae["start"],1.2))
        add("answer_gap",.3,joke=j,joke_no=n)
        ee=add("explain",ed,joke=j,joke_no=n);voices.append((ek,ee["start"],1.16))
        add("explain_gap",.28,joke=j,joke_no=n)
        laugh_start=cursor;add("laugh_visual",laugh_d,joke=j,joke_no=n);voices.append(("laugh",laugh_start,.62))
        aud.append(f"joke {n}: explanation_end={ee['end']:.3f} laugh_start={laugh_start:.3f} gap={laugh_start-ee['end']:.3f}")
        add("laugh_gap",.7,joke=j,joke_no=n)
    ok=f"p{part}-outro";od=probe(speech_path(ok));oe=add("outro",od+.9,subscribe_at=cursor+od*.53);voices.append((ok,oe["start"],1.15))
    duration=math.ceil(cursor*ART_FPS)/ART_FPS
    (WORK/f"part-{part}-laughter-audit.txt").write_text("\n".join(aud),encoding="utf-8")
    return jokes,timeline,voices,duration


def make_music(duration,part):
    sr=24000;n=int(duration*sr);path=WORK/f"part-{part}-music.wav";notes=[261.63,329.63,392,523.25,392,329.63]
    with wave.open(str(path),"wb") as wf:
        wf.setnchannels(1);wf.setsampwidth(2);wf.setframerate(sr);block=bytearray()
        for i in range(n):
            t=i/sr;f=notes[int(t/1.25)%len(notes)];pos=t%.625;env=math.exp(-5*pos)
            v=.012*math.sin(2*math.pi*(f/2)*t)+.018*env*math.sin(2*math.pi*f*t)
            block+=struct.pack("<h",int(v*32767))
            if len(block)>=sr*4:wf.writeframes(block);block.clear()
        if block:wf.writeframes(block)
    return path


def render_part(part,jokes,timeline,voices,duration):
    silent=WORK/f"part-{part}-silent.mp4";output=ROOT/f"silly-animal-jokes-part-{part}.mp4";total=math.ceil(duration*ART_FPS)
    cmd=["ffmpeg","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(ART_FPS),"-i","-","-an","-vf",f"fps={VIDEO_FPS}","-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p",str(silent)]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    for i in range(total):
        if i%(ART_FPS*10)==0:print(f"Part {part}: {i//ART_FPS}/{math.ceil(duration)} seconds",flush=True)
        p.stdin.write(make_frame(part,jokes,i/ART_FPS,timeline).tobytes())
    p.stdin.close()
    if p.wait()!=0:raise RuntimeError("render failed")
    music=make_music(duration,part);inputs=["-i",str(silent),"-i",str(music)];filters=["[1:a]volume=.40[m]"];labels=["[m]"]
    for idx,(key,start,vol) in enumerate(voices,2):
        inputs += ["-i",str(speech_path(key))];delay=round(start*1000);filters.append(f"[{idx}:a]adelay={delay}|{delay},volume={vol}[v{idx}]");labels.append(f"[v{idx}]")
    filters.append("".join(labels)+f"amix=inputs={len(labels)}:normalize=0,alimiter=limit=.88[a]")
    cmd=["ffmpeg","-y"]+inputs+["-filter_complex",";".join(filters),"-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","144k","-ar","24000","-ac","1","-t",f"{duration:.3f}","-movflags","+faststart",str(output)]
    subprocess.run(cmd,check=True)
    # Contact sheet: question, answer and explanation for every joke, plus ending.
    times=[]
    for e in timeline:
        if e["kind"] in ("question","answer","explain"):times.append((e["start"]+min(1,e["end"]-e["start"]-.05)))
    times.append(duration-2)
    sh=Image.new("RGB",(960,math.ceil(len(times)/3)*180),"white")
    for i,t in enumerate(times):
        im=make_frame(part,jokes,t,timeline).resize((320,180),Image.Resampling.LANCZOS);d=ImageDraw.Draw(im);d.rectangle((0,0,68,23),fill="black");d.text((4,3),f"{t:.1f}s",font=font(13),fill="white");sh.paste(im,((i%3)*320,(i//3)*180))
    sh.save(ROOT/f"silly-animal-jokes-part-{part}-contact-sheet.png")
    return output


async def main():
    await make_voice_assets()
    for part in range(1,4):
        jokes,timeline,voices,duration=build_part(part);out=render_part(part,jokes,timeline,voices,duration);print(out)


if __name__=="__main__":asyncio.run(main())
