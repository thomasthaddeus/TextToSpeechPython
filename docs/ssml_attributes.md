Style | Description
style="advertisement_upbeat" | Expresses an excited and high-energy tone for promoting a product or service.
style="affectionate" | Expresses a warm and affectionate tone, with higher pitch and vocal energy. The speaker is in a state of attracting the attention of the listener. The personality of the speaker is often endearing in nature.
style="angry" | Expresses an angry and annoyed tone.
style="assistant" | Expresses a warm and relaxed tone for digital assistants.
style="calm" | Expresses a cool, collected, and composed attitude when speaking. Tone, pitch, and prosody are more uniform compared to other types of speech.
style="chat" | Expresses a casual and relaxed tone.
style="cheerful" | Expresses a positive and happy tone.
style="customerservice" | Expresses a friendly and helpful tone for customer support.
style="depressed" | Expresses a melancholic and despondent tone with lower pitch and energy.
style="disgruntled" | Expresses a disdainful and complaining tone. Speech of this emotion displays displeasure and contempt.
style="documentary-narration" | Narrates documentaries in a relaxed, interested, and informative style suitable for dubbing documentaries, expert commentary, and similar content.
style="embarrassed" | Expresses an uncertain and hesitant tone when the speaker is feeling uncomfortable.
style="empathetic" | Expresses a sense of caring and understanding.
style="envious" | Expresses a tone of admiration when you desire something that someone else has.
style="excited" | Expresses an upbeat and hopeful tone. It sounds like something great is happening and the speaker is happy about it.
style="fearful" | Expresses a scared and nervous tone, with higher pitch, higher vocal energy, and faster rate. The speaker is in a state of tension and unease.
style="friendly" | Expresses a pleasant, inviting, and warm tone. It sounds sincere and caring.
style="gentle" | Expresses a mild, polite, and pleasant tone, with lower pitch and vocal energy.
style="hopeful" | Expresses a warm and yearning tone. It sounds like something good will happen to the speaker.
style="lyrical" | Expresses emotions in a melodic and sentimental way.
style="narration-professional" | Expresses a professional, objective tone for content reading.
style="narration-relaxed" | Expresses a soothing and melodious tone for content reading.
style="newscast" | Expresses a formal and professional tone for narrating news.
style="newscast-casual" | Expresses a versatile and casual tone for general news delivery.
style="newscast-formal" | Expresses a formal, confident, and authoritative tone for news delivery.
style="poetry-reading" | Expresses an emotional and rhythmic tone while reading a poem.
style="sad" | Expresses a sorrowful tone.
style="serious" | Expresses a strict and commanding tone. Speaker often sounds stiffer and much less relaxed with firm cadence.
style="shouting" | Expresses a tone that sounds as if the voice is distant or in another location and making an effort to be clearly heard.
style="sports_commentary" | Expresses a relaxed and interested tone for broadcasting a sports event.
style="sports_commentary_excited" | Expresses an intensive and energetic tone for broadcasting exciting moments in a sports event.
style="whispering" | Expresses a soft tone that's trying to make a quiet and gentle sound.
style="terrified" | Expresses a scared tone, with a faster pace and a shakier voice. It sounds like the speaker is in an unsteady and frantic status.
style="unfriendly" | Expresses a cold and indifferent tone.

| Role                    | Description                               |
| ----------------------- | ----------------------------------------- |
| role="Girl"             | The voice imitates a girl.                |
| role="Boy"              | The voice imitates a boy.                 |
| role="YoungAdultFemale" | The voice imitates a young adult female.  |
| role="YoungAdultMale"   | The voice imitates a young adult male.    |
| role="OlderAdultFemale" | The voice imitates an older adult female. |
| role="OlderAdultMale"   | The voice imitates an older adult male.   |
| role="SeniorFemale"     | The voice imitates a senior female.       |
| role="SeniorMale"       | The voice imitates a senior male.         |

The following table describes the usage of the mstts:express-as element's attributes:

Attribute | Description | Required or optional

style | The voice-specific speaking style. You can express emotions like cheerfulness, empathy, and calmness. You can also optimize the voice for different scenarios like customer service, newscast, and voice assistant. If the style value is missing or invalid, the entire mstts:express-as element is ignored and the service uses the default neutral speech. For custom neural voice styles, see the custom neural voice style example. | Required

styledegree | The intensity of the speaking style. You can specify a stronger or softer style to make the speech more expressive or subdued. The range of accepted values are: 0.01 to 2 inclusive. The default value is 1, which means the predefined style intensity. The minimum unit is 0.01, which results in a slight tendency for the target style. A value of 2 results in a doubling of the default style intensity. If the style degree is missing or isn't supported for your voice, this attribute is ignored. | Optional

## `role`

The speaking role-play. The voice can imitate a different age and gender, but the voice name isn't changed. For example, a male voice can raise the pitch and change the intonation to imitate a female voice, but the voice name isn't be changed. If the role is missing or isn't supported for your voice, this attribute is ignored. | Optional

## More Attributes

Attribute | Description | Required or optional
contour | Contour represents changes in pitch. These changes are represented as an array of targets at specified time positions in the speech output. Sets of parameter pairs define each target.
For example:

```xml
<prosody contour="(0%,+20Hz) (10%,-2st) (40%,+10Hz)">
```

The first value in each set of parameters specifies the location of the pitch change as a percentage of the duration of the text. The second value specifies the amount to raise or lower the pitch by using a relative value or an enumeration value for pitch (see pitch).

## Optional `pitch`

Indicates the baseline pitch for the text. Pitch changes can be applied at the sentence level. The pitch changes should be within 0.5 to 1.5 times the original audio. You can express the pitch as:

- **An absolute value**: Expressed as a number followed by "Hz" (Hertz).
    For example

    ```xml
    <prosody pitch="600Hz">some text</prosody>.
    ```

- **A relative value**:
- **As a relative number**: Expressed as a number preceded by "+" or "-" and followed by "Hz" or "st" that specifies an amount to change the pitch.
    The "st" indicates the change unit is semitone, which is half of a tone (a half step) on the standard diatonic scale.
    For example:

    ```xml
    <prosody pitch="+80Hz">some text</prosody>
    ```

    or

    ```xml
    <prosody pitch="-2st">some text</prosody>
    ```

- **As a percentage**: Expressed as a number preceded by "+" (optionally) or "-" and followed by "%", indicating the relative change.
    For example:

    ```xml
    <prosody pitch="50%">some text</prosody>
    ```

    or

    ```xml
    <prosody pitch="-50%">some text</prosody>
    ```

- **A constant value**: `x-low` | `low` | `medium` | `high` | `x-high` | `default`

## Optional `range`

A value that represents the range of pitch for the text. You can express range by using the same absolute values, relative values, or enumeration values used to describe pitch.

## Optional `rate`

Indicates the speaking rate of the text. Speaking rate can be applied at the word or sentence level. The rate changes should be within 0.5 to 2 times the original audio. You can express rate as:

- **A relative value**:
- **As a relative number**: Expressed as a number that acts as a multiplier of the default. For example, a value of 1 results in no change in the original rate. A value of 0.5 results in a halving of the original rate. A value of 2 results in twice the original rate.
- **As a percentage**: Expressed as a number preceded by "+" (optionally) or "-" and followed by "%", indicating the relative change. For example: <prosody rate="50%">some text</prosody> or <prosody rate="-50%">some text</prosody>.
- **A constant value**: | `x-slow` | `slow` | `medium` | `fast` | `x-fast` | `default`

## Optional `volume`

Indicates the volume level of the speaking voice. Volume changes can be applied at the sentence level. You can express the volume as:

- **An absolute value**: Expressed as a number in the range of 0.0 to 100.0, from quietest to loudest, such as 75. The default value is 100.0.
- **A relative value**:
- **As a relative number**: Expressed as a number preceded by "+" or "-" that specifies an amount to change the volume. Examples are +10 or -5.5.
- **As a percentage**: Expressed as a number preceded by "+" (optionally) or "-" and followed by "%", indicating the relative change.

  - For example:

    ```xml
    <prosody volume="50%">some text</prosody>
    ```

    or

    ```xml
    <prosody volume="+3%">some text</prosody>
    ```

- **A constant value**: `silent` | `x-soft` | `soft` | `medium` | `loud` | `x-loud` | `default`

## Audio Formats

| Format | 8 kHz sample rate        | 16 kHz sample rate               | 24 kHz sample rate               | 48 kHz sample rate               |
| ------ | ------------------------ | -------------------------------- | -------------------------------- | -------------------------------- |
| wav    | riff-8khz-16bit-mono-pcm | riff-16khz-16bit-mono-pcm        | riff-24khz-16bit-mono-pcm        | riff-48khz-16bit-mono-pcm        |
| mp3    | N/A                      | audio-16khz-128kbitrate-mono-mp3 | audio-24khz-160kbitrate-mono-mp3 | audio-48khz-192kbitrate-mono-mp3 |
