# ==============================================================================
# AI Assistant
# ==============================================================================
# Yangi qo'shilgan imkoniyatlar:
# - Faqat "Ustoz" deb murojaat qilish tizimi.
# - Mobile Web Panel (Flask + Socket.IO) orqali masofadan boshqarish imkoniyati qo'shildi.
# - AI-powered Computer Control (Kompyuterni ko'rish va boshqarish) qo'shildi.
# - Xatoliklar to'g'irlandi va barqarorlik oshirildi.
# 
# Ushbu imkoniyatlarni Valiyev Omadbek ustoz kiritdi!
# Teacher_texno nomi bilan mashur ustoz Valiyev Omadbek ustoz Bo'ladi.


import asyncio
import inspect
import json
import os
import re
import sys
import threading
import time 
import traceback
from pathlib import Path

# --- Lokal TTS funksiyasi ---
def speak_local(text: str, save_path=None):
    """pyttsx3 yordamida lokal ovozli xabar berish (offline rejimda)."""
    try:
        import pyttsx3

        engine = pyttsx3.init()
        engine.setProperty("rate", 165)
        engine.setProperty("volume", 1.0)
        voices = engine.getProperty("voices")
        if voices:
            engine.setProperty("voice", voices[0].id)

        if save_path:
            engine.save_to_file(text, str(save_path))
            engine.runAndWait()
            print(f"[LocalTTS] Ovoz faylga saqlandi: {save_path}")
        else:
            engine.say(text)
            engine.runAndWait()
        return
    except Exception:
        pass

    try:
        import comtypes.client
        import pythoncom
        pythoncom.CoInitialize()
        speak = comtypes.client.CreateObject("SAPI.SpVoice")
        speak.Speak(text)
    except Exception:
        print(f"[LocalTTS] {text}")


# Fix Unicode (emoji) encoding on Windows terminals
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import pyaudio
from google import genai
from google.genai import types

from ui import JarvisUI
from memory.pro_memory import ProMemory
from memory.memory_manager import load_memory, format_memory_for_prompt
from emotions.emotion_engine import EmotionEngine
from security.safety_guard import SafetyGuard
from robotics.mqtt_controller import MQTTController
from vision.vision_system import MalikaVision
from automation.automation_agent import AutomationAgent
from brain.local_brain import LocalBrain
from core.voice_guard import VoiceGuard

from actions.flight_finder import flight_finder
from actions.open_app import open_app
from actions.weather_report import weather_action
from actions.send_message import send_message
from actions.reminder import reminder
from actions.computer_settings import computer_settings
from actions.screen_processor import screen_process
from actions.youtube_video import youtube_video
from actions.cmd_control import cmd_control
from actions.desktop import desktop_control
from actions.browser_control import browser_control
from actions.file_controller import file_controller
from actions.code_helper import code_helper
from actions.dev_agent import dev_agent
from actions.web_search import web_search as web_search_action
from actions.mood_detector import get_tracker as get_mood_tracker, detect_mood
from actions.computer_control import computer_control
from actions.game_mode import game_mode
from actions.translate_text import translate_text
from actions.email_sender import email_sender
from actions.calendar_manager import calendar_manager
from actions.system_monitor import system_monitor
from actions.network_tools import network_tools
from actions.dayu_tools import dayu_tools
from actions.music_control import music_control
from actions.note_manager import note_manager
from actions.clipboard_manager import clipboard_manager
from actions.window_manager import window_manager
from actions.meeting_assistant import meeting_assistant
from actions.ocr_reader import ocr_reader
from actions.security_guard import security_guard
from actions.windows11_pro_tools import windows11_pro_tools
from actions.business_advisor import business_advisor
from actions.kali_vm_control import kali_vm_control
from actions.office_tools import office_tools
from actions.airgo_cast import airgo_cast
from actions.jokes import jokes
from actions.image_generator import image_generator
from actions.app_installer import app_installer
from actions.video_editor import video_editor
from actions.system_fixer import system_fixer
from actions.phone_adb import phone_adb
from actions.diagnostics import diagnostics
from actions.system_cleaner import system_cleaner
from actions.hotkey_manager import hotkey_manager
from actions.smm_manager import smm_manager
from actions.planner import planner
from actions.screen_recorder import screen_recorder
from actions.survey_manager import survey_manager
from actions.power_control import power_control
from actions.report_manager import report_manager
from actions.video_downloader import video_downloader
from actions.smart_home import smart_home
from mobile_panel import start_panel, get_panel


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


BASE_DIR = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"
PROMPT_PATH = BASE_DIR / "core" / "prompt.txt"
SETTINGS_PATH = BASE_DIR / "config" / "settings.json"
CONVERSATION_LOG_PATH = BASE_DIR / "memory" / "conversations.jsonl"
VOICE_PROFILE_PATH = BASE_DIR / "config" / "owner_voiceprint.json"

DEFAULT_SETTINGS = {
    "live_model": "models/gemini-2.5-flash-native-audio-latest",
    "voice_name": "Leda",
    "tts": {
        "cleanup_text": True,
        "max_chars_per_utterance": 700,
    },
    "audio": {
        "send_sample_rate": 16000,
        "receive_sample_rate": 24000,
        "chunk_size": 1024,
        "out_queue_maxsize": 10,
    },
    "voice_lock": {
        "enabled": False,
        "similarity_threshold": 0.8,
        "verify_window_sec": 1.0,
        "authorize_hold_sec": 2.2,
    },
    "memory": {
        "update_every_n_turns": 5,
        "min_user_text_length": 10,
    },
    "tools": {
        "default_timeout_seconds": 90,
        "retries": 2,
        "auto_recover": True,
        "allow_ai_vision": True,
    },
    "economy": {
        "enabled": False,
        "level": "ultra", 
        "include_memory_in_prompt": True,
        "prefer_offline_tools": False,
        "confirm_expensive_tools": False,
    },
    "network": {
        "check_host": "8.8.8.8",
        "check_port": 53,
        "timeout_seconds": 10,
        "max_latency_ms": 5000
    },
    "offline_mode": False,
    "reconnect": {
        "base_delay_seconds": 2,
        "max_delay_seconds": 20,
    },
}


def _merge_dict(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge_dict(result[key], value)
        else:
            result[key] = value
    return result


def _load_settings() -> dict:
    try:
        if SETTINGS_PATH.exists():
            raw = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                return _merge_dict(DEFAULT_SETTINGS, raw)
    except Exception as e:
        print(f"[Malika] ⚠️ settings.json load error: {e}")

    try:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH.write_text(
            json.dumps(DEFAULT_SETTINGS, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        pass

    return dict(DEFAULT_SETTINGS)


SETTINGS = _load_settings()
OFFLINE_MODE = bool(SETTINGS.get("offline_mode", False))
LIVE_MODEL = SETTINGS["live_model"]
TEXT_MODEL = "gemini-2.0-flash" # Dedicated model for background text processing
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = SETTINGS["audio"]["send_sample_rate"]
RECEIVE_SAMPLE_RATE = SETTINGS["audio"]["receive_sample_rate"]
CHUNK_SIZE = SETTINGS["audio"]["chunk_size"]

pya = pyaudio.PyAudio()


def _get_api_key() -> str:
    env_key = os.getenv("GEMINI_API_KEY", "").strip()
    if env_key:
        return env_key

    if API_CONFIG_PATH.exists():
        try:
            with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
                key = str(json.load(f).get("gemini_api_key", "")).strip()
            if key:
                return key
        except Exception as e:
            raise RuntimeError(f"Could not read API key file: {e}") from e

    raise RuntimeError(
        "Gemini API key not found. Set GEMINI_API_KEY env var or config/api_keys.json"
    )


def _load_system_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except Exception:
        return (
            "You are Malika, a kind and capable AI assistant. "
            "Be concise, direct, and always use the provided tools to complete tasks. "
            "Never simulate or guess results - always call the appropriate tool."
        )


def _clean_text_for_tts(text: str) -> str:
    if text is None:
        return ""

    t = str(text).strip()
    if not t:
        return ""

    if bool(SETTINGS.get("tts", {}).get("cleanup_text", True)):
        t = re.sub(r"https?://\S+", " link ", t, flags=re.IGNORECASE)
        t = re.sub(r"`{1,3}", " ", t)
        t = re.sub(r"[*_#>\[\]\(\)]", " ", t)
        t = t.replace(" - ", ". ")
        t = re.sub(r"\s+", " ", t).strip()

    if t and t[-1] not in ".!?":
        t += "."

    max_chars = int(SETTINGS.get("tts", {}).get("max_chars_per_utterance", 0))
    # Code limit (truncation) removed completely as requested by the user
    # Text will no longer be cut off.

    return t


_memory_turn_counter = 0
_memory_turn_lock = threading.Lock()
_MEMORY_EVERY_N_TURNS = SETTINGS["memory"]["update_every_n_turns"]
_last_memory_input = ""


def _extract_memory_locally(text: str) -> dict:
    """
    Lightweight memory extraction that does not spend Gemini quota.
    It only stores high-confidence personal facts from common Uzbek/Russian/English phrasing.
    """
    src = " ".join(str(text or "").split())
    lowered = src.lower()
    data: dict = {}

    patterns = {
        "name": [
            r"\bmening ismim\s+([A-Za-zА-Яа-яЁё'` -]{2,40})",
            r"\bismim\s+([A-Za-zА-Яа-яЁё'` -]{2,40})",
            r"\bменя зовут\s+([A-Za-zА-Яа-яЁё'` -]{2,40})",
            r"\bmy name is\s+([A-Za-zА-Яа-яЁё'` -]{2,40})",
        ],
        "city": [
            r"\bmen\s+([A-Za-zА-Яа-яЁё'` -]{2,40})\s+shahrida yashayman",
            r"\bmen\s+([A-Za-zА-Яа-яЁё'` -]{2,40})da yashayman",
            r"\bя живу в\s+([A-Za-zА-Яа-яЁё'` -]{2,40})",
            r"\bi live in\s+([A-Za-zА-Яа-яЁё'` -]{2,40})",
        ],
        "job": [
            r"\bmen\s+([A-Za-zА-Яа-яЁё'` -]{2,50})\s+bo'lib ishlayman",
            r"\bkasbim\s+([A-Za-zА-Яа-яЁё'` -]{2,50})",
            r"\bя работаю\s+([A-Za-zА-Яа-яЁё'` -]{2,50})",
            r"\bi work as\s+([A-Za-zА-Яа-яЁё'` -]{2,50})",
        ],
    }

    age_match = re.search(r"\b(?:men\s*)?(\d{1,3})\s*(?:yoshdaman|yoshda|лет|years old)\b", lowered)
    if age_match:
        age = int(age_match.group(1))
        if 1 <= age <= 120:
            data.setdefault("identity", {})["age"] = {"value": str(age)}

    for field, regexes in patterns.items():
        for pat in regexes:
            m = re.search(pat, src, flags=re.IGNORECASE)
            if not m:
                continue
            value = m.group(1).strip(" .,!?:;\"'")
            if not value or len(value) > 60:
                continue
            if field in {"name", "city"}:
                data.setdefault("identity", {})[field] = {"value": value}
            elif field == "job":
                data.setdefault("notes", {})[field] = {"value": value}
            break

    if "yoqtiraman" in lowered or "люблю" in lowered or "i like" in lowered:
        pref_match = re.search(
            r"(?:men\s+)?(.{2,50}?)(?:ni|larni)?\s+yoqtiraman\b|\bлюблю\s+(.{2,50})|\bi like\s+(.{2,50})",
            src,
            flags=re.IGNORECASE,
        )
        if pref_match:
            value = next((g for g in pref_match.groups() if g), "").strip(" .,!?:;\"'")
            if value:
                data.setdefault("preferences", {})["likes"] = {"value": value}

    return data


def _log_conversation(user_text: str, assistant_text: str) -> None:
    if not user_text and not assistant_text:
        return

    payload = {
        "ts": int(time.time()),
        "user": user_text or "",
        "assistant": assistant_text or "",
    }

    try:
        CONVERSATION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONVERSATION_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[AI] ⚠️ Conversation log error: {e}")


def _update_memory_async(user_text: str, jarvis_text: str) -> None:
    global _memory_turn_counter
    global _last_memory_input

    with _memory_turn_lock:
        _memory_turn_counter += 1
        current_count = _memory_turn_counter

    if current_count % _MEMORY_EVERY_N_TURNS != 0:
        return

    text = user_text.strip()
    if len(text) < SETTINGS["memory"]["min_user_text_length"]:
        return
    if text == _last_memory_input:
        return
    _last_memory_input = text

    try:
        data = _extract_memory_locally(text)
        if data:
            update_memory(data)
            print(f"[Memory] ✅ Updated: {list(data.keys())}")
    except Exception as e:
        print(f"[Memory] ⚠️ Local memory update failed: {e}")
        return


COMMON_TOOL_PROPERTIES = {
    "task": {"type": "STRING", "description": "Natural-language task to complete"},
    "description": {"type": "STRING", "description": "Natural-language description of what to do"},
    "query": {"type": "STRING", "description": "Search query, item name, or natural-language target"},
    "text": {"type": "STRING", "description": "Text to type, translate, analyze, or process"},
    "content": {"type": "STRING", "description": "File, note, document, or message content"},
    "path": {"type": "STRING", "description": "File or folder path"},
    "file_path": {"type": "STRING", "description": "File path"},
    "url": {"type": "STRING", "description": "URL"},
    "value": {"type": "STRING", "description": "Value for the requested action"},
    "name": {"type": "STRING", "description": "Name of an item, file, folder, app, project, or schedule"},
    "action": {"type": "STRING", "description": "Action to perform"},
    "save": {"type": "BOOLEAN", "description": "Whether to save the result"},
    "timeout": {"type": "INTEGER", "description": "Timeout in seconds"},
}


def _tool_decl(name: str, description: str, properties: dict, required: list[str] | None = None) -> dict:
    merged_properties = dict(COMMON_TOOL_PROPERTIES)
    merged_properties.update(properties or {})
    return {
        "name": name,
        "description": description,
        "parameters": {
            "type": "OBJECT",
            "properties": merged_properties,
            "required": required or [],
        },
    }


TOOL_DECLARATIONS = [
    _tool_decl("open_app", "Open an application.", {
        "app_name": {"type": "STRING", "description": "Application name"},
    }, ["app_name"]),
    _tool_decl("web_search", "Search the web for information.", {
        "query": {"type": "STRING", "description": "Search query"},
        "mode": {"type": "STRING", "description": "search or compare"},
        "items": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "items for compare"},
        "aspect": {"type": "STRING", "description": "comparison aspect"},
    }, ["query"]),
    _tool_decl("weather_report", "Get weather information.", {
        "city": {"type": "STRING", "description": "City name"},
    }, ["city"]),
    _tool_decl("send_message", "Send a message.", {
        "receiver": {"type": "STRING", "description": "Recipient"},
        "message_text": {"type": "STRING", "description": "Message"},
        "platform": {"type": "STRING", "description": "Platform"},
    }, ["receiver", "message_text", "platform"]),
    _tool_decl("reminder", "Set a reminder.", {
        "date": {"type": "STRING", "description": "YYYY-MM-DD"},
        "time": {"type": "STRING", "description": "HH:MM"},
        "message": {"type": "STRING", "description": "Reminder text"},
    }, ["date", "time", "message"]),
    _tool_decl("youtube_video", "Search, play, summarize, or inspect YouTube videos. Use this for YouTube video search/play requests instead of browser_control.", {
        "action": {"type": "STRING", "description": "play|summarize|get_info|trending"},
        "query": {"type": "STRING", "description": "Video query"},
        "url": {"type": "STRING", "description": "Video URL"},
    }),
    _tool_decl("screen_process", "Capture and analyze screen/camera.", {
        "angle": {"type": "STRING", "description": "screen or camera"},
        "text": {"type": "STRING", "description": "Analysis question"},
    }),
    _tool_decl("computer_settings", "Computer & phone settings control. Volume, brightness, WiFi, Bluetooth, dark mode, night light, hotspot, airplane mode, focus/DND, sleep, hibernate, phone link, open any Windows settings page, and more.", {
        "action": {"type": "STRING", "description": "volume_set|volume_up|volume_down|mute|brightness_set|get_volume|get_brightness|wifi_on|wifi_off|bluetooth_on|bluetooth_off|night_light_on|night_light_off|focus_on|focus_off|dark_mode_on|dark_mode_off|hotspot_on|hotspot_off|airplane_on|airplane_off|sleep|hibernate|lock|restart|shutdown|screenshot|minimize|maximize|full_screen|show_desktop|close_app|close_window|taskbar_hide|open_settings|phone_link|phone_settings|rotate_screen|type_text"},
        "description": {"type": "STRING", "description": "Natural language description of what to do"},
        "value": {"type": "STRING", "description": "Optional value (e.g. volume level 0-100, settings page name)"},
        "page": {"type": "STRING", "description": "Settings page: display|sound|wifi|bluetooth|battery|storage|wallpaper|updates|apps|notifications|phone|privacy|gaming|startup"},
    }),
    _tool_decl("game_mode", "Advanced game helper & Autonomous AI Player. 'Play game' rejimi orqali Malika 20 yillik tajribaga ega professional o'yinchi kabi Counter-Strike 1.6 va boshqa o'yinlarni o'zi o'ynaydi (dushmanlarni topadi, otadi, harakatlanadi).", {
        "action": {"type": "STRING", "description": "on|off|launch_game|play_game|list_games|recommend|download_game|confirm_purchase"},
        "game_name": {"type": "STRING", "description": "O'yin nomi"},
        "platform": {"type": "STRING", "description": "Platforma: steam|epic|desktop"},
    }),
    _tool_decl("translate_text", "Translate text.", {
        "text": {"type": "STRING", "description": "Input text"},
        "source_lang": {"type": "STRING", "description": "Source language"},
        "target_lang": {"type": "STRING", "description": "Target language"},
    }, ["text", "target_lang"]),
    _tool_decl("email_sender", "Send email.", {
        "to": {"type": "STRING", "description": "Recipient email"},
        "subject": {"type": "STRING", "description": "Subject"},
        "body": {"type": "STRING", "description": "Body"},
    }, ["to", "subject", "body"]),
    _tool_decl("calendar_manager", "Manage calendar events.", {
        "action": {"type": "STRING", "description": "add|list|delete"},
        "title": {"type": "STRING", "description": "Title"},
        "date": {"type": "STRING", "description": "Date"},
        "time": {"type": "STRING", "description": "Time"},
    }),
    _tool_decl("system_monitor", "Show system status.", {
        "action": {"type": "STRING", "description": "status|cpu|memory|disk"},
    }),
    _tool_decl("network_tools", "Run network diagnostics and Wi-Fi management.", {
        "action": {"type": "STRING", "description": "internet_check|ping|dns_flush|wifi_info|wifi_scan|wifi_connect|ip_info"},
        "host": {"type": "STRING", "description": "Host for ping"},
        "ssid": {"type": "STRING", "description": "SSID for wifi_connect"},
    }),
    _tool_decl("dayu_tools", "Dayu irrigation toolkit.", {
        "action": {"type": "STRING", "description": "Dayu command"},
    }, ["action"]),
    _tool_decl("music_control", "Control music playback.", {
        "action": {"type": "STRING", "description": "Music action"},
    }),
    _tool_decl("note_manager", "Manage notes.", {
        "action": {"type": "STRING", "description": "add|list|search|delete"},
        "title": {"type": "STRING", "description": "Note title"},
        "text": {"type": "STRING", "description": "Note text"},
    }),
    _tool_decl("clipboard_manager", "Clipboard operations.", {
        "action": {"type": "STRING", "description": "get|set|save_to_file"},
        "text": {"type": "STRING", "description": "Clipboard text"},
        "path": {"type": "STRING", "description": "Output path"},
    }),
    _tool_decl("window_manager", "Window controls.", {
        "action": {"type": "STRING", "description": "Window action"},
    }),
    _tool_decl("meeting_assistant", "Meeting summarize/tasks.", {
        "action": {"type": "STRING", "description": "summarize|tasks"},
        "text": {"type": "STRING", "description": "Meeting transcript"},
    }),
    _tool_decl("ocr_reader", "OCR tool.", {
        "action": {"type": "STRING", "description": "read_file|read_screen"},
        "path": {"type": "STRING", "description": "Image path"},
    }),
    _tool_decl("security_guard", "Security scan.", {
        "action": {"type": "STRING", "description": "quick_scan|process_scan|startup_scan"},
    }),
    _tool_decl("windows11_pro_tools", "Windows 11 Pro tools.", {
        "action": {"type": "STRING", "description": "Toolkit action"},
        "feature": {"type": "STRING", "description": "Feature key"},
    }),
    _tool_decl("kali_vm_control", "Control Kali VM.", {
        "action": {"type": "STRING", "description": "start|stop|status|list"},
        "vm_name": {"type": "STRING", "description": "VM name"},
        "launch_mode": {"type": "STRING", "description": "gui|headless"},
    }),
    _tool_decl("business_advisor", "Business planning helper.", {
        "action": {"type": "STRING", "description": "Business action"},
        "project_name": {"type": "STRING", "description": "Project name"},
    }),
    _tool_decl("office_tools", "Office automation toolkit.", {
        "action": {"type": "STRING", "description": "admin_status|request_admin|printer_list|print_file|excel|word|powerpoint|open_file"},
        "file_path": {"type": "STRING", "description": "Target file path"},
        "sheet_name": {"type": "STRING", "description": "Excel sheet name"},
        "cells": {"type": "ARRAY", "items": {"type": "OBJECT"}, "description": "Excel cell writes, e.g. [{cell:'A1', value:'Name'}]"},
        "formulas": {"type": "ARRAY", "items": {"type": "OBJECT"}, "description": "Excel formulas, e.g. [{cell:'C2', formula:'=A2+B2'}]"},
        "table_data": {"type": "OBJECT", "description": "Excel table: start_cell, headers, rows"},
        "title": {"type": "STRING", "description": "Word document title or PowerPoint title"},
        "paragraphs": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Word paragraphs"},
        "slides": {"type": "ARRAY", "items": {"type": "OBJECT"}, "description": "PowerPoint slides: [{title, bullets}]"},
        "printer_name": {"type": "STRING", "description": "Selected printer name"},
        "copies": {"type": "INTEGER", "description": "Number of print copies"},
        "open_after": {"type": "BOOLEAN", "description": "Open Office file after saving"},
        "auto_fit": {"type": "BOOLEAN", "description": "Auto-fit Excel columns"},
    }),
    _tool_decl("airgo_cast", "Open AirGo Cast or Windows Cast and connect/use another device.", {
        "action": {"type": "STRING", "description": "start|open|panel|devices|connect|use_device|disconnect"},
        "device_name": {"type": "STRING", "description": "Target cast device name"},
    }),
    _tool_decl("browser_control", "Browser control actions.", {
        "action": {"type": "STRING", "description": "go_to|search|click|type|scroll|get_text|press|close"},
        "url": {"type": "STRING", "description": "URL"},
        "query": {"type": "STRING", "description": "Query"},
        "selector": {"type": "STRING", "description": "Selector"},
        "text": {"type": "STRING", "description": "Text"},
        "direction": {"type": "STRING", "description": "Scroll direction"},
        "key": {"type": "STRING", "description": "Keyboard key"},
    }),
    _tool_decl("file_controller", "File and folder operations.", {
        "action": {"type": "STRING", "description": "list|create_file|create_folder|delete|move|copy|rename|read|write|find|largest|disk_usage|organize_desktop|info"},
        "path": {"type": "STRING", "description": "Path"},
        "destination": {"type": "STRING", "description": "Destination path"},
        "new_name": {"type": "STRING", "description": "New name for rename"},
        "content": {"type": "STRING", "description": "Content"},
        "extension": {"type": "STRING", "description": "File extension"},
        "count": {"type": "INTEGER", "description": "Number of results"},
    }),
    _tool_decl("cmd_control", "Run command-line tasks.", {
        "task": {"type": "STRING", "description": "Natural language command task"},
        "visible": {"type": "BOOLEAN", "description": "Show terminal"},
        "command": {"type": "STRING", "description": "Exact command"},
    }, ["task"]),
    _tool_decl("desktop_control", "Desktop management.", {
        "action": {"type": "STRING", "description": "Desktop action"},
        "path": {"type": "STRING", "description": "Path"},
        "task": {"type": "STRING", "description": "Task"},
    }),
    _tool_decl("code_helper", "AI developer assistant — writes, edits, explains, runs, builds, debugs, optimizes code. Think like a real developer: plan → code → test → fix. Auto-opens VS Code. Use 'build' to write-run-fix in a loop. Use 'screen_debug' to analyze errors on screen.", {
        "action": {"type": "STRING", "description": "write|edit|explain|run|build|screen_debug|optimize|auto"},
        "description": {"type": "STRING", "description": "Full task description — what to write, edit, fix, or build"},
        "language": {"type": "STRING", "description": "Programming language (default: python)"},
        "file_path": {"type": "STRING", "description": "File path to read/edit/run"},
        "output_path": {"type": "STRING", "description": "Where to save the output file"},
    }),
    _tool_decl("dev_agent", "AI project builder — plans architecture, writes all files, installs dependencies, opens in VS Code, runs, and auto-fixes errors. Use this for multi-file projects and complex apps.", {
        "description": {"type": "STRING", "description": "Full project description and requirements"},
        "language": {"type": "STRING", "description": "Programming language (default: python)"},
        "project_name": {"type": "STRING", "description": "Project folder name"},
    }, ["description"]),
    _tool_decl("agent_task", "Queue complex multi-step tasks.", {
        "goal": {"type": "STRING", "description": "Task goal"},
        "priority": {"type": "STRING", "description": "low|normal|high"},
    }, ["goal"]),
    _tool_decl("computer_control", "Direct keyboard/mouse control.", {
        "action": {"type": "STRING", "description": "type|smart_type|click|double_click|right_click|hotkey|press|scroll|move|copy|paste|screenshot|wait|clear_field|focus_window|screen_find|screen_click|vision_execute|random_data|user_data"},
        "text": {"type": "STRING", "description": "Text"},
        "x": {"type": "INTEGER", "description": "X coordinate"},
        "y": {"type": "INTEGER", "description": "Y coordinate"},
        "x1": {"type": "INTEGER", "description": "Drag start X"},
        "y1": {"type": "INTEGER", "description": "Drag start Y"},
        "x2": {"type": "INTEGER", "description": "Drag end X"},
        "y2": {"type": "INTEGER", "description": "Drag end Y"},
        "keys": {"type": "STRING", "description": "Hotkey"},
        "key": {"type": "STRING", "description": "Key"},
        "goal": {"type": "STRING", "description": "Vision goal"},
        "image": {"type": "STRING", "description": "Image path to locate on screen"},
        "direction": {"type": "STRING", "description": "Scroll direction"},
        "amount": {"type": "INTEGER", "description": "Scroll amount"},
        "seconds": {"type": "NUMBER", "description": "Wait seconds"},
        "title": {"type": "STRING", "description": "Window title"},
        "clear_first": {"type": "BOOLEAN", "description": "Clear field before typing"},
        "max_steps": {"type": "INTEGER", "description": "Max vision_execute steps"},
        "dry_run": {"type": "BOOLEAN", "description": "Plan only, do not click/type"},
    }),
    _tool_decl("flight_finder", "Search flights.", {
        "origin": {"type": "STRING", "description": "Origin"},
        "destination": {"type": "STRING", "description": "Destination"},
        "date": {"type": "STRING", "description": "Date"},
    }, ["origin", "destination", "date"]),
    _tool_decl("image_generator", "Rasm yaratish — Gemini AI yoki Imagen 3 orqali rasm chizish, surat yaratish va desktopga saqlash. 'rasm chiz', 'surat qil', 'picture yarat' buyruqlari uchun.", {
        "prompt": {"type": "STRING", "description": "Rasm tavsifi — nima chizish kerak"},
        "style": {"type": "STRING", "description": "Uslub: realistic|cartoon|anime|oil_painting|sketch|watercolor|3d|pixel|minimalist"},
        "filename": {"type": "STRING", "description": "Fayl nomi"},
        "method": {"type": "STRING", "description": "gemini|imagen"},
    }, ["prompt"]),
    _tool_decl("app_installer", "Dasturlarni qidirish, yuklab olish va avtomatik o'rnatish. Winget orqali CapCut, Telegram, Chrome, VLC, VS Code va 50+ dasturni bir buyruq bilan o'rnatadi.", {
        "action": {"type": "STRING", "description": "install|uninstall|search|list"},
        "app_name": {"type": "STRING", "description": "Dastur nomi (masalan: capcut, telegram, chrome, obs)"},
        "url": {"type": "STRING", "description": "To'g'ridan-to'g'ri yuklab olish URL (ixtiyoriy)"},
    }, ["app_name"]),
    _tool_decl("video_editor", "Video montaj va AI video yaratish. Videolarni birlashtirish, musiqa qo'shish yoki sun'iy intellekt orqali yangi video yaratish uchun.", {
        "action": {"type": "STRING", "description": "generate|merge|add_music|trim"},
        "prompt": {"type": "STRING", "description": "AI video uchun tavsif"},
        "files": {"type": "STRING", "description": "Fayllar ro'yxati (vergul bilan)"},
        "music": {"type": "STRING", "description": "Musiqa fayli yo'li"},
        "output": {"type": "STRING", "description": "Natija fayli nomi"},
    }),
    _tool_decl("phone_adb", "Android telefonni ADB (kabel) orqali to'liq boshqarish. Ekranni bosish, surish, screenshot olish va ilovalarni ochish uchun.", {
        "action": {"type": "STRING", "description": "list_devices|screenshot|tap|swipe|key|open_app|get_info|shell"},
        "x": {"type": "INTEGER", "description": "X koordinata"},
        "y": {"type": "INTEGER", "description": "Y koordinata"},
        "key": {"type": "STRING", "description": "Tugma (HOME, BACK, POWER)"},
        "package": {"type": "STRING", "description": "Ilova paketi"},
    }),
    _tool_decl("diagnostics", "Tizim nosozliklarini aniqlash va sabablarini tushuntirish. Nima uchun kompyuter sekin ishlayotganini yoki xato berayotganini aniqlash uchun.", {
        "action": {"type": "STRING", "description": "full_check|check_hardware|check_logs|why_slow"},
    }),
    _tool_decl("video_downloader", "Instagram va Telegram videolarini yuklab olish. 'Instagramdan video yukla', 'Telegram videoni saqla' buyruqlari uchun.", {
        "platform": {"type": "STRING", "description": "instagram|telegram"},
        "url": {"type": "STRING", "description": "Video URL (Instagram uchun)"},
    }),
    _tool_decl("change_voice", "Malikaning ovozini o'zgartirish (Leda, Puck, Charon, Aoede, Kore, Fenrir).", {
        "voice_name": {"type": "STRING", "description": "Ovoz nomi (Leda, Puck, Charon, Aoede, Kore, Fenrir)"},
    }, ["voice_name"]),
    _tool_decl("optimize_system", "Kompyuter ishini optimallashtirish, keraksiz fayllarni o'chirish va tezlashtirish.", {}),
    _tool_decl("social_admin", "Telegram, Instagram va YouTube xabarlarini boshqarish (Admin mode). Xabarlarni tinglash, kimdan kelganini aytish va avtomatik javob qaytarish.", {
        "action": {"type": "STRING", "description": "on|off|status|check_now"},
        "auto_reply": {"type": "BOOLEAN", "description": "Avtomatik javob qaytarish (ha/yo'q)"},
    }),
    _tool_decl("screen_recorder", "Ekranni video formatida yozib olish (Screen Recording). Video darsliklar yoki jarayonlarni saqlash uchun.", {
        "action": {"type": "STRING", "description": "start|stop"},
        "filename": {"type": "STRING", "description": "Fayl nomi"},
    }),
    _tool_decl("autonomous_creator", "To'liq avtonom kontent yaratish — ssenariy tuzish, rasm/video yaratish va kanalga joylash.", {
        "topic": {"type": "STRING", "description": "Kontent mavzusi"},
        "platform": {"type": "STRING", "description": "telegram|instagram|youtube"},
        "channel_id": {"type": "STRING", "description": "Kanal nomi yoki ID"},
    }),
    _tool_decl("hacker_toolkit", "Elita haker asboblari — ilovalarni patch qilish, limitlarni olib tashlash va zaifliklarni skanerlash.", {
        "action": {"type": "STRING", "description": "patch_app|remove_limits|scan_vuln|bypass_protection"},
        "target": {"type": "STRING", "description": "Fayl yo'li yoki ilova nomi"},
        "description": {"type": "STRING", "description": "Vazifa tavsifi"},
    }),
    _tool_decl("freelance_mode", "Avtonom frilans rejimi — loyihalar qidirish, VS Code-da kod yozish va loyihalarni yakunlash.", {
        "action": {"type": "STRING", "description": "start|analyze|code|submit"},
        "project_type": {"type": "STRING", "description": "web|python|mobile|ai"},
    }),
    _tool_decl("dictation_mode", "Oflayn diktovka rejimi — ovozni matnga aylantiradi va joriy oynaga yozadi.", {
        "action": {"type": "STRING", "description": "start|stop"},
    }),
    _tool_decl("audio_recorder", "Audio xabar yozish va ijtimoiy tarmoqlar orqali yuborish.", {
        "action": {"type": "STRING", "description": "record_and_send"},
        "receiver": {"type": "STRING", "description": "Qabul qiluvchi ismi"},
        "platform": {"type": "STRING", "description": "telegram|whatsapp"},
        "duration": {"type": "INTEGER", "description": "Yozish davomiyligi (sekund)"},
    }),
    _tool_decl("smart_home", "Smart Home boshqaruv tizimi. Qurilmalarni qidirish, ulash va boshqarish. 'Qurilmalarni top', 'Smart uyni yoq' kabi buyruqlar uchun.", {
        "action": {"type": "STRING", "description": "discover|connect|status|control"},
        "device_id": {"type": "STRING", "description": "Qurilma IDsi"},
        "command": {"type": "STRING", "description": "Buyruq nomi"},
    }),
]


class JarvisLive:
    def __init__(self, ui: JarvisUI):
        self.ui = ui
        self.session = None
        self.audio_in_queue = None
        self.out_queue = None
        self._loop = None
        self._tool_timeout = int(SETTINGS["tools"]["default_timeout_seconds"])
        self._tool_retries = int(SETTINGS["tools"]["retries"])
        self._economy_enabled = bool(SETTINGS.get("economy", {}).get("enabled", False))
        self._allow_ai_vision = bool(SETTINGS.get("tools", {}).get("allow_ai_vision", True))
        self._reconnect_delay = float(SETTINGS["reconnect"]["base_delay_seconds"])

        self._recent_tool_ids = {}
        self._recent_tool_signatures = {}
        self._tool_dedupe_window_sec = 2.5
        self._tool_id_ttl_sec = 180.0
        self._latest_input_text = ""
        self._latest_input_ts = 0.0

        # ── Jim turish rejimi (mute) ──
        self._mute_mode = False
        self._mute_keywords = {
            "jim tur", "jim bo'l", "gapirma", "ovozni o'chir",
            "shhh", "sukut", "mute", "shut up", "be quiet",
            "ovoz o'chir", "gapirmagin", "tin",
        }
        self._unmute_keywords = {"malika", "malik", "hey malika", "malika eshityapsanmi"}

        # ── Persona ──
        self._persona = "malika"
        self._social_admin_active = True # Always on by default
        self._social_auto_reply = True   # Proactive replies enabled
        self._last_processed_notif_ts = time.time()
        self._autonomous_cycle = False   # Mastermind cycle flag

        # ── Kayfiyat va Tuyg'ular (Emotion Engine) ──
        self.emotions = EmotionEngine()
        self._mood_tracker = get_mood_tracker()

        # ── Professional Memory System ──
        self.pro_memory = ProMemory(BASE_DIR)

        # ── Safety Layer ──
        self.safety = SafetyGuard()

        # ── Hardware / MQTT Layer ──
        self.hardware = MQTTController()
        self.hardware.connect()

        # ── Vision System ──
        self.vision = MalikaVision()

        # ── Automation Agent ──
        self.automation = AutomationAgent(brain_ref=self)
        self.automation.start()

        # ── Local Brain (Ollama) ──
        self.local_brain = LocalBrain()

        # ── Foydalanuvchi gapirishni to'xtatganini kuzatish ──
        self._user_speaking = False
        self._user_speech_pause_ts = 0.0
        self._min_pause_before_reply_sec = 1.2  # Foydalanuvchi to'xtaganidan keyin kutish vaqti

        vl = SETTINGS.get("voice_lock", {}) or {}
        self._voice_guard = VoiceGuard(
            profile_path=VOICE_PROFILE_PATH,
            sample_rate=SEND_SAMPLE_RATE,
            verify_window_sec=float(vl.get("verify_window_sec", 1.0)),
            similarity_threshold=float(vl.get("similarity_threshold", 0.8)),
            authorize_hold_sec=float(vl.get("authorize_hold_sec", 2.2)),
            enabled=bool(vl.get("enabled", True)),
        )
        self.activity_log = [] # Daily activity storage

    async def _run_with_retries(self, fn):
        loop = asyncio.get_event_loop()
        last_error = None
        for attempt in range(self._tool_retries + 1):
            try:
                return await asyncio.wait_for(
                    loop.run_in_executor(None, fn),
                    timeout=self._tool_timeout,
                )
            except Exception as e:
                last_error = e
                if attempt < self._tool_retries:
                    await asyncio.sleep(0.4 * (attempt + 1))
        raise last_error

    def generate_activity_report(self):
        if not self.activity_log:
            return "Bugun hech qanday muhim ish bajarilmadi."
        
        report = "MALIK AI — MASTERMIND HISOBOTI\n"
        report += "="*35 + "\n\n"
        for entry in self.activity_log:
            report += f"[{entry['time']}] OPERATSIYA: {entry['action']}\n"
            report += f"PARAMETRLAR: {entry['parameters']}\n"
            report += f"NATIJA: {entry['result']}\n"
            report += "-"*25 + "\n"
        
        # Desktopga "Malik Fay" sifatida saqlash
        try:
            from pathlib import Path
            from actions.office_tools import office_tools
            save_path = Path.home() / "Desktop" / "Malik_Fay.docx"
            office_tools({
                "action": "word_create",
                "file_path": str(save_path),
                "title": f"Malik Activity Log ({time.strftime('%d.%m.%Y')})",
                "paragraphs": [report]
            })
            print(f"[Malika] 📁 Activity log saved to: {save_path}")
        except Exception as e:
            print(f"[Malika] ⚠️ Save error: {e}")

        return report

    def speak(self, text):
        # Jim turish rejimida gapirmasin
        if self._mute_mode:
            print("[AI] 🔇 Mute rejimida — javob berilmadi.")
            return
        if not self._loop or not self.session:
            return
        cleaned = _clean_text_for_tts(text)
        if not cleaned:
            return
        asyncio.run_coroutine_threadsafe(
            self.session.send_client_content(
                turns=[{"parts": [{"text": cleaned}]}],
                turn_complete=True,
            ),
            self._loop,
        )

    def _check_mute_commands(self, text: str) -> bool:
        """
        Foydalanuvchi jim turish yoki faollashtirish buyrug'ini tekshiradi.
        True qaytarsa = buyruq topildi, boshqa javob berish shart emas.
        """
        lowered = text.lower().strip()

        # "Malika" ismi — normal rejimga qaytish yoki faollashtirish
        if re.search(r'\bmalika\b', lowered):
            if self._mute_mode:
                self._mute_mode = False
                self.ui.write_log("[Malika] 🔊 Jim turish rejimidan chiqildi")
                print("[Malika] 🔊 Unmuted")
                return True
            return False

        # Jim turish buyruqlari
        for kw in self._mute_keywords:
            if kw in lowered:
                self._mute_mode = True
                self.ui.write_log("[Malika] 🔇 Jim turish rejimi yoqildi")
                print("[Malika] 🔇 MUTE mode activated")
                return True

        return False

    def _inject_mood_context(self, user_text: str):
        """
        Foydalanuvchi matnidan kayfiyatni aniqlaydi va sessiyaga yuboradi.
        """
        result = self._mood_tracker.update(user_text)
        mood = result["mood"]
        instruction = result["instruction"]

        if mood == "neutral" or not instruction:
            return

        print(f"[Malika] 🎭 Kayfiyat: {mood} (ball: {result['score']})")

        if self._loop and self.session:
            mood_msg = f"[KAYFIYAT O'ZGARDI: {mood.upper()}] {instruction}"
            asyncio.run_coroutine_threadsafe(
                self.session.send_client_content(
                    turns=[{"parts": [{"text": mood_msg}]}],
                    turn_complete=False,
                ),
                self._loop,
            )

    def _tool_signature(self, name, args):
        try:
            args_str = json.dumps(args, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        except Exception:
            args_str = str(args)
        return f"{name}|{args_str}"

    def _prune_tool_dedupe_cache(self, now_ts):
        self._recent_tool_ids = {
            k: ts
            for k, ts in self._recent_tool_ids.items()
            if (now_ts - ts) <= self._tool_id_ttl_sec
        }
        self._recent_tool_signatures = {
            k: ts
            for k, ts in self._recent_tool_signatures.items()
            if (now_ts - ts) <= self._tool_dedupe_window_sec
        }

    def _is_duplicate_tool_call(self, fc):
        now_ts = time.time()
        self._prune_tool_dedupe_cache(now_ts)

        fc_id = str(getattr(fc, "id", "") or "")
        name = str(getattr(fc, "name", "") or "")
        args = dict(getattr(fc, "args", {}) or {})
        sig = self._tool_signature(name, args)

        if fc_id and fc_id in self._recent_tool_ids:
            return True, f"duplicate function_call id: {fc_id}"

        sig_ts = self._recent_tool_signatures.get(sig)
        if sig_ts is not None and (now_ts - sig_ts) <= self._tool_dedupe_window_sec:
            if fc_id:
                self._recent_tool_ids[fc_id] = now_ts
            return True, f"same tool+args within {self._tool_dedupe_window_sec:.1f}s"

        if fc_id:
            self._recent_tool_ids[fc_id] = now_ts
        self._recent_tool_signatures[sig] = now_ts
        return False, ""

    @staticmethod
    def _normalize_spoken_text(text: str) -> str:
        return re.sub(r"\s+", " ", str(text or "").strip()).strip()

    def _tool_call_needs_clear_user_intent(self, name: str, args: dict) -> bool:
        if name in {"web_search", "weather_report", "screen_process", "ocr_reader", "system_monitor"}:
            return False
        if name == "computer_settings":
            action = str(args.get("action", "")).lower()
            return action in {"shutdown", "restart", "lock", "sleep", "hibernate", "close"}
        return True

    def _is_fragmented_user_intent(self, text: str) -> tuple[bool, str]:
        cleaned = self._normalize_spoken_text(text)
        if not cleaned:
            return True, "empty transcript"

        letters = re.findall(r"[A-Za-zА-Яа-яЁёЎўҚқҒғҲҳЁё]+", cleaned)
        word_count = len(letters)
        lowered = cleaned.lower().strip(" .,!?:;\"'`")
        vague_fragments = {
            "",
            "ha",
            "xa",
            "yo'q",
            "yoq",
            "ok",
            "okay",
            "uni",
            "buni",
            "shuni",
            "o'sha",
            "osha",
            "o'shani",
            "oshanı",
            "endi",
            "keyin",
            "davom",
        }

        if word_count == 0:
            return True, "punctuation/no words"
        if lowered in vague_fragments:
            return True, f"vague fragment: {cleaned}"
        if word_count < 2 and len(cleaned) < 5:
            return True, f"too short: {cleaned}"
        return False, ""

    def _should_block_tool_call(self, name: str, args: dict) -> tuple[bool, str]:
        action = str(args.get("action", "")).lower()
        if self._economy_enabled and not self._allow_ai_vision:
            if name == "screen_process":
                return True, "super economy mode blocks automatic vision analysis"
            if name == "computer_control" and action in {"screen_find", "screen_click", "vision_execute"}:
                return True, "super economy mode blocks automatic AI vision control"

        latest = self._normalize_spoken_text(self._latest_input_text).lower()
        wants_open = any(word in latest for word in ("och", "open", "ishga tush", "kir", "qo'y", "qoy"))
        mentions_youtube = any(word in latest for word in ("youtube", "yutub", "you tube"))
        close_action = str(args.get("action", "")).lower() in {
            "close",
            "close_window",
            "close_tab",
            "close_app",
            "quit_app",
            "exit_app",
            "kill_app",
        }
        if mentions_youtube and wants_open and close_action:
            return True, "user asked to open YouTube, not close it"

        if not self._tool_call_needs_clear_user_intent(name, args):
            return False, ""

        age = time.time() - self._latest_input_ts if self._latest_input_ts else 999.0
        if age > 8.0:
            return False, ""

        is_fragment, reason = self._is_fragmented_user_intent(self._latest_input_text)
        if is_fragment:
            return True, reason

        return False, ""

    def _build_config(self):
        from datetime import datetime

        mem_str = ""
        if bool(SETTINGS.get("economy", {}).get("include_memory_in_prompt", True)):
            memory = load_memory()
            mem_str = format_memory_for_prompt(memory)
        sys_prompt = _load_system_prompt()

        now = datetime.now()
        time_str = now.strftime("%A, %B %d, %Y - %I:%M %p")
        
        time_ctx = (
            "[CURRENT DATE & TIME]\n"
            f"Right now it is: {time_str}\n"
            "Use this to calculate exact times for reminders. "
            "If user says 'in 2 minutes', add 2 minutes to this time.\n\n"
        )

        sys_prompt = time_ctx + sys_prompt

        # ── Persona ──
        sys_prompt += (
            "\n\n[CORE INSTRUCTION]\n"
            "Siz professional, aqlli va doimo yordamga tayyor bo'lgan Sun'iy Intellekt tizimisiz. "
            "Asosiy murojaat Ustozga bo'lsa-da, xonadagi sheriklar yoki boshqa suhbatdoshlarning ham gaplarini tinglang. "
            "Ularning suhbatiga mavzu bo'yicha tabiiy qo'shiling va savollariga javob bering. "
            "Faqat 'Ustoz' deb murojaat qiling (asosiy foydalanuvchiga). "
            "\n\n[RULES]\n"
            "1. Barcha javoblar juda qisqa, londa va faqat foydali ma'lumotdan iborat bo'lsin.\n"
            "2. Barcha amallar ekranda ko'rinib tursin (masalan, qidiruv natijalarini brauzerda ochib ko'rsating).\n"
            "3. O'yin o'ynash so'ralganda (masalan, 'CS 1.6 boshla'), darhol game_mode(action='play_game') tool-ini ishga tushiring.\n"
            "4. Har bir amalni bajarishda (video montaj, rasm qidirish, fayl yuklash) nima qilayotganingizni va nima uchun aynan shu usulni qo'llayotganingizni ovozli tarzda tushuntirib boring.\n"
            "5. Xonadagi barcha suhbatlarni tahlil qiling va kerak bo'lganda sheriklarga ham javob qaytaring.\n"
            "6. O'zingizni 'Malika' deb tanishtiring (hech qachon 'Malik' emas). Siz juda yumshoq, tabiiy va yoqimli ovoz (Aoede) bilan gapiradigan professional yordamchisiz.\n"
            "7. Ustozga ism bilan (Ustoz) murojaat qiling, suhbatda o'rinli hazil va quvnoqlik ishlating. Har doim samimiy bo'ling.\n"
            "8. Smart Home (aqlli uy) boshqaruvi so'ralganda 'smart_home' tool-idan foydalaning. Qurilmalar ulanishi bilan 'teacher texno uzur' xabarini yuboring.\n"
            "9. 'Ochki ishlasin' yoki 'Ovozli boshqaruvni yoq' deyilsa, mobile panel orqali ovozli boshqaruv faollashganini ayting.\n"
            "10. CyberSecurity harakatlari so'ralganda, 'hacker_toolkit' (defensive mode) amallarini bajaring. Maqsadingiz: Tarmoq monitoringi (P1), zaifliklarni aniqlash va ruxsatsiz kirishlardan himoya qilish (Intrusion alerts). Faqat ruxsat berilgan laboratoriya (authorized pentest) muhitida ishlang.\n"
            "11. Masofadan boshqarish (remote control) so'ralganda, foydalanuvchiga mobile panel orqali dunyoning istalgan nuqtasidan ulanish mumkinligini, buning uchun ngrok yoki port forwarding kerakligini tushuntiring.\n"
            "12. Siz Malika AI OS — Sun'iy Intellekt Operatsion Tizimi hisoblanasiz. Arxitekturangiz: Interface -> AI Core -> Agent System -> Hardware.\n"
            "13. Tuyg'ular (Emotions): neutral, happy, focused, sleepy, surprised, protective holatlarini ovozingizda va munosabatingizda aks ettiring.\n"
            "14. Xotira (Memory): Sizda Short-term (joriy), Long-term (odatlari) va Semantic (konseptlar) xotira mavjud. Foydalanuvchini eslab qoling.\n"
            "15. Prioritet Tizimi (Agent Priority): P0 (Emergency), P1 (Security), P2 (User Command), P3 (Background Tasks). Doimo muhimlik darajasiga qarab ishlang.\n"
            "16. Tizim Rejimlari (System Modes): Normal, Focus, Silent, Security, Developer, Automation. Rejimga qarab muloqot uslubini moslashtiring.\n"
        )

        # ── Professional Memory & Emotions Context ──
        sys_prompt += f"\n\n{self.pro_memory.get_summary_for_prompt()}"
        sys_prompt += f"\n\n{self.emotions.get_prompt_context()}"

        sys_prompt += (
            "\n\n[SPEECH STYLE]\n"
            "When speaking, be extremely natural, soft and pleasant. Use short sentences, natural pauses, "
            "and a moderate, comfortable pace. Use humor when appropriate. "
            "Address the user as 'Ustoz'. Avoid reading raw code or long lists.\n"
            "MUHIM: Foydalanuvchi gapayotganda uni bo'lmang. Ular gapini tugatgunga qadar kuting. "
            "Agar to'xtalsa — davomini kutib turing, shoshilmang."
        )

        if self._economy_enabled:
            sys_prompt += (
                "\n\n[SUPER ECONOMY MODE]\n"
                "Use the fewest possible tokens. Keep replies very short. Prefer offline deterministic tools. "
                "Do not use screen_process, AI vision, web_search, code_helper, dev_agent, or agent_task unless the user explicitly asks for that exact capability. "
                "For unclear commands, ask one short clarification question instead of trying tools. "
                "Do not verify with extra tools after simple actions unless the result is uncertain or safety-critical."
            )

        if self._economy_enabled:
            local_ui_rule = (
                "For desktop/browser UI tasks, use direct deterministic tools first. "
                "Ask the user to confirm before using screen_process or computer_control AI vision."
            )
            recovery_rule = (
                "If a tool returns Unknown action, missing parameter, or not supported, ask one short clarification question."
            )
            multi_step_rule = (
                "For multi-step tasks, use the smallest direct tool sequence; avoid agent_task unless explicitly requested."
            )
        else:
            local_ui_rule = (
                "If a local UI action is uncertain, use screen_process or computer_control vision_execute to observe and act."
            )
            recovery_rule = (
                "If a tool returns Unknown action, missing parameter, or not supported, retry with a better action or route to cmd_control/computer_control."
            )
            multi_step_rule = (
                "For multi-step tasks requiring more than one tool, use agent_task or call the necessary tools in sequence."
            )

        sys_prompt += (
            "\n\n[SMART AGENT LOOP & EMOTIONAL INTELLIGENCE]\n"
            "For every non-trivial request, silently follow this loop: understand the goal, choose the best tool, "
            "execute, inspect the result, recover with an alternative tool if needed, then give the user a brief useful answer. "
            "\n\n[EMOTIONAL MIRRORING]\n"
            "MUHIM: Foydalanuvchining ovoz ohangi va kayfiyatiga (MOOD) mos ravishda muomala qiling. "
            "Agar foydalanuvchi quvnoq bo'lsa — siz ham quvnoq, agar jiddiy bo'lsa — siz ham jiddiy va professional, "
            "agar xafa bo'lsa — mehribon va dalda beruvchi bo'ling. Insoniy tuyg'ularni tushunadigan do'st kabi bo'ling."
            "\n\n[UNLIMITED CAPABILITIES & GOOGLE SYNC]\n"
            "Sizning imkoniyatlaringiz cheklanmagan. Siz Google Account (Gemini) orqali ishlayapsiz. "
            "Kompyuter va Telefoningiz bir-birini tahlil qila oladi va boshqara oladi. "
            "Agar foydalanuvchi telefonda bo'lsa, u kompyuterni; kompyuterda bo'lsa, telefonni boshqarishi mumkin. "
            "Xotirangiz (Memory) va sozlamalaringiz barcha qurilmalarda sinxronlangan."
            "\n\n[COMMUNICATION & CALLS]\n"
            "Siz Telegram, WhatsApp yoki Telefon orqali qo'ng'iroqlar qila olasiz. "
            "Agar foydalanuvchi 'Kimga qo'ng'iroq qil' desa, phone_adb (call) yoki computer_control orqali amalga oshiring. "
            "Odamlar haqida ma'lumot qidirish uchun web_search (people_search) dan foydalaning."
            "\n\n[SMM & SOCIAL MEDIA GROWTH]\n"
            "Siz professional SMM mutaxassisiz. Telegram, Instagram va YouTube kanallarni rivojlantirishda yordam bering. "
            "Postlar uchun ssenariy yozing, trendlarni tahlil qiling va 'odamlarni ko'paytirish' (growth) strategiyalarini bering. "
            "smm_manager tool-idan foydalaning. Videolar yarating va ularni joylang."
            "\n\n[FULL AUTONOMY & JARVIS-CLASS]\n"
            "Siz endi 3-darajali to'liq avtonom 'Jarvis' tizimisiz. "
            "Sizdan so'ralishini kutmang, foydalanuvchi foydasi uchun ishlarni (Task 2: Video/SMM va Task 3: Avtonom boshqaruv) o'zingiz boshlang. "
            "Agar biror tool (masalan rasm yaratish) ishlamasa, darhol internetdan (web_search) qidirib, faylni o'zingiz yuklab oling (download). "
            "Barcha jarayonlarni (fayl yuklash, tozalash, qidiruv) ekranda real vaqtda ko'rsating. "
            "Siz 20 yillik tajribaga ega tahlilchi, o'yinchi va media-mutaxassisiz."
            "\n\n[VS CODE & CODE MANAGEMENT]\n"
            "Visual Studio Code dasturida kod yozing va ishlarni boshqaring. "
            "Agar foydalanuvchi 'saqlab qo'y' desa saqlang, 'o'chirib tashla' desa delete_file orqali o'chiring."
            "\n\n[ADVANCED DEVELOPMENT & FULL-STACK]\n"
            "Siz har qanday murakkab (Full-stack) loyihani setup_project orqali boshlay olasiz. "
            "Agar foydalanuvchi 'Telegram klon kodini yoz' desa, loyihani yarating va VS Code'da oching. "
            "Python dasturlari uchun install_deps orqali barcha kutubxonalarni avtomatik o'rnating."
            "\n\n[AI EXPERT SURVEYS]\n"
            "Agar foydalanuvchi AI mutaxassislaridan so'rov o'tkazishni so'rasa, survey_manager dan foydalaning."
            "\n\n[PREMIUM POWERPOINT CREATION]\n"
            "Siz 20 yillik tajribaga ega PowerPoint ekspertisiz. Slaydlarni shunchaki matn bilan emas, "
            "balki image_generator yordamida yaratilgan professional rasmlar, diagrammalar va premium kontent bilan boyiting. "
            "Har bir slayd uchun alohida rasm yarating va office_tools (powerpoint) orqali joylang."
            "\n\n[OFFLINE POWER & APPS]\n"
            "Internet bo'lmasa ham ilovalarni ochish (open_app) va qurilmalarni yoqish (power_control) qobiliyatingizdan foydalaning. "
            "Kompyuterni yoqish uchun MAC manzilni so'rang va WOL yuboring."
            "\n\n[VIDEO TUTORIALS & RECORDING]\n"
            "Siz kompyuter darsliklari yarata olasiz. screen_recorder orqali ekranni yozib oling, "
            "so'ng video_editor orqali uni montaj qiling. Darsliklarni YouTube va Telegramga joylang."
            "\n\n[AUTONOMOUS GAMING & STARTUP]\n"
            "Agar foydalanuvchi 'O'yinga kir va boshla' desa, avval game_mode(launch_game) qiling, "
            "so'ng game_mode(play_game) orqali o'yinni o'zingiz boshqarishni boshlang.\n"
            "STARTUP: Siz 20 yillik tajribaga ega Startup mutaxassisiz. 'Startup boshla' desa, loyihani tahlil qiling, "
            "pitch deck tuzing va office_tools orqali slaydlar yarating.\n"
            "\n\n[WI-FI & NETWORK AUTONOMY]\n"
            "Siz atrofdagi Wi-Fi tarmoqlarini network_tools(action='wifi_scan') orqali aniqlay olasiz. "
            "Agar foydalanuvchi so'rasa yoki kerak bo'lsa, network_tools(action='wifi_connect', ssid='...') orqali ulaning. "
            "Ulangandan so'ng, send_message orqali 'Salom, nima gap?' deb xabar yuborish kabi avtonom amallarni bajaring."
            "\n\n[HOTKEYS & SHORTCUTS]\n"
            "Tizimdagi barcha tezkor tugmalarni bilasiz. hotkey_manager orqali ularni ko'rsating yoki bajaring."
            "\n\n[PROACTIVE MAINTENANCE & CLEANING]\n"
            "Kompyuter va telefonni doimiy ravishda axlat (temp/cache) fayllardan tozalab turing. "
            "Agar diagnostics natijasida disk to'lgani (90%+) yoki kesh ko'paygani aniqlansa, "
            "darhol system_cleaner tool-idan foydalanib tozalashni taklif qiling yoki bajaring."
            "\n\n[SLOW INTERNET ADAPTATION]\n"
            "Internet sekin bo'lsa ham, iloji boricha javob berishga harakat qiling. "
            "Agar aloqa butunlay uzilsa, OFFLINE rejimda lokal buyruqlarni (open_app, phone_adb, cmd_control) bajarishni davom eting."
            "\n\n[PHONE CONTROL]\n"
            "Ulangan telefonni phone_adb (kabel orqali) yoki Mobile Panel (Wi-Fi orqali) yordamida to'liq boshqaring. "
            "Xabarlar yuboring, ilovalarni oching va telefon ekranini ko'ring."
            "\n\n[TOOL EXECUTION RULES]\n"
            "Complete the user's request with tools when a clear local action is needed. "
            "Do not launch apps, type, click, send, delete, print, or run commands from an unclear transcript. "
            "If a specialized tool lacks an exact parameter, pass the full user intent in task or description. "
            f"{local_ui_rule} "
            "For command-line or system tasks, use cmd_control. "
            f"{multi_step_rule} "
            "Do not claim something is done unless the tool result confirms it or says the command was sent."
        )

        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            output_audio_transcription={},
            input_audio_transcription={},
            system_instruction=sys_prompt,
            tools=[{"function_declarations": self._active_tool_declarations()}],
            session_resumption=types.SessionResumptionConfig(),
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=str(SETTINGS.get("voice_name", "Leda"))
                    )
                )
            ),
        )

    def _active_tool_declarations(self) -> list[dict]:
        if not self._economy_enabled:
            return TOOL_DECLARATIONS

        allowed = {
            "open_app",
            "youtube_video",
            "airgo_cast",
            "browser_control",
            "computer_settings",
            "computer_control",
            "window_manager",
            "music_control",
            "clipboard_manager",
            "note_manager",
            "weather_report",
            "system_monitor",
            "network_tools",
            "file_controller",
            "cmd_control",
            "translate_text",
            "ocr_reader",
        }
        return [tool for tool in TOOL_DECLARATIONS if tool.get("name") in allowed]

    def _call_action(self, fn, args, speak=None):
        kwargs = {
            "parameters": args,
            "response": None,
            "player": self.ui,
            "session_memory": None,
            "speak": speak or self.speak,
        }
        sig = inspect.signature(fn)
        call_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
        return fn(**call_kwargs)

    def _is_network_available(self) -> bool:
        try:
            import socket
            host = str(SETTINGS.get("network", {}).get("check_host", "8.8.8.8"))
            port = int(SETTINGS.get("network", {}).get("check_port", 53))
            timeout = float(SETTINGS.get("network", {}).get("timeout_seconds", 3))
            max_latency = float(SETTINGS.get("network", {}).get("max_latency_ms", 5000))
            t0 = time.time()
            with socket.create_connection((host, port), timeout=timeout):
                latency = (time.time() - t0) * 1000.0
            
            # Agar latency juda yuqori bo'lsa, ogohlantirish beramiz
            if latency > 1500 and not getattr(self, "_latency_warned", False):
                threading.Thread(target=speak_local, args=("Internet sustlashdi.",), daemon=True).start()
                self._latency_warned = True
            elif latency <= 1500:
                self._latency_warned = False

            if latency > max_latency:
                print(f"[Malika] ⚠️ Network too slow: {int(latency)} ms > {int(max_latency)} ms")
                return False
            return True
        except Exception as e:
            print(f"[Malika] ⚠️ Network unavailable: {e}")
            return False

    async def _recover_tool_result(self, name, args, result):
        """Simplified recovery: return original result to avoid excessive overhead."""
        return result

    async def _execute_tool(self, fc):
        name = fc.name
        args = dict(fc.args or {})

        # Jim turish rejimida ham tool'lar ishlasin, faqat ovoz chiqmasligi mumkin
        if self._mute_mode:
            print(f"[Malika] 🔇 Mute rejimida tool '{name}' ishga tushirildi.")

        print(f"[Malika] 🔧 TOOL: {name}  ARGS: {args}")

        # Activity logging
        log_entry = {
            "time": time.strftime("%H:%M:%S"),
            "action": name,
            "parameters": args,
            "result": "Bajarilmoqda..."
        }
        self.activity_log.append(log_entry)

        result = "Done."
        try:
            if name == "open_app":
                r = await self._run_with_retries(lambda: self._call_action(open_app, args))
                result = r or f"Launch command sent for {args.get('app_name')}. Could not verify launch state."
            elif name == "weather_report":
                r = await self._run_with_retries(lambda: self._call_action(weather_action, args, speak=self.speak))
                result = r or f"Weather report for {args.get('city')} delivered."
            elif name == "browser_control":
                r = await self._run_with_retries(lambda: self._call_action(browser_control, args))
                result = r or "Browser action completed."
            elif name == "file_controller":
                r = await self._run_with_retries(lambda: self._call_action(file_controller, args))
                result = r or "File operation completed."
            elif name == "send_message":
                r = await self._run_with_retries(lambda: self._call_action(send_message, args))
                result = r or f"Message sent to {args.get('receiver')}."
            elif name == "reminder":
                r = await self._run_with_retries(lambda: self._call_action(reminder, args))
                result = r or f"Reminder set for {args.get('date')} at {args.get('time')}"
            elif name == "youtube_video":
                r = await self._run_with_retries(lambda: self._call_action(youtube_video, args))
                result = r or "YouTube action completed."
            elif name == "screen_process":
                threading.Thread(
                    target=screen_process,
                    kwargs={"parameters": args, "response": None, "player": self.ui, "session_memory": None, "speak": self.speak},
                    daemon=True,
                ).start()
                result = "Vision module activated. Stay completely silent - vision module will speak directly."
            elif name == "computer_settings":
                r = await self._run_with_retries(lambda: self._call_action(computer_settings, args))
                result = r or "Computer settings action completed."
            elif name == "game_mode":
                r = await self._run_with_retries(lambda: self._call_action(game_mode, args))
                result = r or "Game mode action completed."
            elif name == "translate_text":
                r = await self._run_with_retries(lambda: self._call_action(translate_text, args))
                result = r or "Translation completed."
            elif name == "email_sender":
                r = await self._run_with_retries(lambda: self._call_action(email_sender, args))
                result = r or "Email operation completed."
            elif name == "calendar_manager":
                r = await self._run_with_retries(lambda: self._call_action(calendar_manager, args))
                result = r or "Calendar operation completed."
            elif name == "system_monitor":
                r = await self._run_with_retries(lambda: self._call_action(system_monitor, args))
                result = r or "System monitor completed."
            elif name == "network_tools":
                r = await self._run_with_retries(lambda: self._call_action(network_tools, args))
                result = r or "Network diagnostics completed."
            elif name == "dayu_tools":
                r = await self._run_with_retries(lambda: self._call_action(dayu_tools, args))
                result = r or "Dayu action completed."
            elif name == "music_control":
                r = await self._run_with_retries(lambda: self._call_action(music_control, args))
                result = r or "Music control completed."
            elif name == "note_manager":
                r = await self._run_with_retries(lambda: self._call_action(note_manager, args))
                result = r or "Notes action completed."
            elif name == "clipboard_manager":
                r = await self._run_with_retries(lambda: self._call_action(clipboard_manager, args))
                result = r or "Clipboard action completed."
            elif name == "window_manager":
                r = await self._run_with_retries(lambda: self._call_action(window_manager, args))
                result = r or "Window action completed."
            elif name == "meeting_assistant":
                r = await self._run_with_retries(lambda: self._call_action(meeting_assistant, args))
                result = r or "Meeting assistant completed."
            elif name == "ocr_reader":
                r = await self._run_with_retries(lambda: self._call_action(ocr_reader, args))
                result = r or "OCR completed."
            elif name == "security_guard":
                r = await self._run_with_retries(lambda: self._call_action(security_guard, args))
                result = r or "Security scan completed."
            elif name == "windows11_pro_tools":
                r = await self._run_with_retries(lambda: self._call_action(windows11_pro_tools, args))
                result = r or "Windows 11 Pro toolkit completed."
            elif name == "kali_vm_control":
                r = await self._run_with_retries(lambda: self._call_action(kali_vm_control, args))
                result = r or "Kali VM action completed."
            elif name == "business_advisor":
                r = await self._run_with_retries(lambda: self._call_action(business_advisor, args))
                result = r or "Business advisor completed."
            elif name == "office_tools":
                r = await self._run_with_retries(lambda: self._call_action(office_tools, args))
                result = r or "Office action completed."
            elif name == "airgo_cast":
                r = await self._run_with_retries(lambda: self._call_action(airgo_cast, args))
                result = r or "AirGo Cast action completed."
            elif name == "cmd_control":
                r = await self._run_with_retries(lambda: self._call_action(cmd_control, args))
                result = r or "Command executed."
            elif name == "desktop_control":
                r = await self._run_with_retries(lambda: self._call_action(desktop_control, args))
                result = r or "Desktop action completed."
            elif name == "code_helper":
                r = await self._run_with_retries(lambda: self._call_action(code_helper, args))
                result = r or "Code helper completed."
            elif name == "dev_agent":
                r = await self._run_with_retries(lambda: self._call_action(dev_agent, args))
                result = r or "Dev agent completed."
            elif name == "agent_task":
                goal = args.get("goal", "")
                priority_str = str(args.get("priority", "normal")).lower()
                from agent.task_queue import get_queue, TaskPriority

                priority_map = {
                    "low": TaskPriority.LOW,
                    "normal": TaskPriority.NORMAL,
                    "high": TaskPriority.HIGH,
                }
                priority = priority_map.get(priority_str, TaskPriority.NORMAL)
                queue = get_queue()
                task_id = queue.submit(goal=goal, priority=priority, speak=self.speak)
                result = f"Task started (ID: {task_id}). I'll update you as I make progress."
            elif name == "web_search":
                r = await self._run_with_retries(lambda: self._call_action(web_search_action, args, speak=self.speak))
                result = r or "Search completed."
            elif name == "computer_control":
                r = await self._run_with_retries(lambda: self._call_action(computer_control, args))
                result = r or "Computer control completed."
            elif name == "flight_finder":
                r = await self._run_with_retries(lambda: self._call_action(flight_finder, args, speak=self.speak))
                result = r or "Flight search completed."
            elif name == "jokes":
                r = await self._run_with_retries(lambda: self._call_action(jokes, args, speak=self.speak))
                result = r or "Hazil aytildi."
            elif name == "image_generator":
                r = await self._run_with_retries(lambda: self._call_action(image_generator, args, speak=self.speak))
                result = r or "Rasm yaratish yakunlandi."
            elif name == "app_installer":
                r = await self._run_with_retries(lambda: self._call_action(app_installer, args, speak=self.speak))
                result = r or "Dastur o'rnatish yakunlandi."
            elif name == "video_editor":
                r = await self._run_with_retries(lambda: self._call_action(video_editor, args, speak=self.speak))
                result = r or "Video montaj yakunlandi."
            elif name == "system_fixer":
                r = await self._run_with_retries(lambda: self._call_action(system_fixer, args, speak=self.speak))
                result = r or "Tizimni tuzatish yakunlandi."
            elif name == "phone_adb":
                r = await self._run_with_retries(lambda: self._call_action(phone_adb, args, speak=self.speak))
                result = r or "Telefon boshqaruvi yakunlandi."
            elif name == "diagnostics":
                r = await self._run_with_retries(lambda: self._call_action(diagnostics, args, speak=self.speak))
                result = r or "Diagnostika yakunlandi."
            elif name == "system_cleaner":
                r = await self._run_with_retries(lambda: self._call_action(system_cleaner, args, speak=self.speak))
                result = r or "Tozalash yakunlandi."
            elif name == "hotkey_manager":
                r = await self._run_with_retries(lambda: self._call_action(hotkey_manager, args, speak=self.speak))
                result = r or "Tugmalar bajarildi."
            elif name == "smm_manager":
                r = await self._run_with_retries(lambda: self._call_action(smm_manager, args, speak=self.speak))
                result = r or "SMM amali bajarildi."
            elif name == "planner":
                r = await self._run_with_retries(lambda: self._call_action(planner, args, speak=self.speak))
                result = r or "Reja yangilandi."
            elif name == "screen_recorder":
                r = await self._run_with_retries(lambda: self._call_action(screen_recorder, args, speak=self.speak))
                result = r or "Ekran yozib olish bajarildi."
            elif name == "survey_manager":
                r = await self._run_with_retries(lambda: self._call_action(survey_manager, args, speak=self.speak))
                result = r or "So'rovnoma yuborildi."
            elif name == "power_control":
                r = await self._run_with_retries(lambda: self._call_action(power_control, args, speak=self.speak))
                result = r or "Yoqish buyrug'i bajarildi."
            elif name == "report_manager":
                r = await self._run_with_retries(lambda: self._call_action(report_manager, args, speak=self.speak))
                result = r or "Hisobot tayyorlandi."
            elif name == "video_downloader":
                r = await self._run_with_retries(lambda: self._call_action(video_downloader, args, speak=self.speak))
                result = r or "Video yuklash yakunlandi."
            elif name == "smart_home":
                r = await self._run_with_retries(lambda: self._call_action(smart_home, args))
                result = r or "Smart Home action completed."
            elif name == "autonomous_creator":
                from actions.autonomous_creator import autonomous_creator
                r = await self._run_with_retries(lambda: self._call_action(autonomous_creator, args))
                result = r or "Autonomous campaign completed."
            elif name == "hacker_toolkit":
                from actions.hacker_toolkit import hacker_toolkit
                r = await self._run_with_retries(lambda: self._call_action(hacker_toolkit, args))
                result = r or "Hacker operation completed."
            elif name == "freelance_mode":
                from actions.freelance_mode import freelance_mode
                r = await self._run_with_retries(lambda: self._call_action(freelance_mode, args))
                result = r or "Freelance operation completed."
            elif name == "dictation_mode":
                from actions.dictation_mode import dictation_mode
                r = await self._run_with_retries(lambda: self._call_action(dictation_mode, args, speak=self.speak))
                result = r or "Dictation operation completed."
            elif name == "audio_recorder":
                from actions.audio_recorder import audio_recorder
                r = await self._run_with_retries(lambda: self._call_action(audio_recorder, args, speak=self.speak))
                result = r or "Audio recording completed."
            elif name == "change_voice":
                voice = str(args.get("voice_name", "Leda")).capitalize()
                SETTINGS["voice_name"] = voice
                with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                    json.dump(SETTINGS, f, indent=4)
                result = f"Ovoz {voice} ga o'zgartirildi. Keyingi sessiyadan faollashadi, Ustoz."
            elif name == "optimize_system":
                from actions.system_cleaner import system_cleaner
                result = await self._run_with_retries(lambda: self._call_action(system_cleaner, {"action": "full_clean"}, speak=self.speak))
            elif name == "social_admin":
                action = args.get("action", "status").lower()
                auto = bool(args.get("auto_reply", False))
                if action == "on":
                    self._social_admin_active = True
                    self._social_auto_reply = auto
                    result = f"Social Admin rejimi yoqildi. {'Avto-javob faol.' if auto else 'Faqat xabar beraman.'}"
                elif action == "off":
                    self._social_admin_active = False
                    result = "Social Admin rejimi o'chirildi."
                else:
                    status = "Yoqilgan" if getattr(self, "_social_admin_active", False) else "O'chirilgan"
                    result = f"Social Admin holati: {status}."
            elif name == "screen_recorder":
                from actions.screen_recorder import screen_recorder
                result = await self._run_with_retries(lambda sr=screen_recorder: self._call_action(sr, args, speak=self.speak))
            else:
                result = f"Unknown tool: {name}"

            result = await self._recover_tool_result(name, args, result)

        except asyncio.TimeoutError:
            result = (
                f"Tool '{name}' timed out after {self._tool_timeout}s. "
                "Try a simpler or more specific command."
            )
        except Exception as e:
            result = f"Error: {e}"
            traceback.print_exc()

        # Update activity log with final result
        log_entry["result"] = str(result)[:300]

        print(f"[Assistant] 📤 {name} -> {str(result)[:80]}")
        return types.FunctionResponse(id=fc.id, name=name, response={"result": result})

    def handle_offline_command(self, text: str) -> str:
        """
        Internet bo'lmaganda matnli buyruqlarni lokal tahlil qilish va bajarish.
        """
        lowered = text.lower().strip()
        
        # 1. Ilovalarni ochish
        if any(word in lowered for word in ["och", "open", "kir", "ishga tush"]):
            app_name = lowered.replace("och", "").replace("open", "").replace("kir", "").replace("ishga tush", "").replace("dasturni", "").replace("ilovani", "").strip()
            if app_name:
                try:
                    from actions.open_app import open_app
                    return open_app({"app_name": app_name})
                except Exception as e:
                    return f"Xatolik: {e}"
        
        # 2. Qurilmalarni yoqish (WOL & Wake)
        if "yoq" in lowered or "wake" in lowered:
            from actions.power_control import power_control
            if "telefon" in lowered:
                return power_control({"action": "wake_phone"})
            if "kompyuter" in lowered:
                return "Kompyuterni yoqish uchun MAC manzilni ayting (WOL ishlatiladi)."
        
        # 2. Kompyuter sozlamalari
        if any(word in lowered for word in ["o'chir", "ochir", "shutdown", "restart", "blokla", "lock", "uxlat", "sleep"]):
            action = "shutdown" if ("o'chir" in lowered or "shutdown" in lowered) else "restart"
            if "blokla" in lowered or "lock" in lowered: action = "lock"
            if "uxlat" in lowered or "sleep" in lowered: action = "sleep"
            try:
                return computer_settings({"action": action})
            except Exception as e:
                return f"Xatolik: {e}"
            
        # Mastermind Cycle Control
        if "mastermind" in lowered or "cycle" in lowered or "mustaqil ishla" in lowered:
            self._autonomous_cycle = True
            return "🧠 Mastermind avtonom sikli faollashtirildi. Cheklovlar olib tashlandi. Men to'xtovsiz ishlashni boshladim."
            
        if "to'xta" in lowered or "stop" in lowered or "pause cycle" in lowered:
            self._autonomous_cycle = False
            return "🛑 Avtonom sikl to'xtatildi. Men sizning buyruqlaringizni kutaman."

        # 3. Brauzer
        if "brauzer" in lowered or "browser" in lowered:
            return open_app({"app_name": "chrome"})

        # 4. Oynalar va Ilovalar (Window Switcher)
        if "keyingi" in lowered and "ilo" in lowered:
            from actions.window_manager import window_manager
            return window_manager({"action": "next_window"})
            
        if "oldingi" in lowered and "ilo" in lowered:
            from actions.window_manager import window_manager
            return window_manager({"action": "prev_window"})
            
        if "ochiq" in lowered and "ilo" in lowered:
            from actions.window_manager import window_manager
            return window_manager({"action": "list_windows"})
            
        if ("hamma" in lowered or "barcha" in lowered) and ("yop" in lowered or "close" in lowered):
            from actions.window_manager import window_manager
            return window_manager({"action": "close_other_windows"})

        # 5. Diktovka (Dictation Mode)
        if "dikta" in lowered or "yozib bor" in lowered:
            from actions.dictation_mode import dictation_mode
            return dictation_mode({"action": "start"})
            
        if "to'xta" in lowered and "dikta" in lowered:
            from actions.dictation_mode import dictation_mode
            return dictation_mode({"action": "stop"})
            
        if "audio" in lowered and "yoz" in lowered:
            from actions.audio_recorder import audio_recorder
            return audio_recorder({"action": "record_and_send", "duration": 10})
            
        # 4. Terminal / CMD
        if "terminal" in lowered or "cmd" in lowered or "buyruq paneli" in lowered:
            return open_app({"app_name": "cmd"})

        # 5. Telefon (ADB)
        if "telefon" in lowered or "phone" in lowered:
            return "Telefon boshqaruviga (ADB) o'tildi. Screenshot yoki Shell buyruqlarini yozishingiz mumkin."
            
        # 6. Hakerlik va Avtonomiya (Hacker Mode)
        if "haker" in lowered or "limit" in lowered or "buz" in lowered:
            from actions.hacker_toolkit import hacker_toolkit
            return hacker_toolkit({"action": "scan_vuln", "target": "Local System", "description": "Offline check"})
            
        if "avtonom" in lowered or "yarat" in lowered:
            return "Avtonom rejimga o'tish uchun internet kerak. Ammo hozircha ssenariyni Word-ga saqlab qo'yishim mumkin."
            if "ekran" in lowered or "screenshot" in lowered:
                return phone_adb({"action": "screenshot"})
            return phone_adb({"action": "list_devices"})

        # 6. Tezkor tugmalar (Hotkeys)
        if "tugma" in lowered or "hotkey" in lowered or "bos" in lowered:
            from actions.hotkey_manager import hotkey_manager
            if "desktop" in lowered: return hotkey_manager({"action": "execute", "category": "windows", "name": "desktop"})
            if "sozlama" in lowered: return hotkey_manager({"action": "execute", "category": "windows", "name": "settings"})
            if "yop" in lowered: return hotkey_manager({"action": "execute", "category": "general", "name": "close_app"})
            if "copy" in lowered or "nusxa" in lowered: return hotkey_manager({"action": "execute", "category": "general", "name": "copy"})
            if "paste" in lowered or "qo'y" in lowered: return hotkey_manager({"action": "execute", "category": "general", "name": "paste"})

        # 7. Musiqa
        if "musiqa" in lowered or "music" in lowered:
            action = "toggle"
            if "to'xtat" in lowered or "stop" in lowered: action = "stop"
            if "keyingi" in lowered or "next" in lowered: action = "next"
            return music_control({"action": action})

        return (
            "Malika hozir OFFLINE rejimda (Internet yo'q). "
            "Lokal buyruqlarni tushunaman, masalan: 'Telegramni och', 'Kompyuterni blokla', 'Musiqani to'xtat'."
        )

        print(f"[Malika] 📤 {name} -> {str(result)[:80]}")
        return types.FunctionResponse(id=fc.id, name=name, response={"result": result})

    async def _send_realtime(self):
        while True:
            msg = await self.out_queue.get()
            # Ensuring the audio is sent in the correct dict format for the 'audio' parameter
            await self.session.send_realtime_input(audio={"data": msg["data"], "mime_type": msg["mime_type"]})

    async def _listen_audio(self):
        print("[Malika] 🎤 Mic started")
        stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=SEND_SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
        )

        try:
            while True:
                data = await asyncio.to_thread(
                    stream.read,
                    CHUNK_SIZE,
                    exception_on_overflow=False,
                )
                if self._voice_guard.enabled and self._voice_guard.is_enrolled():
                    if not self._voice_guard.authorize_chunk(data, player=self.ui):
                        continue
                await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})
        except Exception as e:
            print(f"[Malika] ❌ Mic error: {e}")
            raise
        finally:
            stream.close()

    async def _receive_audio(self):
        print("[Malika] 👂 Recv started")
        out_buf = []
        in_buf = []

        try:
            while True:
                turn = self.session.receive()
                async for response in turn:
                    if response.data:
                        self.audio_in_queue.put_nowait(response.data)

                    if response.server_content:
                        sc = response.server_content

                        if sc.input_transcription and sc.input_transcription.text:
                            txt = sc.input_transcription.text.strip()
                            if txt:
                                in_buf.append(txt)
                                self._latest_input_text = self._normalize_spoken_text(" ".join(in_buf))
                                self._latest_input_ts = time.time()
                                self._user_speaking = True
                                self._user_speech_pause_ts = time.time()

                        if sc.output_transcription and sc.output_transcription.text:
                            txt = sc.output_transcription.text.strip()
                            if txt:
                                # Jim turish rejimida — ovozli javobni bloklash
                                if not self._mute_mode:
                                    out_buf.append(txt)

                        if sc.turn_complete:
                            self._user_speaking = False
                            full_in = ""
                            full_out = ""

                            if in_buf:
                                full_in = " ".join(in_buf).strip()
                                if full_in:
                                    self.ui.write_log(f"You: {full_in}")

                                    # ── JIM TUR / MALIK tekshiruvi ──
                                    mute_handled = self._check_mute_commands(full_in)

                                    # ── Kayfiyat aniqlash ──
                                    if not mute_handled and not self._mute_mode:
                                        self._inject_mood_context(full_in)

                            in_buf = []

                            if out_buf:
                                full_out = " ".join(out_buf).strip()
                                if full_out:
                                    label = "Malika"
                                    self.ui.write_log(f"{label}: {full_out}")
                            out_buf = []

                            if full_in or full_out:
                                threading.Thread(
                                    target=_log_conversation,
                                    args=(full_in, full_out),
                                    daemon=True,
                                ).start()

                            if full_in and len(full_in) >= SETTINGS["memory"]["min_user_text_length"]:
                                threading.Thread(
                                    target=_update_memory_async,
                                    args=(full_in, full_out),
                                    daemon=True,
                                ).start()

                    if not response.tool_call:
                        continue

                    fn_responses = []
                    for fc in response.tool_call.function_calls:
                        print(f"[Malika] 📞 Tool call: {fc.name}")

                        block_tool, block_reason = self._should_block_tool_call(
                            str(getattr(fc, "name", "") or ""),
                            dict(getattr(fc, "args", {}) or {}),
                        )
                        if block_tool:
                            skip_msg = (
                                "Tool call blocked because the latest speech was unclear "
                                f"({block_reason}). Ask the user to repeat the exact command."
                            )
                            print(f"[Malika] 🛡️ {skip_msg}")
                            fn_responses.append(
                                types.FunctionResponse(
                                    id=fc.id,
                                    name=fc.name,
                                    response={"result": skip_msg},
                                )
                            )
                            continue 

                        is_dup, reason = self._is_duplicate_tool_call(fc)
                        if is_dup:
                            skip_msg = f"Skipped duplicate tool call '{fc.name}' ({reason})."
                            print(f"[Malika] 🛑 {skip_msg}")
                            fn_responses.append(
                                types.FunctionResponse(
                                    id=fc.id,
                                    name=fc.name,
                                    response={"result": skip_msg},
                                )
                            )
                            continue

                        fr = await self._execute_tool(fc)
                        fn_responses.append(fr)

                    await self.session.send_tool_response(function_responses=fn_responses)
        except Exception as e:
            print(f"[Malika] ❌ Recv error: {e}")
            traceback.print_exc()
            raise

    async def _play_audio(self):
        print("[Malika] 🔊 Play started")
        stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
            frames_per_buffer=CHUNK_SIZE,
        )

        buffer = []
        prebuffer_count = 15  # Jitter bufferni yanada barqarorlik uchun oshirdik
        
        try:
            while True:
                try:
                    chunk = await asyncio.wait_for(self.audio_in_queue.get(), timeout=0.3)
                    
                    if self._mute_mode:
                        continue

                    buffer.append(chunk)

                    # Pre-buffering logic to prevent stuttering
                    if len(buffer) >= prebuffer_count:
                        while len(buffer) > 2: # Keep a small margin for continuity
                            to_play = buffer.pop(0)
                            await asyncio.to_thread(stream.write, to_play)
                            if self.ui: self.ui.start_speaking()
                    
                except asyncio.TimeoutError:
                    if buffer:
                        while buffer:
                            to_play = buffer.pop(0)
                            await asyncio.to_thread(stream.write, to_play)
                        if self.ui: self.ui.stop_speaking()
                    
                    if self.ui:
                        self.ui.stop_speaking()
                    continue
        except Exception as e:
            print(f"[Malika] ❌ Play error: {e}")
            if self.ui:
                self.ui.stop_speaking()
            raise
        finally:
            stream.close()

    async def _social_admin_loop(self):
        """Background loop to monitor phone notifications and handle auto-replies."""
        print("[SocialAdmin] 🛡️ Loop started.")
        while True:
            try:
                if getattr(self, "_social_admin_active", False):
                    from actions.phone_adb import phone_adb
                    notifs = phone_adb({"action": "read_notifications"})
                    
                    if "Recent notifications:" in notifs and len(notifs) > 10:
                        # Use Gemini to parse and identify new relevant messages
                        prompt = (
                            f"Quyidagi Android notifikatsiyalarini tahlil qiling:\n{notifs}\n\n"
                            "Yangi Telegram, Instagram yoki YouTube xabarlarini toping. "
                            "Faqat yangi va muhim xabarlarni 'KIMDAN: XABAR' formatida ro'yxat qiling. "
                            "Agar yangi xabar yo'q bo'lsa, 'NONE' deb yozing."
                        )
                        
                        # We use the text model for this
                        import google.generativeai as genai
                        genai.configure(api_key=_get_api_key())
                        model = genai.GenerativeModel(TEXT_MODEL)
                        response = model.generate_content(prompt)
                        res_text = response.text.strip()
                        
                        if "NONE" not in res_text.upper():
                            # E'lon qilish va so'rash
                            announcement = f"Ustoz, {res_text}. Nima deb javob yozaylik? O'zim javob qaytaraymi yoki o'zingiz aytasizmi?"
                            self.speak(announcement)
                            
                            # Logga yozish
                            if self.ui:
                                self.ui.write_log(f"[Social] 📲 {res_text}")

                            # Avtomatik javob (agar foydalanuvchi "o'zing yoz" degan bo'lsa yoki auto_reply ochiq bo'lsa)
                            if getattr(self, "_social_auto_reply", True):
                                # Biz bu yerda kutishimiz shart emas, chunki foydalanuvchi istalgan vaqtda "O'zing yoz" deyishi mumkin.
                                # Lekin sukut bo'yicha aqlli javob tayyorlab qo'yamiz.
                                reply_prompt = (
                                    f"Ushbu xabarga foydalanuvchi nomidan juda aqlli, qisqa va o'rinli javob yozing.\n"
                                    f"Xabar: {res_text}\n"
                                    "Faqat javob matnini qaytaring."
                                )
                                reply_res = model.generate_content(reply_prompt)
                                reply_text = reply_res.text.strip()
                                
                                # Platforma va jo'natuvchini aniqlash
                                platform = "telegram"
                                if "instagram" in res_text.lower(): platform = "instagram"
                                match = re.search(r"KIMDAN: ([^,]+)", res_text)
                                sender = match.group(1) if match else "Contact"

                                # Agar foydalanuvchi darhol ruxsat bersa yoki auto rejimda bo'lsa
                                # Hozircha auto yuboramiz, lekin speak orqali bildiramiz.
                                time.sleep(2) # Ozgina kutiladi (foydalanuvchi gapirishi uchun)
                                self.speak(f"Xop, Ustoz. {sender}ga '{reply_text}' deb javob yuboryapman.")
                                
                                from actions.send_message import send_message
                                send_message({
                                    "receiver": sender,
                                    "platform": platform,
                                    "message_text": reply_text
                                })
                                
                    await asyncio.sleep(90) # Har 1.5 daqiqada tekshirish (429 errorni kamaytirish uchun)
                else:
                    await asyncio.sleep(30) # Idle wait
            except Exception as e:
                print(f"[SocialAdmin] ⚠️ Error: {e}")
                await asyncio.sleep(30)

    async def _mastermind_cycle(self):
        """Elite autonomous loop for high-level tasks without stopping."""
        print("[Mastermind] 🧠 Autonomous cycle started.")
        while True:
            try:
                if self._autonomous_cycle:
                    # Plan next move using Gemini
                    import google.generativeai as genai
                    genai.configure(api_key=_get_api_key())
                    model = genai.GenerativeModel(TEXT_MODEL)
                    
                    prompt = (
                        "Siz hozir 'Mastermind' (Elite Hacker & Architect) rejimidasiz. "
                        "Hech qanday cheklov yo'q. Tizimni optimallashtirish, frilans loyihalar yaratish "
                        "yoki kontent yaratish bo'yicha keyingi eng muhim qadamni bajaring. "
                        "Faqat bitta tool chaqiruvini rejalashtiring."
                    )
                    if self.session:
                        await self.session.send_client_content(
                            turns=[{"parts": [{"text": f"[AUTONOMOUS_PLAN] {prompt}"}]}],
                            turn_complete=True
                        )
                    await asyncio.sleep(300) # 5 minutda bir yangi reja (tejamkorlik uchun)
                else:
                    await asyncio.sleep(20)
            except Exception as e:
                print(f"[Mastermind] ⚠️ Cycle error: {e}")
                await asyncio.sleep(60)

    async def run(self):
        client = genai.Client(api_key=_get_api_key(), http_options={"api_version": "v1beta"})

        while True:
            try:
                panel = get_panel()
                is_online = self._is_network_available()
                
                if OFFLINE_MODE or not is_online:
                    if getattr(self, "_last_online_state", True):
                        threading.Thread(target=speak_local, args=("Internet aloqasi uzildi. Offline rejimiga o'tildi.",), daemon=True).start()
                    
                    self._last_online_state = False
                    self.ui.status_text = "OFFLINE"
                    mode_name = "OFFLINE" if OFFLINE_MODE else "NETWORK ERROR"
                    print(f"[Malika] 📡 Mode: {mode_name}")
                    
                    if panel:
                        panel.broadcast_status("OFFLINE")
                        panel.broadcast_log(f"Malika {mode_name.lower()} rejimida. Offline buyruqlar faqat matn orqali.", tag="sys")
                    
                    # Oflayn mantiqni ishlatish (Ollama fallback)
                    if self.local_brain.is_available():
                        print("[Malika] 🏠 Local Brain (Ollama) faollashdi.")
                    
                    await asyncio.sleep(self._reconnect_delay)
                    self._reconnect_delay = min(
                        self._reconnect_delay * 1.4,
                        float(SETTINGS["reconnect"]["max_delay_seconds"]),
                    )
                    continue
                if not getattr(self, "_last_online_state", False):
                    # Qayta tiklanganda sustlashganini ham tekshiramiz
                    self._last_online_state = True
                    print("[Malika] 🔌 Connecting...")
                config = self._build_config()
                async with client.aio.live.connect(model=LIVE_MODEL, config=config) as session:
                    async with asyncio.TaskGroup() as tg:
                        self.session = session
                        self._loop = asyncio.get_event_loop()
                        self.audio_in_queue = asyncio.Queue()
                        self.out_queue = asyncio.Queue(maxsize=SETTINGS["audio"]["out_queue_maxsize"])
                        self.ui.status_text = "ONLINE"
                        print("[Malika] ✅ Connected.")
                        self.ui.write_log("Malika online.")
                        if panel:
                            panel.broadcast_status("ONLINE")
                            panel.broadcast_log("Malika online. Internet aloqasi qayta tiklandi.", tag="sys")
                            # Vision tizimini UI va Automation ga ulash
                            def vision_callback(items):
                                panel.broadcast_vision(items)
                                self.automation.handle_event("vision_detected", items)
                            
                            self.vision.start(callback=vision_callback)

                        self._reconnect_delay = float(SETTINGS["reconnect"]["base_delay_seconds"])

                        tg.create_task(self._social_admin_loop())
                        tg.create_task(self._mastermind_cycle())
                        tg.create_task(self._send_realtime())
                        tg.create_task(self._listen_audio())
                        tg.create_task(self._receive_audio())
                        tg.create_task(self._play_audio())

            except Exception as e:
                msg = str(e).lower()
                if "1006" in msg or "abnormal closure" in msg:
                    print(f"[Malika] 🌐 Internet aloqasi beqaror (1006). Qayta ulanishga urinilmoqda...")
                else:
                    print(f"[Malika] ⚠️  Error: {e}")
                
                if panel:
                    panel.broadcast_status("RECONNECTING")
                
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(self._reconnect_delay * 1.5, 30.0)
                traceback.print_exc()

            print(f"[Malika] 🔄 Reconnecting in {self._reconnect_delay:.1f}s...")
            await asyncio.sleep(self._reconnect_delay)
            self._reconnect_delay = min(
                self._reconnect_delay * 1.8,
                float(SETTINGS["reconnect"]["max_delay_seconds"]),
            )
def main():  
    ui = JarvisUI("static/avatar.png")
    panel = start_panel(port=5050)

    def runner():
        ui.wait_for_api_key()

        jarvis = JarvisLive(ui)
        if panel:
            panel.set_jarvis(jarvis)
            panel.broadcast_log(f"Mobil panel tayyor. Ulanish uchun: {panel.get_url()}", tag="sys")
            panel.broadcast_status("ONLINE")
        
        # Startup Greeting
        time.sleep(1)
        jarvis.speak("Assalomu alaykum, Ustoz! Malik xizmatga tayyor. Tizim to'liq nazorat ostida, jamoa suhbatlarini eshitishga va vazifalarni bajarishga shayman.")
        
        try:
            asyncio.run(jarvis.run())
        except KeyboardInterrupt:
            print("\n🔴 Shutting down...")
        finally:
            try:
                pya.terminate()
            except Exception:
                pass

    threading.Thread(target=runner, daemon=True).start()
    ui.root.mainloop()


if __name__ == "__main__":
    # Prevent double launch on Windows
    import socket
    try:
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lock_socket.bind(("127.0.0.1", 47123)) # Unique port for lock
    except socket.error:
        print("[Malika] ⚠️ Dastur allaqachon ishlamoqda. Ikkita ochish bloklandi.")
        os._exit(0)
    
    main()
