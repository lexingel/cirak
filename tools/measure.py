"""CPU and RAM of a running Çırak (Cirak.exe + its listener) over N seconds. Starts and kills nothing.

    listener/.venv/Scripts/python.exe tools/measure.py [seconds]
"""
import sys
import time

import psutil


def tree():
    """Cirak.exe and the pythonw listener started from its folder (the listener isn't its child:
    a launcher process starts it and exits)."""
    apps = [p for p in psutil.process_iter(["name", "exe"]) if (p.info["name"] or "").lower() == "cirak.exe"]
    roots = {a.info["exe"].rsplit("\\", 1)[0].lower() for a in apps if a.info["exe"]}
    roots |= {r.rsplit("\\", 1)[0] for r in roots}  # a dev build sits in build/, its listener in ../listener
    py = [p for p in psutil.process_iter(["name", "exe"])
          if (p.info["name"] or "").lower() in ("python.exe", "pythonw.exe")
          and any((p.info["exe"] or "").lower().startswith(r + "\\") for r in roots)]
    return apps + py


def main(seconds=60):
    procs = tree()
    if not procs:
        sys.exit("Cirak.exe is not running")
    cores = psutil.cpu_count() or 1
    for p in procs:
        p.cpu_percent(None)  # first call starts the clock
    samples = {p.pid: [] for p in procs}
    for _ in range(seconds):
        time.sleep(1)
        for p in procs:
            try:
                samples[p.pid].append(p.cpu_percent(None) / cores)  # share of the whole CPU
            except psutil.NoSuchProcess:
                pass
    total_ram = 0
    for p in procs:
        s = samples[p.pid] or [0]
        try:
            ram = p.memory_info().rss / 2**20
        except psutil.Error:
            continue  # gone meanwhile
        total_ram += ram
        print(f"{p.info['name']:12} pid {p.pid:6}  cpu avg {sum(s) / len(s):5.2f}%  max {max(s):5.2f}%  ram {ram:6.0f} MB (working set)")
    print(f"total ram {total_ram:.0f} MB over {seconds} s, {cores} logical cores")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 60)
