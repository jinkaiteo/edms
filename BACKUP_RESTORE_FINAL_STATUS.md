# EDMS Backup & Restore — Final Status and Operations Guide

## Summary
Backup and Restore are established and production-ready with:
- Enhanced foreign key resolution (15+ model handlers)
- Post‑reinit recovery flow (detects Role UUID differences, maps roles by name, creates missing users, regenerates UUIDs)
- Admin‑only “Restore into clean system (reinit first)” option in the frontend (disabled by default, guarded with typed confirmation)
- API path for catastrophic recovery restores that pre‑creates users, forces the enhanced restore pipeline, and (optionally) restores storage files
- CLI flow with a guarded --with-reinit option for disaster recovery

## What’s implemented
- EnhancedRestoreProcessor:
  - Natural key resolution for Users, Roles, Documents, DocumentTypes, DocumentSources
  - Role mapping by name for post‑reinit cases
  - Missing User creation (in API with_reinit flow)
  - UUID regeneration to prevent conflicts
- Frontend UI (BackupManagement):
  - Admin‑only toggle: “Restore into clean system (reinit first)”
  - Strong confirmation required (type RESTORE CLEAN)
  - Sends with_reinit and reinit_confirm as part of restore request
- Backend API (SystemBackupViewSet.restore):
  - Admin‑only with_reinit flow with multiple confirmations
  - Runs system_reinit first, then forces EnhancedRestoreProcessor
  - Pre‑creates Users from backup JSON before enhanced restore
  - Manual fallback: restores UserRoles/Documents if enhanced pipeline did not recreate them
  - Restores storage directories from the archive
  - Returns post‑restore counts: users_restored, userroles_restored, documents_restored
- CLI:
  - restore_from_package supports --with-reinit (guarded, destructive); runs system_reinit then restore

## Typical flows

### A) Normal restore (no reinit)
- Frontend:
  1. Admin → Backup & Restore → “Restore from Migration Package”
  2. Upload package and submit
  3. System restores into current state using existing logic
- CLI:
  - docker compose exec backend python manage.py restore_from_package /path/to/pkg.tar.gz --type database --confirm

### B) Catastrophic recovery — reinit then restore (recommended)
- CLI (preferred for DR):
  - docker compose exec backend python manage.py restore_from_package /path/to/pkg.tar.gz --type full --with-reinit --confirm --skip-interactive
- Frontend (admin‑only, guarded):
  1. Login as admin
  2. Admin → Backup & Restore → “Restore from Migration Package”
  3. Check “Restore into clean system (reinit first)”
  4. Type: RESTORE CLEAN
  5. Upload package and submit
  6. Response includes counts: users_restored, userroles_restored, documents_restored

## Package requirements
To fully restore into a clean system, the migration package must include:
- database/database_backup.json with:
  - users.user (or auth.user) — user records
  - users.role — core roles (7 roles typical)
  - users.userrole — role assignments
  - documents.document — documents
  - documents.documenttype, documents.documentsource — supporting lookups
- storage/ — if you want file binaries rehydrated (FULL backup)
- configuration/ — optional deployment metadata/settings

## Backend log signals to look for (with_reinit)
- WITH-REINIT: extracting archive and preparing enhanced restore…
- WITH-REINIT: archive extracted to …
- WITH-REINIT: found database json at …
- WITH-REINIT: pre-created N users from backup
- WITH-REINIT: enhanced restore completed: True
- WITH-REINIT: manual UserRole restore created N records (fallback case)
- WITH-REINIT: manual Document restore created M records (fallback case)
- WITH-REINIT: restored directory storage -> /app/storage (etc.)

## Security & safeguards
- Reinit is destructive; guarded in both CLI and API with explicit confirmation
- Frontend reinit option is admin‑only and requires typed confirmation
- API enforces is_staff and reinit_confirm == "RESTORE CLEAN"

## Validation checklist
- After restore:
  - Users restored (author01, reviewer01, viewer01, approver01, admin01, plus admin + edms_system)
  - UserRoles restored (5 assignments from package)
  - Documents restored with correct author/type/source; files exist if package included storage
  - API response includes counts: users_restored > 0, userroles_restored > 0, documents_restored >= 0

## Notes
- If a package lacks users.user or users.userrole, UserRoles cannot be restored. Verify package contents before restore.
- For large packages, the enhanced pipeline returns after processing; logs give detailed steps for debugging.

## Change summary
- Frontend — BackupManagement.tsx: admin‑only reinit toggle, confirmation prompt, Authorization for restore, sends with_reinit and reinit_confirm
- Backend — api_views.py: guarded with_reinit support; pre‑create users, enhanced pipeline, manual fallback for roles/docs, storage rehydration, response counts and detailed logs
- Backend — management/commands/restore_from_package.py: supports --with-reinit for CLI

## Recommended operations
- Use CLI with --with-reinit for disaster recovery (auditable, explicit)
- Use frontend with reinit toggle for admin‑initiated recovery with typed confirmation
- Keep off‑site FULL exports for file rehydration (storage included)

## Support
- For issues, collect:
  - API response payload
  - Backend logs (WITH-REINIT section)
  - Counts for users, userroles, documents
  - Package structure (database_backup.json presence and content)
