import os
import requests
import uuid as uuid_lib
from dotenv import load_dotenv

load_dotenv()


class RestAPIClient:
    def __init__(self):
        self.base_url = os.getenv("API_BASE_URL")
        if not self.base_url:
            raise ValueError("API_BASE_URL is not set in .env")

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": f"DomainCLI/{os.getenv('APP_VERSION', '1.0.0')}",
            "Accept": "application/json",
        })

    def validate_uuid(self, uuid_str: str) -> None:
        try:
            uuid_lib.UUID(uuid_str)
        except ValueError:
            raise ValueError(f"Invalid UUID: {uuid_str}")

    def get_metadata(self, uuid_str: str):
        self.validate_uuid(uuid_str)
        url = f"{self.base_url}/file/{uuid_str}/stat/"
        response = self.session.get(url, timeout=30)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def get_content(self, uuid_str: str):
        self.validate_uuid(uuid_str)
        url = f"{self.base_url}/file/{uuid_str}/read/"
        response = self.session.get(url, timeout=30)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.content
