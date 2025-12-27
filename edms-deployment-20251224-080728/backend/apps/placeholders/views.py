"""
Views for Placeholder Management
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import PlaceholderDefinition
from .serializers import (
    PlaceholderDefinitionSerializer, 
    PlaceholderValidationSerializer,
    PlaceholderContentValidationSerializer,
    PlaceholderSuggestionSerializer
)


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
    
    @action(detail=False, methods=['post'])
    def validate(self, request):
        """
        Validate placeholder usage in template content
        
        POST /api/placeholders/validate/
        Body: {"content": "Document {{DOCUMENT_NUMBER}} by {{AUTHOR}}"}
        """
        serializer = PlaceholderContentValidationSerializer(data=request.data)
        
        if serializer.is_valid():
            validation_result = serializer.validated_data
            
            # Add additional validation features
            content = request.data.get('content', '')
            enhanced_result = self._enhance_validation_result(validation_result, content)
            
            return Response(enhanced_result)
        else:
            return Response(
                {'errors': serializer.errors}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _enhance_validation_result(self, validation_result, content):
        """Add enhanced validation features to the basic result"""
        enhanced = validation_result.copy()
        
        # Add placeholder usage statistics
        enhanced['statistics'] = {
            'total_placeholders': len(validation_result['placeholders']),
            'valid_placeholders': len(validation_result['valid_placeholders']),
            'invalid_placeholders': len(validation_result['invalid_placeholders']),
            'unique_placeholders': len(set(p['name'] for p in validation_result['placeholders']))
        }
        
        # Add content analysis
        enhanced['content_analysis'] = {
            'total_characters': len(content),
            'placeholder_density': len(validation_result['placeholders']) / max(len(content.split()), 1),
            'has_version_history': '{{VERSION_HISTORY}}' in content,
            'has_digital_signature': '{{DIGITAL_SIGNATURE}}' in content
        }
        
        # Add recommendations
        recommendations = []
        
        if not any(p['name'] == 'DOCUMENT_NUMBER' for p in validation_result['placeholders']):
            recommendations.append({
                'type': 'suggestion',
                'message': 'Consider adding {{DOCUMENT_NUMBER}} for document identification'
            })
        
        if not any(p['name'] == 'VERSION_HISTORY' for p in validation_result['placeholders']):
            recommendations.append({
                'type': 'suggestion', 
                'message': 'Consider adding {{VERSION_HISTORY}} for professional version tracking'
            })
            
        if not any(p['name'] == 'DIGITAL_SIGNATURE' for p in validation_result['placeholders']):
            recommendations.append({
                'type': 'suggestion',
                'message': 'Consider adding {{DIGITAL_SIGNATURE}} for electronic validation'
            })
        
        if validation_result['invalid_placeholders']:
            recommendations.append({
                'type': 'error',
                'message': f'Fix {len(validation_result["invalid_placeholders"])} invalid placeholders'
            })
        
        enhanced['recommendations'] = recommendations
        
        # Add placeholder categories breakdown
        placeholder_types = {}
        for placeholder in validation_result['valid_placeholders']:
            # Get placeholder definition for category info
            try:
                definition = PlaceholderDefinition.objects.get(name=placeholder['name'])
                p_type = definition.placeholder_type
                if p_type not in placeholder_types:
                    placeholder_types[p_type] = []
                placeholder_types[p_type].append(placeholder['name'])
            except PlaceholderDefinition.DoesNotExist:
                pass
        
        enhanced['placeholder_types'] = placeholder_types
        
        return enhanced
    
    @action(detail=False, methods=['post']) 
    def suggest(self, request):
        """
        Get smart placeholder suggestions based on document type and context
        
        POST /api/placeholders/suggest/
        Body: {"document_type": "SOP", "context": "This is a procedure with approval workflow"}
        """
        serializer = PlaceholderSuggestionSerializer(data=request.data)
        
        if serializer.is_valid():
            suggestions = serializer.validated_data
            return Response(suggestions)
        else:
            return Response(
                {'errors': serializer.errors}, 
                status=status.HTTP_400_BAD_REQUEST
            )