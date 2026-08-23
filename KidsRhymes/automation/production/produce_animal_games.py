"""Render curated 1080p animal shadow, memory, matching, and alphabet games."""

from __future__ import annotations

import argparse
import asyncio
import json
import math
from pathlib import Path
import random
import subprocess

import edge_tts
from PIL import Image, ImageDraw, ImageFilter

import produce_snack_video as base


AUTOMATION = base.AUTOMATION
OUTPUT_DIR = AUTOMATION / "production-output"
WORK_ROOT = AUTOMATION / "production-work"
SNACK_SHEET = AUTOMATION / "production-assets" / "snack-suspects-sheet.png"
ALPHABET_SHEET = AUTOMATION / "production-assets" / "alphabet-animals-a-to-f-sheet.png"
OCEAN_SHEET = AUTOMATION / "production-assets" / "ocean-animals-sheet.png"
FARM_SHEET = AUTOMATION / "production-assets" / "farm-animals-sheet.png"
JUNGLE_SHEET = AUTOMATION / "production-assets" / "jungle-animals-sheet.png"
BIRD_SHEET = AUTOMATION / "production-assets" / "bird-animals-sheet.png"
W, H, ART_FPS, VIDEO_FPS = base.W, base.H, base.ART_FPS, base.VIDEO_FPS
VOICE, VOICE_RATE, VOICE_PITCH = base.VOICE, base.VOICE_RATE, base.VOICE_PITCH
THEMES = {
    "land": {
        "sheet": SNACK_SHEET,
        "names": ["rabbit", "panda", "monkey", "mouse", "giraffe", "squirrel"],
        "facts": {
            "rabbit": "Rabbits use their powerful back legs to hop quickly.",
            "panda": "A giant panda can spend many hours every day eating bamboo.",
            "monkey": "Many monkeys use their hands and tails to move through trees.",
            "mouse": "A mouse uses its whiskers to sense nearby objects.",
            "giraffe": "A giraffe is the tallest animal that lives on land.",
            "squirrel": "Squirrels use their fluffy tails for balance and warmth.",
        },
    },
    "ocean": {
        "sheet": OCEAN_SHEET,
        "names": ["dolphin", "sea turtle", "octopus", "seahorse", "crab", "whale"],
        "facts": {
            "dolphin": "Dolphins communicate with clicks, whistles, and body movements.",
            "sea turtle": "Sea turtles use their strong flippers to travel through the ocean.",
            "octopus": "An octopus has eight arms and can squeeze through small spaces.",
            "seahorse": "A seahorse swims upright and curls its tail around sea plants.",
            "crab": "Crabs usually walk sideways using their jointed legs.",
            "whale": "Whales breathe air through blowholes on top of their heads.",
        },
    },
    "farm": {
        "sheet": FARM_SHEET,
        "names": ["cow", "pig", "sheep", "horse", "chicken", "goat"],
        "facts": {
            "cow": "Cows use their long tongues to pull grass into their mouths.",
            "pig": "Pigs use their strong noses to explore and find food.",
            "sheep": "A sheep's wool helps keep it warm in cool weather.",
            "horse": "A horse can sleep while standing up or lying down.",
            "chicken": "Chickens communicate using many different calls and sounds.",
            "goat": "Goats have rectangular pupils that give them a wide view.",
        },
    },
    "jungle": {
        "sheet": JUNGLE_SHEET,
        "names": ["lion", "tiger", "elephant", "zebra", "hippopotamus", "crocodile"],
        "facts": {
            "lion": "A lion's roar can be heard from several kilometres away.",
            "tiger": "Every tiger has its own unique pattern of stripes.",
            "elephant": "Elephants use low rumbles to communicate over long distances.",
            "zebra": "Every zebra has a unique stripe pattern, like a fingerprint.",
            "hippopotamus": "A hippopotamus can close its ears and nostrils underwater.",
            "crocodile": "Crocodiles can replace many teeth throughout their lives.",
        },
    },
    "birds": {
        "sheet": BIRD_SHEET,
        "names": ["owl", "parrot", "flamingo", "penguin", "peacock", "toucan"],
        "facts": {
            "owl": "An owl can turn its head far around to look behind itself.",
            "parrot": "Parrots use their strong curved beaks to crack seeds and climb.",
            "flamingo": "Flamingos get their pink colour from pigments in their food.",
            "penguin": "Penguins use their wings like flippers to fly through water.",
            "peacock": "A peacock fans its colourful tail feathers to make a huge display.",
            "toucan": "A toucan's large bill helps it reach fruit on small branches.",
        },
    },
}
NAMES = THEMES["land"]["names"]
FACTS = THEMES["land"]["facts"]
ALPHABET = [
    ("A", "alligator", "Alligators are strong swimmers with powerful tails."),
    ("B", "bear", "Bears have an excellent sense of smell."),
    ("C", "cat", "Cats use their whiskers to feel spaces around them."),
    ("D", "dog", "Dogs can hear sounds that are too high for people to hear."),
    ("E", "elephant", "Elephants use their trunks to breathe, smell, drink, and pick things up."),
    ("F", "fox", "Foxes use their large ears to listen for tiny sounds."),
]


def choice_sets() -> list[list[str]]:
    sets = []
    for index, answer in enumerate(NAMES):
        options = [answer, NAMES[(index + 2) % len(NAMES)], NAMES[(index + 4) % len(NAMES)]]
        shift = index % 3
        sets.append(options[shift:] + options[:shift])
    return sets


def disappeared_rounds() -> list[tuple[list[str], str]]:
    return [
        (NAMES[:3], NAMES[1]),
        (NAMES[2:6], NAMES[4]),
        (NAMES[:5], NAMES[2]),
        (NAMES, NAMES[5]),
    ]


def extract_grid(path: Path, names: list[str]) -> dict[str, Image.Image]:
    source = Image.open(path).convert("RGB")
    result = {}
    for index, name in enumerate(names):
        row, col = divmod(index, 3)
        x1, x2 = round(col * source.width / 3), round((col + 1) * source.width / 3)
        y1, y2 = round(row * source.height / 2), round((row + 1) * source.height / 2)
        crop = source.crop((x1, y1, x2, y2))
        mask = Image.new("L", crop.size)
        pixels, alpha = crop.load(), mask.load()
        for y in range(crop.height):
            for x in range(crop.width):
                r, g, b = pixels[x, y]
                alpha[x, y] = max(0, min(255, int(((255 - min(r, g, b)) - 2) * 8)))
        mask = mask.filter(ImageFilter.GaussianBlur(.6))
        rgba = crop.convert("RGBA"); rgba.putalpha(mask); bbox = mask.getbbox()
        if not bbox: raise RuntimeError(f"Could not isolate {name}")
        result[name] = rgba.crop(bbox)
    return result


def speech_file(work: Path, key: str) -> Path:
    return work / f"voice-{key}.mp3"


async def voices(work: Path, game: str) -> list[tuple[str, str]]:
    if game == "shadow":
        lines = [("intro", "Welcome to Guess the Animal Shadow! Look at each silhouette, choose an animal, and check your answer.")]
        choices = choice_sets()
        for i, (answer, options) in enumerate(zip(NAMES, choices), 1):
            lines += [(f"q{i}", f"Let's check the next one. Which animal matches this shadow? Is it {options[0]}, {options[1]}, or {options[2]}?"), (f"a{i}", f"It is the {answer}! {FACTS[answer]}")]
    elif game == "matching":
        choices = choice_sets()
        lines = [("intro", "Welcome to Find the Matching Animal! Look at the big picture, then find its exact match.")]
        for i, (answer, options) in enumerate(zip(NAMES, choices), 1):
            lines += [(f"q{i}", f"Let's check the next one. Find the picture that matches the {answer}. Is it A, B, or C?"), (f"a{i}", f"Great matching! The answer is the {answer}. {FACTS[answer]}")]
    elif game == "disappeared":
        rounds = disappeared_rounds()
        lines = [("intro", "Welcome to What Animal Disappeared! Watch carefully, remember the animals, and find the missing friend.")]
        for i, (group, answer) in enumerate(rounds, 1):
            lines += [(f"m{i}", f"Let's check the next one. Look carefully and remember these {len(group)} animals."), (f"q{i}", "One animal disappeared. Which animal is missing?"), (f"a{i}", f"The {answer} disappeared! Wonderful remembering! {FACTS[answer]}")]
    else:
        lines = [("intro", "Welcome to our Animal Alphabet Adventure! Today we will learn the letters A through F.")]
        for i, (letter, animal, fact) in enumerate(ALPHABET, 1):
            lines.append((f"l{i}", f"{letter} is for {animal}. {letter}, {animal}. {fact}"))
    lines.append(("outro", "Fantastic learning! Please like and subscribe for more Tiny Tales. See you next time!"))
    for key, text in lines:
        target = speech_file(work, key)
        if not target.exists():
            await edge_tts.Communicate(text, VOICE, rate=VOICE_RATE, pitch=VOICE_PITCH, volume="-2%").save(str(target))
    return lines


def make_timeline(work: Path, game: str, lines: list[tuple[str,str]]) -> tuple[list[dict], list[tuple[str,float]], float]:
    lengths = {key: base.duration(speech_file(work,key)) for key,_ in lines}
    events=[];tracks=[];cursor=.3
    def add(kind,length,**data):
        nonlocal cursor
        event={"kind":kind,"start":cursor,"end":cursor+length,**data};events.append(event);cursor=event["end"];return event
    intro=add("intro",max(6.5,lengths["intro"]+.8));tracks.append(("intro",intro["start"]+.12))
    if game in ("shadow","matching"):
        options = choice_sets()
        for i,(answer,choices) in enumerate(zip(NAMES,options),1):
            question=add("question",lengths[f"q{i}"],index=i,answer=answer,choices=choices);tracks.append((f"q{i}",question["start"]))
            add("guess",5,index=i,answer=answer,choices=choices)
            reveal=add("reveal",lengths[f"a{i}"]+.8,index=i,answer=answer,choices=choices);tracks.append((f"a{i}",reveal["start"]+.15))
    elif game == "disappeared":
        rounds=disappeared_rounds()
        for i,(group,answer) in enumerate(rounds,1):
            memory=add("memory",max(6,lengths[f"m{i}"]+.6),index=i,group=group,answer=answer);tracks.append((f"m{i}",memory["start"]+.1))
            question=add("guess",lengths[f"q{i}"]+5,index=i,group=group,answer=answer);tracks.append((f"q{i}",question["start"]+.1))
            reveal=add("reveal",lengths[f"a{i}"]+.8,index=i,group=group,answer=answer);tracks.append((f"a{i}",reveal["start"]+.15))
    else:
        for i,(letter,animal,fact) in enumerate(ALPHABET,1):
            learn=add("learn",lengths[f"l{i}"]+1,index=i,letter=letter,answer=animal,fact=fact);tracks.append((f"l{i}",learn["start"]+.15))
    outro=add("outro",max(7.5,lengths["outro"]+.7));tracks.append(("outro",outro["start"]+.1))
    return events,tracks,math.ceil(cursor*ART_FPS)/ART_FPS


def intro(game: str, t: float) -> Image.Image:
    titles={"shadow":("GUESS THE ANIMAL SHADOW","6 SILHOUETTE PUZZLES"),"matching":("FIND THE MATCHING ANIMAL","LOOK • MATCH • LEARN"),"disappeared":("WHAT ANIMAL DISAPPEARED?","A MEMORY CHALLENGE"),"alphabet":("ANIMAL ALPHABET ADVENTURE","LETTERS A TO F")}
    frame=base.gradient_background(0,t);d=ImageDraw.Draw(frame,"RGBA");base.panel(d,(225,190,1695,895),radius=55,width=9)
    title,sub=titles[game];base.centered(d,(960,360),title,base.F62,(224,74,67,255),2);base.centered(d,(960,480),sub,base.F48,(29,76,106,255));base.centered(d,(960,690),"LOOK  •  THINK  •  DISCOVER",base.F38,(44,151,103,255));return frame.convert("RGB")


def ending(t: float, animals: dict[str,Image.Image]) -> Image.Image:
    frame=base.gradient_background(2,t);d=ImageDraw.Draw(frame,"RGBA");base.panel(d,(225,170,1695,910),radius=55,width=9);base.centered(d,(960,285),"FANTASTIC LEARNING!",base.F62,(224,74,67,255),2);base.centered(d,(960,385),"YOU DID A WONDERFUL JOB",base.F48,(28,72,102,255))
    for i,name in enumerate(list(animals)[:6]):base.contain(frame,animals[name],(270+i*235,470,470+i*235,750))
    base.centered(d,(960,830),"LIKE & SUBSCRIBE FOR MORE TINY TALES",base.F38,(45,151,102,255));return frame.convert("RGB")


def animal_cards(frame: Image.Image, animals: dict[str,Image.Image], choices: list[str], answer: str, reveal: bool, top=655) -> None:
    d=ImageDraw.Draw(frame,"RGBA");count=len(choices);card_w=min(455,(W-180-(count-1)*42)//count);gap=42;total=count*card_w+(count-1)*gap;x0=(W-total)//2
    for index,name in enumerate(choices):
        x=x0+index*(card_w+gap);box=(x,top,x+card_w,1015);correct=reveal and name==answer
        base.panel(d,box,outline=(58,172,91,255) if correct else (255,188,50,255),fill=(235,255,232,247) if correct else (255,254,239,245),radius=34,width=10 if correct else 6)
        base.contain(frame,animals[name],(x+55,top+12,x+card_w-55,940));d.ellipse((x+16,top+16,x+76,top+76),fill=(24,69,100,255));base.centered(d,(x+46,top+46),"ABCDEF"[index],base.F30,(255,255,255,255));base.centered(d,(x+card_w//2,982),name.upper(),base.F30,(43,148,79,255) if correct else (26,67,95,255))


def silhouette(art: Image.Image) -> Image.Image:
    alpha=art.getchannel("A");result=Image.new("RGBA",art.size,(28,49,64,0));result.putalpha(alpha);return result


def standard_frame(game: str,event: dict,t:float,animals:dict[str,Image.Image]) -> Image.Image:
    reveal=event["kind"]=="reveal";frame=base.gradient_background(event.get("index",1),t);d=ImageDraw.Draw(frame,"RGBA")
    title={"shadow":"GUESS THE ANIMAL SHADOW","matching":"FIND THE MATCHING ANIMAL"}[game];base.header(frame,title,"LET'S CHECK THE NEXT ONE")
    base.panel(d,(650,178,1270,570),fill=(255,250,224,244),radius=44,width=7)
    art=animals[event["answer"]] if reveal or game=="matching" else silhouette(animals[event["answer"]]);base.contain(frame,art,(770,195,1150,505))
    label=f"IT IS THE {event['answer'].upper()}!" if reveal else (f"MATCH THE {event['answer'].upper()}" if game=="matching" else "WHOSE SHADOW IS THIS?")
    base.centered(d,(960,530),label,base.F30,(48,153,83,255) if reveal else (30,72,100,255));animal_cards(frame,animals,event["choices"],event["answer"],reveal)
    return frame.convert("RGB")


def disappeared_frame(event:dict,t:float,animals:dict[str,Image.Image]) -> Image.Image:
    frame=base.gradient_background(event["index"],t);d=ImageDraw.Draw(frame,"RGBA");kind=event["kind"];base.header(frame,"WHAT ANIMAL DISAPPEARED?","LOOK CAREFULLY")
    group=event["group"];count=len(group);card_w=min(330,(W-160-(count-1)*28)//count);gap=28;total=count*card_w+(count-1)*gap;x0=(W-total)//2
    for i,name in enumerate(group):
        x=x0+i*(card_w+gap);box=(x,280,x+card_w,720);missing=kind=="guess" and name==event["answer"];correct=kind=="reveal" and name==event["answer"]
        base.panel(d,box,outline=(58,171,91,255) if correct else (255,188,50,255),fill=(235,255,232,247) if correct else (255,254,239,245),radius=32,width=10 if correct else 6)
        if missing:base.centered(d,(x+card_w//2,485),"?",base.F78,(34,75,104,255))
        else:base.contain(frame,animals[name],(x+30,305,x+card_w-30,650));base.centered(d,(x+card_w//2,682),name.upper(),base.F24,(43,148,79,255) if correct else (26,67,95,255))
    prompt="LOOK AND REMEMBER" if kind=="memory" else (f"THE {event['answer'].upper()} DISAPPEARED!" if kind=="reveal" else "WHICH ANIMAL IS MISSING?")
    base.panel(d,(410,790,1510,900),radius=30,width=6);base.centered(d,(960,845),prompt,base.F38,(224,74,67,255) if kind!="memory" else (29,76,106,255));return frame.convert("RGB")


def alphabet_frame(event:dict,t:float,animals:dict[str,Image.Image]) -> Image.Image:
    frame=base.gradient_background(event["index"],t);d=ImageDraw.Draw(frame,"RGBA");base.header(frame,"ANIMAL ALPHABET ADVENTURE","LET'S LEARN THE NEXT LETTER");base.panel(d,(225,200,1695,910),radius=52,width=8)
    base.centered(d,(520,510),event["letter"],base.font(300,True),(225,75,67,255),4);base.contain(frame,animals[event["answer"]],(805,245,1455,730));base.centered(d,(1130,790),f"{event['letter']} IS FOR {event['answer'].upper()}",base.F48,(28,72,102,255));return frame.convert("RGB")


def frame_at(game:str,t:float,events:list[dict],animals:dict[str,Image.Image])->Image.Image:
    event=next((e for e in events if e["start"]<=t<e["end"]),events[-1])
    if event["kind"]=="intro":return intro(game,t)
    if event["kind"]=="outro":return ending(t,animals)
    if game in ("shadow","matching"):return standard_frame(game,event,t,animals)
    if game=="disappeared":return disappeared_frame(event,t,animals)
    return alphabet_frame(event,t,animals)


def render(game:str,work:Path,output:Path,total:float,events:list[dict],tracks:list[tuple[str,float]],animals:dict[str,Image.Image])->None:
    silent=work/"silent.mp4";process=subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(ART_FPS),"-i","-","-an","-vf",f"fps={VIDEO_FPS}","-c:v","libx264","-preset","medium","-crf","18","-profile:v","high","-level","4.1","-pix_fmt","yuv420p",str(silent)],stdin=subprocess.PIPE)
    for n in range(math.ceil(total*ART_FPS)):
        process.stdin.write(frame_at(game,n/ART_FPS,events,animals).tobytes())
        if n%(ART_FPS*15)==0:print(f"Rendered {n/ART_FPS:.0f}/{total:.0f}s",flush=True)
    process.stdin.close()
    if process.wait()!=0:raise RuntimeError("Video render failed")
    bed,sfx=base.make_audio_bed(work,total,events);inputs=["-i",str(silent),"-i",str(bed),"-i",str(sfx)];filters=["[1:a]volume=.68[bed]","[2:a]volume=1.0[sfx]"];labels=["[bed]","[sfx]"]
    for index,(key,start) in enumerate(tracks,3):inputs += ["-i",str(speech_file(work,key))];delay=round(start*1000);filters.append(f"[{index}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay={delay}|{delay},volume=1.22[v{index}]");labels.append(f"[v{index}]")
    filters.append("".join(labels)+f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,alimiter=limit=.93,loudnorm=I=-16:TP=-1.5:LRA=11[a]")
    subprocess.run(["ffmpeg","-y","-loglevel","error"]+inputs+["-filter_complex",";".join(filters),"-map","0:v:0","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k","-ar","48000","-ac","2","-t",f"{total:.3f}","-movflags","+faststart",str(output)],check=True)


def quality(work:Path,output:Path,total:float,game:str,events:list[dict],animals:dict[str,Image.Image])->None:
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration,size","-show_entries","stream=codec_name,codec_type,width,height,r_frame_rate,sample_rate,channels","-of","json",str(output)],text=True));video=next(s for s in probe["streams"] if s["codec_type"]=="video");audio=next(s for s in probe["streams"] if s["codec_type"]=="audio")
    checks={"size":output.stat().st_size>1_000_000,"duration":abs(float(probe["format"]["duration"])-total)<.25,"video":video.get("codec_name")=="h264" and video.get("width")==W and video.get("height")==H and video.get("r_frame_rate")=="30/1","audio":audio.get("codec_name")=="aac" and audio.get("sample_rate")=="48000" and audio.get("channels")==2}
    report={"game":game,"output":str(output),"duration_seconds":float(probe["format"]["duration"]),"checks":checks,"passed":all(checks.values())};(work/"quality-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    sample_events=[events[0]]+[e for e in events if e["kind"] in ("guess","reveal","learn")]+[events[-1]];contact=Image.new("RGB",(960,math.ceil(len(sample_events)/4)*135),"white")
    for i,e in enumerate(sample_events):t=e["start"]+min(1,(e["end"]-e["start"])/2);image=frame_at(game,t,events,animals).resize((240,135),Image.Resampling.LANCZOS);d=ImageDraw.Draw(image);d.rectangle((0,0,56,19),fill="black");d.text((3,2),f"{t:.1f}s",font=base.font(12,True),fill="white");contact.paste(image,((i%4)*240,(i//4)*135))
    contact.save(work/"quality-contact-sheet.png")
    if not report["passed"]:raise RuntimeError(f"Quality gate failed: {report}")


def main()->None:
    global NAMES, FACTS
    parser=argparse.ArgumentParser();parser.add_argument("--game",choices=["shadow","disappeared","matching","alphabet"],required=True);parser.add_argument("--theme",choices=sorted(THEMES),default="land");parser.add_argument("--episode",type=int,default=1);args=parser.parse_args();game=args.game
    if game == "matching":
        raise RuntimeError("The matching-picture format is retired and must not be generated")
    if game == "shadow":
        raise RuntimeError("The animal-shadow format was retired by the user and must not be generated")
    if args.episode < 1:
        raise ValueError("Episode must be at least 1")
    if game == "alphabet" and (args.theme != "land" or args.episode != 1):
        raise RuntimeError("Only the curated land alphabet episode 1 is approved")
    theme = THEMES[args.theme]
    base_names = list(theme["names"])
    random.Random(f"tiny-tales-{args.theme}-{args.episode}").shuffle(base_names)
    NAMES, FACTS = base_names, theme["facts"]
    sheet=ALPHABET_SHEET if game=="alphabet" else theme["sheet"];names=[x[1] for x in ALPHABET] if game=="alphabet" else NAMES
    if not sheet.exists():raise FileNotFoundError(sheet)
    prefix = "" if args.theme == "land" else f"{args.theme}-"
    filenames={"shadow":f"guess-the-{prefix}animal-shadow-{args.episode:02d}.mp4","disappeared":f"what-{prefix}animal-disappeared-{args.episode:02d}.mp4","alphabet":"animal-alphabet-a-to-f-01.mp4"}
    work_name = f"{args.theme}-{game}-episode-{args.episode:02d}"
    output=OUTPUT_DIR/filenames[game];work=WORK_ROOT/work_name;OUTPUT_DIR.mkdir(parents=True,exist_ok=True);work.mkdir(parents=True,exist_ok=True)
    if output.exists():print(f"Completed output already exists; preserving without regeneration: {output}");return
    animals=extract_grid(sheet,names);lines=asyncio.run(voices(work,game));events,tracks,total=make_timeline(work,game,lines);render(game,work,output,total,events,tracks,animals);quality(work,output,total,game,events,animals);print(output)


if __name__=="__main__":main()
