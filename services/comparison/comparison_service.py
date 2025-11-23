"""
Comparison Service.

This module orchestrates the complete comparison workflow for Appian
applications, including analysis, comparison, and result storage.
"""

import time
from pathlib import Path
from typing import Optional

from core.base_service import BaseService
from services.comparison.comparison_request_manager import ComparisonRequestManager
from services.comparison.blueprint_analyzer import BlueprintAnalyzer
from services.comparison.comparison_engine import ComparisonEngine
from models import ComparisonRequest


class ComparisonService(BaseService):
    """
    Main service orchestrating the comparison process.
    
    This service coordinates the entire workflow of comparing two Appian
    application versions, from initial upload through analysis, comparison,
    and result storage.
    
    Example:
        >>> service = ComparisonService()
        >>> request = service.process_comparison(
        ...     'path/to/old.zip',
        ...     'path/to/new.zip'
        ... )
        >>> print(request.status)  # 'completed'
    """
    
    def _initialize_dependencies(self):
        """Initialize service dependencies."""
        self.request_manager = ComparisonRequestManager(self._container)
        self.blueprint_analyzer = BlueprintAnalyzer(self._container)
    
    def process_comparison(
        self,
        old_zip_path: str,
        new_zip_path: str
    ) -> ComparisonRequest:
        """
        Process complete comparison workflow.
        
        Orchestrates the full comparison process including:
        1. Creating a comparison request
        2. Analyzing both application versions
        3. Comparing the results
        4. Storing the comparison data
        
        Uses enhanced comparison system when available, with fallback
        to basic comparison.
        
        Args:
            old_zip_path: Path to old application ZIP file
            new_zip_path: Path to new application ZIP file
            
        Returns:
            ComparisonRequest: Completed comparison request with results
            
        Raises:
            Exception: If analysis or comparison fails
            
        Example:
            >>> request = service.process_comparison(
            ...     'applicationArtifacts/Testing Files/SourceSelectionv2.4.0.zip',
            ...     'applicationArtifacts/Testing Files/SourceSelectionv2.6.0.zip'
            ... )
        """
        start_time = time.time()
        
        # Extract app names from file paths
        old_app_name = Path(old_zip_path).stem
        new_app_name = Path(new_zip_path).stem
        
        # Create request
        request = self.request_manager.create_request(old_app_name, new_app_name)
        
        # Create request-specific logger
        try:
            from services.appian_analyzer.logger import create_request_logger
            logger = create_request_logger(request.reference_id)
        except ImportError:
            # Fallback to basic logging if logger not available
            import logging
            logger = logging.getLogger(__name__)
        
        try:
            if not self.blueprint_analyzer.is_available():
                logger.error("Local appian_analyzer not available")
                raise Exception("Local appian_analyzer not available")
            
            logger.info(f"Starting comparison: {old_app_name} vs {new_app_name}")
            logger.log_stage("Upload", {
                "old_file": old_zip_path,
                "new_file": new_zip_path,
                "old_size_mb": f"{Path(old_zip_path).stat().st_size / 1024 / 1024:.2f}",
                "new_size_mb": f"{Path(new_zip_path).stat().st_size / 1024 / 1024:.2f}"
            })
            
            # Analyze both applications
            logger.log_stage("Analyzing old version", {"app": old_app_name})
            old_result = self.blueprint_analyzer.analyze_application(old_zip_path)
            old_obj_count = old_result['blueprint']['metadata']['total_objects']
            logger.info(f"Old version analyzed: {old_obj_count} objects")
            
            logger.log_stage("Analyzing new version", {"app": new_app_name})
            new_result = self.blueprint_analyzer.analyze_application(new_zip_path)
            new_obj_count = new_result['blueprint']['metadata']['total_objects']
            logger.info(f"New version analyzed: {new_obj_count} objects")
            
            # Use enhanced comparison if available, otherwise fall back
            comparison = self._perform_comparison(
                old_result,
                new_result,
                old_app_name,
                new_app_name,
                logger
            )
            
            total_changes = comparison.get('comparison_summary', {}).get('total_changes', 0)
            impact_level = comparison.get('comparison_summary', {}).get('impact_level', 'UNKNOWN')
            
            logger.log_metrics({
                "total_changes": total_changes,
                "impact_level": impact_level,
                "old_objects": old_obj_count,
                "new_objects": new_obj_count
            })
            
            # Calculate processing time
            processing_time = int(time.time() - start_time)
            
            # Save results
            self.request_manager.save_results(
                request.id,
                old_result["blueprint"],
                new_result["blueprint"],
                comparison,
                processing_time
            )
            
            logger.log_completion(
                status='success',
                total_changes=total_changes,
                processing_time=f"{processing_time}s"
            )
            
            return request
            
        except Exception as e:
            logger.error(f"Comparison failed: {str(e)}", exc_info=True)
            self.request_manager.update_status(request.id, 'error', str(e))
            raise e
    
    def _perform_comparison(
        self,
        old_result: dict,
        new_result: dict,
        old_app_name: str,
        new_app_name: str,
        logger
    ) -> dict:
        """
        Perform comparison using enhanced or basic method.
        
        Args:
            old_result: Analysis result for old version
            new_result: Analysis result for new version
            old_app_name: Name of old application
            new_app_name: Name of new application
            logger: Logger instance
            
        Returns:
            dict: Comparison results
        """
        # Try enhanced comparison first
        try:
            from services.appian_analyzer.enhanced_comparison_service import (
                EnhancedComparisonService
            )
            logger.log_stage("Comparison", {"method": "enhanced"})
            enhanced_service = EnhancedComparisonService()
            return enhanced_service.compare_applications(
                old_result,
                new_result,
                old_app_name,
                new_app_name
            )
        except Exception as enhanced_error:
            logger.warning(f"Enhanced comparison failed: {str(enhanced_error)}")
            logger.info("Falling back to basic comparison")
            
            # Fallback to basic comparison
            logger.log_stage("Comparison", {"method": "basic"})
            engine = ComparisonEngine(old_app_name, new_app_name, self._container)
            return engine.compare_results(old_result, new_result)
    
    def get_request_details(
        self,
        request_id: int
    ) -> Optional[ComparisonRequest]:
        """
        Get detailed request information.
        
        Args:
            request_id: ID of the comparison request
            
        Returns:
            Optional[ComparisonRequest]: Request details if found,
                None otherwise
                
        Example:
            >>> details = service.get_request_details(1)
            >>> print(details.status)
        """
        return self.request_manager.get_request(request_id)
    
    def get_all_requests(self) -> list:
        """
        Get all comparison requests.
        
        Returns:
            list: List of all comparison requests ordered by date
            
        Example:
            >>> requests = service.get_all_requests()
            >>> for req in requests:
            ...     print(f"{req.reference_id}: {req.status}")
        """
        return self.request_manager.get_all_requests()
