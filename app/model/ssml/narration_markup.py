"""Section-level narration markup helpers.

Users can wrap editor text with lightweight narration blocks such as:

[[narration speaker="Avery" voice="en-US-JennyNeural" rate="slow" pause="500ms"]]
Hello from this section.
[[/narration]]

The parser keeps plain text usable while allowing SSML-capable providers to vary
voice, cadence, volume, pitch, emphasis, and pauses per section.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from xml.sax.saxutils import escape


NARRATION_BLOCK_PATTERN = re.compile(
    r"\[\[narration(?P<attrs>[^\]]*)\]\](?P<text>.*?)\[\[/narration\]\]",
    re.DOTALL | re.IGNORECASE,
)
ATTRIBUTE_PATTERN = re.compile(
    r"(?P<name>[a-zA-Z_][\w-]*)\s*=\s*"
    r"(?:\"(?P<double>[^\"]*)\"|'(?P<single>[^']*)'|(?P<bare>[^\s\]]+))"
)

VALID_RATES = {"x-slow", "slow", "medium", "fast", "x-fast"}
VALID_VOLUMES = {"silent", "x-soft", "soft", "medium", "loud", "x-loud"}
VALID_EMPHASIS = {"none", "reduced", "moderate", "strong"}
VALID_PITCHES = {"default", "x-low", "low", "medium", "high", "x-high"}
VALID_PAUSES = {"none", "250ms", "500ms", "1s", "2s"}


@dataclass(frozen=True)
class NarrationSection:
    """One contiguous text section plus optional narration overrides."""

    text: str
    voice: str = ""
    speaker: str = ""
    rate: str = ""
    volume: str = ""
    pitch: str = ""
    pitch_range: str = ""
    emphasis: str = ""
    pause: str = ""


def has_narration_markup(text):
    """Return whether the editor text contains narration blocks."""
    return bool(NARRATION_BLOCK_PATTERN.search(text or ""))


def parse_narration_sections(text):
    """Split editor text into default and marked narration sections."""
    sections = []
    cursor = 0
    source_text = text or ""

    for match in NARRATION_BLOCK_PATTERN.finditer(source_text):
        if match.start() > cursor:
            sections.append(NarrationSection(text=source_text[cursor : match.start()]))

        attrs = _parse_attributes(match.group("attrs"))
        sections.append(
            NarrationSection(
                text=match.group("text"),
                voice=attrs.get("voice", ""),
                speaker=attrs.get("speaker", ""),
                rate=_allowed(attrs.get("rate", ""), VALID_RATES),
                volume=_allowed(attrs.get("volume", ""), VALID_VOLUMES),
                pitch=_allowed(attrs.get("pitch", ""), VALID_PITCHES),
                pitch_range=_allowed(
                    attrs.get("range", attrs.get("pitch_range", "")),
                    VALID_PITCHES,
                ),
                emphasis=_allowed(attrs.get("emphasis", ""), VALID_EMPHASIS),
                pause=_allowed(attrs.get("pause", ""), VALID_PAUSES),
            )
        )
        cursor = match.end()

    if cursor < len(source_text):
        sections.append(NarrationSection(text=source_text[cursor:]))

    return [section for section in sections if section.text.strip()]


def render_plain_narration_text(text, cleaner=None, include_speaker_labels=True):
    """Remove narration markup for providers that do not accept SSML."""
    sections = parse_narration_sections(text)
    if not sections:
        return _clean_text(text, cleaner)

    rendered_sections = []
    for section in sections:
        rendered_text = _clean_text(section.text, cleaner)
        if not rendered_text:
            continue
        if include_speaker_labels and section.speaker:
            rendered_text = f"{section.speaker}: {rendered_text}"
        rendered_sections.append(rendered_text)

    return "\n\n".join(rendered_sections)


def build_narration_ssml(text, settings, cleaner=None):
    """Build an SSML document that honors section-level narration markup."""
    sections = parse_narration_sections(text)
    if not sections:
        sections = [NarrationSection(text=text)]

    body_chunks = [
        _section_to_ssml(section, settings, cleaner)
        for section in sections
        if section.text.strip()
    ]
    body = "\n".join(chunk for chunk in body_chunks if chunk.strip())
    return (
        '<speak version="1.0" '
        'xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">\n'
        f"{body}\n"
        "</speak>"
    )


def _parse_attributes(attribute_text):
    attrs = {}
    for match in ATTRIBUTE_PATTERN.finditer(attribute_text or ""):
        value = (
            match.group("double")
            if match.group("double") is not None
            else match.group("single")
            if match.group("single") is not None
            else match.group("bare")
        )
        attrs[match.group("name").lower()] = (value or "").strip()
    return attrs


def _allowed(value, allowed):
    normalized = (value or "").strip()
    return normalized if normalized in allowed else ""


def _clean_text(text, cleaner):
    if cleaner is None:
        return (text or "").strip()
    return cleaner.clean_all(text or "")


def _effective(value, default_value, ignored_values=()):
    value = (value or "").strip()
    if value and value not in ignored_values:
        return value
    return default_value


def _section_to_ssml(section, settings, cleaner):
    text = _clean_text(section.text, cleaner)
    if not text:
        return ""

    escaped_text = escape(text)
    pause = _effective(section.pause, getattr(settings, "pause_duration", "none"))
    pause_position = getattr(settings, "pause_position", "after")

    if pause != "none":
        pause_tag = f'<break time="{pause}"/>'
        if pause_position == "before":
            escaped_text = f"{pause_tag}{escaped_text}"
        else:
            escaped_text = f"{escaped_text}{pause_tag}"

    emphasis = _effective(
        section.emphasis,
        getattr(settings, "emphasis_level", "none"),
        ignored_values=("none",),
    )
    if emphasis:
        escaped_text = f'<emphasis level="{emphasis}">{escaped_text}</emphasis>'

    prosody_attributes = [
        f'rate="{_effective(section.rate, getattr(settings, "speaking_rate", "medium"))}"',
        f'volume="{_effective(section.volume, getattr(settings, "synthesis_volume", "medium"))}"',
    ]
    pitch = _effective(
        section.pitch,
        getattr(settings, "pitch", "default"),
        ignored_values=("default",),
    )
    pitch_range = _effective(
        section.pitch_range,
        getattr(settings, "pitch_range", "default"),
        ignored_values=("default",),
    )
    if pitch:
        prosody_attributes.append(f'pitch="{pitch}"')
    if pitch_range:
        prosody_attributes.append(f'range="{pitch_range}"')

    prosody_text = (
        f"<prosody {' '.join(prosody_attributes)}>{escaped_text}</prosody>"
    )
    voice = section.voice.strip() or getattr(settings, "voice", "en-US-GuyNeural")
    return f'  <voice name="{escape(voice)}">\n    {prosody_text}\n  </voice>'
