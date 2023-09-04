
module DistanceCalcMsg{

    use ServerConfig;
    use MultiTypeSymbolTable;
    use MultiTypeSymEntry;
    use Message;
    use Reflection;
    use ServerErrors;
    use ServerErrorStrings;
    use Logging;

    private config const logLevel = ServerConfig.logLevel;
    const dcLogger = new Logger(logLevel);

    proc dotProductMsg(cmd: string, msgArgs: borrowed MessageArgs, st: borrowed SymTab): MsgTuple throws {
        param pn = Reflection.getRoutineName();
        var repMsg: string; // response message
        // split request into fields
        const name = msgArgs.getValueOf("array");
        const name2 = msgArgs.getValueOf("vector");

        var gEnt: borrowed GenSymEntry = getGenericTypedArrayEntry(name, st);
        var gEnt2: borrowed GenSymEntry = getGenericTypedArrayEntry(name2, st);

        select(gEnt.dtype, gEnt2.dtype){
            when (DType.Int64, DType.Int64){
                var u = toSymEntry(gEnt, int);
                var v = toSymEntry(gEnt2, int);
                var prod = u.a * v.a;
                var result: int = + reduce prod;
                repMsg = "int64 %i".format(result);
                dcLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),repMsg);
                return new MsgTuple(repMsg, MsgType.NORMAL);
            }
            when (DType.UInt64, DType.UInt64){
                var u = toSymEntry(gEnt, uint);
                var v = toSymEntry(gEnt2, uint);
                var prod = u.a * v.a;
                var result: uint = + reduce prod;
                repMsg = "uint64 %i".format(result);
                dcLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),repMsg);
                return new MsgTuple(repMsg, MsgType.NORMAL);
            }
            when (DType.Float64, DType.Float64){
                var u = toSymEntry(gEnt, real);
                var v = toSymEntry(gEnt2, real);
                var prod = u.a * v.a;
                var result: real = + reduce prod;
                repMsg = "float64 %i".format(result);
                dcLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),repMsg);
                return new MsgTuple(repMsg, MsgType.NORMAL);
            }
            otherwise{
                var errorMsg = notImplementedError("dotProduct", gEnt.dtype);
                dcLogger.error(getModuleName(),getRoutineName(),getLineNumber(),errorMsg);           
                return new MsgTuple(errorMsg, MsgType.ERROR);
            }
        }
    }

    use CommandMap;
    registerFunction("dot", dotProductMsg, getModuleName());
}