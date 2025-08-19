from ballisticgel import ballisticgel as bg
import chipwhisperer as cw
from chipshouter import ChipSHOUTER
import time
from matplotlib import pyplot as plt

import serial.tools.list_ports

# # List all available COM ports
# ports = serial.tools.list_ports.comports()
# for port in ports:
#     print(f"Port: {port.device}")
#     print(f"Description: {port.description}")
#     print(f"Hardware ID: {port.hwid}")
#     print("---")

cs = ChipSHOUTER(comport='/dev/cu.usbserial-NA4PPWV9')


def glitch_on():
    # print(cs) #get all values of device
    cs.voltage = 300
    cs.pulse.width = 160
    cs.armed = 1
    cs.pulse.repeat = 10
    cs.pulse.deadtime = 1
    time.sleep(1)
    cs.pulse = 10
    time.sleep(1)
    cs.armed = 0
    time.sleep(1)
    # print(scope)

def glitch_off():
    cs.armed = 0
    cs.pulse = 0

# voltage = 200  # Example voltage in volts
# scope.glitch.output_voltage = voltage


# find out what we have in ballisticgel
#print(dir(bg))

# find out what we have in chipwhisperer
#print(dir(cw))


#bg.main()


def main2():

    print(" CW521 Ballistic Gel Example Script ")
    print("  by NewAE Technology Inc")
    print(" This script will continue until you exit with Ctrl-C")

    cw521 = bg.CW521()
    cw521.con()

    doplot = True
    savefile = None
    #savefile = 'error_locations.bin' 

    #Raw method is slower but more flexible
    use_raw_method = False

    print("Settings: ")
    print("  Using slow (raw) mode  : " + str(use_raw_method))
    print("  Showing plot of results: " + str(doplot))
    print("  Results filename       : " + str(savefile))

    print("Starting main loop now: \n")

    while True:
        try:
            glitch_off()
            if use_raw_method:
                print("LOOP START: Writing data to SRAM...")
                cw521.raw_test_setup()
                input(" Hit enter when glitch inserted")
                print(" Reading SRAM data...")
                results = cw521.raw_test_compare()
            else:
                print("LOOP START: Writing data to SRAM...")
                cw521.seed_test_setup()
                print("GLITCHIIIIING")
                time.sleep(0.5)
                glitch_on()
                #input(" Hit enter when glitch inserted")
                print(" Reading SRAM data...")
                results = cw521.seed_test_compare()
            
            errdatay = results['errdatay']
            errdatax = results['errdatax']
            errorlist = results['errorlist']
            
            if doplot:
                plt.plot(errdatax, errdatay, '.r')
                plt.axis([0, 8192, 0, 4096])
                plt.show()

            if savefile:
                with open(savefile, "wb") as errfile:
                    errfile.write(bytearray(errorlist))

            print("")

        except:
            cw521.close()
            raise


main2()