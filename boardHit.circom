pragma circom 2.2.3;

include "/usr/local/lib/node_modules/circomlib/circuits/comparators.circom";
include "/usr/local/lib/node_modules/circomlib/circuits/multiplexer.circom";
include "boardCommit_validate.circom";

template Constrainer() {
	signal input i1;
	signal output out;
	component geq = GreaterEqThan(32);
	geq.in[0] <== i1;
	geq.in[1] <== 1;
	out <== geq.out;
}

template BoardHit () {
	signal input coords[10][10];
	signal input blinding;
	signal input hash;
	signal input x;
	signal input y;
	signal input declaredHit;
	component muplexer = Multiplexer(1, 100);
	component constrainer[100];
	for(var i = 0; i < 10; i++) {
		for(var j = 0; j < 10; j++) {
			constrainer[(i * 10) + j] = Constrainer();
			constrainer[(i * 10) + j].i1 <== coords[i][j];
			muplexer.inp[(i * 10) + j][0] <== constrainer[(i * 10) + j].out;
		}
	}
	muplexer.sel <== (x * 10) + y;
	declaredHit === muplexer.out[0];
	component boardCommit = BoardCommit();
	boardCommit.blindingVal <== blinding;
	boardCommit.coords <== coords;
	hash === boardCommit.commitment;
}

component main { public [ hash, x, y, declaredHit ] } = BoardHit();
