"""
Diff hash generation for content-based comparison
"""
import hashlib
from typing import Optional
from .content_normalizer import ContentNormalizer


class DiffHashGenerator:
    """Generates content-based diff hashes using SHA-512"""

    MAX_XML_SIZE = 500_000  # 500KB limit

    def __init__(self):
        """Initialize the diff hash generator"""
        self.normalizer = ContentNormalizer()

    def generate(self, xml_content: str) -> Optional[str]:
        """
        Generate SHA-512 diff hash for XML content

        Args:
            xml_content: Raw XML content string

        Returns:
            SHA-512 hash string (128 hex characters) or None if too large
        """
        if not xml_content:
            return None

        # Check size threshold
        if len(xml_content) > self.MAX_XML_SIZE:
            print(
                f"Warning: XML content exceeds {self.MAX_XML_SIZE} bytes, "
                f"skipping diff hash generation"
            )
            return None

        try:
            # Normalize content to remove version-specific metadata
            normalized = self.normalizer.normalize(xml_content)

            # Generate SHA-512 hash
            hash_obj = hashlib.sha512(normalized.encode('utf-8'))
            return hash_obj.hexdigest()

        except Exception as e:
            print(f"Error generating diff hash: {e}")
            return None

    def generate_for_comparison(
        self,
        xml_content1: str,
        xml_content2: str
    ) -> tuple:
        """
        Generate diff hashes for two XML contents

        Args:
            xml_content1: First XML content
            xml_content2: Second XML content

        Returns:
            Tuple of (hash1, hash2), either can be None if generation fails
        """
        hash1 = self.generate(xml_content1)
        hash2 = self.generate(xml_content2)
        return (hash1, hash2)

    def compare_hashes(
        self,
        hash1: Optional[str],
        hash2: Optional[str]
    ) -> bool:
        """
        Compare two diff hashes

        Args:
            hash1: First hash
            hash2: Second hash

        Returns:
            True if hashes are equal and not None, False otherwise
        """
        if hash1 is None or hash2 is None:
            return False

        return hash1 == hash2

    def validate_hash(self, hash_str: Optional[str]) -> bool:
        """
        Validate that a string is a valid SHA-512 hash

        Args:
            hash_str: Hash string to validate

        Returns:
            True if valid SHA-512 hash format, False otherwise
        """
        if not hash_str:
            return False

        # SHA-512 produces 64 bytes = 128 hex characters
        if len(hash_str) != 128:
            return False

        # Check if all characters are valid hex
        try:
            int(hash_str, 16)
            return True
        except ValueError:
            return False

    def get_hash_info(self, xml_content: str) -> dict:
        """
        Get information about hash generation

        Args:
            xml_content: Raw XML content

        Returns:
            Dictionary with hash generation info
        """
        info = {
            'original_size': len(xml_content) if xml_content else 0,
            'exceeds_limit': len(xml_content) > self.MAX_XML_SIZE
            if xml_content else False,
            'hash': None,
            'normalized_size': 0,
            'normalization_info': {}
        }

        if info['exceeds_limit']:
            return info

        try:
            # Get normalization info
            info['normalization_info'] = (
                self.normalizer.get_normalization_info(xml_content)
            )

            # Normalize and get size
            normalized = self.normalizer.normalize(xml_content)
            info['normalized_size'] = len(normalized)

            # Generate hash
            info['hash'] = self.generate(xml_content)

        except Exception as e:
            info['error'] = str(e)

        return info
