from swiplserver import PrologMQI 
import argparse
from typing import Tuple, List, Optional

def parsePacking(packing:str) -> List[str]:
    """Given a string representation of a list, returns a list of strings. 
    The list represents the packing of the microservices and their corresponding nodes.

    Args:
        packing (str): The string representation of a list.

    Returns:
        list: A list of strings.
    """
    return packing.strip('[]').split(',')

def getParameters() -> Tuple[str, str, str, bool, Optional[List[str]], Optional[int]]:
    """Parses command-line arguments for running experiments.

    Returns:
        tuple: A tuple containing the application file, infrastructure file, mode of operation, a boolean flag, and packing information.
    """
    prsr = argparse.ArgumentParser(description='Run experiments')
    prsr.add_argument('aFile', type=str, help='Application file')
    prsr.add_argument('iFile', type=str, help='Infrastructure file')
    prsr.add_argument('--mode', type=str, choices=['greenonly', 'capacityonly', 'linearcombination', 'exhaustive', 'base'], required=True, help='Mode of operation')
    prsr.add_argument('--t', action='store_true', help=argparse.SUPPRESS)
    prsr.add_argument('--timeout', type=int, default=None, help='Timeout in seconds for the Prolog process')
    # --- Expected packing format = "['on(microservice, node)', 'on(microservice, node)', ...]" --- #
    prsr.add_argument('--p', type=parsePacking, required=False, help='Packing')
    prsdArgs = prsr.parse_args()
    return prsdArgs.aFile, prsdArgs.iFile, prsdArgs.mode, prsdArgs.t, prsdArgs.p, prsdArgs.timeout

def printDict(dict:dict):
    """Prints the contents of a dictionary.

    Args:
        dict (dict): The dictionary to print.
    """
    for n in dict:
        print(f"\t\t\t{n} -> {dict[n]}")

def insert(ms:str, n:str, dict:dict) -> dict:
    """Inserts a microservice into a node in the dictionary.

    Args:
        ms (str): The microservice to insert.
        n (str): The node to insert the microservice into.
        dict (dict): The dictionary to insert the microservice into.

    Returns:
        dict: The updated dictionary.
    """
    if n not in dict:
        dict[n] = [ms]
    else:
        dict[n].append(ms)
    return dict

def unpackP(place: List[dict]) -> dict:
    """Unpacks a list of placements into a dictionary. 
    Builds the dictionary with nodes as keys and the microservices placed on them as values.

    Args:
        place (list): The list of placements.

    Returns:
        dict: A dictionary with nodes as keys and lists of microservices as packings.
    """
    dictP = {}
    for p in place:
        ms, n = p['args'][0], p['args'][1]
        insert(ms, n, dictP)
    return dictP


aFile, iFile, mode, t, p, timeout = getParameters()
result = None
with PrologMQI(query_timeout_seconds = timeout) as mqi:
    with mqi.create_thread() as prolog_thread:
        prolog_thread.query(f"consult('{aFile}').")
        prolog_thread.query(f"consult('{iFile}').")
        if t:
            prolog_thread.query(f"consult('../main.pl').")
        else:
            prolog_thread.query(f"consult('main.pl').")
        if mode=='base' and p:
            p = '[' + ','.join(p) + ']'
            p = p.replace("'","")
            # -- TODO: Change the mode to 'base' -- #
            mode= 'tempBase'
            prolog_thread.query_async(f"timedPlacement({mode}, App, {p}, SCI, N, Time).", find_all=False)
            result = prolog_thread.query_async_result()
        elif mode=='exhaustive':
            prolog_thread.query_async(f"timedPlacement({mode}, App, P, SCI, N, Time).", find_all=False)
            result = prolog_thread.query_async_result()
        else:
            prolog_thread.query_async(f"timedPlacement({mode}, App, P, SCI, N, Time).", find_all=False)
            result = prolog_thread.query_async_result()
        if not t:
            if isinstance(result, bool):
                print("No solution found\n\n")
            else:
                if p:
                    result =  result[0]
                    print(f"\n\nRESULTS   ->\tTIME = {result['Time']:.6f}")
                    print(f"\t\tSCI = {result['SCI']}\n\t\tNUMBER OF NODES = {result['N']}\n\n")
                else:
                    result, resultP = result[0], []
                    dictP = unpackP(result['P'])
                    print(f"\n\nRESULTS   ->\tPACKING = ")
                    printDict(dictP)
                    print(f"\t\tTIME = {result['Time']:.6f}")
                    print(f"\t\tSCI = {result['SCI']}\n\t\tNUMBER OF NODES = {result['N']}\n\n")
        else:
            print(result)
    
        
        
            
