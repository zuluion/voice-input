import asyncio
from src.core.event_bus import EventBus

def test_event_bus_subscribe_and_emit_async():
    async def _run():
        bus = EventBus()
        received_data = []

        async def async_handler(data: str):
            received_data.append(f"async:{data}")

        def sync_handler(data: str):
            received_data.append(f"sync:{data}")

        bus.subscribe("test_event", async_handler)
        bus.subscribe("test_event", sync_handler)

        await bus.emit_async("test_event", "hello")

        assert "async:hello" in received_data
        assert "sync:hello" in received_data

    asyncio.run(_run())

def test_event_bus_unsubscribe():
    async def _run():
        bus = EventBus()
        received = []

        def handler(val: int):
            received.append(val)

        bus.subscribe("count", handler)
        await bus.emit_async("count", 1)
        assert received == [1]

        bus.unsubscribe("count", handler)
        await bus.emit_async("count", 2)
        assert received == [1]

    asyncio.run(_run())

def test_event_bus_exception_isolation():
    async def _run():
        bus = EventBus()
        success_called = False

        def bad_handler():
            raise ValueError("Simulated handler crash")

        def good_handler():
            nonlocal success_called
            success_called = True

        bus.subscribe("error_event", bad_handler)
        bus.subscribe("error_event", good_handler)

        await bus.emit_async("error_event")
        assert success_called is True

    asyncio.run(_run())
