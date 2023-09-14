"""main.py
_summary_

_extended_summary_
"""



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

converter = TextToSSML()
ssml_output = converter.convert(text)
print(ssml_output)


# Voice Effects
voice_effects = SSMLVoiceEffects(default_voice="en-US-JaneNeural")
text = ("I am excited " + voice_effects.adjust_pitch("to be here!", "high") +
       voice_effects.add_emphasis(" It's great.", "strong") +
       voice_effects.change_voice(" How do I sound in another voice?", "en-US-JessaNeural"))
text_with_voice = voice_effects.change_voice(text, "en-US-JasonNeural")

converter = TextToSSML()
ssml_output = converter.convert(text_with_voice)
print(ssml_output)
