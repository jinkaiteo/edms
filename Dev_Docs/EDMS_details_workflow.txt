- Workflows:
  
  1. Review Workflow:
     Start Review Workflow
     └──A user with at least write permission (author)  create a document placeholder where a document number is generated. (Document status: DRAFT)
        └──Author upload document and complete basic information such as (Title, Description, Document Type, Document Source, Document Dependencies (only approved and effective document), etc).
           └──Author select a reviewer and route to document for review. (Document status: Pending Review)
              └──Reviewer downloads document and provide comments.
                 ├──Reviewer Rejects document
                 │  └──Document return to Author for edit, re-upload, etc. (Document status: DRAFT)
                 └──Reviewer Approve document (Document status: Reviewed)
                    └──Author select an approver and route to document for approval. (Document status: Pending Approval)
                       └──Approver downloads document and provide comments.
                          ├──Approver Rejects document
                          │  └──Document return to Author for edit, re-upload, etc. (Document status: DRAFT)
                          └──Approver Approve document (Document status: Reviewed)
                             └──Approver select an effective date. (Document status: Approved, Pending Effective)
                                ├──End Workflow Review
                                └──Scheduler checks if effective date =< today.  (Document status: Approved and Effective)

  2. Up-versioning Workflow:
     Start up-versioning workflow on an Approved and Effective Document
     └──A user with at least write permission (author) initiate a up-versioning (increase minor version). Current approved and effective documents is still visible until workflow is completed.
        └──Author provide reason for the up-versioning.
        └──Author follows Review Workflow.
           ├──End up-versioning workflow (increase major version). Author and approver of documents that depends on the prior version will receive notification to verify impact to dependent documents.
           └──Scheduler checks if effective date =< today.  (Set prior version to: Superseded; New approved document to: Approved and Effective)

  3. Obsolete Workflow:
     App checks for other approved document(s) which depends on an Approved and Effective Document targeted to be absolute.
     ├──If there are dependent documents, prevent any user from initiating Obsolete Workflow.
     └──If there are no dependent documents, a user with at least write permission (author) enters reason to obsolete document.  
        └──Start obsoleting workflow
            └──Author initiate a absolute workflow. Current approved and effective documents is still visible until workflow is completed.
               └──Author provide a reason for obsoleting document.
                  └──Author select an approver and route to document for approval.
                     └──Author select an approver and route to document for approval.
                        ├──Approver Rejects Obsoleting
                        │  └──No change to document.
                        └──Approver Approve Obsoleting (Document status: Pending Obsoletion)
                           └──Approver select an Obsoleting date. (Document status: Approved, Pending Effective)
                              └──Do final check if there are no document depending on target document
                                 ├──If there are dependent documents, terminate workflow.
                                 └──If there are no dependent documents, change document status to Pending Obsoleting. This prevents other workflows such as up-versioning and obsolute workflow and linking as depending document.
                                    └──Scheduler checks if effective date =< today.  (Document status: Obsolete)

  4. Termination of Workflow:
     Author may terminate any workflow before approval by providing a reason. The document status return to its last approved state.

- Types of Downloads:
  1) Original Document: The original unmodified draft
  2) Annotated Document: The original document with appended meta data
  3) Official PDF: The annotated approved document converted to PDF and digitally signed

- Action Menu for Document Download
  ├──Download Original Document
  ├──Download Annotated Document
  │  ├──For .docx files
  │  │  └──find and replace special placeholders (indicated in the EDMS settings) with metadata of document such as document title, document number, version number, author, reviewer, approver, approved date, effective date, revision history, current status, downloaded date, etc.
  │  └──For other files
  │     └──download original document along with text file consisting of meta data.
  └──Action when downloading Official PDF:
     ├──For .docx files
     │  └──Generate Annotated Document
     │     └──Digitally Sign PDF for download
     └──For other files
        └──Convert file to PDF
           └──Annotate meta data
              └──Digitally Sign PDF for download
