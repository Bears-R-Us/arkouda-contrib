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


  proc lshMinMaxMsg(cmd: string, payload: string, st: borrowed SymTab): MsgTuple throws {

      param pn = Reflection.getRoutineName();

      var repMsg: string;

      var (offsets, elts, weights, zbit, numHashes) = payload.splitMsgToTuple(5);

      var zBit = try! zbit: bool;
      # const zBit: bool = zbit.toLower() == "true";
      var numHashes = try! numHashes: uint(8);
      var offsetEnt: borrowed GenSymEntry = st.lookup(offsets);
      var eltEnt: borrowed GenSymEntry = st.lookup(elts);
      var weightEnt: borrowed GenSymEntry = st.lookup(weights);

      var repMsg:string;


      select(offsetEnt.dtype, eltEnt.dtype, weightEnt.dtype) {

          when(DType.UInt64, DType.UInt64, DType.Float64) {

              var setOffsets = toSymEntry(offsetEnt,uint(64)); 
              var setElts =  toSymEntry(eltEnt,uint(64));
              var eltWeights = toSymEntry(weightEnt,real(64));

              var (preimages, hashes) = getMinHashes(setOffsets, setElts, eltWeights, numHashes);

              var pmgName = st.nextName();
              var pmgEntry = new shared SymEntry(preimages);
              st.addEntry(pmgName, pmgEntry);
              repMsg =  "created " + st.attrib(pmgName);

              if(zBit) {
                  var hashName = st.nextName();
                  var hashEntry = new shared SymEntry(hashes);
                  st.addEntry(hashName, hashEntry);
                  repMsg += "+created " + st.attrib(hashName);
              }

              return new MsgTuple(attrMsg, MsgType.NORMAL);
          }
          otherwise {

              var errorMsg = notImplementedError("cwsMinMaxZbit", offsetEnt.dtype);
              dcLogger.error(getModuleName(),getRoutineName(),getLineNumber(),errorMsg);
              return new MsgTuple(errorMsg, MsgType.ERROR);
          }
      }
  }


  proc registerMe() {
      use CommandMap;
      registerFunction("lshMinMax", lshMinMaxMsg);
  }
}
