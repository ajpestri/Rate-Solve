# %%
import numpy as np
import re

def eqn_format(mechcontent):
    #open mechanism file
    # mechfile = open(file_name,"r")
    # mechcontent = mechfile.readlines()
    # mechfile.close()
    # mechcontent = [line.rstrip('\n') for line in mechcontent]

    #extract components of mechanism (species, parents, reactants, products, data column number)
    species = mechcontent[0]    #.split((','))
    parents = mechcontent[1]    #.split((','))
    reactants = mechcontent[2]  #.split((','))
    products = mechcontent[3]   #.split((','))
    columntrack = mechcontent[4]    #.split((','))
    mechanism_id = mechcontent[5]   #.split((','))

    column_numbers = list(set(columntrack))
    species_list = list(species)                                                                              #pre-allocate with a full array because python is dumb. This caused more problems because python really doesn't want to add things to lists in nonsequential order
    species_count = np.linspace(1,len(column_numbers),len(column_numbers))
    column = 0
    for i in species_count:                                                                                 #loop through species
        species_index = [j for j, comparator in enumerate(columntrack) if comparator == str(int(i))]          #get all columns for each iteration
        if len(species_index) == 1:
            species_list[int(column)] = species[int(species_index[0])]                                          #if only one column, drop into column ordered spot on list
        else:
            parent = parents[int(species_index[0])]                                                             #if more than one column, species has hidden intermediates. get parent species
            parent_index = species.index(parent)
            species_list[int(column)] = species[int(parent_index)]
            species_index.remove(parent_index)
            for index in species_index:
                column = column + 1
                species_list[int(column)] = species[int(index)]
        column = column + 1

    eqns = []
    for spec in species_list:
        reactants_location = [j for j, comparator in enumerate(reactants) if comparator == spec]
        product_eqn = []
        if reactants_location:
            for react_idx in reactants_location:
                product_eqn.append('-k'+spec+products[int(react_idx)]+'*'+spec)
        else:
            product_eqn = ''
        product_sequence = ''.join(product_eqn)
        
        products_location = [j for j, comparator in enumerate(products) if comparator == spec]
        reactant_eqn = []
        if products_location:
            for prod_idx in products_location:
                reactant_eqn.append('+k'+reactants[int(prod_idx)]+spec+'*'+reactants[int(prod_idx)])
        else:
            reactant_eqn = ''
        reactant_sequence = ''.join(reactant_eqn)
        eqns.append(reactant_sequence + product_sequence)

    equation_list = []
    for eqn in eqns:
        if eqn.startswith('+'):
            shorteqn = eqn[1:]
        else:
            shorteqn = eqn
        equation_list.append(shorteqn)    
        #print(shorteqn)

    rate_list = []
    i=0
    for react in reactants:
        rate_list.append('k'+react+products[i])
        i=i+1

    interposit = []
    for spec in species_list: interposit.append(parents.count(spec))
    while 0 in interposit: interposit.remove(0)

    inter_counter = []
    for i in range(len(interposit)):
        inter_counter.append(sum(interposit[0:i]))

    parent_list = []
    for i in range(len(interposit)):
        parent_list.append(species_list[inter_counter[i]])

    #print(species_list)
    #print(interposit)
    #print(rate_list)
    #print(mechanism_id)

    #format equations for solving
    equation_array = []
    for eqn in equation_list:
        spec_count = 0
        for spec in species_list:
            target_string = r"(?<![\w])" + spec + r"(?![\w])"
            replace_string = 'y[' + str(spec_count) + ']'
            eqn = re.sub(target_string,replace_string,eqn)
            spec_count = spec_count + 1
        k_count = 0
        for k in rate_list:
            target_string = r"(?<![\w])" + k + r"(?![\w])"
            replace_string = 'k[' + str(k_count) + ']'
            eqn = re.sub(target_string,replace_string,eqn)
            k_count = k_count + 1
        equation_array.append(eqn)

    return(equation_array,equation_list,[species_list,rate_list,parent_list],[interposit,inter_counter],columntrack,mechanism_id)

# file_name = "mech_test_3h1.mec"
# mechfile = open(file_name,"r")
# mechcontent = mechfile.readlines()
# mechfile.close()
# mechcontent = [line.rstrip('\n') for line in mechcontent]
# i=0
# for mechline in mechcontent:
#     mechcontent[i] = mechline.split((','))
#     i=i+1

# print(eqn_format(mechcontent))
# %%
