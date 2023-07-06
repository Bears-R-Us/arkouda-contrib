module Aksparse {
    use ServerConfig;
    
    use Reflection;
    use Message;
    
    use MultiTypeSymbolTable;
    use MultiTypeSymEntry;
    use ServerErrorStrings;
    use ServerErrors;
    use NumPyDType;
    use AryUtil;
    use CommAggregation;
    use BroadcastMsg;
    use Broadcast;
    use Indexing;
    use ReductionMsg;

    use GroupBy;
    use List;

    proc coo_init(args...?n) {
        if args.size == 4 {
            var coo_domain: domain(3) = {0..args[0].size - 1, 0..args[0].size - 1, 0..args[0].size - 1};
            var data = args[0];
            var rows = args[1];
            var columns = args[2];
            var shape = args[3];
        }
        else if args.size == 1 {
            ref dense_matrix = args[0];
            const total_indexes: int = dense_matrix[0].size * dense_matrix.size;
            var val_count: int;

            var temp_data: [0..total_indexes] int;
            var temp_rows: [0..total_indexes] int;
            var temp_columns: [0..total_indexes] int;
        
            for i in 0..dense_matrix.size - 1 {
                for j in 0..dense_matrix[0].size - 1 {
                    var val = dense_matrix[i][j];
                    if val != 0 then {
                        temp_data[val_count] = val;
                        temp_rows[val_count] = i;
                        temp_columns[val_count] = j;
                        val_count += 1;
                    }
                }
            }
            var coo_domain: domain(3) = {0..val_count - 1, 0..val_count - 1, 0..val_count - 1};
            var data: [0..val_count - 1] int = temp_data[0..val_count - 1]; 
            var rows: [0..val_count - 1] int = temp_rows[0..val_count - 1]; 
            var columns: [0..val_count - 1] int = temp_columns[0..val_count - 1];
            var shape = (dense_matrix.size, dense_matrix[0].size);
        }
    }

    proc coo_construct(cmd: string, msgArgs: borrowed MessageArgs, st: borrowed SymTab): MsgTuple throws {
        var valname = msgArgs.getValueOf("data");
        var gEnt: borrowed GenSymEntry = getGenericTypedArrayEntry(valname, st);
        var colname = msgArgs.getValueOf("columns");
        var gEnt2: borrowed GenSymEntry = getGenericTypedArrayEntry(colname, st);
        var rowname = msgArgs.getValueOf("rows");
        var gEnt3: borrowed GenSymEntry = getGenericTypedArrayEntry(rowname, st);

        select(gEnt.dtype, gEnt2.dtype, gEnt3.dtype) {
            when (DType.Int64, DType.Int64, DType.Int64) {
                var v = toSymEntry(gEnt,int);
                var c = toSymEntry(gEnt2,int);
                var r = toSymEntry(gEnt3,int);
            }
        }
        var repMsg = st.attrib(valname) + "+" + st.attrib(colname) + "+" + st.attrib(rowname);
        return new MsgTuple(repMsg, MsgType.NORMAL);
    }

    proc pdarrayIntIndexing(name: string, iname: string, st: borrowed SymTab): string throws {
        param pn = Reflection.getRoutineName();
        var rname = st.nextName();
        var gX: borrowed GenSymEntry = getGenericTypedArrayEntry(name, st);
        var gIV: borrowed GenSymEntry = getGenericTypedArrayEntry(iname, st);     //create a custom message instead of args  

        // Former helper function begins
        var e = toSymEntry(gX,int);
        var iv = toSymEntry(gIV,int);
        if (e.size == 0) && (iv.size == 0) {
            return "ERROR";
        }
        var ivMin = min reduce iv.a;
        var ivMax = max reduce iv.a;
        if ivMin < 0 {
            var errorMsg = "Error: %s: OOBindex %i < 0".format(pn,ivMin);
            return "ERROR";               
        }
        if ivMax >= e.size {
            var errorMsg = "Error: %s: OOBindex %i > %i".format(pn,ivMin,e.size-1);             
            return "ERROR";
        }
        var a = st.addEntry(rname, iv.size, int);
        ref a2 = e.a;
        ref iva = iv.a;
        ref aa = a.a;
        forall (a1,idx) in zip(aa,iva) with (var agg = newSrcAggregator(int)) {
            agg.copy(a1,a2[idx]); //Performance note
        }
        a.max_bits = e.max_bits;

        return rname;
    }

    proc get_unique_keys(gb: GroupBy, st: borrowed SymTab): list(string) throws {
        var dimension_list: list(string);
        for (name, objtype) in zip(gb.keyNames.a, gb.keyTypes.a) {
            select objtype {
                when "pdarray" {
                    var g = getGenericTypedArrayEntry(name, st);
                    select g.dtype {
                        when DType.Int64   {
                            var ukindname = st.nextName();
                            st.addEntry(ukindname, new shared SymEntry(gb.uniqueKeyIndexes.a)); //gb.uniquekeyindexes.name
                            var uk_name = pdarrayIntIndexing(g.name, ukindname, st);
                            dimension_list.append(uk_name);
                        }
                        when DType.UInt64  {
                            throw getErrorWithContext(
                                      msg=dtype2str(g.dtype),
                                      lineNumber=getLineNumber(),
                                      routineName=getRoutineName(),
                                      moduleName=getModuleName(),
                                      errorClass="TypeError"
                                      );
                        }
                        when DType.Float64 {
                            throw getErrorWithContext(
                                      msg=dtype2str(g.dtype),
                                      lineNumber=getLineNumber(),
                                      routineName=getRoutineName(),
                                      moduleName=getModuleName(),
                                      errorClass="TypeError"
                                      );
                        }
                        otherwise { 
                            throw getErrorWithContext(
                                      msg=dtype2str(g.dtype),
                                      lineNumber=getLineNumber(),
                                      routineName=getRoutineName(),
                                      moduleName=getModuleName(),
                                      errorClass="TypeError"
                                      );
                        }
                    }
                }
                otherwise {
                    var errorMsg = "Unrecognized object type: %s".format(objtype);
                    auLogger.error(getModuleName(),getRoutineName(),getLineNumber(),errorMsg);  
                    throw getErrorWithContext(
                                      msg=dtype2str(DType.Int64),
                                      lineNumber=getLineNumber(),
                                      routineName=getRoutineName(),
                                      moduleName=getModuleName(),
                                      errorClass="TypeError"
                                      );                
                }
            }
        }
        return dimension_list;
    }

    proc coo_to_csr(cmd: string, msgArgs: borrowed MessageArgs, st: borrowed SymTab): MsgTuple throws {
        var gEnt: borrowed GenSymEntry = getGenericTypedArrayEntry(msgArgs.getValueOf("data"), st);
        var gEnt2: borrowed GenSymEntry = getGenericTypedArrayEntry(msgArgs.getValueOf("columns"), st);
        var gEnt3: borrowed GenSymEntry = getGenericTypedArrayEntry(msgArgs.getValueOf("rows"), st);
        var shape_height = msgArgs.get("shape_height").getIntValue();
        var shape_width = msgArgs.get("shape_width").getIntValue();

        select(gEnt.dtype, gEnt2.dtype, gEnt3.dtype) {
            when (DType.Int64, DType.Int64, DType.Int64) {
                var v = toSymEntry(gEnt,int);
                var c = toSymEntry(gEnt2,int);
                var r = toSymEntry(gEnt3,int);
                var vname = st.nextName();
                st.addEntry(vname, new shared SymEntry(v.a));
                var cname = st.nextName();
                st.addEntry(cname, new shared SymEntry(c.a));
                var rname = st.nextName();
                st.addEntry(rname, new shared SymEntry(r.a));

                var oldcolname = st.nextName();
                st.addEntry(oldcolname, new shared SymEntry(c.a));
                var oldrowname = st.nextName();
                st.addEntry(oldrowname, new shared SymEntry(r.a));

                var gb = getGroupBy(1, [rname], ["pdarray"], false, st);
                var gb_row_col = getGroupBy(2, [rname, cname], ["pdarray", "pdarray"], false, st);
                
                var colsname = st.nextName();
                st.addEntry(colsname, new shared SymEntry(c.a[gb_row_col.permutation.a]));
                var valsname = st.nextName();
                st.addEntry(valsname, new shared SymEntry(v.a[gb_row_col.permutation.a]));

                var gb_row = getGroupBy(1, [r.name], ["pdarray"], false, st);
                var gb_row_val = getGroupBy(2, [r.name, v.name], ["pdarray", "pdarray"], false, st);
                
                var ukname = st.nextName();
                var uklist = get_unique_keys(gb_row_val, st);
                var gEnt_uk: borrowed GenSymEntry = getGenericTypedArrayEntry(uklist[0], st);
                var uk = toSymEntry(gEnt_uk,int);
                st.addEntry(ukname, new shared SymEntry(uk.a));
                var gb_row_val_uk = getGroupBy(1, [ukname], ["pdarray"], false, st);

                var arrname = st.nextName();
                var arr = [v.a.size];
                st.addEntry(arrname, new shared SymEntry(arr));
                var gEntArr: borrowed GenSymEntry = getGenericTypedArrayEntry(arrname, st);
                var arr_symentry = toSymEntry(gEntArr,int);

                var segs = concatArrays(gb_row_val_uk.segments.a, arr_symentry.a);
                var diffs = segs[1..segs.size - 1] - segs[0..segs.size - 2];  // <--- Might crash with small array
                var ind_ptr: [0..shape_height] int;

                var uk2name = st.nextName();
                var uk2list = get_unique_keys(gb_row_val_uk, st);
                var gEnt_uk2: borrowed GenSymEntry = getGenericTypedArrayEntry(uk2list[0], st);
                var uk2 = toSymEntry(gEnt_uk2,int);
                st.addEntry(uk2name, new shared SymEntry(uk2.a));
                ind_ptr[uk2.a + 1] = diffs;

                var cumsumname = st.nextName();
                overMemLimit(numBytes(int) * ind_ptr.size);
                st.addEntry(cumsumname, new shared SymEntry(+ scan ind_ptr));
                var gEntCumSum: borrowed GenSymEntry = getGenericTypedArrayEntry(cumsumname, st);
                var cumsum_symentry = toSymEntry(gEntCumSum,int);
                var cumsum_arr = cumsum_symentry.a;

                // RIGHT HERE?????
                for i in 0..shape_height - ind_ptr.size - 1{
                    cumsum_arr = concatArrays(cumsum_arr, cumsum_arr[segs.size - 2..segs.size - 2]);
                }
                var finalrowsname = st.nextName();
                st.addEntry(finalrowsname, new shared SymEntry(cumsum_arr));

                // Creating final return message
                var repMsg = st.attrib(valsname) + "+" + st.attrib(colsname) + "+" +
                    st.attrib(oldcolname) + "+" + st.attrib(oldrowname) + "+" + gb_row_col.name + "+" +
                    gb_row.name + "+" + gb_row_val.name + "+" + gb_row_val_uk.name + "+" + st.attrib(finalrowsname);
                return new MsgTuple(repMsg, MsgType.NORMAL);
            }
        }
        var repMsg = st.attrib(gEnt.name);
        return new MsgTuple(repMsg, MsgType.NORMAL);
    }

    proc coo_to_csc(cmd: string, msgArgs: borrowed MessageArgs, st: borrowed SymTab): MsgTuple throws {
        var gEnt: borrowed GenSymEntry = getGenericTypedArrayEntry(msgArgs.getValueOf("data"), st);
        var gEnt2: borrowed GenSymEntry = getGenericTypedArrayEntry(msgArgs.getValueOf("columns"), st);
        var gEnt3: borrowed GenSymEntry = getGenericTypedArrayEntry(msgArgs.getValueOf("rows"), st);
        var shape_height = msgArgs.get("shape_height").getIntValue();
        var shape_width = msgArgs.get("shape_width").getIntValue();

        select(gEnt.dtype, gEnt2.dtype, gEnt3.dtype) {
            when (DType.Int64, DType.Int64, DType.Int64) {
                var v = toSymEntry(gEnt,int);
                var c = toSymEntry(gEnt2,int);
                var r = toSymEntry(gEnt3,int);
                var vname = st.nextName();
                st.addEntry(vname, new shared SymEntry(v.a));
                var cname = st.nextName();
                st.addEntry(cname, new shared SymEntry(c.a));
                var rname = st.nextName();
                st.addEntry(rname, new shared SymEntry(r.a));

                var oldcolname = st.nextName();
                st.addEntry(oldcolname, new shared SymEntry(c.a));
                var oldrowname = st.nextName();
                st.addEntry(oldrowname, new shared SymEntry(r.a));
                var oldvalname = st.nextName();
                st.addEntry(oldvalname, new shared SymEntry(v.a));

                var gb_col_row = getGroupBy(2, [c.name, r.name], ["pdarray", "pdarray"], false, st);
                var gb_row = getGroupBy(1, [r.name], ["pdarray"], false, st);

                var rowsname = st.nextName();
                st.addEntry(rowsname, new shared SymEntry(r.a[gb_col_row.permutation.a]));
                var valsname = st.nextName();
                st.addEntry(valsname, new shared SymEntry(v.a[gb_col_row.permutation.a]));

                var ukname = st.nextName();
                var uklist = get_unique_keys(gb_col_row, st);
                var gEnt_uk: borrowed GenSymEntry = getGenericTypedArrayEntry(uklist[0], st);
                var uk = toSymEntry(gEnt_uk,int);
                st.addEntry(ukname, new shared SymEntry(uk.a));
                var gb_col_row_uk = getGroupBy(1, [ukname], ["pdarray"], false, st);

                var arrname = st.nextName();
                var arr = [v.a.size];
                st.addEntry(arrname, new shared SymEntry(arr));
                var gEntArr: borrowed GenSymEntry = getGenericTypedArrayEntry(arrname, st);
                var arr_symentry = toSymEntry(gEntArr,int);

                var segs = concatArrays(gb_col_row_uk.segments.a, arr_symentry.a);
                var diffs = segs[1..segs.size - 1] - segs[0..segs.size - 2];  // <--- Might crash with small array?
                var ind_ptr: [0..shape_width] int;

                var uk2name = st.nextName();
                var uk2list = get_unique_keys(gb_col_row_uk, st);
                var gEnt_uk2: borrowed GenSymEntry = getGenericTypedArrayEntry(uk2list[0], st);
                var uk2 = toSymEntry(gEnt_uk2,int);
                st.addEntry(uk2name, new shared SymEntry(uk2.a)); // Possibly comment out?
                ind_ptr[uk2.a + 1] = diffs;

                var cumsumname = st.nextName();
                overMemLimit(numBytes(int) * ind_ptr.size);
                st.addEntry(cumsumname, new shared SymEntry(+ scan ind_ptr));
                var gEntCumSum: borrowed GenSymEntry = getGenericTypedArrayEntry(cumsumname, st);
                var cumsum_symentry = toSymEntry(gEntCumSum,int);
                var cumsum_arr = cumsum_symentry.a;
                // writeln("ind_ptr(cumsum) = ", cumsum_symentry.a);

                for i in 0..shape_width - ind_ptr.size - 1{
                    cumsum_arr = concatArrays(cumsum_arr, cumsum_arr[segs.size - 2..segs.size - 2]);
                }
                // writeln("self.rows = ", cumsum_arr);
                var finalcolsname = st.nextName();
                st.addEntry(finalcolsname, new shared SymEntry(cumsum_arr));

                // Creating final return message
                var repMsg = st.attrib(valsname) + "+" + st.attrib(rowsname) + "+" +
                    st.attrib(oldcolname) + "+" + st.attrib(oldrowname) + "+" + st.attrib(oldvalname) + "+" +
                    gb_row.name + "+" + gb_col_row.name + "+" + gb_col_row_uk.name + "+" + st.attrib(finalcolsname) + "+" +
                    vname + "+" + cname + "+" + rname;
                return new MsgTuple(repMsg, MsgType.NORMAL);
            }
        }
        var repMsg = st.attrib(gEnt.name);
        return new MsgTuple(repMsg, MsgType.NORMAL);
    }

    proc spgemm(cmd: string, msgArgs: borrowed MessageArgs, st: borrowed SymTab): MsgTuple throws {
        // Prepare argument arrays
        var gEnt: borrowed GenSymEntry = getGenericTypedArrayEntry(msgArgs.getValueOf("other_indptr"), st);
        var gEnt2: borrowed GenSymEntry = getGenericTypedArrayEntry(msgArgs.getValueOf("other_data"), st);
        var gEnt3: borrowed GenSymEntry = getGenericTypedArrayEntry(msgArgs.getValueOf("self_data"), st);
        var self_shape_width = msgArgs.get("self_shape_width").getIntValue();
        var self_shape_height = msgArgs.get("self_shape_height").getIntValue();
        var other_shape_height = msgArgs.get("other_shape_height").getIntValue();
        var other_shape_width = msgArgs.get("other_shape_width").getIntValue();
        var self_gb_rep_name = msgArgs.getValueOf("self_gb_rep");
        var self_gb_rep = getGroupBy(self_gb_rep_name, st);
        var other_gb_rep_name = msgArgs.getValueOf("other_gb_rep");
        var other_gb_rep = getGroupBy(other_gb_rep_name, st);
        var cname = msgArgs.getValueOf("cname");
        var rname = msgArgs.getValueOf("rname");

        if self_shape_height != other_shape_width {
            writeln("\nERROR SIZE MISMATCH\n");
        }
        var other_indptr = toSymEntry(gEnt,int);
        var other_data = toSymEntry(gEnt2,int);
        var self_data = toSymEntry(gEnt3,int);

        var gb_col_row = getGroupBy(2, [cname, rname], ["pdarray", "pdarray"], false, st);
        var self_gb_rep_uklist = get_unique_keys(gb_col_row, st);
        var gEnt_self_gb_rep_uk0: borrowed GenSymEntry = getGenericTypedArrayEntry(self_gb_rep_uklist[0], st);
        var self_gb_rep_uk0 = toSymEntry(gEnt_self_gb_rep_uk0,int);
        var gEnt_self_gb_rep_uk1: borrowed GenSymEntry = getGenericTypedArrayEntry(self_gb_rep_uklist[1], st);
        var self_gb_rep_uk1 = toSymEntry(gEnt_self_gb_rep_uk1,int);

        var other_gb_rep_uklist = get_unique_keys(other_gb_rep, st);
        var gEnt_other_gb_rep_uk0: borrowed GenSymEntry = getGenericTypedArrayEntry(other_gb_rep_uklist[0], st);
        var other_gb_rep_uk0 = toSymEntry(gEnt_other_gb_rep_uk0,int);
        var gEnt_other_gb_rep_uk1: borrowed GenSymEntry = getGenericTypedArrayEntry(other_gb_rep_uklist[1], st);
        var other_gb_rep_uk1 = toSymEntry(gEnt_other_gb_rep_uk1,int);

        // Identify number of multiplications needed
        var starts = other_indptr.a[self_gb_rep_uk0.a];
        var ends = other_indptr.a[self_gb_rep_uk0.a + 1];
        var fullsize = + reduce (ends - starts);
        var nonzero = ends > starts;
        var lengths = (ends - starts);
        var segs = (+ scan lengths) - lengths;

        var fsegs = boolIndexer(segs, nonzero);
        var fstarts = boolIndexer(starts, nonzero);
        var fends = boolIndexer(ends, nonzero);

        var totlen = + reduce lengths;
        var slices: [0..totlen - 1] int = 1;
        var arg2 = fstarts[1..fstarts.size - 1] - fends[0..fends.size - 2] + 1;
        var diffs = concatArrays(fstarts[0..0], arg2);

        // Set up arrays for multiplication
        slices[fsegs] = diffs;
        var fullsegs = fsegs;
        var ranges = (+ scan slices);

        var fullBdom = other_gb_rep_uk1.a[ranges];
        var nonzero_uk = boolIndexer(self_gb_rep_uk1.a, nonzero);
        var fullAdom = broadcast(fullsegs, nonzero_uk, fullsize);
        
        var fullBval = other_data.a[ranges];
        var nonzero_data = boolIndexer(self_data.a, nonzero);
        var fullAval = broadcast(fullsegs, nonzero_data, fullsize);
        var fullprod = fullAval * fullBval;

        //GroupBy indices and perform aggregate sum
        var Adomname = st.nextName();
        st.addEntry(Adomname, new shared SymEntry(fullAdom));
        var Bdomname = st.nextName();
        st.addEntry(Bdomname, new shared SymEntry(fullBdom));
        var proddomGB = getGroupBy(2, [Adomname, Bdomname], ["pdarray", "pdarray"], false, st);
        
        var permuted_array = fullprod[proddomGB.segments.a];
        var result3 = segSum(permuted_array, proddomGB.segments.a);
        var result1_uklist = get_unique_keys(proddomGB, st);
        var gEnt_result1_uk0: borrowed GenSymEntry = getGenericTypedArrayEntry(result1_uklist[0], st);
        var result1_uk0 = toSymEntry(gEnt_result1_uk0,int);
        var gEnt_result1_uk1: borrowed GenSymEntry = getGenericTypedArrayEntry(result1_uklist[1], st);
        var result1_uk1 = toSymEntry(gEnt_result1_uk1,int);

        var result1name = st.nextName();
        st.addEntry(result1name, new shared SymEntry(result1_uk0.a));
        var result2name = st.nextName();
        st.addEntry(result2name, new shared SymEntry(result1_uk1.a));
        var result3name = st.nextName();
        st.addEntry(result3name, new shared SymEntry(result3));

        var gb_row_val = getGroupBy(2, [result1name, result3name], ["pdarray", "pdarray"], false, st);
        var gb_row_val_uklist = get_unique_keys(gb_row_val, st);
        var gEnt_gb_row_val_uk0: borrowed GenSymEntry = getGenericTypedArrayEntry(gb_row_val_uklist[0], st);
        var gb_row_val_symentry = toSymEntry(gEnt_gb_row_val_uk0,int);
        var gb_row_val_uk = getGroupBy(1, [gb_row_val_symentry.name], ["pdarray"], false, st);
        var gb_row_val_uk_uklist = get_unique_keys(gb_row_val_uk, st);
        var gEnt_gb_row_val_uk_uk0: borrowed GenSymEntry = getGenericTypedArrayEntry(gb_row_val_uk_uklist[0], st);
        var gb_row_val_uk_uk_symentry = toSymEntry(gEnt_gb_row_val_uk_uk0,int);

        var len_arr: [0..0] int = result3.size;
        var segs2 = concatArrays(gb_row_val_uk.segments.a, len_arr); //Fix this?
        var diffs2 = segs2[1..segs2.size - 1] - segs2[0..segs2.size - 2];
        var ind_ptr: [0..self_shape_height] int = 0; //Maybe wrong shape var?
        ind_ptr[gb_row_val_uk_uk_symentry.a + 1] = diffs2;
        
        ind_ptr = + scan ind_ptr;
        for i in 0..(self_shape_height - (ind_ptr.size - 1)) {
            ind_ptr = concatArrays(ind_ptr, ind_ptr[ind_ptr.size - 2..ind_ptr.size - 1]);
        }
        var ind_ptrname = st.nextName();
        st.addEntry(ind_ptrname, new shared SymEntry(ind_ptr));
        
        var reorderedname = st.nextName();
        st.addEntry(reorderedname, new shared SymEntry(result3[proddomGB.permutation.a]));
        var gEnt_reorder: borrowed GenSymEntry = getGenericTypedArrayEntry(reorderedname, st);
        var reordered_result3 = toSymEntry(gEnt_reorder,int);

        var repMsg = st.attrib(ind_ptrname) + "+" + st.attrib(result2name) + "+" +
                    st.attrib(reorderedname);
        return new MsgTuple(repMsg, MsgType.NORMAL);
    }

    use CommandMap;

    registerFunction("coo_construct", coo_construct, getModuleName());
    registerFunction("coo_to_csr", coo_to_csr, getModuleName());
    registerFunction("coo_to_csc", coo_to_csc, getModuleName());
    registerFunction("spgemm", spgemm, getModuleName());
}