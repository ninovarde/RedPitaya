# Frequency monitoring through DC output

'''
This script is written to run completely on the RP FPGA. It allows to 
achieve a live monitoring of a signal frequency by giving as output a DC value 
proportional to the input frequency.
'''


import numpy as np
import rp
import ctypes


# Samples per Acquisition
N = 1000


# Input and output range
margin_MHz = 2                  # Stabilize the signal in the intervals limits      
min_freq_MHz = 30 - margin_MHz
max_freq_MHz = 60 + margin_MHz
min_DC_V = 0
max_DC_V =0.9


# Fix the number of decimal digit on the MHz scale. 
res_digit = 1 
resolution_MHz = 10**(-res_digit)

# Frequency to DC conversion factor 
deriv_fDC = (max_DC_V-min_DC_V)/(max_freq_MHz-min_freq_MHz)
offset_V = min_DC_V - deriv_fDC*min_freq_MHz

def freq_to_DC_conversion(frequency_value_MHz,offset = offset_V,alpha = deriv_fDC):
    return offset + deriv_fDC*frequency_value_MHz

# Counting oscillation function
def count_oscillations(sig,ts):
    return np.count_nonzero((sig[:-1] < ts) & (sig[1:] >= ts))



#? Possible decimations:
#?  RP_DEC_1, RP_DEC_2, RP_DEC_4, RP_DEC_8, RP_DEC_16 , RP_DEC_32 , RP_DEC_64 ,
#?  RP_DEC_128, RP_DEC_256, RP_DEC_512, RP_DEC_1024, RP_DEC_2048, RP_DEC_4096, RP_DEC_8192,
#?  RP_DEC_16384, RP_DEC_32768, RP_DEC_65536

# Sampling rate 
dec = rp.RP_DEC_1
max_sampling_rate = 125e6 # S/s

# Number of oscillation to frequency in MHz conversion
osc_to_freq_conv = max_sampling_rate/N/dec/1e6

# Trigger level, delay and mode
trig_lvl = 0.0
trig_dly = 0
acq_trig_sour = rp.RP_TRIG_SRC_NOW



# Input and output channel setting 
channel = rp.RP_CH_1      

# Setting the DC output 
waveform = rp.RP_WAVEFORM_DC


# Initialize the interface
rp.rp_Init()

# Reset Generation
rp.rp_GenReset()

# Reset Acquisition
rp.rp_AcqReset()



##### Acquisition Settings##### 

# Set Decimation
rp.rp_AcqSetDecimation(dec)
data_raw = np.zeros(N, dtype = int)
ibuff = rp.i16Buffer(N)
ptr = ctypes.cast(int(ibuff.this), ctypes.POINTER(ctypes.c_int16))

# Set trigger level and delay
rp.rp_AcqSetTriggerLevel(rp.RP_T_CH_1, trig_lvl)
rp.rp_AcqSetTriggerDelay(trig_dly)



#### Generation Settings ####
# Starting Value for reference frequency
freq_ref= 0
"""
NB: for every acquisition we compute the frequency, and change the DC output 
    value in accordance with it.
    Since the device need some time to change the DC value of the output, after
    every acquisition we define a reference frequency, which will be compared 
    to the one obtained in the successive measurement. If, considering the 
    eevaluation resolution, they are same, the DC output won't be changed, 
    allowing to go faster to the successive acquisition.
"""

# Initialize the generation of DC signal to 0 V 
rp.rp_GenWaveform(channel, waveform)
rp.rp_GenAmp(channel, 0)
        
# Enable output and trigger the generator
rp.rp_GenOutEnable(channel)
rp.rp_GenTriggerOnly(channel)


# Set contious acquisition after the trigger
rp.rp_AcqSetArmKeep(True)


rp.rp_AcqStart()
# Specify trigger - immediately
rp.rp_AcqSetTriggerSrc(acq_trig_sour)

# Trigger state check
while 1:
    trig_state = rp.rp_AcqGetTriggerState()[1]
    if trig_state == rp.RP_TRIG_STATE_TRIGGERED:
        break
    
# Fill state check
while 1:
    if rp.rp_AcqGetBufferFillState()[1]:
        break
        
tp=rp.rp_AcqGetWritePointerAtTrig()[1]


# Start the monitoring cycle 
print("Start Monitoring...\n\n")
print("Active Input Channel: ",channel+1)
print("DC Output Channel: ",channel+1)
print("Input Frequency Range in MHz: [",min_freq_MHz,',',max_freq_MHz,']')
print("Input Frequency Resolution Measurement in MHz: ", resolution_MHz)
print("Output Voltage Range in V: [",min_DC_V,',',max_DC_V,"]")
print("Sampling Rate: ",max_sampling_rate/dec/1e6," MS/s")
print("Sample per Point: ", N,'\n')
print("To interrupt the monitoring --> KeyboardInterrupt \n\n")





try:
    while True:
        ### Acquisition ###
        
        # RAW
        res = rp.rp_AcqGetDataRaw(channel,tp, N, ibuff.cast())
        
        # Convert in numpy array 
        data_raw = np.ctypeslib.as_array(ptr, shape=(N,))
        frequency_MHz = np.round(osc_to_freq_conv*count_oscillations(data_raw,np.mean(data_raw)),res_digit)
        
        if frequency_MHz!=freq_ref:
            ###### Generation #####
            rp.rp_GenAmp(channel, freq_to_DC_conversion(frequency_MHz))
            freq_ref = frequency_MHz
          
except KeyboardInterrupt:
    # Reset generator
    rp.rp_GenReset()

    # Reset Acquisition
    rp.rp_AcqReset()
    
    # Release resources
    rp.rp_Release()
    print('\nStop Monitoring')