import os
import pyaudio
import wave
from gpiozero import LED
from time import sleep
import numpy as np
from scipy.io import wavfile

import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
coil_A_1_pin = 4 # pink
coil_A_2_pin = 17 # orange
coil_B_1_pin = 23 # blue
coil_B_2_pin = 24 # yellow
enable_pin = 18

# adjust if different
StepCount = 8
Seq = range(0, StepCount)
Seq[0] = [1,0,0,0]
Seq[1] = [1,1,0,0]
Seq[2] = [0,1,0,0]
Seq[3] = [0,1,1,0]
Seq[4] = [0,0,1,0]
Seq[5] = [0,0,1,1]
Seq[6] = [0,0,0,1]
Seq[7] = [1,0,0,1]

GPIO.setup(enable_pin, GPIO.OUT)
GPIO.setup(coil_A_1_pin, GPIO.OUT)
GPIO.setup(coil_A_2_pin, GPIO.OUT)
GPIO.setup(coil_B_1_pin, GPIO.OUT)
GPIO.setup(coil_B_2_pin, GPIO.OUT)

GPIO.output(enable_pin, 1)

def setStep(w1, w2, w3, w4):
    GPIO.output(coil_A_1_pin, w1)
    GPIO.output(coil_A_2_pin, w2)
    GPIO.output(coil_B_1_pin, w3)
    GPIO.output(coil_B_2_pin, w4)

def forward(delay, steps):
    for i in range(steps):
        for j in range(StepCount):
            setStep(Seq[j][0], Seq[j][1], Seq[j][2], Seq[j][3])
            time.sleep(delay)

def backwards(delay, steps):
    for i in range(steps):
        for j in reversed(range(StepCount)):
            setStep(Seq[j][0], Seq[j][1], Seq[j][2], Seq[j][3])
            time.sleep(delay)

# This function normalises the input data and converts it to a float array
def normalise_audio(data):
    return np.float32(data / np.max(data))

# This funciton reads the audio file and extracts the signal
def read_audio_file(file_path, sample_for_seconds = 1):
    samplerate, data = wavfile.read(file_path)
    print (f'sample Rate is {samplerate}')
    data_n = normalise_audio(data[0:int(samplerate * sample_for_seconds)])
    # In case the is two-dimesional, we return only one channel
    return samplerate, data_n[:,0]

# This function calculates the Fourier Transform and cleasn the output signal
def calculate_fft(input_signal):
    # fourier transform and frequency domain
    Y_k_full = np.fft.fft(input_signal)
    # need to take the single-sided spectrum only
    sig_len = input_signal.size
    Y_k = Y_k_full[0:int(sig_len / 2)] / sig_len 
    Y_k[1:] = 2 * Y_k[1:] 
    # be sure to get rid of imaginary part
    return np.abs(Y_k)

led = LED(22)

form_1 = pyaudio.paInt16 # 16-bit resolution
chans = 1 # 1 channel
# samp_rate = 44100 # 44.1kHz sampling rate
samp_rate = 48000 # 48kHz sampling rate
chunk = 4096 # 2^12 samples for buffer
record_secs = 3 # seconds to record
dev_index = 2 # device index found by p.get_device_info_by_index(ii)
wav_output_filename = 'test1.wav' # name of .wav file

audio = pyaudio.PyAudio() # create pyaudio instantiation

os.system('clear')

while True:
    sleep(1)

    print("recording")
    led.on()

    # create pyaudio stream
    stream = audio.open(format = form_1,rate = samp_rate,channels = chans, \
                    input_device_index = dev_index,input = True, \
                    frames_per_buffer=chunk)
    frames = []

    # loop through stream and append audio chunks to frame array
    for ii in range(0,int((samp_rate/chunk)*record_secs)):
        data = stream.read(chunk)
        frames.append(data)

    # stop the stream, close it, and terminate the pyaudio instantiation
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # save the audio frames as .wav file
    wavefile = wave.open(wav_output_filename,'wb')
    wavefile.setnchannels(chans)
    wavefile.setsampwidth(audio.get_sample_size(form_1))
    wavefile.setframerate(samp_rate)
    wavefile.writeframes(b''.join(frames))
    wavefile.close()

    led.off()
    print("finished recording")

    print("Calculating FFT");
    samplerate, data = read_audio_file(wav_output_filename)
    fft_out = calculate_fft(data)

    print("Selecting next part")
    forward(2 / 1000.0, int(300))

