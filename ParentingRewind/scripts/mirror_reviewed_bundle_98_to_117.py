"""Mirror only manually reviewed, technically verified masters to the existing queue."""
import argparse
from datetime import datetime, timezone
import json
from produce_redesigned_bundle_02_to_06 import PROJECT, file_sha256, mirror_to_business_onedrive
from produce_redesigned_bundle_98_to_117 import EPISODES

def main():
    p=argparse.ArgumentParser();p.add_argument('--start',type=int,required=True);p.add_argument('--count',type=int,required=True)
    args=p.parse_args();review=PROJECT/'production-work/review-98-to-117'
    for spec in EPISODES:
        n=spec['number']
        if not args.start<=n<args.start+args.count:continue
        evidence=json.loads((review/f'{n}-verification.json').read_text())
        path=PROJECT/'metadata'/f"parenting-rewind-redesign-{n:02d}-{spec['slug']}-v1.json"
        data=json.loads(path.read_text(encoding='utf-8'));video=PROJECT/data['output']['file']
        digest=file_sha256(video)
        assert evidence['visual_review']=='passed' and evidence['full_decode']=='passed'
        assert digest==evidence['sha256']==data['output']['sha256']
        assert data['upload_authorized'] is True
        speech=review/f'{n}-speech-check.json'
        if speech.exists():
            check=json.loads(speech.read_text());assert check['sha256']==digest and check['status']=='passed'
            evidence['speech_word_similarity']=check['word_similarity']
        data['review']=evidence
        data['status']='validated-awaiting-scheduled-upload'
        path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        destination=mirror_to_business_onedrive(video)
        if destination is None:raise RuntimeError('Configured Business OneDrive source unavailable.')
        assert destination.stat().st_size==video.stat().st_size and file_sha256(destination)==digest
        data['transfer']=dict(business_onedrive_copy=str(destination),sha256=digest,
                              size_bytes=video.stat().st_size,verified_at=datetime.now(timezone.utc).isoformat(),
                              schedule='Existing Parenting Rewind - Public Upload Cadence; oldest episode first')
        path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        print(json.dumps(dict(episode=n,mirrored=True,sha256=digest)),flush=True)

if __name__=='__main__':main()
