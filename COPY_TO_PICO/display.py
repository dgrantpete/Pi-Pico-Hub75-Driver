from machine import Pin, WDT
from utime import sleep_us, sleep, ticks_us, ticks_diff
from rp2 import StateMachine, asm_pio, PIO
from micropython import const
import _thread
import os
import gc
import rp2
import machine

enable_pin = Pin(5, Pin.OUT, value=1)

#LED Matrix Dimensions
MATRIX_SIZE_X = 64
MATRIX_SIZE_Y = 32

#Time before cycling to next image, in seconds
CYCLE_TIME = 5

#The number of data selection addresses on your LED Matrix
MATRIX_ADDRESS_COUNT = const(16)

MEM_CLEAR_THRESH = const(50_000)

PIO_FREQ = const(20_000)
MACHINE_FREQ = const(250_000_000)

''' Calculating correct values to feed into PIO program given dimensions '''

rp2._pio_funcs["max_address_val"] = MATRIX_ADDRESS_COUNT - 1

gc.disable()

machine.freq(MACHINE_FREQ)

crash_wdt = WDT(timeout=10000)

frames_paths = [('/frames/' + plainpath) for plainpath in os.listdir('frames')]

frame_buffer_lock = _thread.allocate_lock()

feed_frames = True

def frames_feeder():
    global frame_buffer
    global feed_frames
    while feed_frames:
        enable_pin.value(0)
        with frame_buffer_lock:
            led_data_sm.put(frame_buffer)

@asm_pio(out_init=(rp2.PIO.OUT_LOW,) * 6, sideset_init=rp2.PIO.OUT_LOW, 
         set_init=(rp2.PIO.OUT_HIGH, ) * 2, out_shiftdir=PIO.SHIFT_RIGHT)
def led_data():
    set(x, 31)
    in_(x, 6)
    in_(x, 1)
    wrap_target()
    mov(x, isr)
    label("Byte Counter")
    pull().side(0)
    out(pins, 6).side(1)
    jmp(x_dec, "Byte Counter")
    irq(block, 4)
    irq(block, 5)
    wrap()
    

@asm_pio(out_init=(rp2.PIO.OUT_LOW,) * 4, set_init=(rp2.PIO.OUT_HIGH, ) * 1,
         out_shiftdir=PIO.SHIFT_RIGHT)
def address_counter():
    max_address_val = MATRIX_ADDRESS_COUNT - 1
    set(x, max_address_val)
    label("Address Decrement")
    wait(1, irq, 4)
    mov(pins, x)
    set(pins, 1)
    set(pins, 0)
    irq(clear, 5)
    jmp(x_dec, "Address Decrement")

led_data_sm = StateMachine(0, led_data, freq=PIO_FREQ, out_base=Pin(10), sideset_base=Pin(9))

address_counter_sm = StateMachine(1, address_counter, freq=PIO_FREQ, out_base=Pin(0), set_base=Pin(4))

address_counter_sm.active(1)
led_data_sm.active(1)

with open(frames_paths[0], 'rb') as frame_data:
        frame_buffer_temp = frame_data.read()

frame_buffer = frame_buffer_temp

_thread.start_new_thread(frames_feeder, ())

for _ in range(10000):
    for path in frames_paths:
        sleep(CYCLE_TIME)
        with open(path, 'rb') as frame_data:
            frame_buffer_temp = frame_data.read()
        with frame_buffer_lock:
            frame_buffer = frame_buffer_temp
        if gc.mem_free() < MEM_CLEAR_THRESH:
            feed_frames = False
            with frame_buffer_lock:
                enable_pin.value(1)
                gc.collect()
                feed_frames = True
                _thread.start_new_thread(frames_feeder, ())
        crash_wdt.feed()