# -*- coding: utf-8 -*-
"""
Created on Tue Oct 22 11:53:04 2024

@author: oscar
"""

# From a determined IF frequency for the first filter, an IF filter has to be 
# chosen. According to the material, the first IF filter's %BW has to be 10 
# times that of the second filter. It will decrease cost if the first filter's
# %BW is not too small. Therefore, we will let some spurs through around our 
# signal, which will then be mixed. The second IF frequency chosen not only has
# to be under 500 MHz but also not have any overlaps with any of the spurs 
# allowed through after the first mixing and filtering stage.


# FUNCTIONS
import matplotlib.pyplot as plt

def calc_LO(f_RF, f_IF):
    return f_RF - f_IF

def calc_spurs(f_RF, f_LO): # IF is at position [3]
    spurs = [f_RF, f_LO, 
             f_RF + f_LO, abs(f_RF - f_LO), 2*f_LO, 2*f_RF,
             abs(2*f_RF - f_LO), abs(2*f_LO - f_RF), 3*f_RF, 3*f_LO, 
             2*f_RF + f_LO, 2*f_LO + f_RF]
    return spurs

def find_overlap(f_IF, spurs):
    
    if f_IF in spurs:
        indx = spurs.index(f_IF)
        return [True, indx]
    else:
        return[False, 0]

def disp_spurs_and_type(spurs_let_through, spur_types, index):
    band_spurs = spurs_let_through[index]
    band_types = spur_types[index]
    
    for i in range(len(band_spurs)):
        spur = band_spurs[i]
        order = band_types[i][0]
        origin = band_types[i][1]
        if order < 2: order = 1
        elif order > 1 and order < 6: order = 2
        else: order = 3
        
        print('The spur at ' + str(spur/1e9) + 'GHz is from ' + str(origin/1e9) + 'GHz and is of order ' + str(order))


# PARAMETERS
f_IF = 1.0175e9 # GHz, this is the IF frequency after the first mixing stage.
filter_1_BW = 10 # %, the first filter's %BW


# Setting up the channels
freq = 3.005e9
channels = [freq]

while freq < 4.995e9:
    freq += 5e6
    channels.append(freq)

# The channels are split up into 2 sections
filter_bands = [channels[:200], channels[200:]]



# Finding the resulting spurs that will be within the first filter's BW

del_f = (filter_1_BW/100)*f_IF
del_f /= 2

filter_max = f_IF + del_f        # Adding and subtracting the half bandwidth of
filter_min = f_IF - del_f        # of the filter will give the max and min 
                                 # frequencies let through by the filter

# spurs_let_through = [[1st channel], [2nd channel], [3rd channel], [4th channel]]
spurs_let_through = []
spur_types = []
counter = 0
denominator = 0

for band in filter_bands:
    channel_spurs = []
    types = []
    
    for desired_channel in band:
        f_LO = calc_LO(desired_channel, f_IF)
        
        for f_RF in band:
            
            if f_RF != desired_channel:
                spurs = calc_spurs(f_RF, f_LO)
                
                for spur in spurs:
                    denominator += 1
                    if spur <= filter_max and spur >= filter_min:
                        counter += 1
                        if spur not in channel_spurs:
                            channel_spurs.append(spur)
                            types.append([spurs.index(spur), f_RF])
                            
    spurs_let_through.append(channel_spurs)
    spur_types.append(types)
    
 
# The loop above goes through every possible desired RF channel in each of the 
# 4 bands. A respective f_LO is calculated for each channel, which is then used
# to find all the spurs that would appear for that local oscillator frequency.
# If the spur calculated is within the BW of the IF filter, it is recorded for 
# its respective band. If a spur is already in the list, it is not added (no 
# point recording the same spur twice, even from a different RF)

print()
print('SPURS THAT ARE LET THROUGH THE FIRST FILTER')
print(str(counter) + '/' + str(denominator) + ' spurs were let through in total')
print('Which equates to ' + str(sum(len(spur) for spur in spurs_let_through)) + ' unique spurs')
print()

print('First Band')
disp_spurs_and_type(spurs_let_through, spur_types, 0)
print()
print('Second Band')
disp_spurs_and_type(spurs_let_through, spur_types, 1)
print()
print()


# Plotting the position of the spurs

plt.figure()
for value in spurs_let_through[0]:
        plt.axvline(x=value, color='r', linestyle='--')
plt.grid(True, which='both', linestyle='--', linewidth=0.5)
plt.xlim(min(spurs_let_through[0]) - 1, max(spurs_let_through[0]) + 1)
plt.ylim(-1, 1)



# Finding the best second IF frequency after mixing the new spurs

# IF Domain
freq = 150e6
f_IF_list = [freq]

while freq < 500e6:
    freq += 1e6
    f_IF_list.append(freq)

f_RF = f_IF
good = []
to_remove = []

all_spurs = []
for band in spurs_let_through:
    for spur in band:
        if spur not in all_spurs:
            all_spurs.append(spur) # List containing the unique spurs let 
                                   # through by the IF filter.
print('Across all 4 bands there are', len(all_spurs),'unique spurs')

good = []
for f_IF in f_IF_list:
    found = False
    f_LO = calc_LO(f_RF, f_IF)
    
    for RF in all_spurs:
        
        new_spurs = calc_spurs(RF, f_LO)
        overlap = find_overlap(f_IF, new_spurs)
        
        if overlap[0]:
            found = True
            break
    if found == False:
        good.append(f_IF)
    
print('There are ' + str(len(good)) + '/' + str(len(f_IF_list)) + ' valid IF frequencies')


# Out of the valid IF frequencies, we need to find the IF frequency which is 
# furthest away from all other spurs

def calc_percentage_BW(spur_value, f_IF):
    return 100*((2*abs(spur_value - f_IF)) / (f_IF))

def calc_top_x(BW_percent):
    
    IFs = []
    BWs = []
    
    for i in range(len(BW_percent)):
        IFs.append(BW_percent[i][0])
        BWs.append(BW_percent[i][1])
    
    sorted_BWs = sorted(BWs, reverse = True)
    sorted_IFs = []
    
    for i in range(len(sorted_BWs)):
        indx = BWs.index(sorted_BWs[i])
        sorted_IFs.append(IFs[indx])

    return [sorted_IFs, sorted_BWs]


# top_x structure explained
# top_x = [channel1, channel2, channel3, channel4]
# channelx = [sorted IFs, sorted BWs]
# sorted IFs/BWs = [a,b,c,d,e,f...]
top_x = []

for spur_band in spurs_let_through:
    BW_percent = []
    for f_IF in good:
        bw = 1000000000
        f_LO = calc_LO(f_RF, f_IF)
            
        for RF in spur_band:
            spurs = calc_spurs(RF, f_LO)
                
            for spur in spurs:
                percentage = calc_percentage_BW(spur, f_IF)
                    
                if percentage < bw:
                    bw = percentage # So if a better %BW is found for an IF, 
                                        # update the variable

        BW_percent.append([f_IF, bw])
    
    top_x_each_band = calc_top_x(BW_percent)
    top_x.append(top_x_each_band)

IFs = []
BWs = []

for i in range(len(top_x[0][0])):
    
    IF_to_compare = top_x[0][0][i]  # Take an IF from the first band
    
    bw1 = top_x[0][1][i]
    bw2 = top_x[1][1][top_x[1][0].index(IF_to_compare)]
    
    bw_compare_list = [bw1, bw2]
    
    if min(bw_compare_list) == bw1:
        IFs.append(IF_to_compare)
        BWs.append(bw1)
    
    elif min(bw_compare_list) == bw2:
        IFs.append(top_x[1][0][top_x[1][1].index(bw2)])
        BWs.append(bw2)
        

sorted_BWs = sorted(BWs, reverse = True)
sorted_IFs = []
        
for i in range(len(BWs)):
    indx = BWs.index(sorted_BWs[i])
    sorted_IFs.append(IFs[indx])

print()
print('Top 5 IFs')
print('1:', str(sorted_IFs[0]/1e6), 'MHz, %BW:', str(sorted_BWs[0]))
print('2:', str(sorted_IFs[1]/1e6), 'MHz, %BW:', str(sorted_BWs[1]))
print('3:', str(sorted_IFs[2]/1e6), 'MHz, %BW:', str(sorted_BWs[2]))
print('4:', str(sorted_IFs[3]/1e6), 'MHz, %BW:', str(sorted_BWs[3]))
print('5:', str(sorted_IFs[4]/1e6), 'MHz, %BW:', str(sorted_BWs[4]))


print()
print(all_spurs)