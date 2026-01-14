"""
SDG Model
Represents UN Sustainable Development Goals
"""
from datetime import datetime
from app.extensions import db


class SDG(db.Model):
    """
    UN Sustainable Development Goals (17 goals)
    """
    __tablename__ = 'sdgs'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # SDG Information
    number = db.Column(db.Integer, unique=True, nullable=False, index=True,
                      comment='SDG number (1-17)')
    name = db.Column(db.String(255), nullable=False,
                    comment='SDG name (e.g., No Poverty)')
    description = db.Column(db.Text,
                           comment='Full SDG description')
    icon_url = db.Column(db.String(500),
                        comment='URL to SDG icon/logo')
    color = db.Column(db.String(7),
                     comment='Official SDG color hex code')

    # Keywords for AI classification
    keywords = db.Column(db.Text,
                        comment='Comma-separated keywords for matching datasets to SDGs')

    # Status
    is_active = db.Column(db.Boolean, default=True, index=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                          onupdate=datetime.utcnow, nullable=False)

    # Relationships
    datasets = db.relationship('Dataset', secondary='dataset_sdgs',
                              back_populates='sdgs', lazy='dynamic')

    def __repr__(self):
        return f'<SDG {self.number}: {self.name}>'

    def to_dict(self, include_datasets=False):
        """Convert SDG to dictionary"""
        data = {
            'id': self.id,
            'number': self.number,
            'name': self.name,
            'description': self.description,
            'icon_url': self.icon_url,
            'color': self.color,
            'keywords': self.keywords.split(',') if self.keywords else [],
            'is_active': self.is_active,
            'dataset_count': self.datasets.count(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

        if include_datasets:
            data['datasets'] = [dataset.to_dict() for dataset in self.datasets]

        return data

    @classmethod
    def find_by_number(cls, number: int):
        """Find SDG by number"""
        return cls.query.filter_by(number=number).first()

    @classmethod
    def get_active_sdgs(cls):
        """Get all active SDGs"""
        return cls.query.filter_by(is_active=True).order_by(cls.number).all()

    @classmethod
    def get_all_ordered(cls):
        """Get all SDGs ordered by number"""
        return cls.query.order_by(cls.number).all()
