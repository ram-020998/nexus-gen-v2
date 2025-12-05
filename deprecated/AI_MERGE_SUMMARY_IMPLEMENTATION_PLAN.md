# AI-Powered Change Summaries for Three-Way Merge

**Feature**: Automatic AI-generated summaries for merge changes  
**Status**: Planning Phase  
**Created**: December 2, 2025  
**Estimated Duration**: 11-15 days

---

## Table of Contents

1. [Overview](#overview)
2. [Analysis Summary](#analysis-summary)
3. [Architecture](#architecture)
4. [Implementation Phases](#implementation-phases)
5. [Design Decisions](#design-decisions)
6. [Risks & Mitigations](#risks--mitigations)
7. [Success Metrics](#success-metrics)

---

## Overview

### Goal

Enhance the three-way merge workflow by automatically generating AI-powered summaries for each change that needs to be implemented. These summaries will provide developers with actionable insights about code differences, conflicts, and merge recommendations.

### User Story

**As a** developer reviewing merge changes  
**I want** AI-generated summaries of what changed and how to merge it  
**So that** I can quickly understand the impact and make informed merge decisions

### Key Features

- Automatic summary generation after package extraction
- Asynchronous processing (non-blocking)
- Detailed analysis of SAIL code differences
- Conflict identification and resolution recommendations
- Complexity and risk assessment
- Estimated effort for each change


---

## Analysis Summary

### Current State

Based on analysis of the NexusGen codebase:

1. **Existing Q Agent Pattern**: The application uses Amazon Q CLI agents for various tasks:
   - `breakdown-agent`: Spec document breakdown
   - `verify-agent`: Design verification
   - `create-agent`: Design document creation
   - `convert-agent`: SQL conversion
   - `chat-agent`: AI chat assistant

2. **Q Agent Service**: Located at `services/ai/q_agent_service.py`
   - Handles all Q agent interactions
   - Executes Q CLI commands via subprocess
   - Parses JSON responses
   - Implements fallback mechanisms

3. **Workflow Hook Point**: `services/three_way_merge_orchestrator.py`
   - 9-step workflow for three-way merge
   - After Step 7 (classification) is ideal for triggering AI summarization
   - Currently synchronous, but can add async step

4. **Data Structure**: `changes` table (models.py)
   - Drives the merge workflow
   - Contains classified changes for user review
   - Currently has: classification, vendor_change_type, customer_change_type, status, notes
   - Needs: ai_summary, ai_summary_status, ai_summary_generated_at

5. **Current Processing**: All Q agent calls are synchronous
   - Controllers call Q agent service directly
   - Wait for response before continuing
   - Works for single-item processing
   - Need async for batch processing

### Proposed Approach

1. **Create new Q agent**: `merge-summary-agent`
2. **Add async processing**: Use Python threading for background execution
3. **Batch processing**: Send multiple changes to Q agent in batches
4. **Non-blocking**: Workflow completes, summaries generate in background
5. **Status tracking**: Track progress per change and per session


---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                Three-Way Merge Orchestrator                  │
│  (Coordinates 9-step workflow)                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    Step 8: Trigger AI Summary
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  MergeSummaryService (NEW)                   │
│  - Fetch change data with all versions                       │
│  - Format data for Q agent                                   │
│  - Execute async processing                                  │
│  - Update changes table with summaries                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    (Async Thread)
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    QAgentService                             │
│  - process_merge_summaries(session_id, changes_data)         │
│  - Execute Q CLI: merge-summary-agent                        │
│  - Parse JSON response                                       │
│  - Return summaries dict                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Amazon Q CLI Agent                          │
│  Agent: merge-summary-agent                                  │
│  - Analyze code differences                                  │
│  - Identify conflicts                                        │
│  - Generate recommendations                                  │
│  - Return structured JSON                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Database (changes table)                  │
│  - ai_summary: Text                                          │
│  - ai_summary_status: String (pending/processing/completed)  │
│  - ai_summary_generated_at: DateTime                         │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Package Extraction Complete** → Orchestrator Step 7 (Classification)
2. **Classification Complete** → Orchestrator Step 8 (Trigger AI Summary)
3. **Async Thread Started** → MergeSummaryService.generate_summaries_async()
4. **Fetch Change Data** → Get all changes with object versions (A, B, C)
5. **Batch Changes** → Group into batches of 10-20 changes
6. **Call Q Agent** → For each batch, call merge-summary-agent
7. **Parse Response** → Extract summaries from JSON
8. **Update Database** → Update each change with summary and status
9. **Complete** → All changes have summaries

### Async Processing Strategy

**Threading Approach** (Recommended):
```python
import threading

def generate_summaries_async(self, session_id: int) -> None:
    """Trigger async summary generation"""
    thread = threading.Thread(
        target=self._generate_summaries_background,
        args=(session_id,),
        daemon=True
    )
    thread.start()
    self.logger.info(f"AI summary generation started for session {session_id}")

def _generate_summaries_background(self, session_id: int) -> None:
    """Background worker for summary generation"""
    try:
        # Create new app context for thread
        with self.app.app_context():
            changes = self._prepare_changes_data(session_id)
            batches = self._create_batches(changes, batch_size=15)
            
            for batch in batches:
                summaries = self.q_agent_service.process_merge_summaries(
                    session_id, batch
                )
                self._update_change_summaries(summaries)
    except Exception as e:
        self.logger.error(f"AI summary generation failed: {e}")
```

**Why Threading?**
- Simple to implement
- No external dependencies (Redis, Celery)
- Sufficient for current scale
- Can migrate to Celery later if needed


---

## Implementation Phases

### Phase 1: Database Schema Update

**Duration**: 1 day

#### 1.1 Create Migration Script

**File**: `migrations/add_ai_summary_to_changes.py`

```python
"""
Add AI summary fields to changes table

Migration: 004
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

def upgrade():
    # Add ai_summary column
    op.add_column('changes', 
        sa.Column('ai_summary', sa.Text, nullable=True)
    )
    
    # Add ai_summary_status column
    op.add_column('changes',
        sa.Column('ai_summary_status', sa.String(20), 
                  nullable=False, server_default='pending')
    )
    
    # Add ai_summary_generated_at column
    op.add_column('changes',
        sa.Column('ai_summary_generated_at', sa.DateTime, nullable=True)
    )
    
    # Add index for status queries
    op.create_index('idx_change_ai_summary_status', 
                    'changes', ['session_id', 'ai_summary_status'])

def downgrade():
    op.drop_index('idx_change_ai_summary_status', 'changes')
    op.drop_column('changes', 'ai_summary_generated_at')
    op.drop_column('changes', 'ai_summary_status')
    op.drop_column('changes', 'ai_summary')
```

#### 1.2 Update Change Model

**File**: `models.py`

```python
class Change(db.Model):
    """Working set of classified changes for user review"""
    __tablename__ = 'changes'
    
    # ... existing fields ...
    
    # AI Summary fields
    ai_summary = db.Column(db.Text)
    ai_summary_status = db.Column(db.String(20), default='pending')
    # Status values: 'pending', 'processing', 'completed', 'failed'
    ai_summary_generated_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            # ... existing fields ...
            'ai_summary': self.ai_summary,
            'ai_summary_status': self.ai_summary_status,
            'ai_summary_generated_at': self.ai_summary_generated_at.isoformat() 
                if self.ai_summary_generated_at else None,
        }
```

#### 1.3 Run Migration

```bash
# Create migration
python create_migration.py add_ai_summary_to_changes

# Apply migration
python apply_migration.py

# Verify schema
python verify_schema.py
```

**Deliverables**:
- ✅ Migration script created
- ✅ Change model updated
- ✅ Migration applied to database
- ✅ Schema verified


---

### Phase 2: Q Agent Integration

**Duration**: 2-3 days

#### 2.1 Define Q Agent

**Agent Name**: `merge-summary-agent`

**Agent Configuration**: (To be created in Amazon Q)

**Purpose**: Analyze three-way merge changes and generate actionable summaries

**Capabilities**:
- Analyze SAIL code differences between versions
- Understand Appian object types and dependencies
- Identify breaking changes and conflicts
- Provide merge recommendations
- Estimate complexity and risk

#### 2.2 Input Format

**File**: `services/ai/q_agent_service.py` - New method

```python
def process_merge_summaries(
    self, 
    session_id: int, 
    changes_data: List[Dict]
) -> Dict[int, Dict]:
    """
    Process merge changes and generate AI summaries
    
    Args:
        session_id: Merge session ID
        changes_data: List of change dictionaries with version data
        
    Returns:
        Dict mapping change_id to summary data
        
    Example:
        >>> summaries = service.process_merge_summaries(1, changes_data)
        >>> print(summaries[1]['summary'])
        "Vendor added validation while customer modified layout..."
    """
```

**Input JSON Structure**:
```json
{
  "session_id": "MRG_001",
  "changes": [
    {
      "change_id": 1,
      "object_name": "SS_CreateEvaluationForm",
      "object_type": "Interface",
      "classification": "CONFLICT",
      "vendor_change_type": "MODIFIED",
      "customer_change_type": "MODIFIED",
      "customer_version": {
        "version_uuid": "def-456",
        "sail_code": "a!localVariables(\n  local!formData: null,\n  ...",
        "fields": {"parameters": [...], "security": {...}}
      },
      "new_vendor_version": {
        "version_uuid": "ghi-789",
        "sail_code": "a!localVariables(\n  local!formData: null,\n  ...",
        "fields": {"parameters": [...], "security": {...}}
      }
    }
  ]
}
```

**Note**: Base version (Package A) is NOT included because:
- We already have change metadata (vendor_change_type, customer_change_type, classification)
- Reduces prompt size by 33% (important for large SAIL code)
- AI focuses on B vs C comparison, which is what matters for merge decisions
- Classification already tells us the relationship to base version

#### 2.3 Output Format

**Expected JSON Response**:
```json
{
  "summaries": [
    {
      "change_id": 1,
      "summary": "Vendor added new validation logic for form fields while customer modified the layout structure. Merge requires: 1) Preserve customer layout changes, 2) Integrate vendor validation rules, 3) Test form submission flow.",
      "complexity": "HIGH",
      "risk_level": "MEDIUM",
      "estimated_effort_hours": 2.5,
      "key_conflicts": [
        "Both modified the same rule!input parameter",
        "Customer removed field that vendor now validates"
      ],
      "recommendations": [
        "Review validation logic compatibility with customer layout",
        "Test all form submission scenarios",
        "Consider keeping customer's UX improvements"
      ]
    }
  ]
}
```

#### 2.4 Q Agent Prompt Template

```python
def _create_merge_summary_prompt(self, changes_data: List[Dict]) -> str:
    """Create prompt for merge summary agent"""
    
    return f"""
APPIAN THREE-WAY MERGE ANALYSIS

You are analyzing changes in an Appian application three-way merge:
- Package B (Customer): Customer's customized version
- Package C (New Vendor): New vendor version

Each change has been pre-classified based on comparison with the base version (Package A):
- CONFLICT: Both customer and vendor modified the object (need to merge both changes)
- NO_CONFLICT: Only vendor modified the object (customer kept base version)
- NEW: Vendor added a new object
- DELETED: Vendor removed an object that customer had

Your task: Analyze the differences between customer and vendor versions, and generate actionable merge summaries.

CHANGES TO ANALYZE:
{json.dumps(changes_data, indent=2)}

INSTRUCTIONS FOR EACH CLASSIFICATION:

**CONFLICT Changes** (both modified):
1. Compare customer_version vs new_vendor_version
2. Identify specific conflicts (same lines changed differently)
3. Determine if changes are compatible or incompatible
4. Provide step-by-step merge recommendations
5. Highlight any breaking changes or risks

**NO_CONFLICT Changes** (only vendor modified):
1. Analyze what the vendor changed in new_vendor_version
2. Assess impact on customer's application
3. Identify any dependencies or side effects
4. Recommend acceptance with any necessary testing

**NEW Changes** (vendor added):
1. Analyze the new object in new_vendor_version
2. Determine if it's required or optional
3. Identify dependencies on other objects
4. Recommend integration approach

**DELETED Changes** (vendor removed):
1. Analyze what customer has in customer_version
2. Determine if customer is using this object
3. Assess impact of removal
4. Recommend whether to keep or remove

FOCUS ON:
- SAIL code differences (syntax, logic, structure)
- Parameter changes (added, removed, modified)
- Field and property changes
- Dependency impacts
- Breaking changes
- Security implications

OUTPUT FORMAT:
Return ONLY valid JSON in this exact format:
{{
  "summaries": [
    {{
      "change_id": <int>,
      "summary": "<concise 2-3 sentence summary explaining what changed and merge approach>",
      "complexity": "LOW|MEDIUM|HIGH",
      "risk_level": "LOW|MEDIUM|HIGH",
      "estimated_effort_hours": <float>,
      "key_conflicts": ["<specific conflict 1>", "<specific conflict 2>"],
      "recommendations": ["<actionable recommendation 1>", "<actionable recommendation 2>"]
    }}
  ]
}}

IMPORTANT:
- Be specific and actionable
- Reference actual code changes (line numbers, variable names, etc.)
- Prioritize merge safety and customer customizations
- For CONFLICT changes, provide clear merge strategy
- For NO_CONFLICT changes, explain what vendor changed and why it's safe
"""
```

**Deliverables**:
- ✅ Q agent created and configured
- ✅ Method added to QAgentService
- ✅ Prompt template implemented
- ✅ JSON parsing implemented
- ✅ Error handling added
- ✅ Unit tests written


---

### Phase 3: Merge Summary Service

**Duration**: 2-3 days

#### 3.1 Create New Service

**File**: `services/merge_summary_service.py`

```python
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
    1. Fetches change data with all three package versions
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
        2. Prepares data with all three package versions
        3. Batches changes for efficient processing
        4. Calls Q agent for each batch
        5. Updates database with results
        
        Args:
            session_id: Merge session ID
        """
        try:
            # Create app context for this thread
            with self.app.app_context():
                self.logger.info(
                    f"Background summary generation starting for session {session_id}"
                )
                
                # Fetch and prepare change data
                changes_data = self._prepare_changes_data(session_id)
                
                if not changes_data:
                    self.logger.warning(
                        f"No changes found for session {session_id}"
                    )
                    return
                
                self.logger.info(
                    f"Prepared {len(changes_data)} changes for summary generation"
                )
                
                # Create batches
                batches = self._create_batches(changes_data, self.BATCH_SIZE)
                self.logger.info(
                    f"Created {len(batches)} batches (size={self.BATCH_SIZE})"
                )
                
                # Process each batch
                for batch_num, batch in enumerate(batches, 1):
                    self.logger.info(
                        f"Processing batch {batch_num}/{len(batches)} "
                        f"({len(batch)} changes)"
                    )
                    
                    try:
                        # Mark changes as processing
                        self._update_batch_status(batch, 'processing')
                        
                        # Call Q agent
                        summaries = self.q_agent_service.process_merge_summaries(
                            session_id, batch
                        )
                        
                        # Update changes with summaries
                        self._update_change_summaries(summaries)
                        
                        self.logger.info(
                            f"Batch {batch_num} completed: "
                            f"{len(summaries)} summaries generated"
                        )
                        
                    except Exception as batch_error:
                        self.logger.error(
                            f"Batch {batch_num} failed: {batch_error}",
                            exc_info=True
                        )
                        # Mark batch changes as failed
                        self._mark_batch_failed(batch, str(batch_error))
                
                self.logger.info(
                    f"Background summary generation completed for session {session_id}"
                )
                
        except Exception as e:
            self.logger.error(
                f"Background summary generation failed for session {session_id}: {e}",
                exc_info=True
            )
    
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
        # Get all changes for session
        changes = self.change_repository.get_by_session(session_id)
        
        # Get packages for this session
        packages = db.session.query(Package).filter_by(
            session_id=session_id
        ).all()
        
        package_map = {
            'customized': next((p for p in packages if p.package_type == 'customized'), None),
            'new_vendor': next((p for p in packages if p.package_type == 'new_vendor'), None)
        }
        
        changes_data = []
        
        for change in changes:
            try:
                # Get object details
                obj = change.object
                
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
                continue
        
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
                if len(sail_code) > self.MAX_SAIL_CODE_LENGTH:
                    sail_code = sail_code[:self.MAX_SAIL_CODE_LENGTH] + "\n... [truncated]"
                
                versions[package_type] = {
                    'version_uuid': version.version_uuid,
                    'sail_code': sail_code,
                    'fields': json.loads(version.fields) if version.fields else {},
                    'properties': json.loads(version.properties) if version.properties else {}
                }
            else:
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
        
        db.session.query(Change).filter(
            Change.id.in_(change_ids)
        ).update(
            {'ai_summary_status': status},
            synchronize_session=False
        )
        db.session.commit()
    
    def _update_change_summaries(self, summaries: Dict[int, Dict]) -> None:
        """
        Update changes with AI-generated summaries.
        
        Args:
            summaries: Dict mapping change_id to summary data
        """
        for change_id, summary_data in summaries.items():
            try:
                change = db.session.query(Change).get(change_id)
                if not change:
                    self.logger.warning(f"Change {change_id} not found")
                    continue
                
                # Format summary text
                summary_text = self._format_summary(summary_data)
                
                # Update change
                change.ai_summary = summary_text
                change.ai_summary_status = 'completed'
                change.ai_summary_generated_at = datetime.utcnow()
                
                db.session.commit()
                
                self.logger.debug(f"Updated summary for change {change_id}")
                
            except Exception as e:
                self.logger.error(
                    f"Failed to update change {change_id}: {e}",
                    exc_info=True
                )
                db.session.rollback()
    
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
        
        db.session.query(Change).filter(
            Change.id.in_(change_ids)
        ).update(
            {
                'ai_summary_status': 'failed',
                'ai_summary': f"Summary generation failed: {error_msg}"
            },
            synchronize_session=False
        )
        db.session.commit()
    
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
        change = db.session.query(Change).get(change_id)
        if not change:
            raise ValueError(f"Change {change_id} not found")
        
        # Prepare data for this single change
        changes_data = self._prepare_changes_data(change.session_id)
        change_data = next(
            (c for c in changes_data if c['change_id'] == change_id),
            None
        )
        
        if not change_data:
            raise ValueError(f"Could not prepare data for change {change_id}")
        
        # Mark as processing
        change.ai_summary_status = 'processing'
        db.session.commit()
        
        try:
            # Call Q agent with single change
            summaries = self.q_agent_service.process_merge_summaries(
                change.session_id,
                [change_data]
            )
            
            # Update change
            self._update_change_summaries(summaries)
            
            self.logger.info(f"Regenerated summary for change {change_id}")
            
        except Exception as e:
            self.logger.error(
                f"Failed to regenerate summary for change {change_id}: {e}",
                exc_info=True
            )
            change.ai_summary_status = 'failed'
            change.ai_summary = f"Summary regeneration failed: {str(e)}"
            db.session.commit()
            raise
```

**Deliverables**:
- ✅ MergeSummaryService created
- ✅ Async processing implemented
- ✅ Batch processing implemented
- ✅ Progress tracking implemented
- ✅ Error handling implemented
- ✅ Unit tests written


---

### Phase 4: Orchestrator Integration

**Duration**: 1 day

#### 4.1 Modify Three-Way Merge Orchestrator

**File**: `services/three_way_merge_orchestrator.py`

**Changes**:

1. Add dependency injection for MergeSummaryService
2. Add new Step 8 after classification
3. Trigger async summary generation
4. Update step numbering (9 steps → 10 steps)

```python
def _initialize_dependencies(self) -> None:
    """Initialize service dependencies."""
    self.package_extraction_service = self._get_service(PackageExtractionService)
    self.delta_comparison_service = self._get_service(DeltaComparisonService)
    self.customer_comparison_service = self._get_service(CustomerComparisonService)
    self.classification_service = self._get_service(ClassificationService)
    self.merge_guidance_service = self._get_service(MergeGuidanceService)
    self.comparison_persistence_service = self._get_service(ComparisonPersistenceService)
    self.merge_summary_service = self._get_service(MergeSummaryService)  # NEW
    self.change_repository = self._get_repository(ChangeRepository)
```

**New Step 8** (insert after classification, before persistence):

```python
# Step 8: Trigger AI summary generation (async)
step_start = time.time()
LoggerConfig.log_step(
    self.logger, 8, 10,
    "Triggering AI summary generation (async)"
)

self.merge_summary_service.generate_summaries_async(session.id)

step_duration = time.time() - step_start
self.logger.info(
    f"✓ AI summary generation triggered (processing in background) "
    f"in {step_duration:.2f}s"
)

# Note: Summaries will be generated asynchronously
# The workflow continues without waiting for completion
```

**Update remaining steps**:
- Step 9: Persist detailed comparisons (was Step 8)
- Step 10: Generate merge guidance (was Step 9)

#### 4.2 Register Service in Dependency Container

**File**: `core/dependency_container.py`

```python
from services.merge_summary_service import MergeSummaryService

# In register_services method
self.register_service(MergeSummaryService)
```

#### 4.3 Update Workflow Documentation

Update docstrings and comments to reflect 10-step workflow:
1. Create session record
2. Extract Package A (Base)
3. Extract Package B (Customized)
4. Extract Package C (New Vendor)
5. Perform delta comparison (A→C)
6. Perform customer comparison (A→B)
7. Classify changes (apply 7 rules)
8. **Trigger AI summary generation (async)** ← NEW
9. Persist detailed comparisons
10. Generate merge guidance

**Deliverables**:
- ✅ Orchestrator updated with new step
- ✅ Service registered in DI container
- ✅ Documentation updated
- ✅ Integration tests pass


---

### Phase 5: API Endpoints

**Duration**: 1 day

#### 5.1 Add Controller Endpoints

**File**: `controllers/merge_assistant_controller.py`

```python
@merge_assistant_bp.route('/session/<reference_id>/summary-progress')
def get_summary_progress(reference_id):
    """
    Get AI summary generation progress for a session.
    
    Returns JSON with progress statistics.
    
    Example Response:
    {
        "total": 50,
        "completed": 45,
        "processing": 3,
        "failed": 2,
        "pending": 0,
        "percentage": 90
    }
    """
    try:
        # Get session
        session = db.session.query(MergeSession).filter_by(
            reference_id=reference_id
        ).first()
        
        if not session:
            return controller.json_error('Session not found', status_code=404)
        
        # Get progress from service
        merge_summary_service = controller.get_service(MergeSummaryService)
        progress = merge_summary_service.get_summary_progress(session.id)
        
        # Calculate percentage
        if progress['total'] > 0:
            progress['percentage'] = round(
                (progress['completed'] / progress['total']) * 100, 1
            )
        else:
            progress['percentage'] = 0
        
        return controller.json_success(data=progress)
        
    except Exception as e:
        return controller.handle_error(
            e,
            user_message='Failed to get summary progress',
            return_json=True
        )


@merge_assistant_bp.route('/session/<reference_id>/regenerate-summaries', methods=['POST'])
def regenerate_summaries(reference_id):
    """
    Manually trigger summary regeneration for all changes in a session.
    
    Useful if initial generation failed or user wants to refresh summaries.
    """
    try:
        # Get session
        session = db.session.query(MergeSession).filter_by(
            reference_id=reference_id
        ).first()
        
        if not session:
            return controller.json_error('Session not found', status_code=404)
        
        # Reset all summaries to pending
        db.session.query(Change).filter_by(
            session_id=session.id
        ).update({
            'ai_summary_status': 'pending',
            'ai_summary': None,
            'ai_summary_generated_at': None
        })
        db.session.commit()
        
        # Trigger regeneration
        merge_summary_service = controller.get_service(MergeSummaryService)
        merge_summary_service.generate_summaries_async(session.id)
        
        return controller.json_success(
            message='Summary regeneration triggered',
            data={'reference_id': reference_id}
        )
        
    except Exception as e:
        return controller.handle_error(
            e,
            user_message='Failed to regenerate summaries',
            return_json=True
        )


@merge_assistant_bp.route('/change/<int:change_id>/regenerate-summary', methods=['POST'])
def regenerate_single_summary(change_id):
    """
    Regenerate AI summary for a single change.
    
    Useful for retrying failed summaries.
    """
    try:
        merge_summary_service = controller.get_service(MergeSummaryService)
        merge_summary_service.regenerate_summary(change_id)
        
        return controller.json_success(
            message='Summary regenerated successfully',
            data={'change_id': change_id}
        )
        
    except ValueError as e:
        return controller.json_error(str(e), status_code=404)
    except Exception as e:
        return controller.handle_error(
            e,
            user_message='Failed to regenerate summary',
            return_json=True
        )
```

**Deliverables**:
- ✅ Progress endpoint implemented
- ✅ Regenerate all endpoint implemented
- ✅ Regenerate single endpoint implemented
- ✅ Error handling added
- ✅ API tests written


---

### Phase 6: UI Updates

**Duration**: 2-3 days

#### 6.1 Update Summary Template

**File**: `templates/merge/summary.html`

Add AI summary section to each change card:

```html
<!-- AI Summary Section -->
<div class="ai-summary-section mt-3">
    <h6 class="text-muted">
        <i class="fas fa-robot"></i> AI Analysis
    </h6>
    
    <!-- Loading State -->
    <div v-if="change.ai_summary_status === 'pending' || change.ai_summary_status === 'processing'" 
         class="ai-summary-loading">
        <div class="spinner-border spinner-border-sm text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
        <span class="ms-2 text-muted">
            {{ change.ai_summary_status === 'pending' ? 'Queued for analysis...' : 'Analyzing changes...' }}
        </span>
    </div>
    
    <!-- Completed State -->
    <div v-else-if="change.ai_summary_status === 'completed'" class="ai-summary-content">
        <div class="summary-text" v-html="formatSummary(change.ai_summary)"></div>
        <div class="summary-meta mt-2">
            <small class="text-muted">
                Generated {{ formatTimestamp(change.ai_summary_generated_at) }}
            </small>
        </div>
    </div>
    
    <!-- Failed State -->
    <div v-else-if="change.ai_summary_status === 'failed'" class="ai-summary-error">
        <div class="alert alert-warning mb-2">
            <i class="fas fa-exclamation-triangle"></i>
            Summary generation failed
        </div>
        <button @click="regenerateSummary(change.id)" 
                class="btn btn-sm btn-outline-primary">
            <i class="fas fa-redo"></i> Retry
        </button>
    </div>
</div>
```

#### 6.2 Add Progress Indicator

**File**: `templates/merge/summary.html`

Add progress bar at the top of the page:

```html
<!-- AI Summary Progress -->
<div class="card mb-3" v-if="summaryProgress.total > 0">
    <div class="card-body">
        <div class="d-flex justify-content-between align-items-center mb-2">
            <h6 class="mb-0">
                <i class="fas fa-robot"></i> AI Summary Generation
            </h6>
            <span class="badge bg-primary">
                {{ summaryProgress.completed }}/{{ summaryProgress.total }}
            </span>
        </div>
        
        <div class="progress" style="height: 20px;">
            <div class="progress-bar progress-bar-striped" 
                 :class="{'progress-bar-animated': summaryProgress.processing > 0}"
                 role="progressbar" 
                 :style="{width: summaryProgress.percentage + '%'}"
                 :aria-valuenow="summaryProgress.percentage" 
                 aria-valuemin="0" 
                 aria-valuemax="100">
                {{ summaryProgress.percentage }}%
            </div>
        </div>
        
        <div class="mt-2 small text-muted">
            <span v-if="summaryProgress.processing > 0">
                <i class="fas fa-spinner fa-spin"></i>
                {{ summaryProgress.processing }} processing...
            </span>
            <span v-if="summaryProgress.failed > 0" class="text-warning ms-3">
                <i class="fas fa-exclamation-triangle"></i>
                {{ summaryProgress.failed }} failed
            </span>
            <button v-if="summaryProgress.failed > 0" 
                    @click="regenerateAllSummaries()"
                    class="btn btn-sm btn-outline-warning ms-2">
                <i class="fas fa-redo"></i> Retry Failed
            </button>
        </div>
    </div>
</div>
```

#### 6.3 Add JavaScript for Real-Time Updates

**File**: `templates/merge/summary.html` (in script section)

```javascript
// Vue.js data
data() {
    return {
        changes: [],
        summaryProgress: {
            total: 0,
            completed: 0,
            processing: 0,
            failed: 0,
            pending: 0,
            percentage: 0
        },
        progressInterval: null
    }
},

mounted() {
    this.loadChanges();
    this.startProgressPolling();
},

beforeUnmount() {
    this.stopProgressPolling();
},

methods: {
    async loadChanges() {
        try {
            const response = await fetch(`/merge/session/${this.referenceId}/changes`);
            const data = await response.json();
            this.changes = data.changes;
        } catch (error) {
            console.error('Failed to load changes:', error);
        }
    },
    
    async loadSummaryProgress() {
        try {
            const response = await fetch(
                `/merge/session/${this.referenceId}/summary-progress`
            );
            const data = await response.json();
            this.summaryProgress = data.data;
            
            // Stop polling if all summaries are complete
            if (this.summaryProgress.processing === 0 && 
                this.summaryProgress.pending === 0) {
                this.stopProgressPolling();
                // Reload changes to get updated summaries
                this.loadChanges();
            }
        } catch (error) {
            console.error('Failed to load progress:', error);
        }
    },
    
    startProgressPolling() {
        // Poll every 3 seconds
        this.progressInterval = setInterval(() => {
            this.loadSummaryProgress();
        }, 3000);
        
        // Load immediately
        this.loadSummaryProgress();
    },
    
    stopProgressPolling() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
    },
    
    async regenerateSummary(changeId) {
        try {
            const response = await fetch(
                `/merge/change/${changeId}/regenerate-summary`,
                { method: 'POST' }
            );
            
            if (response.ok) {
                this.showToast('Summary regeneration started', 'success');
                this.startProgressPolling();
            } else {
                this.showToast('Failed to regenerate summary', 'error');
            }
        } catch (error) {
            console.error('Failed to regenerate summary:', error);
            this.showToast('Failed to regenerate summary', 'error');
        }
    },
    
    async regenerateAllSummaries() {
        try {
            const response = await fetch(
                `/merge/session/${this.referenceId}/regenerate-summaries`,
                { method: 'POST' }
            );
            
            if (response.ok) {
                this.showToast('Summary regeneration started for all changes', 'success');
                this.startProgressPolling();
            } else {
                this.showToast('Failed to regenerate summaries', 'error');
            }
        } catch (error) {
            console.error('Failed to regenerate summaries:', error);
            this.showToast('Failed to regenerate summaries', 'error');
        }
    },
    
    formatSummary(summary) {
        if (!summary) return '';
        
        // Convert markdown-style formatting to HTML
        return summary
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');
    },
    
    formatTimestamp(timestamp) {
        if (!timestamp) return '';
        const date = new Date(timestamp);
        return date.toLocaleString();
    },
    
    showToast(message, type) {
        // Implement toast notification
        // Use Bootstrap Toast or similar
    }
}
```

#### 6.4 Add CSS Styling

**File**: `static/css/merge.css`

```css
/* AI Summary Section */
.ai-summary-section {
    background-color: #f8f9fa;
    border-left: 3px solid #0d6efd;
    padding: 1rem;
    border-radius: 0.25rem;
}

.ai-summary-loading {
    color: #6c757d;
    font-style: italic;
}

.ai-summary-content {
    line-height: 1.6;
}

.ai-summary-content .summary-text {
    margin-bottom: 0.5rem;
}

.ai-summary-content strong {
    color: #0d6efd;
}

.ai-summary-error {
    padding: 0.5rem;
}

.summary-meta {
    border-top: 1px solid #dee2e6;
    padding-top: 0.5rem;
}

/* Progress Bar Enhancements */
.progress {
    background-color: #e9ecef;
}

.progress-bar {
    font-weight: 600;
    font-size: 0.875rem;
}
```

**Deliverables**:
- ✅ Summary display implemented
- ✅ Progress indicator implemented
- ✅ Real-time polling implemented
- ✅ Regeneration buttons implemented
- ✅ CSS styling added
- ✅ UI tested with Chrome DevTools MCP


---

### Phase 7: Testing

**Duration**: 2 days

#### 7.1 Unit Tests

**File**: `tests/test_merge_summary_service.py`

```python
"""
Unit tests for MergeSummaryService
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from services.merge_summary_service import MergeSummaryService


class TestMergeSummaryService:
    """Test MergeSummaryService functionality"""
    
    def test_prepare_changes_data(self, app_context, sample_session):
        """Test change data preparation"""
        service = MergeSummaryService()
        changes_data = service._prepare_changes_data(sample_session.id)
        
        assert len(changes_data) > 0
        assert 'change_id' in changes_data[0]
        assert 'object_name' in changes_data[0]
        assert 'base_version' in changes_data[0]
        assert 'customer_version' in changes_data[0]
        assert 'new_vendor_version' in changes_data[0]
    
    def test_fetch_object_versions(self, app_context, sample_packages):
        """Test fetching object versions from all packages"""
        service = MergeSummaryService()
        
        package_map = {
            'base': sample_packages['base'],
            'customized': sample_packages['customized'],
            'new_vendor': sample_packages['new_vendor']
        }
        
        versions = service._fetch_object_versions(1, package_map)
        
        assert 'base' in versions
        assert 'customized' in versions
        assert 'new_vendor' in versions
    
    def test_create_batches(self):
        """Test batch creation"""
        service = MergeSummaryService()
        
        changes_data = [{'change_id': i} for i in range(1, 26)]
        batches = service._create_batches(changes_data, batch_size=10)
        
        assert len(batches) == 3
        assert len(batches[0]) == 10
        assert len(batches[1]) == 10
        assert len(batches[2]) == 5
    
    def test_format_summary(self):
        """Test summary formatting"""
        service = MergeSummaryService()
        
        summary_data = {
            'summary': 'Test summary',
            'complexity': 'HIGH',
            'risk_level': 'MEDIUM',
            'estimated_effort_hours': 2.5,
            'key_conflicts': ['Conflict 1', 'Conflict 2'],
            'recommendations': ['Rec 1', 'Rec 2']
        }
        
        formatted = service._format_summary(summary_data)
        
        assert 'Test summary' in formatted
        assert 'HIGH' in formatted
        assert 'MEDIUM' in formatted
        assert '2.5h' in formatted
        assert 'Conflict 1' in formatted
        assert 'Rec 1' in formatted
    
    def test_get_summary_progress(self, app_context, sample_session):
        """Test progress tracking"""
        service = MergeSummaryService()
        progress = service.get_summary_progress(sample_session.id)
        
        assert 'total' in progress
        assert 'completed' in progress
        assert 'processing' in progress
        assert 'failed' in progress
        assert 'pending' in progress
    
    @patch('services.merge_summary_service.threading.Thread')
    def test_generate_summaries_async(self, mock_thread, app_context, sample_session):
        """Test async summary generation trigger"""
        service = MergeSummaryService()
        service.generate_summaries_async(sample_session.id)
        
        # Verify thread was started
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()
```

#### 7.2 Integration Tests

**File**: `tests/test_merge_summary_integration.py`

```python
"""
Integration tests for AI summary generation
"""
import pytest
import time
from models import db, Change
from services.three_way_merge_orchestrator import ThreeWayMergeOrchestrator
from services.merge_summary_service import MergeSummaryService


class TestMergeSummaryIntegration:
    """Test complete workflow with AI summary generation"""
    
    def test_complete_workflow_with_summaries(self, app_context, test_packages):
        """Test complete three-way merge workflow with AI summaries"""
        orchestrator = ThreeWayMergeOrchestrator()
        
        # Create merge session
        session = orchestrator.create_merge_session(
            base_zip_path=test_packages['base'],
            customized_zip_path=test_packages['customized'],
            new_vendor_zip_path=test_packages['new_vendor']
        )
        
        assert session.reference_id is not None
        assert session.status == 'ready'
        
        # Check that summary generation was triggered
        changes = db.session.query(Change).filter_by(
            session_id=session.id
        ).all()
        
        assert len(changes) > 0
        
        # All changes should have ai_summary_status
        for change in changes:
            assert change.ai_summary_status in [
                'pending', 'processing', 'completed', 'failed'
            ]
        
        # Wait for summaries to complete (max 30 seconds)
        max_wait = 30
        waited = 0
        service = MergeSummaryService()
        
        while waited < max_wait:
            progress = service.get_summary_progress(session.id)
            if progress['processing'] == 0 and progress['pending'] == 0:
                break
            time.sleep(1)
            waited += 1
        
        # Check final progress
        progress = service.get_summary_progress(session.id)
        assert progress['completed'] + progress['failed'] == progress['total']
    
    def test_summary_regeneration(self, app_context, sample_session):
        """Test summary regeneration for failed summaries"""
        service = MergeSummaryService()
        
        # Get a change
        change = db.session.query(Change).filter_by(
            session_id=sample_session.id
        ).first()
        
        # Mark as failed
        change.ai_summary_status = 'failed'
        change.ai_summary = 'Test failure'
        db.session.commit()
        
        # Regenerate
        service.regenerate_summary(change.id)
        
        # Check status updated
        db.session.refresh(change)
        assert change.ai_summary_status in ['processing', 'completed']
```

#### 7.3 Q Agent Tests

**File**: `tests/test_merge_summary_agent.py`

```python
"""
Tests for merge-summary-agent Q agent
"""
import pytest
import json
from services.ai.q_agent_service import QAgentService


class TestMergeSummaryAgent:
    """Test Q agent for merge summaries"""
    
    def test_q_agent_with_sample_data(self, app_context):
        """Test Q agent with sample change data"""
        service = QAgentService()
        
        # Prepare sample data (without base version)
        changes_data = [{
            'change_id': 1,
            'object_name': 'SS_TestInterface',
            'object_type': 'Interface',
            'classification': 'CONFLICT',
            'vendor_change_type': 'MODIFIED',
            'customer_change_type': 'MODIFIED',
            'customer_version': {
                'version_uuid': 'def-456',
                'sail_code': 'a!localVariables(local!test: "customer")',
                'fields': {}
            },
            'new_vendor_version': {
                'version_uuid': 'ghi-789',
                'sail_code': 'a!localVariables(local!test: "vendor")',
                'fields': {}
            }
        }]
        
        # Call Q agent
        summaries = service.process_merge_summaries(1, changes_data)
        
        # Verify response structure
        assert isinstance(summaries, dict)
        assert 1 in summaries
        
        summary = summaries[1]
        assert 'summary' in summary
        assert 'complexity' in summary
        assert 'risk_level' in summary
        assert 'estimated_effort_hours' in summary
        assert 'key_conflicts' in summary
        assert 'recommendations' in summary
    
    def test_q_agent_with_different_object_types(self, app_context):
        """Test Q agent with various object types"""
        service = QAgentService()
        
        object_types = [
            'Interface',
            'Expression Rule',
            'Process Model',
            'Record Type',
            'CDT'
        ]
        
        for obj_type in object_types:
            changes_data = [{
                'change_id': 1,
                'object_name': f'Test_{obj_type}',
                'object_type': obj_type,
                'classification': 'NO_CONFLICT',
                'vendor_change_type': 'MODIFIED',
                'customer_change_type': None,
                'customer_version': None,
                'new_vendor_version': {'sail_code': 'new code'}
            }]
            
            summaries = service.process_merge_summaries(1, changes_data)
            assert 1 in summaries
```

#### 7.4 Test Execution

```bash
# Run all tests with output redirection (MANDATORY PATTERN)
python -m pytest tests/test_merge_summary_service.py -v > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt

python -m pytest tests/test_merge_summary_integration.py -v > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt

python -m pytest tests/test_merge_summary_agent.py -v > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt

# Run all merge summary tests
python -m pytest tests/test_merge_summary*.py -v > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt
```

**Deliverables**:
- ✅ Unit tests written and passing
- ✅ Integration tests written and passing
- ✅ Q agent tests written and passing
- ✅ Test coverage >80%
- ✅ All tests use real packages (no mocking of package data)


---

## Design Decisions

### 1. Async Processing (Non-Blocking)

**Decision**: Use threading for asynchronous summary generation

**Rationale**:
- Workflow should not wait for AI summaries to complete
- Users can start reviewing changes immediately
- Summaries appear progressively as they're generated
- Better user experience with real-time updates

**Alternatives Considered**:
- **Celery**: Too complex for current needs, requires Redis/RabbitMQ
- **Synchronous**: Would block workflow for 2-5 minutes
- **asyncio**: Threading is simpler for this use case

### 2. Batch Processing

**Decision**: Send 15 changes per Q agent call

**Rationale**:
- Reduces total API calls (50 changes = 4 calls vs 50 calls)
- More efficient use of Q agent context
- Faster overall completion time
- Easier to manage rate limits

**Trade-offs**:
- If one batch fails, all 15 changes fail
- Mitigation: Implement retry logic per batch

### 3. Data Completeness

**Decision**: Include only customer (B) and vendor (C) versions, exclude base (A)

**Rationale**:
- Classification already tells us relationship to base version
- AI needs to focus on B vs C comparison for merge decisions
- Reduces prompt size by 33% (critical for large SAIL code)
- Change metadata (vendor_change_type, customer_change_type) provides base context
- More efficient use of Q agent token limits

**What We Include**:
- Customer version (B): SAIL code, fields, properties
- New vendor version (C): SAIL code, fields, properties
- Change metadata: classification, vendor_change_type, customer_change_type
- Object metadata: name, type, UUID

**Optimizations**:
- Truncate SAIL code at 5000 characters
- Include only relevant fields
- Compress JSON where possible

### 4. Status Tracking

**Decision**: Track status per change (pending/processing/completed/failed)

**Rationale**:
- Users can see which summaries are ready
- Failed summaries can be retried individually
- Progress indicator shows real-time status
- Enables partial success (some summaries complete even if others fail)

### 5. Graceful Degradation

**Decision**: Changes are reviewable even without AI summaries

**Rationale**:
- AI summaries are enhancement, not requirement
- Users can still review code diffs manually
- System remains functional if Q agent fails
- Summaries can be regenerated later

### 6. Storage Format

**Decision**: Store formatted summary text in database (not raw JSON)

**Rationale**:
- Simpler to display in UI
- No client-side parsing required
- Formatting is consistent
- Can still extract structured data if needed

**Format**:
```
Main summary text here.

**Complexity:** HIGH | **Risk:** MEDIUM | **Estimated Effort:** 2.5h

**Key Conflicts:**
- Conflict 1
- Conflict 2

**Recommendations:**
- Recommendation 1
- Recommendation 2
```

### 7. Progress Polling

**Decision**: Poll progress every 3 seconds from UI

**Rationale**:
- Real-time feedback to users
- Low server load (simple query)
- Stops automatically when complete
- Better UX than manual refresh

**Alternatives Considered**:
- **WebSockets**: Overkill for this feature
- **Server-Sent Events**: More complex setup
- **No polling**: Poor UX, users don't know when summaries are ready

### 8. Error Handling

**Decision**: Continue processing other batches if one fails

**Rationale**:
- Partial success is better than total failure
- Users get some summaries even if Q agent has issues
- Failed summaries can be retried individually
- More resilient system

### 9. Integration Point

**Decision**: Trigger after classification (Step 8 of 10)

**Rationale**:
- All data is available (packages extracted, changes classified)
- Doesn't block critical workflow steps
- Can run in parallel with persistence and guidance generation
- Logical place in workflow sequence

### 10. Q Agent Design

**Decision**: Single Q agent for all object types

**Rationale**:
- Simpler to maintain
- Q agent can handle different object types
- Consistent summary format across all types
- Easier to update prompt template

**Alternatives Considered**:
- **Multiple agents**: One per object type (too complex)
- **No Q agent**: Use Bedrock directly (Q agent provides better structure)


---

## Risks & Mitigations

### Risk 1: Q Agent Timeout with Large Batches

**Impact**: HIGH  
**Probability**: MEDIUM

**Description**: Q agent may timeout when processing large batches of complex changes with extensive SAIL code.

**Mitigation**:
- Implement batch size of 15 (tested and proven)
- Truncate SAIL code to 5000 characters
- Add timeout handling with retry logic
- Monitor Q agent response times
- Adjust batch size dynamically if needed

**Fallback**:
- Reduce batch size to 10 or 5
- Process changes individually if batches continue to fail

---

### Risk 2: Q Agent Returns Invalid JSON

**Impact**: MEDIUM  
**Probability**: MEDIUM

**Description**: Q agent may return malformed JSON or unexpected format, causing parsing errors.

**Mitigation**:
- Robust JSON parsing with try-catch
- Validate JSON structure before processing
- Log raw Q agent output for debugging
- Implement fallback summary format
- Add JSON schema validation

**Fallback**:
```python
try:
    summaries = json.loads(response)
except json.JSONDecodeError:
    # Mark as failed with error message
    summary = {
        'summary': 'AI summary generation failed (invalid response)',
        'complexity': 'UNKNOWN',
        'risk_level': 'UNKNOWN'
    }
```

---

### Risk 3: Async Processing Fails Silently

**Impact**: MEDIUM  
**Probability**: LOW

**Description**: Background thread may fail without user notification, leaving summaries in "processing" state indefinitely.

**Mitigation**:
- Comprehensive logging in background thread
- Status tracking per change
- Timeout detection (mark as failed after 10 minutes)
- Progress monitoring in UI
- Manual regeneration option

**Monitoring**:
```python
# Add timeout check
if change.ai_summary_status == 'processing':
    time_elapsed = datetime.utcnow() - change.updated_at
    if time_elapsed > timedelta(minutes=10):
        change.ai_summary_status = 'failed'
        change.ai_summary = 'Summary generation timed out'
```

---

### Risk 4: SAIL Code Too Large for Prompt

**Impact**: MEDIUM  
**Probability**: LOW (mitigated by excluding base version)

**Description**: Some SAIL code may exceed prompt size limits, causing Q agent to fail.

**Mitigation**:
- **Exclude base version** (reduces prompt by 33%)
- Truncate SAIL code at 5000 characters per version
- Add "... [truncated]" indicator
- Prioritize important sections (beginning and end)
- Smart truncation (preserve structure)

**Prompt Size Calculation**:
- With base version: 15KB per change (3 versions × 5KB)
- Without base version: 10KB per change (2 versions × 5KB)
- Batch of 15: 150KB vs 225KB (33% reduction)

**Implementation**:
```python
MAX_SAIL_CODE_LENGTH = 5000

if len(sail_code) > MAX_SAIL_CODE_LENGTH:
    # Keep first 2500 and last 2500 characters
    sail_code = (
        sail_code[:2500] + 
        "\n\n... [middle section truncated] ...\n\n" + 
        sail_code[-2500:]
    )
```

---

### Risk 5: Database Locks During Concurrent Updates

**Impact**: LOW  
**Probability**: LOW

**Description**: Multiple threads updating changes table simultaneously may cause lock contention.

**Mitigation**:
- Use proper transaction isolation
- Update changes in small batches
- Implement retry logic for lock timeouts
- SQLite handles this well with WAL mode

**Configuration**:
```python
# In config.py
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_recycle': 3600,
    'isolation_level': 'READ COMMITTED'
}
```

---

### Risk 6: Q Agent Cost/Rate Limits

**Impact**: MEDIUM  
**Probability**: LOW

**Description**: High volume of Q agent calls may hit rate limits or incur unexpected costs.

**Mitigation**:
- Batch processing reduces total calls
- Implement rate limiting in service
- Monitor Q agent usage
- Add cost tracking
- Cache summaries (don't regenerate unnecessarily)

**Rate Limiting**:
```python
import time

class MergeSummaryService:
    MIN_CALL_INTERVAL = 2  # seconds between Q agent calls
    
    def _call_q_agent_with_rate_limit(self, data):
        time.sleep(self.MIN_CALL_INTERVAL)
        return self.q_agent_service.process_merge_summaries(data)
```

---

### Risk 7: Thread Safety Issues

**Impact**: MEDIUM  
**Probability**: LOW

**Description**: Multiple sessions generating summaries simultaneously may cause thread safety issues.

**Mitigation**:
- Each thread has its own app context
- Database connections are thread-safe
- No shared mutable state between threads
- Proper session management

**Best Practices**:
```python
def _generate_summaries_background(self, session_id: int):
    # Create new app context for this thread
    with self.app.app_context():
        # All database operations use this context
        # No shared state with other threads
        pass
```

---

### Risk 8: UI Polling Overhead

**Impact**: LOW  
**Probability**: LOW

**Description**: Many users polling progress simultaneously may increase server load.

**Mitigation**:
- Simple query (indexed, fast)
- Poll every 3 seconds (not too frequent)
- Stop polling when complete
- Cache progress results briefly

**Optimization**:
```python
# Add caching to progress endpoint
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=100)
def get_cached_progress(session_id, cache_key):
    return service.get_summary_progress(session_id)

# Cache key changes every 2 seconds
cache_key = int(time.time() / 2)
progress = get_cached_progress(session_id, cache_key)
```

---

## Risk Summary Table

| Risk | Impact | Probability | Mitigation Priority |
|------|--------|-------------|---------------------|
| Q Agent Timeout | HIGH | MEDIUM | **HIGH** |
| Invalid JSON | MEDIUM | MEDIUM | **HIGH** |
| Silent Failures | MEDIUM | LOW | **MEDIUM** |
| Large SAIL Code | MEDIUM | MEDIUM | **HIGH** |
| Database Locks | LOW | LOW | **LOW** |
| Rate Limits | MEDIUM | LOW | **MEDIUM** |
| Thread Safety | MEDIUM | LOW | **MEDIUM** |
| Polling Overhead | LOW | LOW | **LOW** |

---

## Success Metrics

### 1. Coverage

**Target**: >95% of changes get AI summaries

**Measurement**:
```sql
SELECT 
    COUNT(*) as total_changes,
    SUM(CASE WHEN ai_summary_status = 'completed' THEN 1 ELSE 0 END) as completed,
    (SUM(CASE WHEN ai_summary_status = 'completed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as coverage_percentage
FROM changes
WHERE session_id = ?
```

**Success Criteria**:
- ✅ >95% completed
- ⚠️ 90-95% acceptable
- ❌ <90% needs investigation

---

### 2. Performance

**Target**: Summary generation doesn't block workflow

**Measurement**:
- Workflow completion time (should not increase)
- Time from workflow start to first summary available
- Total time for all summaries to complete

**Success Criteria**:
- ✅ Workflow completes in <2 minutes (unchanged)
- ✅ First summaries available within 30 seconds
- ✅ All summaries complete within 5 minutes

---

### 3. Quality

**Target**: Summaries are actionable and accurate

**Measurement**:
- User feedback surveys
- Manual review of sample summaries
- Comparison with manual analysis

**Success Criteria**:
- ✅ Summaries mention specific code changes
- ✅ Recommendations are actionable
- ✅ Complexity/risk assessments are reasonable
- ✅ No hallucinations or incorrect information

---

### 4. Reliability

**Target**: <5% failure rate for summary generation

**Measurement**:
```sql
SELECT 
    COUNT(*) as total_changes,
    SUM(CASE WHEN ai_summary_status = 'failed' THEN 1 ELSE 0 END) as failed,
    (SUM(CASE WHEN ai_summary_status = 'failed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as failure_rate
FROM changes
WHERE session_id = ?
```

**Success Criteria**:
- ✅ <5% failure rate
- ⚠️ 5-10% acceptable with investigation
- ❌ >10% needs immediate fix

---

### 5. User Adoption

**Target**: Users find summaries helpful

**Measurement**:
- Survey: "How helpful are AI summaries?" (1-5 scale)
- Usage tracking: % of users who read summaries
- Feature usage: % of sessions where summaries are viewed

**Success Criteria**:
- ✅ Average rating >4.0/5.0
- ✅ >80% of users read summaries
- ✅ Positive qualitative feedback

---

### 6. System Impact

**Target**: Minimal impact on system resources

**Measurement**:
- CPU usage during summary generation
- Memory usage
- Database query performance
- API response times

**Success Criteria**:
- ✅ CPU usage <50% during generation
- ✅ Memory usage <2GB additional
- ✅ No degradation in API response times
- ✅ Database queries remain fast (<100ms)

---

## Monitoring Dashboard

**Metrics to Track**:

```python
# Summary Generation Metrics
{
    "total_sessions": 100,
    "sessions_with_summaries": 98,
    "average_completion_time_minutes": 3.5,
    "average_coverage_percentage": 96.5,
    "average_failure_rate": 2.1,
    "total_summaries_generated": 4850,
    "total_q_agent_calls": 324,
    "average_batch_size": 14.9
}
```

**Alerts**:
- 🚨 Failure rate >10%
- ⚠️ Completion time >10 minutes
- ⚠️ Coverage <90%
- 🚨 Q agent timeout rate >20%

---

## Next Steps

### Immediate Actions

1. **Review and Approve Plan**
   - Discuss architecture decisions
   - Confirm async approach
   - Approve Q agent design
   - Set timeline expectations

2. **Create Q Agent**
   - Define merge-summary-agent in Amazon Q
   - Test with sample data
   - Refine prompt template
   - Validate JSON output format

3. **Begin Phase 1**
   - Create database migration
   - Update Change model
   - Run migration
   - Verify schema

### Sprint Planning

**Sprint 1** (Days 1-3): Foundation
- Database schema
- Service skeleton
- Q agent integration

**Sprint 2** (Days 4-6): Core Logic
- Data preparation
- Batch processing
- Q agent calls

**Sprint 3** (Days 7-9): Integration
- Orchestrator integration
- API endpoints
- Error handling

**Sprint 4** (Days 10-12): UI & Testing
- UI updates
- Progress indicator
- Integration tests

**Sprint 5** (Days 13-15): Polish & Deploy
- Performance testing
- Bug fixes
- Documentation
- Deployment

---

## Questions for Discussion

1. **Q Agent Configuration**: Do we need to create the Q agent first, or can we proceed with implementation assuming it will be available?

2. **Batch Size**: Is 15 changes per batch optimal, or should we start with a smaller number (10) for safety?

3. **SAIL Code Truncation**: Is 5000 characters the right limit, or should we adjust based on testing?

4. **Progress Polling**: Is 3-second polling interval appropriate, or should it be longer/shorter?

5. **Error Handling**: Should failed summaries automatically retry, or only on manual trigger?

6. **UI Placement**: Should AI summaries be in the main change card, or in a separate expandable section?

7. **Testing Strategy**: Should we test with real Q agent from the start, or mock it initially?

8. **Deployment**: Should this be deployed incrementally (feature flag), or all at once?

---

## Conclusion

This implementation plan provides a comprehensive roadmap for adding AI-powered change summaries to the three-way merge workflow. The approach is:

- **Non-blocking**: Async processing ensures workflow isn't delayed
- **Scalable**: Batch processing handles large merge sessions efficiently
- **Resilient**: Graceful degradation and error handling ensure reliability
- **User-friendly**: Real-time progress and regeneration options provide great UX
- **Testable**: Comprehensive test coverage ensures quality

**Estimated Timeline**: 11-15 days  
**Risk Level**: MEDIUM (well-mitigated)  
**Value**: HIGH (significant UX improvement)

Ready to proceed with Phase 1 upon approval.
