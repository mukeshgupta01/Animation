"""Render a warmer, more conversational narration of pilot 01.

This reuses the existing storyboard and visual renderer. It creates a separate
V2 work folder and output so the first pilot remains untouched.
"""

from pathlib import Path

import produce_pilot_01 as base


base.WORK = base.PROJECT / "production-work" / "pilot-01-shoes-v2-conversational"
base.OUTPUT = base.PROJECT / "output" / "parenting-rewind-pilot-01-shoes-v2-conversational.mp4"
base.VOICE = "en-US-AvaMultilingualNeural"
base.VOICE_RATE = "-5%"
base.VOICE_PITCH = "-1Hz"

base.SEGMENTS = [
    {
        "key": "hook",
        "panel": 0,
        "kind": "hook",
        "headline": "ONE SENTENCE TO TRY",
        "caption": "Your child refuses their shoes—\nand you are already late.",
        "voice": (
            "Can I give you one sentence to try the next time your child refuses their shoes? "
            "Especially on those mornings when you are already late, and you can feel yourself getting frustrated."
        ),
        "minimum": 7.0,
    },
    {
        "key": "wrong",
        "panel": 1,
        "kind": "wrong",
        "headline": "WE’VE ALL BEEN THERE",
        "caption": "“Why do you never listen?\nPut your shoes on now!”",
        "voice": (
            "Most of us might say, Why do you never listen? Put your shoes on right now. "
            "It makes sense in the moment. But now there are two problems: the shoes, and a power struggle."
        ),
        "minimum": 8.0,
    },
    {
        "key": "pause",
        "panel": 2,
        "kind": "pause",
        "headline": "TAKE ONE BREATH",
        "caption": "The boundary can stay.\nChange how you say it.",
        "voice": (
            "Before you repeat yourself, just pause for one breath. The boundary does not need to change. "
            "You still have to leave. We are only changing how we say it."
        ),
        "minimum": 7.0,
    },
    {
        "key": "rewind",
        "panel": 2,
        "kind": "rewind",
        "headline": "OKAY—LET’S REWIND",
        "caption": "Fewer words. Calm voice.\nTwo acceptable choices.",
        "voice": "Okay, let us rewind. Fewer words, a calm voice, and two choices you can live with.",
        "minimum": 5.5,
    },
    {
        "key": "better",
        "panel": 3,
        "kind": "better",
        "headline": "TRY THIS",
        "caption": "“It’s time to leave.\nRed shoes or blue shoes?”",
        "voice": "Try this. It is time to leave. Would you like the red shoes, or the blue shoes?",
        "minimum": 5.5,
    },
    {
        "key": "choice",
        "panel": 4,
        "kind": "better",
        "headline": "ONE SMALL DECISION",
        "caption": "You keep the boundary.\nThey make one small choice.",
        "voice": (
            "You are still deciding what needs to happen. Your child just gets one small decision. "
            "And if they do not choose, you can calmly say, Okay, I will choose this time, and help them get ready."
        ),
        "minimum": 8.5,
    },
    {
        "key": "takeaway",
        "panel": 5,
        "kind": "takeaway",
        "headline": "THE SENTENCE TO REMEMBER",
        "caption": "KEEP THE BOUNDARY.\nSHARE A LITTLE CONTROL.",
        "voice": (
            "So that is the sentence to remember: red shoes, or blue shoes? Keep the boundary, and share a little control. "
            "It will not make every morning perfect, but it may make this moment easier."
        ),
        "minimum": 8.5,
    },
]


if __name__ == "__main__":
    base.main()
