module MinHashCWSMsg
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


  proc cantorPairing(setEltIdx: uint(64), hashIdx: uint(8)): uint(64): uint(64) {

      var hashIdx64: uint(64) = hashIdx: uint(64);

      var sum: uint(64) = setEltIdx + hashIdx64;

      var result: uint(64) = (0.5 * sum * (sum + 1)) + hashIdx64;

      return result;
  }


  proc getMinHashes(offsets: [?oD] uint(64), setElts: [?sD] uint(64), weights: [?wD] real(64), numHashes: uint(8)): [?outD] (uint(64), real(64)) {

/* TODO: return domain is wrong! Must be expanded by the number of hashes per set element */

      var outD: domain(1) = {oD.first..numHashes*oD.last};

      var minHashes: [outD] (uint(64),real(64));

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

/* TODO: CSR-style loop over a segmented array */

      // Loop over hashes
      coforall loc in Locales

      forall z in S {

          /* Create a unique, but globally consistent, seed for the 
             RNG by concatenating the set and the hash indices */

          var seedIdx: uint(64) = cantorPairing(s, hashIdx);

          gsl_rng_set(r, seedIdx);

          u_z = gsl_rng_uniform(r);
          g_1 = gsl_ran_gamma(r, 2.0, 1.0);
          g_2  = gsl_ran_gamma(r, 2.0, 1.0);

          t_z = floor((log(weights[z]) / g_1) + u_z);
          y_z = exp(g_1 * (t_z - u_z));
          a_z = (g_2 / (y_z * exp(g_1)));

          if a_z < min_az then
              min_az = a_z;
              min_tz = t_z;
              preimage = setElts[z];
        }

      // Return the preimage of the MinHash and t_z
      return minHashes;
  }


  /* Returns the "zero bit" version of the hash that omits t_z */

  proc getPreimages(offsets: [?oD] uint(64), setElts: [?sD] uint(64), weights: [?wD] real(64), numHashes: uint(8)): [?outD] uint(64) {

/* TODO: return domain is wrong! Must be expanded by the number of hashes per set element */

      var outD: domain(1) = {oD.first..numHashes*oD.last};

      var preimages: [outD] uint(64);

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
      forall z in S {

          /* Create a unique, but globally consistent, seed for the 
             RNG by concatenating the set and the hash indices */

          var seedIdx: uint(64) = cantorPairing(s, hashIdx);

          gsl_rng_set(r, seedIdx);

          u_z = gsl_rng_uniform(r);
          g_1 = gsl_ran_gamma(r, 2.0, 1.0);
          g_2  = gsl_ran_gamma(r, 2.0, 1.0);

          t_z = floor((log(weights[z]) / g_1) + u_z);
          y_z = exp(g_1 * (t_z - u_z));
          a_z = (g_2 / (y_z * exp(g_1)));

          if a_z < min_az then
              min_az = a_z;
              preimage = setElts[z];
        }

      // Return the preimage of the MinHash only
      return preimages;
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


  proc lshMinMaxZbit(cmd: string, payload: string, st: borrowed SymTab): MsgTuple throws {

      param pn = Reflection.getRoutineName();

      var repMsg: string;

      var (offsets, elts, weights, numHashes) = payload.splitMsgToTuple(4);

      var zBit = try! zbit: bool;
      var numHashes = try! numHashes: uint(8);
      var offsetEnt: borrowed GenSymEntry = st.lookup(offsets);
      var eltEnt: borrowed GenSymEntry = st.lookup(elts);
      var weightEnt: borrowed GenSymEntry = st.lookup(weights);

      var attrName = st.nextName();
      var attrMsg:string;


      select(offsetEnt.dtype, eltEnt.dtype, weightEnt.dtype) {

          when(DType.UInt64, DType.UInt64, DType.Float64) {

              var setOffsets = toSymEntry(offsetEnt,uint(64)); 
              var setElts =  toSymEntry(eltEnt,uint(64));
              var eltWeights = toSymEntry(weightEnt,real(64));

              var ret = getPreimages(setOffsets, setElts, eltWeights, numHashes);
              var attrEntry = new shared SymEntry(ret);
              st.addEntry(attrName, attrEntry);
              attrMsg =  'created ' + st.attrib(attrName);

              return new MsgTuple(attrMsg, MsgType.NORMAL);

          }
          otherwise {

              var errorMsg = notImplementedError("lshMinMaxZbit", offsetEnt.dtype);
              dcLogger.error(getModuleName(),getRoutineName(),getLineNumber(),errorMsg);
              return new MsgTuple(errorMsg, MsgType.ERROR);
          }
      }
  }


  proc lshMinMaxZbit(cmd: string, payload: string, st: borrowed SymTab): MsgTuple throws {

      param pn = Reflection.getRoutineName();

      var repMsg: string;

      var (offsets, elts, weights, numHashes) = payload.splitMsgToTuple(4);

      var zBit = try! zbit: bool;
      var numHashes = try! numHashes: uint(8);
      var offsetEnt: borrowed GenSymEntry = st.lookup(offsets);
      var eltEnt: borrowed GenSymEntry = st.lookup(elts);
      var weightEnt: borrowed GenSymEntry = st.lookup(weights);

      var attrName = st.nextName();
      var attrMsg:string;


      select(offsetEnt.dtype, eltEnt.dtype, weightEnt.dtype) {

          when(DType.UInt64, DType.UInt64, DType.Float64) {

              var setOffsets = toSymEntry(offsetEnt,uint(64));
              var setElts =  toSymEntry(eltEnt,uint(64));
              var eltWeights = toSymEntry(weightEnt,real(64));

              var ret = getMinHashes(setOffsets, setElts, eltWeights, numHashes);
              var attrEntry = new shared SymEntry(ret);
              st.addEntry(attrName, attrEntry);
              attrMsg =  'created ' + st.attrib(attrName);

              // TODO: figure out how to return a tuple of pdarrays
              return new MsgTuple(attrMsg, MsgType.NORMAL);

          }
          otherwise {

              var errorMsg = notImplementedError("lshMinMaxZbit", offsetEnt.dtype);
              dcLogger.error(getModuleName(),getRoutineName(),getLineNumber(),errorMsg);
              return new MsgTuple(errorMsg, MsgType.ERROR);
          }
      }
  }


  proc registerMe() {
      use CommandMap;
      registerFunction("lshMinMaxZbit", lshMinMaxZbitMsg);
      registerFunction("lshMinMax", lshMinMaxMsg);
  }
}
