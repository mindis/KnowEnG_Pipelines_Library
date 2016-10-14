def generate_compute_clusters(cluster_ip_addresses, func_name, dependency_list):
    '''
    Generate clusters based on given list of ip address

    Args:
        cluster_ip_addresses: a list of ip address
        func_name: function name
        dependency_list: the dependencies for running the current function

    Returns:
        cluster_list: a list of clusters as dispy object

    '''
    import sys
    import dispy
    import logging
    try:
        cluster_list = []
        range_list = range(0, len(cluster_ip_addresses))
        print(range_list)
        for i in range_list:
            cur_cluster = dispy.JobCluster(func_name,
                                           nodes=[cluster_ip_addresses[i]],
                                           depends=dependency_list,
                                           loglevel=logging.WARNING)
            cluster_list.append(cur_cluster)
        return cluster_list
    except:
        raise OSError(sys.exc_info())


def create_cluster_worker(cluster, i, *args_to_func):
    '''
    Submit a job to cluster.

    Args:
        cluster:
        i:
        *args_to_func: a list of arguments following by the order of arguments defined in
            calling function.


    Returns:

    '''
    import sys
    # print("Start creating clusters {}.....".format(str(i)))
    try:
        send_args = list(args_to_func)

        print("len of send_args = {}".format(len(send_args)))
        job = cluster.submit(*send_args)
        job.id = i
        ret = job()
        print(ret, job.stdout, job.stderr, job.exception, job.ip_addr, job.start_time, job.end_time)
    except:
        raise OSError(sys.exc_info())


def parallel_submitting_job_to_each_compute_node(cluster_list, number_of_jobs_each_node, *arguments):
    '''
    Parallel submitting jobs to each node and start computation.

    Args:
        cluster_list:
        number_of_jobs_each_node:
        *arguments: a list of arguments following by the order of arguments defined in
            calling function.

    Returns:

    '''
    import threading
    import sys

    thread_list = []
    received_args = tuple(arguments)
    print("Start spawning {} threads.....".format(len(cluster_list)))
    try:
        for i in range(len(cluster_list)):
            compute_func_args = received_args + (number_of_jobs_each_node[i],)
            t = threading.Thread(target=create_cluster_worker, args=(cluster_list[i], i) + compute_func_args)
            thread_list.append(t)
            t.start()

        for thread in thread_list:
            thread.join()

        for cluster in cluster_list:
            cluster.print_status()

        for cluster in cluster_list:
            cluster.close()
    except:
        raise OSError(sys.exc_info())


def determine_number_of_compute_nodes(cluster_ip_addresses, number_of_bootstraps):
    '''
    Determine the total number of compute nodes will be used in execution

    Args:
        cluster_ip_addresses: a list of ip address
        number_of_bootstraps:  total number of loops needs to be distributed across clusters

    Returns:
        number_of_compute_nodes: the number of compute nodes

    '''
    available_computing_nodes = len(cluster_ip_addresses)

    if (number_of_bootstraps < available_computing_nodes):
        number_of_compute_nodes = number_of_bootstraps
    else:
        number_of_compute_nodes = available_computing_nodes

    return number_of_compute_nodes


def determine_job_number_on_each_compute_node(number_of_bootstraps, number_of_compute_nodes):
    '''
    Determine total number of jobs run on each compute node

    Args:
        number_of_bootstraps: total number of loops needs to be distributed across compute nodes
        number_of_compute_nodes: total number of available compute nodes

    Returns:
        number_of_scheduled_jobs: a list of integer indicates number of jobs distribution across compute nodes

    '''
    number_of_jobs_on_single_node = int(number_of_bootstraps / number_of_compute_nodes)
    remainder_of_jobs = number_of_bootstraps % number_of_compute_nodes

    number_of_scheduled_jobs = []
    if remainder_of_jobs > 0:
        count = 0
        for i in range(number_of_compute_nodes):
            if (count < remainder_of_jobs):
                number_of_scheduled_jobs.append(number_of_jobs_on_single_node + 1)
            else:
                number_of_scheduled_jobs.append(number_of_jobs_on_single_node)
            count += 1
    else:
        for i in range(number_of_compute_nodes):
            number_of_scheduled_jobs.append(number_of_jobs_on_single_node)

    print("number_of_scheduled_jobs across clusters : {}".format(number_of_scheduled_jobs))
    return number_of_scheduled_jobs


def determine_parallelism_locally(number_of_loops):
    '''
    Determine the parallelism on the current compute node

    Args:
        number_of_loops: total number of loops will be executed on current compute node

    Returns:
        number_of_cpu: parallelism on current compute node

    '''
    import multiprocessing
    number_of_cpu = multiprocessing.cpu_count()
    if (number_of_loops < number_of_cpu):
        return number_of_loops
    else:
        return number_of_cpu


