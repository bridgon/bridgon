#!/usr/bin/env python3
"""
param_extract.py — Non-RTL Parameter Enricher

Merges RTL-extracted parameters (from design analysis) with non-RTL parameters
(from the JSON ditabase) into a unified IP_PARAMS_TOP.imap file.

Usage:
  python param_extract.py --rtl_imap SOC_XYZ_top.imap \
                          --nonrtl_db nonrtl_param_db.json \
                          --chip_prefix MCU_X \
                          --output IP_PARAMS_TOP.imap
"""

import argparse
import json
import os
import xml.etree.ElementTree as ET

def enrich_imap(rtl_imap_path, nonrtl_db_path, chip_prefix, output_path):
    """Merge non-RTL params from the JSON database into an RTL .imap file."""
    
    # Load Non-RTL DB
    with open(nonrtl_db_path) as f:
        nonrtl_db = json.load(f)
    
    chip_data = nonrtl_db.get('chip_prefixes', {}).get(chip_prefix, {})
    instances_db = chip_data.get('instances', {})
    
    # Parse RTL .imap
    tree = ET.parse(rtl_imap_path)
    root = tree.getroot()
    
    enriched_count = 0
    
    for reg_elem in root.findall('reg'):
        instance_name = reg_elem.get('instance_name', '')
        inst_nrtl = instances_db.get(instance_name, {})
        nrtl_params = inst_nrtl.get('nonrtl_params', {})
        
        if not nrtl_params:
            continue
        
        # Add non-RTL comment separator
        comment = ET.Comment(' Non-RTL params enriched from Non-RTL Parameter DB ')
        # Insert after regs_link
        regs_link = reg_elem.find('regs_link')
        if regs_link is not None:
            idx = list(reg_elem).index(regs_link) + 1
            reg_elem.insert(idx, comment)
        
        for param_id, param_value in nrtl_params.items():
            # Skip if already exists from RTL
            existing = reg_elem.find(f'param_override[@param_id="{param_id}"]')
            if existing is None:
                override = ET.SubElement(reg_elem, 'param_override', {'param_id': param_id})
                override.text = str(param_value)
                enriched_count += 1
    
    # Add processing metadata
    metadata_comment = ET.Comment(
        f' Enriched by param_extract.py — {enriched_count} non-RTL parameters added '
        f'from chip_prefix="{chip_prefix}" '
    )
    root.insert(0, metadata_comment)
    
    # Write output
    ET.indent(tree, space='  ')
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    
    print(f"[INFO] Enriched {enriched_count} non-RTL parameters → {output_path}")
    return output_path

def main():
    parser = argparse.ArgumentParser(description='Non-RTL Parameter Enricher')
    parser.add_argument('--rtl_imap', required=True, help='RTL-only .imap file')
    parser.add_argument('--nonrtl_db', required=True, help='nonrtl_param_db.json')
    parser.add_argument('--chip_prefix', required=True, help='Chip family prefix')
    parser.add_argument('--output', required=True, help='Output enriched .imap')
    args = parser.parse_args()
    
    enrich_imap(args.rtl_imap, args.nonrtl_db, args.chip_prefix, args.output)

if __name__ == '__main__':
    main()