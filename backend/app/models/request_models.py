from pydantic import BaseModel


class TextRequest(BaseModel):
    text: str


class TextResponse(BaseModel):
    recognized_text: str | None
    response: str
