/**
 * Test Data Configuration for EDMS Tests
 * Centralized test data and configuration
 */

// Base configuration
const config = {
  baseURL: 'http://localhost:3000',
  loginURL: 'http://localhost:3000/login',
  backendURL: 'http://localhost:8000',
  timeout: 30000,
  adminCredentials: { username: 'admin', password: 'test123' },
  testDocumentPath: 'test_doc/Tikva Quality Policy_template.docx'
};

// Enhanced test users with more realistic data
const testUsers = [
  // Authors
  { 
    username: 'author01', 
    email: 'john.author@edms.test', 
    firstName: 'John', 
    lastName: 'Author', 
    department: 'Engineering',
    position: 'Technical Writer',
    role: 'author', 
    groups: ['Document Authors'],
    password: 'test123'
  },
  { 
    username: 'author02', 
    email: 'sarah.writer@edms.test', 
    firstName: 'Sarah', 
    lastName: 'Writer', 
    department: 'Quality Assurance',
    position: 'QA Specialist',
    role: 'author', 
    groups: ['Document Authors'],
    password: 'test123'
  },
  
  // Reviewers
  { 
    username: 'reviewer01', 
    email: 'mike.reviewer@edms.test', 
    firstName: 'Mike', 
    lastName: 'Reviewer', 
    department: 'Quality Assurance',
    position: 'Senior QA Lead',
    role: 'reviewer', 
    groups: ['Document Reviewers'],
    password: 'test123'
  },
  { 
    username: 'reviewer02', 
    email: 'lisa.checker@edms.test', 
    firstName: 'Lisa', 
    lastName: 'Checker', 
    department: 'Compliance',
    position: 'Compliance Officer',
    role: 'reviewer', 
    groups: ['Document Reviewers'],
    password: 'test123'
  },
  
  // Approvers
  { 
    username: 'approver01', 
    email: 'david.approver@edms.test', 
    firstName: 'David', 
    lastName: 'Approver', 
    department: 'Management',
    position: 'Department Manager',
    role: 'approver', 
    groups: ['Document Approvers'],
    password: 'test123'
  },
  { 
    username: 'approver02', 
    email: 'karen.manager@edms.test', 
    firstName: 'Karen', 
    lastName: 'Manager', 
    department: 'Operations',
    position: 'Operations Manager',
    role: 'approver', 
    groups: ['Document Approvers'],
    password: 'test123'
  },
  
  // Senior Approvers
  { 
    username: 'senior01', 
    email: 'robert.director@edms.test', 
    firstName: 'Robert', 
    lastName: 'Director', 
    department: 'Executive',
    position: 'VP Operations',
    role: 'senior_approver', 
    groups: ['Senior Document Approvers'],
    password: 'test123'
  },
  { 
    username: 'senior02', 
    email: 'patricia.executive@edms.test', 
    firstName: 'Patricia', 
    lastName: 'Executive', 
    department: 'Executive',
    position: 'Chief Quality Officer',
    role: 'senior_approver', 
    groups: ['Senior Document Approvers'],
    password: 'test123'
  },
  
  // Viewers
  { 
    username: 'viewer01', 
    email: 'alice.viewer@edms.test', 
    firstName: 'Alice', 
    lastName: 'Viewer', 
    department: 'Training',
    position: 'Training Coordinator',
    role: 'viewer', 
    groups: [],
    password: 'test123'
  },
  { 
    username: 'viewer02', 
    email: 'bob.reader@edms.test', 
    firstName: 'Bob', 
    lastName: 'Reader', 
    department: 'Production',
    position: 'Production Operator',
    role: 'viewer', 
    groups: [],
    password: 'test123'
  }
];

// Enhanced test documents with more variety
const testDocuments = [
  {
    title: 'Quality Management System Policy V2.0',
    description: 'Comprehensive quality management policy outlining organizational commitment to quality excellence and continuous improvement.',
    documentType: 'POL',
    department: 'Quality Assurance',
    author: 'author01',
    category: 'Policy',
    tags: ['quality', 'management', 'policy']
  },
  {
    title: 'Workplace Safety Procedures V1.5', 
    description: 'Updated workplace safety procedures including emergency protocols, equipment handling, and incident reporting procedures.',
    documentType: 'PROC',
    department: 'Safety',
    author: 'author02',
    category: 'Procedure',
    tags: ['safety', 'emergency', 'procedures']
  },
  {
    title: 'Employee Training and Development Manual V3.0',
    description: 'Comprehensive training manual covering onboarding, skills development, and performance evaluation processes.',
    documentType: 'MAN',
    department: 'Human Resources', 
    author: 'author01',
    category: 'Manual',
    tags: ['training', 'development', 'hr']
  },
  {
    title: 'Internal Audit Checklist and Guidelines V2.1',
    description: 'Detailed audit checklist and guidelines for conducting internal quality audits and compliance assessments.',
    documentType: 'FORM',
    department: 'Quality Assurance',
    author: 'author02',
    category: 'Form',
    tags: ['audit', 'compliance', 'checklist']
  },
  {
    title: 'Document Control Procedures V1.0',
    description: 'Procedures for document creation, review, approval, distribution, and revision control within the EDMS.',
    documentType: 'PROC',
    department: 'Quality Assurance',
    author: 'author01',
    category: 'Procedure',
    tags: ['document', 'control', 'edms']
  }
];

// Comprehensive workflow test scenarios
const workflowScenarios = [
  {
    name: 'Standard Review and Approval Process',
    description: 'Complete workflow from creation to effective status',
    document: 'Quality Management System Policy V2.0',
    expectedDuration: '5-10 minutes',
    steps: [
      { action: 'create_document', actor: 'author01', expectedResult: 'DRAFT' },
      { action: 'submit_for_review', actor: 'author01', reviewer: 'reviewer01', expectedResult: 'PENDING_REVIEW' },
      { action: 'approve_review', actor: 'reviewer01', comment: 'Policy content reviewed and approved for accuracy', expectedResult: 'REVIEWED' },
      { action: 'route_for_approval', actor: 'author01', approver: 'approver01', expectedResult: 'PENDING_APPROVAL' },
      { action: 'approve_document', actor: 'approver01', comment: 'Policy approved for publication and implementation', expectedResult: 'APPROVED' },
      { action: 'set_effective_date', actor: 'author01', effectiveDate: '2025-02-01', expectedResult: 'EFFECTIVE' }
    ]
  },
  {
    name: 'Review Rejection and Resubmission Cycle',
    description: 'Handling review rejections and resubmissions',
    document: 'Workplace Safety Procedures V1.5',
    expectedDuration: '8-12 minutes',
    steps: [
      { action: 'create_document', actor: 'author02', expectedResult: 'DRAFT' },
      { action: 'submit_for_review', actor: 'author02', reviewer: 'reviewer02', expectedResult: 'PENDING_REVIEW' },
      { action: 'reject_review', actor: 'reviewer02', comment: 'Requires additional emergency evacuation procedures', expectedResult: 'REJECTED' },
      { action: 'revise_document', actor: 'author02', comment: 'Added comprehensive emergency evacuation procedures', expectedResult: 'DRAFT' },
      { action: 'submit_for_review', actor: 'author02', reviewer: 'reviewer01', expectedResult: 'PENDING_REVIEW' },
      { action: 'approve_review', actor: 'reviewer01', comment: 'Enhanced safety procedures look comprehensive', expectedResult: 'REVIEWED' },
      { action: 'route_for_approval', actor: 'author02', approver: 'approver02', expectedResult: 'PENDING_APPROVAL' },
      { action: 'approve_document', actor: 'approver02', comment: 'Approved with recommendation for quarterly review', expectedResult: 'APPROVED' }
    ]
  },
  {
    name: 'Senior Approval Escalation Process',
    description: 'High-impact documents requiring senior approval',
    document: 'Employee Training and Development Manual V3.0',
    expectedDuration: '10-15 minutes',
    steps: [
      { action: 'create_document', actor: 'author01', expectedResult: 'DRAFT' },
      { action: 'submit_for_review', actor: 'author01', reviewer: 'reviewer01', expectedResult: 'PENDING_REVIEW' },
      { action: 'approve_review', actor: 'reviewer01', comment: 'Technical content and procedures verified', expectedResult: 'REVIEWED' },
      { action: 'route_for_approval', actor: 'author01', approver: 'senior01', expectedResult: 'PENDING_SENIOR_APPROVAL' },
      { action: 'approve_document', actor: 'senior01', comment: 'Strategic alignment confirmed, organizational impact assessed', expectedResult: 'APPROVED' },
      { action: 'set_effective_date', actor: 'author01', effectiveDate: '2025-03-01', expectedResult: 'EFFECTIVE' }
    ]
  },
  {
    name: 'Approval Rejection and Executive Escalation',
    description: 'Complex approval process with executive intervention',
    document: 'Internal Audit Checklist and Guidelines V2.1',
    expectedDuration: '12-18 minutes',
    steps: [
      { action: 'create_document', actor: 'author02', expectedResult: 'DRAFT' },
      { action: 'submit_for_review', actor: 'author02', reviewer: 'reviewer02', expectedResult: 'PENDING_REVIEW' },
      { action: 'approve_review', actor: 'reviewer02', comment: 'Audit procedures are thorough and compliant', expectedResult: 'REVIEWED' },
      { action: 'route_for_approval', actor: 'author02', approver: 'approver01', expectedResult: 'PENDING_APPROVAL' },
      { action: 'reject_approval', actor: 'approver01', comment: 'Requires additional regulatory compliance review', expectedResult: 'APPROVAL_REJECTED' },
      { action: 'escalate_to_senior', actor: 'author02', approver: 'senior02', expectedResult: 'PENDING_SENIOR_APPROVAL' },
      { action: 'approve_document', actor: 'senior02', comment: 'Approved after executive compliance review', expectedResult: 'APPROVED' },
      { action: 'set_effective_date', actor: 'author02', effectiveDate: '2025-02-15', expectedResult: 'EFFECTIVE' }
    ]
  }
];

// Test validation rules
const validationRules = {
  userCreation: {
    requiredFields: ['username', 'email', 'firstName', 'lastName'],
    emailFormat: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    usernamePattern: /^[a-zA-Z0-9_]{3,20}$/,
    passwordMinLength: 6
  },
  documentCreation: {
    requiredFields: ['title', 'description', 'documentType'],
    titleMinLength: 5,
    titleMaxLength: 200,
    descriptionMinLength: 10,
    allowedDocumentTypes: ['POL', 'PROC', 'MAN', 'FORM', 'GUIDE', 'SPEC']
  },
  workflowTransitions: {
    allowedTransitions: {
      'DRAFT': ['PENDING_REVIEW', 'ARCHIVED'],
      'PENDING_REVIEW': ['REVIEWED', 'REJECTED'],
      'REVIEWED': ['PENDING_APPROVAL', 'DRAFT'],
      'PENDING_APPROVAL': ['APPROVED', 'APPROVAL_REJECTED'],
      'APPROVED': ['EFFECTIVE', 'DRAFT'],
      'EFFECTIVE': ['OBSOLETE', 'SUPERSEDED']
    },
    requiredFields: {
      'submit_for_review': ['reviewer'],
      'approve_review': ['comment'],
      'reject_review': ['comment'],
      'route_for_approval': ['approver'],
      'approve_document': ['comment'],
      'set_effective_date': ['effectiveDate']
    }
  }
};

// API endpoints for validation
const apiEndpoints = {
  auth: {
    login: '/api/v1/auth/token/',
    profile: '/api/v1/auth/profile/',
    logout: '/api/v1/auth/logout/'
  },
  users: {
    list: '/api/users/',
    create: '/api/users/',
    detail: '/api/users/{id}/',
    groups: '/api/users/{id}/groups/'
  },
  documents: {
    list: '/api/documents/',
    create: '/api/documents/',
    detail: '/api/documents/{id}/',
    upload: '/api/documents/upload/',
    download: '/api/documents/{id}/download/'
  },
  workflows: {
    list: '/api/workflows/',
    submit_review: '/api/workflows/submit-review/',
    approve_review: '/api/workflows/approve-review/',
    reject_review: '/api/workflows/reject-review/',
    route_approval: '/api/workflows/route-approval/',
    approve_document: '/api/workflows/approve-document/',
    set_effective: '/api/workflows/set-effective/'
  }
};

module.exports = {
  config,
  testUsers,
  testDocuments,
  workflowScenarios,
  validationRules,
  apiEndpoints
};