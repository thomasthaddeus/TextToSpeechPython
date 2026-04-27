import os
from pathlib import Path
import shutil
import sys
import types

import pytest


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication


def install_azure_speech_stub():
    """Provide the Azure SDK shape needed by controller imports."""
    speechsdk = types.SimpleNamespace(
        SpeechConfig=object,
        SpeechSynthesisOutputFormat=types.SimpleNamespace(
            Audio16Khz32KBitRateMonoMp3="Audio16Khz32KBitRateMonoMp3"
        ),
        SpeechSynthesizer=object,
    )
    azure_module = types.ModuleType("azure")
    cognitiveservices_module = types.ModuleType("azure.cognitiveservices")
    speech_module = types.ModuleType("azure.cognitiveservices.speech")
    speech_module.SpeechConfig = speechsdk.SpeechConfig
    speech_module.SpeechSynthesisOutputFormat = speechsdk.SpeechSynthesisOutputFormat
    speech_module.SpeechSynthesizer = speechsdk.SpeechSynthesizer

    sys.modules.setdefault("azure", azure_module)
    sys.modules.setdefault("azure.cognitiveservices", cognitiveservices_module)
    sys.modules.setdefault("azure.cognitiveservices.speech", speech_module)


install_azure_speech_stub()


@pytest.fixture(scope="session")
def qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def runtime_tmp_path(request):
    test_name = request.node.name
    safe_name = "".join(
        character if character.isalnum() or character in ("-", "_") else "_"
        for character in test_name
    )
    path = Path("data/dynamic/tmp/pytest_runtime") / safe_name
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True, exist_ok=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
