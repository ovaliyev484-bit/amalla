import ctypes
from pathlib import Path


def get_removable_drives() -> list[Path]:
    """Windowsda USB fleshka kabi kiruvchi disklarni aniqlaydi."""
    drives = []
    mask = ctypes.windll.kernel32.GetLogicalDrives()
    for letter_index in range(26):
        if mask & (1 << letter_index):
            drive = f"{chr(65 + letter_index)}:\\"
            drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive)
            if drive_type == 2:  # DRIVE_REMOVABLE
                drives.append(Path(drive))
    return drives


def list_available_voices() -> list[tuple[int, str, str]]:
    try:
        import pyttsx3

        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        return [(i, v.id, getattr(v, 'name', '')) for i, v in enumerate(voices)]
    except Exception:
        return []


def _init_engine(voice_id: str | None = None):
    import pyttsx3

    engine = pyttsx3.init()
    engine.setProperty("rate", 160)
    engine.setProperty("volume", 1.0)
    if voice_id:
        engine.setProperty("voice", voice_id)
    return engine


def speak_text(text: str, voice_id: str | None = None):
    try:
        engine = _init_engine(voice_id)
        print("[TTS Demo] Ovoz chiqarilmoqda...")
        engine.say(text)
        engine.runAndWait()
        print("[TTS Demo] Ovoz chiqarildi.")
    except Exception as e:
        print(f"[TTS Demo] xato: {e}")
        raise


def save_speech(text: str, output_path: Path, voice_id: str | None = None):
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        engine = _init_engine(voice_id)
        engine.save_to_file(text, str(output_path))
        engine.runAndWait()
        print(f"[TTS Demo] Ovoz faylga saqlandi: {output_path}")
    except Exception as e:
        print(f"[TTS Demo] saqlash xatosi: {e}")
        raise


def main():
    text = (
        "Salom! Bu Malika ovozli klon demo namunasi. "
        "Ovoz tiniq va sof bo‘lishiga harakat qildim. "
        "Endi bu namuna kompyuterga yoki USB fleshkaga saqlanishi mumkin."
    )

    voices = list_available_voices()
    print("[TTS Demo] Mavjud ovozlar:")
    for idx, voice_id, name in voices:
        print(f"  {idx}: {name} ({voice_id})")

    selected_voice_id = voices[0][1] if voices else None
    if selected_voice_id:
        print(f"[TTS Demo] Tanlandi: {voices[0][1]}\n")
    else:
        print("[TTS Demo] Hech qanday ovoz topilmadi, standart ovoz ishlatiladi.\n")

    sample_name = "malika_voice_clone_sample.wav"
    local_path = Path.cwd() / sample_name
    save_speech(text, local_path, selected_voice_id)
    speak_text(text, selected_voice_id)

    removable_drives = get_removable_drives()
    if removable_drives:
        usb_path = removable_drives[0] / sample_name
        save_speech(text, usb_path, selected_voice_id)
        print(f"[TTS Demo] Ovoz fayli USB fleshkaga saqlandi: {usb_path}")
    else:
        print("[TTS Demo] USB fleshka topilmadi. Fayl joriy papkaga saqlandi.")
        print(f"[TTS Demo] Joriy papka: {local_path}")


if __name__ == "__main__":
    main()
