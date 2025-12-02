"""
SAIL Code Diff Service
Generates GitHub-style unified diffs for SAIL code comparison
"""
import difflib
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class DiffLineType(Enum):
    """Types of diff lines"""
    UNCHANGED = "unchanged"
    ADDED = "added"
    REMOVED = "removed"
    CONTEXT = "context"


@dataclass
class DiffLine:
    """Represents a single line in a diff"""
    line_type: DiffLineType
    content: str
    old_line_num: Optional[int] = None
    new_line_num: Optional[int] = None


@dataclass
class DiffHunk:
    """Represents a hunk (section) of changes in a diff"""
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: List[DiffLine]


class SailDiffService:
    """Service for generating SAIL code diffs"""
    
    def __init__(self, context_lines: int = 3):
        """
        Initialize the diff service
        
        Args:
            context_lines: Number of context lines to show around changes
        """
        self.context_lines = context_lines
    
    def generate_unified_diff(
        self,
        old_code: Optional[str],
        new_code: Optional[str],
        old_label: str = "Before",
        new_label: str = "After"
    ) -> List[DiffHunk]:
        """
        Generate a unified diff between two SAIL code strings
        
        Args:
            old_code: Original SAIL code
            new_code: New SAIL code
            old_label: Label for old version
            new_label: Label for new version
            
        Returns:
            List of DiffHunk objects representing the changes
        """
        # Handle None cases
        old_code = old_code or ""
        new_code = new_code or ""
        
        # Split into lines
        old_lines = old_code.splitlines(keepends=False)
        new_lines = new_code.splitlines(keepends=False)
        
        # Generate unified diff
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=old_label,
            tofile=new_label,
            lineterm='',
            n=self.context_lines
        )
        
        # Parse diff into hunks
        hunks = self._parse_unified_diff(list(diff), old_lines, new_lines)
        
        return hunks
    
    def _parse_unified_diff(
        self,
        diff_lines: List[str],
        old_lines: List[str],
        new_lines: List[str]
    ) -> List[DiffHunk]:
        """
        Parse unified diff output into structured hunks
        
        Args:
            diff_lines: Raw diff output lines
            old_lines: Original code lines
            new_lines: New code lines
            
        Returns:
            List of DiffHunk objects
        """
        hunks = []
        current_hunk = None
        old_line_num = 0
        new_line_num = 0
        
        for line in diff_lines:
            # Skip header lines
            if line.startswith('---') or line.startswith('+++'):
                continue
            
            # Parse hunk header
            if line.startswith('@@'):
                if current_hunk:
                    hunks.append(current_hunk)
                
                # Parse @@ -old_start,old_count +new_start,new_count @@
                parts = line.split('@@')[1].strip().split()
                old_part = parts[0][1:]  # Remove '-'
                new_part = parts[1][1:]  # Remove '+'
                
                old_start, old_count = self._parse_range(old_part)
                new_start, new_count = self._parse_range(new_part)
                
                current_hunk = DiffHunk(
                    old_start=old_start,
                    old_count=old_count,
                    new_start=new_start,
                    new_count=new_count,
                    lines=[]
                )
                
                old_line_num = old_start
                new_line_num = new_start
                continue
            
            if not current_hunk:
                continue
            
            # Parse diff line
            if line.startswith('-'):
                # Removed line
                current_hunk.lines.append(DiffLine(
                    line_type=DiffLineType.REMOVED,
                    content=line[1:],
                    old_line_num=old_line_num,
                    new_line_num=None
                ))
                old_line_num += 1
            elif line.startswith('+'):
                # Added line
                current_hunk.lines.append(DiffLine(
                    line_type=DiffLineType.ADDED,
                    content=line[1:],
                    old_line_num=None,
                    new_line_num=new_line_num
                ))
                new_line_num += 1
            else:
                # Context line (unchanged)
                content = line[1:] if line.startswith(' ') else line
                current_hunk.lines.append(DiffLine(
                    line_type=DiffLineType.UNCHANGED,
                    content=content,
                    old_line_num=old_line_num,
                    new_line_num=new_line_num
                ))
                old_line_num += 1
                new_line_num += 1
        
        # Add last hunk
        if current_hunk:
            hunks.append(current_hunk)
        
        return hunks
    
    def _parse_range(self, range_str: str) -> Tuple[int, int]:
        """
        Parse a range string like '1,5' or '1' into (start, count)
        
        Args:
            range_str: Range string from diff header
            
        Returns:
            Tuple of (start_line, line_count)
        """
        if ',' in range_str:
            start, count = range_str.split(',')
            return int(start), int(count)
        else:
            return int(range_str), 1
    
    def has_changes(self, old_code: Optional[str], new_code: Optional[str]) -> bool:
        """
        Check if there are any changes between two code strings
        
        Args:
            old_code: Original code
            new_code: New code
            
        Returns:
            True if there are changes, False otherwise
        """
        old_code = old_code or ""
        new_code = new_code or ""
        return old_code.strip() != new_code.strip()
    
    def get_change_stats(
        self,
        old_code: Optional[str],
        new_code: Optional[str]
    ) -> Dict[str, int]:
        """
        Get statistics about changes between two code strings
        
        Args:
            old_code: Original code
            new_code: New code
            
        Returns:
            Dictionary with 'additions', 'deletions', 'changes' counts
        """
        old_code = old_code or ""
        new_code = new_code or ""
        
        old_lines = old_code.splitlines()
        new_lines = new_code.splitlines()
        
        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        
        additions = 0
        deletions = 0
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'insert':
                additions += j2 - j1
            elif tag == 'delete':
                deletions += i2 - i1
            elif tag == 'replace':
                deletions += i2 - i1
                additions += j2 - j1
        
        return {
            'additions': additions,
            'deletions': deletions,
            'changes': additions + deletions
        }
