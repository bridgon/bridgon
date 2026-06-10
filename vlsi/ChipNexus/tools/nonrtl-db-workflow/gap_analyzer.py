#!/usr/bin/env python3
"""
gap_analyzer.py — Non-RTL Parameter Database Gap Analyzer
==========================================================
Part of the Non-RTL Parameter DB update workflow (see docs/nonrtl_db_update_workflow.html).

Detects gaps between .prm parameter files and the JSON Non-RTL Parameter Database
by diffing parameter definitions against existing DB entries per SoC and instance.

Triggers:
  1. New non-RTL param in .prm (source=nonrtl) → gap detected
  2. New SoC/SubSystem added to memory map XLSX → DB entries missing
  3. Param removed from .prm → orphaned DB entries
  4. IP removed from SoC/SubSystem → stale DB entries

Usage:
  python3 gap_analyzer.py \
    --spec-repo ../spec-repo/ \
    --db ../nonrtl-params-db/nonrtl_param_db.json \
    --chip-prefix MCU_X \
    --output-contribution contribution.yaml

Output:
  - Prints gap analysis report to stdout
  - Generates contribution YAML with empty slots per instance
"""

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple


def discover_prm_files(spec_repo: Path) -> Dict[str, Path]:
    """
    Discover all .prm files in the spec repository.
    Returns: {spec_id: path_to_prm_file}
    """
    prm_map = {}
    for prm_file in spec_repo.rglob("*.prm"):
        spec_name = prm_file.parts[-4]  # e.g., IP_FlexCAN_SPEC
        if spec_name not in prm_map:
            prm_map[spec_name] = prm_file
        else:
            # Prefer IP-level .prm over global
            if "GLOBAL" not in spec_name:
                prm_map[spec_name] = prm_file
    return prm_map


def parse_nonrtl_params_from_prm(prm_path: Path) -> List[Dict]:
    """
    Parse non-RTL parameters from a .prm file.
    Returns list of {id, name, class, description, default_value, accepted_values}.
    """
    if not prm_path.exists():
        return []

    tree = ET.parse(prm_path)
    root = tree.getroot()

    params = []
    for param_elem in root.findall('.//parameter'):
        source = param_elem.get('source', '').lower()
        # Only collect non-RTL parameters
        if source != 'nonrtl':
            continue

        param_id = param_elem.get('id', '')
        param_class = param_elem.get('class', 'string')

        name_elem = param_elem.find('name')
        name = name_elem.text if name_elem is not None else param_id

        desc_elem = param_elem.find('description')
        description = desc_elem.text if desc_elem is not None else ''

        default_elem = param_elem.find('default')
        # Try alternate tag name
        if default_elem is None:
            default_elem = param_elem.find('default_value')
        default_value = default_elem.text if default_elem is not None else ''

        accepted_vals_elem = param_elem.find('accepted_values')
        accepted_values = []
        if accepted_vals_elem is not None:
            vals_text = accepted_vals_elem.text or ''
            accepted_values = [v.strip() for v in vals_text.split(',') if v.strip()]
            # Also check for <value> subelements
            for val_elem in accepted_vals_elem.findall('value'):
                if val_elem.text and val_elem.text.strip():
                    accepted_values.append(val_elem.text.strip())

        params.append({
            'id': param_id,
            'name': name,
            'class': param_class,
            'description': description,
            'default_value': default_value,
            'accepted_values': accepted_values,
            'is_new': True,  # Default assumption, updated during gap analysis
        })

    return params


def analyze_gaps(
    prm_map: Dict[str, Path],
    db: Dict,
    chip_prefix: str
) -> Dict:
    """
    Analyze gaps between .prm definitions and DB entries.

    Returns a gap analysis report with:
      - new_params: params in .prm but missing from DB
      - orphaned_entries: params in DB but missing from .prm
      - missing_instances: SoC instances not in DB
      - stale_instances: DB instances not in SoC
    """
    report = {
        'chip_prefix': chip_prefix,
        'timestamp': datetime.now().isoformat(),
        'new_params': [],        # Params in .prm but missing from DB
        'orphaned_entries': [],  # Params in DB but missing from .prm
        'missing_instances': [], # SoC instances not yet in DB
        'stale_instances': [],   # DB instances no longer in SoC
        'summary': {},
    }

    chip_data = db.get('chip_prefixes', {}).get(chip_prefix, {})
    db_instances = chip_data.get('instances', {})

    # Collect all non-RTL param IDs from all .prm files
    all_prm_params: Set[str] = set()
    spec_params: Dict[str, Set[str]] = {}  # spec_ref -> set of param IDs

    for spec_ref, prm_path in prm_map.items():
        params = parse_nonrtl_params_from_prm(prm_path)
        spec_params[spec_ref] = set(p['id'] for p in params)
        all_prm_params.update(spec_params[spec_ref])

    # Collect all param IDs currently in the DB for this chip_prefix
    all_db_params: Set[str] = set()
    for inst_name, inst_data in db_instances.items():
        nrtl = inst_data.get('nonrtl_params', {})
        all_db_params.update(nrtl.keys())

    # --- GAP 1: New params in .prm but missing from DB ---
    new_params = all_prm_params - all_db_params
    for param_id in sorted(new_params):
        # Find which specs have this param
        for spec_ref, param_set in spec_params.items():
            if param_id in param_set:
                report['new_params'].append({
                    'param_id': param_id,
                    'spec_ref': spec_ref,
                    'chip_prefix': chip_prefix,
                })

    # --- GAP 2: Orphaned DB entries (in DB but not in any .prm) ---
    orphaned_params = all_db_params - all_prm_params
    for param_id in sorted(orphaned_params):
        # Find which instances have this param
        affected_instances = []
        for inst_name, inst_data in db_instances.items():
            if param_id in inst_data.get('nonrtl_params', {}):
                affected_instances.append(inst_name)
        report['orphaned_entries'].append({
            'param_id': param_id,
            'affected_instances': affected_instances,
        })

    # --- GAP 3: SoC instances from soc_sub_system_mapping not in DB ---
    soc_mapping = db.get('soc_sub_system_mapping', {})
    soc_instances = []
    for soc_name, soc_data in soc_mapping.items():
        if chip_prefix in soc_name or chip_prefix in soc_data.get('chip_prefix', ''):
            soc_instances.extend(soc_data.get('direct_ip_instances', []))
            # Also add instances from subsystems
            for ss_name in soc_data.get('subsystems', []):
                ss_data = db.get('chip_prefixes', {}).get(chip_prefix, {})
                ss_inst = ss_data.get('subsystems', {}).get(ss_name, {})
                # Subsystem instances are tracked separately

    for instance_name in soc_instances:
        if instance_name not in db_instances:
            report['missing_instances'].append({
                'instance_name': instance_name,
                'chip_prefix': chip_prefix,
            })

    # --- GAP 4: DB instances not referenced by any SoC ---
    for inst_name in db_instances:
        if inst_name not in soc_instances:
            # Check if referenced by any SoC mapping
            found = False
            for soc_name, soc_data in soc_mapping.items():
                if inst_name in soc_data.get('direct_ip_instances', []):
                    found = True
                    break
            if not found:
                report['stale_instances'].append({
                    'instance_name': inst_name,
                    'chip_prefix': chip_prefix,
                })

    # Summary
    report['summary'] = {
        'new_params_count': len(report['new_params']),
        'orphaned_entries_count': len(report['orphaned_entries']),
        'missing_instances_count': len(report['missing_instances']),
        'stale_instances_count': len(report['stale_instances']),
        'has_gaps': (
            len(report['new_params']) > 0 or
            len(report['orphaned_entries']) > 0 or
            len(report['missing_instances']) > 0 or
            len(report['stale_instances']) > 0
        ),
    }

    return report


def print_gap_report(report: Dict):
    """Print a human-readable gap analysis report."""
    s = report['summary']
    print("=" * 60)
    print(f"  Non-RTL Parameter DB Gap Analysis")
    print(f"  Chip Prefix: {report['chip_prefix']}")
    print(f"  Timestamp:   {report['timestamp']}")
    print("=" * 60)

    if not s['has_gaps']:
        print("\n✅  No gaps detected — DB is in sync with .prm definitions.")
        return

    print(f"\n📊  Summary:")
    if s['new_params_count'] > 0:
        print(f"    • {s['new_params_count']} new parameter(s) found in .prm, missing from DB")
    if s['orphaned_entries_count'] > 0:
        print(f"    • {s['orphaned_entries_count']} orphaned parameter(s) in DB, removed from .prm")
    if s['missing_instances_count'] > 0:
        print(f"    • {s['missing_instances_count']} instance(s) in SoC memmap but not in DB")
    if s['stale_instances_count'] > 0:
        print(f"    • {s['stale_instances_count']} instance(s) in DB not referenced by any SoC")

    if report['new_params']:
        print(f"\n🆕  New Parameters (need DB entries):")
        for item in report['new_params']:
            print(f"    - {item['param_id']}  (spec: {item['spec_ref']})")

    if report['orphaned_entries']:
        print(f"\n🗑️   Orphaned DB Entries (consider removing):")
        for item in report['orphaned_entries']:
            instances = ', '.join(item['affected_instances'])
            print(f"    - {item['param_id']}  (affects: {instances})")

    if report['missing_instances']:
        print(f"\n📥  Missing Instances (need DB entries):")
        for item in report['missing_instances']:
            print(f"    - {item['instance_name']}")

    if report['stale_instances']:
        print(f"\n⚠️   Stale Instances (no longer in any SoC):")
        for item in report['stale_instances']:
            print(f"    - {item['instance_name']}")


def generate_contribution_yaml(report: Dict, db: Dict, output_path: str):
    """
    Generate a contribution YAML file with empty slots for missing parameters.
    Auto-assigns to authors based on spec ownership.
    """
    import yaml

    if not report['summary']['has_gaps']:
        return

    # Load author assignments from DB
    author_map = db.get('_author_assignments', {})
    default_author = db.get('_default_author', 'doc-team')

    contributions = {
        'generated_at': report['timestamp'],
        'chip_prefix': report['chip_prefix'],
        'gap_summary': report['summary'],
        'slots': [],
    }

    # Create slots for new parameters
    for item in report['new_params']:
        author = author_map.get(
            item['spec_ref'],
            author_map.get(item['param_id'], default_author)
        )
        contributions['slots'].append({
            'action': 'add_param',
            'param_id': item['param_id'],
            'spec_ref': item['spec_ref'],
            'chip_prefix': report['chip_prefix'],
            'assigned_to': author,
            'status': 'pending',
            'copy_from': None,  # Can reference parent chip values
            'value': None,
            'notes': 'Auto-detected new non-RTL parameter in .prm',
        })

    # Create slots for orphaned entries (mark for removal)
    for item in report['orphaned_entries']:
        contributions['slots'].append({
            'action': 'remove_param',
            'param_id': item['param_id'],
            'affected_instances': item['affected_instances'],
            'assigned_to': default_author,
            'status': 'pending_review',
            'notes': 'Orphaned — param no longer exists in any .prm file',
        })

    # Create slots for missing instances
    for item in report['missing_instances']:
        contributions['slots'].append({
            'action': 'add_instance',
            'instance_name': item['instance_name'],
            'chip_prefix': report['chip_prefix'],
            'assigned_to': default_author,
            'status': 'pending',
            'copy_from': None,
            'notes': 'Instance exists in SoC memmap but not in DB',
        })

    with open(output_path, 'w') as f:
        yaml.dump(contributions, f, default_flow_style=False, sort_keys=False)

    print(f"\n📝  Contribution YAML written to: {output_path}")
    print(f"    {len(contributions['slots'])} slot(s) pending assignment")


def main():
    parser = argparse.ArgumentParser(
        description='Non-RTL Parameter DB Gap Analyzer'
    )
    parser.add_argument(
        '--spec-repo',
        required=True,
        help='Path to the specification repository root'
    )
    parser.add_argument(
        '--db',
        required=True,
        help='Path to the nonrtl_param_db.json file'
    )
    parser.add_argument(
        '--chip-prefix',
        required=True,
        help='Chip prefix to analyze (e.g., MCU_X)'
    )
    parser.add_argument(
        '--output-contribution',
        default='contribution.yaml',
        help='Path for generated contribution YAML'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress report output (useful for CI)'
    )

    args = parser.parse_args()

    # Validate paths
    spec_repo = Path(args.spec_repo)
    if not spec_repo.exists():
        print(f"❌  Spec repo not found: {spec_repo}", file=sys.stderr)
        sys.exit(1)

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"❌  Database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    # Load database
    with open(db_path) as f:
        db = json.load(f)

    # Discover .prm files
    prm_map = discover_prm_files(spec_repo)

    if not prm_map:
        print("⚠️   No .prm files found in spec repo.", file=sys.stderr)

    # Analyze gaps
    report = analyze_gaps(prm_map, db, args.chip_prefix)

    # Print report
    if not args.quiet:
        print_gap_report(report)

    # Generate contribution YAML if gaps exist
    if report['summary']['has_gaps']:
        generate_contribution_yaml(report, db, args.output_contribution)
        sys.exit(1)  # Non-zero exit signals gaps found (useful for CI)
    else:
        sys.exit(0)  # Clean exit — no action needed


if __name__ == '__main__':
    main()