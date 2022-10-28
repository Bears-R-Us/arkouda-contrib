module Arr2DMsg {
  use GenSymIO;
  use SymEntry2D;

  use ServerConfig;
  use MultiTypeSymbolTable;
  use MultiTypeSymEntry;
  use Message;
  use ServerErrors;
  use Reflection;
  use RandArray;
  use Logging;
  use ServerErrorStrings;

  use BinOp;

  private config const logLevel = ServerConfig.logLevel;
  const randLogger = new Logger(logLevel);

  proc array2DMsg(cmd: string, args: string, argSize: int, st: borrowed SymTab): MsgTuple throws {
    var msgArgs = parseMessageArgs(args, argSize);
    var val = msgArgs.get("val");
    var dtype = val.getDType();
    var m: int = msgArgs.get("m").getIntValue();
    var n: int = msgArgs.get("n").getIntValue();
    var rname:string = "";

    overMemLimit(2*m*n);

    if dtype == DType.Int64 {
      var entry = new shared SymEntry2D(m, n, int);
      var localA: [{0..#m, 0..#n}] int = val.getIntValue();
      entry.a = localA;
      rname = st.nextName();
      st.addEntry(rname, entry);
    } else if dtype == DType.Float64 {
      var entry = new shared SymEntry2D(m, n, real);
      var localA: [{0..#m, 0..#n}] real = val.getRealValue();
      entry.a = localA;
      rname = st.nextName();
      st.addEntry(rname, entry);
    } else if dtype == DType.Bool {
      var entry = new shared SymEntry2D(m, n, bool);
      var localA: [{0..#m, 0..#n}] bool = val.getBoolValue();
      entry.a = localA;
      rname = st.nextName();
      st.addEntry(rname, entry);
    }

    var msgType = MsgType.NORMAL;
    var msg:string = "";

    if (MsgType.ERROR != msgType) {
      if (msg.isEmpty()) {
        msg = "created " + st.attrib(rname);
      }
      gsLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),msg);
    }
    return new MsgTuple(msg, msgType);
  }

  proc randint2DMsg(cmd: string, payload: string, argSize: int, st: borrowed SymTab): MsgTuple throws {
    param pn = Reflection.getRoutineName();
    var repMsg: string; // response message
    var msgArgs = parseMessageArgs(payload, argSize);
    var dtype = str2dtype(msgArgs.getValueOf("dtype"));
    const m = msgArgs.get("m").getIntValue();
    const n = msgArgs.get("n").getIntValue();
    const seed = msgArgs.getValueOf("seed");
    var rname = st.nextName();

    select (dtype) {
      when (DType.Int64) {
        overMemLimit(8*m*n);
        var aMin = msgArgs.get("low").getIntValue();
        var aMax = msgArgs.get("high").getIntValue();

        var entry = new shared SymEntry2D(m, n, int);
        var localA: [{0..#m, 0..#n}] int;
        entry.a = localA;
        st.addEntry(rname, entry);
        fillInt(entry.a, aMin, aMax, seed);
      }
      when (DType.Float64) {
        overMemLimit(8*m*n);
        var aMin = msgArgs.get("low").getRealValue();
        var aMax = msgArgs.get("high").getRealValue();

        var entry = new shared SymEntry2D(m, n, real);
        var localA: [{0..#m, 0..#n}] real;
        entry.a = localA;
        st.addEntry(rname, entry);
        fillReal(entry.a, aMin, aMax, seed);
      }
      when (DType.Bool) {
        overMemLimit(8*m*n);

        var entry = new shared SymEntry2D(m, n, bool);
        var localA: [{0..#m, 0..#n}] bool;
        entry.a = localA;
        st.addEntry(rname, entry);
        fillBool(entry.a, seed);
      }
      otherwise {
        var errorMsg = notImplementedError(pn,dtype);
        randLogger.error(getModuleName(),getRoutineName(),getLineNumber(),errorMsg);
        return new MsgTuple(errorMsg, MsgType.ERROR);
      }
    }

    repMsg = "created " + st.attrib(rname);
    return new MsgTuple(repMsg, MsgType.NORMAL);
  }

  proc binopvv2DMsg(cmd: string, payload: string, argSize: int, st: borrowed SymTab): MsgTuple throws {
    param pn = Reflection.getRoutineName();
    var repMsg: string; // response message
    var msgArgs = parseMessageArgs(payload, argSize);

    var rname = st.nextName();
    var left: borrowed GenSymEntry = getGenericTypedArrayEntry(msgArgs.getValueOf("array"), st);
    var right: borrowed GenSymEntry = getGenericTypedArrayEntry(msgArgs.getValueOf("other"), st);
    const op = msgArgs.getValueOf("op");

    use Set;
    var boolOps: set(string);
    boolOps.add("<");
    boolOps.add("<=");
    boolOps.add(">");
    boolOps.add(">=");
    boolOps.add("==");
    boolOps.add("!=");

    select (left.dtype, right.dtype) {
      when (DType.Int64, DType.Int64) {
        var l = left: SymEntry2D(int);
        var r = right: SymEntry2D(int);
        if boolOps.contains(op) {
          var e = st.addEntry2D(rname, l.m, l.n, bool);
          return doBinOpvv(l, r, e, op, rname, pn, st);
        } else if op == "/" {
          var e = st.addEntry2D(rname, l.m, l.n, real);
          return doBinOpvv(l, r, e, op, rname, pn, st);
        }
        var e = st.addEntry2D(rname, l.m, l.n, int);
        return doBinOpvv(l, r, e, op, rname, pn, st);
      }
      when (DType.Int64, DType.Float64) {
        var l = left: SymEntry2D(int);
        var r = right: SymEntry2D(real);
        if boolOps.contains(op) {
          var e = st.addEntry2D(rname, l.m, l.n, bool);
          return doBinOpvv(l, r, e, op, rname, pn, st);
        }
        var e = st.addEntry2D(rname, l.m, l.n, real);
        return doBinOpvv(l, r, e, op, rname, pn, st);
      }
      when (DType.Float64, DType.Int64) {
        var l = left: SymEntry2D(real);
        var r = right: SymEntry2D(int);
        if boolOps.contains(op) {
          var e = st.addEntry2D(rname, l.m, l.n, bool);
          return doBinOpvv(l, r, e, op, rname, pn, st);
        }
        var e = st.addEntry2D(rname, l.m, l.n, real);
        return doBinOpvv(l, r, e, op, rname, pn, st);
      }
      when (DType.Float64, DType.Float64) {
        var l = left: SymEntry2D(real);
        var r = right: SymEntry2D(real);
        if boolOps.contains(op) {
          var e = st.addEntry2D(rname, l.m, l.n, bool);
          return doBinOpvv(l, r, e, op, rname, pn, st);
        }
        var e = st.addEntry2D(rname, l.m, l.n, real);
        return doBinOpvv(l, r, e, op, rname, pn, st);
      }
      when (DType.Bool, DType.Bool) {
        var l = left: SymEntry2D(bool);
        var r = right: SymEntry2D(bool);
        var e = st.addEntry2D(rname, l.m, l.n, bool);
        return doBinOpvv(l, r, e, op, rname, pn, st);
      }
      when (DType.Bool, DType.Int64) {
        var l = left: SymEntry2D(bool);
        var r = right: SymEntry2D(int);
        var e = st.addEntry2D(rname, l.m, l.n, int);
        return doBinOpvv(l, r, e, op, rname, pn, st);
      }
      when (DType.Int64, DType.Bool) {
        var l = left: SymEntry2D(int);
        var r = right: SymEntry2D(bool);
        var e = st.addEntry2D(rname, l.m, l.n, int);
        return doBinOpvv(l, r, e, op, rname, pn, st);
      }
      when (DType.Bool, DType.Float64) {
        var l = left: SymEntry2D(bool);
        var r = right: SymEntry2D(real);
        var e = st.addEntry2D(rname, l.m, l.n, real);
        return doBinOpvv(l, r, e, op, rname, pn, st);
      }
      when (DType.Float64, DType.Bool) {
        var l = left: SymEntry2D(real);
        var r = right: SymEntry2D(bool);
        var e = st.addEntry2D(rname, l.m, l.n, real);
        return doBinOpvv(l, r, e, op, rname, pn, st);
      }
    }
    return new MsgTuple("Bin op not supported", MsgType.NORMAL);
  }

  proc SymTab.addEntry2D(name: string, m, n, type t): borrowed SymEntry2D(t) throws {
    if t == bool {overMemLimit(m*n);} else {overMemLimit(m*n*numBytes(t));}

    var entry = new shared SymEntry2D(m, n, t);
    if (tab.contains(name)) {
      mtLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),
                     "redefined symbol: %s ".format(name));
    } else {
      mtLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),
                     "adding symbol: %s ".format(name));
    }

    tab.addOrSet(name, entry);
    return (tab.getBorrowed(name):borrowed GenSymEntry): SymEntry2D(t);
  }

  proc rowIndex2DMsg(cmd: string, payload: string, argSize: int, st: borrowed SymTab): MsgTuple throws {
    param pn = Reflection.getRoutineName();
    var repMsg: string; // response message
    var (name, rowNumStr) = payload.splitMsgToTuple(2); // split request into fields
    var msgArgs = parseMessageArgs(payload, argSize);
    var row = msgArgs.get("row").getIntValue();

    // get next symbol name
    var rname = st.nextName();
    var gEnt: borrowed GenSymEntry = getGenericTypedArrayEntry(msgArgs.getValueOf("obj"), st);

    proc getRowHelper(type t) throws {
      var e = toSymEntry2D(gEnt, t);
      var a = st.addEntry(rname, e.m, t);
      a.a = e.a[row,..];
      var repMsg = "created " + st.attrib(rname);
      return new MsgTuple(repMsg, MsgType.NORMAL);
    }

    select(gEnt.dtype) {
      when (DType.Int64) {
        return getRowHelper(int);
      }
      when (DType.Float64) {
        return getRowHelper(real);
      }
      when (DType.Bool) {
        return getRowHelper(bool);
      }
      otherwise {
        var errorMsg = notImplementedError(pn,dtype2str(gEnt.dtype));
        return new MsgTuple(errorMsg,MsgType.ERROR);              
      }
    }
  }

  proc reshape1DMsg(cmd: string, payload: string, argSize: int, st: borrowed SymTab): MsgTuple throws {
    param pn = Reflection.getRoutineName();
    var repMsg: string; // response message
    var msgArgs = parseMessageArgs(payload, argSize);
    
    var rname = st.nextName();
    var gEnt: borrowed GenSymEntry = getGenericTypedArrayEntry(msgArgs.getValueOf("obj"), st);
    
    if gEnt.ndim == 1 {
      var inputArr = toSymEntry(gEnt, int);
      var e = st.addEntry(rname, inputArr.size, int);
      e.a = inputArr.a;
    } else {
      var inputArr = toSymEntry2D(gEnt, int);

      var e = st.addEntry(rname, inputArr.size, int);
      e.a = reshape(inputArr.a, {0..#(inputArr.m*inputArr.n)});
    }
    repMsg = "created %s".format(st.attrib(rname));
    return new MsgTuple(repMsg, MsgType.NORMAL);
  }

  proc reshape2DMsg(cmd: string, payload: string, argSize: int, st: borrowed SymTab): MsgTuple throws {
    param pn = Reflection.getRoutineName();
    var repMsg: string; // response message
    var msgArgs = parseMessageArgs(payload, argSize);

    var m = msgArgs.get("m").getIntValue();
    var n = msgArgs.get("n").getIntValue();
    
    var rname = st.nextName();
    var gEnt: borrowed GenSymEntry = getGenericTypedArrayEntry(msgArgs.getValueOf("obj"), st);
    if gEnt.ndim == 1 {
      var inputArr = toSymEntry(gEnt, int);

      var e = st.addEntry2D(rname, m, n, int);
      e.a = reshape(inputArr.a, {0..#m, 0..#n});
    } else {
      var inputArr = toSymEntry2D(gEnt, int);

      var e = st.addEntry2D(rname, m, n, int);
      e.a = reshape(inputArr.a, {0..#m, 0..#n});
    }
    
    repMsg = "created %s".format(st.attrib(rname));
    return new MsgTuple(repMsg, MsgType.NORMAL);
  }

  use CommandMap;
  registerFunction("array2d", array2DMsg, getModuleName());
  registerFunction("randint2d", randint2DMsg, getModuleName());
  registerFunction("binopvv2d", binopvv2DMsg, getModuleName());
  registerFunction("[int2d]", rowIndex2DMsg, getModuleName());
  registerFunction("reshape1D", reshape1DMsg, getModuleName());
  registerFunction("reshape2D", reshape2DMsg, getModuleName());
}
