"""
Expression Rule Repository

Provides data access for Expression Rule objects and related entities.
Handles storage of expression rule-specific data including inputs.
"""

from typing import Optional, List, Dict, Any
from models import ExpressionRule, ExpressionRuleInput
from repositories.base_repository import BaseRepository


class ExpressionRuleRepository(BaseRepository[ExpressionRule]):
    """
    Repository for ExpressionRule entities.
    
    Manages Expression Rule objects with their inputs.
    Each expression rule is linked to object_lookup via object_id.
    
    Key Methods:
        - create_expression_rule: Create expression rule with inputs
        - get_by_object_id: Get expression rule by object_lookup ID
        - get_by_uuid: Get expression rule by UUID
    """
    
    def __init__(self):
        """Initialize repository with ExpressionRule model."""
        super().__init__(ExpressionRule)
    
    def create_expression_rule(
        self,
        object_id: int,
        package_id: int,
        uuid: str,
        name: str,
        version_uuid: Optional[str] = None,
        sail_code: Optional[str] = None,
        output_type: Optional[str] = None,
        description: Optional[str] = None,
        inputs: Optional[List[Dict[str, Any]]] = None
    ) -> ExpressionRule:
        """
        Create expression rule with inputs.

        Args:
            object_id: Reference to object_lookup
            package_id: Reference to package (REQUIRED)
            uuid: Expression rule UUID
            name: Expression rule name
            version_uuid: Version UUID
            sail_code: SAIL code/definition
            output_type: Return type
            description: Description
            inputs: List of input dicts with keys:
                - input_name
                - input_type
                - is_required
                - default_value
                - display_order

        Returns:
            Created ExpressionRule object

        Example:
            >>> rule = repo.create_expression_rule(
            ...     object_id=42,
            ...     package_id=1,
            ...     uuid="abc-123",
            ...     name="My Rule",
            ...     sail_code="a!localVariables()",
            ...     output_type="Text",
            ...     inputs=[
            ...         {"input_name": "param1", "input_type": "Text",
            ...          "is_required": True}
            ...     ]
            ... )
        """
        # Create expression rule
        rule = ExpressionRule(
            object_id=object_id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            version_uuid=version_uuid,
            sail_code=sail_code,
            output_type=output_type,
            description=description
        )
        self.db.session.add(rule)
        self.db.session.flush()

        # Create inputs
        if inputs:
            for input_data in inputs:
                inp = ExpressionRuleInput(
                    rule_id=rule.id,
                    input_name=input_data.get('input_name'),
                    input_type=input_data.get('input_type'),
                    is_required=input_data.get('is_required', False),
                    default_value=input_data.get('default_value'),
                    display_order=input_data.get('display_order')
                )
                self.db.session.add(inp)

        self.db.session.flush()
        return rule
    
    def create_expression_rule_input(
        self,
        rule_id: int,
        data: Dict[str, Any]
    ) -> ExpressionRuleInput:
        """
        Create expression rule input.
        
        Args:
            rule_id: Expression rule ID
            data: Dictionary containing input data with keys:
                - input_name: Input parameter name (required)
                - input_type: Input data type (optional)
                - is_required: Whether input is required (optional, default False)
                - default_value: Default value (optional)
                - display_order: Display order (optional)
        
        Returns:
            Created ExpressionRuleInput object
        
        Example:
            >>> input = repo.create_expression_rule_input(
            ...     rule_id=1,
            ...     data={
            ...         "input_name": "param1",
            ...         "input_type": "Text",
            ...         "is_required": True
            ...     }
            ... )
        """
        inp = ExpressionRuleInput(
            rule_id=rule_id,
            input_name=data.get('input_name'),
            input_type=data.get('input_type'),
            is_required=data.get('is_required', False),
            default_value=data.get('default_value'),
            display_order=data.get('display_order')
        )
        self.db.session.add(inp)
        self.db.session.flush()
        return inp
    
    def get_by_object_id(self, object_id: int) -> Optional[ExpressionRule]:
        """
        Get expression rule by object_lookup ID.

        Note: This returns the first expression rule found for the object.
        Use get_all_by_object_id() to get all package versions.

        Args:
            object_id: Object lookup ID

        Returns:
            ExpressionRule or None if not found
        """
        return self.find_one(object_id=object_id)

    def get_by_object_and_package(
        self,
        object_id: int,
        package_id: int
    ) -> Optional[ExpressionRule]:
        """
        Get expression rule by object_lookup ID and package ID.

        This method returns the specific version of an expression rule
        for a given package.

        Args:
            object_id: Object lookup ID
            package_id: Package ID

        Returns:
            ExpressionRule or None if not found

        Example:
            >>> # Get the customized version of an expression rule
            >>> rule = repo.get_by_object_and_package(
            ...     object_id=42,
            ...     package_id=2  # Customized package
            ... )
        """
        return self.find_one(object_id=object_id, package_id=package_id)

    def get_all_by_object_id(self, object_id: int) -> List[ExpressionRule]:
        """
        Get all expression rules for an object across all packages.

        This method returns all package versions of an expression rule.
        Useful when you need to compare versions across packages.

        Args:
            object_id: Object lookup ID

        Returns:
            List of ExpressionRule objects (one per package)

        Example:
            >>> # Get all versions of an expression rule
            >>> rules = repo.get_all_by_object_id(object_id=42)
            >>> for rule in rules:
            ...     print(f"Package {rule.package_id}: {rule.version_uuid}")
        """
        return self.filter_by(object_id=object_id)

    def get_by_package(self, package_id: int) -> List[ExpressionRule]:
        """
        Get all expression rules in a package.

        This method returns all expression rules that belong to a
        specific package.

        Args:
            package_id: Package ID

        Returns:
            List of ExpressionRule objects

        Example:
            >>> # Get all expression rules in the base package
            >>> rules = repo.get_by_package(package_id=1)
            >>> print(f"Found {len(rules)} expression rules in base package")
        """
        return self.filter_by(package_id=package_id)
    
    def get_by_uuid(self, uuid: str) -> Optional[ExpressionRule]:
        """
        Get expression rule by UUID.
        
        Args:
            uuid: Expression rule UUID
        
        Returns:
            ExpressionRule or None if not found
        """
        return self.find_one(uuid=uuid)
    
    def get_inputs(self, rule_id: int) -> List[ExpressionRuleInput]:
        """
        Get all inputs for an expression rule.
        
        Args:
            rule_id: Expression rule ID
        
        Returns:
            List of ExpressionRuleInput objects
        """
        return self.db.session.query(ExpressionRuleInput).filter_by(
            rule_id=rule_id
        ).order_by(ExpressionRuleInput.display_order).all()
