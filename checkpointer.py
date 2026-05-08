from pymongo import MongoClient
from langgraph.checkpoint.mongodb import MongoDBSaver
from config import MONGO_URL

_saver = None
_client = None


def init_checkpointer():
    """Call once at app startup. Opens MongoDB connection and creates the saver."""
    global _saver, _client
    _client = MongoClient(MONGO_URL)
    _saver = MongoDBSaver(_client)
    return _saver


def get_checkpointer() -> MongoDBSaver:
    """Returns the shared MongoDB checkpointer. Must call init_checkpointer() first."""
    if _saver is None:
        raise RuntimeError("Checkpointer not initialized. Call init_checkpointer() first.")
    return _saver


def close_checkpointer():
    """Call on app shutdown to close the MongoDB connection."""
    global _client
    if _client:
        _client.close()
