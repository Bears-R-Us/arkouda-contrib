use CTypes;
require '-lgsl','-lgslcblas';

extern {
#include "gsl/gsl_rng.h"
#include "gsl/gsl_randist.h"
}



proc cantorPairing(setEltIdx: uint(64), hashIdx: uint(64)): uint(64) {

    var sum: uint(64) = setEltIdx + hashIdx;

    var result: uint(64) = (0.5 * sum * (sum + 1)) + hashIdx;

    return result;
}


var offsetD: domain(1) = {0..10};
var seteltD: domain(1) = {0..49};

var offsets: [offsetD] uint(64) = [0, 3, 10, 15, 27, 31, 38, 40, 44, 49, 50];
var setElts: [seteltD] uint(64) = [3, 4, 1, 3, 7, 8, 2, 1, 8, 4, 2, 5, 6, 9, 2, 5, 3, 2, 8, 8, 9, 1, 5, 3, 9, 3, 3, 3, 1, 8, 1, 6, 9, 9, 8, 7, 3, 5, 1, 1, 3, 8, 8, 6, 4, 6, 5, 1, 7, 1];
var numHashes: uint(64) = 5; 


var outD: domain(1) = {offsetD.first..numHashes*offsetD.last};

var preimages: [outD] uint(64);
var minHashes: [outD] real(64);


forall offsetIdx in offsets {

    for hashIdx in [0..numHashes-1] {
  
        var outIdx: uint(64) = offsetIdx*numHashes + hashIdx;

        var u_z: real(64) = 0.0;
        var g_1: real(64) = 0.0;
        var g_2: real(64) = 0.0;

        var t_z: real(64) = 0.0;
        var y_z: real(64) = 0.0;
        var a_z: real(64) = 0.0;

        var min_az: real(64) = 0xffffffffffffffff: real(64);
        var min_tz: real(64) = 0xffffffffffffffff: real(64);

        var preimage: uint(64) = 0;

        var r = gsl_rng_alloc (gsl_rng_mt19937);

        forall z in setElts[offsetIdx..offsetIdx+1] {

            var weight: real(64) = 1/z; 

            var seedIdx: uint(64) = cantorPairing(z, hashIdx);

            gsl_rng_set(r, seedIdx);

            u_z = gsl_rng_uniform(r);
            g_1 = gsl_ran_gamma(r, 2.0, 1.0);
            g_2  = gsl_ran_gamma(r, 2.0, 1.0);

            t_z = floor((log(weight) / g_1) + u_z);
            y_z = exp(g_1 * (t_z - u_z));
            a_z = (g_2 / (y_z * exp(g_1)));

            if a_z < min_az then {
                min_az = a_z;
                min_tz = t_z;
                preimages[outIdx] = setElts[z];
                minHashes[outIdx] = t_z;
            }

            writeln(z);

        } // end loop over current set

    } // end loop over hashes

} // end loop over set offset
