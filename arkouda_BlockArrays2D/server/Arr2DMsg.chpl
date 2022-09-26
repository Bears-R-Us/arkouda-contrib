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
    var val = msgArgs.getValueOf("val");
    var dtype = DType.UNDEF;
    var m: int;
    var n: int;
    var rname:string = "";

    try {
      dtype = str2dtype(msgArgs.getValueOf("dtype"));
      m = msgArgs.get("m").getIntValue();
      n = msgArgs.get("n").getIntValue();
    } catch {
      var errorMsg = "Error parsing/decoding either dtypeBytes, m, or n";
      gsLogger.error(getModuleName(), getRoutineName(), getLineNumber(), errorMsg);
      return new MsgTuple(errorMsg, MsgType.ERROR);
    }

    overMemLimit(2*m*n);

    if dtype == DType.Int64 {
      var entry = new shared SymEntry2D(m, n, int);
      var localA: [{0..#m, 0..#n}] int = val:int;
      entry.a = localA;
      rname = st.nextName();
      st.addEntry(rname, entry);
    } else if dtype == DType.Float64 {
      var entry = new shared SymEntry2D(m, n, real);
      var localA: [{0..#m, 0..#n}] real = val:real;
      entry.a = localA;
      rname = st.nextName();
      st.addEntry(rname, entry);
    } else if dtype == DType.Bool {
      var entry = new shared SymEntry2D(m, n, bool);
      var localA: [{0..#m, 0..#n}] bool = if val == "True" then true else false;
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

  proc randint2DMsg(cmd: string, args: string, argSize: int, st: borrowed SymTab): MsgTuple throws {
    param pn = Reflection.getRoutineName();
    var repMsg: string; // response message
    var msgArgs = parseMessageArgs(args, argSize);
    var dtype = str2dtype(msgArgs.getValueOf("dtype"));
    var m = msgArgs.get("m").getIntValue();
    var n = msgArgs.get("n").getIntValue();
    var rname = st.nextName();

    select (dtype) {
      when (DType.Int64) {
        overMemLimit(8*m*n);
        var aMin = msgArgs.get("low").getIntValue();
        var aMax = msgArgs.get("high").getIntValue();
        var seed = msgArgs.getValueOf("seed");

        var entry = new shared SymEntry2D(m, n, int);
        var localA: [{0..#m, 0..#n}] int;
        entry.a = localA;
        st.addEntry(rname, entry);
        fillInt(entry.a, aMin, aMax, seed);
      }
      when (DType.Float64) {
        var seed = msgArgs.getValueOf("seed");
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
        var seed = msgArgs.getValueOf("seed");
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

  proc binopvv2DMsg(cmd: string, args: string, argSize: int, st: borrowed SymTab): MsgTuple throws {
    param pn = Reflection.getRoutineName();
    var repMsg: string; // response message

    var msgArgs = parseMessageArgs(args, argSize);
    const op = msgArgs.getValueOf("op");
    var aname = msgArgs.getValueOf("a");
    var bname = msgArgs.getValueOf("b");

    var rname = st.nextName();
    var left: borrowed GenSymEntry = getGenericTypedArrayEntry(aname, st);
    var right: borrowed GenSymEntry = getGenericTypedArrayEntry(bname, st);

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

  proc rowIndex2DMsg(cmd: string, args: string, argSize: int, st: borrowed SymTab): MsgTuple throws {
    param pn = Reflection.getRoutineName();
    var repMsg: string; // response message
    var msgArgs = parseMessageArgs(args, argSize);
    var name = msgArgs.getValueOf("name");
    var row: int;
    try {
       row = msgArgs.get("key").getIntValue();
    } catch {
          var errorMsg = "Error parsing/decoding key";
          gsLogger.error(getModuleName(), getRoutineName(), getLineNumber(), errorMsg);
    }

    // get next symbol name
    var rname = st.nextName();
    var gEnt: borrowed GenSymEntry = getGenericTypedArrayEntry(name, st);

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

  proc reshape1DMsg(cmd: string, args: string, argSize: int, st: borrowed SymTab): MsgTuple throws {
    param pn = Reflection.getRoutineName();
    var repMsg: string; // response message
    var msgArgs = parseMessageArgs(args, argSize);
    var name = msgArgs.getValueOf("name");
    
    var rname = st.nextName();
    var gEnt: borrowed GenSymEntry = getGenericTypedArrayEntry(name, st);
    
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

  proc reshape2DMsg(cmd: string, args: string, argSize: int, st: borrowed SymTab): MsgTuple throws {
    param pn = Reflection.getRoutineName();
    var repMsg: string; // response message
    var msgArgs = parseMessageArgs(args, argSize);
    var name = msgArgs.getValueOf("name");
    var m = msgArgs.get("m").getIntValue();
    var n = msgArgs.get("n").getIntValue();
    
    var rname = st.nextName();
    var gEnt: borrowed GenSymEntry = getGenericTypedArrayEntry(name, st);
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
  registerFunction("array2d", array2DMsg);
  registerFunction("randint2d", randint2DMsg);
  registerFunction("binopvv2d", binopvv2DMsg);
  registerFunction("[int2d]", rowIndex2DMsg);
  registerFunction("reshape1D", reshape1DMsg);
  registerFunction("reshape2D", reshape2DMsg);
}
