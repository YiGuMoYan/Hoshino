from pydantic import BaseModel

class AppSettingsBase(BaseModel):
    language: str = "zh_CN"
    theme: str = "system"
    tmdb_api_key: str = ""

class AppSettingsSchema(AppSettingsBase):
    id: int
    class Config:
        from_attributes = True

class LLMConfigBase(BaseModel):
    provider: str = "openai"
    api_key: str = ""
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model: str = "qwen-plus"

class LLMConfigSchema(LLMConfigBase):
    id: int
    class Config:
        from_attributes = True
