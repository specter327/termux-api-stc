import asyncio, pytest
from termux_api_stc.core import Executor, ExecutionError, ExecutionTimeoutError

@pytest.mark.asyncio
async def test_stream_lines(env_with):
    _, make=env_with
    make("termux-x","print('a',flush=True); print('b',flush=True)")
    got=[]
    async for line in Executor().stream_lines("termux-x"):
        got.append(line)
    assert got==["a","b"]

@pytest.mark.asyncio
async def test_stream_nonzero(env_with):
    _, make=env_with
    make("termux-x","import sys; print('x',flush=True); sys.stderr.write('bad'); raise SystemExit(3)")
    with pytest.raises(ExecutionError):
        async for _ in Executor().stream_lines("termux-x"):
            pass

@pytest.mark.asyncio
async def test_stream_startup_timeout(env_with):
    _, make=env_with
    make("termux-x","import time; time.sleep(5)")
    with pytest.raises(ExecutionTimeoutError):
        async for _ in Executor().stream_lines("termux-x", startup_timeout=0.05):
            pass

@pytest.mark.asyncio
async def test_stream_cancellation(env_with):
    _, make=env_with
    make("termux-x","import time; print('first',flush=True); time.sleep(30)")
    async def consume():
        async for _ in Executor().stream_lines("termux-x"):
            await asyncio.sleep(0)
    t=asyncio.create_task(consume())
    await asyncio.sleep(0.1)
    t.cancel()
    with pytest.raises(asyncio.CancelledError):
        await t
