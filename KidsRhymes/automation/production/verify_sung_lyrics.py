"""Transcribe a rendered song for an objective lyric-intelligibility check."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.signal import resample_poly
import soundfile as sf
from transformers import WhisperForConditionalGeneration, WhisperProcessor


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("audio", type=Path, nargs="+")
    parser.add_argument("--model", default="openai/whisper-tiny.en")
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--chunk-seconds", type=float, default=24.0)
    args = parser.parse_args()

    processor = WhisperProcessor.from_pretrained(args.model, cache_dir=str(args.cache_dir))
    model = WhisperForConditionalGeneration.from_pretrained(args.model, cache_dir=str(args.cache_dir))
    tracks = []
    for audio_path in args.audio:
        samples, rate = sf.read(audio_path, always_2d=True, dtype="float32")
        mono = samples.mean(axis=1)
        if rate != 16000:
            divisor = int(np.gcd(rate, 16000))
            mono = resample_poly(mono, 16000 // divisor, rate // divisor).astype(np.float32)
        chunk_size = round(args.chunk_seconds * 16000)
        chunks = []
        for start in range(0, len(mono), chunk_size):
            audio_chunk = mono[start : start + chunk_size]
            if len(audio_chunk) < 8000:
                continue
            inputs = processor(audio_chunk, sampling_rate=16000, return_tensors="pt")
            predicted_ids = model.generate(inputs.input_features, attention_mask=inputs.get("attention_mask"))
            transcript = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0].strip()
            chunks.append({
                "start": round(start / 16000, 3),
                "end": round((start + len(audio_chunk)) / 16000, 3),
                "text": transcript,
            })
        tracks.append({"audio": str(audio_path), "text": " ".join(chunk["text"] for chunk in chunks), "chunks": chunks})
    result = tracks[0] if len(tracks) == 1 else {"tracks": tracks}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
