import csv
import json
import os
import pickle
import locale
import xlrd
import math
import numpy as np

def load_from_pickle(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def save_to_pickle(data, path):
    with open(ensure_path(path), "wb") as f:
        pickle.dump(data, f)


def load_json(input_path):
    with open(input_path, "r") as f:
        return json.load(f)


def save_list_as_text(data, output_path):
    output_path = ensure_path(output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        for word in data:
            f.write("{}\n".format(word))


def load_text_as_list(input_path):
    with open(input_path, 'r', encoding="utf-8") as f:
        return f.read().splitlines()


def ensure_path(path):
    directory = os.path.dirname(path)
    if len(directory) > 0 and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    return path


def write_csv(content, header, path, delimiter=","):
    path = ensure_path(path)
    with open(path, 'w', encoding="utf-8", newline='') as f:
        csv_writer = csv.writer(f, delimiter=delimiter, quotechar='"', quoting=csv.QUOTE_MINIMAL)
        if header is not None:
            csv_writer.writerow(header)

        for row in content:
            csv_writer.writerow(row)


def read_csv(path, load_header=False, delimiter=","):
    content = []
    # try:
    with open(path, "r", encoding="utf-8") as f:
        csv_reader = csv.reader(f, delimiter=delimiter, quotechar='"')
        if load_header:
            for row in csv_reader:
                content.append(row)
            # [content.append(row) for row in csv_reader]
        else:
            [content.append(row) for i, row in enumerate(csv_reader) if i > 0]
    # except Exception as e:
    #     print(e)
    return content


def convert_to_xls(file_to_rename):
    pre, ext = os.path.splitext(file_to_rename)
    os.rename(file_to_rename, pre + ".xls")

def csv_from_excel(file_to_convert):
    pre, ext = os.path.splitext(file_to_convert)
    wb = xlrd.open_workbook(file_to_convert)
    sh = wb.sheet_by_name('Sheet1')
    your_csv_file = open(pre + '.csv', 'w', newline='')
    wr = csv.writer(your_csv_file, quoting=csv.QUOTE_ALL)

    for rownum in range(sh.nrows):
        wr.writerow(sh.row_values(rownum))

    your_csv_file.close()


def extract_avg_label(window, index):
    labels = []

    for i in range(len(window)):
        labels.append(int(float(window[i][index])))

    return np.average(labels)


def extract_rms(window, index):
    sum_of_squares = 0

    for i in range(len(window)):
        sum_of_squares += math.pow(float(window[i][index]), 2.0)

    return math.sqrt(sum_of_squares / len(window))


def extract_rms_np(window, index):
    li = []
    for i in range(len(window)):
        li.append(float(window[i][index]))

    return np.sqrt(np.mean(np.array(li)**2))


def extract_std(window, index):
    li = []
    for i in range(len(window)):
        li.append(float(window[i][index]))

    return np.std(li, ddof=1)


def extract_std_v2(window, index):
    window = np.array(window).astype(float)
    std_li = np.std(np.array(window), axis=0, ddof=1)

    return std_li[index]

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

    for x in range(len(window)):
        sample = window[x]

        left_accx.append(float(sample[left_acc_ind_first]))
        left_accy.append(float(sample[left_acc_ind_first+1]))
        left_accz.append(float(sample[left_acc_ind_first+2]))

    left_accx_fft = list(map(abs, np.fft.fft(left_accx)))
    left_accy_fft = list(map(abs, np.fft.fft(left_accy)))
    left_accz_fft = list(map(abs, np.fft.fft(left_accz)))

    left_accx_power = list(map(lambda y: pow(y, 2.0), left_accx_fft))
    left_accy_power = list(map(lambda y: pow(y, 2.0), left_accy_fft))
    left_accz_power = list(map(lambda y: pow(y, 2.0), left_accz_fft))

    left_window = []

    for x in range(len(window)):
        left_window.append(left_accx_power[x] + left_accy_power[x] + left_accz_power[x])

    bin_width = 50.0 / len(window)
    lb_low = int(lb_low_hz / bin_width)
    lb_high = int(lb_high_hz / bin_width)
    fb_low = int(fb_low_hz / bin_width)
    fb_high = int(fb_high_hz / bin_width)

    lb_power_left = 0
    fb_power_left = 0

    for x in range(lb_low, lb_high+1):
        lb_power_left += left_window[x]
    for x in range(fb_low, fb_high+1):
        fb_power_left += left_window[x]

    return fb_power_left / lb_power_left


def extract_fi(window, left_acc_ind_first, right_acc_ind_first, lb_low_hz, lb_high_hz, fb_low_hz, fb_high_hz):
    left_accx = []
    left_accy = []
    left_accz = []
    right_accx = []
    right_accy = []
    right_accz = []

    for x in range(len(window)):
        sample = window[x]

        left_accx.append(float(sample[left_acc_ind_first]))
        left_accy.append(float(sample[left_acc_ind_first+1]))
        left_accz.append(float(sample[left_acc_ind_first+2]))
        right_accx.append(float(sample[right_acc_ind_first]))
        right_accy.append(float(sample[right_acc_ind_first+1]))
        right_accz.append(float(sample[right_acc_ind_first+2]))

    left_accx_fft = list(map(abs, np.fft.fft(left_accx)))
    left_accy_fft = list(map(abs, np.fft.fft(left_accy)))
    left_accz_fft = list(map(abs, np.fft.fft(left_accz)))
    right_accx_fft = list(map(abs, np.fft.fft(right_accx)))
    right_accy_fft = list(map(abs, np.fft.fft(right_accy)))
    right_accz_fft = list(map(abs, np.fft.fft(right_accz)))

    left_accx_power = list(map(lambda y: pow(y, 2.0), left_accx_fft))
    left_accy_power = list(map(lambda y: pow(y, 2.0), left_accy_fft))
    left_accz_power = list(map(lambda y: pow(y, 2.0), left_accz_fft))
    right_accx_power = list(map(lambda y: pow(y, 2.0), right_accx_fft))
    right_accy_power = list(map(lambda y: pow(y, 2.0), right_accy_fft))
    right_accz_power = list(map(lambda y: pow(y, 2.0), right_accz_fft))

    left_window = []
    right_window = []

    for x in range(len(window)):
        left_window.append(left_accx_power[x] + left_accy_power[x] + left_accz_power[x])
        right_window.append(right_accx_power[x] + right_accy_power[x] + right_accz_power[x])

    bin_width = 50.0 / len(window)
    lb_low = int(lb_low_hz / bin_width)
    lb_high = int(lb_high_hz / bin_width)
    fb_low = int(fb_low_hz / bin_width)
    fb_high = int(fb_high_hz / bin_width)

    lb_power_left = 0
    fb_power_left = 0
    lb_power_right = 0
    fb_power_right = 0
    for x in range(lb_low, lb_high+1):
        lb_power_left += left_window[x]
        lb_power_right += right_window[x]
    for x in range(fb_low, fb_high+1):
        fb_power_left += left_window[x]
        fb_power_right += right_window[x]

    return ((fb_power_right / lb_power_right) + (fb_power_left / lb_power_left)) / 2.0


def check_accuracy(predicted_labels, actual_labels):
    score = 0
    for i in range(len(predicted_labels)):
        if predicted_labels[i] == actual_labels[i]:
            score += 1

    return float(score / len(predicted_labels))
