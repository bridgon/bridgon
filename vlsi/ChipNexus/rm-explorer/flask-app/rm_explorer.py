#!/usr/bin/env python3
"""
rm_explorer.py — Reference Manual Explorer Flask Application

Serves an interactive webhelp-style interface for resolved DITA content.
Provides a REST API for TOC navigation, full-text search, topic rendering,
memory map visualization, and an AI chatbot powered by RAG + Claude API.
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
import json
import os
import sys
from pathlib import Path

# Add parent directory for RAG module import
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('RM_EXPLORER_SECRET', 'dev-secret-key')

# ─────────────────────────────────────────────────────────
# Mock Knowledge Base (for demo/development without full RAG setup)
# ─────────────────────────────────────────────────────────
class MockKnowledgeBase:
    """Lightweight mock KB for development and demonstration purposes."""

    def __init__(self):
        self.toc = {
            'title': 'MCU_X9Z SoC Reference Manual',
            'children': [
                {
                    'id': 'overview', 'title': 'SoC Overview', 'type': 'chapter',
                    'children': [
                        {'id': 'block_diagram', 'title': 'Top-Level Block Diagram', 'type': 'topic'},
                        {'id': 'feature_summary', 'title': 'Feature Summary', 'type': 'topic'},
                    ]
                },
                {
                    'id': 'flexcan_chapter', 'title': 'FlexCAN Controller', 'type': 'chapter',
                    'children': [
                        {'id': 'flexcan_overview', 'title': 'Overview', 'type': 'topic'},
                        {'id': 'flexcan_features', 'title': 'Features', 'type': 'topic'},
                        {
                            'id': 'flexcan_registers', 'title': 'Register Descriptions', 'type': 'topic',
                            'children': [
                                {'id': 'reg_MCR', 'title': 'MCR — Module Configuration Register', 'type': 'register'},
                                {'id': 'reg_CTRL1', 'title': 'CTRL1 — Control 1 Register', 'type': 'register'},
                            ]
                        },
                    ]
                },
                {
                    'id': 'dma_chapter', 'title': 'DMA Controller', 'type': 'chapter',
                    'children': [
                        {'id': 'dma_overview', 'title': 'Overview', 'type': 'topic'},
                    ]
                },
                {
                    'id': 'soc_architecture', 'title': 'SoC Architecture', 'type': 'chapter',
                    'children': [
                        {'id': 'clocking', 'title': 'Clocking Architecture', 'type': 'topic'},
                        {'id': 'reset', 'title': 'Reset Architecture', 'type': 'topic'},
                        {'id': 'interrupt', 'title': 'Interrupt Mapping', 'type': 'topic'},
                        {'id': 'power', 'title': 'Power Management', 'type': 'topic'},
                    ]
                },
            ]
        }

        self.topics = {
            'reg_MCR': {
                'id': 'reg_MCR',
                'title': 'Module Configuration Register (MCR)',
                'type': 'reference',
                'register': {
                    'name': 'MCR',
                    'offset': '0x00',
                    'size': 32,
                    'access': 'RW',
                    'reset_value': '0x5000000F',
                    'description': 'Contains global module control and configuration bits for the FlexCAN module.',
                    'bitfields': [
                        {'msb': 31, 'lsb': 31, 'name': 'MDIS', 'access': 'RW',
                         'description': 'Module Disable — 0: Module enabled, 1: Module disabled (clock gated)'},
                        {'msb': 30, 'lsb': 30, 'name': 'FRZ', 'access': 'RW',
                         'description': 'Freeze Enable — Enables entry to Freeze mode upon FRZ_ACK'},
                        {'msb': 25, 'lsb': 24, 'name': 'CLK_SRC', 'access': 'RW',
                         'description': 'Clock Source Selection — 00: Oscillator, 01: PLL, 10: External'},
                        {'msb': 7, 'lsb': 0, 'name': 'MAXMB', 'access': 'RW',
                         'description': 'Maximum Number of Mailboxes — Defines the upper message buffer index (0..127)'},
                    ]
                }
            },
            'reg_CTRL1': {
                'id': 'reg_CTRL1',
                'title': 'Control 1 Register (CTRL1)',
                'type': 'reference',
                'register': {
                    'name': 'CTRL1',
                    'offset': '0x04',
                    'size': 32,
                    'access': 'RW',
                    'reset_value': '0x00000000',
                    'description': 'Primary control register for operation mode selection and bit-timing configuration.',
                    'bitfields': [
                        {'msb': 31, 'lsb': 24, 'name': 'PRESDIV', 'access': 'RW',
                         'description': 'Prescaler Division Factor — Divides the CAN clock (1–256)'},
                        {'msb': 23, 'lsb': 22, 'name': 'RJW', 'access': 'RW',
                         'description': 'Resynchronization Jump Width (0–3)'},
                        {'msb': 21, 'lsb': 19, 'name': 'PSEG1', 'access': 'RW',
                         'description': 'Phase Segment 1 (2–8)'},
                        {'msb': 18, 'lsb': 16, 'name': 'PSEG2', 'access': 'RW',
                         'description': 'Phase Segment 2 (2–8)'},
                    ]
                }
            },
        }

        self.memory_map = {
            'instances': [
                {'name': 'FlexCAN_core_0', 'start': '0x40024000', 'end': '0x40027FFF', 'size': '16KB', 'ip': 'FlexCAN'},
                {'name': 'FlexCAN_core_1', 'start': '0x40028000', 'end': '0x4002BFFF', 'size': '16KB', 'ip': 'FlexCAN'},
                {'name': 'DMA_engine_0', 'start': '0x40010000', 'end': '0x40010FFF', 'size': '4KB', 'ip': 'DMA'},
                {'name': 'UART_inst_0', 'start': '0x40030000', 'end': '0x40030FFF', 'size': '4KB', 'ip': 'UART'},
                {'name': 'GPIO_block_0', 'start': '0x40040000', 'end': '0x40040FFF', 'size': '4KB', 'ip': 'GPIO'},
            ]
        }

    def get_toc(self):
        return self.toc

    def get_topic(self, topic_id):
        return self.topics.get(topic_id, {'id': topic_id, 'title': topic_id, 'type': 'unknown'})

    def search(self, query):
        results = []
        qlower = query.lower()
        for tid, topic in self.topics.items():
            if qlower in topic['title'].lower():
                results.append({'id': tid, 'title': topic['title'], 'type': topic['type']})
        return results

    def get_memory_map(self):
        return self.memory_map


# Initialize KB
kb = MockKnowledgeBase()


# ─────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────

@app.route('/')
def index():
    """Serve the RM Explorer main page."""
    return render_template('explorer.html')


@app.route('/api/toc')
def get_toc():
    """Return the Table of Contents."""
    return jsonify(kb.get_toc())


@app.route('/api/topic/<path:topic_id>')
def get_topic(topic_id):
    """Return a specific topic by its ID."""
    topic = kb.get_topic(topic_id)
    return jsonify(topic)


@app.route('/api/search')
def search():
    """Full-text search across documentation."""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    results = kb.search(query)
    return jsonify(results)


@app.route('/api/memorymap')
def memory_map():
    """Return the system memory map."""
    return jsonify(kb.get_memory_map())


@app.route('/api/register/<reg_id>')
def get_register(reg_id):
    """Return detailed register information."""
    topic = kb.get_topic(reg_id)
    if topic.get('register'):
        return jsonify(topic['register'])
    return jsonify({'error': 'Register not found'}), 404


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    AI chatbot endpoint.
    Uses mock responses for demo; production uses Claude API with RAG context.
    """
    data = request.get_json()
    query = data.get('query', '')
    history = data.get('history', [])

    qlower = query.lower()

    if 'reset' in qlower and 'mcr' in qlower:
        answer = (
            "The FlexCAN **Module Configuration Register (MCR)** at offset `0x00` "
            "has a reset value of **0x5000000F**.\n\n"
            "Key bit-fields:\n"
            "- **Bit 31 (MDIS):** Module Disable — resets to 0 (enabled)\n"
            "- **Bit 30 (FRZ):** Freeze Enable — resets to 0\n"
            "- **Bits 7:0 (MAXMB):** Max Mailboxes — resets to 0x0F (15)\n\n"
            "*Source: FlexCAN Module — MCR Register (§4.2.1)*"
        )
    elif 'flexcan' in qlower or 'can' in qlower:
        answer = (
            "The **FlexCAN module** is a CAN bus controller supporting:\n"
            "- Up to **64 message buffers** (mailboxes)\n"
            "- **CAN-FD** (Flexible Data-rate) with payloads up to 64 bytes\n"
            "- **32-deep RX FIFO** for high-throughput receive operations\n"
            "- Configurable acceptance filters for standard and extended IDs\n\n"
            "FlexCAN is instantiated twice in MCU_X9Z:\n"
            "- **FlexCAN_core_0** at `0x40024000` (64 mailboxes, CAN-FD enabled)\n"
            "- **FlexCAN_core_1** at `0x40028000` (32 mailboxes, CAN-FD disabled)\n\n"
            "*Source: FlexCAN Chapter — Functional Description*"
        )
    elif 'dma' in qlower:
        answer = (
            "The **DMA Controller** in MCU_X9Z provides **32 independent channels** "
            "with **64-bit data width** and **scatter-gather** support.\n\n"
            "- Base address: `0x40010000`\n"
            "- Channel FIFO depth: 16 entries per channel\n"
            "- Supports memory-to-memory, peripheral-to-memory, and memory-to-peripheral transfers\n\n"
            "*Source: DMA Controller — Overview*"
        )
    elif 'memory map' in qlower or 'address' in qlower:
        answer = (
            "**MCU_X9Z System Memory Map** (Peripheral Region):\n\n"
            "| IP Block         | Base Address  | Size  |\n"
            "|------------------|---------------|-------|\n"
            "| DMA_engine_0     | `0x40010000`  | 4KB   |\n"
            "| FlexCAN_core_0   | `0x40024000`  | 16KB  |\n"
            "| FlexCAN_core_1   | `0x40028000`  | 16KB  |\n"
            "| UART_inst_0      | `0x40030000`  | 4KB   |\n"
            "| GPIO_block_0     | `0x40040000`  | 4KB   |\n\n"
            "*Source: SoC Memory Map — System Overview*"
        )
    else:
        answer = (
            f"I searched the documentation for information about '{query}' but "
            f"couldn't find a specific match. This topic may be covered in the "
            f"following chapters:\n"
            f"- SoC Overview\n"
            f"- FlexCAN Controller\n"
            f"- DMA Controller\n"
            f"- SoC Architecture (Clocking, Reset, Interrupts, Power)\n\n"
            f"Try rephrasing your question or browse the Table of Contents."
        )

    return jsonify({
        'answer': answer,
        'sources': []
    })


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files (CSS, JS, images)."""
    return send_from_directory('../static', filename)


# ─────────────────────────────────────────────────────────
# Launch
# ─────────────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('RM_EXPLORER_PORT', 5000))
    debug = os.environ.get('RM_EXPLORER_DEBUG', 'true').lower() == 'true'

    print(f"""
╔══════════════════════════════════════════════════════════╗
║  CRR Reference Manual Explorer                          ║
║  Running on: http://localhost:{port}                      ║
║  API Docs:   http://localhost:{port}/api/toc              ║
╚══════════════════════════════════════════════════════════╝
    """)

    app.run(host='0.0.0.0', port=port, debug=debug)