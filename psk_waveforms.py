import os
from typing import Dict, Tuple

import numpy as np
import matplotlib.pyplot as plt


def generate_mpsk_waveform(
	M: int,
	num_symbols: int = 64,
	samples_per_symbol: int = 20,
	carrier_frequency_hz: float = 3000.0,
	symbol_rate_baud: float = 1000.0,
	phase_offset_rad: float | None = None,
	random_seed: int = 0,
) -> Dict[str, np.ndarray]:
	"""
	Generate a passband waveform for M-PSK with rectangular pulse shaping.

	Returns a dict containing time vector `t`, passband signal `s`, baseband `i` and `q`,
	and metadata including `fs`, `Rs`, `fc`, `M`, `symbols`, and `phases`.
	"""
	if M < 2 or (M & (M - 1)) != 0:
		raise ValueError("M must be a power of two and at least 2 (e.g., 2, 4, 8, 16)")
	if samples_per_symbol % 2 != 0:
		raise ValueError("samples_per_symbol must be even to support OQPSK comparisons")

	# Defaults: use 0 for BPSK and pi/M for conventional offset on higher-order PSK
	if phase_offset_rad is None:
		phase_offset_rad = 0.0 if M == 2 else (np.pi / M)

	RNG = np.random.default_rng(random_seed)
	symbols = RNG.integers(low=0, high=M, size=num_symbols, endpoint=False)
	# Natural mapping; could switch to Gray if desired for BER analysis
	phases = 2.0 * np.pi * symbols / M + phase_offset_rad

	# Rectangular (NRZ) pulse shaping at baseband
	complex_symbols = np.exp(1j * phases)  # unit magnitude
	i_bb = np.repeat(np.real(complex_symbols), samples_per_symbol)
	q_bb = np.repeat(np.imag(complex_symbols), samples_per_symbol)

	Rs = float(symbol_rate_baud)
	fc = float(carrier_frequency_hz)
	fs = samples_per_symbol * Rs
	N = num_symbols * samples_per_symbol
	t = np.arange(N) / fs

	# Quadrature modulation to passband
	carrier_cos = np.cos(2.0 * np.pi * fc * t)
	carrier_sin = np.sin(2.0 * np.pi * fc * t)
	# s(t) = I(t) cos(2πf_ct) - Q(t) sin(2πf_ct)
	s_passband = i_bb * carrier_cos - q_bb * carrier_sin

	return {
		"t": t,
		"s": s_passband,
		"i": i_bb,
		"q": q_bb,
		"fs": np.array([fs]),
		"Rs": np.array([Rs]),
		"fc": np.array([fc]),
		"M": np.array([M]),
		"symbols": symbols,
		"phases": phases,
	}


def generate_oqpsk_waveform(
	num_symbols: int = 64,
	samples_per_symbol: int = 20,
	carrier_frequency_hz: float = 3000.0,
	symbol_rate_baud: float = 1000.0,
	random_seed: int = 1,
) -> Dict[str, np.ndarray]:
	"""
	Generate an OQPSK (Offset QPSK) passband waveform.

	I and Q are NRZ ±1 streams with the Q branch delayed by T/2.
	"""
	if samples_per_symbol % 2 != 0:
		raise ValueError("samples_per_symbol must be even for OQPSK")

	RNG = np.random.default_rng(random_seed)
	# I and Q symbol streams are independent ±1
	i_symbols = 2 * RNG.integers(0, 2, size=num_symbols, endpoint=False) - 1
	q_symbols = 2 * RNG.integers(0, 2, size=num_symbols, endpoint=False) - 1

	i_bb = np.repeat(i_symbols, samples_per_symbol)
	q_bb_no_delay = np.repeat(q_symbols, samples_per_symbol)

	# Delay Q by T/2 (half-symbol): prepend half-symbol of first Q level and truncate tail
	half = samples_per_symbol // 2
	q_lead = np.repeat(q_symbols[0], half)
	q_bb = np.concatenate([q_lead, q_bb_no_delay[:-half]])

	Rs = float(symbol_rate_baud)
	fc = float(carrier_frequency_hz)
	fs = samples_per_symbol * Rs
	N = num_symbols * samples_per_symbol
	t = np.arange(N) / fs

	carrier_cos = np.cos(2.0 * np.pi * fc * t)
	carrier_sin = np.sin(2.0 * np.pi * fc * t)
	s_passband = i_bb * carrier_cos - q_bb * carrier_sin

	return {
		"t": t,
		"s": s_passband,
		"i": i_bb,
		"q": q_bb,
		"fs": np.array([fs]),
		"Rs": np.array([Rs]),
		"fc": np.array([fc]),
		"M": np.array([4]),  # Underlying constellation is QPSK
		"symbols": None,
		"phases": None,
	}


def _ensure_output_dir(out_dir: str) -> None:
	if not os.path.isdir(out_dir):
		os.makedirs(out_dir, exist_ok=True)


def plot_passband_comparison(
	results: Dict[str, Dict[str, np.ndarray]],
	out_dir: str,
	max_symbols_to_show: int = 10,
) -> Tuple[str, str]:
	"""
	Create comparison plots of time-domain passband waveforms.

	Returns the saved file paths for the stacked subplot figure and the overlay figure.
	"""
	_ensure_output_dir(out_dir)

	# Determine uniform time window across all results
	first_key = next(iter(results))
	Rs = float(results[first_key]["Rs"][0])
	sps = int(round(results[first_key]["fs"][0] / Rs))
	max_samples = max_symbols_to_show * sps

	# Stacked subplots per modulation
	mod_names = list(results.keys())
	fig, axes = plt.subplots(len(mod_names), 1, figsize=(12, 2.0 * len(mod_names)), sharex=True)
	if len(mod_names) == 1:
		axes = [axes]

	for ax, name in zip(axes, mod_names):
		res = results[name]
		t = res["t"]
		s = res["s"]
		Nshow = min(len(t), max_samples)
		ax.plot(t[:Nshow] * 1e3, s[:Nshow], lw=1.0)
		ax.set_ylabel(f"{name}\namp")
		ax.grid(True, alpha=0.3)

	ax.set_xlabel("time (ms)")
	fig.suptitle("PSK Family: Passband Waveforms (first %d symbols)" % max_symbols_to_show)
	fig.tight_layout(rect=[0, 0.03, 1, 0.95])
	stacked_path = os.path.join(out_dir, "waveforms_stacked.png")
	fig.savefig(stacked_path, dpi=150)
	plt.close(fig)

	# Overlay plot to compare envelopes visually
	fig2, ax2 = plt.subplots(figsize=(12, 3.5))
	for name in mod_names:
		res = results[name]
		t = res["t"]
		s = res["s"]
		Nshow = min(len(t), max_samples)
		ax2.plot(t[:Nshow] * 1e3, s[:Nshow], lw=1.0, label=name)

	ax2.set_title("Overlay: Passband waveforms")
	ax2.set_xlabel("time (ms)")
	ax2.set_ylabel("amplitude")
	ax2.grid(True, alpha=0.3)
	ax2.legend(ncol=3)
	fig2.tight_layout()
	overlay_path = os.path.join(out_dir, "waveforms_overlay.png")
	fig2.savefig(overlay_path, dpi=150)
	plt.close(fig2)

	return stacked_path, overlay_path


def main() -> None:
	# Common parameters for apples-to-apples comparison
	Rs = 1000.0  # 1 kSym/s
	sps = 20     # must be even
	fc = 3000.0  # 3 kHz carrier (fs = 20 kHz -> Nyquist-safe)
	Nsym = 64

	results: Dict[str, Dict[str, np.ndarray]] = {}

	# BPSK (no offset)
	results["BPSK (M=2)"] = generate_mpsk_waveform(
		M=2,
		num_symbols=Nsym,
		samples_per_symbol=sps,
		carrier_frequency_hz=fc,
		symbol_rate_baud=Rs,
		phase_offset_rad=0.0,
		random_seed=42,
	)

	# QPSK (pi/4 offset, conventional)
	results["QPSK (pi/4)"] = generate_mpsk_waveform(
		M=4,
		num_symbols=Nsym,
		samples_per_symbol=sps,
		carrier_frequency_hz=fc,
		symbol_rate_baud=Rs,
		phase_offset_rad=np.pi / 4.0,
		random_seed=43,
	)

	# 8-PSK
	results["8-PSK"] = generate_mpsk_waveform(
		M=8,
		num_symbols=Nsym,
		samples_per_symbol=sps,
		carrier_frequency_hz=fc,
		symbol_rate_baud=Rs,
		phase_offset_rad=np.pi / 8.0,
		random_seed=44,
	)

	# 16-PSK
	results["16-PSK"] = generate_mpsk_waveform(
		M=16,
		num_symbols=Nsym,
		samples_per_symbol=sps,
		carrier_frequency_hz=fc,
		symbol_rate_baud=Rs,
		phase_offset_rad=np.pi / 16.0,
		random_seed=45,
	)

	# OQPSK (interpreting OPSK in prompt as Offset QPSK)
	results["OQPSK"] = generate_oqpsk_waveform(
		num_symbols=Nsym,
		samples_per_symbol=sps,
		carrier_frequency_hz=fc,
		symbol_rate_baud=Rs,
		random_seed=46,
	)

	out_dir = os.path.join(os.getcwd(), "psk_plots")
	stacked, overlay = plot_passband_comparison(results, out_dir=out_dir, max_symbols_to_show=10)

	print(f"Saved stacked subplot comparison to: {stacked}")
	print(f"Saved overlay comparison to: {overlay}")


if __name__ == "__main__":
	main()

