import React from 'react';

interface SensitivityBadgeProps {
  label: 'PUBLIC' | 'INTERNAL' | 'CONFIDENTIAL' | 'RESTRICTED' | 'PROPRIETARY';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  showTooltip?: boolean;
}

const SENSITIVITY_CONFIG = {
  PUBLIC: {
    label: 'Public',
    icon: '🌐',
    bg: 'bg-green-100',
    text: 'text-green-800',
    border: 'border-green-300',
    ring: 'ring-green-500',
    description: 'Can be shared externally'
  },
  INTERNAL: {
    label: 'Internal Use Only',
    shortLabel: 'Internal',
    icon: '🏢',
    bg: 'bg-blue-100',
    text: 'text-blue-800',
    border: 'border-blue-300',
    ring: 'ring-blue-500',
    description: 'Company employees only'
  },
  CONFIDENTIAL: {
    label: 'Confidential',
    icon: '🔒',
    bg: 'bg-orange-100',
    text: 'text-orange-800',
    border: 'border-orange-300',
    ring: 'ring-orange-500',
    description: 'Need-to-know basis only'
  },
  RESTRICTED: {
    label: 'Restricted',
    icon: '⚠️',
    bg: 'bg-purple-100',
    text: 'text-purple-800',
    border: 'border-purple-300',
    ring: 'ring-purple-500',
    description: 'Regulatory/Compliance - Manager approval required'
  },
  PROPRIETARY: {
    label: 'Proprietary',
    icon: '🛡️',
    bg: 'bg-red-100',
    text: 'text-red-800',
    border: 'border-red-300',
    ring: 'ring-red-500',
    description: 'Trade secret - Executive approval required'
  }
};

const SIZE_CLASSES = {
  xs: 'px-1.5 py-0.5 text-xs',
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-3 py-1 text-sm',
  lg: 'px-4 py-2 text-base'
};

const ICON_SIZE_CLASSES = {
  xs: 'text-xs',
  sm: 'text-sm',
  md: 'text-base',
  lg: 'text-lg'
};

const SensitivityBadge: React.FC<SensitivityBadgeProps> = ({ 
  label, 
  size = 'md',
  showIcon = true,
  showTooltip = true
}) => {
  const config = SENSITIVITY_CONFIG[label];
  
  if (!config) {
    console.warn(`Unknown sensitivity label: ${label}`);
    return <span className="text-gray-500 text-sm">Unknown</span>;
  }

  const displayLabel = size === 'xs' && config.shortLabel ? config.shortLabel : config.label;

  return (
    <span 
      className={`
        inline-flex items-center gap-1 rounded-full border font-medium
        ${config.bg} ${config.text} ${config.border} ${SIZE_CLASSES[size]}
        transition-all duration-200 hover:ring-2 ${config.ring}
      `}
      title={showTooltip ? `${config.label}: ${config.description}` : undefined}
    >
      {showIcon && (
        <span className={ICON_SIZE_CLASSES[size]} aria-label="sensitivity icon">
          {config.icon}
        </span>
      )}
      <span>{displayLabel}</span>
    </span>
  );
};

export default SensitivityBadge;
