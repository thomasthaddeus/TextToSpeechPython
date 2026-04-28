# Gemini TTS Configuration

Gemini TTS uses a dedicated config file instead of Azure's `.env` or Polly's
AWS config path. Keeping Gemini auth and region settings in their own file
makes provider-specific failures much easier to trace.

## Recommended Path

1. Create a local `.gemini.env` file in INI format.
2. Create or choose a Google Cloud service account JSON file with access to
   Cloud Text-to-Speech and the `aiplatform.endpoints.predict` permission.
3. Open `Tools > Settings`.
4. Set `TTS Provider` to `Gemini TTS`.
5. Point `Gemini Config File` at the dedicated config file.
6. Choose a Gemini model, language code, voice, and optional style prompt.
7. Use `Test Gemini TTS`.

## Expected `.gemini.env` Format

```ini
[GEMINI]
project_id = YOUR_GOOGLE_CLOUD_PROJECT_ID
service_account_json = C:\path\to\service-account.json
region = global
```

`project_id` and `service_account_json` are required. `region` defaults to
`global` if omitted.

## Supported Models

The app currently exposes these Gemini-TTS model choices:

- `gemini-2.5-flash-tts`
- `gemini-2.5-pro-tts`

## Prompt And Input Limits

Based on the current Google Cloud Gemini-TTS docs:

- the `text` field can be up to 4,000 bytes
- the `prompt` field can be up to 4,000 bytes
- `text + prompt` can be up to 8,000 bytes total

If those limits are exceeded, the app raises a clear Gemini-specific error
instead of sending a bad request.

## Notes

- Gemini TTS is prompt-controlled and does not use SSML in this app path.
- Gemini-TTS supports style prompts, single-speaker output, and multi-speaker
  output at the provider capability level.
- Region/model availability depends on the configured Google Cloud region.
