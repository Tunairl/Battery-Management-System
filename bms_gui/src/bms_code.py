import time
import board
import adafruit_dht
from gpiozero import MCP3008
from time import strftime


cell_1   = MCP3008(channel=0)
cell_2   = MCP3008(channel=1)
cell_3   = MCP3008(channel=2)

# Initial the dht device, with data pin connected to:
dhtDevice = adafruit_dht.DHT22(board.D4,  use_pulseio=False)
# you can pass DHT22 use_pulseio=False if you wouldn't like to use pulseio.
# This may be necessary on a Linux single board computer like the Raspberry Pi,
# but it will not work in CircuitPython.
# dhtDevice = adafruit_dht.DHT22(board.D18, use_pulseio=False)

while True:
    try:
        full_datetime = strftime("%d/%m/%y at %I:%M%p")
        cell1 = (cell_1.value * 3.3) *4.3 # R1=4.7K R2=1K 5.7/1=5.7
        cell2 = (cell_2.value * 3.3) *3.127 # R1=10K R2=4.7K 14.7/4.7=
        cell3 = (cell_3.value * 3.3) *1.47 # R1=4.7K R2=10K 14.7/10=1.47
        # Print the values to the serial port
        temperature_c = dhtDevice.temperature
        temperature_f = temperature_c * (9 / 5) + 32
        print(
            "Date-Time: {} Temp: {:.1f} F / {:.1f} C cell1:{:.2f} V  cell2:{:.2f} V  cell3:{:.2f} V".format(
                full_datetime, temperature_f, temperature_c, cell1, cell2, cell3
            )
        )

    except RuntimeError as error:
        # Errors happen fairly often, DHT's are hard to read, just keep going
        print(error.args[0])
        time.sleep(2.0)
        continue
    except Exception as error:
        dhtDevice.exit()
        raise error

    time.sleep(2.0)

