from abc import ABC, abstractmethod
from typing import Optional, Dict
import time

from models import Profile
from config import PROFILE_TTL_SECONDS

class ProfileStore(ABC):
    @abstractmethod
    def get_profile(self, user_id: str) -> Optional[Profile]:
        pass

    @abstractmethod
    def save_profile(self, user_id: str, profile: Profile) -> None:
        pass

class InMemoryProfileStore(ProfileStore):
    def __init__(self):
        self._store: Dict[str, Dict[str, any]] = {}
        self._ttl = PROFILE_TTL_SECONDS

    def get_profile(self, user_id: str) -> Optional[Profile]:
        entry = self._store.get(user_id)
        if entry:
            if time.time() < entry["expiry_time"]:
                return Profile(**entry["profile_data"])
            else:
                # Entry has expired
                del self._store[user_id]
        return None

    def save_profile(self, user_id: str, profile: Profile) -> None:
        expiry_time = time.time() + self._ttl
        self._store[user_id] = {
            "profile_data": profile.model_dump(), # Store as dict for Pydantic re-creation
            "expiry_time": expiry_time
        }

# Singleton instance for the application to use
# This can be replaced with a more sophisticated dependency injection system later if needed.
profile_store_instance: ProfileStore = InMemoryProfileStore() 