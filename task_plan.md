# Task Plan - Local LLM, WebDAV Fix, Logo & Versioning Alignment

## Task Summary
在 `feature/2026-07-30_local_llm_and_fixes` 开发分支上实现以下 4 项增强与修复：
1. **WebDAV 路径优化**：修复 WebDAV 下载配置时找不到路径的问题（规范化 URL / Subpath 拼接，下载前自动递归检查父目录）。
2. **Logo 设计与应用**：设计并生成 Logo 图片，待用户确认后在 About 页及主界面应用。
3. **About 页版本号联动**：新增 `src/utils/version.py` 动态获取 `VERSION` 文件单源版本号。
4. **新增本地 LLM 模型/供应商**：在后处理模型列表中新增“本地模型 (GGUF / Local)”，支持模型列表选择、自动下载至 `~/.voiceinput/models/`（含代理支持与确认弹窗）、本地删除模型功能。

---

## Plan Steps

### Phase 1: Logo 确认与版本控制单源化 (Version & Logo)
- [x] Step 1.1: 创建开发分支 `feature/2026-07-30_local_llm_and_fixes`
- [x] Step 1.2: 生成 Logo 提议图像，展示给用户请求确认
- [x] Step 1.3: 创建 `src/utils/version.py` 统一版本号读取逻辑，更新 `src/ui/settings/about_tab.py`

### Phase 2: WebDAV 路径修复 (WebDAV Fix)
- [x] Step 2.1: 升级 `src/utils/webdav.py` 路径拼装算法（处理基础 URL 子路径与转义）
- [x] Step 2.2: 在下载/恢复时确保本地存放目录与远端路径正确，添加详细错误日志与单元测试

### Phase 3: 本地 LLM 供应商与模型管理 (Local LLM Provider)
- [x] Step 3.1: 在 `src/config.py` 与 `src/refine/llm.py` 中重构 LLM 供应商，加入 `local` 模式与预设模型配置
- [x] Step 3.2: 建立模型下载管理器 `src/utils/model_downloader.py`（支持代理、断点续传、~/.voiceinput/models 路径、弹窗确认）
- [x] Step 3.3: 在 `src/ui/settings/llm_tab.py` 中接入本地模型下拉选择、弹窗下载、状态指示与“删除本地模型”按钮
- [x] Step 3.4: 更新 `src/i18n.py` 完善中英文翻译字典

### Phase 4: 验证与多语言对齐 (Verification & Alignment)
- [x] Step 4.1: 运行单元测试 / 集成验证，确保 LLM 本地与云端引擎、WebDAV 上传下载、About 页正常工作
- [x] Step 4.2: 依据 AGENTS.md 规范更新文档 (VERSION, CHANGELOG.md, findings.md, progress.md)
