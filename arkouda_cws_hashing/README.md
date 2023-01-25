# Arkouda Consistent Weighted Sampling (CWS)/Locality-Sensitive Hashing for the MinMax Kernel

Arkouda implementation of the consistent weighted sampling (CWS) scheme for the MinMax (i.e. weighted Jaccard) kernel originally described in "Consistent Weighted Sampling" by Manasse, McSherry, and Talwar (https://www.microsoft.com/en-us/research/wp-content/uploads/2010/06/ConsistentWeightedSampling2.pdf). 

The specific implementation is a mathematically equivalent algorithm from Sergey Ioffe described in "Improved Consistent Sampling, Weighted Minhash, and L1 Sketching" (https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/36928.pdf) that improves the runtime of the hashing step from expected constant time to constant time.

Both the original consistent weighted sampling scheme and the approximate "zero-bit" version described by Ping Li in "0-bit Consistent Weighted Sampling" (https://dl.acm.org/doi/abs/10.1145/2783258.2783406) are provided.

Efficient pair construction required for locality-sensitive hashing (LSH) has not yet been implemented. Minhash banding is also yet to be implemented. The GNU Scientific Library (https://www.gnu.org/software/gsl/) is required for random number generation.


asdf

## Methods
- `lshMinMax()` generate a user-specified number of minhashes for a collection of sets comprised of weighted set elements. The first two arguments (both pdarrays) comprise a segmented array consisting of the set offsets and the set values. The third argument is a pdarray of set element weights aligned with the second array. Taken together, the first three arguments may be identified with a weighted compressed-sparse row (CSR) matrix/graph with weights assigned to the column index/target vertex. The fourth argument is a boolean flag that selects between the original CWS output ("False") consisting of a tuple of pdarrays, one containing the integer set samples and the other the reals, and the "zero-bit" version ("True") consisting of only the first array of integer samples. The final argument is the number of minhashes to generate per set.
