"""
Merge Summary Service

Generates AI-powered summaries for merge changes asynchronously.
"""
import logging
import threading
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from core.base_service import BaseService
from core.logger import LoggerConfig, get_merge_logger
from models import db, Change, ObjectLookup, ObjectVersion, Package
from services.ai.q_agent_service import QAgentService
from repositories.change_repository import ChangeRepository


class MergeSummaryService(BaseService):
    """
    Service for generating AI summaries of merge changes.
    
    This service:
    1. Fetches change data with customer and vendor versions
    2. Formats data for Q agent consumption
    3. Calls Q agent asynchronously in batches
    4. Updates changes table with summaries
    5. Tracks progress and handles errors
    
    Example:
        >>> service = MergeSummaryService()
        >>> service.generate_summaries_async(session_id=1)
        >>> # Summaries generate in background
        >>> progress = service.get_summary_progress(session_id=1)
        >>> print(f"Progress: {progress['completed']}/{progress['total']}")
    """
    
    BATCH_SIZE = 15  # Process 15 changes per Q agent call
    MAX_SAIL_CODE_LENGTH = 5000  # Truncate SAIL code to prevent prompt overflow
    
    def __init__(self, container=None):
        """Initialize service with dependencies."""
        super().__init__(container)
        self.logger = get_merge_logger()
        self.app = None  # Will be set when needed for threading
    
    def _initialize_dependencies(self) -> None:
        """Initialize service dependencies."""
        self.q_agent_service = self._get_service(QAgentService)
        self.change_repository = self._get_repository(ChangeRepository)
    
    def generate_summaries_async(self, session_id: int) -> None:
        """
        Trigger asynchronous AI summary generation for all changes in session.
        
        This method starts a background thread and returns immediately.
        Summaries are generated in batches and the database is updated
        as each batch completes.
        
        Args:
            session_id: Merge session ID
            
        Example:
            >>> service.generate_summaries_async(session_id=1)
            >>> # Returns immediately, processing continues in background
        """
        from app import create_app
        
        LoggerConfig.log_function_entry(
            self.logger,
            'generate_summaries_async',
            session_id=session_id
        )
        
        # Store app instance for thread context
        self.app = create_app()
        
        # Start background thread
        thread = threading.Thread(
            target=self._generate_summaries_background,
            args=(session_id,),
            daemon=True,
            name=f"MergeSummary-{session_id}"
        )
        thread.start()
        
        self.logger.info(
            f"AI summary generation started in background for session {session_id}"
        )
        
        LoggerConfig.log_function_exit(
            self.logger,
            'generate_summaries_async',
            result="Background thread started"
        )
    
    def _generate_summaries_background(self, session_id: int) -> None:
        """
        Background worker for summary generation.
        
        This runs in a separate thread and:
        1. Fetches all changes for the session
        2. Prepares data with customer and vendor versions
        3. Batches changes for efficient processing
        4. Calls Q agent for each batch
        5. Updates database with results
        
        Args:
            session_id: Merge session ID
        """
        start_time = datetime.utcnow()
        self.logger.info("="*80)
        self.logger.info(f"AI SUMMARY GENERATION STARTED - Session {session_id}")
        self.logger.info(f"Thread: {threading.current_thread().name}")
        self.logger.info(f"Start Time: {start_time.isoformat()}")
        self.logger.info("="*80)
        
        try:
            # Create app context for this thread
            with self.app.app_context():
                self.logger.debug(f"App context created for thread")
                
                # Fetch and prepare change data
                self.logger.info(f"Step 1/4: Fetching and preparing change data...")
                prep_start = datetime.utcnow()
                changes_data = self._prepare_changes_data(session_id)
                prep_duration = (datetime.utcnow() - prep_start).total_seconds()
                
                if not changes_data:
                    self.logger.warning(
                        f"No changes found for session {session_id} - Exiting"
                    )
                    return
                
                self.logger.info(
                    f"✓ Prepared {len(changes_data)} changes in {prep_duration:.2f}s"
                )
                
                # Log sample of changes
                self.logger.debug(f"Sample changes (first 3):")
                for i, change in enumerate(changes_data[:3], 1):
                    self.logger.debug(
                        f"  {i}. Change {change['change_id']}: "
                        f"{change['object_name']} ({change['object_type']}) - "
                        f"Classification: {change['classification']}"
                    )
                
                # Create batches
                self.logger.info(f"Step 2/4: Creating batches...")
                batches = self._create_batches(changes_data, self.BATCH_SIZE)
                self.logger.info(
                    f"✓ Created {len(batches)} batches (size={self.BATCH_SIZE})"
                )
                
                # Process each batch
                self.logger.info(f"Step 3/4: Processing batches...")
                successful_batches = 0
                failed_batches = 0
                total_summaries = 0
                
                for batch_num, batch in enumerate(batches, 1):
                    batch_start = datetime.utcnow()
                    self.logger.info("-"*60)
                    self.logger.info(
                        f"Batch {batch_num}/{len(batches)}: "
                        f"Processing {len(batch)} changes"
                    )
                    
                    # Log batch contents
                    change_ids = [c['change_id'] for c in batch]
                    self.logger.debug(f"  Change IDs: {change_ids}")
                    
                    try:
                        # Mark changes as processing
                        self.logger.debug(f"  Marking batch as 'processing'...")
                        self._update_batch_status(batch, 'processing')
                        self.logger.debug(f"  ✓ Status updated")
                        
                        # Call Q agent
                        self.logger.info(f"  Calling Q Agent for summary generation...")
                        agent_start = datetime.utcnow()
                        summaries = self.q_agent_service.process_merge_summaries(
                            session_id, batch
                        )
                        agent_duration = (datetime.utcnow() - agent_start).total_seconds()
                        
                        self.logger.info(
                            f"  ✓ Q Agent returned {len(summaries)} summaries "
                            f"in {agent_duration:.2f}s"
                        )
                        
                        # Update changes with summaries
                        self.logger.debug(f"  Updating changes with summaries...")
                        update_start = datetime.utcnow()
                        self._update_change_summaries(summaries)
                        update_duration = (datetime.utcnow() - update_start).total_seconds()
                        
                        batch_duration = (datetime.utcnow() - batch_start).total_seconds()
                        
                        self.logger.info(
                            f"  ✓ Batch {batch_num} completed in {batch_duration:.2f}s "
                            f"(agent: {agent_duration:.2f}s, update: {update_duration:.2f}s)"
                        )
                        
                        successful_batches += 1
                        total_summaries += len(summaries)
                        
                    except Exception as batch_error:
                        batch_duration = (datetime.utcnow() - batch_start).total_seconds()
                        self.logger.error(
                            f"  ✗ Batch {batch_num} FAILED after {batch_duration:.2f}s: {batch_error}",
                            exc_info=True
                        )
                        # Mark batch changes as failed
                        self.logger.debug(f"  Marking batch as 'failed'...")
                        self._mark_batch_failed(batch, str(batch_error))
                        failed_batches += 1
                
                # Final summary
                total_duration = (datetime.utcnow() - start_time).total_seconds()
                self.logger.info("="*80)
                self.logger.info(f"AI SUMMARY GENERATION COMPLETED - Session {session_id}")
                self.logger.info(f"Total Duration: {total_duration:.2f}s")
                self.logger.info(f"Successful Batches: {successful_batches}/{len(batches)}")
                self.logger.info(f"Failed Batches: {failed_batches}/{len(batches)}")
                self.logger.info(f"Total Summaries Generated: {total_summaries}")
                self.logger.info(f"Average Time per Summary: {total_duration/total_summaries:.2f}s" if total_summaries > 0 else "N/A")
                self.logger.info("="*80)
                
        except Exception as e:
            total_duration = (datetime.utcnow() - start_time).total_seconds()
            self.logger.error("="*80)
            self.logger.error(
                f"AI SUMMARY GENERATION FAILED - Session {session_id}",
                exc_info=True
            )
            self.logger.error(f"Failed after {total_duration:.2f}s")
            self.logger.error(f"Error: {e}")
            self.logger.error("="*80)
    
    def _prepare_changes_data(self, session_id: int) -> List[Dict]:
        """
        Prepare change data with customer and vendor versions.
        
        Fetches:
        - Change metadata (classification, change types)
        - Object details (name, type, UUID)
        - Customer version (B) and New Vendor version (C) with SAIL code and fields
        
        Note: Base version (A) is NOT included to reduce prompt size.
        The classification already tells us the relationship to base version.
        
        Args:
            session_id: Merge session ID
            
        Returns:
            List of change dictionaries ready for Q agent
        """
        self.logger.debug(f"Fetching changes for session {session_id}...")
        
        # Get all changes for session
        changes = self.change_repository.get_by_session(session_id)
        self.logger.info(f"Found {len(changes)} changes in database")
        
        # Get packages for this session
        self.logger.debug(f"Fetching packages for session {session_id}...")
        packages = db.session.query(Package).filter_by(
            session_id=session_id
        ).all()
        self.logger.info(f"Found {len(packages)} packages")
        
        for pkg in packages:
            self.logger.debug(
                f"  Package: {pkg.package_type} - {pkg.filename} "
                f"({pkg.total_objects} objects)"
            )
        
        package_map = {
            'customized': next((p for p in packages if p.package_type == 'customized'), None),
            'new_vendor': next((p for p in packages if p.package_type == 'new_vendor'), None)
        }
        
        if not package_map['customized']:
            self.logger.warning("No 'customized' package found!")
        if not package_map['new_vendor']:
            self.logger.warning("No 'new_vendor' package found!")
        
        changes_data = []
        failed_count = 0
        
        self.logger.debug(f"Preparing data for {len(changes)} changes...")
        
        for idx, change in enumerate(changes, 1):
            try:
                if idx % 10 == 0:
                    self.logger.debug(f"  Processing change {idx}/{len(changes)}...")
                
                # Get object details
                obj = change.object
                
                if not obj:
                    self.logger.error(f"Change {change.id} has no associated object!")
                    failed_count += 1
                    continue
                
                # Fetch versions for customer and vendor packages only
                versions = self._fetch_object_versions(
                    change.object_id,
                    package_map
                )
                
                change_dict = {
                    'change_id': change.id,
                    'object_name': obj.name,
                    'object_type': obj.object_type,
                    'object_uuid': obj.uuid,
                    'classification': change.classification,
                    'vendor_change_type': change.vendor_change_type,
                    'customer_change_type': change.customer_change_type,
                    'customer_version': versions.get('customized'),
                    'new_vendor_version': versions.get('new_vendor')
                }
                
                changes_data.append(change_dict)
                
            except Exception as e:
                self.logger.error(
                    f"Failed to prepare change {change.id}: {e}",
                    exc_info=True
                )
                failed_count += 1
                continue
        
        self.logger.info(
            f"Successfully prepared {len(changes_data)} changes "
            f"({failed_count} failed)"
        )
        
        return changes_data
    
    def _fetch_object_versions(
        self,
        object_id: int,
        package_map: Dict[str, Package]
    ) -> Dict[str, Optional[Dict]]:
        """
        Fetch object versions from customer and vendor packages.
        
        Note: Base version is NOT fetched to reduce prompt size.
        
        Args:
            object_id: Object ID from object_lookup
            package_map: Dict mapping package type to Package instance
                        (only 'customized' and 'new_vendor')
            
        Returns:
            Dict with 'customized' and 'new_vendor' version data
        """
        versions = {}
        
        for package_type, package in package_map.items():
            if not package:
                self.logger.debug(
                    f"No package for type '{package_type}' - skipping version fetch"
                )
                versions[package_type] = None
                continue
            
            # Query object_versions table
            version = db.session.query(ObjectVersion).filter_by(
                object_id=object_id,
                package_id=package.id
            ).first()
            
            if version:
                # Truncate SAIL code if too long
                sail_code = version.sail_code or ""
                original_length = len(sail_code)
                
                if len(sail_code) > self.MAX_SAIL_CODE_LENGTH:
                    sail_code = sail_code[:self.MAX_SAIL_CODE_LENGTH] + "\n... [truncated]"
                    self.logger.debug(
                        f"Truncated SAIL code for object {object_id} in {package_type}: "
                        f"{original_length} -> {self.MAX_SAIL_CODE_LENGTH} chars"
                    )
                
                versions[package_type] = {
                    'version_uuid': version.version_uuid,
                    'sail_code': sail_code,
                    'fields': json.loads(version.fields) if version.fields else {},
                    'properties': json.loads(version.properties) if version.properties else {}
                }
                
                self.logger.debug(
                    f"Fetched version for object {object_id} in {package_type}: "
                    f"version_uuid={version.version_uuid}, "
                    f"sail_code_length={len(sail_code)}"
                )
            else:
                self.logger.debug(
                    f"No version found for object {object_id} in {package_type}"
                )
                versions[package_type] = None
        
        return versions
    
    def _create_batches(
        self,
        changes_data: List[Dict],
        batch_size: int
    ) -> List[List[Dict]]:
        """
        Create batches of changes for processing.
        
        Args:
            changes_data: List of change dictionaries
            batch_size: Number of changes per batch
            
        Returns:
            List of batches (each batch is a list of changes)
        """
        batches = []
        for i in range(0, len(changes_data), batch_size):
            batch = changes_data[i:i + batch_size]
            batches.append(batch)
        return batches
    
    def _update_batch_status(
        self,
        batch: List[Dict],
        status: str
    ) -> None:
        """
        Update status for all changes in a batch.
        
        Args:
            batch: List of change dictionaries
            status: New status ('processing', 'completed', 'failed')
        """
        change_ids = [change['change_id'] for change in batch]
        
        self.logger.debug(
            f"Updating {len(change_ids)} changes to status '{status}'"
        )
        
        result = db.session.query(Change).filter(
            Change.id.in_(change_ids)
        ).update(
            {'ai_summary_status': status},
            synchronize_session=False
        )
        
        db.session.commit()
        
        self.logger.debug(f"Updated {result} changes to status '{status}'")
    
    def _update_change_summaries(self, summaries: Dict[int, Dict]) -> None:
        """
        Update changes with AI-generated summaries.
        
        Args:
            summaries: Dict mapping change_id to summary data
        """
        self.logger.debug(f"Updating {len(summaries)} changes with summaries...")
        
        success_count = 0
        fail_count = 0
        
        for change_id, summary_data in summaries.items():
            try:
                change = db.session.query(Change).get(change_id)
                if not change:
                    self.logger.warning(f"Change {change_id} not found in database")
                    fail_count += 1
                    continue
                
                # Format summary text
                summary_text = self._format_summary(summary_data)
                
                self.logger.debug(
                    f"Formatted summary for change {change_id}: "
                    f"{len(summary_text)} chars"
                )
                
                # Update change
                change.ai_summary = summary_text
                change.ai_summary_status = 'completed'
                change.ai_summary_generated_at = datetime.utcnow()
                
                db.session.commit()
                
                self.logger.debug(f"✓ Updated summary for change {change_id}")
                success_count += 1
                
            except Exception as e:
                self.logger.error(
                    f"✗ Failed to update change {change_id}: {e}",
                    exc_info=True
                )
                db.session.rollback()
                fail_count += 1
        
        self.logger.info(
            f"Summary updates: {success_count} succeeded, {fail_count} failed"
        )
    
    def _format_summary(self, summary_data: Dict) -> str:
        """
        Format summary data into readable text.
        
        Args:
            summary_data: Dict with summary, complexity, recommendations, etc.
            
        Returns:
            Formatted summary text
        """
        parts = []
        
        # Main summary
        parts.append(summary_data.get('summary', 'No summary available'))
        
        # Complexity and risk
        complexity = summary_data.get('complexity', 'UNKNOWN')
        risk = summary_data.get('risk_level', 'UNKNOWN')
        effort = summary_data.get('estimated_effort_hours', 0)
        
        parts.append(
            f"\n\n**Complexity:** {complexity} | "
            f"**Risk:** {risk} | "
            f"**Estimated Effort:** {effort}h"
        )
        
        # Key conflicts
        conflicts = summary_data.get('key_conflicts', [])
        if conflicts:
            parts.append("\n\n**Key Conflicts:**")
            for conflict in conflicts:
                parts.append(f"\n- {conflict}")
        
        # Recommendations
        recommendations = summary_data.get('recommendations', [])
        if recommendations:
            parts.append("\n\n**Recommendations:**")
            for rec in recommendations:
                parts.append(f"\n- {rec}")
        
        return ''.join(parts)
    
    def _mark_batch_failed(self, batch: List[Dict], error_msg: str) -> None:
        """
        Mark all changes in a batch as failed.
        
        Args:
            batch: List of change dictionaries
            error_msg: Error message to store
        """
        change_ids = [change['change_id'] for change in batch]
        
        self.logger.warning(
            f"Marking {len(change_ids)} changes as failed: {error_msg}"
        )
        
        result = db.session.query(Change).filter(
            Change.id.in_(change_ids)
        ).update(
            {
                'ai_summary_status': 'failed',
                'ai_summary': f"Summary generation failed: {error_msg}"
            },
            synchronize_session=False
        )
        
        db.session.commit()
        
        self.logger.debug(f"Marked {result} changes as failed")
    
    def get_summary_progress(self, session_id: int) -> Dict[str, int]:
        """
        Get progress of AI summary generation for a session.
        
        Args:
            session_id: Merge session ID
            
        Returns:
            Dict with total, completed, processing, failed, pending counts
            
        Example:
            >>> progress = service.get_summary_progress(1)
            >>> print(progress)
            {
                'total': 50,
                'completed': 45,
                'processing': 3,
                'failed': 2,
                'pending': 0
            }
        """
        from sqlalchemy import func
        
        results = db.session.query(
            Change.ai_summary_status,
            func.count(Change.id).label('count')
        ).filter(
            Change.session_id == session_id
        ).group_by(
            Change.ai_summary_status
        ).all()
        
        status_counts = {status: count for status, count in results}
        
        total = sum(status_counts.values())
        
        return {
            'total': total,
            'completed': status_counts.get('completed', 0),
            'processing': status_counts.get('processing', 0),
            'failed': status_counts.get('failed', 0),
            'pending': status_counts.get('pending', 0)
        }
    
    def regenerate_summary(self, change_id: int) -> None:
        """
        Regenerate AI summary for a single change.
        
        Useful for retrying failed summaries or updating existing ones.
        
        Args:
            change_id: Change ID
            
        Example:
            >>> service.regenerate_summary(change_id=123)
        """
        self.logger.info(f"Regenerating summary for change {change_id}...")
        
        change = db.session.query(Change).get(change_id)
        if not change:
            self.logger.error(f"Change {change_id} not found")
            raise ValueError(f"Change {change_id} not found")
        
        self.logger.debug(
            f"Change {change_id}: {change.object.name} ({change.object.object_type}) - "
            f"Classification: {change.classification}"
        )
        
        # Prepare data for this single change
        self.logger.debug(f"Preparing change data for session {change.session_id}...")
        changes_data = self._prepare_changes_data(change.session_id)
        change_data = next(
            (c for c in changes_data if c['change_id'] == change_id),
            None
        )
        
        if not change_data:
            self.logger.error(f"Could not prepare data for change {change_id}")
            raise ValueError(f"Could not prepare data for change {change_id}")
        
        self.logger.debug(f"Change data prepared successfully")
        
        # Mark as processing
        self.logger.debug(f"Marking change {change_id} as 'processing'...")
        change.ai_summary_status = 'processing'
        db.session.commit()
        
        try:
            # Call Q agent with single change
            self.logger.info(f"Calling Q Agent for change {change_id}...")
            agent_start = datetime.utcnow()
            
            summaries = self.q_agent_service.process_merge_summaries(
                change.session_id,
                [change_data]
            )
            
            agent_duration = (datetime.utcnow() - agent_start).total_seconds()
            self.logger.info(
                f"Q Agent completed in {agent_duration:.2f}s, "
                f"returned {len(summaries)} summaries"
            )
            
            # Update change
            self.logger.debug(f"Updating change {change_id} with summary...")
            self._update_change_summaries(summaries)
            
            self.logger.info(f"✓ Successfully regenerated summary for change {change_id}")
            
        except Exception as e:
            self.logger.error(
                f"✗ Failed to regenerate summary for change {change_id}: {e}",
                exc_info=True
            )
            change.ai_summary_status = 'failed'
            change.ai_summary = f"Summary regeneration failed: {str(e)}"
            db.session.commit()
            raise
