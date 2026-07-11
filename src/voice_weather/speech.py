import shutil
import subprocess


class SpeechError(RuntimeError):
    pass


VOICE_PREFERENCES = {
    "zh": ["Tingting", "Meijia"],
    "en": ["Samantha", "Daniel", "Alex"],
    "fr": ["Thomas", "Amelie"],
    "es": ["Monica", "Jorge", "Paulina"],
    "ja": ["Kyoko", "Otoya"],
}


def available_voices() -> list[str]:
    if shutil.which("say") is None:
        return []
    result = subprocess.run(["say", "-v", "?"], capture_output=True, text=True, check=False)
    return [line.split()[0] for line in result.stdout.splitlines() if line.strip()]


def voice_for(language: str) -> str:
    installed = set(available_voices())
    return next((voice for voice in VOICE_PREFERENCES.get(language, []) if voice in installed), "")


def speak(text: str, language: str) -> None:
    if shutil.which("say") is None:
        raise SpeechError("找不到 macOS 的 say 命令")
    voice = voice_for(language)
    if not voice:
        raise SpeechError(f"No installed macOS voice supports language: {language}")
    rate = "190" if language == "zh" else "180"
    result = subprocess.run(["say", "-v", voice, "-r", rate, text], check=False)
    if result.returncode:
        raise SpeechError(f"语音播报失败，退出码 {result.returncode}")
