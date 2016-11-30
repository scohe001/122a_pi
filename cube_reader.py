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
import subprocess

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

def get_cube():
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
                                #Find the means and run the numbers
                                hsv_mean = cv2.mean(cv2.cvtColor(raw, cv2.COLOR_BGR2HSV), mask)
                                bgr_mean = cv2.mean(raw, mask)
                                c = getColor(hsv_mean, bgr_mean)
                                if(c != 'N'): side[row][col] = c
                                if(side[row][col] != 'N'):
                                        cv2.putText(image, side[row][col], text_corner, cv2.FONT_HERSHEY_SIMPLEX, 1, 255)
                                #if(test%3 == 0): print hsv_mean,; print bgr_mean
                                        
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
                        
                
                # show the frame
                cv2.imshow("Frame", image)
                key = cv2.waitKey(1) & 0xFF

                # clear the stream in preparation for the next frame
                rawCapture.truncate(0)

                # if the `q` key was pressed, break from the loop
                if key == ord("q"):
                        break

def convert_sol(solution):
        sides = ["L", "F", "R", "B"]

        loaded = ["L", "F", "R", "B"]
        unloaded = ["U", "D"]
        final_sol = []

        for x in xrange(0, len(solution)):
                if solution[x][0] not in loaded: #If we're not loaded...
                        best = 0
                        #Figure out the most optimal way to flip
                        for y in xrange(x + 1, len(solution)):
                                if(solution[y][0] in unloaded): continue
                                if(solution[y][0] in [loaded[0], loaded[2]]): break
                                best = 1; break #it's either loaded 1 or loaded 3
                        if best is 0:
                                final_sol.append("LR")
                                loaded[1], unloaded[1] = unloaded[1], loaded[1]
                                loaded[3], unloaded[0] = unloaded[0], loaded[3]
                        else:
                                final_sol.append("BF")
                                loaded[0], unloaded[1] = unloaded[1], loaded[0]
                                loaded[2], unloaded[0] = unloaded[0], loaded[2]
                                
                        unloaded[0], unloaded[1] = unloaded[1], unloaded[0]
                        #print final_sol[len(final_sol)-1] + " ",
                                
                #We're loaded now, so throw stuff in
                final_sol.append(sides[loaded.index(solution[x][0])] + ("" if len(solution[x]) is 1 else solution[x][1]))
                #print loaded,; print " ",
                #print unloaded
                #print final_sol[len(final_sol)-1]
        return final_sol


fl = fcntl.fcntl(sys.stdin.fileno(), fcntl.F_GETFL)
fcntl.fcntl(sys.stdin.fileno(), fcntl.F_SETFL, fl | os.O_NONBLOCK)
print "Press enter to lock in a side of the cube!"
cube_state = get_cube()
cube_str = ""
cube_dict = {'G':'F', 'R':'R', 'O':'L', 'B':'B', 'W':'U', 'Y':'D'}
#                      0 1 2 3 4 5
#Read in in the order: F R B L U D
#Kociemba requires:    U R F D L B
face_order = [4, 1, 0, 5, 3, 2] #order Korciemba requires our faces
for face in face_order:
        for row in xrange(0, 3):
                for col in xrange(0, 3):
                        cube_str = cube_str + cube_dict[cube_state[face][col][row]]

print cube_str

#cube_str = "BDUBUFFFDLDFURDBFURRFBFLBLDDFLDDULURUUDRLLFBRRLLRBBBRU"

solution = kociemba.solve(cube_str)
print solution
solution = solution.split()
#print solution

#LR is right clockwise, LR' is left clockwise (right counter)
#BF is front clockwise, BF' is back clockwise (front counter)
moves = ["R", "R'", "R2", "L", "L'", "L2", "F", "F'", "F2", "B", "B'", "B2", "LR", "LR'", "BF", "BF'"]
final_sol = convert_sol(solution)             
print                
for x in  final_sol:
        print x + " ",
print
print len(solution)
print len(final_sol)

popen = subprocess.Popen(("/home/pi/Desktop/a.out", "5"), stdout=subprocess.PIPE)
popen.wait()
output = popen.stdout.read()

#TODO: loop through final_sol and send the corresponding index in moves
#TODO: over SPI to the Atmega1284. Call the c program?

#print moves.index(solution[1])
        
        

#For testing to split and send the kociemba string
#Another test string: ULRRUBDLFLDFRRULUURFUFFUDLBLBDFDBULFBDBRLDBRFDURFBBRDL
#sol = kociemba.solve("DUULUBBBDFUFURDFDLURRFFRBLURBLRDBFLBRFLLLDLFURFBRBDDUD")
#print sol.split()
