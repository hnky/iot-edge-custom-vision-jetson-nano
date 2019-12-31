# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import os
import random
import sys
import time

import uuid
import asyncio

import azure.iot.device
from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device import Message

import CameraCapture
from CameraCapture import CameraCapture

async def send_to_Hub_callback(strMessage):
    print("Start sending message")
    print(strMessage)
    msg = Message(strMessage)
    msg.message_id = uuid.uuid4()
    msg.correlation_id = "test-1234"
    await hubManager.send_message_to_output(msg,"output1")
    print("Done sending message")
       

# global counters
SEND_CALLBACKS = 0

def send_confirmation_callback(message, result, user_context):
    global SEND_CALLBACKS
    SEND_CALLBACKS += 1

async def main(
        videoPath,
        imageProcessingEndpoint="",
        imageProcessingParams="",
        showVideo=False,
        verbose=False,
        resizeWidth=0,
        resizeHeight=0,
):
    '''
    Capture a camera feed, send it to processing and forward outputs to EdgeHub

    :param int videoPath: camera device path such as /dev/video0 or a test video file such as /TestAssets/myvideo.avi. Mandatory.
    :param str imageProcessingEndpoint: service endpoint to send the frames to for processing. Example: "http://face-detect-service:8080". Leave empty when no external processing is needed (Default). Optional.
    :param str imageProcessingParams: query parameters to send to the processing service. Example: "'returnLabels': 'true'". Empty by default. Optional.
    :param bool showVideo: show the video in a windows. False by default. Optional.
    :param bool verbose: show detailed logs and perf timers. False by default. Optional.
    :param int resizeWidth: resize frame width before sending to external service for processing. Does not resize by default (0). Optional.
    :param int resizeHeight: resize frame width before sending to external service for processing. Does not resize by default (0). Optional.ion(
    '''
    try:
        print("\nPython %s\n" % sys.version)
        print("Camera Capture Azure IoT Edge Module. Press Ctrl-C to exit.")
        try:
            global hubManager
            hubManager = IoTHubModuleClient.create_from_edge_environment()
            await hubManager.connect()
        except:
            print("Unexpected error IoTHub")
            return
            
        with CameraCapture(videoPath, imageProcessingEndpoint, imageProcessingParams, showVideo, verbose, resizeWidth, resizeHeight, send_to_Hub_callback) as cameraCapture:
            await cameraCapture.start()
    except KeyboardInterrupt:
        print("Camera capture module stopped")


def __convertStringToBool(env):
    if env in ['True', 'TRUE', '1', 'y', 'YES', 'Y', 'Yes']:
        return True
    elif env in ['False', 'FALSE', '0', 'n', 'NO', 'N', 'No']:
        return False
    else:
        raise ValueError('Could not convert string to bool.')


if __name__ == '__main__':
    try:
        VIDEO_PATH = os.getenv('VIDEO_PATH', 0)
        IMAGE_PROCESSING_ENDPOINT = os.getenv('IMAGE_PROCESSING_ENDPOINT', "http://192.168.163.225/image")
        IMAGE_PROCESSING_PARAMS = os.getenv('IMAGE_PROCESSING_PARAMS', "")
        SHOW_VIDEO = __convertStringToBool(os.getenv('SHOW_VIDEO', 'True'))
        VERBOSE = __convertStringToBool(os.getenv('VERBOSE', 'False'))
        RESIZE_WIDTH = int(os.getenv('RESIZE_WIDTH', 0))
        RESIZE_HEIGHT = int(os.getenv('RESIZE_HEIGHT', 0))

    except ValueError as error:
        print(error)
        sys.exit(1)

    asyncio.run(main(VIDEO_PATH, IMAGE_PROCESSING_ENDPOINT, IMAGE_PROCESSING_PARAMS, SHOW_VIDEO,VERBOSE,RESIZE_WIDTH, RESIZE_HEIGHT))
