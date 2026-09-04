import asyncio, pytest
from termux_api_stc.core import Executor, ExecutionError, ExecutionTimeoutError

@pytest.mark.asyncio
async def test_async_stdout(env_with):
    _, make=env_with
    make("termux-x","print('ok')")
    r=await Executor().execute_async("termux-x")
    assert r.stdout.strip()==b"ok"

@pytest.mark.asyncio
async def test_async_stdin(env_with):
    _, make=env_with
    make("termux-x","import sys; sys.stdout.buffer.write(sys.stdin.buffer.read())")
    r=await Executor().execute_async("termux-x", input=b"data")
    assert r.stdout==b"data"

@pytest.mark.asyncio
async def test_async_nonzero(env_with):
    _, make=env_with
    make("termux-x","raise SystemExit(9)")
    with pytest.raises(ExecutionError):
        await Executor().execute_async("termux-x")

@pytest.mark.asyncio
async def test_async_timeout(env_with):
    _, make=env_with
    make("termux-x","import time; time.sleep(5)")
    with pytest.raises(ExecutionTimeoutError):
        await Executor().execute_async("termux-x", timeout=0.05)

@pytest.mark.asyncio
async def test_async_cancel_reaps_child(env_with):
    _, make=env_with
    make("termux-x","import time; time.sleep(30)")
    task=asyncio.create_task(Executor().execute_async("termux-x"))
    await asyncio.sleep(0.05)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
