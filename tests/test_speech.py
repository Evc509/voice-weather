from voice_weather import speech


class FakeProcess:
    def __init__(self):
        self.terminated = False

    def poll(self):
        return None if not self.terminated else -15

    def terminate(self):
        self.terminated = True

    def wait(self):
        return 0


def test_stop_speech_terminates_active_process():
    process = FakeProcess()
    speech._process = process
    speech.stop_speech()
    assert process.terminated is True
    assert speech._process is None
