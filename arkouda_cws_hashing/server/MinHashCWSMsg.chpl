module MinHashCWSMsg
{

  use CTypes;
  use ServerConfig;
  use MultiTypeSymEntry;
  use ServerErrorStrings;
  use MultiTypeSymbolTable;

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


  proc cantorPairing(setEltIdx: uint(64), hashIdx: uint(8)): uint(64): uint(64) {

    var hashIdx64: uint(64) = hashIdx: uint(64);

    var sum: uint(64) = setEltIdx + hashIdx64;

    var result: uint(64) = (0.5 * sum * (sum + 1)) + hashIdx64;

    return result;
  }


  proc getMinHash(S: [?S_Dom] uint(64), hashIdx: uint(8)): (uint(64), real(64)) {

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

    // Loop over hashes
    for s in S {

        /* Create a unique, but globally consistent, seed for the 
           RNG by concatenating the set and the hash indices */

        var seedIdx: uint(64) = cantorPairing(s, hashIdx);

        gsl_rng_set(r, seedIdx);

        u_z = gsl_rng_uniform(r);
        g_1 = gsl_ran_gamma(r, 2.0, 1.0);
        g_2  = gsl_ran_gamma(r, 2.0, 1.0);

        t_z = floor((log(u_z+1) / g_1) + u_z);
        y_z = exp(g_1 * (t_z - u_z));
        a_z = (g_2 / (y_z * exp(g_1)));

        if a_z < min_az then
            min_az = a_z;
            min_tz = t_z;
            preimage = s;
      }

    // Return the preimage of the MinHash and t_z
    return (preimage, min_tz);
  }


  /* Returns the "zero bit" version of the hash that omits t_z */

  proc getMinHash_ZBit(S: [?S_Dom] uint(64), hashIdx: uint(8)): uint(64) {

    var u_z: real(64) = 0.0;
    var g_1: real(64) = 0.0;
    var g_2: real(64) = 0.0;

    var t_z: real(64) = 0.0;
    var y_z: real(64) = 0.0;
    var a_z: real(64) = 0.0;

    var min_az: real(64) = 0xffffffffffffffff: real(64);

    var preimage: uint(64) = 0;

    var r = gsl_rng_alloc (gsl_rng_mt19937);

    // Loop over hashes
    for s in S {

        /* Create a unique, but globally consistent, seed for the 
           RNG by concatenating the set and the hash indices */

        var seedIdx: uint(64) = cantorPairing(s, hashIdx);

        gsl_rng_set(r, seedIdx);

        u_z = gsl_rng_uniform(r);
        g_1 = gsl_ran_gamma(r, 2.0, 1.0);
        g_2  = gsl_ran_gamma(r, 2.0, 1.0);

        t_z = floor((log(u_z+1) / g_1) + u_z);
        y_z = exp(g_1 * (t_z - u_z));
        a_z = (g_2 / (y_z * exp(g_1)));

        if a_z < min_az then
            min_az = a_z;
            preimage = s;
      }

    // Return the preimage of the MinHash only
    return preimage;
  }


  proc getSamples(A: [?A_Dom] uint(64), numHashes: uint(8), zbit: bool): [A_Dom] uint(64), [A_Dom] real(64) {

    // Outer loop over hash indices
        // Inner loop over sets
            // Call either GetMinHash() 
  }


  proc getSamples_ZBit(A: [?A_Dom] uint(64), numHashes: uint(8), zbit: bool): [A_Dom] uint(64) {

    // Outer loop over hash indices
        // Inner loop over sets
            // Call either GetMinHash_ZBit()
  }


  //TODO: add knn lookup and survivor pairing/scoring routines


  /*
  Parse, execute, and respond to a foo message
  :arg payload: request containing (cmd,dtype,size)
  :type reqMsg: string
  :arg st: SymTab to act on
  :type st: borrowed SymTab
  :returns: (string) response message
  */

  proc MinHashCWSMsg(payload: string, st: borrowed SymTab): string throws {

    var repMsg: string; // response message

    // split request into fields
    var (cmd, name, numHashes, zbit) = payload.splitMsgToTuple(4);

    var zBit = zbit: bool;

    var numHashes = numHashes: uint(8);

    // get next symbol name
    var rname = st.nextName();

    var gEnt: borrowed GenSymEntry = st.lookup(name);

    if (gEnt == nil) {return unknownSymbolError("set",name);}

    // if verbose print action
    if v {try! writeln("%s %s: %s".format(cmd,name,rname)); try! stdout.flush();}

    select (gEnt.dtype) {

        when (DType.uint64) {

                if(zBit) {

                  var e = toSymEntry(gEnt,int);

                  var ret = generateSamples_ZBit(e.a, numHashes, zBit);

                  st.addEntry(rname, new shared SymEntry(ret));

                } else {

                    var e = toSymEntry(gEnt,int);

                    var ret = generateSamples(e.a, numHashes, zBit);

                    st.addEntry(rname, new shared SymEntry(ret));
                }
        }
        otherwise {return notImplementedError("generateSamples",gEnt.dtype);}
    }

    // response message
    return try! "created " + st.attrib(rname);
  }


  proc registerMe() {
    use CommandMap;
    registerFunction("generateSamples", MinHashCWSMsg);
  }
}
