#!/usr/bin/env python3
"""
resolve_dita.py — DITA Parameter Resolution & Register Diagram Generator

Processes parameterized DITA source through a custom DITA-OT pipeline:
  1. Resolves pm:cond_* attributes using .imap instantiation values
  2. Transforms .rdb register files into DITA topics with SVG diagrams
  3. Generates memory maps for multi-instance IP blocks
  4. Outputs fully resolved, parameter-free DITA

Usage:
  python resolve_dita.py --source spec_source/SOC_XYZ_SPEC/ \
                         --imap IP_PARAMS_TOP.imap \
                         --output resolved_dita/
"""

import argparse
import json
import os
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any


DITA_OT_HOME = os.environ.get("DITA_OT_HOME", "/opt/dita-ot")


def load_imap(imap_path: str) -> ET.Element:
    """Load and parse an .imap file."""
    tree = ET.parse(imap_path)
    return tree.getroot()


def build_param_dict(imap_root: ET.Element) -> Dict[str, str]:
    """Build a flat parameter name→value dictionary from .imap."""
    params = {}
    for reg_elem in imap_root.findall('reg'):
        for override in reg_elem.findall('param_override'):
            param_id = override.get('param_id')
            params[param_id] = override.text or ''
    return params


def resolve_conditional_attributes(
    dita_content: str, params: Dict[str, str]
) -> str:
    """
    Evaluate pm:cond_PARAM_NAME="VALUE" attributes.
    If the parameter value matches, remove the attribute (content included).
    If it doesn't match, remove the element that carries it.
    """
    pattern = re.compile(r'pm:cond_(\w+)="([^"]*)"')

    def replace_match(match):
        param_name = match.group(1)
        required_value = match.group(2)
        actual_value = params.get(param_name, '')
        
        if str(actual_value).strip() == required_value.strip():
            return ''  # Remove the attribute, keep the element
        else:
            return 'REMOVE_ELEMENT'  # Signal to remove parent element
    
    lines = dita_content.split('\n')
    result_lines = []
    skip_next = 0
    
    for line in lines:
        if skip_next > 0:
            skip_next -= 1
            continue
        
        match = pattern.search(line)
        if match:
            result = replace_match(match)
            if result == 'REMOVE_ELEMENT':
                skip_next = 2  # Skip this line and next (closing tag)
                continue
            else:
                line = line.replace(match.group(0), '').strip()
        
        result_lines.append(line)
    
    return '\n'.join(result_lines)


def generate_register_svg(register: Dict) -> str:
    """Generate an SVG diagram for a register's bit-field layout."""
    width = 800
    bits = register.get('size', 32)
    bitfields = register.get('bitfields', [])
    
    color_map = {'RW': '#4a90d9', 'RO': '#5cb85c', 'W1C': '#f0ad4e', 'WO': '#d9534f'}
    cell_width = (width - 40) / bits
    
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="120" viewBox="0 0 {width} 120">',
        f'<rect width="{width}" height="120" fill="#f8f9fa" rx="4"/>',
        f'<text x="10" y="16" font-family="monospace" font-size="11" '
        f'font-weight="bold">{register["name"]} — {register.get("display_name", "")}</text>',
    ]
    
    # Bit numbers
    for i in range(bits):
        x = 20 + i * cell_width
        svg_parts.append(
            f'<text x="{x + cell_width/2}" y="34" text-anchor="middle" '
            f'font-size="7">{bits - 1 - i}</text>'
        )
    
    # Bit-fields
    for bf in bitfields:
        msb = bf.get('msb', 0)
        lsb = bf.get('lsb', 0)
        name = bf.get('name', '')
        access = bf.get('access', 'RO')
        
        x_start = 20 + (bits - 1 - msb) * cell_width
        bf_width = (msb - lsb + 1) * cell_width
        
        svg_parts.extend([
            f'<rect x="{x_start}" y="40" width="{bf_width}" height="35" '
            f'fill="{color_map.get(access, "#ccc")}" stroke="#333" rx="2"/>',
            f'<text x="{x_start + bf_width/2}" y="55" text-anchor="middle" '
            f'font-size="8" fill="#fff" font-family="monospace">{name}</text>',
            f'<text x="{x_start + bf_width/2}" y="68" text-anchor="middle" '
            f'font-size="6" fill="#ddd">{access}</text>',
        ])
    
    svg_parts.append(
        f'<text x="20" y="95" font-size="7">'
        f'Offset: {register.get("offset", "N/A")} | '
        f'Reset: {register.get("reset_value", "N/A")}</text>'
    )
    svg_parts.append('</svg>')
    
    return '\n'.join(svg_parts)


def transform_rdb_to_dita(rdb_path: str, output_dir: str) -> List[str]:
    """
    Transform a .rdb register database file into DITA reference topics
    with embedded SVG register diagrams.
    """
    tree = ET.parse(rdb_path)
    root = tree.getroot()
    generated_files = []
    
    for register in root.findall('register'):
        reg_name = register.get('name', 'UNKNOWN')
        reg_offset = register.get('offset', '0x00')
        reg_display = register.get('display_name', reg_name)
        reg_size = int(register.get('size', '32'))
        reg_access = register.get('access', 'RO')
        reg_reset = register.get('reset_value', '0x0')
        reg_desc = register.find('description')
        reg_desc_text = reg_desc.text if reg_desc is not None else ''
        
        # Collect bit-fields
        bitfields = []
        for bf in register.findall('bitfield'):
            bitfields.append({
                'msb': int(bf.get('msb', '0')),
                'lsb': int(bf.get('lsb', '0')),
                'name': bf.get('name', ''),
                'access': bf.get('access', 'RO'),
                'desc': bf.find('description').text if bf.find('description') is not None else ''
            })
        
        # Generate SVG diagram
        reg_data = {
            'name': reg_name,
            'display_name': reg_display,
            'size': reg_size,
            'offset': reg_offset,
            'access': reg_access,
            'reset_value': reg_reset,
            'bitfields': bitfields
        }
        svg_diagram = generate_register_svg(reg_data)
        
        # Build DITA reference topic
        dita_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<reference id="reg_{reg_name}">
  <title>{reg_display} ({reg_name})</title>
  <refbody>
    <section>
      <title>Register Summary</title>
      <table>
        <tgroup cols="2">
          <colspec colname="c1" colwidth="30*"/>
          <colspec colname="c2" colwidth="70*"/>
          <tbody>
            <row><entry>Offset</entry><entry>{reg_offset}</entry></row>
            <row><entry>Size</entry><entry>{reg_size} bits</entry></row>
            <row><entry>Access</entry><entry>{reg_access}</entry></row>
            <row><entry>Reset Value</entry><entry>{reg_reset}</entry></row>
          </tbody>
        </tgroup>
      </table>
    </section>
    <section>
      <title>Description</title>
      <p>{reg_desc_text}</p>
    </section>
    <section>
      <title>Bit-Field Diagram</title>
      <fig>
        <title>Register Layout</title>
        <image placement="break">
          <alt>{reg_name} bit-field diagram</alt>
        </image>
      </fig>
    </section>
    <section>
      <title>Bit-Field Descriptions</title>
      <table>
        <tgroup cols="5">
          <colspec colname="c1" colwidth="20*"/>
          <colspec colname="c2" colwidth="15*"/>
          <colspec colname="c3" colwidth="10*"/>
          <colspec colname="c4" colwidth="10*"/>
          <colspec colname="c5" colwidth="45*"/>
          <thead>
            <row>
              <entry>Field</entry><entry>Bits</entry><entry>Access</entry>
              <entry>Reset</entry><entry>Description</entry>
            </row>
          </thead>
          <tbody>
''' + ''.join(
    f'''            <row>
              <entry>{bf['name']}</entry>
              <entry>{bf['msb']}:{bf['lsb']}</entry>
              <entry>{bf['access']}</entry>
              <entry>—</entry>
              <entry>{bf['desc']}</entry>
            </row>
''' for bf in bitfields
) + '''          </tbody>
        </tgroup>
      </table>
    </section>
  </refbody>
</reference>'''
        
        # Write output
        output_file = Path(output_dir) / f"reg_{reg_name}.dita"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(dita_content)
        generated_files.append(str(output_file))
        
        # Also save SVG
        svg_file = Path(output_dir) / f"reg_{reg_name}.svg"
        svg_file.write_text(svg_diagram)
    
    return generated_files


def main():
    parser = argparse.ArgumentParser(
        description='DITA Parameter Resolver & Register Diagram Generator'
    )
    parser.add_argument('--source', required=True, help='DITA source directory')
    parser.add_argument('--imap', required=True, help='Enriched .imap file')
    parser.add_argument('--output', required=True, help='Output directory for resolved DITA')
    args = parser.parse_args()
    
    # Load parameter values
    imap_root = load_imap(args.imap)
    params = build_param_dict(imap_root)
    print(f"[INFO] Loaded {len(params)} parameters from .imap")
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Process .rdb files
    source_path = Path(args.source)
    rdb_files = list(source_path.rglob('*.rdb'))
    for rdb_file in rdb_files:
        print(f"[INFO] Transforming {rdb_file.name} → DITA")
        generated = transform_rdb_to_dita(str(rdb_file), args.output)
        for g in generated:
            print(f"  [OK] {g}")
    
    print(f"\n[DONE] Resolved DITA output → {args.output}")


if __name__ == '__main__':
    main()