import requests
from typing import Dict, List, Optional

def get_together_models(api_key: str) -> Optional[List[Dict]]:
    """
    Fetch available models from Together AI API
    
    Args:
        api_key (str): Your Together AI API key
    
    Returns:
        Optional[List[Dict]]: List of available models and their details, or None if error occurs
    """
    url = "https://api.together.xyz/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching models: {e}")
        return None