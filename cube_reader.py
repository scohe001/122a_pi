# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import numpy as np
from matplotlib import pyplot as plt
import argparse
import time
import cv2
import sys
import os
import fcntl
from copy import deepcopy
import kociemba

#TODO setup these guys for the Chung labs
def getColor(hsv_mean, bgr_mean):
        #these first three are bomb af
        if bgr_mean[0] < 15 and bgr_mean[1] > 120 and bgr_mean[2] > 120:
                return "Y"
        if bgr_mean[0] > 50 and bgr_mean[1] > 100 and bgr_mean[2] > 100:
                return "W"
        if bgr_mean[2] != 0 and bgr_mean[1] >= 50 and bgr_mean[1] / bgr_mean[2] > 2:
                return "G"
        if bgr_mean[0] < 80 and bgr_mean[1] > 15 and bgr_mean[1] < 100 and bgr_mean[2] > 200 and hsv_mean[2] > 180:
                return "O"
        if bgr_mean[0] < 25 and bgr_mean[1] < 60 and bgr_mean[2] > 110:
                return "R"
        if hsv_mean[0] > 50 and bgr_mean[1] < 50 and bgr_mean[2] < 50:
                return "B"
        return "N"

def main():
        # initialize the camera and grab a reference to the raw camera capture
        camera = PiCamera()
        camera.resolution = (640, 480)
        camera.framerate = 32
        rawCapture = PiRGBArray(camera, size=(640, 480))

        # allow the camera to warmup
        time.sleep(0.1)

        cube_sz = 40 #Size of the cube template on screen
        cube = [[['N', 'N', 'N'], ['N', 'N', 'N'], ['N', 'N', 'N']], [['N', 'N', 'N'], ['N', 'N', 'N'], ['N', 'N', 'N']], [['N', 'N', 'N'], ['N', 'N', 'N'], ['N', 'N', 'N']], [['N', 'N', 'N'], ['N', 'N', 'N'], ['N', 'N', 'N']], [['N', 'N', 'N'], ['N', 'N', 'N'], ['N', 'N', 'N']], [['N', 'N', 'N'], ['N', 'N', 'N'], ['N', 'N', 'N']]]
        sides = ["Orange -> Green <- Red", "Green -> Red <- Blue", "Red -> Blue <- Orange", "Blue -> Orange <- Green", "Orange -> White <- Red", "Orange -> Yellow <- Red"]
        sides_vals = ['G', 'R', 'B', 'O', 'W', 'Y']
        side = [['N', 'N', 'N'], ['N', 'N', 'N'], ['N', 'N', 'N']]
        curr_side = 0
        test = 0

        print "Show me side: " + sides[curr_side]
        # capture frames from the camera
        for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
                # grab the raw NumPy array representing the image, then initialize the timestamp
                # and occupied/unoccupied text
                image = frame.array
                raw = deepcopy(image)
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                edges = cv2.Canny(gray,100,25)
                im2, contours, h = cv2.findContours(edges,1,2)
                
                
                #cv2.line(image, (320-3*cube_sz, 240-cube_sz), (320+3*cube_sz, 240-cube_sz), (255, 255, 0))
                #cv2.line(image, (320-3*cube_sz, 240+cube_sz), (320+3*cube_sz, 240+cube_sz), (255, 255, 0))
                #cv2.line(image, (320-cube_sz, 240-3*cube_sz), (320-cube_sz, 240+3*cube_sz), (255, 255, 0))
                #cv2.line(image, (320+cube_sz, 240-3*cube_sz), (320+cube_sz, 240+3*cube_sz), (255, 255, 0))

                #mask[y:y+h,x:x+w] = 255
                totalmask = np.zeros(raw.shape[:2], np.uint8)
                #test += 1
                #for row in xrange(1,2):
                #       for col in xrange(1,2):
                for row in xrange(0,3):
                        for col in xrange(0,3):
                                #Draw cube template
                                cv2.rectangle(image, (320+(col*4-5)*(cube_sz/2), 240+(row*4-5)*(cube_sz/2)), (320+(col*4-3)*(cube_sz/2), 240+(row*4-3)*(cube_sz/2)), (255, 255, 0))
                                text_corner = ((320-3*cube_sz) + (2*row+1)*cube_sz - 10, (240-3*cube_sz) + (2*col+1)*cube_sz + 10)
                                #Create mask to only look at this cubie
                                mask = np.zeros(raw.shape[:2], np.uint8)
                                mask[240+(cube_sz/2)*(col*4-5):240+(cube_sz/2)*(col*4-3),320+(cube_sz/2)*(row*4-5):320+(cube_sz/2)*(row*4-3)] = 255
                                totalmask = cv2.bitwise_or(totalmask, mask)
                                #Find the means and run the numbers
                                hsv_mean = cv2.mean(cv2.cvtColor(raw, cv2.COLOR_BGR2HSV), mask)
                                bgr_mean = cv2.mean(raw, mask)
                                c = getColor(hsv_mean, bgr_mean)
                                if(c != 'N'): side[row][col] = c
                                if(side[row][col] != 'N'):
                                        cv2.putText(image, side[row][col], text_corner, cv2.FONT_HERSHEY_SIMPLEX, 1, 255)
                                if(test%3 == 0): print hsv_mean,; print bgr_mean
                                        
                #cv2.imshow("Mask", cv2.bitwise_and(raw, raw, mask=totalmask))
                                        
                try:
                        stdin = sys.stdin.read()
                        if curr_side < 6 and stdin[0] == "\n":
                                if 'N' in side:
                                        print "Not everything has been read!"
                                elif side[1][1] != sides_vals[curr_side]:
                                        print "This doesn't look like the right side..."
                                        print "Looking for " + sides_vals[curr_side] + " found " + side[1][1]
                                        print side
                                else:
                                        cube[curr_side] = deepcopy(side)
                                        print sides_vals[curr_side] + " was read!"
                                        print side
                                        curr_side += 1
                                        if curr_side >= 6:
                                                print "If no more changes, type done!"
                                        else:
                                                print "Now show me: " + sides[curr_side]
                        elif len(stdin.split()) == 3:
                                params = stdin.split()
                                print "Changing (" + params[0] + ", " + params[1] + ") to " + params[2].upper()
                                cube[curr_side - 1][int(params[0])][int(params[1])] = params[2].upper()
                                print cube[curr_side - 1]
                                if curr_side < 6: print "Now show me: " + sides[curr_side]
                        elif "done" in stdin.lower():
                                if curr_side < 6:
                                        print "But I haven't seen all the sides yet!"
                                else:
                                        return cube
                        else:
                                print "Invalid input"
                except IOError:
                        pass
                        
        ##        for cnt in contours:
        ##            approx = cv2.approxPolyDP(cnt,0.01*cv2.arcLength(cnt,True),True)
        ##            #print len(approx)
        ##            if len(approx)==5: continue
        ##                #print "pentagon"
        ##                  #-1 means contours are filled. should use 1 for me
        ##                #cv2.drawContours(image,[cnt],0,255,-1)
        ##            elif len(approx)==3: continue
        ##                #print "triangle"
        ##                #cv2.drawContours(image,[cnt],0,(0,255,0),-1)
        ##            elif len(approx)==4:
        ##                #print "square"
        ##                cv2.drawContours(image,[cnt],0,(0,0,255),3)
        ##            elif len(approx) == 9: continue
        ##                #print "half-circle"
        ##                #cv2.drawContours(image,[cnt],0,(255,255,0),-1)
        ##            elif len(approx) > 15: continue
        ##                #print "circle"
        ##                #cv2.drawContours(image,[cnt],0,(0,255,255),-1)
                
        ##        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        ##        vals = [[np.array([50,100,100]), np.array([70,255,255])],
        ##                [np.array([110, 50, 50]), np.array([130, 255, 255])]]
        ##        height, width, channels = image.shape
        ##        res = np.zeros((height, width, 3), np.uint8)
        ##        res[:,:] = (255, 255, 255)
        ##        whiteimg = res
        ##        for x in xrange(0, 1):#len(vals)): 
        ##                shapeMask = cv2.inRange(hsv, vals[x][0], vals[x][1])
        ##                res = cv2.bitwise_and(res, whiteimg, mask=shapeMask)
        ##
        ##        greenMask = cv2.inRange(hsv, vals[0][0], vals[0][1])
        ##        blueMask = cv2.inRange(hsv, vals[1][0], vals[1][1])
        ##        gbMask = cv2.bitwise_or(greenMask, blueMask)
        ##        res = cv2.bitwise_and(image, image, mask=gbMask)
                
                

                #plt.subplot(121), plt.imshow(image,cmap = 'gray')
                #plt.title('Original Image'), plt.xticks([]), plt.yticks([])
                #plt.subplot(122), plt.imshow(edges,cmap = 'gray')
                #plt.title('Edge Image'), plt.xticks([]), plt.yticks([])

                #plt.show()
                
                # show the frame
                cv2.imshow("Frame", image)
                key = cv2.waitKey(1) & 0xFF

                # clear the stream in preparation for the next frame
                rawCapture.truncate(0)

                # if the `q` key was pressed, break from the loop
                if key == ord("q"):
                        break

fl = fcntl.fcntl(sys.stdin.fileno(), fcntl.F_GETFL)
fcntl.fcntl(sys.stdin.fileno(), fcntl.F_SETFL, fl | os.O_NONBLOCK)
print "Press enter to lock in a side of the cube!"
cube_state = main()
cube_string = ""
cube_dict = {'G':'F', 'R':'R', 'O':'L', 'B':'B', 'W':'U', 'Y':'D'}
#                      0 1 2 3 4 5
#Read in in the order: F R B L U D
#Kociemba requires:    U R F D L B
face_order = [4, 1, 0, 5, 3, 2] #order Korciemba requires our faces
for face in face_order:
        for row in xrange(0, 3):
                for col in xrange(0, 3):
                        cube_string = cube_string + cube_dict[cube_state[face][col][row]]

print cube_string

print kociemba.solve(cube_string)

#For testing to split and send the kociemba string
#Another test string: ULRRUBDLFLDFRRULUURFUFFUDLBLBDFDBULFBDBRLDBRFDURFBBRDL
#sol = kociemba.solve("DUULUBBBDFUFURDFDLURRFFRBLURBLRDBFLBRFLLLDLFURFBRBDDUD")
#print sol.split()
