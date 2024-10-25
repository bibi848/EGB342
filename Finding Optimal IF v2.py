# -*- coding: utf-8 -*-
"""
Created on Wed Oct 23 10:20:11 2024

@author: oscar
"""

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

def desc_overlap(li, spurs):
    
    if li[0]:
        print('Yes there is an overlap:')
        print('Overlap:', spurs[li[1]]/1e9,'GHz')
        
        if li[1] < 2:
            print('First Order Spur')
        elif li[1] > 1 and li[1] < 5:
            print('Second Order Spur')
        else:
            print('Third Order Spur')
        
    else:
        print('No there is no overlap')

import math
def round_to_sf(number, sig_figs):
    if number == 0:
        return 0
    else:
        return round(number, sig_figs - int(math.floor(math.log10(abs(number)))) - 1)


# Setting up the channels

freq = 3.005e9
channels = [freq]

while freq < 4.995e9:
    freq += 5e6
    channels.append(freq)

# IF Domain
freq = 1e9
f_IF_list = [freq]

while freq < 3e9:
    freq += 3.5e6
    f_IF_list.append(freq)

filter_bands = [channels[:242],channels[162:]]

print()
print('First Filter Band: ' + str(filter_bands[0][0]/1e9) + ' to ' + str(filter_bands[0][-1]/1e9) + ' GHz')
print('Second Filter Band: ' + str(filter_bands[1][0]/1e9) + ' to ' + str(filter_bands[1][-1]/1e9) + ' GHz')

f_RF_list = filter_bands[0]
good = []

# Initial selection of IF frequencies in the first band
for f_IF in f_IF_list:
    found = False
    
    for desired_channel in f_RF_list:
        f_LO = calc_LO(desired_channel, f_IF)
    
        for f_RF in f_RF_list:
            if f_RF != desired_channel:
                spurs = calc_spurs(f_RF, f_LO)
                overlap = find_overlap(f_IF, spurs)
            
                if overlap[0]:
                    found = True
                    break
        if found:
            break
    
    if found == False:
        good.append(f_IF)

# print(good)
print(str(len(good)) + '/' + str(len(f_IF_list)) + ' passed')
print()


# Now test the 'good' IF frequencies when used on the other 3 bands

for f_RF_list in filter_bands[1:]:
    to_remove = []
    for f_IF in good:
        found = False
        
        for desired_channel in f_RF_list:
            f_LO = calc_LO(desired_channel, f_IF)
            
            for f_RF in f_RF_list:
                
                if f_RF != desired_channel:
                    spurs = calc_spurs(f_RF, f_LO)
                    overlap = find_overlap(f_IF, spurs)
                    
                    if overlap[0]:
                        found = True
                        to_remove.append(f_IF)
                        break
            if found:
                break
    
    for f_IF in to_remove:
        good.remove(f_IF)
    
    # print(good)
    print(str(len(good)) + '/' + str(len(f_IF_list)) + ' passed')
    print()

        

print()
print('Therefore valid IF Frequencies are:')
print(good)


# # Test whether found IFs are actually valid
print()
overlapps = []

for f_RF_list in filter_bands:
    
    for f_IF in good:
        found = False
        
        for desired_channel in f_RF_list:
            f_LO = calc_LO(desired_channel, f_IF)
            
            for f_RF in f_RF_list:
                if f_RF != desired_channel:
                    spurs = calc_spurs(f_RF, f_LO)
                    overlap = find_overlap(f_IF, spurs)
                    
                    if overlap[0]:
                        found = True
                        desc_overlap(overlap, spurs)
                        if f_IF not in overlapps:
                            overlapps.append(f_IF)
                        break
                    
                if found:
                    break
    
print('test done')
print()


# Finding the IF frequency which can have the highest %bandwidth
# For this, only need to find the closest spur to each IF frequency, and then 
# multiply the difference by 2 to find the %BW

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

# Top 5 for each of the channel bands - highest common factor wins
top_x = []

for i in range(len(filter_bands)):
    f_RF_list = filter_bands[i]
    print('Checking', str(i+1), 'band')
    print()
    
    BW_percent = []
    
    for f_IF in good:
        bw = 1000000000
        
        for desired_channel in f_RF_list:
            f_LO = calc_LO(desired_channel, f_IF)
            
            for f_RF in f_RF_list:
                if f_RF != desired_channel:
                    spurs = calc_spurs(f_RF, f_LO)
                    
                    for spur in spurs:
                        percentage = calc_percentage_BW(spur, f_IF)
                        
                        if percentage < bw:
                            bw = percentage # So if a better %BW is found for an IF, 
                                            # update the variable

        BW_percent.append([f_IF, bw])
    
    top_x_each_band = calc_top_x(BW_percent)
    top_x.append(top_x_each_band)


# top_x structure explained
# top_x = [channel1, channel2, channel3, channel4]
# channelx = [sorted IFs, sorted BWs]
# sorted IFs/BWs = [a,b,c,d,e,f...]

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
    
print('Top 5 IFs')
print('1:', str(sorted_IFs[0]/1e9), 'GHz, %BW:', str(sorted_BWs[0]))
print('2:', str(sorted_IFs[1]/1e9), 'GHz, %BW:', str(sorted_BWs[1]))
print('3:', str(sorted_IFs[2]/1e9), 'GHz, %BW:', str(sorted_BWs[2]))
print('4:', str(sorted_IFs[3]/1e9), 'GHz, %BW:', str(sorted_BWs[3]))
print('5:', str(sorted_IFs[4]/1e9), 'GHz, %BW:', str(sorted_BWs[4]))