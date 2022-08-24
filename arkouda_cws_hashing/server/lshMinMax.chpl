module lshMinMax
{

  use CTypes;
  use ServerConfig;
  use MultiTypeSymEntry;
  use ServerErrorStrings;
  use MultiTypeSymbolTable;
  use Message;
  use Reflection;
  use ServerErrors;
  use Logging;

  require '-lgsl','-lgslcblas';

  extern {
    #include "gsl/gsl_rng.h"
    #include "gsl/gsl_randist.h"
  }


  // TODO: adapt 3D grid from 2.5D communication-avoiding matmul
  // of Demmel and Solomonik to load-balance pair construction
  // among LSH survivors analogous to Burkhardt's Toeplitz
  // load-balancing strategy for all-pairs exact Jaccard similarity?
  // Note that this was developed for dense matrices, and the
  // LSH survivor output is likely to be sparse


  proc cantorPairing(setEltIdx: uint(64), hashIdx: uint(64)): uint(64) {

      var sum: uint(64) = setEltIdx + hashIdx;

      var result: uint(64) = (0.5 * sum * (sum + 1)) + hashIdx;

      return result;
  }


  /* Returns a tuple consisting of aligned arrays of length numHashes*numSets containing 
     sampled set elements and hashes */

  proc getMinHashes(offsets: [?oD] uint(64), setElts: [?sD] uint(64), 
                    weights: [sD] real(64), numHashes: uint(64)) throws {

/* TODO: return domain is wrong! Must be expanded by the number of hashes per set element */

      var outD: domain(1) = {oD.first..numHashes*oD.last};


/* TODO: define segments of these locally within the innermost loop, then assemble them into
         the global output vectors later to avoid unnecessary communication over the network */

      var preimages: [outD] uint(64);
      var minHashes: [outD] real(64);

      /* CSR-style loop over a segmented array. Outer loop is data parallel. */

      forall offsetIdx in offsets {

          /* Loop over hashes. Should be serial as parallel span is minimal */

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


              /* Loop over set elements. Should be serial in most cases, but might
                 benefit from parallelism for skewed distributions, e.g. such as
                 adjacency lists of "power-law" graphs */

              forall z in setElts[offsetIdx..offsetIdx+1] {

                  /* Create a unique, but globally consistent, seed for the
                     RNG by concatenating the set and the hash indices */

                  var seedIdx: uint(64) = cantorPairing(z, hashIdx);

                  gsl_rng_set(r, seedIdx);

                  u_z = gsl_rng_uniform(r);
                  g_1 = gsl_ran_gamma(r, 2.0, 1.0);
                  g_2  = gsl_ran_gamma(r, 2.0, 1.0);

                  t_z = floor((log(weights[z]) / g_1) + u_z);
                  y_z = exp(g_1 * (t_z - u_z));
                  a_z = (g_2 / (y_z * exp(g_1)));

/* TODO: replace accesses to preimages and minHashes with local segments that will be 
         read into the global output vectors (preimages and minHashes) later */
 
                  if a_z < min_az then {
                      min_az = a_z;
                      min_tz = t_z;
                      preimages[outIdx] = setElts[z];
                      minHashes[outIdx] = t_z;
                  }

              } // end loop over current set 

          } // end loop over hashes

/* TODO: read local output into global output vectors (primages and minHashes) */

      } // end loop over set offsets

      // Return the preimage of the MinHash and t_z
      return (preimages, minHashes);
  }

}
