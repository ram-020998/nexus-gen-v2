"""
Content normalization for diff hash generation
Removes version-specific metadata from XML content
"""
import re


class ContentNormalizer:
    """Normalizes XML content for diff hash generation"""

    # Regex patterns for elements to remove
    VERSION_UUID_PATTERN = r'<versionUuid>.*?</versionUuid>'
    VERSION_HISTORY_PATTERN = r'<history>.*?</history>'
    SCHEMA_ATTR_PATTERN = r'\s+xmlns:\w+="[^"]*"'
    SCHEMA_INSTANCE_PATTERN = r'\s+xsi:\w+="[^"]*"'
    
    # Additional patterns for Appian-specific metadata
    MIGRATION_VERSION_PATTERN = r'<migrationVersion>.*?</migrationVersion>'
    HAUL_PATTERN = r'<\w+Haul>.*?</\w+Haul>'

    def __init__(self):
        """Initialize the content normalizer"""
        # Compile patterns for better performance
        self.patterns = [
            (re.compile(self.VERSION_UUID_PATTERN, re.DOTALL),
             'version UUID'),
            (re.compile(self.VERSION_HISTORY_PATTERN, re.DOTALL),
             'version history'),
            (re.compile(self.SCHEMA_ATTR_PATTERN), 'schema attributes'),
            (re.compile(self.SCHEMA_INSTANCE_PATTERN),
             'schema instance attributes'),
            (re.compile(self.MIGRATION_VERSION_PATTERN, re.DOTALL),
             'migration version'),
            (re.compile(self.HAUL_PATTERN, re.DOTALL), 'haul elements'),
        ]

    def normalize(self, xml_content: str) -> str:
        """
        Remove version-specific metadata from XML

        Args:
            xml_content: Raw XML content string

        Returns:
            Normalized XML content with metadata removed
        """
        if not xml_content:
            return ""

        normalized = xml_content

        # Apply all normalization patterns
        for pattern, description in self.patterns:
            try:
                normalized = pattern.sub('', normalized)
            except Exception as e:
                print(
                    f"Warning: Failed to remove {description}: {e}"
                )

        # Remove extra whitespace created by removals
        normalized = self._clean_whitespace(normalized)

        return normalized.strip()

    def _clean_whitespace(self, content: str) -> str:
        """
        Clean up extra whitespace from content

        Args:
            content: Content with potential extra whitespace

        Returns:
            Content with normalized whitespace
        """
        # Replace multiple consecutive newlines with single newline
        content = re.sub(r'\n\s*\n', '\n', content)

        # Replace multiple spaces with single space
        content = re.sub(r' +', ' ', content)

        return content

    def normalize_for_comparison(
        self,
        xml_content1: str,
        xml_content2: str
    ) -> tuple:
        """
        Normalize two XML contents for comparison

        Args:
            xml_content1: First XML content
            xml_content2: Second XML content

        Returns:
            Tuple of (normalized_content1, normalized_content2)
        """
        return (
            self.normalize(xml_content1),
            self.normalize(xml_content2)
        )

    def get_normalization_info(self, xml_content: str) -> dict:
        """
        Get information about what was normalized

        Args:
            xml_content: Raw XML content

        Returns:
            Dictionary with counts of removed elements
        """
        info = {}

        for pattern, description in self.patterns:
            matches = pattern.findall(xml_content)
            info[description] = len(matches)

        return info
