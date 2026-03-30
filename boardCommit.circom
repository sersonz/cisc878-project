pragma circom 2.2.3;
include "/usr/local/lib/node_modules/circomlib/circuits/pedersen.circom";

template BoardCommit() {
    signal input coords[10][10];
    signal input blindingVal;
    signal output commitment;
    var bit = 0;
    component pedersen = Pedersen(2);
    for (var i = 0; i < 10; i++) {
    	for (var j = 0; j < 10; j++) {
    		var expand = 2 ** ((10 * i) + j);
    		bit += (coords[i][j] * expand);
    	}
    }
    pedersen.in[0] <== bit;
    pedersen.in[1] <== blindingVal;
    commitment <== pedersen.out[1];
}

component main = BoardCommit();
