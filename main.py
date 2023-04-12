# This program is meant to read the data from the 4 DAQ channels at a high rate,
#   then publish the data to MQTT at 4 Hz packets with the data from that time
#   period

# The data is stored in a list of tuples, with the format (time, (data0, data1, data2, data3))

# The data is published to the MQTT broker at 5 Hz, with the data from the last 200ms

import nidaqmx
from nidaqmx.constants import AcquisitionType
import numpy as np
import paho.mqtt.client as mqtt
import json
import matplotlib.pyplot as plt

# MQTT setup
broker_address = ""  # TODO: Add broker address
client = mqtt.Client("DAQ")
client.connect(broker_address)


# DAQ setup
#  Create a DAQ task that reads from the 4 channels at 20000 Hz and returns the data in 500ms chunks
def acquire_data(device_name, channels, sampling_rate, samples_per_channel):
    # Combine device name and channel numbers into channel names
    channel_names = [f"{device_name}/ai{channel}" for channel in channels]

    # Create a task
    with nidaqmx.Task() as task:
        # Add voltage channels to the task
        for channel_name in channel_names:
            task.ai_channels.add_ai_voltage_chan(channel_name)

        # Set the task timing
        task.timing.cfg_samp_clk_timing(
            rate=sampling_rate,
            sample_mode=AcquisitionType.CONTINUOUS,
            samps_per_chan=samples_per_channel
        )

        # Start the task
        task.start()

        # Subscribe to /DAQ/Stop to stop the task
        client.subscribe("/DAQ/Stop")

        try:
            # Collect data in batches
            while True:
                # Read the data
                data = task.read(number_of_samples_per_channel=samples_per_channel)
                data_array = np.array(data)

                # Do a fourier transform on the data per channel
                data_array_fft = np.fft.fft(data_array)

                # Send the data to the MQTT broker
                client.publish("DAQ", json.dumps(data_array.tolist()))
                client.publish("DAQ_FFT", json.dumps(data_array_fft.tolist()))

                # Show a graph of the data in 2 windows
                plt.figure(1)
                plt.clf()
                plt.plot(data_array)
                plt.pause(0.001)
                plt.figure(2)
                plt.clf()
                plt.plot(data_array_fft)
                plt.pause(0.001)

                if client.on_message("/DAQ/Stop", "Stop"):
                    break

        except KeyboardInterrupt:
            # Stop the task if the user presses Ctrl+C
            task.stop()
            print("Data acquisition stopped.")


# Main function
def main():
    # Set the DAQ parameters
    device_name = "Dev1"  # TODO: Add device name
    channels = [0, 1, 2, 3]  # TODO: Add channels
    sampling_rate = 25_000  # TODO: Add sampling rate
    mqtt_rate = 5  # TODO: Add MQTT rate
    samples_per_channel = int(sampling_rate / mqtt_rate)

    # Start the data acquisition
    acquire_data(device_name, channels, sampling_rate, samples_per_channel)


if __name__ == "__main__":
    main()
