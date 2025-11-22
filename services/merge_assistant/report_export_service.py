"""
Report Export Service

Handles export of merge reports in PDF and JSON formats.
"""
import json
from typing import Dict, Any
from datetime import datetime


class ReportExportService:
    """
    Service for exporting merge reports in various formats

    Provides PDF and JSON export capabilities for merge session reports.
    """

    def __init__(self):
        """Initialize the report export service"""
        pass
    
    def export_json(self, report_data: Dict[str, Any]) -> str:
        """
        Export report as JSON string

        Args:
            report_data: Complete report data dictionary

        Returns:
            JSON string with formatted report data
        """
        # Create a clean export structure
        export_data = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'format_version': '1.0',
                'report_type': 'three_way_merge'
            },
            'session': {
                'reference_id': report_data['session']['reference_id'],
                'status': report_data['session']['status'],
                'created_at': report_data['session']['created_at'],
                'updated_at': report_data['session']['updated_at']
            },
            'packages': report_data['summary']['packages'],
            'statistics': report_data['statistics'],
            'summary': {
                'estimated_complexity': report_data['summary']['estimated_complexity'],
                'estimated_time_hours': report_data['summary']['estimated_time_hours'],
                'breakdown_by_type': report_data['summary']['breakdown_by_type']
            },
            'changes': []
        }

        # Add changes with essential information
        for change in report_data['changes']:
            change_export = {
                'uuid': change.get('uuid'),
                'name': change.get('name'),
                'type': change.get('type'),
                'classification': change.get('classification'),
                'review_status': change.get('review_status'),
                'user_notes': change.get('user_notes'),
                'reviewed_at': change.get('reviewed_at')
            }

            # Add merge guidance if present
            if 'merge_guidance' in change:
                guidance = change['merge_guidance']
                change_export['merge_guidance'] = {
                    'strategy': guidance.get('strategy'),
                    'recommendations': guidance.get('recommendations', [])
                }

            # Add dependencies if present
            if 'dependencies' in change:
                change_export['dependencies'] = change['dependencies']

            export_data['changes'].append(change_export)

        # Add changes by category summary
        changes_by_cat = report_data['changes_by_category']
        export_data['changes_by_category'] = {
            'NO_CONFLICT': len(changes_by_cat['NO_CONFLICT']),
            'CONFLICT': len(changes_by_cat['CONFLICT']),
            'CUSTOMER_ONLY': len(changes_by_cat['CUSTOMER_ONLY']),
            'REMOVED_BUT_CUSTOMIZED': len(
                changes_by_cat['REMOVED_BUT_CUSTOMIZED']
            )
        }

        return json.dumps(export_data, indent=2)
    
    def export_pdf_html(self, report_data: Dict[str, Any]) -> str:
        """
        Generate HTML content for PDF export

        This generates a print-friendly HTML version that can be
        printed to PDF using the browser's print functionality.

        Args:
            report_data: Complete report data dictionary

        Returns:
            HTML string formatted for PDF printing
        """
        session = report_data['session']
        summary = report_data['summary']
        statistics = report_data['statistics']
        changes_by_category = report_data['changes_by_category']

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Merge Report - {session['reference_id']}</title>
    <style>
        @media print {{
            @page {{
                size: A4;
                margin: 2cm;
            }}
            body {{
                font-family: Arial, sans-serif;
                font-size: 10pt;
                line-height: 1.4;
                color: #000;
            }}
            .page-break {{
                page-break-after: always;
            }}
            .no-break {{
                page-break-inside: avoid;
            }}
        }}
        
        body {{
            font-family: Arial, sans-serif;
            max-width: 210mm;
            margin: 0 auto;
            padding: 20px;
            background: white;
            color: #000;
        }}
        
        h1 {{
            color: #5b21b6;
            border-bottom: 3px solid #5b21b6;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        
        h2 {{
            color: #5b21b6;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 8px;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        
        h3 {{
            color: #374151;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            margin: 0;
            border: none;
        }}
        
        .header .subtitle {{
            color: #6b7280;
            font-size: 14px;
            margin-top: 5px;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .info-item {{
            padding: 10px;
            background: #f9fafb;
            border-left: 3px solid #5b21b6;
        }}
        
        .info-label {{
            font-weight: bold;
            color: #374151;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .info-value {{
            color: #000;
            margin-top: 3px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .stat-box {{
            text-align: center;
            padding: 15px;
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 5px;
        }}
        
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #5b21b6;
        }}
        
        .stat-label {{
            font-size: 11px;
            color: #6b7280;
            text-transform: uppercase;
            margin-top: 5px;
        }}
        
        .packages {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding: 15px;
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 5px;
        }}
        
        .package {{
            flex: 1;
            text-align: center;
        }}
        
        .package-label {{
            font-size: 10px;
            color: #6b7280;
            text-transform: uppercase;
            margin-bottom: 5px;
        }}
        
        .package-name {{
            font-weight: bold;
            color: #000;
        }}
        
        .arrow {{
            color: #9ca3af;
            font-size: 20px;
            padding: 0 10px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        
        th {{
            background: #5b21b6;
            color: white;
            padding: 10px;
            text-align: left;
            font-weight: bold;
            font-size: 11px;
        }}
        
        td {{
            padding: 8px 10px;
            border-bottom: 1px solid #e5e7eb;
            font-size: 10px;
        }}
        
        tr:nth-child(even) {{
            background: #f9fafb;
        }}
        
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 9px;
            font-weight: bold;
            text-transform: uppercase;
        }}
        
        .badge-no-conflict {{
            background: #d1fae5;
            color: #065f46;
        }}
        
        .badge-conflict {{
            background: #fee2e2;
            color: #991b1b;
        }}
        
        .badge-customer-only {{
            background: #dbeafe;
            color: #1e40af;
        }}
        
        .badge-removed {{
            background: #fef3c7;
            color: #92400e;
        }}
        
        .badge-reviewed {{
            background: #d1fae5;
            color: #065f46;
        }}
        
        .badge-skipped {{
            background: #fef3c7;
            color: #92400e;
        }}
        
        .badge-pending {{
            background: #e5e7eb;
            color: #374151;
        }}
        
        .notes {{
            font-style: italic;
            color: #6b7280;
            font-size: 9px;
        }}
        
        .footer {{
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #e5e7eb;
            text-align: center;
            color: #6b7280;
            font-size: 9px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Three-Way Merge Report</h1>
        <div class="subtitle">{session['reference_id']}</div>
    </div>
    
    <div class="no-break">
        <h2>Session Information</h2>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Reference ID</div>
                <div class="info-value">{session['reference_id']}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Status</div>
                <div class="info-value">{session['status'].upper()}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Created</div>
                <div class="info-value">{self._format_datetime(session['created_at'])}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Complexity</div>
                <div class="info-value">{summary['estimated_complexity']}</div>
            </div>
        </div>
    </div>
    
    <div class="no-break">
        <h2>Packages</h2>
        <div class="packages">
            <div class="package">
                <div class="package-label">Base Package (A)</div>
                <div class="package-name">{summary['packages']['base']}</div>
            </div>
            <div class="arrow">→</div>
            <div class="package">
                <div class="package-label">Customized Package (B)</div>
                <div class="package-name">{summary['packages']['customized']}</div>
            </div>
            <div class="arrow">→</div>
            <div class="package">
                <div class="package-label">New Vendor Package (C)</div>
                <div class="package-name">{summary['packages']['new_vendor']}</div>
            </div>
        </div>
    </div>
    
    <div class="no-break">
        <h2>Summary Statistics</h2>
        <div class="stats-grid">
            <div class="stat-box">
                <div class="stat-value">{statistics['total_changes']}</div>
                <div class="stat-label">Total Changes</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{statistics['reviewed']}</div>
                <div class="stat-label">Reviewed</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{statistics['skipped']}</div>
                <div class="stat-label">Skipped</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{statistics['conflicts']}</div>
                <div class="stat-label">Conflicts</div>
            </div>
        </div>
    </div>
    
    <div class="page-break"></div>
    
    <h2>Changes by Category</h2>
"""
        
        # Add changes for each category
        categories = [
            ('NO_CONFLICT', 'No Conflicts', 'badge-no-conflict'),
            ('CONFLICT', 'Conflicts', 'badge-conflict'),
            ('CUSTOMER_ONLY', 'Customer Only', 'badge-customer-only'),
            ('REMOVED_BUT_CUSTOMIZED', 'Removed but Customized', 'badge-removed')
        ]
        
        for category_key, category_name, badge_class in categories:
            changes = changes_by_category.get(category_key, [])
            if not changes:
                continue
            
            html += f"""
    <div class="no-break">
        <h3>{category_name} ({len(changes)})</h3>
        <table>
            <thead>
                <tr>
                    <th>Object Name</th>
                    <th>Type</th>
                    <th>Review Status</th>
                    <th>Notes</th>
                </tr>
            </thead>
            <tbody>
"""
            
            for change in changes:
                review_status = change.get('review_status', 'pending')
                review_badge_class = f'badge-{review_status}'
                notes = change.get('user_notes', '')
                notes_display = notes[:100] + '...' if notes and len(notes) > 100 else notes or '-'
                
                html += f"""
                <tr>
                    <td>{change.get('name', 'Unknown')}</td>
                    <td>{change.get('type', 'Unknown')}</td>
                    <td><span class="badge {review_badge_class}">{review_status}</span></td>
                    <td class="notes">{notes_display}</td>
                </tr>
"""
            
            html += """
            </tbody>
        </table>
    </div>
"""

        # Add footer
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        html += f"""
    <div class="footer">
        <p>Generated on {now_str} UTC</p>
        <p>NexusGen Three-Way Merge Assistant</p>
    </div>
</body>
</html>
"""

        return html
    
    def _format_datetime(self, dt_string: str) -> str:
        """
        Format datetime string for display
        
        Args:
            dt_string: ISO format datetime string
            
        Returns:
            Formatted datetime string
        """
        try:
            dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, AttributeError):
            return dt_string
