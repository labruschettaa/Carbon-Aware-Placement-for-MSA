from data import ModeTest, ModeEnv
import os, subprocess, sys, re, json, csv, argparse
from swiplserver import PrologMQI
import json, pandas, random

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
    NODES = json_data['LST_NUMBER_OF_NODES']
    NODES.sort()
    SEEDS = json_data['LST_SEEDS_FOR_RANDOM_INFRASTRUCTURE']
    ITERATIONS = json_data['NUMBER_OF_ITERATIONS']
    TIMEOUT_SECONDS = json_data['TIMEOUT_SECONDS']
    INFRASTRUCTURE_DIRECTORY = json_data['GENERATED_INFRASTRUCTURE_DIRECTORY']
    APPLICATION_DIRECTORY = json_data['APPLICATION_DIRECTORY']
    FULL_APPLICATION_DIRECTORY = json_data['FULL_APPLICATION_DIRECTORY']
    CSV_DIRECTORY = json_data['CSV_DIRECTORY']
    return NODES, SEEDS, ITERATIONS, TIMEOUT_SECONDS, INFRASTRUCTURE_DIRECTORY, APPLICATION_DIRECTORY, FULL_APPLICATION_DIRECTORY, CSV_DIRECTORY

NODES, SEEDS, ITERATIONS, TIMEOUT_SECONDS, INFRASTRUCTURE_DIRECTORY, APPLICATION_DIRECTORY, FULL_APPLICATION_DIRECTORY, CSV_DIRECTORY = initializeSettings()

def countMicroservices(filePath):
    """Counts the number microservice facts in a file'.

    Args:
        file_path (str): The path to the file.

    Returns:
        int: The number of lines that begin with 'microservice('.
    """
    with PrologMQI() as mqi:
        with mqi.create_thread() as prolog_thread:
            prolog_thread.query(f"consult('{filePath}').")
            result = prolog_thread.query("findall(M, microservice(_,_,_), L), length(L, N).")
        return result[0]['N']

class CSVWriter:
    """A class to handle writing test results to a CSV file.

    Attributes:
        csvFile (str): The path to the CSV file.
        file (file object): The file object for the CSV file.
    """
    def __init__(self, csvFile):
        """Initializes the CSVWriter with the specified CSV file.

        Args:
            csvFile (str): The path to the CSV file.
        """
        if not os.path.exists(csvFile):
            self.__file =  open(csvFile, 'w', newline='')
            csvwriter = csv.writer(self.__file)
            csvwriter.writerow(["Iteration", "Microservices", "InfrastructureNodes", "Time_exhaustive", "Time_greenonly", "Time_capacityonly", "Time_linearcombination", "SCI_exhaustive", "SCI_greenonly", "SCI_capacityonly", "SCI_linearcombination", "NumNodes_exhaustive", "NumNodes_greenonly", "NumNodes_capacityonly", "NumNodes_linearcombination"])
        else:
            self.__file = open(csvFile, 'a', newline='')
        

    def writeResults(self, nList, resultsListExhaustive, resultsListGreenOnly, resultsListCapacityOnly, resultsListLinearCombination):
        """Writes the test results to the CSV file.

        Args:
            nList (list): List of n values.
            resultsListExhaustive (list): Results for the exhaustive test.
            resultsListGreenOnly (list): Results for the configuration greenonly.
            resultsListCapacityOnly (list): Results for the configuration capacityonly.
            resultsListLinearCombination (list): Results for the configuration linearcombination.
        """
        csvwriter = csv.writer(self.__file)
        for i, _ in enumerate(nList):
            resGO = resultsListGreenOnly[i]
            resCO = resultsListCapacityOnly[i]
            resLC = resultsListLinearCombination[i]
            resO = resultsListExhaustive[i]
            if resGO['Ms'] != resO['Ms'] or resGO['I'] != resO['I']:
                print("Error: Ms mismatch")
            csvwriter.writerow(
                [resO['I'] + 1, resO['Ms'], nList[i],
                 resO['Time'], resGO['Time'], resCO['Time'], resLC['Time'],
                 resO['SCI'], resGO['SCI'], resCO['SCI'], resLC['SCI'],
                 resO['N'], resGO['N'], resCO['N'], resLC['N']]
            )

class Test:
    """Class that represents a test to be executed."""
    def __init__(self, mode:ModeTest):
        """Initializes the Test with the specified CSV file.
        Args:
            mode (ModeTest): The mode in which the test is executed.
        """
        self.__mode = mode
        self._nList, self._resultsGreenOnly, self._resultsCapacityOnly, self._resultsLinearCombination, self._resultsExhaustive = [], [], [], [], []

    

    def _placementResults(self, apath:str, fpath:str, mode:ModeTest, results, iteration:int, ms:int, failed=False, packing=None):
        """Processes the placement results and updates the results list.

        Args:
            apath (str): The path to the application file.
            fpath (str): The path to the file where results are stored.
            mode (str): The mode in which the placement is executed.    
            results (list): The list to store the results.
            iteration (int): The current iteration number.
            ms (int): The number of MS.
            failed (bool, optional): Indicates if the placement failed. Defaults to False.

        Returns:
            bool: True if the placement was successful, False otherwise.
        """
        # --- If the placement failed for previous smaller infrastructure, it 
        #      will count as failed for the current infrastructure. --- #
        res = None
        if not failed:
            # --- Case: The placement is in BASE mode. --- #
            if mode == ModeTest.BASE and packing is not None:
                res = self._place(apath, fpath, mode, packing)
                res = res.decode('utf-8').strip().replace("'", '"')
                res = json.loads(res)[0]
                # --- Saves the result as the EXHAUSTIVEimal placement. --- #
                self._resultsExhaustive.append({'I': iteration, 'Ms': ms, 'Time': res['Time'], 'SCI': res['SCI'], 'N': res['N']})
                return True
            else:
                res = self._place(apath, fpath, mode)
        # --- Case: The placement failed (timeout). --- #
        if res is None or failed:
            results.append({'I': iteration, 'Ms': ms, 'Time': 'X', 'SCI': 'X', 'N': 'X'})
            return False
        else:
            res = res.decode('utf-8').strip().replace("'", '"')

            # --- Case: The placement failed (no solution). --- #
            if res == 'True' or res == 'False':
                results.append({'I': iteration, 'Ms': ms, 'Time': '/', 'SCI': '/', 'N': '/'})

            # --- Case: The placement was successful. --- #
            else:
                res = json.loads(res)[0]
                results.append({'I': iteration, 'Ms': ms, 'Time': res['Time'], 'SCI': res['SCI'], 'N': res['N']})
            return True
        
    def _place(self, app:str, infra:str, mode:ModeTest, packing=None):
        """Executes the placement process using the specified mode.

        Args:
            app (str): The path to the application file.
            infra (str): The path to the infrastructure file.
            mode (Mode): The mode in which the placement is executed.
            packing (int, optional): The packing for the placement. Defaults to None.

        Returns:
            bytes: The standard output from the subprocess if successful.
            None: If an error occurs or the subprocess times out.
        """
        try:
            if mode == ModeTest.BASE and packing is not None:
                # --- TODO: Fix the packing option for the base mode. --- #
                command = [sys.executable, '../wrapper.py', app, infra, '--m', mode.name.lower(), '--t', '--p', str(packing), '--timeout', str(TIMEOUT_SECONDS)]
            else:
                command = [sys.executable, '../wrapper.py', app, infra, '--m', mode.name.lower(), '--t', '--timeout', str(TIMEOUT_SECONDS)]
            sp = subprocess.run(command,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL,
                                timeout=TIMEOUT_SECONDS)
            return sp.stdout
        except subprocess.CalledProcessError as e:
            print(f"An error occurred: {e}")
            return None
        except subprocess.TimeoutExpired:
            print(f"The subprocess timed out after {TIMEOUT_SECONDS} seconds.")
            return None
    
    def _extractNumber(self, filename):
        """Extracts the first number found in a string.

        Args:
            filename (str): The string from which to extract the number.

        Returns:
            int: The first number found in the string, or 0 if no number is found.
        """
        match = re.search(r'\d+', filename)
        return int(match.group()) if match else 0
    
    def _getIterationIndex(self, csvFile:str) -> int:
        iterationIndex = 1
        if os.path.exists(csvFile) and os.path.getsize(csvFile) > 0:
            df = pandas.read_csv(csvFile)
            if 'Iteration' in df.columns:
                max = df['Iteration'].max()
                if not pandas.isna(max):
                    iterationIndex = df['Iteration'].max() + 1
        if (iterationIndex + ITERATIONS) > SEEDS.__len__():
            print("The number of iterations exceeds the length of the array of seeds.\nA random seed will be generated for the next iterations, proceed? (y/n)")
            while True:
                response = input().strip().lower()
                if response in ['no', 'n']:
                    raise ValueError("Operation aborted by the user.")
                elif response in ['yes', 'y']:
                    break
                else:
                    print("Invalid response. (y/n)")
        return iterationIndex
    
    def _getTestFiles(self, directory, regex):
        """Gets the test files from the specified directory."""
        directory = os.path.dirname(directory)
        if not os.path.exists(directory):
            os.makedirs(directory)

        files = os.listdir(directory)
        testFiles = [f for f in files if regex.match(f)]
        sortedFiles = sorted(testFiles, key=self._extractNumber)
        
        return sortedFiles
    
    def _deleteTestFiles(self, directory, regex):
        """Deletes all the test files from the specified directory that match the given regex."""
        
        testFiles = self._getTestFiles(directory, regex)
        
        for file in testFiles:
            filePath = os.path.join(directory, file)
            os.remove(filePath)
    
    def runTests(self):
        if self.__mode == ModeEnv.RANDOM:
            return RandomTestEnv().runTests()
        elif self.__mode == ModeEnv.CURATED:
            if any(node < countMicroservices(FULL_APPLICATION_DIRECTORY) for node in NODES):
                print("Error: A curated enviroment test cannot have less nodes than the number of microservices in the application.")
                sys.exit(1)
            return CuratedTestEnv().runTests()
        else:
            print("Invalid mode of operation.")
            return False

class RandomTestEnv(Test):
    """A class to execute tests in realistic generated environments.
    After a tests is terminated its results are written to a CSV file."""

    def __init__(self):
        """Initializes the RandomTestEnv with default values."""
        super().__init__(ModeEnv.RANDOM)
        csvFile = CSV_DIRECTORY + "Realistic_Experiment_" + os.path.basename(os.path.normpath(APPLICATION_DIRECTORY)) + ".csv"
        self.__csvWriter = CSVWriter(csvFile)
        self.__numMS = countMicroservices(FULL_APPLICATION_DIRECTORY)
        self.__iterationIndex = self._getIterationIndex(csvFile)
        
    def runTests(self):
        """Runs the tests with the specified settings."""
        generatedSeeds = []
        for iteration in range(self.__iterationIndex, self.__iterationIndex + ITERATIONS):
            print(f'Iteration {iteration} starting...')

            # --- Generates the infrastructures specified in NODES. --- #
            self._deleteTestFiles(INFRASTRUCTURE_DIRECTORY, re.compile(r'rnd_(\d+)\.pl'))
            nodesSTR = ' '.join(map(str, NODES))
            try:
                seed = SEEDS[iteration]
            except IndexError:
                seed = random.randint(0, 1000000)
                print(f"Seed for iteration {iteration} was not found. Using random seed: {seed}")
                generatedSeeds.append({"iteration": iteration, "seed": seed})

            command = [sys.executable, 'generate.py', '--infraDir', INFRASTRUCTURE_DIRECTORY, '--mode', 'random', '--seed',  str(SEEDS[iteration]), nodesSTR]  
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # --- Executes all the test for each application in the application directory. --- #
            for afile in sorted(os.listdir(APPLICATION_DIRECTORY)):
                apath = os.path.join(APPLICATION_DIRECTORY, afile)
                ms = re.search(r'application(\d+)ms\.pl', afile)
                if ms:
                    ms = ms.group(1)
                else:
                    ms = self.__numMS

                # --- Executes the exhaustive and heuristic solutions for each infrastructure generated. --- #
                failed = False
                for file in self._getTestFiles(INFRASTRUCTURE_DIRECTORY, re.compile(r'rnd_(\d+)\.pl')):
                    self._nList.append(self._extractNumber(file))
                    print(f'Executing tests for file: {file}, number of microservices: {ms}...')
                    fpath = os.path.join(INFRASTRUCTURE_DIRECTORY, file)

                    # --- Executes the exhaustive solution. --- #
                    if self._placementResults(apath, fpath, ModeTest.EXHAUSTIVE, self._resultsExhaustive, iteration, ms, failed) == False:
                        failed = True

                    # --- Executes the heuristic solutions. --- #
                    self._placementResults(apath, fpath, ModeTest.GREENONLY, self._resultsGreenOnly, iteration, ms)
                    self._placementResults(apath, fpath, ModeTest.CAPACITYONLY, self._resultsCapacityOnly, iteration, ms)
                    self._placementResults(apath, fpath, ModeTest.LINEARCOMBINATION, self._resultsLinearCombination, iteration, ms)

                # -- Writes the results to the CSV file, after all the tests for an application are completed. -- #
                self.__csvWriter.writeResults(self._nList, self._resultsExhaustive, self._resultsGreenOnly, self._resultsCapacityOnly, self._resultsLinearCombination)
                self._nList, self._resultsGreenOnly, self._resultsCapacityOnly, self._resultsLinearCombination, self._resultsExhaustive = [], [], [], [], []

        if generatedSeeds:
            print("Experiment completed, generated seeds:")
            for seed in generatedSeeds:
                print(f"\tIteration: {seed['iteration']}, Seed: {seed['seed']}")
        else:
            print("Experiment completed.")

class CuratedTestEnv(Test):
    """Class to execute tests in the curated environments."""

    def __init__(self):
        """Initializes the CuratedTestEnv with default values."""
        super().__init__(ModeEnv.CURATED)
        csvFile = CSV_DIRECTORY + "Curated_Experiment_" + os.path.basename(os.path.normpath(APPLICATION_DIRECTORY)) + ".csv"
        self.__csvWriter = CSVWriter(csvFile)
        self.__iterationIndex = self._getIterationIndex(csvFile)
        self.__fullApp = FULL_APPLICATION_DIRECTORY
        self.__numMS = countMicroservices(self.__fullApp)
        self.__output = []

    def runTests(self):
        """Runs the tests for the curated test environment.

        Iterates through the specified number of iterations, generates infrastructure, extracts optimal placements,
        and executes tests for each generated infrastructure. Writes the results to a CSV file.

        Raises:
            json.JSONDecodeError: If there is an error decoding JSON from the output of generate.py.
        """
        for iteration in range(self.__iterationIndex, self.__iterationIndex + ITERATIONS):
            print(f'Iteration {iteration + 1} starting...')
            nodesSTR = ' '.join(map(str, NODES))
            self._deleteTestFiles(INFRASTRUCTURE_DIRECTORY, re.compile(r'crtd_(\d+)\.pl'))
            command = [sys.executable, 'generate.py', '--m', 'curated', '--s', str(SEEDS[iteration]), '--infraDir', INFRASTRUCTURE_DIRECTORY, '--appFile', self.__fullApp, nodesSTR]
            sp = subprocess.run(command, capture_output=True, text=True)

            # --- Exctracts the EXHAUSTIVEimal placement for each infrastructure generated returned by generate.py. --- #
            for line in sp.stdout.strip().split('\n'):
                try:
                    line = line.replace("'", '"')
                    items = json.loads(line)
                    self.__output.append([f"on({item['Ms']}, {item['N']})" for item in items])
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")

            # --- Executes the tests for each infrastructure generated. --- #
            for indexFile, file in enumerate(self._getTestFiles(INFRASTRUCTURE_DIRECTORY, re.compile(r'crtd_(\d+)\.pl'))):
                self._nList.append(self._extractNumber(file))
                print(f'Executing tests for file: {file}...')
                fpath = os.path.join(INFRASTRUCTURE_DIRECTORY, file)

                # --- Find the SCI score for the EXHAUSTIVEimal placement of that generated infrastructure. --- #
                self._placementResults(self.__fullApp, fpath, ModeTest.BASE, self._resultsExhaustive, iteration, self.__numMS, False, self.__output[indexFile])

                # --- Executes the heuristic solutions for the generated infrastructure. --- #
                self._placementResults(self.__fullApp, fpath, ModeTest.GREENONLY, self._resultsGreenOnly, iteration, self.__numMS)
                self._placementResults(self.__fullApp, fpath, ModeTest.CAPACITYONLY, self._resultsCapacityOnly, iteration, self.__numMS)
                self._placementResults(self.__fullApp, fpath, ModeTest.LINEARCOMBINATION, self._resultsLinearCombination, iteration, self.__numMS)

            self.__csvWriter.writeResults(self._nList, self._resultsExhaustive, self._resultsGreenOnly, self._resultsCapacityOnly, self._resultsLinearCombination)
            self._nList, self._resultsGreenOnly, self._resultsCapacityOnly, self._resultsLinearCombination, self._resultsExhaustive = [], [], [], [], []

prsr = argparse.ArgumentParser(description='Run experiments')
prsr.add_argument('--envMode', type=str, choices=['random', 'curated'], required=True, help='Mode of operation')
prsr.add_argument('--clean', action='store_true', help='Clean the testing directory of previous generated infrastructures before running the tests')
prsdArgs = prsr.parse_args()
envMode = ModeEnv[prsdArgs.envMode.upper()]

initializeSettings()

test = Test(envMode)
test.runTests()

