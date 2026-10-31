"""Writes an OBS scene collection for the stream: tools/obs/tmnt-alttp-scenes.json (import it in OBS under
Scene Collection -> Import).

    .venv/Scripts/python.exe tools/make_obs_collection.py [--server ws://localhost:38281] [--alttp Link]
                                                          [--tmnt Turtles]

Scenes (1920x1080):
  Hyrule            the ALttP BizHawk window and the go mode panel with both games' items, as a column
  Kloak (övergång)  a sewer-green backdrop, a caption, the go mode panel and both PopTrackers
  New York          the TMNT BizHawk window and the same panel column
and the pizza-wipe stinger (tools/make_stinger.py) as the default transition. The window captures match the
fixed titles tools/start_stream.ps1 gives the windows. Paths are absolute for this checkout; rerun the script
after moving the repo.
"""
import argparse
import json
import uuid
from pathlib import Path

OBS_DIR = Path(__file__).resolve().parent / "obs"
OUT = OBS_DIR / "tmnt-alttp-scenes.json"
NAME = "TMNT x ALttP"
WIDTH, HEIGHT = 1920, 1080
BIZHAWK_CLASS = "WindowsForms10.Window.8.app.0.3297317_r6_ad1"  # BizHawk 2.11.1's main form, seen 2026-10-31
TRANSITION_POINT_MS = 500  # tools/make_stinger.py

# BizHawk's window has a menu bar and a status bar around the game picture (2x zoom, client area).
BIZHAWK_CROP = {"crop_top": 21, "crop_bottom": 22, "crop_left": 0, "crop_right": 0}


def source(kind: str, name: str, settings: dict) -> dict:
    return {"name": name, "uuid": str(uuid.uuid4()), "id": kind, "versioned_id": kind, "settings": settings,
            "mixers": 0, "sync": 0, "flags": 0, "volume": 1.0, "balance": 0.5, "enabled": True, "muted": False,
            "push-to-mute": False, "push-to-mute-delay": 0, "push-to-talk": False, "push-to-talk-delay": 0,
            "hotkeys": {}, "deinterlace_mode": 0, "deinterlace_field_order": 0, "monitoring_type": 0,
            "private_settings": {}}


def window(name: str, title: str, window_class: str, exe: str) -> dict:
    # method 2 = Windows Graphics Capture, which also captures PopTracker's OpenGL window.
    return source("window_capture", name, {"window": f"{title}:{window_class}:{exe}", "method": 2,
                                          "cursor": False, "client_area": True, "priority": 1})


def item(src: dict, item_id: int, x: float, y: float, width: float, height: float, crop: dict | None = None) -> dict:
    """A scene item scaled to fit inside the box (x, y, width, height), keeping its aspect ratio."""
    return {"name": src["name"], "source_uuid": src["uuid"], "visible": True, "locked": False, "rot": 0.0,
            "align": 5, "bounds_type": 2, "bounds_align": 0, "bounds_crop": False,
            **(crop or {"crop_left": 0, "crop_top": 0, "crop_right": 0, "crop_bottom": 0}),
            "id": item_id, "group_item_backup": False, "pos": {"x": x, "y": y}, "scale": {"x": 1.0, "y": 1.0},
            "bounds": {"x": width, "y": height}, "scale_filter": "point", "blend_method": "default",
            "blend_type": "normal", "show_transition": {"duration": 0}, "hide_transition": {"duration": 0},
            "private_settings": {}}


def scene(name: str, items: list[dict]) -> dict:
    src = source("scene", name, {"id_counter": len(items), "custom_size": False, "items": items})
    src["hotkeys"] = {"OBSBasic.SelectScene": []}
    return src


def build(server: str, alttp: str, tmnt: str) -> dict:
    alttp_game = window("ALttP (BizHawk)", "alttp-stream [SNES] - BizHawk", BIZHAWK_CLASS, "EmuHawk.exe")
    tmnt_game = window("TMNT (BizHawk)", "tmnt-stream [NES] - BizHawk", BIZHAWK_CLASS, "EmuHawk.exe")
    alttp_tracker = window("ALttP-tracker (PopTracker)", "PopTracker - A Link to the Past-Map Tracker via AP",
                           "SDL_app", "poptracker.exe")
    tmnt_tracker = window("TMNT-tracker (PopTracker)",
                          "PopTracker - Teenage Mutant Ninja Turtles-Item Tracker via AP", "SDL_app", "poptracker.exe")
    panel_url = (OBS_DIR / "go-mode.html").as_uri() + f"?server={server}&alttp={alttp}&tmnt={tmnt}"
    browser = {"is_local_file": False, "fps_custom": False, "shutdown": False, "restart_when_active": False}
    panel = source("browser_source", "Go mode panel", {**browser, "url": panel_url, "width": 1000, "height": 260})
    panel_column = source("browser_source", "Go mode panel (column)",
                          {**browser, "url": panel_url + "&layout=column", "width": 520, "height": 440})
    sewer = source("color_source_v3", "Kloak-bakgrund", {"color": 0xFF1F2A1B, "width": WIDTH, "height": HEIGHT})
    caption = source("text_gdiplus_v3", "Kloak-text", {
        "text": "Into the sewers...", "font": {"face": "Segoe UI", "size": 96, "style": "Bold", "flags": 1},
        "color": 0xFF4AD8FF, "align": "center", "outline": True, "outline_size": 6, "outline_color": 0xFF101418})

    game_box = (0, 0, 1240, 1080)  # 256x224 games at 2x keep their shape inside this
    # Both games' items in one column next to the game, so viewers always see the whole go mode picture.
    hyrule = scene("Hyrule", [item(alttp_game, 1, *game_box, BIZHAWK_CROP),
                              item(panel_column, 2, 1250, 20, 660, 1040)])
    new_york = scene("New York", [item(tmnt_game, 1, *game_box, BIZHAWK_CROP),
                                  item(panel_column, 2, 1250, 20, 660, 1040)])
    sewer_scene = scene("Kloak (övergång)", [item(sewer, 1, 0, 0, WIDTH, HEIGHT),
                                             item(caption, 2, 160, 120, 1600, 200),
                                             item(panel, 3, 160, 330, 1600, 420),
                                             item(alttp_tracker, 4, 40, 740, 560, 320),
                                             item(tmnt_tracker, 5, 1320, 740, 560, 320)])

    stinger = {"name": "Pizza-wipe", "uuid": str(uuid.uuid4()), "id": "obs_stinger_transition",
               "versioned_id": "obs_stinger_transition",
               "settings": {"path": str(OBS_DIR / "pizza_wipe.webm"), "tp_type": 0,
                            "transition_point": TRANSITION_POINT_MS}}
    scenes = [hyrule, sewer_scene, new_york]
    return {"name": NAME, "current_scene": "Hyrule", "current_program_scene": "Hyrule",
            "scene_order": [{"name": s["name"]} for s in scenes],
            "sources": [alttp_game, tmnt_game, alttp_tracker, tmnt_tracker, panel, panel_column, sewer, caption,
                        *scenes],
            "groups": [], "transitions": [stinger], "current_transition": "Pizza-wipe", "transition_duration": 300,
            "quick_transitions": [], "saved_projectors": [], "modules": {}, "preview_locked": False,
            "scaling_enabled": False, "scaling_level": 0, "scaling_off_x": 0.0, "scaling_off_y": 0.0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default="ws://localhost:38281")
    parser.add_argument("--alttp", default="Link")
    parser.add_argument("--tmnt", default="Turtles")
    args = parser.parse_args()
    OUT.write_text(json.dumps(build(args.server, args.alttp, args.tmnt), indent=4, ensure_ascii=False),
                   encoding="utf-8")
    print(f"scene collection '{NAME}' -> {OUT}")
