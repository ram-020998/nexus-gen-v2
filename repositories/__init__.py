"""
Repositories package for data access layer.
"""

from repositories.base_repository import BaseRepository
from repositories.request_repository import RequestRepository
from repositories.chat_session_repository import ChatSessionRepository
from repositories.object_lookup_repository import ObjectLookupRepository
from repositories.package_object_mapping_repository import (
    PackageObjectMappingRepository
)
from repositories.delta_comparison_repository import DeltaComparisonRepository
from repositories.change_repository import ChangeRepository

# Object-specific repositories
from repositories.interface_repository import InterfaceRepository
from repositories.expression_rule_repository import ExpressionRuleRepository
from repositories.process_model_repository import ProcessModelRepository
from repositories.record_type_repository import RecordTypeRepository
from repositories.cdt_repository import CDTRepository
from repositories.integration_repository import IntegrationRepository
from repositories.web_api_repository import WebAPIRepository
from repositories.site_repository import SiteRepository
from repositories.group_repository import GroupRepository
from repositories.constant_repository import ConstantRepository
from repositories.connected_system_repository import ConnectedSystemRepository
from repositories.unknown_object_repository import UnknownObjectRepository

# Comparison repositories
from repositories.comparison.interface_comparison_repository import (
    InterfaceComparisonRepository
)
from repositories.comparison.process_model_comparison_repository import (
    ProcessModelComparisonRepository
)
from repositories.comparison.record_type_comparison_repository import (
    RecordTypeComparisonRepository
)

__all__ = [
    'BaseRepository',
    'RequestRepository',
    'ChatSessionRepository',
    'ObjectLookupRepository',
    'PackageObjectMappingRepository',
    'DeltaComparisonRepository',
    'ChangeRepository',
    # Object-specific repositories
    'InterfaceRepository',
    'ExpressionRuleRepository',
    'ProcessModelRepository',
    'RecordTypeRepository',
    'CDTRepository',
    'IntegrationRepository',
    'WebAPIRepository',
    'SiteRepository',
    'GroupRepository',
    'ConstantRepository',
    'ConnectedSystemRepository',
    'UnknownObjectRepository',
    # Comparison repositories
    'InterfaceComparisonRepository',
    'ProcessModelComparisonRepository',
    'RecordTypeComparisonRepository',
]
