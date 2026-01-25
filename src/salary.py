import ollama
import logging
import json
import pandas as pd
import re
from pathlib import Path
from utils.logger import setup_logging
from utils.file_path import FILTERED_FILE_PATH

class SalaryParser:
    def __init__(self, model_name="qwen2.5"):
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

            clean_json = self._extract_json(content)
            
            return clean_json

        except Exception as e:
            self.logger.warning(f"Error parsing '{raw_text}': {e}")
            return {"min": 0, "max": 0, "currency": "Error"}

    def _extract_json(self, text: str) -> dict:
        """Helper to ensure we get a dict back even if LLM adds text around it"""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return {"min": 0, "max": 0, "currency": "ParseError"}

def extract_salary(text:str):
    result = parser.parse(text)
    return result

if __name__ == "__main__":
    
    # Will need to process mroe files
    setup_logging()
    logger = logging.getLogger(__name__)
    path = Path(FILTERED_FILE_PATH/'20260125_Arron_Machine Learning_filtered.csv')
    df = pd.read_csv(path)
    parser = SalaryParser(model_name="qwen2.5")
    df[['min_salary', 'max_salary', 'currency']] = df['Salary'].apply(lambda x: pd.Series(parser.parse(x)))
    df.to_csv(path)