# Sensitivity Label Configuration for EDMS - UPDATED FOR ACTUAL ROLE SYSTEM
# 5-Tier Classification System for Pharmaceutical/Medical Device QMS

SENSITIVITY_CHOICES = [
    ('PUBLIC', 'Public'),
    ('INTERNAL', 'Internal Use Only'),
    ('CONFIDENTIAL', 'Confidential'),
    ('RESTRICTED', 'Restricted - Regulatory/Compliance'),
    ('PROPRIETARY', 'Proprietary / Trade Secret'),
]

# Comprehensive metadata for each sensitivity level
# UPDATED: Uses actual permission_level hierarchy (read, write, review, approve, admin)
SENSITIVITY_METADATA = {
    'PUBLIC': {
        'display': 'Public',
        'short_display': 'Public',
        'description': 'Can be shared externally - already public information',
        'detailed_description': (
            'Information that is already publicly available or intended for public consumption. '
            'No confidentiality restrictions apply.'
        ),
        'color': 'green',
        'icon': '🌐',
        'watermark_color': (0, 150, 0),
        'watermark_text': 'PUBLIC',
        'risk_level': 'None',
        'access_level': 'Anyone',
        'handling_requirements': [
            'No restrictions on sharing or distribution',
            'Can be posted on public websites',
            'No encryption required',
        ],
        'examples': [
            'Published quality certificates',
            'Marketing materials and brochures',
            'Public-facing quality policy statements',
            'Product catalogs (non-sensitive)',
            'Job postings',
            'Press releases',
        ],
        'access_control': {
            'requires_login': False,
            'requires_specific_permission': False,
            'minimum_permission_levels': [],  # No permission required
            'log_downloads': False,
            'log_views': False,
            'allow_printing': True,
            'allow_external_sharing': True,
        }
    },
    'INTERNAL': {
        'display': 'Internal Use Only',
        'short_display': 'Internal',
        'description': 'Company employees only - should not leave premises',
        'detailed_description': (
            'Information intended for use within the company by all employees. '
            'Should not be shared with external parties without proper authorization.'
        ),
        'color': 'blue',
        'icon': '🏢',
        'watermark_color': (0, 100, 200),
        'watermark_text': 'INTERNAL USE ONLY',
        'risk_level': 'Low',
        'access_level': 'All employees',
        'handling_requirements': [
            'Should not leave company premises',
            'No external sharing without approval',
            'Basic access logging',
            'Encrypted storage recommended',
        ],
        'examples': [
            'Standard Operating Procedures (SOPs)',
            'Quality Manual',
            'Work Instructions',
            'Training materials',
            'Internal policies and procedures',
            'Forms and templates',
            'Meeting minutes',
            'Equipment maintenance logs',
        ],
        'access_control': {
            'requires_login': True,
            'requires_specific_permission': False,  # Any authenticated user
            'minimum_permission_levels': ['read', 'write', 'review', 'approve', 'admin'],
            'log_downloads': True,
            'log_views': False,
            'allow_printing': True,
            'allow_external_sharing': False,
        }
    },
    'CONFIDENTIAL': {
        'display': 'Confidential',
        'short_display': 'Confidential',
        'description': 'Restricted access - need-to-know basis, NDA required for external viewing',
        'detailed_description': (
            'Sensitive business information that could cause competitive disadvantage or '
            'legal liability if disclosed. Access limited to those with legitimate business need.'
        ),
        'color': 'orange',
        'icon': '🔒',
        'watermark_color': (255, 140, 0),
        'watermark_text': 'CONFIDENTIAL',
        'risk_level': 'Medium-High',
        'access_level': 'Need-to-know only',
        'handling_requirements': [
            'Encrypted storage required',
            'Access logging and monitoring',
            'NDAs required for external viewing',
            'Watermarked when printed',
            'No unauthorized copying',
            'Regular access reviews',
        ],
        'examples': [
            'Internal audit reports',
            'Customer contracts and agreements',
            'Supplier agreements',
            'Test results (pre-publication)',
            'Validation protocols and reports',
            'Product specifications (detailed)',
            'CAPA investigations',
            'Deviation reports',
            'Financial data',
            'Employee personnel records',
        ],
        'access_control': {
            'requires_login': True,
            'requires_specific_permission': True,
            'minimum_permission_levels': ['review', 'approve', 'admin'],  # Review+ required
            'log_downloads': True,
            'log_views': True,
            'allow_printing': True,  # But watermarked
            'allow_external_sharing': False,
            'requires_justification': True,
        }
    },
    'RESTRICTED': {
        'display': 'Restricted - Regulatory/Compliance',
        'short_display': 'Restricted',
        'description': 'Regulatory/compliance documents - strict access control and audit trail',
        'detailed_description': (
            'Documents subject to regulatory oversight or with significant compliance implications. '
            'Unauthorized access or disclosure could result in regulatory action, legal penalties, '
            'or damage to regulatory standing. Requires approver-level permissions.'
        ),
        'color': 'purple',
        'icon': '⚠️',
        'watermark_color': (128, 0, 128),
        'watermark_text': 'RESTRICTED - REGULATORY/COMPLIANCE',
        'risk_level': 'High',
        'access_level': 'Approver-level only',
        'handling_requirements': [
            'Highest encryption standards',
            'Complete access audit trail',
            'Regulatory compliance tracking',
            'Time-limited access grants',
            'Approver authorization for access',
            'No printing without authorization',
            'Secure disposal procedures',
            'Access reviews every 90 days',
        ],
        'examples': [
            'FDA/EMA submissions and correspondence',
            'Regulatory inspection responses',
            'Agency meeting minutes',
            'Clinical trial data',
            'Regulatory audit findings',
            'Compliance investigation reports',
            'Warning letter responses',
            'Pre-market approval documents',
            'Post-market surveillance reports',
        ],
        'access_control': {
            'requires_login': True,
            'requires_specific_permission': True,
            'minimum_permission_levels': ['approve', 'admin'],  # Approver+ required
            'log_downloads': True,
            'log_views': True,
            'allow_printing': False,  # Requires approval
            'allow_external_sharing': False,
            'requires_justification': True,
            'requires_manager_approval': True,
            'alert_on_access': True,
            'time_limited_access': True,
        }
    },
    'PROPRIETARY': {
        'display': 'Proprietary / Trade Secret',
        'short_display': 'Proprietary',
        'description': 'Trade secrets and critical IP - highest protection level',
        'detailed_description': (
            'Information representing critical competitive advantage, trade secrets, or core '
            'intellectual property. Unauthorized disclosure could threaten business viability. '
            'Admin-level permissions required.'
        ),
        'color': 'red',
        'icon': '🛡️',
        'watermark_color': (200, 0, 0),
        'watermark_text': 'PROPRIETARY - TRADE SECRET',
        'risk_level': 'Critical',
        'access_level': 'Admin only',
        'handling_requirements': [
            'Maximum encryption (AES-256)',
            'Complete audit trail with video logging',
            'Admin approval for all access',
            'No printing allowed',
            'Watermarked on every page if printed',
            'Screen recording blocked',
            'Physical security for any printouts',
            'Clean desk policy enforced',
            'Access reviews monthly',
            'Immediate revocation on role change',
        ],
        'examples': [
            'Manufacturing processes (unique/secret methods)',
            'Proprietary formulations',
            'Proprietary designs and innovations',
            'Patent applications (pre-filing)',
            'Strategic business plans',
            'M&A documents and negotiations',
            'Source code and algorithms',
            'Competitive intelligence',
            'Trade secret documentation',
            'Breakthrough research data',
        ],
        'access_control': {
            'requires_login': True,
            'requires_specific_permission': True,
            'minimum_permission_levels': ['admin'],  # Admin only
            'log_downloads': True,
            'log_views': True,
            'allow_printing': False,
            'allow_external_sharing': False,
            'requires_justification': True,
            'requires_executive_approval': True,
            'alert_on_access': True,
            'time_limited_access': True,
            'requires_signed_acknowledgment': True,
            'background_check_required': True,
        }
    },
}

# Risk level ordering (for comparison operations)
SENSITIVITY_RISK_ORDER = [
    'PUBLIC',      # 0 - No risk
    'INTERNAL',    # 1 - Low risk
    'CONFIDENTIAL', # 2 - Medium-High risk
    'RESTRICTED',  # 3 - High risk
    'PROPRIETARY', # 4 - Critical risk
]

# Helper functions
def get_sensitivity_level(label: str) -> int:
    """Get numeric risk level for sensitivity label (0-4)."""
    try:
        return SENSITIVITY_RISK_ORDER.index(label)
    except ValueError:
        return 1  # Default to INTERNAL level

def is_higher_sensitivity(label1: str, label2: str) -> bool:
    """Check if label1 is more sensitive than label2."""
    return get_sensitivity_level(label1) > get_sensitivity_level(label2)

def get_sensitivity_display(label: str) -> str:
    """Get display name for sensitivity label."""
    return SENSITIVITY_METADATA.get(label, {}).get('display', label)

def get_sensitivity_icon(label: str) -> str:
    """Get icon for sensitivity label."""
    return SENSITIVITY_METADATA.get(label, {}).get('icon', '📄')

def get_handling_requirements(label: str) -> list:
    """Get handling requirements for sensitivity label."""
    return SENSITIVITY_METADATA.get(label, {}).get('handling_requirements', [])

def get_access_control_config(label: str) -> dict:
    """Get access control configuration for sensitivity label."""
    return SENSITIVITY_METADATA.get(label, {}).get('access_control', {})

def requires_specific_permission(label: str) -> bool:
    """Check if sensitivity level requires specific permission level."""
    config = get_access_control_config(label)
    return config.get('requires_specific_permission', False)

def get_minimum_permission_levels(label: str) -> list:
    """Get list of permission levels that can access this sensitivity level."""
    config = get_access_control_config(label)
    return config.get('minimum_permission_levels', [])
