include "/usr/local/lib/node_modules/circomlib/circuits/comparators.circom";

template uniqueArray(n) {
	signal input in[n];
	signal output out;

	var acc = 0;
	var i = 0;
	var j = 0;
	while(i <= n-1) {
		while(j <= n-1) {
			if(i == j) {
				acc += 1;
			}
			else {
				var eq1 = IsEqual()([in[i], in[j]]);
				var eq2 = IsEqual()([in[i+1], in[j+1]]);
				acc += 1 - eq1 - eq2;
			}
			j += 2;
 		}
		i += 2;
		j = 0;
	}
	acc === (n/2) * ((n/2) - 1) / 2;
	out <== acc;
}
