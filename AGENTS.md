# AGENTS.md — Voice Input Project Guidelines

## 1. 语言与沟通规范 (Language & Communication)
- **对话语言**：对话统一使用**中文**，专业术语（如函数名、类名、API、设计模式、CLI 命令等）保持英文原称。
- **代码规范**：代码中的标识符、变量名、方法名、注释与 Docstring 一律使用**英文**。

## 2. 编码风格 (Coding Guidelines)
- **简洁优先**：不过度抽象，代码自解释，不添加无意义的装饰性注释。
- **极简防护**：不在不需要时主动加冗余的错误处理、fallback 或兜底验证——仅在系统边界处（如网络请求 API、设备驱动接入、Win32 API 调用）添加防御逻辑。
- **按需开发 (YAGNI)**：不设计未来才可能用到的功能，不提前重构未出现问题的模块。

## 3. 协作与操作规则 (Collaboration Protocol)
- **破坏性操作**：执行删除文件、`git push --force`、清理环境等破坏性动作前，必须明确向用户确认。
- **Commit 机制**：不主动执行 `git commit`，仅在用户明确提出提交要求时再进行 commit。
- **范围变更**：若发现修改范围将超出当前任务描述，须先给出调整方案并征得同意。

### Agent Pre-Commit Hook (Agent 提交前文档检查与更新机制)
在 Agent 响应用户指令执行 `git commit` 或发布新版本之前，必须自动触发 Agent Pre-Commit Hook 检查：
1. **文档关联变更判断**：检查所有暂存/修改的文件。若涉及核心代码 (`src/`)、架构逻辑或 UI 交互变更，判断是否需要同步更新相关文档。
2. **自动一键同步更新**：若判断需要更新，Agent 须自动同步更新所有涉及的文档（包含但不限于 `AGENTS.md`、`README.md`、`docs/specs/speech_input_windows_spec.md`、`findings.md`、`task_plan.md` 及 `progress.md`）。
3. **版本与 CHANGELOG 强制对齐**：若发生版本递增或新功能发布，Agent 须自动将 `VERSION` 文件递增，并在 `CHANGELOG.md` 中追加对应版本的变更树说明，确认无误后方可执行 `git commit` 提交。

## 4. Git 规范 (Git Standards)

### Commit Message 规范
提交信息必须遵循 Conventional Commits 并在 Body 中提供树状变更说明：

```text
type(scope): short description in english

修改文件：
├── path/to/file1.py    — 变更说明
├── path/to/file2.py    — 变更说明
└── path/to/
    ├── file3.py        — 变更说明
    └── file4.py        — 变更说明
```

- **type**：`feat` / `fix` / `refactor` / `chore` / `docs` / `test` / `style` / `perf`
- **scope**：（可选）描述受影响的模块（小写英文，如 `asr`, `ui`, `audio`, `injector`）。
- **description**：使用英文，祈使句（如 `add`, `fix`, `update`），首字母小写，结尾**不加句号**。
- **修改文件**：使用树状结构完整列出所有暂存的变更文件，每个文件使用 `—` 分隔并附带简要变更说明（**变更说明统一使用中文**）。

### 分支命名规范
```text
type/YYYY-MM-DD_业务描述
```
- **type**：`feature` / `fix` / `hotfix` / `refactor` / `chore`
- **格式**：日期 `YYYY-MM-DD` 搭配下划线连接小写英文描述。
- **示例**：`feature/2026-07-29_windows_voice_input_pyside6`

### 预推送合并与冲突预防规范 (Pre-Push & Conflict Prevention Standard)
为防止 GitHub Actions 自动化工作流在 `master` 发布 Release 后自动更新 `voice-input.json` 导致合并推送冲突，项目统一遵循以下无冲突流转规范：

1. **功能分支独立推拉 (Feature Branch Push/Pull)**：
   - 所有功能开发、测试与临时备份均在 `type/YYYY-MM-DD_业务描述` 独立功能分支上进行。
   - **开发分支自由 Push**：功能分支可随时自由执行 `git push origin <feature-branch>` 上传远程。由于 CI/CD 仅监听 `master`/`main` 触发 Release，功能分支不会受到 Scoop Manifest 自动提交的冲突打扰。
2. **合并至 Master 前的三步消隐冲突法**：
   当准备将功能分支合并至 `master` 主分支进行最终 Release 发布时，按以下顺序操作：
   - **Step 1 (拉取主分支)**：`git checkout master && git pull origin master`（此时主分支无本地冲突，100% 顺畅同步远端）。
   - **Step 2 (分支内部消解)**：`git checkout <feature-branch> && git merge master`（在功能分支内部消化 `voice-input.json` 等潜在冲突并验证测试）。
   - **Step 3 (主分支 Fast-Forward 推送)**：`git checkout master && git merge <feature-branch> && git push origin master`（100% 顺畅 Fast-Forward 快速推送，触发 CI/CD 自动构建）。

---

## 5. 项目架构与技术栈概览 (Project Stack)
- **操作系统与环境**：Windows 10 / 11 (支持 `uv` 包管理器与 `.python-version` 锁定 Python 3.12)
- **UI 框架**：PySide6 (`Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool`)
- **音频引擎**：`sounddevice` + NumPy RMS 包络平滑
- **热键引擎**：`pynput` / Win32 API 键盘监听
- **ASR 支持**：豆包 WebSocket, 通义千问 WebSocket, 小米 MiMo (`mimo-v2.5-asr`), OpenAI HTTP REST
- **LLM 精修**：OpenAI / Local GGUF / DeepSeek / Qwen / Xiaomi / Ollama 7 大供应商，保守纠错 System Prompt
- **文本注入**：`win32clipboard` 备份/恢复 + Win32 `SendInput(Ctrl+V)` 模拟

---

## 6. 版本管理规范 (Versioning Standards)

### 滚动式版本格式 (Rolling Versioning)
项目采用**滚动式版本控制**，统一存放在项目根目录的 `VERSION` 文件中作为单源真实版本号 (Single Source of Truth)：

```text
YYYY.MM.DD.xxx
```
- **YYYY.MM.DD**：发布当日的公历日期（例如 `2026.07.29`）。
- **xxx**：当日发布的递增序号，补足 3 位数字（例如 `001`, `002`）。
- **示例**：`2026.07.29.001`

### 自动发布与 Scoop 同步机制
1. **单源版本变更**：在进行新功能或 Bug 修复发布前，须将根目录 `VERSION` 文件更新为最新的滚动版本号，并在 `CHANGELOG.md` 中同步追加对应版本的变更说明。
2. **GitHub Actions 自动构建与 Release 说明**：每次提交 `git push` 后，GitHub Actions 自动化工作流会自动解析 `CHANGELOG.md` 中与 `VERSION` 匹配的变更说明，作为 Release Message 自动发布 GitHub Release，并附带 PyInstaller 构建的单文件可执行程序 `VoiceInput.exe`。
3. **Scoop Manifest 自动更新**：发布流程会自动计算构建产物的 SHA-256 哈希值，更新根目录下的 `voice-input.json` Scoop 清单，确保支持 Scoop 包管理器的无缝自动升级 (`scoop update voice-input`)。
