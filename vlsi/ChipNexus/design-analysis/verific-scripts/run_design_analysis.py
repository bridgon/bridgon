#!/usr/bin/env python3
"""
run_design_analysis.py — Complete Design Analysis & Parameter Extraction Pipeline
==================================================================================
Production-grade RTL elaboration and parameter extraction supporting:

  Verific (commercial) — Full SystemVerilog/VHDL 2008 with hierarchy resolution
  Yosys (open-source) — Free alternative for SV synthesis subset

Extracts module parameters, register definitions, hierarchy paths, and
generates module_parameters.json ready for the Bridgon SoC DocFlow pipeline.

Also supports importing Hjson register definitions (OpenTitan reggen format)
and converting them to Bridgon .rdb register database format, unifying both
workflows into a single source-of-truth pipeline.

Usage:
  # Verific-based
  python3 run_design_analysis.py --engine verific \
    --top-module soc_top --filelist rtl.flist --output output.json

  # Yosys-based (free/open-source)
  python3 run_design_analysis.py --engine yosys \
    --top-module uart_core --filelist rtl.flist --output output.json

  # Import OpenTitan Hjson registers
  python3 run_design_analysis.py --engine hjson \
    --hjson uart.hjson --output-rdb uart_regs.rdb

Verific Integration Details:
  This script connects to Verific via its Python C-API (libverific.so).
  The Verific installation must be available at $VERIFIC_HOME.
  See: https://www.verific.com/products/

  The Verific API provides:
    - veri_file::Analyze()     — Parse SystemVerilog source
    - vhdl_file::Analyze()     — Parse VHDL source
    - veri_module::Elaborate() — Elaborate design hierarchy
    - Get parameters with full type system (integer, boolean, string, etc.)
    - Resolve hierarchical parameter overrides (defparam, generate, module instances)
    - Trace parameter source locations (file, line number)
"""

import argparse
import json
import os
import re
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════
# VERIFIC ENGINE (Commercial EDA Tool)
# ═══════════════════════════════════════════════════════════════

class VerificEngine:
    """
    Complete Verific integration using the Python C-API.
    
    Verific provides:
      - Full SystemVerilog IEEE 1800-2017 parsing
      - Full VHDL IEEE 1076-2008 parsing
      - Complete design elaboration with hierarchy resolution
      - Module parameter definitions with their full type system
      - Hierarchical parameter overrides through defparam,
        module instantiation, and generate blocks
      - Parameter expressions, dependencies, and macro-resolved values
      - Source location tracking (file path, line number)
    """
    
    VERIFIC_HOME = os.environ.get("VERIFIC_HOME", "/opt/verific")
    
    # SystemVerilog type to parameter class mapping
    SV_TYPE_MAP = {
        # Integer types
        "int": "integer", "integer": "integer", "byte": "integer",
        "shortint": "integer", "longint": "integer",
        "bit": "integer", "logic": "integer", "reg": "integer",
        "wire": "integer",
        # Boolean types
        "boolean": "boolean",
        # String types
        "string": "string",
        # Floating point
        "real": "float", "shortreal": "float", "realtime": "float",
    }
    
    def __init__(self):
        self._libverific = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """Load and initialize the Verific Python C-API library."""
        try:
            # Verific ships with a Python module 'verific'
            import verific
            self._libverific = verific
            
            # Set analysis options
            verific.set_option("verilog_syntax", "2017")  # IEEE 1800-2017
            verific.set_option("sv_syntax", True)
            verific.set_option("vhdl_syntax", "2008")       # IEEE 1076-2008
            verific.set_option("elaborate_generate", True)   # Expand generate blocks
            verific.set_option("resolve_params", True)       # Resolve param expressions
            
            self._initialized = True
            return True
        except ImportError:
            print("[WARNING] Verific Python API not available. "
                  f"Check $VERIFIC_HOME ({self.VERIFIC_HOME})")
            return False
    
    def is_available(self) -> bool:
        return self._initialized
    
    def analyze_verilog(self, filepath: str) -> bool:
        """Analyze a SystemVerilog source file."""
        if not self._initialized:
            return False
        
        try:
            result = self._libverific.analyze_verilog(filepath)
            if result != 0:
                print(f"  [WARN] {filepath}: analysis returned code {result}")
                return False
            return True
        except Exception as e:
            print(f"  [ERROR] {filepath}: {e}")
            return False
    
    def analyze_vhdl(self, filepath: str) -> bool:
        """Analyze a VHDL source file."""
        if not self._initialized:
            return False
        
        try:
            result = self._libverific.analyze_vhdl(filepath)
            if result != 0:
                print(f"  [WARN] {filepath}: analysis returned code {result}")
                return False
            return True
        except Exception as e:
            print(f"  [ERROR] {filepath}: {e}")
            return False
    
    def elaborate(self, top_module: str) -> bool:
        """Elaborate the design starting from the top module."""
        if not self._initialized:
            return False
        
        try:
            result = self._libverific.elaborate(top_module)
            if result != 0:
                print(f"[ERROR] Elaboration of '{top_module}' failed (code {result})")
                return False
            return True
        except Exception as e:
            print(f"[ERROR] Elaboration failed: {e}")
            return False
    
    def extract_parameters(self, top_module: str) -> Dict[str, Any]:
        """
        Extract all parameters from the elaborated design hierarchy.
        
        Returns a structured dictionary:
        {
            "module_path": {
                "module_name": "...",
                "instance_name": "...",
                "source_file": "...",
                "source_line": 123,
                "parameters": {
                    "PARAM_NAME": {
                        "type": "integer",
                        "sv_type": "int unsigned",
                        "default_value": 64,
                        "resolved_value": 64,
                        "is_overridden": false,
                        "override_source": null,
                        "source_file": "...",
                        "source_line": 87,
                        "min_val": null,
                        "max_val": null,
                    }
                }
            }
        }
        """
        if not self._initialized:
            return {}
        
        try:
            # Verific API: get_design_modules() returns all modules in the elaborated design
            design_modules = self._libverific.get_design_modules(top_module)
        except Exception:
            # Fallback: iterate over all modules
            design_modules = self._libverific.get_all_modules()
        
        result = {}
        
        for module_ref in design_modules:
            # Get hierarchical path
            hier_path = module_ref.get_hierarchical_name()
            module_name = module_ref.get_name()
            source_file = module_ref.get_source_file()
            source_line = module_ref.get_source_line()
            
            # Extract parameters
            parameters = {}
            param_list = module_ref.get_parameters()
            
            for param in param_list:
                param_name = param.get_name()
                sv_type = param.get_type_string()
                param_class = self.SV_TYPE_MAP.get(
                    sv_type.lower().split()[0], "string"
                )
                
                # Get values
                default_val = param.get_default_value()
                resolved_val = param.get_resolved_value()
                is_overridden = default_val != resolved_val
                
                # Get source location
                param_file = param.get_source_file()
                param_line = param.get_source_line()
                
                # Get override source if applicable
                override_source = None
                if is_overridden:
                    override_info = param.get_override_source()
                    if override_info:
                        override_source = (
                            f"{override_info.get('file')}:"
                            f"{override_info.get('line')}"
                        )
                
                # Get constraints
                min_val = param.get_min_value()
                max_val = param.get_max_value()
                
                parameters[param_name] = {
                    "type": param_class,
                    "sv_type": sv_type,
                    "default_value": self._coerce_value(default_val, param_class),
                    "resolved_value": self._coerce_value(resolved_val, param_class),
                    "is_overridden": is_overridden,
                    "override_source": override_source,
                    "source_file": param_file,
                    "source_line": param_line,
                    "min_val": min_val,
                    "max_val": max_val,
                    "description": param.get_comment() or
                        f"RTL parameter '{param_name}' defined in {module_name}",
                    "source": "RTL",
                }
            
            result[hier_path] = {
                "module_name": module_name,
                "source_file": source_file,
                "source_line": source_line,
                "parameters": parameters,
            }
        
        return result
    
    def extract_registers(self, top_module: str) -> Dict[str, Any]:
        """
        Extract register definitions from the elaborated design.
        
        This requires the registers to be defined in a structured way
        (IP-XACT, SystemRDL, or custom attributes). Verific can extract
        register information if the design uses standard register-generation
        patterns (common in OpenTitan, RISC-V, ARM-based SoCs).
        """
        if not self._initialized:
            return {}
        
        result = {}
        try:
            design_modules = self._libverific.get_design_modules(top_module)
        except Exception:
            design_modules = self._libverific.get_all_modules()
        
        for module_ref in design_modules:
            hier_path = module_ref.get_hierarchical_name()
            
            # Extract registers from module attributes/comments
            registers = module_ref.get_registers() or []
            if registers:
                reg_list = []
                for reg in registers:
                    reg_list.append({
                        "name": reg.get("name", ""),
                        "offset": reg.get("offset", "0x00"),
                        "size": int(reg.get("width", 32)),
                        "access": reg.get("access", "RW"),
                        "reset_value": reg.get("reset", "0x0"),
                        "description": reg.get("description", ""),
                    })
                result[hier_path] = reg_list
        
        return result
    
    @staticmethod
    def _coerce_value(value: Any, param_class: str) -> Any:
        """Convert Verific value types to JSON-serializable Python types."""
        if value is None:
            return None
        if param_class == "boolean":
            if isinstance(value, str):
                return value.lower() in ("true", "1", "1'b1", "yes")
            return bool(int(value))
        if param_class == "integer":
            try:
                return int(value)
            except (ValueError, TypeError):
                return str(value)
        return str(value)


# ═══════════════════════════════════════════════════════════════
# YOSYS ENGINE (Open-Source Alternative)
# ═══════════════════════════════════════════════════════════════

class YosysEngine:
    """
    Open-source RTL elaboration using Yosys.
    
    Yosys is a free and open-source synthesis tool that supports a subset
    of SystemVerilog IEEE 1800-2017. It can elaborate designs and extract
    parameter values, making it a viable alternative when Verific is not
    available.
    
    Limitations vs. Verific:
      - Limited VHDL 2008 support
      - Some SystemVerilog constructs not fully supported
      - No parameter expression traceback to source line numbers
      - Limited type tracking (primarily integer/string)
    
    See: https://yosyshq.net/yosys/
    """
    
    YOSYS_BIN = os.environ.get("YOSYS", "yosys")
    
    def is_available(self) -> bool:
        """Check if Yosys is installed and accessible."""
        try:
            result = subprocess.run(
                [self.YOSYS_BIN, "--version"],
                capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def elaborate_and_extract(
        self,
        rtl_files: List[str],
        top_module: str,
        working_dir: str,
    ) -> Dict[str, Any]:
        """
        Run Yosys to elaborate the design and extract parameters.
        
        The Yosys pipeline:
          1. read_verilog -sv  → Parse SystemVerilog sources
          2. hierarchy -top    → Build design hierarchy
          3. proc              → Convert processes to netlists
          4. param             → Extract all parameter values
          5. tee -o            → Save structured output
        """
        os.makedirs(working_dir, exist_ok=True)
        
        # Build Yosys script
        read_cmds = "\n".join(
            f"read_verilog -sv -defer {f}" for f in rtl_files
        )
        
        yosys_script = f"""
# ── Yosys Design Elaboration & Parameter Extraction ──
# Generated by run_design_analysis.py (Yosys engine)
# Target: {top_module}

# Read all design files
{read_cmds}

# Elaborate the top module
hierarchy -top {top_module}

# Convert processes (expand always blocks for parameter context)
proc

# Extract parameters in structured format
tee -o {working_dir}/yosys_params.txt param -all

# Write JSON output
write_json {working_dir}/yosys_design.json

# Exit
exit
"""
        script_path = Path(working_dir) / "yosys_script.ys"
        script_path.write_text(yosys_script)
        
        print(f"[INFO] Running Yosys with script: {script_path}")
        
        try:
            result = subprocess.run(
                [self.YOSYS_BIN, "-s", str(script_path)],
                capture_output=True, text=True,
                timeout=300, cwd=working_dir,
            )
            if result.returncode != 0:
                # Yosys often returns non-zero but still produces useful output
                print(f"[WARN] Yosys exited with code {result.returncode}")
        except FileNotFoundError:
            print(f"[ERROR] Yosys not found at '{self.YOSYS_BIN}'")
            return {}
        except subprocess.TimeoutExpired:
            print("[ERROR] Yosys elaboration timed out (300s)")
            return {}
        
        # Parse Yosys parameter output
        params = self._parse_yosys_params(
            Path(working_dir) / "yosys_params.txt"
        )
        
        # Parse Yosys JSON output
        design_json = self._parse_yosys_json(
            Path(working_dir) / "yosys_design.json"
        )
        
        # Merge results
        return self._merge_yosys_results(params, design_json, top_module)
    
    def _parse_yosys_params(self, params_file: Path) -> Dict[str, Any]:
        """
        Parse Yosys 'param' command output.
        
        Format:
          module_name.parameter_name = value
          \hierarchical.path.parameter_name = value
        """
        if not params_file.exists():
            return {}
        
        params = {}
        param_pattern = re.compile(
            r'\\(.+?)\.(.+?) = (.+)'
        )
        
        for line in params_file.read_text().split('\n'):
            line = line.strip()
            match = param_pattern.match(line)
            if match:
                module_path, param_name, value = match.groups()
                # Clean Yosys escape sequences
                module_path = module_path.replace('\\', '')
                
                if module_path not in params:
                    params[module_path] = {}
                
                # Determine type from value format
                clean_value = value.strip()
                if clean_value.isdigit() or (
                    clean_value.startswith('-') and clean_value[1:].isdigit()
                ):
                    param_type = "integer"
                    parsed_val = int(clean_value)
                elif clean_value.lower() in ("1'b1", "1'b0", "1", "0"):
                    param_type = "boolean"
                    parsed_val = clean_value.lower() in ("1'b1", "1", "true")
                else:
                    param_type = "string"
                    parsed_val = clean_value
                
                params[module_path][param_name] = {
                    "type": param_type,
                    "resolved_value": parsed_val,
                    "default_value": parsed_val,
                    "is_overridden": False,
                    "source": "RTL",
                    "extraction_engine": "yosys",
                }
        
        return params
    
    def _parse_yosys_json(self, json_file: Path) -> Dict[str, Any]:
        """Parse Yosys 'write_json' output."""
        if not json_file.exists():
            return {}
        try:
            with open(json_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def _merge_yosys_results(
        self,
        params: Dict,
        design_json: Dict,
        top_module: str,
    ) -> Dict[str, Any]:
        """Merge Yosys parameter and design JSON outputs."""
        result = {}
        
        # Prefer structured param output
        if params:
            for module_path, module_params in params.items():
                result[module_path] = {
                    "module_name": module_path.split('.')[-1],
                    "parameters": module_params,
                    "extraction_engine": "yosys",
                }
            return result
        
        # Fallback: extract from design JSON
        modules = design_json.get("modules", {})
        for module_name, module_data in modules.items():
            module_params = {}
            for attr_name, attr_value in module_data.get("attributes", {}).items():
                module_params[attr_name] = {
                    "type": "string",
                    "resolved_value": str(attr_value),
                    "source": "RTL",
                    "extraction_engine": "yosys",
                }
            
            if module_params:
                result[module_name] = {
                    "module_name": module_name,
                    "parameters": module_params,
                    "extraction_engine": "yosys",
                }
        
        return result


# ═══════════════════════════════════════════════════════════════
# HJSON REGISTER IMPORT (OpenTitan-Inspired)
# ═══════════════════════════════════════════════════════════════

class HjsonRegisterImporter:
    """
    Import register definitions from Hjson format (OpenTitan reggen style)
    and convert them to Bridgon .rdb format.
    
    This enables interoperability between the OpenTitan reggen workflow
    and the Bridgon SoC DocFlow pipeline. Teams using Hjson for register
    definitions can seamlessly generate Bridgon .rdb files, .prm parameter
    definitions, and documentation.
    
    OpenTitan Hjson Schema:
      {
        name: "ip_name",
        registers: [
          {
            name: "REG_NAME",
            desc: "Register description",
            swaccess: "rw",
            hwaccess: "hro",
            fields: [
              { bits: "7:0", name: "FIELD", desc: "..." }
            ]
          }
        ]
      }
    
    Bridgon .rdb Schema:
      <rdb ip_name="IP_NAME" regs_id="IP_CORE">
        <register offset="0x00" name="REG_NAME" ...>
          <description>...</description>
          <bitfield msb="7" lsb="0" name="FIELD" access="RW">
            <description>...</description>
          </bitfield>
        </register>
      </rdb>
    """
    
    # OpenTitan swaccess to Bridgon access type mapping
    ACCESS_MAP = {
        "rw": "RW", "ro": "RO", "wo": "WO",
        "rw1c": "W1C", "rw1s": "RW", "w1c": "W1C",
        "rc": "RO", "rs": "RO", "wc": "WO",
        "ws": "WO", "wosc": "WO", "hro": "RO",
        "hrw": "RW", "hwo": "WO",
    }
    
    def __init__(self):
        self._has_hjson = False
        try:
            import hjson
            self._hjson = hjson
            self._has_hjson = True
        except ImportError:
            print("[WARNING] 'hjson' Python package not installed. "
                  "Install with: pip install hjson")
    
    def is_available(self) -> bool:
        return self._has_hjson
    
    def parse_hjson_file(self, hjson_path: str) -> Dict[str, Any]:
        """Parse an Hjson register definition file."""
        if not self._has_hjson:
            # Fallback: parse as JSON-like
            with open(hjson_path) as f:
                content = f.read()
            # Strip comments and trailing commas for basic JSON parsing
            content = re.sub(r'//.*', '', content)
            content = re.sub(r',\s*([}\]])', r'\1', content)
            content = re.sub(r"'''", '"', content)
            return json.loads(content)
        
        with open(hjson_path) as f:
            return self._hjson.load(f)
    
    def convert_to_rdb(
        self,
        hjson_data: Dict[str, Any],
        ip_name: Optional[str] = None,
    ) -> str:
        """
        Convert Hjson register data to Bridgon .rdb XML format.
        
        Handles:
          - Register offsets (auto-assigned if not present)
          - Bitfield msb/lsb parsing from "7:0" format
          - Access type mapping
          - Enum values for enumerated fields
          - Multi-register blocks
        """
        ip_name = ip_name or hjson_data.get("name", "UNKNOWN")
        human_name = hjson_data.get("human_name", ip_name.upper())
        
        lines = []
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append('<!--')
        lines.append(f'  Auto-generated from {ip_name}.hjson')
        lines.append(f'  IP: {human_name}')
        lines.append(f'  Generated: {datetime.now().isoformat()}')
        lines.append('-->')
        lines.append(
            f'<rdb xmlns="http://bridgon.com/schemas/register-db"'
            f'\n     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
            f'\n     xsi:schemaLocation="http://bridgon.com/schemas/register-db '
            f'http://bridgon.com/schemas/bridgon-rdb.xsd"'
            f'\n     ip_name="{ip_name}" regs_id="{ip_name.upper()}_CORE">'
        )
        lines.append('')
        
        registers = hjson_data.get("registers", [])
        
        for idx, reg in enumerate(registers):
            reg_name = reg.get("name", f"REG_{idx}")
            reg_desc = reg.get("desc", reg.get("description", ""))
            swaccess = self.ACCESS_MAP.get(
                reg.get("swaccess", "rw").lower(), "RW"
            )
            reg_width = str(hjson_data.get("regwidth", 32))
            
            # Auto-assign or use declared offset
            offset = reg.get("offset")
            if offset is None:
                # Assume registers are sequential, 4-byte aligned
                offset = f"0x{idx * 4:02X}"
            elif isinstance(offset, int):
                offset = f"0x{offset:02X}"
            
            # Get reset value
            reset_val = "0x0"
            resval = reg.get("resval")
            if resval is not None:
                reset_val = f"0x{int(resval):X}" if isinstance(resval, int) else str(resval)
            
            lines.append(
                f'  <register offset="{offset}" name="{reg_name}"'
                f'\n            display_name="{reg.get("human_name", reg_name)}"'
                f'\n            size="{reg_width}" access="{swaccess}"'
                f'\n            reset_value="{reset_val}">'
            )
            
            if reg_desc:
                # Escape XML special characters
                desc = reg_desc.replace('&', '&').replace('<', '<').replace('>', '>')
                lines.append(f'    <description>{desc}</description>')
            
            # Process bitfields
            fields = reg.get("fields", [])
            for field in fields:
                self._write_bitfield(lines, field, hjson_data)
            
            lines.append('  </register>')
            lines.append('')
        
        lines.append('</rdb>')
        return '\n'.join(lines)
    
    def _write_bitfield(
        self,
        lines: List[str],
        field: Dict[str, Any],
        hjson_data: Dict[str, Any],
    ):
        """Write a single bitfield XML element."""
        bits = field.get("bits", "0")
        msb, lsb = self._parse_bit_range(bits)
        
        field_name = field.get("name", "")
        field_desc = field.get("desc", field.get("description", ""))
        field_access = self.ACCESS_MAP.get(
            field.get("swaccess", "rw").lower(), "RW"
        )
        
        lines.append(
            f'    <bitfield msb="{msb}" lsb="{lsb}"'
            f'\n              name="{field_name}" access="{field_access}">'
        )
        
        if field_desc:
            desc = field_desc.replace('&', '&').replace('<', '<').replace('>', '>')
            lines.append(f'      <description>{desc}</description>')
        
        # Write enum values if present
        enum_vals = field.get("enum", [])
        for enum_entry in enum_vals:
            val = enum_entry.get("value", "0")
            name = enum_entry.get("name", "")
            edesc = enum_entry.get("desc", "")
            lines.append(
                f'      <encoding value="{val}" meaning="{name}: {edesc}"/>'
            )
        
        lines.append('    </bitfield>')
    
    @staticmethod
    def _parse_bit_range(bits: str) -> Tuple[int, int]:
        """Parse bit range string like '7:0' or '31:16' or single '5'."""
        if ':' in bits:
            msb_str, lsb_str = bits.split(':', 1)
            return int(msb_str.strip()), int(lsb_str.strip())
        else:
            bit = int(bits.strip())
            return bit, bit


# ═══════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════

def run_verific_analysis(
    top_module: str,
    filelist: str,
    working_dir: str,
    output_json: str,
) -> str:
    """Run the full Verific-based design analysis pipeline."""
    engine = VerificEngine()
    
    if not engine.initialize():
        print("[FALLBACK] Verific unavailable — switching to Yosys")
        return run_yosys_analysis(top_module, filelist, working_dir, output_json)
    
    # Read file list
    with open(filelist) as f:
        rtl_files = [
            line.strip() for line in f
            if line.strip() and not line.strip().startswith("#")
        ]
    
    print(f"[INFO] Analyzing {len(rtl_files)} RTL files with Verific...")
    
    verilog_exts = {'.v', '.sv', '.svh'}
    vhdl_exts = {'.vhd', '.vhdl'}
    
    for fp in rtl_files:
        ext = Path(fp).suffix.lower()
        if ext in verilog_exts:
            success = engine.analyze_verilog(fp)
        elif ext in vhdl_exts:
            success = engine.analyze_vhdl(fp)
        else:
            print(f"  [SKIP] Unknown extension: {fp}")
            continue
        
        if not success:
            print(f"  [FAIL] {fp}")
    
    # Elaborate
    print(f"[INFO] Elaborating top module: {top_module}")
    if not engine.elaborate(top_module):
        raise RuntimeError(f"Elaboration of '{top_module}' failed")
    
    # Extract parameters
    print("[INFO] Extracting parameters...")
    modules = engine.extract_parameters(top_module)
    
    # Extract registers (if available)
    print("[INFO] Extracting register definitions...")
    registers = engine.extract_registers(top_module)
    
    # Build output
    output = {
        "metadata": {
            "generator": "bridgon_design_analysis",
            "engine": "verific",
            "schema_version": "2.0",
            "timestamp": datetime.now().isoformat(),
            "top_module": top_module,
            "total_modules": len(modules),
        },
        "modules": modules,
        "registers": registers if registers else None,
    }
    
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"[SUCCESS] module_parameters.json → {output_json}")
    print(f"[INFO]   Modules analyzed: {len(modules)}")
    print(f"[INFO]   Register sets:   {len(registers)}")
    
    return output_json


def run_yosys_analysis(
    top_module: str,
    filelist: str,
    working_dir: str,
    output_json: str,
) -> str:
    """Run the full Yosys-based design analysis pipeline."""
    engine = YosysEngine()
    
    if not engine.is_available():
        raise RuntimeError(
            "Yosys not found. Install with: "
            "sudo apt install yosys  (or see https://yosyshq.net/yosys/)"
        )
    
    # Read file list
    with open(filelist) as f:
        rtl_files = [
            line.strip() for line in f
            if line.strip() and not line.strip().startswith("#")
        ]
    
    print(f"[INFO] Analyzing {len(rtl_files)} RTL files with Yosys...")
    
    modules = engine.elaborate_and_extract(rtl_files, top_module, working_dir)
    
    if not modules:
        raise RuntimeError("Yosys extraction produced no results")
    
    # Build output
    output = {
        "metadata": {
            "generator": "bridgon_design_analysis",
            "engine": "yosys",
            "schema_version": "2.0",
            "timestamp": datetime.now().isoformat(),
            "top_module": top_module,
            "total_modules": len(modules),
        },
        "modules": modules,
    }
    
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"[SUCCESS] module_parameters.json → {output_json}")
    print(f"[INFO]   Modules analyzed: {len(modules)}")
    
    return output_json


def run_hjson_import(
    hjson_path: str,
    output_rdb: Optional[str] = None,
    output_prm: Optional[str] = None,
) -> Dict[str, str]:
    """Import Hjson register definitions and convert to Bridgon formats."""
    importer = HjsonRegisterImporter()
    
    if not importer.is_available():
        print("[WARNING] hjson package not installed — using built-in parser")
    
    print(f"[INFO] Parsing Hjson file: {hjson_path}")
    hjson_data = importer.parse_hjson_file(hjson_path)
    
    ip_name = hjson_data.get("name", "UNKNOWN")
    results = {}
    
    # Generate .rdb
    if output_rdb:
        rdb_xml = importer.convert_to_rdb(hjson_data, ip_name)
        with open(output_rdb, 'w') as f:
            f.write(rdb_xml)
        print(f"[SUCCESS] .rdb → {output_rdb}")
        results['rdb'] = output_rdb
    
    # Generate .prm (extract parameters from Hjson)
    if output_prm:
        prm_xml = _generate_prm_from_hjson(hjson_data)
        with open(output_prm, 'w') as f:
            f.write(prm_xml)
        print(f"[SUCCESS] .prm → {output_prm}")
        results['prm'] = output_prm
    
    return results


def _generate_prm_from_hjson(hjson_data: Dict[str, Any]) -> str:
    """Generate a .prm parameter definition file from Hjson data."""
    ip_name = hjson_data.get("name", "UNKNOWN")
    params = hjson_data.get("param_list", [])
    
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append(
        f'<prm xmlns="http://bridgon.com/schemas/param-mapping"'
        f'\n     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        f'\n     xsi:schemaLocation="http://bridgon.com/schemas/param-mapping '
        f'http://bridgon.com/schemas/bridgon-prm.xsd"'
        f'\n     spec_id="IP_{ip_name.upper()}">'
    )
    lines.append('')
    
    for param in params:
        pid = param.get("name", f"PARAM_{len(lines)}")
        ptype = param.get("type", "int").lower()
        default = param.get("default", "")
        desc = param.get("desc", "")
        local = param.get("local", False)
        
        class_map = {"int": "integer", "bit": "integer", "logic": "integer",
                     "string": "string", "bool": "boolean"}
        param_class = class_map.get(ptype, "string")
        
        lines.append(f'  <parameter id="{pid}" class="{param_class}" source="RTL">')
        lines.append(f'    <name>{pid}</name>')
        lines.append(f'    <default>{default}</default>')
        if desc:
            lines.append(f'    <description>{desc}</description>')
        lines.append('  </parameter>')
        lines.append('')
    
    lines.append('</prm>')
    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Bridgon Design Analysis & Parameter Extraction Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Verific-based analysis
  %(prog)s --engine verific --top-module soc_top \\
    --filelist rtl.flist --working-dir /tmp/da --output output.json

  # Yosys-based analysis (free/open-source)
  %(prog)s --engine yosys --top-module uart_core \\
    --filelist rtl.flist --output output.json

  # Import OpenTitan Hjson registers
  %(prog)s --engine hjson --hjson uart.hjson \\
    --output-rdb uart_regs.rdb --output-prm uart_params.prm
"""
    )
    
    parser.add_argument("--engine", choices=["verific", "yosys", "hjson"],
                        default="verific",
                        help="Design analysis engine (default: verific)")
    
    # Verific/Yosys options
    parser.add_argument("--top-module",
                        help="Name of top-level RTL module")
    parser.add_argument("--filelist",
                        help="Text file listing RTL source paths")
    parser.add_argument("--working-dir", default="/tmp/design_analysis",
                        help="Working directory for artifacts")
    parser.add_argument("--output", "--output-json",
                        help="Path for output module_parameters.json")
    
    # Hjson options
    parser.add_argument("--hjson",
                        help="Path to Hjson register definition file")
    parser.add_argument("--output-rdb",
                        help="Path for output .rdb register database file")
    parser.add_argument("--output-prm",
                        help="Path for output .prm parameter definition file")
    
    args = parser.parse_args()
    
    try:
        if args.engine == "hjson":
            if not args.hjson:
                parser.error("--hjson required for hjson engine")
            run_hjson_import(args.hjson, args.output_rdb, args.output_prm)
        
        elif args.engine == "yosys":
            if not all([args.top_module, args.filelist, args.output]):
                parser.error(
                    "--top-module, --filelist, --output required for yosys"
                )
            run_yosys_analysis(
                args.top_module, args.filelist,
                args.working_dir, args.output
            )
        
        else:  # verific
            if not all([args.top_module, args.filelist, args.output]):
                parser.error(
                    "--top-module, --filelist, --output required for verific"
                )
            run_verific_analysis(
                args.top_module, args.filelist,
                args.working_dir, args.output
            )
        
        print("[DONE] Design analysis complete.")
    
    except Exception as e:
        print(f"[FATAL] {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()