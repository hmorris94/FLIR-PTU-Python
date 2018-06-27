import serial
from warnings import warn


__all__ = ['PTU']


class PTU(object):

    def __init__(self, port, baud=9600, baud_already_set=False, timeout=60):

        self.serial = serial.Serial(port=port, baudrate=9600, timeout=timeout)
        self._TERM = b'\r\n'

        # Change baud rate if not default
        if baud in [600, 1200, 2400, 4800, 19200, 38400, 57600, 115200]:
            if not baud_already_set:
                self.__send_command(b'@(' + str(baud).encode() + b',0,F) ')
                self.__get_response()
            self.serial.baudrate = baud
        elif baud != 9600:
            warn('Baud should be one of {600, 1200, 2400, 4800, 9600, 19200, '
                 + '38400, 57600, 115200}. Defaulting to 9600.')

        self.__echo = self._determine_echo_state()
        self.__panResolution = self._determine_pan_resolution()
        self.__tiltResolution = self._determine_tilt_resolution()
        self.__minPan = self._determine_min_pan()
        self.__maxPan = self._determine_max_pan()
        self.__minTilt = self._determine_min_tilt()
        self.__maxTilt = self._determine_max_tilt()
        self.__maxPanSpeed = self._determine_max_pan_speed()
        self.__maxTiltSpeed = self._determine_max_tilt_speed()
        self.__controlMode = self._determine_control_mode()

    def __del__(self):

        self.halt()
        self.serial.read(self.serial.in_waiting)
        self.serial.close()

    # Basic serial functions

    def __send_command(self, command):
        '''Writes command to serial port, first checking for
        any pending inputs.'''
        if isinstance(command, str):
            command = command.encode()
        assert isinstance(command, bytes)

        if self.serial.in_waiting > 0:
            self.__handle_async_input(self.serial.read(self.serial.in_waiting))

        self.serial.write(command)

    def __get_response(self):
        '''Returns serial response as a string.'''
        return self.serial.read_until(self._TERM).decode()

    def __handle_async_input(self, contents):
        '''Read buffer should generally be empty before sending commands.
        This is called otherwise.'''
        warn('Device asynchronously displayed: ' + contents.encode(),
             category=RuntimeWarning)

    # Functions to determine initial states

    def _determine_echo_state(self):
        '''Return True if echo enabled, False otherwise.'''
        self.__send_command(b'E ')
        response = self.__get_response()
        if response == 'E * Echoing ON' + self._TERM.decode():
            return True
        elif response == '* Echoing OFF' + self._TERM.decode():
            return False
        else:
            raise RuntimeError(
                'When queried for echo state, device gave unexpected reply:',
                response)

    def _determine_pan_resolution(self):
        '''Returns panning resolution in arcseconds per position.'''
        response = self.send(b'PR ')
        # response == '* 23.142857 seconds arc per position'
        return float(response.split()[1])

    def _determine_tilt_resolution(self):
        '''Returns tilting resolution in arcseconds per position.'''
        response = self.send(b'TR ')
        # response == '* 11.571429 seconds arc per position'
        return float(response.split()[1])

    def _determine_min_pan(self):
        '''Returns minimum pan position set on the PTU.'''
        response = self.send(b'PN ')
        # len('* Minimum Pan position is ') == 26
        return int(response[26:])

    def _determine_max_pan(self):
        '''Returns maximum pan position set on the PTU.'''
        response = self.send(b'PX ')
        # len('* Maximum Pan position is ') == 26
        return int(response[26:])

    def _determine_min_tilt(self):
        '''Returns minimum tilt position set on the PTU.'''
        response = self.send(b'TN ')
        # len('* Minimum Tilt position is ') == 27
        return int(response[27:])

    def _determine_max_tilt(self):
        '''Returns maximum tilt position set on the PTU.'''
        response = self.send(b'TX ')
        # len('* Maximum Tilt position is ') == 27
        return int(response[27:])

    def _determine_max_pan_speed(self):
        '''Returns maximum panning speed set on the PTU.'''
        response = self.send(b'PU ')
        # '* Maximum Pan speed is 12000 positions/sec'
        return int(response.split()[5])

    def _determine_max_tilt_speed(self):
        '''Returns maximum tilting speed set on the PTU.'''
        response = self.send(b'TU ')
        # '* Maximum Tilt speed is 12000 positions/sec'
        return int(response.split()[5])

    def _determine_control_mode(self):
        '''Returns current control mode ('pos' or 'vel').'''
        response = self.send(b'C ')
        # '* PTU is in Independent Mode'
        return 'pos' if (response.split()[5].lower() == "independent") else 'vel'

    # Define a few properties

    @property
    def echo(self):
        '''Whether PTU is configured to repeat commands back to host.'''
        return self.__echo

    @echo.setter
    def echo(self, on):
        if not isinstance(on, bool):
            raise TypeError('Echo must be either True or False')
        if on:
            self.__send_command(b'EE ')
            self.__get_response()
            self.__echo = True
        else:
            self.__send_command(b'ED ')
            self.__get_response()
            self.__echo = False

    @property
    def controlMode(self):
        '''Control mode ('pos' or 'vel')'''
        return self.__controlMode

    # TODO - doesn't work
    @controlMode.setter
    def controlMode(self, mode):
        if not isinstance(mode, str):
            raise TypeError('Mode must be "pos" or "vel"')
        if mode.lower() == 'pos':
            self.__send_command(b'CI ')
            self.__get_response()
            self.__controlMode = 'pos'
        elif mode.lower() == 'vel':
            self.__send_command(b'CV ')
            self.__get_response()
            self.__controlMode = 'vel'
        else:
            raise ValueError('Mode must be "pos" or "vel"')

    @property
    def panResolution(self):
        '''Panning resolution in arcseconds per position.'''
        return self.__panResolution

    @property
    def tiltResolution(self):
        '''Tilting resolution in arcseconds per position.'''
        return self.__tiltResolution

    @property
    def minPan(self):
        '''Minimum pan position.'''
        return self.__minPan

    @property
    def maxPan(self):
        '''Maximum pan position.'''
        return self.__maxPan

    @property
    def minTilt(self):
        '''Minimum tilt position.'''
        return self.__minTilt

    @property
    def maxTilt(self):
        '''Maximum tilt position.'''
        return self.__maxTilt

    @property
    def maxPanSpeed(self):
        '''Maximum panning speed.'''
        return self.__maxPanSpeed

    @property
    def maxTiltSpeed(self):
        '''Maximum tilting speed.'''
        return self.__maxTiltSpeed

    def send(self, command, strip_echo=True):
        '''Wraps serial.write() with some additional checks.
        Returns response without terminating characters.'''
        command = command.upper()

        # Convert command to bytes, check for valid terminating character
        if isinstance(command, str):
            if command[-1] != ' ':
                raise ValueError("Commands must end with a space (' ')")
            command = command.encode()
        elif isinstance(command, bytes):
            if command.decode()[-1] != ' ':
                raise ValueError("Commands must end with a space (' ')")
        else:
            raise TypeError('Commands should be of type bytes')

        # TODO - See sections 4.5 and 7.1
        if command[:-1] in ['LE', 'LD', 'LU', 'PNU', 'PXU', 'TNU', 'TXU']:
            warn('Setting limits is not currently supported')
        # TODO - See section 4.6
        elif command[:-1] in ['I', 'S']:
            warn('Changing execution mode is not currently supported')
        # TODO - See section 4.9 and 4.10
        elif command[:-1] in ['ME', 'MD']:
            warn('Monitoring is not currently supported')

        self.__send_command(command)
        response = self.__get_response()

        if command == b'EE ':
            self.__echo = True
        elif command == b'ED ':
            self.__echo = False

        if strip_echo and self.echo:
            return response[len(command):len(response) - len(self._TERM)]
        else:
            return response[:len(response) - len(self._TERM)]

    # Set pan and tilt values

    def setPanPosition(self, pos, blocking=False):
        '''Command PTU to go to a pan position.'''
        resp = self.send(b'PP' + str(int(pos)).encode() + b' ')

        if blocking:
            self.send(b'A ')

        if resp[0] != '*':
            warn('Pan position response: ' + resp, RuntimeWarning)
            return False
        else:
            return True

    def setTiltPosition(self, pos, blocking=False):
        '''Command PTU to go to a tilt position.'''
        resp = self.send(b'TP' + str(int(pos)).encode() + b' ')

        if blocking:
            self.send(b'A ')

        if resp[0] != '*':
            warn('Tilt position response: ' + resp, RuntimeWarning)
            return False
        else:
            return True

    def setPosition(self, pan, tilt, blocking=False):
        '''Command PTU to go to a pan and tilt position.'''
        resp1 = self.setPanPosition(pan, blocking=False)
        resp2 = self.setTiltPosition(tilt, blocking=blocking)

        return (resp1 and resp2)

    def setPanSpeed(self, speed, blocking=False):
        '''Set a target panning speed.'''
        resp = self.send(b'PS' + str(int(speed)).encode() + b' ')

        if blocking:
            self.send(b'A ')

        if resp[0] != '*':
            warn('Pan speed response: ' + resp, RuntimeWarning)
            return False
        else:
            return True

    def setTiltSpeed(self, speed, blocking=False):
        '''Set a target tilting speed.'''
        resp = self.send(b'TS' + str(int(speed)).encode() + b' ')

        if blocking:
            self.send(b'A ')

        if resp[0] != '*':
            warn('Tilt speed response: ' + resp, RuntimeWarning)
            return False
        else:
            return True

    def setSpeed(self, pan, tilt, blocking=False):
        '''Set a target panning and tilting speed.'''
        resp1 = self.setPanSpeed(pan, blocking=False)
        resp2 = self.setTiltSpeed(tilt, blocking=blocking)

        return (resp1 and resp2)

    def setPositionAndSpeed(
            self, panPos, tiltPos, panSpeed, tiltSpeed, blocking=False):
        '''Command PTU to go to a pan and tilt position at a particular
        pan and tilt speed.'''
        resp = self.send(b'B' + str(int(panPos)).encode() + b','
                         + str(int(tiltPos)).encode() + b','
                         + str(int(panSpeed)).encode() + b','
                         + str(int(tiltSpeed)).encode() + b' ')

        if blocking:
            self.send(b'A ')

        if resp[0] != '*':
            warn('Set position and speed response: ' + resp, RuntimeWarning)
            return False
        else:
            return True

    def halt(self):
        '''Command PTU to stop moving.'''
        resp = self.send('H ')
        return (resp[0] == '*')

    # Get current pan and tilt data

    def getPanPosition(self):
        '''Returns current pan position.'''
        resp = self.send(b'PP ')
        # len('* Current Pan position is ') == 26
        return int(resp[26:])

    def getTiltPosition(self):
        '''Returns current tilt position.'''
        resp = self.send(b'TP ')
        # len('* Current Tilt position is ') == 27
        return int(resp[27:])

    def getPosition(self):
        '''Returns current pan and tilt position.'''
        return self.getPanPosition(), self.getTiltPosition()

    def getPanSpeed(self):
        '''Returns current panning speed.'''
        resp = self.send(b'PD ')
        # len('* Current Pan position is ') == 26
        return int(resp[26:])

    def getTiltSpeed(self):
        '''Returns current tilting speed.'''
        resp = self.send(b'TD ')
        # len('* Current Tilt position is ') == 27
        return int(resp[27:])

    def getSpeed(self):
        '''Returns current panning and tilting speed.'''
        return self.getPanSpeed(), self.getTiltSpeed()

    # Set pan and tilt offset from current position

    def setPanPositionOffset(self, offset, blocking=False):
        '''Command PTU to move pan position by a specified number of positions
        from current position.'''
        resp = self.send(b'PO' + str(int(offset)).encode() + b' ')

        if blocking:
            self.send(b'A ')

        if resp[0] != '*':
            warn('Pan position offset response: ' + resp, RuntimeWarning)
            return False
        else:
            return True

    def setTiltPositionOffset(self, offset, blocking=False):
        '''Command PTU to move tilt position by a specified number of positions
        from current position.'''
        resp = self.send(b'TO' + str(int(offset)).encode() + b' ')

        if blocking:
            self.send(b'A ')

        if resp[0] != '*':
            warn('Tilt position offset response: ' + resp, RuntimeWarning)
            return False
        else:
            return True

    def setPositionOffset(self, pan, tilt, blocking=False):
        '''Command PTU to move pan and tilt positions by a specified number of
        positions from current position.'''
        resp1 = self.setPanPositionOffset(pan, blocking=False)
        resp2 = self.setTiltPositionOffset(tilt, blocking=blocking)

        return (resp1 and resp2)

    def setPanSpeedOffset(self, offset, blocking=False):
        '''Command PTU to pan a specified number of arcseconds faster than its
        currently defined speed.'''
        resp = self.send(b'PD' + str(int(offset)).encode() + b' ')

        if blocking:
            self.send(b'A ')

        if resp[0] != '*':
            warn('Pan speed offset response: ' + resp, RuntimeWarning)
            return False
        else:
            return True

    def setTiltSpeedOffset(self, offset, blocking=False):
        '''Command PTU to tilt a specified number of arcseconds faster than its
        currently defined speed.'''
        resp = self.send(b'TD' + str(int(offset)).encode() + b' ')

        if blocking:
            self.send(b'A ')

        if resp[0] != '*':
            warn('Tilt speed offset response: ' + resp, RuntimeWarning)
            return False
        else:
            return True

    def setSpeedOffset(self, pan, tilt, blocking=False):
        '''Command PTU to pan and tilt a specified number of arcseconds faster
        than its currently defined speed.'''
        resp1 = self.setPanSpeedOffset(pan, blocking=False)
        resp2 = self.setTiltSpeedOffset(tilt, blocking=blocking)

        return (resp1 and resp2)

    # Get intended pan and tilt positions, in contrast to current positions

    def getTargetPanPosition(self):
        '''Returns pan position that PTU may be currently moving towards.'''
        resp = self.send(b'PO ')
        # len('* Target Pan position is ') == 25
        return int(resp[25:])

    def getTargetTiltPosition(self):
        '''Returns tilt position that PTU may be currently moving towards.'''
        resp = self.send(b'TO ')
        # len('* Target Tilt position is ') == 26
        return int(resp[26:])

    def getTargetPosition(self):
        '''Returns pan and tilt positiosn that PTU may be currently moving
        towards.'''
        return self.getTargetPanPosition(), self.getTargetTiltPosition()

    def getTargetPanSpeed(self):
        '''Returns currently set speed at which PTU should pan.'''
        resp = self.send(b'PS ')
        # '* Target Pan speed is 1000 positions/sec'
        return int(resp.split()[5])

    def getTargetTiltSpeed(self):
        '''Returns currently set speed at which PTU should tilt.'''
        resp = self.send(b'TS ')
        # '* Target Tilt speed is 1000 positions/sec'
        return int(resp.split()[5])

    def getTargetSpeed(self):
        '''Returns currently set speed at which PTU should pan and tilt.'''
        return self.getTargetPanSpeed(), self.getTargetTiltSpeed()

    # Determine positions necessary to move provided an angle (in degrees)

    def panAngleToPosition(self, angle):
        '''Convert an angle (in degrees) to a number of pan positions.'''
        return round(angle / (self.panResolution / 3600))

    def tiltAngleToPosition(self, angle):
        '''Convert an angle (in degrees) to a number of tilt positions.'''
        return round(angle / (self.panResolution / 3600))
