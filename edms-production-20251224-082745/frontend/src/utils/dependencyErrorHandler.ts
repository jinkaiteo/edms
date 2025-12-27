/**
 * Utility for handling and parsing circular dependency errors from the backend
 */

export interface CircularDependencyError {
  non_field_errors?: string[];
  dependency_chain_preview?: Array<{
    document_id: number;
    type: string;
    is_critical: boolean;
  }>;
}

export interface ParsedDependencyError {
  isCircularDependency: boolean;
  message: string;
  fromDocument?: string;
  toDocument?: string;
  chainPreview?: Array<{
    document_id: number;
    type: string;
    is_critical: boolean;
  }>;
  suggestions: string[];
}

/**
 * Parse error response to identify circular dependency errors
 */
export const parseCircularDependencyError = (error: any): ParsedDependencyError => {
  const defaultResult: ParsedDependencyError = {
    isCircularDependency: false,
    message: 'An error occurred',
    suggestions: ['Please try again or contact support']
  };

  // Handle different error response formats
  let errorData = error;
  
  // If it's an axios error, extract the response data
  if (error?.response?.data) {
    errorData = error.response.data;
  }
  
  // If it's a JSON string, parse it
  if (typeof errorData === 'string') {
    try {
      errorData = JSON.parse(errorData);
    } catch {
      return { ...defaultResult, message: errorData };
    }
  }

  // Check for circular dependency indicators
  const circularIndicators = [
    'circular dependency detected',
    'would create a dependency loop',
    'circular dependency',
    'dependency cycle'
  ];

  let isCircularDependency = false;
  let message = '';
  let fromDocument = '';
  let toDocument = '';

  // Check non_field_errors array
  if (errorData?.non_field_errors && Array.isArray(errorData.non_field_errors)) {
    for (const errorMsg of errorData.non_field_errors) {
      if (typeof errorMsg === 'string' && 
          circularIndicators.some(indicator => 
            errorMsg.toLowerCase().includes(indicator)
          )) {
        isCircularDependency = true;
        message = errorMsg;
        
        // Extract document numbers from message if possible
        const docNumberRegex = /from ([A-Z0-9-]+) to ([A-Z0-9-]+)/i;
        const match = errorMsg.match(docNumberRegex);
        if (match) {
          fromDocument = match[1];
          toDocument = match[2];
        }
        break;
      }
    }
  }

  // Check for direct error message
  if (!isCircularDependency && errorData?.error && typeof errorData.error === 'string') {
    const errorMsg = errorData.error.toLowerCase();
    if (circularIndicators.some(indicator => errorMsg.includes(indicator))) {
      isCircularDependency = true;
      message = errorData.error;
    }
  }

  // Check for field-specific errors (e.g., dependency field)
  if (!isCircularDependency && errorData?.dependency) {
    const depError = Array.isArray(errorData.dependency) 
      ? errorData.dependency[0] 
      : errorData.dependency;
    
    if (typeof depError === 'string' && 
        circularIndicators.some(indicator => 
          depError.toLowerCase().includes(indicator)
        )) {
      isCircularDependency = true;
      message = depError;
    }
  }

  if (!isCircularDependency) {
    // Not a circular dependency error, return generic error info
    return {
      ...defaultResult,
      message: errorData?.detail || errorData?.error || 'An error occurred'
    };
  }

  // Generate helpful suggestions for circular dependency errors
  const suggestions = [
    'Remove one of the conflicting dependencies to break the cycle',
    'Consider if both dependency relationships are actually necessary',
    'Use a different dependency type (e.g., "References" instead of "Implements")',
    'Create a parent document that both documents can depend on instead',
    'Review the dependency chain for logical consistency'
  ];

  // Add specific suggestions based on extracted information
  if (fromDocument && toDocument) {
    suggestions.unshift(
      `Check if ${toDocument} really needs to depend on ${fromDocument}`,
      `Consider reversing the dependency relationship if appropriate`
    );
  }

  return {
    isCircularDependency: true,
    message,
    fromDocument,
    toDocument,
    chainPreview: errorData?.dependency_chain_preview,
    suggestions
  };
};

/**
 * Check if an error response contains circular dependency information
 */
export const isCircularDependencyError = (error: any): boolean => {
  const parsed = parseCircularDependencyError(error);
  return parsed.isCircularDependency;
};

/**
 * Get user-friendly message for circular dependency errors
 */
export const getCircularDependencyMessage = (error: any): string => {
  const parsed = parseCircularDependencyError(error);
  
  if (!parsed.isCircularDependency) {
    return parsed.message;
  }

  let message = '🔄 Circular Dependency Detected\n\n';
  message += parsed.message + '\n\n';
  
  if (parsed.fromDocument && parsed.toDocument) {
    message += `This would create a dependency cycle involving ${parsed.fromDocument} and ${parsed.toDocument}.\n\n`;
  }
  
  message += 'Suggestions to resolve:\n';
  parsed.suggestions.forEach((suggestion, index) => {
    message += `${index + 1}. ${suggestion}\n`;
  });

  return message;
};

/**
 * Format error for display in UI components
 */
export const formatDependencyErrorForUI = (error: any) => {
  const parsed = parseCircularDependencyError(error);
  
  return {
    type: parsed.isCircularDependency ? 'circular-dependency' : 'general',
    title: parsed.isCircularDependency ? 'Circular Dependency Detected' : 'Error',
    message: parsed.message,
    details: parsed.isCircularDependency ? {
      fromDocument: parsed.fromDocument,
      toDocument: parsed.toDocument,
      chainPreview: parsed.chainPreview,
      suggestions: parsed.suggestions
    } : null
  };
};