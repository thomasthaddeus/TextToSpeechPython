""" data_processor.py
_summary_

_extended_summary_

Returns:
    _type_: _description_
"""

import pandas as pd
from app.model.api.azure_tts_api import AzureTTSAPI
from app.model.processors.ssml_audio_processor import SSMLAudioProcessor
from app.model.scraper.pptx_scraper import PPTXScraper


class DataProcessor:
    """
     _summary_

    _extended_summary_
    """
    def __init__(self, api_config_path, ssml_config_path=None):
        """
        __init__ _summary_

        _extended_summary_

        Args:
            api_config_path (_type_): Path to Azure API configuration.
            ssml_config_path (_type_): Retained for backward compatibility.
        """
        # Initialize API and SSML processors with their respective configurations
        self.api_processor = AzureTTSAPI(api_config_path)
        self.ssml_processor = SSMLAudioProcessor()

    def process_text_data(self, text):
        """
        process_text_data _summary_

        _extended_summary_

        Args:
            text (_type_): _description_

        Returns:
            _type_: _description_
        """
        # Process text data to convert it to SSML
        ssml_data = self.ssml_processor.convert_text_to_ssml(text)
        return ssml_data

    def generate_tts_audio(self, ssml_data):
        """
        generate_tts_audio _summary_

        _extended_summary_

        Args:
            ssml_data (_type_): _description_

        Returns:
            _type_: _description_
        """
        # Generate TTS audio from SSML data
        audio_data = self.api_processor.get_audio_from_ssml(ssml_data)
        return audio_data

    def extract_data_from_pptx(self, pptx_path):
        """
        extract_data_from_pptx _summary_

        _extended_summary_

        Args:
            pptx_path (_type_): _description_

        Returns:
            _type_: _description_
        """
        # Extract data from PPTX file
        extracted_data = PPTXScraper().scrape_pptx(pptx_path)
        return extracted_data

    def load_and_process_datafile(self, datafile_path):
        """
        load_and_process_datafile _summary_

        _extended_summary_

        Args:
            datafile_path (_type_): _description_

        Returns:
            _type_: _description_
        """
        # Load and process a data file (e.g., CSV, Excel)
        df = pd.read_csv(datafile_path)
        # Add any specific data processing steps here
        processed_data = df
        return processed_data
