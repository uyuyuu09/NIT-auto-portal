from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()


class GetNotice(BaseModel):
    user_id: str = os.getenv("USERNAME")
    passward: str = os.getenv("PASSWORD")
    email: str = os.getenv("EMAIL")
