import numpy as np
import os 
import matplotlib.pyplot as plt
os.chdir(os.path.dirname(__file__))

a = 1  # downsample factor
data = np.loadtxt("ricker_surface.acc")[::a]
time = np.loadtxt("ricker_surface.time")[::a]

dt = time[1] - time[0]

# append zero to make the length even for 
len = 2048
if data.shape[0] < len:
    data = np.append(data, np.zeros(len - data.shape[0]))

time = np.arange(0, len*dt, dt)



# calcute the frequency content using FFT
n = data.shape[0]
freq = np.fft.rfftfreq(n, d=dt)
fft_values = np.fft.rfft(data)

amplitude_spectrum = np.abs(fft_values)
phase_spectrum = np.angle(fft_values)
plt.figure(figsize=(10, 6))
plt.subplot(2, 1, 1)
plt.plot(freq, amplitude_spectrum, color='blue', linewidth=1.5)
plt.title('Amplitude Spectrum of Ricker Wavelet')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Amplitude')
plt.grid(True, linestyle='--', alpha=0.7)
plt.xlim(0, 50)
plt.subplot(2, 1, 2)
# time-domain signal for reference
plt.plot(time, data, "b-o", markersize=2)
plt.xlim(0, 0.5)
plt.show()