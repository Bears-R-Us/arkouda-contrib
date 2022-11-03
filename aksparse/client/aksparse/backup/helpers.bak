import arkouda as ak

def gen_ranges(starts, ends):
    """ 
    Generate a segmented array of variable-length, contiguous 
    ranges between pairs of start- and end-points.

    #TODO: Bring up what zero-filter does. Rename zero_filter.

    Parameters
    ----------
    starts : pdarray, int64
        The start value of each range
    ends : pdarray, int64
        The end value (exclusive) of each range

    Returns
    -------
    segments : pdarray, int64
        The starting index of each range in the resulting array
    ranges : pdarray, int64
        The actual ranges, flattened into a single array
    """


    lengths = ends - starts
    segs = ak.cumsum(lengths) - lengths

    zero_scan = segs[1:] - segs[:-1]
    zero_filter = (zero_scan != 0)
    zero_filter = ak.concatenate([zero_filter, ak.array([True])])

    fsegs = segs[zero_filter]
    fstarts = starts[zero_filter]
    fends = ends[zero_filter]

    totlen = lengths.sum()
    slices = ak.ones(totlen, dtype=ak.int64)
    diffs = ak.concatenate((ak.array([fstarts[0]]),
                            fstarts[1:] - fends[:-1] +1))
    slices[fsegs] = diffs
    return fsegs, zero_filter, ak.cumsum(slices)

def expand(vals, segs, size, zfilter):
    '''
    TODO: Fix this docstring to be accurate.
    Broadcast per-segment values to a segmented array. Equivalent 
    to ak.GroupBy.broadcast(vals) but accepts explicit segments and size arguments.

    Also takes in a filter to ignore zero-length segments.
    '''
    fvals = vals[zfilter]

    temp = ak.zeros(size, dtype=vals.dtype)
    diffs = ak.concatenate((ak.array([fvals[0]]), 
                            fvals[1:] - fvals[:-1]))
    temp[segs] = diffs

    return ak.cumsum(temp)

def reindex_pdarray(pdarray):
    ''' returns a one-up count reindexing of a given pdarra.
        e.g. [7, 4, 0, 3] -> [3, 2, 0, 1]
        NOTE: should probably go in akutils
    '''
    by_values = ak.GroupBy(pdarray)
    unique_keys = by_values.unique_keys
    indices = ak.arange(0, len(unique_keys), 1)
    reindexed_vals = ak.ones_like(by_values.keys)
    reindexed_vals[by_values.permutation] = by_values.broadcast(indices)
    return reindexed_vals
