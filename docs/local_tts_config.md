# Offline Python TTS Configuration

Offline Python TTS uses a dedicated optional config file so platform-specific
driver problems can be traced back to one place, while still allowing a no-key,
no-network fallback with default settings.

## Recommended Path

1. Open `Tools > Settings`.
2. Set `TTS Provider` to `Offline Python TTS`.
3. Optionally point `Local TTS Config File` at a dedicated config file.
4. Choose a driver or leave it on `auto`.
5. Use `Test Offline Python TTS`.

## Optional `.local_tts.env` Format

```ini
[LOCAL_TTS]
driver_name = auto
```

Supported driver values in the UI are:

- `auto`
- `sapi5`
- `nsss`
- `espeak`

## Notes

- `Offline Python TTS` is backed by `pyttsx3` and works without cloud
  credentials.
- It is intended as a basic local fallback for privacy-sensitive or offline
  work, not as a full feature match for cloud providers.
- SSML, style prompts, and multi-speaker generation are not supported in this
  provider path.
- Voice availability depends on the operating system and installed local speech
  engines.
- According to the current `pyttsx3` project docs, common platform engines are
  SAPI5 on Windows, NSSpeechSynthesizer on macOS, and eSpeak on Linux.
