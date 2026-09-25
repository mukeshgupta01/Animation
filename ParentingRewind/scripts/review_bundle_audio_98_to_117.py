"""Offline speech recognition of encoded mixes using an existing local Whisper model."""
import argparse
import difflib
import json
import os
from pathlib import Path
import re
import subprocess
os.environ['HF_HUB_OFFLINE']='1'
os.environ['TRANSFORMERS_OFFLINE']='1'
import torch
from transformers import pipeline

def words(text):return re.findall(r"[a-z0-9]+",text.lower())

def main():
    p=argparse.ArgumentParser();p.add_argument('--start',type=int,default=98);p.add_argument('--count',type=int,default=20)
    p.add_argument('--model',default='C:/DocSphere/kid-explainer-studio/tools/MuseTalk/models/whisper')
    args=p.parse_args();root=Path(__file__).resolve().parents[1];review=root/'production-work/review-98-to-117'
    torch.set_num_threads(4)
    transcriber=pipeline('automatic-speech-recognition',model=args.model,device=-1)
    for n in range(args.start,args.start+args.count):
        files=list((root/'metadata').glob(f'parenting-rewind-redesign-{n}-*-v1.json'))
        assert len(files)==1,files
        data=json.loads(files[0].read_text(encoding='utf-8'));destination=review/f'{n}-speech-check.json'
        if destination.exists() and json.loads(destination.read_text()).get('sha256')==data['output']['sha256']:continue
        wav=review/f'{n}-encoded-mix.wav'
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(root/data['output']['file']),'-vn','-ar','16000','-ac','1',str(wav)],check=True)
        result=transcriber(str(wav),chunk_length_s=20,stride_length_s=3,return_timestamps=True,
                           generate_kwargs={'language':'english','task':'transcribe','max_new_tokens':180})
        ratio=difflib.SequenceMatcher(None,words(data['narration']['transcript']),words(result['text']),autojunk=False).ratio()
        report=dict(episode=n,sha256=data['output']['sha256'],word_similarity=ratio,
                    transcript=result['text'],chunks=result.get('chunks'),
                    status='passed' if ratio>=.90 else 'needs-listening-review')
        destination.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({k:v for k,v in report.items() if k not in ('chunks','transcript')}),flush=True)

if __name__=='__main__':main()
