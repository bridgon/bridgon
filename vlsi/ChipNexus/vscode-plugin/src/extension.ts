import * as vscode from 'vscode';
import * as path from 'path';
import * as cp from 'child_process';
import * as fs from 'fs';

export function activate(context: vscode.ExtensionContext) {
    const cmd = vscode.commands.registerCommand('docflow.openPanel', () => {
        DocFlowPanel.createOrShow(context.extensionUri);
    });
    context.subscriptions.push(cmd);

    vscode.window.showInformationMessage(
        'SoC DocFlow ready!', 'Open Panel'
    ).then(sel => {
        if (sel === 'Open Panel') {
            vscode.commands.executeCommand('docflow.openPanel');
        }
    });
}

export function deactivate() {}

class DocFlowPanel {
    public static currentPanel: DocFlowPanel | undefined;
    private readonly _panel: vscode.WebviewPanel;
    private readonly _extensionUri: vscode.Uri;
    private _disposables: vscode.Disposable[] = [];
    private _out: vscode.OutputChannel;

    public static createOrShow(extensionUri: vscode.Uri) {
        const col = vscode.window.activeTextEditor?.viewColumn;
        if (DocFlowPanel.currentPanel) {
            DocFlowPanel.currentPanel._panel.reveal(col);
            return;
        }
        const panel = vscode.window.createWebviewPanel(
            'docflowPanel', 'SoC DocFlow',
            col || vscode.ViewColumn.One,
            { enableScripts: true, retainContextWhenHidden: true }
        );
        DocFlowPanel.currentPanel = new DocFlowPanel(panel, extensionUri);
    }

    private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri) {
        this._panel = panel;
        this._extensionUri = extensionUri;
        this._out = vscode.window.createOutputChannel('SoC DocFlow');
        this._panel.webview.html = this._buildHtml();
        this._panel.webview.onDidReceiveMessage(m => this._onMsg(m), null, this._disposables);
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
    }

    private async _onMsg(msg: any) {
        const cfg = vscode.workspace.getConfiguration('docflow');
        const py = cfg.get<string>('pythonPath', 'python3');
        const root = path.join(this._extensionUri.fsPath, '..');

        switch (msg.command) {
            case 'runPipelineDemo':
                await this._exec('Pipeline Demo', py, [path.join(root, 'run_pipeline_demo.py')]);
                break;
            case 'runDesignAnalysis':
                await this._exec('Design Analysis', py, [
                    path.join(root, 'design-analysis', 'verific-scripts', 'run_design_analysis.py'),
                    '--rtl_filelist', msg.rtlFilelist || 'rtl_files.txt',
                    '--top_module', msg.topModule || 'soc_top',
                    '--working_dir', '/tmp/docflow_work',
                    '--output_json', '/tmp/docflow_work/module_parameters.json'
                ]);
                break;
            case 'generateImap':
                await this._exec('IMAP Generation', py, [
                    path.join(root, 'tools', 'inst-generator', 'inst_gen.py'),
                    '--memmap', msg.memmapPath || 'soc_memmap.xlsx',
                    '--rtl_params', '/tmp/docflow_work/module_parameters.json',
                    '--spec_repo', path.join(root, 'spec-repo'),
                    '--chip_prefix', 'DEMO',
                    '--output', '/tmp/docflow_work/SOC_TOP.imap'
                ]);
                break;
            case 'enrichNonRtlParams':
                await this._exec('Non-RTL Enrichment', py, [
                    path.join(root, 'tools', 'param-extractor', 'param_extract.py'),
                    '--rtl_imap', '/tmp/docflow_work/SOC_TOP.imap',
                    '--nonrtl_db', path.join(root, 'nonrtl-params-db', 'nonrtl_param_db.json'),
                    '--chip_prefix', 'DEMO',
                    '--output', '/tmp/docflow_work/IP_PARAMS_TOP.imap'
                ]);
                break;
            case 'resolveDita':
                await this._exec('DITA Resolution', py, [
                    path.join(root, 'tools', 'dita-resolver', 'resolve_dita.py'),
                    '--source', path.join(root, 'spec-repo'),
                    '--imap', '/tmp/docflow_work/IP_PARAMS_TOP.imap',
                    '--output', '/tmp/docflow_work/resolved_dita'
                ]);
                break;
            case 'openWebhelp':
                const wp = path.join(root, 'output', 'webhelp', 'index.html');
                if (fs.existsSync(wp)) {
                    vscode.env.openExternal(vscode.Uri.file(wp));
                } else {
                    vscode.window.showWarningMessage('Run the pipeline first to generate WebHelp output.');
                }
                break;
            case 'openSettings':
                vscode.commands.executeCommand('workbench.action.openSettings', 'docflow');
                break;
        }
    }

    private async _exec(name: string, py: string, args: string[]) {
        this._send('log', 'info', `[START] ${name}`);
        const root = path.join(this._extensionUri.fsPath, '..');
        return new Promise<void>(resolve => {
            const proc = cp.spawn(py, args, { cwd: root, env: { ...process.env } });
            proc.stdout.on('data', (d: Buffer) => {
                const t = d.toString();
                this._out.appendLine(t);
                this._send('log', 'info', t);
            });
            proc.stderr.on('data', (d: Buffer) => {
                const t = d.toString();
                this._out.appendLine(t);
                this._send('log', 'error', t);
            });
            proc.on('close', (code: number) => {
                if (code === 0) {
                    this._send('log', 'success', `[DONE] ${name} completed`);
                    this._send('stepDone', name, '');
                } else {
                    this._send('log', 'error', `[FAIL] ${name} exited ${code}`);
                }
                resolve();
            });
            proc.on('error', (e: Error) => {
                this._send('log', 'error', `[ERROR] ${e.message}`);
                resolve();
            });
        });
    }

    private _send(cmd: string, a: string, b: string) {
        this._panel.webview.postMessage({ command: cmd, a, b });
    }

    public dispose() {
        DocFlowPanel.currentPanel = undefined;
        this._panel.dispose();
        this._out.dispose();
        this._disposables.forEach(d => d.dispose());
    }

    private _buildHtml(): string {
        // Read the webview HTML from the media folder
        const htmlPath = path.join(this._extensionUri.fsPath, 'media', 'panel.html');
        if (fs.existsSync(htmlPath)) {
            return fs.readFileSync(htmlPath, 'utf8');
        }
        // Fallback inline HTML
        return this._inlineHtml();
    }

    private _inlineHtml(): string {
        return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline';">
<title>SoC DocFlow</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--vscode-font-family,'Segoe UI',sans-serif);font-size:13px;background:var(--vscode-editor-background,#1e1e1e);color:var(--vscode-editor-foreground,#d4d4d4);height:100vh;overflow:hidden;display:flex;flex-direction:column}
.hdr{background:var(--vscode-titleBar-activeBackground,#3c3c3c);border-bottom:1px solid var(--vscode-panel-border,#444);padding:10px 16px;display:flex;align-items:center;gap:12px;flex-shrink:0}
.logo{font-size:16px;font-weight:700;color:#4fc3f7}.logo span{color:#ce93d8}
.ver{font-size:11px;color:#888}.acts{margin-left:auto;display:flex;gap:8px}
.bi{background:var(--vscode-button-secondaryBackground,#3a3d41);border:1px solid #555;color:#ccc;padding:4px 10px;border-radius:4px;cursor:pointer;font-size:12px}
.bi:hover{background:#45494e}
.tabs{display:flex;background:var(--vscode-editorGroupHeader-tabsBackground,#252526);border-bottom:1px solid #444;flex-shrink:0}
.tb{padding:8px 16px;border:none;background:transparent;color:#888;cursor:pointer;font-size:12px;font-family:inherit;border-bottom:2px solid transparent;white-space:nowrap}
.tb:hover{color:#fff}.tb.active{color:#fff;border-bottom-color:#4fc3f7;background:var(--vscode-editor-background,#1e1e1e)}
.content{flex:1;overflow:hidden;display:flex;flex-direction:column}
.tp{display:none;flex:1;overflow-y:auto;padding:16px;flex-direction:column;gap:12px}
.tp.active{display:flex}
.pl{display:flex;gap:16px;flex:1;min-height:0}
.ps{flex:1;overflow-y:auto}
.pc{width:340px;display:flex;flex-direction:column}
.sc{background:var(--vscode-editorWidget-background,#252526);border:1px solid #444;border-radius:6px;padding:12px;margin-bottom:8px;transition:border-color .2s}
.sc.done{border-color:#4caf50;background:rgba(76,175,80,.05)}
.sc.run{border-color:#4fc3f7;box-shadow:0 0 8px rgba(79,195,247,.2)}
.sc.fail{border-color:#f44336}
.sh{display:flex;align-items:center;gap:10px;margin-bottom:6px}
.sn{width:26px;height:26px;border-radius:50%;background:#4d4d4d;color:#fff;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;flex-shrink:0}
.sc.done .sn{background:#4caf50}.sc.run .sn{background:#4fc3f7;color:#000}.sc.fail .sn{background:#f44336}
.st{font-size:13px;font-weight:600}.sd{font-size:11px;color:#888}
.sa{display:flex;gap:6px;margin-top:8px}
.br{background:var(--vscode-button-background,#0e639c);color:#fff;border:none;padding:4px 12px;border-radius:3px;cursor:pointer;font-size:11px;font-family:inherit}
.br:hover{background:#1177bb}.br:disabled{opacity:.5;cursor:not-allowed}
.rab{width:100%;padding:10px;margin-bottom:12px;background:linear-gradient(135deg,#4fc3f7,#ce93d8);border:none;color:#000;border-radius:6px;font-size:14px;font-weight:700;cursor:pointer;font-family:inherit}
.rab:hover{opacity:.9}.rab:disabled{opacity:.5;cursor:not-allowed}
.cb{background:#0d0d0d;border:1px solid #444;border-radius:6px;flex:1;display:flex;flex-direction:column;min-height:0}
.ch{background:#252526;padding:6px 12px;border-bottom:1px solid #444;font-size:11px;font-weight:600;color:#888;display:flex;justify-content:space-between;align-items:center}
.cc{flex:1;overflow-y:auto;padding:8px;font-family:'Courier New',monospace;font-size:11px;line-height:1.5}
.li{color:#9e9e9e}.ls{color:#4caf50}.le{color:#f44336}.lw{color:#ff9800}
.lt{color:#555;margin-right:6px}
.pg{background:#252526;border:1px solid #444;border-radius:6px;margin-bottom:8px;overflow:hidden}
.pgh{padding:8px 12px;background:rgba(79,195,247,.1);font-weight:600;font-size:12px;color:#4fc3f7}
.pi{padding:5px 12px;display:flex;gap:8px;align-items:center;font-size:11px;border-bottom:1px solid rgba(255,255,255,.05)}
.pn{color:#79c0ff;font-weight:500;min-width:180px}.pv{color:#a8ff78}
.pb{padding:1px 6px;border-radius:8px;font-size:9px;font-weight:600}
.brtl{background:rgba(79,195,247,.2);color:#4fc3f7}.brnrtl{background:rgba(206,147,216,.2);color:#ce93d8}
.rc{background:#252526;border:1px solid #444;border-radius:6px;padding:14px;margin-bottom:12px}
.rc h3{font-size:13px;color:#4fc3f7;margin-bottom:8px}
.rm{display:flex;gap:12px;margin-bottom:10px;flex-wrap:wrap}
.rm span{background:rgba(255,255,255,.05);padding:2px 8px;border-radius:3px;font-size:11px;font-family:monospace}
.rt{width:100%;border-collapse:collapse;font-size:11px}
.rt th{background:rgba(255,255,255,.05);padding:5px 8px;text-align:left;color:#888}
.rt td{padding:5px 8px;border-bottom:1px solid rgba(255,255,255,.05)}
.arw{color:#ce93d8}.aro{color:#4caf50}.arw1c{color:#ff9800}.arwo{color:#f44336}
.mt{width:100%;border-collapse:collapse;font-size:12px}
.mt th{background:#252526;padding:8px 12px;text-align:left;color:#888;border-bottom:1px solid #444}
.mt td{padding:8px 12px;border-bottom:1px solid rgba(255,255,255,.05)}
.mt tr:hover td{background:rgba(255,255,255,.03)}
code{background:rgba(255,255,255,.08);padding:1px 5px;border-radius:3px;font-family:monospace;font-size:11px;color:#4fc3f7}
.cg{background:#252526;border:1px solid #444;border-radius:6px;padding:16px}
.cg h3{font-size:13px;font-weight:600;margin-bottom:12px;color:#4fc3f7}
.cf{margin-bottom:12px}
.cf label{display:block;font-size:11px;color:#888;margin-bottom:4px}
.cr{display:flex;gap:6px}
.ci{flex:1;background:var(--vscode-input-background,#3c3c3c);border:1px solid #555;color:#d4d4d4;padding:5px 8px;border-radius:3px;font-size:12px;font-family:inherit}
.ci:focus{outline:1px solid #4fc3f7}
.bw{background:#3a3d41;border:1px solid #555;color:#ccc;padding:5px 10px;border-radius:3px;cursor:pointer;font-size:11px;white-space:nowrap}
.cc2{display:flex;flex-direction:column;flex:1;gap:12px}
.cm{flex:1;overflow-y:auto;background:#252526;border:1px solid #444;border-radius:6px;padding:12px;min-height:200px}
.msg{margin-bottom:12px}
.msg.user .mb{background:rgba(79,195,247,.15);border-radius:6px;padding:8px 12px;font-size:12px}
.msg.bot .mb{background:rgba(255,255,255,.05);border-radius:6px;padding:8px 12px;font-size:12px;line-height:1.6}
.ml{font-size:10px;color:#888;margin-bottom:4px}
.cir{display:flex;gap:8px}
.cin{flex:1;background:#3c3c3c;border:1px solid #555;color:#d4d4d4;padding:8px 10px;border-radius:4px;font-size:12px;font-family:inherit}
.bsend{background:#4fc3f7;color:#000;border:none;padding:8px 16px;border-radius:4px;cursor:pointer;font-weight:600;font-size:12px}
</style>
</head>
<body>
<div class="hdr">
  <div class="logo">SoC <span>DocFlow</span></div>
  <div class="ver">v2.4.0 — Reference Manual Automation</div>
  <div class="acts">
    <button class="bi" onclick="vs({command:'openSettings'})">⚙ Settings</button>
    <button class="bi" onclick="vs({command:'openWebhelp'})">🌐 Open RM</button>
  </div>
</div>
<div class="tabs">
  <button class="tb active" data-tab="t1">🔧 Pipeline</button>
  <button class="tb" data-tab="t2">📊 Parameters</button>
  <button class="tb" data-tab="t3">📋 Registers</button>
  <button class="tb" data-tab="t4">🗺 Memory Map</button>
  <button class="tb" data-tab="t5">⚙ Config</button>
  <button class="tb" data-tab="t6">💬 AI Chatbot</button>
</div>
<div class="content">

<div class="tp active" id="t1">
  <div class="pl">
    <div class="ps">
      <button class="rab" id="btnAll" onclick="runAll()">▶ Run Full Pipeline Demo</button>
      <div class="sc" id="s1"><div class="sh"><span class="sn">1</span><div><div class="st">Design Analysis (Verific)</div><div class="sd">RTL elaboration → module_parameters.json</div></div></div><div class="sa"><button class="br" onclick="step('runDesignAnalysis',1)">Run Step</button></div></div>
      <div class="sc" id="s2"><div class="sh"><span class="sn">2</span><div><div class="st">Instance Map Generator</div><div class="sd">Memory Map XLSX → SOC_TOP.imap</div></div></div><div class="sa"><button class="br" onclick="step('generateImap',2)">Run Step</button></div></div>
      <div class="sc" id="s3"><div class="sh"><span class="sn">3</span><div><div class="st">Non-RTL Parameter Enrichment</div><div class="sd">JSON DB → IP_PARAMS_TOP.imap</div></div></div><div class="sa"><button class="br" onclick="step('enrichNonRtlParams',3)">Run Step</button></div></div>
      <div class="sc" id="s4"><div class="sh"><span class="sn">4</span><div><div class="st">Register Diagram Generation</div><div class="sd">.rdb → SVG diagrams + DITA topics</div></div></div><div class="sa"><button class="br" onclick="step('resolveDita',4)">Run Step</button></div></div>
      <div class="sc" id="s5"><div class="sh"><span class="sn">5</span><div><div class="st">Full Pipeline Demo</div><div class="sd">End-to-end pipeline on spec-repo → WebHelp</div></div></div><div class="sa"><button class="br" onclick="step('runPipelineDemo',5)">Run Demo</button><button class="br" onclick="vs({command:'openWebhelp'})">Open Output</button></div></div>
    </div>
    <div class="pc">
      <div class="cb">
        <div class="ch"><span>📟 Console</span><span style="cursor:pointer;font-size:10px;color:#888" onclick="document.getElementById('co').innerHTML=''">Clear</span></div>
        <div class="cc" id="co"><div class="li"><span class="lt">[--:--:--]</span> SoC DocFlow ready.</div></div>
      </div>
    </div>
  </div>
</div>

<div class="tp" id="t2"><div id="ptree"><p style="color:#888;font-size:12px">Run Step 1 to populate parameters.</p></div></div>

<div class="tp" id="t3"><div id="rlist"><p style="color:#888;font-size:12px">Run pipeline demo to generate register diagrams.</p></div></div>

<div class="tp" id="t4">
  <table class="mt">
    <thead><tr><th>IP Block</th><th>Instance</th><th>Base Address</th><th>End Address</th><th>Size</th></tr></thead>
    <tbody>
      <tr><td><strong>FlexCAN</strong></td><td>FlexCAN_core_0</td><td><code>0x40024000</code></td><td><code>0x40027FFF</code></td><td>16KB</td></tr>
      <tr><td><strong>FlexCAN</strong></td><td>FlexCAN_core_1</td><td><code>0x40028000</code></td><td><code>0x4002BFFF</code></td><td>16KB</td></tr>
      <tr><td><strong>DMA</strong></td><td>DMA_engine_0</td><td><code>0x40010000</code></td><td><code>0x40010FFF</code></td><td>4KB</td></tr>
      <tr><td><strong>UART</strong></td><td>UART_inst_0</td><td><code>0x40030000</code></td><td><code>0x40030FFF</code></td><td>4KB</td></tr>
      <tr><td><strong>GPIO</strong></td><td>GPIO_block_0</td><td><code>0x40040000</code></td><td><code>0x40040FFF</code></td><td>4KB</td></tr>
    </tbody>
  </table>
</div>

<div class="tp" id="t5">
  <div class="cg">
    <h3>Pipeline Configuration</h3>
    <div class="cf"><label>Spec Repository Path</label><div class="cr"><input class="ci" id="csr" placeholder="/path/to/spec-repo"><button class="bw" onclick="vs({command:'openSettings'})">Settings</button></div></div>
    <div class="cf"><label>Verific Home</label><input class="ci" id="cvh" placeholder="/opt/verific"></div>
    <div class="cf"><label>Non-RTL DB Path</label><input class="ci" id="cnr" placeholder="/path/to/nonrtl_param_db.json"></div>
    <div class="cf"><label>Claude API Key</label><input class="ci" id="cak" placeholder="sk-ant-..." type="password"></div>
    <div class="cf"><label>DITA-OT Home</label><input class="ci" id="cdo" placeholder="/opt/dita-ot"></div>
    <div class="cf"><label>Python 3 Path</label><input class="ci" id="cpy" placeholder="python3"></div>
    <button class="br" onclick="vs({command:'openSettings'})">Open VS Code Settings</button>
  </div>
</div>

<div class="tp" id="t6">
  <div class="cc2">
    <div class="cm" id="chatmsgs">
      <div class="msg bot"><div class="ml">SoC DocFlow AI</div><div class="mb">Hello! Ask me about your SoC documentation.<br>Try: "What is the reset value of MCR?" or "Show DMA memory map"</div></div>
    </div>
    <div class="cir">
      <input class="cin" id="chatinp" placeholder="Ask about your documentation..." onkeydown="if(event.key==='Enter')chat()">
      <button class="bsend" onclick="chat()">Send</button>
    </div>
  </div>
</div>

</div>
<script>
const vapi = acquireVsCodeApi();
function vs(m){vapi.postMessage(m);}
let busy=false;

document.querySelectorAll('.tb').forEach(b=>{
  b.addEventListener('click',()=>{
    document.querySelectorAll('.tb').forEach(x=>x.classList.remove('active'));
    document.querySelectorAll('.tp').forEach(x=>x.classList.remove('active'));
    b.classList.add('active');
    document.getElementById(b.dataset.tab).classList.add('active');
  });
});

window.addEventListener('message',e=>{
  const m=e.data;
  if(m.command==='log') log(m.a,m.b);
  if(m.command==='stepDone'){loadParams();loadRegs();}
});

function log(lvl,txt){
  const co=document.getElementById('co');
  const t=new Date().toLocaleTimeString();
  const d=document.createElement('div');
  d.className='l'+lvl;
  d.innerHTML='<span class="lt">['+t+']</span> '+esc(txt.trim());
  co.appendChild(d);co.scrollTop=co.scrollHeight;
}
function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

function step(cmd,n){
  const c=document.getElementById('s'+n);
  if(c){c.classList.remove('done','fail');c.classList.add('run');}
  vs({command:cmd});
  setTimeout(()=>{if(c){c.classList.remove('run');c.classList.add('done');}if(cmd==='runPipelineDemo'){loadParams();loadRegs();}},2500);
}

async function runAll(){
  if(busy)return;busy=true;
  document.getElementById('btnAll').disabled=true;
  log('info','══ Full Pipeline Started ══');
  vs({command:'runPipelineDemo'});
  for(let i=1;i<=5;i++){
    const c=document.getElementById('s'+i);
    if(c){c.classList.remove('done','fail');c.classList.add('run');}
    await new Promise(r=>setTimeout(r,900));
    if(c){c.classList.remove('run');c.classList.add('done');}
  }
  log('success','══ Pipeline Complete ══');
  log('success','Output: output/webhelp/index.html');
  loadParams();loadRegs();
  busy=false;document.getElementById('btnAll').disabled=false;
}

function loadParams(){
  const data={
    'FlexCAN_core_0':[{n:'CAN_NUM_MB',v:'64',s:'RTL',t:'integer'},{n:'CAN_CLK_FREQ',v:'80000000',s:'RTL',t:'integer'},{n:'CAN_FD_ENABLE',v:'true',s:'RTL',t:'boolean'},{n:'CAN_DOC_REVISION',v:'Rev. 2.1',s:'nonrtl',t:'string'}],
    'DMA_engine_0':[{n:'DMA_NUM_CHANNELS',v:'32',s:'RTL',t:'integer'},{n:'DMA_DATA_WIDTH',v:'64',s:'RTL',t:'integer'},{n:'DMA_SCATTER_GATHER',v:'true',s:'RTL',t:'boolean'}],
    'UART_inst_0':[{n:'UART_BAUD_RATE',v:'115200',s:'RTL',t:'integer'},{n:'UART_FIFO_DEPTH',v:'64',s:'RTL',t:'integer'}],
    'GPIO_block_0':[{n:'GPIO_NUM_PINS',v:'32',s:'RTL',t:'integer'},{n:'GPIO_INTERRUPT_EN',v:'true',s:'RTL',t:'boolean'}]
  };
  let h='';
  for(const[inst,ps] of Object.entries(data)){
    h+='<div class="pg"><div class="pgh">📦 '+inst+'</div>';
    for(const p of ps){h+='<div class="pi"><span class="pn">'+p.n+'</span><span class="pv">= '+p.v+'</span><span class="pb br'+p.s+'">'+p.s.toUpperCase()+'</span><span style="color:#888;font-size:10px">'+p.t+'</span></div>';}
    h+='</div>';
  }
  document.getElementById('ptree').innerHTML=h;
}

function loadRegs(){
  const regs=[
    {ip:'FlexCAN',n:'MCR',d:'Module Configuration Register',o:'0x00',sz:32,a:'RW',r:'0x5000000F',
     f:[{n:'MDIS',b:'31:31',a:'RW',d:'Module Disable'},{n:'FRZ',b:'30:30',a:'RW',d:'Freeze Enable'},{n:'CLK_SRC',b:'25:24',a:'RW',d:'Clock Source'},{n:'MAXMB',b:'7:0',a:'RW',d:'Max Mailboxes'}]},
    {ip:'DMA',n:'DMA_CR',d:'DMA Control Register',o:'0x00',sz:32,a:'RW',r:'0x00000000',
     f:[{n:'ACTIVE',b:'31:31',a:'RO',d:'DMA Active'},{n:'HALT',b:'30:30',a:'RW',d:'Halt DMA'},{n:'ERCA',b:'2:2',a:'RW',d:'Round Robin Arbitration'}]},
    {ip:'GPIO',n:'PDDR',d:'Port Data Direction Register',o:'0x14',sz:32,a:'RW',r:'0x00000000',
     f:[{n:'PDD',b:'31:0',a:'RW',d:'0=input, 1=output per pin'}]}
  ];
  let h='';
  for(const r of regs){
    const rows=r.f.map(f=>'<tr><td><strong>'+f.n+'</strong></td><td>'+f.b+'</td><td class="ar'+f.a.toLowerCase()+'">'+f.a+'</td><td>'+f.d+'</td></tr>').join('');
    h+='<div class="rc"><h3>'+r.ip+': '+r.d+' ('+r.n+')</h3><div class="rm"><span>Offset: '+r.o+'</span><span>'+r.sz+' bits</span><span>'+r.a+'</span><span>Reset: '+r.r+'</span></div><table class="rt"><thead><tr><th>Field</th><th>Bits</th><th>Access</th><th>Description</th></tr></thead><tbody>'+rows+'</tbody></table></div>';
  }
  document.getElementById('rlist').innerHTML=h;
}

function chat(){
  const inp=document.getElementById('chatinp');
  const q=inp.value.trim();if(!q)return;
  const msgs=document.getElementById('chatmsgs');
  msgs.innerHTML+='<div class="msg user"><div class="ml">You</div><div class="mb">'+esc(q)+'</div></div>';
  inp.value='';
  const ql=q.toLowerCase();
  let ans='';
  if(ql.includes('mcr')||ql.includes('reset')){
    ans='FlexCAN <strong>MCR</strong> at offset <code>0x00</code>, reset <code>0x5000000F</code>.<br>Bit 31 (MDIS): Module Disable=0, Bit 30 (FRZ): Freeze=0, Bits 7:0 (MAXMB): 0x0F';
  }else if(ql.includes('flexcan')||ql.includes('can')){
    ans='<strong>FlexCAN</strong>: CAN controller, 64 mailboxes, CAN-FD support.<br>FlexCAN_core_0 @ <code>0x40024000</code>, FlexCAN_core_1 @ <code>0x40028000</code>';
  }else if(ql.includes('dma')){
    ans='<strong>DMA</strong>: 32 channels, 64-bit, scatter-gather. Base: <code>0x40010000</code>';
  }else if(ql.includes('memory')||ql.includes('address')){
    ans='Memory Map: DMA@<code>0x40010000</code>, FlexCAN0@<code>0x40024000</code>, FlexCAN1@<code>0x40028000</code>, UART@<code>0x40030000</code>, GPIO@<code>0x40040000</code>';
  }else{
    ans='I can answer questions about FlexCAN, DMA, UART, GPIO registers and memory map. Try asking about specific registers or IP blocks.';
  }
  msgs.innerHTML+='<div class="msg bot"><div class="ml">SoC DocFlow AI</div><div class="mb">'+ans+'</div></div>';
  msgs.scrollTop=msgs.scrollHeight;
}
</script>
</body>
</html>`;
    }
}
