# 🧪 Local Testing Guide

## Access Points

### Frontend
- **URL:** http://localhost:3000
- **Status:** ✅ Running

### Backend API
- **URL:** http://localhost:8000
- **Admin:** http://localhost:8000/admin
- **Status:** ✅ Running

---

## 👥 User Credentials

| User | Password | Role |
|------|----------|------|
| author01 | `Author01!` | Author |
| reviewer01 | `Reviewer01!` | Reviewer |
| approver01 | `Approver01!` | Approver |
| admin | `admin123` | Admin |

---

## ✅ Test Checklist

### Basic Tests
- [ ] Login as author01
- [ ] View dashboard
- [ ] See document POL-2026-0002-v01.00
- [ ] Click on document to view details

### Workflow Tests
- [ ] Submit document for review (as author01)
- [ ] Logout, login as reviewer01
- [ ] Check notifications (should have 1 task)
- [ ] Start review
- [ ] Complete review with approval
- [ ] Logout, login as author01
- [ ] Route document for approval
- [ ] Logout, login as approver01
- [ ] Check notifications (should have 1 task)
- [ ] Approve document with effective date
- [ ] Verify final status: APPROVED_PENDING_EFFECTIVE

### Admin Panel Tests
- [ ] Login to admin: http://localhost:8000/admin
- [ ] View documents
- [ ] View users
- [ ] View workflows
- [ ] Create new document (workaround for UI)

---

## 🎬 Step-by-Step Workflow Test

### Phase 1: Submit for Review (Author)
1. Login: http://localhost:3000
   - Username: `author01`
   - Password: `Author01!`
2. Click on document **POL-2026-0002-v01.00**
3. Look for "Submit for Review" or "Actions" button
4. Click and add comment: "Ready for review"
5. Confirm submission
6. Status should change to **PENDING_REVIEW**

### Phase 2: Review Document (Reviewer)
1. Logout from author01
2. Login as `reviewer01` / `Reviewer01!`
3. Check notifications icon (should show 1)
4. Click on notification or find document
5. Click "Start Review" button
6. Review the document
7. Click "Complete Review"
8. Select "Approve" and add comment
9. Status should change to **REVIEWED**

### Phase 3: Route for Approval (Author)
1. Logout from reviewer01
2. Login as `author01` / `Author01!`
3. Open the document (now shows REVIEWED)
4. Click "Route for Approval"
5. Select approver: `approver01`
6. Add comment: "Please approve"
7. Status should change to **PENDING_APPROVAL**

### Phase 4: Approve Document (Approver)
1. Logout from author01
2. Login as `approver01` / `Approver01!`
3. Check notifications (should show 1)
4. Open the document
5. Click "Approve" button
6. Select "Approve" (not reject)
7. Set effective date (e.g., tomorrow)
8. Add comment: "Approved!"
9. Final status: **APPROVED_PENDING_EFFECTIVE** ✅

---

## 🐛 Troubleshooting

### Issue: Can't login
**Solution:** Check services running
```bash
docker compose ps
```

### Issue: Frontend shows error
**Solution:** Check backend is running
```bash
curl http://localhost:8000/health/
```

### Issue: No notifications appearing
**Solution:** Wait 30-60 seconds (polling interval)

### Issue: Button is disabled
**Possible causes:**
- Wrong user (check if you're the assigned person)
- Document in wrong state
- Missing permissions

### Issue: Want to create new document
**Solution:** Use admin panel
1. Go to http://localhost:8000/admin
2. Login: admin / admin123
3. Documents → Add Document

---

## 📊 What to Check

### Dashboard
- [ ] Shows list of documents
- [ ] Shows document status
- [ ] Shows notifications badge

### Document Detail View
- [ ] Shows document metadata
- [ ] Shows current status
- [ ] Shows available actions
- [ ] Shows workflow history

### Notifications
- [ ] Updates every 30-60 seconds
- [ ] Shows count in badge
- [ ] Lists pending tasks
- [ ] Links to documents

### Workflow Actions
- [ ] Submit for Review (author)
- [ ] Start Review (reviewer)
- [ ] Complete Review (reviewer)
- [ ] Route for Approval (author)
- [ ] Approve/Reject (approver)

---

## 🎉 Success Criteria

You've successfully tested the app if:
✅ Logged in as all 4 users
✅ Submitted document for review
✅ Completed review as reviewer
✅ Routed for approval as author
✅ Approved document as approver
✅ Document reaches APPROVED_PENDING_EFFECTIVE status

---

## 📸 Take Screenshots!

Capture these screens:
1. Login page
2. Dashboard with documents
3. Document detail view
4. Submit for review dialog
5. Reviewer's notification
6. Review completion
7. Approval dialog
8. Final approved status

---

## 💡 Tips

- **Use multiple browsers** or incognito windows to stay logged in as different users
- **Check the browser console** (F12) if something doesn't work
- **Notifications update every 30-60 seconds** - be patient
- **The "unhealthy" status for Celery is cosmetic** - services work fine
- **Document creation UI is broken** - use admin panel workaround

---

**Ready to test? Open http://localhost:3000 and login as author01!** 🚀
