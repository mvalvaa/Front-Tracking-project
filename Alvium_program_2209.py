from pymba import Vimba
from pymba import Frame
import cv2
import time
import numpy as np

## user inputs
#stop_image_processing = 16*3600*1
total_time = int(5*60*60)    #total time (s)
user_time_interval = 1    #time interval (s)
inside_d = 1.15                #inside diameter (mm)
outside_d = 1.6             #outside diameter (mm)

## GLOBAL VARIABLES
i = 0
Area = 3.14*((inside_d/2)*(inside_d/2))
pos = 0
x_coord = []
last_pos = 0 
last_time = 0
mean_flow = []
flow = 0
vector_of_flow = []
vector_of_dist = []
text_flow = 0
results = False

##  CAMERA SETUP (features)
def camera_setup():
    with Vimba() as vimba:
        #camera id
        camera_id = vimba.camera_ids()
        #access camera
        camera = vimba.camera(0)
        camera.open()

        #Change camera features
        fps = camera.feature('AcquisitionFrameRate')
        exposure_time = camera.feature('ExposureTime')
        exposure_time.value = 40000
        pixel_format = camera.feature('PixelFormat')
        pixel_format.value = 'Mono8'
        acquisition_mode = camera.feature('AcquisitionMode')
        acquisition_mode.value = 'Continuous'

        print('FPS: ', fps.value)
        print('Exposure time: ', exposure_time.value)
        print('Pixel format: ', pixel_format.value)
        print('Acquisition mode: ', acquisition_mode.value)

        camera.close()

##  SELECT SCALE
def select_scale():

    with Vimba() as vimba:
        camera = vimba.camera(0)
        camera.open()
        #Single frame capture
        camera.arm('SingleFrame')
        frame_data = camera.acquire_frame()
        frame = frame_data.buffer_data_numpy()
        scale_image = frame

        camera.disarm()
        camera.close()

        #cv2.imwrite('Scale_image.jpg', scale_image)

        global resize_factor_w
        global resize_factor_h
        global outside_d
        global ROI1            
        global d_tube
        global scale
        global middle_y

        #Scale image to fit screen
        scale_image_scaled = cv2.resize(scale_image,(1280,720))
        resize_factor_w = (4024/1280)
        resize_factor_h = (3026/720)

        ROI1 = cv2.selectROI(scale_image_scaled)         #select tube diameter
        cv2.destroyAllWindows()
        
        d_tube = ROI1[3]*resize_factor_h
        scale = outside_d/d_tube
        print('Scale: ', scale, ' mm/px')
        middle_y = round(ROI1[1]*resize_factor_h + (d_tube/2))  #tube middle point
        
        #Define meniscus search area
        global search_area

        y = int(middle_y - 100)
        y1 = int(middle_y + 100)
        x = 0
        x1 = 4024
        
        search_area_image = frame[y:y1, x:x1]
        #cv2.imwrite('Search_area.jpg', search_area_image)
        search_area = (y,y1,x,x1)

## SELECT THRESHOLD VALUE
def select_threshold():

    with Vimba() as vimba:
        camera = vimba.camera(0)
        camera.open()
        #Single frame capture
        camera.arm('SingleFrame')
        frame_data = camera.acquire_frame()
        frame = frame_data.buffer_data_numpy()
        threshold_image = frame

        camera.disarm()
        camera.close()

        global threshold_value

        def nothing(x):
            pass

        #create window with trackbar to select value
        cv2.namedWindow('Select Threshold')
        cv2.createTrackbar('Value','Select Threshold',0,255,nothing)
        #Scale image to fit screen
        threshold_image_scaled = cv2.resize(threshold_image,(1280,720))
        #threshold_image_scaled = cv2.GaussianBlur(threshold_image_scaled,(5,5),0)        
        threshold_image_scaled = cv2.cvtColor(threshold_image_scaled, cv2.COLOR_GRAY2BGR)
        threshold_image_scaled_double = threshold_image_scaled
        

        while (1):
            cv2.imshow('Select Threshold',threshold_image_scaled)
            cv2.putText(threshold_image_scaled, 'Press q to accept', (50,50), cv2.FONT_HERSHEY_PLAIN, 1, (0,255,0), 1)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break

            threshold_value = cv2.getTrackbarPos('Value','Select Threshold')
            ret,threshold_image_scaled = cv2.threshold(threshold_image_scaled_double,threshold_value,255,cv2.THRESH_BINARY)
            
        ret,threshold_image = cv2.threshold(threshold_image,threshold_value,255,cv2.THRESH_BINARY)
        #cv2.imwrite('Threshold_image.jpg', threshold_image)  

##  CALLBACK FOR CAMERA.ARM
def image_processing_callback(frame: Frame):

    #set pos value (equal to last_pos to create circle in all images)
    global pos
    global last_pos
    pos = last_pos

    #get frame number
    global i
    i = int(format(frame.data.frameID))
    #print('\nFrame', i)

    #get a copy of the frame data
    global image
    image = frame.buffer_data_numpy()
    frame_time = time.time()

    #Search area
    global search_area
    y = search_area[0]
    y1 = search_area[1]
    x = search_area[2]
    x1 = search_area[3]
    global search_area_image
    search_area_image = image[y:y1, x:x1]
    
    #Give color
    color_image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    if i%(16*user_time_interval) == 0 and (pos < 4000):
        
        ## PROCESSING PART

        #Time interval
        global last_time
        global time_interval
        time_interval = frame_time - last_time
        last_time = frame_time
        print('Time interval: ', time_interval)

        #Apply Threshold
        global threshold_value
        global threshold_image
        #blur = cv2.GaussianBlur(search_area_image,(5,5),0)
        ret,threshold_image = cv2.threshold(search_area_image,threshold_value,255,cv2.THRESH_BINARY)

        #Find Contours
        global color_image_contours
        global contours
        contours,hierarchy = cv2.findContours(threshold_image,1,cv2.CHAIN_APPROX_NONE)
        color = cv2.cvtColor(search_area_image, cv2.COLOR_GRAY2BGR)
        color_image_contours = cv2.drawContours(color, contours, -1, (0,255,0), 2)

        #Find meniscus base position
        global scale
        global Area
        global middle_y
        global x_coord
        global mean_flow
        global flow
        global vector_of_flow
        global vector_of_dist
        global text_flow

        middle = 100

        try:
            for a in range (len(contours)):         #discover points with y equal to middle_y
                for b in range (len(contours[a])):
                    for c in range (len(contours[a][b])):
                        if contours[a][b][c][1] == middle or contours[a][b][c][1] == (middle+1) or contours[a][b][c][1] == (middle-1):
                            x_coord.append(contours[a][b][c][0])
        except Warning:
            print ('No flow')

        try:
            x_coord = list(set(x_coord))
            x_coord.remove(max(x_coord))
            pos = max(x_coord)            
        except ValueError:
            pos = 0

        x_coord = []

        #Calculate distance
        dist = [(last_pos - pos),(time_interval)]
        last_pos = pos

        if pos != 0 and last_pos != 0:
            
            vector_of_dist.append(dist)
            
            #Calculate instant flow
            flow = ((dist[0]*scale*Area)/(time_interval)*3.6)
            #format(flow, '.6f')
            #print('\n', flow)
            #print( dist)
            print ('Pos: ', pos)

            
            vector_of_flow.append(flow)
            try:
                text_flow = np.mean(vector_of_flow)
            except Exception:
                text_flow = 0
                pass

    #Create point in the image
    cv2.circle(color_image,(pos,middle_y),20,(255,0,0),-1)
    
    #display image
    color_image_scaled = cv2.resize(color_image,(1280,720))
    #Show instant average flow
    cv2.putText(color_image_scaled, 'Average Flow: ' + str(text_flow) + ' mL/h          Instant flow: ' + str(flow) + ' mL/h', (50,50), cv2.FONT_HERSHEY_PLAIN, 1, (0,255,0), 1)
    cv2.imshow('Video Stream', color_image_scaled)
    cv2.waitKey(1)

## WHERE IMAGE PROCESSING IS MADE
def image_processing():       

    with Vimba() as vimba:
        #camera id
        camera_id = vimba.camera_ids()
        #access camera
        camera = vimba.camera(0)
        camera.open()
        
        #Start capture engine and create frames
        camera.arm(mode = 'Continuous', callback = image_processing_callback)
        global total_time
        #Acquire and stream frames (to the specified callback function)
        try:
            #start_time = time.time()
            while True:
                camera.start_frame_acquisition()
                if (pos > 5 and pos < 100) or (i*(1/16) > total_time):
                    break
        except KeyboardInterrupt:                   ##press ctrl/C to pass
            print('\n Interrupt \nClosing...')
            pass
    
        #Stop acquiring frames and close camera
        camera.stop_frame_acquisition()

        #Average flow
        print('\nAverage Flow: ', np.mean(vector_of_flow))
        print_results()
        
        cv2.imwrite('threshold_image.jpg', threshold_image)

        cv2.imwrite('search_area_image.jpg', search_area_image)
        
        cv2.imwrite('color_image_contours.jpg', color_image_contours)
        
        camera.disarm()
        camera.close()

## Print Results
def print_results():
    global results
    global scale
    global vector_of_dist
    global inside_d
    name = 'Distances ' + str(np.random.randint(low=10000, high=99999))+'.txt'
    file = open(name,'w')
    file.write('\nInside diameter: ' + str(inside_d))
    file.write('\nOutside diameter: ' + str(outside_d))
    file.write('\nScale: ' + str(scale))
    
    for y in range (len(vector_of_dist)):

        dist_time = str(vector_of_dist[y-1][0])+'      '+str(vector_of_dist[y-1][1])
        file.write('\n'+dist_time)

    file.close()
    print('\nResults saved')
    results = True

## MAIN
def main():

    end = False
    setup = False
    scale = False
    threshold = False
    processing = False
    global results
    
    while not end == True:
        
        input_ = int(input('\nChoose task: '))
        if input_ == 1:
            camera_setup()
            setup = True
            
        if input_ == 2:
            select_scale()
            scale = True
            
        if input_ == 3:
            select_threshold()
            threshold = True
            
        if input_ == 4:
            if (setup == True) and (scale == True) and (threshold == True):
                image_processing()
                processing = True
                print('\nImage processing done')
            else:
                print('Complete all tasks')
                
        if input_ == 0:
            if processing == True and results == False:
                print_results()                
            end = True
            print('Finish')

## START MAIN 
main()


    
