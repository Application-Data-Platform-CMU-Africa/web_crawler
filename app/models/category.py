"""
Category Model
Represents dataset categories/themes
"""
from datetime import datetime
from app.extensions import db


class Category(db.Model):
    """
    Dataset categories (e.g., Health, Education, Agriculture)
    """
    __tablename__ = 'categories'

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Category Information
    name = db.Column(db.String(255), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True,
                    comment='URL-friendly name')
    description = db.Column(db.Text)
    icon = db.Column(db.String(100),
                    comment='Icon name or emoji for UI display')
    color = db.Column(db.String(7),
                     comment='Hex color code for UI (e.g., #FF5733)')

    # Hierarchy Support
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='CASCADE'),
                         nullable=True, index=True)
    parent = db.relationship('Category', remote_side=[id], backref='subcategories')

    # Status
    is_active = db.Column(db.Boolean, default=True, index=True)
    display_order = db.Column(db.Integer, default=0,
                             comment='Order for displaying categories')

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                          onupdate=datetime.utcnow, nullable=False)

    # Relationships
    datasets = db.relationship('Dataset', secondary='dataset_categories',
                              back_populates='categories', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'

    def to_dict(self, include_datasets=False):
        """Convert category to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'icon': self.icon,
            'color': self.color,
            'parent_id': self.parent_id,
            'is_active': self.is_active,
            'display_order': self.display_order,
            'dataset_count': self.datasets.count(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

        if include_datasets:
            data['datasets'] = [dataset.to_dict() for dataset in self.datasets]

        return data

    @classmethod
    def find_by_slug(cls, slug: str):
        """Find category by slug"""
        return cls.query.filter_by(slug=slug).first()

    @classmethod
    def get_active_categories(cls):
        """Get all active categories"""
        return cls.query.filter_by(is_active=True).order_by(cls.display_order).all()

    @classmethod
    def get_top_level_categories(cls):
        """Get categories without parent"""
        return cls.query.filter_by(parent_id=None, is_active=True).order_by(cls.display_order).all()
