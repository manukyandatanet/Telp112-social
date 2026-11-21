"""Procedural background track for promo reels (no licensing issues).
usage: sound.py spec.json out.wav   -> soft pad + gentle pulse + whooshes on scene changes + end chime"""
import sys, json, wave
import numpy as np
spec = json.load(open(sys.argv[1])); SR = 44100
durs = [s['dur'] for s in spec['scenes']]; T = sum(durs) + 0.3; n = int(T * SR); t = np.arange(n) / SR
rng = np.random.default_rng(7)
def env(a, r, length):
    e = np.ones(length); ai = min(int(a * SR), length // 2); ri = min(int(r * SR), length // 2)
    e[:ai] = np.linspace(0, 1, ai); e[-ri:] *= np.linspace(1, 0, ri); return e
out = np.zeros((n, 2))
# pad: Am9 -> Fmaj7 -> C -> G (each 4 beats at 96 bpm)
bpm = 96; beat = 60 / bpm; bar = 4 * beat
chords = [[110, 164.81, 220, 261.63, 329.63], [87.31, 174.61, 220, 261.63, 329.63], [130.81, 196, 261.63, 329.63, 392], [98, 196, 246.94, 293.66, 392]]
k = 0; pos = 0.0
while pos < T:
    a = int(pos * SR); L = min(int(bar * SR) + int(0.6 * SR), n - a)
    if L < 2000: break
    tt = np.arange(L) / SR; e = env(0.5, 0.8, L); sig = np.zeros(L)
    for f in chords[k % 4]:
        sig += np.sin(2 * np.pi * f * tt + 0.3) * 0.6 + np.sin(2 * np.pi * f * 1.003 * tt) * 0.4
    sig = sig / 5 * e * 0.16
    out[a:a + L, 0] += sig; out[a:a + L, 1] += np.roll(sig, 220)
    pos += bar; k += 1
# soft kick + shaker on beats
b = 0.0
while b < T - 1.0:
    a = int(b * SR); L = min(int(0.35 * SR), n - a); tt = np.arange(L) / SR
    kick = np.sin(2 * np.pi * (50 + 70 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 9) * 0.32
    out[a:a + L] += kick[:, None]
    a2 = int((b + beat / 2) * SR); L2 = min(int(0.06 * SR), n - a2)
    if L2 > 0:
        sh = rng.standard_normal(L2) * np.exp(-np.arange(L2) / SR * 60) * 0.035
        sh = np.diff(np.concatenate([[0], sh]))
        out[a2:a2 + L2, 0] += sh; out[a2:a2 + L2, 1] += sh * 0.7
    b += beat
# whoosh at each scene change
acc = 0.0
for d in durs[:-1]:
    acc += d; c = acc - 0.25; a = max(0, int(c * SR)); L = int(0.5 * SR); L = min(L, n - a)
    nz = rng.standard_normal(L); w = np.sin(np.linspace(0, np.pi, L)) ** 2
    lp = np.convolve(nz, np.ones(30) / 30, mode='same') * w * 0.22
    out[a:a + L, 0] += lp * np.linspace(1, .4, L); out[a:a + L, 1] += lp * np.linspace(.4, 1, L)
# end chime
c = sum(durs[:-1]) + 0.2; a = int(c * SR); L = min(int(2.5 * SR), n - a); tt = np.arange(L) / SR
ch = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * 2.2) for f in [523.25, 659.25, 783.99, 1046.5]) * 0.07
out[a:a + L] += ch[:, None]
fade = int(1.0 * SR); out[-fade:] *= np.linspace(1, 0, fade)[:, None]; out[:int(0.05 * SR)] *= np.linspace(0, 1, int(0.05 * SR))[:, None]
out = out / max(1e-9, np.abs(out).max()) * 0.7
with wave.open(sys.argv[2], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())
