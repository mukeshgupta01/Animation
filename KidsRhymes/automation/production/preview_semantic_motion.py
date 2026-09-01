"""Build start/action/end evidence sheets without rendering full video masters."""

from __future__ import annotations

import argparse
import importlib

import semantic_motion


PRODUCERS = {
    "felix": "produce_felix_firefly_parade",
    "basil": "produce_basil_beaver_workshop",
    "gus": "produce_gus_gecko_museum",
    "nellie": "produce_nellie_narwhal_lights",
    "tilly": "produce_tilly_turtle_bakery",
    "pogo": "produce_pogo_penguin_bridge",
    "zara": "produce_zara_zebra_crossing",
}


def preview(theme: str) -> None:
    producer = importlib.import_module(PRODUCERS[theme])
    producer.configure_engine()
    plan = producer.load_plan()
    events = []
    for index, scene in enumerate(plan["scenes"]):
        start = index * producer.SCENE_SECONDS
        events.append({
            "phase": f"scene_{index + 1}",
            "scene": index + 1,
            "start": start,
            "end": start + producer.SCENE_SECONDS,
            "asset": producer.ASSETS[index],
            "visual_action": scene.get("visual_action") or scene.get("action"),
        })
    assets = producer.engine.load_assets()
    audit, sheet = semantic_motion.write_evidence(
        producer.WORK, events, producer.frame_for, assets, theme
    )
    print(f"{theme}: {sheet} | {audit}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("themes", nargs="*", choices=tuple(PRODUCERS))
    args = parser.parse_args()
    for theme in (args.themes or PRODUCERS):
        preview(theme)


if __name__ == "__main__":
    main()
