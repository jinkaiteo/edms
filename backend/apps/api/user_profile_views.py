"""
User Profile API Views
Allows users to view and update their own profile information
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile data
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'department',
            'position',
            'employee_id',
            'phone_number',
        ]
        read_only_fields = ['id', 'username', 'email', 'full_name']
    
    def get_full_name(self, obj):
        """Get user's full name"""
        return obj.get_full_name() or obj.username


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    """
    Get current user's profile information
    """
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    """
    Update current user's profile information
    
    Editable fields:
    - department
    - position
    - first_name
    - last_name
    - phone_number
    """
    user = request.user
    
    # Only allow updating specific fields
    allowed_fields = ['department', 'position', 'first_name', 'last_name', 'phone_number']
    
    # Update only allowed fields
    updated_fields = []
    for field in allowed_fields:
        if field in request.data:
            setattr(user, field, request.data[field])
            updated_fields.append(field)
    
    # Validate
    try:
        user.full_clean()
        user.save()
    except Exception as e:
        return Response(
            {'error': f'Validation failed: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Return updated profile
    serializer = UserProfileSerializer(user)
    
    return Response({
        'message': 'Profile updated successfully',
        'updated_fields': updated_fields,
        'profile': serializer.data
    })
