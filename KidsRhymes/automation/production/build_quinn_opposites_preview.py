"""Build review stills for Quinn Quokka's connected opposite-parcel story."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import produce_animal_action_alphabet as animals
import produce_snack_video as base


AUTOMATION = base.AUTOMATION
PROJECT = AUTOMATION.parent
ITEM_ID = "quinn-quokka-opposite-parcel-quest-01"
WORK = AUTOMATION / "production-work" / ITEM_ID
PLAN = PROJECT / "metadata" / f"{ITEM_ID}-plan.json"
ASSETS = AUTOMATION / "production-assets"
FONT = "C:/Windows/Fonts/arialbd.ttf"
SCENE_NAMES = (
    "quinn-opposites-empty-full-v1.png",
    "quinn-opposites-up-down-v1.png",
    "quinn-opposites-near-far-v1.png",
    "quinn-opposites-fast-slow-v1.png",
    "quinn-opposites-open-closed-v1.png",
    "quinn-opposites-light-heavy-v1.png",
    "quinn-opposites-finale-v1.png",
)


def shadow_panel(frame: Image.Image, box: tuple[int, int, int, int], fill: tuple[int, int, int, int]) -> None:
    layer = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    x1, y1, x2, y2 = box
    draw.rounded_rectangle((x1 + 14, y1 + 18, x2 + 14, y2 + 18), 38, fill=(10, 18, 38, 110))
    draw.rounded_rectangle(box, 38, fill=fill, outline=(255, 255, 255, 235), width=6)
    frame.alpha_composite(layer.filter(ImageFilter.GaussianBlur(5)))


def parcel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], colour: tuple[int, int, int], glow: bool = False) -> None:
    x1, y1, x2, y2 = box
    if glow:
        draw.rounded_rectangle((x1-12,y1-12,x2+12,y2+12),26,fill=(*colour,50))
    draw.rounded_rectangle(box, 24, fill=(*colour,255), outline=(255,245,215,255), width=6)
    mid=(x1+x2)//2
    draw.rectangle((mid-12,y1,mid+12,y2),fill=(255,224,112,235))
    draw.rectangle((x1,(y1+y2)//2-10,x2,(y1+y2)//2+10),fill=(255,224,112,235))
    draw.ellipse((mid-28,y1-25,mid,y1+12),fill=(255,224,112,245))
    draw.ellipse((mid,y1-25,mid+28,y1+12),fill=(255,224,112,245))


def header(draw: ImageDraw.ImageDraw, pair: str, accent: tuple[int, int, int]) -> None:
    font=ImageFont.truetype(FONT,54)
    box=draw.textbbox((0,0),pair,font=font,stroke_width=3)
    width=box[2]-box[0]
    draw.rounded_rectangle((70,58,130+width,150),28,fill=(*accent,225),outline="white",width=5)
    draw.text((100,76),pair,font=font,fill=(255,248,154),stroke_width=4,stroke_fill=(20,29,54))


def gate(draw: ImageDraw.ImageDraw, box: tuple[int,int,int,int], opened: bool) -> None:
    x1,y1,x2,y2=box
    draw.rounded_rectangle(box,55,fill=(28,106,158,240),outline=(255,218,112,255),width=14)
    if opened:
        draw.rounded_rectangle((x1+38,y1+38,x2-38,y2-38),38,fill=(113,226,255,155),outline="white",width=6)
        draw.polygon([(x1+95,(y1+y2)//2),(x1+170,(y1+y2)//2-55),(x1+170,(y1+y2)//2+55)],fill=(255,239,125,245))
    else:
        draw.rounded_rectangle((x1+38,y1+38,x2-38,y2-38),38,fill=(17,49,91,245),outline=(190,220,245,255),width=6)
        draw.rectangle(((x1+x2)//2-28,(y1+y2)//2-20,(x1+x2)//2+28,(y1+y2)//2+80),fill=(246,190,70,255))
        draw.ellipse(((x1+x2)//2-55,(y1+y2)//2-70,(x1+x2)//2+55,(y1+y2)//2+30),outline=(246,190,70,255),width=20)


def load() -> dict:
    sprites=animals.split_sheet(ASSETS/"animal-action-3d-m-r.png",3,2)
    backgrounds={
        "meadow":animals.fit_background(ASSETS/"animal-action-meadow-stage.png"),
        "jungle":animals.fit_background(ASSETS/"animal-action-jungle-stage.png"),
        "ocean":animals.fit_background(ASSETS/"animal-action-ocean-stage.png"),
        "sunset":animals.fit_background(ASSETS/"animal-action-sunset-stage.png"),
        "finale":animals.fit_background(ASSETS/"animal-action-finale-stage.png"),
    }
    return {"quinn":sprites[4],"olive":sprites[2],"backgrounds":backgrounds}


def base_frame(source: Image.Image, seed: float) -> Image.Image:
    return animals.camera(source,4.0,seed).convert("RGBA")


def frame(scene: int, assets: dict) -> Image.Image:
    env=("meadow","jungle","ocean","sunset","finale","meadow","finale")[scene]
    image=base_frame(assets["backgrounds"][env],scene+0.5)
    draw=ImageDraw.Draw(image,"RGBA")
    accents=((47,125,104),(177,82,43),(26,112,163),(169,75,42),(46,90,156),(109,74,156),(42,122,118))
    pairs=("EMPTY  /  FULL","UP  /  DOWN","NEAR  /  FAR","FAST  /  SLOW","OPEN  /  CLOSED","LIGHT  /  HEAVY","OPPOSITES FIND THE WAY!")
    header(draw,pairs[scene],accents[scene])
    if scene==0:
        shadow_panel(image,(750,230,1810,950),(35,91,100,160))
        draw=ImageDraw.Draw(image,"RGBA")
        draw.rounded_rectangle((890,515,1210,805),55,fill=(24,120,130,245),outline=(255,223,128,255),width=8)
        draw.arc((920,400,1180,650),180,360,fill=(255,223,128,255),width=18)
        for i in range(3): parcel(draw,(1300+i*145,560-(i%2)*45,1415+i*145,685-(i%2)*45),(236-25*i,91+45*i,92+55*i),True)
        animals.place(image,assets["quinn"],(535,995),650,-4)
        animals.place(image,assets["olive"],(1615,505),335,5)
    elif scene==1:
        shadow_panel(image,(690,205,1795,955),(77,55,34,120)); draw=ImageDraw.Draw(image,"RGBA")
        draw.rounded_rectangle((1080,280,1450,820),30,fill=(35,62,80,150),outline=(255,214,103,255),width=8)
        draw.line((1265,330,1265,760),fill=(255,238,143,255),width=18)
        draw.polygon([(1265,260),(1215,340),(1315,340)],fill=(255,238,143,255)); draw.polygon([(1265,850),(1215,770),(1315,770)],fill=(255,238,143,255))
        draw.rounded_rectangle((1095,650,1435,775),22,fill=(55,151,142,245),outline="white",width=5); parcel(draw,(1190,545,1340,665),(234,96,82),True)
        animals.place(image,assets["quinn"],(600,995),640,2); animals.place(image,assets["olive"],(1600,530),350,-5)
    elif scene==2:
        draw=ImageDraw.Draw(image,"RGBA")
        # Large near shell mailbox and small far mailbox create real depth.
        draw.ellipse((1060,380,1760,1010),fill=(240,180,128,240),outline=(255,244,220,255),width=12)
        draw.ellipse((1170,500,1650,910),fill=(51,154,194,220),outline=(255,244,220,255),width=8)
        draw.ellipse((870,255,1060,430),fill=(112,194,224,205),outline="white",width=5)
        draw.rectangle((925,390,1005,520),fill=(235,185,83,235)); parcel(draw,(1280,650,1440,790),(230,92,121),True)
        animals.place(image,assets["quinn"],(650,1000),650,-2); animals.place(image,assets["olive"],(1030,600),310,4)
    elif scene==3:
        draw=ImageDraw.Draw(image,"RGBA")
        draw.rounded_rectangle((850,670,1720,900),55,fill=(101,65,37,230),outline=(255,221,125,255),width=10)
        for x in (1040,1510): draw.ellipse((x-100,790,x+100,990),fill=(47,58,72,255),outline=(255,214,96,255),width=12)
        parcel(draw,(1190,590,1380,735),(57,143,165),True)
        draw.line((885,610,1085,610),fill=(238,74,70,230),width=18); draw.polygon([(1100,610),(1040,570),(1040,650)],fill=(238,74,70,240))
        draw.line((1420,550,1510,550),fill=(79,184,117,230),width=18)
        animals.place(image,assets["quinn"],(590,995),640,3); animals.place(image,assets["olive"],(1645,490),320,-4)
    elif scene==4:
        draw=ImageDraw.Draw(image,"RGBA"); gate(draw,(730,245,1180,940),False); gate(draw,(1270,245,1720,940),True)
        animals.place(image,assets["quinn"],(520,1000),650,-2); animals.place(image,assets["olive"],(1480,520),325,5)
    elif scene==5:
        draw=ImageDraw.Draw(image,"RGBA")
        draw.line((850,760,1680,760),fill=(92,61,47,255),width=28); draw.line((1265,420,1265,900),fill=(92,61,47,255),width=32)
        draw.polygon([(830,745),(1110,745),(1020,860),(920,860)],fill=(61,147,148,235),outline=(255,236,142,255))
        draw.polygon([(1420,745),(1700,745),(1620,910),(1500,910)],fill=(61,147,148,235),outline=(255,236,142,255))
        draw.ellipse((920,650,1030,720),fill=(250,245,215,245)); parcel(draw,(1500,570,1640,720),(142,82,159),True)
        animals.place(image,assets["quinn"],(560,1000),650,1); animals.place(image,assets["olive"],(1210,515),315,-3)
    else:
        draw=ImageDraw.Draw(image,"RGBA")
        for i,(label,colour) in enumerate((("EMPTY / FULL",(49,137,116)),("UP / DOWN",(210,97,52)),("NEAR / FAR",(42,136,190)),("FAST / SLOW",(173,76,53)),("OPEN / CLOSED",(74,91,170)))):
            x=160+i*335
            draw.rounded_rectangle((x,690,x+300,850),30,fill=(*colour,225),outline="white",width=5)
            font=ImageFont.truetype(FONT,28); box=draw.textbbox((0,0),label,font=font); draw.text((x+(300-(box[2]-box[0]))//2,748),label,font=font,fill=(255,248,154),stroke_width=3,stroke_fill=(20,28,50))
        animals.place(image,assets["quinn"],(760,1000),720,-4); animals.place(image,assets["olive"],(1260,850),560,5)
    return image.convert("RGB")


def main() -> None:
    json.loads(PLAN.read_text(encoding="utf-8"))
    WORK.mkdir(parents=True,exist_ok=True)
    assets=load(); images=[]
    for index,name in enumerate(SCENE_NAMES):
        still=frame(index,assets); path=ASSETS/name; still.save(path,quality=95); images.append(still)
    sheet=Image.new("RGB",(960,540),(18,24,40))
    for index,image in enumerate(images): sheet.paste(image.resize((240,135),Image.Resampling.LANCZOS),((index%4)*240,(index//4)*135))
    sheet.save(WORK/"scene-preview-contact-sheet.jpg",quality=92)
    print(json.dumps({"scenes":len(images),"contact_sheet":str(WORK/"scene-preview-contact-sheet.jpg"),"assets":[str(ASSETS/name) for name in SCENE_NAMES]},indent=2))


if __name__=="__main__":
    main()
