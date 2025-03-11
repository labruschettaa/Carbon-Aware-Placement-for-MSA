from swiplserver import PrologMQI
import random as rnd
from data import FactoryNode, NodeT, Microservice, ModeEnv
import argparse, os, re, sys, json
from typing import Tuple, List, Optional

JSON_FILE_PATH = "testing_settings.json"
with open(JSON_FILE_PATH, 'r') as file:
        json_data = json.load(file)
GENERATED_INFRASTRUCTURE_DIRECTORY = json_data['GENERATED_INFRASTRUCTURE_DIRECTORY']
APPLICATION_DIRECTORY = json_data['APPLICATION_DIRECTORY']

def getParameters() -> Tuple[Optional[str], Optional[str], List[int], Optional['ModeEnv'], Optional[int], bool]:
    """Parses and returns the command-line arguments for generating infrastructures.

    Returns:
        tuple: A tuple containing the following elements:
            - appFile (str or None): The application file directory.
            - infraFile (str or None): The infrastructure file directory.
            - args_list (list of int): A list of integers parsed from the command-line arguments.
            - mode (Mode or None): The mode of generation.
            - seed (int or None): The seed value.
            - clean (bool): Whether to clean the generated infrastructure directory.

    Raises:
        SystemExit: If required arguments are missing when --clean is not specified.
    """
    prsr = argparse.ArgumentParser(description='Run experiments')
    prsr.add_argument('--infraDir', type=str, help='Infrastructure directory', default=GENERATED_INFRASTRUCTURE_DIRECTORY)
    prsr.add_argument('--appFile', type=str, help='Application file directory')
    prsr.add_argument('--mode', type=str, choices=['random', 'curated'], help='Mode of operation: rnd (Random/Realistic) or crtd (Curated)')
    prsr.add_argument('--seed', type=int, help='Seed value')
    prsr.add_argument('--clean', action='store_true', help='Clean the testing directory')
    prsr.add_argument('args', type=str, help='String of integers')
    prsdArgs = prsr.parse_args()
    modeEnv = ModeEnv[prsdArgs.mode.upper()]

    if modeEnv == ModeEnv.CURATED and not prsdArgs.appFile:
        prsr.error("The application file (appFile) must be specified to generate the curated environment.")

    args_list = [int(x) for x in prsdArgs.args.split() if x]
    return prsdArgs.appFile, prsdArgs.infraDir, args_list, modeEnv, prsdArgs.seed, prsdArgs.clean


def cleanDirectory(dir: str):
    """Cleans the specified directory by removing all files and subdirectories.

    Args:
        dir (str): The path to the directory to be cleaned.

    Raises:
        Exception: If an error occurs while deleting a file or directory.
    """
    try:
        for fname in os.listdir(dir):
            fpath = os.path.join(dir, fname)
            if os.path.isfile(fpath):
                os.remove(fpath)
            elif os.path.isdir(fpath):
                os.rmdir(fpath)
    except Exception as e:
        print(f"Failed to delete: {fpath}. Reason: {e}")


class Env():
    """Abstract base class for environment generation."""

    def __init__(self, mode: ModeEnv, numNodes: int, infraDirectory: str, appFile: str = None):
        """Initializes the Env class with the specified parameters.

        Args:
            mode (Mode): The mode of generation.
            numNodes (int): Number of nodes.
            infraDirectory (str): The directory to save the generated environment.
            appFile (str, optional): The application file required for the CRTD mode of generation.

        Raises:
            Exception: If CRTD mode is selected and aFile is not provided.
        """
        self._numNodes = numNodes
        self._infraDirectory = infraDirectory
        self._mode = mode
        self._appFile = appFile

    def _generateNodes(self, numNodes: int, nodeT: NodeT, microservice: Microservice = None):
        """Generates nodes and their carbon intensities.

        Args:
            numNodes (int): Number of nodes to generate.
            nodeT (NodeT): The type of node to generate.
            microservice (Microservice, optional): The microservice associated with the node.

        Returns:
            tuple: A tuple containing the generated nodes and their carbon intensities.

        Raises:
            Exception: If the microservice is not provided for FIT nodes.
        """
        if nodeT == NodeT.FIT and microservice is None:
            raise Exception("Microservice must be provided for FIT nodes.")
        nodes, intensities = "", ""
        # --- Generates the node using the FactoryNode and returns the node and its carbon intensity in a prolog syntax form --- #
        for _ in range(numNodes):
            node = FactoryNode.node(nodeT, microservice)
            nodes += f"node('{node.name}', tor({node.ncpu}, {node.ram}, {node.bwin}, {node.bwout}), {node.e}, {node.el}, {node.te}, {node.pue}).\n"
            intensities += f"carbon_intensity('{node.name}', {node.i}).\n"
        return nodes, intensities

    def generate(self):
        """Generates the environment based on the specified mode.

        Returns:
            str: The generated environment.

        Raises:
            Exception: If an invalid mode is specified.
        """
        if self._mode == ModeEnv.RANDOM:
            return RndEnv(self._numNodes, self._infraDirectory).generate()
        elif self._mode == ModeEnv.CURATED:
            return CrtdEnv(self._numNodes, self._infraDirectory, self._appFile).generate()
        else:
            raise Exception("Invalid mode.")


class CrtdEnv(Env):
    """Class for generating a curated environment.

    Inherits from the Env class and generates a curated environment with the specified number of nodes.
    """

    def __init__(self, numNodes: int, infraDirectory:str, appFile: str):
        """Initializes the CrtdEnv class with the specified parameters.

        Args:
            numNodes (int): Number of nodes.
            infraDirectory (str): The directory to save the generated environment.
            appFile (str): The application file required for the CURATED mode of generation.
        """
        super().__init__(ModeEnv.CURATED, numNodes, infraDirectory, appFile)
        self.__optimal = []

    def getOptimal(self) -> List[dict]:
        """Returns the optimal placement of microservices.

        Returns:
            list: A list of dictionaries containing the optimal placement of microservices.
        """
        return self.__optimal

    def generate(self):
        """Generates the curated environment and writes it to the specified file.

        This method resets the node counters of the FactoryNode class, consults the application file, generates the nodes and their carbon intensities,
        creates the infrastructure directory if it doesn't exist, and writes the generated data to the file.

        Raises:
            Exception: If the number of nodes is less than the number of microservices.
        """
        FactoryNode.resetNumNodesS()
        FactoryNode.resetNumNodesT()
        nodes, intensities = "", ""

        msList = []
        with PrologMQI().create_thread() as prolog_thread:
            prolog_thread.query(f"consult('{self._appFile}')")
            msNameList = prolog_thread.query(f"application(A, MS, EPs).")[0]['MS']
            if self._numNodes < len(msNameList):
                print(f"Number of nodes ({self._numNodes}) must be greater than the number of microservices ({len(msNameList)}).")
                sys.exit(1)
            k = self._numNodes - len(msNameList)
            # --- Retrieves the microservices and their respective resource requirements and TiR and appends them to a list --- #
            for msName in msNameList:
                ms = prolog_thread.query(f"microservice({msName}, rr(CPU, RAM, BWIN, BWOUT), TiR).")[0]
                ms = Microservice(msName, ms['CPU'], ms['RAM'], ms['BWIN'], ms['BWOUT'], ms['TiR'])
                msList.append(ms)
            # --- Generates BROKEN and DIRTY nodes and their respective carbon intensities --- #
            for _ in range(int(k / 2)):
                randMs = rnd.choice(msList)
                brokenNode, brokenIntensity = self._generateNodes(1, NodeT.BROKEN, randMs)
                dirtyNode, dirtyIntensity = self._generateNodes(1, NodeT.DIRTY, randMs)
                nodes += dirtyNode + brokenNode
                intensities += dirtyIntensity + brokenIntensity
            # --- Generates the FIT nodes and their respective carbon intensities --- #
            for ms in msList:
                fitNode, fitIntensity = self._generateNodes(1, NodeT.FIT, ms)
                match = re.search(r"node\('([^']+)'", fitNode).group(1)
                # --- Saves the optimal packing solution by appending it to the list --- #
                self.__optimal.append({'Ms': ms.name, 'N': match})
                nodes += fitNode
                intensities += fitIntensity
            if not os.path.exists(infraDirectory):
                os.makedirs(infraDirectory)
            with open(self._infraDirectory + f"/crtd_{self._numNodes}.pl", "w") as file:
                file.write(nodes + intensities)
        print(self.getOptimal())


class RndEnv(Env):
    """Class for generating a realistic random environment.

    Inherits from the Env class and generates a random environment with the specified number of nodes.
    """

    def __init__(self, numNodes: int, infraDirectory:str):
        """Initializes the RndEnv class with the specified parameters.

        Args:
            numNodes (int): Number of nodes.
            infraDirectory (str): The directory to save the generated environment.
        """
        super().__init__(ModeEnv.RANDOM, numNodes, infraDirectory)

    def generate(self):
        """Generates the random environment and writes it to the specified file.

        This method resets the node counters of the class FactoryNode, generates the nodes and their carbon intensities,
        creates the infrastructure directory if it doesn't exist, and writes the generated data to the file.
        """
        FactoryNode.resetNumNodesS()
        FactoryNode.resetNumNodesT()
        nodes, intensities = self._generateNodes(self._numNodes, NodeT.RANDOM)
        if not os.path.exists(infraDirectory):
            os.makedirs(infraDirectory)
        with open(self._infraDirectory + f"/rnd_{self._numNodes}.pl", "w") as file:
            file.write(nodes + intensities)


with PrologMQI() as mqi:
    appDirectory, infraDirectory, nList, mode, seed, clean = getParameters()
    env = None

    if clean:
        cleanDirectory(infraDirectory)
    
    if seed is not None:
        rnd.seed(seed)

    for n in nList:
        env = Env(mode, n, infraDirectory, appDirectory)
        env.generate()
    """
    if mode == ModeEnv.RANDOM:
        infraFileName = infraDirectory + f"rnd_{n}.pl"
        env = RndEnv(n, infraFileName)
    elif mode == ModeEnv.CURATED:
        infraFileName = infraDirectory + f"crtd_{n}.pl"
        env = CrtdEnv(n, infraFileName, appDirectory)
    else:
        raise Exception("Invalid mode.")
    env.generate()
    if mode == ModeEnv.CURATED:
        print(env.getOptimal())
    """
