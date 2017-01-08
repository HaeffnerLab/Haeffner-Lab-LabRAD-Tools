import labrad
import numpy as np
from datetime import datetime as dt
from datetime import timedelta as td
from pytz import timezone
from math import pi
from functools import partial
import os
import traceback
import time
import warnings
import h5py
from bokeh.plotting import figure, output_file, show, reset_output
from bokeh.models import DatetimeTickFormatter, ColumnDataSource
from bokeh.layouts import gridplot, widgetbox, row, column, layout
from bokeh.models.widgets import Toggle, TextInput, Select, Div
from bokeh.models.annotations import Legend
from bokeh.io import curdoc, push_session, push
from bokeh.document import without_document_lock
from concurrent.futures import ThreadPoolExecutor
from tornado import gen


#global stuff
cxn = labrad.connection()
scope = cxn.dsox3034a
doc = curdoc()

executor = ThreadPoolExecutor(max_workers=2)
executor_pc = ThreadPoolExecutor(max_workers=2)

channel_flag = [True, True, True, True]
PC_flag = [False] 
res = [[], [], [], []]
res_PC = [None]
single_plot = [[], [], [], []]
multi = [[], [], [], []]
number_points_select_value = [100]
channel_select_value = ["Channel 1", "Channel 1"]
time_range_select_value = ["1000"]
trigger_level_input_value = [1]
PT = timezone("US/Pacific")
curr_day = [dt.now(PT).day]
reference_date = [dt(2017,1,1,0,0, tzinfo=PT)]
reference_offset = [(reference_date[0].utcoffset()-dt.now(PT).utcoffset()).total_seconds()]
channel_names = ["Channel 1","Channel 2", "Channel 3", "Channel 4"]
source_PC = ColumnDataSource(data=dict(x=[],y=[]))
home_dir = "/home/lattice/ITdata"

channel_button = []
source = []
source_load = []
for i in range(4):
    channel_button.append(Toggle(label="Channel" + str(i+1) + " On", button_type="success"))
    source.append(ColumnDataSource(data=dict(x=[], y=[])))
    source_load.append(ColumnDataSource(data=dict(x=[], y=[])))



#initialize scope
scope.connect((0x0957,0x17a4, '')) #include S/N if more than one device
scope.reset()
scope.autoScale()
scope.setAcquireType('hres')
scope.setWaveformPoints(100)
scope.setWaveformFormat('ASCii')



#Initialize Plots
#channel 1 plot
with warnings.catch_warnings(): #doesn't like having two wheel zooms
    warnings.simplefilter("ignore")
    single_plot[0] = figure(title="Channel 1:   Channel 1 ", x_axis_label='Time', y_axis_label='Volts', 
                    x_axis_type="datetime", tools="pan,ywheel_zoom,box_zoom,reset,save,xwheel_zoom,hover", 
                    active_scroll='ywheel_zoom')
single_plot[0].xaxis.major_label_orientation = pi/4
single_plot[0].line(x='x',y='y', source=source[0], legend=False, line_width=2)
single_plot[0].circle(x='x',y='y', source=source[0], size=5, color='black')

#channel 2 plot
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    single_plot[1] = figure(title="Channel 2:    Channel 2", x_axis_label='Time', y_axis_label='Volts', 
                    x_axis_type="datetime", tools="pan,ywheel_zoom,box_zoom,reset,save,xwheel_zoom,hover", 
                    active_scroll='ywheel_zoom')
single_plot[1].xaxis.major_label_orientation = pi/4
single_plot[1].line(x='x',y='y', source=source[1], legend=False, line_width=2)
single_plot[1].circle(x='x',y='y', source=source[1], size=5, color='black')

#channel 3 plot
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    single_plot[2] = figure(title="Channel 3:    Channel 3", x_axis_label='Time', y_axis_label='Volts', 
                    x_axis_type="datetime", tools="pan,ywheel_zoom,box_zoom,reset,save,xwheel_zoom,hover", 
                    active_scroll='ywheel_zoom')
single_plot[2].line(x='x',y='y', source=source[2], legend=False, line_width=2)
single_plot[2].circle(x='x',y='y', source=source[2], size=5, color='black')

#channel 4 plot
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    single_plot[3] = figure(title="Channel 4:    Channel 4", x_axis_label='Time', y_axis_label='Volts', 
                    x_axis_type="datetime", tools="pan,ywheel_zoom,box_zoom,reset,save,xwheel_zoom,hover", 
                    active_scroll='ywheel_zoom')
single_plot[3].xaxis.major_label_orientation = pi/4
single_plot[3].line(x='x',y='y', source=source[3], legend=False, line_width=2)
single_plot[3].circle(x='x',y='y', source=source[3], size=5, color='black')

#multi-plot
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    multi_plot = figure(title="Multi-plot", x_axis_label="Time", y_axis_label="Volts", x_axis_type="datetime",
                tools="pan,ywheel_zoom,box_zoom,reset,save,xwheel_zoom,hover", active_scroll='ywheel_zoom')
multi_plot.xaxis.major_label_orientation = pi/4
multi[0] = multi_plot.line(x='x',y='y', source=source[0], legend="Channel 1", line_width=2, color='blue')
multi_plot.circle(x='x',y='y', source=source[0], size=5, color='blue', line_width=.5, line_color='black')
multi[1] = multi_plot.line(x='x',y='y', source=source[1], legend="Channel 2", line_width=2, color='red')
multi_plot.circle(x='x',y='y', source=source[1], size=5, color='red', line_width=.5, line_color='black')
multi[2] = multi_plot.line(x='x',y='y', source=source[2], legend="Channel 3", line_width=2, color='green')
multi_plot.circle(x='x',y='y', source=source[2], size=5, color='green', line_width=.5, line_color='black')
multi[3] = multi_plot.line(x='x',y='y', source=source[3], legend="Channel 4", line_width=2, color='orange')
multi_plot.circle(x='x',y='y', source=source[3], size=5, color='orange', line_width=.5, line_color='black')
multi_plot.plot_width=1200
multi_plot.title.align = "center"

#pulse capture plot
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    pc_plot = figure(title="Pulse Capture", x_axis_label="Time (us)", y_axis_label="Volts",
                tools="pan,ywheel_zoom,box_zoom,reset,save,xwheel_zoom,hover", active_scroll='ywheel_zoom')
pc_plot.circle(x='x',y='y', source=source_PC, size=5, line_color='black', fill_color='red', line_width=.5)
pc_plot.xaxis.major_label_orientation = pi/4
pc_plot.plot_width=1200
pc_plot.plot_height=700
pc_plot.title.align = "center"

#load plot
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    load_plot = figure(title="Loaded Data", x_axis_label="Time", y_axis_label="Volts", x_axis_type="datetime",
                tools="pan,ywheel_zoom,box_zoom,reset,save,xwheel_zoom,hover", active_scroll='ywheel_zoom')
load_p_line_chan1= load_plot.line(x="x",y="y", source=source_load[0], legend="Channel 1", line_width=2, color="blue")
load_p_circ_chan1 = load_plot.circle(x="x",y="y", source=source_load[0], size=5, color="blue", line_width=.5, 
                                line_color='black')
load_p_line_chan2= load_plot.line(x="x",y="y", source=source_load[1], legend="Channel 2", line_width=2, color="red")
load_p_circ_chan2 = load_plot.circle(x="x",y="y", source=source_load[1], size=5, color="red", line_width=.5, 
                                line_color='black')
load_p_line_chan3= load_plot.line(x="x",y="y", source=source_load[2], legend="Channel 3", line_width=2, color="green")
load_p_circ_chan3 = load_plot.circle(x="x",y="y", source=source_load[2], size=5, color="green", line_width=.5, 
                                line_color='black')
load_p_line_chan4= load_plot.line(x="x",y="y", source=source_load[3], legend="Channel 4", line_width=2, color="orange")
load_p_circ_chan4 = load_plot.circle(x="x",y="y", source=source_load[3], size=5, color="orange", line_width=.5, 
                                line_color='black')
load_plot.plot_width=1200
load_plot.plot_height=700
load_plot.title.align="center"



# Periodic callback functions
# unlocked callback
@gen.coroutine
@without_document_lock
def updateChannels():
    if 'acq_period_list' not in globals():
        global acq_period_list
        acq_period_list = [0 for i in range(200)]
    
    if len(acq_period_list) != float(acq_period_select.value)/.5:
        acq_period_list.append(0)
        return
    else:
        acq_period_list = [0]
    
    if channel_flag != [False, False, False, False]:  
        scope.digitize(0)
    
    for i in range(1,5):
        if channel_flag[i-1]:
            res[i-1] = yield executor.submit(updateChannel, i)
        else:
            res[i-1] = [],[]
    
    doc.add_next_tick_callback(partial(updatePlots, res[0], res[1], res[2], res[3]))


def updateChannel(channel):
    scope.setWaveformSource(channel)
    scope.setWaveformPoints(int(num_avgs_select.value))
    curr_data = np.mean(scope.getWaveformData()) 
    preamble = scope.getWaveformPreamble()
    now = dt.now(PT)
    t = [now + td(seconds=i*float(preamble[0])) for i in range(int(num_avgs_select.value))]
    curr_time = t[len(t)/2]
    return [curr_time], [curr_data]
        

# the unlocked callback uses this locked callback to safely update
@gen.coroutine
def updatePlots(*args):
    for i in range(4):
        source[i].stream(dict(x=args[i][0], y=args[i][1]))
        

@gen.coroutine
@without_document_lock
def updateChannelsPC():
    if not PC_flag[0]:
        return
    curr_channel = int(channel_select_value[1][-1])
    scope.setTriggerSource(curr_channel)
    scope.setTriggerLevel(trigger_level_input_value[0])
    scope.setTriggerReferenceLeft()
    scope.setTimeRange(float(time_range_select_value[0])/1000000.)
    scope.setWaveformSource(curr_channel)
    scope.setWaveformPoints(number_points_select_value[0])
    scope.digitize(curr_channel)
    result = yield executor_pc.submit(updateChannelPC, curr_channel)
    res_PC[0] = result
    doc.add_next_tick_callback(partial(updatePlotsPC, res_PC[0]))

def updateChannelPC(channel):
    if not PC_flag[0]:
        return
    
    preamble = scope.getWaveformPreamble()
    curr_data_list = list(scope.getWaveformData())
    t_PC = [i*float(preamble[0])*1E6 for i in range(scope.getWaveformPoints())]
    return t_PC, curr_data_list

@gen.coroutine
def updatePlotsPC(*args):
    if not PC_flag[0]:
        return
    
    source_PC.stream(dict(x=args[0][0], y=args[0][1]), rollover=10000)


def updateSave():
    date = dt.now(PT)
    if auto_save_button.active:
        return
    
    if curr_day[0] == date.day:
        return
    else:
    
    save_filepath = save_filepath_input.value
    if not os.path.exists(save_filepath):
        save_filepath_input.value = "Invalid file path!"
        auto_save_button.active = True
        return
    
    if save_filepath[-1] != "/":
        save_filepath += "/"
    
    name = save_filepath + str(curr_day[0].year) + "_" + str(curr_day[0].month) + "_" + str(curr_day[0].day) + ".h5"
    saveFiles(name)

    curr_day[0] = date.day    
    for i in range(4):
        source[i].data = dict(x=[],y=[])

def saveFiles(filename, PC_on=False):
    source_xlist = []
    source_ylist = []
    channel_list = []
    
    if not PC_on:
        beg, end = 0,4
    else:
        PC_channel = int(channel_name_select2.value[-1])-1
        beg, end = PC_channel, PC_channel+1
    
    for i in range(beg, end):
        c_name = channel_names[i]
        
        if not PC_on:
            s_xdata = source[i].data['x']
            s_ydata = source[i].data['y']
        else:
            s_xdata = source_PC.data['x']
            s_ydata = source_PC.data['y']
        for j in enumerate(s_xdata): #for some reason first element of s_xdata is a float sometimes, should figure out why
            if type(j[1]) == float:
                del s_xdata[j[0]]
                del s_ydata[j[0]]
        
        if s_xdata == [] or s_ydata == []: #got this situtation when testing with save period smaller than acquisition period
           print "Can't save empty lists."
           return
    
        x_temp = np.asarray(s_xdata)
        y = np.asarray(s_ydata)
        if not PC_on:
            x = [(i - reference_date[0]).total_seconds()-reference_offset[0] for i in x_temp] #convert datetime to float
        else:
            x = x_temp
        
        source_xlist.append(x)
        source_ylist.append(y)
        channel_list.append(c_name)

    with h5py.File(filename, "w") as hf:
        d = hf.create_group("data")
        cnames = hf.create_group("channel_names")
        if not PC_on:
        	beg, end = 0,4
        else:
        	beg, end = 0,1

        for i in range(beg, end):
            d.create_dataset("x"+str(i+1), data=source_xlist[i],
                    compression="gzip", compression_opts=9)
            d.create_dataset("y"+str(i+1), data=source_ylist[i],
                    compression="gzip", compression_opts=9)
            cnames.create_dataset("c"+str(i+1), data=channel_list[i])



#Callback functions
def channel_ButtonClick(channel):
    if PC_flag[0]:
        channel_button[channel-1].active = True
        return
    
    if channel_flag[channel-1]:
        channel_flag[channel-1]=False
        channel_button[channel-1].label = "Channel" + str(channel) + " Off"
    else:
        channel_flag[channel-1]=True
        channel_button[channel-1].label = "Channel" + str(channel) + " On"

def allOff_ButtonClick():
    for i in range(4):
        channel_flag[i] = False
        channel_button[i].label = "Channel" + str(i+1) + " Off"
        channel_button[i].active = True
    all_off_button.active = False

def allOn_ButtonClick():
    if PC_flag[0]:
        all_on_button.active = False
        return
    
    for i in range(4):
        channel_flag[i] = True
        channel_button[i].label = "Channel" + str(i+1) + " On"
        channel_button[i].active = False
    
    all_on_button.active = False

def pulseCapture_ButtonClick():
    if not PC_flag[0]:
        PC_flag[0] = True
        source_PC.data = dict(x=[],y=[])
        pc_plot.title.text = "Pulse Capture"
        scope.setAcquireType('normal')
        time_range_select_value[0] = time_range_input.value
        channel_select_value[1] = channel_name_select2.value
        number_points_select_value[0] = int(number_points_select.value)
        trigger_level_input_value[0] = float(trigger_level_input.value)
        for i in range(4):
            channel_flag[i] = False
            channel_button[i].label = "Channel" + str(i+1) + " Off"
            channel_button[i].active = True
        
        time.sleep(1) #Not sure if this is necessary, trying to prevent usb comm errors

    else:
        PC_flag[0] = False
        time.sleep(1) # See above
        scope.reset()
        scope.autoScale()
        scope.setAcquireType('hres')
        time.sleep(1) # See above

def reset_ButtonClick():
    if channel_flag == [False, False, False, False] and not PC_flag[0]:
        scope.reset()
        reset_button.active = False
    else:
        reset_button.active = False

def autoscale_ButtonClick():
    if channel_flag == [False, False, False, False] and not PC_flag[0]:
        scope.autoScale()
        autoscale_button.active = False
    else:
        autoscale_button.active = False

def autoSave_ButtonClick():
    if auto_save_button.active:
        auto_save_button.label = "Start Auto Save"
    else:
        auto_save_button.label = "Stop Auto Save"

def load_ButtonClick():
    if load_plot_type_select.value == "Multi-plot":
        updateLoad()
    elif load_plot_type_select.value == "Pulse Capture Plot":
        updateLoad(PC=True)
    load_button.active = False

def updateLoad(PC=False):
    for i in range(4):
        source_load[i].data = dict(x=[], y=[])
    filepath = load_file_input.value
    if not os.path.isfile(filepath):
        return
    
    if filepath.split(".")[-1] != "h5":
        return
    
    try:
        with h5py.File(filepath, "r") as hf:
            d = hf.get("data")
            c = hf.get("channel_names")
            legend = load_plot.legend[0]
        
            if not PC:
                beg, end = 1,5
            else:
                beg, end = 1,2
                for i in range(1,4):
                    legend.items[i].label['value'] = None
        
            for i in range(beg, end):
                x_temp = list(d.get("x"+str(i)))
                if not PC:
                    x = [reference_date[0] + td(seconds=j) for j in x_temp] #convert floats back to datetime
                    load_p_line_chan1.visible = True          
                else:
                    x = x_temp
		    load_p_line_chan1.visible = False

                y = list(d.get("y"+str(i)))
                cname = str(c.get("c"+str(i))[()])
                source_load[i-1].data['x'] = x
                source_load[i-1].data['y'] = y
                item = legend.items[i-1]
                item.label['value'] = cname

    except:
        for i in range(4):
            source_load[i].data = dict(x=[], y=[])
        traceback.print_exc()
        
    load_plot.title.text = filepath.split("/")[-1].split(".")[0]

def forceSave_ButtonClick():
    save_filepath = save_filepath_input.value
    if not os.path.exists(save_filepath):
        save_filepath_input.value = "Invalid file path!"
        force_save_button.active = False
        return
    
    if save_filepath[-1] != "/":
        save_filepath += "/"
    
    force_save_name = force_save_filename_input.value
    if force_save_name.split(".")[-1] != "h5":
        force_save_filename_input.value = "Invalid file name!"
        force_save_button.active = False
        return    
    
    saveFiles(save_filepath+force_save_name)
    force_save_button.active = False    

def savePC_ButtonClick():
    filepath = save_filepath_PC_input.value + save_filename_PC_input.value
    saveFiles(filepath, PC_on=True)
    save_PC_button.active = False
 
def acqPeriod_SelectChange(attr, old, new):
    acq_period_list[:] = [0]

def chanNameSelect1_SelectChange(attr, old, new):
    channel_name_input.value = channel_names[int(new[-1])-1] 

def channelName_InputChange(attr, old, new):
    n = int(channel_name_select1.value[-1])-1
    single_plot[n].title.text = "Channel " + str(n+1) + ":    " + new
    legend = multi_plot.legend[0]
    item = legend.items[n]
    for i in item.label:
        item.label[i] = new
    
    channel_names[n] = new

def triggerLevel_InputChange(attr, old, new):
    if float(new) < -20 or float(new) > 20:
        trigger_level_input.value = old

def timeRange_InputChange(attr, old, new):
    if float(new) < .002 or float(new) > 500000000:
        time_range_input.value = old

def saveFilepath_InputChange(attr, old, new):
    if not os.path.exists(new):
        save_filepath_input.value = old 

def forceSaveFilename_InputChange(attr, old, new):
    if "." not in new:
        force_save_filename_input.value = new + ".h5"
    elif new.split(".")[-1] != "h5":
        force_save_filename_input.value = old

def loadFile_InputChange(attr, old, new):
    if not os.path.isfile(new):
        load_file_input.value = old



#Initialize Widgets
# toggle buttons
all_off_button = Toggle(label="All Off", button_type="warning")
all_on_button = Toggle(label="All On", button_type="warning")
reset_button = Toggle(label="Reset Scope", button_type="warning")
autoscale_button = Toggle(label="AutoScale Scope", button_type="warning")
pulse_capture_button = Toggle(label="Pulse Capture", button_type="success")
auto_save_button = Toggle(label="Stop Auto Save", button_type="warning")
load_button = Toggle(label="Load", button_type="success")
force_save_button = Toggle(label="Force Save", button_type="warning")
save_PC_button = Toggle(label="Save", button_type="warning")


# Single select dropdown menus
acq_period_select = Select(title="Acquisition Period (s):", value="100",
                        options=[".5","1","10","100","300","1000"])
num_avgs_select = Select(title="Number of Points to Average:", value="100", 
                        options=["100","1000","10000","100000","1000000"])
channel_name_select1 = Select(title='Channel Select:', value="Channel 1",
                        options =["Channel 1", "Channel 2", "Channel 3", "Channel 4"])
channel_name_select2 = Select(title='Channel Names:', value="Channel 1",
                        options =["Channel 1", "Channel 2", "Channel 3", "Channel 4"])
number_points_select = Select(title="Number of Points", value="100",
                        options =["100", "200", "500", "1000", "5000", "10000", "100000", "1000000"])
load_plot_type_select = Select(title="Plot Type:", value="Multi-plot",
			options =["Multi-plot", "Pulse Capture Plot"])


# Text inputs
channel_name_input = TextInput(title="Name:")
trigger_level_input = TextInput(value="1", title="Trigger Level (V)")
time_range_input = TextInput(value="1000", title="Time Range (us)")
load_file_input = TextInput(value=home_dir, title="Load file:")
save_filepath_input = TextInput(value=home_dir, title="Save to directory:")
force_save_filename_input = TextInput(value=str(dt.now(PT).year)+"_"+str(dt.now(PT).month)+"_"+str(dt.now(PT).day)+".h5", 
                                title="Save as filename:")
save_filepath_PC_input = TextInput(value=home_dir, title="Save to directory:")
save_filename_PC_input = TextInput(value="PC_"+str(dt.now(PT).year)+"_"+str(dt.now(PT).month)+"_"+str(dt.now(PT).day)+".h5",
                                title="Save as filename:")


#setup event handlers
all_off_button.on_click(lambda x: allOff_ButtonClick())
all_on_button.on_click(lambda x: allOn_ButtonClick())
reset_button.on_click(lambda x: reset_ButtonClick())
autoscale_button.on_click(lambda x: autoscale_ButtonClick())
channel_button[0].on_click(lambda x: channel_ButtonClick(1))
channel_button[1].on_click(lambda x: channel_ButtonClick(2))
channel_button[2].on_click(lambda x: channel_ButtonClick(3))
channel_button[3].on_click(lambda x: channel_ButtonClick(4))
pulse_capture_button.on_click(lambda x: pulseCapture_ButtonClick())
auto_save_button.on_click(lambda x: autoSave_ButtonClick())
load_button.on_click(lambda x: load_ButtonClick())
force_save_button.on_click(lambda x: forceSave_ButtonClick())
save_PC_button.on_click(lambda x: savePC_ButtonClick())

acq_period_select.on_change("value", acqPeriod_SelectChange)
channel_name_select1.on_change("value", chanNameSelect1_SelectChange)

force_save_filename_input.on_change("value", forceSaveFilename_InputChange)
channel_name_input.on_change("value", channelName_InputChange)
time_range_input.on_change("value", timeRange_InputChange)
trigger_level_input.on_change("value", triggerLevel_InputChange)
save_filepath_input.on_change("value", saveFilepath_InputChange)
load_file_input.on_change("value", loadFile_InputChange)
save_filepath_PC_input.on_change("value", saveFilepath_InputChange)      #
save_filename_PC_input.on_change("value", forceSaveFilename_InputChange) #reusing callbacks


#set up layout
doc.title = "Intensity Tracker"

grid = gridplot([
        [channel_button[0],channel_button[1],channel_button[2],channel_button[3]], 
        [all_on_button, all_off_button, reset_button, autoscale_button], 
        [channel_name_select1, channel_name_input, acq_period_select, num_avgs_select], 
        [single_plot[0], single_plot[1]],
        [single_plot[2], single_plot[3]],
        [multi_plot],
        [save_filepath_input, auto_save_button, force_save_button, force_save_filename_input],
        [Div(text="_"*242, render_as_text=True, width=1205)], 
        [Div(text=" ", render_as_text=True, width=1205)], 
        [channel_name_select2, trigger_level_input, time_range_input, number_points_select],
        [pulse_capture_button, save_filepath_PC_input, save_filename_PC_input, save_PC_button],
        [pc_plot],
        [Div(text="_"*242, render_as_text=True, width=1205)],
        [Div(text=" ", render_as_text=True, width=1205)],
        [load_button, load_file_input, load_plot_type_select],
        [load_plot],
        [Div(text="_"*242, render_as_text=True, width=1205)],
        [Div(text=" ", render_as_text=True, width=1205)]
        ], merge_tools=False, sizing_mode="scale_width")

doc.add_root(grid)

# open a session to keep our local document in sync with server,
# shows up as localhost:5006/?bokeh-session-id=session_id
session = push_session(doc, session_id='ITracker')

doc.add_periodic_callback(updateChannels, 500)
doc.add_periodic_callback(updateChannelsPC ,250)
doc.add_periodic_callback(updateSave, 300000)

session.show() # open the document in a browser
session.loop_until_closed() # run forever

#output_file("IntensityTracker.html")
