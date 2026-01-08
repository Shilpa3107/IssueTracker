from pydantic import BaseModel

class LabelCreate(BaseModel):
    name: str

class LabelRead(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
