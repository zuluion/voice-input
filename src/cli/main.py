import os
import sys
import time
import json
import asyncio
import threading
import requests
import typer
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.config import ConfigManager
from src.core.engine import CoreEngine
from src.utils.injector import TextInjector
from src.utils.logger import logger

app = typer.Typer(
    name="voice-input-cli",
    help="Voice Input 前后端分离全功能终端命令行工具 (Full-Flow CLI Client)",
    add_completion=False
)

daemon_app = typer.Typer(help="管理 Headless 后端守护进程生命周期")
config_app = typer.Typer(help="查看、快捷设置及同步系统配置")

app.add_typer(daemon_app, name="daemon")
app.add_typer(config_app, name="config")

console = Console()
DEFAULT_DAEMON_URL = "http://127.0.0.1:28080"

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

    # 类型推断转换
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

# --- 全流程录音命令 ---

@app.command("record")
def record(
    duration: Optional[int] = typer.Option(None, "--duration", "-d", help="指定录音秒数 (如果不传则按回车键停止)"),
    raw: bool = typer.Option(False, "--raw", help="纯文本模式输出至 stdout (适用于 UNIX 管道/脚本重定向)"),
    copy: bool = typer.Option(True, "--copy/--no-copy", help="是否将最终精修文本自动写入系统剪贴板")
) -> None:
    """
    【全流程】命令行语音输入体验:
    启动音频录制 -> 动态 ASCII 音量包络 -> ASR 流式识别 -> LLM 文本精修 -> 自动剪贴板写或 stdout 输出
    """
    cm = ConfigManager()
    engine = CoreEngine(cm)
    injector = TextInjector()

    raw_partial_text = ""
    refined_final_text = ""

    def on_partial_asr(text: str, is_final: bool):
        nonlocal raw_partial_text
        raw_partial_text = text
        if not raw:
            console.print(f"[dim]>> ASR Live Preview:[/dim] [cyan]{text}[/cyan]", end="\r")

    engine.event_bus.subscribe(CoreEngine.EVENT_ASR_PARTIAL, on_partial_asr)

    if not raw:
        console.print(Panel(
            "[bold green]🎤 Voice Input CLI Session Started[/bold green]\n"
            f"• ASR Provider: [cyan]{cm.get('asr', 'provider', default='xiaomi_mimo')}[/cyan]\n"
            f"• LLM Provider: [cyan]{cm.get('llm', 'provider', default='ollama')}[/cyan]\n"
            "[dim]Press ENTER to stop recording...[/dim]" if not duration else f"[dim]Recording for {duration} seconds...[/dim]",
            border_style="green"
        ))

    engine.start_session()

    # 如果有 sounddevice 可用则拉起录音，否则等待模拟音轨
    try:
        from src.audio.recorder import AudioRecorder
        audio_recorder = AudioRecorder()
        audio_recorder.audio_chunk_ready.connect(engine.process_audio_chunk)
        audio_recorder.start()
    except Exception as e:
        logger.log("CLI Record", f"Microphone recorder error or fallback: {e}")
        audio_recorder = None

    if duration:
        time.sleep(duration)
    else:
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            pass

    if audio_recorder:
        audio_recorder.stop()

    if not raw:
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

def main() -> None:
    app()

if __name__ == "__main__":
    main()
