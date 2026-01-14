"""
Association Tables
Many-to-many relationship tables
"""
from app.extensions import db

# Dataset <-> Category (many-to-many)
dataset_categories = db.Table('dataset_categories',
    db.Column('dataset_id', db.Integer, db.ForeignKey('datasets.id', ondelete='CASCADE'),
              primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id', ondelete='CASCADE'),
              primary_key=True),
    db.Column('created_at', db.DateTime, server_default=db.func.now())
)

# Dataset <-> SDG (many-to-many)
dataset_sdgs = db.Table('dataset_sdgs',
    db.Column('dataset_id', db.Integer, db.ForeignKey('datasets.id', ondelete='CASCADE'),
              primary_key=True),
    db.Column('sdg_id', db.Integer, db.ForeignKey('sdgs.id', ondelete='CASCADE'),
              primary_key=True),
    db.Column('confidence_score', db.Float, default=0.0,
              comment='AI classification confidence 0-1'),
    db.Column('created_at', db.DateTime, server_default=db.func.now())
)
