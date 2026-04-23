"""Text cleaning helpers adapted for TTS preprocessing."""

from __future__ import annotations

import re


class TextCleaner:
    """
    Clean text before it is converted into SSML or speech.
    """

    DEFAULT_CONTRACTIONS = {
        "can't": "cannot",
        "don't": "do not",
        "i'm": "i am",
        "it's": "it is",
        "that's": "that is",
        "there's": "there is",
        "they're": "they are",
        "we're": "we are",
        "what's": "what is",
        "won't": "will not",
        "you're": "you are",
    }

    def __init__(self, contractions=None):
        self.url_pattern = re.compile(r"https?://\S+|www\.\S+")
        self.html_pattern = re.compile(r"<[^>]+>")
        self.email_pattern = re.compile(r"\S+@\S+")
        self.extra_spaces_pattern = re.compile(r"\s+")
        self.contractions = contractions or self.DEFAULT_CONTRACTIONS

    def clean_all(self, text):
        """
        Apply a conservative cleaning pass for speech synthesis.
        """
        cleaned = self.remove_urls(text)
        cleaned = self.remove_html_tags(cleaned)
        cleaned = self.remove_emails(cleaned)
        cleaned = self.expand_contractions(cleaned)
        cleaned = self.remove_extra_spaces(cleaned)
        return cleaned.strip()

    def remove_urls(self, text):
        return self.url_pattern.sub("", text)

    def remove_html_tags(self, text):
        return self.html_pattern.sub(" ", text)

    def remove_emails(self, text):
        return self.email_pattern.sub("", text)

    def remove_extra_spaces(self, text):
        return self.extra_spaces_pattern.sub(" ", text)

    def expand_contractions(self, text):
        expanded = text
        for contraction, full_text in self.contractions.items():
            expanded = re.sub(
                rf"\b{re.escape(contraction)}\b",
                full_text,
                expanded,
                flags=re.IGNORECASE,
            )
        return expanded
