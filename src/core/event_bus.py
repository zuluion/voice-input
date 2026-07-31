import asyncio
import inspect
from typing import Callable, Dict, List, Any, Optional
from src.utils.logger import logger

class EventBus:
    """
    轻量级异步 Pub/Sub 事件总线，解耦系统各模块（UI/Backend Daemon/CLI），
    支持安全的跨线程/事件循环消息广播。
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
        """同步/线程安全方式触发事件（跨线程提交给绑定的主事件循环）"""
        handlers = list(self._subscribers.get(event_name, []))
        
        target_loop = self._loop
        if not target_loop:
            try:
                target_loop = asyncio.get_running_loop()
            except RuntimeError:
                pass

        for handler in handlers:
            try:
                if inspect.iscoroutinefunction(handler):
                    if target_loop and target_loop.is_running():
                        try:
                            try:
                                curr = asyncio.get_running_loop()
                            except RuntimeError:
                                curr = None
                            if curr is target_loop:
                                target_loop.create_task(handler(*args, **kwargs))
                            else:
                                asyncio.run_coroutine_threadsafe(handler(*args, **kwargs), target_loop)
                        except Exception as exc:
                            import sys
                            sys.stderr.write(f"EventBus emit error: {exc}\n"); sys.stderr.flush()
                    else:
                        try:
                            asyncio.run(handler(*args, **kwargs))
                        except Exception as exc:
                            import sys
                            sys.stderr.write(f"EventBus asyncio.run error: {exc}\n"); sys.stderr.flush()
                else:
                    handler(*args, **kwargs)
            except Exception as e:
                logger.log("EventBus Exception", f"Error executing sync handler for '{event_name}': {e}")

