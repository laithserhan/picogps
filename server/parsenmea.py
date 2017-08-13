# convert our nmea-like data to real coordinates
#1    = YYMMDDHHmm
#2    = Latitude in nmea format
#3    = Longitude in nmea format
#4    = E or W (negate Longitude if W)
#5 = ALtitude above datum
#6    = GPS quality indicator 4 fix 5 float
#7    = Horizontal dilution of position
#8    = Number of satellites in use [not those in view]
# this sample should be at 50.953711210 1.641447010
#sample = '1707301731,5057.2226726,138.4868206,W,130.71,5,1.4,8'
sample = '1707301731,6354.1234567,1638.1234567,W,130.71,5,1.4,8'

def parsefixdata(data):
	f =  data.split(',')			
	timestamp = f[0]
	# only works if above 10 degrees!
	lat = float(f[1][0:2]) + (float(f[1][2:])/60.0)
	# carefully take one or two figures from lat as we stripped 00s
	decpart = f[2].split('.')[0] # 138
	fracpart = decpart[len(decpart)-2:] # 38
	#print(decpart)
	decpart = decpart[:len(decpart)-2]
	#print(decpart)
	fracpart = fracpart + '.' + f[2].split('.')[1] # 4868206
	#print(fracpart)
	lon = float(decpart) + (float(fracpart)/60.0)
	E = f[3]
	if f[3] == 'W':
		lon = -lon
	alt = f[4]
	qual = f[5]
	hdop = f[6]		
	sats = f[7]
	location = (timestamp,lat,lon, alt, qual,hdop,sats)
	return location

loc = parsefixdata(sample)
print(loc)
