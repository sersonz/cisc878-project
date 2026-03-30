import math
from zkpy.ptau import PTau
from zkpy.circuit import Circuit, GROTH, PLONK, FFLONK
import json
import os
import secrets
import subprocess
from utils import log, warn

SHIPS = { "carrier": { "size": 5,  "num": 1, "letter": "C" }, "battleship": { "size": 4, "num": 2, "letter": "B" }, "cruiser": { "size": 3, "num": 3, "letter": "R" }, "submarine": { "size": 3, "num": 4, "letter": "S" }, "destroyer": { "size": 2, "num": 5, "letter": "D" } }

class BattleshipGame:

    def __init__(self, player1_file=None, player2_file=None):
        self.player_hits = [[[False, False, False, False, False, False, False, False, False, False] for i in range(10)] for j in range(2)]
        self.player_validated = [False for i in range(2)]
        self.player_hash = [0 for i in range(2)]
        self.ptau_ready = False
        if player1_file != None:
            log(self.__class__.__name__, "Input files provided, loading those instead of asking players for board state")
            with open(player1_file, "r") as p1, open(player2_file, "r") as p2:
                player1 = json.load(p1)
                player2 = json.load(p2)
            self.player_coords = [player1["coords"], player2["coords"]]
            self.player_blinding = [player1["blinding"], player2["blinding"]]
            self.setupPtau()
            self.validatePlayer(1)
            self.validatePlayer(2)
            self.doGame()
        else:
            self.player_coords = [[[0, 0, 0, 0, 0, 0, 0, 0, 0, 0] for i in range(10)] for j in range(2)]
            self.player_blinding = [secrets.randbits(212) for i in range(2)]
            self.prepareGame(1)
            self.prepareGame(2)
            self.doGame()
        
        
    def putShipAtCoords(self, player, x1, y1, x2, y2, shipType):
        if player != 1 and player != 2:
            raise ValueError("Invalid player number " + str(player) + "(valid options: 1, 2)")
        if shipType not in SHIPS.keys():
            raise ValueError("Invalid ship type " + str(shipType) + "(valid options: carrier, battleship, cruiser, submarine, destroyer)")
        x_coords = [x1 + math.ceil(i*(x2-x1)/SHIPS[shipType]["size"]) for i in range(SHIPS[shipType]["size"])]
        y_coords = [y1 + math.ceil(i*(y2-y1)/SHIPS[shipType]["size"]) for i in range(SHIPS[shipType]["size"])]
        for i in range(SHIPS[shipType]["size"]):
            self.player_coords[player-1][x_coords[i]][y_coords[i]] = SHIPS[shipType]["num"]
                    
    def renderPlayerGrid(self, player, gridType):
        string = "  0123456789\n"
        helpString = "X: Empty\n"
        if player != 1 and player != 2:
            raise ValueError("Invalid player number " + str(player) + "(valid options: 1, 2)")
        match gridType:
            case "prepare":
                numbers_to_letters = ["X"] + [SHIPS[ship]["letter"] for ship in SHIPS.keys()]
                for i in range(10):
                    string += str(i) + " "
                    for j in range(10):
                        string += numbers_to_letters[self.player_coords[player-1][i][j]]
                    string += "\n"
                string += "\n"
                for ship in SHIPS.keys():
                    string += SHIPS[ship]["letter"] + ": " + ship + "\n"
                string += "\n"
                string += "Blinding factor: " + str(self.player_blinding[player-1]) + "\n"
                return string
            case "guess":
                for i in range(10):
                    string += str(i) + " "
                    for j in range(10):
                        match self.player_hits[player-1][i][j]:
                            case 0:
                                string += "X"
                            case 1:
                                string += "H"
                            case -1:
                                string += "M"
                    string += "\n"
                string += "\n"
                string += "X: Unknown\nH: Hit\nM: Miss\n"
                return string;
        
    def setupPtau(self):
        if self.ptau_ready:
            warnings.warn(self.__class__.__name__, "setupPtau called but ptau is already ready")
        log(self.__class__.__name__, "Preparing ptau")
        self.ptau = PTau(working_dir=os.getcwd() + "/tmp", ptau_file=os.getcwd() + "/tmp/game.ptau")
        self.ptau.start(constraints="14")
        self.ptau.contribute()
        self.ptau.beacon()
        self.ptau.prep_phase2()
        self.ptau.verify()
        log(self.__class__.__name__, "Ptau ready")
        self.ptau_ready = True
        
    def validatePlayer(self, player):
        # Create a master player input file
        # This contains the blinding factor and would thus normally be hidden,
        # but it's easier to visualize how the circuits interact if it's public
        if not self.ptau_ready:
            self.setupPtau()
        with open(os.getcwd() + "/tmp/board_" + str(player) + ".json", "w") as player_board_file:
            player_board = {"coords": self.player_coords[player-1], "blinding": self.player_blinding[player-1]}
            json.dump(player_board, player_board_file)
            with open(os.getcwd() + "/tmp/commit_board_player_" + str(player) + "_input.json", "w") as file2:
                del player_board["blinding"]
                player_board["blindingVal"] = self.player_blinding[player-1]
                json.dump(player_board, file2)
        committer = Circuit("./boardCommit.circom")
        committer.compile()
        committer.gen_witness(os.getcwd() + "/tmp/commit_board_player_" + str(player) + "_input.json", output_file=os.getcwd() + "/witness/commit_board_player_" + str(player) + "_witness.wtns")
        committer.setup(PLONK, self.ptau, output_file = os.getcwd() + "/zkey/commit_board_player_" + str(player) + "_zkey.zkey")
        committer.prove(PLONK, proof_out=os.getcwd() + "/proof/commit_board_player_" + str(player) + "_proof.json", public_out=os.getcwd() + "/public/commit_board_player_" + str(player) + "_public.json")
        committer.export_vkey(output_file=os.getcwd() + "/keys/commit_board_player_" + str(player) + "_vkey.json")
        committer.verify(PLONK, vkey_file=os.getcwd() + "/keys/commit_board_player_" + str(player) + "_vkey.json", public_file=os.getcwd() + "/public/commit_board_player_" + str(player) + "_public.json", proof_file=os.getcwd() + "/proof/commit_board_player_" + str(player) +"_proof.json")
        with open(os.getcwd() + "/tmp/validate_board_player_" + str(player) + "_input.json", "w") as validate_file:
            player_board = {"coords": self.player_coords[player-1], "blinding": self.player_blinding[player-1]}
            subprocess.run(["snarkjs", "wtns", "export", "json", os.getcwd() + "/witness/commit_board_player_" + str(player) + "_witness.wtns", os.getcwd() + "/tmp/commit_board_player_" + str(player) + "_witness.json"])
            with open(os.getcwd() + "/tmp/commit_board_player_" + str(player) + "_witness.json", "r") as tmp:
                tmp2 = json.load(tmp)
                player_board["hash"] = tmp2[1]
                self.player_hash[player-1] = tmp2[1]
            json.dump(player_board, validate_file)
        validator = Circuit("./boardValidate.circom")
        validator.compile()
        validator.gen_witness(os.getcwd() + "/tmp/validate_board_player_" + str(player) + "_input.json", output_file=os.getcwd() + "/witness/validate_board_player_" + str(player) + "_witness.wtns")
        validator.setup(PLONK, self.ptau)
        validator.prove(PLONK, proof_out=os.getcwd() + "/proof/validate_board_player_" + str(player) + "_proof.json", public_out=os.getcwd() + "/public/validate_board_player_" + str(player) + "_public.json")
        validator.export_vkey(output_file=os.getcwd() + "/keys/validate_board_player_" + str(player) + "_vkey.json")
        validator.verify(PLONK, vkey_file=os.getcwd() + "/keys/validate_board_player_" + str(player) + "_vkey.json", public_file=os.getcwd() + "/public/validate_board_player_" + str(player) + "_public.json", proof_file=os.getcwd() + "/proof/validate_board_player_" + str(player) +"_proof.json")
        log(self.__class__.__name__, "Player " + str(player) + " now ready")
        
    def prepareGame(self, player):
        while not self.player_validated[player-1]:
            print("PLAYER " + str(player) + " BOARD PREPARATION\n")
            print(self.renderPlayerGrid(player, "prepare"))
            print("To place a ship, enter ship x1 y1 x2 y2 where ship is one of [" + ", ".join(SHIPS.keys()) + "],  x1, y1 are the start column and row and x2, y2 are the end column and row")
            print("To change blinding factor, enter blinding num where num is a positive integer or enter -1 to generate a random blinding factor")
            print("To clear board and start over, enter clear")
            print("To preset a sample board, enter debug-preset")
            print("To submit for validation, enter submit")
            args = input("Command: ").split(" ")
            match args[0]:
                case _ if args[0] in SHIPS.keys():
                    ship = str(args[0])
                    x1, y1, x2, y2 = [int(x) for x in args[1:]]
                    # Invert the x and y coordinates for the sake of intuitiveness
                    # TODO: fix this to properly be column major order like OTB
                    self.putShipAtCoords(player, y1, x1, y2, x2, ship)
                case "blinding":
                    num = args[1]
                    if int(num) == -1:
                        self.player_blinding[player-1] = secrets.randbits(212)
                    else:
                        self.player_blinding[player-1] = int(num)
                case "clear":
                    self.player_coords[player-1] = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0] for i in range(10)]
                case "debug-preset":
                    self.putShipAtCoords(player, 0, 0, 4, 0, "carrier")
                    self.putShipAtCoords(player, 0, 1, 3, 1, "battleship")
                    self.putShipAtCoords(player, 0, 2, 2, 2, "cruiser")
                    self.putShipAtCoords(player, 0, 3, 2, 3, "submarine")
                    self.putShipAtCoords(player, 0, 4, 1, 4, "destroyer")
                case "submit":
                    try:
                        self.validatePlayer(player)
                        self.player_validated[player-1] = True
                        print("Player " + str(player) + " is now ready")
                    except Exception as e:
                        print("Board was not validated successfully. Either your board is not legal, or another error has occurred.")
                        print(e)
                        
    def doGame(self):
        player_hit_count = [0, 0]
        curPlayer = 1
        f_oppPlayer = lambda x: 2 if x==1 else 1
        while 17 not in player_hit_count:
            print("PLAYER " + str(curPlayer) + "'S TURN")
            print(self.renderPlayerGrid(curPlayer, "guess"))
            args = input("Enter coordinate column row to target: ").split(" ")
            x = int(args[0])
            y = int(args[1])
            correctDeclare = False
            while not correctDeclare:
                print("PLAYER " + str(f_oppPlayer(curPlayer)) + "'S BOARD")
                print(self.renderPlayerGrid(f_oppPlayer(curPlayer), "prepare"))
                print("Opponent targets " + str(x) + ", " + str(y))
                res = input("Enter Y to declare hit, enter N to declare miss: ")
                input_file = {"coords": self.player_coords[f_oppPlayer(curPlayer) - 1], "blinding": self.player_blinding[f_oppPlayer(curPlayer) - 1], "hash": self.player_hash[f_oppPlayer(curPlayer) - 1], "x": x, "y": y}
                match res:
                    case "Y":
                        input_file["declaredHit"] = 1
                    case "N":
                        input_file["declaredHit"] = 0
                with open(os.getcwd() + "/tmp/board_player_" + str(f_oppPlayer(curPlayer)) + "_hit_input.json", "w") as file:
                    json.dump(input_file, file)
                try:
                    validator = Circuit("./boardHit.circom")
                    validator.compile()
                    validator.gen_witness(os.getcwd() + "/tmp/board_player_" + str(f_oppPlayer(curPlayer)) + "_hit_input.json", output_file=os.getcwd() + "/witness/board_player_" + str(f_oppPlayer(curPlayer)) + "_hit_witness.wtns")
                    validator.setup(PLONK, self.ptau)
                    validator.prove(PLONK, proof_out=os.getcwd() + "/proof/validate_board_player_" + str(f_oppPlayer(curPlayer)) + "_hit_proof.json", public_out=os.getcwd() + "/public/validate_board_player_" + str(f_oppPlayer(curPlayer)) + "_hit_public.json")
                    validator.export_vkey(output_file=os.getcwd() + "/keys/validate_board_player_" + str(f_oppPlayer(curPlayer)) + "_hit_vkey.json")
                    validator.verify(PLONK, vkey_file=os.getcwd() + "/keys/validate_board_player_" + str(f_oppPlayer(curPlayer)) + "_hit_vkey.json", public_file=os.getcwd() + "/public/validate_board_player_" + str(f_oppPlayer(curPlayer)) + "_hit_public.json", proof_file=os.getcwd() + "/proof/validate_board_player_" + str(f_oppPlayer(curPlayer)) +"_hit_proof.json") 
                    correctDeclare = True
                    # For simplicity's sake, we'll just read from the player coords array
                    # This interface is a PoI for the circuits anyway;
                    # in practice you'd want to read from the validate_board_player_$curPlayer_hit_public file
                    if self.player_coords[f_oppPlayer(curPlayer)-1][x][y] != 0:
                        self.player_hits[curPlayer-1][x][y] = True
                        player_hit_count[curPlayer-1] += 1
                    else:
                        self.player_hits[curPlayer-1][x][y] = False
                    curPlayer = f_oppPlayer(curPlayer)
                except Exception as e:
                    print("Hit validator did not accept declaration. Either you tried to lie, or another error occurred.")
                    print(e)
        if player_hit_count[0] == 17:
            print("Player 1 wins")
        else:
            print("Player 2 wins")
