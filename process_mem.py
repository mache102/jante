import psutil
import os 
import time 

INTERVAL = 1
MAX = 99
TOP = 20


def convert(x, unit=2):
    return x / (1024 ** unit)

def get_constant_value():
    self_pid = os.getpid()

    # Get total RAM usage
    total_ram = psutil.virtual_memory().total

    min_rrm = total_ram * (100 - MAX) / 100

    return self_pid, min_rrm
    
def get_processes():
    # Get a list of all running processes and their memory usage
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
        processes.append([proc.info['pid'], 
                        proc.info['name'], 
                        convert(proc.info['memory_info'].rss)])

    # Sort the list of processes by memory usage (descending order)
    processes.sort(key=lambda x: x[2], reverse=True)
    return processes

def main():
    self_pid, min_rrm = get_constant_value()

    while (True):
              
        processes = get_processes()
        rrm = psutil.virtual_memory().available

        os.system('cls')
        print('Monitoring processes...')

        # Print the list of processes sorted by memory usage
        print(f"Top {TOP} process usage:")
        for pid, name, mem_usage in processes[:TOP]:
            print(f"PID: {pid:<8} | Name: {name:<20} | Memory Usage: {mem_usage:>8.1f} MB")

        print(f'Memory available: {convert(rrm):.1f} MB')
        print('\n')
        if rrm < min_rrm:
            print('Exceeded maximum memory usage. Killing processes.')

            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] == 'python.exe' and proc.info['pid'] != self_pid:
                    proc.kill()
            
            exit()

        time.sleep(INTERVAL)

if __name__ == '__main__':
    main()