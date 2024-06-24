import pyvisa as visa
rm = visa.ResourceManager()
i_source = rm.open_resource('TCPIP0::169.254.47.133::1394::SOCKET', write_termination='\r', read_termination='\n')
i_source.write("*idn?")
print (i_source.read())

j_source = rm.open_resource('GPIB0::7::INSTR', write_termination='\r', read_termination='\n')
j_source.write("*idn?")
print (j_source.read())