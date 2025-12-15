"""
Helper launcher to start GPT-SoVITS TTS server and the local proxy together.

Requirements:
- You have already cloned https://github.com/RVC-Boss/GPT-SoVITS.git
- You installed its dependencies and downloaded the required models.
- FFmpeg and (optionally) CUDA stack are set up if you want GPU.

Defaults:
- GPT-SoVITS repo at ../GPT-SoVITS relative to this project (override with env GPT_SOVITS_PATH)
- TTS API on port 9880
- Proxy on port 8001

Usage (from project root):
  python scripts/run_tts_stack.py

Stop with Ctrl+C; the script will terminate both child processes.
"""
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent.parent
    gpt_path = Path(os.getenv("GPT_SOVITS_PATH", root.parent / "GPT-SoVITS")).resolve()

    if not gpt_path.exists():
        print(f"[!] GPT-SoVITS path not found: {gpt_path}")
        print("    Clone it with: git clone https://github.com/RVC-Boss/GPT-SoVITS.git ../GPT-SoVITS")
        sys.exit(1)

    # Commands
    tts_cmd = [sys.executable, "api.py", "--host", "0.0.0.0", "--port", "9880"]
    proxy_cmd = [sys.executable, "-m", "uvicorn", "server.tts_proxy:app", "--port", "8001", "--host", "0.0.0.0"]

    env = os.environ.copy()

    procs = []
    try:
        print(f"[*] Starting GPT-SoVITS API in {gpt_path} ...")
        procs.append(
            subprocess.Popen(
                tts_cmd,
                cwd=gpt_path,
                env=env,
            )
        )

        print(f"[*] Starting local proxy (8001) in {root} ...")
        procs.append(
            subprocess.Popen(
                proxy_cmd,
                cwd=root,
                env=env,
            )
        )

        print("\nEverything started. Endpoints:")
        print("  GPT-SoVITS: http://127.0.0.1:9880/tts")
        print("  Proxy:      http://127.0.0.1:8001/tts\n")
        print("Press Ctrl+C to stop both.")

        # Wait on child processes; if one exits, terminate the other.
        while True:
            for p in list(procs):
                code = p.poll()
                if code is not None:
                    raise RuntimeError(f"Process {p.args} exited with code {code}")
            # simple wait loop
            if hasattr(signal, "pause"):
                try:
                    signal.pause()
                except KeyboardInterrupt:
                    raise
            else:
                time.sleep(1)

    except KeyboardInterrupt:
        print("\n[!] Stopping...")
    except Exception as exc:  # noqa: BLE001
        print(f"\n[!] Error: {exc}")
    finally:
        for p in procs:
            if p.poll() is None:
                try:
                    p.terminate()
                except Exception:
                    pass
        for p in procs:
            try:
                p.wait(timeout=5)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass


if __name__ == "__main__":
    main()

