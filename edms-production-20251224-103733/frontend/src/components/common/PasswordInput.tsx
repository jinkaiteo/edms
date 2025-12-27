import React, { useState } from 'react';

interface PasswordInputProps {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  placeholder?: string;
  required?: boolean;
  minLength?: number;
  className?: string;
  disabled?: boolean;
  id?: string;
  name?: string;
}

const PasswordInput: React.FC<PasswordInputProps> = ({
  value,
  onChange,
  placeholder = "Enter password...",
  required = false,
  minLength,
  className = "",
  disabled = false,
  id,
  name,
}) => {
  const [showPassword, setShowPassword] = useState(false);

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const baseClasses = "mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500";
  const finalClasses = className || baseClasses;

  return (
    <div className="relative">
      <input
        id={id}
        name={name}
        type={showPassword ? "text" : "password"}
        required={required}
        minLength={minLength}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className={`${finalClasses} pr-10`}
        disabled={disabled}
      />
      <button
        type="button"
        className="absolute inset-y-0 right-0 pr-3 flex items-center"
        onClick={togglePasswordVisibility}
        disabled={disabled}
        tabIndex={-1}
      >
        {showPassword ? (
          <svg 
            className="h-5 w-5 text-gray-400 hover:text-gray-600" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
            aria-label="Hide password"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L12 12m6.878-6.878L21 3m-3.122 6.878a3 3 0 11-4.243 4.243m4.243-4.243L19 9.5" 
            />
          </svg>
        ) : (
          <svg 
            className="h-5 w-5 text-gray-400 hover:text-gray-600" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
            aria-label="Show password"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" 
            />
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" 
            />
          </svg>
        )}
      </button>
    </div>
  );
};

export default PasswordInput;