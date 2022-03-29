
module DistanceCalcMsg{

    use ServerConfig;
    use DistanceCalc;
    use Message;

    // TODO - add logging

    proc dotProductMsg(cmd: string, payload: string, st: borrowed SymTab): MsgTuple throws {
        param pn = Reflection.getRoutineName();
        var repMsg: string; // response message
        // split request into fields
        var (name, name2) = payload.splitMsgToTuple(2);

        var gEnt: borrowed GenSymEntry = getGenericTypedArrayEntry(name, st);
        var gEnt2: borrowed GenSymEntry = getGenericTypedArrayEntry(name2, st);

        select(gEnt.dtype, gEnt2.dtype){
            when (DType.Int64, DType.Int64){
                var u = toSymEntry(gEnt, int);
                var v = toSymEntry(gEnt2, int);
                var prod = u.a * v.a;
                var result: int = + reduce prod;
                repMsg = "int64 %i".format(result);
                asLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),repMsg);
                return new MsgTuple(repMsg, MsgType.NORMAL);
            }
            when (DType.UInt64, DType.UInt64){
                var u = toSymEntry(gEnt, uint);
                var v = toSymEntry(gEnt2, uint);
                var prod = u.a * v.a;
                var result: uint = + reduce prod;
                repMsg = "uint64 %i".format(result);
                asLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),repMsg);
                return new MsgTuple(repMsg, MsgType.NORMAL);
            }
            when (DType.Float64, DType.Float64){
                var u = toSymEntry(gEnt, real);
                var v = toSymEntry(gEnt2, real);
                var prod = u.a * v.a;
                var result: real = + reduce prod;
                repMsg = "float64 %i".format(result);
                asLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),repMsg);
                return new MsgTuple(repMsg, MsgType.NORMAL);
            }
            otherwise{
                var errorMsg = notImplementedError("dot",gEnt.dtype);
                asLogger.error(getModuleName(),getRoutineName(),getLineNumber(),errorMsg);           
                return new MsgTuple(errorMsg, MsgType.ERROR);
            }
        }
    }

    proc registerMe() {
        use CommandMap;
        registerFunction("dot", dotProductMsg, getModuleName());
    }
}