from pymba import Vimba
from pymba import Frame
import cv2
import time

#global variables
i = 0
stop = 5

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
        exposure_time.value = 10000
        pixel_format = camera.feature('PixelFormat')
        pixel_format.value = 'Mono8'
        acquisition_mode = camera.feature('AcquisitionMode')
        acquisition_mode.value = 'Continuous'

        print('FPS: ', fps.value)
        print('Exposure time: ', exposure_time.value)
        print('Pixel format: ', pixel_format.value)
        print('Acquisition mode: ', acquisition_mode.value)

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

        cv2.imwrite('Scale_image.jpg scale_image)

        global resize_factor_w
        global resize_factor_h            
        global d_tube
        global scale
        global middle_y
        global ROI1
        global E_outside_d
        global outside_d

        #Scale image to feet screen
        scale_image_scaled = cv2.resize(scale_image,(1280,720))
        resize_factor_w = (4024/1280)
        resize_factor_h = (3026/720)

        outside_d = 2.3
        ROI1 = cv2.selectROI(scale_image_scaled)         #select tube diameter

        d_tube = ROI1[3]*resize_factor_h
        scale = outside_d/d_tube
        print('scale: ', scale, ' mm/px')
        middle_y = round((ROI1[1])*resize_factor_h + (d_tube/2))  #tube middle point

        camera.disarm()
        camera.close()
        

##  CALLBACK FOR CAMERA.ARM
def image_processing_callback(frame: Frame):
    
    global i
    i = int(format(frame.data.frameID))
    print('Frame', i)

    # get a copy of the frame data
    image = frame.buffer_data_numpy()

    # display image
    cv2.imshow('Image', image)
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

        #Acquire and stream frames (to the specified callback function)
        try:
            while True:
                camera.start_frame_acquisition()
                if i == stop:
                    break
        except KeyboardInterrupt:                   ##press ctrl/C to pass
            pass
        
        #time.sleep(2)

        #Stop acquiring frames and close camera
        camera.stop_frame_acquisition()
        camera.disarm()
        camera.close()
