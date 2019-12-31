#To make python 2 and python 3 compatible code
from __future__ import division
from __future__ import absolute_import

#Imports
import sys
import cv2
import numpy
import requests
import json
import time
import asyncio

import VideoStream
from VideoStream import VideoStream
import ImageServer
from ImageServer import ImageServer

class CameraCapture(object):

    def __init__(
            self,
            videoPath,
            imageProcessingEndpoint = "",
            imageProcessingParams = "", 
            showVideo = False, 
            verbose = False,
            resizeWidth = 0,
            resizeHeight = 0,
            sendToHubCallback = None):
        self.videoPath = videoPath
        self.imageProcessingEndpoint = imageProcessingEndpoint
        if imageProcessingParams == "":
            self.imageProcessingParams = "" 
        else:
            self.imageProcessingParams = json.loads(imageProcessingParams)
        self.showVideo = showVideo
        self.verbose = verbose
        self.resizeWidth = resizeWidth
        self.resizeHeight = resizeHeight
        self.nbOfPreprocessingSteps = 0
        self.autoRotate = False
        self.sendToHubCallback = sendToHubCallback
        self.vs = None
        if self.resizeWidth != 0 or self.resizeHeight != 0:
            self.nbOfPreprocessingSteps +=1
        if self.verbose:
            print("Initialising the camera capture with the following parameters: ")
            print("   - Video path: ",self.videoPath)
            print("   - Image processing endpoint: " + self.imageProcessingEndpoint)
            print("   - Image processing params: " + json.dumps(self.imageProcessingParams))
            print("   - Show video: " + str(self.showVideo))
            print("   - Resize width: " + str(self.resizeWidth))
            print("   - Resize height: " + str(self.resizeHeight))
            print("   - Send processing results to hub: " + str(self.sendToHubCallback is not None))
            print()
        
        self.displayFrame = None
        if self.showVideo:
            self.imageServer = ImageServer(5012, self)
            self.imageServer.start()

    def __sendFrameForProcessing(self, frame):
        headers = {'Content-Type': 'application/octet-stream'}
        try:
            response = requests.post(self.imageProcessingEndpoint, headers = headers, params = self.imageProcessingParams, data = frame)
        except Exception as e:
            print('__sendFrameForProcessing Excpetion -' + str(e))
            return "[]"

        if self.verbose:
            try:
                print("Response from external processing service: (" + str(response.status_code) + ") " + json.dumps(response.json()))
            except Exception:
                print("Response from external processing service (status code): " + str(response.status_code))
        return json.dumps(response.json())

    def __displayTimeDifferenceInMs(self, endTime, startTime):
        return str(int((endTime-startTime) * 1000)) + " ms"

    def __enter__(self):
        self.vs = VideoStream(int(self.videoPath)).start()
        time.sleep(1.0) #needed to load at least one frame into the VideoStream class
        return self

    def get_display_frame(self):
        return self.displayFrame

    async def start(self):
        frameCounter = 0
        perfForOneFrameInMs = None
        while True:
            time.sleep(5)
            if self.showVideo or self.verbose:
                startOverall = time.time()
            if self.verbose:
                startCapture = time.time()

            frameCounter +=1
            frame = self.vs.read()

            if self.verbose:
                print("Frame number: " + str(frameCounter))
                print("Time to capture (+ straighten up) a frame: " + self.__displayTimeDifferenceInMs(time.time(), startCapture))
                startPreProcessing = time.time()
            
            #Pre-process locally           
            if self.nbOfPreprocessingSteps == 1 and (self.resizeWidth != 0 or self.resizeHeight != 0):
                preprocessedFrame = cv2.resize(frame, (self.resizeWidth, self.resizeHeight))

           
            if self.verbose:
                print("Time to pre-process a frame: " + self.__displayTimeDifferenceInMs(time.time(), startPreProcessing))
                startEncodingForProcessing = time.time()

            #Process externally
            if self.imageProcessingEndpoint != "":

                #Encode frame to send over HTTP
                if self.nbOfPreprocessingSteps == 0:
                    encodedFrame = cv2.imencode(".jpg", frame)[1].tostring()
                else:
                    encodedFrame = cv2.imencode(".jpg", preprocessedFrame)[1].tostring()

                if self.verbose:
                    print("Time to encode a frame for processing: " + self.__displayTimeDifferenceInMs(time.time(), startEncodingForProcessing))
                    startProcessingExternally = time.time()

                #Send over HTTP for processing
                response = self.__sendFrameForProcessing(encodedFrame)
                if self.verbose:
                    print("Time to process frame externally: " + self.__displayTimeDifferenceInMs(time.time(), startProcessingExternally))
                    startSendingToEdgeHub = time.time()

                #forwarding outcome of external processing to the EdgeHub
                if response != "[]" and self.sendToHubCallback is not None:
                    await self.sendToHubCallback(response)
                    if self.verbose:
                        print("Time to message from processing service to edgeHub: " + self.__displayTimeDifferenceInMs(time.time(), startSendingToEdgeHub))
                        startDisplaying = time.time()

            #Display frames
            if self.showVideo:
                try:
                    if self.nbOfPreprocessingSteps == 0:
                        

                        if self.verbose and (perfForOneFrameInMs is not None):
                            cv2.putText(frame, "FPS " + str(round(1000/perfForOneFrameInMs, 2)),(10, 35),cv2.FONT_HERSHEY_SIMPLEX,1.0,(0,0,255), 2)
#                            data = json.loads(response)
 #                           offset=35
  #                          for item in data["predictions"]:
   #                             offset = offset+35
    #                            cv2.putText(frame, item["tagName"]+" "+str(item["probability"]),(10, offset),cv2.FONT_HERSHEY_SIMPLEX,1.0,(0,0,255), 2)

                        self.displayFrame = cv2.imencode('.jpg', frame)[1].tobytes()
                    else:
                        if self.verbose and (perfForOneFrameInMs is not None):
                            cv2.putText(preprocessedFrame, "FPS " + str(round(1000/perfForOneFrameInMs, 2)),(10, 35),cv2.FONT_HERSHEY_SIMPLEX,1.0,(0,0,255), 2)
     #                       data = json.loads(response)
      #                      offset=35
       #                     for item in data["predictions"]:
        #                        offset = offset+35
         #                       cv2.putText(preprocessedFrame, item["tagName"]+" "+str(item["probability"]),(10, offset),cv2.FONT_HERSHEY_SIMPLEX,1.0,(0,0,255), 2)                        
                        
                        self.displayFrame = cv2.imencode('.jpg', preprocessedFrame)[1].tobytes()
                except Exception as e:
                    print("Could not display the video to a web browser.") 
                    print('Excpetion -' + str(e))
                if self.verbose:
                    if 'startDisplaying' in locals():
                        print("Time to display frame: " + self.__displayTimeDifferenceInMs(time.time(), startDisplaying))
                    elif 'startSendingToEdgeHub' in locals():
                        print("Time to display frame: " + self.__displayTimeDifferenceInMs(time.time(), startSendingToEdgeHub))
                    else:
                        print("Time to display frame: " + self.__displayTimeDifferenceInMs(time.time(), startEncodingForProcessing))
                perfForOneFrameInMs = int((time.time()-startOverall) * 1000)


            if self.verbose:
                perfForOneFrameInMs = int((time.time()-startOverall) * 1000)
                print("Total time for one frame: " + self.__displayTimeDifferenceInMs(time.time(), startOverall))

    def __exit__(self, exception_type, exception_value, traceback):
        if self.showVideo:
            self.imageServer.close()
            cv2.destroyAllWindows()
