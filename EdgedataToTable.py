import sys
import pandas as pd
import matplotlib.pyplot as plt
from pylab import *
import math

pathR= "R\outputs\\"
#'/home/moises/Sumo/2024-02-01-14-19-59-2/Exp/R/outputs/'
pathO= "O\outputs\\"
#'/home/moises/Sumo/2024-02-01-14-19-59-2/Exp/O/outputs/'
  
def detectors_out_to_table(sim_data_df, field_name):
    # parse all the intervals in the edgedata file 
    time_intervals = sim_data_df['interval_id'].unique()
    data_dict = {}
    for time_interval in time_intervals:
        # get the DF related to time_interval
        data_interval = sim_data_df.loc[sim_data_df['interval_id'] == time_interval]
        # get the IDs of the edges that has an edgedata output value in the current time interval
        list_edges = data_interval['edge_id'].unique()
        for edge_id in list_edges:
            # get the data for all the edges
            data = data_interval.loc[data_interval['edge_id'] == edge_id][field_name]
            if time_interval not in data_dict:
                data_dict[time_interval] = {}
            data_dict[time_interval][edge_id] = data.item()

    return pd.DataFrame.from_dict(data_dict)

def plots_hist(dO, dfO, dfR, arg):
    time_intervals = dO['interval_id'].unique()
    #
    #rang_max= dfR.max()
    #print(round(rang_max))
    idx = 1
    num = len(time_intervals)
    fig, ax = plt.subplots(figsize=(10, 20), nrows=2, ncols=1, sharex=True, sharey=True)
    for name in time_intervals:
        subplot(num,1,idx)
        ax = plt.hist([dfO[name],dfR[name]], bins= 10, label=['open', 'rerouting'])#, range=[0,rang_max])
        plt.title(name)
        plt.xlabel("Values")
        plt.ylabel("Frequency")
        plt.legend(loc='upper right')
        plt.margins(x=0.02, tight=True)
        ax = plt.gca()
        idx += 1
        #plt.xlim(0,40)
        #plt.ylim(0, 110)
        #mode_index = ax.argmax()
        #print(mode_index)
    plt.suptitle('Comparing timeframes in term of ' + arg + ', closing and nonclosing edges', fontsize=16, y=1)
    plt.tight_layout()
    fig.savefig('histogram_'+arg+'.pdf', bbox_inches='tight')



if __name__ == '__main__':
    arg = sys.argv[1]
    # this is obtained by converting the xml edgedata file to CSV
    # using xml2csv tool (included in SUMO)
    edgedata_csv_file_O = pathO+"0_to_3600.out.csv"
    edgedata_csv_file_R = pathR+"0_to_3600.out.csv"
    dO = pd.read_csv(edgedata_csv_file_O, sep=";")
    dR = pd.read_csv(edgedata_csv_file_R, sep=";")
    dfO = detectors_out_to_table(dO, arg)
    dfR = detectors_out_to_table(dR, arg)
    df = dfR - dfO
    plots_hist(dO, dfO, dfR, arg)
    df.to_csv('OUTPUT.csv', sep=";", na_rep='0')
