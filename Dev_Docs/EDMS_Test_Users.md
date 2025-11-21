# EDMS Test Users

This document provides a comprehensive list of test users with appropriate roles for testing the 21 CFR Part 11 compliant EDMS system.

## Role Definitions

Based on the EDMS requirements, each operational module has these permission levels:
- **read**: Minimum access level - view documents only
- **write**: Create and edit entries + read access
- **review**: Review documents + write access
- **approve**: Approve documents + review access
- **admin**: Assign roles, reset passwords, add/remove users + approve access

## Test User Accounts

### Superuser Accounts
| Username | Password | Role | Full Name | Department | Email |
|----------|----------|------|-----------|------------|--------|
| `superadmin` | `SuperAdmin123!` | Superuser | Super Administrator | IT/Systems | superadmin@edmstest.com |

### Document Management Users (O1. EDMS Module)

#### Document Viewers (Base Permission: read)
| Username | Password | Role | Full Name | Department | Email |
|----------|----------|------|-----------|------------|--------|
| `viewer01` | `Viewer123!` | Document Viewer | Alice Johnson | Quality Assurance | alice.johnson@edmstest.com |
| `viewer02` | `Viewer123!` | Document Viewer | Bob Wilson | Manufacturing | bob.wilson@edmstest.com |
| `viewer03` | `Viewer123!` | Document Viewer | Carol Davis | Research | carol.davis@edmstest.com |

#### Document Authors (Base Permission: write)
| Username | Password | Role | Full Name | Department | Email |
|----------|----------|------|-----------|------------|--------|
| `author01` | `Author123!` | Document Author | David Brown | Quality Assurance | david.brown@edmstest.com |
| `author02` | `Author123!` | Document Author | Emma Garcia | Regulatory Affairs | emma.garcia@edmstest.com |
| `author03` | `Author123!` | Document Author | Frank Miller | Manufacturing | frank.miller@edmstest.com |
| `author04` | `Author123!` | Document Author | Grace Lee | Research & Development | grace.lee@edmstest.com |

#### Document Reviewers (Base Permission: review)
| Username | Password | Role | Full Name | Department | Email |
|----------|----------|------|-----------|------------|--------|
| `reviewer01` | `Reviewer123!` | Document Reviewer | Henry Taylor | Quality Assurance | henry.taylor@edmstest.com |
| `reviewer02` | `Reviewer123!` | Document Reviewer | Isabel Martinez | Regulatory Affairs | isabel.martinez@edmstest.com |
| `reviewer03` | `Reviewer123!` | Document Reviewer | Jack Anderson | Manufacturing | jack.anderson@edmstest.com |

#### Document Approvers (Base Permission: approve)
| Username | Password | Role | Full Name | Department | Email |
|----------|----------|------|-----------|------------|--------|
| `approver01` | `Approver123!` | Document Approver | Karen White | Quality Assurance | karen.white@edmstest.com |
| `approver02` | `Approver123!` | Document Approver | Lucas Thompson | Regulatory Affairs | lucas.thompson@edmstest.com |
| `approver03` | `Approver123!` | Document Approver | Maria Rodriguez | Manufacturing | maria.rodriguez@edmstest.com |

#### Document Administrators (Base Permission: admin)
| Username | Password | Role | Full Name | Department | Email |
|----------|----------|------|-----------|------------|--------|
| `docadmin01` | `DocAdmin123!` | Document Admin | Nancy Jackson | Quality Assurance | nancy.jackson@edmstest.com |
| `docadmin02` | `DocAdmin123!` | Document Admin | Oscar Chen | Regulatory Affairs | oscar.chen@edmstest.com |

### Service Module Access Users

#### User Management (S1)
| Username | Password | Role | Full Name | Department | Email |
|----------|----------|------|-----------|------------|--------|
| `useradmin` | `UserAdmin123!` | User Administrator | Patricia Kim | Human Resources | patricia.kim@edmstest.com |

#### Audit Trail Administrator (S2)
| Username | Password | Role | Full Name | Department | Email |
|----------|----------|------|-----------|------------|--------|
| `auditadmin` | `AuditAdmin123!` | Audit Administrator | Robert Chang | Compliance | robert.chang@edmstest.com |

#### Scheduler Administrator (S3)
| Username | Password | Role | Full Name | Department | Email |
|----------|----------|------|-----------|------------|--------|
| `schedadmin` | `SchedAdmin123!` | Scheduler Admin | Sandra Lopez | IT Operations | sandra.lopez@edmstest.com |

#### Backup Administrator (S4)
| Username | Password | Role | Full Name | Department | Email |
|----------|----------|------|-----------|------------|--------|
| `backupadmin` | `BackupAdmin123!` | Backup Administrator | Thomas Wilson | IT Operations | thomas.wilson@edmstest.com |

#### Workflow Administrator (S5)
| Username | Password | Role | Full Name | Department | Email |
|----------|----------|------|-----------|------------|--------|
| `workflowadmin` | `WorkflowAdmin123!` | Workflow Admin | Victoria Green | Process Engineering | victoria.green@edmstest.com |

#### Placeholder Administrator (S6)
| Username | Password | Role | Full Name | Department | Email |
|----------|----------|------|-----------|------------|--------|
| `placeholderadmin` | `PlaceholderAdmin123!` | Placeholder Admin | William Davis | Document Control | william.davis@edmstest.com |

#### App Settings Administrator (S7)
| Username | Password | Role | Full Name | Department | Email |
|----------|----------|------|-----------|------------|--------|
| `appadmin` | `AppAdmin123!` | App Administrator | Yvonne Martinez | IT Administration | yvonne.martinez@edmstest.com |

## Test Scenarios by User Type

### Document Lifecycle Testing
1. **Author Creates Document**: `author01` creates new SOP
2. **Reviewer Reviews**: `reviewer01` reviews and provides feedback
3. **Author Revises**: `author01` makes changes based on feedback
4. **Reviewer Approves**: `reviewer01` approves document
5. **Approver Final Approval**: `approver01` gives final approval
6. **Version Control**: `author02` creates new version of approved document

### Access Control Testing
- **Viewer Access**: `viewer01` can only view approved documents
- **Permission Escalation**: Test that `viewer01` cannot perform write operations
- **Cross-Department**: Test access between different departments

### Workflow Testing
- **Review Workflow**: Full cycle from draft to approval
- **Up-versioning Workflow**: Version increment testing
- **Obsolete Workflow**: Document obsolescence process
- **Workflow Termination**: Author terminates workflow before approval

### Administrative Testing
- **User Management**: `useradmin` creates/modifies user accounts
- **Role Assignment**: `docadmin01` assigns document roles
- **System Configuration**: Service module administrators test their respective areas

## Security Considerations

- All passwords follow strong password policies
- Users should be required to change passwords on first login
- Multi-factor authentication should be enabled for admin accounts
- Regular password rotation should be enforced
- Failed login attempts should be monitored and logged

## Department Structure for Testing

- **Quality Assurance**: Document creation, review, and approval focus
- **Regulatory Affairs**: Compliance and regulatory document focus
- **Manufacturing**: Operational procedure focus
- **Research & Development**: Technical document focus
- **IT Operations**: System administration and maintenance
- **Human Resources**: User management focus
- **Compliance**: Audit and regulatory oversight
- **Process Engineering**: Workflow design and optimization
- **Document Control**: Placeholder and template management

This user structure provides comprehensive coverage for testing all EDMS functionalities while maintaining realistic organizational roles and responsibilities.