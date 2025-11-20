import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
from scipy.optimize import least_squares
from sympy import symbols, lambdify, sympify, parse_expr
import mech2eqn_array

#Adds the y values of hidden intermediates to the parent values
def hidinter_combine(y_sol,hidinter_array,num_columns):
    i = 0
    hidcount = 0
    comb_intermediates = np.zeros([num_columns,np.size(y_sol,1)])
    for intcount in hidinter_array:
        comb_intermediates[i,:] = sum(y_sol[hidcount:hidcount+intcount])
        hidcount = hidcount+intcount
        i=i+1

    return(comb_intermediates)

#set up differential system with numeric values and range
def ode_system(t, y_vec, params, ode_func):
    return ode_func(t, *y_vec, *params)

#run numeric solver
def solve_ode(params, t_span, size_array, t_eval, ode_values):
    ode_func = ode_values[0]
    interposit = ode_values[1]
    inter_counter = ode_values[2]
    rates = params[0:size_array[0]]
    y0 = params[size_array[0]:size_array[0]+size_array[2]]
    bc = params[size_array[0]+size_array[2]:]
    y0_sub = np.zeros(size_array[1])
    i=0
    for base in bc:
        y0_sub[inter_counter[i]] = y0[i] - 0 #base
        i=i+1
    sol = solve_ivp(lambda t, y: ode_system(t, y, rates, ode_func), t_span, y0_sub, t_eval=t_eval, method='RK45')
    y_comb = hidinter_combine(sol.y,interposit,size_array[2])
    y_corr = np.empty([np.size(y_comb,0),np.size(y_comb,1)])
    i = 0
    for baseline in bc:
        y_corr[i,:] = y_comb[i,:] + baseline
        i=i+1
    y_hidden = sol.y
    i=0
    for index in inter_counter:
        y_hidden[index,:] = y_hidden[index,:] + bc[i]
        i=i+1
    return y_corr,y_hidden

def generate_differential(initial_values,t_data,mechanism):

    eqns,eqn_list,variable_lists,variable_counters,column_track,mech_id = mech2eqn_array.eqn_format(mechanism)
    species,rates,parents = variable_lists
    interposit,inter_counter = variable_counters

    number_species = len(species)
    number_rates = len(rates)
    number_parents = len(parents)

    t = symbols('t')
    y = symbols(species)
    k = symbols(rates)

    equation_strings = eqn_list

    # Convert strings to sympy expressions
    variable_names = species + rates                                                #form list of variables
    variable_dict = {name: symbols(name) for name in variable_names}                #create symbolic dictionary of variables
    equations = []
    for eq in equation_strings:                                                     #loop through set of equations
        eq_sym = parse_expr(eq, local_dict=variable_dict)                           #parse equation string and substitute in symbolic values (with dictionary acts as sanitation)
        equations.append(sympify(eq_sym))                                           #convert to symbolic equation

    #combine equations into one system
    ode_func = lambdify((t, *y, *k), equations, modules='numpy')

    #set up arrays for passing information to solving functions
    type_sizes = [number_rates,number_species,number_parents]
    ode_values = [ode_func,interposit,inter_counter]

    y_fit,y_fit_hidden = solve_ode(initial_values, (t_data[0], t_data[-1]), type_sizes, t_data, ode_values)
   
    #make output data array
    t_out_array = np.array(t_data,ndmin=2).reshape(-1,1)
    yfit_out_array = np.array(y_fit,ndmin=2).T
    row_sums = np.sum(yfit_out_array,axis=1,keepdims=True)
    print(row_sums)
    print(yfit_out_array)
    ynorm = yfit_out_array/row_sums
    outdata = t_out_array
    outdata = np.append(outdata,ynorm,axis=1)
    parent_string = ",".join(parents)
    header_string = 'time,'+parent_string

    return [outdata,header_string]