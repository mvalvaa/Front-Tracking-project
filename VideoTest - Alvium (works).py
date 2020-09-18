from pymba import Vimba
import cv2


PIXEL_FORMATS_CONVERSIONS = {'BayerRG8': cv2.COLOR_BAYER_RG2RGB,}


with Vimba() as vimba:
  camera = vimba.camera(0)
  camera.open()

  camera.arm('SingleFrame')

  while(True):
    frame = camera.acquire_frame()
    
    image = frame.buffer_data_numpy()


    cv2.imshow('Video', image)
  

    if cv2.waitKey(1) & 0xFF == ord('q'):
      break

  camera.disarm()
  camera.close()
  cv2.destroyAllWindows()
