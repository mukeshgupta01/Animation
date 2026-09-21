"""Independent encoded-file checks; never publishes or transfers."""
import json
import subprocess
from PIL import Image, ImageDraw
from produce_redesigned_bundle_96_to_97 import EPISODES, CTA
from produce_redesigned_bundle_02_to_06 import PROJECT, WORK_ROOT, file_sha256

review=PROJECT/'production-work/review-96-to-97'
review.mkdir(parents=True,exist_ok=True)
reports=[]
for spec in EPISODES:
    ident=f"parenting-rewind-redesign-{spec['number']:02d}-{spec['slug']}"
    path=PROJECT/'metadata'/f'{ident}-v1.json'
    data=json.loads(path.read_text(encoding='utf-8'))
    video=PROJECT/data['output']['file'];total=data['output']['duration_seconds']
    decoded=subprocess.run(['ffmpeg','-v','error','-i',str(video),'-f','null','-'],capture_output=True,text=True)
    if decoded.returncode or decoded.stderr.strip():raise RuntimeError(decoded.stderr)
    level=subprocess.run(['ffmpeg','-hide_banner','-i',str(video),'-af','ebur128=peak=true','-vn','-f','null','-'],capture_output=True,text=True,check=True)
    (review/f'{spec["number"]}-audio.txt').write_text(level.stderr,encoding='utf-8')
    sheet=Image.new('RGB',(1080,680),(24,28,34));draw=ImageDraw.Draw(sheet)
    for i in range(6):
        at=(i+0.5)*total/6
        frame=review/f'{spec["number"]}-frame-{i}.jpg'
        subprocess.run(['ffmpeg','-v','error','-y','-ss',str(at),'-i',str(video),'-frames:v','1','-vf','scale=180:320',str(frame)],check=True)
        sheet.paste(Image.open(frame),(i*180,30));draw.text((i*180+6,10),f'{at:.1f}s',fill='white')
    # Additional full-size final caption review alongside the scene strip.
    cta=review/f'{spec["number"]}-cta.jpg'
    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(total-2.5),'-i',str(video),'-frames:v','1','-vf','scale=180:320',str(cta)],check=True)
    sheet.paste(Image.open(cta),(450,355))
    sheet.save(review/f'{spec["number"]}-contact-sheet.jpg',quality=95)
    captions=(PROJECT/data['captions']['sidecar']).read_text(encoding='utf-8')
    assert 'like and subscribe' in captions
    assert data['narration']['transcript'].endswith(CTA)
    assert data['output']['sha256']==file_sha256(video)
    reports.append(dict(episode=ident,full_decode='passed',sha256=data['output']['sha256'],duration_seconds=total,spoken_and_captioned_cta=True))
(review/'verification.json').write_text(json.dumps(reports,indent=2)+'\n')
print(json.dumps(reports,indent=2))
