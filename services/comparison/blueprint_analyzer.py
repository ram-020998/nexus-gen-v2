"""
Blueprint Analyzer Service.

This module analyzes Appian application blueprints using the local
appian_analyzer package.
"""

from typing import Dict, Any

from core.base_service import BaseService


class BlueprintAnalyzer(BaseService):
    """
    Analyzes Appian application blueprints.
    
    This service uses the local appian_analyzer package to extract
    and analyze Appian application structures from ZIP files.
    
    Example:
        >>> analyzer = BlueprintAnalyzer()
        >>> result = analyzer.analyze_application('path/to/app.zip')
        >>> print(result['blueprint']['metadata']['total_objects'])
    """
    
    def _initialize_dependencies(self):
        """Initialize dependencies."""
        # Import analyzer here to avoid circular imports
        try:
            from services.appian_analyzer.analyzer import AppianAnalyzer
            self._analyzer_class = AppianAnalyzer
            self._analyzer_available = True
        except ImportError:
            self._analyzer_class = None
            self._analyzer_available = False
    
    def analyze_application(self, zip_path: str) -> Dict[str, Any]:
        """
        Analyze single application using local analyzer.
        
        Extracts and analyzes all objects from an Appian application
        ZIP file, including object metadata, relationships, and SAIL code.
        
        Args:
            zip_path: Path to the Appian application ZIP file
            
        Returns:
            Dict[str, Any]: Analysis result containing:
                - blueprint: Complete application blueprint
                - object_lookup: UUID to object mapping
                - metadata: Application metadata
                
        Raises:
            Exception: If analyzer is not available or analysis fails
            
        Example:
            >>> result = analyzer.analyze_application(
            ...     'applicationArtifacts/Testing Files/SourceSelectionv2.4.0.zip'
            ... )
            >>> objects = result['blueprint']['metadata']['total_objects']
        """
        if not self._analyzer_available:
            raise Exception("Local appian_analyzer not available")
        
        try:
            analyzer = self._analyzer_class(zip_path)
            result = analyzer.analyze()
            return result
        except Exception as e:
            raise Exception(f"Blueprint analysis failed: {str(e)}")
    
    def is_available(self) -> bool:
        """
        Check if the analyzer is available.
        
        Returns:
            bool: True if analyzer is available, False otherwise
            
        Example:
            >>> if analyzer.is_available():
            ...     result = analyzer.analyze_application('app.zip')
        """
        return self._analyzer_available
