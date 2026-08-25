#!/usr/bin/env python3
"""朗读录音的声学分析：停顿分布、语速、发声占比。

用法：
    python3 analyze.py 录音.m4a > data.json

依赖：只用标准库 + macOS 自带的 afconvert（转 16k 单声道 wav）。
配套 words.swift 负责转写和逐词时间戳（macOS 26 本机 Speech 框架，离线）。
"""
import array
import json
import math
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

HOP = 0.010          # 帧移 10ms
WIN = 0.025          # 帧长 25ms
MIN_PAUSE = 0.25     # 只统计 250ms 以上的停顿
FLOOR_PCT = 0.10     # 用第 10 百分位当本底噪声
ABOVE_FLOOR_DB = 8   # 高出本底多少 dB 算发声


def to_wav(src: Path) -> Path:
    """afconvert → 16kHz 单声道 wav（已经是 wav 就原样返回）。"""
    if src.suffix.lower() == ".wav":
        return src
    dst = Path(tempfile.mkdtemp()) / "audio.wav"
    subprocess.run(
        ["afconvert", "-f", "WAVE", "-d", "LEI16@16000", "-c", "1", str(src), str(dst)],
        check=True,
    )
    return dst


def envelope(wav: Path):
    """逐帧 RMS → 相对峰值的 dB 曲线。"""
    with wave.open(str(wav)) as w:
        sr, n = w.getframerate(), w.getnframes()
        pcm = array.array("h")
        pcm.frombytes(w.readframes(n))
    hop, win = int(HOP * sr), int(WIN * sr)
    db = []
    for i in range(0, len(pcm) - win, hop):
        acc = sum(pcm[j] * pcm[j] for j in range(i, i + win, 4))  # 每 4 点取 1，够用且快
        db.append(math.sqrt(acc / (win / 4)))
    peak = max(db) or 1.0
    return [20 * math.log10(v / peak + 1e-9) for v in db], n / sr


def find_pauses(db):
    """低于阈值且持续 ≥MIN_PAUSE 的段 = 一次停顿。"""
    floor = sorted(db)[int(len(db) * FLOOR_PCT)]
    thr = max(floor + ABOVE_FLOOR_DB, -40)
    pauses, start = [], None
    for k, d in enumerate(db + [0.0]):          # 末尾补一帧，收掉结尾的静音
        if d < thr and start is None:
            start = k
        elif d >= thr and start is not None:
            if (k - start) * HOP >= MIN_PAUSE:
                pauses.append({"start": round(start * HOP, 2),
                               "end": round(k * HOP, 2),
                               "dur": round((k - start) * HOP, 2)})
            start = None
    return pauses, round(thr, 1)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    db, duration = envelope(to_wav(src))
    pauses, thr = find_pauses(db)
    pause_total = round(sum(p["dur"] for p in pauses), 2)
    speech = round(duration - pause_total, 2)
    json.dump({
        "source": src.name,
        "duration": round(duration, 2),
        "threshold_db": thr,
        "pause_count": len(pauses),
        "pause_total": pause_total,
        "pause_ratio": round(pause_total / duration, 3),
        "speech_time": speech,
        "pauses": pauses,
    }, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
