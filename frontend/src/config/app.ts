/**
 * Application Configuration
 * 
 * Centralized configuration for app-wide settings
 * that can be customized via environment variables
 */

export const APP_CONFIG = {
  // Application title - customizable via REACT_APP_TITLE environment variable
  title: process.env.REACT_APP_TITLE || 'EDMS',
  
  // Full application name
  fullName: 'Electronic Document Management System',
  
  // Compliance note
  compliance: '21 CFR Part 11 Compliant',
};

export default APP_CONFIG;
