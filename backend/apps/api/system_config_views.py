"""
System Configuration API Views
Handles system-wide settings like logo upload, company branding
"""
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from apps.documents.models import SystemConfiguration
from apps.users.permissions import CanManageSystem
import os


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_system_config(request):
    """
    Get current system configuration including logo URL
    """
    config = SystemConfiguration.get_instance()
    
    return Response({
        'company_name': config.company_name,
        'logo_url': request.build_absolute_uri(config.logo.url) if config.logo else None,
        'has_logo': bool(config.logo),
        'updated_at': config.updated_at,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageSystem])
@parser_classes([MultiPartParser, FormParser])
def upload_logo(request):
    """
    Upload company logo
    
    Accepts: PNG, JPG, JPEG
    Max size: 2MB
    Recommended: 300x100px
    """
    if 'logo' not in request.FILES:
        return Response(
            {'error': 'No logo file provided'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    logo_file = request.FILES['logo']
    
    # Validate file type
    allowed_types = ['image/png', 'image/jpeg', 'image/jpg']
    if logo_file.content_type not in allowed_types:
        return Response(
            {'error': 'Invalid file type. Please upload PNG or JPG file.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate file size (2MB max)
    max_size = 2 * 1024 * 1024  # 2MB
    if logo_file.size > max_size:
        return Response(
            {'error': f'File too large. Maximum size is 2MB. Your file: {logo_file.size / 1024 / 1024:.2f}MB'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get singleton instance
    config = SystemConfiguration.get_instance()
    
    # Delete old logo if exists
    if config.logo:
        try:
            default_storage.delete(config.logo.path)
        except Exception:
            pass
    
    # Save new logo
    config.logo = logo_file
    config.updated_by = request.user
    config.save()
    
    return Response({
        'message': 'Logo uploaded successfully',
        'logo_url': request.build_absolute_uri(config.logo.url),
        'updated_at': config.updated_at,
    }, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, CanManageSystem])
def delete_logo(request):
    """
    Remove company logo
    """
    config = SystemConfiguration.get_instance()
    
    if not config.logo:
        return Response(
            {'error': 'No logo to delete'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Delete logo file
    try:
        default_storage.delete(config.logo.path)
    except Exception:
        pass
    
    config.logo = None
    config.updated_by = request.user
    config.save()
    
    return Response({
        'message': 'Logo deleted successfully'
    }, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAuthenticated, CanManageSystem])
def update_company_name(request):
    """
    Update company name
    """
    company_name = request.data.get('company_name')
    
    if not company_name:
        return Response(
            {'error': 'Company name is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    config = SystemConfiguration.get_instance()
    config.company_name = company_name
    config.updated_by = request.user
    config.save()
    
    return Response({
        'message': 'Company name updated successfully',
        'company_name': config.company_name,
        'updated_at': config.updated_at,
    })
