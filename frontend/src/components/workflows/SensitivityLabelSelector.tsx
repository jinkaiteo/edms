import React, { useState } from 'react';
import SensitivityBadge from '../common/SensitivityBadge';

interface SensitivityOption {
  value: string;
  label: string;
  icon: string;
  description: string;
  detailedDescription: string;
  riskLevel: string;
  examples: string[];
}

const SENSITIVITY_OPTIONS: SensitivityOption[] = [
  {
    value: 'PUBLIC',
    label: 'Public',
    icon: '🌐',
    description: 'Can be shared externally - already public information',
    detailedDescription: 'Information that is already publicly available or intended for public consumption. No confidentiality restrictions apply.',
    riskLevel: 'None',
    examples: [
      'Published quality certificates',
      'Marketing materials',
      'Press releases',
      'Product catalogs (non-sensitive)'
    ]
  },
  {
    value: 'INTERNAL',
    label: 'Internal Use Only',
    icon: '🏢',
    description: 'Company employees only - should not leave premises',
    detailedDescription: 'Information intended for use within the company by all employees. Should not be shared with external parties without proper authorization.',
    riskLevel: 'Low',
    examples: [
      'Standard Operating Procedures (SOPs)',
      'Quality Manual',
      'Work Instructions',
      'Training materials',
      'Internal policies'
    ]
  },
  {
    value: 'CONFIDENTIAL',
    label: 'Confidential',
    icon: '🔒',
    description: 'Restricted access - need-to-know basis, NDA required for external viewing',
    detailedDescription: 'Sensitive business information that could cause competitive disadvantage or legal liability if disclosed. Access limited to those with legitimate business need.',
    riskLevel: 'Medium-High',
    examples: [
      'Internal audit reports',
      'Customer contracts',
      'Test results',
      'Validation reports',
      'Financial data'
    ]
  },
  {
    value: 'RESTRICTED',
    label: 'Restricted - Regulatory/Compliance',
    icon: '⚠️',
    description: 'Regulatory/compliance documents - strict access control and audit trail',
    detailedDescription: 'Documents subject to regulatory oversight or with significant compliance implications. Unauthorized access or disclosure could result in regulatory action or legal penalties.',
    riskLevel: 'High',
    examples: [
      'FDA/EMA submissions',
      'Regulatory inspection responses',
      'Agency meeting minutes',
      'Clinical trial data',
      'Compliance investigations'
    ]
  },
  {
    value: 'PROPRIETARY',
    label: 'Proprietary / Trade Secret',
    icon: '🛡️',
    description: 'Trade secrets and critical IP - highest protection level',
    detailedDescription: 'Information representing critical competitive advantage, trade secrets, or core intellectual property. Unauthorized disclosure could threaten business viability.',
    riskLevel: 'Critical',
    examples: [
      'Manufacturing processes (unique methods)',
      'Proprietary formulations',
      'Patent applications (pre-filing)',
      'Strategic business plans',
      'Trade secret documentation'
    ]
  }
];

interface SensitivityLabelSelectorProps {
  value: string;
  onChange: (value: string, reason: string) => void;
  inheritedFrom?: string | null;
  originalValue?: string;
  required?: boolean;
  disabled?: boolean;
  showGuide?: boolean;
}

const SensitivityLabelSelector: React.FC<SensitivityLabelSelectorProps> = ({
  value,
  onChange,
  inheritedFrom,
  originalValue,
  required = true,
  disabled = false,
  showGuide = true
}) => {
  const [changeReason, setChangeReason] = useState('');
  const [showDetails, setShowDetails] = useState(false);
  const [selectedForPreview, setSelectedForPreview] = useState<string | null>(null);

  const selectedOption = SENSITIVITY_OPTIONS.find(opt => opt.value === value);
  const hasChanged = originalValue && originalValue !== value;

  const handleSensitivityChange = (newValue: string) => {
    onChange(newValue, changeReason);
  };

  const handleReasonChange = (reason: string) => {
    setChangeReason(reason);
    onChange(value, reason);
  };

  const previewOption = selectedForPreview 
    ? SENSITIVITY_OPTIONS.find(opt => opt.value === selectedForPreview)
    : selectedOption;

  return (
    <div className="space-y-4">
      {/* Inheritance Notice */}
      {inheritedFrom && !hasChanged && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <span className="text-blue-600 text-xl">ℹ️</span>
            <div className="flex-1">
              <p className="text-sm font-medium text-blue-900">
                Inherited Sensitivity Classification
              </p>
              <p className="text-sm text-blue-700 mt-1">
                This version has inherited the <strong>{selectedOption?.label}</strong> classification 
                from {inheritedFrom}. You can confirm or change this classification below.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Sensitivity Label Selector */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Sensitivity Classification {required && <span className="text-red-500">*</span>}
        </label>
        
        <div className="grid grid-cols-1 gap-2">
          {SENSITIVITY_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              disabled={disabled}
              onClick={() => handleSensitivityChange(option.value)}
              onMouseEnter={() => setSelectedForPreview(option.value)}
              onMouseLeave={() => setSelectedForPreview(null)}
              className={`
                relative flex items-start gap-3 p-4 rounded-lg border-2 text-left
                transition-all duration-200
                ${value === option.value
                  ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-500 ring-opacity-50'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              {/* Radio Circle */}
              <div className="flex items-center pt-1">
                <div className={`
                  w-5 h-5 rounded-full border-2 flex items-center justify-center
                  ${value === option.value 
                    ? 'border-blue-500 bg-blue-500' 
                    : 'border-gray-300 bg-white'
                  }
                `}>
                  {value === option.value && (
                    <div className="w-2 h-2 rounded-full bg-white"></div>
                  )}
                </div>
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-lg">{option.icon}</span>
                  <span className="font-medium text-gray-900">{option.label}</span>
                  <span className="text-xs text-gray-500 ml-auto">
                    Risk: {option.riskLevel}
                  </span>
                </div>
                
                <p className="text-sm text-gray-600 mb-2">
                  {option.description}
                </p>

                {/* Examples (show when selected or hovered) */}
                {(value === option.value || selectedForPreview === option.value) && (
                  <div className="text-xs text-gray-500 mt-2 space-y-1">
                    <p className="font-medium">Examples:</p>
                    <ul className="list-disc list-inside space-y-0.5 ml-2">
                      {option.examples.slice(0, 3).map((example, idx) => (
                        <li key={idx}>{example}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </button>
          ))}
        </div>

        {/* Guide Link */}
        {showGuide && (
          <div className="flex items-center gap-2 mt-2">
            <button
              type="button"
              onClick={() => setShowDetails(!showDetails)}
              className="text-sm text-blue-600 hover:text-blue-800 underline"
            >
              {showDetails ? '▼' : '▶'} Need help choosing? View classification guide
            </button>
          </div>
        )}
      </div>

      {/* Detailed Guide (Expandable) */}
      {showDetails && previewOption && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-3">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{previewOption.icon}</span>
            <h4 className="font-semibold text-gray-900">{previewOption.label}</h4>
          </div>
          
          <div className="space-y-2 text-sm">
            <div>
              <p className="font-medium text-gray-700">Description:</p>
              <p className="text-gray-600">{previewOption.detailedDescription}</p>
            </div>
            
            <div>
              <p className="font-medium text-gray-700">Risk Level:</p>
              <p className="text-gray-600">{previewOption.riskLevel}</p>
            </div>
            
            <div>
              <p className="font-medium text-gray-700">Common Examples:</p>
              <ul className="list-disc list-inside space-y-1 text-gray-600 ml-2">
                {previewOption.examples.map((example, idx) => (
                  <li key={idx}>{example}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Change Warning */}
      {hasChanged && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <span className="text-yellow-600 text-xl">⚠️</span>
            <div className="flex-1">
              <p className="text-sm font-medium text-yellow-900">
                Sensitivity Classification Change Detected
              </p>
              <p className="text-sm text-yellow-700 mt-1">
                Changing from <strong>{SENSITIVITY_OPTIONS.find(o => o.value === originalValue)?.label}</strong> to{' '}
                <strong>{selectedOption?.label}</strong>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Change Reason (Required if changed) */}
      {hasChanged && (
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            Reason for Classification Change <span className="text-red-500">*</span>
          </label>
          <textarea
            value={changeReason}
            onChange={(e) => handleReasonChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            rows={3}
            placeholder="Explain why the sensitivity classification is being changed... (minimum 20 characters)"
            required
            disabled={disabled}
          />
          <p className="text-xs text-gray-500">
            Required for audit compliance and change control. Minimum 20 characters.
          </p>
          {changeReason.length > 0 && changeReason.length < 20 && (
            <p className="text-xs text-red-600">
              Reason too short: {changeReason.length}/20 characters
            </p>
          )}
        </div>
      )}

      {/* Quick Reference */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <p className="text-xs text-blue-900 font-medium mb-2">💡 Quick Reference:</p>
        <ul className="text-xs text-blue-800 space-y-1">
          <li>• <strong>Default:</strong> INTERNAL (most common for SOPs, policies)</li>
          <li>• <strong>Regulatory docs:</strong> Use RESTRICTED (FDA submissions, audits)</li>
          <li>• <strong>Trade secrets:</strong> Use PROPRIETARY (formulations, processes)</li>
          <li>• <strong>When unsure:</strong> Choose INTERNAL (safer default)</li>
        </ul>
      </div>
    </div>
  );
};

export default SensitivityLabelSelector;
