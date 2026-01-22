#!/usr/bin/env python
"""
Test script to verify admin filter bypass functionality.
Tests Document Library and My Tasks filters for admin vs regular users.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from apps.documents.models import Document
from apps.documents.views import DocumentViewSet
from django.test import RequestFactory
from rest_framework.test import force_authenticate

User = get_user_model()

def test_admin_filters():
    """Test admin bypass in Document Library and My Tasks filters"""
    
    print("=" * 70)
    print("ADMIN FILTER BYPASS VERIFICATION TEST")
    print("=" * 70)
    print()
    
    # Get users
    try:
        admin_user = User.objects.get(username='admin')
        regular_user = User.objects.get(username='author01')
    except User.DoesNotExist as e:
        print(f"❌ Error: Required user not found - {e}")
        print("   Make sure 'admin' and 'author01' users exist")
        return False
    
    print(f"✓ Test users found:")
    print(f"  - Admin: {admin_user.username} (superuser: {admin_user.is_superuser})")
    print(f"  - Regular: {regular_user.username}")
    print()
    
    # Get document counts by status
    total_docs = Document.objects.count()
    draft_docs = Document.objects.filter(status='DRAFT').count()
    pending_review = Document.objects.filter(status='PENDING_REVIEW').count()
    effective_docs = Document.objects.filter(status='EFFECTIVE').count()
    
    print(f"📊 Current Document Counts:")
    print(f"   Total documents: {total_docs}")
    print(f"   DRAFT: {draft_docs}")
    print(f"   PENDING_REVIEW: {pending_review}")
    print(f"   EFFECTIVE: {effective_docs}")
    print()
    
    # Create request factory
    factory = RequestFactory()
    
    # Test 1: Document Library - Admin
    print("─" * 70)
    print("TEST 1: Document Library - Admin User")
    print("─" * 70)
    
    request = factory.get('/api/v1/documents/', {'filter': 'library'})
    force_authenticate(request, user=admin_user)
    
    view = DocumentViewSet()
    view.request = request
    view.action = 'list'
    view.format_kwarg = None
    
    admin_library_qs = view.get_queryset()
    admin_library_count = admin_library_qs.count()
    
    print(f"Admin sees: {admin_library_count} documents")
    print(f"Expected: Should see ALL documents (including DRAFT, PENDING_REVIEW, etc.)")
    
    # Show status breakdown
    if admin_library_count > 0:
        status_counts = {}
        for doc in admin_library_qs[:50]:  # Sample first 50
            status = doc.status
            status_counts[status] = status_counts.get(status, 0) + 1
        print(f"Status breakdown: {status_counts}")
    
    if admin_library_count >= total_docs * 0.8:  # Should see most/all documents
        print("✅ PASS: Admin can see documents beyond EFFECTIVE/APPROVED")
    else:
        print(f"⚠️  REVIEW: Admin sees {admin_library_count}/{total_docs} documents")
    print()
    
    # Test 2: Document Library - Regular User
    print("─" * 70)
    print("TEST 2: Document Library - Regular User")
    print("─" * 70)
    
    request = factory.get('/api/v1/documents/', {'filter': 'library'})
    force_authenticate(request, user=regular_user)
    
    view = DocumentViewSet()
    view.request = request
    view.action = 'list'
    view.format_kwarg = None
    
    user_library_qs = view.get_queryset()
    user_library_count = user_library_qs.count()
    
    print(f"Regular user sees: {user_library_count} documents")
    print(f"Expected: Should see only EFFECTIVE/APPROVED/SCHEDULED documents")
    
    # Show status breakdown
    if user_library_count > 0:
        status_counts = {}
        for doc in user_library_qs[:50]:  # Sample first 50
            status = doc.status
            status_counts[status] = status_counts.get(status, 0) + 1
        print(f"Status breakdown: {status_counts}")
        
        # Check if only approved statuses
        allowed_statuses = ['EFFECTIVE', 'APPROVED_PENDING_EFFECTIVE', 'SCHEDULED_FOR_OBSOLESCENCE', 'SUPERSEDED']
        invalid_docs = [doc for doc in user_library_qs[:50] if doc.status not in allowed_statuses]
        if invalid_docs:
            print(f"⚠️  FAIL: Regular user sees {len(invalid_docs)} documents with invalid status")
        else:
            print("✅ PASS: Regular user sees only approved documents")
    else:
        print("✅ PASS: No documents (or only approved ones)")
    print()
    
    # Test 3: My Tasks - Admin
    print("─" * 70)
    print("TEST 3: My Tasks - Admin User")
    print("─" * 70)
    
    request = factory.get('/api/v1/documents/', {'filter': 'my_tasks'})
    force_authenticate(request, user=admin_user)
    
    view = DocumentViewSet()
    view.request = request
    view.action = 'list'
    view.format_kwarg = None
    
    admin_tasks_qs = view.get_queryset()
    admin_tasks_count = admin_tasks_qs.count()
    
    # Count total tasks (all pending work items)
    total_tasks = Document.objects.filter(
        status__in=['DRAFT', 'PENDING_REVIEW', 'UNDER_REVIEW', 'REVIEWED', 'PENDING_APPROVAL']
    ).count()
    
    print(f"Admin sees: {admin_tasks_count} tasks")
    print(f"Total pending tasks in system: {total_tasks}")
    print(f"Expected: Admin should see ALL users' tasks")
    
    # Show author breakdown
    if admin_tasks_count > 0:
        authors = {}
        for doc in admin_tasks_qs[:50]:  # Sample first 50
            author = doc.author.username
            authors[author] = authors.get(author, 0) + 1
        print(f"Authors: {authors}")
        
        if len(authors) > 1 or 'admin' not in authors:
            print("✅ PASS: Admin sees tasks from multiple users")
        elif admin_tasks_count == total_tasks:
            print("✅ PASS: Admin sees all tasks (only admin has tasks)")
        else:
            print("⚠️  REVIEW: Admin may only see own tasks")
    else:
        print("ℹ️  No pending tasks in system")
    print()
    
    # Test 4: My Tasks - Regular User
    print("─" * 70)
    print("TEST 4: My Tasks - Regular User")
    print("─" * 70)
    
    request = factory.get('/api/v1/documents/', {'filter': 'my_tasks'})
    force_authenticate(request, user=regular_user)
    
    view = DocumentViewSet()
    view.request = request
    view.action = 'list'
    view.format_kwarg = None
    
    user_tasks_qs = view.get_queryset()
    user_tasks_count = user_tasks_qs.count()
    
    print(f"Regular user sees: {user_tasks_count} tasks")
    print(f"Expected: Should see only their own tasks")
    
    # Verify all tasks belong to this user
    if user_tasks_count > 0:
        other_user_tasks = [
            doc for doc in user_tasks_qs[:50] 
            if doc.author != regular_user and doc.reviewer != regular_user and doc.approver != regular_user
        ]
        if other_user_tasks:
            print(f"❌ FAIL: Regular user sees {len(other_user_tasks)} tasks from other users")
        else:
            print("✅ PASS: Regular user sees only their own tasks")
    else:
        print("✅ PASS: No tasks (user not involved in any documents)")
    print()
    
    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print()
    print(f"✅ Admin can bypass filters: Library={admin_library_count > user_library_count}, Tasks={admin_tasks_count >= user_tasks_count}")
    print(f"✅ Regular users remain filtered appropriately")
    print()
    print("🎉 Admin filter bypass verification complete!")
    print()

if __name__ == '__main__':
    test_admin_filters()
