#!/usr/bin/env python3
"""
DSP Utilities for Generic DSP Debugging
Common signal processing and analysis functions
"""

import numpy as np
from scipy import signal
from scipy.fft import fft, fftfreq, ifft
from typing import Tuple, List, Dict, Optional, Union
import logging

logger = logging.getLogger(__name__)

class DSPAnalyzer:
    """Comprehensive DSP analysis tools"""
    
    @staticmethod
    def calculate_thd(signal_data: np.ndarray, fs: float, fundamental_freq: Optional[float] = None) -> float:
        """
        Calculate Total Harmonic Distortion (THD)
        
        Args:
            signal_data: Input signal
            fs: Sampling frequency
            fundamental_freq: Known fundamental frequency (if None, auto-detect)
        
        Returns:
            THD in percentage
        """
        # Perform FFT
        n = len(signal_data)
        yf = fft(signal_data)
        xf = fftfreq(n, 1/fs)
        
        # Get positive frequencies
        pos_mask = xf > 0
        xf_pos = xf[pos_mask]
        yf_pos = np.abs(yf[pos_mask])
        
        if fundamental_freq is None:
            # Find fundamental (strongest frequency)
            fundamental_idx = np.argmax(yf_pos)
            fundamental_freq = xf_pos[fundamental_idx]
        else:
            # Find closest to specified fundamental
            fundamental_idx = np.argmin(np.abs(xf_pos - fundamental_freq))
        
        fundamental_power = yf_pos[fundamental_idx] ** 2
        
        # Find harmonics (2x, 3x, 4x, 5x fundamental)
        harmonic_power = 0
        for harmonic in range(2, 6):
            harmonic_freq = harmonic * fundamental_freq
            if harmonic_freq < fs/2:  # Below Nyquist
                harmonic_idx = np.argmin(np.abs(xf_pos - harmonic_freq))
                harmonic_power += yf_pos[harmonic_idx] ** 2
        
        # Calculate THD
        if fundamental_power > 0:
            thd = 100 * np.sqrt(harmonic_power / fundamental_power)
        else:
            thd = 0
        
        return thd
    
    @staticmethod
    def calculate_snr(signal_data: np.ndarray, fs: float, signal_freq: Optional[float] = None) -> float:
        """
        Calculate Signal-to-Noise Ratio (SNR)
        
        Args:
            signal_data: Input signal
            fs: Sampling frequency
            signal_freq: Known signal frequency (if None, auto-detect)
        
        Returns:
            SNR in dB
        """
        # Perform FFT
        n = len(signal_data)
        yf = fft(signal_data)
        xf = fftfreq(n, 1/fs)
        
        # Get positive frequencies
        pos_mask = xf > 0
        xf_pos = xf[pos_mask]
        yf_pos = np.abs(yf[pos_mask])
        
        if signal_freq is None:
            # Find signal (strongest frequency)
            signal_idx = np.argmax(yf_pos)
        else:
            # Find closest to specified frequency
            signal_idx = np.argmin(np.abs(xf_pos - signal_freq))
        
        # Signal power (including some bins around peak)
        bandwidth_bins = 3  # Include neighboring bins
        signal_indices = range(max(0, signal_idx - bandwidth_bins), 
                              min(len(yf_pos), signal_idx + bandwidth_bins + 1))
        signal_power = np.sum(yf_pos[signal_indices] ** 2)
        
        # Noise power (everything else)
        noise_mask = np.ones(len(yf_pos), dtype=bool)
        noise_mask[signal_indices] = False
        noise_power = np.sum(yf_pos[noise_mask] ** 2)
        
        if noise_power > 0:
            snr_db = 10 * np.log10(signal_power / noise_power)
        else:
            snr_db = float('inf')
        
        return snr_db
    
    @staticmethod
    def design_fir_filter(filter_type: str, cutoff: Union[float, Tuple[float, float]], 
                         fs: float, num_taps: int = 51) -> np.ndarray:
        """
        Design FIR filter using window method
        
        Args:
            filter_type: 'lowpass', 'highpass', 'bandpass', 'bandstop'
            cutoff: Cutoff frequency (Hz) or tuple of (low, high) for band filters
            fs: Sampling frequency
            num_taps: Number of filter coefficients (odd number)
        
        Returns:
            Filter coefficients
        """
        nyquist = fs / 2
        
        if filter_type == 'lowpass':
            if isinstance(cutoff, (list, tuple)):
                cutoff = cutoff[0]
            return signal.firwin(num_taps, cutoff/nyquist)
        
        elif filter_type == 'highpass':
            if isinstance(cutoff, (list, tuple)):
                cutoff = cutoff[0]
            return signal.firwin(num_taps, cutoff/nyquist, pass_zero=False)
        
        elif filter_type == 'bandpass':
            if not isinstance(cutoff, (list, tuple)) or len(cutoff) != 2:
                raise ValueError("Bandpass filter requires (low, high) cutoff frequencies")
            return signal.firwin(num_taps, [cutoff[0]/nyquist, cutoff[1]/nyquist], 
                                pass_zero=False)
        
        elif filter_type == 'bandstop':
            if not isinstance(cutoff, (list, tuple)) or len(cutoff) != 2:
                raise ValueError("Bandstop filter requires (low, high) cutoff frequencies")
            return signal.firwin(num_taps, [cutoff[0]/nyquist, cutoff[1]/nyquist])
        
        else:
            raise ValueError(f"Unknown filter type: {filter_type}")
    
    @staticmethod
    def design_iir_filter(filter_type: str, cutoff: Union[float, Tuple[float, float]], 
                         fs: float, order: int = 4, 
                         design_method: str = 'butterworth') -> Tuple[np.ndarray, np.ndarray]:
        """
        Design IIR filter
        
        Args:
            filter_type: 'lowpass', 'highpass', 'bandpass', 'bandstop'
            cutoff: Cutoff frequency (Hz) or tuple for band filters
            fs: Sampling frequency
            order: Filter order
            design_method: 'butterworth', 'chebyshev1', 'chebyshev2', 'elliptic'
        
        Returns:
            Tuple of (b, a) filter coefficients
        """
        nyquist = fs / 2
        
        # Normalize cutoff frequency
        if isinstance(cutoff, (list, tuple)):
            wn = [f/nyquist for f in cutoff]
        else:
            wn = cutoff/nyquist
        
        if design_method == 'butterworth':
            return signal.butter(order, wn, btype=filter_type)
        elif design_method == 'chebyshev1':
            return signal.cheby1(order, 0.5, wn, btype=filter_type)  # 0.5 dB ripple
        elif design_method == 'chebyshev2':
            return signal.cheby2(order, 40, wn, btype=filter_type)  # 40 dB stopband
        elif design_method == 'elliptic':
            return signal.ellip(order, 0.5, 40, wn, btype=filter_type)
        else:
            raise ValueError(f"Unknown design method: {design_method}")
    
    @staticmethod
    def calculate_power_spectrum(signal_data: np.ndarray, fs: float, 
                                window: str = 'hann') -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate power spectral density
        
        Args:
            signal_data: Input signal
            fs: Sampling frequency
            window: Window function ('hann', 'hamming', 'blackman', 'bartlett')
        
        Returns:
            Tuple of (frequencies, power_spectrum)
        """
        frequencies, power = signal.periodogram(signal_data, fs, window=window)
        return frequencies, 10 * np.log10(power)  # Convert to dB
    
    @staticmethod
    def calculate_spectrogram(signal_data: np.ndarray, fs: float, 
                            window_size: int = 256) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate spectrogram (STFT)
        
        Args:
            signal_data: Input signal
            fs: Sampling frequency
            window_size: Window size for STFT
        
        Returns:
            Tuple of (times, frequencies, spectrogram_matrix)
        """
        f, t, Sxx = signal.spectrogram(signal_data, fs, nperseg=window_size)
        return t, f, 10 * np.log10(Sxx)  # Convert to dB
    
    @staticmethod
    def detect_peaks(signal_data: np.ndarray, threshold: Optional[float] = None, 
                    min_distance: int = 1) -> np.ndarray:
        """
        Detect peaks in signal
        
        Args:
            signal_data: Input signal
            threshold: Minimum peak height
            min_distance: Minimum distance between peaks
        
        Returns:
            Array of peak indices
        """
        if threshold is None:
            threshold = np.mean(signal_data) + np.std(signal_data)
        
        peaks, properties = signal.find_peaks(signal_data, 
                                             height=threshold, 
                                             distance=min_distance)
        return peaks
    
    @staticmethod
    def calculate_rms(signal_data: np.ndarray) -> float:
        """Calculate RMS value of signal"""
        return np.sqrt(np.mean(signal_data ** 2))
    
    @staticmethod
    def calculate_crest_factor(signal_data: np.ndarray) -> float:
        """Calculate crest factor (peak/RMS ratio)"""
        rms = DSPAnalyzer.calculate_rms(signal_data)
        if rms > 0:
            return np.max(np.abs(signal_data)) / rms
        return 0
    
    @staticmethod
    def apply_window(signal_data: np.ndarray, window_type: str = 'hann') -> np.ndarray:
        """
        Apply window function to signal
        
        Args:
            signal_data: Input signal
            window_type: 'hann', 'hamming', 'blackman', 'bartlett', 'kaiser'
        
        Returns:
            Windowed signal
        """
        n = len(signal_data)
        
        if window_type == 'hann':
            window = signal.windows.hann(n)
        elif window_type == 'hamming':
            window = signal.windows.hamming(n)
        elif window_type == 'blackman':
            window = signal.windows.blackman(n)
        elif window_type == 'bartlett':
            window = signal.windows.bartlett(n)
        elif window_type == 'kaiser':
            window = signal.windows.kaiser(n, beta=8.6)
        else:
            window = np.ones(n)
        
        return signal_data * window
    
    @staticmethod
    def calculate_autocorrelation(signal_data: np.ndarray, max_lag: Optional[int] = None) -> np.ndarray:
        """
        Calculate autocorrelation of signal
        
        Args:
            signal_data: Input signal
            max_lag: Maximum lag to compute
        
        Returns:
            Autocorrelation values
        """
        if max_lag is None:
            max_lag = len(signal_data) // 2
        
        # Normalize signal
        signal_norm = signal_data - np.mean(signal_data)
        
        # Calculate autocorrelation using FFT (fast method)
        autocorr = signal.correlate(signal_norm, signal_norm, mode='full')
        autocorr = autocorr[len(autocorr)//2:]  # Take positive lags
        autocorr = autocorr[:max_lag]
        
        # Normalize
        autocorr = autocorr / autocorr[0]
        
        return autocorr
    
    @staticmethod
    def calculate_crosscorrelation(signal1: np.ndarray, signal2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate cross-correlation between two signals
        
        Args:
            signal1: First signal
            signal2: Second signal
        
        Returns:
            Tuple of (lags, correlation_values)
        """
        # Normalize signals
        sig1_norm = signal1 - np.mean(signal1)
        sig2_norm = signal2 - np.mean(signal2)
        
        # Calculate cross-correlation
        correlation = signal.correlate(sig1_norm, sig2_norm, mode='full')
        lags = signal.correlation_lags(len(sig1_norm), len(sig2_norm), mode='full')
        
        # Normalize
        correlation = correlation / (np.std(signal1) * np.std(signal2) * len(signal1))
        
        return lags, correlation


class FixedPointConverter:
    """Fixed-point arithmetic utilities for DSP implementations"""
    
    @staticmethod
    def float_to_fixed(value: float, word_length: int = 16, 
                       fraction_length: int = 15) -> int:
        """
        Convert floating-point to fixed-point representation
        
        Args:
            value: Floating-point value
            word_length: Total bits in fixed-point word
            fraction_length: Number of fractional bits
        
        Returns:
            Fixed-point integer representation
        """
        scale = 2 ** fraction_length
        max_val = 2 ** (word_length - 1) - 1
        min_val = -2 ** (word_length - 1)
        
        fixed_val = int(value * scale)
        
        # Saturate
        fixed_val = max(min_val, min(max_val, fixed_val))
        
        return fixed_val
    
    @staticmethod
    def fixed_to_float(fixed_value: int, fraction_length: int = 15) -> float:
        """
        Convert fixed-point to floating-point
        
        Args:
            fixed_value: Fixed-point integer
            fraction_length: Number of fractional bits
        
        Returns:
            Floating-point value
        """
        scale = 2 ** fraction_length
        return fixed_value / scale
    
    @staticmethod
    def quantize_coefficients(coefficients: np.ndarray, word_length: int = 16, 
                            fraction_length: int = 15) -> np.ndarray:
        """
        Quantize filter coefficients for fixed-point implementation
        
        Args:
            coefficients: Floating-point coefficients
            word_length: Total bits in fixed-point word
            fraction_length: Number of fractional bits
        
        Returns:
            Quantized coefficients
        """
        quantized = []
        for coeff in coefficients:
            fixed = FixedPointConverter.float_to_fixed(coeff, word_length, fraction_length)
            quantized.append(FixedPointConverter.fixed_to_float(fixed, fraction_length))
        
        return np.array(quantized)


class PWMGenerator:
    """PWM signal generation utilities"""
    
    @staticmethod
    def generate_pwm(frequency: float, duty_cycle: float, fs: float, 
                    duration: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate PWM signal
        
        Args:
            frequency: PWM frequency (Hz)
            duty_cycle: Duty cycle (0-1)
            fs: Sampling frequency
            duration: Signal duration (seconds)
        
        Returns:
            Tuple of (time_array, pwm_signal)
        """
        t = np.arange(0, duration, 1/fs)
        period_samples = int(fs / frequency)
        on_samples = int(period_samples * duty_cycle)
        
        # Generate one period
        one_period = np.concatenate([np.ones(on_samples), np.zeros(period_samples - on_samples)])
        
        # Repeat for full duration
        num_periods = int(len(t) / period_samples) + 1
        pwm = np.tile(one_period, num_periods)[:len(t)]
        
        return t, pwm
    
    @staticmethod
    def generate_spwm(carrier_freq: float, modulation_freq: float, 
                     modulation_index: float, fs: float, 
                     duration: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate Sinusoidal PWM (SPWM) signal
        
        Args:
            carrier_freq: Carrier frequency (Hz)
            modulation_freq: Modulation frequency (Hz)
            modulation_index: Modulation index (0-1)
            fs: Sampling frequency
            duration: Signal duration (seconds)
        
        Returns:
            Tuple of (time_array, spwm_signal)
        """
        t = np.arange(0, duration, 1/fs)
        
        # Generate carrier (triangle wave)
        carrier = signal.sawtooth(2 * np.pi * carrier_freq * t, 0.5)
        
        # Generate modulation (sine wave)
        modulation = modulation_index * np.sin(2 * np.pi * modulation_freq * t)
        
        # Compare to generate PWM
        spwm = (modulation > carrier).astype(float)
        
        return t, spwm
    
    @staticmethod
    def calculate_pwm_spectrum(pwm_signal: np.ndarray, fs: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate frequency spectrum of PWM signal
        
        Args:
            pwm_signal: PWM signal
            fs: Sampling frequency
        
        Returns:
            Tuple of (frequencies, magnitudes)
        """
        n = len(pwm_signal)
        yf = fft(pwm_signal)
        xf = fftfreq(n, 1/fs)
        
        # Take positive frequencies only
        pos_mask = xf > 0
        xf_pos = xf[pos_mask]
        yf_pos = 2.0/n * np.abs(yf[pos_mask])
        
        return xf_pos, yf_pos


def generate_test_signals(signal_type: str, fs: float, duration: float, **kwargs) -> np.ndarray:
    """
    Generate various test signals for DSP testing
    
    Args:
        signal_type: Type of signal ('sine', 'square', 'sawtooth', 'chirp', 'noise', 'impulse')
        fs: Sampling frequency
        duration: Signal duration
        **kwargs: Additional parameters specific to signal type
    
    Returns:
        Generated signal
    """
    t = np.arange(0, duration, 1/fs)
    
    if signal_type == 'sine':
        freq = kwargs.get('frequency', 1000)
        amplitude = kwargs.get('amplitude', 1.0)
        phase = kwargs.get('phase', 0)
        return amplitude * np.sin(2 * np.pi * freq * t + phase)
    
    elif signal_type == 'square':
        freq = kwargs.get('frequency', 1000)
        duty = kwargs.get('duty_cycle', 0.5)
        return signal.square(2 * np.pi * freq * t, duty)
    
    elif signal_type == 'sawtooth':
        freq = kwargs.get('frequency', 1000)
        return signal.sawtooth(2 * np.pi * freq * t)
    
    elif signal_type == 'chirp':
        f0 = kwargs.get('start_freq', 100)
        f1 = kwargs.get('end_freq', 1000)
        method = kwargs.get('method', 'linear')
        return signal.chirp(t, f0, duration, f1, method=method)
    
    elif signal_type == 'noise':
        noise_type = kwargs.get('noise_type', 'white')
        amplitude = kwargs.get('amplitude', 1.0)
        
        if noise_type == 'white':
            return amplitude * np.random.randn(len(t))
        elif noise_type == 'pink':
            # Simplified pink noise generation
            white = np.random.randn(len(t))
            # Apply 1/f filter
            b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
            a = [1, -2.494956002, 2.017265875, -0.522189400]
            return amplitude * signal.lfilter(b, a, white)
    
    elif signal_type == 'impulse':
        delay = kwargs.get('delay', 0)
        delay_samples = int(delay * fs)
        sig = np.zeros(len(t))
        sig[delay_samples] = 1.0
        return sig
    
    else:
        raise ValueError(f"Unknown signal type: {signal_type}")


# Export main classes and functions
__all__ = [
    'DSPAnalyzer',
    'FixedPointConverter', 
    'PWMGenerator',
    'generate_test_signals'
]