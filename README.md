# SoC DocFlow — AI-Powered SoC Reference Manual Automation Platform

<p align="center">
  <img src="vlsi/ChipNexus/vscode-plugin/media/icon.svg" width="120" alt="SoC DocFlow Logo">
</p>

<p align="center">
  <strong>From 6–8 weeks to under 4 hours. Zero parameter errors. Single-source publishing.</strong>
</p>

<p align="center">
  <a href="#-quick-start"><strong>Quick Start</strong></a> &nbsp;|&nbsp;
  <a href="#-architecture"><strong>Architecture</strong></a> &nbsp;|&nbsp;
  <a href="#-subsystems"><strong>Subsystems</strong></a> &nbsp;|&nbsp;
  <a href="#-for-semiconductor-teams"><strong>For Semiconductor Teams</strong></a> &nbsp;|&nbsp;
  <a href="#-custom-solutions"><strong>Custom Solutions</strong></a> &nbsp;|&nbsp;
  <a href="#-getting-started"><strong>Getting Started</strong></a>
</p>

---

## ❓ What Problem Does This Solve?

Modern SoCs contain **50+ IP blocks**, each with **hundreds of registers** and **thousands of configurable parameters**. The Reference Manual documenting all of this is the primary interface between the silicon design team and software developers.

**The Traditional Pain:**
- Engineers manually extract RTL parameter values from synthesis/verification logs (**4–6 hours per IP, 15% error rate**)
- Authors manually type register addresses, bit-field positions, and reset values into XML files
- Configuration parameters are maintained in personal spreadsheets with no version control
- Building the documentation output requires **3–5 attempts per release** due to parameter conflicts
- **6–8 weeks** of manual effort per SoC program

**SoC DocFlow replaces ALL of this** with an automated pipeline that extracts parameters directly from the design using Verific elaboration, generates documentation source programmatically, resolves conditional content automatically, and produces multi-format output (PDF, WebHelp, RAG knowledge base) — all from a single source of truth.

---

## 📊 Results Snapshot

| Metric | Before SoC DocFlow | After SoC DocFlow | Impact |
|:-------|:------------------:|:-----------------:|:-------|
| End-to-End SoC RM Time | 6–8 weeks | **< 4 hours** | ~270× faster |
| Parameter Extraction Accuracy | ~85% | **100%** | Zero errors |
| Manual Address Entry Errors | ~12 per SoC | **0** | Eliminated |
| Non-RTL Parameter Inconsistencies | ~8 per release | **0** | Eliminated |
| Build Failures per Release | 3–5 | **0–1** | 80% reduction |
| Internal Support Queries | Baseline | **−40%** | Self-service via AI chatbot |
| New Author Onboarding | 4 weeks | **1 week** | 75% faster |
| IP Spec Reuse Across SoCs | 30% | **95%** | Single-source publishing |

---

## 🧭 Repository Structure

```
Bridgon/
│
├── README.md                               ← You are here
├── .gitignore
│
└── vlsi/
    ├── ChipNexus/                          ← SoC DocFlow Platform
    │   │
    │   ├── vscode-plugin/                  # VS Code Extension (TypeScript)
    │   │   ├── src/extension.ts             #   Extension entry point
    │   │   ├── package.json                 #   Extension manifest (v2.4.0)
    │   │   ├── tsconfig.json
    │   │   ├── media/                       #   Icons and assets
    │   │   └── out/                         #   Compiled JS output
    │   │
    │   ├── design-analysis/                # RTL Design Analysis
    │   │   └── verific-scripts/
    │   │       └── run_design_analysis.py   #   Verific-based elaboration & extraction
    │   │
    │   ├── tools/                          # Pipeline Tooling
    │   │   ├── param-extractor/             #   RTL parameter extraction engine
    │   │   │   └── param_extract.py
    │   │   ├── inst-generator/              #   Instance map (.imap) generator
    │   │   │   └── inst_gen.py
    │   │   └── dita-resolver/              #   DITA parameter resolution & transform
    │   │       └── resolve_dita.py
    │   │
    │   ├── spec-repo/                      # Specification Repository (Single Source of Truth)
    │   │   ├── IP_DMA_SPEC/                #   DMA Controller Spec
    │   │   ├── IP_FlexCAN_SPEC/            #   FlexCAN Controller Spec
    │   │   ├── IP_GPIO_SPEC/               #   GPIO Peripheral Spec
    │   │   ├── IP_UART_SPEC/               #   UART Peripheral Spec
    │   │   ├── SOC_XYZ_SPEC/               #   Top-Level SoC Spec
    │   │   └── SS_AHB_SPEC/                #   AHB Subsystem Spec
    │   │   └── (each contains spec_source/
    │   │       ├── imap/   ← instance maps
    │   │       ├── prm/    ← parameter definitions
    │   │       ├── rdb/    ← register databases
    │   │       ├── maps/   ← DITA maps & publications
    │   │       ├── topics/ ← documentation topics
    │   │       └── images/ ← diagrams)
    │   │
    │   ├── global-params/                  # SoC-Level Global Parameters
    │   │   └── global_params.prm
    │   │
    │   ├── nonrtl-params-db/               # Non-RTL Parameter Database
    │   │   └── nonrtl_param_db.json        #   Git-versioned JSON "ditabase"
    │   │
    │   ├── rm-explorer/                    # Reference Manual Explorer (Flask)
    │   │   ├── flask-app/
    │   │   │   └── rm_explorer.py          #   Flask web application
    │   │   ├── static/                      #   CSS, JS, images
    │   │   └── templates/                   #   Jinja2 HTML templates
    │   │
    │   ├── chatbot/                        # RAG-Based AI Chatbot
    │   ├── rag-module/                     # Retrieval-Augmented Generation
    │   ├── ui-tool/                        # Web Pipeline Dashboard
    │   │   ├── index.html
    │   │   └── app.js
    │   │
    │   ├── output/                         # Pipeline-Generated Artifacts
    │   │   ├── register_svgs/              #   SVG register bit-field diagrams
    │   │   ├── resolved_dita/              #   Parameter-resolved DITA topics
    │   │   └── webhelp/                    #   Interactive HTML documentation
    │   │
    │   ├── templates/                      # DITA Templates
    │   ├── docs/                           # Documentation & Whitepapers
    │   │   ├── Bridgon_RM_Platform_Project_Report.docx/pdf
    │   │   ├── Bridgon_RM_Platform_Whitepaper.docx/pdf
    │   │   ├── nonrtl_db_update_workflow.html
    │   │   └── rm_platform.html
    │   │
    │   ├── run_pipeline_demo.py            # End-to-End Pipeline Demo Script
    │   ├── SoC_DocFlow_Overview.html       # Visual Overview Webpage
    │   ├── Whitepaper_AI_Driven_SoC_Documentation.md
    │   ├── Project_Report_AI_Reference_Manual_Generation.md
    │   └── parameters_db.odt
    │
    └── opentitan/                          # OpenTitan (separate repo — gitignored)
```

---

## 🏗️ Architecture

### High-Level System Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         VS CODE EXTENSION (Unified UI)                        │
│                                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Design   │  │ Memory   │  │ Non-RTL  │  │ DITA     │  │ RM Explorer  │  │
│  │ Analysis │  │Map→ IMAP │  │ DB       │  │ Generator│  │ Launcher     │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘  │
└───────┼────────────┼────────────┼────────────┼──────────────┼──────────────┘
        │            │            │            │              │
   ┌────▼──────┐ ┌──▼────────┐ ┌─▼─────────┐ ┌─▼────────┐ ┌──▼───────────┐
   │  Verific  │ │ SoC Mem   │ │ Non-RTL   │ │ DITA-OT  │ │  Flask RM    │
   │  Design   │ │ Map       │ │ DB        │ │ + XSLT   │ │  Explorer    │
   │  Elab.    │ │ (XLSX)    │ │ (JSON)    │ │ Engine   │ │  + RAG       │
   └────┬──────┘ └──┬────────┘ └─┬─────────┘ └─┬────────┘ └────┬─────────┘
        │           │            │              │              │
   ┌────▼───────────▼────────────▼──────────────▼──────────────▼──────────────┐
   │                          OUTPUT ARTIFACTS                                 │
   │                                                                          │
   │  module_parameters.json  ──→  IP_PARAMS_TOP.imap  ──→  Resolved DITA    │
   │                                                                │         │
   │                                          ┌─────────────────────┘         │
   │                                          ▼                               │
   │                              PDF / WebHelp / RAG Knowledge Base          │
   └──────────────────────────────────────────────────────────────────────────┘
```

### Data Flow Pipeline (7 Steps)

```
 STEP 1            STEP 2                STEP 3                STEP 4
┌─────────┐     ┌───────────┐        ┌───────────┐        ┌──────────────┐
│ RTL     │     │ SoC       │        │ Non-RTL   │        │ DITA Source  │
│ Filelist│────▶│ MemMap    │───────▶│ DB        │───────▶│ Auto-Gen     │
│ +       │     │ .xlsx     │        │ Enricher  │        │ + Claude API │
│ Verific │     │ + JSON    │        │ (JSON)    │        │              │
│ Elab.   │     │ params    │        │           │        │              │
└────┬────┘     └─────┬─────┘        └─────┬─────┘        └──────┬───────┘
     │                │                    │                      │
     ▼                ▼                    ▼                      ▼
module_params    SOC_top.imap      IP_PARAMS_TOP.imap     .ditamap, .pub,
   .json                                                    .prm, .dita

 STEP 5                STEP 6                STEP 7
┌──────────────┐    ┌──────────────┐     ┌─────────────────┐
│ Custom       │    │ RAG          │     │ Published       │
│ DITA-OT      │───▶│ Knowledge    │     │ Documentation   │
│ Plugin       │    │ Base Ingest  │     │                 │
│ + XSLT       │    │              │     │  ┌─ PDF         │
└──────┬───────┘    └──────┬───────┘     │  ├─ WebHelp     │
       │                   │             │  └─ Chatbot KB  │
       ▼                   ▼             └─────────────────┘
  Resolved DITA       Vector KB
  + Register SVGs     (for AI chatbot)
```

### Design Principles

| Principle | What It Means |
|:----------|:--------------|
| **Single Source of Truth** | Every piece of data — RTL parameters, register definitions, memory map entries — originates from ONE authoritative source and flows automatically through the pipeline. NO manual transcription. |
| **Full Automation with Human Oversight** | Pipeline handles 95% of mechanical work. Humans only create narrative content and review AI-generated chapters. |
| **Defense in Depth** | Multiple validation layers: RTL-vs-documentation checking, address collision detection, conditional processing verification. Errors caught BEFORE publication. |
| **Tool-Agnostic Interfaces** | Abstractions allow swapping Verific for another elaborator, DITA-OT for another publishing engine, Claude for another LLM — without architectural changes. |

---

## 🔧 Subsystems (Detailed)

### 1. VS Code Extension (`vscode-plugin/`)

The unified graphical interface for the entire platform. Designed for mixed-skill teams: from traditional technical writers who prefer XML editing to front-end designers who prefer visual interfaces.

**Key Features:**

| Feature | What It Does |
|:--------|:-------------|
| **One-Click Design Analysis** | Triggers Verific elaboration with pre-configured RTL file lists |
| **Parameter Explorer** | Hierarchical tree view of all parameters, filterable by IP, type (RTL/non-RTL), and value range |
| **Build Pipeline WebView** | Visual workflow with step-by-step progress indicators and collapsible console output |
| **DITA Preview** | Inline preview of auto-generated DITA source with XML syntax highlighting |
| **RM Explorer Launcher** | Single-click launch of the Flask-based documentation explorer |
| **Register Validator** | Side-by-side comparison of .rdb definitions vs. RTL-extracted values |

**Installation:**
```bash
cd vlsi/ChipNexus/vscode-plugin
npm install
npm run compile
# Press F5 in VS Code to launch Extension Development Host
```

**Configuration (`settings.json`):**
```json
{
  "docflow.specRepoPath": "/path/to/spec-repo",
  "docflow.designAnalysisScript": "/path/to/run_design_analysis.py",
  "docflow.nonRtlDbPath": "/path/to/nonrtl_param_db.json",
  "docflow.rmExplorerPort": 5000
}
```

---

### 2. Design Analysis: Verific-Based Parameter Extraction (`design-analysis/`)

The most critical accuracy improvement in the platform. The legacy approach — parsing LEC (Logic Equivalence Checking) tool logs — had a 15% error rate because LEC compares netlists, not the full design hierarchy. Parameter values can appear at incorrect hierarchy levels in comparison logs.

**Verific solves this by:**
- Full SystemVerilog (IEEE 1800-2017) and VHDL (IEEE 1076-2008) parsing
- Complete design elaboration with hierarchy resolution
- Module parameter definitions with their full type system (integer, boolean, string, enumerated, float)
- Hierarchical parameter overrides through `defparam`, module instantiation, and `generate` blocks
- Parameter expressions, dependencies, and macro-resolved values

**Example: Extracted Parameters JSON Fragment**
```json
{
  "module": "flexcan_core",
  "instance_path": "soc_top.ahb_bus.flexcan_0.can_core",
  "parameters": {
    "CAN_NUM_MB": {
      "type": "integer",
      "value": 64,
      "default": 64,
      "source_expression": "64",
      "line_number": 87,
      "file": "flexcan_core.sv",
      "is_overridden": false
    },
    "CAN_FD_ENABLE": {
      "type": "boolean",
      "value": true,
      "default": false,
      "source_expression": "1'b1",
      "line_number": 92,
      "file": "flexcan_core.sv",
      "is_overridden": true,
      "override_source": "soc_top.sv:314"
    }
  }
}
```

**Usage:**
```bash
python3 design-analysis/verific-scripts/run_design_analysis.py \
  --top-module soc_top \
  --filelist rtl/flist/soc.flist \
  --output output/module_parameters.json
```

---

### 3. Memory Map-Driven Instance Map Generator (`tools/inst-generator/`)

Bridges the gap between the hardware architecture team (who maintain the SoC address map in Excel) and the documentation team (who need structured XML Instance Map files).

**Input:** SoC Memory Map spreadsheet (`.xlsx`) with columns:

| Column | Example Value | Description |
|:-------|:-------------|:------------|
| IP_Name | FlexCAN | IP block identifier |
| Instance_Name | FlexCAN_0 | Unique instance identifier |
| Start_Address | 0x40024000 | Base address in hex |
| End_Address | 0x40027FFF | End address in hex |
| Slot_Size | 16K | Address space allocation |
| Address_Space | AHB0 | Bus/address space type |
| RDB_File | FlexCAN_core_regs.rdb | Register database file |
| Spec_Ref | IP_FlexCAN_SPEC | Specification identifier |

**Output:** Structured `.imap` XML file with:
- Register instances with base addresses
- RTL parameter values merged from design analysis JSON
- Support for multi-instance scenarios (e.g., FlexCAN_0 at 0x40024000 with 64 mailboxes vs. FlexCAN_1 at 0x40028000 with 32 mailboxes)

**Usage:**
```bash
python3 tools/inst-generator/inst_gen.py \
  --memmap SoC_MemMap.xlsx \
  --params module_parameters.json \
  --spec-repo spec-repo/ \
  --output SOC_top.imap
```

---

### 4. Non-RTL Parameter Database (`nonrtl-params-db/`)

A critical design insight: parameters fall into two completely different categories.

| Category | Examples | Source | Can Be Automated? |
|:---------|:---------|:-------|:-----------------:|
| **RTL Parameters** | `CAN_NUM_MB=64`, `DMA_CHANNELS=32`, `FIFO_DEPTH=16` | Hardware Design | ✅ Yes — via Verific elaboration |
| **Non-RTL Parameters** | `DOC_REVISION="Rev 2.1"`, `SECURITY_CLASS="CONFIDENTIAL"`, `PUBLISH_MODE="external"`, `CHIP_FAMILY_PREFIX="MCUX"` | Documentation Process | ❌ No — these don't exist in RTL |

The Non-RTL Parameter Database is a **Git-versioned JSON "ditabase"** that stores all non-RTL parameters with hierarchical associations:

```
Parameter → IP Instance → SubSystem → SoC → Chip Family
```

**Example:**
```json
{
  "chip_prefixes": {
    "MCU_X9Z": {
      "instances": {
        "FlexCAN_core_0": {
          "spec_ref": "IP_FlexCAN_SPEC",
          "nonrtl_params": {
            "CAN_DOC_REVISION": "Rev. 2.1",
            "CAN_SECURITY_CLASS": "CONFIDENTIAL",
            "CAN_CONFIDENTIALITY_LEVEL": "PUBLIC"
          }
        },
        "FlexCAN_core_1": {
          "spec_ref": "IP_FlexCAN_SPEC",
          "nonrtl_params": {
            "CAN_DOC_REVISION": "Rev. 2.1",
            "CAN_SECURITY_CLASS": "CONFIDENTIAL",
            "CAN_CONFIDENTIALITY_LEVEL": "INTERNAL"
          }
        }
      },
      "subsystems": {
        "SS_AHB_BUS": {
          "nonrtl_params": {
            "SS_DOC_REVISION": "Rev. 3.0",
            "SS_PUBLISH_MODE": "external"
          }
        }
      },
      "soc_level_params": {
        "SOC_DOC_REVISION": "Rev. 3.0",
        "SOC_CHIP_FAMILY": "MCU_X9Z",
        "SOC_PRODUCT_NAME": "MCU X9Z Series Automotive Microcontroller"
      }
    }
  }
}
```

**Why JSON instead of SQL?**
- ✅ **Version-control friendly:** Diffable and mergeable in Git
- ✅ **Zero infrastructure:** No database server required
- ✅ **Schema-flexible:** Naturally accommodates deeply nested hierarchies
- ✅ **Directly consumable:** Python, JavaScript, and TCL tooling can all read it natively

---

### 5. AI-Assisted DITA Source Generation

Automates the most labor-intensive documentation task: assembling the hierarchical document structure (DITA maps, publications, parameter definitions) and generating SoC-specific chapter content from architecture specifications using the Claude API.

**What Gets Auto-Generated:**

| Artifact | Description |
|:---------|:------------|
| **`.ditamap`** | SoC-level DITA map with `ipref` links to each IP spec, `ssref` links to SubSystem specs, and references to SoC-specific chapters |
| **`.pub`** | Publishing instructions defining register resolution groups, instance selectors, merging rules |
| **`.prm`** | SoC-level parameter definitions aggregating all parameters referenced across IP and SubSystem specs |
| **`.dita` topics** | SoC-specific chapters: clocking architecture, reset architecture, interrupt mapping, power management, memory map overview |

**AI Chapter Generation Example (Claude API Prompt):**

```
You are a semiconductor documentation architect. Given the attached
architecture specification PDF for SoC MCU_X9Z, extract and structure
the following as DITA topic types:

1. CLOCKING ARCHITECTURE (concept topic):
   - Clock sources (oscillators, PLLs, external inputs)
   - Clock tree hierarchy
   - Clock domain assignments per IP block
   - Clock gating and power-saving mechanisms

2. RESET ARCHITECTURE (concept topic):
   - Reset sources (power-on, external pin, watchdog, software)
   - Reset sequencing and timing
   - Reset domains and signal distribution

3. INTERRUPT MAPPING (reference topic):
   - Interrupt controller configuration (NVIC/GIC)
   - Vector table with source-to-vector assignments
   - Priority levels and nesting behavior
   - Wakeup-capable interrupt sources

Cross-reference all register names to their .rdb definitions.
Format output as valid DITA 2.0 XML.
```

**IMPORTANT:** All AI-generated chapters are reviewed by human authors before inclusion. The platform automates **extraction and structuring** but preserves **human oversight** for technical accuracy.

---

### 6. Resolved DITA & Register Diagram Generation (`tools/dita-resolver/`)

A custom DITA-OT plugin that processes parameterized DITA source through a multi-stage pipeline:

**Stage 1: Parameter Resolution**
Evaluates `pm:cond_*` attributes on DITA elements against instantiated parameter values:

```xml
<!-- This topicref is included ONLY when CAN_FD_ENABLE=true -->
<topicref href="FlexCAN_CANFD_Support.dita"
          pm:cond_CAN_FD_ENABLE="true">
```

Elements whose parameter conditions match the instance configuration are retained; non-matching elements are suppressed. Since parameter values come directly from design elaboration, conditional processing is guaranteed consistent with hardware.

**Stage 2: Register File Transformation**

The `.rdb` (Register Database) format is transformed into DITA reference topics with:

| Output Element | Description |
|:---------------|:------------|
| **SVG Bit-Field Diagrams** | Register layout with colour-coded access types: Blue (R/W), Green (RO), Orange (W1C) |
| **HTML Tables** | Columns: Offset, Field Name, Bit Range, Access, Reset Value, Description |
| **Cross-Reference Links** | Links to related registers, programming model topics |

**Example: Generated SVG Register Diagram**

```
 ┌────────────────── FlexCAN_MCR (0x00) ─── Reset: 0x5000000F ──────────────────┐
 │  31   30   29   28   27   26   25:24    23   22   21:18   17      16   15:8  │
 │ ┌───┐┌───┐┌───┐┌───┐┌───┐┌──────┐ ┌───┐┌───┐┌──────┐┌───┐ ┌──────┐┌──────┐ │
 │ │MDIS││FRZ││   ││   ││   ││CLK_SRC│ │   ││   ││      ││SRX│ │      ││      │ │
 │ │RW ││RW ││   ││   ││   ││ RW   │ │   ││   ││      ││DIS│ │      ││      │ │
 │ └───┘└───┘└───┘└───┘└───┘└──────┘ └───┘└───┘└──────┘└───┘ └──────┘└──────┘ │
 │                                                                              │
 │  7:0                                                                        │
 │ ┌──────┐  Legend:  ■ R/W  ■ RO  ■ W1C                                      │
 │ │MAXMB │                                                                     │
 │ │ RW   │                                                                     │
 │ └──────┘                                                                     │
 └──────────────────────────────────────────────────────────────────────────────┘
```

**Stage 3: Memory Map Generation**
For multi-instance scenarios, generates tables showing each instance's base address, address range, and instance-specific configuration:

| Instance | Base Address | Address Range | CAN_NUM_MB | CAN_FD_ENABLE |
|:---------|:-------------|:--------------|:----------:|:-------------:|
| FlexCAN_0 | 0x4002_4000 | 0x4002_4000 – 0x4002_7FFF | 64 | Enabled |
| FlexCAN_1 | 0x4002_8000 | 0x4002_8000 – 0x4002_BFFF | 32 | Disabled |

**Stage 4: Multi-Format Output**

| Format | Technology | Use Case |
|:-------|:-----------|:---------|
| **PDF** | DITA-OT PDF2 + custom XSL-FO | Corporate template, print-ready, official release |
| **WebHelp** | Responsive HTML5 | Collapsible TOC, full-text search, bookmark persistence |
| **RAG Knowledge Base** | Chunked embeddings | AI chatbot context for natural language queries |

---

### 7. Reference Manual Explorer (`rm-explorer/`)

A Flask-based web application that transforms resolved DITA content into an interactive documentation portal with integrated AI chatbot.

**WebHelp Frontend Features:**
- Collapsible sidebar TOC derived from the resolved ditamap
- Register information displayed as interactive SVG diagrams with hover tooltips
- System-level memory map visualization with colour-coded IP blocks
- Full-text search across all documentation topics
- Responsive design for desktop and tablet access

**RAG-Based AI Chatbot:**

```
User Query ──→ ┌────────────────┐    ┌────────────────┐
"What is the   │  Embedding     │───▶│ Vector Search   │
reset value of │  Model         │    │ (Cosine Sim.)   │
FlexCAN MCR?"  └────────────────┘    └───────┬────────┘
                                              │
                                     Top-5 Chunks Retrieved
                                              │
                                              ▼
                                    ┌────────────────┐    ┌────────────────┐
                                    │ Claude API     │───▶│ Grounded       │
                                    │ (Context + Q)  │    │ Response       │
                                    └────────────────┘    └────────────────┘
```

**Example Chatbot Interaction:**

> **User:** What is the reset value of the FlexCAN MCR register?

> **Chatbot:** The FlexCAN Module Configuration Register (MCR) at offset 0x00 has a reset value of **0x5000000F**. This 32-bit register contains:
> - Bit 31 (MDIS): Module Disable — resets to 0
> - Bit 30 (FRZ): Freeze Enable — resets to 0
> - Bits 25:24 (CLK_SRC): Clock Source Selection — resets to 00
> - Bits 7:0 (MAXMB): Max Number of Mailboxes — resets to 0x0F (15)
>
> *Source: FlexCAN Module — Module Configuration Register (MCR), §4.2.1*

**Launch:**
```bash
cd vlsi/ChipNexus/rm-explorer/flask-app
pip install flask
python3 rm_explorer.py
# Open http://localhost:5000
```

---

## 📁 Core File Formats Reference

### Format Overview

| Extension | Name | Purpose | Schema |
|:----------|:-----|:--------|:-------|
| `.rdb` | Register Database | Defines registers, bitfields, access types, reset values | Custom XML (IP-XACT compatible) |
| `.imap` | Instance Map | Instantiates parameter values for a specific documentation instance | Custom XML with `pm:` namespace |
| `.prm` | Parameter Definition | Defines configurable parameters with defaults, constraints, types | Custom XML |
| `.pub` | Publishing Instructions | Defines resolve groups, instance selectors, merging rules | Custom XML |
| `.ditamap` | DITA Map | Hierarchical documentation structure | OASIS DITA 2.0 + `pm:cond_*` |
| `.dita` | DITA Topic | Individual documentation topic | OASIS DITA 2.0 |

### Register Database Example (`.rdb`)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<registers xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           ip_name="FlexCAN" regs_id="CAN_CORE">

  <register offset="0x00" name="MCR"
            display_name="Module Configuration Register"
            size="32" access="RW" reset_value="0x5000000F">
    <description>Contains global module control and configuration bits for
    the FlexCAN module, including freeze, halt, and supervisory mode
    settings.</description>

    <bitfield msb="31" lsb="31" name="MDIS" access="RW">
      <description>Module Disable — 0: Module enabled, 1: Clock gated</description>
    </bitfield>
    <bitfield msb="30" lsb="30" name="FRZ" access="RW">
      <description>Freeze Enable — Enables entry to Freeze mode upon FRZ_ACK</description>
    </bitfield>
    <bitfield msb="25" lsb="24" name="CLK_SRC" access="RW">
      <description>Clock Source — 00: Oscillator, 01: PLL, 10: External, 11: Reserved</description>
    </bitfield>
    <bitfield msb="7" lsb="0" name="MAXMB" access="RW">
      <description>Maximum Number of Mailboxes (0..127)</description>
    </bitfield>
  </register>
</registers>
```

### Parameter Definition Example (`.prm`)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<param_definitions xmlns:pm="http://bridgon.org/schema/param-mapping">

  <param id="CAN_NUM_MB" class="integer" source="RTL">
    <description>Number of CAN message buffers (mailboxes)</description>
    <default_value>64</default_value>
    <low_limit>16</low_limit>
    <high_limit>128</high_limit>
  </param>

  <param id="CAN_FD_ENABLE" class="boolean" source="RTL">
    <description>Enable CAN-FD (Flexible Data-Rate) support</description>
    <default_value>false</default_value>
  </param>

  <param id="CAN_DOC_REVISION" class="string" source="nonrtl">
    <description>Document revision string for published output</description>
    <default_value>Rev. 1.0</default_value>
  </param>

  <param id="CAN_SECURITY_CLASS" class="enumerated" source="nonrtl">
    <description>Security classification for documentation</description>
    <default_value>PUBLIC</default_value>
    <accepted_values>
      <value>PUBLIC</value>
      <value>INTERNAL</value>
      <value>CONFIDENTIAL</value>
      <value>RESTRICTED</value>
    </accepted_values>
  </param>

</param_definitions>
```

### Parameter Class System

| Class | Validation Rule | Example Value |
|:------|:----------------|:--------------|
| `integer` | Bounded by `low_limit` and `high_limit` | `64` (range: 16–128) |
| `boolean` | Must be `"true"` or `"false"` | `true` |
| `float` | Any decimal value | `2.5` |
| `string` | Free-form text | `"Rev. 2.1"` |
| `enumerated` | Must match one of the listed `accepted_values` | `"CONFIDENTIAL"` |

---

## 🎯 For Semiconductor Documentation Teams

### Who Benefits From This Platform?

| Role | Pain Point Solved |
|:-----|:------------------|
| **Technical Writers** | No more manual register table typing, parameter value transcription, or DITA map assembly. Focus on creating high-quality narrative content and reviewing AI-generated chapters. |
| **RTL Design Engineers** | Zero time spent supporting documentation parameter extraction. RTL is parsed automatically by Verific elaboration. |
| **Architecture Teams** | Memory map spreadsheets become the single source of truth — changes propagate automatically to documentation without manual re-entry. |
| **Verification Engineers** | RTL-to-documentation validation catches register description errors before publication. |
| **Applications Engineers** | Self-service AI chatbot answers register-level questions instantly, reducing support query volume by 40%. |
| **Field Application Engineers** | Interactive webhelp with full-text search replaces multi-thousand-page PDFs on tablet devices. |
| **Documentation Managers** | 270× faster cycle time, zero parameter errors, cross-geo standardization, 75% faster new author onboarding. |

### How to Adopt This Platform In Your Organization

#### Phase 1: Assessment (Week 1–2)

1. **Inventory your current documentation artifacts:**
   - What register description formats do you use? (IP-XACT, SystemRDL, custom XML, Word tables, Excel)
   - How are memory maps maintained? (Spreadsheets, RTL attributes, address manager tools)
   - What publishing formats do you need? (PDF, HTML, DITA, FrameMaker, custom web portals)

2. **Identify your single sources of truth:**
   - RTL parameters: Which synthesis/elaboration tools are available? (Verific, Design Compiler, Genus)
   - Non-RTL parameters: Where do revision strings, security classifications, and publishing modes live today?
   - Register databases: Do you have .rdb files, IP-XACT, or SystemRDL sources?

3. **Map your pipeline stages:**
   - How does register information flow from RTL → documentation today?
   - Where do manual transcription steps exist? (These are your automation targets)
   - What review/approval gates are required?

#### Phase 2: Customization (Week 3–6)

1. **Adapter for your register format:**
   If you use IP-XACT instead of `.rdb`, write a converter:

   ```python
   def ipxact_to_rdb(ipxact_path: str, rdb_output_path: str):
       """Convert IEEE 1685 IP-XACT to SoC DocFlow .rdb format."""
       import xml.etree.ElementTree as ET
       tree = ET.parse(ipxact_path)
       ns = {'spirit': 'http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009'}

       rdb_root = ET.Element('registers', ip_name="...")

       for reg in tree.findall('.//spirit:register', ns):
           rdb_reg = ET.SubElement(rdb_root, 'register', {
               'name': reg.find('spirit:name', ns).text,
               'offset': reg.find('spirit:addressOffset', ns).text,
               'size': reg.find('spirit:size', ns).text,
           })
           # ... map fields and descriptions

       ET.indent(rdb_root)
       tree_out = ET.ElementTree(rdb_root)
       tree_out.write(rdb_output_path, encoding='utf-8', xml_declaration=True)
   ```

2. **Adapter for your parameter extraction tool:**
   If you use a different design elaboration tool, adapt the extraction script:

   ```python
   def extract_params_with_design_compiler(
       filelist: List[str],
       top_module: str,
       output_json: str
   ):
       """Extract parameters using Synopsys Design Compiler instead of Verific."""
       # Generate TCL script for DC
       tcl_script = f"""
       analyze -format sverilog {" ".join(filelist)}
       elaborate {top_module}
       # ... DC-specific parameter extraction commands
       """
       # Execute and parse output into module_parameters.json
   ```

3. **Non-RTL Database Migration:**
   Migrate your existing spreadsheets to the JSON format:

   ```python
   import pandas as pd
   import json

   df = pd.read_excel("non_rtl_params.xlsx")
   db = {"chip_prefixes": {}}

   for _, row in df.iterrows():
       chip = row['chip_prefix']
       if chip not in db['chip_prefixes']:
           db['chip_prefixes'][chip] = {"instances": {}}

       db['chip_prefixes'][chip]['instances'][row['instance_name']] = {
           "spec_ref": row['spec_ref'],
           "nonrtl_params": json.loads(row['params_json'])
       }

   with open("nonrtl_param_db.json", "w") as f:
       json.dump(db, f, indent=2)
   ```

4. **Output format customization:**
   Swap DITA-OT PDF2 stylesheets for your corporate template:
   ```bash
   cp /path/to/corporate/stylesheet.xsl tools/dita-resolver/styles/
   # Update resolve_dita.py to reference the new stylesheet
   ```

#### Phase 3: Pilot Program (Week 7–8)

1. **Select a pilot IP block** — Choose one IP (e.g., UART) with well-defined registers and an existing manual
2. **Run the full pipeline** as a side-by-side comparison with the existing manual process
3. **Validate register accuracy** — Compare every register field, address, and reset value
4. **Gather author feedback** — What's faster? What needs improvement?
5. **Iterate on the adapter layer** based on feedback

#### Phase 4: Rollout (Week 9+)

1. **Onboard remaining IP specs** into the spec-repo structure
2. **Connect to CI/CD** — Trigger automatic RM builds on RTL commits
3. **Train the team** on the VS Code extension workflow
4. **Decommission the legacy process** — No more manual parameter spreadsheets

---

## 🏗️ Building Custom Solutions on SoC DocFlow

### Customization Axes

The platform is designed with modularity at every layer. Here's what you can customize and how:

```
┌─────────────────────────────────────────────────────────────────┐
│                     CUSTOMIZATION LAYERS                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. REGISTER FORMAT  ← Swap .rdb for IP-XACT, SystemRDL, CSR   │
│                              spec, or CSV                       │
│                                                                 │
│  2. ELABORATION ENGINE  ← Swap Verific for DC, Genus, Jasper,   │
│                              or open-source Yosys               │
│                                                                 │
│  3. PARAMETER DB  ← Swap JSON for SQLite, PostgreSQL, REST API  │
│                                                                 │
│  4. AI MODEL  ← Swap Claude for GPT-4, LLaMA, or local models   │
│                                                                 │
│  5. PUBLISHING ENGINE  ← Swap DITA-OT for Sphinx, AsciiDoc,    │
│                              MkDocs, or custom HTML generator    │
│                                                                 │
│  6. UI LAYER  ← Swap VS Code for web dashboard, CLI, or REST   │
│                              API                                │
│                                                                 │
│  7. OUTPUT FORMATS  ← Add PDF/A, Markdown, Confluence,          │
│                              Jupyter Book, or custom portal      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Scenario 1: Adding IP-XACT Import Support

```python
# Create: tools/ipxact-converter/ipxact_to_rdb.py
"""
Convert IEEE 1685-2014 IP-XACT register descriptions to
SoC DocFlow's .rdb format for pipeline compatibility.
"""

import xml.etree.ElementTree as ET

def convert_ipxact_to_rdb(ipxact_path: str, rdb_output_path: str):
    """
    Reads a IP-XACT memory map file and produces a SoC DocFlow
    .rdb register database file.

    IP-XACT structure:
      memoryMap → addressBlock → register → field

    Mapped to .rdb:
      registers → register → bitfield
    """
    tree = ET.parse(ipxact_path)
    root = tree.getroot()

    # Determine namespace dynamically
    ns = {'spirit': 'http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2014'}

    ip_name = root.find('.//spirit:component/spirit:name', ns).text

    rdb = ET.Element('registers', ip_name=ip_name, regs_id=ip_name.upper())

    for reg_elem in root.findall('.//spirit:register', ns):
        name = reg_elem.find('spirit:name', ns).text
        offset = reg_elem.find('spirit:addressOffset', ns).text
        size = reg_elem.find('spirit:size', ns).text or '32'

        desc_elem = reg_elem.find('spirit:description', ns)
        description = desc_elem.text if desc_elem is not None else ''

        reg = ET.SubElement(rdb, 'register', {
            'offset': offset,
            'name': name,
            'size': size,
            'access': 'RW',
            'reset_value': '0x0'
        })

        if description:
            desc = ET.SubElement(reg, 'description')
            desc.text = description

        for field_elem in reg_elem.findall('.//spirit:field', ns):
            field_name = field_elem.find('spirit:name', ns).text
            bit_offset = int(field_elem.find('spirit:bitOffset', ns).text)
            bit_width = int(field_elem.find('spirit:bitWidth', ns).text)
            msb = bit_offset + bit_width - 1
            lsb = bit_offset

            bf = ET.SubElement(reg, 'bitfield', {
                'msb': str(msb),
                'lsb': str(lsb),
                'name': field_name,
                'access': 'RW'
            })

            field_desc = field_elem.find('spirit:description', ns)
            if field_desc is not None and field_desc.text:
                bf_desc = ET.SubElement(bf, 'description')
                bf_desc.text = field_desc.text

    ET.indent(rdb)
    ET.ElementTree(rdb).write(rdb_output_path, encoding='utf-8', xml_declaration=True)

    print(f"✅ Converted {ipxact_path} → {rdb_output_path}")
```

### Scenario 2: Using Yosys (Open-Source) Instead of Verific

```python
# Create: design-analysis/yosys-scripts/extract_params.py
"""
Extract SystemVerilog parameters using Yosys (open-source synthesis tool).
Alternative to Verific for organizations without a Verific license.
"""

import subprocess
import json
import re

def extract_params_yosys(filelist: list[str], top_module: str) -> dict:
    """
    Use Yosys to elaborate the design and extract parameter values.

    Advantages:
      - Free and open-source
      - Supports SystemVerilog IEEE 1800-2017 subset
      - No license server or commercial toolchain required

    Limitations (vs. Verific):
      - Limited VHDL 2008 support
      - Some SystemVerilog constructs not fully supported
      - No parameter expression traceback to source line numbers
    """

    # Build Yosys script
    yosys_script = f"""
    # Read all design files
    {" ".join(f'read_verilog -sv {f}' for f in filelist)}

    # Elaborate the top module
    hierarchy -top {top_module}

    # Extract design hierarchy and parameters
    tee -o /tmp/yosys_hierarchy.txt hierarchy

    # Extract parameters
    tee -o /tmp/yosys_params.txt param
    """

    # Execute Yosys
    proc = subprocess.run(
        ['yosys', '-p', yosys_script],
        capture_output=True, text=True
    )

    # Parse Yosys output to build module_parameters.json
    parameters = {}

    # Yosys "param" command output format:
    #   \module_name.parameter_name = value
    param_pattern = re.compile(r'\\(.+?)\.(.+?) = (.+)')

    for line in proc.stdout.split('\n'):
        match = param_pattern.match(line.strip())
        if match:
            module_path, param_name, value = match.groups()
            if module_path not in parameters:
                parameters[module_path] = {}
            parameters[module_path][param_name] = {
                "value": value.strip(),
                "type": "auto-detected",
                "source": "yosys_elaboration"
            }

    return parameters
```

### Scenario 3: Adding a Sphinx/AsciiDoc Output Pipeline

```python
# Create: tools/sphinx-generator/dita_to_rst.py
"""
Convert resolved DITA to reStructuredText for Sphinx documentation.
Enables teams using Python documentation ecosystems (Sphinx, ReadTheDocs)
to leverage the SoC DocFlow pipeline.
"""

import xml.etree.ElementTree as ET
from pathlib import Path

def dita_to_rst(dita_dir: str, rst_output_dir: str):
    """
    Walk a directory of resolved DITA topics and convert each to
    reStructuredText (.rst) format suitable for Sphinx builds.

    Conversion mapping:
      DITA <topic>     → RST document with title
      DITA <section>   → RST section (underlined heading)
      DITA <table>     → RST grid table
      DITA <codeph>    → RST ``inline literal``
      DITA <b>         → RST **bold**
      DITA <i>         → RST *italic*
      DITA <xref>      → RST :ref:`target`
      DITA <image>     → RST .. image:: directive
    """

    dita_path = Path(dita_dir)
    rst_path = Path(rst_output_dir)
    rst_path.mkdir(parents=True, exist_ok=True)

    for dita_file in dita_path.rglob("*.dita"):
        tree = ET.parse(dita_file)
        root = tree.getroot()

        rst_lines = []

        # Extract title
        title = root.find('title')
        if title is not None and title.text:
            rst_lines.append("=" * len(title.text))
            rst_lines.append(title.text)
            rst_lines.append("=" * len(title.text))
            rst_lines.append("")

        # Process body elements
        body = root.find('body')
        if body is not None:
            for elem in body:
                if elem.tag == 'section':
                    section_title = elem.find('title')
                    if section_title is not None and section_title.text:
                        rst_lines.append(section_title.text)
                        rst_lines.append("-" * len(section_title.text))
                        rst_lines.append("")
                    # Recurse into section content
                    rst_lines.extend(_process_body_elements(elem))

                elif elem.tag == 'table':
                    rst_lines.extend(_dita_table_to_rst_grid(elem))

                elif elem.tag == 'p':
                    text = _process_inline_markup(elem)
                    rst_lines.append(text)
                    rst_lines.append("")

                elif elem.tag == 'image':
                    href = elem.get('href', '')
                    alt = elem.find('alt')
                    alt_text = alt.text if alt is not None else ''
                    rst_lines.append(f".. image:: {href}")
                    rst_lines.append(f"   :alt: {alt_text}")
                    rst_lines.append("")

        # Write RST file
        rst_file = rst_path / dita_file.with_suffix('.rst').name
        rst_file.write_text('\n'.join(rst_lines))
        print(f"  Converted: {dita_file.name} → {rst_file.name}")


def _process_body_elements(parent) -> list[str]:
    """Process DITA body-level elements into RST lines."""
    lines = []
    for elem in parent:
        if elem.tag in ('p', 'note'):
            text = _process_inline_markup(elem)
            if elem.tag == 'note':
                lines.append(f".. note:: {text}")
            else:
                lines.append(text)
            lines.append("")
    return lines


def _process_inline_markup(elem) -> str:
    """Convert DITA inline elements to RST markup."""
    text_parts = []
    if elem.text:
        text_parts.append(elem.text)
    for child in elem:
        if child.tag == 'b':
            text_parts.append(f"**{child.text}**")
        elif child.tag == 'i':
            text_parts.append(f"*{child.text}*")
        elif child.tag == 'codeph':
            text_parts.append(f"``{child.text}``")
        elif child.tag == 'xref':
            target = child.get('href', '')
            text_parts.append(f":ref:`{child.text or target}<{target}>`")
        else:
            if child.text:
                text_parts.append(child.text)
        if child.tail:
            text_parts.append(child.tail)
    return ''.join(text_parts)


def _dita_table_to_rst_grid(table_elem) -> list[str]:
    """Convert DITA table to RST grid table format."""
    # Extract table structure: title → colspecs → tgroup → thead/tbody → rows
    # This is a simplified example — a production version would handle:
    #   - colspec widths
    #   - column spans (namest/nameend)
    #   - rowsep/colsep
    #   - entry alignment

    lines = []

    title = table_elem.find('title')
    if title is not None and title.text:
        lines.append(f".. table:: {title.text}")
        lines.append("")

    # Collect all rows
    rows = []
    for row in table_elem.findall('.//row'):
        cells = []
        for entry in row.findall('entry'):
            cells.append(entry.text or '')
        rows.append(cells)

    if not rows:
        return lines

    # Build grid table
    col_count = len(rows[0])
    col_widths = []
    for c in range(col_count):
        max_w = max(len(row[c]) for row in rows) + 2
        col_widths.append(max_w)

    # Separator line
    sep = '+' + '+'.join('-' * w for w in col_widths) + '+'

    lines.append(sep)

    # Header row
    header = '|' + '|'.join(f" {rows[0][c]:<{col_widths[c]-1}}" for c in range(col_count)) + '|'
    lines.append(header)

    # Header separator
    header_sep = '+' + '+'.join('=' * w for w in col_widths) + '+'
    lines.append(header_sep)

    # Data rows
    for row in rows[1:]:
        data_line = '|' + '|'.join(f" {row[c]:<{col_widths[c]-1}}" for c in range(col_count)) + '|'
        lines.append(data_line)
        lines.append(sep)

    lines.append("")
    return lines
```

### Scenario 4: Multi-Language Support

```python
# Create: tools/i18n/generate_multilang.py
"""
Extend the pipeline to generate translated Reference Manuals.
Supports Chinese, Japanese, and other languages from the same DITA source.
"""

import anthropic

def generate_translated_topics(
    dita_source_dir: str,
    target_language: str,
    claude_api_key: str
):
    """
    Use Claude API to translate resolved DITA topics while preserving
    XML structure, cross-references, and technical terminology.

    The AI is prompted to:
      - Preserve all XML tags and attributes exactly
      - Keep register names, bit-field names, and addresses untranslated
      - Use established semiconductor terminology in the target language
      - Maintain table structures and code blocks
      - Localize descriptions while preserving technical accuracy
    """

    client = anthropic.Anthropic(api_key=claude_api_key)

    language_config = {
        'zh-CN': {
            'name': 'Simplified Chinese',
            'terminology_rules': [
                'Use GB/T 11499 standard semiconductor terminology',
                'Keep all register names and signal names in English',
                'Translate descriptions to natural Chinese technical prose',
                'Use full-width punctuation (，。；：)',
            ]
        },
        'ja-JP': {
            'name': 'Japanese',
            'terminology_rules': [
                'Use JEITA standard semiconductor terminology',
                'Keep all register names and signal names in English',
                'Use katakana for foreign technical terms',
                'Translate descriptions to natural Japanese technical prose',
            ]
        },
    }

    config = language_config.get(target_language)
    if not config:
        raise ValueError(f"Unsupported language: {target_language}")

    # Walk DITA source and translate each topic
    dita_path = Path(dita_source_dir)
    for dita_file in dita_path.rglob("*.dita"):
        original = dita_file.read_text(encoding='utf-8')

        prompt = f"""You are a semiconductor documentation translator specializing
in {config['name']} ({target_language}) translations.

Translation rules:
{chr(10).join(f'- {rule}' for rule in config['terminology_rules'])}

Translate the following DITA XML topic to {config['name']}:
<dita>
{original}
</dita>

Return ONLY the translated XML. Do not modify any XML tags, attributes,
cross-references (href), or code blocks. Keep register names, bit-field
names, and addresses exactly as they are."""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )

        translated = response.content[0].text

        # Preserve XML by extracting between <dita> tags from response
        # (production code would use XML parsing for robustness)

        output_dir = Path(f"output/translated/{target_language}")
        output_dir.mkdir(parents=True, exist_ok=True)

        relative = dita_file.relative_to(dita_source_dir)
        output_path = output_dir / relative
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(translated, encoding='utf-8')

    print(f"✅ Translated all topics to {config['name']}")
```

---

## 🚀 Getting Started

### Prerequisites

| Tool | Version | Purpose |
|:-----|:--------|:--------|
| **Python** | 3.9+ | Pipeline scripts, Flask explorer, parameter extraction |
| **Node.js** | 18+ | VS Code extension compilation |
| **VS Code** | 1.85+ | Extension host |
| **Git** | 2.0+ | Version control for spec-repo and non-RTL parameter database |

### 5-Minute Quick Start

```bash
# 1. Clone the repository
git clone <repo-url> Bridgon
cd Bridgon

# 2. Run the end-to-end pipeline demo
cd vlsi/ChipNexus
python3 run_pipeline_demo.py

# 3. Check generated outputs
ls output/register_svgs/       # SVG register diagrams
ls output/resolved_dita/        # Parameter-resolved DITA topics
ls output/webhelp/              # Interactive HTML documentation

# 4. View the webhelp output
open output/webhelp/index.html   # macOS
xdg-open output/webhelp/index.html  # Linux
start output/webhelp/index.html   # Windows

# 5. Launch the Reference Manual Explorer
cd rm-explorer/flask-app
pip install flask
python3 rm_explorer.py
# Open http://localhost:5000 in your browser

# 6. Install the VS Code extension (optional)
cd ../vscode-plugin
npm install
npm run compile
# In VS Code: Press F5 → launches Extension Development Host
# Run "SoC DocFlow: Open Pipeline Panel" from Command Palette (Ctrl+Shift+P)
```

### Adding Your Own IP Spec to the Spec Repository

To add a new IP block to the documentation pipeline:

```bash
# Create the spec directory structure
mkdir -p vlsi/ChipNexus/spec-repo/IP_MYIP_SPEC/spec_source/{imap,prm,rdb,maps,topics,images}

# 1. Create your register database (.rdb)
# vlsi/ChipNexus/spec-repo/IP_MYIP_SPEC/spec_source/rdb/myip_regs.rdb
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<registers ip_name="MY_IP" regs_id="MY_IP_CORE">
  <register offset="0x00" name="CTRL" display_name="Control Register"
            size="32" access="RW" reset_value="0x00000000">
    <description>Primary control register for MY_IP module.</description>
    <bitfield msb="31" lsb="31" name="EN" access="RW">
      <description>Enable bit — 0: Disabled, 1: Enabled</description>
    </bitfield>
    <bitfield msb="15" lsb="0" name="CONFIG" access="RW">
      <description>Configuration value (16-bit)</description>
    </bitfield>
  </register>

  <register offset="0x04" name="STATUS" display_name="Status Register"
            size="32" access="RO" reset_value="0x00000000">
    <description>Read-only status register.</description>
    <bitfield msb="31" lsb="31" name="READY" access="RO">
      <description>Ready flag — 0: Busy, 1: Ready</description>
    </bitfield>
    <bitfield msb="30" lsb="30" name="ERROR" access="W1C">
      <description>Error flag — Write 1 to clear</description>
    </bitfield>
  </register>
</registers>
```

```bash
# 2. Create your parameter definitions (.prm)
# vlsi/ChipNexus/spec-repo/IP_MYIP_SPEC/spec_source/prm/myip.prm
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<param_definitions>
  <param id="MY_IP_CHANNELS" class="integer" source="RTL">
    <description>Number of data channels</description>
    <default_value>4</default_value>
    <low_limit>1</low_limit>
    <high_limit>16</high_limit>
  </param>
  <param id="MY_IP_FIFO_DEPTH" class="integer" source="RTL">
    <description>FIFO depth per channel</description>
    <default_value>256</default_value>
    <low_limit>64</low_limit>
    <high_limit>4096</high_limit>
  </param>
  <param id="MY_IP_DOC_REVISION" class="string" source="nonrtl">
    <description>Document revision</description>
    <default_value>Rev. 1.0</default_value>
  </param>
</param_definitions>
```

```bash
# 3. Add to the Non-RTL Parameter Database
# Edit vlsi/ChipNexus/nonrtl-params-db/nonrtl_param_db.json
# Add your IP instance entries under the appropriate chip_prefix

# 4. Create the instance map (.imap)
# vlsi/ChipNexus/spec-repo/IP_MYIP_SPEC/spec_source/imap/MY_IP_top.imap

# 5. Re-run the pipeline
python3 run_pipeline_demo.py
```

---

## 📈 Adoption & Impact Metrics

| Metric | Value |
|:-------|:------|
| Active Users | **40+** (technical writers, front-end designers, applications engineers) |
| Product Lines | **5** actively using the platform |
| SoC Programs | **100%** of new programs onboarded |
| Rollbacks to Legacy | **Zero** since initial deployment |
| Reference Manuals Generated | **50+** through the platform |
| Cross-Geo Teams | India, France, Italy, USA using identical toolchains |

---

## 📚 Full Documentation

| Document | Format | Path |
|:---------|:-------|:-----|
| **White Paper** | Markdown | [`vlsi/ChipNexus/Whitepaper_AI_Driven_SoC_Documentation.md`](vlsi/ChipNexus/Whitepaper_AI_Driven_SoC_Documentation.md) |
| **Project Report** | Markdown | [`vlsi/ChipNexus/Project_Report_AI_Reference_Manual_Generation.md`](vlsi/ChipNexus/Project_Report_AI_Reference_Manual_Generation.md) |
| **Visual Overview** | HTML | [`vlsi/ChipNexus/SoC_DocFlow_Overview.html`](vlsi/ChipNexus/SoC_DocFlow_Overview.html) |
| **Platform Docs** | DOCX/PDF/HTML | [`vlsi/ChipNexus/docs/`](vlsi/ChipNexus/docs/) |
| **Non-RTL DB Workflow** | HTML | [`vlsi/ChipNexus/docs/nonrtl_db_update_workflow.html`](vlsi/ChipNexus/docs/nonrtl_db_update_workflow.html) |

---

## 🔮 Roadmap

### Near-Term (Next 6 Months)
- **GitLab CI Integration:** Fully automated nightly RM builds triggered by RTL repository commits
- **Enhanced AI Chapter Generation:** Expand Claude-based extraction to security architecture, safety mechanisms, DFT/DFM
- **Multi-Language Support:** Pipeline extensions for Chinese and Japanese RM generation from the same DITA source

### Medium-Term (6–12 Months)
- **Native IP-XACT Import:** Direct IEEE 1685 IP-XACT import to eliminate the custom .rdb format conversion step
- **Formal Register Verification:** Use formal methods to verify register access policies (read-only bits not being written, W1C behaviour)
- **Collaborative Authoring:** Real-time collaborative DITA editing within the VS Code extension

### Long-Term Vision
- **Fully Autonomous RM Pipeline:** Zero-touch RM generation — the platform autonomously detects RTL changes, regenerates affected documentation, and requests human review only for content additions
- **Industry Standardization:** Propose the parameterized DITA model, `.prm`/`.imap` file formats, and automated generation pipeline as an industry standard through Accellera or OASIS

---

## 🤝 Contributing

Contributions are welcome. Please ensure:

1. **Python code** follows PEP 8 style — run `python3 -m py_compile` on all scripts
2. **TypeScript code** passes `npm run lint` in the vscode-plugin directory
3. **New tools** include usage documentation and an entry in the tools/ README
4. **Pipeline demo** (`run_pipeline_demo.py`) must run successfully before submitting a PR
5. **New spec contributions** follow the directory structure convention: `spec-repo/IP_NAME_SPEC/spec_source/{imap,prm,rdb,maps,topics,images}/`

### Repository Hygiene Notes
- `vlsi/opentitan/` is **gitignored** — it's a separate repository. If you need it tracked, use `git submodule add`
- `node_modules/` is **gitignored** globally — never commit npm dependencies
- `.vsix` files are **gitignored** — install the extension via `npm install && npm run compile` instead
- Build outputs in `out/` directories are **gitignored** — compile locally from source

---

## 📄 License

Apache 2.0

---

## 👤 Author

**Jayant Kaushik** — Principal Technical Writer & Platform Architect, Bridgon

- **Platform Development:** July 2022 – Present
- **Organization:** Bridgon, India
- **Users Served:** 40+ technical authors across 5 product lines and multiple geographies

---

<p align="center">
  <sub>Built with ❤️ for semiconductor documentation teams everywhere.</sub>
</p>