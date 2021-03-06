import matplotlib.pyplot as plt
content = []
with open('s0-eth2.txt', 'r') as the_file:
	content = the_file.readlines()
print len(content)



def generateDetailedRateXY(content,index_X,index_Y):
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

def generateAveragedRateXY(content,index_X,index_Y):
        x_axis = []
        y_axis = []
        cumulative_time = 0.0
        x_axis.append(cumulative_time)
        rate= 0.0
        prev_total_byte = float(content[0].split(',')[index_Y])
        y_axis.append(rate)
        interval = 0.2 # set a interval that you want to average out
	end_time = interval #
        for i in range(len(content)):
                if i != 0:
                        # cal time
                        delta_time = float(content[i].split(',')[index_X])
                        cumulative_time = cumulative_time+float(delta_time)
			if cumulative_time < end_time:
                        	# cal rate
				pass
			else:
                        	curr_total_byte = float(content[i].split(',')[index_Y])
                        	rate = (curr_total_byte-prev_total_byte)*8/interval/1024
                        	prev_total_byte = curr_total_byte
                        	
				x_axis.append(end_time)
                        	y_axis.append(rate)
				end_time = end_time+interval
        return x_axis, y_axis


def generateNumOfFlowXY(content, index_X, index_Y):
	x_axis = []
        y_axis = []
        cumulative_time = 0.0
        x_axis.append(cumulative_time)
        #rate= 0.0
        init_flows = float(content[0].split(',')[index_Y])
        y_axis.append(init_flows)
        for i in range(len(content)):
                if i != 0:
                        # cal time
                        delta_time = float(content[i].split(',')[index_X])
                                # cal rate
                        cumulative_time = cumulative_time+float(delta_time)
                        num_of_flows = float(content[i].split(',')[index_Y])
			#print num_of_flows
                        x_axis.append(cumulative_time)
                        y_axis.append(num_of_flows)
        return x_axis, y_axis




rate1_X, rate1_Y = generateAveragedRateXY(content, 1, 2)
rate2_X, rate2_Y = generateAveragedRateXY(content, 1, 3)
fig = plt.figure()
ax1 = fig.add_subplot(211)
ax1.plot(rate1_X, rate1_Y, 'r')
ax1.plot(rate2_X, rate2_Y, 'b')

nVideo_X, nVideo_Y = generateNumOfFlowXY(content, 1, -2)
nData_X, nData_Y = generateNumOfFlowXY(content, 1, -1)
ax2 = fig.add_subplot(212)
ax2.plot(nVideo_X, nVideo_Y, 'r')
ax2.plot(nData_X, nData_Y, 'b')
plt.savefig('s0-eth2.png')

