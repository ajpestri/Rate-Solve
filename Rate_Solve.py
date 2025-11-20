import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog, ttk, Toplevel
import math as math
import re as re
import mss
import mss.tools
import os
import ast
import sys
import mech2eqn_array
import diffsolve
import diffgen
import matplotlib.pyplot as plt
import distinctipy
import numpy as np
import pyautogui
import random
import ttkthemes

#Versions
#RateSolve 1.0. Embedded MechDraw in solver and fitting, with GUI for parameter and file control

#to do
#maybe
#storing the mechanism the first time causes the canvas to resize. It's related to taking the screenshot, window resets to system DPI. currently using another package, but it only works on the primary monitor
#DONE: add type restrictions to object entries (alpha numberic, numeric only)
#DONE: ban "t" from input as it's a hardcoded variable in the differential solver
#add ability for users to change color scheme?
#bug sometimes occurs where lines disconnect when click over text boxes to drag. Not able to reproduce reliably. Been around forever, very rare
#DONE: put mechanism file and id boxes at bottom of buttons
#add default text to data and output boxes

#Bugs
#TEST: initial point accounting for baseline seems to be wrong. (subtracting baseline before solving made system account for adjustment, and then account again by adding it back in). Need to test in user and data mode
#DONE: adding noise results in points not adding to one
#DONE: need clear all button for individual parameters
#for file selectors, cannot select a folder without selecting a file, so cannot select an empty folder
#need to think through logic of import and mech browse directory choosing
#if directory is chosen, open file browser in that directory
#numbers in certain places as species names still breaks the solver
#some file names seem to break things for some reason.
#DONE: double check multiple starting species doesn't break things - update: it does. (seems fine. If using individual parameters can struggle to find good fit)
#figure out how fucking themes work
#DONE: drop down boxes scale differently from object rectangles, can overlap on some screens
#DONE: shift drop down boxes on top of one another instead of side by side
#DONE: text box needs to scroll automatically
#DONE: need to update file reader (multiple delimiters) for the plot function (done for solve and generate)
#fix spacing of data and output file titles over boxes
#fix UI freeze during fitting


#this all badly needs a refactor


class FlowChartApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RateSolve")
        self.root.grid_rowconfigure([0],weight=1)
        self.root.grid_rowconfigure([1],weight=0)
        self.root.grid_columnconfigure([0,1,2],weight=1)

        # Initialize flowchart objects
        self.objects = []
        self.box_objects = []
        self.text_objects = []
        self.tag_objects = []
        self.parent_drop = []
        self.parent_menu = []
        self.par_variable = []
        self.column_objects = []
        self.column_drop = []
        self.column_menu = []
        self.col_variable = []
        self.selected_objects = []  # Store the last two clicked objects
        self.target_objects = []    #store two objects for connection
        self.drag_data = {"x": 0, "y": 0}
        self.connection_line = []  # Store connection lines
        self.connection_obj_1 = []
        self.connection_obj_2 = []
        self.text_list = []
        self.tag_list = []
        self.column_list = []
        self.delete_objects = []
        self.entry = []
        self.param_window = []
        self.mecfilebrowsed = []
        self.datafilebrowsed = []
        self.resultfilebrowsed = []
        self.param_window = None

        #set object sizes
        self.box_width = 150
        self.box_height = 100
        #initial positions
        self.object_x = 100
        self.object_y = 100
        #set object colors
        self.box_color = "seagreen1"
        self.line_color = "black"
        self.target_color = "red"
        self.delete_color = "yellow"
        self.canvas_color = "slate blue"
        self.control_color = 'green'
        #set default texts
        self.object_title = "Title"
        self.object_parent = "Parent"
        self.object_number = "Column"
        self.default_param_values = [0, 0, 0, 10, 1, .1, 1, 1, 0]

        #let's mess around with colors and shapes a bit
        #self.system_style = ttkthemes.ThemedStyle()
        self.system_style = ttk.Style()
        self.box_style = ttk.Style()
        #self.system_style.theme_use('breeze')
        self.box_style.configure('box.Tbutton',background=self.box_color)
        self.system_style.configure('TFrame',color='cornflowerblue')

        #set component frames
        #self.control_frame = ttk.Frame(root, bd=2, relief="groove", width=300, height=600)
        self.control_frame = ttk.Frame(root, width=100, height=600)
        self.control_frame.grid(row=0,column=1,rowspan=2,padx=5,pady=5,sticky='nsew')
        self.canvas_frame = ttk.Frame(root,width=1400, height=580)
        self.canvas_frame.grid(row=0,column=0,padx=5,pady=5,sticky='nsew')
        self.button_frame = ttk.Frame(root, width=1400,height=20)        #create frame for buttons
        self.button_frame.grid(row=1,column=0,padx=5,pady=5,sticky='ew')

        # Initialize canvas
        self.canvas = tk.Canvas(self.canvas_frame, bg=self.canvas_color, width=1200, height=580)
        self.canvas.pack(fill="both", expand=True)

        # Create buttons
        self.button_frame.columnconfigure([0,1,2,3,4,5,6],weight=1)
        self.create_button = ttk.Button(self.button_frame, text="Create Object",command=lambda: self.create_object(self.object_x,self.object_y,self.object_title,self.object_parent,self.object_number))
        self.create_button.grid(row=0,column=0,sticky='we')

        self.connect_button = ttk.Button(self.button_frame, text="Connect Highlighted Objects", command=self.connect_objects)
        self.connect_button.grid(row=0,column=1,sticky='we')

        self.process_button = ttk.Button(self.button_frame,text="Store Mechanism",command=self.get_and_write_mechanism)
        self.process_button.grid(row=0,column=2,sticky='we')

        self.clear_target_button = ttk.Button(self.button_frame,text="Clear Highlighted",command=self.clear_target_objects)
        self.clear_target_button.grid(row=0,column=3,sticky='we')

        self.delete_selection_button = ttk.Button(self.button_frame,text="Delete Selected",command=self.delete_selections)
        self.delete_selection_button.grid(row=0,column=4,sticky='we')

        self.clear_button = ttk.Button(self.button_frame,text="Delete All", command=self.clear_objects)
        self.clear_button.grid(row=0,column=5,sticky='we')

        self.import_button = ttk.Button(self.button_frame,text="Import Model",command=self.import_model)
        self.import_button.grid(row=0,column=6,sticky='we')

        self.file_label = ttk.Label(self.button_frame,text="Output File")                      #Label and box for output file name
        self.file_label.grid(row=1,column=0,sticky='e')
        self.file_box = ttk.Entry(self.button_frame,textvariable=())
        self.file_box.grid(row=1,column=1,columnspan=3,sticky='we')
        self.file_box.insert(0,"file_name.mec")
        self.file_select = ttk.Button(self.button_frame,text="Browse",command=self.browse_mec_files,)
        self.file_select.grid(row=1,column=4,sticky='EW')
        self.model_label = ttk.Label(self.button_frame,text="Model ID")                        #Label and box for id tag input
        self.model_label.grid(row=1,column=5,sticky='E')
        self.model_box = ttk.Entry(self.button_frame,width=15,textvariable=())
        self.model_box.grid(row=1,column=6,sticky='WE')
        self.model_box.insert(0,"1")

        #Create Control Panel Widgets
        self.control_frame.columnconfigure([0,1,2,3],weight=1)
        self.control_frame.rowconfigure([20],weight=1)
        self.control_label = ttk.Label(self.control_frame,text='Solving Settings',font=('Arial',18))
        self.control_label.grid(row=0,column=0,sticky='n',columnspan=4,pady=10)
        self.param_label = ttk.Label(self.control_frame,text="Fit Parameters",font=('Arial',14))
        self.param_label.grid(row=1,column=0,sticky='n',columnspan=4,pady=10)
        self.k_label = ttk.Label(self.control_frame,text="Rate Constant",font=('Arial',10))
        self.y0_label = ttk.Label(self.control_frame,text="Initial Value",font=('Arial',10))
        self.bc_label = ttk.Label(self.control_frame,text="Baseline",font=('Arial',10))
        self.k_label.grid(row=2,column=1)
        self.y0_label.grid(row=2,column=2)
        self.bc_label.grid(row=2,column=3)
        self.lb_label = ttk.Label(self.control_frame,text="Lower Bound",font=('Arial',10))
        self.ub_label = ttk.Label(self.control_frame,text="Upper Bound",font=('Arial',10))
        self.guess_label = ttk.Label(self.control_frame,text="Initial Guess",font=('Arial',10))
        self.lb_label.grid(row=3,column=0,sticky='e')
        self.ub_label.grid(row=4,column=0,sticky='e')
        self.guess_label.grid(row=5,column=0,sticky='e')
        self.parameter_entries = []
        i=0
        for r in range(3):
            for c in range(3):
                param_entry = ttk.Entry(self.control_frame,textvariable=(),width=12)
                param_entry.insert(0,self.default_param_values[i])
                param_entry.grid(row=r+3,column=c+1)
                self.parameter_entries.append(param_entry)
                i=i+1
        bound_modes = ['Fit','User','Data']
        self.bound_mode = [tk.StringVar(value=bound_modes[2]),tk.StringVar(value=bound_modes[0]),tk.StringVar(value=bound_modes[0])]
        #self.rate_mode = ttk.Combobox(self.control_frame,textvariable=self.bound_mode[0],values=bound_modes,width=10,state='readonly').grid(row=8,column=1)
        self.y0_mode = ttk.Combobox(self.control_frame,textvariable=self.bound_mode[1],values=bound_modes,width=10,state='readonly')
        self.y0_mode.grid(row=6,column=2)
        #self.base_mode = ttk.Combobox(self.control_frame,textvariable=self.bound_mode[2],values=bound_modes,width=10,state='readonly').grid(row=8,column=3)
        self.y0_multiplier_label = ttk.Label(self.control_frame,text="Initial Value Bound",font=('Arial',10))
        self.y0_multiplier_label.grid(row=7,column=0,columnspan=2,sticky='e',pady=15)
        self.y0_multiplier = ttk.Entry(self.control_frame,textvariable=(),width=12)
        self.y0_multiplier.grid(row=7,column=2,pady=15)
        self.y0_multiplier.insert(0,1)
        self.indiv_params_button = ttk.Button(self.control_frame,text='Individual Parameters',command=lambda:self.open_param_window())
        self.indiv_params_button.grid(row=8,column=1,columnspan=3,pady=10)
        self.generate_title = ttk.Label(self.control_frame,text='Data Generation Parameters',font=('Arial',14)).grid(row=9,column=0,columnspan=4,pady=10,sticky='n')
        self.xmin_label = ttk.Label(self.control_frame,text='x start',font=('Arial',10)).grid(row=10,column=0)
        self.xmax_label = ttk.Label(self.control_frame,text='x end',font=('Arial',10)).grid(row=10,column=1)
        self.xnum_label = ttk.Label(self.control_frame,text='No. Points',font=('Arial',10)).grid(row=10,column=2)
        self.ynoise_label = ttk.Label(self.control_frame,text='y noise (%)',font=('Arial',10)).grid(row=10,column=3)
        self.xmin_entry = ttk.Entry(self.control_frame,textvariable=(),width=12)
        self.xmin_entry.grid(row=11,column=0)
        self.xmin_entry.insert(0,0)
        self.xmax_entry = ttk.Entry(self.control_frame,textvariable=(),width=12)
        self.xmax_entry.grid(row=11,column=1)
        self.xmax_entry.insert(0,10)
        self.xnum_entry = ttk.Entry(self.control_frame,textvariable=(),width=12)
        self.xnum_entry.grid(row=11,column=2)
        self.xnum_entry.insert(0,21)
        self.ynoise_entry = ttk.Entry(self.control_frame,textvariable=(),width=12)
        self.ynoise_entry.grid(row=11,column=3)
        self.ynoise_entry.insert(0,0)
        self.data_file_label = ttk.Label(self.control_frame,text='Data File',font=('Arial',10)).grid(row=12,column=0,sticky='ws',pady=15)
        self.data_file_entry = ttk.Entry(self.control_frame,textvariable=())
        self.data_file_entry.grid(row=13,column=0,columnspan=3,stick='we')
        self.data_file_button = ttk.Button(self.control_frame,text='Browse',command=self.browse_data_files).grid(row=13,column=3,sticky='we')
        self.result_file_label = ttk.Label(self.control_frame,text='Output File',font=('Arial',10)).grid(row=14,column=0,sticky='ws',pady=15)
        self.result_file_entry = ttk.Entry(self.control_frame,textvariable=())
        self.result_file_entry.grid(row=15,column=0,columnspan=3,stick='we')
        self.result_file_button = ttk.Button(self.control_frame,text='Browse',command=self.browse_result_files).grid(row=15,column=3,sticky='we')
        self.solve_button = tk.Button(self.control_frame,text='Solve and Fit',command=lambda:self.solve_and_fit(),font=('Arial',10,'bold'))
        self.solve_button.grid(row=16,column=0,columnspan=2,pady=15,sticky='we')
        self.generate_button = tk.Button(self.control_frame,text='Generate',command=lambda:self.generate_data(),font=('Arial',10,'bold'))
        self.generate_button.grid(row=16,column=2,pady=15,sticky='we')
        self.plot_button = tk.Button(self.control_frame,text='Plot Data',command=lambda:self.plot_data(),font=('Arial',10,'bold'))
        self.plot_button.grid(row=16,column=3,pady=15,sticky='we')
        self.terminal_window = scrolledtext.ScrolledText(self.control_frame,wrap='word',height=12,width=60)
        self.terminal_window.grid(row=20,column=0,columnspan=4,rowspan=4,sticky='ns')
        self.terminal_window.tag_config('error_text',foreground='red')
        self.terminal_window.tag_config('default_text',foreground='black')      
        #self.radio_test_button = tk.Button(self.control_frame,text='Rate Mode',command=lambda:self.print_to_window(self.terminal_window,self.bound_mode[2].get()))
        #self.radio_test_button.grid(row=21,column=0)

        # Bind mouse events
        self.canvas.bind("<Button-1>", self.on_canvas_click)                                #left click
        self.canvas.bind("<B1-Motion>", self.on_object_drag)                                #left click and drag
        self.canvas.bind("<ButtonRelease-1>", self.on_object_release)                       #left click release
        self.canvas.bind("<Button-3>", self.on_canvas_rclick)                               #right click
        self.canvas.bind("<ButtonRelease-3>",self.on_object_release)                        #right click release
        self.canvas.bind("<Button-2>",self.on_text_click)                                   #middle mouse click
        self.canvas.bind("<Control-Button-1>",self.select_to_delete)                        #ctrl + left click
    
    def open_param_window(self):
        if self.param_window:
            self.param_window.destroy()
        self.indiv_params_button["state"] = tk.DISABLED
        self.param_window = tk.Toplevel()
        self.param_window.protocol("WM_DELETE_WINDOW", lambda: self.indiv_params_button.configure(state='normal') or self.param_window.destroy())
        self.param_window.title('RateSolve Parameters')
        self.param_window.config(width=500,height=500)
        self.param_window.grid_rowconfigure([0],weight=1)
        self.param_window.grid_rowconfigure([1],weight=0)
        self.param_window.grid_columnconfigure([0],weight=1)
        self.param_frame = ttk.Frame(self.param_window, width=500, height=480)
        self.param_button_frame = ttk.Frame(self.param_window, width=500, height=20)
        #self.param_frame.grid(row=0,column=0,padx=2,pady=2,sticky='nsew')
        #self.param_button_frame.grid(row=1,column=0,padx=2,pady=2,sticky='nsew')
        self.update_params_button = ttk.Button(self.param_button_frame,text='Update Entries',command=self.open_param_window).grid(row=0,column=0,sticky='nsew')
        self.reset_params_button = ttk.Button(self.param_button_frame,text='Reset Parameters',command=self.open_param_window).grid(row=0,column=1,sticky='nsew')
        mech_array = self.get_mechanism()
        equation_array,equation_list,variable_lists,counter_lists,columntrack,mechanism_id = mech2eqn_array.eqn_format(mech_array)
        species_list,rate_list,parent_list = variable_lists
        interpost,inter_counter = counter_lists
        self.param_rate_heading = ttk.Label(self.param_frame,text='Rates',font=('Arial',12)).grid(row=0,column=0,columnspan=4,pady=5)
        self.param_rate_lb = ttk.Label(self.param_frame,text='Lower Bound',font=('Arial',10)).grid(row=1,column=1,pady=2)
        self.param_rate_guess = ttk.Label(self.param_frame,text='Guess',font=('Arial',10)).grid(row=1,column=2,pady=2)
        self.param_rate_ub = ttk.Label(self.param_frame,text='Upper Bound',font=('Arial',10)).grid(row=1,column=3,pady=2)
        self.k_lb_array = []
        self.k_g_array = []
        self.k_ub_array = []
        for i,k in enumerate(rate_list):
            name = ttk.Label(self.param_frame,text=k,font=('Arial',10))
            name.grid(row=2+i,column=0,sticky='e')
            self.k_lb_array.append(ttk.Entry(self.param_frame,textvariable=(),width=10))
            self.k_lb_array[i].grid(row=2+i,column=1)
            self.k_lb_array[i].insert(0,self.parameter_entries[0].get())
            self.k_g_array.append(ttk.Entry(self.param_frame,textvariable=(),width=10))
            self.k_g_array[i].grid(row=2+i,column=2)
            self.k_g_array[i].insert(0,self.parameter_entries[6].get())
            self.k_ub_array.append(ttk.Entry(self.param_frame,textvariable=(),width=10))
            self.k_ub_array[i].grid(row=2+i,column=3)
            self.k_ub_array[i].insert(0,self.parameter_entries[3].get())
        self.param_y0_heading = ttk.Label(self.param_frame,text='Initial Value',font=('Arial',12)).grid(row=0,column=4,columnspan=4,pady=5)
        self.param_y0_lb = ttk.Label(self.param_frame,text='Lower Bound',font=('Arial',10)).grid(row=1,column=5,pady=2)
        self.param_y0_guess = ttk.Label(self.param_frame,text='Guess',font=('Arial',10)).grid(row=1,column=6,pady=2)
        self.param_y0_ub = ttk.Label(self.param_frame,text='Upper Bound',font=('Arial',10)).grid(row=1,column=7,pady=2)
        self.y0_lb_array = []
        self.y0_g_array = []
        self.y0_ub_array = []
        for i,y in enumerate(parent_list):
            name = ttk.Label(self.param_frame,text=y,font=('Arial',10))
            name.grid(row=2+i,column=4,sticky='e')
            self.y0_lb_array.append(ttk.Entry(self.param_frame,textvariable=(),width=10))
            self.y0_lb_array[i].grid(row=2+i,column=5)
            self.y0_lb_array[i].insert(0,self.parameter_entries[1].get())
            self.y0_g_array.append(ttk.Entry(self.param_frame,textvariable=(),width=10))
            self.y0_g_array[i].grid(row=2+i,column=6)
            self.y0_g_array[i].insert(0,self.parameter_entries[7].get())
            self.y0_ub_array.append(ttk.Entry(self.param_frame,textvariable=(),width=10))
            self.y0_ub_array[i].grid(row=2+i,column=7)
            self.y0_ub_array[i].insert(0,self.parameter_entries[4].get())
        self.param_bc_heading = ttk.Label(self.param_frame,text='Baseline Correction',font=('Arial',12)).grid(row=0,column=8,columnspan=4,pady=5)
        self.param_bc_lb = ttk.Label(self.param_frame,text='Lower Bound',font=('Arial',10)).grid(row=1,column=9,pady=2)
        self.param_bc_guess = ttk.Label(self.param_frame,text='Guess',font=('Arial',10)).grid(row=1,column=10,pady=2)
        self.param_bc_ub = ttk.Label(self.param_frame,text='Upper Bound',font=('Arial',10)).grid(row=1,column=11,pady=2)
        self.bc_lb_array = []
        self.bc_g_array = []
        self.bc_ub_array = []
        for i,y in enumerate(parent_list):
            name = ttk.Label(self.param_frame,text=y,font=('Arial',10))
            name.grid(row=2+i,column=8,sticky='e')
            self.bc_lb_array.append(ttk.Entry(self.param_frame,textvariable=(),width=10))
            self.bc_lb_array[i].grid(row=2+i,column=9)
            self.bc_lb_array[i].insert(0,self.parameter_entries[2].get())
            self.bc_g_array.append(ttk.Entry(self.param_frame,textvariable=(),width=10))
            self.bc_g_array[i].grid(row=2+i,column=10)
            self.bc_g_array[i].insert(0,self.parameter_entries[8].get())
            self.bc_ub_array.append(ttk.Entry(self.param_frame,textvariable=(),width=10))
            self.bc_ub_array[i].grid(row=2+i,column=11)
            self.bc_ub_array[i].insert(0,self.parameter_entries[5].get())
        self.param_frame.grid_rowconfigure(list(range(self.param_frame.grid_size()[1])),weight=1)
        self.param_frame.grid_columnconfigure(list(range(self.param_frame.grid_size()[0])),weight=1)
        self.param_frame.grid(row=0,column=0,padx=2,pady=2,sticky='nsew')
        self.param_button_frame.grid_rowconfigure(list(range(self.param_frame.grid_size()[1])),weight=1)
        self.param_button_frame.grid_columnconfigure(list(range(self.param_frame.grid_size()[0])),weight=1)
        self.param_button_frame.grid(row=1,column=0,padx=2,pady=2,sticky='nsew')
   
    def print_to_window(self,text_window,text,color_tag="default_text"):
        text_window.insert(tk.END,text+'\n',color_tag)
        text_window.see(tk.END)
        self.root.update_idletasks()
    
    def create_object(self,init_x,init_y,text_title,text_parent,text_num):
        # Create a flowchart object (text box)
        x, y = init_x+random.randint(0,50), init_y+random.randint(0,50)  # Initial position
        width, height = self.box_width, self.box_height  # Size
        obj = self.canvas.create_rectangle(x, y, x + width, y + height, fill=self.box_color, tags="flowchart_object")               #create object box
        self.box_objects.append(obj)
        text_obj = self.canvas.create_text((x + x + width) / 2, (y + (height/4)), text=text_title, font=("Arial", 12, "bold"))           #add title text box
        text_coords = self.canvas.bbox(text_obj)
        #self.text_objects.append(text_obj)
        #self.update_text_list()
        self.par_variable.append(tk.StringVar(value=text_parent))
        self.parent_drop.append((obj,ttk.Combobox(self.canvas,textvariable=self.par_variable[-1],values=self.parent_menu,postcommand=lambda:self.update_parent_drop(), state='readonly',width=10,background=self.box_color)))
        tag_obj = self.canvas.create_window(x+(.5*width), (y + (height*2/4)), window=self.parent_drop[-1][1])
        tag_coords = self.canvas.bbox(tag_obj)
        #tag_obj = self.canvas.create_text(x+(width/4), (y + (height*3/4)),text=text_parent, font=("Arial",10))                         #add parent text box
        #self.tag_objects.append(tag_obj)
        #self.update_tag_list()
        self.col_variable.append(tk.StringVar(value=text_num))
        self.column_drop.append((obj,ttk.Combobox(self.canvas,textvariable=self.col_variable[-1],values=self.column_menu,postcommand=lambda:self.update_column_drop(), state='readonly',width=7,background=self.box_color)))
        col_obj = self.canvas.create_window(x+(.5*width),(y + (height*3/4)),window=self.column_drop[-1][1])             #add column text box
        col_coords = self.canvas.bbox(col_obj)
        #col_obj = self.canvas.create_text(x+(3/4*width),(y + (height*3/4)),text=text_num,font=("Arial",10),justify="right")            #add column text box
        #self.column_objects.append(col_obj)
        
        text_height = text_coords[3] - text_coords[1]
        tag_height = tag_coords[3] - tag_coords[1]
        col_height = col_coords[3] - col_coords[1]
        total_height = text_height + tag_height + col_height
        box_height = round(total_height/.7)
        box_width = round(box_height*(self.box_width/self.box_height))
        self.canvas.coords(obj,x,y,x+box_width,y+box_height)
        self.canvas.coords(text_obj,x+0.5*box_width,y+.1*box_height+.5*text_height)
        self.canvas.coords(tag_obj,x+0.5*box_width,y+.15*box_height+text_height+0.5*tag_height)
        self.canvas.coords(col_obj,x+0.5*box_width,y+.2*box_height+text_height+tag_height+0.5*col_height)
        self.text_objects.append(text_obj)
        self.tag_objects.append(tag_obj)
        self.column_objects.append(col_obj)
        #self.update_column_list()
        self.objects.append((obj, text_obj, tag_obj))                                                                               #add to overall object list, and appropriate object lists
        self.update_text_list()                                                                                                     #update output lists
        self.update_tag_list()
        self.update_column_list()
        self.box_height = box_height
        self.box_width = box_width

    def update_parent_drop(self):
        for i,_ in enumerate(self.parent_drop):
            self.parent_drop[i][1].configure(values = self.parent_menu)

    def update_column_drop(self):
        for i,_ in enumerate(self.column_drop):
            self.column_drop[i][1].configure(values = self.column_menu)

    #Connect targeted objects
    def connect_objects(self):
        if len(self.target_objects) < 2:                                                                                        #throw error if two objects are not selected
            messagebox.showwarning("Error", "Select two objects to connect.")
            return

        # Get the centers of the selected objects
        center1 = self.get_object_center(self.target_objects[0])
        center2 = self.get_object_center(self.target_objects[1])

        #store connected objects
        self.connection_obj_1.append(self.target_objects[0])
        self.connection_obj_2.append(self.target_objects[1])
        
        #Get target points on box borders
        box1_intercept = self.get_box_intercept(center1[0],center1[1],center2[0],center2[1],self.box_width,self.box_height)
        box2_intercept = self.get_box_intercept(center2[0],center2[1],center1[0],center1[1],self.box_width,self.box_height)
        
        # Draw an arrow connecting the target points
        self.connection_line.append(self.canvas.create_line(box1_intercept,box2_intercept, fill=self.line_color, width=4, arrow=tk.LAST, arrowshape=(10,13,8)))

        #clear connection selections
        self.clear_target_objects()

    #Right click to select box for connection
    def on_canvas_rclick(self, event):
        rclicked_object = self.canvas.find_overlapping(event.x, event.y, event.x+1, event.y+1)          #get list of objects overlapping with click position
        if self.entry:                                                                                  #if text box is open update text and close it
            self.update_text(self.text_id_hold)
        if rclicked_object and rclicked_object[0] in self.box_objects:                                  #check if clicked on box
            obj_id = rclicked_object[0]
            if obj_id in self.delete_objects:                                                           #if box is selected for deletion, remove from delete list
                del self.delete_objects[self.delete_objects.index(obj_id)]
            if obj_id in self.target_objects:                                                           #if box is already targeted, remove from target list
                del self.target_objects[self.target_objects.index(obj_id)]
            else:                                                                                       #otherwise add the box id to the target list
                self.target_objects.append(obj_id)
            if len(self.target_objects) > 2:                                                            #if this is the third box on the list, remove the first one
                self.target_objects.pop(0)
            if len(self.target_objects) == 2:                                                           #if boxes are already on the list in the same order, clear the target list (prevents duplicate connections)
                if self.target_objects[0] in self.connection_obj_1 and self.target_objects[1] in self.connection_obj_2:
                    if self.connection_obj_1.index(self.target_objects[0]) == self.connection_obj_2.index(self.target_objects[1]):
                        self.target_objects = []
        self.update_colors()                                                                            #update colors on all objects         

    #Ctrl+Click on object to select for deletion
    def select_to_delete(self,event):
        ctrl_click_object = self.canvas.find_overlapping(event.x,event.y, event.x+1,event.y+1)          #find object overlapping click location
        if self.entry:                                                                                  #if text box is open, update and close it
            self.update_text(self.text_id_hold)
        if ctrl_click_object:
            if ctrl_click_object[0] in self.target_objects:                                             #if object is box targeted for connection, remove from connection list
                del self.target_objects[self.target_objects.index(ctrl_click_object[0])]
            if ctrl_click_object[0] in self.delete_objects:                                             #if object is already on delete list, remove it from list
                reset_id = ctrl_click_object[0]
                del self.delete_objects[self.delete_objects.index(reset_id)]
            else:                                                                                       #otherwise add it to delete list
                self.delete_objects.append(ctrl_click_object[0])
        self.update_colors()                                                                            #update colors on all objects

    #delete selected objects
    def delete_selections(self):
        if self.entry:                                                                                  #if text box is open, update and delete
            self.update_text(self.text_id_hold)
        if self.delete_objects:
            for del_id in self.delete_objects:                                                          #loop through list of deletion objects
                if del_id in self.box_objects:                                                          #if object is box, delete box and all associated text boxes
                    del self.box_objects[self.box_objects.index(del_id)]
                    del self.text_objects[self.text_objects.index(del_id+1)]
                    del self.tag_objects[self.tag_objects.index(del_id+2)]
                    del self.column_objects[self.column_objects.index(del_id+3)]
                    for par,col in zip(self.parent_drop,self.column_drop):
                        if par[0] == del_id:
                            self.parent_drop.remove(par)
                        if col[0] == del_id:
                            self.column_drop.remove(col)
                    self.canvas.delete(del_id,del_id+1,del_id+2,del_id+3)                               #delete ids and remove from lists
                    self.update_text_list()
                    self.update_tag_list()
                    self.update_column_list()
                elif del_id in self.connection_line:                                                    #if object is arrow, remove line
                    del_idx = self.connection_line.index(del_id)
                    del self.connection_line[del_idx]
                    del self.connection_obj_1[del_idx]                                                  #clear connection list
                    del self.connection_obj_2[del_idx]
                    self.canvas.delete(del_id)
                else:
                    pass
            self.delete_objects = []                                                                    #clear deletion list
            self.update_colors()                                                                        #update colors (shouldn't be necessary, but no harm in running)

    #Get center of a box object
    def get_object_center(self, obj):
        bbox = self.canvas.bbox(obj)                #get x,y bounds of box
        x_center = (bbox[0] + bbox[2]) / 2          #find average of bounds to get centerpoint
        y_center = (bbox[1] + bbox[3]) / 2
        return x_center, y_center                   #return x,y coords of center

    #Clicking box objects
    def on_canvas_click(self, event):
        # Check if an object is clicked
        clicked_object = self.canvas.find_overlapping(event.x, event.y, event.x+1, event.y+1)
        if self.entry:
            self.update_text(self.text_id_hold)                             #if text box is open, update and close
        if clicked_object:
            obj_id = clicked_object[0]                                      #select first item from list. This should avoid selecting text boxes as they are always created after the main object box
            if obj_id in self.box_objects:                                  #check a box object is selected
                self.selected_objects.append(obj_id)                        #mark box as selected
                if len(self.selected_objects) > 1:
                    self.selected_objects.pop(0)                            # Keep only the last clicked objects
                self.drag_data["x"] = event.x                               #record position of click
                self.drag_data["y"] = event.y
            else:
                self.selected_objects = []
        else:
            self.selected_objects = []

    #move boxes by dragging
    def on_object_drag(self, event):
        if self.selected_objects:                                           #check a box is selected
            dx = event.x - self.drag_data["x"]                              #get distance pointer moved from initial point in drag
            dy = event.y - self.drag_data["y"]
            obj_id = self.selected_objects[0]
            self.canvas.move(obj_id, dx, dy)                                #move object and associated text boxes
            self.canvas.move(obj_id+1, dx, dy)
            self.canvas.move(obj_id+2, dx, dy)
            self.canvas.move(obj_id+3, dx, dy)
            self.drag_data["x"] = event.x                                   #reset drag starting positions
            self.drag_data["y"] = event.y

            # Update connection lines if they exist
            if self.connection_line:
                i = -1
                for line in self.connection_line:
                    i = i+1
                    center1 = self.get_object_center(self.connection_obj_1[i])          #get box centers
                    center2 = self.get_object_center(self.connection_obj_2[i])
                    box1_intercept = self.get_box_intercept(center1[0],center1[1],center2[0],center2[1],self.box_width,self.box_height)         #get target point on box borders
                    box2_intercept = self.get_box_intercept(center2[0],center2[1],center1[0],center1[1],self.box_width,self.box_height)
                    self.canvas.coords(line, box1_intercept, box2_intercept)                                                                    #update line position

    #clear selection when release mouse button
    def on_object_release(self, event):
        self.selected_objects = []
        pass
    
    #Clear entire canvas
    def clear_objects(self):
        self.canvas.delete("all")                   #remove all objects
        if self.entry:                              #if any text boxes exists, delete them
            self.entry.destroy()
        self.objects = []                           #clear all arrays
        self.box_objects = []
        self.text_objects = []
        self.tag_objects = []
        self.parent_drop = []
        self.column_objects = []
        self.column_drop = []
        self.selected_objects = []
        self.target_objects = []
        self.connection_line = []
        self.connection_obj_1 = []
        self.connection_obj_2 = []
        self.entry = []
    
    #Clears target (objects to be connected) list
    def clear_target_objects(self):
        if self.target_objects:                                                                         #if target list exists, clear it
            self.target_objects = []
        self.update_colors()                                                                            #update object colors

    #Edit text boxes
    def on_text_click(self,event):
        clicked_text = self.canvas.find_overlapping(event.x, event.y, event.x+1, event.y+1)
        if clicked_text and len(clicked_text) > 1:                                                      #check a text box in an object was clicked
            if self.entry:                                                                              #if text box is open, save and close it
                self.update_text(self.text_id_hold)
            if clicked_text[1] in self.text_objects:                                                    #if clicked on title box
                text_id = clicked_text[1]                                                               #get id of box
                self.text_id_hold = text_id                                                             #globally save id to allow for other functions to close the box
                x,y = self.canvas.coords(text_id)                                                       #get coords of box
                text = self.canvas.itemcget(text_id,"text")                                             #get text
                self.entry = tk.Entry(self.canvas)                                                      #create text entry box
                self.entry.insert(0,text)                                                               #add existing text to the new box
                self.entry.place(x=x-(self.box_width/2),y=y-(self.box_height/4))                        #place entry box
                self.entry.bind("<Return>", lambda event, text_id=text_id: self.update_text(text_id))   #on "Enter" run save and close function
            # elif clicked_text[1] in self.tag_objects:                                                   #if click is on parent box
            #     text_id = clicked_text[1]                                                               #repeat function
            #     self.text_id_hold = text_id                                                             #should probably make this its own function, but there's a lot of info to pass
            #     x,y = self.canvas.coords(text_id)
            #     text = self.canvas.itemcget(text_id,"text")
            #     self.entry = tk.Entry(self.canvas)
            #     self.entry.insert(0,text)
            #     self.entry.place(x=x-(self.box_width/2),y=y-(self.box_height/4)) 
            #     self.entry.bind("<Return>", lambda event, text_id=text_id: self.update_text(text_id))
            # elif clicked_text[1] in self.column_objects:                                                #same deal for clicking on the column text
            #     text_id = clicked_text[1]
            #     self.text_id_hold = text_id
            #     x,y = self.canvas.coords(text_id)
            #     text = self.canvas.itemcget(text_id,"text")
            #     self.entry = tk.Entry(self.canvas)
            #     self.entry.insert(0,text)
            #     self.entry.place(x=x-(self.box_width/4),y=y-(self.box_height/4)) 
            #     self.entry.bind("<Return>", lambda event, text_id=text_id: self.update_text(text_id))
            else:
                pass

    #Update text from box, and close entry box
    def update_text(self,text_id):
        good_characters,error_message = self.check_text(self.entry.get())
        if good_characters:
            self.canvas.itemconfig(text_id, text=self.entry.get())      #get text from entry and enter into selected text box
        else:
            self.print_to_window(self.terminal_window,error_message,'error_text')
        self.entry.destroy()                                        #delete entry box
        self.update_text_list()                                     #update all text lists
        self.update_tag_list()
        self.update_column_list()
        self.entry = []                                             #delete entry id
        self.parent_menu = []
        for id in self.text_objects:
            self.parent_menu.append(self.canvas.itemcget(id,"text"))

    def check_text(self,text):
        if not text.isalnum():
            error_text = 'Species names can only contain alphanumeric characters'
            name_check = False
        elif text == 't':
            name_check = False
            error_text = 't is reserved and cannot be a species name'
        else:
            name_check = True
            error_text = ''
        return name_check,error_text

    #update list of object titles
    def update_text_list(self):
        self.text_list = []                                                 #clear title list
        for text_id in self.text_objects:
            self.text_list.append(self.canvas.itemcget(text_id,"text"))     #sequentially add all titles to list
    
    #update list of parents
    def update_tag_list(self):
        self.tag_list = []                                                  #clear parent list
        self.parent_menu = []
        for tag in self.parent_drop:
            self.tag_list.append(tag[1].get())                                 #sequentially add all parents to list
            self.parent_menu.append(self.tag_list[-1])

    #update list of column ids
    def update_column_list(self):                                           
        self.column_list = []                                               #clear column list
        self.column_menu = []
        for i,tag in enumerate(self.column_drop):
            self.column_list.append(tag[1].get())                              #sequentially add all column ids to the list
            self.column_menu.append(i+1)

    #Update all object colors
    def update_colors(self):
        for i in self.box_objects:                                          #box objects
            self.canvas.itemconfig(i,fill=self.box_color)
        for i in self.connection_line:                                      #connection lines
            self.canvas.itemconfig(i,fill=self.line_color)
        for i in self.delete_objects:                                       #overwrite to color deletion objects
            self.canvas.itemconfig(i,fill=self.delete_color)
        for i in self.target_objects:                                       #overwrite to color connection objects
            self.canvas.itemconfig(i,fill=self.target_color)

    #find box edges where arrows should start and end
    def get_box_intercept(self,x1,y1,x2,y2,width,height):
        dx = x1 - x2                                    #find direction in x and y from origin box to target box
        dy = y1 - y2
        xspot = x1 - math.copysign(1,dx)*(width/2)
        yspot = y1 - math.copysign(1,dy)*(height/2)
        if (x2-x1) == 0:                                #find line between box centers. If x coord is same set very steep slope to avoid /0
            slope = 10000
        else:
            slope = (y2-y1)/(x2-x1)
        intercept = y1 - slope*x1
        ycheck = slope*xspot + intercept                #check if line crosses vertical bound of box
        if ycheck <= y1 + (height/2) and ycheck >= y1 - (height/2):
            ycoord = ycheck                             #if yes, use found coords
            xcoord = xspot
        else:
            xcoord = (yspot-intercept)/slope            #else calculate intercept with x bound
            ycoord = yspot
        return(xcoord,ycoord)

    def browse_files(self,box_title,filetype_array):
        current_dir = os.getcwd()
        fullfile = filedialog.askopenfilename(initialdir=current_dir,title=box_title,filetypes=filetype_array)
        if fullfile:
            filepath = os.path.dirname(fullfile)
            filename = os.path.basename(fullfile)
            return(filepath,filename)
        else:
            filepath = []
            filename = []
            return(filepath,filename)

    def browse_mec_files(self):
        [self.mec_filepath,self.mec_filename] = self.browse_files("Select Model File",[("mec files","*.mec"),("all files","*.*")])
        if self.mec_filepath:
            self.mecfilebrowsed = True
            self.file_box.delete(0,tk.END)
            self.file_box.insert(0,self.mec_filename)

    def browse_data_files(self):
        [self.data_filepath,self.data_filename] = self.browse_files("Select Data File",[("txt files","*.txt"),("all files","*.*")])
        if self.data_filepath:
            self.datafilebrowsed = True
            self.data_file_entry.delete(0,tk.END)
            self.data_file_entry.insert(0,self.data_filename)

    def browse_result_files(self):
        [self.result_filepath,self.result_filename] = self.browse_files("Select Data File",[("txt files","*.txt"),("all files","*.*")])
        if self.result_filepath:
            self.resultfilebrowsed = True
            self.result_file_entry.delete(0,tk.END)
            self.result_file_entry.insert(0,self.result_filename)

    #import model from previously made file   
    def import_model(self):
        self.browse_mec_files()
        if not self.mec_filename:
            return
        if self.mecfilebrowsed:
            output_filepath = self.mec_filepath
        else:
            output_filepath = os.getcwd()
        filename = os.path.join(output_filepath,self.mec_filename)
        self.clear_objects()
        modelfile = open(filename,"r+")
        modeldata = modelfile.read().splitlines()                                           #read data from file
        modelfile.close
        species = modeldata[0].split(',')                                                   #format info for each object (title, parent, column number)
        parents = modeldata[1].split(',')
        columns = modeldata[4].split(',')
        locations = ast.literal_eval(modeldata[6])
        i=0
        for coords in locations:                                                            #loop through boxes
            xpos =  coords[0]                                                               #get coordinates
            ypos = coords[1]
            self.create_object(xpos,ypos,species[i],parents[i],columns[i])                  #create object with info at given position. Adds info to appropriate lists
            i=i+1
        
        connect1 = modeldata[2].split(',')                                                  #pull connection data
        connect2 = modeldata[3].split(',')
        i=0
        for con in connect1:                                                                #loop through connections
            specid1 = species.index(con)                                                    #get index of connection species in species list
            self.target_objects.append(self.box_objects[specid1])                           #use that index to get object id and append it to target array
            specid2 = species.index(connect2[i])                                            #repeat for second connection object
            self.target_objects.append(self.box_objects[specid2])
            self.connect_objects()                                                          #run connect objects function
            self.target_objects = []                                                        #clear target array to prevent overflow
            i=i+1
        
    #store drawn objects as mechanism
    def get_mechanism(self):
        if self.entry:                                                                  #if entry box is open, save and close it
            self.update_text(self.text_id_hold)
        self.update_text_list()                                                         #update title, parent, and column lists
        self.update_tag_list()
        self.update_column_list()
        reactant_list = []
        product_list = []
        for product_id in self.connection_obj_1:
            reactant_list.append(self.canvas.itemcget(product_id+1,"text"))             #get text of connection origin objects and add to reactant list
        for reactant_id in self.connection_obj_2:
            product_list.append(self.canvas.itemcget(reactant_id+1,"text"))             #get text of connection termination objects and add to product list
        model_id = self.model_box.get()                                                 #get model id from text box
        box_coords = []
        for box in self.box_objects:                                                    #get coordinates of each box and store
            box_loc = self.canvas.coords(box)
            box_coords.append([box_loc[0],box_loc[1]])
        output_array = [self.text_list,self.tag_list,reactant_list,product_list,self.column_list,model_id,box_coords]      #combine title, parent, reactants, products, columns, model, and coordinates into one array
        #self.write_mechanism(output_array)
        return(output_array)
        #print(output_array,)
        
    def write_mechanism(self,output_array):    
        output_filename = self.file_box.get()                                               #get file name from text box
        if self.mecfilebrowsed:
            output_filepath = self.mec_filepath
        else:
            output_filepath = os.getcwd()
        output_file = os.path.join(output_filepath,output_filename)
        if output_file.endswith(".mec") == False:                                       #if name does not include .mec extension...
            ext = os.path.splitext(output_file)                                         #check if another extension is present...
            if ext:
                output_file = re.sub(str(ext[1])+'$','',output_file)                    #if yes, remove it
            output_file = output_file + ".mec"                                          #add mec extension to base file name
        with open(output_file,'w') as f:                                                #save model info to file
            for arr in output_array:
                if isinstance(arr,list):
                    arr_str = ",".join(map(str,arr))
                else:
                    arr_str = str(arr)
                f.write(arr_str + "\n")
        print(output_file)
        output_base = output_file                                                       #insert model id into file name
        store_id = "_" + output_array[5] + ".mec"
        store_file = re.sub(r"\.mec",store_id,output_base)
        with open(store_file,'w') as f:                                                 #save model info to file with adjusted name
            for arr in output_array:
                if isinstance(arr,list):
                    arr_str = ",".join(map(str,arr))
                else:
                    arr_str = str(arr)
                f.write(arr_str + "\n")
        print(store_file)
        self.print_to_window(self.terminal_window,f"Wrote mechanism file: {os.path.basename(store_file)}")
        image_id = "_" + output_array[5] + "_img.png"                                          #form file name for screenshot
        image_file = re.sub(r"\.mec",image_id,output_base)

        self.save_canvas(image_file)                                                    #take screenshot of canvas and save as png. This seems to cause the canvas to rescale even though it doesn't touch that?????
        print(image_file)
        self.mechanism_file = output_file

    def get_and_write_mechanism(self):
        output_array = self.get_mechanism()
        self.write_mechanism(output_array)
    
    #save screenshot of canvas
    def save_canvas(self,imagefile):
        x = root.winfo_rootx() + self.canvas.winfo_x()                                  #get x and y coords of canvas on screen. This is wonky on multiple monitors. Python is adding extra pixels to my second monitor that don't exist. No idea why, but it screws up the coordinates
        y = root.winfo_rooty() + self.canvas.winfo_y()
        width = self.canvas.winfo_width()                                               #get width and height of canvas
        height = self.canvas.winfo_height()
        monitor_region = {"top":y, "left":x,"width":width,"height":height}              #set screenshot area using canvas position and size
        #screenshot = mss.mss().grab(monitor_region) 
        #only works on primary monitor, but avoids rescaling issue with mss
        pyautogui.screenshot(imagefile,region=(x,y,width,height))                                    #take screenshot
        #mss.tools.to_png(screenshot.rgb, screenshot.size, output=imagefile)             #save screenshot

    def solve_and_fit(self):
        self.print_to_window(self.terminal_window,'Solving mechanism and fitting to data...')
        mech_params = self.get_mechanism()
        if not mech_params[0]:
            self.print_to_window(self.terminal_window,'No mechanism present','error_text')
            return
        print(mech_params)
        self.write_mechanism(mech_params)
        
        #convert mech information to usuable data
        equation_array,equation_list,variable_lists,counter_lists,columntrack,mechanism_id = mech2eqn_array.eqn_format(mech_params)
        species,rates,parents = variable_lists
        interposit,inter_counter = counter_lists

        datafile_name = self.data_file_entry.get()
        if not datafile_name:
            self.print_to_window(self.terminal_window,'No data file selected','error_text')
            return
        if self.datafilebrowsed:
            datafile_path = self.data_filepath
        else:
            datafile_path = os.getcwd()
        datafile = os.path.join(datafile_path,datafile_name)
        self.print_to_window(self.terminal_window,f"Using data file: {datafile_name}")

        try:
            cleandata = []
            with open(datafile) as file:
                for line in file:
                    line = line.strip()
                    for delim in [",","\t"]:
                        line = line.replace(delim," ")
                    cleandata.append(line)
            rawdata = np.loadtxt(cleandata)
        except:
            self.print_to_window(self.terminal_window,'Unable to open data file','error_text')
            return
        num_data_columns = int(rawdata.size/len(rawdata)-1)
        y0_data = rawdata[:,1]

        number_rates = len(rates)
        number_species = len(species)
        number_parents = len(parents)

        base_lb = []
        base_ub = []
        base_guess = []
        for i in range(3):
            base_lb.append(float(self.parameter_entries[i].get()))
            base_ub.append(float(self.parameter_entries[i+3].get()))
            base_guess.append(float(self.parameter_entries[i+6].get()))

        if not num_data_columns == number_parents:
            self.print_to_window(self.terminal_window,'Number of data columns does not match number required for mechanism','error_text')
            return
        
        #get bounds and initial guesses
        #if individual parameters window not open use default values
        if not self.param_window or not tk.Toplevel.winfo_exists(self.param_window):
            self.print_to_window(self.terminal_window,'Applying default bounds to all species')
            lower_bounds = []
            for lb,bound in zip(base_lb,[number_rates,number_parents,number_parents]):
                lower_bounds.append([lb]*bound)
            lower_bounds = [item for sublist in lower_bounds for item in sublist]
            upper_bounds = []
            for ub,bound in zip(base_ub,[number_rates,number_parents,number_parents]):
                upper_bounds.append([ub]*bound)
            upper_bounds = [item for sublist in upper_bounds for item in sublist]
            initial_guesses = []
            for g,guess in zip(base_guess,[number_rates,number_parents,number_parents]):
                initial_guesses.append([g]*guess)
            initial_guesses = [item for sublist in initial_guesses for item in sublist]

        else:
            if len(self.k_g_array) != number_rates or len(self.y0_g_array) != number_parents:
                self.print_to_window(self.terminal_window,'Individual parameters do not match mechanism. Update parameters window','error_text')
                return
            self.print_to_window(self.terminal_window,'Using individual parameter bounds')
            lower_bounds = []
            lower_bound_list = self.k_lb_array + self.y0_lb_array + self.bc_lb_array
            for entry in lower_bound_list:
                lower_bounds.append(float(entry.get()))
            upper_bounds = []
            upper_bound_list = self.k_ub_array + self.y0_ub_array + self.bc_ub_array
            for entry in upper_bound_list:
                upper_bounds.append(float(entry.get()))
            initial_guesses = []
            initial_guess_list = self.k_g_array + self.y0_g_array + self.bc_g_array
            for entry in initial_guess_list:
                initial_guesses.append(float(entry.get()))

        #y0 formatting
        y0_bound_mode = self.y0_mode.get()
        y0_bound = float(self.y0_multiplier.get())
        y0_guesses = [None]*number_parents
        y0_lb = [None]*number_parents
        y0_ub = [None]*number_parents
        if y0_bound_mode == 'Fit':
            if not self.param_window or not tk.Toplevel.winfo_exists(self.param_window):
                self.print_to_window(self.terminal_window,'Fitting function start points based on initial data points')
                for i in range(number_parents):
                    y0_guesses[i] = y0_data[i]
                    y0_lb[i] = y0_guesses[i] - y0_guesses[i]*y0_bound
                    y0_ub[i] = y0_guesses[i] + y0_guesses[i]*y0_bound
            else:
                self.print_to_window(self.terminal_window,'Fitting function start points with individual bounds')
                y0_guesses = initial_guesses[number_rates:number_rates+number_parents]
                y0_lb = y0_guesses
                y0_ub = y0_guesses
        elif y0_bound_mode == 'User':
            if not self.param_window or not tk.Toplevel.winfo_exists(self.param_window):
                self.print_to_window(self.terminal_window,'Tried to use user set function start points, but individual values not set','error_text')
                return
            else:
                self.print_to_window(self.terminal_window,'Using individually set values for function start points')
                y0_guesses = initial_guesses[number_rates:number_rates+number_parents]
                y0_lb = y0_guesses
                y0_ub = y0_guesses
        elif y0_bound_mode == 'Data':
            self.print_to_window(self.terminal_window,'Using first data points as function start points')
            for i in range(number_parents):
                y0_guesses[i] = y0_data[i]
                y0_lb[i] = y0_guesses[i]
                y0_ub[i] = y0_guesses[i]
        else:
            self.print_to_window(self.terminal_window,'Incorrect or no mode set for function start points','error_text')
        initial_guesses[number_rates:number_rates+number_parents] = y0_guesses
        lower_bounds[number_rates:number_rates+number_parents] = y0_lb
        upper_bounds[number_rates:number_rates+number_parents] = y0_ub

        for lb,ub in zip(lower_bounds,upper_bounds):
            if lb > ub:
                self.print_to_window(self.terminal_window,'A lower bound is larger than its upper bound','error_text')
                return
        
        for i in range(number_rates+number_parents+number_parents):
            if initial_guesses[i] < lower_bounds[i] or initial_guesses[i] > upper_bounds[i]:
                initial_guesses[i] = (upper_bounds[i]+lower_bounds[i])/2
                self.print_to_window(self.terminal_window,f"Initial guess {str(i)} outside bounds, reset to average of bounds")

        if not len(initial_guesses) == number_rates+number_parents+number_parents:
            self.print_to_window(self.terminal_window,'Wrong number of initial guesses','error_text')
            return
        if not len(lower_bounds) == len(initial_guesses):
            self.print_to_window(self.terminal_window,'Wrong number of lower bounds','error_text')
            return
        if not len(upper_bounds) == len(initial_guesses):
            self.print_to_window(self.terminal_window,'Wrong number of upper bounds','error_text')
            return
        
        for g,lb,ub in zip(initial_guesses,lower_bounds,upper_bounds):
            if not g or not lb or not ub:
                if not isinstance(g,(int,float)) or not isinstance(lb,(int,float)) or not isinstance(ub,(int,float)):
                    print(g,lb,ub)
                    self.print_to_window(self.terminal_window,'Blank entry found in bounds or initial values','error_text')
                    return

        for i in range(len(lower_bounds)):
            if upper_bounds[i] <= lower_bounds[i]:
                if not upper_bounds[i] == 0:
                    upper_bounds[i] = upper_bounds[i] + upper_bounds[i]*.001
                else:
                    upper_bounds[i] = upper_bounds[i] + .00001
        #print(lower_bounds,upper_bounds,initial_guesses)
        self.print_to_window(self.terminal_window,'Fitting...')
        data_array,report_array,variable_sizes,variable_lists,iterators,fit_quality = diffsolve.solve_differential(initial_guesses,lower_bounds,upper_bounds,datafile,mech_params)
        #print(report_array)

        species,parents,rates = variable_lists
        number_rates,number_species,number_columns = variable_sizes
        interposit,inter_counter = iterators
        outdata,out_header = data_array
        overall_rss,overall_r2 = fit_quality

        self.print_to_window(self.terminal_window,f"Overall RSS is {overall_rss:<4}")
        self.print_to_window(self.terminal_window,f"Overall R2 is {overall_r2:<4}")

        plt.close('all')
        fig1,ax1 = plt.subplots()
        labels = species
        index = 0
        colors = distinctipy.get_colors(number_columns)
        for i in range(int(number_columns)):
            ax1.scatter(outdata[:,[0]], outdata[:,[i+1]], marker=".",s=32, label=f'{labels[inter_counter[i]]}',color=colors[i])
            for j in range(interposit[i]):
                ax1.plot(outdata[:,[0]],outdata[:,[index+number_columns+1]],linestyle="--",color=colors[i])
                index=index+1
            ax1.plot(outdata[:,[0]], outdata[:,[i+number_columns+number_species+1]],color=colors[i])
        plt.xlabel('Time')
        plt.ylabel('Abundance')
        plt.title('Kinetic Data Fit')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show(block=False)

        resultfile_name = self.result_file_entry.get()
        if not resultfile_name:
            self.print_to_window(self.terminal_window,'No output file name selected','error_text')
            return
        if self.resultfilebrowsed:
            resultfile_path = self.result_filepath
        else:
            resultfile_path = os.getcwd()

        fitdata_string = '_' + self.model_box.get() + '_fit_data.txt'
        fitbase_string = os.path.splitext(resultfile_name)[0]
        fitdata_name = fitbase_string + fitdata_string
        resultfile = os.path.join(resultfile_path,fitdata_name)
        np.savetxt(resultfile,outdata,delimiter=',',header=out_header)
        self.print_to_window(self.terminal_window,f"Wrote fitting data to: {fitdata_name}")

        fitreport_string = '_' + self.model_box.get() + '_fit_report.txt'
        fitreport_name = fitbase_string + fitreport_string
        reportfile = os.path.join(resultfile_path,fitreport_name)
        report_array.append(f"\nInput mechanism file is: {self.mechanism_file}")
        report_array.append(f"Input data file is: {datafile}")
        report_array.append("\n\nRateSolve: Anthony Pestritto, Indiana University, Department of Chemistry. 2025")
        with open(reportfile,'w') as report_file:
            for row in report_array:
                report_file.write(row + '\n')
        self.print_to_window(self.terminal_window,f"Wrote fitting report to: {fitreport_name}")

    def generate_data(self):
        self.print_to_window(self.terminal_window,'Solving mechanism and generating data...')
        mech_params = self.get_mechanism()
        if not mech_params[0]:
            self.print_to_window(self.terminal_window,'No mechanism present','error_text')
            return
        
        #convert mech information to usuable data
        equation_array,equation_list,variable_lists,counter_lists,columntrack,mechanism_id = mech2eqn_array.eqn_format(mech_params)
        species,rates,parents = variable_lists
        interposit,inter_counter = counter_lists

        number_rates = len(rates)
        number_species = len(species)
        number_parents = len(parents)

        t_start = int(self.xmin_entry.get())
        t_end = int(self.xmax_entry.get())
        t_points = int(self.xnum_entry.get())
        ynoise = float(self.ynoise_entry.get())

        t_data = np.linspace(t_start,t_end,t_points)

        start_index = []
        i=0
        for eqn in equation_list:
            if eqn[0] == '-':
                start_index.append(i)
            i=i+1
        y0_values = [0]*number_parents
        for starty in start_index:
            y0_values[int(starty)] = 1

        base_guess = []
        for i in range(3):
            base_guess.append(float(self.parameter_entries[i+6].get()))

        if not self.param_window or not tk.Toplevel.winfo_exists(self.param_window):
            self.print_to_window(self.terminal_window,'Applying default bounds to all species')
            initial_guesses = []
            for g,guess in zip(base_guess,[number_rates,number_parents,number_parents]):
                initial_guesses.append([g]*guess)
            initial_guesses = [item for sublist in initial_guesses for item in sublist]
            for i,y0 in enumerate(y0_values):
                initial_guesses[number_rates+i] = y0

        else:
            self.print_to_window(self.terminal_window,'Using individual parameter bounds')
            initial_guesses = []
            initial_guess_list = self.k_g_array + self.y0_g_array + self.bc_g_array
            for entry in initial_guess_list:
                initial_guesses.append(float(entry.get()))

        #Solve differential system and get y values
        generated_data = diffgen.generate_differential(initial_guesses,t_data,mech_params)
        gen_data,y_header = generated_data
        y_data = gen_data[:,1:]
        y_shape = y_data.shape

        #add noise to data
        random_array = np.random.uniform(-1,1,size=(y_shape[0],y_shape[1]))
        scaled_array = (random_array/100)*ynoise
        y_data_noise = y_data + scaled_array
        y_data_noise[y_data_noise < 0] = 0
        y_max = np.max(y_data_noise)
        y_data_noise = y_data_noise/y_max
        row_sums = np.sum(y_data_noise,axis=1,keepdims=True)
        ynorm = y_data_noise/row_sums

        plt.close('all')
        colors = distinctipy.get_colors(number_parents)
        fig2,ax1 = plt.subplots()
        if ynoise == 0:
            for i in range(int(number_parents)):
                ax1.plot(t_data, ynorm[:,[i]], 'o-',color=colors[i],label=f'{parents[i]}')
        else:
            for i in range(int(number_parents)):
                ax1.scatter(t_data, ynorm[:,[i]], marker='.',s=64,color=colors[i],label=f'{parents[i]}')
        plt.xlabel('Time')
        plt.ylabel('Abundance')
        plt.title('Generated Data')
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show(block=False)

        resultfile_name = self.result_file_entry.get()
        if not resultfile_name:
            self.print_to_window(self.terminal_window,'No output file name selected','error_text')
            return
        if self.resultfilebrowsed:
            resultfile_path = self.result_filepath
        else:
            resultfile_path = os.getcwd()

        t_data = t_data.reshape(-1,1)
        outdata = np.concatenate((t_data,ynorm),axis=1)
        fitdata_string = '_' + self.model_box.get() + '_sim_data.txt'
        fitbase_string = os.path.splitext(resultfile_name)[0]
        fitdata_name = fitbase_string + fitdata_string
        resultfile = os.path.join(resultfile_path,fitdata_name)
        np.savetxt(resultfile,outdata,delimiter=',')
        self.print_to_window(self.terminal_window,f"Wrote generated data to: {fitdata_name}")

    def plot_data(self):
        self.print_to_window(self.terminal_window,'Plotting data...')
        datafile_name = self.data_file_entry.get()
        if not datafile_name:
            self.print_to_window(self.terminal_window,'No data file selected','error_text')
            return
        if self.datafilebrowsed:
            datafile_path = self.data_filepath
        else:
            datafile_path = os.getcwd()
        datafile = os.path.join(datafile_path,datafile_name)
        self.print_to_window(self.terminal_window,f"Using data file: {datafile_name}")

        try:
            cleandata = []
            with open(datafile) as file:
                for line in file:
                    line = line.strip()
                    for delim in [",","\t"]:
                        line = line.replace(delim," ")
                    cleandata.append(line)
            rawdata = np.loadtxt(cleandata)
            #rawdata = np.genfromtxt(datafile,delimiter=',')
        except:
            self.print_to_window(self.terminal_window,'Unable to open data file','error_text')
            return
        number_columns = int(rawdata.size/len(rawdata)-1)
        t_data = rawdata[:,0]
        y_data = rawdata[:,1:]

        plt.close('all')
        colors = distinctipy.get_colors(number_columns)
        fig2,ax1 = plt.subplots()
        for i in range(int(number_columns)):
            ax1.scatter(t_data, y_data[:,[i]], marker=".",s=32,color=colors[i])
        plt.xlabel('Time')
        plt.ylabel('Abundance')
        plt.title('Data')
        plt.grid(True)
        plt.tight_layout()
        plt.show(block=False)


if __name__ == "__main__":
    root = tk.Tk()
    app = FlowChartApp(root)
    root.mainloop()