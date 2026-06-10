#!/usr/bin/env python3
"""
schema_validator.py — Non-RTL Parameter DB Schema Validator
============================================================
Part of the Non-RTL Parameter DB update workflow (see docs/nonrtl_db_update_workflow.html).

Validates contribution YAML and the JSON database against the parameter schema:
  - Type checking (string, integer, boolean, float, enumerated)
  - Range validation (low_limit / high_limit for integers)
  - Enum validation (accepted_values)
  - Required field presence
  - Cross-reference integrity (spec_ref, instance_name existence)

Usage:
  python3 schema_validator.py \
    --contribution contribution.yaml \
    --db ../nonrtl-params-db/nonrtl_param_db.json \
    --schema-version 2.1

Exit codes:
  0 — All validations passed
  1 — Validation errors found (PR blocked)
"""

import argparse
import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional


def load_json(path: str) -> Dict:
    """Load and parse a JSON file."""
    with open(path) as f:
        return json.load(f)


def load_yaml(path: str) -> Dict:
    """Load and parse a YAML file."""
    try:
        import yaml
        with open(path) as f:
            return yaml.safe_load(f)
    except ImportError:
        # Fallback: simple YAML parser for the contribution format
        return _simple_yaml_parse(path)


def _simple_yaml_parse(path: str) -> Dict:
    """Basic YAML-like parser for the contribution file format."""
    with open(path) as f:
        content = f.read()
    # This is a fallback; production systems should have PyYAML installed
    result = {}
    current_section = None
    current_slot = None
    for line in content.split('\n'):
        stripped = line.strip()
        if stripped.startswith('#') or not stripped:
            continue
        if ':' in stripped and not stripped.startswith(' ') and not stripped.startswith('-'):
            key, _, val = stripped.partition(':')
            result[key.strip()] = val.strip().strip("'\"")
            current_section = key.strip()
        elif stripped.startswith('- action:'):
            if 'slots' not in result:
                result['slots'] = []
            current_slot = {}
            result['slots'].append(current_slot)
            _, _, val = stripped.partition(':')
            current_slot['action'] = val.strip().strip("'\"")
        elif current_slot is not None and ':' in stripped:
            key = stripped.lstrip('- ').split(':')[0].strip()
            _, _, val = stripped.partition(':')
            current_slot[key.strip()] = val.strip().strip("'\"")
    return result


class SchemaValidator:
    """Validates non-RTL parameter values against the parameter schema."""

    VALID_CLASSES = {'string', 'integer', 'boolean', 'float', 'enumerated'}
    VALID_SOURCES = {'rtl', 'RTL', 'nonrtl', 'nonRTL', 'NONRTL'}

    def __init__(self, db_path: str):
        self.db = load_json(db_path)
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_contribution(self, contribution_path: str) -> bool:
        """Validate a contribution YAML file."""
        contrib = load_yaml(contribution_path)
        is_valid = True

        if not contrib:
            self.errors.append("Empty or invalid contribution file")
            return False

        slots = contrib.get('slots', [])
        if not slots:
            self.warnings.append("Contribution has no slots — nothing to validate")
            return True

        chip_prefix = contrib.get('chip_prefix', '')

        for i, slot in enumerate(slots):
            slot_prefix = f"Slot [{i}] ({slot.get('action', 'unknown')})"
            is_valid &= self._validate_slot(slot, slot_prefix, chip_prefix)

        return is_valid

    def _validate_slot(self, slot: Dict, prefix: str, chip_prefix: str) -> bool:
        """Validate a single contribution slot."""
        is_valid = True
        action = slot.get('action', '')

        if action == 'add_param':
            param_id = slot.get('param_id', '')
            value = slot.get('value')
            spec_ref = slot.get('spec_ref', '')
            copy_from = slot.get('copy_from')

            # Required fields
            if not param_id:
                self.errors.append(f"{prefix}: Missing 'param_id'")
                is_valid = False

            # Look up parameter definition
            param_def = self._find_parameter_definition(param_id, spec_ref)
            if param_def:
                param_class = param_def.get('class', 'string')
                accepted_values = param_def.get('accepted_values', [])
                low_limit = param_def.get('low_limit')
                high_limit = param_def.get('high_limit')

                # Validate value if provided
                if value is not None and not copy_from:
                    is_valid &= self._validate_value(
                        value, param_class, accepted_values,
                        low_limit, high_limit, param_id, prefix
                    )
            else:
                self.warnings.append(
                    f"{prefix}: Parameter '{param_id}' not found in any .prm definition"
                )

        elif action == 'remove_param':
            param_id = slot.get('param_id', '')
            affected = slot.get('affected_instances', [])
            if not param_id:
                self.errors.append(f"{prefix}: Missing 'param_id'")
                is_valid = False
            if not affected:
                self.warnings.append(
                    f"{prefix}: No affected instances listed for removal of '{param_id}'"
                )

        elif action == 'add_instance':
            instance_name = slot.get('instance_name', '')
            if not instance_name:
                self.errors.append(f"{prefix}: Missing 'instance_name'")
                is_valid = False
            # Check instance naming convention
            if instance_name and not re.match(r'^[A-Za-z][A-Za-z0-9_]*$', instance_name):
                self.errors.append(
                    f"{prefix}: Invalid instance name '{instance_name}' — "
                    f"must match [A-Za-z][A-Za-z0-9_]*"
                )
                is_valid = False

        else:
            self.errors.append(f"{prefix}: Unknown action '{action}'")
            is_valid = False

        return is_valid

    def _validate_value(
        self,
        value: Any,
        param_class: str,
        accepted_values: List[str],
        low_limit: Any,
        high_limit: Any,
        param_id: str,
        prefix: str
    ) -> bool:
        """Validate a parameter value against its class constraints."""
        is_valid = True

        if param_class == 'string':
            if not isinstance(value, str):
                self.errors.append(
                    f"{prefix}: '{param_id}' expects string, got {type(value).__name__}"
                )
                is_valid = False

        elif param_class == 'integer':
            try:
                int_val = int(value)
                if low_limit is not None and int_val < int(low_limit):
                    self.errors.append(
                        f"{prefix}: '{param_id}' = {int_val} below low_limit {low_limit}"
                    )
                    is_valid = False
                if high_limit is not None and int_val > int(high_limit):
                    self.errors.append(
                        f"{prefix}: '{param_id}' = {int_val} above high_limit {high_limit}"
                    )
                    is_valid = False
            except (ValueError, TypeError):
                self.errors.append(
                    f"{prefix}: '{param_id}' = '{value}' is not a valid integer"
                )
                is_valid = False

        elif param_class == 'boolean':
            if str(value).lower() not in ('true', 'false', '1', '0'):
                self.errors.append(
                    f"{prefix}: '{param_id}' = '{value}' is not a valid boolean"
                )
                is_valid = False

        elif param_class == 'float':
            try:
                float(value)
            except (ValueError, TypeError):
                self.errors.append(
                    f"{prefix}: '{param_id}' = '{value}' is not a valid float"
                )
                is_valid = False

        elif param_class == 'enumerated':
            if accepted_values and str(value) not in accepted_values:
                self.errors.append(
                    f"{prefix}: '{param_id}' = '{value}' not in accepted_values: "
                    f"{accepted_values}"
                )
                is_valid = False

        return is_valid

    def _find_parameter_definition(
        self,
        param_id: str,
        spec_ref: str
    ) -> Optional[Dict]:
        """Find a parameter definition in the database's parameter_associations."""
        associations = self.db.get('parameter_associations', {})
        if param_id in associations:
            return associations[param_id]

        # Search by spec_ref
        for assoc_id, assoc_data in associations.items():
            if assoc_id == param_id or spec_ref in assoc_data.get('applies_to', []):
                return assoc_data

        return None

    def validate_database_integrity(self) -> bool:
        """Validate the nonrtl_param_db.json for structural integrity."""
        is_valid = True

        # Check schema version
        schema_version = self.db.get('_schema_version', '1.0')
        if not schema_version:
            self.errors.append("DB missing '_schema_version' field")

        # Check chip_prefixes structure
        chip_prefixes = self.db.get('chip_prefixes', {})
        if not chip_prefixes:
            self.errors.append("DB has no 'chip_prefixes' entries")
            return False

        for prefix, prefix_data in chip_prefixes.items():
            # Validate instances
            instances = prefix_data.get('instances', {})
            for inst_name, inst_data in instances.items():
                spec_ref = inst_data.get('spec_ref', '')
                if not spec_ref:
                    self.errors.append(
                        f"chip_prefixes.{prefix}.instances.{inst_name}: "
                        f"missing 'spec_ref'"
                    )
                    is_valid = False

                nrtl_params = inst_data.get('nonrtl_params', {})
                for param_id, param_value in nrtl_params.items():
                    # Find param definition
                    param_assoc = self.db.get('parameter_associations', {}).get(param_id)
                    if param_assoc:
                        param_type = param_assoc.get('type', 'string')
                        # Basic type check
                        if param_type == 'integer' and not isinstance(param_value, (int, str)):
                            self.errors.append(
                                f"{prefix}.{inst_name}.{param_id}: "
                                f"expected integer, got {type(param_value).__name__}"
                            )
                            is_valid = False

            # Validate subsystems
            subsystems = prefix_data.get('subsystems', {})
            for ss_name, ss_data in subsystems.items():
                if 'nonrtl_params' not in ss_data:
                    self.warnings.append(
                        f"chip_prefixes.{prefix}.subsystems.{ss_name}: "
                        f"no nonrtl_params defined"
                    )

        # Validate soc_sub_system_mapping references
        soc_mapping = self.db.get('soc_sub_system_mapping', {})
        for soc_name, soc_data in soc_mapping.items():
            for ss_name in soc_data.get('subsystems', []):
                # Check subsystem exists in chip_prefixes
                found = False
                for prefix_data in chip_prefixes.values():
                    if ss_name in prefix_data.get('subsystems', {}):
                        found = True
                        break
                if not found:
                    self.warnings.append(
                        f"soc_sub_system_mapping.{soc_name}: "
                        f"subsystem '{ss_name}' not found in any chip_prefix"
                    )

            for inst_name in soc_data.get('direct_ip_instances', []):
                found = False
                for prefix_data in chip_prefixes.values():
                    if inst_name in prefix_data.get('instances', {}):
                        found = True
                        break
                if not found:
                    self.warnings.append(
                        f"soc_sub_system_mapping.{soc_name}: "
                        f"instance '{inst_name}' not found in any chip_prefix"
                    )

        return is_valid

    def print_results(self):
        """Print validation results."""
        if self.errors:
            print(f"\n❌  VALIDATION FAILED — {len(self.errors)} error(s):")
            for error in self.errors:
                print(f"    ✗  {error}")

        if self.warnings:
            print(f"\n⚠️   {len(self.warnings)} warning(s):")
            for warning in self.warnings:
                print(f"    ↪  {warning}")

        if not self.errors and not self.warnings:
            print("\n✅  All validations passed.")


def main():
    parser = argparse.ArgumentParser(
        description='Non-RTL Parameter DB Schema Validator'
    )
    parser.add_argument(
        '--contribution',
        help='Path to contribution YAML file to validate'
    )
    parser.add_argument(
        '--db',
        required=True,
        help='Path to the nonrtl_param_db.json file'
    )
    parser.add_argument(
        '--validate-db',
        action='store_true',
        help='Also validate database structural integrity'
    )

    args = parser.parse_args()

    if not Path(args.db).exists():
        print(f"❌  Database not found: {args.db}", file=sys.stderr)
        sys.exit(1)

    validator = SchemaValidator(args.db)
    has_errors = False

    # Validate contribution YAML if provided
    if args.contribution:
        if not Path(args.contribution).exists():
            print(f"❌  Contribution file not found: {args.contribution}", file=sys.stderr)
            sys.exit(1)

        print(f"Validating contribution: {args.contribution}")
        if not validator.validate_contribution(args.contribution):
            has_errors = True

    # Validate database integrity
    if args.validate_db:
        print("Validating database integrity...")
        if not validator.validate_database_integrity():
            has_errors = True

    validator.print_results()

    sys.exit(1 if has_errors else 0)


if __name__ == '__main__':
    main()