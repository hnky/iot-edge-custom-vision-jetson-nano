import os
import json
import random
import sys
import time

import asyncio
from six.moves import input
import threading

import uuid

import azure.iot.device
from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device import Message

def highestProbabilityTagMeetingThreshold(message, threshold):
    highestProbabilityTag = 'none'
    highestProbability = 0
    for prediction in message['predictions']:
        if prediction['probability'] > highestProbability and prediction['probability'] > threshold:
            highestProbability = prediction['probability']
            highestProbabilityTag = prediction['tagName']
    #data = {}
    #data['tag'] = highestProbabilityTag
    #data['probability'] = highestProbability
    return highestProbabilityTag


async def main():
    # The client object is used to interact with your Azure IoT hub.
    module_client = IoTHubModuleClient.create_from_edge_environment()

    # connect the client.
    await module_client.connect()

    # define behavior for receiving an input message on input1
    async def input1_listener(module_client):
        while True:
            input_message = await module_client.receive_message_on_input("input1")  # blocking call
            print("the data in the message received on input1 was ")
            print(input_message.data)
            print("custom properties are")
            print(input_message.custom_properties)
            data = json.loads(input_message.data)
            highestProbabilityTag = highestProbabilityTagMeetingThreshold(data, 0.6)

            if highestProbabilityTag == "none":
              print("Not sending alert to hub")
            else:
              print("Sending alert to hub for: {} ".format(highestProbabilityTag))
              output_msg = Message(input_message.data)
              output_msg.message_id = uuid.uuid4()
              output_msg.correlation_id = "test-1234"
              await module_client.send_message_to_output(output_msg,"output1")
              print("Message send")


    # define behavior for halting the application
    def stdin_listener():
        print("Started listening...")
        while True:
          ja = True
          if ja == False:
            break
 #           selection = input("Press Q to quit\n")
  #          if selection == "Q" or selection == "q":
   #             print("Quitting...")
    #            break

    # Schedule task for listeners
    listeners = asyncio.gather(input1_listener(module_client))

    # Run the stdin listener in the event loop
    loop = asyncio.get_running_loop()
    user_finished = loop.run_in_executor(None, stdin_listener)

    # Wait for user to indicate they are done listening for messages
    await user_finished

    # Cancel listening
    listeners.cancel()

    # Finally, disconnect
    await module_client.disconnect()


if __name__ == "__main__":
    print("Start...")
    asyncio.run(main())
