from fastapi import APIRouter
from pydantic import BaseModel
try:
    from pypinyin import pinyin, Style, lazy_pinyin
    PYPINYIN_AVAILABLE = True
except ImportError:
    PYPINYIN_AVAILABLE = False

router = APIRouter()

class TextPayload(BaseModel):
    text: str

@router.post("/initial")
def get_text_initial(payload: TextPayload):
    """
    Get the initial letter/character for grouping (A-Z, #)
    """
    text = payload.text
    if not text:
        return {"initial": "#"}
        
    first_char = text[0]
    
    # English or Number
    if 'a' <= first_char.lower() <= 'z':
        return {"initial": first_char.upper()}
    if '0' <= first_char <= '9':
        return {"initial": "#"}
        
    # Chinese
    if PYPINYIN_AVAILABLE:
        try:
            initials = pinyin(first_char, style=Style.FIRST_LETTER)
            if initials and initials[0]:
                char = initials[0][0][0].upper()
                if 'A' <= char <= 'Z':
                    return {"initial": char}
        except:
            pass
    
    return {"initial": "#"}
