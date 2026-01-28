import json
import os
import logging
import pandas as pd
import ollama
from pathlib import Path
from typing import Dict, Union
from utils.logger import setup_logging
import numpy as np
from utils.file_path import FILTERED_FILE_PATH

class SalaryParser:
    """
    A utility class to extract and standardize salary information from job descriptions
    using a local Large Language Model (LLM).
    """

    def __init__(self, model_name: str):
        """
        Initializes the SalaryParser with a specific LLM model.

        Args:
            model_name (str): The name of the Ollama model to use (e.g., 'llama3.1').
        """
        self.model = model_name
        self.logger = logging.getLogger(self.__class__.__name__)

    def parse(self, raw_text: str) -> Dict[str, Union[int, str]]:
        """
        Parses a raw salary string into structured annual salary data.

        Args:
            raw_text (str): The raw salary text from a job posting.

        Returns:
            dict: A dictionary containing 'min' (int), 'max' (int), and 'currency' (str).
        """
        if not raw_text or pd.isna(raw_text) or str(raw_text).strip() == "":
            return {"min": 0, "max": 0, "currency": "N/A"}

        # Key Prompt (Kept exactly as provided)
        prompt = f"""
        You are a data extraction engine. Extract annual salary details from the text.

        ### RULES:
        1. **Standardize to Annual:** If text is hourly (e.g., "$60/hr"), multiply by 2000 to get annual. If monthly, multiply by 12.
        2. **Range Logic:** - "100k - 150k" -> min=100000, max=150000
           - "80k+" -> min=80000, max=80000
        3. **Single Value Logic:**
           - If text says "Up to X", "Max X", or just one number "X", set 'min' to 0 and 'max' to X.
        4. **Noise Handling:** If no specific numbers are found (e.g., "Competitive"), output 0 for both.
        5. **Currency:** Defaults to 'CAD' unless 'USD' is explicitly mentioned.
        
        ### OUTPUT FORMAT:
        Strictly output a JSON object: {{"min": <int>, "max": <int>, "currency": "<str>"}}

        ### INPUT TEXT:
        "{raw_text}"
        """

        try:
            # Inference using Ollama with temperature 0 for deterministic results
            response = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                format='json', 
                options={'temperature': 0}
            )
            
            content = response['message']['content']
            return json.loads(content)

        except Exception as e:
            self.logger.warning(f"Error parsing '{raw_text}': {e}")
            return {"min": 0, "max": 0, "currency": "Error"}

    def process_file(self, filename: str):
        """
        Loads a CSV file, parses the 'Salary' column, and updates the file with 
        structured 'Min Salary', 'Max Salary', and 'Currency' columns.

        Args:
            filename (str): The name of the CSV file located in the filtered file path.
        """
        path = Path(FILTERED_FILE_PATH / filename)
        
        try:
            df = pd.read_csv(path)
            self.logger.info(f"Processing salary data for: {filename}")
            
            # Apply parsing logic across the 'Salary' column
            salary_data = df['Salary'].apply(lambda x: pd.Series(self.parse(x)))
            df[['Min Salary', 'Max Salary', 'Currency']] = salary_data
            
            # Save updated dataframe back to the source path
            df.to_csv(path, index=False)
            self.logger.info(f"Successfully saved structured salary data to {path}")
            return df 
        except Exception as e:
            self.logger.error(f"Failed to process file {filename}: {e}")
            return df

    def process_df(self, df: pd.DataFrame):
        """
        Loads a df, parses the 'Salary' column, and updates the file with 
        structured 'Min Salary', 'Max Salary', and 'Currency' columns.

        Args:
            df: The dataframe object from LinkedinScrapper
        """
        
        try:
            self.logger.info(f"Processing salary data.")
            
            # Apply parsing logic across the 'Salary' column
            salary_data = df['Salary'].apply(lambda x: pd.Series(self.parse(x)))
            df[['Min Salary', 'Max Salary', 'Currency']] = salary_data
            
            # Return df
            self.logger.info(f"Successfully extracted structured salary. ")
            
        except Exception as e:
            df[['Min Salary', 'Max Salary', 'Currency']] = np.nan
            self.logger.error(f"Failed to process file.")

# if __name__ == "__main__":
#     # Setup global logging
#     setup_logging()
#     logging.getLogger("httpx").setLevel(logging.WARNING)
#     # Initialize parser and execute processing
#     filename = '20260127_Arron_Machine Learning_filtered.csv'
#     parser = SalaryParser(model_name="llama3.1")
#     parser.process_file(filename)