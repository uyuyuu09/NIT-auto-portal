from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()


class GetNotice(BaseModel):
    userid: str = os.getenv("USERID")
    passward: str = os.getenv("PASSWORD")
    email: str = os.getenv("EMAIL")
