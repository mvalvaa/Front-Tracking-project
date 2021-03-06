#Image processing software for Front Tracking method
#Instituto Português da Qaulidade - IPQ
#NOVA School of Science and Technologies - NOVA FCT

print("Python code is starting...")

import cv2
#from time import time
import numpy as np

import os
import tkinter as tk
import tkinter.constants
import tkinter.filedialog
import tkinter.font as tkFont
from tkinter import *
#import time

Start = 0            #variable that change start button when requirments are good
mode = None

#Live Mode
def live_mode():
    global mode
    mode = 'live'
    global video
    global fps
    global frame
    global img
    global video_length

    video = cv2.VideoCapture(0) #Start Video Capture
    video.set(cv2.CAP_PROP_FRAME_WIDTH,640)
    video.set(cv2.CAP_PROP_FRAME_HEIGHT,480)
    fps = video.get(cv2.CAP_PROP_FPS)
    print('Frames per second: ',fps)
    video_length = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

    insert_textbox('\nMode: Live')
    insert_textbox(' Frames per second: ' + str(fps))

    ok, frame = video.read()
    img = frame

    global Start
    Start += 1

#Archive mode
def archive_mode():
    global E1
    button_directory = tk.Button(window,text="Choose File",command = choose_file).grid(row=2,column=1)
    insert_textbox('\nMode: Archive')
    insert_textbox('\nSelect File')
    button_done = tk.Button(window,text="Done",command = done).grid(row=3,column=1)

def done():
    global video
    global fps
    global frame
    global img
    global video_length
    global E1
    global file

    file_name = file
    print(file_name)
    video = cv2.VideoCapture(file_name,0)           #Read Saved File

    fps = round(video.get(cv2.CAP_PROP_FPS))
    print('Frames per second: ',fps)
    video_length = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    print('Total frames: ',video_length)

    insert_textbox('\nFrames per second: ' + str(fps))
    insert_textbox('\nTotal frames: ' + str(video_length))

    ok, frame = video.read()
    img = frame

    global Start
    Start += 1

#Choose directory function
def choose_file():
    window.filename = tk.filedialog.askopenfilename()
    global file
    file = window.filename

#Close window function
def close_window():
    global mode
    if mode == 'live':
        video.release()
    print("Quit")
    window.destroy()

#Select Scale
def select_scale():

    img_scale = frame

    global d_tube
    global scale
    global middle_y
    global ROI1
    global E_outside_d
    global outside_d

    outside_d = float(E_outside_d.get())
    ROI1 = cv2.selectROI(img_scale)         #select tube diameter
    d_tube = ROI1[3]
    scale = outside_d/d_tube
    print('scale: ', scale, ' mm/px')
    insert_textbox('\nScale: ' + str(scale) + ' mm/px')

    cv2.destroyAllWindows()

    middle_y = round(ROI1[1] + (d_tube/2))  #tube middle point

    global Start
    Start += 1

    cv2.destroyAllWindows()

#Select Threshold value
def select_Threshold():

    global thresh_value

    img5 = frame

    def nothing(x):
        pass

    cv2.namedWindow('Select Threshold')
    cv2.createTrackbar('Value','Select Threshold',0,255,nothing)

    while (1):
        #trackbar to select Threshold
        cv2.imshow('Select Threshold',img5)
        cv2.putText(img5, 'Press q to accept', (50,50), cv2.FONT_HERSHEY_PLAIN, 1, (0,255,0), 1)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        thresh_value = cv2.getTrackbarPos('Value','Select Threshold')
        ret,img5 = cv2.threshold(frame,thresh_value,255,cv2.THRESH_BINARY)

    global Start
    Start += 1

    cv2.destroyAllWindows()

#Adjust Mask
def select_Mask():

    global mask
    global ROI1
    global black1
    global img6

    img6 = frame
    black1 = np.zeros((img.shape[0], img.shape[1], 3), np.uint8)  #create a black frame

    def nothing(x):
        pass

    cv2.namedWindow('Adjust Mask')
    cv2.createTrackbar('Value','Adjust Mask',0,int(ROI1[3]/2),nothing)

    while (1):                              #trackbar to select Threshold

        cv2.putText(img6, 'Press q to accept', (50,50), cv2.FONT_HERSHEY_PLAIN, 1, (0,255,0), 1)
        cv2.imshow('Adjust Mask',img6)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        value = cv2.getTrackbarPos('Value','Adjust Mask')

        black1 = np.zeros((img.shape[0], img.shape[1], 3), np.uint8)  #create a black frame
        black1 = cv2.rectangle(black1,(0,(ROI1[1]+value)),(img.shape[1],(ROI1[1]+ROI1[3]-value)),(255, 255, 255), -1)

        gray = cv2.cvtColor(black1,cv2.COLOR_BGR2GRAY)
        ret, mask = cv2.threshold(gray,127,255, 0)                  #mask to isolate tube

        img6 = cv2.bitwise_and(black1,frame,mask = mask)

    global Start
    Start += 1

    cv2.destroyAllWindows()

def insert_textbox(text):
    text_box.configure(state='normal')
    text_box.insert(tk.END, text)
    text_box.configure(state='disable')

#Create file with distance values
def print_results():
    global time_interval
    global scale
    global vector_of_dist
    file = open('Distances.txt','w')
    file.write('\nInside diameter: ' + str(inside_d))
    file.write('\nOutside diameter: ' + str(outside_d))
    file.write('\nTime interval: ' + str(time_interval))
    file.write('\nScale: ' + str(scale))
    for y in range (len(vector_of_dist)):
        volume = str(vector_of_dist[y-1])
        file.write(volume+'\n')
    file.close()
    insert_textbox('\nResults Printed')

def main():

    global vector_of_dist
    global scale
    global E_inside_d
    global inside_d
    inside_d = float(E_inside_d.get())
    Area = 3.14*((inside_d/2)*(inside_d/2))     #tube inside area

    ok, frame = video.read()
    img = frame
    delta_time = 1/fps                      #time between frame

    global E_time_interval
    global time_interval
    time_interval = float(E_time_interval.get())
    pos = 0
    x_coord = []
    last_time = 0
    last_pos = 0
    mean_flow = []
    i = 1
    flow = 0
    vector_of_flow = []
    vector_of_dist = []
    text_flow = 0
    start = 0
    finish = 0
    alfa = 0

    global mode
    if mode == 'live':
        alfa = 5

    while(True):

        ok, frame = video.read()
        img = frame

        #Apply mask
        masked_frame = cv2.bitwise_and(black1,frame,mask = mask)
        grey_frame = cv2.cvtColor(masked_frame, cv2.COLOR_BGR2GRAY)
        #Apply Threshold
        ret,threshold = cv2.threshold(grey_frame,thresh_value,255,cv2.THRESH_BINARY)
        threshold = 255 - threshold #invert color

        #Find Contours
        contours,hierarchy = cv2.findContours(threshold,1,cv2.CHAIN_APPROX_NONE)
        frame = cv2.drawContours(frame, contours, -1, (0,255,0), 1)

        if cv2.waitKey(1) & 0xFF == ord('s'):
            start = 1

        if start == 1:

            if i%(time_interval*fps) == 0:

                try:
                    for a in range (len(contours)):         #discover points with y equal to middle_y
                        for b in range (len(contours[a])):
                            for c in range (len(contours[a][b])):
                                if contours[a][b][c][1] == middle_y or contours[a][b][c][1] == (middle_y+1) or contours[a][b][c][1] == (middle_y-1):
                                    x_coord.append(contours[a][b][c][0])
                except Warning:
                    print ('No flow')

                try:
                    pos = max(x_coord)
                except ValueError:
                    pos = 0

                x_coord = []
                #Create point in the image
                cv2.circle(frame,(pos,middle_y),1,(255,0,0),5)
                #Calculate distance
                dist = last_pos - pos
                last_pos = pos
                vector_of_dist.append(dist)

                if i > (time_interval*fps):
                    #Calculate instant flow
                    flow = ((dist*scale*Area)/(delta_time*time_interval*fps)*3.6)
                    format(flow, '.6f')
                    print('\n', flow)
                    #print( dist)
                    print (pos)
                    #insert_textbox('\n' + str(pos))

                    vector_of_flow.append(flow)
                    try:
                        text_flow = np.mean(vector_of_flow)
                    except Exception:
                        text_flow = 0
                        pass

            cv2.circle(frame,(pos,middle_y),1,(255,0,0),5)
            #Show instant average flow
            cv2.putText(frame, 'Flow: ' + str(text_flow) + ' mL/h', (50,50), cv2.FONT_HERSHEY_PLAIN, 1, (0,255,0), 1)
            i = i + 1

        else:
            #Press 's' to start measurement
            cv2.putText(frame, 'Press s to start', (50,50), cv2.FONT_HERSHEY_PLAIN, 1, (0,255,0), 1)

        cv2.imshow('Video', frame)

        #Press 'q' to stop
        if cv2.waitKey(1) & 0xFF == ord('q') or i == (video_length-5*fps) or (alfa == 5 and i > (time_interval*fps) and pos < 30):
            insert_textbox('\nFinish')
            finish = 1
            break

    video.release()

    mean_flow = np.mean(vector_of_flow)
    print('Flow: ', mean_flow, ' mL/h')

    if finish == 1:
        button_print = tk.Button(window,text="Print Results",command = print_results).grid(row=3,column=3)

    video.release()
    cv2.destroyAllWindows()

#Create Window
window = tk.Tk()
window.title("Front Tracking")
window.geometry("700x400")
window.configure(bg='#bcdaeb')
window.grid_propagate(False) #tamanho da janela constante

times20 = tkFont.Font(family = "Times",size = 15,weight = "bold")

label_1=tk.Label(window, text = "Front Tracking software", font = times20, bg = "#bcdaeb").grid(row=0,column=2)

OptionList = ["Mode", "Live", "Archive"]
variable = tk.StringVar(window)
variable.set(OptionList[0])
opt = tk.OptionMenu(window, variable, *OptionList)
opt.grid(row=1,column=1)

def callback(*args):
    mode = variable.get()
    if mode == "Live":
        print("Live Mode")
        live_mode()
    if mode == "Archive":
        print("Archive Mode")
        archive_mode()

variable.trace("w", callback)

E_time_interval = tk.Entry(window)
E_time_interval.insert(0, 'Time interval (s)')
E_time_interval.grid(row=1, column = 2)

E_inside_d = tk.Entry(window)
E_inside_d.insert(0, 'Inside diameter (mm)')
E_inside_d.grid(row=2, column = 2)

E_outside_d = tk.Entry(window)
E_outside_d.insert(0, 'Outside diameter (mm)')
E_outside_d.grid(row=3, column = 2)

button_Scale = tk.Button(window,text="Choose Scale",command = select_scale).grid(row=5,column=2)
button_Threshold = tk.Button(window,text="Threshold Value",command = select_Threshold).grid(row=6,column=2)
button_Mask = tk.Button(window,text="Select Mask",command = select_Mask).grid(row=7,column=2)

button_Start = tk.Button(window,text="Start",command = main, bg = "#9af792").grid(row=1,column=3)
button_Quit = tk.Button(window, text="Quit", command = close_window).grid(row=2,column=3)

scroll = Scrollbar(window)
scroll.grid(row=9,column=3,rowspan=1,sticky='NS')

text_box = tk.Text(window, yscrollcommand = scroll.set,height = 5, width = 40)
text_box.grid(row=9, column=2, columnspan=1)
scroll.config(command = text_box.yview)

window.grid_rowconfigure((0,1,2,3,5,6,7,9,10), weight=1)
window.grid_rowconfigure((4,8), weight=2)
window.grid_columnconfigure((0,1,2,3,4), weight=2)

insert_textbox('... \nSelect mode')

tk.mainloop()
