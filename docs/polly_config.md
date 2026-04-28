# Amazon Polly Configuration

Amazon Polly uses a dedicated config file instead of reusing the Azure `.env`
path. That separation makes provider-specific credential and region problems
much easier to trace.

## Recommended Path

1. Create a local `.polly.env` file in INI format.
2. Open `Tools > Settings`.
3. Set `TTS Provider` to `Amazon Polly`.
4. Point `Polly Config File` at the dedicated config file.
5. Choose a Polly engine and voice, then use `Test Amazon Polly`.

## Expected `.polly.env` Format

```ini
[POLLY]
aws_access_key_id = YOUR_AWS_ACCESS_KEY_ID
aws_secret_access_key = YOUR_AWS_SECRET_ACCESS_KEY
aws_session_token = OPTIONAL_SESSION_TOKEN
region = us-east-1
```

`aws_session_token` is optional. The other fields are required.

## Resolution Behavior

When the app needs Polly settings, it reads the configured Polly file path from
the saved app settings and then loads the `[POLLY]` section from that file.

If the file is missing or invalid, Polly generation/export stays unavailable
and the app shows a provider-specific setup error instead of falling back to
Azure settings.

## Notes

- Keep the Polly config file local and uncommitted.
- `Amazon Polly` supports `standard`, `neural`, `long-form`, and `generative`
  engines, but actual voice availability depends on the configured AWS region.
- The settings connection test can refresh the voice list from the configured
  AWS region when the Polly config file is valid.
