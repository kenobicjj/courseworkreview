from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

class Criteria(db.Model):
    """Assessment criteria model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    text = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'text': self.text,
            'file_path': self.file_path,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Submission(db.Model):
    """Submission model for storing student submissions"""
    id = db.Column(db.Integer, primary_key=True)
    folder_name = db.Column(db.String(255), nullable=False)
    notebook_file = db.Column(db.String(255), nullable=True)  # Main notebook file
    file_path = db.Column(db.String(512), nullable=True)  # Path to extracted folder
    notebook_content = db.Column(db.JSON, nullable=True)  # Store notebook content as JSON
    feedback = db.Column(db.Text, nullable=True)
    analyzed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    files = db.relationship('SubmissionFile', backref='submission', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'folder_name': self.folder_name,
            'notebook_file': self.notebook_file,
            'file_path': self.file_path,
            'files': [file.filename for file in self.files],
            'feedback': self.feedback,
            'analyzed': self.analyzed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class SubmissionFile(db.Model):
    """Individual files within a submission"""
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submission.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)  # Full path to file
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'submission_id': self.submission_id,
            'filename': self.filename,
            'file_path': self.file_path,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AnalysisSettings(db.Model):
    """Configuration for analysis prompts"""
    id = db.Column(db.Integer, primary_key=True)
    preamble = db.Column(db.Text, nullable=True)  # Text to add before the prompt
    postamble = db.Column(db.Text, nullable=True)  # Text to add after the prompt
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'preamble': self.preamble,
            'postamble': self.postamble,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }