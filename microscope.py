#!/usr/bin/python

#
# A control class for the Hitachi S3000N and attached 5-axis goniometer stage
# Portability to other Hitachi products of similar vintage likely, but not guaranteed (S2600N, S3500N, etc)
# Jacob Kabel, 2015, The University of British Columbia
#

# Required functions:
#   Read stage
#   Move stage
#   Correct scan rotation (scan X,Y not parallel to stage X,Y)
#   Activate auto focus
#   Trigger photo capture
#   Turn off high voltage when complete
#   Set magnification
#   
# Things to note:
#   Coordinates are given as a hex value in steps, 6 characters with leading zeroes, all caps
#     "{0:0>6X}".format(number) will get you there
#   int('ABC', base=16)
#   X = 00
#   Y = 01
#   R = 10
#   Z = 20
#   T = 21

import serial, io, time, re, sys

class Microscope:

  def __init__(self, port=None, debug=False):
    self.connection=None
    self.connect(port)
    self.iostream = io.TextIOWrapper(io.BufferedRWPair(self.connection,self.connection, 1), newline="\r", encoding='ascii', line_buffering = True)
    self.debug=debug
    # Number of pulses on each stepper that correspond to actual movements
    self._pulses_per_micron_x = 25.6
    self._pulses_per_micron_y = 25.6
    self._pulses_per_micron_z = 22.32
    self._pulses_per_degree_r = 1849
    self._pulses_per_degree_t = 3528
    # Controller/motor addresses for each axis
    self._x_address = '00'
    self._y_address = '01'
    self._z_address = '20'
    self._r_address = '10'
    self._t_address = '21'
    self._xy_axis = '0'
    self._zt_axis = '2'
    self._r_axis = '1'
    # Slew rates (empirical), microns/s
    self._x_slew_rate = 1250
    self._y_slew_rate = 1250
    # Internal position tracking
    self._x_position = self.get_x_position()
    self._y_position = self.get_y_position()
    self._z_position = self.get_z_position()
    self._r_position = self.get_r_position()
    self._t_position = self.get_t_position()

  class CommandError(Exception):
    def __init__(self, value):
      self.value = value
    def __str__(self):
      return repr(self.value)

  def connect(self, port):
    if self.connection:
      self.connection.close()
      self.connection = serial.Serial(port, baudrate=9600, bytesize=8, parity='N', timeout=30)
    else:
      self.connection = serial.Serial(port, baudrate=9600, bytesize=8, parity='N', timeout=30)
    if self.connection:
      return True
    else:
      return False 

  def _write(self, command):
    if self.debug:
      print "Writing {command}\r\n".format(command=command)
    self.iostream.write(unicode(command) + "\r")
    self.iostream.flush()
    response = self.iostream.readline()
    if self.debug:
      print response + "\r\n"
    stageError = re.compile("([0-9]+)(E[0-9])")
    stageErrorMatch = stageError.match(response)
    if response == "":
      # No response
      raise self.CommandError("No response from microscope")
    elif response == "E1":
      # Abnormal end error
      raise self.CommandError("Abnormal end error")
    elif response == "E2":
      # Unexecuted/unexecutable error
      raise self.CommandError("Unexecuted/unexecutable error")
    elif response == "E6":
      # Stage drive disconnected error
      raise self.CommandError("Stage drive disconnected")
    elif response == "E7":
      # Data reading error
      raise self.CommandError("Data reading error")
    elif response == "E8":
      # Undefined command received
      raise self.CommandError("Undefined command receieved")
    elif response == "E9":
      # Unacceptable set value received
      raise self.CommandError("Unacceptable value receieved")
    elif stageErrorMatch != None:
      if stageErrorMatch.groups()[1] == "E1":
        raise self.CommandError("Stage command error")
      elif stageErrorMatch.groups()[1] == "E2":
        raise self.CommandError("Stage communication error")
    else:
      return response

  def _await_halt_code(self, address, delay):
    time.sleep(delay)
    response = self.iostream.readline()
    if self.debug == True:
      print response
    haltCode = re.compile("([0-9]{2})([0-9])")
    haltCodeMatch = haltCode.match(response)
    code = haltCodeMatch.groups()[1]
    if self.debug == True:
      print response + "\r\n"
    if code == "0":
      # Good response
      return code
    elif code == "4":
      # Stage halted with abort command
      raise self.CommandError("Command halted")
    elif code == "1":
      # Beyond CW limit
      raise self.CommandError("Relevant axis beyond CW limit")
    elif code == "2":
      # Beyond CCW limit
      raise self.CommandError("Relevant axis beyond CCW limit")
    elif code == "6":
      # Within CW limit
      raise self.CommandError("Relevant axis within CW limit")
    elif code == "7":
      # Within CCW limit
      raise self.CommandError("Relevant axis within CCW limit")
    elif code == "8":
      # Overcurrent
      raise self.CommandError("Activation of overcurrent protection")
    elif code == "9":
      # Motor error
      raise self.CommandError("Motor error (no encode return pulse)")
    elif code == "K":
      # Touch sensor ON
      raise self.CommandError("Touch sensor ON")
    elif code == "L":
      # Touch sensor OFF
      raise self.CommandError("Touch sensor OFF")
    else:
      # Wholly unexpected
      raise self.CommandError("Completely unexpected response")

  def _stop_axis(self, address):
    try:
      response = self._write("#{address}S0".format(address=address))
      return response
    except CommandError as e:
      print e.value
      self.disable_stage_control()
      self.connection.close()
      sys.exit()

  def _get_position(self, address):
    try:
      stagePosition = re.compile("([0-2]+P)([0-9A-Fa-f]{6})([\+\-]?)")
      response = self._write("#{address}R1".format(address=address))
      stagePositionMatch = stagePosition.match(response)
      if stagePositionMatch:
        return int(stagePositionMatch.groups()[1], base=16)
    except self.CommandError as e:
      print e.value
      self.disable_stage_control()
      self.connection.close()
      sys.exit()

  def _set_position(self, address, position):
    try:
      response = self._write("#{address}M0 {position:0>6X}".format(address=address, position=position))
      return response
    except self.CommandError as e:
      print e.value
      self.disable_stage_control()
      self.connection.close()
      sys.exit()

  def _commit_move(self, axis):
    try:
      response = self._write("#{axis}0C0".format(axis=axis))
      return response
    except self.CommandError as e:
      print e.value
      self.disable_stage_control()
      self.connection.close()
      sys.exit()

  def _get_value(self, value):
    try:
      parameter = re.compile("R {0} (.*)".format(value=value))
      response = self._write("R {0}".format(value=value))
      parameterMatch = parameter.match(response)
      if parameterMatch:
        return parameterMatch.groups()[0]
    except self.CommandError as e:
      print e.value
      self.connection.close()
      sys.exit()

  def _set_value(self, command, value):
    try:
      response = self._write("{command} {value}".format(command=command, value=value))
      return response
    except self.CommandError as e:
      print e.value
      self.connection.close()
      sys.exit()

  def enable_stage_control(self):
    self._write("#STAGE ON")

  def disable_stage_control(self):
    self._write("#STAGE OFF")

  def fov(self):
    # Mag referenced to polaroid 545
    # Real output width is 127mm, 127000um
    # X scan width is therefore 127000/MAG
    # Real output width is 101.6mm, 101600um
    # X scan width is therefore 101600/MAG
    # Read the mag
    mag = self.get_magnification
    x = 127000/mag
    y = 101600/mag
    return (x, y)

  def estop(self):
    self.enable_stage_control()
    self._stop_axis(self._x_address)
    self._stop_axis(self._y_address)
    self._stop_axis(self._z_address)
    self._stop_axis(self._t_address)
    self._stop_axis(self._r_address)
    self.disable_stage_control

  def get_x_position(self):
    self.enable_stage_control()
    response = self._get_position(self._x_address)
    self.disable_stage_control()
    position = response/self._pulses_per_micron_x
    self._x_position = position
    return position

  def set_x_position(self, position):
    self.enable_stage_control()
    # Calculate delay to wait for halt code, subtract 5 seconds to put it in the readline timeout window
    delay = abs(position - self._x_position)/self._x_slew_rate
    if delay > 5:
      delay -= 5
    if self.debug == True:
      print str(delay) + "\r\n"
    # Set to int, rounded to the closest pulse on the stepper
    position = int(position*self._pulses_per_micron_x)
    self._set_position(self._x_address, position)
    self._commit_move(self._xy_axis)
    self._await_halt_code(self._x_address, delay)
    self.disable_stage_control()
    return position
    
  def get_y_position(self):
    self.enable_stage_control()
    response = self._get_position(self._y_address)
    self.disable_stage_control()
    position = response/self._pulses_per_micron_y
    self._y_position = position
    return position

  def set_y_position(self, position):
    self.enable_stage_control()
    # Calculate delay to wait for halt code, subtract 5 seconds to put it in the readline timeout window
    delay = abs(position - self._y_position)/self._y_slew_rate
    if delay > 5:
      delay -= 5
    if self.debug == True:
      print str(delay) + "\r\n"
    # Set to int, rounded to the closest pulse on the stepper
    position = int(position*self._pulses_per_micron_x)
    self._set_position(self._y_address, position)
    self._commit_move(self._xy_axis)
    self._await_halt_code(self._y_address, delay)
    self.disable_stage_control()
    return position

  def get_z_position(self):
    self.enable_stage_control()
    response = self._get_position(self._z_address)
    self.disable_stage_control()
    position = response/self._pulses_per_micron_z
    self._z_position = position
    return position

  def get_r_position(self):
    self.enable_stage_control()
    response = self._get_position(self._r_address)
    self.disable_stage_control()
    position = response/self._pulses_per_degree_r
    self._r_position = position
    return position

  def get_t_position(self):
    self.enable_stage_control()
    response = self._get_position(self._t_address)
    self.disable_stage_control()
    position = response/self._pulses_per_degree_t
    self._t_position = position
    return position

  def get_magnification(self):
    magnification = re.compile("([0-9\.]+)([k]?)")
    response = self._get_value("MAG")
    magnificationMatch = magnification.match(response)
    if magnificationMatch:
      if magnificationMatch.groups()[1] == 'k':
        return int(float(magnificationMatch.groups()[0])*1000)
      else:
        return int(magnificationMatch.groups()[0])
    else:
      False

  def get_photo_speed(self):
    photoSpeed = re.compile("([0-9]+)")
    response = self._get_value("MPSPEED")
    photoSpeedMatch = photoSpeed.match(response)
    if photoSpeedMatch:
      return int(photoSpeedMatch.groups()[0])
    else:
      False

  def get_hv(self):
    hv = re.compile("([0-9\.OF]+)")
    response = self._get_value("HV")
    hvMatch = hv.match(response)
    if hvMatch:
      if hvMatch.groups()[1] == 'OFF':
        return False
      else:
        return int(hvMatch.groups()[0])
    else:
      False

  def enable_raster_rotation(self):
    response = self._set_value('ROTATION', 'ON')
    return response

  def disable_raster_rotation(self):
    response = self._set_value('ROTATION', 'OFF')
    return response

  def set_raster_rotation(self, value):
    value = int(value)
    if value >= 0 and value <= 359:
      response = self._set_value('ROTATION', value)
      return response
    else
      False

  def take_photo(self):
    photoSpeed = self.get_photo_speed()
    response = self._set_value('#PHOTO', 'ON')
    time.sleep(photoSpeed+10)


#  def set_xy_position(self, x, y):
#    self.enable_stage_control
#    self.write("#00M0 {0:0>6X}".format(x))
#    self.write("#00C0")
#    self.write("#01M0 {0:0>6X}".format(y))
#    self.write("#00C0")
#    self.disable_stage_control




