"""Render three local-only Tiny Tales hidden-object kindness quests."""

from __future__ import annotations

import asyncio
import json
import math
from pathlib import Path

import edge_tts
from PIL import Image, ImageDraw

import produce_snack_video as base
import produce_animal_games as games
import produce_clue_detective_batch as shared


AUTOMATION = base.AUTOMATION
OUTPUT_DIR = AUTOMATION / "production-output"
WORK_ROOT = AUTOMATION / "production-work"
META_DIR = AUTOMATION.parent / "metadata"

EPISODES = [
    {
        "id": "farm-find-sheeps-bell-01", "theme": "FARM", "title": "FIND SHEEP'S LOST BELL",
        "sheet": AUTOMATION / "production-assets" / "farm-animals-sheet.png", "names": ["cow", "pig", "sheep", "horse", "chicken", "goat"],
        "clues": [
            {"helper": "pig", "target": "HOOFPRINT", "position": (1220, 690), "question": "Pig wants to help Sheep. Can you find the tiny hoofprint near the muddy path?", "reveal": "There it is! The hoofprint points from the farmyard toward the hay."},
            {"helper": "horse", "target": "WOOL TUFT", "position": (1490, 530), "question": "Horse follows the path to the hay. Can you spot a little white tuft of wool?", "reveal": "You found the wool! Sheep must have walked beside this haystack."},
            {"helper": "chicken", "target": "RED RIBBON", "position": (1080, 760), "question": "Chicken searches beside the fence. Can you find the small red ribbon from Sheep's bell?", "reveal": "Ribbon found! A gentle breeze carried it close to the barn door."},
            {"helper": "sheep", "target": "GOLDEN BELL", "position": (1430, 690), "question": "Everyone reaches the barn. Look carefully: where is Sheep's golden bell hiding?", "reveal": "Bell found! The friends solved every clue and returned it to Sheep together."},
        ],
    },
    {
        "id": "ocean-turtle-friendship-badge-01", "theme": "OCEAN", "title": "TURTLE'S FRIENDSHIP BADGE",
        "sheet": AUTOMATION / "production-assets" / "ocean-animals-sheet.png", "names": ["dolphin", "sea turtle", "octopus", "seahorse", "crab", "whale"],
        "clues": [
            {"helper": "dolphin", "target": "BUBBLE TRAIL", "position": (1510, 410), "question": "Turtle's friendship badge drifted away. Can you find the trail of three bright bubbles?", "reveal": "Bubble trail spotted! It curves toward the swaying seagrass."},
            {"helper": "seahorse", "target": "GREEN RIBBON", "position": (1180, 660), "question": "Seahorse checks the meadow. Can you find the badge's little green ribbon among the plants?", "reveal": "You found the ribbon! The current carried the badge toward the rocky reef."},
            {"helper": "octopus", "target": "GOLD STAR", "position": (1500, 720), "question": "Octopus searches between the reef shapes. Can you spot one small golden star?", "reveal": "Star spotted! It is the shiny centre from Turtle's badge."},
            {"helper": "sea turtle", "target": "FRIENDSHIP BADGE", "position": (1250, 520), "question": "The friends reach a quiet rock pool. Can you find the complete friendship badge?", "reveal": "Badge rescued! Turtle thanks every friend for following the clues together."},
        ],
    },
    {
        "id": "bird-cozy-nest-quest-01", "theme": "BIRD", "title": "THE COZY NEST QUEST",
        "sheet": AUTOMATION / "production-assets" / "bird-animals-sheet.png", "names": ["owl", "parrot", "flamingo", "penguin", "peacock", "toucan"],
        "clues": [
            {"helper": "owl", "target": "FORKED TWIG", "position": (1400, 650), "question": "The wind scattered the nest supplies. Can you find a forked brown twig among the branches?", "reveal": "Twig found! Its forked shape can help make a sturdy nest frame."},
            {"helper": "parrot", "target": "SOFT LEAF", "position": (1140, 490), "question": "Parrot looks for something soft. Can you spot the bright green leaf?", "reveal": "Leaf found! Soft plant pieces can help line a comfortable nest."},
            {"helper": "peacock", "target": "BLUE FEATHER", "position": (1510, 750), "question": "Peacock donated a loose feather. Can you find the small blue feather below the tree?", "reveal": "Feather found! Naturally shed feathers can become soft nest lining."},
            {"helper": "toucan", "target": "COZY NEST", "position": (1270, 480), "question": "The supplies are ready. Can you find the finished cozy nest tucked between the branches?", "reveal": "Nest complete! The bird friends combined their different finds to make a safe resting place."},
        ],
    },
]


def voice_path(work: Path, key: str) -> Path:
    return work / f"voice-{key}.mp3"


async def make_voices(work: Path, spec: dict) -> list[tuple[str, str]]:
    lines = [("intro", f"A Tiny Tales kindness quest is beginning: {spec['title'].lower()}! Look carefully at each scene, find the hidden clue, and help the animal friends solve the story together.")]
    for index, item in enumerate(spec["clues"], 1):
        lines.append((f"q{index}", f"Search scene {index}. {item['question']}"))
        lines.append((f"a{index}", item["reveal"]))
    lines.append(("outro", "Kindness quest complete! Careful looking and teamwork helped every friend. Which hidden clue was hardest for you to find?"))
    for key, text in lines:
        target = voice_path(work, key)
        if not target.exists():
            await edge_tts.Communicate(text, base.VOICE, rate=base.VOICE_RATE, pitch=base.VOICE_PITCH, volume="-2%").save(str(target))
    return lines


def draw_target(draw: ImageDraw.ImageDraw, target: str, position: tuple[int, int], scale: float = 1.0) -> tuple[int, int, int, int]:
    x, y = position; s = scale
    box = (round(x - 55*s), round(y - 55*s), round(x + 55*s), round(y + 55*s))
    if target == "HOOFPRINT":
        draw.ellipse((x-28*s,y-20*s,x+28*s,y+35*s),fill=(91,67,45,255)); draw.ellipse((x-45*s,y-48*s,x-5*s,y-10*s),fill=(91,67,45,255)); draw.ellipse((x+5*s,y-48*s,x+45*s,y-10*s),fill=(91,67,45,255))
    elif target == "WOOL TUFT":
        for dx,dy in ((-30,0),(0,-20),(30,0),(0,25)): draw.ellipse((x+(dx-32)*s,y+(dy-32)*s,x+(dx+32)*s,y+(dy+32)*s),fill=(250,247,230,255),outline=(145,130,110,255),width=max(2,round(3*s)))
    elif "RIBBON" in target:
        colour=(216,65,70,255) if "RED" in target else (55,155,82,255); draw.ellipse((x-45*s,y-30*s,x+45*s,y+30*s),outline=colour,width=max(5,round(12*s))); draw.polygon([(x-10*s,y+25*s),(x-45*s,y+75*s),(x,y+55*s),(x+20*s,y+80*s),(x+38*s,y+25*s)],fill=colour)
    elif "BELL" in target:
        draw.pieslice((x-48*s,y-55*s,x+48*s,y+55*s),180,360,fill=(239,184,55,255),outline=(143,101,28,255),width=max(3,round(6*s))); draw.rectangle((x-48*s,y,x+48*s,y+28*s),fill=(239,184,55,255)); draw.ellipse((x-12*s,y+20*s,x+12*s,y+45*s),fill=(143,101,28,255))
    elif target == "BUBBLE TRAIL":
        for dx,dy,r in ((-35,35,18),(0,0,25),(38,-45,32)): draw.ellipse((x+(dx-r)*s,y+(dy-r)*s,x+(dx+r)*s,y+(dy+r)*s),outline=(65,170,214,255),width=max(3,round(6*s)))
    elif "STAR" in target or "BADGE" in target:
        points=[]
        for i in range(10):
            angle=-math.pi/2+i*math.pi/5; radius=(52 if i%2==0 else 24)*s; points.append((x+math.cos(angle)*radius,y+math.sin(angle)*radius))
        draw.polygon(points,fill=(242,190,48,255),outline=(145,98,24,255));
        if "BADGE" in target: draw.ellipse((x-65*s,y-65*s,x+65*s,y+65*s),outline=(54,154,83,255),width=max(4,round(9*s)))
    elif target == "FORKED TWIG":
        draw.line((x-50*s,y+50*s,x+25*s,y-30*s,x+65*s,y-65*s),fill=(118,78,45,255),width=max(5,round(10*s))); draw.line((x+15*s,y-20*s,x-10*s,y-70*s),fill=(118,78,45,255),width=max(4,round(8*s)))
    elif target == "SOFT LEAF":
        draw.ellipse((x-60*s,y-35*s,x+60*s,y+35*s),fill=(75,169,78,255),outline=(42,112,52,255),width=max(3,round(5*s))); draw.line((x-50*s,y+25*s,x+55*s,y-25*s),fill=(42,112,52,255),width=max(2,round(4*s)))
    elif target == "BLUE FEATHER":
        draw.ellipse((x-25*s,y-70*s,x+25*s,y+65*s),fill=(63,126,201,255),outline=(33,75,140,255),width=max(3,round(5*s))); draw.line((x,y-60*s,x,y+85*s),fill=(33,75,140,255),width=max(2,round(4*s)))
    elif target == "COZY NEST":
        draw.arc((x-80*s,y-45*s,x+80*s,y+75*s),0,180,fill=(126,82,42,255),width=max(8,round(18*s))); draw.arc((x-65*s,y-25*s,x+65*s,y+55*s),0,180,fill=(179,126,63,255),width=max(6,round(12*s)))
    return box


def scene(frame: Image.Image, spec: dict, item: dict, reveal: bool, t: float) -> None:
    draw=ImageDraw.Draw(frame,"RGBA"); theme=spec["theme"]
    draw.rounded_rectangle((530,175,1790,870),radius=45,fill=(255,250,230,235),outline=(49,132,174,255),width=8)
    if theme=="OCEAN":
        draw.rectangle((550,195,1770,850),fill=(184,229,242,255));
        for x in range(620,1750,180): draw.arc((x,700,x+180,830),190,350,fill=(64,151,186,255),width=8)
        for x in (680,980,1320,1600): draw.line((x,800,x+20,600),fill=(61,157,87,255),width=15)
    elif theme=="FARM":
        draw.rectangle((550,195,1770,850),fill=(220,241,191,255)); draw.rectangle((550,690,1770,850),fill=(184,150,93,255));
        for x in range(600,1750,190): draw.line((x,500,x,800),fill=(131,91,52,255),width=12); draw.line((560,600,1760,600),fill=(131,91,52,255),width=16)
        draw.polygon([(1430,430),(1600,300),(1760,430)],fill=(202,74,65,255)); draw.rectangle((1480,430,1710,690),fill=(224,158,93,255))
    else:
        draw.rectangle((550,195,1770,850),fill=(216,241,207,255));
        for x in (670,980,1320,1610): draw.rectangle((x-18,380,x+18,830),fill=(123,82,47,255)); draw.ellipse((x-110,250,x+110,470),fill=(73,155,78,255))
        draw.line((570,610,1760,500),fill=(123,82,47,255),width=22)
    x,y=item["position"]
    for index in range(9):
        dx=((index*173)%1050)-520; dy=((index*97)%430)-215
        draw.ellipse((x+dx-10,y+dy-10,x+dx+10,y+dy+10),fill=(225,174,80,140))
    target_box=draw_target(draw,item["target"],item["position"],0.72)
    if reveal:
        x1,y1,x2,y2=target_box; draw.ellipse((x1-35,y1-35,x2+35,y2+35),outline=(224,74,67,255),width=14)


def frame_for(event: dict,t: float,spec: dict,animals: dict[str,Image.Image])->Image.Image:
    if event["kind"]=="intro":
        frame=base.gradient_background(1,t);draw=ImageDraw.Draw(frame,"RGBA");base.panel(draw,(185,145,1735,935),radius=55,width=9);base.centered(draw,(960,300),spec["title"],base.F78,(224,74,67,255),2);base.centered(draw,(960,470),"A HIDDEN-OBJECT KINDNESS QUEST",base.F48,(29,76,106,255));base.centered(draw,(960,650),"SEARCH  •  FIND  •  HELP",base.F38,(44,151,103,255));return frame.convert("RGB")
    if event["kind"]=="outro":return games.ending(t,animals)
    item=event["item"];reveal=event["kind"]=="reveal";frame=base.gradient_background(event["index"]+26,t).convert("RGBA");draw=ImageDraw.Draw(frame,"RGBA");base.header(frame,spec["title"],f"SEARCH {event['index']} OF {len(spec['clues'])}");base.panel(draw,(120,175,480,870),radius=42,width=8)
    sprite=animals[item["helper"]].copy();sprite.thumbnail((310,330),Image.Resampling.LANCZOS);frame.alpha_composite(sprite,(300-sprite.width//2,470-sprite.height//2));base.centered(draw,(300,700),f"{item['helper'].upper()} IS HELPING",base.F30,(29,76,106,255));scene(frame,spec,item,reveal,t)
    if reveal: base.centered(draw,(1160,930),item["reveal"].split("!")[0].upper()+"!",base.F38,(46,151,84,255))
    elif event["kind"]=="think": base.centered(draw,(1160,930),f"FIND THE {item['target']} — SIX SECONDS!",base.F30,(224,74,67,255))
    return frame.convert("RGB")


def write_metadata(spec:dict,output:Path,total:float)->None:
    title=f"{spec['title'].title()} | Hidden-Object Kindness Quest for Kids";doc={"id":spec["id"],"title":title[:100],"description":f"Join a connected Tiny Tales {spec['theme'].lower()} kindness story. Search four illustrated scenes, find each hidden clue, and help animal friends complete the quest together.\n\nA gentle adventure supporting visual scanning, listening, story sequence, persistence, animal vocabulary, and cooperative problem-solving for children ages 3 to 7.","tags":["hidden objects for kids","animal story","kindness for kids","preschool adventure","find the object","Tiny Tales",f"{spec['theme'].lower()} animals"],"category_id":"27","made_for_kids":True,"privacy":"private","upload_authorized":False,"output":str(output),"duration_seconds":total,"new_image_generation_calls":0};META_DIR.mkdir(parents=True,exist_ok=True);(META_DIR/f"{spec['id']}.json").write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8")


def main()->None:
    OUTPUT_DIR.mkdir(parents=True,exist_ok=True);shared.frame_for=frame_for
    for spec in EPISODES:
        output=OUTPUT_DIR/f"{spec['id']}.mp4";work=WORK_ROOT/spec["id"];work.mkdir(parents=True,exist_ok=True);report=work/"quality-report.json"
        if output.exists() and report.exists() and json.loads(report.read_text(encoding="utf-8")).get("passed"):print(f"Preserving completed output: {output}",flush=True);continue
        animals=games.extract_grid(spec["sheet"],spec["names"]);lines=asyncio.run(make_voices(work,spec));events,tracks,total=shared.make_timeline(work,spec,lines);shared.render(work,output,total,events,tracks,spec,animals);shared.validate(work,output,total,events,spec,animals);report_doc=json.loads(report.read_text(encoding="utf-8"));report_doc["format"]="hidden-object-kindness-story";report.write_text(json.dumps(report_doc,indent=2)+"\n",encoding="utf-8");write_metadata(spec,output,total);print(json.dumps({"id":spec["id"],"status":"completed","duration_seconds":total}),flush=True)


if __name__=="__main__":main()
