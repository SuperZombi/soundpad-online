import numpy as np
from scipy.signal import lfilter
from pitch_shifter import pitch_shift


class StreamingPitchShifter:
    def __init__(
        self,
        sr: int,
        n_steps: float,
        chunk_size: int,
        history_chunks: int = 4,
        **pitch_kwargs,
    ):
        self.sr = sr
        self.n_steps = n_steps
        self.chunk_size = chunk_size
        self.pitch_kwargs = pitch_kwargs

        self.history = np.zeros(chunk_size * history_chunks, dtype=np.float32)

        self.crossfade_len = max(1, chunk_size // 2)
        self.prev_tail = np.zeros(self.crossfade_len, dtype=np.float32)

        fade = np.linspace(0.0, 1.0, self.crossfade_len, dtype=np.float32)
        self._fade_in = fade
        self._fade_out = 1.0 - fade

    def process(self, chunk: np.ndarray) -> np.ndarray:
        if chunk.dtype != np.float32:
            chunk = chunk.astype(np.float32)

        window = np.concatenate([self.history, chunk])

        shifted = pitch_shift(
            window, sr=self.sr, n_steps=self.n_steps, **self.pitch_kwargs
        )

        out_chunk = np.asarray(shifted[-self.chunk_size:], dtype=np.float32).copy()

        n = self.crossfade_len
        out_chunk[:n] = out_chunk[:n] * self._fade_in + self.prev_tail * self._fade_out
        self.prev_tail = out_chunk[-n:].copy()

        self.history = window[-self.history.shape[0]:]

        return out_chunk

    def reset(self) -> None:
        self.history[:] = 0
        self.prev_tail[:] = 0


class CaveReverb:
    _COMB_DELAYS_MS = (29.7, 37.1, 41.1, 43.7)
    _COMB_FEEDBACK = 0.78
    _ALLPASS_DELAYS_MS = (5.0, 1.7)
    _ALLPASS_FEEDBACK = 0.5

    def __init__(self, sr: int, wet: float = 0.35, lowpass_alpha: float = 0.2):
        self.sr = sr
        self.wet = wet

        self._comb_filters = []
        for ms in self._COMB_DELAYS_MS:
            n = max(1, int(sr * ms / 1000))
            b = np.array([1.0])
            a = np.zeros(n + 1)
            a[0] = 1.0
            a[n] = -self._COMB_FEEDBACK
            self._comb_filters.append([b, a, np.zeros(n)])

        self._allpass_filters = []
        for ms in self._ALLPASS_DELAYS_MS:
            n = max(1, int(sr * ms / 1000))
            g = self._ALLPASS_FEEDBACK
            b = np.zeros(n + 1)
            b[0] = -g
            b[n] = 1.0
            a = np.zeros(n + 1)
            a[0] = 1.0
            a[n] = -g
            self._allpass_filters.append([b, a, np.zeros(n)])

        self._lp_b = np.array([lowpass_alpha])
        self._lp_a = np.array([1.0, -(1.0 - lowpass_alpha)])
        self._lp_zi = np.zeros(1)

    def process(self, chunk: np.ndarray) -> np.ndarray:
        x = chunk.astype(np.float64)

        wet = np.zeros_like(x)
        for f in self._comb_filters:
            b, a, zi = f
            y, zf = lfilter(b, a, x, zi=zi)
            f[2] = zf
            wet += y
        wet /= len(self._comb_filters)

        for f in self._allpass_filters:
            b, a, zi = f
            wet, zf = lfilter(b, a, wet, zi=zi)
            f[2] = zf

        wet, self._lp_zi = lfilter(self._lp_b, self._lp_a, wet, zi=self._lp_zi)

        out = x * (1.0 - self.wet) + wet * self.wet
        return out.astype(np.float32)

    def reset(self) -> None:
        for f in self._comb_filters:
            f[2][:] = 0
        for f in self._allpass_filters:
            f[2][:] = 0
        self._lp_zi[:] = 0


def make_child(sr, chunk_size):
    return StreamingPitchShifter(sr=sr, n_steps=8, chunk_size=chunk_size)

def make_man(sr, chunk_size):
    return StreamingPitchShifter(sr=sr, n_steps=-5, chunk_size=chunk_size)

def make_cave(sr, chunk_size):
    return CaveReverb(sr=sr, wet=0.45)

EFFECTS = {
    "child": make_child,
    "man": make_man,
    "cave": make_cave,
}
