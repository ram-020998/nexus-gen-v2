"""
Merge Guidance Service

Generates merge strategies and recommendations for each change in the
three-way merge workflow. Identifies vendor additions, modifications,
and conflict sections to provide actionable guidance for users.
"""
from typing import Dict, Any, List, Optional
from enum import Enum


class MergeStrategy(Enum):
    """Merge strategy types"""
    INCORPORATE_VENDOR_ADDITIONS = "INCORPORATE_VENDOR_ADDITIONS"
    ADOPT_VENDOR_CHANGES = "ADOPT_VENDOR_CHANGES"
    KEEP_CUSTOMER_VERSION = "KEEP_CUSTOMER_VERSION"
    MANUAL_MERGE_REQUIRED = "MANUAL_MERGE_REQUIRED"
    REVIEW_VENDOR_REMOVAL = "REVIEW_VENDOR_REMOVAL"


class MergeGuidanceService:
    """
    Generates merge guidance and recommendations

    Analyzes changes to provide specific guidance on how to incorporate
    vendor changes into customer versions while preserving customizations.
    """

    def __init__(self):
        """Initialize the merge guidance service"""
        pass

    def generate_guidance(
        self,
        change: Dict[str, Any],
        base_object: Optional[Dict[str, Any]],
        customer_object: Optional[Dict[str, Any]],
        vendor_object: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate merge guidance for a change

        Args:
            change: Change object with classification
            base_object: Object from base package (A), or None if not present
            customer_object: Object from customized package (B), or None
            vendor_object: Object from new vendor package (C), or None

        Returns:
            Dictionary with:
            {
                'strategy': 'INCORPORATE_VENDOR_ADDITIONS',
                'recommendations': [list of recommendation strings],
                'vendor_additions': [list of additions],
                'vendor_modifications': [list of modifications],
                'conflict_sections': [list of conflicts]
            }
        """
        classification = change.get('classification', '')

        # Initialize guidance structure
        guidance = {
            'strategy': None,
            'recommendations': [],
            'vendor_additions': [],
            'vendor_modifications': [],
            'conflict_sections': []
        }

        # Generate guidance based on classification
        if classification == 'NO_CONFLICT':
            guidance = self._generate_no_conflict_guidance(
                change,
                base_object,
                vendor_object
            )
        elif classification == 'CONFLICT':
            guidance = self._generate_conflict_guidance(
                change,
                base_object,
                customer_object,
                vendor_object
            )
        elif classification == 'CUSTOMER_ONLY':
            guidance = self._generate_customer_only_guidance(
                change,
                customer_object
            )
        elif classification == 'REMOVED_BUT_CUSTOMIZED':
            guidance = self._generate_removed_but_customized_guidance(
                change,
                customer_object
            )

        return guidance

    def _generate_no_conflict_guidance(
        self,
        change: Dict[str, Any],
        base_object: Optional[Dict[str, Any]],
        vendor_object: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate guidance for NO_CONFLICT changes

        These are vendor-only changes that should be adopted into
        the customer version.

        Args:
            change: Change object
            base_object: Base object (A)
            vendor_object: Vendor object (C)

        Returns:
            Guidance dictionary
        """
        guidance = {
            'strategy': MergeStrategy.ADOPT_VENDOR_CHANGES.value,
            'recommendations': [],
            'vendor_additions': [],
            'vendor_modifications': [],
            'conflict_sections': []
        }

        # Identify what the vendor changed
        if base_object is None:
            # New object added by vendor
            guidance['recommendations'].append(
                f"This is a new {change.get('type', 'object')} added by the "
                f"vendor. Review and adopt it into your customized version."
            )
            guidance['vendor_additions'].append({
                'type': 'new_object',
                'description': f"New {change.get('type', 'object')}: "
                f"{change.get('name', 'Unknown')}"
            })
        elif vendor_object is None:
            # Object removed by vendor
            guidance['strategy'] = MergeStrategy.REVIEW_VENDOR_REMOVAL.value
            guidance['recommendations'].append(
                f"The vendor removed this {change.get('type', 'object')}. "
                f"Consider removing it from your customized version as well."
            )
        else:
            # Object modified by vendor
            vendor_mods = self._identify_vendor_modifications(
                base_object,
                vendor_object
            )
            guidance['vendor_modifications'] = vendor_mods

            if vendor_mods:
                guidance['recommendations'].append(
                    f"The vendor made {len(vendor_mods)} modification(s) to "
                    f"this {change.get('type', 'object')}. Review and adopt "
                    f"these changes into your customized version."
                )

                # Add specific recommendations for each modification
                for mod in vendor_mods:
                    guidance['recommendations'].append(
                        f"  - {mod.get('description', 'Modification detected')}"
                    )

        return guidance

    def _generate_conflict_guidance(
        self,
        change: Dict[str, Any],
        base_object: Optional[Dict[str, Any]],
        customer_object: Optional[Dict[str, Any]],
        vendor_object: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate guidance for CONFLICT changes

        These require careful analysis to identify what needs to be
        incorporated from the vendor while preserving customer changes.

        Args:
            change: Change object
            base_object: Base object (A)
            customer_object: Customer object (B)
            vendor_object: Vendor object (C)

        Returns:
            Guidance dictionary
        """
        guidance = {
            'strategy': MergeStrategy.MANUAL_MERGE_REQUIRED.value,
            'recommendations': [],
            'vendor_additions': [],
            'vendor_modifications': [],
            'conflict_sections': []
        }

        # Identify vendor additions (new features not in customer version)
        if base_object and vendor_object and customer_object:
            vendor_additions = self._identify_vendor_additions(
                base_object,
                vendor_object,
                customer_object
            )
            guidance['vendor_additions'] = vendor_additions

            # Identify vendor modifications
            vendor_mods = self._identify_vendor_modifications(
                base_object,
                vendor_object
            )
            guidance['vendor_modifications'] = vendor_mods

            # Identify conflict sections
            conflicts = self._identify_conflict_sections(
                base_object,
                customer_object,
                vendor_object
            )
            guidance['conflict_sections'] = conflicts

            # Generate strategy based on findings
            if vendor_additions and not conflicts:
                guidance['strategy'] = (
                    MergeStrategy.INCORPORATE_VENDOR_ADDITIONS.value
                )
                guidance['recommendations'].append(
                    f"The vendor added {len(vendor_additions)} new "
                    f"feature(s) that don't conflict with your customizations. "
                    f"Incorporate these additions into your customized version."
                )
            elif conflicts:
                guidance['recommendations'].append(
                    f"Both you and the vendor modified {len(conflicts)} "
                    f"section(s) of this {change.get('type', 'object')}. "
                    f"Manual merge required to combine both changes."
                )

            # Add specific recommendations
            for addition in vendor_additions:
                guidance['recommendations'].append(
                    f"  + Add: {addition.get('description', 'New feature')}"
                )

            for conflict in conflicts:
                guidance['recommendations'].append(
                    f"  ⚠ Merge: {conflict.get('description', 'Conflicting section')}"
                )

        return guidance

    def _generate_customer_only_guidance(
        self,
        change: Dict[str, Any],
        customer_object: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate guidance for CUSTOMER_ONLY changes

        These are customer customizations that don't conflict with vendor.

        Args:
            change: Change object
            customer_object: Customer object (B)

        Returns:
            Guidance dictionary
        """
        guidance = {
            'strategy': MergeStrategy.KEEP_CUSTOMER_VERSION.value,
            'recommendations': [
                f"This {change.get('type', 'object')} was only modified by "
                f"you (not by the vendor). Keep your customized version."
            ],
            'vendor_additions': [],
            'vendor_modifications': [],
            'conflict_sections': []
        }

        return guidance

    def _generate_removed_but_customized_guidance(
        self,
        change: Dict[str, Any],
        customer_object: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate guidance for REMOVED_BUT_CUSTOMIZED changes

        The vendor removed this object but the customer customized it.

        Args:
            change: Change object
            customer_object: Customer object (B)

        Returns:
            Guidance dictionary
        """
        guidance = {
            'strategy': MergeStrategy.KEEP_CUSTOMER_VERSION.value,
            'recommendations': [
                f"The vendor removed this {change.get('type', 'object')}, "
                f"but you have customizations. Consider keeping your version "
                f"unless the vendor's removal was intentional and necessary."
            ],
            'vendor_additions': [],
            'vendor_modifications': [],
            'conflict_sections': []
        }

        return guidance

    def _identify_vendor_additions(
        self,
        base_object: Dict[str, Any],
        vendor_object: Dict[str, Any],
        customer_object: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify new code/features added by vendor

        Finds additions in vendor version (A→C) that don't exist in
        customer version (B).

        Args:
            base_object: Base object (A)
            vendor_object: Vendor object (C)
            customer_object: Customer object (B)

        Returns:
            List of vendor additions
        """
        additions = []

        # Check SAIL code additions
        if 'sail_code' in vendor_object and 'sail_code' in base_object:
            vendor_sail = vendor_object.get('sail_code', '')
            base_sail = base_object.get('sail_code', '')
            customer_sail = customer_object.get('sail_code', '')

            # Simple line-based diff to find additions
            vendor_lines = set(vendor_sail.split('\n'))
            base_lines = set(base_sail.split('\n'))
            customer_lines = set(customer_sail.split('\n'))

            # Lines added by vendor
            vendor_added_lines = vendor_lines - base_lines

            # Lines added by vendor but not in customer
            new_vendor_lines = vendor_added_lines - customer_lines

            if new_vendor_lines:
                additions.append({
                    'type': 'sail_code',
                    'description': f"Vendor added {len(new_vendor_lines)} "
                    f"new line(s) of SAIL code",
                    'content': '\n'.join(sorted(new_vendor_lines)),
                    'location': 'SAIL code'
                })

        # Check field additions (for record types)
        if 'fields' in vendor_object and 'fields' in base_object:
            vendor_fields = vendor_object.get('fields', [])
            base_fields = base_object.get('fields', [])
            customer_fields = customer_object.get('fields', [])

            # Get field names
            base_field_names = {
                f.get('name') for f in base_fields if isinstance(f, dict)
            }
            vendor_field_names = {
                f.get('name') for f in vendor_fields if isinstance(f, dict)
            }
            customer_field_names = {
                f.get('name') for f in customer_fields if isinstance(f, dict)
            }

            # Fields added by vendor but not in customer
            new_vendor_fields = (
                vendor_field_names - base_field_names - customer_field_names
            )

            if new_vendor_fields:
                additions.append({
                    'type': 'fields',
                    'description': f"Vendor added {len(new_vendor_fields)} "
                    f"new field(s)",
                    'content': list(new_vendor_fields),
                    'location': 'Fields'
                })

        # Check property additions
        if 'properties' in vendor_object and 'properties' in base_object:
            vendor_props = vendor_object.get('properties', {})
            base_props = base_object.get('properties', {})
            customer_props = customer_object.get('properties', {})

            # Properties added by vendor but not in customer
            new_vendor_props = set(vendor_props.keys()) - \
                set(base_props.keys())
            new_vendor_props = new_vendor_props - set(customer_props.keys())

            if new_vendor_props:
                additions.append({
                    'type': 'properties',
                    'description': f"Vendor added {len(new_vendor_props)} "
                    f"new propert(y/ies)",
                    'content': {k: vendor_props[k] for k in new_vendor_props},
                    'location': 'Properties'
                })

        return additions

    def _identify_vendor_modifications(
        self,
        base_object: Dict[str, Any],
        vendor_object: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify modifications made by vendor

        Finds changes in vendor version (A→C) to existing code/features.

        Args:
            base_object: Base object (A)
            vendor_object: Vendor object (C)

        Returns:
            List of vendor modifications
        """
        modifications = []

        # Check SAIL code modifications
        if 'sail_code' in vendor_object and 'sail_code' in base_object:
            vendor_sail = vendor_object.get('sail_code', '')
            base_sail = base_object.get('sail_code', '')

            if vendor_sail != base_sail:
                # Count changed lines
                vendor_lines = vendor_sail.split('\n')
                base_lines = base_sail.split('\n')

                added = len(set(vendor_lines) - set(base_lines))
                removed = len(set(base_lines) - set(vendor_lines))

                modifications.append({
                    'type': 'sail_code',
                    'description': f"SAIL code modified "
                    f"(+{added} lines, -{removed} lines)",
                    'location': 'SAIL code'
                })

        # Check field modifications
        if 'fields' in vendor_object and 'fields' in base_object:
            vendor_fields = vendor_object.get('fields', [])
            base_fields = base_object.get('fields', [])

            if vendor_fields != base_fields:
                modifications.append({
                    'type': 'fields',
                    'description': "Field definitions modified",
                    'location': 'Fields'
                })

        # Check property modifications
        if 'properties' in vendor_object and 'properties' in base_object:
            vendor_props = vendor_object.get('properties', {})
            base_props = base_object.get('properties', {})

            # Find modified properties
            modified_props = []
            for key in set(vendor_props.keys()) & set(base_props.keys()):
                if vendor_props[key] != base_props[key]:
                    modified_props.append(key)

            if modified_props:
                modifications.append({
                    'type': 'properties',
                    'description': f"{len(modified_props)} propert(y/ies) "
                    f"modified: {', '.join(modified_props)}",
                    'location': 'Properties'
                })

        # Check business logic modifications
        if 'business_logic' in vendor_object and 'business_logic' in base_object:
            vendor_logic = vendor_object.get('business_logic', '')
            base_logic = base_object.get('business_logic', '')

            if vendor_logic != base_logic:
                modifications.append({
                    'type': 'business_logic',
                    'description': "Business logic modified",
                    'location': 'Business Logic'
                })

        return modifications

    def _identify_conflict_sections(
        self,
        base_object: Dict[str, Any],
        customer_object: Dict[str, Any],
        vendor_object: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify sections modified by both parties

        Finds areas where both customer and vendor made changes to the
        same sections of code or configuration.

        Args:
            base_object: Base object (A)
            customer_object: Customer object (B)
            vendor_object: Vendor object (C)

        Returns:
            List of conflict sections
        """
        conflicts = []

        # Check SAIL code conflicts
        if ('sail_code' in vendor_object and 'sail_code' in base_object and
                'sail_code' in customer_object):
            vendor_sail = vendor_object.get('sail_code', '')
            base_sail = base_object.get('sail_code', '')
            customer_sail = customer_object.get('sail_code', '')

            # Find lines changed by both
            base_lines = set(base_sail.split('\n'))
            vendor_lines = set(vendor_sail.split('\n'))
            customer_lines = set(customer_sail.split('\n'))

            vendor_changed = vendor_lines - base_lines
            customer_changed = customer_lines - base_lines

            # Lines changed by both (different changes)
            both_changed = vendor_changed & customer_changed
            if both_changed:
                conflicts.append({
                    'type': 'sail_code',
                    'description': f"{len(both_changed)} line(s) of SAIL code "
                    f"modified by both parties",
                    'location': 'SAIL code',
                    'severity': 'high'
                })

            # Also check for different changes to same area
            # (lines removed by one, modified by other)
            vendor_removed = base_lines - vendor_lines
            customer_removed = base_lines - customer_lines

            if vendor_removed & customer_changed:
                conflicts.append({
                    'type': 'sail_code',
                    'description': "Vendor removed lines that customer modified",
                    'location': 'SAIL code',
                    'severity': 'high'
                })

            if customer_removed & vendor_changed:
                conflicts.append({
                    'type': 'sail_code',
                    'description': "Customer removed lines that vendor modified",
                    'location': 'SAIL code',
                    'severity': 'high'
                })

        # Check field conflicts
        if ('fields' in vendor_object and 'fields' in base_object and
                'fields' in customer_object):
            vendor_fields = vendor_object.get('fields', [])
            base_fields = base_object.get('fields', [])
            customer_fields = customer_object.get('fields', [])

            # Get field names
            base_field_names = {
                f.get('name') for f in base_fields if isinstance(f, dict)
            }
            vendor_field_names = {
                f.get('name') for f in vendor_fields if isinstance(f, dict)
            }
            customer_field_names = {
                f.get('name') for f in customer_fields if isinstance(f, dict)
            }

            # Fields modified by both
            vendor_modified_fields = (
                (vendor_field_names - base_field_names) |
                (base_field_names - vendor_field_names)
            )
            customer_modified_fields = (
                (customer_field_names - base_field_names) |
                (base_field_names - customer_field_names)
            )

            conflicting_fields = (
                vendor_modified_fields & customer_modified_fields
            )

            if conflicting_fields:
                conflicts.append({
                    'type': 'fields',
                    'description': f"{len(conflicting_fields)} field(s) "
                    f"modified by both parties",
                    'location': 'Fields',
                    'severity': 'medium',
                    'fields': list(conflicting_fields)
                })

        # Check property conflicts
        if ('properties' in vendor_object and 'properties' in base_object and
                'properties' in customer_object):
            vendor_props = vendor_object.get('properties', {})
            base_props = base_object.get('properties', {})
            customer_props = customer_object.get('properties', {})

            # Properties modified by both
            conflicting_props = []
            for key in set(vendor_props.keys()) & set(customer_props.keys()):
                if (key in base_props and
                        vendor_props[key] != base_props[key] and
                        customer_props[key] != base_props[key] and
                        vendor_props[key] != customer_props[key]):
                    conflicting_props.append(key)

            if conflicting_props:
                conflicts.append({
                    'type': 'properties',
                    'description': f"{len(conflicting_props)} propert(y/ies) "
                    f"modified by both parties",
                    'location': 'Properties',
                    'severity': 'medium',
                    'properties': conflicting_props
                })

        return conflicts

    def _generate_merge_strategy(
        self,
        classification: str,
        vendor_additions: List[Dict[str, Any]],
        conflict_sections: List[Dict[str, Any]]
    ) -> str:
        """
        Determine appropriate merge strategy

        Args:
            classification: Change classification
            vendor_additions: List of vendor additions
            conflict_sections: List of conflict sections

        Returns:
            Merge strategy string
        """
        if classification == 'NO_CONFLICT':
            return MergeStrategy.ADOPT_VENDOR_CHANGES.value

        if classification == 'CUSTOMER_ONLY':
            return MergeStrategy.KEEP_CUSTOMER_VERSION.value

        if classification == 'REMOVED_BUT_CUSTOMIZED':
            return MergeStrategy.KEEP_CUSTOMER_VERSION.value

        if classification == 'CONFLICT':
            if vendor_additions and not conflict_sections:
                return MergeStrategy.INCORPORATE_VENDOR_ADDITIONS.value
            else:
                return MergeStrategy.MANUAL_MERGE_REQUIRED.value

        return MergeStrategy.MANUAL_MERGE_REQUIRED.value
