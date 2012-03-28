#!/usr/bin/env python
# -*- coding: utf-8 -*-
# generated by wxGlade 0.6.3 on Sun Mar 27 21:05:20 2011

import wx
import wx.grid
import wx.lib.buttons
import sys, os, re, copy
import numpy

# Climb the tree to find out where we are
p = os.path.abspath(sys.argv[0])
t = ""
while t != "src":
    (p, t) = os.path.split(p)
    if p == "":
        print "I have no idea where I am; this is ridiculous"
        sys.exit(1)

sys.path.append(os.path.join(p,"src","lib"))

import fsa, project
import mapRenderer

# begin wxGlade: extracode
# end wxGlade

class SysDummySensorHandler:
    def __init__(self, parent):
        self.parent = parent

    def __getitem__(self, name):
        if name == "initializing_handler":
            return {}
        else:
            return compile("self.h_instance['sensor'].getSensorValue('%s')" % name, "<string>", "eval")

    def getSensorValue(self, name):
        return self.parent.sensorStates[name]

class EnvDummySensorHandler:
    def __init__(self, parent):
        self.parent = parent

    def __getitem__(self, name):
        if name == "initializing_handler":
            return {}
        else:
            return compile("self.h_instance['sensor'].getSensorValue('%s')" % name, "<string>", "eval")

    def getSensorValue(self, name):
        m = re.match('^bit(\d+)$', name)
        if m is not None:
            # Handle region encodings specially
            # bit0 is MSB
            bitnum = int(m.group(1))
            # from http://www.daniweb.com/software-development/python/code/216539
            bs = "{0:0>{1}}".format(bin(self.parent.current_region)[2:], self.parent.num_bits)
            return bs[bitnum]
        else:
            return self.parent.actuatorStates[name]

class SysDummyActuatorHandler:
    def __init__(self):
        pass

    def __getitem__(self, name):
        if name == "initializing_handler":
            return {}
        else:
            return compile("self.h_instance['actuator'].setActuator('%s', new_val)" % name, "<string>", "eval")

    def setActuator(self, name, val):
        pass

class EnvDummyActuatorHandler:
    def __init__(self, parent):
        self.parent = parent

    def __getitem__(self, name):
        if name == "initializing_handler":
            return {}
        else:
            return compile("self.h_instance['actuator'].setActuator('%s', new_val)" % name, "<string>", "eval")

    def setActuator(self,name,val):
        self.parent.sensorStates[name] = val
        try:
            for btn in self.parent.env_buttons:
                if btn.GetLabelText() == name:
                    if int(val) == 1:
                        btn.SetBackgroundColour(wx.Colour(0, 255, 0)) 
                        btn.SetValue(True)
                    else:
                        btn.SetBackgroundColour(wx.Colour(255, 0, 0)) 
                        btn.SetValue(False)
                    break
        except AttributeError:
            pass # The buttons haven't been created yet

class DummyMotionHandler:
    def __init__(self):
        pass
    def gotoRegion(self,a,b):
        return True

class MopsyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: MopsyFrame.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.window_1 = wx.SplitterWindow(self, -1, style=wx.SP_3D|wx.SP_BORDER)
        self.window_1_pane_2 = wx.Panel(self.window_1, -1)
        self.window_1_pane_1 = wx.Panel(self.window_1, -1)
        self.mopsy_frame_statusbar = self.CreateStatusBar(1, 0)
        self.history_grid = wx.grid.Grid(self.window_1_pane_1, -1, size=(1, 1))
        self.panel_1 = wx.Panel(self.window_1_pane_2, -1, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL)
        self.label_5 = wx.StaticText(self.window_1_pane_2, -1, "Current environment state:")
        self.label_6 = wx.StaticText(self.window_1_pane_2, -1, "Please choose your response:")
        self.label_movingto = wx.StaticText(self.window_1_pane_2, -1, "Moving to XXX ...")
        self.label_8 = wx.StaticText(self.window_1_pane_2, -1, "Actuator states:")
        self.label_9 = wx.StaticText(self.window_1_pane_2, -1, "Internal propositions:")
        self.label_violation = wx.StaticText(self.window_1_pane_2, -1, "")
        self.button_next = wx.Button(self.window_1_pane_2, -1, "Execute Move >>")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.onButtonNext, self.button_next)
        # end wxGlade
        
        self.dest_region = None
        self.current_region = None
        self.regionsToHide = []
        self.actuatorStates = {}
        self.sensorStates = {}

        self.panel_1.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.mapBitmap = None

        # Load in the project and map
        self.proj = project.Project()
        self.proj.loadProject(sys.argv[1])
        self.proj.rfi = self.proj.loadRegionFile(decomposed=True)
        self.Bind(wx.EVT_SIZE, self.onResize, self)
        self.panel_1.Bind(wx.EVT_PAINT, self.onPaint)
        self.panel_1.Bind(wx.EVT_ERASE_BACKGROUND, self.onEraseBG)
        self.panel_1.Bind(wx.EVT_LEFT_DOWN, self.onMapClick)
        self.onResize()

        self.proj.determineEnabledPropositions()

        # Load in automatons
        self.sysDummySensorHandler = SysDummySensorHandler(self)
        self.envDummySensorHandler = EnvDummySensorHandler(self)
        self.sysDummyActuatorHandler = SysDummyActuatorHandler()
        self.envDummyActuatorHandler = EnvDummyActuatorHandler(self)
        self.dummyMotionHandler = DummyMotionHandler()

        print "Loading safety constraints..."
        self.safety_aut = fsa.Automaton(self.proj.rfi.regions, self.proj.regionMapping, self.sysDummySensorHandler, self.sysDummyActuatorHandler, self.dummyMotionHandler, {"sensor": self.sysDummySensorHandler, "actuator": self.sysDummyActuatorHandler, "motionControl":self.dummyMotionHandler}) 
        self.safety_aut.loadFile(self.proj.getFilenamePrefix() + "_safety.aut", self.proj.enabled_sensors, self.proj.enabled_actuators, self.proj.all_customs)
        print "Loading environment counter-strategy..."
        self.num_bits = int(numpy.ceil(numpy.log2(len(self.proj.rfi.regions))))  # Number of bits necessary to encode all regions
        region_props = ["bit" + str(n) for n in xrange(self.num_bits)]
        self.env_aut = fsa.Automaton(self.proj.rfi.regions, self.proj.regionMapping, self.envDummySensorHandler, self.envDummyActuatorHandler, self.dummyMotionHandler, {"sensor": self.envDummySensorHandler, "actuator": self.envDummyActuatorHandler, "motionControl":self.dummyMotionHandler})
        # We are being a little tricky here by just reversing the sensor and actuator propositions
        # to create a sort of dual of the usual automaton
        self.env_aut.loadFile(self.proj.getFilenamePrefix() + ".aut", self.proj.enabled_actuators + self.proj.all_customs + region_props, self.proj.enabled_sensors, [])
        
        # Force initial state to state #0 in counter-strategy
        self.env_aut.current_region = None
        self.env_aut.current_state = self.env_aut.states[0]
        # Internal aut housekeeping (ripped from chooseInitialState; hacky)
        self.env_aut.last_next_states = []
        self.env_aut.next_state = None
        self.env_aut.next_region = None
        
        #self.env_aut.dumpStates([self.env_aut.current_state])

        # Set initial sensor values
        self.env_aut.updateOutputs()

        # Figure out what actuator/custom-prop settings the system should start with
        for k,v in self.env_aut.current_state.inputs.iteritems():
            # Skip any "bitX" region encodings
            if re.match('^bit\d+$', k): continue 
            self.actuatorStates[k] = int(v)
        
        # Figure out what region the system should start from (ripped from regionFromState)
        self.current_region = 0
        for bit in range(self.num_bits):
            if (int(self.env_aut.current_state.inputs["bit" + str(bit)]) == 1):
                # bit0 is MSB
                self.current_region += int(2**(self.num_bits-bit-1))
        
        self.dest_region = self.current_region

        # Create all the sensor/actuator buttons
        self.env_buttons = [] # This will later hold our buttons
        self.act_buttons = [] # This will later hold our buttons
        self.cust_buttons = [] # This will later hold our buttons

        actprops = copy.deepcopy(self.actuatorStates)
        for s in self.proj.all_customs:
            del(actprops[s])
        custprops = copy.deepcopy(self.actuatorStates)
        for s in self.proj.enabled_actuators:
            del(custprops[s])

        self.populateToggleButtons(self.sizer_env, self.env_buttons, self.sensorStates)
        self.populateToggleButtons(self.sizer_act, self.act_buttons, actprops)
        self.populateToggleButtons(self.sizer_prop, self.cust_buttons, custprops)

        # Make the env buttons not clickable (TODO: maybe replace with non-buttons)
        for b in self.env_buttons:
            b.Enable(False)

        # Set up the logging grid
        colheaders = self.proj.enabled_sensors + ["Region"] + self.proj.enabled_actuators + self.proj.all_customs
        self.history_grid.CreateGrid(0,len(colheaders))
        for i,n in enumerate(colheaders):
            self.history_grid.SetColLabelValue(i," " + n + " ")
            self.history_grid.SetColSize(i,-1)  # Auto-size
        self.history_grid.EnableEditing(False)

        # Put initial condition into log
        self.appendToHistory()

        # Find the appropriate starting state in the sys safety aut
        init_outputs = [o for o in self.actuatorStates.keys() if (self.actuatorStates[o] == 1)]

        if self.safety_aut.chooseInitialState(self.current_region, init_outputs) is None:
            print "Counterstrategy initial state not found in system safety automaton. Something's off."
            return

        # Start initial environment move
        # All transitionable states have the same env move, so just use the first
        if (len(self.env_aut.current_state.transitions) >=1 ): 
            self.env_aut.updateOutputs(self.env_aut.current_state.transitions[0])

        self.label_movingto.SetLabel("Stay in region " + self.safety_aut.getAnnotatedRegionName(self.current_region))
        self.applySafetyConstraints()

    def applySafetyConstraints(self):
        # Determine transitionable regions

        goable = []
        goable_states = []
        trans = self.safety_aut.findTransitionableStates()

        # Look for any transition states that agree with our current outputs (ignoring dest_region)
        for s in trans:
            okay = True
            for k,v in s.outputs.iteritems():   
                # Skip any "bitX" region encodings
                if re.match('^bit\d+$', k): continue 
                if int(v) != int(self.actuatorStates[k]):
                    okay = False
                    break
            if okay:
                goable.append(self.proj.rfi.regions[self.safety_aut.regionFromState(s)].name)
                goable_states.append(s)

        region_constrained_goable_states = [s for s in goable_states if (self.safety_aut.regionFromState(s) == self.dest_region)]
        if region_constrained_goable_states == []:
            #print "Safety violation!"
            self.label_violation.SetLabel("Current move invalid under system constraints")
            self.button_next.Enable(False)
        else:
            self.label_violation.SetLabel("")
            self.button_next.Enable(True)

        self.regionsToHide = list(set([r.name for r in self.proj.rfi.regions])-set(goable))

        self.onResize() # Force map redraw

        # If there is no next state, this implies that the system has no possible move (including staying in place)
        if len(self.env_aut.current_state.transitions[0].transitions) == 0:
            self.label_violation.SetLabel("Checkmate: no possible system moves.")
            for b in self.act_buttons + self.cust_buttons + [self.button_next]:
                b.Enable(False)

    def appendToHistory(self):
        self.history_grid.AppendRows(1)
        newvals = [self.sensorStates[s] for s in self.proj.enabled_sensors] + \
                  [self.safety_aut.getAnnotatedRegionName(self.current_region)] + \
                  [self.actuatorStates[s] for s in self.proj.enabled_actuators] + \
                  [self.actuatorStates[s] for s in self.proj.all_customs] 
        lastrow = self.history_grid.GetNumberRows()-1

        for i,v in enumerate(newvals):
            if v == 0:
                self.history_grid.SetCellValue(lastrow,i,"False")
                self.history_grid.SetCellBackgroundColour(lastrow,i,wx.Colour(255, 0, 0))
            elif v == 1:
                self.history_grid.SetCellValue(lastrow,i,"True")
                self.history_grid.SetCellBackgroundColour(lastrow,i,wx.Colour(0, 255, 0))
            else:
                self.history_grid.SetCellValue(lastrow,i,v)
        self.history_grid.ClearSelection()
        self.history_grid.MakeCellVisible(lastrow,0)
        self.history_grid.ForceRefresh()
        self.mopsy_frame_statusbar.SetStatusText("Currently in step #"+str(lastrow+2), 0)
           

    def onMapClick(self, event):
        x = event.GetX()/self.mapScale
        y = event.GetY()/self.mapScale
        for i, region in enumerate(self.proj.rfi.regions):
            if region.objectContainsPoint(x, y) and region.name not in self.regionsToHide:
                self.dest_region = i
                if self.dest_region == self.current_region:
                    self.label_movingto.SetLabel("Stay in region " + self.safety_aut.getAnnotatedRegionName(self.proj.rfi.regions.index(region)))
                else:
                    self.label_movingto.SetLabel("Move to region " + self.safety_aut.getAnnotatedRegionName(self.proj.rfi.regions.index(region)))

                self.applySafetyConstraints()
                break 

        self.onResize() # Force map redraw
        event.Skip()

    def populateToggleButtons(self, target_sizer, button_container, items):
        for item_name, item_val in items.iteritems():
            # Create the new button and add it to the sizer
            button_container.append(wx.lib.buttons.GenToggleButton(self.window_1_pane_2, -1, item_name))
            target_sizer.Add(button_container[-1], 1, wx.EXPAND, 0)

            # Set the initial value as appropriate
            if int(item_val) == 1:
                button_container[-1].SetValue(True)
                button_container[-1].SetBackgroundColour(wx.Colour(0, 255, 0)) 
            else:
                button_container[-1].SetValue(False)
                button_container[-1].SetBackgroundColour(wx.Colour(255, 0, 0)) 

            self.window_1_pane_2.Layout() # Update the frame
            self.Refresh()

            # Bind to event handler
            #self.Bind(wx.EVT_TOGGLEBUTTON, self.sensorToggle, button_container[-1])
            self.Bind(wx.EVT_BUTTON, self.sensorToggle, button_container[-1])

    def sensorToggle(self, event):
        btn = event.GetEventObject()

        #print btn.GetLabelText() + "=" + str(btn.GetValue())

        self.actuatorStates[btn.GetLabelText()] = int(btn.GetValue())

        # TODO: Button background colour doesn't show up very well
        if btn.GetValue():
            btn.SetBackgroundColour(wx.Colour(0, 255, 0)) 
        else:
            btn.SetBackgroundColour(wx.Colour(255, 0, 0)) 

        self.Refresh()
        self.applySafetyConstraints()

        event.Skip()

    def onResize(self, event=None):
        size = self.panel_1.GetSize()
        self.mapBitmap = wx.EmptyBitmap(size.x, size.y)
        if self.dest_region is not None:
            hl = [self.proj.rfi.regions[self.dest_region].name]
        else:
            hl = []

        self.mapScale = mapRenderer.drawMap(self.mapBitmap, self.proj.rfi, scaleToFit=True, drawLabels=True, memory=True, highlightList=hl, deemphasizeList=self.regionsToHide)

        self.Refresh()
        self.Update()

        if event is not None:
            event.Skip()

    def onPaint(self, event=None):
        if self.mapBitmap is None:
            return

        if event is None:
            dc = wx.ClientDC(self.panel_1)
        else:
            pdc = wx.AutoBufferedPaintDC(self.panel_1)
            try:
                dc = wx.GCDC(pdc)
            except:
                dc = pdc
            else:
                self.panel_1.PrepareDC(pdc)

        self.panel_1.PrepareDC(dc)
        dc.BeginDrawing()

        # Draw background
        dc.DrawBitmap(self.mapBitmap, 0, 0)

        # Draw robot
        if self.current_region is not None:
            [x,y] = map(lambda x: int(self.mapScale*x), self.proj.rfi.regions[self.current_region].getCenter()) 
            dc.DrawCircle(x, y, 5)

        dc.EndDrawing()
        
        if event is not None:
            event.Skip()

    def onEraseBG(self, event):
        # Avoid unnecessary flicker by intercepting this event
        pass

    def __set_properties(self):
        # begin wxGlade: MopsyFrame.__set_properties
        self.SetTitle("Counter-Strategy Visualizer")
        self.SetSize((1024, 636))
        self.mopsy_frame_statusbar.SetStatusWidths([-1])
        # statusbar fields
        mopsy_frame_statusbar_fields = ["Loading..."]
        for i in range(len(mopsy_frame_statusbar_fields)):
            self.mopsy_frame_statusbar.SetStatusText(mopsy_frame_statusbar_fields[i], i)
        self.label_5.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.label_6.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.label_violation.SetForegroundColour(wx.Colour(255, 0, 0))
        self.label_violation.SetFont(wx.Font(10, wx.DEFAULT, wx.ITALIC, wx.NORMAL, 0, ""))
        self.button_next.SetDefault()
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MopsyFrame.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_4 = wx.BoxSizer(wx.VERTICAL)
        sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_prop = wx.BoxSizer(wx.HORIZONTAL)
        sizer_act = wx.BoxSizer(wx.HORIZONTAL)
        sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_env = wx.BoxSizer(wx.HORIZONTAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_2.Add(self.history_grid, 1, wx.EXPAND, 2)
        self.window_1_pane_1.SetSizer(sizer_2)
        sizer_3.Add(self.panel_1, 1, wx.EXPAND, 0)
        sizer_3.Add((10, 20), 0, 0, 0)
        sizer_4.Add((20, 10), 0, 0, 0)
        sizer_4.Add(self.label_5, 0, 0, 0)
        sizer_4.Add(sizer_env, 1, wx.EXPAND, 0)
        sizer_4.Add((20, 10), 0, 0, 0)
        sizer_4.Add(self.label_6, 0, 0, 0)
        sizer_6.Add(self.label_movingto, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_6.Add((20, 20), 0, 0, 0)
        sizer_4.Add(sizer_6, 1, wx.EXPAND, 0)
        sizer_4.Add(self.label_8, 0, 0, 0)
        sizer_4.Add(sizer_act, 1, wx.EXPAND, 0)
        sizer_4.Add(self.label_9, 0, 0, 0)
        sizer_4.Add(sizer_prop, 1, wx.EXPAND, 0)
        sizer_4.Add((20, 20), 0, 0, 0)
        sizer_5.Add(self.label_violation, 1, wx.EXPAND|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_5.Add(self.button_next, 0, 0, 0)
        sizer_5.Add((20, 20), 0, 0, 0)
        sizer_4.Add(sizer_5, 1, wx.EXPAND, 0)
        sizer_3.Add(sizer_4, 1, wx.EXPAND, 0)
        sizer_3.Add((10, 20), 0, 0, 0)
        self.window_1_pane_2.SetSizer(sizer_3)
        self.window_1.SplitHorizontally(self.window_1_pane_1, self.window_1_pane_2)
        sizer_1.Add(self.window_1, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        self.Layout()
        # end wxGlade
        self.sizer_env = sizer_env
        self.sizer_act = sizer_act
        self.sizer_prop = sizer_prop

    def onButtonNext(self, event): # wxGlade: MopsyFrame.<event_handler>
        # TODO: full safety check
        self.current_region = self.dest_region
        self.appendToHistory()
        self.env_aut.runIteration()

        # Find the new state in the sys safety aut (to check contraints in the next step)
        init_outputs = [o for o in self.actuatorStates.keys() if (self.actuatorStates[o] == 1)]

        if self.safety_aut.chooseInitialState(self.current_region, init_outputs) is None:
            print "New state not found in system safety automaton. Something's off."
            return

        ### Make environment move

        # All transitionable states have the same env move, so just use the first
        self.env_aut.updateOutputs(self.env_aut.current_state.transitions[0])
        self.label_movingto.SetLabel("Stay in region " + self.safety_aut.getAnnotatedRegionName(self.current_region))
        self.applySafetyConstraints()

        event.Skip()

# end of class MopsyFrame


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: %s [spec_file]" % sys.argv[0]
        sys.exit(-1)

    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    mopsy_frame = MopsyFrame(None, -1, "")
    app.SetTopWindow(mopsy_frame)
    mopsy_frame.Show()
    app.MainLoop()
