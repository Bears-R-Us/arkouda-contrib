
extern {
#include "gsl/gsl_rng.h"
#include "gsl/gsl_randist.h"
#include "gsl/gsl_cdf.h"
}

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


  // Applied to each individual set in a collection of sets
   
  proc GetMinHash(S: [?S_Dom] uint(64)): [S_Dom] uint(64) {

    var u_z: real(64) = 0.0;
    var g_1: real(64) = 0.0;
    var g_2: real(64) = 0.0;

    var t_z: real(64) = 0.0;
    var y_z: real(64) = 0.0;
    var a_z: real(64) = 0.0;

    var min_a_z: real(64) = 0xffffffffffffffff: real(64);

    var r = gsl_rng_alloc (gsl_rng_taus2);

    // Loop over hashes
    for idx  {
        gsl_rng_set(r, idx: uint(64));

        u_z = gsl_rng_uniform(r);
        g_1 = gsl_ran_gamma(r, 2.0, 1.0);
        g_2  = gsl_ran_gamma(r, 2.0, 1.0);

        t_z = floor((log(u_z+1) / g_1) + u_z);
        y_z = exp(g_1 * (t_z - u_z));
        a_z = (g_2 / (y_z * exp(g_1)));

        if a_z < min_a_z then
            min_a_z = a_z;
      }

    // Return the preimage of the MinHash and t_z
    
  }

  // Applied to each individual set in a collection of sets
  // Returns the "zero bit" version of the hash that omits t_z above

  proc GetMinHash_ZBit(S: [?S_Dom] uint(64)): [S_Dom] uint(64) {

    var u_z: real(64) = 0.0;
    var g_1: real(64) = 0.0;
    var g_2: real(64) = 0.0;

    var t_z: real(64) = 0.0;
    var y_z: real(64) = 0.0;
    var a_z: real(64) = 0.0;

    var min_a_z: real(64) = 0xffffffffffffffff: real(64);

    var r = gsl_rng_alloc (gsl_rng_taus2);

    // Loop over hashes
    for idx  {
        gsl_rng_set(r, idx: uint(64));

        u_z = gsl_rng_uniform(r);
        g_1 = gsl_ran_gamma(r, 2.0, 1.0);
        g_2  = gsl_ran_gamma(r, 2.0, 1.0);

        t_z = floor((log(u_z+1) / g_1) + u_z);
        y_z = exp(g_1 * (t_z - u_z));
        a_z = (g_2 / (y_z * exp(g_1)));

        if a_z < min_a_z then
            min_a_z = a_z;
      }

    // Return the preimage of the MinHash only

  }

  proc Sample(A: [?A_Dom] uint(64), bool ZBit): [A_Dom] uint(64) {


  }


  /*
  Parse, execute, and respond to a foo message
  :arg reqMsg: request containing (cmd,dtype,size)
  :type reqMsg: string
  :arg st: SymTab to act on
  :type st: borrowed SymTab
  :returns: (string) response message
  */

  proc MinHashCWSMsg(reqMsg: string, st: borrowed SymTab): string throws {

    var repMsg: string; // response message

    // split request into fields
    var (cmd, name) = reqMsg.splitMsgToTuple(2);

    // get next symbol name
    var rname = st.nextName();

    var gEnt: borrowed GenSymEntry = st.lookup(name);

    if (gEnt == nil) {return unknownSymbolError("set",name);}

    // if verbose print action
    if v {try! writeln("%s %s: %s".format(cmd,name,rname)); try! stdout.flush();}

    select (gEnt.dtype) {
        when (DType.Int64) {
            var e = toSymEntry(gEnt,int);
            var ret = foo(e.a);
            st.addEntry(rname, new shared SymEntry(ret));
        }
        otherwise {return notImplementedError("foo",gEnt.dtype);}
    }

    // response message
    return try! "created " + st.attrib(rname);
  }


  proc registerMe() {
    use CommandMap;
    registerFunction("Sample", MinHashCWSMsg);
  }
}
