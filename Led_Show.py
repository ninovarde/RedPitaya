# Led Show

# Just Run and Enjoy
import sys
import time 
import redpitaya_scpi as scpi
import random as rn


IP = '169.254.205.2'  # Change to your Red Pitaya's IP
PORT = 5000          # Identify the type of connection of the RP

rp_s = scpi.scpi(host = IP)




leds = list(range(8))
short = 0.05

def all_off():
    for i in leds:
        rp_s.tx_txt(f'DIG:PIN LED{i},0')

def strobe(times=20):
    for _ in range(times):
        for i in leds:
            rp_s.tx_txt(f'DIG:PIN LED{i},1')
        time.sleep(0.01)
        for i in leds:
            rp_s.tx_txt(f'DIG:PIN LED{i},0')
        time.sleep(0.01)

def glitchstorm(duration=2.0):
    end_time = time.time() + duration
    while time.time() < end_time:
        pin = rn.choice(leds)
        rp_s.tx_txt(f'DIG:PIN LED{pin},{rn.randint(0,1)}')
        time.sleep(rn.uniform(0.005, 0.03))

def laser_sweep(cycles=3):
    for _ in range(cycles):
        for i in range(len(leds) - 1):
            all_off()
            rp_s.tx_txt(f'DIG:PIN LED{i},1')
            rp_s.tx_txt(f'DIG:PIN LED{i+1},1')
            time.sleep(short)
        for i in reversed(range(1, len(leds))):
            all_off()
            rp_s.tx_txt(f'DIG:PIN LED{i},1')
            rp_s.tx_txt(f'DIG:PIN LED{i-1},1')
            time.sleep(short)
    all_off()

def stack_n_explode():
    # Stack up
    for i in range(len(leds)):
        rp_s.tx_txt(f'DIG:PIN LED{i},1')
        time.sleep(0.025)
    time.sleep(0.05)
    # Random explosion
    for _ in range(10):
        rp_s.tx_txt(f'DIG:PIN LED{rn.choice(leds)},0')
        time.sleep(rn.uniform(0.025, 0.05))
    all_off()

def disco_spin(cycles=10):
    pattern = [0, 1] * 4
    for _ in range(cycles):
        for i in range(len(leds)):
            for j in range(len(leds)):
                val = pattern[(j + i) % len(leds)]
                rp_s.tx_txt(f'DIG:PIN LED{j},{val}')
            time.sleep(0.04)
    all_off()

def meltdown():
    for _ in range(3):
        glitchstorm(0.3)
        strobe(8)
        laser_sweep(1)
        stack_n_explode()
        disco_spin(4)

def combo_explosion():
    """New high-energy pattern: fast chaos + sweep + flash."""
    # Rapid random blinking
    for _ in range(10):
        pin = rn.choice(leds)
        rp_s.tx_txt(f'DIG:PIN LED{pin},{rn.randint(0,1)}')
        time.sleep(rn.uniform(0.005, 0.015))

    # Sweep up and down
    for i in leds:
        rp_s.tx_txt(f'DIG:PIN LED{i},1')
        time.sleep(0.01)
    for i in reversed(leds):
        rp_s.tx_txt(f'DIG:PIN LED{i},0')
        time.sleep(0.01)

    # Full strobe
    for _ in range(3):
        for i in leds:
            rp_s.tx_txt(f'DIG:PIN LED{i},1')
        time.sleep(0.025)
        for i in leds:
            rp_s.tx_txt(f'DIG:PIN LED{i},0')
        time.sleep(0.025)
        
def laser_sweep_fast(cycles=2):
    for _ in range(cycles):
        for i in range(len(leds)):
            all_off()
            rp_s.tx_txt(f'DIG:PIN LED{i},1')
            time.sleep(0.01)
        for i in reversed(range(len(leds))):
            all_off()
            rp_s.tx_txt(f'DIG:PIN LED{i},1')
            time.sleep(0.01)
    all_off()

def psycho_spin(cycles=3):
    pattern = [rn.randint(0, 1) for _ in leds]
    for _ in range(cycles):
        pattern = pattern[-1:] + pattern[:-1]
        for i, val in enumerate(pattern):
            rp_s.tx_txt(f'DIG:PIN LED{i},{val}')
        time.sleep(0.025)
    all_off()

def pulse_wave():
    for i in leds:
        rp_s.tx_txt(f'DIG:PIN LED{i},1')
        time.sleep(0.025)
        rp_s.tx_txt(f'DIG:PIN LED{i},0')


led_sequence_final = [
  'combo_explosion', 'meltdown', 'combo_explosion', 'combo_explosion',
  'meltdown', 'combo_explosion', 'combo_explosion', 'meltdown',
  'combo_explosion', 'meltdown', 'combo_explosion', 'combo_explosion',
  'combo_explosion', 'combo_explosion', 'combo_explosion'
]

print(3)
time.sleep(1)
print(2)
time.sleep(1)
print(1)
time.sleep(1)
print('Start')

try:
    for effect in led_sequence_final:
        if effect == "combo_explosion":
            combo_explosion()
        elif effect == "meltdown":
            meltdown()
        elif effect == "psycho_spin":
            psycho_spin()
        elif effect == "laser_sweep_fast":
            laser_sweep_fast()
        elif effect == "strobe":
            strobe()
        elif effect == "pulse_wave":
            pulse_wave()
        time.sleep(0.1)  # matches chunk_ms
except KeyboardInterrupt:
    all_off()
    print("💥 Show interrupted.")
