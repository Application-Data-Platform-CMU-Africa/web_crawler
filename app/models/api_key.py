"""
API Key Model
Manages API authentication keys
"""
import uuid
import hashlib
from datetime import datetime, timedelta
from app.extensions import db


class APIKey(db.Model):
    """API Key model for authentication"""

    __tablename__ = 'api_keys'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<APIKey {self.name}>'

    @staticmethod
    def hash_key(key):
        """Hash an API key using SHA-256"""
        return hashlib.sha256(key.encode()).hexdigest()

    @staticmethod
    def generate_key():
        """Generate a new random API key"""
        import secrets
        return f"sk_{'live'}_{secrets.token_urlsafe(32)}"

    def is_expired(self):
        """Check if the API key has expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False

    def is_valid(self):
        """Check if the API key is valid (active and not expired)"""
        return self.is_active and not self.is_expired()

    def update_last_used(self):
        """Update the last used timestamp"""
        self.last_used_at = datetime.utcnow()
        db.session.commit()

    def to_dict(self, include_hash=False):
        """Convert API key to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'is_active': self.is_active,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
        if include_hash:
            data['key_hash'] = self.key_hash
        return data
