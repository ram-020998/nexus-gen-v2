"""
Force regenerate report with new formatting.
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
    
    print(f"📊 Regenerating report for session: {session.reference_id}")
    print(f"   Status: {session.status}")
    print(f"   Total Changes: {session.total_changes}")
    
    # Clear cache first
    service = ReportGenerationService()
    service.clear_cache(session.reference_id)
    print("\n🗑️  Cache cleared")
    
    # Generate report
    try:
        report_path = service.generate_report(
            session.reference_id,
            format='xlsx'
        )
        print(f"\n✅ Report generated successfully with new formatting!")
        print(f"   Path: {report_path}")
        print(f"\n📁 Open the report to see:")
        print(f"   • Modern color scheme with gradients")
        print(f"   • Professional section headers with icons")
        print(f"   • Color-coded categories (Conflict=Red, No Conflict=Green, etc.)")
        print(f"   • Complexity indicators with colors")
        print(f"   • Auto-filter enabled on Changes sheet")
        print(f"   • Proper column widths and row heights")
        
    except Exception as e:
        print(f"\n❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
