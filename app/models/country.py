"""
Country Model
Represents countries for geographic filtering
"""
from datetime import datetime
from app.extensions import db


class Country(db.Model):
    """
    Countries with ISO codes for geographic filtering
    """
    __tablename__ = 'countries'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Country Information
    name = db.Column(db.String(255), nullable=False, index=True,
                    comment='Full country name')
    code = db.Column(db.String(3), unique=True, nullable=False, index=True,
                    comment='ISO 3166-1 alpha-3 code (e.g., UGA for Uganda)')
    code_alpha2 = db.Column(db.String(2), unique=True,
                           comment='ISO 3166-1 alpha-2 code (e.g., UG)')
    region = db.Column(db.String(100), index=True,
                      comment='Geographic region (e.g., East Africa)')
    continent = db.Column(db.String(50), index=True,
                         comment='Continent (e.g., Africa)')

    # Additional Information
    flag_emoji = db.Column(db.String(10),
                          comment='Unicode flag emoji')
    has_data_portal = db.Column(db.Boolean, default=False, index=True,
                               comment='Whether country has open data portal')
    portal_url = db.Column(db.String(500),
                          comment='URL to national data portal if exists')

    # Status
    is_active = db.Column(db.Boolean, default=True, index=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                          onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Country {self.code}: {self.name}>'

    def to_dict(self):
        """Convert country to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'code_alpha2': self.code_alpha2,
            'region': self.region,
            'continent': self.continent,
            'flag_emoji': self.flag_emoji,
            'has_data_portal': self.has_data_portal,
            'portal_url': self.portal_url,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    @classmethod
    def find_by_code(cls, code: str):
        """Find country by ISO alpha-3 code"""
        return cls.query.filter_by(code=code.upper()).first()

    @classmethod
    def find_by_alpha2(cls, code: str):
        """Find country by ISO alpha-2 code"""
        return cls.query.filter_by(code_alpha2=code.upper()).first()

    @classmethod
    def get_active_countries(cls):
        """Get all active countries"""
        return cls.query.filter_by(is_active=True).order_by(cls.name).all()

    @classmethod
    def get_countries_with_portals(cls):
        """Get countries that have data portals"""
        return cls.query.filter_by(has_data_portal=True, is_active=True).order_by(cls.name).all()

    @classmethod
    def get_by_region(cls, region: str):
        """Get countries in a specific region"""
        return cls.query.filter_by(region=region, is_active=True).order_by(cls.name).all()

    @classmethod
    def get_by_continent(cls, continent: str):
        """Get countries in a specific continent"""
        return cls.query.filter_by(continent=continent, is_active=True).order_by(cls.name).all()
