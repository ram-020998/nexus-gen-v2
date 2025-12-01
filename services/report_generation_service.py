"""
Report Generation Service

Generates comprehensive merge reports in PDF and Word formats.
Includes session information, statistics, and detailed change lists.
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

from core.base_service import BaseService
from models import db, MergeSession, Change, Package, ObjectVersion


class ReportGenerationService(BaseService):
    """
    Service for generating merge reports.

    Provides methods for:
    - Generating Excel reports
    - Caching generated reports
    - Including comprehensive session data

    Reports include:
    - Session Information
    - Package Information
    - Statistics (by classification, by object type)
    - Detailed Change List with SAIL code

    Example:
        >>> service = ReportGenerationService()
        >>> report_path = service.generate_report('MS_ABC123', format='xlsx')
        >>> print(f"Report generated: {report_path}")
    """

    def __init__(self, container=None):
        """Initialize service with dependencies."""
        super().__init__(container)
        self.logger = logging.getLogger(__name__)
        self.reports_dir = 'outputs/reports'
        self._ensure_reports_directory()

    def _initialize_dependencies(self) -> None:
        """Initialize service dependencies."""
        pass

    def _ensure_reports_directory(self) -> None:
        """Ensure the reports directory exists."""
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
            self.logger.info(f"Created reports directory: {self.reports_dir}")

    def generate_report(
        self,
        reference_id: str,
        format: str = 'xlsx'
    ) -> str:
        """
        Generate a merge report.

        Args:
            reference_id: Session reference ID
            format: Report format ('xlsx' only)

        Returns:
            Path to generated report file

        Raises:
            ValueError: If session not found or format invalid

        Example:
            >>> report_path = service.generate_report(
            ...     'MS_ABC123', format='xlsx'
            ... )
        """
        # Validate format
        if format not in ['xlsx']:
            raise ValueError(
                f"Invalid format: {format}. Must be 'xlsx'"
            )

        # Check cache first
        cached_path = self._get_cached_report_path(reference_id, format)
        if cached_path and os.path.exists(cached_path):
            # Check if cache is still valid (less than 1 hour old)
            cache_age = (
                datetime.now().timestamp() - os.path.getmtime(cached_path)
            )
            if cache_age < 3600:  # 1 hour in seconds
                self.logger.info(
                    f"Using cached report for {reference_id} "
                    f"(age: {int(cache_age/60)} minutes)"
                )
                return cached_path

        # Get session
        session = db.session.query(MergeSession).filter_by(
            reference_id=reference_id
        ).first()

        if not session:
            raise ValueError(f"Session not found: {reference_id}")

        # Gather report data
        data = self._gather_report_data(session)

        # Generate Excel report
        report_path = self._generate_excel_report(session, data)

        self.logger.info(
            f"Generated {format.upper()} report for {reference_id}: "
            f"{report_path}"
        )

        return report_path

    def _get_cached_report_path(
        self,
        reference_id: str,
        format: str
    ) -> str:
        """
        Get the path to a cached report.

        Args:
            reference_id: Session reference ID
            format: Report format

        Returns:
            Path to cached report file
        """
        filename = f"{reference_id}_report.{format}"
        return os.path.join(self.reports_dir, filename)

    def _gather_report_data(self, session: MergeSession) -> Dict[str, Any]:
        """
        Gather all data needed for report generation.

        Args:
            session: Merge session

        Returns:
            Dict containing all report data
        """
        # Get packages
        packages = db.session.query(Package).filter_by(
            session_id=session.id
        ).all()

        package_info = {}
        for pkg in packages:
            package_info[pkg.package_type] = {
                'filename': pkg.filename,
                'total_objects': pkg.total_objects
            }

        # Get changes with object details
        changes = db.session.query(Change).filter_by(
            session_id=session.id
        ).order_by(Change.display_order).all()

        change_list = []
        for change in changes:
            obj = change.object

            # Get SAIL code from vendor version if available
            vendor_pkg = next(
                (p for p in packages if p.package_type == 'new_vendor'),
                None
            )
            sail_code = None
            if vendor_pkg:
                version = db.session.query(ObjectVersion).filter_by(
                    object_id=obj.id,
                    package_id=vendor_pkg.id
                ).first()
                if version:
                    sail_code = version.sail_code

            change_list.append({
                'display_order': change.display_order,
                'object_name': obj.name,
                'object_uuid': obj.uuid,
                'object_type': obj.object_type,
                'description': obj.description,
                'classification': change.classification,
                'vendor_change_type': change.vendor_change_type,
                'customer_change_type': change.customer_change_type,
                'status': change.status,
                'notes': change.notes,
                'sail_code': sail_code
            })

        # Calculate statistics
        stats = self._calculate_statistics(session, changes)

        return {
            'session': session,
            'packages': package_info,
            'changes': change_list,
            'statistics': stats
        }

    def _calculate_statistics(
        self,
        session: MergeSession,
        changes: list
    ) -> Dict[str, Any]:
        """
        Calculate statistics for the report.

        Args:
            session: Merge session
            changes: List of Change objects

        Returns:
            Dict containing statistics
        """
        # Classification breakdown
        by_classification = {}
        classifications = ['NO_CONFLICT', 'CONFLICT', 'NEW', 'DELETED']
        for classification in classifications:
            count = sum(
                1 for c in changes if c.classification == classification
            )
            by_classification[classification] = count

        # Object type breakdown
        by_object_type = {}
        for change in changes:
            obj_type = change.object.object_type
            by_object_type[obj_type] = by_object_type.get(obj_type, 0) + 1

        # Status breakdown
        by_status = {}
        for status in ['pending', 'reviewed', 'skipped']:
            count = sum(1 for c in changes if c.status == status)
            by_status[status] = count

        return {
            'total_changes': session.total_changes,
            'reviewed_count': session.reviewed_count,
            'skipped_count': session.skipped_count,
            'pending_count': (
                session.total_changes -
                session.reviewed_count -
                session.skipped_count
            ),
            'by_classification': by_classification,
            'by_object_type': by_object_type,
            'by_status': by_status,
            'estimated_complexity': session.estimated_complexity,
            'estimated_time_hours': session.estimated_time_hours
        }

    def _generate_excel_report(
        self,
        session: MergeSession,
        data: Dict[str, Any]
    ) -> str:
        """
        Generate Excel report using openpyxl.

        Args:
            session: Merge session
            data: Report data

        Returns:
            Path to generated Excel file
        """
        # Create workbook
        wb = Workbook()

        # Create sheets
        self._create_summary_sheet(wb, session, data)
        self._create_changes_sheet(wb, session, data)

        # Remove default sheet if it exists
        if 'Sheet' in wb.sheetnames:
            wb.remove(wb['Sheet'])

        # Save workbook
        report_path = self._get_cached_report_path(
            session.reference_id,
            'xlsx'
        )
        wb.save(report_path)

        return report_path

    def _create_summary_sheet(
        self,
        wb: Workbook,
        session: MergeSession,
        data: Dict[str, Any]
    ) -> None:
        """Create summary sheet with session and package information."""
        ws = wb.active
        ws.title = 'Summary'

        # Title
        ws['A1'] = 'Three-Way Merge Analysis Report'
        ws['A1'].font = Font(bold=True, size=16)
        ws.merge_cells('A1:B1')

        # Session Information
        row = 3
        ws[f'A{row}'] = 'Session Information'
        ws[f'A{row}'].font = Font(bold=True, size=14)
        row += 1

        session_data = [
            ('Reference ID', session.reference_id),
            ('Status', session.status),
            ('Created', session.created_at.strftime('%Y-%m-%d %H:%M:%S')),
            ('Total Changes', session.total_changes),
            ('Estimated Complexity', session.estimated_complexity or 'N/A'),
            (
                'Estimated Time',
                f"{session.estimated_time_hours or 0} hours"
            )
        ]

        for label, value in session_data:
            ws[f'A{row}'] = label
            ws[f'A{row}'].font = Font(bold=True)
            ws[f'B{row}'] = value
            row += 1

        # Package Information
        row += 1
        ws[f'A{row}'] = 'Package Information'
        ws[f'A{row}'].font = Font(bold=True, size=14)
        row += 1

        packages = data['packages']
        for pkg_type in ['base', 'customized', 'new_vendor']:
            if pkg_type in packages:
                pkg = packages[pkg_type]
                ws[f'A{row}'] = pkg_type.replace('_', ' ').title()
                ws[f'A{row}'].font = Font(bold=True)
                row += 1
                ws[f'A{row}'] = '  Filename'
                ws[f'B{row}'] = pkg['filename']
                row += 1
                ws[f'A{row}'] = '  Total Objects'
                ws[f'B{row}'] = pkg['total_objects']
                row += 1

        # Statistics
        stats = data['statistics']
        row += 1
        ws[f'A{row}'] = 'Statistics'
        ws[f'A{row}'].font = Font(bold=True, size=14)
        row += 1

        # Progress
        ws[f'A{row}'] = 'Progress'
        ws[f'A{row}'].font = Font(bold=True)
        row += 1

        progress_data = [
            ('Total Changes', stats['total_changes']),
            ('Reviewed', stats['reviewed_count']),
            ('Skipped', stats['skipped_count']),
            ('Pending', stats['pending_count'])
        ]

        for label, value in progress_data:
            ws[f'A{row}'] = f'  {label}'
            ws[f'B{row}'] = value
            row += 1

        # Classification breakdown
        row += 1
        ws[f'A{row}'] = 'By Classification'
        ws[f'A{row}'].font = Font(bold=True)
        row += 1

        classifications = [
            ('NO_CONFLICT', 'No Conflict'),
            ('CONFLICT', 'Conflict'),
            ('NEW', 'New'),
            ('DELETED', 'Deleted')
        ]

        for key, label in classifications:
            ws[f'A{row}'] = f'  {label}'
            ws[f'B{row}'] = stats['by_classification'].get(key, 0)
            row += 1

        # Object type breakdown
        row += 1
        ws[f'A{row}'] = 'By Object Type'
        ws[f'A{row}'].font = Font(bold=True)
        row += 1

        obj_types = sorted(
            stats['by_object_type'].items(),
            key=lambda x: x[1],
            reverse=True
        )

        for obj_type, count in obj_types:
            ws[f'A{row}'] = f'  {obj_type}'
            ws[f'B{row}'] = count
            row += 1

        # Adjust column widths
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 50

    def _create_changes_sheet(
        self,
        wb: Workbook,
        session: MergeSession,
        data: Dict[str, Any]
    ) -> None:
        """Create changes sheet with detailed change list."""
        ws = wb.create_sheet('Changes')

        # Header style
        header_fill = PatternFill(
            start_color='366092',
            end_color='366092',
            fill_type='solid'
        )
        header_font = Font(bold=True, color='FFFFFF', size=11)

        # Headers
        headers = [
            'Change #',
            'Object Name',
            'Object Type',
            'UUID',
            'Classification',
            'Vendor Change',
            'Customer Change',
            'Status',
            'Description',
            'Notes',
            'SAIL Code'
        ]

        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')

        # Add changes
        changes = data['changes']
        for row, change in enumerate(changes, 2):
            ws.cell(row=row, column=1).value = change['display_order']
            ws.cell(row=row, column=2).value = change['object_name']
            ws.cell(row=row, column=3).value = change['object_type']
            ws.cell(row=row, column=4).value = change['object_uuid']
            ws.cell(row=row, column=5).value = change['classification']
            ws.cell(
                row=row, column=6
            ).value = change['vendor_change_type'] or 'N/A'
            ws.cell(
                row=row, column=7
            ).value = change['customer_change_type'] or 'N/A'
            ws.cell(row=row, column=8).value = change['status']
            ws.cell(
                row=row, column=9
            ).value = change['description'] or 'N/A'
            ws.cell(row=row, column=10).value = change['notes'] or ''

            # Add SAIL code (truncated to 500 chars)
            if change['sail_code']:
                sail_code = change['sail_code'][:500]
                if len(change['sail_code']) > 500:
                    sail_code += '...'
                ws.cell(row=row, column=11).value = sail_code
            else:
                ws.cell(row=row, column=11).value = ''

        # Adjust column widths
        column_widths = [10, 30, 20, 40, 15, 15, 15, 12, 40, 30, 50]
        for col, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = width

        # Freeze header row
        ws.freeze_panes = 'A2'

    def clear_cache(self, reference_id: Optional[str] = None) -> None:
        """
        Clear cached reports.

        Args:
            reference_id: If provided, clear only reports for this session.
                         If None, clear all cached reports.

        Example:
            >>> service.clear_cache('MS_ABC123')  # Clear specific
            >>> service.clear_cache()  # Clear all cached reports
        """
        if reference_id:
            # Clear specific session reports
            for format in ['xlsx']:
                report_path = self._get_cached_report_path(
                    reference_id, format
                )
                if os.path.exists(report_path):
                    os.remove(report_path)
                    self.logger.info(f"Cleared cached report: {report_path}")
        else:
            # Clear all reports
            if os.path.exists(self.reports_dir):
                for filename in os.listdir(self.reports_dir):
                    file_path = os.path.join(self.reports_dir, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        self.logger.info(
                            f"Cleared cached report: {file_path}"
                        )
