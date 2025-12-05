"""
Test script for report generation with new formatting.
"""

from app import create_app
from models import db, MergeSession
from services.report_generation_service import ReportGenerationService

app = create_app()

with app.app_context():
    # Get the most recent session
    session = db.session.query(MergeSession).order_by(
        MergeSession.created_at.desc()
    ).first()
    
    if not session:
        print("❌ No merge sessions found in database")
        exit(1)
    
    print(f"📊 Testing report generation for session: {session.reference_id}")
    print(f"   Status: {session.status}")
    print(f"   Total Changes: {session.total_changes}")
    
    # Generate report
    service = ReportGenerationService()
    
    try:
        report_path = service.generate_report(
            session.reference_id,
            format='xlsx'
        )
        print(f"\n✅ Report generated successfully!")
        print(f"   Path: {report_path}")
        print(f"\n📁 You can open the report at: {report_path}")
        
    except Exception as e:
        print(f"\n❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
