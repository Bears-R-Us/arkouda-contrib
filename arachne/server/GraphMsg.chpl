module GraphMsg {
    // Chapel modules.
    use IO;
    use Reflection;
    use Set;
    use Time; 
    use Sort; 
    
    // Arachne Modules.
    use GraphArray;
    
    // Arkouda modules.
    use MultiTypeSymbolTable;
    use MultiTypeSymEntry;
    use ServerConfig;
    use ArgSortMsg;
    use AryUtil;
    use Logging;
    use Message;

    
    private config const logLevel = LogLevel.DEBUG;
    const smLogger = new Logger(logLevel);
    var outMsg:string;

    config const start_min_degree = 1000000;

    /**
    * Set the neighbor and start_i arrays for the graph data structure.
    *
    * lsrc: int array of src vertices
    * lstart_i: int array of start vertex values based off src
    * lneighbor: int array of number of neighbors based off src
    *
    * returns: nothing
    */
    private proc set_neighbor(lsrc: [?D1] int, lstart_i: [?D2] int, lneighbor: [?D3] int) { 
        var Ne = D1.size;
        forall i in lstart_i {
            i = -1;
        }
        forall i in lneighbor {
            i = 0;
        }
        for i in 0..Ne-1 do {
            lneighbor[lsrc[i]] += 1;
            if (lstart_i[lsrc[i]] == -1) {
                lstart_i[lsrc[i]] = i;
            }
        }
    }// end set_neighbor(...)

    /**
    * Search for a given key in a sorted array. 
    *
    * ary: int array
    * l: low index bound
    * h: high index bound
    * key: value we are searching for
    *
    * returns: index if key is found, -1 if not found
    */
    private proc bin_search_v(ary: [?D] int, l: int, h: int, key: int): int throws {
        if ( (l < D.lowBound) || (h > D.highBound) || (l < 0)) {
            return -1;
        }
        if ( (l > h) || ((l == h) &&  (ary[l] != key))) {
            return -1;
        }
        if (ary[l] == key) {
            return l;
        }
        if (ary[h] == key) {
            return h;
        }
        
        var m = (l + h) / 2: int;
        
        if ((m == l) ) {
            return -1;
        }
        if (ary[m] == key ) {
            return m;
        } else {
            if (ary[m] < key) {
                return bin_search_v(ary, m+1, h, key);
            }
            else {
                return bin_search_v(ary, l, m-1, key);
            }
        }
    }// end bin_search_v(...)

    /**
    * Remap vertices to the range 0..Nv-1.
    *
    * lsrc: src array
    * ldst: dst array
    * num_v: number of vertices
    *
    * returns: new array size
    */
    private proc vertex_remap(lsrc: [?D1] int, ldst: [?D2] int, num_v: int): int throws {
        var num_e = lsrc.size;
        var tmpe: [D1] int;
        
        //TODO: remove if not needed.
        //var vertex_mapping:[0..num_v-1] int;

        var vertex_set = new set(int, parSafe = true);
        
        forall (i,j) in zip (lsrc,ldst) with (ref vertex_set) {
            vertex_set.add(i);
            vertex_set.add(j);
        }
        
        var vertex_ary = vertex_set.toArray();
        
        if (vertex_ary.size != num_v) {
            smLogger.error(getModuleName(), getRoutineName(), getLineNumber(), 
                           "Number of vertices is not equal to the given number!");
        }
        
        smLogger.debug(getModuleName(), getRoutineName(), getLineNumber(),
                       "Total Vertices=" + vertex_ary.size:string + " ? Nv=" + num_v:string);

        sort(vertex_ary);

        // TODO: possible optimization by using Map {old_val : new_index} (hash table) in Chapel.
        forall i in 0..num_e-1 {
            lsrc[i] = bin_search_v(vertex_ary, 0, vertex_ary.size-1, lsrc[i]);
            ldst[i] = bin_search_v(vertex_ary, 0, vertex_ary.size-1, ldst[i]);
        }
        
        return vertex_ary.size;
    }

    /**
    * Sort the two arrays together, src and dst. 
    * 
    * lsrc: src array
    * ldst: dst arrray
    * l_weight: edge weight array
    * lWeightedFlag: if edge weight array exists or not
    * sortw: sort the weight array
    *
    * returns: nothing
    */
    // TODO: combine_sort has bugs, compare against Arkouda version.
    private proc combine_sort(lsrc: [?D1] int, ldst: [?D2] int, le_weight: [?D3] int, 
                              lWeightedFlag: bool, sortw = false: bool) {
        param bitsPerDigit = RSLSD_bitsPerDigit;
        var bitWidths: [0..1] int;
        var negs: [0..1] bool;
        var totalDigits: int;
        var size = D1.size;
        var iv: [D1] int;

        for (bitWidth, ary, neg) in zip(bitWidths, [lsrc,ldst], negs) {
            (bitWidth, neg) = getBitWidth(ary);
            totalDigits += (bitWidth + (bitsPerDigit-1)) / bitsPerDigit;
        }

        /**
        * Sort two integers at the same time, src and dst.
        * 
        * halfDig: number of digits to sort. Two values for src and dst
        *
        * returns index vector that sorts the array.
        */
        proc mergedArgsort(param halfDig): [D1] int throws {
            param numBuckets = 1 << bitsPerDigit;
            param maskDigit = numBuckets-1;
            var merged = makeDistArray(size, halfDig*2*uint(bitsPerDigit));
            for jj in 0..size-1 {
                forall i in 0..halfDig-1 {
                    merged[jj][i] = (((lsrc[jj]:uint) >> ((halfDig-i-1)*bitsPerDigit)) & 
                                       (maskDigit:uint)): uint(bitsPerDigit);
                    merged[jj][i+halfDig] = (((ldst[jj]:uint) >> ((halfDig-i-1)*bitsPerDigit)) & 
                                              (maskDigit:uint)): uint(bitsPerDigit);
                }
            }
            var tmpiv = argsortDefault(merged);
            return tmpiv;
        }// end mergedArgsort(...)

        try {
            iv = mergedArgsort(2);
        } catch {
            try! smLogger.error(getModuleName(), getRoutineName(), getLineNumber(),
                                "Merge array error.");
        }

        var tmpedges = lsrc[iv];
        lsrc = tmpedges;
        tmpedges = ldst[iv];
        ldst = tmpedges;
    }//end combine_sort(...)

    /**
    * Sort the vertices based on their degrees.
    *
    * lsrc: src array
    * ldst: dst array
    * lstart_i: start_i array
    * lneighbor: neighbor array
    * le_weight: e_weight array
    * lneighborR: neighborR array
    * WeightedFlag: flag noting if the graph is weighted or not
    *
    * returns: nothing
    */
    private proc part_degree_sort(lsrc: [?D1] int, ldst: [?D2] int, lstart_i: [?D3] int, 
                                  lneighbor: [?D4] int,le_weight: [?D5] int, lneighborR: [?D6] int,
                                  lWeightedFlag: bool) {
        var DegreeArray, vertex_mapping: [D4] int;
        var tmpedge: [D1] int;
        var Nv = D4.size;
        var iv: [D1] int;

        coforall loc in Locales  {
            on loc {
                forall i in lneighbor.localSubdomain(){
                    DegreeArray[i] = lneighbor[i] + lneighborR[i];
                }
            }
        }
 
        var tmpiv:[D4] int;
        
        try {
            // Get the index based on each vertex's degree
            tmpiv = argsortDefault(DegreeArray);
        } catch {
            try! smLogger.debug(getModuleName(), getRoutineName(), getLineNumber(), 
                                "Error in part degree sort.");
        }
        forall i in 0..Nv-1 {
            // We assume the vertex ID is in 0..Nv-1
            // Given old vertex ID, map it to the new vertex ID
            vertex_mapping[tmpiv[i]]=i;
        }
        coforall loc in Locales  {
            on loc {
                forall i in lsrc.localSubdomain(){
                    tmpedge[i]=vertex_mapping[lsrc[i]];
                }
            }
        }
        lsrc = tmpedge;
        coforall loc in Locales  {
            on loc {
                forall i in ldst.localSubdomain() {
                    tmpedge[i]=vertex_mapping[ldst[i]];
                  }
            }
        }
        ldst = tmpedge;
        coforall loc in Locales  {
            on loc {
                forall i in lsrc.localSubdomain(){
                    if lsrc[i]>ldst[i] {
                        lsrc[i]<=>ldst[i];
                    }
                }
            }
        }
        try  {
            combine_sort(lsrc, ldst,le_weight,lWeightedFlag, true);
        } catch {
            try! smLogger.error(getModuleName(), getRoutineName(), getLineNumber(),
                                "Combine sort error!");
        }
        set_neighbor(lsrc, lstart_i, lneighbor);
    }// end part_degree_sort(...)

    /**
    * Degree sort for an undirected graph.
    *
    * lsrc: src array
    * ldst: dst array
    * lstart_i: start_i array
    * lneighbor: neighbor array
    * lsrcR: srcR array
    * ldstR: dstR array
    * lstart_iR: start_iR array
    * lneighborR: neighborR array
    * le_weight: weight array
    * lWeightedFlag: flag noting if graph is directed or not.
    *
    * returns: nothing
    */
    private proc degree_sort_u(lsrc: [?D1] int, ldst: [?D2] int, lstart_i: [?D3] int, 
                               lneighbor: [?D4] int, lsrcR: [?D5] int, ldstR: [?D6] int, 
                               lstart_iR: [?D7] int, lneighborR: [?D8] int, le_weight: [?D9] int,
                               lWeightedFlag: bool) {

        part_degree_sort(lsrc, ldst, lstart_i, lneighbor, le_weight, lneighborR, lWeightedFlag);
        coforall loc in Locales {
            on loc {
                forall i in lsrcR.localSubdomain(){
                    lsrcR[i]=ldst[i];
                    ldstR[i]=lsrc[i];
                }
            }
        }
        try {
            combine_sort(lsrcR, ldstR,le_weight,lWeightedFlag, false);
        } catch {
            try! smLogger.error(getModuleName(), getRoutineName(), getLineNumber(),
                               "Combine sort error!");
        }
        set_neighbor(lsrcR, lstart_iR, lneighborR);
    } 

    /**
    * Degree sort for an undirected graph.
    *
    * ary: arry to perform the search in
    * l: lowest index of search
    * h: highest index of search
    * key: value we are looking for
    *
    * returns: true if found. 
    */
    proc binSearchE(ary:[?D] int, l:int, h:int, key:int):int {
        if ( (l>h) || ((l==h) && ( ary[l] != key)))  {
            return -1;
        }
        if (ary[l]==key){
            return l;
        }
        if (ary[h]==key){
            return h;
        }
        var m = (l+h)/2:int;
        if ((m==l) ) {
            return -1;
        }
        if (ary[m]==key ){
            return m;
        } else {
            if (ary[m]<key) {
                return binSearchE(ary,m+1,h,key);
            }
            else {
                return binSearchE(ary,l,m-1,key);
            }
        }
      }// end of binSearchE(...)

    /**
    * Preprocess a graph to remove all selfloops and duplicate edges and write back out to new file.
    *
    * cmd: operation to perform. 
    * payload: parameters from the python frontend. 
    * argSize: number of arguments. 
    * SymTab: symbol table used for storage. 
    *
    * returns: message back to Python.
    */
    proc segGraphPreProcessingMsg(cmd: string, msgArgs: borrowed MessageArgs, st: borrowed SymTab): MsgTuple throws {
        var NeS = msgArgs.getValueOf("NumOfEdges");
        var NvS = msgArgs.getValueOf("NumOfVertices");
        var ColS = msgArgs.getValueOf("NumOfColumns");
        var DirectedS = msgArgs.getValueOf("Directed");
        var FileName = msgArgs.getValueOf("FileName");
        var SkipLineS = msgArgs.getValueOf("SkipLines");
        var RemapVertexS = msgArgs.getValueOf("RemapFlag");
        var DegreeSortS = msgArgs.getValueOf("DegreeSortFlag");
        var RCMS = msgArgs.getValueOf("RCMFlag");
        var RwriteS = msgArgs.getValueOf("WriteFlag");
        var AlignedArrayS = msgArgs.getValueOf("AlignedFlag");

        var Ne:int = (NeS:int);
        var Nv:int = (NvS:int);
     
        var NumCol = ColS:int;
        var DirectedFlag:bool = false;
        var WeightedFlag:bool = false;

        var SkipLineNum:int = (SkipLineS:int);
        var timer:Timer;
        var RCMFlag:bool = false;
        var DegreeSortFlag:bool = false;
        var RemapVertexFlag:bool = false;
        var WriteFlag:bool = false;
        var AlignedArray:int = (AlignedArrayS:int);
        outMsg = "read file =" + FileName;
        smLogger.info(getModuleName(),getRoutineName(),getLineNumber(),outMsg);


        timer.start();
    
        var NewNe,NewNv:int;

        if (DirectedS:int)==1 {
            DirectedFlag=true;
        }
        if NumCol>2 {
            WeightedFlag=true;
        }
        if(RemapVertexS:int)==1 {
            RemapVertexFlag=true;
        }
        if (DegreeSortS:int)==1 {
            DegreeSortFlag=true;
        }
        if (RCMS:int)==1 {
            RCMFlag=true;
        }
        if (RwriteS:int)==1 {
            WriteFlag=true;
        }
        var src = makeDistArray(Ne,int);
        var edgeD=src.domain;

        var neighbor=makeDistArray(Nv,int);
        var vertexD=neighbor.domain;

        var dst,e_weight,srcR,dstR, iv: [edgeD] int ;
        var start_i,neighborR, start_iR,depth, v_weight: [vertexD] int;

        var linenum:int=0;
        var repMsg: string;

        var tmpmindegree:int = start_min_degree;

        // Check to see if the file can be opened correctly. 
        try {
            var f = open(FileName, iomode.r);
            f.close();
        } catch {
            smLogger.error(getModuleName(),getRoutineName(),getLineNumber(), "Error opening file.");
        }

        proc readLinebyLine() throws {
            coforall loc in Locales  {
                on loc {
                    var f = open(FileName, iomode.r);
                    var r = f.reader(kind=ionative);
                    var line:string;
                    var a,b,c:string;
                    var curline=0:int;
                    var srclocal=src.localSubdomain();
                    var ewlocal=e_weight.localSubdomain();
                    var mylinenum=SkipLineNum;

                    while r.readLine(line) {
                        if line[0]=="%" || line[0]=="#" {
                            continue;
                        }
                        if mylinenum>0 {
                            mylinenum-=1;
                            continue;
                        }
                        if NumCol==2 {
                            (a,b)=  line.splitMsgToTuple(2);
                        } else {
                            (a,b,c)=  line.splitMsgToTuple(3);
                        }
                        if a==b {
                            smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                                "self cycle "+ a +"->"+b);
                        }
                        if srclocal.contains(curline) {
                            src[curline]=(a:int);
                            dst[curline]=(b:int);
                        }
                        curline+=1;
                        if curline>srclocal.highBound {
                            break;
                        }
                    } 
                    if (curline<=srclocal.highBound) {
                        var myoutMsg="The input file " + FileName + " does not give enough edges for locale " + here.id:string +" current line="+curline:string;
                        smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),myoutMsg);
                    }
                    r.close();
                    f.close();
                }// end on loc
            }//end coforall
        }//end readLinebyLine


        readLinebyLine(); 
        NewNv=vertex_remap(src,dst,Nv);
      
        try  { 
            combine_sort(src, dst,e_weight,WeightedFlag, false);
        } catch {
            try! smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),"Combine sort error.");
        }

        set_neighbor(src,start_i,neighbor);

        // Read in undirected graph parts into reversed arrays.
        if (!DirectedFlag) {
            smLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),"Read undirected graph.");
            coforall loc in Locales  {
                on loc {
                    forall i in srcR.localSubdomain(){
                        srcR[i]=dst[i];
                        dstR[i]=src[i];
                    }
                }
            }
            try  { 
                combine_sort(srcR, dstR,e_weight,WeightedFlag, false);
            } catch {
                try!  smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),"Combine sort error");
            }
            set_neighbor(srcR,start_iR,neighborR);

            if (DegreeSortFlag) {
                degree_sort_u(src, dst, start_i, neighbor, srcR, dstR, start_iR, neighborR,e_weight,WeightedFlag);
            }
        }

        smLogger.debug(getModuleName(),getRoutineName(),getLineNumber(), "Remove self-loops and duplicated edges");
        var cur=0;
        var tmpsrc=src;
        var tmpdst=dst;
        for i in 0..Ne-1 {
            // Ignore self-loops. 
            if src[i]==dst[i] {
                continue;
            }
            if (cur==0) {
                tmpsrc[cur]=src[i];
                tmpdst[cur]=dst[i]; 
                cur+=1;
                continue;
            }
            // Ignore duplicated edges.
            if (tmpsrc[cur-1]==src[i]) && (tmpdst[cur-1]==dst[i]) {
                continue;
            } else {
                if (src[i]>dst[i]) {
                    var u=src[i]:int;
                    var v=dst[i]:int;
                    var lu=start_i[u]:int;
                    var nu=neighbor[u]:int;
                    var lv=start_i[v]:int;
                    var nv=neighbor[v]:int;
                    var DupE:int;
                    DupE = binSearchE(dst,lv,lv+nv-1,u);
                    //find v->u 
                    if DupE!=-1 {
                        continue;
                    }
                }

                tmpsrc[cur]=src[i];
                tmpdst[cur]=dst[i]; 
                cur+=1;
            }
        }
        NewNe=cur;    
 
        if (NewNe<Ne ) {
            smLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),
                "removed "+(Ne-NewNe):string +" edges");

            var mysrc=makeDistArray(NewNe,int);
            var myedgeD=mysrc.domain;

            var myneighbor=makeDistArray(NewNv,int);
            var myvertexD=myneighbor.domain;

            var mydst,mye_weight,mysrcR,mydstR, myiv: [myedgeD] int ;
            var mystart_i,myneighborR, mystart_iR,mydepth, myv_weight: [myvertexD] int;

            forall i in 0..NewNe-1 {
                mysrc[i]=tmpsrc[i];
                mydst[i]=tmpdst[i];
            }
            try  { 
                combine_sort(mysrc, mydst,mye_weight,WeightedFlag, false);
            } catch {
                try!  smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),"Combine sort error");
            }

            set_neighbor(mysrc,mystart_i,myneighbor);

            if (!DirectedFlag) { //undirected graph
                coforall loc in Locales  {
                    on loc {
                        forall i in mysrcR.localSubdomain(){
                            mysrcR[i]=mydst[i];
                            mydstR[i]=mysrc[i];
                        }
                    }
                }
                try  { 
                    combine_sort(mysrcR, mydstR,mye_weight,WeightedFlag, false);
                } catch {
                    try!  smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),"Combine sort error");
                }
                set_neighbor(mysrcR,mystart_iR,myneighborR);
                if (DegreeSortFlag) {
                    degree_sort_u(mysrc, mydst, mystart_i, myneighbor, mysrcR, mydstR, mystart_iR, myneighborR,mye_weight,WeightedFlag);
                }
            }//end of undirected
            else {
                if (DegreeSortFlag) {
                    part_degree_sort(mysrc, mydst, mystart_i, myneighbor,mye_weight,myneighbor,WeightedFlag);
                }  
            }  
            if (WriteFlag) {
                var wf = open(FileName+".pr", iomode.cw);
                var mw = wf.writer(kind=ionative);
                for i in 0..NewNe-1 {
                    mw.writeln("%-15i    %-15i".format(mysrc[i],mydst[i]));
                }
                mw.writeln("Num Edge=%i  Num Vertex=%i".format(NewNe, NewNv));
                mw.close();
                wf.close();
            }
            } else {
                if (WriteFlag) {
                    var wf = open(FileName+".pr", iomode.cw);
                    var mw = wf.writer(kind=ionative);
                    for i in 0..NewNe-1 {
                        mw.writeln("%-15i    %-15i".format(src[i],dst[i]));
                    }
                    mw.writeln("Num Edge=%i  Num Vertex=%i".format(NewNe, NewNv));
                    mw.close();
                    wf.close();
                }
            }
        timer.stop();
        outMsg="PreProcessing  File takes " + timer.elapsed():string;
        smLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),outMsg);
        repMsg =  "PreProcessing success"; 
        return new MsgTuple(repMsg, MsgType.NORMAL);
    } // end of segGraphPreProcessingMsg

    // directly read a graph from given file and build the SegGraph class in memory
    proc segGraphFileMsg(cmd: string, msgArgs: borrowed MessageArgs, st: borrowed SymTab): MsgTuple throws {
        var NeS=msgArgs.getValueOf("NumOfEdges");
        var NvS=msgArgs.getValueOf("NumOfVertices");
        var ColS=msgArgs.getValueOf("NumOfColumns");
        var DirectedS=msgArgs.getValueOf("Directed");
        var FileName=msgArgs.getValueOf("FileName");
        var RemapVertexS=msgArgs.getValueOf("RemapFlag");
        var DegreeSortS=msgArgs.getValueOf("DegreeSortFlag");
        var RCMS=msgArgs.getValueOf("RCMFlag");
        var RwriteS=msgArgs.getValueOf("WriteFlag");

        var Ne:int =(NeS:int);
        var Nv:int =(NvS:int);
        var NumCol=ColS:int;
        var DirectedFlag:bool=false;
        var WeightedFlag:bool=false;
        var timer: Timer;
        var RCMFlag:bool=false;
        var DegreeSortFlag:bool=false;
        var RemapVertexFlag:bool=false;
        var WriteFlag:bool=false;
        outMsg="read file ="+FileName;
        smLogger.info(getModuleName(),getRoutineName(),getLineNumber(),outMsg);
        timer.start();

        if (DirectedS:int)==1 {
            DirectedFlag=true;
        }
        if NumCol>2 {
            WeightedFlag=true;
        }
        if (RemapVertexS:int)==1 {
            RemapVertexFlag=true;
        }
        if (DegreeSortS:int)==1 {
            DegreeSortFlag=true;
        }
        if (RCMS:int)==1 {
            RCMFlag=true;
        }
        if (RwriteS:int)==1 {
            WriteFlag=true;
        }
        var src=makeDistArray(Ne,int);
        var edgeD=src.domain;

        var neighbor=makeDistArray(Nv,int);
        var vertexD=neighbor.domain;

        var dst,e_weight,srcR,dstR, iv: [edgeD] int ;
        var start_i,neighborR, start_iR,depth, v_weight: [vertexD] int;

        var linenum:int=0;
        var repMsg: string;

        var tmpmindegree:int =start_min_degree;

        try {
            var f = open(FileName, iomode.r);
            // we check if the file can be opened correctly
            f.close();
        } catch {
            smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),"Open file error");
        }

        proc readLinebyLine() throws {
            coforall loc in Locales  {
                on loc {
                    var f = open(FileName, iomode.r);
                    var r = f.reader(kind=ionative);
                    var line:string;
                    var a,b,c:string;
                    var curline=0:int;
                    var srclocal=src.localSubdomain();
                    var ewlocal=e_weight.localSubdomain();

                    while r.readLine(line) {
                        if line[0]=="%" {
                            smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),"edge  error");
                            continue;
                        }
                        if NumCol==2 {
                            (a,b)=  line.splitMsgToTuple(2);
                        } else {
                            (a,b,c)=  line.splitMsgToTuple(3);
                        }
                        if a==b {
                            smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),"self cycle "+ a +"->"+b);
                        }
                        if (RemapVertexFlag) {
                            if srclocal.contains(curline) {
                                src[curline]=(a:int);
                                dst[curline]=(b:int);
                            }
                        } else {
                            if srclocal.contains(curline) {
                                src[curline]=(a:int)%Nv;
                                dst[curline]=(b:int)%Nv;
                            }
                        }
                        curline+=1;
                        if curline>srclocal.highBound {
                            break;
                        }
                    } 
                    if (curline<=srclocal.highBound) {
                        var myoutMsg="The input file " + FileName + " does not give enough edges for locale " + here.id:string +" current line="+curline:string;
                        smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),myoutMsg);
                    }
                    r.close();
                    f.close();
                }// end on loc
            }//end coforall
        }//end readLinebyLine
      
        // readLinebyLine sets ups src, dst, start_i, neightbor.  e_weights will also be set if it is an edge weighted graph
        // currently we ignore the weight.

        readLinebyLine(); 
        timer.stop();

        outMsg="Reading File takes " + timer.elapsed():string;
        smLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),outMsg);

        timer.clear();
        timer.start();
        try  { 
            combine_sort(src, dst,e_weight,WeightedFlag, false);
        } catch {
            try!  smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),"combine sort error");
        }

      set_neighbor(src,start_i,neighbor);

      // Make a composable SegGraph object that we can store in a GraphSymEntry later
        var graph = new shared SegGraph(Ne, Nv, DirectedFlag);
        graph.withSRC(new shared SymEntry(src):GenSymEntry)
            .withDST(new shared SymEntry(dst):GenSymEntry)
            .withSTART_IDX(new shared SymEntry(start_i):GenSymEntry)
            .withNEIGHBOR(new shared SymEntry(neighbor):GenSymEntry);

        if (!DirectedFlag) { //undirected graph
            coforall loc in Locales  {
                on loc {
                    forall i in srcR.localSubdomain(){
                        srcR[i]=dst[i];
                        dstR[i]=src[i];
                    }
                }
            }
            try  { 
                combine_sort(srcR, dstR,e_weight,WeightedFlag, false);
            } catch {
                try! smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),"combine sort error");
            }
                set_neighbor(srcR,start_iR,neighborR);

            if (DegreeSortFlag) {
                degree_sort_u(src, dst, start_i, neighbor, srcR, dstR, start_iR, neighborR,e_weight,WeightedFlag);
            }

            graph.withSRC_R(new shared SymEntry(srcR):GenSymEntry)
                .withDST_R(new shared SymEntry(dstR):GenSymEntry)
                .withSTART_IDX_R(new shared SymEntry(start_iR):GenSymEntry)
                .withNEIGHBOR_R(new shared SymEntry(neighborR):GenSymEntry);

        }//end of undirected
        else {
            if (DegreeSortFlag) {
                part_degree_sort(src, dst, start_i, neighbor,e_weight,neighbor,WeightedFlag);
            }
        }//end of else
        if (WriteFlag) {
            var wf = open(FileName+".my.gr", iomode.cw);
            var mw = wf.writer(kind=ionative);
            for i in 0..Ne-1 {
                mw.writeln("%-15n    %-15n".format(src[i],dst[i]));
            }
            mw.close();
            wf.close();
        }
        var sNv=Nv:string;
        var sNe=Ne:string;
        var sDirected:string;
        var sWeighted:string;
        if (DirectedFlag) {
            sDirected="1";
        } else {
            sDirected="0";
        }

        if (WeightedFlag) {
            sWeighted="1";
        } else {
            sWeighted="0";
        }
        var graphEntryName = st.nextName();
        var graphSymEntry = new shared GraphSymEntry(graph);
        st.addEntry(graphEntryName, graphSymEntry);
        repMsg =  sNv + '+ ' + sNe + '+ ' + sDirected + '+ ' + sWeighted + '+' +  graphEntryName; 
        timer.stop();
        outMsg="Sorting Edges takes "+ timer.elapsed():string;
        smLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),outMsg);
        smLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),repMsg);
        return new MsgTuple(repMsg, MsgType.NORMAL);
    } // end of segGraphFileMsg

    use CommandMap;
    registerFunction("segmentedGraphFile",segGraphFileMsg,getModuleName());
    registerFunction("segmentedGraphPreProcessing", segGraphPreProcessingMsg,getModuleName());
}