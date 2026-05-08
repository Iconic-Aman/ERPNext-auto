from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

_checkpointer = None


async def get_checkpointer() -> AsyncSqliteSaver:
    """Returns a shared SQLite checkpointer (dev). Swap for Redis in production."""
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = AsyncSqliteSaver.from_conn_string("checkpoints.db")
    return _checkpointer
