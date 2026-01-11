"""
Management command to detect and analyze circular dependencies in the document system.

This command helps identify existing circular dependencies and provides
detailed reports for system administrators.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.documents.models import Document, DocumentDependency
import json


class Command(BaseCommand):
    help = 'Detect and analyze circular dependencies in the document system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Automatically fix circular dependencies by deactivating problematic ones',
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output results to JSON file',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed dependency chains',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 Analyzing document dependency system for circular dependencies...'))
        self.stdout.write('   Using base document number approach for version-aware detection')
        
        # Detect circular dependencies using base number approach
        cycles = DocumentDependency.detect_circular_dependencies()
        
        if not cycles:
            self.stdout.write(self.style.SUCCESS('✅ No circular dependencies detected!'))
            return

        # Report findings
        self.stdout.write(self.style.WARNING(f'⚠️  Found {len(cycles)} circular dependency chain(s):'))
        
        results = {
            'total_cycles': len(cycles),
            'cycles': [],
            'affected_document_families': set(),
            'affected_documents': set(),
            'recommendations': []
        }
        
        for i, cycle in enumerate(cycles):
            self.stdout.write(f'\n📄 Circular Dependency Chain #{i + 1} (Document Families):')
            
            cycle_info = {
                'chain_id': i + 1,
                'base_document_numbers': cycle,
                'affected_documents': [],
                'dependency_details': []
            }
            
            # Show base document numbers in the cycle
            self.stdout.write(f'   🔗 Base Document Chain: {" → ".join(cycle)}')
            
            # Get all actual documents involved in this circular dependency
            for base_number in cycle:
                results['affected_document_families'].add(base_number)
                
                # Find all versions of this document family
                matching_docs = Document.objects.filter(
                    document_number__startswith=base_number,
                    is_active=True
                ).values('id', 'document_number', 'title', 'status')
                
                if matching_docs:
                    self.stdout.write(f'\n   📋 Document Family: {base_number}')
                    for doc in matching_docs:
                        cycle_info['affected_documents'].append({
                            'id': doc['id'],
                            'document_number': doc['document_number'],
                            'title': doc['title'],
                            'status': doc['status']
                        })
                        results['affected_documents'].add(doc['id'])
                        self.stdout.write(f'      • {doc["document_number"]} - {doc["title"]} ({doc["status"]})')
                else:
                    self.stdout.write(self.style.ERROR(f'   ❌ No documents found for base number: {base_number}'))
            
            # Show dependency details if verbose
            if options['verbose']:
                self.stdout.write(f'   🔗 Actual dependencies in this circular chain:')
                
                # Find actual dependencies between document families in the cycle
                for j in range(len(cycle)):
                    current_base = cycle[j]
                    next_base = cycle[(j + 1) % len(cycle)]  # Loop back to start
                    
                    # Find dependencies from current_base family to next_base family
                    dependencies = DocumentDependency.objects.filter(
                        is_active=True,
                        document__document_number__startswith=current_base,
                        depends_on__document_number__startswith=next_base
                    ).select_related('document', 'depends_on')
                    
                    if dependencies:
                        self.stdout.write(f'\n      📎 {current_base} → {next_base}:')
                        for dep in dependencies:
                            dep_detail = {
                                'from_doc': dep.document.document_number,
                                'to_doc': dep.depends_on.document_number,
                                'dependency_type': dep.dependency_type,
                                'is_critical': dep.is_critical,
                                'created_at': dep.created_at.isoformat(),
                            }
                            
                            cycle_info['dependency_details'].append(dep_detail)
                            
                            self.stdout.write(
                                f'         • {dep.document.document_number} '
                                f'({dep.get_dependency_type_display()}) '
                                f'→ {dep.depends_on.document_number}'
                                f'{" [CRITICAL]" if dep.is_critical else ""}'
                            )
                    else:
                        self.stdout.write(f'\n      📎 {current_base} → {next_base}: No direct dependencies found')
                        self.stdout.write(f'         (May be part of longer chain through other document families)')
            
            results['cycles'].append(cycle_info)
        
        # Convert set to list for JSON serialization
        results['affected_documents'] = list(results['affected_documents'])
        
        # Generate recommendations
        self._generate_recommendations(results, cycles)
        
        # Auto-fix if requested
        if options['fix']:
            self._auto_fix_dependencies(cycles)
        
        # Save to file if requested
        if options['output']:
            self._save_results(results, options['output'])
        
        # Summary
        self.stdout.write(f'\n📊 Summary:')
        self.stdout.write(f'   • Total circular dependency chains: {len(cycles)}')
        self.stdout.write(f'   • Total affected document families: {len(results["affected_document_families"])}')
        self.stdout.write(f'   • Total affected individual documents: {len(results["affected_documents"])}')
        self.stdout.write(f'   • Total active dependencies in system: {DocumentDependency.objects.filter(is_active=True).count()}')
        self.stdout.write(f'   • Detection method: Base document number (version-aware)')
        
        if not options['fix']:
            self.stdout.write(f'\n💡 To automatically fix these issues, run:')
            self.stdout.write(f'   python manage.py check_circular_dependencies --fix')

    def _generate_recommendations(self, results, cycles):
        """Generate recommendations for fixing circular dependencies."""
        recommendations = []
        
        for i, cycle in enumerate(cycles):
            chain_recommendations = []
            
            # Analyze cycle to suggest which dependency to break
            if len(cycle) == 3:  # Simple A→B→A cycle
                chain_recommendations.append(
                    "Consider breaking the newest dependency or the non-critical one"
                )
            elif len(cycle) > 3:  # Complex cycle
                chain_recommendations.append(
                    "Consider breaking dependencies that are not critical to operations"
                )
            
            # Check for critical dependencies in cycle
            critical_deps = []
            for j in range(len(cycle) - 1):
                try:
                    dep = DocumentDependency.objects.get(
                        document_id=cycle[j],
                        depends_on_id=cycle[j + 1],
                        is_active=True
                    )
                    if dep.is_critical:
                        critical_deps.append(f"{dep.document.document_number}→{dep.depends_on.document_number}")
                except DocumentDependency.DoesNotExist:
                    pass
            
            if critical_deps:
                chain_recommendations.append(
                    f"Critical dependencies found: {', '.join(critical_deps)}. "
                    "Review business requirements before making changes."
                )
            
            recommendations.append({
                'chain_id': i + 1,
                'suggestions': chain_recommendations
            })
        
        results['recommendations'] = recommendations
        
        self.stdout.write(f'\n💡 Recommendations:')
        for rec in recommendations:
            self.stdout.write(f'   Chain #{rec["chain_id"]}:')
            for suggestion in rec['suggestions']:
                self.stdout.write(f'      • {suggestion}')

    def _auto_fix_dependencies(self, cycles):
        """Automatically fix circular dependencies by deactivating problematic ones."""
        self.stdout.write(self.style.WARNING('\n🔧 Auto-fixing circular dependencies...'))
        
        fixed_count = 0
        
        with transaction.atomic():
            for i, cycle in enumerate(cycles):
                self.stdout.write(f'\n   Fixing chain #{i + 1}:')
                
                # Strategy: Deactivate the newest non-critical dependency in each cycle
                dependencies_in_cycle = []
                
                for j in range(len(cycle) - 1):
                    try:
                        dep = DocumentDependency.objects.get(
                            document_id=cycle[j],
                            depends_on_id=cycle[j + 1],
                            is_active=True
                        )
                        dependencies_in_cycle.append(dep)
                    except DocumentDependency.DoesNotExist:
                        pass
                
                if dependencies_in_cycle:
                    # Sort by: non-critical first, then by creation date (newest first)
                    dependencies_in_cycle.sort(key=lambda d: (d.is_critical, -d.created_at.timestamp()))
                    
                    # Deactivate the first (safest) dependency
                    dep_to_fix = dependencies_in_cycle[0]
                    dep_to_fix.is_active = False
                    dep_to_fix.save()
                    
                    fixed_count += 1
                    
                    self.stdout.write(self.style.SUCCESS(
                        f'      ✅ Deactivated dependency: {dep_to_fix.document.document_number} '
                        f'→ {dep_to_fix.depends_on.document_number} '
                        f'({dep_to_fix.get_dependency_type_display()})'
                        f'{" [was CRITICAL]" if dep_to_fix.is_critical else ""}'
                    ))
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Auto-fix completed! Deactivated {fixed_count} dependencies.'))
        self.stdout.write('   Note: Deactivated dependencies can be manually reviewed and reactivated if needed.')

    def _save_results(self, results, filename):
        """Save analysis results to JSON file."""
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            self.stdout.write(self.style.SUCCESS(f'📁 Results saved to {filename}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Failed to save results: {str(e)}'))