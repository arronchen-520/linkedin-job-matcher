import ollama
import logging
import json
import pandas as pd
import re
from pathlib import Path
from utils.logger import setup_logging
from utils.file_path import FILTERED_FILE_PATH

class SalaryParser:
    def __init__(self, model_name):
        self.model = model_name
        self.logger = logging.getLogger(self.__class__.__name__)

    def parse(self, raw_text: str) -> dict:
        """
        Parses raw salary string into structured annual salary data.
        Returns: {'min': int, 'max': int, 'currency': str}
        """
        if not raw_text or pd.isna(raw_text) or str(raw_text).strip() == "":
            return {"min": 0, "max": 0, "currency": "N/A"}

        # Key Prompt
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
            # ollama, format = 'json'
            response = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                format='json', 
                options={'temperature': 0} # Certainty
            )
            
            content = response['message']['content']
            
            return json.loads(content)

        except Exception as e:
            self.logger.warning(f"Error parsing '{raw_text}': {e}")
            return {"min": 0, "max": 0, "currency": "Error"}

if __name__ == "__main__":
    
    # Will need to process mroe files
    setup_logging()
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logger = logging.getLogger(__name__)
    filename = '20260127_Arron_Machine Learning_filtered.csv'
    path = Path(FILTERED_FILE_PATH/filename)
    df = pd.read_csv(path)
    parser = SalaryParser(model_name="llama3.1") # or gemma3:12b
    df[['Min Salary', 'Max Salary', 'Currency']] = df['Salary'].apply(lambda x: pd.Series(parser.parse(x)))
    df.to_csv(path, index = False)