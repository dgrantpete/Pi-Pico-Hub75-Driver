import machine
from utime import sleep

if machine.reset_cause() is machine.PWRON_RESET:
    sleep(3)
    import display
    
else:
    print("Crash reset detected, will not run file automatically.")