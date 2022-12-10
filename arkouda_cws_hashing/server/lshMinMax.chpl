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


  class cwsReduceOp: ReduceScanOp {

      type eltType;

      var value: eltType;

      proc identity {
	  if eltType == (real, int, real) then return (max(real), 0, 0.0);
      }

      proc accumulate(x: eltType) {
	  const (a_z, s_z, t_z) = x;
          const (min_az, min_sz, min_tz) = value;

	  if a_z < min_az {
              value = (a_z, s_z, t_z);
          }
      }

      proc accumulateOntoState(ref state, x: eltType) {
          const (a_z, s_z, t_z) = x;
	  const (min_az, min_sz, min_tz) = state;

	  if a_z < min_az {
              state = (a_z, s_z, t_z);
	  }
      }

      proc combine(s: borrowed cwsReduceOp(eltType)) {
          accumulate(s.value);
      }

      proc generate() {
          return value;
      }

      proc clone() {
          return new unmanaged cwsReduceOp(eltType=eltType);
      }
  }


  proc cantorPairing(setEltIdx: int, hashIdx: int): real {

      var sum = setEltIdx + hashIdx;

      var result = (0.5 * sum * (sum + 1)) + hashIdx;

      return result;
  }



  proc getMinHashes(offsets: [?oD] int, setElts: [?sD] int,
                    weights: [sD] real, numHashes: int) throws {

      var outD: domain(1) = {oD.first..numHashes*oD.last-1};

      var preimages: [outD] int;
      var minHashes: [outD] real;

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


      /* CSR-style loop over a segmented array. Outer loop is data parallel. */

      forall (o, s, l) in zip(offsets, setIds, setSizes) {

          coforall hashIdx in 0..numHashes-1 {

              var outIdx = s*numHashes + hashIdx;

	      var r = gsl_rng_alloc (gsl_rng_mt19937);

              /* Loop over set elements. Should be serial in most cases, but might
                 benefit from parallelism for skewed distributions, e.g. such as
                 adjacency lists of "power-law" graphs */

	      var setD: domain = {o..#l};
              var hashes: [setD] (real, int, real);

	      forall z in setD {

		  var u_z, g_1, g_2, t_z, y_z, a_z = 0.0;

                  /* Create a unique, but globally consistent, seed for the
                     RNG by concatenating the set and the hash indices */

                  var seedIdx: uint = cantorPairing(setElts[z], hashIdx): uint;

                  gsl_rng_set(r, seedIdx);

                  u_z = gsl_rng_uniform(r);
                  g_1 = gsl_ran_gamma(r, 2.0, 1.0);
                  g_2  = gsl_ran_gamma(r, 2.0, 1.0);

                  t_z = floor((log(weights[z]) / g_1) + u_z);
                  y_z = exp(g_1 * (t_z - u_z));
                  a_z = (g_2 / (y_z * exp(g_1)));

		  hashes[z] = (a_z, setElts[z], t_z);

              } // end loop over current set 

	      var cwsMinHash: (real, int, real); 
	      cwsMinHash = cwsReduceOp reduce hashes;

	      preimages[outIdx] = cwsMinHash(1);
	      minHashes[outIdx] = cwsMinHash(2);

          } // end loop over hashes

      } // end loop over set offsets

      // Return the preimage of the MinHash and t_z
      return (preimages, minHashes);
  }

}
