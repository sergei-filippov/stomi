import json
import os
import pingparsing
import matplotlib.pyplot as plt
import numpy as np

frame_sizes=['64', '128', '256', '512', '1024', '1280', '1518']   

end_data = {'Mbytes':[],
            'Mbps':[],
            'Jitter':[],
            'Lost_packets':[],
            'Packets':[],
            'Lost_percent':[],
}

def run_iperf3(ip_address, result_folder, duration, throughput):
    os.system('mkdir -p ' + result_folder + '/json_files')
    os.system('mkdir -p ' + result_folder + '/plot_files/end_data')
    for frame_size in frame_sizes:
        json_file_address = result_folder+'/json_files/frame_size_'+frame_size+'.json'
        os.system('iperf3 -c ' + ip_address +' -u -b ' + str(throughput) + 'M -t ' + str(duration) + ' -l '+ frame_size + ' -J --logfile ' + json_file_address)
        plot_folder = result_folder + '/plot_files/frame_size_'+frame_size
        os.system('mkdir ' + plot_folder)
        parse_iperf3(json_file_address, plot_folder+'/', frame_size, throughput)  # reads JSONs and plot the results for each frame size
    for key,item in end_data.items():
        plot_per_test(key, item, result_folder, throughput, duration)  # plots bar-chart with final data of the test


def detect_throughput(ip_address, throughput_threshold, result_folder, start_bandwidth, bandwidth_step):
    lost_percent = []
    bandwidth_array = []
    os.system('mkdir -p ' + result_folder + '/throughput/json_files')
    bandwidth = start_bandwidth
    while(True):
        bandwidth_array.append(bandwidth)
        json_file_address = result_folder + '/throughput/json_files/target_bandwidth_' + str(bandwidth) + '.json'
        os.system('iperf3 -c ' + str(ip_address) +' -u -b ' + str(bandwidth)+'M -t 10 -J --logfile ' + json_file_address)
        with open(json_file_address) as file:
            iperf_dict = json.load(file)
        lost_percent.append(iperf_dict['end']['sum']['lost_percent'])  # saves new data in the array
        if(iperf_dict['end']['sum']['lost_percent']) < throughput_threshold:  # if the value is below threshold, connection is considered lossless
            break
        else:
            bandwidth = bandwidth - bandwidth_step  # deacrease test bandwidth
            if bandwidth == 0:
                break

    ypoints = lost_percent
    xpoints = bandwidth_array

    plt.title("Lossless bandwidth detection")
    plt.xlabel('Mbit/s')  
    plt.ylabel("Lost packets %") 
    plt.plot(xpoints ,ypoints)
    plt.savefig(result_folder + "/throughput/throughput.png", format="png", bbox_inches="tight")
    plt.close()
    return bandwidth


def parse_iperf3(json_file_address, plot_folder, frame_size, throughput):
    Mbytes_num = []
    Mbits_per_second = []
    packets = []
    with open(json_file_address) as file:
        iperf_dict = json.load(file)
        intervals = iperf_dict['intervals']
        for interval in intervals:
            streams = interval['streams']
            for stream in streams:
                Mbytes_num.append(stream['bytes'] / 1000 / 1000)  #into MB
                Mbits_per_second.append(stream['bits_per_second'] / 1000 / 1000)   #into Mbit/s
                packets.append(stream['packets'])
        file.close() 

    end_data['Mbytes'].append(iperf_dict['end']['sum']['bytes'])
    end_data['Mbps'].append(iperf_dict['end']['sum']['bits_per_second'])
    end_data['Jitter'].append(iperf_dict['end']['sum']['jitter_ms'])
    end_data['Lost_packets'].append(iperf_dict['end']['sum']['lost_packets'])
    end_data['Packets'].append(iperf_dict['end']['sum']['packets'])
    end_data['Lost_percent'].append(iperf_dict['end']['sum']['lost_percent'])

    plot_per_frame_size(Mbytes_num, plot_folder, "MBytes", frame_size, throughput)
    plot_per_frame_size(Mbits_per_second, plot_folder, "Mbps", frame_size, throughput)
    plot_per_frame_size(packets, plot_folder, "Packets", frame_size, throughput)


def plot_per_test(key, item, result_folder, throughput, duration):
    xpoints = frame_sizes
    ypoints = item
    plt.title(str(duration) + ' seconds test. Throughput = ' + str(throughput) + ' Mbit/s')
    plt.xlabel('Frame sizes')  
    plt.ylabel(key) 
    plt.bar(xpoints, ypoints, width = 0.3)   
    plt.savefig(result_folder + '/plot_files/end_data/' + key + ".png", format="png", bbox_inches="tight")
    plt.close()


def plot_per_frame_size(array, plot_file_address, file_name, frame_size, throughput):
    ypoints = array
    plt.title('Frame size = ' + frame_size+'. Throughput = ' + str(throughput) + ' Mbit/s')
    plt.xlabel('Seconds')  
    plt.ylabel(file_name) 
    plt.plot(ypoints)
    plt.savefig(plot_file_address + '/' + file_name + ".png", format="png", bbox_inches="tight")
    plt.close()


def run_ping(ip_address, ping_amount, folder_name):
    ping_folder = folder_name + '/ping/'
    os.system('mkdir -p ' + ping_folder)
    time = []
    os.system('ping -c ' + str(ping_amount)+ ' ' + ip_address + ' > ' + ping_folder + 'ping.txt')  # run ping command
    os.system('pingparsing ' + ping_folder + 'ping.txt --icmp-reply > ' + ping_folder + 'ping.json') # parse output into JSON
    with open(ping_folder+'ping.json') as file:
        ping_dict = json.load(file)
        for icmp_reply in ping_dict[ping_folder+'ping.txt']['icmp_replies']:
            time.append(icmp_reply['time'])
        file.close()         
        ypoints = np.array(time)
        plt.title('Ping')
        plt.xlabel('Seconds')  
        plt.ylabel('RTT (ms)') 
        plt.plot(ypoints)
        plt.savefig(ping_folder + "ping.png", format="png", bbox_inches="tight")
        plt.close()


def test_connection(ip_address, result_folder):
    test_connection_file = result_folder + '/test_connection.json'
    os.system('mkdir -p ' + result_folder)
    os.system('iperf3 -c '+ str(ip_address) + ' -u -t 1 -J --logfile ' + test_connection_file) # simple 1 second udp test
    with open(test_connection_file) as file:
        content = file.read()
        file.close() 
        if content.find("error") != -1:
            return content
        else:
            return True
            

def main():
    duration = 5 # seconds of each iperf3 measurement
    ping_amount = 5 # amount of pings. equals to seconds, as 1 ping = 1 second
    ip_address = '192.168.0.6'  # aim IP address
    folder_name = "test_5sec_bar-chart"  # where all the plots will be stored
    throughput_threshold = 1 # maximum allowed lost percentage
    start_bandwidth = 300 # the upper limit, higher than maximum expected rate. in Mbit/s e.x. 15000M = 15Gbit/s
    bandwidth_step = 50 # how fast and precise search of the throughtput is. in Mbit/s

    os.system('rm -rf ' + folder_name)  # delete all previos data in the folder. if you want your data saved than change the name of the folder

    connection_result = test_connection(ip_address, folder_name)  # test the availability of the iperf3 server
    
    if connection_result == True:
        throughput = detect_throughput(ip_address, throughput_threshold, folder_name, start_bandwidth, bandwidth_step)  # detect maximum lossless bandiwidth
        if throughput != 0:
            run_iperf3(ip_address,folder_name,duration, throughput)     # run main measurements
            run_ping(ip_address, ping_amount, folder_name)
            print('Test was run with throughput = '+ str(throughput) + '\nAll successfull, check the folder now!')
        else:
            print("Error occured: the medium is too lossy. Throughput detection couldn't overcome the threshold of lost packets.")
    else:
        print("The test was unsuccessful. The error message: ", connection_result)

    
    # add burst_mode with -b / specifier (back2back test)


if __name__ == "__main__":
    main()