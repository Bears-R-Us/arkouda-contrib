module GraphMsg {
    // Chapel modules.
    use Reflection;
    use Set;
    use Time; 
    use Sort; 
    
    // Arachne Modules.
    use Utils; 
    use GraphArray;
    
    // Arkouda modules.
    use MultiTypeSymbolTable;
    use MultiTypeSymEntry;
    use ServerConfig;
    use ArgSortMsg;
    use AryUtil;
    use Logging;
    use Message;
    
    // Server message logger. 
    private config const logLevel = LogLevel.DEBUG;
    const smLogger = new Logger(logLevel);
    var outMsg:string;

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
    }// end set_neighbor()

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
    }// end bin_search_v()

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
    private proc combine_sort(lsrc: [?D1] int, ldst: [?D2] int, le_weight: [?D3] real, 
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
        // TODO: Does this have to be a proc within a proc?
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
        }// end mergedArgsort()

        try {
            if (totalDigits <= 2) {
                iv = mergedArgsort(2);
            } else {
                iv = mergedArgsort(4);
            }
        } catch {
            try! smLogger.error(getModuleName(), getRoutineName(), getLineNumber(),
                                "Merge array error.");
        }

        var tmpedges = lsrc[iv];
        lsrc = tmpedges;
        tmpedges = ldst[iv];
        ldst = tmpedges;

        if (lWeightedFlag && sortw) {
          var tmpedges = le_weight[iv];
          le_weight = tmpedges;
        }
    }//end combine_sort()

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
                                  lneighbor: [?D4] int, le_weight: [?D5] real, lneighborR: [?D6] int,
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
    }// end part_degree_sort()

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
    // TODO: degree_sort_u() exists and will be used, but not in this pull request saved for future.
    private proc degree_sort_u(lsrc: [?D1] int, ldst: [?D2] int, lstart_i: [?D3] int,
                               lneighbor: [?D4] int, lsrcR: [?D5] int, ldstR: [?D6] int,
                               lstart_iR: [?D7] int, lneighborR: [?D8] int, le_weight: [?D9] real,
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
    }// end of binSearchE()

    /**
    * Read a graph whose number of vertices and edges are known before analysis. Saves time in 
    * building the graph data structure. 
    *
    * cmd: operation to perform. 
    * msgArgs: arugments passed to backend. 
    * SymTab: symbol table used for storage. 
    *
    * returns: message back to Python.
    */
    proc readKnownEdgelistMsg(cmd: string, msgArgs: borrowed MessageArgs, st: borrowed SymTab): 
                              MsgTuple throws {
        // Parse the message from Python to extract needed data. 
        var neS = msgArgs.getValueOf("NumOfEdges");
        var nvS = msgArgs.getValueOf("NumOfVertices");
        var pathS = msgArgs.getValueOf("Path");
        var weightedS = msgArgs.getValueOf("Weighted");
        var directedS = msgArgs.getValueOf("Directed");
        var commentsS = msgArgs.getValueOf("Comments");
        var filetypeS = msgArgs.getValueOf("FileType");

        // Convert parsed message to needed data types for Chapel operations.
        var ne:int = (neS:int);
        var nv:int = (nvS:int);
        var path:string = (pathS:string);

        var weighted:bool; 
        weightedS = weightedS.toLower();
        weighted = (weightedS:bool);

        var directed:bool;
        directedS = directedS.toLower();
        directed = (directedS:bool);

        var comments:string = (commentsS:string);
        var filetype:string = (filetypeS:string);

        // Write message to show which file was read in. 
        outMsg = "path of read file = " + path;
        smLogger.info(getModuleName(),getRoutineName(),getLineNumber(),outMsg);

        // Graph data structure building timer. 
        var timer:stopwatch;
        timer.start();

        // Initializing the arrays that make up our double-index data structure.
        var src = makeDistArray(ne,int);
        var edge_domain = src.domain;

        var neighbor = makeDistArray(nv,int);
        var vertex_domain = neighbor.domain;

        // TODO: We intitialize memory we do not need. For example, directed graphs do not require
        //       reversed arrays. This must be fixed, but may require significant code changes.
        // Edge index arrays. 
        var dst, srcR, dstR, iv: [edge_domain] int;
        var e_weight, e_weightR: [edge_domain] real;
        // Vertex index arrays. 
        var start_i, neighborR, start_iR,depth: [vertex_domain] int;

        // Check to see if the file can be opened correctly. 
        try {
            var f = open(path, iomode.r);
            f.close();
        } catch {
            smLogger.error(getModuleName(),getRoutineName(),getLineNumber(), "Error opening file.");
        }

        // Read the file line by line. 
        readLinebyLine(src, dst, e_weight, path, comments, weighted);

        // Sort our edge arrays for easy lookup of neighbor vertices. 
        if (!weighted) {
            try { 
                combine_sort(src, dst, e_weight, weighted, false);
            } catch {
                try! smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                                    "Combine sort error.");
            }
        } else {
            try { 
                combine_sort(src, dst, e_weight, weighted, true);
            } catch {
                try! smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                                    "Combine sort error.");
            }
        }

        // Set neighbor (vertex index array) information based off edges, 
        set_neighbor(src, start_i, neighbor);

        // Create the reversed arrays for undirected graphs
        if (!directed) {
            smLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),
                           "Read undirected graph.");
            coforall loc in Locales  {
                on loc {
                    forall i in srcR.localSubdomain(){
                        srcR[i] = dst[i];
                        dstR[i] = src[i];

                        if (weighted) {
                            e_weightR = e_weight[i];
                        }
                    }
                }
            }
            if (!weighted) {
                try  { 
                    combine_sort(srcR, dstR, e_weightR, weighted, false);
                } catch {
                    try! smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),"Combine sort error");
                }
            } else {
                try  { 
                    combine_sort(srcR, dstR, e_weightR, weighted, true);
                } catch {
                    try! smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),"Combine sort error");
                }
            }
            set_neighbor(srcR,start_iR,neighborR);
        }

        // Add graph data structure to the symbol table. 
        var graph = new shared SegGraph(ne, nv, directed, weighted);
        graph.withSRC(new shared SymEntry(src):GenSymEntry)
             .withDST(new shared SymEntry(dst):GenSymEntry)
             .withSTART_IDX(new shared SymEntry(start_i):GenSymEntry)
             .withNEIGHBOR(new shared SymEntry(neighbor):GenSymEntry);

        if (!directed) {
            graph.withSRC_R(new shared SymEntry(srcR):GenSymEntry)
                 .withDST_R(new shared SymEntry(dstR):GenSymEntry)
                 .withSTART_IDX_R(new shared SymEntry(start_iR):GenSymEntry)
                 .withNEIGHBOR_R(new shared SymEntry(neighborR):GenSymEntry);
        }

        if (weighted) {
            graph.withEDGE_WEIGHT(new shared SymEntry(e_weight):GenSymEntry);

            if (!directed) {
                graph.withEDGE_WEIGHT_R(new shared SymEntry(e_weightR):GenSymEntry);
            }
        }

        // Print for debugging server-side from Utils.chpl. 
        if(debug_print) {
            print_graph_serverside(neighbor, start_i, src, dst, neighborR, start_iR, srcR, dstR, 
                                   e_weight, e_weightR, directed, weighted);
        }

        // Add graph to the specific symbol table entry. 
        var graphEntryName = st.nextName();
        var graphSymEntry = new shared GraphSymEntry(graph);
        st.addEntry(graphEntryName, graphSymEntry);
        var repMsg = nvS + '+ ' + neS + '+ ' + directedS + '+ ' + weighted:int:string + '+' + graphEntryName;
        
        // Print out the length of time it takes to read in and build a known graph file.
        timer.stop();
        outMsg = "Building graph from known edge file takes " + timer.elapsed():string;
        
        // Print out debug information to arkouda server output. 
        smLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),outMsg);
        smLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),repMsg);

        return new MsgTuple(repMsg, MsgType.NORMAL);
    } // end of readKnownEdgelistMsg

    /**
    * Read a graph whose number of vertices and edges are unknown before analysis.
    *
    * cmd: operation to perform. 
    * msgArgs: arugments passed to backend. 
    * SymTab: symbol table used for storage. 
    *
    * returns: message back to Python.
    */
    proc readEdgelistMsg(cmd: string, msgArgs: borrowed MessageArgs, st: borrowed SymTab): MsgTuple throws {
        // Parse the message from Python to extract needed data. 
        var pathS = msgArgs.getValueOf("Path");
        var weightedS = msgArgs.getValueOf("Weighted");
        var directedS = msgArgs.getValueOf("Directed");
        var commentsS = msgArgs.getValueOf("Comments");
        var filetypeS = msgArgs.getValueOf("FileType");

        // Convert parsed message to needed data types for Chapel operations.
        var path:string = (pathS:string);

        var weighted:bool; 
        weightedS = weightedS.toLower();
        weighted = (weightedS:bool);

        var directed:bool;
        directedS = directedS.toLower();
        directed = (directedS:bool);

        var comments:string = (commentsS:string);
        var filetype:string = (filetypeS:string);

        if (filetype == "mtx") {
            comments = "%";
        }

        // Graph data structure building timer. 
        var timer:stopwatch;
        timer.start();

        // Check to see if the file can be opened correctly. 
        try {
            var f = open(path, iomode.r);
            f.close();
        } catch {
            smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),"Error opening file.");
        }

        // Perform a first pass over the file to get number of edges and vertices.
        var f = open(path, iomode.r);
        var r = f.reader(kind = ionative);
        var line:string;
        var a,b,c:string;
        var edge_count:int = 0;

        // Add vertices to a set and count number of lines which is number of edges.
        var vertex_set = new set(int, parSafe = true);
        while (r.readLine(line)) {
            // Ignore comments for all files and matrix dimensions for mtx files.
            if (line[0] == comments) {
                edge_count -= 1; 
                continue;
            } else {
                if (edge_count < 0) {
                    edge_count = 0; 
                    continue;
                }
            }

            // Parse our vertices and weights, if applicable. 
            if (weighted == false) {
                (a,b) = line.splitMsgToTuple(2);
            } else {
                (a,b,c) = line.splitMsgToTuple(3);
            }
            
            // Add vertices to a vertex_set. 
            vertex_set.add(a:int);
            vertex_set.add(b:int);

            // Keep track of the number of edges read from file lines. 
            edge_count += 1;
        }

        // Write the number of edges and vertices. 
        var ne:int = edge_count; 
        var nv:int = (vertex_set.size:int);

        // Initializing the arrays that make up our double-index data structure.
        var src = makeDistArray(ne, int);
        var edge_domain = src.domain;

        var neighbor = makeDistArray(nv,int);
        var vertex_domain = neighbor.domain;

        // TODO: We intitialize memory we do not need. For example, directed graphs do not require
        //       reversed arrays. This must be fixed, but may require significant code changes.
        // Edge index arrays. 
        var dst, srcR, dstR, iv: [edge_domain] int;
        var e_weight, e_weightR: [edge_domain] real;
        // Vertex index arrays. 
        var start_i, neighborR, start_iR,depth: [vertex_domain] int;

        // Read the file line by line.
        readLinebyLine(src, dst, e_weight, path, comments, weighted); 
        
        // Remap the vertices to a new range.
        var new_nv:int = vertex_remap(src, dst, nv);
      
        if (!weighted) {
            try { 
                combine_sort(src, dst, e_weight, weighted, false);
            } catch {
                try! smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),"Combine sort error.");
            }
        } else {
            try { 
                combine_sort(src, dst, e_weight, weighted, true);
            } catch {
                try! smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),"Combine sort error.");
            }
        }

        // Set neighbor (vertex index array) information based off edges,
        set_neighbor(src, start_i, neighbor);

        // Read in undirected graph parts into reversed arrays.
        if (!directed) {
            smLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),"Read undirected graph.");
            coforall loc in Locales  {
                on loc {
                    forall i in srcR.localSubdomain(){
                        srcR[i] = dst[i];
                        dstR[i] = src[i];
                        e_weightR = e_weight[i];
                    }
                }
            }
            if (!weighted) {
                try  { 
                    combine_sort(srcR, dstR, e_weightR, weighted, false);
                } catch {
                    try!  smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                                        "Combine sort error");
                }
            } else {
                try  { 
                    combine_sort(srcR, dstR, e_weightR, weighted, false);
                } catch {
                    try!  smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                                        "Combine sort error");
                }
            }
            set_neighbor(srcR, start_iR, neighborR);
        }

        // Remove self loops and duplicated edges.
        smLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),
                       "Remove self loops and duplicated edges");
        var cur = 0;
        var tmpsrc = src;
        var tmpdst = dst;
        var tmpe_weight = e_weight;
        
        for i in 0..ne - 1 {
            // Ignore self-loops. 
            if src[i]==dst[i] {
                continue;
            }
            if (cur == 0) {
                tmpsrc[cur] = src[i];
                tmpdst[cur] = dst[i]; 
                tmpe_weight[cur] = e_weight[i];
                cur += 1;
                continue;
            }
            
            // Ignore duplicated edges.
            if (tmpsrc[cur-1] == src[i]) && (tmpdst[cur-1] == dst[i]) {
                continue;
            } else {
                if (src[i] > dst[i]) {
                    var u = src[i]:int;
                    var v = dst[i]:int;
                    var lu = start_i[u]:int;
                    var nu = neighbor[u]:int;
                    var lv = start_i[v]:int;
                    var nv = neighbor[v]:int;
                    var DupE:int;
                    
                    // Find v->u.
                    DupE = binSearchE(dst,lv,lv+nv-1,u);
                    if (DupE != -1) {
                        continue;
                    }
                }
                tmpsrc[cur] = src[i];
                tmpdst[cur] = dst[i]; 
                tmpe_weight[cur] = e_weight[i]; 
                cur+=1;
            }
        }
        var new_ne = cur;  
 
        var mysrc = makeDistArray(new_ne, int);
        var myedgeD = mysrc.domain;

        var myneighbor = makeDistArray(new_nv, int);
        var myvertexD=myneighbor.domain;

        // Arrays made from the edge domain. 
        var mydst, mysrcR, mydstR, myiv: [myedgeD] int;
        var mye_weight, mye_weightR: [myedgeD] real;

        // Arrays made from the vertex domain. 
        var mystart_i, myneighborR, mystart_iR, mydepth: [myvertexD] int;
        
        // Finish creating the new arrays after removing self-loops and multiedges.
        if (new_ne < ne ) {
            smLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),
                "Removed " + (ne - new_ne):string + " edges");

            forall i in 0..new_ne-1 {
                mysrc[i] = tmpsrc[i];
                mydst[i] = tmpdst[i];
                mye_weight[i] = tmpe_weight[i];
            }
            try { 
                combine_sort(mysrc, mydst, mye_weight, weighted, false);
            } catch {
                try! smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                                    "Combine sort error.");
            }

            set_neighbor(mysrc, mystart_i, myneighbor);

            if (!directed) { // undirected graph
                coforall loc in Locales  {
                    on loc {
                        forall i in mysrcR.localSubdomain(){
                            mysrcR[i] = mydst[i];
                            mydstR[i] = mysrc[i];
                            mye_weightR[i] = mye_weight[i];
                        }
                    }
                }

                if(!weighted) {
                    try  { 
                        combine_sort(mysrcR, mydstR, mye_weightR, weighted, false);
                    } catch {
                        try! smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                                            "Combine sort error");
                    }
                } else {
                    try  { 
                        combine_sort(mysrcR, mydstR, mye_weightR, weighted, true);
                    } catch {
                        try! smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                                            "Combine sort error");
                    }
                }
                
                set_neighbor(mysrcR, mystart_iR, myneighborR);
            }//end of undirected
        }

        // Finish building graph data structure.
        var graph = new shared SegGraph(ne, nv, directed, weighted);
        if (new_ne < ne) { // Different arrays for when edges had to be removed.
            // Print for debugging server-side from Utils.chpl. 
            if(debug_print) {
                print_graph_serverside(myneighbor, mystart_i, mysrc, mydst, myneighborR, mystart_iR, mysrcR, mydstR, 
                                    mye_weight, mye_weightR, directed, weighted);
            }

            graph.withSRC(new shared SymEntry(mysrc):GenSymEntry)
                .withDST(new shared SymEntry(mydst):GenSymEntry)
                .withSTART_IDX(new shared SymEntry(mystart_i):GenSymEntry)
                .withNEIGHBOR(new shared SymEntry(myneighbor):GenSymEntry);

            if (!directed) {
                graph.withSRC_R(new shared SymEntry(mysrcR):GenSymEntry)
                    .withDST_R(new shared SymEntry(mydstR):GenSymEntry)
                    .withSTART_IDX_R(new shared SymEntry(mystart_iR):GenSymEntry)
                    .withNEIGHBOR_R(new shared SymEntry(myneighborR):GenSymEntry);
            }

            if (weighted) {
                graph.withEDGE_WEIGHT(new shared SymEntry(mye_weight):GenSymEntry);

                if (!directed) {
                    graph.withEDGE_WEIGHT_R(new shared SymEntry(mye_weightR):GenSymEntry);
                }
            }
        } else { // No edge removals.
            // Print for debugging server-side from Utils.chpl. 
            if(debug_print) {
                print_graph_serverside(neighbor, start_i, src, dst, neighborR, start_iR, srcR, dstR, 
                                    e_weight, e_weightR, directed, weighted);
            }

            graph.withSRC(new shared SymEntry(src):GenSymEntry)
                .withDST(new shared SymEntry(dst):GenSymEntry)
                .withSTART_IDX(new shared SymEntry(start_i):GenSymEntry)
                .withNEIGHBOR(new shared SymEntry(neighbor):GenSymEntry);

            if (!directed) {
                graph.withSRC_R(new shared SymEntry(srcR):GenSymEntry)
                    .withDST_R(new shared SymEntry(dstR):GenSymEntry)
                    .withSTART_IDX_R(new shared SymEntry(start_iR):GenSymEntry)
                    .withNEIGHBOR_R(new shared SymEntry(neighborR):GenSymEntry);
            }

            if (weighted) {
                graph.withEDGE_WEIGHT(new shared SymEntry(e_weight):GenSymEntry);

                if (!directed) {
                    graph.withEDGE_WEIGHT_R(new shared SymEntry(e_weightR):GenSymEntry);
                }
            }
        }

        // Add graph to the specific symbol table entry. 
        var graphEntryName = st.nextName();
        var graphSymEntry = new shared GraphSymEntry(graph);
        st.addEntry(graphEntryName, graphSymEntry);
        var repMsg = new_nv:string + '+ ' + new_ne:string + '+ ' + directedS + '+ ' + weighted:int:string + '+' + graphEntryName;
        
        // Print out the length of time it takes to read in and build a known graph file.
        timer.stop();
        outMsg = "Building graph from unknown edge file takes " + timer.elapsed():string;
        
        // Print out debug information to arkouda server output. 
        smLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),outMsg);
        smLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),repMsg);

        return new MsgTuple(repMsg, MsgType.NORMAL);
    } // end of readEdgelistMsg

    /**
    * Convert akarrays to a graph object. 
    *
    * cmd: operation to perform. 
    * msgArgs: arugments passed to backend. 
    * SymTab: symbol table used for storage. 
    *
    * returns: message back to Python.
    */
    proc addEdgesFromMsg(cmd: string, msgArgs: borrowed MessageArgs, st: borrowed SymTab): MsgTuple throws {
        // Parse the message from Python to extract needed data. 
        var akarray_srcS = msgArgs.getValueOf("AkArraySrc");
        var akarray_dstS = msgArgs.getValueOf("AkArrayDst");
        var akarray_weightS = msgArgs.getValueOf("AkArrayWeight");
        var weightedS = msgArgs.getValueOf("Weighted");
        var directedS = msgArgs.getValueOf("Directed");

        // Convert parsed message to needed data types for Chapel operations.
        var src_name:string = (akarray_srcS:string);
        var dst_name:string = (akarray_dstS:string);
        var weight_name:string = (akarray_weightS:string);

        var weighted:bool; 
        weightedS = weightedS.toLower();
        weighted = (weightedS:bool);

        var directed:bool;
        directedS = directedS.toLower();
        directed = (directedS:bool);

        // Graph data structure building timer. 
        var timer:stopwatch;
        timer.start();

        // Extract the entry names from the symbol table to extract the data for use.
        var akarray_src_entry: borrowed GenSymEntry = getGenericTypedArrayEntry(src_name, st);
        var akarray_dst_entry: borrowed GenSymEntry = getGenericTypedArrayEntry(dst_name, st);

        // Extract the data for use. 
        var akarray_src_sym = toSymEntry(akarray_src_entry,int);
        var src = akarray_src_sym.a;

        var akarray_dst_sym = toSymEntry(akarray_dst_entry,int);
        var dst = akarray_dst_sym.a;

        // Perform a first pass over the data to get number of edges and vertices.
        var a,b,c:string;
        var curline:int = 0;

        // Add vertices to a set and count number of lines which is number of edges.
        var vertex_set = new set(int, parSafe = true);
        forall (u,v) in zip(src, dst) with (ref vertex_set){            
            // Add vertices to a vertex_set. 
            vertex_set.add(u:int);
            vertex_set.add(v:int);
        }

        // Write the number of edges and vertices. 
        var ne:int = src.size:int; 
        var nv:int = (vertex_set.size:int);

        // Initializing the arrays that make up our double-index data structure.
        var edge_domain = src.domain;

        var neighbor = makeDistArray(nv,int);
        var vertex_domain = neighbor.domain;

        // TODO: We intitialize memory we do not need. For example, directed graphs do not require
        //       reversed arrays. This must be fixed, but may require significant code changes.
        // Edge index arrays. 
        var srcR, dstR, iv: [edge_domain] int;
        var e_weight, e_weightR: [edge_domain] real;
        // Vertex index arrays. 
        var start_i, neighborR, start_iR,depth: [vertex_domain] int;

        if weighted {
            var akarray_weight_entry: borrowed GenSymEntry = getGenericTypedArrayEntry(weight_name, st);
            var akarray_weight_sym = toSymEntry(akarray_weight_entry, real);
            e_weight = akarray_weight_sym.a;
        }

        // Remap the vertices to a new range.
        var new_nv:int = vertex_remap(src, dst, nv);
      
        if (!weighted) {
            try { 
                combine_sort(src, dst, e_weight, weighted, false);
            } catch {
                try! smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),"Combine sort error.");
            }
        } else {
            try { 
                combine_sort(src, dst, e_weight, weighted, true);
            } catch {
                try! smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),"Combine sort error.");
            }
        }

        // Set neighbor (vertex index array) information based off edges,
        set_neighbor(src, start_i, neighbor);

        // Read in undirected graph parts into reversed arrays.
        if (!directed) {
            smLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),"Read undirected graph.");
            coforall loc in Locales  {
                on loc {
                    forall i in srcR.localSubdomain(){
                        srcR[i] = dst[i];
                        dstR[i] = src[i];
                        e_weightR = e_weight[i];
                    }
                }
            }
            if (!weighted) {
                try  { 
                    combine_sort(srcR, dstR, e_weightR, weighted, false);
                } catch {
                    try!  smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                                        "Combine sort error");
                }
            } else {
                try  { 
                    combine_sort(srcR, dstR, e_weightR, weighted, false);
                } catch {
                    try!  smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                                        "Combine sort error");
                }
            }
            set_neighbor(srcR, start_iR, neighborR);
        }

        // Remove self loops and duplicated edges.
        smLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),
                       "Remove self loops and duplicated edges");
        var cur = 0;
        var tmpsrc = src;
        var tmpdst = dst;
        var tmpe_weight = e_weight;
        
        for i in 0..ne - 1 {
            // Ignore self-loops. 
            if src[i]==dst[i] {
                continue;
            }
            if (cur == 0) {
                tmpsrc[cur] = src[i];
                tmpdst[cur] = dst[i]; 
                tmpe_weight[cur] = e_weight[i];
                cur += 1;
                continue;
            }
            
            // Ignore duplicated edges.
            if (tmpsrc[cur-1] == src[i]) && (tmpdst[cur-1] == dst[i]) {
                continue;
            } else {
                if (src[i] > dst[i]) {
                    var u = src[i]:int;
                    var v = dst[i]:int;
                    var lu = start_i[u]:int;
                    var nu = neighbor[u]:int;
                    var lv = start_i[v]:int;
                    var nv = neighbor[v]:int;
                    var DupE:int;
                    
                    // Find v->u.
                    DupE = binSearchE(dst,lv,lv+nv-1,u);
                    if (DupE != -1) {
                        continue;
                    }
                }
                tmpsrc[cur] = src[i];
                tmpdst[cur] = dst[i]; 
                tmpe_weight[cur] = e_weight[i]; 
                cur+=1;
            }
        }
        var new_ne = cur;  
 
        var mysrc = makeDistArray(new_ne, int);
        var myedgeD = mysrc.domain;

        var myneighbor = makeDistArray(new_nv, int);
        var myvertexD=myneighbor.domain;

        // Arrays made from the edge domain. 
        var mydst, mysrcR, mydstR, myiv: [myedgeD] int;
        var mye_weight, mye_weightR: [myedgeD] real;

        // Arrays made from the vertex domain. 
        var mystart_i, myneighborR, mystart_iR, mydepth: [myvertexD] int;
        
        // Finish creating the new arrays after removing self-loops and multiedges.
        if (new_ne < ne ) {
            smLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),
                "Removed " + (ne - new_ne):string + " edges");

            forall i in 0..new_ne-1 {
                mysrc[i] = tmpsrc[i];
                mydst[i] = tmpdst[i];
                mye_weight[i] = tmpe_weight[i];
            }
            try { 
                combine_sort(mysrc, mydst, mye_weight, weighted, false);
            } catch {
                try! smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                                    "Combine sort error.");
            }

            set_neighbor(mysrc, mystart_i, myneighbor);

            if (!directed) { // undirected graph
                coforall loc in Locales  {
                    on loc {
                        forall i in mysrcR.localSubdomain(){
                            mysrcR[i] = mydst[i];
                            mydstR[i] = mysrc[i];
                            mye_weightR[i] = mye_weight[i];
                        }
                    }
                }

                if(!weighted) {
                    try  { 
                        combine_sort(mysrcR, mydstR, mye_weightR, weighted, false);
                    } catch {
                        try! smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                                            "Combine sort error");
                    }
                } else {
                    try  { 
                        combine_sort(mysrcR, mydstR, mye_weightR, weighted, true);
                    } catch {
                        try! smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                                            "Combine sort error");
                    }
                }
                set_neighbor(mysrcR, mystart_iR, myneighborR);
            }//end of undirected
        }

        // Finish building graph data structure.
        var graph = new shared SegGraph(ne, nv, directed, weighted);
        if (new_ne < ne) { // Different arrays for when edges had to be removed.
            // Print for debugging server-side from Utils.chpl. 
            if(debug_print) {
                print_graph_serverside(myneighbor, mystart_i, mysrc, mydst, myneighborR, mystart_iR, mysrcR, mydstR, 
                                    mye_weight, mye_weightR, directed, weighted);
            }

            graph.withSRC(new shared SymEntry(mysrc):GenSymEntry)
                .withDST(new shared SymEntry(mydst):GenSymEntry)
                .withSTART_IDX(new shared SymEntry(mystart_i):GenSymEntry)
                .withNEIGHBOR(new shared SymEntry(myneighbor):GenSymEntry);

            if (!directed) {
                graph.withSRC_R(new shared SymEntry(mysrcR):GenSymEntry)
                    .withDST_R(new shared SymEntry(mydstR):GenSymEntry)
                    .withSTART_IDX_R(new shared SymEntry(mystart_iR):GenSymEntry)
                    .withNEIGHBOR_R(new shared SymEntry(myneighborR):GenSymEntry);
            }

            if (weighted) {
                graph.withEDGE_WEIGHT(new shared SymEntry(mye_weight):GenSymEntry);

                if (!directed) {
                    graph.withEDGE_WEIGHT_R(new shared SymEntry(mye_weightR):GenSymEntry);
                }
            }
        } else { // No edge removals.
            // Print for debugging server-side from Utils.chpl. 
            if(debug_print) {
                print_graph_serverside(neighbor, start_i, src, dst, neighborR, start_iR, srcR, dstR, 
                                    e_weight, e_weightR, directed, weighted);
            }

            graph.withSRC(new shared SymEntry(src):GenSymEntry)
                .withDST(new shared SymEntry(dst):GenSymEntry)
                .withSTART_IDX(new shared SymEntry(start_i):GenSymEntry)
                .withNEIGHBOR(new shared SymEntry(neighbor):GenSymEntry);

            if (!directed) {
                graph.withSRC_R(new shared SymEntry(srcR):GenSymEntry)
                    .withDST_R(new shared SymEntry(dstR):GenSymEntry)
                    .withSTART_IDX_R(new shared SymEntry(start_iR):GenSymEntry)
                    .withNEIGHBOR_R(new shared SymEntry(neighborR):GenSymEntry);
            }

            if (weighted) {
                graph.withEDGE_WEIGHT(new shared SymEntry(e_weight):GenSymEntry);

                if (!directed) {
                    graph.withEDGE_WEIGHT_R(new shared SymEntry(e_weightR):GenSymEntry);
                }
            }
        }

        // Add graph to the specific symbol table entry. 
        var graphEntryName = st.nextName();
        var graphSymEntry = new shared GraphSymEntry(graph);
        st.addEntry(graphEntryName, graphSymEntry);
        var repMsg = new_nv:string + '+ ' + new_ne:string + '+ ' + directedS + '+ ' + weighted:int:string + '+' + graphEntryName;
        
        // Print out the length of time it takes to read in and build a known graph file.
        timer.stop();
        outMsg = "Building graph from two edge arrays takes " + timer.elapsed():string;
        
        // Print out debug information to arkouda server output. 
        smLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),outMsg);
        smLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),repMsg);

        return new MsgTuple(repMsg, MsgType.NORMAL);
    } // end of addEdgesFromMsg

    use CommandMap;
    registerFunction("readKnownEdgelist", readKnownEdgelistMsg, getModuleName());
    registerFunction("readEdgelist", readEdgelistMsg, getModuleName());
    registerFunction("addEdgesFrom", addEdgesFromMsg, getModuleName());
}