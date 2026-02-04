from functools import lru_cache
from app.services.core.organizer import OrganizerService

@lru_cache()
def get_organizer_service() -> OrganizerService:
    """
    Returns a singleton instance of OrganizerService.
    This ensures that the 'journal' (rollback history) is preserved across requests.
    """
    return OrganizerService()
