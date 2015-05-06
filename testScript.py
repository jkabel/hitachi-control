import microscope
m=microscope.Microscope(port="COM4", debug=True)

def take_mosaic(microscope, rows, columns, abc=False):
  x_fov=m.fov()[0]
  y_fov=m.fov()[1]
  overlap=0.9
  x_move=x_fov*overlap
  y_move=y_fov*overlap
  start_x=m.get_x_position()
  start_y=m.get_y_position()
  x=start_x
  y=start_y
  microscope.enable_raster_rotation()
  # Empirically determined on my scope as the delta between the stage xy and image xy -JK
  microscope.set_raster_rotation(3)
  photo=0
  for row in range(0,rows):
    for column in range(0,columns):
      if photo == 14:
        ack = raw_input('Please save buffered images and hit any key to continue...')
        photo=0
      microscope.trigger_abc()
      microscope.take_photo()
      photo+=1
      microscope.set_x_position(microscope.get_x_position() + x_move)
    microscope.set_y_position(microscope.get_y_position() + y_move)
    microscope.set_x_position(start_x)
  microscope.disable_raster_rotation()

def take_series(microscope, afc=False, aff=False, abc=False)





import microscope
m=microscope.Microscope(port="COM4", debug=True)
m.set_magnification(20000)
m.take_photo()
m.set_magnification(10000)
m.take_photo()
m.set_magnification(5000)
m.take_photo()
m.set_magnification(2000)
m.take_photo()
m.set_magnification(500)
m.take_photo()
m.set_magnification(200)
m.take_photo()
m.set_magnification(100)
m.take_photo()
