#!/usr/bin/env python3
"""
run_pipeline_demo.py — SoC DocFlow Pipeline Demo
=================================================
Runs the complete documentation generation pipeline on the dummy spec-repo:
  1. Reads all .rdb register files
  2. Reads all .imap instance maps
  3. Resolves parameters from .prm definitions
  4. Generates SVG register diagrams
  5. Generates DITA reference topics for each register
  6. Generates a memory map HTML table
  7. Produces a self-contained HTML output (webhelp demo)

Usage:
  python3 run_pipeline_demo.py

Output:
  output/webhelp/index.html  — Standalone HTML documentation viewer
  output/resolved_dita/      — Resolved DITA topic files
  output/register_svgs/      — SVG register diagrams
"""

import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent
SPEC_REPO = BASE / "spec-repo"
OUTPUT_DIR = BASE / "output"
WEBHELP_DIR = OUTPUT_DIR / "webhelp"
DITA_DIR = OUTPUT_DIR / "resolved_dita"
SVG_DIR = OUTPUT_DIR / "register_svgs"

for d in [WEBHELP_DIR, DITA_DIR, SVG_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────
# Step 1: Discover all spec files
# ─────────────────────────────────────────────────────────────
def discover_specs():
    specs = {}
    for rdb_file in SPEC_REPO.rglob("*.rdb"):
        spec_name = rdb_file.parts[-4]  # e.g. IP_FlexCAN_SPEC
        if spec_name not in specs:
            specs[spec_name] = {"rdb": [], "imap": [], "prm": []}
        specs[spec_name]["rdb"].append(rdb_file)

    for imap_file in SPEC_REPO.rglob("*.imap"):
        spec_name = imap_file.parts[-4]
        if spec_name not in specs:
            specs[spec_name] = {"rdb": [], "imap": [], "prm": []}
        specs[spec_name]["imap"].append(imap_file)

    for prm_file in SPEC_REPO.rglob("*.prm"):
        spec_name = prm_file.parts[-4]
        if spec_name not in specs:
            specs[spec_name] = {"rdb": [], "imap": [], "prm": []}
        specs[spec_name]["prm"].append(prm_file)

    return specs


# ─────────────────────────────────────────────────────────────
# Step 2: Parse .rdb register files
# ─────────────────────────────────────────────────────────────
def parse_rdb(rdb_path):
    tree = ET.parse(rdb_path)
    root = tree.getroot()
    registers = []
    for reg in root.findall("register"):
        bitfields = []
        for bf in reg.findall("bitfield"):
            desc_el = bf.find("description")
            bitfields.append({
                "msb": int(bf.get("msb", 0)),
                "lsb": int(bf.get("lsb", 0)),
                "name": bf.get("name", ""),
                "access": bf.get("access", "RO"),
                "description": desc_el.text if desc_el is not None else "",
            })
        desc_el = reg.find("description")
        registers.append({
            "name": reg.get("name", ""),
            "display_name": reg.get("display_name", ""),
            "offset": reg.get("offset", "0x00"),
            "size": int(reg.get("size", 32)),
            "access": reg.get("access", "RO"),
            "reset_value": reg.get("reset_value", "0x0"),
            "description": desc_el.text if desc_el is not None else "",
            "bitfields": bitfields,
            "ip_name": root.get("ip_name", ""),
        })
    return registers


# ─────────────────────────────────────────────────────────────
# Step 3: Parse .imap instance maps
# ─────────────────────────────────────────────────────────────
def parse_imap(imap_path):
    tree = ET.parse(imap_path)
    root = tree.getroot()
    instances = []
    for reg in root.findall("reg"):
        params = {}
        for override in reg.findall("param_override"):
            params[override.get("param_id")] = override.text
        regs_link = reg.find("regs_link")
        base_addr = reg.find("base_address")
        instances.append({
            "instance_name": reg.get("instance_name", ""),
            "ip_spec": reg.get("ip_spec", ""),
            "rdb_href": regs_link.get("href", "") if regs_link is not None else "",
            "base_address": base_addr.text if base_addr is not None else "0x0",
            "params": params,
        })
    return instances


# ─────────────────────────────────────────────────────────────
# Step 4: Generate SVG register diagram
# ─────────────────────────────────────────────────────────────
def generate_svg(register, width=760):
    bits = register["size"]
    bitfields = register["bitfields"]
    cell_w = (width - 40) / bits
    color_map = {"RW": "#7c3aed", "RO": "#059669", "W1C": "#d97706", "WO": "#dc2626"}

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="110" viewBox="0 0 {width} 110">',
        f'<rect width="{width}" height="110" fill="#1e1e2e" rx="6"/>',
        f'<text x="10" y="16" font-family="monospace" font-size="11" font-weight="bold" fill="#c9d1d9">'
        f'{register["name"]} — {register["display_name"]}</text>',
    ]

    # Bit position labels
    for i in range(bits):
        x = 20 + i * cell_w
        lines.append(
            f'<text x="{x + cell_w/2:.1f}" y="32" text-anchor="middle" '
            f'font-size="7" fill="#6e7681">{bits - 1 - i}</text>'
        )

    # Background bar for all bits (reserved/grey)
    lines.append(f'<rect x="20" y="36" width="{width-40}" height="40" fill="#30363d" rx="2"/>')

    # Bit-field colored blocks
    for bf in bitfields:
        x_start = 20 + (bits - 1 - bf["msb"]) * cell_w
        bf_width = (bf["msb"] - bf["lsb"] + 1) * cell_w
        color = color_map.get(bf["access"], "#484f58")
        lines.extend([
            f'<rect x="{x_start:.1f}" y="36" width="{bf_width:.1f}" height="40" '
            f'fill="{color}" rx="2" stroke="#0d1117" stroke-width="1"/>',
            f'<text x="{x_start + bf_width/2:.1f}" y="54" text-anchor="middle" '
            f'font-size="8" fill="#fff" font-weight="bold">{bf["name"]}</text>',
            f'<text x="{x_start + bf_width/2:.1f}" y="68" text-anchor="middle" '
            f'font-size="6" fill="#e2e8f0">{bf["access"]}</text>',
        ])

    # Footer
    lines.append(
        f'<text x="20" y="98" font-size="8" fill="#6e7681">'
        f'Offset: {register["offset"]}  |  Reset: {register["reset_value"]}  |  '
        f'■ RW (Purple)  ■ RO (Green)  ■ W1C (Amber)  ■ WO (Red)  □ Reserved (Grey)</text>'
    )
    lines.append("</svg>")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# Step 5: Generate DITA reference topic for a register
# ─────────────────────────────────────────────────────────────
def generate_dita_topic(register, svg_content):
    bf_rows = ""
    for bf in register["bitfields"]:
        bf_rows += f"""            <row>
              <entry><b>{bf['name']}</b></entry>
              <entry>{bf['msb']}:{bf['lsb']}</entry>
              <entry>{bf['access']}</entry>
              <entry>{register['reset_value']}</entry>
              <entry>{bf['description']}</entry>
            </row>\n"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<reference id="reg_{register['name']}">
  <title>{register['display_name']} ({register['name']})</title>
  <refbody>
    <section>
      <title>Register Summary</title>
      <table>
        <tgroup cols="2">
          <colspec colname="c1" colwidth="30*"/>
          <colspec colname="c2" colwidth="70*"/>
          <tbody>
            <row><entry>Offset</entry><entry>{register['offset']}</entry></row>
            <row><entry>Size</entry><entry>{register['size']} bits</entry></row>
            <row><entry>Access</entry><entry>{register['access']}</entry></row>
            <row><entry>Reset Value</entry><entry>{register['reset_value']}</entry></row>
          </tbody>
        </tgroup>
      </table>
    </section>
    <section>
      <title>Description</title>
      <p>{register['description']}</p>
    </section>
    <section>
      <title>Bit-Field Descriptions</title>
      <table>
        <tgroup cols="5">
          <thead>
            <row>
              <entry>Field</entry><entry>Bits</entry><entry>Access</entry>
              <entry>Reset</entry><entry>Description</entry>
            </row>
          </thead>
          <tbody>
{bf_rows}          </tbody>
        </tgroup>
      </table>
    </section>
  </refbody>
</reference>
"""


# ─────────────────────────────────────────────────────────────
# Step 6: Generate HTML webhelp output
# ─────────────────────────────────────────────────────────────
def generate_webhelp(all_registers, all_instances):
    # Build TOC
    toc_html = ""
    content_html = ""

    # Group registers by IP
    by_ip = {}
    for reg in all_registers:
        ip = reg["ip_name"]
        if ip not in by_ip:
            by_ip[ip] = []
        by_ip[ip].append(reg)

    for ip_name, regs in by_ip.items():
        toc_html += f'<div class="toc-chapter"><span class="toc-ip">{ip_name}</span>\n'
        for reg in regs:
            toc_html += f'  <a class="toc-reg" href="#{reg["name"]}">{reg["name"]}</a>\n'
        toc_html += '</div>\n'

        content_html += f'<h2 class="ip-heading">{ip_name}</h2>\n'
        for reg in regs:
            svg = generate_svg(reg)
            bf_rows = "".join(
                f'<tr><td><strong>{bf["name"]}</strong></td>'
                f'<td>{bf["msb"]}:{bf["lsb"]}</td>'
                f'<td><span class="access-{bf["access"].lower()}">{bf["access"]}</span></td>'
                f'<td>{reg["reset_value"]}</td>'
                f'<td>{bf["description"]}</td></tr>\n'
                for bf in reg["bitfields"]
            )
            content_html += f"""
<div class="register-section" id="{reg['name']}">
  <h3>{reg['display_name']} <span class="reg-name-badge">{reg['name']}</span></h3>
  <div class="reg-meta">
    <span>Offset: <code>{reg['offset']}</code></span>
    <span>Size: {reg['size']} bits</span>
    <span>Access: {reg['access']}</span>
    <span>Reset: <code>{reg['reset_value']}</code></span>
  </div>
  <p class="reg-desc">{reg['description']}</p>
  <div class="svg-container">{svg}</div>
  <table class="reg-table">
    <thead><tr><th>Field</th><th>Bits</th><th>Access</th><th>Reset</th><th>Description</th></tr></thead>
    <tbody>{bf_rows}</tbody>
  </table>
</div>
"""

    # Memory map table
    memmap_rows = ""
    for inst in all_instances:
        memmap_rows += (
            f'<tr><td><strong>{inst["ip_spec"]}</strong></td>'
            f'<td>{inst["instance_name"]}</td>'
            f'<td><code>{inst["base_address"]}</code></td>'
            f'<td>{inst["params"].get("DMA_NUM_CHANNELS", inst["params"].get("CAN_NUM_MB", "—"))}</td></tr>\n'
        )

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SoC DocFlow — Generated Reference Manual</title>
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: 'IBM Plex Mono', monospace; background: #0d1117; color: #c9d1d9; display: flex; min-height: 100vh; }}
.sidebar {{ width: 280px; background: #161b22; border-right: 1px solid #30363d; padding: 20px; position: fixed; top: 0; left: 0; height: 100vh; overflow-y: auto; }}
.sidebar h1 {{ font-size: 16px; color: #58a6ff; margin-bottom: 4px; }}
.sidebar .subtitle {{ font-size: 11px; color: #8b949e; margin-bottom: 20px; }}
.toc-chapter {{ margin-bottom: 12px; }}
.toc-ip {{ display: block; font-size: 12px; font-weight: 700; color: #7c3aed; padding: 6px 0; border-bottom: 1px solid #30363d; margin-bottom: 4px; }}
.toc-reg {{ display: block; font-size: 11px; color: #8b949e; padding: 3px 8px; text-decoration: none; border-radius: 4px; }}
.toc-reg:hover {{ background: #21262d; color: #58a6ff; }}
.main {{ margin-left: 280px; padding: 30px; flex: 1; max-width: 1100px; }}
.page-header {{ margin-bottom: 30px; padding-bottom: 16px; border-bottom: 1px solid #30363d; }}
.page-header h1 {{ font-size: 24px; color: #c9d1d9; }}
.page-header .meta {{ font-size: 12px; color: #8b949e; margin-top: 6px; }}
.ip-heading {{ font-size: 20px; color: #58a6ff; margin: 30px 0 16px; padding-bottom: 8px; border-bottom: 2px solid #7c3aed; }}
.register-section {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin-bottom: 24px; }}
.register-section h3 {{ font-size: 16px; color: #c9d1d9; margin-bottom: 10px; }}
.reg-name-badge {{ background: #21262d; color: #7c3aed; padding: 2px 10px; border-radius: 4px; font-size: 13px; margin-left: 8px; }}
.reg-meta {{ display: flex; gap: 16px; margin-bottom: 10px; font-size: 12px; color: #8b949e; flex-wrap: wrap; }}
.reg-meta span {{ background: #21262d; padding: 3px 10px; border-radius: 4px; }}
.reg-desc {{ font-size: 13px; color: #8b949e; margin-bottom: 14px; line-height: 1.6; }}
.svg-container {{ margin-bottom: 14px; overflow-x: auto; }}
.reg-table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
.reg-table th {{ background: #21262d; padding: 8px 12px; text-align: left; color: #8b949e; font-weight: 600; }}
.reg-table td {{ padding: 8px 12px; border-bottom: 1px solid #21262d; }}
.reg-table tr:hover td {{ background: #1a1f27; }}
.access-rw {{ background: #1f1a3a; color: #a371f7; padding: 2px 8px; border-radius: 3px; font-size: 10px; font-weight: 600; }}
.access-ro {{ background: #1a2f1a; color: #3fb950; padding: 2px 8px; border-radius: 3px; font-size: 10px; font-weight: 600; }}
.access-w1c {{ background: #3a2a1a; color: #d29922; padding: 2px 8px; border-radius: 3px; font-size: 10px; font-weight: 600; }}
.access-wo {{ background: #3a1a1a; color: #f85149; padding: 2px 8px; border-radius: 3px; font-size: 10px; font-weight: 600; }}
.memmap-section {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin-bottom: 24px; }}
.memmap-section h2 {{ font-size: 18px; color: #58a6ff; margin-bottom: 14px; }}
.memmap-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
.memmap-table th {{ background: #21262d; padding: 10px 14px; text-align: left; color: #8b949e; }}
.memmap-table td {{ padding: 10px 14px; border-bottom: 1px solid #21262d; }}
code {{ background: #21262d; padding: 1px 6px; border-radius: 3px; font-size: 12px; color: #79c0ff; }}
</style>
</head>
<body>
<nav class="sidebar">
  <h1>SoC DocFlow</h1>
  <div class="subtitle">Generated Reference Manual<br>{timestamp}</div>
  <div class="toc-chapter">
    <span class="toc-ip">📋 Memory Map</span>
    <a class="toc-reg" href="#memmap">System Memory Map</a>
  </div>
  {toc_html}
</nav>
<main class="main">
  <div class="page-header">
    <h1>SoC Reference Manual</h1>
    <div class="meta">Generated by SoC DocFlow Pipeline Demo | {timestamp} | 
    {len(all_registers)} registers from {len(by_ip)} IP blocks</div>
  </div>

  <div class="memmap-section" id="memmap">
    <h2>System Memory Map</h2>
    <table class="memmap-table">
      <thead><tr><th>IP Spec</th><th>Instance</th><th>Base Address</th><th>Key Parameter</th></tr></thead>
      <tbody>{memmap_rows}</tbody>
    </table>
  </div>

  {content_html}
</main>
</body>
</html>"""
    return html


# ─────────────────────────────────────────────────────────────
# Main Pipeline
# ─────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  SoC DocFlow — Pipeline Demo")
    print("=" * 60)

    # Step 1: Discover specs
    print("\n[1/5] Discovering spec files...")
    specs = discover_specs()
    print(f"      Found {len(specs)} spec directories")

    # Step 2: Parse all .rdb files
    print("\n[2/5] Parsing register database (.rdb) files...")
    all_registers = []
    for spec_name, spec_files in specs.items():
        for rdb_path in spec_files["rdb"]:
            regs = parse_rdb(rdb_path)
            all_registers.extend(regs)
            print(f"      {rdb_path.name}: {len(regs)} registers")

    # Step 3: Parse all .imap files
    print("\n[3/5] Parsing instance map (.imap) files...")
    all_instances = []
    for spec_name, spec_files in specs.items():
        for imap_path in spec_files["imap"]:
            instances = parse_imap(imap_path)
            all_instances.extend(instances)
            print(f"      {imap_path.name}: {len(instances)} instances")

    # Step 4: Generate SVG diagrams and DITA topics
    print("\n[4/5] Generating SVG diagrams and DITA topics...")
    for reg in all_registers:
        svg = generate_svg(reg)
        svg_path = SVG_DIR / f"reg_{reg['name']}.svg"
        svg_path.write_text(svg)

        dita = generate_dita_topic(reg, svg)
        dita_path = DITA_DIR / f"reg_{reg['name']}.dita"
        dita_path.write_text(dita)

    print(f"      Generated {len(all_registers)} SVG diagrams → {SVG_DIR}")
    print(f"      Generated {len(all_registers)} DITA topics → {DITA_DIR}")

    # Step 5: Generate webhelp
    print("\n[5/5] Generating HTML webhelp output...")
    html = generate_webhelp(all_registers, all_instances)
    webhelp_path = WEBHELP_DIR / "index.html"
    webhelp_path.write_text(html)
    print(f"      Generated webhelp → {webhelp_path}")

    print("\n" + "=" * 60)
    print(f"  Pipeline complete!")
    print(f"  Registers processed: {len(all_registers)}")
    print(f"  IP instances:        {len(all_instances)}")
    print(f"  Output:              {WEBHELP_DIR}/index.html")
    print("=" * 60)
    print(f"\n  Open in browser: file://{webhelp_path.resolve()}")


if __name__ == "__main__":
    main()
