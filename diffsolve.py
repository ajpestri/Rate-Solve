# %%
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
from scipy.optimize import least_squares
from sympy import symbols, lambdify, sympify, parse_expr
import mech2eqn_array

#bound and guess values: rates, x=0 function value, baseline correction value
#number of rate values = number rate constants
#number of y0 values = number of data columns
#number of baseline values = number of data columns
#mechanism file: output from Mech_Draw
#data file: comma delimited numerical file. First column is x values. then column for each set of y data

#calculates rss
def rss(data,fit):
    e = data - fit
    esq = e**2
    Sres = sum(esq)
    return Sres

#calculates rsquared
def r2(data,fit):
    Sres = rss(data,fit)
    Stot = sum(fit)
    Rsq = 1-(Sres/Stot)
    return Rsq

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
        y0_sub[inter_counter[i]] = y0[i] - base
        i=i+1
    sol = solve_ivp(lambda t, y: ode_system(t, y, rates, ode_func), t_span, y0_sub, t_eval=t_eval, method='RK45')
    y_comb = hidinter_combine(sol.y,interposit,size_array[2])
    y_corr = y_comb #np.empty([np.size(y_comb,0),np.size(y_comb,1)])
    #add baseline to data with hidden intermediates added to parent data
    i = 0
    for baseline in bc:
        y_corr[i,:] = y_comb[i,:] + baseline
        i=i+1
    #add baseline to individual data (hidden intermediates not summed)
    y_hidden = sol.y
    i=0
    for index in inter_counter:
        y_hidden[index,:] = y_hidden[index,:] + bc[i]
        i=i+1
    return y_corr,y_hidden

#call solver, calculate residuals between data and solved fit
def residuals(p, t_data, y_data, size_array,ode_values):
    y_model,yunused = solve_ode(p, (t_data[0], t_data[-1]), size_array, t_data,ode_values)
    residual = np.ravel(y_model - y_data)
    #print(sum(abs(residual)))
    return residual

def solve_differential(initial_guesses,lower_bounds,upper_bounds,datafile,mechanism):
    #import mechanism
    eqns,eqn_list,variable_lists,variable_counters,column_track,mech_id = mech2eqn_array.eqn_format(mechanism)
    species,rates,parents = variable_lists
    interposit,inter_counter = variable_counters

    #import data
    #rawdata = np.genfromtxt(datafile,delimiter=',')
    cleandata = []
    with open(datafile) as file:
        for line in file:
            line = line.strip()
            for delim in [",","\t"]:
                line = line.replace(delim," ")
            cleandata.append(line)
    rawdata = np.loadtxt(cleandata)
    num_columns = int(rawdata.size/len(rawdata)-1)
    t_data = rawdata[:,0]
    y_data = np.transpose(rawdata[:,1:])

    #calculate number of species and rate constants
    number_species = len(species)
    number_rates = len(rates)
    # inter_counter = []
    # for i in range(num_columns):
    #     inter_counter.append(sum(interposit[0:i]))
    # parents = []
    # for i in range(num_columns):
    #     parents.append(species[inter_counter[i]])

    #Define symbolic variables
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
    type_sizes = [number_rates,number_species,num_columns]
    ode_values = [ode_func,interposit,inter_counter]
    
    #Fit parameters
    result = least_squares(residuals, initial_guesses, args=(t_data, y_data, type_sizes,ode_values),bounds=(lower_bounds,upper_bounds))
    fitted_params = result.x
    print(fitted_params)

    #Solve with fitted parameters
    y_fit,y_fit_hidden = solve_ode(fitted_params, (t_data[0], t_data[-1]), type_sizes, t_data, ode_values)
    fitted_rates = fitted_params[0:number_rates]
    fitted_y0 = fitted_params[number_rates:number_rates+num_columns]
    fitted_bc = fitted_params[number_rates+num_columns:]
    #print(fitted_rates)
    #print(fitted_y0)
    #print(fitted_bc)

    #calculate R2 and RSS for each species and overall system
    residual_sums = []
    rsquared = []
    Resq = []
    Sres = []
    Ryf = []
    Stot = []
    for i in range(num_columns):
        residual_sums.append(rss(y_data[i],y_fit[i]))
        rsquared.append(r2(y_data[i],y_fit[i]))
        Ryhat = sum(y_data[i])/len(y_data[i])
        for yd,yf in zip(y_data[i],y_fit[i]):
            Re = yd-yf
            Resq.append(Re**2)
            Ryf.append((yd-Ryhat)**2)
        Sres.append(sum(Resq))
        Stot.append(sum(Ryf))
    StotT = sum(Stot)
    overall_rss = sum(Sres)
    overall_r2 = 1-(overall_rss/StotT)
    print(overall_rss)
    print(overall_r2)

    #make report array
    report_array = []
    title_row = [f"{'Species':<10}",f"{'RSS':<10}",f"{'R-Squared':<10}",f"{'x0 Value':<10}",f"{'Baseline':<10}"]
    report_array.append('\t'.join(title_row))
    i=0
    for spec in parents:
        species_row = [f"{spec:<10}",f"{residual_sums[i]:<10.6f}",f"{rsquared[i]:<10.6f}",f"{fitted_y0[i]:<10.6f}",f"{fitted_bc[i]:<10.6f}"]
        report_array.append('\t'.join(map(str,species_row)))
        i=i+1
    overall_row = [f"{'Overall':<10}",f"{overall_rss:<10.6f}",f"{overall_r2:<10.6f}",f"{'N/A':<10}",f"{'N/A':<10}"]
    report_array.append('\t'.join(map(str,overall_row)))
    report_array.append(f"\nOverall RSS is {overall_rss:.6f}")
    report_array.append(f"\nOverall R-Squared is {overall_r2:.6f}\n")
    rate_title_row = [f"{'Rate Constant':<15}",f"{'Value':<15}"]
    report_array.append('\t'.join(map(str,rate_title_row)))
    i=0
    for r in rates:
        rate_row = [f"{r:<15}",f"{fitted_rates[i]:<15.10f}"]
        report_array.append('\t'.join(map(str,rate_row)))
        i=i+1
    #report_array.append(f"\nInput mechanism file is: {mechfile}")
    #report_array.append(f"Input data file is: {datafile}")
    #report_array.append("\n\nRateSolve: Anthony Pestritto, Indiana University, Department of Chemistry. 2025")

    #make output data array
    t_out_array = np.array(t_data,ndmin=2).reshape(-1,1)
    y_out_array = np.array(y_data,ndmin=2).T
    yfit_out_array = np.array(y_fit,ndmin=2).T
    yfit_hid_out_array = np.array(y_fit_hidden,ndmin=2).T
    species_string = ",".join(species)
    parent_string = ",".join(parents)
    outdata = t_out_array
    index = 0
    for i in range(num_columns):
        species_subarray = y_out_array[:,[i]]
        for j in range(interposit[i]):
            species_subarray = np.append(species_subarray,yfit_hid_out_array[:,[index]],axis=1)
            index=index+1
        species_subarray = np.append(species_subarray,yfit_out_array[:,[i]],axis=1)
    outdata = np.append(outdata,y_out_array,axis=1)
    outdata = np.append(outdata,yfit_hid_out_array,axis=1)
    outdata = np.append(outdata,yfit_out_array,axis=1)
    header_string = 'time,'+parent_string+','+species_string+','+parent_string

    #output data, report, and info for writing and plotting
    return [outdata,header_string], report_array, [number_rates,number_species,num_columns], [species,parents,rates],[interposit,inter_counter],[overall_rss,overall_r2]

# mechanism_file = "mech_test_5s2.mec"
# datafile_name = 'mech_test_5s2_simdata.txt'
# output_data_file = "mech_test_5s2_py_data.txt"
# output_report_file = "mech_test_5s2_py_report.txt"

# lower_bounds = [0,0,0,0,0,0,0,0,0,0,0,0,0,0]
# upper_bounds = [10,10,10,10,1,1,.001,.001,.001,.001,.001,.001,.001,.001]
# initial_guesses = [1,1,1,1,1,1,0,0,0,0,0,0,0,0]

# mechfile = open(mechanism_file,"r")
# mechcontent = mechfile.readlines()
# mechfile.close()
# mechcontent = [line.rstrip('\n') for line in mechcontent]
# i=0
# for mechline in mechcontent:
#     mechcontent[i] = mechline.split((','))
#     i=i+1

# data_array,report_array,variable_sizes,variable_lists,iterators = solve_differential(initial_guesses,lower_bounds,upper_bounds,datafile_name,mechcontent)

# species,parents,rates = variable_lists
# number_rates,number_species,num_columns = variable_sizes
# interposit,inter_counter = iterators
# outdata,out_header = data_array

# with open(output_report_file,'w') as report_file:
#     for row in report_array:
#         report_file.write(row + '\n')

# #Plot results
# fig2,ax1 = plt.subplots()
# labels = species
# index = 0
# colors = distinctipy.get_colors(num_columns)
# for i in range(int(num_columns)):
#     ax1.scatter(outdata[:,[0]], outdata[:,[i+1]], marker=".",s=32, label=f'{labels[inter_counter[i]]}',color=colors[i])
#     for j in range(interposit[i]):
#         ax1.plot(outdata[:,[0]],outdata[:,[index+num_columns+1]],linestyle="--",color=colors[i])
#         index=index+1
#     ax1.plot(outdata[:,[0]], outdata[:,[i+num_columns+number_species+1]],color=colors[i])
# plt.xlabel('Time')
# plt.ylabel('Values')
# plt.title('ODE Fit to Data')
# plt.legend()
# plt.grid(True)
# plt.tight_layout()
# plt.show()
# %%
