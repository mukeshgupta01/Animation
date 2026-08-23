import asyncio
import json
import math
import struct
import subprocess
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import edge_tts


ROOT = Path(__file__).resolve().parent
WORK = ROOT / "lost-rainbow-work"
OUTPUT = ROOT / "the-lost-rainbow-adventure.mp4"
SILENT = WORK / "lost-rainbow-silent.mp4"
CONTACT = ROOT / "lost-rainbow-motion-contact-sheet.png"
W, H, VIDEO_FPS, ART_FPS = 1280, 720, 24, 8
# Ana is a youthful neural voice.  Use a calmer, slightly lower delivery for the
# storyteller and a brighter delivery for Pip so both roles sound like children
# while remaining easy to distinguish.
NARRATOR = "en-US-AnaNeural"
PIP_VOICE = "en-US-AnaNeural"
NARRATOR_RATE, PIP_RATE = "-13%", "-8%"
NARRATOR_PITCH, PIP_PITCH = "-2Hz", "+8Hz"
VOICE_CUT = "child-voices"

SCENES = [
    {"name": "RED FLOWER MEADOW", "color": "red", "rgb": (239, 72, 65), "bg": ROOT / "rainbow-red-meadow.png",
     "activity": "POINT TO 3 RED FLOWERS", "kind": "flowers",
     "arrival": "Pip and you arrive in the Red Flower Meadow. The poppies dance in the breeze, but their special red glow is missing.",
     "prompt": "Can you point to three red flowers? Look carefully, and take your time.",
     "success": "Wonderful! The flowers are glowing. Reach out and catch the red sparkle!",
     "reaction": "Red is back! One beautiful color found."},
    {"name": "ORANGE BUTTERFLY ORCHARD", "color": "orange", "rgb": (247, 145, 43), "bg": ROOT / "rainbow-orange-orchard.png",
     "activity": "FLUTTER YOUR ARMS GENTLY", "kind": "butterfly",
     "arrival": "Next, Pip floats into the Orange Butterfly Orchard. The trees are bright, but the little butterfly is too sleepy to fly.",
     "prompt": "Flutter your arms gently like butterfly wings. Can you help it wake up?",
     "success": "There it goes! The butterfly loops through the sunshine and leaves an orange sparkle behind.",
     "reaction": "Orange is back! Our rainbow is growing."},
    {"name": "YELLOW SUNSHINE HILL", "color": "yellow", "rgb": (255, 213, 61), "bg": ROOT / "rainbow-yellow-hill.png",
     "activity": "CLAP 3 TIMES", "kind": "sun",
     "arrival": "Now you reach Yellow Sunshine Hill. The sunflowers are waiting for the warm yellow light to shine.",
     "prompt": "Clap three gentle times to wake the sunshine. Ready?",
     "success": "The hill is glowing! A golden yellow sparkle is dancing toward Pip.",
     "reaction": "Yellow is back! Everything feels warm and bright."},
    {"name": "GREEN GROWING FOREST", "color": "green", "rgb": (73, 181, 93), "bg": ROOT / "rainbow-green-forest.png",
     "activity": "STRETCH UP LIKE A TREE", "kind": "grow",
     "arrival": "The path leads into the Green Growing Forest. Tiny sprouts peek from the ground, ready to grow tall.",
     "prompt": "Stretch your arms up high like a growing tree. Hold your stretch while the forest grows.",
     "success": "Look at those new leaves! A fresh green sparkle has appeared between the trees.",
     "reaction": "Green is back! Thank you for helping the forest."},
    {"name": "BLUE SINGING RIVER", "color": "blue", "rgb": (55, 151, 235), "bg": ROOT / "rainbow-blue-river.png",
     "activity": "SWAY LIKE THE RIVER", "kind": "river",
     "arrival": "Soon, Pip reaches the Blue Singing River. The water is quiet and needs your gentle movement.",
     "prompt": "Sway slowly from side to side like the river. Keep going, nice and gently.",
     "success": "The river is flowing and sparkling again! A blue light rises from the water.",
     "reaction": "Blue is back! Only one color is still missing."},
    {"name": "PURPLE STAR GARDEN", "color": "purple", "rgb": (151, 92, 214), "bg": ROOT / "rainbow-purple-garden.png",
     "activity": "TWINKLE YOUR FINGERS", "kind": "stars",
     "arrival": "At last, you enter the Purple Star Garden. The sky is waiting for its tiny stars to twinkle.",
     "prompt": "Wiggle your fingers like little stars. Make them sparkle softly across the sky.",
     "success": "Beautiful! The stars are shining, and the final purple sparkle is flying to Pip.",
     "reaction": "Purple is back! We found every color!"},
]

RAINBOW = [(239, 72, 65), (247, 145, 43), (255, 213, 61), (73, 181, 93), (55, 151, 235), (151, 92, 214)]
LINES = []
VOICE_DUR = {}
SPEAKING = []
INTRO_END = 18.0
FINAL_START = 0.0
DURATION = 0.0
BACKGROUNDS = []


def font(size, bold=False):
    for name in (["arialbd.ttf", "calibrib.ttf"] if bold else ["arial.ttf", "calibri.ttf"]):
        p = Path("C:/Windows/Fonts") / name
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


F18, F24, F30, F42, F56 = font(18, True), font(24, True), font(30, True), font(42, True), font(56, True)


def fit_overscan(path):
    src = Image.open(path).convert("RGB")
    tw, th = W + 50, H + 30
    scale = max(tw / src.width, th / src.height)
    res = src.resize((round(src.width * scale), round(src.height * scale)), Image.Resampling.LANCZOS)
    left = (res.width - tw) // 2; top = (res.height - th) // 2
    return res.crop((left, top, left + tw, top + th)).convert("RGBA")


def cover(frame, box, fill=(255, 253, 235, 235), outline=(255, 193, 52, 255), radius=24, width=4):
    ImageDraw.Draw(frame, "RGBA").rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def centered(draw, xy, text, fnt, fill, stroke=0):
    draw.text(xy, text, anchor="mm", font=fnt, fill=fill, stroke_width=stroke, stroke_fill=(255, 255, 255, 255))


def smooth(p):
    p = max(0.0, min(1.0, p)); return p * p * (3 - 2 * p)


def star_points(cx, cy, outer, inner, count=5, phase=-math.pi / 2):
    pts = []
    for i in range(count * 2):
        a = phase + i * math.pi / count; r = outer if i % 2 == 0 else inner
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def speaking_at(t, speaker="pip"):
    return any(sp == speaker and start <= t <= end for start, end, sp in SPEAKING)


def draw_pip(frame, t, x, y, scale=1.0, happy=True, wave=False):
    layer = Image.new("RGBA", frame.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer, "RGBA")
    bob = math.sin(t * 2.2) * 7 * scale; x, y = x, y + bob
    shadow_w = 150 * scale; d.ellipse((x-shadow_w/2, y+76*scale, x+shadow_w/2, y+102*scale), fill=(55, 91, 126, 40))
    outline = (160, 215, 244, 255); white = (255, 255, 255, 255)
    blobs = [(-92, 10, 70), (-45, -38, 83), (22, -46, 92), (88, 0, 72), (10, 28, 108)]
    for bx, by, r in blobs:
        box = (x+(bx-r)*scale, y+(by-r)*scale, x+(bx+r)*scale, y+(by+r)*scale)
        d.ellipse(box, fill=white, outline=outline, width=max(2, round(4*scale)))
    # Arms move continuously, and one arm waves during celebrations.
    arm_y = y + 26 * scale
    left_end = (x - 142*scale, arm_y + math.sin(t*3)*12*scale)
    right_lift = -52*scale if wave else math.sin(t*2.5+1)*12*scale
    right_end = (x + 145*scale, arm_y + right_lift)
    d.line((x-80*scale, arm_y, left_end[0], left_end[1]), fill=outline, width=max(3, round(7*scale)))
    d.line((x+78*scale, arm_y, right_end[0], right_end[1]), fill=outline, width=max(3, round(7*scale)))
    d.ellipse((left_end[0]-8*scale, left_end[1]-8*scale, left_end[0]+8*scale, left_end[1]+8*scale), fill=white, outline=outline, width=2)
    d.ellipse((right_end[0]-8*scale, right_end[1]-8*scale, right_end[0]+8*scale, right_end[1]+8*scale), fill=white, outline=outline, width=2)
    blink = (t % 4.8) < .14
    eye_y = y - 12*scale
    for ex in (x-33*scale, x+33*scale):
        if blink:
            d.line((ex-11*scale, eye_y, ex+11*scale, eye_y), fill=(36, 69, 92, 255), width=max(2, round(4*scale)))
        else:
            d.ellipse((ex-11*scale, eye_y-15*scale, ex+11*scale, eye_y+15*scale), fill=(36, 69, 92, 255))
            d.ellipse((ex-4*scale, eye_y-10*scale, ex+2*scale, eye_y-4*scale), fill=white)
    d.ellipse((x-63*scale, y+10*scale, x-43*scale, y+24*scale), fill=(255, 155, 165, 135))
    d.ellipse((x+43*scale, y+10*scale, x+63*scale, y+24*scale), fill=(255, 155, 165, 135))
    talking = speaking_at(t, "pip")
    if talking and int(t * 7) % 2 == 0:
        d.ellipse((x-14*scale, y+17*scale, x+14*scale, y+46*scale), fill=(96, 55, 75, 255))
    elif happy:
        d.arc((x-25*scale, y+8*scale, x+25*scale, y+43*scale), 10, 170, fill=(96, 55, 75, 255), width=max(2, round(5*scale)))
    else:
        d.arc((x-22*scale, y+24*scale, x+22*scale, y+50*scale), 190, 350, fill=(96, 55, 75, 255), width=max(2, round(5*scale)))
    frame.alpha_composite(layer)


def draw_collected(frame, t, x, y, count):
    d = ImageDraw.Draw(frame, "RGBA")
    for i in range(count):
        a = t * .8 + i * (2 * math.pi / max(1, count)); r = 125
        cx = x + math.cos(a) * r; cy = y + math.sin(a) * 43 - 90
        d.ellipse((cx-13, cy-13, cx+13, cy+13), fill=RAINBOW[i] + (235,), outline=(255,255,255,240), width=3)
        d.ellipse((cx-5, cy-7, cx, cy-2), fill=(255,255,255,180))


def draw_magic_flight(frame, scene, t, pip_x, pip_y):
    p = smooth((t - scene["reveal"]) / 2.8)
    if p <= 0 or p >= 1: return
    sx, sy = (985, 240) if scene["kind"] in ("sun", "stars") else (730, 420)
    cx = (1-p)*(1-p)*sx + 2*(1-p)*p*850 + p*p*pip_x
    cy = (1-p)*(1-p)*sy + 2*(1-p)*p*160 + p*p*(pip_y-65)
    d = ImageDraw.Draw(frame, "RGBA")
    for k in range(6, 0, -1):
        q = max(0, p-k*.035); tx = (1-q)*(1-q)*sx + 2*(1-q)*q*850 + q*q*pip_x; ty = (1-q)*(1-q)*sy + 2*(1-q)*q*160 + q*q*(pip_y-65)
        d.ellipse((tx-5-k, ty-5-k, tx+5+k, ty+5+k), fill=scene["rgb"] + (35+k*22,))
    d.polygon(star_points(cx, cy, 25, 11), fill=scene["rgb"] + (255,), outline=(255,255,255,255))


def draw_butterfly(frame, t, scene):
    local = t - scene["start"]; active = local > 5
    x = 790 + math.sin(local*.7)*150; y = 270 + math.sin(local*1.3)*55
    flap = .35 + .65*abs(math.sin(t*8)) if active else .22
    d = ImageDraw.Draw(frame, "RGBA"); orange = (247,145,43,235); brown=(100,61,40,255)
    d.ellipse((x-5,y-20,x+5,y+22), fill=brown)
    d.ellipse((x-48*flap,y-38,x-4,y+5), fill=orange, outline=(255,225,150,255), width=3)
    d.ellipse((x+4,y-38,x+48*flap,y+5), fill=orange, outline=(255,225,150,255), width=3)
    d.ellipse((x-35*flap,y,x-3,y+30), fill=(255,187,75,230)); d.ellipse((x+3,y,x+35*flap,y+30), fill=(255,187,75,230))


def draw_activity(frame, scene, t):
    d = ImageDraw.Draw(frame, "RGBA"); kind = scene["kind"]
    qstart, reveal = scene["prompt_start"], scene["reveal"]
    quiet_p = smooth((t-qstart) / max(.1, reveal-qstart))
    if kind == "flowers":
        for i, x in enumerate([420, 545, 680, 820]):
            sway = math.sin(t*2+i)*10
            d.line((x,650,x+sway,570), fill=(49,140,65,230), width=7)
            d.ellipse((x+sway-23,540,x+sway+23,583), fill=(239,72,65,235), outline=(255,220,170,230), width=2)
    elif kind == "butterfly":
        draw_butterfly(frame, t, scene)
    elif kind == "sun":
        for pulse in [reveal-4.1, reveal-2.8, reveal-1.5]:
            age = t-pulse
            if 0 <= age <= 1.2:
                r = 55 + age*90; alpha=int(130*(1-age/1.2))
                d.ellipse((910-r,145-r,910+r,145+r), outline=(255,225,70,alpha), width=12)
    elif kind == "grow":
        for i,x in enumerate([475,610,750,875]):
            p = smooth(quiet_p*1.2-i*.08); top=650-p*125
            d.line((x,665,x,top), fill=(44,130,67,240), width=7)
            if p>.3:
                d.ellipse((x-34,top+20,x,top+50), fill=(77,181,93,235)); d.ellipse((x,top+3,x+34,top+34), fill=(95,198,105,235))
    elif kind == "river":
        off=(t*70)%80
        for y in [520,575,630]:
            for x in range(-80,1360,160):
                d.arc((x+off,y-18,x+off+110,y+18), 200,340, fill=(185,235,255,190), width=5)
    elif kind == "stars":
        for i,(x,y) in enumerate([(430,180),(570,130),(715,205),(850,145),(980,225),(1050,115)]):
            p=smooth(quiet_p*1.25-i*.07); r=5+p*(12+5*math.sin(t*4+i))
            d.polygon(star_points(x,y,r,r*.45), fill=(255,241,183,int(220*p)))


def draw_banner(frame, text, color, y=610, width=770):
    x1=(W-width)//2; x2=x1+width
    cover(frame,(x1,y-38,x2,y+38),fill=(255,253,235,238),outline=color+(255,),radius=24,width=4)
    centered(ImageDraw.Draw(frame,"RGBA"),(W//2,y),text,F30,(28,65,92,255))


def background_at(index, t):
    bg=BACKGROUNDS[index]; dx=round(12*math.sin(t*.13+index)); dy=round(5*math.sin(t*.17+index))
    return bg.crop((25+dx,15+dy,25+dx+W,15+dy+H))


def scene_frame(scene, index, t):
    frame=background_at(index,t)
    local=t-scene["start"]
    # Crossfade from the previous location while Pip travels.
    if index>0 and local<1.2:
        prev=background_at(index-1,t); frame=Image.blend(prev,frame,smooth(local/1.2))
    frame.alpha_composite(Image.new("RGBA",frame.size,(255,248,215,12)))
    pip_x=240+25*math.sin(t*.45); pip_y=380
    if local<2.0: pip_x=-190+smooth(local/2.0)*430
    if scene["end"]-t<1.4: pip_x=240+smooth((1.4-(scene["end"]-t))/1.4)*1250
    draw_activity(frame,scene,t)
    collected=index + (1 if t>=scene["reveal"]+2.75 else 0)
    draw_collected(frame,t,pip_x,pip_y,collected)
    draw_pip(frame,t,pip_x,pip_y,scale=.72,happy=True,wave=t>=scene["reveal"])
    draw_magic_flight(frame,scene,t,pip_x,pip_y)
    d=ImageDraw.Draw(frame,"RGBA")
    if local<4.3:
        alpha=int(255*min(1,local/.6)*min(1,(4.3-local)/.8))
        cover(frame,(280,22,1000,92),fill=(255,253,235,max(0,alpha-20)),outline=scene["rgb"]+(alpha,),radius=22,width=4)
        centered(d,(640,57),scene["name"],F30,(25,62,91,alpha))
    if scene["prompt_start"]<=t<scene["reveal"]:
        draw_banner(frame,scene["activity"],scene["rgb"])
    elif scene["reveal"]<=t<scene["reveal"]+4.8:
        draw_banner(frame,scene["color"].upper()+" IS BACK!",scene["rgb"])
    return frame


def draw_rainbow(frame,t):
    d=ImageDraw.Draw(frame,"RGBA"); elapsed=t-FINAL_START
    box=(170,65,1110,690)
    for i,color in enumerate(RAINBOW):
        p=smooth((elapsed-1.5-i*.48)/2.0)
        if p>0:
            inset=i*27; b=(box[0]+inset,box[1]+inset,box[2]-inset,box[3]-inset)
            d.arc(b,185,185+170*p,fill=color+(245,),width=25)


def intro_frame(t):
    frame=background_at(2,t); frame.alpha_composite(Image.new("RGBA",frame.size,(215,245,255,35)))
    worried = 8.7 <= t <= 14.9
    draw_pip(frame,t,640,345,scale=1.05,happy=not worried,wave=False)
    d=ImageDraw.Draw(frame,"RGBA")
    if t<5.8:
        cover(frame,(170,65,1110,190),fill=(255,253,235,235),radius=30,width=5)
        centered(d,(640,110),"THE LOST RAINBOW",F56,(42,72,111,255),1)
        centered(d,(640,165),"A colorful adventure with Pip",F24,(40,157,151,255))
    elif t>8:
        cover(frame,(245,555,1035,650),fill=(255,253,235,235),radius=25,width=4)
        centered(d,(640,602),"HELP PIP FIND 6 MISSING COLORS",F30,(42,72,111,255))
    return frame


def final_frame(t):
    frame=background_at(0,t); frame.alpha_composite(Image.new("RGBA",frame.size,(255,247,215,25)))
    draw_rainbow(frame,t)
    draw_pip(frame,t,640,430,scale=.9,happy=True,wave=True)
    draw_collected(frame,t,640,430,6)
    d=ImageDraw.Draw(frame,"RGBA"); elapsed=t-FINAL_START
    if 8<elapsed<16:
        cover(frame,(210,35,1070,128),fill=(255,253,235,238),radius=26,width=5)
        centered(d,(640,82),"THE RAINBOW IS BACK!",F42,(42,72,111,255),1)
    if elapsed>=16:
        cover(frame,(190,38,1090,165),fill=(255,253,235,240),radius=28,width=5)
        centered(d,(640,82),"LIKE & SUBSCRIBE",F42,(239,72,65,255),1)
        centered(d,(640,132),"for more magical adventures!",F24,(42,72,111,255))
    # Continuous celebration sparkles.
    for i in range(22):
        x=(i*173+int(t*55))%1280; y=90+(i*91)%500; r=5+4*abs(math.sin(t*3+i))
        d.polygon(star_points(x,y,r,r*.45),fill=RAINBOW[i%6]+(170,))
    return frame


def frame_at(t):
    if t<INTRO_END: return intro_frame(t).convert("RGB")
    for i,s in enumerate(SCENES):
        if s["start"]<=t<s["end"]: return scene_frame(s,i,t).convert("RGB")
    return final_frame(t).convert("RGB")


TEXTS = [
    ("intro1","narrator","High above a sunny valley lived a little cloud named Pip. Pip loved painting rainbows across the sky."),
    ("intro2","pip","Oh no! My rainbow has lost all of its colors!"),
    ("intro3","narrator","The six colors have scattered into magical places. Pip needs your movement, imagination, and careful eyes to bring them home."),
]


async def make_speech():
    WORK.mkdir(exist_ok=True); items=list(TEXTS)
    for i,s in enumerate(SCENES):
        items += [(f"arrival{i}","narrator",s["arrival"]),(f"prompt{i}","pip",s["prompt"]),
                  (f"success{i}","narrator",s["success"]),(f"reaction{i}","pip",s["reaction"])]
    items += [("final1","narrator","You found every missing color. Watch them sweep across the sky and join together!"),
              ("final2","pip","We did it! The rainbow is brighter than ever. Thank you for being such a wonderful helper!"),
              ("subscribe","narrator","If you enjoyed helping Pip, please like and subscribe for more magical adventures. See you next time!")]
    for key,speaker,text in items:
        path=WORK/f"lost-rainbow-{VOICE_CUT}-{key}.mp3"
        if not path.exists():
            voice=PIP_VOICE if speaker=="pip" else NARRATOR
            rate=PIP_RATE if speaker=="pip" else NARRATOR_RATE
            pitch=PIP_PITCH if speaker=="pip" else NARRATOR_PITCH
            print("Narration:",key,flush=True)
            await edge_tts.Communicate(text,voice,rate=rate,pitch=pitch,volume="-2%").save(str(path))
    return items


def probe_duration(path):
    r=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","json",str(path)],capture_output=True,text=True,check=True)
    return float(json.loads(r.stdout)["format"]["duration"])


def build_timeline(items):
    global LINES,VOICE_DUR,SPEAKING,INTRO_END,FINAL_START,DURATION
    VOICE_DUR={key:probe_duration(WORK/f"lost-rainbow-{VOICE_CUT}-{key}.mp3") for key,_,_ in items}
    bykey={key:(speaker,text) for key,speaker,text in items}; LINES=[]; SPEAKING=[]
    def add(key,start):
        speaker,text=bykey[key]; end=start+VOICE_DUR[key]; LINES.append((key,start,text,speaker)); SPEAKING.append((start,end,speaker)); return end
    end=add("intro1",.3); end=add("intro2",end+.35); end=add("intro3",end+.35)
    INTRO_END=max(18.0,end+.8); cursor=INTRO_END
    response=[]
    for i,s in enumerate(SCENES):
        s["start"]=cursor; end=add(f"arrival{i}",cursor+.65); s["prompt_start"]=end+.35
        pend=add(f"prompt{i}",s["prompt_start"]); s["reveal"]=round((pend+5.0)*ART_FPS)/ART_FPS
        end=add(f"success{i}",s["reveal"]+.3); end=add(f"reaction{i}",end+.35)
        s["end"]=max(cursor+32.0,end+1.2); response.append((s["color"],pend,s["reveal"],s["reveal"]-pend)); cursor=s["end"]
    FINAL_START=cursor; end=add("final1",cursor+.7); end=add("final2",end+.4); end=add("subscribe",max(cursor+16.0,end+.6))
    DURATION=max(cursor+25.0,end+.8)
    (WORK/"lost-rainbow-activity-gap-audit.txt").write_text("\n".join(f"{c}: prompt_end={pe:.3f} magic={rv:.3f} quiet_gap={g:.3f}" for c,pe,rv,g in response),encoding="utf-8")
    report=[]
    for i,(key,start,_,speaker) in enumerate(LINES):
        end=start+VOICE_DUR[key]; nxt=LINES[i+1][1] if i+1<len(LINES) else DURATION; gap=nxt-end
        if gap<.18: raise RuntimeError(f"Voice overlap after {key}: {gap:.3f}")
        report.append(f"{key} ({speaker}): start={start:.3f} duration={VOICE_DUR[key]:.3f} end={end:.3f} gap={gap:.3f}")
    (WORK/"lost-rainbow-voice-timing.txt").write_text("\n".join(report),encoding="utf-8")


def make_audio():
    sr=24000; n=int(DURATION*sr); bed=WORK/"lost-rainbow-bed.wav"; sfx=WORK/"lost-rainbow-sfx.wav"
    notes=[261.63,329.63,392.0,440.0,349.23,392.0,493.88,440.0]
    with wave.open(str(bed),"wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); block=bytearray()
        for i in range(n):
            t=i/sr; f=notes[int(t/4)%len(notes)]; fade=min(1,t/1.5,(DURATION-t)/1.5)
            v=(.46*math.sin(2*math.pi*f*t)+.20*math.sin(2*math.pi*f/2*t)+.09*math.sin(2*math.pi*f*1.5*t))*.031*fade
            block+=struct.pack("<h",int(v*32767))
            if len(block)>=65536: wf.writeframes(block); block.clear()
        if block: wf.writeframes(block)
    data=[0.0]*n; events=[]
    for s in SCENES:
        events += [(s["start"],"whoosh"),(s["reveal"],"magic"),(s["reveal"]+1.0,"spark"),(s["reveal"]+1.7,"spark")]
        if s["kind"]=="sun": events += [(s["reveal"]-4.1,"clap"),(s["reveal"]-2.8,"clap"),(s["reveal"]-1.5,"clap")]
    events += [(FINAL_START+1.5+i*.48,"magic") for i in range(6)]
    for start,kind in events:
        n0=int(start*sr); dur={"whoosh":.55,"magic":.9,"spark":.25,"clap":.18}[kind]
        for j in range(int(dur*sr)):
            tt=j/sr
            if kind=="whoosh": v=math.sin(2*math.pi*(240+420*tt)*tt)*math.sin(math.pi*tt/dur)*.028
            elif kind=="magic": v=math.exp(-tt*3.5)*(math.sin(2*math.pi*659*tt)+.45*math.sin(2*math.pi*988*tt))*.085
            elif kind=="spark": v=math.exp(-tt*12)*math.sin(2*math.pi*1180*tt)*.045
            else: v=math.exp(-tt*20)*math.sin(2*math.pi*520*tt)*.06
            if 0<=n0+j<n: data[n0+j]+=v
    with wave.open(str(sfx),"wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        for k in range(0,n,32768): wf.writeframes(b"".join(struct.pack("<h",int(max(-1,min(1,v))*32767)) for v in data[k:k+32768]))


def render_silent():
    cmd=["ffmpeg","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(ART_FPS),"-i","-","-an","-vf",f"fps={VIDEO_FPS}","-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p",str(SILENT)]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE); total=math.ceil(DURATION*ART_FPS)
    for n in range(total):
        p.stdin.write(frame_at(n/ART_FPS).tobytes())
        if n%(ART_FPS*10)==0: print(f"Rendered {n/ART_FPS:.0f}/{DURATION:.0f} seconds",flush=True)
    p.stdin.close()
    if p.wait()!=0: raise RuntimeError("Silent render failed")


def mix_audio():
    inputs=["-i",str(SILENT),"-i",str(WORK/"lost-rainbow-bed.wav"),"-i",str(WORK/"lost-rainbow-sfx.wav")]
    filters=["[1:a]volume=.48[bed]","[2:a]volume=.90[sfx]"]; labels=["[bed]","[sfx]"]
    for idx,(key,start,_,speaker) in enumerate(LINES,3):
        inputs += ["-i",str(WORK/f"lost-rainbow-{VOICE_CUT}-{key}.mp3")]; delay=round(start*1000)
        vol=1.20 if speaker=="narrator" else 1.15; filters.append(f"[{idx}:a]adelay={delay}|{delay},volume={vol}[v{idx}]"); labels.append(f"[v{idx}]")
    filters.append("".join(labels)+f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,alimiter=limit=.93[aout]")
    subprocess.run(["ffmpeg","-y"]+inputs+["-filter_complex",";".join(filters),"-map","0:v","-map","[aout]","-c:v","copy","-c:a","aac","-b:a","192k","-t",str(DURATION),"-movflags","+faststart",str(OUTPUT)],check=True)


def make_contact_sheet():
    times=[2.0,10.0]
    for s in SCENES: times += [s["start"]+5,s["prompt_start"]+2,s["reveal"]+1.5]
    times += [FINAL_START+3,FINAL_START+10,FINAL_START+19]
    sheet=Image.new("RGB",(1280,720),"white")
    for i,t in enumerate(times[:25]):
        im=frame_at(t).resize((256,144),Image.Resampling.LANCZOS); d=ImageDraw.Draw(im); d.rectangle((0,0,62,20),fill="black"); d.text((4,2),f"{t:.1f}s",font=font(11,True),fill="white")
        sheet.paste(im,((i%5)*256,(i//5)*144))
    sheet.save(CONTACT)


def main():
    global BACKGROUNDS
    WORK.mkdir(exist_ok=True); BACKGROUNDS=[fit_overscan(s["bg"]) for s in SCENES]
    items=asyncio.run(make_speech()); build_timeline(items); make_audio(); render_silent(); mix_audio(); make_contact_sheet(); print(OUTPUT)


if __name__=="__main__": main()
