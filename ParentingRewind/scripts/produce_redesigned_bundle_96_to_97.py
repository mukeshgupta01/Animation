"""Two researched episodes with local review before the verified transfer."""
import asyncio
import json
from PIL import Image, ImageFilter, ImageOps
from produce_redesigned_bundle_02_to_06 import PROJECT, WORK_ROOT, produce, split_panels

CTA = 'If this helped, like and subscribe for more practical Parenting Rewind ideas.'
EPISODES = [
    dict(number=96, slug='follow-preschoolers-play',
         title="Let Your Preschooler Lead the Play",
         asset='child-led-play-father-daughter-storyboard-01.png', grid=[3,2], order=[0,1,2,3,4,5],
         source=dict(organization='Centers for Disease Control and Prevention',
                     title='Tips for Connecting and Communicating',
                     url='https://www.cdc.gov/parenting-toddlers/communication/index.html'),
         beat_labels=['THE URGE TO TEACH','NOTICE THE TAKEOVER','WATCH FIRST','FOLLOW THEIR IDEA','DESCRIBE THE PLAY','TRY IT TOGETHER'],
         narration=[
             'Your preschooler lines up blocks, and you start showing them how to build a better tower. But they had a different game in mind.',
             'It is easy to take over when you want to help. For a few minutes, try joining their safe play instead.',
             'Watch what interests them. Let their idea guide what happens next, while you stay nearby.',
             'If they roll a truck beside the blocks, roll your own truck too. You can follow along without changing their design.',
             'Describe what you notice: You made a long road for your truck. Your attention can show that their ideas matter. Keep safety limits, and enjoy discovering their game.', CTA],
         description='A row of blocks does not have to become the tower you imagined. This preschool parenting example shows how to watch, imitate and describe a child\'s safe play without taking over. Try joining their idea for a few minutes and noticing what they choose.\n\nGeneral parenting education for adults; adapt to your child and keep appropriate safety limits.'),
    dict(number=97, slug='model-your-own-phone-boundary',
         title='Put Your Own Phone Down First',
         asset='teen-sharenting-permission-mother-daughter-storyboard-01.png', grid=[3,2], order=[1,2,5,3,5,3],
         source=dict(organization='American Academy of Pediatrics / HealthyChildren.org',
                     title='Be a Digital Role Model for Your Child',
                     url='https://www.healthychildren.org/English/family-life/Media/Pages/be-a-digital-role-model.aspx'),
         beat_labels=['A FAMILIAR MOMENT','CHECK YOUR HABIT','PUT IT DOWN','OWN THE INTERRUPTION','BE PRESENT','START WITH YOURSELF'],
         narration=[
             'Your teenager starts telling you something, but you keep checking your phone. Then you ask why they never talk to you.',
             'Before another reminder about their screen habits, notice what your own phone is doing to this moment.',
             'Pause the scrolling and put it down. Turn toward your teenager so your attention matches your words.',
             'Try: I was distracted. I want to hear you. Please tell me that part again. If something urgent needs an answer, explain briefly and return.',
             'Make room for time together without screens, and practise the habits you ask of them. Being a role model starts with your next small choice.', CTA],
         description='When your teenager starts talking, is your phone still getting your attention? This practical example focuses on the parent\'s own digital habits: noticing distraction, putting the phone down and returning to the conversation. The sample wording is an example, not a promise that a teen will open up.\n\nGeneral parenting education for adults. This lesson is about modelling attention, separate from overnight phone rules or permission to post photos.'),
]

for spec in EPISODES:
    spec.update(reviewed_on='2026-09-22', upload_authorized=True, mirror_to_onedrive=False,
                recycled_visuals_approved=spec['number']==97,
                new_image_generation_calls=1 if spec['number']==96 else 0,
                generation_prompt_record='production-assets/asset-audit-96-to-97.md', title_duration=5.0)

def prepare_portrait_panels(spec):
    """Preserve both faces and hands; use soft background fill in the video frame."""
    episode_id=f"parenting-rewind-redesign-{spec['number']:02d}-{spec['slug']}"
    work=WORK_ROOT/episode_id
    originals=split_panels(PROJECT/'production-assets'/spec['asset'],spec['grid'],work/'source-panels')
    panels=work/'panels';panels.mkdir(parents=True,exist_ok=True)
    for i,path in enumerate(originals):
        source=Image.open(path).convert('RGB')
        canvas=ImageOps.fit(source,(1080,1920)).filter(ImageFilter.GaussianBlur(36))
        canvas=Image.blend(canvas,Image.new('RGB',canvas.size,(15,20,24)),0.30)
        foreground=ImageOps.contain(source,(1020,1120))
        canvas.paste(foreground,((1080-foreground.width)//2,(1920-foreground.height)//2))
        canvas.save(panels/f'panel-{i}.jpg',quality=95)

async def main():
    results=[]
    for spec in EPISODES:
        name=f"parenting-rewind-redesign-{spec['number']:02d}-{spec['slug']}-v1.json"
        path=PROJECT/'metadata'/name
        prior=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
        prepare_portrait_panels(spec)
        results.append(await produce(spec))
        data=json.loads(path.read_text(encoding='utf-8'))
        if prior.get('output',{}).get('sha256') == data.get('output',{}).get('sha256'):
            for key in ('review','transfer','status'):
                if key in prior:data[key]=prior[key]
        data['description']=spec['description']+'\n\nSource: '+spec['source']['title']+'\n'+spec['source']['url']+'\n\nOriginal illustrative visuals, synthetic narration and original music.\nLike and subscribe for more practical Parenting Rewind ideas.\n\n#ParentingRewind #ParentingTips'
        data['artwork']['framing']='Full panel preserved over soft portrait background; no face-removing centre crop.'
        data['tags']=['Parenting Rewind','parenting tips','preschool play' if spec['number']==96 else 'parenting teenagers']
        path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        (WORK_ROOT/'bundle-96-to-97-ledger.json').write_text(json.dumps({'results':results},indent=2)+'\n')
        print(json.dumps(results[-1]),flush=True)

if __name__=='__main__':
    asyncio.run(main())
