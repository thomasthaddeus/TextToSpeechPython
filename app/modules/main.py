"""main.py
_summary_

_extended_summary_
"""

from ssml.ssml_config import SSMLConfig
from ssml.ssml_audio_effects import SSMLAudioEffects
from ssml.ssml_voice_effects import SSMLVoiceEffects
from ssml.text_to_ssml import TextToSSML



# Text to SSML
converter = TextToSSML()
text = f"Hello, {converter.add_emphasis('how are you?', 'strong')}" \
       f"{converter.add_break('1s')} I hope" \
       f"{converter.change_rate('everything is fine.', 'slow')}"

ssml_output = converter.convert(text)
ssml_output = converter.convert("Hello, how are you?")
print(ssml_output)


# Audio Effects
audio_effects = SSMLAudioEffects()
text = "Here's a chime sound: " + audio_effects.sound_effect('chime')

# Voice Effects
config = SSMLConfig()
config.set_voice("en-US-JasonNeural")

voice_effects = SSMLVoiceEffects(config)
text = ("I am excited " + voice_effects.adjust_pitch("to be here!", "high") +
       voice_effects.add_emphasis(" It's great.", "strong") +
       voice_effects.change_voice(" How do I sound in another voice?", "en-US-JessaNeural"))

# It will use the "en-US-JasonNeural" voice set in the config
text_with_voice = voice_effects.change_voice(text)

converter = TextToSSML()
ssml_output = converter.convert(text_with_voice)
print(ssml_output)


# Initialize TTS API and the audio processor
tts_api = HypotheticalTTSAPI()  # Placeholder for the actual TTS API
processor = SSMLAudioProcessor(tts_api, './output', 'sample_audio')

audio_effects = SSMLAudioEffects()
text_list = ["Hello, how are you?", "Goodbye!", "See you soon!"]

for text in text_list:
    ssml = audio_effects.add_background_sound(text, "http://example.com/background.mp3")
    processor.generate_and_save_audio(ssml)
