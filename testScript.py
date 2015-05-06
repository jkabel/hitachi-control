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

def take_series(microscope, af=False, abc=False):
  series=[]
  photo=0
  while ack == "y":
    position_x = microscope.get_x_position()
    position_y = microscope.get_x_position()
    mag = microscope.get_magnification()
    series.append([position_x, position_y, mag])
    ack = raw_input('Add another point? (y/n)')
  for point in series:
    microscope.set_x_position(point[0])
    microscope.set_y_position(point[1])
    microscope.set_magnification(point[2])
    if abc:
      microscope.trigger_abc()
    if af:
      microscope.set_magnification(point[2]*5)
      microscope.trigger_autofocus_coarse()
      microscope.trigger_autofocus_fine()
      microscope.set_magnification(point[2])
    if photo == 14:
      ack = raw_input('Please save buffered images and hit any key to continue...')
      photo=0
    microscope.take_photo()
    photo+=1
    

