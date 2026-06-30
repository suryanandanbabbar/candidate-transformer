import datetime
import json
import os
import shutil
import socket
import subprocess
from pathlib import Path
from typing import Optional

from candidate_transformer.utils.logger import logger

RUNTIME_DIR = Path.home() / ".ctsh" / "runtime"
PID_FILE = RUNTIME_DIR / "server.pid"
DB_FILE = RUNTIME_DIR / "db.json"

class JsonServerManager:
    @classmethod
    def _find_open_port(cls, start_port: int = 3000) -> int:
        port = start_port
        while port < 65535:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('localhost', port)) != 0:
                    return port
            port += 1
        raise RuntimeError("No available ports found.")

    @classmethod
    def _is_process_alive(cls, pid: int) -> bool:
        if os.name == 'nt':
            try:
                # Use tasklist to check for the PID on Windows
                result = subprocess.run(
                    ['tasklist', '/FI', f'PID eq {pid}', '/NH'],
                    capture_output=True, text=True
                )
                return str(pid) in result.stdout
            except Exception:
                return False
        else:
            try:
                os.kill(pid, 0)
                return True
            except ProcessLookupError:
                return False
            except PermissionError:
                return True

    @classmethod
    def _read_metadata(cls) -> Optional[dict]:
        if not PID_FILE.exists():
            return None
        try:
            with open(PID_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return None

    @classmethod
    def status(cls) -> dict:
        meta = cls._read_metadata()
        if not meta:
            return {"status": "Stopped"}

        pid = meta.get("pid")
        if pid and cls._is_process_alive(pid):
            return {
                "status": "Running",
                "workspace": meta.get("workspace"),
                "pid": pid,
                "port": meta.get("port"),
                "started_at": meta.get("started_at")
            }
        else:
            # Cleanup stale pid file
            if PID_FILE.exists():
                PID_FILE.unlink()
            return {"status": "Stopped"}

    @classmethod
    def start(cls, workspace: str) -> dict:
        current_status = cls.status()
        if current_status["status"] == "Running":
            return current_status  # Already running

        if not shutil.which("json-server"):
            raise RuntimeError("json-server is not installed.\n\nInstall it using:\n\nnpm install -g json-server")

        if not DB_FILE.exists():
            raise FileNotFoundError(f"{DB_FILE} not found. Run export first.")

        port = cls._find_open_port(3000)
        
        # Detach the process
        creationflags = 0
        start_new_session = False
        if os.name == 'nt':
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            start_new_session = True

        logger.info("Starting JSON Server")
        
        process = subprocess.Popen(
            ["json-server", DB_FILE.name, "--port", str(port)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=str(RUNTIME_DIR),
            start_new_session=start_new_session,
            creationflags=creationflags
        )
        
        meta = {
            "pid": process.pid,
            "port": port,
            "workspace": workspace,
            "started_at": datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")
        }
        
        with open(PID_FILE, "w") as f:
            json.dump(meta, f, indent=2)
            
        logger.info(f"JSON Server running on port {port}")
        return cls.status()

    @classmethod
    def stop(cls) -> bool:
        meta = cls._read_metadata()
        if not meta:
            return False

        pid = meta.get("pid")
        if not pid or not cls._is_process_alive(pid):
            if PID_FILE.exists():
                PID_FILE.unlink()
            return False

        try:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/F', '/PID', str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                import signal
                os.kill(pid, signal.SIGTERM)
        except Exception:
            pass

        if PID_FILE.exists():
            PID_FILE.unlink()
            
        logger.info("Server stopped")
        return True
