import shutil
import subprocess
import threading


class SpeechError(RuntimeError):
    pass


VOICE_PREFERENCES = {
    "zh": ["Tingting", "Meijia"],
    "en": ["Samantha", "Daniel", "Alex"],
    "fr": ["Thomas", "Amelie"],
    "es": ["Monica", "Jorge", "Paulina"],
    "ja": ["Kyoko", "Otoya"],
}

_process_lock = threading.Lock()
_process = None


def available_voices() -> list[str]:
    if shutil.which("say") is None:
        return []
    result = subprocess.run(["say", "-v", "?"], capture_output=True, text=True, check=False)
    return [line.split()[0] for line in result.stdout.splitlines() if line.strip()]


def voice_for(language: str) -> str:
    installed = set(available_voices())
    return next((voice for voice in VOICE_PREFERENCES.get(language, []) if voice in installed), "")


def speak(text: str, language: str) -> None:
    global _process
    if shutil.which("say") is None:
        raise SpeechError("找不到 macOS 的 say 命令")
    voice = voice_for(language)
    if not voice:
        raise SpeechError(f"No installed macOS voice supports language: {language}")
    rate = "190" if language == "zh" else "180"
    with _process_lock:
        _stop_locked()
        process = subprocess.Popen(["say", "-v", voice, "-r", rate, text])
        _process = process
    returncode = process.wait()
    with _process_lock:
        if _process is not process:
            return
        _process = None
    if returncode:
        raise SpeechError(f"语音播报失败，退出码 {returncode}")


def _stop_locked() -> None:
    global _process
    process, _process = _process, None
    if process is not None and process.poll() is None:
        process.terminate()


def stop_speech() -> None:
    with _process_lock:
        _stop_locked()
