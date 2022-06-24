use CTypes;
require '-lgsl','-lgslcblas';

extern {  
#include "gsl/gsl_rng.h"
#include "gsl/gsl_randist.h"
#include "gsl/gsl_cdf.h"
}
