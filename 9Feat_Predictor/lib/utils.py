import csv
import json
import os
import pickle
import locale
import xlrd
import math
import pywt
import numpy as np
from scipy.stats import kurtosis, skew

def ensure_path(path):
    directory = os.path.dirname(path)
    if len(directory) > 0 and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    return path

def extract_rms(window, index):
    sum_of_squares = 0

    for i in range(len(window)):
        sum_of_squares += math.pow(float(window[i][index]), 2.0)

    return math.sqrt(sum_of_squares / len(window))

def extract_std(window, index):
    li = []
    for i in range(len(window)):
        li.append(float(window[i][index]))

    return np.std(li, ddof=1)
    
def extract_std_welford(window, index):
    mean = 0
    sum = 0

    for i in range(len(window)):
        x = float(window[i][index])
        old_mean = mean
        mean = mean + (x-mean)/(i+1)
        sum = sum + (x-mean)*(x-old_mean)

    return math.sqrt(sum/(len(window) - 1))


def extract_fi_one_side(window, left_acc_ind_first, lb_low_hz, lb_high_hz, fb_low_hz, fb_high_hz):
    left_accx = []
    left_accy = []
    left_accz = []
    
    bin_width = 50.0 / len(window)
    lb_low = int(lb_low_hz / bin_width)
    lb_high = int(lb_high_hz / bin_width)
    fb_low = int(fb_low_hz / bin_width)
    fb_high = int(fb_high_hz / bin_width)

    for x in range(len(window)):
        sample = window[x]

        left_accx.append(float(sample[left_acc_ind_first]))
        left_accy.append(float(sample[left_acc_ind_first+1]))
        left_accz.append(float(sample[left_acc_ind_first+2]))

    left_accx_fft = list(map(abs, np.fft.fft(left_accx)[lb_low:fb_high+1]))
    left_accy_fft = list(map(abs, np.fft.fft(left_accy)[lb_low:fb_high+1]))
    left_accz_fft = list(map(abs, np.fft.fft(left_accz)[lb_low:fb_high+1]))

    left_accx_power = list(map(lambda y: pow(y, 2.0), left_accx_fft))
    left_accy_power = list(map(lambda y: pow(y, 2.0), left_accy_fft))
    left_accz_power = list(map(lambda y: pow(y, 2.0), left_accz_fft))

    lb_power_left = sum(left_accx_power[lb_low-1:lb_high]) + sum(left_accy_power[lb_low-1:lb_high]) + sum(left_accz_power[lb_low-1:lb_high])
    fb_power_left = sum(left_accx_power[fb_low-1:fb_high]) + sum(left_accy_power[fb_low-1:fb_high]) + sum(left_accz_power[fb_low-1:fb_high])

    
    return fb_power_left / lb_power_left

def extract_lb_fb_one_side(window, left_acc_ind_first, lb_low_hz, lb_high_hz, fb_low_hz, fb_high_hz):
    left_accx = []
    left_accy = []
    left_accz = []
    
    bin_width = 50.0 / len(window)
    lb_low = int(lb_low_hz / bin_width)
    lb_high = int(lb_high_hz / bin_width)
    fb_low = int(fb_low_hz / bin_width)
    fb_high = int(fb_high_hz / bin_width)

    for x in range(len(window)):
        sample = window[x]

        left_accx.append(float(sample[left_acc_ind_first]))
        #left_accy.append(float(sample[left_acc_ind_first+1]))
        left_accz.append(float(sample[left_acc_ind_first+2]))

    left_accx_fft = list(map(abs, np.fft.fft(left_accx)[lb_low:fb_high+1]))
    #left_accy_fft = list(map(abs, np.fft.fft(left_accy)[lb_low:fb_high+1]))
    left_accz_fft = list(map(abs, np.fft.fft(left_accz)[lb_low:fb_high+1]))

    left_accx_power = list(map(lambda y: pow(y, 2.0), left_accx_fft))
    #left_accy_power = list(map(lambda y: pow(y, 2.0), left_accy_fft))
    left_accz_power = list(map(lambda y: pow(y, 2.0), left_accz_fft))

    #lb_power_left = sum(left_accx_power[lb_low-1:lb_high]) + sum(left_accy_power[lb_low-1:lb_high]) + sum(left_accz_power[lb_low-1:lb_high])
    #fb_power_left = sum(left_accx_power[fb_low-1:fb_high]) + sum(left_accy_power[fb_low-1:fb_high]) + sum(left_accz_power[fb_low-1:fb_high])

    lb_power_left = sum(left_accz_power[lb_low-1:lb_high])
    fb_power_left = sum(left_accx_power[fb_low-1:fb_high])

    return (lb_power_left, fb_power_left)

#====================== New Feature Functions ======================

def extract_min_max(window):

    min = max = None

    for val in window:
        if min is None or val < min: 
            min = val
        if max is None or val > max:
            max = val

    return min, max

def extract_w_freq(WX, WY, WZ):
    
    # Getting Constants
    bin_width = 50.0 / len(WX)
    lb_low = int( 0.5 / bin_width)
    lb_high = int( 3 / bin_width)
    fb_low = int( 3 / bin_width)
    fb_high = int( 8 / bin_width)

    # Getting FFT Transform
    accx_fft = list(map(abs, np.fft.fft(WX)[lb_low:fb_high+1]))
    accy_fft = list(map(abs, np.fft.fft(WY)[lb_low:fb_high+1]))
    accz_fft = list(map(abs, np.fft.fft(WZ)[lb_low:fb_high+1]))
    # Getting Frequency Band Power
    accx_power = list(map(lambda y: pow(y, 2.0), accx_fft))
    accy_power = list(map(lambda y: pow(y, 2.0), accy_fft))
    accz_power = list(map(lambda y: pow(y, 2.0), accz_fft))

    wx_lb = sum(accx_power[lb_low-1:lb_high])
    wy_lb = sum(accy_power[lb_low-1:lb_high])
    wz_lb = sum(accz_power[lb_low-1:lb_high])

    lb_power = wx_lb + wy_lb + wz_lb
    fb_power = sum(accx_power[fb_low-1:fb_high]) + sum(accy_power[fb_low-1:fb_high]) + sum(accz_power[fb_low-1:fb_high])

    fi = fb_power / lb_power

    return (fi, wx_lb, wy_lb, wz_lb)

def extract_a_freq(AX, AY, AZ):
    
    # Getting Constants
    bin_width = 50.0 / len(AX)
    lb_low = int( 0.5 / bin_width)
    lb_high = int( 3 / bin_width)
    fb_low = int( 3 / bin_width)
    fb_high = int( 8 / bin_width)

    # Getting FFT Transform
    accx_fft = list(map(abs, np.fft.fft(AX)[lb_low:fb_high+1]))
    accy_fft = list(map(abs, np.fft.fft(AY)[lb_low:fb_high+1]))
    accz_fft = list(map(abs, np.fft.fft(AZ)[lb_low:fb_high+1]))
    # Getting Frequency Band Power
    accx_power = list(map(lambda y: pow(y, 2.0), accx_fft))
    accy_power = list(map(lambda y: pow(y, 2.0), accy_fft))
    accz_power = list(map(lambda y: pow(y, 2.0), accz_fft))

    lb_power = sum(accx_power[lb_low-1:lb_high]) + sum(accy_power[lb_low-1:lb_high]) + sum(accz_power[lb_low-1:lb_high])
    fb_power = sum(accx_power[fb_low-1:fb_high]) + sum(accy_power[fb_low-1:fb_high]) + sum(accz_power[fb_low-1:fb_high])

    a_fi = fb_power / lb_power

    return a_fi

def extract_dwtfeat(wy, ay, az):

    cA, cD = pywt.dwt(wy, 'db1')
    wy_cA_var = np.var(cA)
    wy_var = np.var(wy)

    cA, cD = pywt.dwt(ay, 'db1')
    ay_cA_mean = np.mean(cA)

    cA, cD = pywt.dwt(az, 'db1')
    az_cD_Kurt = kurtosis(cD)

    return wy_cA_var, wy_var, ay_cA_mean, az_cD_Kurt


def extract_sepfeat(window):

    pred_feat = [] 
    dect_feat = [] 

    lax = []; lay = []; laz = []
    lwx = []; lwy = []; lwz = []

    rax = []; ray = []; raz = []
    rwx = []; rwy = []; rwz = []

    for i in range(len(window)):
        lwx.append(window[i][0])
        lwy.append(window[i][1])
        lwz.append(window[i][2])
        lax.append(window[i][3])
        lay.append(window[i][4])
        laz.append(window[i][5])

        rwx.append(window[i][6])
        rwy.append(window[i][7])
        rwz.append(window[i][8])
        rax.append(window[i][9])
        ray.append(window[i][10])
        raz.append(window[i][11])


    #Extracting FoG Prediction Features
    #Left Leg
    #lwy_min, lwy_max = extract_min_max(lwy)
    lax_min, lax_max = extract_min_max(lax)
    lay_min, lay_max = extract_min_max(lay)
    laz_min, laz_max = extract_min_max(laz)

    pred_feat.append(laz_min)
    pred_feat.append(laz_max)
    pred_feat.append(lax_min)
    pred_feat.append(np.max(lwx))
    pred_feat.append(np.max(lwy))
    pred_feat.append(lay_max)
    pred_feat.append(np.median(lay))
    pred_feat.append(lax_max) 
    pred_feat.append(lay_min) 
    #pred_feat.append(lwy_min) 

    #Right Leg
    #rwy_min, rwy_max = extract_min_max(rwy)
    rax_min, rax_max = extract_min_max(rax)
    ray_min, ray_max = extract_min_max(ray)
    raz_min, raz_max = extract_min_max(raz)

    pred_feat.append(raz_min)
    pred_feat.append(raz_max)
    pred_feat.append(rax_min)
    pred_feat.append(np.max(rwx))
    pred_feat.append(np.max(rwy))
    pred_feat.append(ray_max)
    pred_feat.append(np.median(ray))
    pred_feat.append(rax_max) 
    pred_feat.append(ray_min) 
    #pred_feat.append(rwy_min) 
    
    #Extracting FoG Detetion Features
    #Left_Leg
    w_fi, wx_lb, wy_lb, wz_lb = extract_w_freq(lwx,lwy,lwz)
    wy_cA_var, wy_var, ay_cA_mean, az_cD_Kurt = extract_dwtfeat(lwy, lay, laz)
    a_fi = extract_a_freq(lax,lay,laz)
    dect_feat.append(wy_lb)
    dect_feat.append(w_fi)
    dect_feat.append(wy_cA_var)
    dect_feat.append(wz_lb)
    dect_feat.append(a_fi)
    dect_feat.append(wy_var)
    dect_feat.append(ay_cA_mean)
    dect_feat.append(az_cD_Kurt)
    dect_feat.append(wx_lb)
    #dect_feat.append(ax_lb)
    
    #Right_leg
    w_fi, wx_lb, wy_lb, wz_lb = extract_w_freq(rwx,rwy,rwz)
    wy_cA_var, wy_var, ay_cA_mean, az_cD_Kurt = extract_dwtfeat(rwy, ray, raz)
    a_fi= extract_a_freq(rax,ray,raz)
    dect_feat.append(wy_lb)
    dect_feat.append(w_fi)
    dect_feat.append(wy_cA_var)
    dect_feat.append(wz_lb)
    dect_feat.append(a_fi)
    dect_feat.append(wy_var)
    dect_feat.append(ay_cA_mean)
    dect_feat.append(az_cD_Kurt)
    dect_feat.append(wx_lb)
    #dect_feat.append(ax_lb)


    return pred_feat, dect_feat