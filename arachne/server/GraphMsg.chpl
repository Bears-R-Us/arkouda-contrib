module GraphMsg {
    use IO;
    use Reflection;
    use Set;
    use Time; 
    
    use ArgSortMsg;
    use AryUtil;
    use GraphArray;
    use Logging;
    use Message;
    use MultiTypeSymbolTable;
    use MultiTypeSymEntry;
    use ServerConfig;
    
    private config const logLevel = LogLevel.DEBUG;
    const smLogger = new Logger(logLevel);
    var outMsg:string;

    config const start_min_degree = 1000000;

    private proc set_neighbour(lsrc:[?D1]int, lstart_i :[?D2] int, lneighbour :[?D3] int ){ 
        var Ne=D1.size;
        forall i in lstart_i {
            i = -1;
        }
        forall i in lneighbour {
            i = 0;
        }
        for i in 0..Ne-1 do {
             lneighbour[lsrc[i]]+=1;
             if (lstart_i[lsrc[i]] ==-1){
                 lstart_i[lsrc[i]]=i;
             }
        }
    }

  private proc binSearchV(ary:[?D] int,l:int,h:int,key:int):int {
                       if ( (l<D.lowBound) || (h>D.highBound) || (l<0)) {
                           return -1;
                       }
                       if ( (l>h) || ((l==h) && ( ary[l]!=key)))  {
                            return -1;
                       }
                       if (ary[l]==key){
                            return l;
                       }
                       if (ary[h]==key){
                            return h;
                       }
                       var m= (l+h)/2:int;
                       if ((m==l) ) {
                            return -1;
                       }
                       if (ary[m]==key ){
                            return m;
                       } else {
                            if (ary[m]<key) {
                              return binSearchV(ary,m+1,h,key);
                            }
                            else {
                                    return binSearchV(ary,l,m-1,key);
                            }
                       }
  }// end of proc

  // map vertex ID from a large range to 0..Nv-1
  private proc vertex_remap( lsrc:[?D1] int, ldst:[?D2] int, numV:int) :int throws {

          var numE=lsrc.size;
          var tmpe:[D1] int;
          var VertexMapping:[0..numV-1] int;

          var VertexSet= new set(int,parSafe = true);
          forall (i,j) in zip (lsrc,ldst) with (ref VertexSet) {
                VertexSet.add(i);
                VertexSet.add(j);
          }
          var vertexAry=VertexSet.toArray();
          if vertexAry.size!=numV {
               smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                         "number of vertices is not equal to the given number`");
          }
          smLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),
                         "Total Vertices="+vertexAry.size:string+" ? Nv="+numV:string);


          sort(vertexAry);
          forall i in 0..numE-1 {
               lsrc[i]=binSearchV(vertexAry,0,vertexAry.size-1,lsrc[i]);
               ldst[i]=binSearchV(vertexAry,0,vertexAry.size-1,ldst[i]);
          }
          return vertexAry.size; 

  }
      /* 
       * we sort the combined array [src dst] here
       */
  private proc combine_sort( lsrc:[?D1] int, ldst:[?D2] int, le_weight:[?D3] int,  lWeightedFlag: bool, sortw=false: bool )   {
             param bitsPerDigit = RSLSD_bitsPerDigit;
             var bitWidths: [0..1] int;
             var negs: [0..1] bool;
             var totalDigits: int;
             var size=D1.size;
             var iv:[D1] int;



             for (bitWidth, ary, neg) in zip(bitWidths, [lsrc,ldst], negs) {
                       (bitWidth, neg) = getBitWidth(ary);
                       totalDigits += (bitWidth + (bitsPerDigit-1)) / bitsPerDigit;
             }
             proc mergedArgsort(param halfDig):[D1] int throws {
                    param numBuckets = 1 << bitsPerDigit; // these need to be const for comms/performance reasons
                    param maskDigit = numBuckets-1;
                    var merged = makeDistArray(size, halfDig*2*uint(bitsPerDigit));
                    for jj in 0..size-1 {
                    //for (m,s,d ) in zip(merged, lsrc,ldst) {
                          forall i in 0..halfDig-1 {
                              // here we assume the vertex ID>=0
                              //m[i]=(  ((s:uint) >> ((halfDig-i-1)*bitsPerDigit)) & (maskDigit:uint) ):uint(bitsPerDigit);
                              //m[i+halfDig]=( ((d:uint) >> ((halfDig-i-1)*bitsPerDigit)) & (maskDigit:uint) ):uint(bitsPerDigit);
                              merged[jj][i]=(  ((lsrc[jj]:uint) >> ((halfDig-i-1)*bitsPerDigit)) & (maskDigit:uint) ):uint(bitsPerDigit);
                              merged[jj][i+halfDig]=( ((ldst[jj]:uint) >> ((halfDig-i-1)*bitsPerDigit)) & (maskDigit:uint) ):uint(bitsPerDigit);
                          }
                          //    writeln("[src[",jj,"],dst[",jj,"]=",lsrc[jj],",",ldst[jj]);
                          //    writeln("merged[",jj,"]=",merged[jj]);
                    }
                    var tmpiv = argsortDefault(merged);
                    return tmpiv;
             }

             try {
                      iv = mergedArgsort(2);

             } catch  {
                  try! smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                      "merge array error" );
             }

             var tmpedges=lsrc[iv];
             lsrc=tmpedges;
             tmpedges=ldst[iv];
             ldst=tmpedges;
             //if (lWeightedFlag && sortw ){
             //   tmpedges=le_weight[iv];
             //   le_weight=tmpedges;
             //}

  }//end combine_sort

  //sorting the vertices based on their degrees.
  private proc part_degree_sort(lsrc:[?D1] int, ldst:[?D2] int, lstart_i:[?D3] int, lneighbour:[?D4] int,le_weight:[?D5] int,lneighbourR:[?D6] int,lWeightedFlag:bool) {
             var DegreeArray, VertexMapping: [D4] int;
             var tmpedge:[D1] int;
             var Nv=D4.size;
             var iv:[D1] int;

             coforall loc in Locales  {
                on loc {
                  forall i in lneighbour.localSubdomain(){
                        DegreeArray[i]=lneighbour[i]+lneighbourR[i];
                  }
                }
             }
 
             var tmpiv:[D4] int;
             try {
                 tmpiv =  argsortDefault(DegreeArray);
                 //get the index based on each vertex's degree
             } catch {
                  try! smLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),"error");
             }
             forall i in 0..Nv-1 {
                 VertexMapping[tmpiv[i]]=i;
                 // we assume the vertex ID is in 0..Nv-1
                 //given old vertex ID, map it to the new vertex ID
             }

             coforall loc in Locales  {
                on loc {
                  forall i in lsrc.localSubdomain(){
                        tmpedge[i]=VertexMapping[lsrc[i]];
                  }
                }
             }
             lsrc=tmpedge;
             coforall loc in Locales  {
                on loc {
                  forall i in ldst.localSubdomain(){
                        tmpedge[i]=VertexMapping[ldst[i]];
                  }
                }
             }
             ldst=tmpedge;
             coforall loc in Locales  {
                on loc {
                  forall i in lsrc.localSubdomain(){
                        if lsrc[i]>ldst[i] {
                           lsrc[i]<=>ldst[i];
                        }
                   }
                }
             }

             try  { combine_sort(lsrc, ldst,le_weight,lWeightedFlag, true);
             } catch {
                  try! smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                      "combine sort error");
             }
             set_neighbour(lsrc,lstart_i,lneighbour);
  }

  //degree sort for an undirected graph.
  private  proc degree_sort_u(lsrc:[?D1] int, ldst:[?D2] int, lstart_i:[?D3] int, lneighbour:[?D4] int,
                      lsrcR:[?D5] int, ldstR:[?D6] int, lstart_iR:[?D7] int, lneighbourR:[?D8] int,le_weight:[?D9] int,lWeightedFlag:bool) {

             part_degree_sort(lsrc, ldst, lstart_i, lneighbour,le_weight,lneighbourR,lWeightedFlag);
             coforall loc in Locales  {
               on loc {
                  forall i in lsrcR.localSubdomain(){
                        lsrcR[i]=ldst[i];
                        ldstR[i]=lsrc[i];
                   }
               }
             }
             try  { combine_sort(lsrcR, ldstR,le_weight,lWeightedFlag, false);
             } catch {
                  try! smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                      "combine sort error");
             }
             set_neighbour(lsrcR,lstart_iR,lneighbourR);

  }





  // directly read a graph from given file and build the SegGraph class in memory
  proc segGraphPreProcessingMsg(cmd: string, payload: string, argSize:int, st: borrowed SymTab): MsgTuple throws {
      //var (NeS,NvS,ColS,DirectedS,FileName,SkipLineS, RemapVertexS,DegreeSortS,RCMS,RwriteS,AlignedArrayS) = payload.splitMsgToTuple(11);


      var msgArgs = parseMessageArgs(payload, argSize);
      var NeS=msgArgs.getValueOf("NumOfEdges");
      var NvS=msgArgs.getValueOf("NumOfVertices");
      var ColS=msgArgs.getValueOf("NumOfColumns");
      var DirectedS=msgArgs.getValueOf("Directed");
      var FileName=msgArgs.getValueOf("FileName");
      var SkipLineS=msgArgs.getValueOf("SkipLines");
      var RemapVertexS=msgArgs.getValueOf("RemapFlag");
      var DegreeSortS=msgArgs.getValueOf("DegreeSortFlag");
      var RCMS=msgArgs.getValueOf("RCMFlag");
      var RwriteS=msgArgs.getValueOf("WriteFlag");
      var AlignedArrayS=msgArgs.getValueOf("AlignedFlag");


      var Ne:int =(NeS:int);
      var Nv:int =(NvS:int);
     
      var NumCol=ColS:int;
      var DirectedFlag:bool=false;
      var WeightedFlag:bool=false;

      var SkipLineNum:int=(SkipLineS:int);
      var timer: Timer;
      var RCMFlag:bool=false;
      var DegreeSortFlag:bool=false;
      var RemapVertexFlag:bool=false;
      var WriteFlag:bool=false;
      var AlignedArray:int=(AlignedArrayS:int);
      outMsg="read file ="+FileName;
      smLogger.info(getModuleName(),getRoutineName(),getLineNumber(),outMsg);

      proc binSearchE(ary:[?D] int,l:int,h:int,key:int):int {
                       //if ( (l<D.lowBound) || (h>D.highBound) || (l<0)) {
                       //    return -1;
                       //}
                       if ( (l>h) || ((l==h) && ( ary[l]!=key)))  {
                            return -1;
                       }
                       if (ary[l]==key){
                            return l;
                       }
                       if (ary[h]==key){
                            return h;
                       }
                       var m= (l+h)/2:int;
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
      }// end of proc


      timer.start();
    
      var NewNe,NewNv:int;


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


      var neighbour=makeDistArray(Nv,int);
      var vertexD=neighbour.domain;


      var dst,e_weight,srcR,dstR, iv: [edgeD] int ;
      var start_i,neighbourR, start_iR,depth, v_weight: [vertexD] int;

      var linenum:int=0;
      var repMsg: string;

      var tmpmindegree:int = start_min_degree;

      try {
           var f = open(FileName, iomode.r);
           // we check if the file can be opened correctly
           f.close();
      } catch {
                  smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                      "Open file error");
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
                            //if ewlocal.contains(curline){
                            //    e_weight[curline]=c:int;
                            //}
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
      
      // readLinebyLine sets ups src, dst, start_i, neightbor.  e_weights will also be set if it is an edge weighted graph
      // currently we ignore the weight.

      readLinebyLine(); 
      NewNv=vertex_remap(src,dst,Nv);
      
      try  { combine_sort(src, dst,e_weight,WeightedFlag, false);
      } catch {
             try!  smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                      "combine sort error");
      }

      set_neighbour(src,start_i,neighbour);

      if (!DirectedFlag) { //undirected graph
          smLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),
                      "Handle undirected graph");
          coforall loc in Locales  {
              on loc {
                  forall i in srcR.localSubdomain(){
                        srcR[i]=dst[i];
                        dstR[i]=src[i];
                   }
              }
          }
          try  { combine_sort(srcR, dstR,e_weight,WeightedFlag, false);
          } catch {
                 try!  smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                      "combine sort error");
          }
          set_neighbour(srcR,start_iR,neighbourR);

          if (DegreeSortFlag) {
                    degree_sort_u(src, dst, start_i, neighbour, srcR, dstR, start_iR, neighbourR,e_weight,WeightedFlag);
          }



      }//end of undirected
      else {
          //part_degree_sort(src, dst, start_i, neighbour,e_weight,neighbour,WeightedFlag);
      }

      smLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),
                      "Handle self loop and duplicated edges");
      var cur=0;
      var tmpsrc=src;
      var tmpdst=dst;
      for i in 0..Ne-1 {
          if src[i]==dst[i] {
              continue;
              //self loop
          }
          if (cur==0) {
             tmpsrc[cur]=src[i];
             tmpdst[cur]=dst[i]; 
             cur+=1;
             continue;
          }
          if (tmpsrc[cur-1]==src[i]) && (tmpdst[cur-1]==dst[i]) {
              //duplicated edges
              continue;
          } else {
               if (src[i]>dst[i]) {

                    var u=src[i]:int;
                    var v=dst[i]:int;
                    var lu=start_i[u]:int;
                    var nu=neighbour[u]:int;
                    var lv=start_i[v]:int;
                    var nv=neighbour[v]:int;
                    var DupE:int;
                    DupE=binSearchE(dst,lv,lv+nv-1,u);
                    if DupE!=-1 {
                         //find v->u 
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

          var myneighbour=makeDistArray(NewNv,int);
          var myvertexD=myneighbour.domain;

          var mydst,mye_weight,mysrcR,mydstR, myiv: [myedgeD] int ;
          var mystart_i,myneighbourR, mystart_iR,mydepth, myv_weight: [myvertexD] int;



          forall i in 0..NewNe-1 {
             mysrc[i]=tmpsrc[i];
             mydst[i]=tmpdst[i];
          }
          try  { combine_sort(mysrc, mydst,mye_weight,WeightedFlag, false);
          } catch {
                 try!  smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                      "combine sort error");
          }

          set_neighbour(mysrc,mystart_i,myneighbour);


          if (!DirectedFlag) { //undirected graph
              coforall loc in Locales  {
                  on loc {
                       forall i in mysrcR.localSubdomain(){
                            mysrcR[i]=mydst[i];
                            mydstR[i]=mysrc[i];
                       }
                  }
              }
              try  { combine_sort(mysrcR, mydstR,mye_weight,WeightedFlag, false);
              } catch {
                     try!  smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                          "combine sort error");
              }
              set_neighbour(mysrcR,mystart_iR,myneighbourR);
              if (DegreeSortFlag) {
                    degree_sort_u(mysrc, mydst, mystart_i, myneighbour, mysrcR, mydstR, mystart_iR, myneighbourR,mye_weight,WeightedFlag);
              }
              if (AlignedArray==1) {
              }

          }//end of undirected
          else {
              if (DegreeSortFlag) {
                 part_degree_sort(mysrc, mydst, mystart_i, myneighbour,mye_weight,myneighbour,WeightedFlag);

              }  
              if (AlignedArray==1) {
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
  }





  // directly read a graph from given file and build the SegGraph class in memory
  proc segGraphNDEMsg(cmd: string, payload: string, argSize:int, st: borrowed SymTab): MsgTuple throws {
      //var (NeS,NvS,ColS,DirectedS,FileName,SkipLineS, RemapVertexS,DegreeSortS,RCMS,RwriteS) = payload.splitMsgToTuple(10);


      var msgArgs = parseMessageArgs(payload, argSize);
      var NeS=msgArgs.getValueOf("NumOfEdges");
      var NvS=msgArgs.getValueOf("NumOfVertices");
      var ColS=msgArgs.getValueOf("NumOfColumns");
      var DirectedS=msgArgs.getValueOf("Directed");
      var FileName=msgArgs.getValueOf("FileName");
      var SkipLineS=msgArgs.getValueOf("SkipLines");
      var RemapVertexS=msgArgs.getValueOf("RemapFlag");
      var DegreeSortS=msgArgs.getValueOf("DegreeSortFlag");
      var RCMS=msgArgs.getValueOf("RCMFlag");
      var RwriteS=msgArgs.getValueOf("WriteFlag");

      var Ne:int =(NeS:int);
      var Nv:int =(NvS:int);
     
      var NumCol=ColS:int;
      var DirectedFlag:bool=false;
      var WeightedFlag:bool=false;

      var SkipLineNum:int=(SkipLineS:int);
      var timer: Timer;
      var RCMFlag:bool=false;
      var DegreeSortFlag:bool=false;
      var RemapVertexFlag:bool=false;
      var WriteFlag:bool=false;
      outMsg="read file ="+FileName;
      smLogger.info(getModuleName(),getRoutineName(),getLineNumber(),outMsg);

      proc binSearchE(ary:[?D] int,l:int,h:int,key:int):int {
                       //if ( (l<D.lowBound) || (h>D.highBound) || (l<0)) {
                       //    return -1;
                       //}
                       if ( (l>h) || ((l==h) && ( ary[l]!=key)))  {
                            return -1;
                       }
                       if (ary[l]==key){
                            return l;
                       }
                       if (ary[h]==key){
                            return h;
                       }
                       var m= (l+h)/2:int;
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
      }// end of proc


      timer.start();
    
      var NewNe,NewNv:int;


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


      var neighbour=makeDistArray(Nv,int);
      var vertexD=neighbour.domain;


      var dst,e_weight,srcR,dstR, iv: [edgeD] int ;
      var start_i,neighbourR, start_iR,depth, v_weight: [vertexD] int;

      var linenum:int=0;
      var repMsg: string;

      var tmpmindegree:int =start_min_degree;

      try {
           var f = open(FileName, iomode.r);
           // we check if the file can be opened correctly
           f.close();
      } catch {
                  smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                      "Open file error");
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
                            //if ewlocal.contains(curline){
                            //    e_weight[curline]=c:int;
                            //}
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
      
      // readLinebyLine sets ups src, dst, start_i, neightbor.  e_weights will also be set if it is an edge weighted graph
      // currently we ignore the weight.

      readLinebyLine(); 
      NewNv=vertex_remap(src,dst,Nv);
      
      try  { combine_sort(src, dst,e_weight,WeightedFlag, false);
      } catch {
             try!  smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                      "combine sort error");
      }

      set_neighbour(src,start_i,neighbour);

      if (!DirectedFlag) { //undirected graph
          smLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),
                      "Handle undirected graph");
          coforall loc in Locales  {
              on loc {
                  forall i in srcR.localSubdomain(){
                        srcR[i]=dst[i];
                        dstR[i]=src[i];
                   }
              }
          }
          try  { combine_sort(srcR, dstR,e_weight,WeightedFlag, false);
          } catch {
                 try!  smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                      "combine sort error");
          }
          set_neighbour(srcR,start_iR,neighbourR);

          if (DegreeSortFlag) {
                    degree_sort_u(src, dst, start_i, neighbour, srcR, dstR, start_iR, neighbourR,e_weight,WeightedFlag);
          }



      }//end of undirected
      else {
          //part_degree_sort(src, dst, start_i, neighbour,e_weight,neighbour,WeightedFlag);
      }

      smLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),
                      "Handle self loop and duplicated edges");
      var cur=0;
      var tmpsrc=src;
      var tmpdst=dst;
      for i in 0..Ne-1 {
          if src[i]==dst[i] {
              continue;
              //self loop
          }
          if (cur==0) {
             tmpsrc[cur]=src[i];
             tmpdst[cur]=dst[i]; 
             cur+=1;
             continue;
          }
          if (tmpsrc[cur-1]==src[i]) && (tmpdst[cur-1]==dst[i]) {
              //duplicated edges
              continue;
          } else {
               if (src[i]>dst[i]) {

                    var u=src[i]:int;
                    var v=dst[i]:int;
                    var lu=start_i[u]:int;
                    var nu=neighbour[u]:int;
                    var lv=start_i[v]:int;
                    var nv=neighbour[v]:int;
                    var DupE:int;
                    DupE=binSearchE(dst,lv,lv+nv-1,u);
                    if DupE!=-1 {
                         //find v->u 
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

          var myneighbour=makeDistArray(NewNv,int);
          var myvertexD=myneighbour.domain;

          var mydst,mye_weight,mysrcR,mydstR, myiv: [myedgeD] int ;
          var mystart_i,myneighbourR, mystart_iR,mydepth, myv_weight: [myvertexD] int;



          forall i in 0..NewNe-1 {
             mysrc[i]=tmpsrc[i];
             mydst[i]=tmpdst[i];
          }
          try  { combine_sort(mysrc, mydst,mye_weight,WeightedFlag, false);
          } catch {
                 try!  smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                      "combine sort error");
          }

          set_neighbour(mysrc,mystart_i,myneighbour);


          if (!DirectedFlag) { //undirected graph
              coforall loc in Locales  {
                  on loc {
                       forall i in mysrcR.localSubdomain(){
                            mysrcR[i]=mydst[i];
                            mydstR[i]=mysrc[i];
                       }
                  }
              }
              try  { combine_sort(mysrcR, mydstR,mye_weight,WeightedFlag, false);
              } catch {
                     try!  smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                          "combine sort error");
              }
              set_neighbour(mysrcR,mystart_iR,myneighbourR);
              if (DegreeSortFlag) {
                    degree_sort_u(mysrc, mydst, mystart_i, myneighbour, mysrcR, mydstR, mystart_iR, myneighbourR,mye_weight,WeightedFlag);
              }

          }//end of undirected
          else {
              if (DegreeSortFlag) {
                 part_degree_sort(mysrc, mydst, mystart_i, myneighbour,mye_weight,myneighbour,WeightedFlag);

              }  
          }  
          if (WriteFlag) {
                  var wf = open(FileName+".nde", iomode.cw);
                  var mw = wf.writer(kind=ionative);
                  mw.writeln("%-15i".format(NewNv));
                  for i in 0..NewNv-1 {
                      mw.writeln("%-15i    %-15i".format(i,myneighbour[i]+myneighbourR[i]));
                  }
                  for i in 0..NewNe-1 {
                      mw.writeln("%-15i    %-15i".format(mysrc[i],mydst[i]));
                  }
                  mw.close();
                  wf.close();
          }
      } else {
    
          if (WriteFlag) {
                  var wf = open(FileName+".nde", iomode.cw);
                  var mw = wf.writer(kind=ionative);
                  mw.writeln("%-15i".format(NewNv));
                  for i in 0..NewNv-1 {
                      mw.writeln("%-15i    %-15i".format(i,neighbour[i]+neighbourR[i]));
                  }
                  for i in 0..NewNe-1 {
                      mw.writeln("%-15i    %-15i".format(src[i],dst[i]));
                  }
                  mw.close();
                  wf.close();
          }
      }
      timer.stop();
      outMsg="Transfermation  File takes " + timer.elapsed():string;
      smLogger.debug(getModuleName(),getRoutineName(),getLineNumber(),outMsg);
      repMsg =  "To NDE  success"; 
      return new MsgTuple(repMsg, MsgType.NORMAL);
  }




  // directly read a graph from given file and build the SegGraph class in memory
  proc segGraphFileMsg(cmd: string, payload: string, argSize:int, st: borrowed SymTab): MsgTuple throws {
      //var (NeS,NvS,ColS,DirectedS, FileName,RemapVertexS,DegreeSortS,RCMS,RwriteS,AlignedArrayS) = payload.splitMsgToTuple(10);
      var msgArgs = parseMessageArgs(payload, argSize);
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

      /*
      var dst=makeDistArray(Ne,int);
      var e_weight=makeDistArray(Ne,int);
      var srcR=makeDistArray(Ne,int);
      var dstR=makeDistArray(Ne,int);
      var iv=makeDistArray(Ne,int);
      */

      var neighbour=makeDistArray(Nv,int);
      var vertexD=neighbour.domain;

      /*
      var start_i=makeDistArray(Nv,int);
      var neighbourR=makeDistArray(Nv,int);
      var start_iR=makeDistArray(Nv,int);
      var depth=makeDistArray(Nv,int);
      var v_weight=makeDistArray(Nv,int);
      */

      var dst,e_weight,srcR,dstR, iv: [edgeD] int ;
      var start_i,neighbourR, start_iR,depth, v_weight: [vertexD] int;

      var linenum:int=0;
      var repMsg: string;

      var tmpmindegree:int =start_min_degree;

      try {
           var f = open(FileName, iomode.r);
           // we check if the file can be opened correctly
           f.close();
      } catch {
                  smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                      "Open file error");
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
                          smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                                "edge  error");
                          continue;
                      }
                      if NumCol==2 {
                           (a,b)=  line.splitMsgToTuple(2);
                      } else {
                           (a,b,c)=  line.splitMsgToTuple(3);
                            //if ewlocal.contains(curline){
                            //    e_weight[curline]=c:int;
                            //}
                      }
                      if a==b {
                          smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                                "self cycle "+ a +"->"+b);
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
      try  { combine_sort(src, dst,e_weight,WeightedFlag, false);
      } catch {
             try!  smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                      "combine sort error");
      }

      set_neighbour(src,start_i,neighbour);

      // Make a composable SegGraph object that we can store in a GraphSymEntry later
      var graph = new shared SegGraph(Ne, Nv, DirectedFlag);
      graph.withSRC(new shared SymEntry(src):GenSymEntry)
           .withDST(new shared SymEntry(dst):GenSymEntry)
           .withSTART_IDX(new shared SymEntry(start_i):GenSymEntry)
           .withNEIGHBOR(new shared SymEntry(neighbour):GenSymEntry);

      if (!DirectedFlag) { //undirected graph
          coforall loc in Locales  {
              on loc {
                  forall i in srcR.localSubdomain(){
                        srcR[i]=dst[i];
                        dstR[i]=src[i];
                   }
              }
          }
          try  { combine_sort(srcR, dstR,e_weight,WeightedFlag, false);
          } catch {
                 try!  smLogger.error(getModuleName(),getRoutineName(),getLineNumber(),
                      "combine sort error");
          }
          set_neighbour(srcR,start_iR,neighbourR);

          if (DegreeSortFlag) {
             degree_sort_u(src, dst, start_i, neighbour, srcR, dstR, start_iR, neighbourR,e_weight,WeightedFlag);
          }


          graph.withSRC_R(new shared SymEntry(srcR):GenSymEntry)
               .withDST_R(new shared SymEntry(dstR):GenSymEntry)
               .withSTART_IDX_R(new shared SymEntry(start_iR):GenSymEntry)
               .withNEIGHBOR_R(new shared SymEntry(neighbourR):GenSymEntry);

      }//end of undirected
      else {
        if (DegreeSortFlag) {
             part_degree_sort(src, dst, start_i, neighbour,e_weight,neighbour,WeightedFlag);
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
  }

    use CommandMap;
    registerFunction("segmentedGraphFile",segGraphFileMsg,getModuleName());
}