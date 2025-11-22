"""
Blueprint Generation Service for Three-Way Merge Assistant

Wraps the existing AppianAnalyzer to generate blueprints for
merge session packages with parallel processing support.
"""
import os
from typing import Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from services.appian_analyzer import AppianAnalyzer


class BlueprintGenerationError(Exception):
    """Raised when blueprint generation fails"""
    pass


class BlueprintGenerationService:
    """
    Service for generating blueprints from Appian packages.
    Wraps AppianAnalyzer with error handling and parallel processing.
    """

    def __init__(self):
        """Initialize the blueprint generation service"""
        pass

    def generate_blueprint(self, zip_path: str) -> Dict[str, Any]:
        """
        Generate blueprint for a single Appian package.

        Args:
            zip_path: Path to the Appian package ZIP file

        Returns:
            Dictionary containing blueprint and object_lookup

        Raises:
            BlueprintGenerationError: If generation fails
        """
        if not os.path.exists(zip_path):
            raise BlueprintGenerationError(
                f"Package file not found: {zip_path}"
            )

        if not zip_path.endswith('.zip'):
            raise BlueprintGenerationError(
                f"Invalid file format: {zip_path}. Expected ZIP file."
            )

        try:
            # Initialize analyzer
            analyzer = AppianAnalyzer(zip_path)

            # Perform analysis
            result = analyzer.analyze()

            # Close the analyzer
            analyzer.close()

            # Validate that we got a valid blueprint
            if not result or 'blueprint' not in result:
                raise BlueprintGenerationError(
                    f"Invalid blueprint structure generated from {zip_path}"
                )

            # Check if any objects were parsed
            blueprint = result['blueprint']
            if 'metadata' in blueprint:
                total_objects = blueprint['metadata'].get('total_objects', 0)
                if total_objects == 0:
                    raise BlueprintGenerationError(
                        f"No Appian objects found in {zip_path}. "
                        "This may not be a valid Appian package."
                    )

            return result

        except BlueprintGenerationError:
            # Re-raise our own exceptions
            raise
        except Exception as e:
            raise BlueprintGenerationError(
                f"Failed to generate blueprint for {zip_path}: {str(e)}"
            ) from e

    def generate_all_blueprints(
        self,
        base_path: str,
        customized_path: str,
        new_vendor_path: str,
        logger=None
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """
        Generate blueprints for all three packages in parallel.

        Args:
            base_path: Path to base package (A)
            customized_path: Path to customized package (B)
            new_vendor_path: Path to new vendor package (C)
            logger: Optional logger instance

        Returns:
            Tuple of (base_blueprint, customized_blueprint,
            new_vendor_blueprint)

        Raises:
            BlueprintGenerationError: If any generation fails
        """
        import time
        
        packages = {
            'base': base_path,
            'customized': customized_path,
            'new_vendor': new_vendor_path
        }

        # Validate all paths exist
        for name, path in packages.items():
            if not os.path.exists(path):
                raise BlueprintGenerationError(
                    f"{name.capitalize()} package not found: {path}"
                )

        results = {}
        errors = {}

        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all tasks
            future_to_package = {}
            for name, path in packages.items():
                if logger:
                    logger.log_blueprint_generation_start(name)
                start_time = time.time()
                future = executor.submit(self.generate_blueprint, path)
                future_to_package[future] = (name, start_time)

            # Collect results as they complete
            for future in as_completed(future_to_package):
                package_name, start_time = future_to_package[future]
                elapsed = time.time() - start_time
                try:
                    result = future.result()
                    results[package_name] = result
                    
                    # Log completion
                    if logger:
                        total_objects = result.get('blueprint', {}).get(
                            'metadata', {}
                        ).get('total_objects', 0)
                        logger.log_blueprint_generation_complete(
                            package_name,
                            total_objects,
                            elapsed
                        )
                except Exception as e:
                    errors[package_name] = str(e)
                    if logger:
                        logger.log_blueprint_generation_error(
                            package_name,
                            str(e)
                        )

        # Check if any generation failed
        if errors:
            error_msg = "Blueprint generation failed for: " + ", ".join(
                f"{name} ({error})" for name, error in errors.items()
            )
            raise BlueprintGenerationError(error_msg)

        # Return in the expected order
        return (
            results['base'],
            results['customized'],
            results['new_vendor']
        )

    def _extract_package_name(self, zip_path: str) -> str:
        """
        Extract package name from ZIP file path.

        Args:
            zip_path: Path to ZIP file

        Returns:
            Package name without extension
        """
        return os.path.basename(zip_path).replace('.zip', '')
