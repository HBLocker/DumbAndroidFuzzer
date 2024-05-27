import subprocess
import time
import os
import itertools
import random
import threading
from queue import PriorityQueue, Queue

# Constants
FUZZ_WAIT = 5
DEBUG = True
ADB_BINARY = "./adb"
CRASH_IDENTIFIERS = ['SI_QUEUE', 'SIGSEGV', 'SIGFPE', 'SIGILL', 'SIGABRT', 'OOM', 'OutOfMemoryError',
                     'java.lang.OutOfMemoryError']  # Removed 'java.lang.NullPointerException'
NOT_CRASHED = 0
CRASHED = 1
FUZZ_IP = "10.14.14.204"
# Device Settings
DEVICE_ID = "R5CWA2ZJ70N"
SERVER_IP = "0.0.0.0"
SERVER_PORT = 1337

service_enum_q = Queue()
call_q = PriorityQueue()

# Dictionary containing data types and values for fuzzing
parcels = {"i32": [1, 0, 65535, 0xfffffffe, 0xfffffff],
           "i64": [0xffffffffffffffffe, 0xfffffffffffffffff, 1, 0],
           "f": [-1, 3.141592],
           "s16": ["3%%n%x%%s%s%%n1", "A" * 10, "A" * 4, "\xff\xfff\xff\xff\xff\xff\xff\xfc"]
           }


# Locks for synchronization
has_crashed_lock = threading.Lock()
queue_lock = threading.Lock()

# Variable to track crash status
HAS_CRASHED = 0


def enum_services():
    """
    Enumerate available services on the device and prompt the user to select services for fuzzing.
    """
    adb = ADB_BINARY
    x = subprocess.run([adb, "shell", "service list"], stdout=subprocess.PIPE)
    lines = x.stdout.split(b"\n")  # Split the output into lines
    available_services = []
    for line in lines:
        line = line.strip()  # Remove leading and trailing whitespace
        if b":" in line:
            service_name = line.split(b":")[0].strip().decode()  # Extract the service name
            available_services.append(service_name)
    print("Available services:")
    for idx, service in enumerate(available_services, start=1):
        print(f"{idx}. {service}")

    # Prompt the user to enter a list of four services to fuzz
    selected_services = []
    while len(selected_services) < 1:
        try:
            idx = int(input("Enter the number of the service to fuzz: "))
            if 1 <= idx <= len(available_services):
                service = available_services[idx - 1]
                if service not in selected_services:
                    selected_services.append(service)
                else:
                    print("Service already selected. Choose a different one.")
            else:
                print("Invalid input. Please enter a number corresponding to an available service.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    return selected_services


def adb_connection_init():
    """
    Initialize ADB connection and prepare the device for fuzzing.
    """
    adb = ADB_BINARY
    dev_id = DEVICE_ID
    subprocess.call([adb, "kill-server"])
    subprocess.call([adb, "start-server"])
    subprocess.call([adb, "-s", dev_id, "wait-for-device"])


def mutate(service_name):
    """
    Fuzz the specified service by generating and executing fuzzed commands.
    """
    try:
        # Remove the leading '288\t' from the service name
        service_name = service_name.split('\t')[-1]

        for method_no in range(1, 128):
            for args_count in range(4):  # the number of args (outputs) that the fuzzer will produce
                for args_schema in itertools.combinations(parcels.keys(), args_count):
                    arg_collection = []
                    for arg_type in args_schema:
                        for current_arg_value in parcels[arg_type]:
                            arg_collection.append("{} \"{}\" ".format(arg_type, current_arg_value))
                    for fuzzed_args in itertools.combinations(arg_collection, args_count):
                        arg_list = [a for a in fuzzed_args]
                        str_args = "".join(arg_list)
                        FUZZCMD = "service call {} {} {}".format(service_name, method_no, str_args)
                        with queue_lock:
                            call_q.put((random.randrange(1, 100), FUZZCMD))
    except Exception as e:
        print(f"Error occurred while mutating service {service_name}: {e}")


def check_if_crash(service_name, process):
    """
    Check if the specified process has crashed by analyzing logcat output.
    """
    global HAS_CRASHED
    nr_de_iter = 1
    adb = ADB_BINARY
    crash_identifiers = CRASH_IDENTIFIERS
    args = [adb, "shell"] + list(process.split(" "))
    try:
        out = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0]
        # Process the output if needed
    except Exception as e:
        pass  # Ignore the error silently

    logcat_args = [adb, 'logcat', '-d']
    logcat = subprocess.Popen(
        logcat_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    time.sleep(FUZZ_WAIT)
    logcat.kill()
    logcat2 = [line.strip().decode('utf-8', errors='backslashreplace').replace("\\", "").rstrip().lstrip() for line
               in iter(logcat.stdout.readline, b'')]

    # Filter out log messages containing "FATAL EXCEPTION IN SYSTEM PROCESS: WifiHandlerThread"
    filtered_logs = [log for log in logcat2 if "FATAL EXCEPTION IN SYSTEM PROCESS: WifiHandlerThread" not in log]

    logcat_args = [adb, 'logcat', '-b', 'crash', '-d']
    logcat_crash_positive = subprocess.Popen(
        logcat_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    logcat_crash_positive.wait()
    logcat_crash_positive_result = [line.strip().decode('utf-8', errors='backslashreplace').replace("\\", "").rstrip().lstrip() for line
                                     in iter(logcat_crash_positive.stdout.readline, b'')]
    if len(logcat_crash_positive_result) > 0:
        print("[!] Crashed")
        print(logcat_crash_positive_result)

    nr_de_iter += 1
    filtered_logs = "\n".join(filtered_logs)
    logcat_crash_positive_result = "\n".join(logcat_crash_positive_result)

    FLAG = False  # Initialize FLAG outside the loop
    for id_string in crash_identifiers:
        if id_string in filtered_logs or id_string in logcat_crash_positive_result:
            # Check if any of the out-of-memory error variations are present
            if not any(error_str in filtered_logs for error_str in ["OutOfMemoryError", "java.lang.OutOfMemoryError"]) \
                    and not any(error_str in logcat_crash_positive_result for error_str in ["OutOfMemoryError", "java.lang.OutOfMemoryError"]) \
                    and "java.lang.NullPointerException" not in filtered_logs \
                    and "java.lang.NullPointerException" not in logcat_crash_positive_result:
                FLAG = True
                break

    if FLAG:
        with has_crashed_lock:
            HAS_CRASHED = 1
            crash_filename = f"{service_name}.txt"
            crash_path = os.path.join("AndroidCrashes", crash_filename)
            with open(crash_path, "a") as crash_file:  # Change mode to "a" for append
                crash_file.write("Crash Detected:\n")
                crash_file.write(f"Service: {service_name}\n")
                crash_file.write("Logcat Output:\n")
                crash_file.write(filtered_logs + "\n")
                crash_file.write("Crash Log Output:\n")
                crash_file.write(logcat_crash_positive_result + "\n")
                crash_file.write("Command with Crash:\n")
                crash_file.write(process + "\n")
                print(f"Crash report saved: {crash_path}")
            HAS_CRASHED = 0


def producer():
    """
    Generate fuzzed commands for the selected services and add them to the call queue.
    """
    print(f"Started Producer {threading.get_ident()}")
    while True:
        service = service_enum_q.get()
        if service == "stop":
            service_enum_q.task_done()
            break
        mutate(service)
        service_enum_q.task_done()
    print(f"Done Producer {threading.get_ident()}")


def consumer():
    """
    Consume fuzzed commands from the call queue and check for crashes.
    """
    print(f"Started Consumer {threading.get_ident()}")
    while True:
        _, call = call_q.get()
        print("[!]::", call)
        if call == "stop":
            call_q.task_done()
            break
        try:
            service_name = call.split()[2]  # Extract the service name from the call
            check_if_crash(service_name, call)  # Pass the extracted service_name
        except Exception as e:
            print(f"Error occurred while checking for crash: {e}")
        call_q.task_done()
    print(f"Done Consumer {threading.get_ident()}")


def Fuzz():
    """
    Main function to start the fuzzing process.
    """
    global HAS_CRASHED
    adb_connection_init()

    prod_threads = []
    consumer_threads = []
    for _ in range(20):
        t = threading.Thread(target=producer)
        t.start()
        prod_threads.append(t)

    enum_services()

    for _ in range(20):
        service_enum_q.put('stop')

    for _ in range(20):
        t = threading.Thread(target=consumer)
        t.start()
        consumer_threads.append(t)

    service_enum_q.join()

    for _ in range(20):
        call_q.put((1000, 'stop'))
    call_q.join()


if __name__ == '__main__':
    selected_services = enum_services()  # Prompt the user to select services

    NUM_CONSUMERS = 100  # Define the number of consumer threads
    # Start the fuzzing process for each selected service
    for service_name in selected_services:
        try:
            mutate(service_name)
        except Exception as e:
            print(f"Error occurred while mutating service {service_name}: {e}")

    # Start the consumer threads to perform the fuzzing
    consumer_threads = []
    for _ in range(NUM_CONSUMERS):
        consumer_thread = threading.Thread(target=consumer)
        consumer_thread.start()
        consumer_threads.append(consumer_thread)

    # Wait for all consumer threads to finish
    for consumer_thread in consumer_threads:
        consumer_thread.join()
    Fuzz()
