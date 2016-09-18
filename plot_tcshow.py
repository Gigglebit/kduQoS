import matplotlib.pyplot as plt
content = []
with open('s0-eth2.txt', 'r') as the_file:
	content = the_file.readlines()
print len(content)



def generateRateXY(content,index_X,index_Y):
	x_axis = []
	y_axis = []
	cumulative_time = 0.0
	x_axis.append(cumulative_time)
	rate= 0.0
	prev_byte = float(content[0].split(',')[index_Y])
	y_axis.append(rate)
	for i in range(len(content)):
    		if i != 0:
    			# cal time
			delta_time = float(content[i].split(',')[index_X])
    			cumulative_time = cumulative_time+float(delta_time)
			# cal rate
			curr_byte = float(content[i].split(',')[index_Y])
			rate = (curr_byte - prev_byte)*8/delta_time/1024
			prev_byte = curr_byte
			x_axis.append(cumulative_time)
			y_axis.append(rate)
	return x_axis, y_axis




rate1_X, rate1_Y = generateRateXY(content, 1, 2)
rate2_X, rate2_Y = generateRateXY(content, 1, 3)
plt.plot(rate1_X, rate1_Y, 'r')
plt.plot(rate2_X, rate2_Y, 'b')
plt.show()
