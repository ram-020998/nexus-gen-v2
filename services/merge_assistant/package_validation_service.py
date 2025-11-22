"""
Package Validation Service for Three-Way Merge Assistant

Validates Appian application packages before processing.
"""
import os
import zipfile
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ValidationError:
    """Represents a validation error"""
    code: str
    message: str
    details: Optional[str] = None


class PackageValidationError(Exception):
    """Raised when package validation fails"""
    
    def __init__(
        self, errors: List[ValidationError], package_name: str = None
    ):
        self.errors = errors
        self.package_name = package_name
        messages = [f"{e.code}: {e.message}" for e in errors]
        super().__init__("; ".join(messages))
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'package': self.package_name or 'Unknown',
            'errors': [
                {
                    'code': e.code,
                    'message': e.message,
                    'details': e.details
                }
                for e in self.errors
            ]
        }


class PackageValidationService:
    """Validates Appian application packages"""
    
    # Required files in an Appian package (optional - not all packages have these)
    REQUIRED_FILES = []
    
    # Required directories in an Appian package
    # At least one of these should exist for a valid Appian package
    REQUIRED_DIRECTORIES = [
        'interface/',
        'rule/',
        'processModel/',
        'recordType/',
        'dataType/',
        'datatype/',  # Some packages use lowercase
        'constant/',
        'group/',
        'site/',
        'connectedSystem/',
        'webApi/'
    ]
    
    # Maximum file size (100MB by default)
    DEFAULT_MAX_SIZE = 100 * 1024 * 1024
    
    def __init__(self, max_file_size: int = None):
        """
        Initialize validation service
        
        Args:
            max_file_size: Maximum allowed file size in bytes
        """
        self.max_file_size = max_file_size or self.DEFAULT_MAX_SIZE
    
    def validate_package(
        self,
        file_path: str,
        package_name: str = None
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Validate an Appian application package
        
        Args:
            file_path: Path to the ZIP file
            package_name: Name of the package (A, B, or C) for error messages
        
        Returns:
            Tuple of (is_valid, error_dict)
            - is_valid: True if package is valid
            - error_dict: Dictionary with error details if invalid, None if valid
        
        Raises:
            PackageValidationError: If validation fails
        """
        errors = []
        
        # Validate file exists
        if not os.path.exists(file_path):
            errors.append(ValidationError(
                code='FILE_NOT_FOUND',
                message='Package file not found',
                details=f'The file {file_path} does not exist'
            ))
            raise PackageValidationError(errors, package_name)
        
        # Validate file size
        file_size = os.path.getsize(file_path)
        if file_size > self.max_file_size:
            errors.append(ValidationError(
                code='FILE_TOO_LARGE',
                message='Package file exceeds maximum size limit',
                details=(
                    f'File size: {file_size / (1024*1024):.2f}MB, '
                    f'Maximum: {self.max_file_size / (1024*1024):.2f}MB'
                )
            ))
        
        if file_size == 0:
            errors.append(ValidationError(
                code='FILE_EMPTY',
                message='Package file is empty',
                details='The file has 0 bytes'
            ))
        
        # Validate ZIP format
        if not zipfile.is_zipfile(file_path):
            errors.append(ValidationError(
                code='INVALID_ZIP_FORMAT',
                message='File is not a valid ZIP archive',
                details='The file cannot be opened as a ZIP file'
            ))
            # If not a ZIP, can't continue with other validations
            raise PackageValidationError(errors, package_name)
        
        # Validate ZIP contents
        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                # Check for corrupted ZIP
                bad_file = zf.testzip()
                if bad_file:
                    errors.append(ValidationError(
                        code='CORRUPTED_ZIP',
                        message='ZIP file is corrupted',
                        details=f'Corrupted file in archive: {bad_file}'
                    ))
                
                # Get list of files in ZIP
                file_list = zf.namelist()
                
                # Validate required files (if any)
                if self.REQUIRED_FILES:
                    missing_files = []
                    for required_file in self.REQUIRED_FILES:
                        if required_file not in file_list:
                            missing_files.append(required_file)
                    
                    if missing_files:
                        errors.append(ValidationError(
                            code='MISSING_REQUIRED_FILES',
                            message='Package is missing required Appian files',
                            details=f'Missing files: {", ".join(missing_files)}'
                        ))
                
                # Validate at least one required directory exists
                has_appian_content = False
                found_directories = []
                for required_dir in self.REQUIRED_DIRECTORIES:
                    if any(f.startswith(required_dir) for f in file_list):
                        has_appian_content = True
                        found_directories.append(required_dir)
                
                if not has_appian_content:
                    dirs_str = ", ".join(self.REQUIRED_DIRECTORIES)
                    errors.append(ValidationError(
                        code='NO_APPIAN_OBJECTS',
                        message='Package does not contain any Appian objects',
                        details=f'Expected at least one of: {dirs_str}'
                    ))
                
                # Validate XML files are parseable (sample check)
                xml_files = [f for f in file_list if f.endswith('.xml')]
                if not xml_files:
                    errors.append(ValidationError(
                        code='NO_XML_FILES',
                        message='Package does not contain any XML files',
                        details='Appian packages should contain XML object definitions'
                    ))
        
        except zipfile.BadZipFile as e:
            errors.append(ValidationError(
                code='BAD_ZIP_FILE',
                message='ZIP file is corrupted or invalid',
                details=str(e)
            ))
        except Exception as e:
            errors.append(ValidationError(
                code='VALIDATION_ERROR',
                message='Unexpected error during validation',
                details=str(e)
            ))
        
        # If there are errors, raise exception
        if errors:
            raise PackageValidationError(errors, package_name)
        
        # Package is valid
        return True, None
    
    def validate_all_packages(
        self,
        base_path: str,
        customized_path: str,
        new_vendor_path: str
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Validate all three packages
        
        Args:
            base_path: Path to base package (A)
            customized_path: Path to customized package (B)
            new_vendor_path: Path to new vendor package (C)
        
        Returns:
            Tuple of (all_valid, error_dict)
            - all_valid: True if all packages are valid
            - error_dict: Dictionary with error details if any invalid
        
        Raises:
            PackageValidationError: If any validation fails
        """
        packages = [
            (base_path, 'Base Package (A)'),
            (customized_path, 'Customized Package (B)'),
            (new_vendor_path, 'New Vendor Package (C)')
        ]
        
        for path, name in packages:
            try:
                self.validate_package(path, name)
            except PackageValidationError as e:
                # Re-raise with package name
                raise PackageValidationError(e.errors, name)
        
        return True, None
    
    def generate_error_message(
        self,
        error: PackageValidationError
    ) -> Dict[str, str]:
        """
        Generate user-friendly error message
        
        Args:
            error: PackageValidationError instance
        
        Returns:
            Dictionary with formatted error message
        """
        package_name = error.package_name or 'Unknown Package'
        
        # Determine title based on error codes
        error_codes = [e.code for e in error.errors]
        
        if 'FILE_NOT_FOUND' in error_codes:
            title = 'Package File Not Found'
            suggested_action = (
                'Please ensure you have selected the correct file and '
                'try uploading again.'
            )
        elif 'INVALID_ZIP_FORMAT' in error_codes or 'BAD_ZIP_FILE' in error_codes:
            title = 'Invalid Package Format'
            suggested_action = (
                'Please ensure you uploaded a valid ZIP file exported from '
                'Appian. The file should be a ZIP archive containing Appian '
                'application objects.'
            )
        elif 'FILE_TOO_LARGE' in error_codes:
            title = 'Package File Too Large'
            suggested_action = (
                f'Please upload a package smaller than '
                f'{self.max_file_size / (1024*1024):.0f}MB.'
            )
        elif 'MISSING_REQUIRED_FILES' in error_codes:
            title = 'Invalid Appian Package'
            suggested_action = (
                'Please ensure you uploaded a complete Appian application '
                'package exported from Appian. The package should contain '
                'application.properties and Appian object definitions.'
            )
        elif 'NO_APPIAN_OBJECTS' in error_codes:
            title = 'No Appian Objects Found'
            suggested_action = (
                'Please ensure you uploaded an Appian application package '
                'that contains interfaces, rules, process models, or other '
                'Appian objects.'
            )
        else:
            title = 'Package Validation Failed'
            suggested_action = (
                'Please check the error details and ensure you uploaded a '
                'valid Appian application package.'
            )
        
        # Build detailed message
        error_messages = []
        for err in error.errors:
            msg = err.message
            if err.details:
                msg += f' ({err.details})'
            error_messages.append(msg)
        
        message = (
            f'The {package_name} you uploaded is not valid. '
            f'{" ".join(error_messages)}'
        )
        
        return {
            'title': title,
            'message': message,
            'package': package_name,
            'technical_details': '; '.join(
                f'{e.code}: {e.details or e.message}' for e in error.errors
            ),
            'suggested_action': suggested_action,
            'error_codes': error_codes
        }
