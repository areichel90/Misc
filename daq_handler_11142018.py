###Script to read in comma separated string output from Agilent Data Loggers and
# export .csv columnizing file by timestamp, channel num., and reading, sorted by 
# channel number for easier handling.  Input from DAQ must be in Value, Timestamp, 
# Channel order. Configure DAQ to follow expected schema.  
# Direct bugs and questions to areichel@irobot.com

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os, sys

usage = "Usage: stop sucking"

sample_freq = 0
xaxis_margin = 25 #buffer before and after plot (whitespace)
channels_in = ('Voltage','Current','Processor','PMIC','Memory','WiFi','GPS','Ambient')
channels_plot = ('Power','Processor','PMIC','Memory','WiFi','GPS','Ambient')

while True:
	if len(sys.argv) == 2:
		file_in = sys.argv[1]

		if "/" in file_in:
			input = file_in.split('/')
			file = input[2]
		else:
			file = file_in
		file_name = file#[:-4] #removes file extension from string
		print "Parsing file: %s" %file_name
		daq_df = pd.read_csv(file_in,header=None,skiprows=1)

		count = 0
		df_array = []
		for i in daq_df.loc[0,]:
			count +=1
			df_array.append(i)
		
		def get_channels(df_in):
		    channels = []
		    for i in df_in['Channel']:
			if i not in channels:
			    channels.append(int(i))
			else:
			    continue
		    return channels			
					
		split_array = np.array_split(df_array,len(df_array)/3) #splits data into list of arrays (value,timestamp,channel)
		df_master = pd.DataFrame(split_array) #creates a column-wise dataframe from list of arrays
		df_master.columns = ('Value','Timestamp','Channel')
		channels = get_channels(df_master) #create list of channels found in log

		order = ['Timestamp','Channel','Value']
		df_ordered = df_master[order]
		df_out = df_ordered.sort_values(by = ['Channel','Timestamp'])
		print 'Channels in log: %s' %channels	
		
		#separate dataset into column-wise matrix by daq channel
		column_data = {}
		for channel in channels:
			data = df_out[df_out['Channel']==channel]
			column_data[channel] = data['Value'].values #creates array from channel values only		
		df_neat = pd.DataFrame.from_dict(column_data)
		df_neat.columns=channels_in
		power_in = df_neat['Voltage']*df_neat['Current'] #calculates input power to nav board
		df_neat['Power']=power_in #add power column to 'neat' dataframe
		print df_neat.head()
		runtime = np.arange(0,df_master['Timestamp'].max(),5) #minutes
		df_neat['Runtime']=runtime
		df_plot = df_neat[['Runtime','Power','Processor','PMIC','Memory','WiFi','GPS','Ambient']]	

		#plot data in timeseries
		fig, ax = plt.subplots(figsize=(16,4.75))
		ax1 = df_plot.plot(ax=ax,x='Runtime',y=['Processor','PMIC','Memory','WiFi','GPS','Ambient'],ylim=(0,80))
		ax2 = df_plot.plot(ax=ax, secondary_y=True,x='Runtime', y='Power')
		ax1.set_xlabel('Runtime (sec)')
		ax1.set_xlim(-xaxis_margin,df_plot['Runtime'].max()+xaxis_margin)
		ax1.set_ylabel('Temp. [Absolute] (degC)')
		ax2.set_ylabel('Power (W)')
		ax2.set_ylim(0,10)
		ax1.set_facecolor('#f6f6f6')
		ax1.grid()
		plt.title(file_name)

		plt_filename = "%s.jpg"%file_name
		print "Saving Plot as %s"%plt_filename	
		plt.savefig(plt_filename)
		csv_filename = file_name + '_out.csv'
		#df_neat.to_csv(csv_filename)	#save csv of formatted dataframe
		#print "%s created successfully!" %csv_filename
		plt.show()
		break

	if len(sys.argv) >= 2:
		print "Too Many Inputs!"
		print usage
		break

	if len(sys.argv) <=2:
		print "No Input File Detected"
		print usage
		break 