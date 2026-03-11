from dependencies import env
import requests
from dto.process import DataFormat

def save_data(body: DataFormat):
    response = requests.post(f"{env.ORCHESTRATION_URL}/save-data", json=body)
    response.raise_for_status()