pragma circom 2.1.6;

include "/usr/local/lib/node_modules/circomlib/circuits/pedersen.circom";
include "/usr/local/lib/node_modules/circomlib/circuits/comparators.circom";

template BoardValidator () {
	signal input ships[5][4];
	var shipLengths[5] = [5, 4, 3, 3, 2];
	
	// Valid position check
	for (var ship = 0; ship < 5; ship++) {
		assert(
			(
				(ships[ship][0] - ships[ship][2] == shipLengths[ship] - 1 || ships[ship][2] - ships[ship][0] == shipLengths[ship] - 1) && (ships[ship][1] == ships[ship][3])
			) ||
			(
				(ships[ship][1] - ships[ship][3] == shipLengths[ship] - 1 || ships[ship][3] - ships[ship][1] == shipLengths[ship] - 1) && (ships[ship][0] == ships[ship][2])
			)
		);
	}
	
	// Non-overlapping check
	var var_ships[5][4];
	var coords[10][10];
	for(var ship = 0; ship < 5; ship++) {
		var_ships[ship][0] = ships[ship][0];
		var_ships[ship][1] = ships[ship][1];
		var_ships[ship][2] = ships[ship][2];
		var_ships[ship][3] = ships[ship][3];
	}
	for (var ship = 0; ship < 5; ship++) {
		if(var_ships[ship][0] == var_ships[ship][2]) {
			for (var y = var_ships[ship][1]; y <= var_ships[ship][3]; y++) {
				coords[var_ships[ship][0]][y] = 1;
			}
		}
		else {
			for (var x = var_ships[ship][0]; x <= var_ships[ship][2]; x++) {
				coords[x][ships[ship][0]] = 1;
			}
		}
	}
	
	var tmp = 0;
	for (var x = 0; x < 10; x++) {
		for (var y = 0; y < 10; y++) {
			tmp += coords[x][y];
		}
	}
	assert(tmp == 17);
}

component main { public [ ships ] } = BoardValidator();
