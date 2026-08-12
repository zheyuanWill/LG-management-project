"""Helpers for running async coroutines from synchronous (Celery) code.

Celery's prefork workers execute tasks in threads that have no running event
loop, so ``asyncio.get_event_loop()`` raises ``RuntimeError``.

The naive fix of ``asyncio.run(coro)`` per task is *also* wrong: ``asyncio.run``
creates and then **closes** a fresh event loop every call, but libraries such as
SQLAlchemy's async engine cache connection-pool sockets bound to the loop they
were first opened on. After the first loop is closed, the next call opens a new
loop and the engine tries to reuse a connection attached to the previous (now
closed) loop -> "Task/Future attached to a different loop" / "Event loop is
closed".

The correct approach is a single **persistent** event loop per thread that is
created lazily and never closed, so every async resource stays bound to the
same loop for the life of the worker process.
"""

import asyncio
import threading

_lock = threading.Lock()
_thread_local = threading.local()


def run_async(coro):
    """Run an async coroutine to completion and return its result.

    Safe to call from any worker thread. Reuses one persistent event loop per
    thread so async resources (DB connection pools, HTTP clients) remain valid
    across repeated invocations.
    """
    loop = getattr(_thread_local, "loop", None)
    if loop is None or loop.is_closed():
        with _lock:
            loop = getattr(_thread_local, "loop", None)
            if loop is None or loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                _thread_local.loop = loop

    if loop.is_running():
        # Loop is currently running in another thread; schedule safely.
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result()

    return loop.run_until_complete(coro)
