"""Three varied, researched episodes; review locally before verified transfer."""
import asyncio
import json
import shutil
from PIL import Image
from produce_redesigned_bundle_02_to_06 import PROJECT, WORK_ROOT, produce

CTA = 'If this helped, like and subscribe for more practical Parenting Rewind ideas.'
EPISODES = [
    dict(number=93, slug='help-one-dressing-step',
         title='Help With One Step, Then Let Your Preschooler Try',
         asset='preschool-zipper-mother-daughter-storyboard-01.png', grid=[3,2], order=[0,1,2,3,4,5],
         source=dict(organization='American Academy of Pediatrics / HealthyChildren.org',
                     title='Growing Independence: Tips for Parents of Young Children',
                     url='https://www.healthychildren.org/English/ages-stages/preschool/Pages/Growing-Independence-Tips-for-Parents-of-Young-Children.aspx'),
         narration=[
             'Your preschooler wants to zip their own jacket. You are ready to leave, but that tiny fastening is taking forever.',
             'Finishing every step for them gets the coat on quickly, but leaves less time to practise.',
             'Pause. Dressing is a skill that grows with guidance and repetition. Choose a moment when you have a little extra time.',
             'Try: Would you like help getting the bottom started? I can hold this part while you pull. Offer only the help they need.',
             'Let them finish a manageable step, and notice their effort. If they need more help today, that is okay. Independence does not mean doing everything alone.', CTA]),
    dict(number=94, slug='practise-asking-teacher-for-help',
         title='Practise Asking the Teacher for Help',
         asset='school-ask-help-father-son-storyboard-01.png', grid=[3,2], order=[1,0,2,3,4,5],
         source=dict(organization='Pearson / SSIS SEL', title='Teaching children to ask for help',
                     url='https://www.pearsonclinical.ca/content/dam/school/global/clinical/us/assets/ssis-sel/SSIS-Intervention-Brief-4.pdf'),
         narration=[
             'Your child brings home confusing schoolwork, and you reach for the pencil. Solving it yourself feels like the quickest way to help.',
             'But your child may also need practice telling the teacher exactly where they are stuck.',
             'Pause and ask: Which part do you understand, and where do you need help? Listen before offering an answer.',
             'Rehearse a short question together: I tried this first step, but I am confused here. Could you explain what to do next?',
             'Practise getting the teacher\'s attention in the usual classroom way. If the difficulty continues, contact the teacher together. Asking for support is a skill worth learning.', CTA]),
    dict(number=95, slug='teen-trusted-adult-exit-plan',
         title='Agree on a Way Home Before Your Teen Needs One',
         asset='teen-exit-plan-mother-daughter-storyboard-01.png', grid=[3,2], order=[0,2,1,3,4,5],
         source=dict(organization='American Academy of Pediatrics / HealthyChildren.org',
                     title='Underage Drinking: How To Talk With Your Child About Alcohol Use',
                     url='https://www.healthychildren.org/English/ages-stages/teen/substance-abuse/Pages/Why-to-Have-the-Alcohol-Talk-Early.aspx'),
         narration=[
             'Before your teenager goes out with friends, talk about what they can do if a situation starts to feel uncomfortable.',
             'Practise how they can contact you. A short agreed message can mean: Please help me leave.',
             'Make the plan realistic. Agree who can collect them, where to meet safely, and which trusted adult is the backup if you cannot answer.',
             'Try: If you need help getting home, contact me. We will deal with getting you safe first and talk things through afterwards.',
             'Follow through calmly when they ask. Later, listen and discuss what happened, including any safety limits. Reaching out for help should remain possible, even after a mistake.', CTA]),
]

for spec in EPISODES:
    spec.update(reviewed_on='2026-09-13', upload_authorized=True, mirror_to_onedrive=False,
                recycled_visuals_approved=False, new_image_generation_calls=1,
                generation_prompt_record='production-assets/storyboard-prompts-93-to-95.md')

async def main():
    results=[]
    for spec in EPISODES:
        episode_id=f"parenting-rewind-redesign-{spec['number']:02d}-{spec['slug']}"
        # Generated sheets have unequal rows/columns: measured boundaries prevent neighbour strips.
        boxes = {
            94: [(0,0,371,517),(379,0,747,517),(756,0,1199,517),
                 (0,526,371,1312),(380,526,793,1312),(805,526,1199,1312)],
            95: [(0,0,414,553),(423,0,832,553),(843,0,1254,553),
                 (0,568,414,1254),(423,568,832,1254),(843,568,1254,1254)],
        }.get(spec['number'])
        meta_path=PROJECT/'metadata'/f'{episode_id}-v1.json'
        prior=json.loads(meta_path.read_text()) if meta_path.exists() else {}
        if boxes:
            old=json.loads(meta_path.read_text()) if meta_path.exists() else {}
            if old.get('artwork',{}).get('measured_crop_boxes') != boxes and old.get('artwork',{}).get('measured_crop_boxes') != [list(b) for b in boxes]:
                output=PROJECT/'output'/f'{episode_id}-v1.mp4'
                if output.exists():
                    archive=WORK_ROOT/episode_id/'before-crop-correction.mp4'
                    if not archive.exists():
                        shutil.copy2(output,archive)
                spec['force_rebuild']=True
            panels=WORK_ROOT/episode_id/'panels'
            panels.mkdir(parents=True,exist_ok=True)
            source=Image.open(PROJECT/'production-assets'/spec['asset']).convert('RGB')
            for index,(x1,y1,x2,y2) in enumerate(boxes):
                source.crop((x1+7,y1+7,x2-7,y2-7)).save(panels/f'panel-{index}.jpg',quality=95)
        results.append(await produce(spec))
        metadata=json.loads(meta_path.read_text())
        if prior.get('description'):
            metadata['description']=prior['description']
        if prior.get('output',{}).get('sha256') == metadata.get('output',{}).get('sha256'):
            for key in ('review','transfer'):
                if key in prior:
                    metadata[key]=prior[key]
        if boxes:
            metadata['artwork']['measured_crop_boxes']=boxes
        meta_path.write_text(json.dumps(metadata,indent=2)+'\n')
        (WORK_ROOT/'bundle-93-to-95-ledger.json').write_text(json.dumps({'results':results},indent=2))
        print(json.dumps(results[-1]),flush=True)

if __name__=='__main__':
    asyncio.run(main())
