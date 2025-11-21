"""
Version history extraction for Appian objects
"""
import xml.etree.ElementTree as ET
from typing import List, Optional
from datetime import datetime
from .models import VersionInfo


class VersionHistoryExtractor:
    """Extracts and manages version history from Appian XML"""

    def __init__(self):
        self.namespaces = {
            'a': 'http://www.appian.com/ae/types/2009',
            'xsd': 'http://www.w3.org/2001/XMLSchema'
        }

    def extract_from_xml(self, root: ET.Element) -> List[VersionInfo]:
        """
        Extract version history from XML metadata

        Args:
            root: Root XML element

        Returns:
            List of VersionInfo objects
        """
        version_history = []

        # Look for history element
        history_elem = root.find('.//history')
        if history_elem is None:
            # Try with namespace
            history_elem = root.find('.//a:history', self.namespaces)

        if history_elem is None:
            return version_history

        # Extract version entries
        for version_elem in history_elem.findall('.//version'):
            version_info = self._parse_version_element(version_elem)
            if version_info:
                version_history.append(version_info)

        # Also try with namespace
        for version_elem in history_elem.findall('.//a:version',
                                                  self.namespaces):
            version_info = self._parse_version_element(version_elem)
            if version_info:
                version_history.append(version_info)

        return version_history

    def _parse_version_element(
        self,
        version_elem: ET.Element
    ) -> Optional[VersionInfo]:
        """
        Parse a single version element

        Args:
            version_elem: Version XML element

        Returns:
            VersionInfo object or None if parsing fails
        """
        try:
            # Extract version UUID
            version_uuid_elem = version_elem.find('versionUuid')
            if version_uuid_elem is None:
                version_uuid_elem = version_elem.find(
                    'a:versionUuid',
                    self.namespaces
                )

            if version_uuid_elem is None or not version_uuid_elem.text:
                return None

            version_uuid = version_uuid_elem.text.strip()

            # Extract timestamp
            timestamp_elem = version_elem.find('timestamp')
            if timestamp_elem is None:
                timestamp_elem = version_elem.find(
                    'a:timestamp',
                    self.namespaces
                )

            timestamp = self._parse_timestamp(timestamp_elem)

            # Extract author
            author_elem = version_elem.find('author')
            if author_elem is None:
                author_elem = version_elem.find('a:author', self.namespaces)

            author = ""
            if author_elem is not None and author_elem.text:
                author = author_elem.text.strip()

            # Extract description
            desc_elem = version_elem.find('description')
            if desc_elem is None:
                desc_elem = version_elem.find(
                    'a:description',
                    self.namespaces
                )

            description = ""
            if desc_elem is not None and desc_elem.text:
                description = desc_elem.text.strip()

            return VersionInfo(
                version_uuid=version_uuid,
                timestamp=timestamp,
                author=author,
                description=description
            )

        except Exception as e:
            # Log warning but don't fail
            print(f"Warning: Failed to parse version element: {e}")
            return None

    def _parse_timestamp(
        self,
        timestamp_elem: Optional[ET.Element]
    ) -> datetime:
        """
        Parse timestamp from XML element

        Args:
            timestamp_elem: Timestamp XML element

        Returns:
            datetime object, defaults to epoch if parsing fails
        """
        if timestamp_elem is None or not timestamp_elem.text:
            return datetime.fromtimestamp(0)

        try:
            timestamp_str = timestamp_elem.text.strip()

            # Try ISO format first
            try:
                return datetime.fromisoformat(
                    timestamp_str.replace('Z', '+00:00')
                )
            except ValueError:
                pass

            # Try common Appian timestamp formats
            formats = [
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue

            # If all parsing fails, return epoch
            print(f"Warning: Could not parse timestamp: {timestamp_str}")
            return datetime.fromtimestamp(0)

        except Exception as e:
            print(f"Warning: Timestamp parsing error: {e}")
            return datetime.fromtimestamp(0)

    def find_version_in_history(
        self,
        target_uuid: str,
        history: List[VersionInfo]
    ) -> bool:
        """
        Check if version UUID exists in history

        Args:
            target_uuid: Version UUID to search for
            history: List of VersionInfo objects

        Returns:
            True if version UUID found in history, False otherwise
        """
        if not target_uuid or not history:
            return False

        return any(
            version.version_uuid == target_uuid
            for version in history
        )

    def extract_current_version_uuid(
        self,
        root: ET.Element
    ) -> Optional[str]:
        """
        Extract current version UUID from XML

        Args:
            root: Root XML element

        Returns:
            Current version UUID or None
        """
        # Look for versionUuid at root level
        version_uuid_elem = root.find('.//versionUuid')
        if version_uuid_elem is None:
            version_uuid_elem = root.find(
                './/a:versionUuid',
                self.namespaces
            )

        if version_uuid_elem is not None and version_uuid_elem.text:
            return version_uuid_elem.text.strip()

        return None
