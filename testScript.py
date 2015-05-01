import microscope
m=microscope.Microscope(port="COM4", debug=True)
x_fov=m.fov()[0]
y_fov=m.fov()[1]

overlap=0.9
#top left
x_move=x_fov*overlap
y_move=y_fov*overlap
start_x=m.get_x_position()
start_y=m.get_y_position()
x=start_x
y=start_y
m.enable_raster_rotation()
# Empirically determined on my scope as the delta between the stage xy and image xy -JK
m.set_raster_rotation(3)

#4by4

photo=0
for row in range(0,4):
  for column in range(0,4):
    if photo == 14:
      ack = raw_input('Please save buffered images and hit any key to continue...')
      photo=0
    m.take_photo()
    photo+=1
    m.set_x_position(m.get_x_position() + x_move)
  m.set_y_position(m.get_y_position() + y_move)
  m.set_x_position(start_x)
m.disable_raster_rotation()

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
