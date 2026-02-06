# Sensitivity Label Classification Guide for Approvers

## Quick Reference Decision Tree

```
START: Does this document contain...

├─ Already public information? → PUBLIC
│
├─ Standard company procedures? → INTERNAL
│
├─ Business-sensitive information? 
│  ├─ Regulatory/FDA submissions? → RESTRICTED
│  ├─ Trade secrets/formulations? → PROPRIETARY
│  └─ Contracts/audit reports? → CONFIDENTIAL
│
└─ When in doubt? → INTERNAL (safe default)
```

---

## The 5 Sensitivity Levels

### 🌐 PUBLIC
**Who can access:** Anyone (external sharing allowed)

**Use this label when:**
- ✅ Information is already publicly available
- ✅ Document is intended for external distribution
- ✅ No confidentiality concerns exist
- ✅ Company wants to share this externally

**Examples:**
- Published quality certificates (ISO certifications)
- Marketing materials and product brochures
- Public-facing quality policy statements
- Product catalogs (non-sensitive specifications)
- Job postings
- Press releases
- Published research papers

**Handling:**
- No restrictions on distribution
- Can be posted on public websites
- No encryption required

**Risk if leaked:** None - already public information

---

### 🏢 INTERNAL USE ONLY (Default)
**Who can access:** All company employees

**Use this label when:**
- ✅ Standard operating procedures (SOPs)
- ✅ Company policies and procedures
- ✅ Training materials
- ✅ Work instructions
- ✅ Internal forms and templates
- ✅ General project documentation

**Examples:**
- Quality Manual
- Standard Operating Procedures (SOPs)
- Work Instructions (WIs)
- Training materials and presentations
- Internal policies and procedures
- Meeting minutes (non-confidential)
- Equipment maintenance logs
- General forms and templates
- Internal memos

**Handling:**
- Should not leave company premises
- No external sharing without approval
- Basic access logging
- Encrypted storage recommended

**Risk if leaked:** Low - minor business disruption

**💡 This should be your DEFAULT choice** - Most quality/compliance documents are INTERNAL.

---

### 🔒 CONFIDENTIAL
**Who can access:** Need-to-know basis only

**Use this label when:**
- ✅ Internal audit reports
- ✅ Customer contracts
- ✅ Supplier agreements
- ✅ Test results (pre-publication)
- ✅ Product specifications (detailed)
- ✅ Financial data
- ✅ Employee records
- ✅ CAPA investigations
- ✅ Deviation reports

**Examples:**
- Internal audit reports
- Customer contracts and agreements
- Supplier agreements and pricing
- Test results (pre-publication)
- Validation protocols and reports
- Product specifications (detailed technical)
- CAPA (Corrective and Preventive Action) investigations
- Deviation reports and investigations
- Financial data and budgets
- Employee personnel records
- Risk assessments
- Change control records

**Handling:**
- Encrypted storage required
- Access logging and monitoring
- NDAs required for external viewing
- Watermarked when printed
- No unauthorized copying
- Regular access reviews

**Risk if leaked:** Medium-High
- Competitive disadvantage
- Regulatory scrutiny
- Legal liability
- Customer trust damage

**When to choose CONFIDENTIAL vs RESTRICTED:**
- Choose CONFIDENTIAL for business-sensitive information
- Choose RESTRICTED for regulatory/compliance documents (see below)

---

### ⚠️ RESTRICTED - Regulatory/Compliance
**Who can access:** Authorized personnel only (QA Manager+ approval)

**Use this label when:**
- ✅ FDA/EMA submissions
- ✅ Regulatory correspondence
- ✅ Audit responses
- ✅ Clinical trial data
- ✅ Regulatory inspection documents

**Examples:**
- FDA/EMA submissions (510k, PMA, NDA)
- Regulatory correspondence and queries
- Agency meeting minutes and responses
- Clinical trial data and protocols
- Regulatory audit findings
- Compliance investigation reports
- Warning letter responses
- Pre-market approval documents
- Post-market surveillance reports
- Regulatory inspection responses

**Handling:**
- Highest encryption standards
- Complete access audit trail
- Regulatory compliance tracking
- Time-limited access grants
- Manager approval required for access
- No printing without authorization
- Secure disposal procedures
- Access reviews every 90 days

**Risk if leaked:** High
- Regulatory action
- Legal penalties
- Damage to regulatory standing
- Product approval delays
- Company reputation damage

**Key Difference from CONFIDENTIAL:**
RESTRICTED is specifically for documents with **regulatory oversight** or **compliance implications**. If unauthorized disclosure could result in regulatory action or legal penalties from health authorities, use RESTRICTED.

---

### 🛡️ PROPRIETARY / Trade Secret
**Who can access:** Executive approval required

**Use this label when:**
- ✅ Manufacturing processes (unique methods)
- ✅ Proprietary formulations
- ✅ Patent applications (pre-filing)
- ✅ Strategic business plans
- ✅ Source code/algorithms

**Examples:**
- Manufacturing processes (unique/secret methods)
- Proprietary formulations and recipes
- Proprietary designs and innovations
- Patent applications (pre-filing)
- Strategic business plans
- M&A documents and negotiations
- Source code and algorithms
- Competitive intelligence
- Trade secret documentation
- Breakthrough research data

**Handling:**
- Maximum encryption (AES-256)
- Complete audit trail with video logging
- Executive approval for all access
- No printing allowed
- Watermarked on every page if printed
- Screen recording blocked
- Physical security for any printouts
- Clean desk policy enforced
- Access reviews monthly
- Immediate revocation on role change

**Risk if leaked:** Critical
- Business survival threat
- Major competitive advantage lost
- Patent rights compromised
- Legal action required
- Valuation impact

**When to use PROPRIETARY:**
Only use this for information that represents **core competitive advantage** or **trade secrets**. If competitors obtaining this information would threaten business viability, use PROPRIETARY.

---

## Decision Flowchart

```
┌─────────────────────────────────────────┐
│ START: Classifying Document             │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│ Is this already publicly available?     │
│ (certificates, press releases, etc.)    │
└──────┬──────────────────────┬───────────┘
       │ YES                  │ NO
       ▼                      ▼
   ┌────────┐        ┌──────────────────────────────┐
   │ PUBLIC │        │ Does it contain regulatory/  │
   └────────┘        │ FDA submission information?  │
                     └──────┬──────────────┬────────┘
                            │ YES          │ NO
                            ▼              ▼
                     ┌────────────┐   ┌──────────────────────────┐
                     │ RESTRICTED │   │ Does it contain trade    │
                     └────────────┘   │ secrets or proprietary   │
                                      │ formulations/processes?  │
                                      └──────┬──────────┬────────┘
                                             │ YES      │ NO
                                             ▼          ▼
                                      ┌────────────┐  ┌─────────────────────┐
                                      │PROPRIETARY │  │ Is it business      │
                                      └────────────┘  │ confidential?       │
                                                      │ (contracts, audits) │
                                                      └──────┬──────┬───────┘
                                                             │ YES  │ NO
                                                             ▼      ▼
                                                      ┌──────────────┐ ┌──────────┐
                                                      │CONFIDENTIAL  │ │ INTERNAL │
                                                      └──────────────┘ └──────────┘
```

---

## Common Classification Scenarios

### Quality Management System Documents

| Document Type | Typical Classification | Notes |
|---------------|----------------------|-------|
| Quality Manual | INTERNAL | Standard company policy |
| SOPs | INTERNAL | Standard procedures for all staff |
| Work Instructions | INTERNAL | Step-by-step guides |
| Forms/Templates | INTERNAL | Blank forms for data collection |
| Training Records | CONFIDENTIAL | Contains employee data |

### Product Development Documents

| Document Type | Typical Classification | Notes |
|---------------|----------------------|-------|
| Product Specifications (general) | INTERNAL | High-level specs |
| Product Specifications (detailed) | CONFIDENTIAL | Detailed technical specs |
| Manufacturing Process (standard) | INTERNAL | Common processes |
| Manufacturing Process (unique) | PROPRIETARY | Trade secret methods |
| Formulations (proprietary) | PROPRIETARY | Competitive advantage |
| Design Files | CONFIDENTIAL to PROPRIETARY | Depends on novelty |

### Regulatory/Compliance Documents

| Document Type | Typical Classification | Notes |
|---------------|----------------------|-------|
| FDA Submissions | RESTRICTED | Regulatory oversight |
| Audit Reports (internal) | CONFIDENTIAL | Business sensitive |
| Audit Reports (regulatory) | RESTRICTED | Regulatory implications |
| Inspection Responses | RESTRICTED | Direct regulatory communication |
| Certificates (published) | PUBLIC | Already public |
| Compliance Reports | RESTRICTED | Regulatory tracking |

### Business/Commercial Documents

| Document Type | Typical Classification | Notes |
|---------------|----------------------|-------|
| Customer Contracts | CONFIDENTIAL | Business sensitive |
| Supplier Agreements | CONFIDENTIAL | Business sensitive |
| Pricing Information | CONFIDENTIAL | Competitive information |
| Financial Reports | CONFIDENTIAL | Business sensitive |
| Strategic Plans | PROPRIETARY | Competitive advantage |
| M&A Documents | PROPRIETARY | Critical business |

---

## Changing Sensitivity Labels

### When Up-Versioning Documents

**Default Behavior:** New versions inherit the sensitivity label from the previous version.

**What you'll see during approval:**
- Inherited sensitivity will be pre-selected
- You can confirm or change it
- If you change it, you MUST provide a reason

### Upgrading Sensitivity (Low → High)

**Example:** INTERNAL → CONFIDENTIAL

**When to upgrade:**
- Document now contains trade secrets
- Regulatory submission added
- Customer-specific information added
- Competitive intelligence added

**Requirements:**
- Provide reason for upgrade (audit trail)
- Minimum 20 characters

**Example reason:**
"Added customer-specific requirements per PM-2024-045. Document now contains confidential pricing and technical specifications that could cause competitive disadvantage if disclosed."

### Downgrading Sensitivity (High → Low)

**Example:** PROPRIETARY → PUBLIC

**When to downgrade:**
- Patent has been published
- Information is now public domain
- Trade secret no longer applies
- Document declassified by management

**Requirements:**
- Detailed justification required (minimum 20 characters)
- Additional scrutiny on downgrades

**Example reason:**
"Patent US-12345678 has been published and is now in public domain. Information contained in this document is no longer proprietary and can be shared publicly per legal guidance memo LG-2024-089."

---

## Frequently Asked Questions

### Q: What if I'm not sure which label to use?

**A:** Choose **INTERNAL** as the safe default. This ensures the document is accessible to employees but not shared externally. You can always upgrade the sensitivity later if needed.

### Q: Can I change the sensitivity label after approval?

**A:** No. Sensitivity labels are set during approval and become part of the permanent document record. If sensitivity needs to change, create a new version with the updated classification.

### Q: What's the difference between CONFIDENTIAL and RESTRICTED?

**A:** 
- **CONFIDENTIAL:** Business-sensitive information (contracts, audits, financial data)
- **RESTRICTED:** Regulatory/compliance documents with potential regulatory implications

If the document involves health authorities (FDA, EMA, etc.), use RESTRICTED.

### Q: Do I need to classify every document?

**A:** Yes. Every document requires a sensitivity label at approval. This is required for compliance and access control.

### Q: What if the document has mixed content?

**A:** Use the **highest sensitivity level** that applies to any content in the document. For example, if most of the document is INTERNAL but one section contains CONFIDENTIAL information, classify the entire document as CONFIDENTIAL.

### Q: Can lower-level staff view RESTRICTED documents?

**A:** RESTRICTED documents require QA Manager or higher approval. Staff below this level need manager authorization to access these documents.

### Q: How long does a sensitivity classification last?

**A:** The sensitivity label is permanent for that document version. It travels with the document and is inherited by new versions (but can be changed during approval).

---

## Examples of Correct Classification

### Example 1: Standard Operating Procedure
**Document:** "SOP-2025-0001 Document Control Procedure"
**Content:** How to create, review, and approve documents
**Classification:** **INTERNAL**
**Reasoning:** Standard company procedure for all employees

---

### Example 2: FDA Submission
**Document:** "510k Submission for Device XYZ"
**Content:** FDA pre-market notification submission
**Classification:** **RESTRICTED**
**Reasoning:** Regulatory submission with compliance implications

---

### Example 3: Customer Contract
**Document:** "Service Agreement with Acme Corp"
**Content:** Terms, pricing, confidentiality obligations
**Classification:** **CONFIDENTIAL**
**Reasoning:** Business-sensitive with competitive pricing

---

### Example 4: Manufacturing Process
**Document:** "Proprietary Coating Process for Product ABC"
**Content:** Unique coating method that competitors don't have
**Classification:** **PROPRIETARY**
**Reasoning:** Trade secret providing competitive advantage

---

### Example 5: Quality Certificate
**Document:** "ISO 13485:2016 Certificate"
**Content:** Published quality certification
**Classification:** **PUBLIC**
**Reasoning:** Already publicly available, posted on website

---

## Tips for Approvers

✅ **DO:**
- Take time to review document content before classifying
- Consider who needs access to this information
- Provide clear reasons when changing inherited sensitivity
- Ask for guidance if unsure (default to INTERNAL)
- Consider regulatory implications

❌ **DON'T:**
- Rush through classification - it's a critical compliance step
- Downgrade sensitivity without strong justification
- Use PUBLIC for internal documents "just in case"
- Ignore inherited classification without reason
- Classify based on convenience instead of content

---

## Getting Help

**If you're unsure about classification:**

1. **Consult the QA Manager** - They can provide guidance on classification
2. **Review similar documents** - Check how similar documents were classified
3. **Default to INTERNAL** - The safe default for most documents
4. **Escalate to higher authority** - For PROPRIETARY or RESTRICTED decisions

**Contact:**
- QA Manager: [Contact Info]
- Regulatory Affairs: [Contact Info]
- Document Control: [Contact Info]

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-02-05 | Initial classification guide | EDMS System |

---

**Remember:** Sensitivity classification is a **compliance requirement** and **security control**. Take it seriously. When in doubt, choose a higher classification or ask for guidance.
