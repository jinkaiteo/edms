"""
EDMS Test User Seeding Script

Creates test users with appropriate roles and permissions based on
Dev_Docs/EDMS_Test_Users_Credentials.md

Usage:
    python manage.py seed_test_users [--clear-existing]
"""

import os
import sys
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.contrib.auth.hashers import make_password
from apps.users.models import Role, UserRole

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed test users for EDMS development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing test users before seeding new ones',
        )
        parser.add_argument(
            '--update-passwords',
            action='store_true',
            help='Update passwords for existing users to test123',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🌱 Starting EDMS Test User Seeding...')
        )

        try:
            with transaction.atomic():
                # Clear existing test users if requested
                if options['clear_existing']:
                    self.clear_existing_users()
                
                # Create or update system roles first
                self.create_system_roles()
                
                # Seed test users
                self.seed_test_users(options['update_passwords'])
                
                # Assign roles to users
                self.assign_user_roles()
                
                # Display summary
                self.display_summary()

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error during user seeding: {e}')
            )
            raise CommandError(f'User seeding failed: {e}')

    def clear_existing_users(self):
        """Clear existing test users (except superuser)"""
        self.stdout.write('🧹 Clearing existing test users...')
        
        test_usernames = [
            'viewer01', 'viewer02', 'viewer03',
            'author01', 'author02', 'author03', 'author04',
            'reviewer01', 'reviewer02', 'reviewer03',
            'approver01', 'approver02', 'approver03'
        ]
        
        deleted_count = 0
        for username in test_usernames:
            try:
                user = User.objects.get(username=username)
                if not user.is_superuser:
                    user.delete()
                    deleted_count += 1
                    self.stdout.write(f'   ✅ Deleted user: {username}')
            except User.DoesNotExist:
                continue
        
        self.stdout.write(f'   ✅ Cleared {deleted_count} existing test users')

    def create_system_roles(self):
        """Create system roles for EDMS document management"""
        self.stdout.write('🔧 Creating/updating system roles...')
        
        roles_data = [
            {
                'name': 'Document Viewer',
                'description': 'Can view approved/effective documents only',
                'module': 'O1',
                'permission_level': 'read'
            },
            {
                'name': 'Document Author',
                'description': 'Can create, edit, and submit documents for review',
                'module': 'O1', 
                'permission_level': 'write'
            },
            {
                'name': 'Document Reviewer',
                'description': 'Can review and approve/reject documents during review process',
                'module': 'O1',
                'permission_level': 'review'
            },
            {
                'name': 'Document Approver', 
                'description': 'Can give final approval to documents and set effective dates',
                'module': 'O1',
                'permission_level': 'approve'
            },
            {
                'name': 'Document Admin',
                'description': 'Full administrative access to document management system',
                'module': 'O1',
                'permission_level': 'admin'
            }
        ]
        
        created_roles = 0
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                module=role_data['module'],
                permission_level=role_data['permission_level'],
                defaults={
                    'name': role_data['name'],
                    'description': role_data['description'],
                    'is_system_role': True
                }
            )
            
            if created:
                created_roles += 1
                self.stdout.write(f'   ✅ Created role: {role.name}')
            else:
                # Update existing role
                role.name = role_data['name']
                role.description = role_data['description']
                role.is_system_role = True
                role.save()
                self.stdout.write(f'   🔄 Updated role: {role.name}')
        
        self.stdout.write(f'   ✅ Processed {len(roles_data)} system roles ({created_roles} new)')

    def seed_test_users(self, update_passwords=False):
        """Create test users from credentials file"""
        self.stdout.write('👥 Creating test users...')
        
        # Test users data based on EDMS_Test_Users_Credentials.md
        test_users = [
            # Document Viewers (Read Permission)
            {
                'username': 'viewer01',
                'password': 'test123',
                'email': 'alice.johnson@edmstest.com',
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'department': 'Quality Assurance',
                'role': 'Document Viewer'
            },
            {
                'username': 'viewer02',
                'password': 'test123',
                'email': 'bob.wilson@edmstest.com',
                'first_name': 'Bob',
                'last_name': 'Wilson',
                'department': 'Manufacturing',
                'role': 'Document Viewer'
            },
            {
                'username': 'viewer03',
                'password': 'test123',
                'email': 'carol.davis@edmstest.com',
                'first_name': 'Carol',
                'last_name': 'Davis',
                'department': 'Research',
                'role': 'Document Viewer'
            },
            
            # Document Authors (Write Permission)
            {
                'username': 'author01',
                'password': 'test123',
                'email': 'david.brown@edmstest.com',
                'first_name': 'David',
                'last_name': 'Brown',
                'department': 'Quality Assurance',
                'role': 'Document Author'
            },
            {
                'username': 'author02',
                'password': 'test123',
                'email': 'emma.garcia@edmstest.com',
                'first_name': 'Emma',
                'last_name': 'Garcia',
                'department': 'Regulatory Affairs',
                'role': 'Document Author'
            },
            {
                'username': 'author03',
                'password': 'test123',
                'email': 'frank.miller@edmstest.com',
                'first_name': 'Frank',
                'last_name': 'Miller',
                'department': 'Manufacturing',
                'role': 'Document Author'
            },
            {
                'username': 'author04',
                'password': 'test123',
                'email': 'grace.lee@edmstest.com',
                'first_name': 'Grace',
                'last_name': 'Lee',
                'department': 'Research Development',
                'role': 'Document Author'
            },
            
            # Document Reviewers (Review Permission)
            {
                'username': 'reviewer01',
                'password': 'test123',
                'email': 'henry.taylor@edmstest.com',
                'first_name': 'Henry',
                'last_name': 'Taylor',
                'department': 'Quality Assurance',
                'role': 'Document Reviewer'
            },
            {
                'username': 'reviewer02',
                'password': 'test123',
                'email': 'isabel.martinez@edmstest.com',
                'first_name': 'Isabel',
                'last_name': 'Martinez',
                'department': 'Regulatory Affairs',
                'role': 'Document Reviewer'
            },
            {
                'username': 'reviewer03',
                'password': 'test123',
                'email': 'jack.anderson@edmstest.com',
                'first_name': 'Jack',
                'last_name': 'Anderson',
                'department': 'Manufacturing',
                'role': 'Document Reviewer'
            },
            
            # Document Approvers (Approve Permission)
            {
                'username': 'approver01',
                'password': 'test123',
                'email': 'karen.white@edmstest.com',
                'first_name': 'Karen',
                'last_name': 'White',
                'department': 'Quality Assurance',
                'role': 'Document Approver'
            },
            {
                'username': 'approver02',
                'password': 'test123',
                'email': 'lucas.thompson@edmstest.com',
                'first_name': 'Lucas',
                'last_name': 'Thompson',
                'department': 'Regulatory Affairs',
                'role': 'Document Approver'
            },
            {
                'username': 'approver03',
                'password': 'test123',
                'email': 'maria.rodriguez@edmstest.com',
                'first_name': 'Maria',
                'last_name': 'Rodriguez',
                'department': 'Manufacturing',
                'role': 'Document Approver'
            }
        ]
        
        created_users = 0
        updated_users = 0
        
        for user_data in test_users:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'department': user_data['department'],
                    'password': make_password(user_data['password']),
                    'is_active': True,
                    'is_staff': False,
                    'is_superuser': False,
                    'is_validated': True
                }
            )
            
            if created:
                created_users += 1
                self.stdout.write(f'   ✅ Created user: {user_data["username"]} ({user_data["first_name"]} {user_data["last_name"]})')
            else:
                # Update existing user if needed
                updated = False
                if user.email != user_data['email']:
                    user.email = user_data['email']
                    updated = True
                if user.first_name != user_data['first_name']:
                    user.first_name = user_data['first_name']
                    updated = True
                if user.last_name != user_data['last_name']:
                    user.last_name = user_data['last_name']
                    updated = True
                if user.department != user_data['department']:
                    user.department = user_data['department']
                    updated = True
                
                if update_passwords or not user.has_usable_password():
                    user.password = make_password(user_data['password'])
                    updated = True
                
                if updated:
                    user.save()
                    updated_users += 1
                    self.stdout.write(f'   🔄 Updated user: {user_data["username"]}')
                else:
                    self.stdout.write(f'   ℹ️ User exists: {user_data["username"]}')
        
        self.stdout.write(f'   ✅ Processed {len(test_users)} users ({created_users} new, {updated_users} updated)')

    def assign_user_roles(self):
        """Assign roles to users based on their intended role"""
        self.stdout.write('🔗 Assigning user roles...')
        
        # Role mapping based on user role designation
        role_mapping = {
            'Document Viewer': 'read',
            'Document Author': 'write', 
            'Document Reviewer': 'review',
            'Document Approver': 'approve'
        }
        
        assigned_roles = 0
        
        for user in User.objects.filter(is_superuser=False, is_staff=False):
            # Determine role from user data or username pattern
            role_permission = None
            
            if user.username.startswith('viewer'):
                role_permission = 'read'
            elif user.username.startswith('author'):
                role_permission = 'write'
            elif user.username.startswith('reviewer'):
                role_permission = 'review'
            elif user.username.startswith('approver'):
                role_permission = 'approve'
            
            if role_permission:
                try:
                    role = Role.objects.get(
                        module='O1',  # Document management module
                        permission_level=role_permission
                    )
                    
                    user_role, created = UserRole.objects.get_or_create(
                        user=user,
                        role=role,
                        defaults={
                            'assignment_reason': f'Assigned via test user seeding script',
                            'is_active': True
                        }
                    )
                    
                    if created:
                        assigned_roles += 1
                        self.stdout.write(f'   ✅ Assigned {role.name} to {user.username}')
                    else:
                        self.stdout.write(f'   ℹ️ Role already assigned: {user.username} -> {role.name}')
                        
                except Role.DoesNotExist:
                    self.stdout.write(f'   ⚠️ Role not found: O1/{role_permission} for {user.username}')
        
        self.stdout.write(f'   ✅ Assigned {assigned_roles} new role assignments')

    def display_summary(self):
        """Display summary of created users and roles"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('🎉 EDMS Test User Seeding Complete!'))
        self.stdout.write('='*60)
        
        # Count users by role type
        viewers = User.objects.filter(username__startswith='viewer').count()
        authors = User.objects.filter(username__startswith='author').count() 
        reviewers = User.objects.filter(username__startswith='reviewer').count()
        approvers = User.objects.filter(username__startswith='approver').count()
        superusers = User.objects.filter(is_superuser=True).count()
        
        self.stdout.write(f'\n👥 User Summary:')
        self.stdout.write(f'   • Superusers: {superusers}')
        self.stdout.write(f'   • Document Viewers (read): {viewers}')
        self.stdout.write(f'   • Document Authors (write): {authors}')
        self.stdout.write(f'   • Document Reviewers (review): {reviewers}')
        self.stdout.write(f'   • Document Approvers (approve): {approvers}')
        self.stdout.write(f'   • Total Users: {User.objects.count()}')
        
        # Display role assignments
        role_assignments = UserRole.objects.filter(is_active=True).count()
        self.stdout.write(f'\n🔗 Role Assignments: {role_assignments}')
        
        # Display login credentials
        self.stdout.write(f'\n🔑 Login Credentials:')
        self.stdout.write(f'   • All test users use password: test123')
        self.stdout.write(f'   • Superuser: admin / test123')
        
        # Sample login instructions
        self.stdout.write(f'\n📋 Sample Test Users:')
        self.stdout.write(f'   • Author: author01 / test123 (David Brown, QA)')
        self.stdout.write(f'   • Reviewer: reviewer01 / test123 (Henry Taylor, QA)')
        self.stdout.write(f'   • Approver: approver01 / test123 (Karen White, QA)')
        
        self.stdout.write(f'\n✨ Ready for workflow testing!')
        self.stdout.write(f'   Users can now login and test complete document workflows')
        self.stdout.write(f'   with proper segregation of duties between authors, reviewers, and approvers.')
        self.stdout.write('')