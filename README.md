<div align="center">

<img src="https://raw.githubusercontent.com/Murugarajr/ohm-mcp-pypi/refs/heads/main/image/ohm-mcp.png?token=GHSAT0AAAAAADQXBQJXVCRGZAMLBZA5U2MW2KAQUWQ" alt="OHM-MCP" width="300">

# OHM-MCP

**AI-Powered Python Refactoring & Code Quality Assistant**

Works with **GitHub Copilot**, **Cursor IDE**, **Cline**, and any MCP-compatible AI assistant.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-0.1.0+-green.svg)](https://modelcontextprotocol.io)
[![AST-Based](https://img.shields.io/badge/AST--Based-100%25-brightgreen.svg)]()
[![License](https://img.shields.io/badge/license-MIT-blue.svg)]()

</div>

---

## ✨ Core Capabilities

<table>
<tr>
<td width="50%">

### 🏗️ **Architecture**
- God Object Detection
- SOLID Violation Analysis
- Design Pattern Suggestions
- Dependency Injection Refactoring

### 🔧 **Code Quality**
- AST Extract Method (100% accurate)
- Dead Code Elimination
- Import Refactoring
- Symbol Renaming (project-wide)
- Duplication Detection

</td>
<td width="50%">

### 📊 **Type Safety**
- Type Coverage Analysis
- Type Stub Generation
- Auto Test Generation

### ⚡ **Performance**
- O(n²) Pattern Detection
- Hotspot Analysis
- Coverage-Driven Prioritization

### 🤖 **Automation**
- Auto-Apply with Rollback
- Operation History
- Quality Dashboard

</td>
</tr>
</table>

---

## 🚀 Quick Start

### Installation
```bash
pip install -e .
```

### IDE Configuration

#### 📦 **Option 1: NPX (Recommended - Auto-installs dependencies)**

<details>
<summary><b>🔵 GitHub Copilot (VS Code) with NPX</b></summary>

**After publishing to npm:**
```json
{
  "mcpServers": {
    "ohm-mcp": {
      "command": "npx",
      "args": ["ohm-mcp@latest"]
    }
  }
}
```

**For local development:**
```json
{
  "mcpServers": {
    "ohm-mcp": {
      "command": "npx",
      "args": ["--package", "/path/to/ohm-mcp-npm", "ohm-mcp"]
    }
  }
}
```

**Usage:**
- Open Copilot Chat
- Type `#` and select `ohm-mcp` tools
- Ask: "Analyze this file and suggest refactorings"

</details>

<details>
<summary><b>🟣 Cursor IDE with NPX</b></summary>

**Global (After publishing to npm):**
```json
{
  "mcpServers": {
    "ohm-mcp": {
      "command": "npx",
      "args": ["-y", "ohm-mcp@latest"]
    }
  }
}
```

**For local development:**
```json
{
  "mcpServers": {
    "ohm-mcp": {
      "command": "npx",
      "args": ["--package", "/path/to/ohm-mcp-npm", "ohm-mcp"]
    }
  }
}
```

**Usage:**
- Open Cursor Chat (Cmd+L / Ctrl+L)
- Tools are automatically available
- Ask: "Use ohm-mcp to detect dead code"

</details>

<details>
<summary><b>🟢 Cline (VS Code Extension) with NPX</b></summary>

**Global (After publishing to npm):**
```json
{
  "mcpServers": {
    "ohm-mcp": {
      "command": "npx",
      "args": ["-y", "ohm-mcp@latest"]
    }
  }
}
```

**For local development:**
```json
{
  "mcpServers": {
    "ohm-mcp": {
      "command": "npx",
      "args": ["--package", "/path/to/ohm-mcp-npm", "ohm-mcp"]
    }
  }
}
```

**Usage:**
- Open Cline panel
- Tools are available in agent context
- Ask: "Analyze type coverage and suggest improvements"

</details>

<details>
<summary><b>🟠 Antigravity with NPX</b></summary>

**Global (After publishing to npm):**
```json
{
  "mcpServers": {
    "ohm-mcp": {
      "command": "npx",
      "args": ["-y", "ohm-mcp@latest"],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

**Usage:**
- Tools are automatically available in Antigravity
- Ask: "Use ohm-mcp to analyze architecture"

</details>

<details>
<summary><b>🔴 Roo Code with NPX</b></summary>

**Global (After publishing to npm):**
```json
{
  "mcpServers": {
    "ohm-mcp": {
      "command": "npx",
      "args": ["-y", "ohm-mcp@latest"]
    }
  }
}
```

**Usage:**
- Open Roo Code panel
- Tools are available in agent context
- Ask: "Use ohm-mcp to detect duplicates"

</details>

<details>
<summary><b>⚫ Codex VS Code with NPX</b></summary>

**Configuration (config.toml):**
```toml
[mcp_servers.ohm-mcp]
args = ["-y", "ohm-mcp@latest"]
command = "npx"
```

**Usage:**
- Open Codex panel
- Tools are automatically available
- Ask: "Use ohm-mcp to suggest design patterns"

</details>

<details>
<summary><b>🟡 Kilo Code with NPX (Local/Global)</b></summary>

**Local (For local development with virtual environment):**
```json
{
  "mcpServers": {
    "ohm-mcp": {
      "command": "/Users/username/project/venv/bin/python",
      "args": ["-m", "ohm_mcp.server"],
      "disabled": false,
      "alwaysAllow": []
    }
  }
}
```

**Global (After publishing to npm):**
```json
{
  "mcpServers": {
    "ohm-mcp": {
      "command": "npx",
      "args": ["-y", "ohm-mcp@latest"]
    }
  }
}
```

**Usage:**
- Open Kilo Code panel
- Tools are available in agent context
- Ask: "Use ohm-mcp for refactoring"

</details>

#### 🐍 **Option 2: Direct Python (Manual setup)**

<details>
<summary><b>🔵 GitHub Copilot (VS Code) with Python</b></summary>

First install: `pip install ohm-mcp`

Then add to `.vscode/mcp.json`:
```json
{
  "servers": {
    "ohm-mcp": {
      "command": "python",
      "args": ["-m", "ohm_mcp.server"]
    }
  },
  "inputs": []
}
```

**Usage:**
- Open Copilot Chat
- Type `#` and select `ohm-mcp` tools
- Ask: "Analyze this file and suggest refactorings"

</details>

<details>
<summary><b>🟣 Cursor IDE with Python</b></summary>

First install: `pip install ohm-mcp`

Then add to Cursor's MCP settings file (`.cursorrules` or MCP config):
```json
{
  "mcpServers": {
    "ohm-mcp": {
      "command": "python",
      "args": ["-m", "ohm_mcp.server"]
    }
  },
  "inputs": []
}
```

**Example with virtual environment:**
```json
{
  "mcpServers": {
    "ohm-mcp": {
      "command": "/Users/username/projects/venv/bin/python",
      "args": ["-m", "ohm_mcp.server"]
    }
  }
}
```

**Usage:**
- Open Cursor Chat (Cmd+L / Ctrl+L)
- Tools are automatically available
- Ask: "Use ohm-mcp to detect dead code"

</details>

<details>
<summary><b>🟢 Cline (VS Code Extension) with Python</b></summary>

First install: `pip install ohm-mcp`

Then add to Cline's MCP settings:
```json
{
  "mcpServers": {
    "ohm-mcp": {
      "command": "python",
      "args": ["-m", "ohm_mcp.server"]
    }
  }
}
```

**Example with virtual environment:**
```json
{
  "mcpServers": {
    "ohm-mcp": {
      "command": "/Users/username/projects/venv/bin/python",
      "args": ["-m", "ohm_mcp.server"]
    }
  }
}
```

**Note:** Cline requires absolute paths for both `command` and `cwd`.

**Usage:**
- Open Cline panel
- Tools are available in agent context
- Ask: "Analyze type coverage and suggest improvements"

</details>

<details>
<summary><b>🔧 Other MCP-Compatible Clients</b></summary>

Any MCP-compatible client can use this server. General configuration:

```json
{
  "mcpServers": {
    "ohm-mcp": {
      "command": "<python-interpreter-path>",
      "args": ["<path-to-mcp_server.py>"],
      "cwd": "<project-directory>"
    }
  }
}
```

**Finding your Python path:**
```bash
# Unix/Mac
which python
# or
which python3

# Windows
where python
```

</details>

---

## 🎯 Key Tools

<details>
<summary><b>🏗️ Architecture & Design (4 tools)</b></summary>

| Tool | Purpose | Output |
|------|---------|--------|
| `analyze_architecture` | Detect God Objects, SOLID violations | Detailed issue report |
| `suggest_design_patterns` | Recommend patterns (Strategy, Factory, Observer) | Pattern suggestions + examples |
| `analyze_tight_coupling` | Find coupling issues | DI recommendations |
| `suggest_di_refactor` | Generate DI code | Before/after refactor |

</details>

<details>
<summary><b>🔧 Code Quality & Refactoring (6 tools)</b></summary>

| Tool | Purpose | Key Feature |
|------|---------|-------------|
| `extract_method_ast` | Extract code into function | 100% AST-based accuracy |
| `suggest_extractable_methods` | Find extractable blocks | Cohesion scoring |
| `detect_dead_code` | Find unused code | 5 types of dead code |
| `refactor_imports` | Update imports project-wide | Safe module renaming |
| `rename_symbol` | Rename across codebase | Conflict detection |
| `detect_code_duplicates` | Find DRY violations | Exact + near duplicates |

**Example - Extract Method:**
```python
# Input: Lines 45-60
result = extract_method_ast(code, 45, 60, "calculate_total")

# Output: Refactored code + patch + auto-detected params/returns
```

</details>

<details>
<summary><b>📊 Type Safety & Testing (4 tools)</b></summary>

| Tool | Purpose | Benefit |
|------|---------|---------|
| `analyze_type_hints` | Check type coverage | Migration plan |
| `generate_type_stub` | Create .pyi files | Gradual typing |
| `generate_characterization_tests` | Auto-generate tests | Safe refactoring |
| `generate_test_for_function` | Single function tests | Targeted testing |

</details>

<details>
<summary><b>⚡ Performance & Coverage (2 tools)</b></summary>

| Tool | Purpose | Detects |
|------|---------|---------|
| `analyze_performance` | Find bottlenecks | Nested loops, mutable defaults, O(n²) |
| `prioritize_by_coverage` | Risk-based prioritization | High-risk uncovered code |

</details>

<details>
<summary><b>🤖 Automated Execution (3 tools)</b></summary>

```mermaid
graph LR
    A[apply_refactoring] --> B{Dry Run?}
    B -->|Yes| C[Show Preview]
    B -->|No| D[Create Backup]
    D --> E[Apply Changes]
    E --> F{Run Tests}
    F -->|Pass| G[Success]
    F -->|Fail| H[Auto Rollback]
    H --> I[rollback_refactoring]
```

**Features:**
- ✅ Automatic backup before changes
- ✅ Test execution validation
- ✅ Auto-rollback on failure
- ✅ Full audit trail (`show_refactoring_history`)

</details>

<details>
<summary><b>📈 Metrics & Reporting (1 tool)</b></summary>

**`generate_quality_report`** - Comprehensive dashboard in HTML/Markdown/JSON

**Output Preview:**

```
📊 Health Score: 85/100 (Good)
📁 Files: 47 | Lines: 12,450 | Tech Debt: 23 pts

📊 Type Coverage: 67%
🗑️ Dead Code: 8 imports, 12 variables, 3 functions
⚡ Performance: 4 nested loops, 2 mutable defaults
📋 Duplication: 3 exact, 5 near-duplicates
```

**Visual Dashboard:**
- 🎨 Circular health gauge
- 📊 Color-coded metrics (🟢🟡🔴)
- 📈 Trend tracking ready
- 🔗 CI/CD integration (JSON export)

</details>

---

## 💡 Common Workflows

### 1️⃣ **Safe Refactoring**
```bash
generate_characterization_tests → pytest → extract_method_ast → pytest
```

### 2️⃣ **Eliminate Duplication**
```bash
detect_code_duplicates → review suggestions → extract_method_ast
```

### 3️⃣ **Type Migration**
```bash
analyze_type_hints → follow migration plan → generate_type_stub
```

### 4️⃣ **Performance Optimization**
```bash
analyze_performance → prioritize_by_coverage → apply fixes
```

### 5️⃣ **Module Refactoring**
```bash
refactor_imports(old="myapp.old", new="myapp.new") → review patches
```

### 6️⃣ **Symbol Renaming**
```bash
rename_symbol(old="calc", new="calculate", preview_only=True) → apply
```

### 7️⃣ **Quality Tracking**
```bash
generate_quality_report(format="html") → open dashboard → track trends
```

---

## 🎨 Visual Examples

### Quality Dashboard Preview

```
┌─────────────────────────────────────────────┐
│  🔍 Code Quality Dashboard                  │
├─────────────────────────────────────────────┤
│                                             │
│       ╭─────────╮     📁 Overview          │
│       │   85    │     Files: 47            │
│       │  /100   │     Lines: 12,450        │
│       ╰─────────╯     Tech Debt: 23        │
│     Health Score                            │
│                                             │
├─────────────────────────────────────────────┤
│  📊 Type Coverage       ⚡ Performance      │
│  ████████░░ 67%         🔴 4 nested loops  │
│  120/180 typed          🟡 2 mutable args  │
├─────────────────────────────────────────────┤
│  🗑️ Dead Code           📋 Duplication      │
│  8 imports              3 exact            │
│  12 variables           5 near             │
│  3 functions                               │
└─────────────────────────────────────────────┘
```

### Symbol Rename Preview

```diff
# Before
- def calc(x, y):
-     return x + y
- result = calc(5, 3)

# After
+ def calculate_sum(x, y):
+     return x + y
+ result = calculate_sum(5, 3)

✅ 1 function renamed
✅ 3 call sites updated
✅ 0 conflicts detected
```

---

## 🧠 Design Principles

| Principle | Implementation |
|-----------|----------------|
| 🧪 **Test-First** | Auto-generate characterization tests before refactoring |
| ↩️ **Reversible** | Every change = backup + rollback capability |
| 🎯 **AST-Driven** | 100% accurate (no regex) |
| 📊 **Risk-Aware** | Coverage + complexity = prioritization |
| 🏛️ **SOLID** | Detect violations + concrete fixes |
| 🚫 **No Blindness** | Analyze → Plan → Validate |

---

## 🔌 IDE Compatibility

<table>
<tr>
<td align="center" width="100%">
<b>🤖 Any MCP Client</b><br>
✅ Standard Protocol<br>
✅ Easy Setup<br>
✅ Works with all MCP-compatible AI assistants
</td>
</tr>
</table>

---


## 📊 Comparison

| Feature | OHM MCP | Traditional Tools |
|---------|---------|-------------------|
| Accuracy | 100% AST | ~70% Regex |
| Safety | Auto backup/rollback | Manual |
| Testing | Auto-generates | Manual |
| Automation | Full | Suggestions only |
| Dashboard | HTML/JSON/MD | Text logs |
| IDE Support | Copilot/Cursor/Cline | Limited |

---

## 🎯 Use Cases

<table>
<tr>
<td><b>👨‍💻 Developers</b><br>• Refactor legacy code safely<br>• Find dead code<br>• Optimize performance</td>
<td><b>👥 Teams</b><br>• Track tech debt<br>• Enforce standards<br>• Design patterns</td>
<td><b>🚀 CI/CD</b><br>• Quality gates<br>• Trend tracking<br>• Block bad PRs</td>
</tr>
</table>

---

## 📈 Metrics

```
✅ 13 Advanced Capabilities
✅ 30+ Static Checks
✅ 100% AST Accuracy
✅ Zero Regex Patterns
✅ Automated Execution
✅ Beautiful Dashboards
✅ Universal MCP Compatibility
```

---

## 🛠️ Troubleshooting

<details>
<summary><b>MCP Connection Issues</b></summary>

1. **Verify Python path:**
   ```bash
   which python  # Unix/Mac
   where python  # Windows
   ```

2. **Test MCP server directly:**
   ```bash
   python mcp_server.py
   ```

3. **Check logs:**
   - VS Code: Check Output panel
   - Cursor: Check Cursor logs
   - Cline: Check Cline settings panel

4. **Common issues:**
   - ❌ Relative paths in `command` → Use absolute paths
   - ❌ Missing virtual environment → Activate venv first
   - ❌ Wrong `cwd` for Cline → Must be absolute path

</details>

---

## 🤝 Contributing

Run before submitting:
```bash
./static_analyser.sh  # Runs ruff, mypy, pylint, flake8
pytest                 # All tests must pass
```

---

## 🙏 Credits

Built with [Model Context Protocol](https://modelcontextprotocol.io) • Python AST • Compatible with GitHub Copilot, Cursor IDE, Cline

---

<div align="center">

**Made with ❤️ for better code quality**

⭐ **Star this repo** if it helps you write cleaner code!

[Documentation](https://www.ohm-mcp.dev) 

</div>
