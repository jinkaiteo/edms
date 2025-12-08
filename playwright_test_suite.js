const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

// Test configuration
const config = {
  baseURL: 'http://localhost:3000',
  timeout: 30000,
  adminCredentials: { username: 'admin', password: 'test123' },
  testDocumentPath: path.join(__dirname, 'test_doc', 'Tikva Quality Policy_template.docx')
};

// Test users to be created with various roles
const testUsers = [
  // Authors
  { username: 'author01', email: 'author01@edms.test', firstName: 'John', lastName: 'Author', role: 'author', groups: ['Document Authors'] },
  { username: 'author02', email: 'author02@edms.test', firstName: 'Sarah', lastName: 'Writer', role: 'author', groups: ['Document Authors'] },
  
  // Reviewers
  { username: 'reviewer01', email: 'reviewer01@edms.test', firstName: 'Mike', lastName: 'Reviewer', role: 'reviewer', groups: ['Document Reviewers'] },
  { username: 'reviewer02', email: 'reviewer02@edms.test', firstName: 'Lisa', lastName: 'Checker', role: 'reviewer', groups: ['Document Reviewers'] },
  
  // Approvers
  { username: 'approver01', email: 'approver01@edms.test', firstName: 'David', lastName: 'Approver', role: 'approver', groups: ['Document Approvers'] },
  { username: 'approver02', email: 'approver02@edms.test', firstName: 'Karen', lastName: 'Manager', role: 'approver', groups: ['Document Approvers'] },
  
  // Senior Approvers
  { username: 'senior01', email: 'senior01@edms.test', firstName: 'Robert', lastName: 'Director', role: 'senior_approver', groups: ['Senior Document Approvers'] },
  { username: 'senior02', email: 'senior02@edms.test', firstName: 'Patricia', lastName: 'Executive', role: 'senior_approver', groups: ['Senior Document Approvers'] },
  
  // Viewers
  { username: 'viewer01', email: 'viewer01@edms.test', firstName: 'Alice', lastName: 'Viewer', role: 'viewer', groups: [] },
  { username: 'viewer02', email: 'viewer02@edms.test', firstName: 'Bob', lastName: 'Reader', role: 'viewer', groups: [] }
];

// Test documents to be created
const testDocuments = [
  {
    title: 'Quality Policy V1.0',
    description: 'Company quality policy document for 2025',
    documentType: 'POL',
    department: 'Quality Assurance',
    author: 'author01'
  },
  {
    title: 'Safety Procedures V1.0', 
    description: 'Updated safety procedures and protocols',
    documentType: 'PROC',
    department: 'Safety',
    author: 'author02'
  },
  {
    title: 'Training Manual V2.0',
    description: 'Employee training manual with new procedures',
    documentType: 'MAN',
    department: 'Human Resources', 
    author: 'author01'
  },
  {
    title: 'Audit Checklist V1.1',
    description: 'Internal audit checklist and procedures',
    documentType: 'FORM',
    department: 'Quality Assurance',
    author: 'author02'
  }
];

// Workflow test scenarios
const workflowScenarios = [
  {
    name: 'Standard Review and Approval',
    document: 'Quality Policy V1.0',
    steps: [
      { action: 'submit_for_review', actor: 'author01', reviewer: 'reviewer01' },
      { action: 'approve_review', actor: 'reviewer01', comment: 'Document reviewed and approved' },
      { action: 'route_for_approval', actor: 'author01', approver: 'approver01' },
      { action: 'approve_document', actor: 'approver01', comment: 'Document approved for publication' },
      { action: 'set_effective_date', actor: 'author01', effectiveDate: '2025-01-01' }
    ]
  },
  {
    name: 'Review with Rejection and Resubmission',
    document: 'Safety Procedures V1.0',
    steps: [
      { action: 'submit_for_review', actor: 'author02', reviewer: 'reviewer02' },
      { action: 'reject_review', actor: 'reviewer02', comment: 'Needs additional safety protocols' },
      { action: 'submit_for_review', actor: 'author02', reviewer: 'reviewer01' },
      { action: 'approve_review', actor: 'reviewer01', comment: 'Updated version looks good' },
      { action: 'route_for_approval', actor: 'author02', approver: 'approver02' },
      { action: 'approve_document', actor: 'approver02', comment: 'Approved with minor suggestions' }
    ]
  },
  {
    name: 'Senior Approval Required',
    document: 'Training Manual V2.0',
    steps: [
      { action: 'submit_for_review', actor: 'author01', reviewer: 'reviewer01' },
      { action: 'approve_review', actor: 'reviewer01', comment: 'Technical content verified' },
      { action: 'route_for_approval', actor: 'author01', approver: 'senior01' },
      { action: 'approve_document', actor: 'senior01', comment: 'Strategic alignment confirmed' },
      { action: 'set_effective_date', actor: 'author01', effectiveDate: '2025-02-01' }
    ]
  },
  {
    name: 'Approval Rejection and Escalation',
    document: 'Audit Checklist V1.1', 
    steps: [
      { action: 'submit_for_review', actor: 'author02', reviewer: 'reviewer02' },
      { action: 'approve_review', actor: 'reviewer02', comment: 'Content is accurate' },
      { action: 'route_for_approval', actor: 'author02', approver: 'approver01' },
      { action: 'reject_approval', actor: 'approver01', comment: 'Needs compliance review' },
      { action: 'route_for_approval', actor: 'author02', approver: 'senior02' },
      { action: 'approve_document', actor: 'senior02', comment: 'Approved after compliance review' }
    ]
  }
];

module.exports = {
  config,
  testUsers,
  testDocuments,
  workflowScenarios
};