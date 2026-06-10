# White Paper: Revolutionizing SoC Reference Manual Generation Through AI-Driven Automation

**Authors:** Jayant Kaushik, Principal Technical Writer & Platform Architect
**Organization:** Bridgon
**Date:** June 2026
**Classification:** Bridgon Confidential

---

## Abstract

The semiconductor industry faces a growing documentation crisis: as System-on-Chip (SoC) complexity doubles with each generation, the effort required to produce accurate, comprehensive Reference Manuals has become a critical bottleneck in the tape-out process. Traditional manual documentation workflows—relying on engineers to manually extract RTL parameters, cross-reference memory maps, and assemble multi-thousand-page documents—can consume 6-8 weeks per SoC and introduce errors that compromise product quality.

This white paper presents an AI-powered automated Reference Manual generation platform developed at Bridgon that reduces SoC documentation time from 6-8 weeks to under 4 hours while eliminating parameter extraction errors entirely. The platform integrates six interconnected subsystems: (1) a VS Code extension providing a unified authoring interface, (2) Verific-based design analysis for accurate RTL parameter extraction, (3) memory map-driven automatic instance map generation, (4) a JSON-based Non-RTL Parameter Database for documentation-specific configuration management, (5) AI-assisted DITA source auto-generation using the Claude API, and (6) a custom DITA-OT pipeline with register diagram generation and parameter resolution.

Key results include a 270x reduction in documentation generation time, zero parameter transcription errors, 80% fewer build failures, and 40% reduction in internal support queries through an AI-powered Reference Manual Explorer with RAG-based chatbot capabilities.

---

## 1. Introduction

### 1.1 The Documentation Challenge in Modern SoC Design

Modern System-on-Chip designs integrate dozens of IP blocks—processors, memory controllers, communication peripherals, security modules, and power management units—each with hundreds of configurable parameters and thousands of registers. The Reference Manual (RM) documenting these components is the primary interface between the silicon design team and the software developers, system integrators, and field application engineers who must program and deploy the chip.

As SoC complexity has grown exponentially (driven by advanced process nodes, heterogeneous compute architectures, and automotive safety requirements), the documentation burden has grown proportionally. A typical automotive-grade SoC Reference Manual spans 8,000-15,000 pages, referencing over 50 IP blocks, each with multiple configuration instances and parameter variations.

### 1.2 The Legacy Documentation Flow

The traditional documentation workflow at Bridgon (and across much of the semiconductor industry) followed a predominantly manual process:

1. **Parameter Extraction:** Engineers manually extracted RTL (Register Transfer Level) parameter values from LEC (Logic Equivalence Checking) tool logs—a process requiring 4-6 hours per IP block with approximately 15% error rates due to incorrect hierarchy level selection.

2. **Instance Map Authoring:** Documentation authors manually created XML Instance Map files by cross-referencing multiple spreadsheets, typing in base addresses, parameter overrides, and register file references.

3. **Non-RTL Parameter Management:** Publishing-specific parameters (document revisions, security classifications, publishing modes) were maintained in personal spreadsheets with no centralized database or programmatic linkage to the build process.

4. **DITA Map Assembly:** Creating the hierarchical DITA map for an SoC—which aggregates IP-level documentation, SubSystem-level documentation, and SoC-specific chapters—required 2-3 days of manual assembly with a high risk of missing references.

5. **Chapter Authoring:** SoC-specific chapters on clocking, reset architecture, interrupt mapping, and power domains were written from scratch for each chip family by manually extracting information from architecture specification PDFs.

6. **Build & Resolution:** Running the DITA-OT pipeline with custom parameter resolution required 3-5 build attempts per release due to parameter conflicts and conditional processing errors.

**Cumulative Impact:** 6-8 weeks of manual effort per SoC, with documentation on the critical path for tape-out.

### 1.3 The Business Case for Automation

The business drivers for automating this workflow were compelling:

- **Time-to-Market:** Documentation delays directly delayed product releases
- **Quality:** Parameter errors in documentation led to customer silicon bugs (software accessing wrong register addresses)
- **Resource Scalability:** The documentation team could not scale linearly with the growing number of SoC programs
- **Consistency:** Different authors produced inconsistent outputs for the same IP across different SoCs
- **Engineer Productivity:** Highly skilled RTL engineers spent non-trivial time supporting documentation tasks rather than design work

---

## 2. System Architecture

### 2.1 Design Principles

The platform was architected around four core design principles:

1. **Single Source of Truth:** Every piece of information—RTL parameters, register definitions, memory map entries, non-RTL configuration—originates from a single authoritative source and flows automatically through the pipeline without manual transcription.

2. **Full Automation with Human Oversight:** The pipeline handles 95% of the documentation assembly automatically. Human authors intervene only for content creation (writing functional descriptions, application notes) and final review.

3. **Defense in Depth:** Multiple validation layers—RTL-vs-documentation parameter checking, address space collision detection, conditional processing verification—catch errors before publication.

4. **Tool-Agnostic Interfaces:** While the current implementation uses Verific, DITA-OT, and Claude, all interfaces are abstracted to allow technology substitution without architectural changes.

### 2.2 High-Level Architecture

The system architecture comprises six integrated subsystems operating in a sequential pipeline, orchestrated through a VS Code extension that provides a unified graphical interface:

```
┌────────────────────────────────────────────────────────────────┐
│                 VS CODE EXTENSION (Unified UI)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐ │
│  │ Design   │ │ Memory   │ │ Non-RTL  │ │ DITA     │ │ RM   │ │
│  │ Analysis │ │Map→IMAP  │ │ DB       │ │ Generator│ │Expl. │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └──┬───┘ │
└───────┼────────────┼────────────┼────────────┼──────────┼─────┘
        │            │            │            │          │
   ┌────▼────┐  ┌────▼────┐  ┌───▼────┐  ┌───▼────┐ ┌──▼──────┐
   │ Verific │  │ SoC Mem │  │ Non-RTL│  │DITA-OT │ │ Flask   │
   │ Design  │  │ Map     │  │ DB     │  │+ XSLT  │ │ RM      │
   │ Elab.   │  │ (XLSX)  │  │ (JSON) │  │ Engine │ │ Explorer│
   └────┬────┘  └────┬────┘  └───┬────┘  └───┬────┘ └────┬────┘
        │            │            │            │          │
   ┌────▼────────────▼────────────▼────────────▼──────────▼────┐
   │                    OUTPUT ARTIFACTS                        │
   │  module_params.json → IP_PARAMS_TOP.imap → Resolved DITA  │
   │                              ↓                  ↓         │
   │                     DITA Source (auto-gen)  PDF / WebHelp │
   └───────────────────────────────────────────────────────────┘
```

### 2.3 Data Flow Pipeline

```
Step 1: RTL Filelist ──→ [Verific Elaboration] ──→ module_parameters.json
Step 2: SoC MemMap.xlsx + module_parameters.json ──→ [IMAP Generator] ──→ SOC_top.imap
Step 3: SOC_top.imap ──→ [Non-RTL DB Enricher] ──→ IP_PARAMS_TOP.imap (RTL + non-RTL)
Step 4: IP_PARAMS_TOP.imap ──→ [DITA Source Generator + Claude API] ──→ .ditamap, .pub, .prm, .dita topics
Step 5: DITA Source ──→ [Custom DITA-OT Plugin + XSLT] ──→ Resolved DITA + Register Diagrams
Step 6: Resolved DITA ──→ [RAG Knowledge Base Ingester] ──→ Vector KB ──→ Chatbot Context
Step 7: Resolved DITA ──→ [DITA-OT PDF / WebHelp] ──→ Published Documentation
```

---

## 3. Subsystem Deep Dives

### 3.1 VS Code Extension: Unified Authoring Interface

The VS Code extension (CRR: Chip Reference Manual Generator) serves as the primary user interface for the entire platform. It was designed to accommodate the range of technical proficiency within the documentation team—from traditional technical writers comfortable with XML editors to front-end designers who prefer graphical interfaces.

**Key Features:**

| Feature | Function |
|---------|----------|
| One-Click Design Analysis | Triggers Verific elaboration with pre-configured RTL file lists |
| Parameter Explorer | Hierarchical tree view of all extracted parameters, filterable by IP, type (RTL/non-RTL), and value |
| Build Pipeline WebView | Visual workflow with step-by-step progress indicators and console output |
| DITA Preview | Inline preview of auto-generated DITA source with syntax highlighting |
| RM Explorer Launcher | Single-click launch of the Flask-based documentation explorer |
| Register Validator | Side-by-side comparison of .rdb definitions vs. RTL-extracted values |

The extension implements the VS Code TreeView API for the Parameter Explorer, providing a familiar file-explorer-like interface for navigating the hierarchical parameter space. The Build Pipeline panel uses the WebView API to render a visual pipeline with animated progress indicators and collapsible console output sections.

### 3.2 Design Analysis: Verific-Based Parameter Extraction

The design analysis subsystem represents the most critical accuracy improvement in the platform. The legacy approach—parsing LEC tool logs—suffered from fundamental limitations:

- LEC compares two netlists, not the full design hierarchy
- Parameter values can appear at incorrect hierarchy levels in comparison logs
- No structured output format; required regex-based text parsing
- No support for SystemVerilog parameter types beyond simple integers

The new approach uses Verific (verific.com), a commercial EDA tool providing full SystemVerilog (IEEE 1800-2017) and VHDL (IEEE 1076-2008) parsing with complete design elaboration. Verific resolves:

- Module parameter definitions with their full type system (integer, boolean, string, enumerated, float)
- Hierarchical parameter overrides through defparam, module instantiation, and generate blocks
- Parameter expressions and dependencies
- Macro and preprocessor-resolved values

A Python wrapper script generates Verific TCL automation scripts dynamically based on the RTL file list and top module name. The output is a structured `module_parameters.json` file containing all parameters for every module instance in the elaborated design, keyed by hierarchical instance path.

**Parameter Validation:** A separate validation step cross-references the RTL-extracted parameters against the documented .prm (Parameter Definition) files, flagging discrepancies in default values, type mismatches, or missing parameter definitions. This catches errors where the documentation claims a different default value than what the actual RTL implements.

### 3.3 Memory Map-Driven Instance Generation

This subsystem bridges the gap between the hardware architecture team (who maintain the SoC address map in Excel spreadsheets) and the documentation team (who need structured XML Instance Map files).

The memory map spreadsheet follows a standardized format with columns for IP name, instance name, start address, end address, slot size, address space type, .rdb register file reference, and IP spec identifier. From this spreadsheet, the IMAP Generator:

1. Populates required IP spec directories from the central spec repository
2. Constructs SoC-level .imap files with register instances containing base addresses and RTL parameter values sourced from the design analysis JSON
3. Handles complex memory hierarchies where the same IP is instantiated multiple times with different parameter configurations (e.g., FlexCAN_0 with 64 mailboxes at 0x40024000 vs. FlexCAN_1 with 32 mailboxes at 0x40028000)
4. Auto-generates SubSystem-level .imap files that link to their constituent IP instances

The .imap format supports a rich parameter override mechanism: each register instance can specify parameter values that differ from the IP-level defaults defined in the .prm file. This enables a single IP specification to serve multiple SoC instances with different configurations.

### 3.4 Non-RTL Parameter Database: Configuration Management

A critical insight in designing the platform was recognizing that parameters fall into two distinct categories:

**RTL Parameters:** Exist in the hardware design and can be extracted automatically. Examples: number of DMA channels, FIFO depth, CAN-FD enable.

**Non-RTL Parameters:** Documentation-specific configurations that have no representation in RTL. Examples: document revision string, security classification, publishing mode, chip family prefix.

The Non-RTL Parameter Database is a JSON-based "ditabase" that stores all non-RTL parameters with hierarchical associations:

```
Parameter → IP Instance → SubSystem → SoC → Chip Family
```

The use of JSON (rather than SQL) was an intentional design choice. JSON files are:
- Version-control friendly (diffable and mergeable in Git)
- Zero-infrastructure (no database server required)
- Schema-flexible (naturally accommodates deeply nested hierarchies)
- Directly consumable by Python, JavaScript, and TCL tooling

The `chip_prefix` serves as the primary lookup key, enabling the same instance name (e.g., "FlexCAN_core_0") to have different non-RTL parameter values in different chip families (e.g., MCU_X vs. MCU_Y). The enrichment step merges the RTL .imap (containing only hardware parameters) with the non-RTL database entries to produce a unified `IP_PARAMS_TOP.imap` file.

### 3.5 AI-Assisted DITA Source Generation

The DITA Source Generator creates the complete documentation source structure from the enriched .imap file. This subsystem automates what was previously the most labor-intensive documentation task: assembling the hierarchical document structure.

**Automated Actions:**

1. **DITA Map Generation:** Creates the SoC-level .ditamap with `ipref` links to each IP spec ditamap, `ssref` links to SubSystem specs, and references to SoC-specific chapters. The generator groups IPs by spec reference and orders them according to the memory map layout.

2. **Publishing Instructions Generation:** Creates .pub files defining resolve groups with instance selectors, register merging rules, and output configuration. For multi-instance IPs (e.g., two FlexCAN instances), the .pub specifies how to merge common register information while preserving per-instance address information in the memory map table.

3. **Parameter Definition Consolidation:** Generates the SoC-level .prm file that aggregates all parameter definitions referenced across IP and SubSystem specs.

4. **AI Chapter Generation:** Uses the Claude API (Anthropic) to extract SoC-specific chapter content from architecture specification PDFs. The AI is prompted to:
   - Identify clocking architecture information (sources, PLLs, dividers, domains)
   - Extract reset architecture details (sources, sequencing, isolation)
   - Map interrupt controller configuration (vector table, priority scheme)
   - Document power management (domains, low-power modes, wakeup sources)
   - Structure the extracted content as proper DITA topic types (concept, reference, task)
   - Cross-reference relevant register descriptions from the IP specs

The AI-generated chapters are reviewed by human authors before inclusion—the system automates extraction and structuring but preserves human oversight for accuracy.

### 3.6 Resolved DITA Generation & Register Diagrams

The final documentation output subsystem is a custom DITA-OT plugin that processes parameterized DITA source through a multi-stage pipeline:

**Stage 1: Parameter Resolution**
The plugin evaluates `pm:cond_*` attributes on DITA elements against the instantiated parameter values in the .imap file. Elements whose parameter conditions match the instantiated values are retained; non-matching elements are suppressed. For example, a topicref for CAN-FD operation is included only when `CAN_FD_ENABLE=true` in the instance configuration.

**Stage 2: Register File Transformation**
The .rdb (Register Database) format—an IP-XACT-like XML vocabulary—is transformed into DITA reference topics with:
- SVG bit-field diagrams showing register layout with colour-coded access types (Blue: R/W, Green: RO, Orange: W1C)
- HTML tables with columns for offset, field name, bit range, access type, reset value, and description
- Cross-reference links to related registers and programming model topics

**Stage 3: Memory Map Generation**
For multi-instance scenarios, the plugin generates memory map tables showing each instance's base address, address range, and instance-specific configuration. Common register descriptions from the first instance are preserved; only address information varies per instance.

**Stage 4: Multi-Format Output**
The resolved, parameter-free DITA is rendered into multiple output formats:
- **PDF:** Via DITA-OT's PDF2 plugin with custom XSL-FO stylesheets for Bridgon's corporate template
- **WebHelp:** Responsive HTML5 with collapsible TOC, full-text search, and bookmark persistence
- **RAG Knowledge Base:** Chunked embeddings for the AI chatbot context

---

## 4. Reference Manual Explorer: AI-Powered Documentation Portal

Beyond automating generation, the platform transforms how internal consumers access documentation through the RM Explorer—a Flask-based web application with integrated AI chatbot.

### 4.1 WebHelp Frontend

The RM Explorer renders resolved DITA content as an interactive web application featuring:
- Collapsible sidebar TOC derived from the resolved ditamap
- Register information displayed as interactive SVG diagrams with tooltips
- System-level memory map visualization with colour-coded IP blocks
- Full-text search across all topics
- Responsive design for desktop and tablet access

### 4.2 RAG-Based AI Chatbot

The chatbot subsystem implements Retrieval-Augmented Generation (RAG) for natural language documentation queries:

1. **Knowledge Base Construction:** Resolved DITA content is chunked by topic boundaries and section headings. Each chunk is embedded into a vector space (using hash-based fingerprints in the current implementation; production deploys Claude embeddings for semantic search). Topic metadata (IP name, register offset, chapter heading) is stored alongside embeddings.

2. **Query Processing:** User queries are embedded and matched against the knowledge base using cosine similarity. The top-5 most relevant chunks are retrieved.

3. **Context-Grounded Response Generation:** Retrieved chunks are provided as context to the Claude API, which generates answers grounded in the actual documentation content. The system prompt enforces rules: answer only from provided context, cite specific sections/registers, format responses as technical prose.

4. **Source Attribution:** All chatbot responses include citations linking back to the specific DITA topics and sections used as context, enabling users to verify information directly.

**Example Interaction:**

> **User:** What is the reset value of the FlexCAN MCR register?

> **Chatbot:** The FlexCAN Module Configuration Register (MCR) at offset 0x00 has a reset value of **0x5000000F**. This 32-bit register contains the following key fields:
> - Bit 31 (MDIS): Module Disable — resets to 0 (module enabled)
> - Bit 30 (FRZ): Freeze Enable — resets to 0
> - Bits 7:0 (MAXMB): Maximum Number of Mailboxes — resets to 0x0F (15)
>
> *Source: FlexCAN Module — Module Configuration Register (MCR), §4.2.1*

---

## 5. File Format Innovations

The platform introduces several custom file formats that extend standard DITA/XML practices for semiconductor documentation:

### 5.1 File Extension Map

| Extension | Full Name | Purpose |
|-----------|-----------|---------|
| `.prm` | Parameter Definition | Defines all configurable parameters with defaults, constraints, type information, and source classification (RTL/non-RTL) |
| `.imap` | Instance Map | Instantiates parameter values for a specific documentation instance (IP-level, SS-level, or SoC-level) |
| `.rdb` | Register Database | Defines register and bit-field descriptions in an IP-XACT-compatible XML format |
| `.pub` | Publishing Instructions | Defines register resolution groups, instance selectors, merging rules, and output format configuration |
| `.ditamap` | DITA Map | Standard DITA map extended with ipref, ssref, and pm:cond_* attributes |

### 5.2 Parameter Class System

The `.prm` format defines a comprehensive parameter type system supporting five classes:

| Class | Validation | Example |
|-------|-----------|---------|
| `integer` | Bounded by low_limit and high_limit | `CAN_NUM_MB = 64` (range 16-128) |
| `boolean` | Must be "true" or "false" | `CAN_FD_ENABLE = true` |
| `float` | Any decimal value | Used for analog parameters |
| `string` | Free-form text | `CAN_DOC_REVISION = "Rev. 2.1"` |
| `enumerated` | Must match one of the listed accepted_values | `CAN_SECURITY_CLASS = "CONFIDENTIAL"` |

Each parameter also carries a `source` attribute ("RTL" or "nonrtl") that determines how it flows through the enrichment pipeline.

### 5.3 Parameterized Content Model

The platform introduces `pm:cond_*` attributes in the `http://bridgon.com/schemas/param-mapping` namespace. These attributes enable conditional content inclusion/exclusion based on instantiated parameter values:

```xml
<topicref href="FlexCAN_CANFD_Support.dita"
          pm:cond_CAN_FD_ENABLE="true">
```

This mechanism is more powerful than standard DITAVAL filtering because parameter values come directly from the design elaboration, ensuring consistency between the hardware configuration and the documentation output.

---

## 6. Results & Business Impact

### 6.1 Quantitative Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| End-to-End SoC RM Time | 6-8 weeks | <4 hours | ~270x faster |
| Parameter Extraction Accuracy | ~85% | 100% | Eliminated errors |
| Manual Address Entry Errors | ~12 per SoC | 0 | Zero defects |
| Non-RTL Parameter Inconsistencies | ~8 per release | 0 | Eliminated |
| Build Failures per Release | 3-5 | 0-1 | 80% reduction |
| Internal Support Queries | Baseline | -40% | Self-service via chatbot |
| New Author Onboarding Time | 4 weeks | 1 week | 75% faster |
| IP Spec Reuse Across SoCs | 30% | 95% | Single-source publishing |

### 6.2 Qualitative Impact

**Accelerated Time-to-Market:** Documentation is no longer on the critical path for tape-out. The RM can be generated overnight after RTL freeze, enabling same-day documentation availability for early software development.

**Improved Quality:** The elimination of manual parameter transcription removes an entire class of documentation defects. Register addresses in the published RM are guaranteed to match the actual hardware because they flow directly from the memory map spreadsheet through automated XML generation—not through human typing.

**Single-Source Publishing:** The same .rdb and .prm files serve IP-level, SubSystem-level, and SoC-level documentation with zero duplication. An IP spec author maintains one set of register descriptions; the platform handles all multi-instance variation automatically.

**Engineer Productivity:** RTL design engineers spend zero time supporting documentation parameter extraction—a task that previously consumed 4-6 hours per IP block per SoC program.

**Cross-Geo Standardization:** Teams in India, France, Italy, and the US use identical toolchains, eliminating the format inconsistencies that previously required manual cleanup during document integration.

### 6.3 Adoption Metrics

- **40+ active users** across technical writing, front-end design, and applications engineering teams
- **5 product lines** actively using the platform for SoC documentation
- **100% of new SoC programs** onboarded to the automated flow
- **Zero rollbacks** to the legacy manual process since initial deployment
- **Over 50 SoC Reference Manuals** generated through the platform

---

## 7. Lessons Learned

### 7.1 Technical Lessons

1. **Design Elaboration is Non-Negotiable:** Attempting to extract parameters from synthesis or LEC logs fundamentally cannot achieve 100% accuracy because those tools optimize away hierarchy information. Full design elaboration through a parser like Verific is the only reliable approach.

2. **JSON Beats SQL for Configuration Data:** The decision to implement the Non-RTL Parameter Database as JSON rather than SQL proved correct. Git-based version control, zero operational overhead, and native consumption by all toolchain components (Python, JavaScript, TCL) simplified development and deployment significantly.

3. **AI as Assistant, Not Author:** The Claude API is remarkably effective at extracting structured information from architecture specification PDFs, but human review remains essential for accuracy. The optimal workflow is AI-extract, human-verify, pipeline-include.

4. **File Format Standardization Pays Dividends:** Defining clear, versioned file formats (.prm, .imap, .rdb, .pub) with comprehensive validation enabled independent development of each pipeline stage and simplified debugging when issues occurred.

### 7.2 Organizational Lessons

1. **Meet Authors Where They Are:** The VS Code extension was crucial for adoption. Not all technical writers are comfortable with command-line tools; providing a graphical interface lowered the barrier to entry significantly.

2. **Automation Threatens, Then Empowers:** Initial resistance from authors who feared automation would eliminate their roles was overcome by demonstrating that the platform handles the tedious, error-prone mechanical work, freeing authors to focus on high-value content creation and review.

3. **Cross-Functional Buy-In is Critical:** The platform spans RTL design, verification, architecture, and documentation teams. Early engagement with all stakeholders—particularly the architecture team that maintains the memory map spreadsheet—was essential for establishing the single-source-of-truth principle.

---

## 8. Future Directions

### 8.1 Near-Term (6 Months)

- **Enhanced AI Chapter Generation:** Expand Claude-based extraction to additional chapter types (security architecture, safety mechanisms, DFT/DFM)
- **GitLab CI Integration:** Fully automated nightly RM builds triggered by RTL repository commits
- **Multi-Language Support:** Pipeline extensions for Chinese and Japanese RM generation from the same DITA source

### 8.2 Medium-Term (6-12 Months)

- **Native IP-XACT Import:** Direct IEEE 1685 IP-XACT import to eliminate the custom .rdb format conversion step
- **Formal Register Verification:** Expand RTL-to-documentation validation using formal methods to verify register access policies (read-only bits not being written, write-1-to-clear behaviour, etc.)
- **Collaborative Authoring:** Real-time collaborative DITA editing within the VS Code extension

### 8.3 Long-Term Vision

- **Fully Autonomous RM Pipeline:** Zero-touch RM generation where the platform autonomously detects RTL changes, regenerates affected documentation, and requests human review only for content additions
- **Industry Standardization:** Propose the parameterized DITA model, .prm/.imap file formats, and automated generation pipeline as an industry standard through Accellera or OASIS

---

## 9. Conclusion

The AI-powered automated Reference Manual generation platform has fundamentally transformed how SoC documentation is created at Bridgon. By integrating commercial-grade RTL elaboration, structured authoring frameworks, and generative AI into a unified pipeline, the platform has:

- Reduced documentation generation time from 6-8 weeks to under 4 hours
- Eliminated parameter extraction and transcription errors
- Enabled single-source publishing across IP, SubSystem, and SoC levels
- Empowered documentation consumers with AI-assisted self-service exploration

The platform demonstrates that the documentation function in semiconductor companies need not be a bottleneck or a source of defects. With thoughtful automation architecture, strong single-source-of-truth discipline, and strategic use of AI for content extraction and retrieval, documentation can become a competitive advantage—accelerating time-to-market, improving product quality, and enhancing the developer experience for silicon customers.

---

## References

1. OASIS DITA 2.0 Specification. https://docs.oasis-open.org/dita/dita/v2.0/
2. Verific Design Automation. https://www.verific.com/products/
3. Anthropic Claude API Documentation. https://docs.anthropic.com/
4. IEEE 1685-2014: Standard for IP-XACT. https://standards.ieee.org/standard/1685-2014.html
5. Lewis, P., et al. "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." NeurIPS 2020.
6. DITA Open Toolkit. https://www.dita-ot.org/