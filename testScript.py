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
m.set_raster_rotation(3)

#4by4

for row in range(0,4):
  for column in range(0,4):
    m.take_photo()
    m.set_x_position(m.get_x_position() + x_move)
  m.set_y_position(m.get_y_position() + y_move)


  
