### Script to analyze results of Trident Board "Stress" tests.  NOT INTENDED FOR DISTRIBUTION, but if used, send questions to areichel@irobot.com ###

import pandas as pd
import time
import matplotlib.pyplot as plt
import numpy as np
import os, sys

now = time.strftime("%d%m%Y")
run = True
while run == True:
	if len(sys.argv) >= 2:
		if len(sys.argv) == 2:
		    Templog_in = sys.argv[1]
		    BKPlog_pres = False
		    DAQ_pres = False
		if len(sys.argv) == 3:
		    print"No DAQ File Present"
		    BKPlog_pres = True
		    DAQ_pres = False
		    Templog_in = sys.argv[1]
		    BKPlog_in = sys.argv[2]
		if len(sys.argv) == 4:
		    print"DAQ File Present, no DAQ data handling at this time."
		    BKPlog_pres = True
		    DAQ_pres = True
		    Templog_in = sys.argv[1]
		    BKPlog_in = sys.argv[2]
		    DAQ_in = sys.argv[3]
	else:
	    print 'Too Few Arguments. Please include templog.txt and BKPlog.txt paths.' 
	    run = False
	    break

	df_die = pd.read_csv(Templog_in,delimiter= ' ',skipinitialspace=True)
	df_speed = df_die.loc[:,('Fcpu','Fcpu.1','Fcpu.2','Fcpu.3')]
	df_temp = df_die.loc[:,('Ts0','Ts1','Ts2','Ts3','Ts4')]
	df_tempspeed = df_die.loc[:,('Fcpu','Fcpu.1','Fcpu.2','Fcpu.3','Ts0','Ts1','Ts2','Ts3','Ts4')]
	if BKPlog_pres == True:
	    df_Pin = pd.read_csv(BKPlog_in)
	if DAQ_pres == True:
	    df_DAQ_in = pd.read_csv(DAQ_in, header=2, skiprows=1)
	    DAQ_keep = df_DAQ_in.iloc[1:len(df_DAQ_in)-1,2]
	    print 'length of DAQ_keep: %i' %len(DAQ_keep)
	    daq_array = []
	    for i in DAQ_keep:
		daq_array.append(float(i))
	    df_DAQ = pd.DataFrame(daq_array)
	    df_temp = pd.concat([df_temp,df_DAQ],axis=1)
	    df_temp.columns=('Ts0','Ts1','Ts2','Ts3','Ts4','TC_Shield')
	    df_tempspeed = pd.concat([df_tempspeed,df_DAQ],axis=1)
	    df_tempspeed.columns=('Fcpu','Fcpu.1','Fcpu.2','Fcpu.3','Ts0','Ts1','Ts2','Ts3','Ts4','Shield')

	#Function to check if of the 4x CPU cores exhibited throttling during test
	def throttle_check(df_in):
	    max_cpu = 1267200
	    throttle = False
	    while throttle == False:
		for col in df_in:
		    array = df_in.loc[:,col]
		    for i in array:
		        if i == max_cpu:
		            continue
		        else:
		            print col
		            throttle = True
		            print 'Throttle Detected!'
		            break
		break

	#Function to generate time axis for time series plot.
	def make_x (df_in):
	    	axis_out = []
	    	sam_freq = 5 #sec/sample
	    	n = len(df_in.loc[:,'Ts0'])
		x_axis = range(0,(n*sam_freq),sam_freq)
	    	for i in x_axis:
		    axis_out.append(float(i)/60.0)
		df_xaxis = pd.DataFrame(axis_out,columns=['Runtime (min)'])
		df_tempspeed_time = pd.concat([df_xaxis,df_tempspeed],axis=1)
	    	return df_tempspeed_time

	#Function to handle and process BKPlog data. Returns a pandas dataframe of voltage and current	
	def BKP_cleanup(df_in):
	    arrayV = []
	    arrayi = []
	    arrayV_out = []
	    arrayi_out = []
	    
	    for col in df_in:
		for inst in df_in.loc[:,col]:
		    if inst != 'OK':
		        v = inst[-8:-4]
		        i = inst[-4:]
		        arrayV.append(v)
		        arrayi.append(i)
		    else:
		        continue
	    for i in arrayV:
		new_val = float(i)/1000.
		arrayV_out.append(new_val)
	    for i in arrayi:
		new_val = float(i)/10.
		arrayi_out.append(new_val)        
	    df_V = pd.DataFrame(arrayV_out)
	    df_i = pd.DataFrame(arrayi_out)
	    df_out = pd.concat([df_V,df_i],axis= True)
	    df_out.columns=['V_in','i_in']
	    return df_out

	#Checks for CPU throttling, prints Max CPU core temp, aggregates matrices and exports master csv
	#and plots CPU Speed, Temp, and input Voltage and Current
	df_tempspeed_time = make_x(df_tempspeed)
	throttle_check(df_speed)
	for col in df_temp:
		max_temp_CPU = df_temp.loc[:,col].max()
		print 'Max %s temp: %f C' %(col,max_temp_CPU)	

	#plot temperatures and CPU speeds on time series graph
	test_title = raw_input('Test Title: ')
	fig,ax = plt.subplots(figsize=(16,6))
	ax.set_facecolor('#f6f6f6')	
	df_tempspeed_time.plot(x ='Runtime (min)', y = ['Ts0','Ts1','Ts2','Ts3','Ts4'],legend=False, ax=ax)
	ax.set_xlabel('Runtime')
	ax.set_ylabel('Temperature')
	plt.legend(loc='center left', bbox_to_anchor=(1.025,0.5))
	df_tempspeed_time.plot(ax=ax,x='Runtime (min)',y=['Fcpu','Fcpu.1','Fcpu.2','Fcpu.3'],secondary_y=True, linestyle =  '--',legend = False)
	ax.grid('on')
	ax.set_title('Qualcomm CPU Temperature & Speed \n %s' %test_title)
	plt.ylabel('CPU Speed')
	plt.ylim(0,2800000)
	plt.savefig('%s.jpg' %test_title) 

	'''
	fig, ax1 = plt.subplots(figsize=(12,3))
	ax1.plot(df_temp)	
	ax1.set_ylim([0,100])
	ax1.set_ylabel('CPU Speed')
	ax1.legend()
	ax2 = ax1.twinx()
	ax2.plot(df_speed)
	ax2.set_xlim([0,len(df_speed)])
	ax2.set_ylim([1.0E6,1.50E6])
	ax2.set_ylabel('Temperature (C)')
	plt.title('CPU Temps/Speed')	
	fig.savefig('SpeedTemp_plot.jpg')

	
	df_temp.plot(figsize=(12,3),title='Core Temperatures')
	plt.savefig('CPUtemp_plot.jpg')
	df_speed.plot(secondary_y=True, figsize=(12,3),title='CPU Core Speeds', ylim=(1230000,1267200+100000))
	plt.savefig('CPUspeeds_plot.jpeg')

	speed_min = df_speed.loc[:,'Fcpu'].min()
	speed_max = df_speed.loc[:,'Fcpu'].max()
	throttle_perc = (float((speed_max - speed_min))/speed_max)#100
	print 'Percent Throttle: %f' %throttle_perc
	if BKPlog_pres == True:
		print 'Parsing BKP...'
		BKP_cleanup(df_Pin).plot(figsize=(12,3),title = 'Power Supply')
		plt.savefig('InputPower_plot.jpeg')
		avg_i_in = BKP_cleanup(df_Pin).loc[:,'i_in'].mean()
		max_i_in = BKP_cleanup(df_Pin).loc[:,'i_in'].max()
		print 'Average Current Draw: %f mA' %avg_i_in
		print 'Max Input Current: %f mA' % max_i_in
		df_out = pd.concat([df_die,BKP_cleanup(df_Pin)],axis=1)
		master_matrix = 'NavTherm_Test_'+ str(now) + '.csv'
		print 'Saving aggregated matrix to: %s' %master_matrix
		if DAQ_pres == False:
			df_out.to_csv(path_or_buf=master_matrix)
	if DAQ_pres == True:
		print 'Parsing DAQ...'
		df_DAQ.plot(figsize=(12,3), title='Shield Temp')
		plt.savefig('TEMPS_PLOT.jpeg')
		max_temp_shield = df_DAQ.max()
		print 'Max. Shield Temp: %f' %max_temp_shield
		print 'Max Temp. Delta: %f' %(float(max_temp_CPU)-float(max_temp_shield))
		print 'Length of Shield Temp file: %i' %len(df_DAQ)
		#df_delta = pd.concat([df_temp,df_DAQ],axis=1)
		#df_delta.columns=('Ts0','Ts1','Ts2','Ts3','Ts4','Shield_TC')
		#df_temp.plot(figsize=(16,4),title='CPU Temp v. Shield Temp')
		#plt.savefig('DELTA_PLOT.jpeg')
		df_delta_out = pd.concat([df_out,df_DAQ],axis=1)
	'''
	plt.show()
	run = False


