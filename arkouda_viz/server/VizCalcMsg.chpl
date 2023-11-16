
module VizCalcMsg{

    use ServerConfig;
    use MultiTypeSymbolTable;
    use MultiTypeSymEntry;
    use Message;
    use Reflection;
    use ServerErrors;
    use ServerErrorStrings;
    use Logging;
    use Math;

    private config const logLevel = ServerConfig.logLevel;
    const dcLogger = new Logger(logLevel);
 
    proc datashadeMsg(cmd: string, msgArgs: borrowed MessageArgs, st: borrowed SymTab): MsgTuple throws {
        param pn = Reflection.getRoutineName();
        var repMsg: string;

        const colX = msgArgs.getValueOf("column_1");
        const colY = msgArgs.getValueOf("column_2");
        var xBins = msgArgs.get("xBins").getIntValue();
        var yBins = msgArgs.get("yBins").getIntValue();

        var gEnt: borrowed GenSymEntry = getGenericTypedArrayEntry(colX, st);
        var gEnt2: borrowed GenSymEntry = getGenericTypedArrayEntry(colY, st);

        select(gEnt.dtype, gEnt2.dtype){
            when (DType.Int64, DType.Int64){
                var arr1 = toSymEntry(gEnt, int);
                var arr2 = toSymEntry(gEnt2, int);

                var rname = st.nextName();
                var binCounts = st.addEntry(rname, xBins*yBins, int);

                var minVal_1 = min reduce arr1.a;
                var maxVal_1 = max reduce arr1.a;

                var minVal_2 = min reduce arr2.a;
                var maxVal_2 = max reduce arr2.a;

                var binWidth_1 = ((maxVal_1 - minVal_1):real / xBins): real;
                var binWidth_2 = ((maxVal_2 - minVal_2):real / yBins): real;

                for (entry_1, entry_2) in zip(arr1.a, arr2.a) {

                    var binIdx = [floor((entry_1 - minVal_1) / binWidth_1):int, floor((entry_2 - minVal_2) / binWidth_2):int];

                    if (entry_1 == maxVal_1){
                        binIdx[0] = xBins - 1;
                    }

                    if (entry_2 == maxVal_2){
                        binIdx[1] = yBins - 1;
                    }

                    var flatIndex = binIdx[1] * xBins + binIdx[0];
                    binCounts.a[flatIndex] += 1;
                }

                var repMsg = "created " + st.attrib(rname);

                dcLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),"Processing complete.");
                return new MsgTuple(repMsg, MsgType.NORMAL);

            }

            when (DType.Float64, DType.Float64){
                var arr1 = toSymEntry(gEnt, real);
                var arr2 = toSymEntry(gEnt2, real);

                var rname = st.nextName();
                var binCounts = st.addEntry(rname, xBins*yBins, int);

                var minVal_1 = min reduce arr1.a;
                var maxVal_1 = max reduce arr1.a;

                var minVal_2 = min reduce arr2.a;
                var maxVal_2 = max reduce arr2.a;

                var binWidth_1 = ((maxVal_1 - minVal_1):real / xBins): real;
                var binWidth_2 = ((maxVal_2 - minVal_2):real / yBins): real;

                for (entry_1, entry_2) in zip(arr1.a, arr2.a) {

                    var binIdx = [floor((entry_1 - minVal_1) / binWidth_1):int, floor((entry_2 - minVal_2) / binWidth_2):int];

                    if (entry_1 == maxVal_1){
                        binIdx[0] = xBins - 1;
                    }

                    if (entry_2 == maxVal_2){
                        binIdx[1] = yBins - 1;
                    }

                    var flatIndex = binIdx[1] * xBins + binIdx[0];
                    binCounts.a[flatIndex] += 1;
                }

                var repMsg = "created " + st.attrib(rname);

                dcLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),"Processing complete.");
                return new MsgTuple(repMsg, MsgType.NORMAL);
            }

            when (DType.Int64, DType.Float64){
                var arr1 = toSymEntry(gEnt, int);
                var arr2 = toSymEntry(gEnt2, real);

                var rname = st.nextName();
                var binCounts = st.addEntry(rname, xBins*yBins, int);

                var minVal_1 = min reduce arr1.a;
                var maxVal_1 = max reduce arr1.a;

                var minVal_2 = min reduce arr2.a;
                var maxVal_2 = max reduce arr2.a;

                var binWidth_1 = ((maxVal_1 - minVal_1):real / xBins): real;
                var binWidth_2 = ((maxVal_2 - minVal_2):real / yBins): real;

                for (entry_1, entry_2) in zip(arr1.a, arr2.a) {

                    var binIdx = [floor((entry_1 - minVal_1) / binWidth_1):int, floor((entry_2 - minVal_2) / binWidth_2):int];

                    if (entry_1 == maxVal_1){
                        binIdx[0] = xBins - 1;
                    }

                    if (entry_2 == maxVal_2){
                        binIdx[1] = yBins - 1;
                    }

                    var flatIndex = binIdx[1] * xBins + binIdx[0];
                    binCounts.a[flatIndex] += 1;
                }

                var repMsg = "created " + st.attrib(rname);

                dcLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),"Processing complete.");
                return new MsgTuple(repMsg, MsgType.NORMAL);
            }

            when (DType.Float64, DType.Int64){
                var arr1 = toSymEntry(gEnt, real);
                var arr2 = toSymEntry(gEnt2, int);

                var rname = st.nextName();
                var binCounts = st.addEntry(rname, xBins*yBins, int);

                var minVal_1 = min reduce arr1.a;
                var maxVal_1 = max reduce arr1.a;

                var minVal_2 = min reduce arr2.a;
                var maxVal_2 = max reduce arr2.a;

                var binWidth_1 = ((maxVal_1 - minVal_1):real / xBins): real;
                var binWidth_2 = ((maxVal_2 - minVal_2):real / yBins): real;

                for (entry_1, entry_2) in zip(arr1.a, arr2.a) {

                    var binIdx = [floor((entry_1 - minVal_1) / binWidth_1):int, floor((entry_2 - minVal_2) / binWidth_2):int];

                    if (entry_1 == maxVal_1){
                        binIdx[0] = xBins - 1;
                    }

                    if (entry_2 == maxVal_2){
                        binIdx[1] = yBins - 1;
                    }

                    var flatIndex = binIdx[1] * xBins + binIdx[0];
                    binCounts.a[flatIndex] += 1;
                }

                var repMsg = "created " + st.attrib(rname);

                dcLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),"Processing complete.");
                return new MsgTuple(repMsg, MsgType.NORMAL);
            }

            otherwise{
                var errorMsg = notImplementedError("datashade", gEnt.dtype);
                dcLogger.error(getModuleName(),getRoutineName(),getLineNumber(),errorMsg);           
                return new MsgTuple(errorMsg, MsgType.ERROR);
            }
        }
    }

    use CommandMap;
    registerFunction("datashade_server", datashadeMsg, getModuleName());
}