# Record Retention Policy - Implementation Guide

**Purpose:** Define how long different document types must be retained and when they can be archived or deleted  
**Estimated Time:** 4-6 hours to create and implement  
**Compliance:** Meets 21 CFR Part 11 §11.10(b) requirements

---

## 📋 What is a Record Retention Policy?

A **Record Retention Policy** is a documented plan that specifies:

1. **How long** different types of records must be kept
2. **When** records can be archived or deleted
3. **Who** is responsible for retention decisions
4. **How** records are stored and protected during retention period
5. **What happens** when retention period expires

---

## 🎯 Why You Need One

### **For Compliance:**
- ✅ Required by 21 CFR Part 11 for FDA-regulated systems
- ✅ Required by ISO 9001 for quality management
- ✅ Required by many industry regulations

### **For Business:**
- ✅ Legal protection (keep records for litigation)
- ✅ Operational efficiency (don't keep unnecessary data)
- ✅ Storage management (control database growth)
- ✅ Audit readiness (know what you have and where)

---

## 📝 Step-by-Step: Create Your Retention Policy

### **Step 1: Identify Document Types (30 minutes)**

List all document types in your EDMS and their purposes:

#### **Example Document Types:**

| Document Type | Purpose | Examples |
|---------------|---------|----------|
| **SOPs** | Standard procedures | Manufacturing SOPs, Testing SOPs |
| **Work Instructions** | Detailed instructions | Equipment operation, Cleaning |
| **Forms** | Data collection | Batch records, Test results |
| **Policies** | Company policies | Quality policy, Safety policy |
| **Reports** | Analysis reports | Validation reports, Audit reports |
| **Records** | Evidence of activities | Training records, Calibration records |
| **Specifications** | Product/process specs | Raw material specs, Product specs |
| **Protocols** | Test plans | Validation protocols, Stability protocols |

**Action:** Create a spreadsheet with your document types

```
Document Type | Description | Current Usage
-------------------------------------------------
SOP           | Procedures  | 50 active documents
Work Instr    | Instructions| 30 active documents
Forms         | Templates   | 20 active documents
...
```

---

### **Step 2: Research Retention Requirements (1 hour)**

Determine how long each document type must be kept based on:

#### **A. Regulatory Requirements**

**FDA (21 CFR Part 11):**
- Equipment/Process Records: Lifetime of equipment + 1 year
- Batch Records: 1 year after expiration date
- Complaint Records: 3 years (OTC), 5 years (Rx)
- Quality Records: 7 years minimum

**ISO 9001:**
- Quality records: Varies by document type
- Typically 3-7 years

**OSHA:**
- Employee medical records: 30 years after termination
- Safety training records: 5 years

#### **B. Legal Requirements**

**General Business Records:**
- Tax records: 7 years (IRS)
- Employment records: 7 years after termination
- Contracts: 7 years after expiration
- Corporate records: Indefinitely

#### **C. Industry Standards**

**Quality Management:**
- Master documents: Until superseded + 3 years
- Obsolete documents: 3-7 years after obsolescence
- Training records: Duration of employment + 3 years

#### **D. Business Needs**

**Operational:**
- Reference documents: As long as needed
- Historical data: For trending and analysis
- Archived products: Lifetime of product line

**Action:** Create retention requirements table

```
Document Type | Regulatory | Legal | Business | Minimum Retention
----------------------------------------------------------------
SOP           | 7 years    | N/A   | Forever  | Until superseded + 7 years
Batch Record  | 1 yr+exp   | 7 yrs | 10 yrs   | 10 years after production
Training      | 3 years    | 7 yrs | Duration | Duration + 7 years
...
```

---

### **Step 3: Define Retention Periods (1 hour)**

Create your retention schedule based on Step 2 research:

#### **Example Retention Schedule:**

| Document Type | Retention Period | Trigger | Notes |
|---------------|-----------------|---------|-------|
| **SOPs (Active)** | Until superseded | Supersession | Keep active until replaced |
| **SOPs (Obsolete)** | 7 years | Obsolete date | After superseded |
| **Work Instructions** | 7 years | Obsolete date | Same as SOPs |
| **Batch Records** | 10 years | Production date | Or 1 year after expiry |
| **Training Records** | Employment + 7 years | Termination | OSHA compliance |
| **Validation Reports** | Lifetime + 7 years | Equipment retirement | FDA requirement |
| **Quality Records** | 7 years | Creation date | Minimum retention |
| **Audit Reports** | 10 years | Audit date | Internal policy |
| **Product Specifications** | Product life + 7 years | Discontinuation | Complaint support |
| **Complaint Records** | 5 years | Complaint date | FDA requirement |
| **Change Controls** | 7 years | Approval date | Quality records |
| **CAPA Records** | 7 years | Closure date | Quality records |

#### **Special Cases:**

**Permanent Retention (Never Delete):**
- Master Quality Policy
- Regulatory licenses
- Corporate registration documents
- Patents and IP documents

**Event-Based Retention:**
- Litigation hold: Indefinite until released
- Product recall: 10 years after resolution
- Regulatory inspection: 7 years after closure

---

### **Step 4: Create Policy Document (2 hours)**

Write the formal policy document. Here's a template:

---

## 📄 **TEMPLATE: Record Retention Policy**

### **DOCUMENT RETENTION AND DISPOSITION POLICY**

**Document Number:** QP-XXX  
**Effective Date:** [Date]  
**Review Date:** [Annual]  
**Approved By:** [Quality Manager]

---

#### **1. PURPOSE**

This policy establishes requirements for the retention and disposition of records maintained in the Electronic Document Management System (EDMS) to ensure compliance with regulatory requirements and support business operations.

---

#### **2. SCOPE**

This policy applies to all electronic records created, received, or maintained in the EDMS, including:
- Standard Operating Procedures (SOPs)
- Work Instructions
- Forms and Templates
- Quality Records
- Training Records
- Validation Documentation
- Manufacturing Records
- All other controlled documents

---

#### **3. DEFINITIONS**

**Active Record:** A record currently in use or subject to frequent reference.

**Inactive Record:** A record no longer in active use but must be retained for regulatory or business purposes.

**Archived Record:** An inactive record moved to long-term storage while remaining accessible.

**Retention Period:** The minimum time a record must be retained before it can be evaluated for disposition.

**Disposition:** The action taken at the end of the retention period (archive, retain, or destroy).

**Regulatory Hold:** Suspension of normal retention rules due to legal or regulatory requirements.

---

#### **4. RESPONSIBILITIES**

**Quality Manager:**
- Approve and maintain this policy
- Oversee compliance with retention requirements
- Authorize record destruction

**Document Control:**
- Implement retention schedules
- Monitor retention periods
- Execute approved dispositions

**System Administrator:**
- Configure retention settings in EDMS
- Generate retention reports
- Maintain audit trail of dispositions

**Users:**
- Create accurate records
- Do not delete records outside policy
- Report retention concerns

---

#### **5. RETENTION SCHEDULE**

##### **5.1 Standard Operating Procedures**

| Status | Retention Period | Trigger Date |
|--------|-----------------|--------------|
| Active | Until superseded | Approval date |
| Obsolete | 7 years | Obsolete date |

**Notes:**
- All versions retained
- Superseded versions marked obsolete
- Cannot be deleted while active

##### **5.2 Quality Records**

| Record Type | Retention Period | Trigger Date |
|-------------|-----------------|--------------|
| Batch/Lot Records | 10 years | Production completion |
| Validation Reports | Equipment life + 7 years | Equipment retirement |
| Audit Reports | 10 years | Audit date |
| CAPA Records | 7 years | Closure date |
| Change Controls | 7 years | Implementation date |
| Training Records | Employment + 7 years | Training date |

##### **5.3 Product-Related Records**

| Record Type | Retention Period | Trigger Date |
|-------------|-----------------|--------------|
| Product Specifications | Product life + 7 years | Discontinuation |
| Stability Studies | Product life + 7 years | Study completion |
| Complaints | 5 years | Complaint receipt |
| Adverse Events | 10 years | Event date |

##### **5.4 Business Records**

| Record Type | Retention Period | Trigger Date |
|-------------|-----------------|--------------|
| Policies | Until superseded + 3 years | Supersession |
| Meeting Minutes | 7 years | Meeting date |
| Correspondence | 3 years | Date sent/received |

---

#### **6. RETENTION PROCEDURES**

##### **6.1 Automatic Retention**

The EDMS automatically:
1. Tracks document creation/approval dates
2. Calculates retention expiration dates
3. Prevents deletion of documents within retention period
4. Flags documents approaching end of retention
5. Maintains audit trail of all retention actions

##### **6.2 Retention Review Process**

**Quarterly Review:**
1. System generates list of records approaching retention end
2. Document Control reviews list
3. Determine disposition:
   - **Extend:** Continue retention if business need
   - **Archive:** Move to long-term storage
   - **Destroy:** Permanently delete (with approval)

**Annual Review:**
1. Review entire retention schedule
2. Update retention periods if regulations change
3. Verify compliance with retention policy

##### **6.3 Exceptions and Extensions**

Retention may be extended for:
- Ongoing litigation
- Regulatory investigations
- Audit findings
- Business need
- Customer requirements

**Process:**
1. Requestor submits retention extension request
2. Quality Manager reviews and approves
3. System Administrator updates retention date
4. Extension documented in audit trail

---

#### **7. DISPOSITION PROCEDURES**

##### **7.1 Archive**

For records past retention that may have future value:
1. Move to archive storage
2. Maintain full searchability
3. Update status to "Archived"
4. Record remains accessible but read-only

##### **7.2 Destruction**

For records past retention with no future value:

**Requirements:**
- Quality Manager approval required
- Audit trail entry created
- Document metadata retained (not content)
- Cannot destroy if:
  - Under litigation hold
  - Subject to investigation
  - Referenced by active records

**Process:**
1. Generate disposition list
2. Quality Manager review and approve
3. System Administrator executes destruction
4. Generate destruction certificate
5. Retain destruction records for 7 years

---

#### **8. SPECIAL CIRCUMSTANCES**

##### **8.1 Litigation Hold**

When legal action is anticipated or active:
1. All related records placed on hold
2. Normal retention suspended
3. Records cannot be destroyed
4. Hold remains until legal releases

##### **8.2 Regulatory Inspection**

During FDA or other regulatory inspection:
1. All records related to inspection on hold
2. Extends 7 years from inspection close
3. Cannot destroy without regulatory review

##### **8.3 Product Recall**

All records related to recalled product:
1. Immediate hold on all related records
2. Extends 10 years from recall resolution
3. Includes batch records, complaints, investigations

---

#### **9. AUDIT TRAIL**

The EDMS maintains an audit trail of:
- Document creation dates
- Status changes (active → obsolete)
- Retention period assignments
- Retention extensions/modifications
- Archive actions
- Destruction actions
- All retention-related access

Audit trail records retained for 7 years beyond record retention.

---

#### **10. TRAINING**

All users must complete training on:
- This retention policy
- Their responsibilities
- How to access retention information
- Proper record handling

Training recorded in EDMS training system.

---

#### **11. POLICY REVIEW**

This policy reviewed annually and updated as needed for:
- Regulatory changes
- Business changes
- System changes
- Audit findings

---

#### **12. REFERENCES**

- 21 CFR Part 11 - Electronic Records and Signatures
- 21 CFR Part 820 - Quality System Regulation
- ISO 9001 - Quality Management Systems
- IRS Guidelines - Tax Record Retention
- OSHA Requirements - Safety Records

---

#### **APPROVAL**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Quality Manager | | | |
| Regulatory Affairs | | | |
| IT Manager | | | |

---

### **Step 5: Implement in EDMS (1-2 hours)**

Now implement the policy in your system:

#### **Option A: Add Retention Fields to Models**

```python
# backend/apps/documents/models.py

class Document(models.Model):
    # ... existing fields ...
    
    # Retention fields
    retention_period_years = models.IntegerField(
        default=7,
        help_text="Number of years to retain after trigger date"
    )
    retention_trigger_date = models.DateField(
        null=True, blank=True,
        help_text="Date from which retention period is calculated"
    )
    retention_expiration_date = models.DateField(
        null=True, blank=True,
        help_text="Date when document can be archived/destroyed"
    )
    retention_status = models.CharField(
        max_length=20,
        choices=[
            ('ACTIVE', 'Active Retention'),
            ('APPROACHING', 'Approaching Expiration'),
            ('EXPIRED', 'Retention Expired'),
            ('HOLD', 'Legal/Regulatory Hold'),
            ('EXTENDED', 'Retention Extended'),
        ],
        default='ACTIVE'
    )
    retention_hold_reason = models.TextField(
        blank=True,
        help_text="Reason for hold or extension"
    )
    
    def calculate_retention_expiration(self):
        """Calculate when retention period expires."""
        if self.retention_trigger_date and self.retention_period_years:
            from datetime import timedelta
            expiration = self.retention_trigger_date + timedelta(days=365 * self.retention_period_years)
            return expiration
        return None
    
    def update_retention_status(self):
        """Update retention status based on current date."""
        from datetime import date, timedelta
        
        if self.retention_hold_reason:
            self.retention_status = 'HOLD'
            return
        
        expiration = self.calculate_retention_expiration()
        if not expiration:
            return
        
        today = date.today()
        days_until_expiration = (expiration - today).days
        
        if days_until_expiration < 0:
            self.retention_status = 'EXPIRED'
        elif days_until_expiration < 90:  # 3 months warning
            self.retention_status = 'APPROACHING'
        else:
            self.retention_status = 'ACTIVE'
```

#### **Option B: Configure Retention by Document Type**

```python
# backend/apps/documents/models.py

class DocumentType(models.Model):
    # ... existing fields ...
    
    # Default retention settings
    default_retention_years = models.IntegerField(
        default=7,
        help_text="Default retention period for this document type"
    )
    retention_trigger = models.CharField(
        max_length=20,
        choices=[
            ('CREATION', 'Creation Date'),
            ('APPROVAL', 'Approval Date'),
            ('EFFECTIVE', 'Effective Date'),
            ('OBSOLETE', 'Obsolete Date'),
            ('COMPLETION', 'Completion Date'),
        ],
        default='APPROVAL'
    )
```

#### **Option C: Create Management Command**

```bash
# Run retention checks
python manage.py check_retention
python manage.py generate_retention_report
```

---

### **Step 6: Create Retention Reports (30 minutes)**

Add ability to track and report on retention:

**Reports needed:**
1. **Retention Expiration Report** - Documents approaching retention end
2. **Hold Report** - Documents on legal/regulatory hold
3. **Destruction Report** - Documents approved for destruction
4. **Compliance Report** - Overall retention compliance status

---

### **Step 7: Train Users (1 hour)**

Train all users on:
- Policy requirements
- Their responsibilities
- How to check retention status
- Who to contact with questions

---

## 📊 **Simple Implementation (Quick Start)**

If you want to start simple without code changes:

### **1. Create Retention Spreadsheet**

```
Document ID | Document Type | Approval Date | Retention Years | Expiration Date | Status
---------------------------------------------------------------------------------------
SOP-001     | SOP          | 2020-01-15    | 7              | 2027-01-15      | Active
SOP-002     | SOP          | 2021-05-20    | 7              | 2028-05-20      | Active
BR-001      | Batch Record | 2023-03-10    | 10             | 2033-03-10      | Active
```

### **2. Set Calendar Reminders**

- Quarterly: Review retention expiration list
- Annually: Review retention policy

### **3. Document in SOP**

Create simple SOP documenting:
- Retention periods by document type
- Who is responsible
- Review frequency

---

## ✅ **Success Criteria**

Your retention policy is complete when you have:

- [ ] Policy document written and approved
- [ ] Retention periods defined for all document types
- [ ] Implementation method chosen (code vs. manual)
- [ ] Reports available to track retention
- [ ] Users trained on policy
- [ ] Quarterly review process established
- [ ] Annual policy review scheduled

---

## 🎯 **Your Next Steps**

1. **Choose implementation approach:**
   - Full implementation (add fields to database) - 4-6 hours
   - Simple implementation (spreadsheet + SOP) - 2 hours

2. **Create retention schedule** using template above

3. **Write policy document** using template

4. **Get approval** from Quality Manager

5. **Implement** in EDMS or as manual process

6. **Train users** on policy

---

**Would you like me to help you:**
1. **Create the policy document** for your specific needs?
2. **Implement retention fields** in the database?
3. **Create a simple spreadsheet version** to start?

Let me know and I can help with the specific implementation! 📋
