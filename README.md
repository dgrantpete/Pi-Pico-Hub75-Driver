# LED-Matrix-Compiler
An open source Hub-75 Driver for the Raspberry Pi Pico that allows for the display of images, running up to 125MHz! THIS PROJECT IS A VERY EARLY WORK IN PROGRESS; better instructions for setting up will follow shortly!

NOTE: Currently only works on Windows for some of the read/write operations of 'png_to_frame.py', planning on making cross compatible soon!

To use: 
1. First go to 'config.ini' and follow the options there, namely 'dimensions'.
2. Put your desired image input files into directory, as specified in 'config.ini'.
3. Run 'png_to_frame.py'.
Now, onto the Raspberry Pi Pico:
4. Copy contents inside 'COPY_TO_PICO' to Raspberry Pi and save (easiest way to do this is from the Thonny editor).
5. Hook up pins on Pico to HUB 75 interface, and set up pin configuration in 'display.py'.
6. Copy output directory from 'png_to_frame.py', and upload it to the Pico. You will need to rename it 'frames' if you changed it from the default.
7. Power cycle the Pico, and it should be displaying your image(s)!

Feel free to contact me if you need help getting it to work! Still a work in progress, working on adding video support!
