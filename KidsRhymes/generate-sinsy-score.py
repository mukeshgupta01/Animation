"""Create a MusicXML vocal score for Sinsy's English singing voice."""

from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output" / "baa-baa-black-sheep" / "audio" / "baa-baa-black-sheep-sinsy.musicxml"

# Each duration is measured in eighth notes. Every phrase fills one 4/4 bar.
PHRASES = [
    ([67, 67, 69, 67], [1, 1, 2, 4], [("Baa", "single"), ("baa", "single"), ("black", "single"), ("sheep", "single")]),
    ([64, 64, 62, 60, 60], [1, 1, 2, 2, 2], [("Have", "single"), ("you", "single"), ("an", "begin"), ("y", "end"), ("wool", "single")]),
    ([67, 67, 69, 67], [1, 1, 2, 4], [("Yes", "single"), ("sir", "single"), ("yes", "single"), ("sir", "single")]),
    ([62, 60, 60], [2, 2, 4], [("Three", "single"), ("bags", "single"), ("full", "single")]),
    ([64, 64, 65, 67, 67], [1, 1, 2, 2, 2], [("One", "single"), ("for", "single"), ("the", "single"), ("mas", "begin"), ("ter", "end")]),
    ([69, 67, 64, 64], [2, 2, 2, 2], [("One", "single"), ("for", "single"), ("the", "single"), ("dame", "single")]),
    ([62, 62, 64, 65, 67, 64, 60], [1, 1, 1, 1, 1, 1, 2], [("And", "single"), ("one", "single"), ("for", "single"), ("the", "single"), ("lit", "begin"), ("tle", "end"), ("child", "single")]),
    ([67, 64, 62, 60, 60], [1, 1, 2, 2, 2], [("Who", "single"), ("lives", "single"), ("down", "single"), ("the", "single"), ("lane", "single")]),
]


def pitch_name(midi: int) -> tuple[str, int, int]:
    names = [("C", 0), ("C", 1), ("D", 0), ("D", 1), ("E", 0), ("F", 0),
             ("F", 1), ("G", 0), ("G", 1), ("A", 0), ("A", 1), ("B", 0)]
    step, alter = names[midi % 12]
    return step, alter, midi // 12 - 1


def add_rest(measure: ET.Element) -> None:
    note = ET.SubElement(measure, "note")
    ET.SubElement(note, "rest")
    ET.SubElement(note, "duration").text = "8"
    ET.SubElement(note, "type").text = "whole"


def add_phrase(measure: ET.Element, phrase) -> None:
    pitches, durations, lyrics = phrase
    for midi, duration, (text, syllabic) in zip(pitches, durations, lyrics):
        note = ET.SubElement(measure, "note")
        pitch = ET.SubElement(note, "pitch")
        step, alter, octave = pitch_name(midi)
        ET.SubElement(pitch, "step").text = step
        if alter:
            ET.SubElement(pitch, "alter").text = str(alter)
        ET.SubElement(pitch, "octave").text = str(octave)
        ET.SubElement(note, "duration").text = str(duration)
        ET.SubElement(note, "type").text = {1: "eighth", 2: "quarter", 4: "half"}[duration]
        lyric = ET.SubElement(note, "lyric", number="1")
        ET.SubElement(lyric, "syllabic").text = syllabic
        ET.SubElement(lyric, "text").text = text


def main() -> None:
    score = ET.Element("score-partwise", version="3.1")
    part_list = ET.SubElement(score, "part-list")
    score_part = ET.SubElement(part_list, "score-part", id="P1")
    ET.SubElement(score_part, "part-name").text = "English Vocal"
    part = ET.SubElement(score, "part", id="P1")

    first = ET.SubElement(part, "measure", number="1")
    attrs = ET.SubElement(first, "attributes")
    ET.SubElement(attrs, "divisions").text = "2"
    key = ET.SubElement(attrs, "key")
    ET.SubElement(key, "fifths").text = "0"
    time = ET.SubElement(attrs, "time")
    ET.SubElement(time, "beats").text = "4"
    ET.SubElement(time, "beat-type").text = "4"
    clef = ET.SubElement(attrs, "clef")
    ET.SubElement(clef, "sign").text = "G"
    ET.SubElement(clef, "line").text = "2"
    direction = ET.SubElement(first, "direction", placement="above")
    dtype = ET.SubElement(direction, "direction-type")
    metronome = ET.SubElement(dtype, "metronome")
    ET.SubElement(metronome, "beat-unit").text = "quarter"
    ET.SubElement(metronome, "per-minute").text = "96"
    ET.SubElement(direction, "sound", tempo="96")
    add_rest(first)

    measure_number = 2
    for _ in range(3):
        for phrase in PHRASES:
            measure = ET.SubElement(part, "measure", number=str(measure_number))
            add_phrase(measure, phrase)
            measure_number += 1
    for _ in range(3):
        measure = ET.SubElement(part, "measure", number=str(measure_number))
        add_rest(measure)
        measure_number += 1

    ET.indent(score, space="  ")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(score).write(OUTPUT, encoding="utf-8", xml_declaration=True)
    print(OUTPUT)


if __name__ == "__main__":
    main()
