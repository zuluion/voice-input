import os
import sys
import time
import json
import asyncio
import threading
import requests
import typer
from typing import Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.config import ConfigManager
from src.core.engine import CoreEngine
from src.utils.injector import TextInjector
from src.utils.logger import logger
from src.audio.recorder import AudioRecorder

app = typer.Typer(
    name="voice-input-cli",
    help="Voice Input 前后端分离全功能终端命令行工具 (Full-Flow CLI Client)",
    invoke_without_command=True
)

daemon_app = typer.Typer(help="管理 Headless 后端守护进程生命周期")
config_app = typer.Typer(help="查看、快捷设置及同步系统配置")

app.add_typer(daemon_app, name="daemon")
app.add_typer(config_app, name="config")

console = Console()
DEFAULT_DAEMON_URL = "http://127.0.0.1:28080"
ASCII_BARS = [" ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]

# --- Daemon 管理命令 ---

@daemon_app.command("status")
def daemon_status(url: str = DEFAULT_DAEMON_URL) -> None:
    """检查后端守护进程运行健康状态与连接连通性"""
    try:
        res = requests.get(f"{url}/api/v1/health", timeout=3, proxies={"http": None, "https": None})
        if res.status_code == 200:
            data = res.json()
            console.print(Panel(
                f"[bold green]✓ Core Backend Daemon is Running[/bold green]\n\n"
                f"• URL: {url}\n"
                f"• Engine State: [bold yellow]{data.get('engine_state')}[/bold yellow]\n"
                f"• Active ASR: [bold cyan]{data.get('asr_provider')}[/bold cyan]\n"
                f"• Active LLM: [bold cyan]{data.get('llm_provider')}[/bold cyan]\n"
                f"• Language: {data.get('language')}",
                title="Voice Input Daemon Health",
                border_style="green"
            ))
        else:
            console.print(f"[bold red]Daemon returned error status code: {res.status_code}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]✗ Unable to connect to Core Backend Daemon at {url}[/bold red]")
        console.print(f"[dim]Error: {e}[/dim]")

@daemon_app.command("start")
def daemon_start(port: int = 28080) -> None:
    """启动本地无头后端守护进程 (Headless Daemon)"""
    console.print(f"[bold green]Starting Local Voice Input Daemon on port {port}...[/bold green]")
    from src.backend.main_daemon import start_daemon
    start_daemon(port=port)

# --- Config 管理命令 ---

@config_app.command("show")
def config_show() -> None:
    """打印并查看当前系统的全局配置对象"""
    cm = ConfigManager()
    table = Table(title="Voice Input Global Configuration", border_style="cyan")
    table.add_column("Category / Key", style="bold yellow")
    table.add_column("Value", style="cyan")

    for key, val in cm.config.items():
        if isinstance(val, dict):
            table.add_row(f"[{key}]", "")
            for sub_k, sub_v in val.items():
                if "key" in sub_k.lower() or "secret" in sub_k.lower():
                    masked_v = f"{str(sub_v)[:4]}****" if sub_v else "(empty)"
                    table.add_row(f"  └─ {sub_k}", masked_v)
                else:
                    table.add_row(f"  └─ {sub_k}", str(sub_v))
        else:
            table.add_row(key, str(val))

    console.print(table)

@config_app.command("set")
def config_set(key_path: str, value: str) -> None:
    """快捷更新配置项，例如: voice-input-cli config set asr.provider doubao"""
    cm = ConfigManager()
    parts = key_path.split(".")
    target = cm.config

    for part in parts[:-1]:
        if part not in target or not isinstance(target[part], dict):
            target[part] = {}
        target = target[part]

    if value.lower() == "true":
        typed_val = True
    elif value.lower() == "false":
        typed_val = False
    elif value.isdigit():
        typed_val = int(value)
    else:
        typed_val = value

    target[parts[-1]] = typed_val
    cm.save_config()

    try:
        requests.put(f"{DEFAULT_DAEMON_URL}/api/v1/config", json=cm.config, timeout=2, proxies={"http": None, "https": None})
    except Exception:
        pass

    console.print(f"[bold green]✓ Updated configuration key '{key_path}' -> {typed_val}[/bold green]")

@config_app.command("sync")
def config_sync(url: str = DEFAULT_DAEMON_URL) -> None:
    """触发 WebDAV 手动配置同步"""
    try:
        res = requests.post(f"{url}/api/v1/config/sync", timeout=10, proxies={"http": None, "https": None})
        if res.status_code == 200:
            console.print(f"[bold green]✓ WebDAV Sync Succeeded:[/bold green] {res.json().get('message')}")
        else:
            console.print(f"[bold red]✗ WebDAV Sync Failed:[/bold red] {res.json().get('detail')}")
    except Exception as e:
        console.print(f"[bold red]✗ WebDAV Sync Exception:[/bold red] {e}")

# --- 交互式 ASR / LLM 供应商管理中心 ---

ASR_PROVIDERS = [
    ("xiaomi_mimo", "小米 MiMo ASR"),
    ("doubao", "火山豆包 ASR"),
    ("qwen", "阿里通义千问 ASR"),
    ("openai", "OpenAI Whisper REST")
]

# 核心 7 大 LLM 供应商矩阵 (与 AGENTS.md 及 config 完备对齐)
LLM_PROVIDERS = [
    ("local", "系统内置离线模型 (内置 Ollama 引擎 - 默认 qwen2.5:1.5b)"),
    ("ollama", "自定义 Ollama 服务 (Ollama REST API Endpoint)"),
    ("deepseek", "DeepSeek LLM"),
    ("qwen", "阿里通义千问 LLM"),
    ("openai", "OpenAI LLM"),
    ("xiaomi", "小米 LLM"),
    ("custom", "自定义 OpenAI 兼容 Endpoint (Custom API)")
]

def safe_prompt(prompt_text: str, default_val: str = "") -> Optional[str]:
    """安全输入辅助函数: 支持按 Ctrl+C 或输入 'q' / 'cancel' 随时中途取消返回"""
    try:
        user_input = Prompt.ask(f"{prompt_text} (输入 'q' 取消)", default=default_val).strip()
        if user_input.lower() in ["q", "cancel"]:
            console.print("[yellow]操作已取消[/yellow]")
            return None
        return user_input
    except KeyboardInterrupt:
        console.print("\n[yellow]操作已取消[/yellow]")
        return None

def check_asr_provider_status(asr_cfg: Dict[str, Any], p_id: str) -> str:
    sub = asr_cfg.get(p_id, {})
    if p_id == "doubao":
        has_id = bool(sub.get("appid"))
        has_tok = bool(sub.get("token"))
        return "[bold green]✓ 已配置 (AppID/Token)[/bold green]" if (has_id and has_tok) else "[bold yellow]⚠️ 缺少 AppID/Token[/bold yellow]"
    else:
        has_key = bool(sub.get("api_key") or asr_cfg.get("api_key"))
        return "[bold green]✓ 已配置 (API Key)[/bold green]" if has_key else "[bold red]✗ 未配置 API Key[/bold red]"

def check_llm_provider_status(llm_cfg: Dict[str, Any], p_id: str) -> str:
    sub = llm_cfg.get(p_id, {})
    if p_id in ["ollama", "local"]:
        model = sub.get("model", "qwen2.5:1.5b")
        return f"[bold green]✓ 就绪 ({model})[/bold green]"
    else:
        has_key = bool(sub.get("api_key") or llm_cfg.get("api_key"))
        model = sub.get("model", "默认模型")
        return f"[bold green]✓ 已配置 Key ({model})[/bold green]" if has_key else "[bold red]✗ 未配置 Key[/bold red]"

def interactive_asr_detail(p_id: str, p_name: str) -> None:
    """ASR 供应商详情查看与精细化修改二级菜单"""
    while True:
        cm = ConfigManager()
        asr_cfg = cm.get("asr", default={})
        active_asr = asr_cfg.get("provider", "xiaomi_mimo")
        is_active = (active_asr == p_id)
        sub = asr_cfg.get(p_id, {})

        console.print()
        table = Table(title=f"⚙️  {p_name} 全量参数配置面板", border_style="cyan")
        table.add_column("字段说明", style="bold yellow")
        table.add_column("当前配置数值", style="cyan")

        table.add_row("全局激活状态", "[bold green]⚡ 当前全局生效[/bold green]" if is_active else "[dim]未激活[/dim]")

        if p_id == "doubao":
            table.add_row("AppID (必填)", str(sub.get("appid") or "[red](未设置)[/red]"))
            table.add_row("Access Token (必填)", f"{str(sub.get('token', ''))[:4]}****" if sub.get("token") else "[red](未设置)[/red]")
            table.add_row("Cluster ID (选填)", str(sub.get("cluster") or "[dim](默认: volc_auc_common)[/dim]"))
        elif p_id == "xiaomi_mimo":
            key_val = sub.get("api_key") or asr_cfg.get("api_key", "")
            table.add_row("API Key (必填)", f"{str(key_val)[:4]}****" if key_val else "[red](未设置)[/red]")
            table.add_row("Base URL (选填)", str(sub.get("base_url") or "[dim](默认: https://api.xiaomimimo.com/v1)[/dim]"))
            table.add_row("Model (选填)", str(sub.get("model") or "[dim](默认: mimo-v2.5-asr)[/dim]"))
        elif p_id == "qwen":
            key_val = sub.get("api_key") or asr_cfg.get("api_key", "")
            table.add_row("API Key (必填)", f"{str(key_val)[:4]}****" if key_val else "[red](未设置)[/red]")
            table.add_row("Model (选填)", str(sub.get("model") or "[dim](默认: paraformer-realtime-v2)[/dim]"))
        else: # openai
            key_val = sub.get("api_key") or asr_cfg.get("api_key", "")
            table.add_row("API Key (必填)", f"{str(key_val)[:4]}****" if key_val else "[red](未设置)[/red]")
            table.add_row("Base URL (选填)", str(sub.get("base_url") or "[dim](默认: https://api.openai.com/v1)[/dim]"))
            table.add_row("Model (选填)", str(sub.get("model") or "[dim](默认: whisper-1)[/dim]"))

        console.print(table)

        options_panel = "[bold green]1.[/bold green] ⚡ 切换设为当前全局生效的 ASR 服务商\n"
        if p_id == "doubao":
            options_panel += "[bold green]2.[/bold green] ✏️  修改 AppID\n[bold green]3.[/bold green] ✏️  修改 Access Token\n[bold green]4.[/bold green] ✏️  修改 Cluster ID (选填)\n"
        elif p_id == "xiaomi_mimo":
            options_panel += "[bold green]2.[/bold green] ✏️  修改 API Key\n[bold green]3.[/bold green] ✏️  修改 Base URL (选填)\n[bold green]4.[/bold green] ✏️  修改 Model 名称 (选填)\n"
        elif p_id == "qwen":
            options_panel += "[bold green]2.[/bold green] ✏️  修改 API Key\n[bold green]3.[/bold green] ✏️  修改 Model 名称 (选填)\n"
        else: # openai
            options_panel += "[bold green]2.[/bold green] ✏️  修改 API Key\n[bold green]3.[/bold green] ✏️  修改 Base URL (选填)\n[bold green]4.[/bold green] ✏️  修改 Model 名称 (选填)\n"
        
        options_panel += "[bold red]0.[/bold red] 🔙 返回 ASR 服务商列表"
        console.print(options_panel)

        c = Prompt.ask("请选择操作", default="0")

        if c == "0":
            break
        elif c == "1":
            config_set("asr.provider", p_id)
            console.print(f"[bold green]✓ 成功切换 {p_name} 为当前全局 ASR 服务商！[/bold green]")
        elif c == "2":
            if p_id == "doubao":
                v = safe_prompt("请输入豆包 AppID", str(sub.get("appid", "")))
                if v is not None: config_set("asr.doubao.appid", v)
            else:
                v = safe_prompt(f"请输入 {p_name} API Key", str(sub.get("api_key", "")))
                if v is not None: config_set(f"asr.{p_id}.api_key", v)
        elif c == "3":
            if p_id == "doubao":
                v = safe_prompt("请输入豆包 Access Token", str(sub.get("token", "")))
                if v is not None: config_set("asr.doubao.token", v)
            elif p_id == "xiaomi_mimo":
                v = safe_prompt("请输入小米 MiMo Base URL", str(sub.get("base_url", "")))
                if v is not None: config_set("asr.xiaomi_mimo.base_url", v)
            elif p_id == "qwen":
                v = safe_prompt("请输入 Qwen ASR Model", str(sub.get("model", "")))
                if v is not None: config_set("asr.qwen.model", v)
            elif p_id == "openai":
                v = safe_prompt("请输入 OpenAI Base URL", str(sub.get("base_url", "")))
                if v is not None: config_set("asr.openai.base_url", v)
        elif c == "4":
            if p_id == "doubao":
                v = safe_prompt("请输入豆包 Cluster ID", str(sub.get("cluster", "")))
                if v is not None: config_set("asr.doubao.cluster", v)
            elif p_id == "xiaomi_mimo":
                v = safe_prompt("请输入小米 MiMo Model 名称", str(sub.get("model", "")))
                if v is not None: config_set("asr.xiaomi_mimo.model", v)
            elif p_id == "openai":
                v = safe_prompt("请输入 OpenAI Model 名称", str(sub.get("model", "")))
                if v is not None: config_set("asr.openai.model", v)

def interactive_asr_center() -> None:
    """ASR 语音识别服务商管理中心"""
    while True:
        cm = ConfigManager()
        asr_cfg = cm.get("asr", default={})
        active_asr = asr_cfg.get("provider", "xiaomi_mimo")

        table = Table(title="🎙️ ASR 语音识别服务商管理中心", border_style="cyan")
        table.add_column("编号", style="bold yellow", justify="center")
        table.add_column("服务商名称", style="bold white")
        table.add_column("当前激活状态", justify="center")
        table.add_column("密钥与参数配置状态", justify="center")

        for idx, (p_id, p_name) in enumerate(ASR_PROVIDERS, 1):
            is_active = "[bold green]⚡ 已激活[/bold green]" if active_asr == p_id else "[dim]未激活[/dim]"
            status_str = check_asr_provider_status(asr_cfg, p_id)
            table.add_row(str(idx), p_name, is_active, status_str)

        console.print()
        console.print(table)
        console.print("[dim]提示：输入编号 (1-4) 进入对应服务商参数修改或激活设置；输入 0 返回主菜单[/dim]")

        choice = Prompt.ask("请选择操作 [0-4]", choices=["0", "1", "2", "3", "4"], default="0")
        if choice == "0":
            break
        else:
            selected_id, selected_name = ASR_PROVIDERS[int(choice) - 1]
            interactive_asr_detail(selected_id, selected_name)

def interactive_llm_detail(p_id: str, p_name: str) -> None:
    """LLM 供应商详情查看与精细化修改二级菜单"""
    while True:
        cm = ConfigManager()
        llm_cfg = cm.get("llm", default={})
        active_llm = llm_cfg.get("provider", "ollama")
        is_active = (active_llm == p_id)
        sub = llm_cfg.get(p_id, {})

        console.print()
        table = Table(title=f"⚙️  {p_name} 全量参数配置面板", border_style="cyan")
        table.add_column("配置项说明", style="bold yellow")
        table.add_column("当前配置数值", style="cyan")

        table.add_row("全局激活状态", "[bold green]⚡ 当前全局生效[/bold green]" if is_active else "[dim]未激活[/dim]")
        table.add_row("模型名称 (Model)", str(sub.get("model") or "[dim](使用默认预设模型)[/dim]"))

        if p_id not in ["ollama", "local"]:
            key_val = sub.get("api_key") or llm_cfg.get("api_key", "")
            table.add_row("API Key (必填)", f"{str(key_val)[:4]}****" if key_val else "[red](未设置)[/red]")
            table.add_row("Base URL (选填)", str(sub.get("base_url") or "[dim](使用官方默认Endpoint)[/dim]"))
            table.add_row("System Prompt (选填)", "[✓ 已配置自定义 Prompt]" if sub.get("system_prompt") else "[dim](使用系统默认保守纠错 Prompt)[/dim]")

        console.print(table)

        options_panel = "[bold green]1.[/bold green] ⚡ 切换设为当前全局生效的 LLM 服务商\n"
        options_panel += "[bold green]2.[/bold green] ✏️  修改模型名称 (Model)\n"
        if p_id not in ["ollama", "local"]:
            options_panel += "[bold green]3.[/bold green] ✏️  修改 API Key\n"
            options_panel += "[bold green]4.[/bold green] ✏️  修改 Base URL (选填)\n"
            options_panel += "[bold green]5.[/bold green] ✏️  修改 System Prompt (选填)\n"
        
        options_panel += "[bold red]0.[/bold red] 🔙 保存并返回 LLM 服务商列表"
        console.print(options_panel)

        c = Prompt.ask("请选择操作", default="0")

        if c == "0":
            break
        elif c == "1":
            config_set("llm.provider", p_id)
            console.print(f"[bold green]✓ 成功切换 {p_name} 为当前全局 LLM 服务商！[/bold green]")
        elif c == "2":
            v = safe_prompt("请输入模型名称 (Model)", str(sub.get("model", "")))
            if v is not None: config_set(f"llm.{p_id}.model", v)
        elif c == "3" and p_id not in ["ollama", "local"]:
            v = safe_prompt("请输入 API Key", str(sub.get("api_key", "")))
            if v is not None: config_set(f"llm.{p_id}.api_key", v)
        elif c == "4" and p_id not in ["ollama", "local"]:
            v = safe_prompt("请输入 Base URL", str(sub.get("base_url", "")))
            if v is not None: config_set(f"llm.{p_id}.base_url", v)
        elif c == "5" and p_id not in ["ollama", "local"]:
            v = safe_prompt("请输入 System Prompt", str(sub.get("system_prompt", "")))
            if v is not None: config_set(f"llm.{p_id}.system_prompt", v)

def interactive_llm_center() -> None:
    """LLM 文本精修 7 大服务商管理中心"""
    while True:
        cm = ConfigManager()
        llm_cfg = cm.get("llm", default={})
        active_llm = llm_cfg.get("provider", "ollama")

        table = Table(title="🤖 LLM 文本精修服务商管理中心 (7大供应商)", border_style="cyan")
        table.add_column("编号", style="bold yellow", justify="center")
        table.add_column("服务商名称", style="bold white")
        table.add_column("当前激活状态", justify="center")
        table.add_column("模型与密钥配置状态", justify="center")

        for idx, (p_id, p_name) in enumerate(LLM_PROVIDERS, 1):
            is_active = "[bold green]⚡ 已激活[/bold green]" if active_llm == p_id else "[dim]未激活[/dim]"
            status_str = check_llm_provider_status(llm_cfg, p_id)
            table.add_row(str(idx), p_name, is_active, status_str)

        console.print()
        console.print(table)
        console.print("[dim]提示：输入编号 (1-7) 进入对应服务商参数修改或激活设置；输入 0 返回主菜单[/dim]")

        choice = Prompt.ask("请选择操作 [0-7]", choices=["0", "1", "2", "3", "4", "5", "6", "7"], default="0")
        if choice == "0":
            break
        else:
            selected_id, selected_name = LLM_PROVIDERS[int(choice) - 1]
            interactive_llm_detail(selected_id, selected_name)

# --- 全流程录音命令 ---

@app.command("record")
def record(
    duration: Optional[int] = typer.Option(None, "--duration", "-d", help="指定录音秒数 (如果不传则按回车键停止)"),
    raw: bool = typer.Option(False, "--raw", help="纯文本模式输出至 stdout (适用于 UNIX 管道/脚本重定向)"),
    copy: bool = typer.Option(True, "--copy/--no-copy", help="是否将最终精修文本自动写入系统剪贴板")
) -> None:
    """
    【全流程】命令行语音输入体验:
    检测录音设备 -> 启动音频录制 -> 动态 ASCII 音量包络 -> ASR 流式识别 -> LLM 文本精修 -> 自动剪贴板写或 stdout 输出
    """
    cm = ConfigManager()
    engine = CoreEngine(cm)
    injector = TextInjector()

    raw_partial_text = ""
    refined_final_text = ""
    total_captured_bytes = 0

    device_name = AudioRecorder.get_input_device_name()

    def on_partial_asr(text: str, is_final: bool):
        nonlocal raw_partial_text
        raw_partial_text = text
        if not raw:
            console.print(f"[dim]>> ASR Live Preview:[/dim] [cyan]{text}[/cyan]", end="\r")

    engine.event_bus.subscribe(CoreEngine.EVENT_ASR_PARTIAL, on_partial_asr)

    if not raw:
        console.print(Panel(
            f"[bold green]🎤 Voice Input CLI Session Started[/bold green]\n"
            f"• Device: [bold yellow]{device_name}[/bold yellow]\n"
            f"• ASR Provider: [cyan]{cm.get('asr', 'provider', default='xiaomi_mimo')}[/cyan]\n"
            f"• LLM Provider: [cyan]{cm.get('llm', 'provider', default='ollama')}[/cyan]\n"
            + ("[dim]Press ENTER to stop recording...[/dim]" if not duration else f"[dim]Recording for {duration} seconds...[/dim]"),
            border_style="green"
        ))

    engine.start_session()

    audio_recorder = AudioRecorder()

    def on_audio_chunk(chunk: bytes):
        nonlocal total_captured_bytes
        total_captured_bytes += len(chunk)
        engine.process_audio_chunk(chunk)

    def on_volume_change(bars: list):
        if not raw:
            ascii_str = "".join(ASCII_BARS[min(len(ASCII_BARS)-1, int(v * (len(ASCII_BARS)-1)))] for v in bars)
            kb_captured = total_captured_bytes / 1024.0
            console.print(f"[green]Recording...[/green] Audio Level: [{ascii_str}] Sent: {kb_captured:.1f} KB", end="\r")

    def on_audio_error(err_msg: str):
        if not raw:
            console.print(f"\n[bold red]✗ Audio Capture Error:[/bold red] {err_msg}")

    audio_recorder.on_chunk_cb = on_audio_chunk
    audio_recorder.on_volume_cb = on_volume_change
    audio_recorder.on_error_cb = on_audio_error

    audio_recorder.start()

    if duration:
        time.sleep(duration)
    else:
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            pass

    audio_recorder.stop()

    if not raw:
        console.print(f"\n[dim]Microphone captured total {total_captured_bytes / 1024.0:.1f} KB audio PCM data.[/dim]")
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold yellow]Refining text via LLM Engine...[/bold yellow]"),
            transient=True
        ) as progress:
            progress.add_task("refining", total=None)
            refined_final_text = engine.stop_session_and_refine()
    else:
        refined_final_text = engine.stop_session_and_refine()

    if raw:
        sys.stdout.write(refined_final_text)
        sys.stdout.flush()
    else:
        console.print()
        console.print(Panel(
            f"[bold white]{refined_final_text}[/bold white]" if refined_final_text else "[dim](No text recognized)[/dim]",
            title="✨ Refined Output Text",
            border_style="cyan"
        ))

        if copy and refined_final_text.strip():
            injector.inject(refined_final_text)
            console.print("[bold green]✓ Text copied to system clipboard![/bold green]")

# --- 交互式 TUI 主菜单 ---

@app.command("interactive")
def interactive() -> None:
    """启动 Voice Input 交互式 TUI 终端控制台菜单 (Interactive Console)"""
    while True:
        console.print()
        console.print(Panel(
            "[bold cyan]🎤 Voice Input 全功能终端交互控制中心 (TUI Console)[/bold cyan]\n\n"
            "[bold green]1.[/bold green] 🎤 开始全流程语音输入 (Voice Record Session)\n"
            "[bold green]2.[/bold green] 🎙️  ASR 语音识别服务商管理中心 (ASR Provider Center)\n"
            "[bold green]3.[/bold green] 🤖 LLM 文本精修 7 大服务商管理中心 (LLM Provider Center)\n"
            "[bold green]4.[/bold green] 🔍 检查 Backend Daemon 服务健康状态 (Daemon Status)\n"
            "[bold green]5.[/bold green] ⚙️  查看全局系统配置对象 (Show Global Config)\n"
            "[bold green]6.[/bold green] 🔄 触发 WebDAV 配置增量同步 (Sync WebDAV)\n"
            "[bold red]0.[/bold red] 🚪 退出 TUI 控制台",
            title="Interactive Main Menu",
            border_style="cyan"
        ))
        
        choice = Prompt.ask("请选择功能编号", choices=["0", "1", "2", "3", "4", "5", "6"], default="1")

        if choice == "0":
            console.print("[bold yellow]👋 感谢使用 Voice Input CLI，已退出控制台！[/bold yellow]")
            break
        elif choice == "1":
            dur_str = Prompt.ask("请输入录音秒数 (直接按回车则手动按回车停止)", default="")
            dur = int(dur_str) if dur_str.isdigit() else None
            record(duration=dur, raw=False, copy=True)
        elif choice == "2":
            interactive_asr_center()
        elif choice == "3":
            interactive_llm_center()
        elif choice == "4":
            daemon_status()
        elif choice == "5":
            config_show()
        elif choice == "6":
            config_sync()

@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context):
    """当用户直接运行 python -m src.cli.main 且没有提供子命令时，默认唤起交互式菜单"""
    if ctx.invoked_subcommand is None:
        interactive()

def main() -> None:
    app()

if __name__ == "__main__":
    main()
