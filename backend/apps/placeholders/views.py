"""
Views for Placeholder Management
"""

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import PlaceholderDefinition
from .serializers import PlaceholderDefinitionSerializer


class PlaceholderDefinitionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing placeholder definitions.
    Provides read-only access to placeholder configurations.
    """
    
    queryset = PlaceholderDefinition.objects.filter(is_active=True).order_by('name')
    serializer_class = PlaceholderDefinitionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter placeholders based on user permissions"""
        queryset = super().get_queryset()
        
        # Add any permission-based filtering here if needed
        # For now, all authenticated users can view placeholders
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get placeholder categories"""
        categories = self.get_queryset().values_list('placeholder_type', flat=True).distinct()
        return Response({'categories': list(categories)})
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get placeholders grouped by type"""
        placeholders_by_type = {}
        
        for placeholder in self.get_queryset():
            p_type = placeholder.placeholder_type
            if p_type not in placeholders_by_type:
                placeholders_by_type[p_type] = []
            
            placeholders_by_type[p_type].append({
                'name': placeholder.name,
                'display_name': placeholder.display_name,
                'description': placeholder.description,
                'data_source': placeholder.data_source,
                'source_field': placeholder.source_field,
                'default_value': placeholder.default_value
            })
        
        return Response(placeholders_by_type)