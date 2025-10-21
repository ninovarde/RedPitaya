# Frequency counter SCPI script for Red Pitaya. 

"""
In this code the Red Pitaya is operated in Deep Memory Acquisition Mode (DMA)
to obtain access to all the space in its RAM, allowing for longer data 
acquisitions. More info on this operating mode, and on how to modify the 
dimension of the accessible memoty for data sampling can be found at 
https://redpitaya.readthedocs.io/en/latest/appsFeatures/remoteControl/deepMemoryMode.html#deep-memory-generation-dmg
"""

"""
NB: For very long sample this script can take a couple of minutes to process 
    the data.
    If the time needed for the acqusition gets suspiciously long, try to change
    the trigger mode.
"""

import sys
import redpitaya_scpi as scpi
import matplotlib.pyplot as plt
import struct
import numpy as np 
import time as tm
import random as rn

%matplotlib


IP = '169.254.205.2'  # Change to your Red Pitaya's IP
PORT = 5000           # Identify the type of connection of the RP

rp_s = scpi.scpi(host = IP)


# Reset acquisition and set data format
rp_s.tx_txt('ACQ:RST')              
rp_s.tx_txt('ACQ:DATA:FORMAT BIN')


# Take raw data to avoid the time necessary for the volt conversion
rp_s.tx_txt('ACQ:AXI:DATA:UNITS RAW')
print('ACQ:AXI:DATA:UNITS?: ',rp_s.txrx_txt('ACQ:AXI:DATA:UNITS?'))
rp_s.check_error()


# Set the sampling rate for the data acquisition 
rp_s.tx_txt('ACQ:AXI:DEC 1')
print('ACQ:AXI:DEC?: ',rp_s.txrx_txt('ACQ:AXI:DEC?'))
rp_s.check_error()


# Set the samples dimension 
decimation = int(rp_s.txrx_txt('ACQ:AXI:DEC?'))

start = int(rp_s.txrx_txt('ACQ:AXI:START?'))        # Starting Bit
size = int(rp_s.txrx_txt('ACQ:AXI:SIZE?'))          # Size of the usable memory

"""
The sample dimensions can be defined by choosing the which fraction of the max
possible samples we want to take.
"""
max_sample = size//2                                # Maximum number of samples
max_sample_fraction = 0.01

samples =  max_sample * max_sample_fraction         # 1 sample = 2 B
samples_MB = 2*samples/(2**20)

rp_s.check_error()


# Print the acquisition parameters
print("\nSize of aviable memory: ",size/(2**20),' MB')
print("Sample size: ", samples_MB, ' MB')
print("Sampling rate: ", 125/decimation, ' MS/s')
print("Sampling lenght ", 1e3 * samples* decimation/125e6, ' ms\n')


# Specify the memory and data buffer sizes in bytes for the first channel
"""
NB: first you need to fill the memory buffer, and then to decide how much of 
    it you want to save by choosing the number of samples to use after the 
    trigger event. The saved data will constitute the data buffer.
"""

add_str_ch1 = 'ACQ:AXI:SOUR1:SET:Buffer ' + str(start) + ',' + str(size)
rp_s.tx_txt(add_str_ch1)
rp_s.check_error()

rp_s.tx_txt('ACQ:AXI:SOUR1:Trig:Dly '+ str(samples))
rp_s.check_error()


# Enable the data acquisition in DMA mode for Ch. 1
rp_s.tx_txt('ACQ:AXI:SOUR1:ENable ON')
rp_s.check_error()


# Start data the acquisition using a positive edge trigger mode
rp_s.tx_txt('ACQ:START')
rp_s.tx_txt('ACQ:TRIG CH1_PE')
rp_s.check_error()


#Check if the data buffer is full. 
"""
NB : The SCPI command 'ACQ:AXI:SOUR1:TRIG:FILL?' return 1 if the buffer is 
     full, otherwise it returns 0.
"""
while 1:
    rp_s.tx_txt('ACQ:AXI:SOUR1:TRIG:FILL?')
    if rp_s.rx_txt() == '1':
        break
    
rp_s.tx_txt('ACQ:STOP')
print("\n\nData acquisition concluded.")




# At this point the data are collected and we have to transfer it to our PC
"""
NB: It is quite difficult for the server to transfer a large amount of data at 
    once. For this reason, we request data from the server in parts.
"""


# Check the position of the trigger inside the memory buffer. 
trig = int(rp_s.txrx_txt('ACQ:AXI:SOUR1:Trig:Pos?'))


# Frequency value acquisition

# Frequency evaluation function
def count_oscillations(full_signal,sample_dimension,sample_duration,freq_res):
    """
    NB: if full_signal%sample_dim !=0, last sample will be discarded since there are
        not enough samples to properly measure the frequency.
    
    NB: the output frequencies are in MHz. freq_res indicates the number of 
        decimal digits with wich we want to evaluate the frequency. 
        The reccomended values are 0 or 1.
    """
    frequencies = []
    # Detect rising zero crossings
    for i in range(int(len(full_signal)/sample_dimension)):
        sample_sig = full_signal[sample_dimension*i:sample_dimension*i + sample_dimension]
        theshold = np.mean(sample_sig)
        crossings = (sample_sig[:-1] < theshold) & (sample_sig[1:] >= theshold)
        frequencies = np.append(frequencies, np.round( np.sum(crossings)/sample_duration/1e6,freq_res))
    return frequencies


# Start transfering data to the PC
received_size = 0

"""
The acquired data will be transfered in block of block_size samples. These 
samples will be subdivided in smaller samples of lenght frequency_samples_size, 
and we will compute the frequency for each of them. 
"""
block_size = 1e5
frequency_values_MHz = []
frequency_samples_size = 1e3
freq_resolution_digit = 0
freq_resolution = 10**-freq_resolution_digit
print('\nFrequency Sample Size:',frequency_samples_size*1/(125/decimation),'us')
print('Resolution',freq_resolution,'MHz')
frequency_samples_duration = frequency_samples_size*decimation/125e6
while received_size < samples:
    """
    This 'if' manage the last block of data when samples%block_size !=0
    """
    if (received_size + block_size) > samples:
        block_size = samples - received_size
    
    buff_byte = False
    rp_s.tx_txt('ACQ:AXI:SOUR1:DATA:Start:N? ' + str(trig)+',' + str(block_size))
    
    while buff_byte ==False:
        buff_byte = rp_s.rx_arb() 
    buff =np.array( [struct.unpack('!h',bytearray(buff_byte[i:i+2]))[0] for i in range(0, len(buff_byte), 2)])
    frequency_values_MHz = np.append(
                                frequency_values_MHz, 
                                count_oscillations(
                                                    full_signal = buff,
                                                    sample_dimension = int(frequency_samples_size),
                                                    sample_duration = frequency_samples_duration,
                                                    freq_res = freq_resolution_digit
                                                    )
                                )
    trig += block_size
    trig = trig % samples
    received_size += block_size



time_s = np.arange(0.5,len(frequency_values_MHz)+0.5,1)* frequency_samples_duration
plt.plot(time_s*1000,frequency_values_MHz)
plt.ylabel('Frequency (MHz)',fontsize = 20)
plt.xlabel('Time (ms)',fontsize = 20)
plt.grid()
plt.show()
plt.tight_layout()


"""
NB: the "check_error()" function check if the device is working well by asking
    its status byte, which is a 8-bit value that that provides a summary of the
    instrument’s current status, including error conditions, operation 
    completion, and other flags.
"""
