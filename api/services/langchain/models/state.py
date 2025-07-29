from pydantic import BaseModel
from langchain_core.messages import BaseMessage

class State(BaseModel):
    messages: list[BaseMessage] = []
