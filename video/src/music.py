"""Original BGM + sound effects for the JOB HUNT promo, synthesized from scratch.

No samples or third-party music are used, so there are no licensing issues.
120 BPM (1 beat = 0.5 s, 1 bar = 2 s); events are aligned with promo.html's timeline.

usage: python3 music.py out.wav
"""
import sys
import numpy as np
from scipy import signal
import pyloudnorm as pyln

SR = 44100
DUR = 36.0
N = int(DUR * SR)
BEAT = 0.5
BAR = 2.0
rng = np.random.default_rng(20261110)


# ---------------------------------------------------------------- helpers
def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tt(dur):
    return np.arange(int(dur * SR)) / SR


def sos(kind, f, order=2):
    return signal.butter(order, f, kind, fs=SR, output='sos')


def filt(x, kind, f, order=2):
    return signal.sosfilt(sos(kind, f, order), x)


def fade(x, a=0.002, r=0.005):
    x = x.copy()
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    x[:na] *= np.linspace(0, 1, na)
    x[-nr:] *= np.linspace(1, 0, nr)
    return x


_tables = {}


def saw_table(k):
    if k not in _tables:
        ph = np.arange(4096) / 4096
        tb = np.zeros(4096)
        for h in range(1, k + 1):
            tb += np.sin(2 * np.pi * h * ph) / h
        _tables[k] = tb * (2 / np.pi)
    return _tables[k]


def osc_saw(f, n, phase=0.0):
    """Band-limited sawtooth via wavetable."""
    k = int(max(1, min(60, 15000 / f)))
    tb = saw_table(k)
    ph = (phase + f * np.arange(n) / SR) % 1.0
    idx = ph * 4096
    i0 = idx.astype(int)
    fr = idx - i0
    return tb[i0] * (1 - fr) + tb[(i0 + 1) % 4096] * fr


class Bus:
    def __init__(self):
        self.x = np.zeros((2, N))

    def add(self, sig, t, gain=1.0, pan=0.0):
        i = int(round(t * SR))
        if i >= N:
            return
        if sig.ndim == 1:
            a = (pan + 1) * np.pi / 4
            sig = np.stack([sig * np.cos(a), sig * np.sin(a)]) * np.sqrt(2)
        n = min(sig.shape[1], N - i)
        if i < 0:
            sig, n, i = sig[:, -i:], min(sig.shape[1] + i, N), 0
        self.x[:, i:i + n] += sig[:, :n] * gain


drums, bass_bus, music, sfx, send = Bus(), Bus(), Bus(), Bus(), Bus()

# ---------------------------------------------------------------- instruments
def kick():
    t = tt(0.5)
    f = 46 + 150 * np.exp(-t / 0.032)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.17)
    click = filt(rng.standard_normal(len(t)), 'lowpass', 4000) * np.exp(-t / 0.004) * 0.35
    s = np.tanh(1.6 * (body + click)) / np.tanh(1.6)
    return fade(s, 0.0005, 0.02)


def clap():
    t = tt(0.4)
    nz = filt(rng.standard_normal(len(t)), 'bandpass', [900, 3200])
    env = np.zeros_like(t)
    for d in (0.0, 0.010, 0.021):
        env += (t >= d) * np.exp(-np.clip(t - d, 0, None) / 0.005)
    env += (t >= 0.03) * np.exp(-np.clip(t - 0.03, 0, None) / 0.11) * 0.8
    body = np.sin(2 * np.pi * 185 * t) * np.exp(-t / 0.04) * 0.35
    return fade(nz * env * 0.9 + body, 0.0005, 0.02)


def hat(open_=False):
    t = tt(0.45 if open_ else 0.08)
    nz = filt(rng.standard_normal(len(t)), 'highpass', 7000, 4)
    return fade(nz * np.exp(-t / (0.16 if open_ else 0.022)), 0.0005, 0.01)


def crash(dur=2.6):
    t = tt(dur)
    out = []
    for _ in range(2):
        nz = filt(rng.standard_normal(len(t)), 'highpass', 3800, 2)
        sh = filt(rng.standard_normal(len(t)), 'bandpass', [6000, 11000]) * 0.5
        out.append((nz + sh) * np.exp(-t / 0.85))
    return np.stack([fade(o, 0.002, 0.2) for o in out])


def boom(dur=1.4):
    t = tt(dur)
    f = 36 + 90 * np.exp(-t / 0.06)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.45)
    nz = filt(rng.standard_normal(len(t)), 'lowpass', 500) * np.exp(-t / 0.12) * 0.6
    return fade(np.tanh(1.4 * (s + nz)), 0.001, 0.2)


def pluck_chord(notes, dur=0.45):
    """Detuned-saw chord stab with a decaying filter envelope (bright -> dark)."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    L = np.zeros(n)
    R = np.zeros(n)
    for j, m in enumerate(notes):
        f = mtof(m)
        for d, pan in ((-9, -0.6), (0, 0.0), (9, 0.6)):
            v = osc_saw(f * 2 ** (d / 1200), n, phase=rng.random())
            a = (pan + 1) * np.pi / 4
            L += v * np.cos(a)
            R += v * np.sin(a)
    ef = np.exp(-t / 0.09)
    env = np.exp(-t / 0.22)
    out = []
    for ch in (L, R):
        bright = filt(ch, 'lowpass', 6500)
        dark = filt(ch, 'lowpass', 900)
        out.append(fade((bright * ef + dark * (1 - ef)) * env, 0.002, 0.03))
    return np.stack(out) / (3 * len(notes)) * 1.6


def pad(notes, dur, cutoff=2400):
    n = int(dur * SR)
    t = np.arange(n) / SR
    L = np.zeros(n)
    R = np.zeros(n)
    for m in notes:
        f = mtof(m)
        for d, pan in ((-16, -0.9), (-6, -0.3), (0, 0), (6, 0.3), (16, 0.9)):
            v = osc_saw(f * 2 ** (d / 1200), n, phase=rng.random())
            a = (pan + 1) * np.pi / 4
            L += v * np.cos(a)
            R += v * np.sin(a)
    env = np.minimum(1, t / 0.12) * np.minimum(1, (dur - t) / 0.25).clip(0, 1)
    return np.stack([filt(L, 'lowpass', cutoff) * env, filt(R, 'lowpass', cutoff) * env]) / (5 * len(notes))


def bass_note(m, dur=0.23):
    t = tt(dur)
    f = mtof(m)
    s = filt(osc_saw(f, len(t)), 'lowpass', 700) * 0.7 + np.sin(2 * np.pi * f * t) * 0.6
    env = np.minimum(1, t / 0.004) * np.exp(-t / 0.35)
    return fade(s * env, 0.002, 0.03)


def arp_note(m, dur=0.16):
    t = tt(dur)
    f = mtof(m)
    s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.03)
    return fade(s * np.exp(-t / 0.07), 0.001, 0.02)


def tv_filter(x, fc, kind='bandpass', q=1.0):
    """Time-varying filter via STFT overlap-add. fc: array of centre/cutoff Hz per sample."""
    nfft, hop = 2048, 512
    win = np.hanning(nfft)
    pad_x = np.concatenate([np.zeros(nfft), x, np.zeros(nfft)])
    fcp = np.concatenate([np.full(nfft, fc[0]), fc, np.full(nfft, fc[-1])])
    out = np.zeros_like(pad_x)
    norm = np.zeros_like(pad_x)
    freqs = np.fft.rfftfreq(nfft, 1 / SR)
    for s in range(0, len(pad_x) - nfft, hop):
        seg = pad_x[s:s + nfft] * win
        c = fcp[s + nfft // 2]
        if kind == 'bandpass':
            g = np.exp(-0.5 * (np.log2(np.maximum(freqs, 1) / c) / (0.7 * q)) ** 2)
        else:  # highpass
            g = 1 / (1 + (c / np.maximum(freqs, 1)) ** 4)
        out[s:s + nfft] += np.fft.irfft(np.fft.rfft(seg) * g) * win
        norm[s:s + nfft] += win ** 2
    out = out / np.maximum(norm, 1e-6)
    return out[nfft:nfft + len(x)]


def whoosh(dur=0.55, pan_from=0.8, pan_to=-0.8):
    n = int(dur * SR)
    t = np.arange(n) / SR
    p = t / dur
    fc = 350 + 2600 * np.sin(np.pi * np.clip(p / 0.75, 0, 1) * 0.5) ** 2 * (1 - 0.6 * np.clip((p - 0.75) / 0.25, 0, 1))
    nz = tv_filter(rng.standard_normal(n), fc, 'bandpass', 0.8)
    env = np.where(p < 0.65, (p / 0.65) ** 2, ((1 - p) / 0.35) ** 1.5)
    s = nz * env
    pan = pan_from + (pan_to - pan_from) * p
    a = (pan + 1) * np.pi / 4
    return np.stack([s * np.cos(a), s * np.sin(a)]) * 1.4


def riser(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    p = t / dur
    nz = tv_filter(rng.standard_normal(n), 300 * (30 ** p), 'highpass')
    sweep = np.sin(2 * np.pi * np.cumsum(220 * 2 ** (2.2 * p)) / SR) * 0.25
    s = (nz + sweep) * p ** 2.2
    return fade(s, 0.01, 0.01)


def pop(f0=520, f1=1150):
    t = tt(0.16)
    f = f1 + (f0 - f1) * np.exp(-t / 0.018)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.05)
    return fade(s, 0.0008, 0.02)


def tick(f):
    t = tt(0.12)
    s = (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 2 * f * t)) * np.exp(-t / 0.04)
    return fade(s, 0.0008, 0.02)


# ---------------------------------------------------------------- harmony
# A minor / C major: Am - F - C - G per bar, final bar resolves on C.
CHORDS = [
    dict(stab=[57, 60, 64, 69], pad=[57, 60, 64], bass=45),  # Am
    dict(stab=[57, 60, 65, 69], pad=[53, 57, 60], bass=41),  # F
    dict(stab=[55, 60, 64, 67], pad=[55, 60, 64], bass=48),  # C
    dict(stab=[55, 59, 62, 67], pad=[55, 59, 62], bass=43),  # G
]
FINAL = dict(stab=[60, 64, 67, 72, 74], pad=[48, 55, 60, 64, 67], bass=36)
ARP_STEPS = [0, 1, 2, 3, 2, 1, 2, 3, 0, 1, 2, 3, 2, 3, 1, 2]

kick_times = []

for b in range(18):
    t0 = b * BAR
    ch = FINAL if b == 17 else CHORDS[b % 4]

    # --- pads
    if b <= 1:
        music.add(pad(ch['pad'], BAR + 0.1, cutoff=700 if b == 0 else 1500), t0, 0.9)
    elif b < 17:
        music.add(pad(ch['pad'], BAR + 0.05, cutoff=2600), t0, 0.55)
    else:
        music.add(pad(ch['pad'], 2.0, cutoff=3200), t0, 1.0)

    if b == 17:
        music.add(pluck_chord(ch['stab'], 1.8), t0, 0.9)
        send.add(pluck_chord(ch['stab'], 1.8), t0, 0.5)
        bass_bus.add(bass_note(ch['bass'], 1.8), t0, 1.0)
        continue

    main = 2 <= b <= 16
    build = b == 13
    for beat in range(4):
        tb = t0 + beat * BEAT
        # kick: main groove, dropped in the last 2 beats of the build
        if main and not (build and beat >= 2):
            drums.add(kick(), tb, 1.0)
            kick_times.append(tb)
        # clap on 2 & 4
        if main and beat in (1, 3) and not build:
            drums.add(clap(), tb, 0.5, 0.05)
            send.add(clap(), tb, 0.25)
        # closed hats on the offbeat (intro bar 1 onwards)
        if b >= 1:
            drums.add(hat(), tb + BEAT / 2, 0.22 if main else 0.14, 0.25)
        # 16th hats in the B section
        if 6 <= b <= 16 and not build:
            drums.add(hat(), tb + BEAT / 4, 0.07, -0.3)
            drums.add(hat(), tb + 3 * BEAT / 4, 0.07, -0.3)
        if main and beat == 3 and not build:
            drums.add(hat(True), tb + BEAT / 2, 0.12, 0.3)
        # offbeat bass
        if main and not (build and beat >= 2):
            bass_bus.add(bass_note(ch['bass']), tb + BEAT / 2, 0.9)
            if beat in (1, 3):
                bass_bus.add(bass_note(ch['bass'] + 12, 0.12), tb + 3 * BEAT / 4, 0.35)

    # chord stabs (syncopated 16th pattern)
    if main and not build:
        for s16 in (0, 3, 6, 10, 12):
            ts = t0 + s16 * BEAT / 4
            music.add(pluck_chord(ch['stab'], 0.4), ts, 0.55)
            send.add(pluck_chord(ch['stab'], 0.4), ts, 0.18)

    # arpeggio from bar 4
    if 4 <= b <= 16 and not build:
        tones = [m + 12 for m in ch['stab']]
        for k, step in enumerate(ARP_STEPS):
            ta = t0 + k * BEAT / 4
            pan = -0.5 if k % 2 == 0 else 0.5
            music.add(arp_note(tones[step % len(tones)]), ta, 0.12, pan)
            send.add(arp_note(tones[step % len(tones)]), ta, 0.05, pan)

# build-up snare roll (26 -> 28 s)
for k in range(24):
    p = k / 24
    tr = 26.0 + 2.0 * (1 - (1 - p) ** 1.6)
    drums.add(clap(), tr, 0.12 + 0.45 * p, 0.0)

# ---------------------------------------------------------------- sound effects (aligned to visuals)
sfx.add(riser(2.0), 2.0, 0.35)
sfx.add(riser(2.0), 26.0, 0.40)
sfx.add(boom(), 0.62, 0.55)                       # flag lands
for i, f in enumerate([660, 784, 880]):          # J O B
    sfx.add(tick(f), 0.68 + i * 0.07, 0.16, -0.3)
for i, f in enumerate([988, 1175, 1319, 1568]):  # H U N T
    sfx.add(tick(f), 0.93 + i * 0.07, 0.16, 0.3)
sfx.add(pop(), 1.86, 0.30)                        # pill
sfx.add(whoosh(0.5, 0, 0), 3.5, 0.45)             # circle reveal
sfx.add(crash(), 4.0, 0.30)
sfx.add(boom(), 5.22, 0.55)                       # 「誰と働くか」 punch
sfx.add(crash(1.6), 5.22, 0.15)
sfx.add(pop(), 6.78, 0.28, 0.5)                   # badge
sfx.add(whoosh(), 7.45, 0.50)                     # swipe
for t in (8.28, 11.28, 14.28):                    # feature icons
    sfx.add(pop(480, 1000), t, 0.30, -0.3)
for t in (10.62, 13.62):                          # feature change
    sfx.add(whoosh(0.4, 0.5, -0.5), t, 0.22)
sfx.add(whoosh(), 16.45, 0.50)                    # swipe
for i in range(6):                                # timeline items
    sfx.add(tick([784, 880, 988, 1175, 1319, 1568][i]), 17.66 + i * 0.5, 0.18, -0.5 + i * 0.2)
sfx.add(pop(), 20.68, 0.30, 0.5)                  # sticker
sfx.add(whoosh(), 22.45, 0.50)                    # swipe
for i, t in enumerate((23.58, 24.48, 25.38)):     # voice cards
    sfx.add(pop(500 + i * 60, 1100 + i * 120), t, 0.28, -0.5 + i * 0.5)
sfx.add(whoosh(0.5, 0, 0), 27.5, 0.40)            # circle reveal
sfx.add(crash(), 28.0, 0.34)
sfx.add(boom(), 28.0, 0.50)
sfx.add(boom(), 29.16, 0.45)                      # 「ここから変わる」 punch
sfx.add(whoosh(0.45, -0.2, 0.2), 30.2, 0.20)      # card slides up
sfx.add(pop(), 31.58, 0.30, 0.3)                  # QR
sfx.add(crash(3.0), 34.0, 0.34)
sfx.add(boom(2.0), 34.0, 0.55)

# ---------------------------------------------------------------- mix
# sidechain ducking driven by the kick
duck = np.ones(N)
curve_t = np.arange(int(0.3 * SR)) / SR
curve = 1 - 0.55 * np.minimum(1, curve_t / 0.003) * np.exp(-curve_t / 0.09)
for kt in kick_times:
    i = int(kt * SR)
    n = min(len(curve), N - i)
    duck[i:i + n] = np.minimum(duck[i:i + n], curve[:n])
music.x *= duck
bass_bus.x *= 0.5 + 0.5 * duck

# reverb send: decorrelated exponentially-decaying noise IR
ir_t = np.arange(int(1.6 * SR)) / SR
ir = []
for _ in range(2):
    h = rng.standard_normal(len(ir_t)) * np.exp(-ir_t / 0.38)
    h = filt(h, 'lowpass', 6000)
    h[: int(0.012 * SR)] = 0
    ir.append(h / np.sqrt(np.sum(h ** 2)))
rev = np.stack([signal.fftconvolve(send.x[c], ir[c])[:N] for c in range(2)])

mix = drums.x * 0.85 + bass_bus.x * 0.75 + music.x * 0.8 + sfx.x * 0.9 + rev * 0.35
mix = np.stack([filt(mix[c], 'highpass', 28) for c in range(2)])

# fade out the last 1.2 s
fo = int(1.2 * SR)
mix[:, -fo:] *= np.linspace(1, 0, fo) ** 2

# loudness: -14 LUFS (typical for web/SNS video), soft-limited peaks
meter = pyln.Meter(SR)
loud = meter.integrated_loudness(mix.T)
mix *= 10 ** ((-14.0 - loud) / 20)
ceiling = 10 ** (-1.2 / 20)
mix = np.tanh(mix / ceiling) * ceiling
final_loud = meter.integrated_loudness(mix.T)

out = sys.argv[1] if len(sys.argv) > 1 else 'bgm.wav'
pcm = (np.clip(mix.T, -1, 1) * 32767).astype(np.int16)
from scipy.io import wavfile
wavfile.write(out, SR, pcm)
print(f'wrote {out}: {DUR}s, integrated {final_loud:.1f} LUFS, peak {20*np.log10(np.abs(mix).max()):.1f} dBFS')
