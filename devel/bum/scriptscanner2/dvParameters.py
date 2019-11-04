def saveParameters(dv, d, context):
    """Save the parameters from the dictionary dict into datavault"""
    for name in d.keys():
        dv.add_parameter(name, d[name], context = context)

def measureParameters(cxn, cxnlab, specified = None):
    """Measures parameters in the list and returns the dictionary containing these"""
    d = {}
    local = {
            'endcaps':measure_endcaps,
            'compensation':measure_compensation,
            'dds_cw':measure_dds_cw_frequencies,
            'line_trigger':measure_linetrigger,
            'dds_gui':measure_dds_gui_values,
            'drift_tracker':measure_drifttracker
            }
    lab = {
            'cavity397':measure_cavity('397'),
            'cavity866':measure_cavity('866'),
            'cavity422':measure_cavity('422'),
            'cavity854':measure_cavity('854'),
            'cavity397D':measure_cavity('397D'),
            'cavity729inject':measure_cavity('729inject'),
            'multiplexer397':measure_multiplexer('397 diode'),
            'multiplexer397':measure_multiplexer('794'),
            'multiplexer866':measure_multiplexer('866'),
           }

    for setting,connection in [(local, cxn),(lab, cxnlab)]:
        if specified is None:
            for name in setting.keys():
                measure = setting[name]
                try:
                    measure(connection, d)
                except Exception, e:
                    print 'Unable to Measure {0}'.format(name), e
        else:
            raise NotImplementedError
    return d

def measure_drifttracker(cxn, d):
    server = cxn.sd_tracker
    d['drift_tracker_current_b'] = server.get_current_b()
    d['drift_tracker_current_center'] = server.get_current_center()    

def measure_linetrigger(cxn, d):
    server = cxn.pulser
    d['line_trigger_state'] = server.line_trigger_state()
    d['line_trigger_duration'] = server.line_trigger_duration()        

def measure_dds_gui_values(cxn, d):
    server = cxn.pulser
    for k in server.get_dds_channels():        
        d['gui_dds_freq_' + k] = server.frequency(k)
        d['gui_dds_ampl_' + k] = server.amplitude(k)
    
def measure_dds_cw_frequencies(cxn, d):
    server = cxn.dds_cw
    for k in server.get_dds_channels():        
        d['dds_cw_freq_' + k] = server.frequency(k)
        d['dds_cw_ampl_' + k] = server.amplitude(k)

def measure_trapdrive(cxn, d):
    server = cxn.trap_drive
    d['rffreq'] = server.frequency()
    d['rfpower'] = server.amplitude()

def measure_endcaps(cxn , d):
    server = cxn.dac
    # ??????????????
    # these are not the endcap voltages
    # not sure what happened here
    #d['endcap1'] = server.get_voltage('endcap1')
    #d['endcap2'] = server.get_voltage('endcap2')
    d['endcap1'] = server.get_voltage('comp1')
    d['endcap2'] = server.get_voltage('comp2')

def measure_compensation(cxn , d):
    #server = cxn.dac
    # ?????????????????
    # these are not the compensation voltages
    #d['comp1'] = server.get_voltage('comp1')
    #d['comp2'] = server.get_voltage('comp2')

    # now, taking the voltages from the shq_222m_server
    server = cxn.shq_222m_server
    d['comp1'] = server.get_actual_voltage(1)
    d['comp2'] = server.get_actual_voltage(2)
    
def measure_dcoffsetonrf(cxn , d):
    server = cxn.dac
    d['dconrf1'] = server.get_voltage('dconrf1')
    d['dconrf2'] = server.get_voltage('dconrf2')

def measure_cavity(wavelegnth):
    def func(cxnlab ,d):
        server = cxnlab.laserdac
        d['cavity{}'.format(wavelegnth)] = server.getvoltage(wavelegnth)
    return func

def measure_multiplexer(wavelegnth):
    def func(cxnlab ,d):
        server = cxnlab.multiplexer_server
        d['multiplexer{}'.format(wavelegnth)] = server.get_frequency(wavelegnth)
    return func



