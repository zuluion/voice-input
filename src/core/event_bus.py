import asyncio
import inspect
from typing import Callable, Dict, List, Any, Optional
from src.utils.logger import logger

class EventBus:
    """
    轻量级异步 Pub/Sub 事件总线，解耦系统各模块（UI/Backend Daemon/CLI），
    完全替代 PySide6.QtCore.Signal 的内存消息传递机制。
    """
    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        self._subscribers: Dict[str, List[Callable[..., Any]]] = {}
        self._loop = loop

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def subscribe(self, event_name: str, handler: Callable[..., Any]) -> None:
        """注册事件订阅者"""
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        if handler not in self._subscribers[event_name]:
            self._subscribers[event_name].append(handler)

    def unsubscribe(self, event_name: str, handler: Callable[..., Any]) -> None:
        """取消事件订阅"""
        if event_name in self._subscribers and handler in self._subscribers[event_name]:
            self._subscribers[event_name].remove(handler)

    async def emit_async(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        """异步触发事件广播"""
        handlers = list(self._subscribers.get(event_name, []))
        for handler in handlers:
            try:
                if inspect.iscoroutinefunction(handler):
                    await handler(*args, **kwargs)
                else:
                    handler(*args, **kwargs)
            except Exception as e:
                logger.log("EventBus Exception", f"Error executing async handler for '{event_name}': {e}")

    def emit(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        """同步/线程安全方式触发事件（支持在主线程事件循环或 Worker 线程中发送）"""
        handlers = list(self._subscribers.get(event_name, []))
        for handler in handlers:
            try:
                if inspect.iscoroutinefunction(handler):
                    try:
                        running_loop = self._loop or asyncio.get_running_loop()
                        if running_loop.is_running():
                            asyncio.run_coroutine_threadsafe(handler(*args, **kwargs), running_loop)
                        else:
                            running_loop.run_until_complete(handler(*args, **kwargs))
                    except RuntimeError:
                        asyncio.run(handler(*args, **kwargs))
                else:
                    handler(*args, **kwargs)
            except Exception as e:
                logger.log("EventBus Exception", f"Error executing sync handler for '{event_name}': {e}")
