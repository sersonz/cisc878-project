pragma circom 2.2.3;

include "/usr/local/lib/node_modules/circomlib/circuits/comparators.circom";
include "boardCommit_validate.circom";

template BoardValidator () {
	signal input coords[10][10];
	signal input blinding;
	signal input hash;
	signal numOfShipPositions[5];
	var posFound[5] = [0, 0, 0, 0, 0];
	component equals[500];
	for(var ship = 0; ship < 5; ship++) {
		for(var i = 0; i < 10; i++) {
			for(var j = 0; j < 10; j++) {
				equals[(ship * 100) + (10 * i) + j] = IsEqual();
				equals[(ship * 100) + (10 * i) + j].in[0] <== coords[i][j];
				equals[(ship * 100) + (10 * i) + j].in[1] <== ship + 1;
				posFound[ship] += equals[(ship * 100) + (10 * i) + j].out;
			}
		}
		numOfShipPositions[ship] <== posFound[ship];
	}
	numOfShipPositions[0] === 5;
	numOfShipPositions[1] === 4;
	numOfShipPositions[2] === 3;
	numOfShipPositions[3] === 3;
	numOfShipPositions[4] === 2;
	component boardCommit = BoardCommit();
	boardCommit.blindingVal <== blinding;
	boardCommit.coords <== coords;
	hash === boardCommit.commitment;
}

component main { public [ hash ] } = BoardValidator();

