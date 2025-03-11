import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json, argparse
from data import ModeEnv, ModeTest

def initializeSettings():
    """Initializes the testing settings from the JSON configuration file.

    Returns:
        tuple: A tuple containing the following settings:
            - NODES (list): List of number of nodes per infrastructure.
            - SEEDS (list): List of seeds for random infrastructure generation.
            - ITERATIONS (int): Number of iterations.
            - TIMEOUT_SECONDS (int): Timeout in seconds for each test.
            - INFRASTRUCTURE_DIRECTORY (str): Directory for generated infrastructures.
            - APPLICATION_DIRECTORY (str): Directory for application files.
    """
    JSON_FILE_PATH = "testing_settings.json"
    with open(JSON_FILE_PATH, 'r') as file:
        json_data = json.load(file)
    RND_CSV = json_data['CSV_DIRECTORY'] + 'Realistic_Experiment.csv'
    HRST_CSV = json_data['CSV_DIRECTORY'] + 'Curated_Experiment.csv'
    return RND_CSV, HRST_CSV

RND_CSV, HRST_CSV = initializeSettings()
ENDPOINTS = list(range(1, 7))

def scalabilityResults(csvFile:str, modeTest:ModeTest, modeEnv:ModeEnv):
    """Plots the scalability results from a CSV file.

    Args:
        csvFile (str): Path to the CSV file containing the data.
        modeTest (Enum): Enum representing the test mode.
        modeEnv (Enum): Enum representing the environment mode. Can be either CRTD or RND.

    Raises:
        FileExistsError: If the CSV file is not found.
        ValueError: If an invalid modeEnv is provided.

    """
    try:
        df = pd.read_csv(csvFile)
    except:
        raise FileExistsError(f'\n\nFile {csvFile} not found\n')
    
    modetest = modeTest.name.lower()
    df.replace(['X', '/'], pd.NA, inplace=True)
    print(modetest)
    df[f'Time_{modetest}'] = pd.to_numeric(df[f'Time_{modetest}'], errors='coerce')
    
    df = df.dropna(subset=[f'Time_{modetest}'])
    
    avgTime = df.groupby(['Microservices', 'InfrastructureNodes'])[f'Time_{modetest}'].mean().reset_index()
    print(avgTime)
    
    plt.figure(figsize=(10, 6))
    if modeEnv == ModeEnv.CURATED:
        plt.plot(avgTime['InfrastructureNodes'], avgTime[f'Time_{modetest}'], marker='o', linestyle='-', label='6 Endpoints')
    elif modeEnv == ModeEnv.RANDOM:
        for i, ms in enumerate(avgTime['Microservices'].unique()):
            ms_data = avgTime[avgTime['Microservices'] == ms]
            plt.plot(ms_data['InfrastructureNodes'], ms_data[f'Time_{modetest}'], marker='o', linestyle='-', label=f'Microservices {ms}')
    else:
        raise ValueError('Invalid modeEnv')

    plt.xlabel('Nodes')
    plt.xscale('log', base=2)
    plt.ylabel('Time (seconds)')
    plt.legend()
    plt.grid(True)
    plt.show()


def accuracyResults(csvFile:str, modeTest:ModeTest, modeEnv:ModeEnv):
    """Plots the accuracy results from a CSV file.

    Args:
        csvFile (str): Path to the CSV file containing the data.
        modeTest (Enum): Enum representing the test mode.
        modeEnv (Enum): Enum representing the environment mode.

    Raises:
        FileExistsError: If the CSV file is not found.
        ValueError: If an invalid modeEnv is provided.

    """
    try:
        df = pd.read_csv(csvFile)
    except:
        raise FileExistsError(f'\n\nFile {csvFile} not found\n')
    
    modetest = modeTest.name.lower()
    df[f'SCI_{modetest}'] = pd.to_numeric(df[f'SCI_{modetest}'], errors='coerce')
    df['SCI_exhaustive'] = pd.to_numeric(df['SCI_exhaustive'], errors='coerce')
    df['InfrastructureNodes'] = pd.to_numeric(df['InfrastructureNodes'], errors='coerce')
    df['Microservices'] = pd.to_numeric(df['Microservices'], errors='coerce')

    df['SCI_diff'] = abs(df[f'SCI_{modetest}'] - df['SCI_exhaustive']) / df['SCI_exhaustive'] 

    df = df.dropna(subset=['SCI_diff'])
    avgSCIDiff = None

    plt.figure(figsize=(10, 6))
    if modeEnv == ModeEnv.CURATED:
        avgSCIDiff = df.groupby('InfrastructureNodes')['SCI_diff'].mean().reset_index()
        if not avgSCIDiff.empty:
            plt.plot(avgSCIDiff['InfrastructureNodes'], avgSCIDiff['SCI_diff'], marker='o', linestyle='-', color='b', label='6 Endpoints')
        else:
            print("No data available for CRTD mode.")
    elif modeEnv == ModeEnv.RANDOM:
        avgSCIDiff = df.groupby(['Microservices', 'InfrastructureNodes'])['SCI_diff'].mean().reset_index()
        colormap = plt.colormaps.get_cmap('tab10')
        colors = [colormap(i) for i in range(len(avgSCIDiff['Microservices'].unique()))]
        for i, ms in enumerate(avgSCIDiff['Microservices'].unique()):
            msData = avgSCIDiff[avgSCIDiff['Microservices'] == ms]
            plt.plot(msData['InfrastructureNodes'], msData['SCI_diff'], marker='o', linestyle='-', color=colors[i], label=f'Microservices {ms}')
    else:
        raise ValueError('Invalid modeEnv')

    plt.xlabel('Nodes')
    plt.ylabel('SCI Difference')
    plt.yscale('linear')
    plt.xscale('log', base=2)

    plt.legend()
    plt.grid(True)
    plt.show()
    

prsr = argparse.ArgumentParser(description='Visualize the results of the experiments')
prsr.add_argument('--modeEnv', type=str, choices=['random', 'curated'], required=True, help='The mode of operation of the experiment that is to be visualized')
prsr.add_argument('--modeTest', type=str, choices=['exhaustive','greenonly','capacityonly','linearcombination'], required=True, help='The mode of the solution that is to be visualized')
prsr.add_argument('--parameter', type=str, choices=['accuracy', 'scalability'], required=True, help='The parameter that is to be visualized')
prsdArgs = prsr.parse_args()
mode = ModeEnv[prsdArgs.modeEnv.upper()]
test = ModeTest[prsdArgs.modeTest.upper()]
parameter = prsdArgs.parameter


if parameter == 'accuracy':
    if mode == ModeEnv.CURATED:
        accuracyResults(HRST_CSV, test, mode)
    elif mode == ModeEnv.RANDOM:
        accuracyResults(RND_CSV, test, mode)
    else:
        raise ValueError('Invalid modeEnv')
elif parameter == 'scalability':
    if mode == ModeEnv.CURATED:
        scalabilityResults(HRST_CSV, test, mode)
    elif mode == ModeEnv.RANDOM:
        scalabilityResults(RND_CSV, test, mode)
    else:
        raise ValueError('Invalid modeEnv')

