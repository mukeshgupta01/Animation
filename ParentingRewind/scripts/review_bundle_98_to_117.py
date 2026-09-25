"""Review encoded masters without publishing or mirroring them."""
import argparse
import json
import re
import subprocess
from PIL import Image, ImageDraw
from produce_redesigned_bundle_98_to_117 import EPISODES, CTA
from produce_redesigned_bundle_02_to_06 import PROJECT, WORK_ROOT, file_sha256

def review_episode(spec):
    review=PROJECT/'production-work/review-98-to-117'
    review.mkdir(parents=True,exist_ok=True)
    n=spec['number'];ident=f"parenting-rewind-redesign-{n:02d}-{spec['slug']}"
    data=json.loads((PROJECT/'metadata'/f'{ident}-v1.json').read_text(encoding='utf-8'))
    video=PROJECT/data['output']['file'];total=data['output']['duration_seconds']
    digest=file_sha256(video)
    record=review/f'{n}-verification.json'
    if record.exists() and json.loads(record.read_text()).get('sha256')==digest:
        return json.loads(record.read_text())
    decoded=subprocess.run(['ffmpeg','-v','error','-i',str(video),'-f','null','-'],capture_output=True,text=True)
    if decoded.returncode or decoded.stderr.strip():raise RuntimeError(decoded.stderr)
    level=subprocess.run(['ffmpeg','-hide_banner','-i',str(video),'-af','ebur128=peak=true','-vn','-f','null','-'],capture_output=True,text=True,check=True)
    (review/f'{n}-audio.txt').write_text(level.stderr,encoding='utf-8')
    summary=level.stderr.rsplit('Summary:',1)[-1]
    integrated=float(re.search(r'I:\s*(-?[\d.]+) LUFS',summary)[1])
    peak=float(re.search(r'Peak:\s*(-?[\d.]+) dBFS',summary)[1])
    assert -20<=integrated<=-12 and peak<0,(integrated,peak)
    sheet=Image.new('RGB',(1260,380),(24,28,34));draw=ImageDraw.Draw(sheet)
    for i,at in enumerate([(i+.5)*total/6 for i in range(6)]+[total-2.5]):
        frame=review/f'{n}-frame-{i}.jpg'
        subprocess.run(['ffmpeg','-v','error','-y','-ss',str(at),'-i',str(video),'-frames:v','1','-vf','scale=180:320',str(frame)],check=True)
        with Image.open(frame) as im:sheet.paste(im,(i*180,35))
        draw.text((i*180+5,15),f'{n} / {at:.1f}s',fill='white')
    sheet.save(review/f'{n}-contact-sheet.jpg',quality=95)
    captions=(PROJECT/data['captions']['sidecar']).read_text(encoding='utf-8')
    assert 'like and subscribe' in captions
    assert data['narration']['transcript'].endswith(CTA)
    assert data['output']['sha256']==digest
    assert data['upload_authorized'] and len(spec['narration'])==6
    result=dict(episode=n,episode_id=ident,full_decode='passed',sha256=digest,
                duration_seconds=total,spoken_and_captioned_cta=True,integrated_lufs=integrated,
                true_peak_dbfs=peak,visual_review='pending',source=spec['source']['url'])
    record.write_text(json.dumps(result,indent=2)+'\n')
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--start',type=int,default=98);p.add_argument('--count',type=int,default=20)
    args=p.parse_args()
    for s in EPISODES:
        if args.start<=s['number']<args.start+args.count:print(json.dumps(review_episode(s)),flush=True)

if __name__=='__main__':main()
