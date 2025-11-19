# LED-Matrix-Compiler

**I will be making some significant updates to this project in the coming weeks! Life has gotten busy since I initially created (and neglected) this project, but after having gained a decent amount of personal and professional experience, I will be completely revamping everything! [Stay tuned!](https://github.com/dgrantpete/Pi-Pico-Hub75-Driver/tree/release/v1.0.0)**

An open source Hub-75 Driver for the Raspberry Pi Pico that allows for the display of images, running up to 125MHz! THIS PROJECT IS A VERY EARLY WORK IN PROGRESS; better instructions for setting up will follow shortly!

NOTE: Currently only works on Windows for some of the read/write operations of 'png_to_frame.py', planning on making cross compatible soon!

To use, starting on a PC: 
1. First go to 'config.ini' and follow the options there, namely 'dimensions'.
2. Put your desired image input files into directory, as specified in 'config.ini'.
3. Run 'png_to_frame.py'.
Now, onto the Raspberry Pi Pico:
4. Copy contents inside 'COPY_TO_PICO' to Raspberry Pi and save (easiest way to do this is from the Thonny editor).
5. Hook up pins on Pico to HUB 75 interface, and set up pin configuration in 'display.py'.
6. Copy output directory from 'png_to_frame.py', and upload it to the Pico. You will need to rename it 'frames' if you changed it from the default.
7. Power cycle the Pico, and it should be displaying your image(s)!

Feel free to contact me if you need help getting it to work! Still a work in progress, working on adding video support!

Roadmap:
* Implement DMA from memory to HUB-75 interface; this will allow for video playback, tighter timings (and therefore a drastic reduction in flickering when frames change), and free up the second core to interface with an SD card, allowing for frame data to not be restricted by memory.
* Potentially moving 'png_to_frame.py' directly to the Pico, allowing conversion from png images to HUB-75 bytes in a precompilation step, without the need for seperate machine first. (DMA implementation would be a prerequisite for this, since an SD card would be needed to hold the compiled HUB-75 bytes and the much larger png images).
* Add interface from a live video input (such as HDMI or VGA), most likely by using a second Pico's state machines, or a standard Raspberry Pi, to serialize data in usable format and transmit to main Pico.
