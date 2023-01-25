module lshMinMaxMsg
{

  use lshMinMax;
  use ServerConfig;
  use MultiTypeSymEntry;
  use ServerErrorStrings;
  use MultiTypeSymbolTable;
  use Message;
  use Reflection;
  use ServerErrors;
  use Logging;


  private config const logLevel = ServerConfig.logLevel;
  const cwsLogger = new Logger(logLevel);


  /* An implementation of a locality-sensitive hashing scheme for the MinMax (i.e. weighted 
     Jaccard) kernel originally described in "Consistent Weighted Sampling" (Manasse, McSherry
     Talwar). The specific implementation is an equivalent version by Sergey Ioffe described 
     in "Improved Consistent Sampling, Weighted Minhash, and L1 Sketching" that improves the
     runtime of the hashing setp from expected constant time to constant time. */


  proc lshMinMaxMsg(cmd: string, msgArgs: borrowed MessageArgs, st: borrowed SymTab): MsgTuple throws {

      param pn = Reflection.getRoutineName();

      const offsets = msgArgs.getValueOf("offsets");
      const elts = msgArgs.getValueOf("elts");
      const weights = msgArgs.getValueOf("weights");

      const zBit: bool = msgArgs.get("zbit").getBoolValue();
      const numHashes: int = msgArgs.get("hashes").getIntValue();

      var offsetEnt: borrowed GenSymEntry = getGenericTypedArrayEntry(offsets, st);
      var eltEnt: borrowed GenSymEntry = getGenericTypedArrayEntry(elts, st);
      var weightEnt: borrowed GenSymEntry = getGenericTypedArrayEntry(weights, st);

      var repMsg:string;


      select(offsetEnt.dtype, eltEnt.dtype, weightEnt.dtype) {

          when(DType.Int64, DType.Int64, DType.Float64) {

              var setOffsets = toSymEntry(offsetEnt,int); 
              var setElts =  toSymEntry(eltEnt,int);
              var eltWeights = toSymEntry(weightEnt,real);

              var (preimages, hashes) = getMinHashes(setOffsets.a, setElts.a, eltWeights.a, numHashes);


	      const pmgName: string = st.nextName();
	      st.addEntry(pmgName, new shared SymEntry(preimages));
	      repMsg = "created %s".format(st.attrib(pmgName));

              if(zBit == false) {
		  const hashName: string = st.nextName();
		  st.addEntry(hashName, new shared SymEntry(hashes));
                  repMsg += "+created %s".format(st.attrib(hashName));
              }

              cwsLogger.error(getModuleName(),getRoutineName(),getLineNumber(),repMsg);
              return new MsgTuple(repMsg, MsgType.NORMAL);
          }
          otherwise {

              var errorMsg = notImplementedError("lshMinMax", offsetEnt.dtype);
              cwsLogger.error(getModuleName(),getRoutineName(),getLineNumber(),errorMsg);
              return new MsgTuple(errorMsg, MsgType.ERROR);
          }
      }
  }

  use CommandMap;
  registerFunction("lshMinMax", lshMinMaxMsg, getModuleName());
}
