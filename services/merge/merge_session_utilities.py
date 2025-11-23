"""
Merge Session Utilities

Utility functions for merge session management including
reference ID generation and package name extraction.
"""
import os
from models import MergeSession


class MergeSessionUtilities:
    """
    Utility functions for merge session operations
    
    Provides helper methods for generating reference IDs,
    extracting package names, and other utility operations.
    """
    
    @staticmethod
    def generate_reference_id() -> str:
        """
        Generate unique reference ID for merge session

        Returns:
            Reference ID in format MRG_001, MRG_002, etc.
        """
        # Get the highest existing reference ID
        last_session = MergeSession.query.order_by(
            MergeSession.id.desc()
        ).first()

        if last_session and last_session.reference_id:
            # Extract number from last reference ID
            try:
                last_num = int(last_session.reference_id.split('_')[1])
                next_num = last_num + 1
            except (IndexError, ValueError):
                next_num = 1
        else:
            next_num = 1

        return f"MRG_{next_num:03d}"

    @staticmethod
    def extract_package_name(zip_path: str) -> str:
        """
        Extract package name from ZIP file path

        Args:
            zip_path: Path to ZIP file

        Returns:
            Package name without extension
        """
        return os.path.basename(zip_path).replace('.zip', '')
