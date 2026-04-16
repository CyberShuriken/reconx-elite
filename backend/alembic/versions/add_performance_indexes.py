"""Add performance indexes and constraints - Migration"""
from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    """Add database indexes for performance."""
    
    # User table indexes
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_created_at', 'users', ['created_at'])
    
    # Target table indexes
    op.create_index('idx_targets_user_id', 'targets', ['user_id'])
    op.create_index('idx_targets_created_at', 'targets', ['created_at'])
    op.create_index('idx_targets_name', 'targets', ['name'])
    
    # Scan table indexes
    op.create_index('idx_scans_target_id', 'scans', ['target_id'])
    op.create_index('idx_scans_user_id', 'scans', ['user_id'])
    op.create_index('idx_scans_status', 'scans', ['status'])
    op.create_index('idx_scans_created_at', 'scans', ['created_at'])
    
    # Vulnerability table indexes
    op.create_index('idx_vulnerabilities_scan_id', 'vulnerabilities', ['scan_id'])
    op.create_index('idx_vulnerabilities_severity', 'vulnerabilities', ['severity'])
    op.create_index('idx_vulnerabilities_created_at', 'vulnerabilities', ['created_at'])
    
    # Composite indexes for common queries
    op.create_index(
        'idx_scans_user_status_created',
        'scans',
        ['user_id', 'status', 'created_at']
    )
    
    op.create_index(
        'idx_vulnerabilities_scan_severity',
        'vulnerabilities',
        ['scan_id', 'severity']
    )


def downgrade() -> None:
    """Remove database indexes."""
    
    # Drop composite indexes
    op.drop_index('idx_vulnerabilities_scan_severity')
    op.drop_index('idx_scans_user_status_created')
    
    # Drop vulnerability indexes
    op.drop_index('idx_vulnerabilities_created_at')
    op.drop_index('idx_vulnerabilities_severity')
    op.drop_index('idx_vulnerabilities_scan_id')
    
    # Drop scan indexes
    op.drop_index('idx_scans_created_at')
    op.drop_index('idx_scans_status')
    op.drop_index('idx_scans_user_id')
    op.drop_index('idx_scans_target_id')
    
    # Drop target indexes
    op.drop_index('idx_targets_name')
    op.drop_index('idx_targets_created_at')
    op.drop_index('idx_targets_user_id')
    
    # Drop user indexes
    op.drop_index('idx_users_created_at')
    op.drop_index('idx_users_email')
