"""Disposable loopback fixture; credentials and paid calls remain disabled."""
import argparse
import tempfile
from pathlib import Path

import uvicorn
from app.main import create_app
from app.engines.mixroute import Settings
from app.storage.database import Store

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8792)
    args = parser.parse_args()
    runtime = Path(__file__).resolve().parents[1] / 'data/runtime'
    runtime.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='browser-repair-', dir=runtime) as directory:
        store = Store(Path(directory) / 'fixture.db')
        uvicorn.run(create_app(store, Settings(enabled=False)), host='127.0.0.1', port=args.port)
