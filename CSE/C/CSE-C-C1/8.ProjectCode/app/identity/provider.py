from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from app.models.models import VoterProfile, User
from app.security.crypto import hash_aadhaar
from app.identity.verhoeff import validate_verhoeff

class IdentityVerificationProvider(ABC):
    @abstractmethod
    def verify(self, aadhaar_number: str, db: Session) -> dict:
        pass

class DemoAadhaarProvider(IdentityVerificationProvider):
    """
    Simulated/demo identity provider for Aadhaar verification.
    Does NOT contact UIDAI. Uses locally generated synthetic records.
    Can be replaced by a real adapter implementing the same interface.
    """
    def verify(self, aadhaar_number: str, db: Session) -> dict:
        # checks
        clean = aadhaar_number.replace(" ", "").replace("-", "")
        if len(clean) != 12 or not clean.isdigit():
            return {"success": False, "reason": "Invalid Aadhaar format: must be 12 digits"}
        if not validate_verhoeff(clean):
            return {"success": False, "reason": "Invalid Aadhaar checksum (Verhoeff)"}
        # check existence
        h = hash_aadhaar(clean)
        profile = db.query(VoterProfile).filter(VoterProfile.aadhaar_hash == h).first()
        if not profile:
            return {"success": False, "reason": "Aadhaar not found in voter registry"}
        user = db.query(User).filter(User.id == profile.user_id).first()
        return {
            "success": True,
            "profile": profile,
            "user": user,
            "masked": profile.aadhaar_masked,
            "reason": "Verified via DemoAadhaarProvider (local synthetic registry)"
        }

demo_provider = DemoAadhaarProvider()
