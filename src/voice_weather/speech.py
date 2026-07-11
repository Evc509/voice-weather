import shutil
import subprocess


class SpeechError(RuntimeError):
    pass


def speak(text: str, language: str) -> None:
    if shutil.which("say") is None:
        raise SpeechError("找不到 macOS 的 say 命令")
    voice, rate = ("Tingting", "190") if language == "zh" else ("Samantha", "180")
    result = subprocess.run(["say", "-v", voice, "-r", rate, text], check=False)
    if result.returncode:
        raise SpeechError(f"语音播报失败，退出码 {result.returncode}")

