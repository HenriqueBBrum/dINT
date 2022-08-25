import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
import math
import csv
import argparse
import os
import numpy as np
from collections import OrderedDict
import glob


metric_unit = {'b': 1, 'k':1000, 'm':1000000, 'g':1000000000}


def add_value_labels(ax, spacing=4, y_spacing=0, color='gray'):
    # For each bar: Place a label
    for rect in ax.patches:
        # Get X and Y placement of label from rect.
        y_value = rect.get_height()
        x_value = rect.get_x() + rect.get_width() / 2

        # Number of points between bar and label. Change to your liking.
        space = spacing
        # Vertical alignment for positive values
        va = 'bottom'

        # If value of bar is negative: Place label below bar
        if y_value < 0:
            # Invert space to place label below
            space *= -1
            # Vertically align label at top
            va = 'top'

        # Use Y value as label and format number with one decimal place
        label = "{:.1f}".format(y_value)

        # Create annotation
        ax.annotate(
            label,                      # Use `label` as label
            (x_value, y_value),         # Place label at end of the bar
            xytext=(y_spacing, space),          # Vertically shift label by `space`
            textcoords="offset points", # Interpret `xytext` as offset in points
            ha='center',                # Horizontally center label
            va=va,
            color=color)                      # Vertically align label differently for
                                        # positive and negative values.

# pos = postion in data to be used, mult is the scale factor
def crete_bar_graph_rects(data, pos, mult):
    sw_type_count = {}
    rects = {}
    labels = []
    for k, v in data.items():
        sw_type, push_time = k.split('_')

        if sw_type not in sw_type_count:
            sw_type_count[sw_type] = 1

        labels.append(push_time)
        if sw_type not in rects:
            rects[sw_type] = [(v[pos]/v[0])*mult]
        else:
            rects[sw_type].append((v[pos]/v[0])*mult)
            sw_type_count[sw_type] = sw_type_count[sw_type]+1

    return labels, rects, sw_type_count


def plot_bar_graph(filepath, title, ylabel, color, ticks_freq, labels, rects, sw_type_count):
    fig, ax = plt.subplots()
    labels = list(dict.fromkeys(labels))

    sw_type_count_x_map = {}
    for k, v in sw_type_count.items():
        sw_type_count_x_map[k] = np.arange(1 if v == 0 else v)

    width=0.20
    ct = 0
    multi = -1
    pos = 0
    print(rects.items)
    for k, v in rects.items():
        x = sw_type_count_x_map[k]
        r = ax.bar(x-width*multi*pos, v, width, label=k.capitalize(), hatch='\\', align='edge')
       
        if ct%2 == 0:
            pos = pos +1
        else:
            multi = multi*-1

        ct = ct +1


    add_value_labels(ax, y_spacing=-2, color='orange')

    ax.set_title(title)
    ax.set_ylabel(ylabel)
    

    max_ = 0
    for rect in rects.values():
        local_max = max(rect)
        if(local_max > max_): max_ = local_max
    
    ax.set_ylim([0, max_+0.5*max_])
    start, end = ax.get_ylim()
    ax.yaxis.set_ticks(np.arange(start, end, ticks_freq))

    ax.set_xticklabels(labels)
    ax.set_xticks(x)
    ax.set_xlabel('Telemetry push time (s)')

    h1, l1 = ax.get_legend_handles_labels()
    ax.legend(h1, l1, loc='upper center')

    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    fig.savefig(filepath)

# Review error with unit change. Problem is probably an excess of ticks or labels
def plot_graphs(output_folder, traffic_type, sw_id, total_time, data, unit):
    if len(data) <= 0:
        return

    rmse_title = 'Measurement Error - '+'SW'+sw_id+' | '+total_time+'s'
    rmse_filepath = output_folder+traffic_type+'_RMSE_'+sw_id+'_'+total_time.split('.')[0]+'s.png'
    plot_bar_graph(rmse_filepath, rmse_title, 'RMSE (%)', 'tab:orange', 5, *crete_bar_graph_rects(data, 1, 100))


    byte_cnt_title = 'Telemetry Overhead - '+'SW'+sw_id+' | '+total_time+'s'
    byte_cnt_filepath = output_folder+traffic_type+'s_Tel_Overhead_'+sw_id+'_'+total_time.split('.')[0]+'s.png'
    plot_bar_graph(byte_cnt_filepath, byte_cnt_title, 'Bytes ('+unit.upper()+')', 'tab:green', 200, *crete_bar_graph_rects(data, 2, metric_unit[unit]))

  


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--file_folder', type=str, help="Folder with input files", required=True)
    parser.add_argument('-g', '--graphs_output_folder', type=str, help="Folder for output files", required=True)
    parser.add_argument('-u', '--unit', type=str, help = "Metric Unit (b, k, m, g)", required=False, default="b")


    return vars(parser.parse_args())

def main():
    args = parse_args()

    rmse_and_byte_cnt_files = glob.glob(args['file_folder']+"*.csv")
    for f in rmse_and_byte_cnt_files:
        traffic_type = f.split("/")[-1].split(".")[0]

        my_dict = OrderedDict()
        graph_dict = OrderedDict()

        with open(f) as csvfile:
            data = csv.DictReader(csvfile, delimiter=',')
            for row in data:
                f_key = row['sw_id']+"_"+row['experiment_time']
                s_key = row['sw_type']+"_"+row['min_telemetry_push_time']
                if (f_key+s_key) in my_dict:
                    count, previous_rmse, previous_byte_count, previous_experiment_time = my_dict[(f_key+s_key)]
                    updated_value = (float(count+1), previous_rmse+float(row['rmse']), previous_byte_count+float(row['telemetry_byte_count']),
                                previous_experiment_time+float(row['experiment_time']))

                    my_dict[(f_key+s_key)] = updated_value
                    graph_dict[f_key][s_key] = updated_value
                else:
                    value = (1, float(row['rmse']), float(row['telemetry_byte_count']), float(row['experiment_time']))
                    my_dict[(f_key+s_key)] = value
                    if f_key not in graph_dict:
                        graph_dict[f_key] = {}
                        graph_dict[f_key][s_key] = value
                    else:
                        graph_dict[f_key][s_key] = value

       
        final_dict = OrderedDict()
        for k, v in graph_dict.items():
            print(k, v)
            sw_id, total_time = k.split('_')
            plot_graphs(args['graphs_output_folder'], traffic_type, sw_id, total_time, v, args['unit'])
           


if __name__ == '__main__':
    main()
