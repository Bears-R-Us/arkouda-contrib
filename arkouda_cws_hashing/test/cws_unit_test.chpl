use CTypes;
require '-lgsl','-lgslcblas';


extern {
#include "gsl/gsl_rng.h"
#include "gsl/gsl_randist.h"
}


proc cantorPairing(setEltIdx: int, hashIdx: int): real {

    var sum = setEltIdx + hashIdx;

    var result = 0.5 * sum * (sum + 1) + hashIdx;

    return result;
}


var offsets: [0..9] int(64) = [0, 3, 10, 15, 27, 31, 38, 40, 44, 49];
var setElts: [0..49] int(64) = [3, 4, 1, 3, 7, 8, 2, 1, 8, 4, 2, 5, 6, 9, 2, 5, 3, 2, 8, 8, 9, 1, 5, 3, 9, 3, 3, 3, 1, 8, 1, 6, 9, 9, 8, 7, 3, 5, 1, 1, 3, 8, 8, 6, 4, 6, 5, 1, 7, 1];
var weights: [0..49] real(64) = [0.333333, 0.25, 1.0, 0.333333, 0.142857, 0.125, 0.5, 1.0, 0.125, 0.25, 0.5, 0.2, 0.166667, 0.111111, 0.5, 0.2, 0.333333, 0.5, 0.125, 0.125, 0.111111, 1.0, 0.2, 0.333333, 0.111111, 0.333333, 0.333333, 0.333333, 1.0, 0.125, 1.0, 0.166667, 0.111111, 0.111111, 0.125, 0.142857, 0.333333, 0.2, 1.0, 1.0, 0.333333, 0.125, 0.125, 0.166667, 0.25, 0.166667, 0.2, 1.0, 0.142857, 1.0];


var numHashes: int = 3; 

var preimages: [0..29] int;
var minHashes: [0..29] real;

var setIds: [offsets.domain] int;
var setSizes: [offsets.domain] int;

const maxIdx = offsets.domain.high;

forall (i, o, s, l) in zip(offsets.domain, offsets, setIds, setSizes) {

  if i == maxIdx {
      l = setElts.size - o;
  } else {
      l = offsets[i+1] - o;  
  }

  s = i;
}


forall (o, s, l) in zip(offsets, setIds, setSizes) {

    for hashIdx in 0..numHashes-1 {

        var outIdx = s*numHashes + hashIdx;

        var u_z, g_1, g_2, t_z, y_z, a_z = 0.0;

        var min_az: real = 0xffffffffffffffff: real;
        var min_tz: real = 0xffffffffffffffff: real;

        var r = gsl_rng_alloc (gsl_rng_mt19937);

	for z in o..#l {

            var seedIdx: uint = cantorPairing(setElts[z], hashIdx): uint;

            gsl_rng_set(r, seedIdx);

            u_z = gsl_rng_uniform(r);
            g_1 = gsl_ran_gamma(r, 2.0, 1.0);
            g_2  = gsl_ran_gamma(r, 2.0, 1.0);

            t_z = floor((log(weights[z]) / g_1) + u_z);
            y_z = exp(g_1 * (t_z - u_z));
            a_z = (g_2 / (y_z * exp(g_1)));

            if a_z < min_az then {
                min_az = a_z;
                min_tz = t_z;
                preimages[outIdx] = setElts[z];
                minHashes[outIdx] = t_z;
            }

        } // end loop over current set elements

//        writeln("Index: ", outIdx, ", Set: ", s, ", Hash: ", hashIdx, ", Preimage: ", preimages[outIdx], ", Minhash: ", minHashes[outIdx]);

    } // end loop over hashes

} // end loop over current set

for i in preimages.domain.first..preimages.domain.last {
  writeln("Index: ", i, ", Preimage: ", preimages[i], ", MinHash: ", minHashes[i]);
}
