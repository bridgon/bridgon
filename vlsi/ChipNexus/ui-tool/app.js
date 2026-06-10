// ============================================================
// SoC DocFlow — Open-Source Reference Manual Automation Platform
// Multi-Tab UI Tool
// ============================================================

const appState = {
    workingDir: '/home/jkaushik/Code/vscode_extn/CRR',
    rtlFilelist: '',
    topModule: '',
    memmapXlsx: '',
    chipPrefix: '',
    claudeApiKey: '',
    pipelineRunning: false,
    logs: [],
    params: {},
    memoryMap: [],
    generatedFiles: [],
};

// ── Tab Navigation ────────────────────────────────────────
function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelector(`.tab-btn[data-tab="${tabId}"]`).classList.add('active');
    document.getElementById(tabId).classList.add('active');
}

// ── Logging ───────────────────────────────────────────────
function log(level, message) {
    const time = new Date().toLocaleTimeString();
    appState.logs.push({ time, level, message });
    renderLogs();
}

function renderLogs() {
    const container = document.getElementById('console-output');
    if (!container) return;
    container.innerHTML = appState.logs.slice(-50).map(l =>
        `<div class="log-line log-${l.level}"><span class="log-time">[${l.time}]</span> ${l.message}</div>`
    ).join('');
    container.scrollTop = container.scrollHeight;
}

// ── Step 1: Design Analysis ───────────────────────────────
async function runDesignAnalysis() {
    log('info', 'Starting design analysis pipeline...');
    log('info', 'Reading RTL file list...');

    // Mock RTL files for demo
    const rtlFiles = [
        '/libs/can/rtl/can_top.sv',
        '/libs/can/rtl/can_core.sv',
        '/libs/can/rtl/can_mb.sv',
        '/libs/dma/rtl/dma_top.sv',
        '/libs/dma/rtl/dma_channel.sv',
        '/libs/uart/rtl/uart_top.sv',
        '/libs/gpio/rtl/gpio_top.sv',
        '/soc/soc_top.sv',
    ];
    log('info', `Loaded ${rtlFiles.length} RTL source files`);

    // Simulate Verific elaboration
    log('info', 'Analyzing RTL files via Verific...');
    for (const f of rtlFiles) {
        log('info', `  Analyzing: ${f}`);
        await sleep(50);
    }

    log('info', 'Elaborating top module: soc_top');
    await sleep(200);

    // Mock parameter extraction results
    appState.params = {
        'FlexCAN_core_0': {
            'CAN_NUM_MB': { default: 64, class: 'integer', source: 'RTL' },
            'CAN_CLK_FREQ': { default: 80000000, class: 'integer', source: 'RTL' },
            'CAN_FD_ENABLE': { default: true, class: 'boolean', source: 'RTL' },
            'CAN_RXFIFO_DEPTH': { default: 32, class: 'integer', source: 'RTL' },
            'CAN_TXMB_COUNT': { default: 8, class: 'integer', source: 'RTL' },
        },
        'FlexCAN_core_1': {
            'CAN_NUM_MB': { default: 32, class: 'integer', source: 'RTL' },
            'CAN_CLK_FREQ': { default: 80000000, class: 'integer', source: 'RTL' },
            'CAN_FD_ENABLE': { default: false, class: 'boolean', source: 'RTL' },
            'CAN_RXFIFO_DEPTH': { default: 16, class: 'integer', source: 'RTL' },
        },
        'DMA_engine_0': {
            'DMA_NUM_CHANNELS': { default: 32, class: 'integer', source: 'RTL' },
            'DMA_DATA_WIDTH': { default: 64, class: 'integer', source: 'RTL' },
            'DMA_SCATTER_GATHER': { default: true, class: 'boolean', source: 'RTL' },
        },
        'UART_inst_0': {
            'UART_BAUD_RATE': { default: 115200, class: 'integer', source: 'RTL' },
            'UART_DATA_BITS': { default: 8, class: 'integer', source: 'RTL' },
            'UART_FIFO_DEPTH': { default: 64, class: 'integer', source: 'RTL' },
        },
        'GPIO_block_0': {
            'GPIO_NUM_PINS': { default: 32, class: 'integer', source: 'RTL' },
            'GPIO_INTERRUPT_EN': { default: true, class: 'boolean', source: 'RTL' },
        },
    };

    log('success', 'Design analysis complete! Extracted parameters from 5 IP instances');
    renderParameterTree();
    updateStepIndicator(1);
}

function renderParameterTree() {
    const container = document.getElementById('param-tree');
    if (!container) return;
    let html = '<div class="param-tree">';
    for (const [instance, params] of Object.entries(appState.params)) {
        html += `<div class="param-group">
            <div class="param-group-header">📦 ${instance}</div>`;
        for (const [pname, pinfo] of Object.entries(params)) {
            html += `<div class="param-item">
                <span class="param-name">${pname}</span>
                <span class="param-value">= ${pinfo.default}</span>
                <span class="param-badge badge-rtl">${pinfo.source}</span>
                <span class="param-type">${pinfo.class}</span>
            </div>`;
        }
        html += '</div>';
    }
    html += '</div>';
    container.innerHTML = html;
}

// ── Step 2: Memory Map → IMAP Generation ─────────────────
async function generateImap() {
    log('info', 'Loading memory map spreadsheet...');

    appState.memoryMap = [
        { ip_name: 'FlexCAN', inst_name: 'FlexCAN_core_0', start_addr: '0x40024000', end_addr: '0x40027FFF',
          slot_size: '16KB', addr_space: 'PERIPHERAL',
          rdb_path: 'IP_FlexCAN_SPEC/spec_source/rdb/FlexCAN_core_regs.rdb',
          spec_ref: 'IP_FlexCAN_SPEC' },
        { ip_name: 'FlexCAN', inst_name: 'FlexCAN_core_1', start_addr: '0x40028000', end_addr: '0x4002BFFF',
          slot_size: '16KB', addr_space: 'PERIPHERAL',
          rdb_path: 'IP_FlexCAN_SPEC/spec_source/rdb/FlexCAN_core_regs.rdb',
          spec_ref: 'IP_FlexCAN_SPEC' },
        { ip_name: 'DMA', inst_name: 'DMA_engine_0', start_addr: '0x40010000', end_addr: '0x40010FFF',
          slot_size: '4KB', addr_space: 'PERIPHERAL',
          rdb_path: 'IP_DMA_SPEC/spec_source/rdb/DMA_core_regs.rdb',
          spec_ref: 'IP_DMA_SPEC' },
        { ip_name: 'UART', inst_name: 'UART_inst_0', start_addr: '0x40030000', end_addr: '0x40030FFF',
          slot_size: '4KB', addr_space: 'PERIPHERAL',
          rdb_path: 'IP_UART_SPEC/spec_source/rdb/UART_core_regs.rdb',
          spec_ref: 'IP_UART_SPEC' },
        { ip_name: 'GPIO', inst_name: 'GPIO_block_0', start_addr: '0x40040000', end_addr: '0x40040FFF',
          slot_size: '4KB', addr_space: 'PERIPHERAL',
          rdb_path: 'IP_GPIO_SPEC/spec_source/rdb/GPIO_core_regs.rdb',
          spec_ref: 'IP_GPIO_SPEC' },
    ];

    log('info', `Loaded ${appState.memoryMap.length} IP instances from memory map`);
    log('info', 'Generating SoC-level .imap file...');

    // Build IMAP XML
    let imapHeader = `<?xml version="1.0" encoding="UTF-8"?>
<!-- Auto-generated SoC Instance Map -->
<instance spec_id="SOC_TOP" chip_prefix="DEMO">
`;
    for (const inst of appState.memoryMap) {
        imapHeader += `  <reg instance_name="${inst.inst_name}" ip_spec="${inst.spec_ref}">
    <regs_link href="../../../${inst.rdb_path}"/>
    <base_address>${inst.start_addr}</base_address>
    <slot_size>${inst.slot_size}</slot_size>
    <address_space>${inst.addr_space}</address_space>
`;
        const params = appState.params[inst.inst_name] || {};
        for (const [pname, pinfo] of Object.entries(params)) {
            imapHeader += `    <param_override param_id="${pname}">${pinfo.default}</param_override>\n`;
        }
        imapHeader += '  </reg>\n';
    }
    imapHeader += '</instance>';
    appState.generatedImap = imapHeader;

    log('success', `Generated .imap with ${appState.memoryMap.length} register instances`);
    log('info', 'RTL parameters populated from design analysis');
    updateStepIndicator(2);
}

// ── Step 3: Non-RTL Parameter Enrichment ──────────────────
async function enrichNonRtlParams() {
    log('info', 'Loading Non-RTL Parameter Database...');
    log('info', 'Enriching instances with documentation-specific parameters...');

    const nonRtlParams = {
        'FlexCAN_core_0': { DOC_REVISION: 'Rev. 2.1', SECURITY_CLASS: 'CONFIDENTIAL', PUBLISH_MODE: 'FULL' },
        'FlexCAN_core_1': { DOC_REVISION: 'Rev. 2.1', SECURITY_CLASS: 'CONFIDENTIAL', PUBLISH_MODE: 'FULL' },
        'DMA_engine_0': { PUBLISH_MODE: 'FULL', DOC_REVISION: 'Rev. 1.7' },
        'UART_inst_0': { PUBLISH_MODE: 'FULL', DOC_REVISION: 'Rev. 3.0' },
        'GPIO_block_0': { PUBLISH_MODE: 'FULL', DOC_REVISION: 'Rev. 2.4' },
    };

    let enrichedCount = 0;
    let enrichedImap = appState.generatedImap;
    for (const [instName, nrtlParams] of Object.entries(nonRtlParams)) {
        for (const [pname, pvalue] of Object.entries(nrtlParams)) {
            enrichedImap = enrichedImap.replace(
                `  <reg instance_name="${instName}"`,
                `  <reg instance_name="${instName}"\n    <!-- Non-RTL -->`
            );
            // Add non-RTL params after address_space
            enrichedImap = enrichedImap.replace(
                new RegExp(`(${instName}.*?</address_space>)`, 's'),
                `$1\n    <param_override param_id="${pname}">${pvalue}</param_override>`
            );
            enrichedCount++;
        }
    }

    appState.enrichedImap = enrichedImap;
    log('success', `Enriched ${enrichedCount} non-RTL parameters`);
    log('info', 'Merged RTL + non-RTL parameters into unified imap');
    updateStepIndicator(3);
}

// ── Step 4: Register Diagram Rendering ────────────────────
async function renderRegisterDiagrams() {
    log('info', 'Loading register database files (.rdb)...');
    log('info', 'Generating SVG bit-field diagrams...');

    const registers = [
        {
            name: 'MCR', display_name: 'Module Configuration Register',
            offset: '0x00', size: 32, access: 'RW', reset_value: '0x5000000F',
            ip: 'FlexCAN',
            bitfields: [
                { msb: 31, lsb: 31, name: 'MDIS', access: 'RW', desc: 'Module Disable' },
                { msb: 30, lsb: 30, name: 'FRZ', access: 'RW', desc: 'Freeze Enable' },
                { msb: 25, lsb: 24, name: 'CLK_SRC', access: 'RW', desc: 'Clock Source Select' },
                { msb: 17, lsb: 17, name: 'SRX_DIS', access: 'RW', desc: 'Self-Reception Disable' },
                { msb: 7, lsb: 0, name: 'MAXMB', access: 'RW', desc: 'Maximum Mailboxes' },
            ]
        },
        {
            name: 'CTRL1', display_name: 'Control 1 Register',
            offset: '0x04', size: 32, access: 'RW', reset_value: '0x00000000',
            ip: 'FlexCAN',
            bitfields: [
                { msb: 31, lsb: 24, name: 'PRESDIV', access: 'RW', desc: 'Prescaler Division (1-256)' },
                { msb: 23, lsb: 22, name: 'RJW', access: 'RW', desc: 'Resync Jump Width' },
                { msb: 21, lsb: 19, name: 'PSEG1', access: 'RW', desc: 'Phase Segment 1' },
                { msb: 18, lsb: 16, name: 'PSEG2', access: 'RW', desc: 'Phase Segment 2' },
                { msb: 15, lsb: 15, name: 'BOFF_MSK', access: 'RW', desc: 'Bus-Off Int Mask' },
            ]
        },
        {
            name: 'DMA_CTRL', display_name: 'DMA Control Register',
            offset: '0x00', size: 32, access: 'RW', reset_value: '0x00000000',
            ip: 'DMA',
            bitfields: [
                { msb: 31, lsb: 31, name: 'DMA_EN', access: 'RW', desc: 'DMA Enable' },
                { msb: 30, lsb: 30, name: 'INT_EN', access: 'RW', desc: 'Interrupt Enable' },
                { msb: 23, lsb: 16, name: 'CH_SEL', access: 'RW', desc: 'Channel Select' },
                { msb: 7, lsb: 0, name: 'PRIORITY', access: 'RW', desc: 'Channel Priority' },
            ]
        },
    ];

    const container = document.getElementById('register-diagrams');
    if (!container) return;

    let html = '';
    for (const reg of registers) {
        html += `<div class="register-card">
            <h3>${reg.ip}: ${reg.display_name} (${reg.name})</h3>
            <div class="reg-meta">
                <span>Offset: ${reg.offset}</span>
                <span>Size: ${reg.size} bits</span>
                <span>Access: ${reg.access}</span>
                <span>Reset: ${reg.reset_value}</span>
            </div>
            <div class="reg-diagram">
                <svg width="750" height="100" viewBox="0 0 750 100">
                    <rect width="750" height="100" fill="#1e1e2e" rx="4"/>
                    ${generateSvgBitfields(reg, 750)}
                </svg>
            </div>
            <table class="reg-table">
                <thead><tr><th>Field</th><th>Bits</th><th>Access</th><th>Description</th></tr></thead>
                <tbody>
                    ${reg.bitfields.map(bf => `
                    <tr>
                        <td><strong>${bf.name}</strong></td>
                        <td>${bf.msb}:${bf.lsb}</td>
                        <td><span class="access-badge access-${bf.access.toLowerCase()}">${bf.access}</span></td>
                        <td>${bf.desc}</td>
                    </tr>`).join('')}
                </tbody>
            </table>
        </div>`;
    }
    container.innerHTML = html;

    log('success', `Rendered ${registers.length} register diagrams with bit-field tables`);
    log('info', 'Generated SVG diagrams with color-coded access types');
    updateStepIndicator(4);
}

function generateSvgBitfields(register, totalWidth) {
    const bits = register.size;
    const cellWidth = (totalWidth - 40) / bits;
    const colorMap = { 'RW': '#7c3aed', 'RO': '#059669', 'W1C': '#d97706', 'WO': '#dc2626' };

    let parts = '';
    // Bit labels
    for (let i = 0; i < bits; i++) {
        const x = 20 + i * cellWidth;
        parts += `<text x="${x + cellWidth/2}" y="22" text-anchor="middle" font-size="8" fill="#94a3b8">${bits-1-i}</text>`;
    }
    // Bit-fields
    for (const bf of register.bitfields) {
        const xStart = 20 + (bits - 1 - bf.msb) * cellWidth;
        const bfWidth = (bf.msb - bf.lsb + 1) * cellWidth;
        const color = colorMap[bf.access] || '#64748b';
        parts += `<rect x="${xStart}" y="28" width="${bfWidth}" height="42" fill="${color}" rx="3" opacity="0.9"/>`;
        parts += `<text x="${xStart + bfWidth/2}" y="48" text-anchor="middle" font-size="9" fill="#fff" font-weight="bold">${bf.name}</text>`;
        parts += `<text x="${xStart + bfWidth/2}" y="62" text-anchor="middle" font-size="7" fill="#e2e8f0">${bf.access}</text>`;
    }
    // Legend
    parts += `<text x="20" y="88" font-size="8" fill="#94a3b8">■ RW (Purple) ■ RO (Green) ■ W1C (Amber) ■ WO (Red)</text>`;
    return parts;
}

// ── Step 5: DITA Map Generation ──────────────────────────
async function generateDitaMap() {
    log('info', 'Auto-generating DITA map structure...');

    const ditamap = `<?xml version="1.0" encoding="UTF-8"?>
<map xmlns:ditaarch="http://dita.oasis-open.org/architecture/2005/"
     ditaarch:DITAArchVersion="2.0" xml:lang="en">

  <title>SoC Reference Manual</title>

  <topicref href="../topics/SOC_Overview.dita" navtitle="SoC Overview" type="concept">
    <topicref href="../topics/SOC_Block_Diagram.dita" navtitle="Block Diagram"/>
    <topicref href="../topics/SOC_Memory_Map.dita" navtitle="System Memory Map"/>
  </topicref>

  <topicref href="ipref:IP_FlexCAN_SPEC" navtitle="FlexCAN Controller" type="concept"/>
  <topicref href="ipref:IP_DMA_SPEC" navtitle="DMA Controller" type="concept"/>
  <topicref href="ipref:IP_UART_SPEC" navtitle="UART Interface" type="concept"/>
  <topicref href="ipref:IP_GPIO_SPEC" navtitle="GPIO Controller" type="concept"/>

  <topicref href="ssref:SS_AHB_BUS" navtitle="AHB Bus SubSystem" type="concept"/>

  <topicref href="../topics/SOC_Clocking.dita" navtitle="Clocking Architecture" type="concept"/>
  <topicref href="../topics/SOC_Reset.dita" navtitle="Reset Architecture" type="concept"/>

</map>`;

    appState.generatedDitamap = ditamap;
    log('success', 'Generated DITA map with 4 IP references and 1 SubSystem reference');
    log('info', 'SoC-specific chapters identified for AI-assisted generation');
    updateStepIndicator(5);
}

// ── Step 6: Resolved DITA Output ──────────────────────────
async function resolveDitaOutput() {
    log('info', 'Running DITA-OT with custom parameter resolution plugin...');
    log('info', 'Resolving pm:cond_* attributes against .imap values...');
    await sleep(300);
    log('info', 'Transforming .rdb register files to DITA reference topics...');
    await sleep(200);
    log('info', 'Generating memory map tables for multi-instance IP blocks...');
    await sleep(300);

    log('success', 'DITA resolution complete!');
    log('success', 'Output formats generated: PDF, WebHelp, RAG Knowledge Base');

    // Display generated file summary
    appState.generatedFiles = [
        'SOC_TOP_resolved.ditamap',
        'output/pdf/SOC_Ref_Manual.pdf',
        'output/webhelp/index.html',
        'output/knowledge_base/vectors.json',
        'reg_MCR.dita',
        'reg_CTRL1.dita',
        'reg_DMA_CTRL.dita',
    ];

    const fileList = document.getElementById('generated-files');
    if (fileList) {
        fileList.innerHTML = appState.generatedFiles.map(f =>
            `<div class="file-item">📄 ${f}</div>`
        ).join('');
    }

    updateStepIndicator(6);
}

// ── Step 7: Launch Documentation Explorer ─────────────────
async function launchExplorer() {
    log('info', 'Starting Documentation Explorer server...');
    log('info', '  → Loading resolved DITA content');
    log('info', '  → Building RAG knowledge base');
    log('info', '  → Initializing AI chatbot');
    log('info', '  → http://localhost:5000');
    log('success', 'Documentation Explorer running at http://localhost:5000');
    log('success', 'Chatbot ready — ask natural language questions about the documentation');
    updateStepIndicator(7);
}

// ── Pipeline Runner ───────────────────────────────────────
async function runFullPipeline() {
    if (appState.pipelineRunning) return;
    appState.pipelineRunning = true;
    document.getElementById('run-pipeline').disabled = true;

    log('info', '══════ Pipeline Started ══════');
    log('info', 'Step 1/7: Running design analysis (Verific)...');
    await runDesignAnalysis();

    log('info', 'Step 2/7: Generating SoC Instance Map from memory map...');
    await generateImap();

    log('info', 'Step 3/7: Enriching with non-RTL documentation parameters...');
    await enrichNonRtlParams();

    log('info', 'Step 4/7: Rendering register diagrams and tables...');
    await renderRegisterDiagrams();

    log('info', 'Step 5/7: Auto-generating DITA map structure...');
    await generateDitaMap();

    log('info', 'Step 6/7: Resolving DITA and generating output...');
    await resolveDitaOutput();

    log('info', 'Step 7/7: Launching Documentation Explorer...');
    await launchExplorer();

    log('info', '══════ Pipeline Complete ══════');
    log('success', `Total time: ~4 minutes. Manual equivalent: 6-8 weeks.`);

    appState.pipelineRunning = false;
    document.getElementById('run-pipeline').disabled = false;
}

function updateStepIndicator(step) {
    for (let i = 1; i <= 7; i++) {
        const el = document.getElementById(`step-${i}`);
        if (el) {
            el.classList.remove('completed', 'running');
            if (i < step) el.classList.add('completed');
            else if (i === step) el.classList.add('running');
        }
    }
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ── Init ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    // Tab navigation
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    // Pipeline run button
    const runBtn = document.getElementById('run-pipeline');
    if (runBtn) runBtn.addEventListener('click', runFullPipeline);

    // Individual step buttons
    document.querySelectorAll('.step-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const step = btn.dataset.step;
            const actions = {
                '1': runDesignAnalysis,
                '2': generateImap,
                '3': enrichNonRtlParams,
                '4': renderRegisterDiagrams,
                '5': generateDitaMap,
                '6': resolveDitaOutput,
                '7': launchExplorer,
            };
            if (actions[step]) await actions[step]();
        });
    });

    log('info', 'Reference Manual Automation Platform ready.');
    log('info', 'Click "Run Full Pipeline" or execute individual steps.');
});