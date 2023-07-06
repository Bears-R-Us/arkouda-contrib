from argparse import ArgumentError, ArgumentTypeError
from typing import cast
import arkouda as ak
import os

def set_arkouda_init(flag_val):
    """If set to 1, certain functions will use Arkouda objects/functions
      instead of work being done entirely on the Chapel server."""
    if flag_val == True:
        flag_val = 1
    elif flag_val == False:
        flag_val = 0
    if flag_val != 1 and flag_val != 0:
        print("Please enter either a 1 or a 0")
    else:
        os.environ.setdefault('ARKOUDA_INIT', str(flag_val))

class SparseMatrix:
    """The parent class for COO, CSR, and CSC sparse matrix formats. 
    This class should not be used on its own in lieu of one of those three."""

    _binop_list = ["+",
                   "-",
                   "*",
                   "/"]
    
    def __repr__(self):
        return f"Data: {self.data}\nRows: {self.rows}\nColumns: {self.cols}"

    def _binop(self, other, binop):
        # Supported types for arithmetic operations
        is_pdarray = issubclass(type(other), ak.pdarray)
        is_sparse_matrix = issubclass(type(other), SparseMatrix)
        is_int = issubclass(type(other), int)
        is_float = issubclass(type(other), float)

        if not is_pdarray and not is_int and not is_float and not is_sparse_matrix:
            return NotImplemented
        elif binop not in self._binop_list:
            return ValueError(f"Operator {binop} not supported.")
        else:
            if binop == "+":
                if is_int:
                    return self.__plus_scalar(other)
                elif is_float:
                    return self.__plus_scalar(other)
                elif is_pdarray:
                    return self.__plus_vector(other)
                elif is_sparse_matrix:
                    return "Base sparse_matrix class provided. Please use a specific format (COO, CSC, CSR)"
            elif binop == "-":
                if is_int:
                    return self.__sub_scalar(other)
                elif is_float:
                    return self.__sub_scalar(other)
                elif is_pdarray:
                    return self.__sub_vector(other)
                elif is_sparse_matrix:
                    return "Base sparse_matrix class provided. Please use a specific format (COO, CSC, CSR)"
            elif binop == "*":
                if is_int:
                    return self.__mul_scalar(other)
                elif is_float:
                    return self.__mul_scalar(other)
                elif is_pdarray:
                    return self.__mul_vector(other)
                elif is_sparse_matrix:
                    return "Base sparse_matrix class provided. Please use a specific format (COO, CSC, CSR)"


    def _binop_r(self, other, binop):
        # Supported types for arithmetic operations
        is_pdarray = issubclass(type(other), ak.pdarray)
        is_sparse_matrix = issubclass(type(other), SparseMatrix)
        is_int = issubclass(type(other), int)
        is_float = issubclass(type(other), float)

        if not is_pdarray and not is_int and not is_float and not is_sparse_matrix:
            return NotImplemented
        elif binop not in self._binop_list:
            return ValueError(f"Operator {binop} not supported.")
        else:
            if binop == "+":
                if is_int:
                    return self.__plus_scalar(other)
                elif is_float:
                    return self.__plus_scalar(other)
                elif is_pdarray:
                    return self.__plus_vector(other)
                elif is_sparse_matrix:
                    return "Base sparse_matrix class provided. Please use a specific format (COO, CSC, CSR)"
            elif binop == "*":
                if is_int:
                    return self.__mul_scalar(other)
                elif is_float:
                    return self.__mul_scalar(other)
                elif is_pdarray:
                    return self.__mul_vector(other)
                elif is_sparse_matrix:
                    return "Base sparse_matrix class provided. Please use a specific format (COO, CSC, CSR)"

    # Arithmetic operations (specific functionality added in subclasses) ---------------------------
    def __add__(self, other):
        return self._binop(other, "+")

    def __radd__(self, other):
        return self._binop_r(other, "+")

    def __sub__(self, other):
        return self._binop(other, "-")

    def __rsub__(self, other):
        return self._binop_r(other, "-")

    def __mul__(self, other):
        return self._binop(other, "*")

    def __rmul__(self, other):
        return self._binop_r(other, "*")

    def __plus_scalar(self, scalar):
        return

    def __sub_scalar(self, scalar):
        return

    def __mul_scalar(self, scalar):
        return

    def __plus_vector(self, vector):
        return

    def __sub_vector(self, vector):
        return

    def __mul_vector(self, vector):
        return

    # Additional features to be added from scipy.sparse.coo_matrix()
    # https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.coo_matrix.html#scipy.sparse.coo_matrix

class Coo(SparseMatrix):
    """A sparse matrix in COOrdinate format. Also known as the 'ijv' or 'triplet' format."""

    def __init__(self, data, rows, columns, shape):
        if os.environ.get('ARKOUDA_INIT') == "1":
            self.rows = rows
            self.cols = columns
            self.shape = shape
            sorting_gb = ak.GroupBy([self.rows, self.cols])
            self.data = data[sorting_gb.permutation]
            self.nnz = len(self.data)
        else:
            self.shape = shape
            resp = cast(str, ak.client.generic_msg(cmd="coo_construct", args={"data": data, "rows": rows, "columns": columns}))
            arr_ids = resp.split("+")
            self.data = ak.create_pdarray(f"created {arr_ids[0]}")
            self.cols = ak.create_pdarray(f"created {arr_ids[1]}")
            self.rows = ak.create_pdarray(f"created {arr_ids[2]}")
            self.nnz = len(self.data)

    # Format conversion functions ---------------------------------------------------
    def to_coo(self):
        """Convert this array to COOrdinate format."""
        return self

    def to_csr(self, assign_vals=False):
        """Convert this matrix to Compressed Sparse Row format."""
        return Csr(self.data, self.rows, self.cols, self.shape)

    def to_csc(self):
        """Convert this matrix to Compressed Sparse Column format."""
        return Csc(self.data, self.rows, self.cols, self.shape)

    # Arithmetic operation functions ---------------------------------------------------
    def __plus_scalar(self, scalar):
        self_copy = Coo(self.data, self.rows, self.cols, self.shape)
        self_copy.data = self_copy.data + scalar
        return self_copy
    
    def __sub_scalar(self, scalar):
        self_copy = Coo(self.data, self.rows, self.cols, self.shape)
        self_copy.data = self.data - scalar
        return self_copy

    def __mul_scalar(self, scalar):
        self_copy = Coo(self.data, self.rows, self.cols, self.shape)
        self_copy.data = self.data * scalar
        return self_copy

    def __plus_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        self_copy = Coo(self.data, self.rows, self.cols, self.shape)
        self_copy.data = self.data + vector[self.cols]
        return self_copy

    def __sub_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        self_copy = Coo(self.data, self.rows, self.cols, self.shape)
        self_copy.data = self.data - vector[self.cols]
        return self_copy

    def __mul_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        self_copy = Coo(self.data, self.rows, self.cols, self.shape)
        self_copy.data = self.data * vector[self.cols]
        return self_copy

    def dot(self, input):
        """ Dot product method for CSR class. Must provide additional matrix of any format to multiply in parameters. """
        if issubclass(type(input), ak.pdarray):
            temp_csr = self.to_csr()
            return temp_csr.vector_matrix_dot(input)
        if issubclass(type(input), ak.pdarray):
            raise NotImplementedError
            # temp_csr = self.to_csr()
            # return temp_csr.matrix_matrix_dot(input)
        else:
            raise ArgumentTypeError



class Csr(SparseMatrix):
    """Compressed Sparse Row matrix."""

    def __init__(self, data, rows, columns, shape, assign_vals=None):
        if os.environ.get('ARKOUDA_INIT') == "1":
            self._old_columns = columns
            self._old_rows = rows

            self._gb_row_col = ak.GroupBy([rows, columns])
            self._gb_row = ak.GroupBy(rows)
            self.data = data
            self.nnz = len(self.data)
            self.indices = columns
            self._gb_row_val = ak.GroupBy([rows, data])
            self._gb_row_val_uk = ak.GroupBy(self._gb_row_val.unique_keys[0])

            self.shape = shape

            segs = ak.concatenate([self._gb_row_val_uk.segments, ak.array([len(self.data)])])
            diffs = segs[1:] - segs[:-1]
            ind_ptr = ak.zeros(shape[1] + 1, ak.int64)
            ind_ptr[self._gb_row_val_uk.unique_keys + 1] = diffs
            ind_ptr = ak.cumsum(ind_ptr)
            for i in range(shape[1] - (len(ind_ptr) - 1)):
                ind_ptr = ak.concatenate([ind_ptr, ind_ptr[-1:]])
            self.indptr = ind_ptr
        elif assign_vals:
            self.data = data
            self.nnz = len(self.data)
            self.indices = columns
            self.indptr = rows
            self.shape = shape
        else:
            resp = cast(str, ak.client.generic_msg(cmd="coo_to_csr", args={"data": data, "rows": rows, "columns": columns, "shape_width": shape[0], "shape_height": shape[1]}))
            arr_ids = resp.split("+")
            self.data = ak.create_pdarray(f"created {arr_ids[0]}")
            self.nnz = len(self.data)
            self.indices = ak.create_pdarray(f"created {arr_ids[1]}")
            self.shape = shape
            
            self._old_columns = ak.create_pdarray(f"created {arr_ids[2]}")
            self._old_rows = ak.create_pdarray(f"created {arr_ids[3]}")
            self._gb_row_col = arr_ids[4]
            self._gb_row = arr_ids[5]
            self._gb_row_val = arr_ids[6]
            self._gb_row_val_uk = arr_ids[7]
            self.indptr = ak.create_pdarray(f"created {arr_ids[8]}")

    def __repr__(self):
        return f"Data: {self.data}\nColumn Indices: {self.indices}\nRow Pointers: {self.indptr}"

    # Format conversion functions ---------------------------------------------------
    def to_coo(self):  
        """Convert this array to COOrdinate format."""
        return Coo(self.data, self._old_rows, self._old_columns, self.shape)

    def to_csr(self):
        """Convert this matrix to Compressed Sparse Row format."""
        return self

    def to_csc(self):
        """Convert this matrix to Compressed Sparse Column format."""
        temp_coo = Coo(self.data, self._old_rows, self._old_columns, self.shape)
        return temp_coo.to_csc()

    # Arithmetic operation functions ---------------------------------------------------
    def __plus_scalar(self, scalar):
        self_copy = Csr(self.data, self._old_rows, self._old_columns, self.shape)
        self_copy.data = self.data + scalar
        self_copy.gb_row_val = ak.GroupBy([self._old_rows, self.data])
        self_copy.gb_row_val_uk = ak.GroupBy(self.gb_row_val.unique_keys[0])
        return self_copy

    def __sub_scalar(self, scalar):
        self_copy = Csr(self.data, self._old_rows, self._old_columns, self.shape)
        self_copy.data = self.data - scalar
        self_copy.gb_row_val = ak.GroupBy([self._old_rows, self.data])
        self_copy.gb_row_val_uk = ak.GroupBy(self.gb_row_val.unique_keys[0])
        return self_copy

    def __mul_scalar(self, scalar):
        self_copy = Csr(self.data, self._old_rows, self._old_columns, self.shape)
        self_copy.data = self.data * scalar
        self_copy.gb_row_val = ak.GroupBy([self._old_rows, self.data])
        self_copy.gb_row_val_uk = ak.GroupBy(self.gb_row_val.unique_keys[0])
        return self_copy

    def __plus_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        self_copy = Csr(self.data, self._old_rows, self._old_columns, self.shape)
        self_copy.data = self.data + vector[self.cols]
        self_copy.gb_row_val = ak.GroupBy([self._old_rows, self.data])
        self_copy.gb_row_val_uk = ak.GroupBy(self.gb_row_val.unique_keys[0])
        return self_copy

    def __sub_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        self_copy = Csr(self.data, self._old_rows, self._old_columns, self.shape)
        self_copy.data = self.data - vector[self.cols]
        self_copy.gb_row_val = ak.GroupBy([self._old_rows, self.data])
        self_copy.gb_row_val_uk = ak.GroupBy(self.gb_row_val.unique_keys[0])
        return self_copy

    def __mul_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        self_copy = Csr(self.data, self._old_rows, self._old_columns, self.shape)
        self_copy.data = self.data * vector[self.cols]
        self_copy.gb_row_val = ak.GroupBy([self._old_rows, self.data])
        self_copy.gb_row_val_uk = ak.GroupBy(self.gb_row_val.unique_keys[0])
        return self_copy

    def dot(self, input):
        """ Dot product method for CSR class. Must provide additional matrix of any format to multiply in parameters. """
        if str(type(input)) == "<class 'arkouda.pdarrayclass.pdarray'>":
            return self.vector_matrix_dot(input)
        if str(type(input)) == "<class ''>":
            raise NotImplementedError
            # return self.matrix_matrix_dot(input)
        else:
            print(type(input))

    def vector_matrix_dot(self, vector):
        vec = vector[self.cols]
        return self.gb_row.aggregate(vec * self.data, "sum")[1]

        

class Csc(SparseMatrix):
    """Compressed Sparse Column matrix."""

    def __init__(self, data, rows, columns, shape, assign_vals=None):
        if os.environ.get('ARKOUDA_INIT') == "1":
            self._old_data = data
            self._old_columns = columns
            self._old_rows = rows

            self._gb_row_col = ak.GroupBy([rows, columns])
            self._gb_col_row = ak.GroupBy([columns, rows])
            self._gb_row = ak.GroupBy(rows)
            self._gb_col_row_uk = ak.GroupBy(self._gb_col_row.unique_keys[0])
            self.data = data[self._gb_col_row.permutation]
            self.nnz = len(self.data)
            self.indices = rows[self._gb_col_row.permutation]
            self.shape = shape

            segs = ak.concatenate([self._gb_col_row_uk.segments, ak.array([len(self.data)])])
            diffs = segs[1:] - segs[:-1]
            ind_ptr = ak.zeros(shape[0] + 1, ak.int64)
            ind_ptr[self._gb_col_row_uk.unique_keys + 1] = diffs
            ind_ptr = ak.cumsum(ind_ptr)
            for i in range(shape[0] - (len(ind_ptr) - 1)):
                ind_ptr = ak.concatenate([ind_ptr, ind_ptr[-1:]])
            self.indptr = ind_ptr
        elif assign_vals:
            self.data = data
            self.nnz = len(self.data)
            self.indices = columns
            self.indptr = rows
            self.shape = shape
        else:
            resp = cast(str, ak.client.generic_msg(cmd="coo_to_csc", args={"data": data, "rows": rows, "columns": columns, "shape_width": shape[0], "shape_height": shape[1]}))
            arr_ids = resp.split("+")
            self.data = ak.create_pdarray(f"created {arr_ids[0]}")
            self.nnz = len(self.data)
            self.indices = ak.create_pdarray(f"created {arr_ids[1]}")
            self.shape = shape
            
            self._old_columns = ak.create_pdarray(f"created {arr_ids[2]}")
            self._old_rows = ak.create_pdarray(f"created {arr_ids[3]}")
            self._old_data = ak.create_pdarray(f"created {arr_ids[4]}")
            self._gb_row = arr_ids[5]
            self._gb_col_row = arr_ids[6]
            self._gb_col_row_uk = arr_ids[7]
            self.indptr = ak.create_pdarray(f"created {arr_ids[8]}")
            self._vname = arr_ids[9]
            self._cname = arr_ids[10]
            self._rname = arr_ids[11]

    def __repr__(self):
        return f"Data: {self.data}\nRow Indices: {self.indices}\nColumn Pointers: {self.indptr}"
    
    # Format conversion functions ---------------------------------------------------
    def to_coo(self, assign_vals=None):
        """Convert this array to COOrdinate format."""
        return Coo(self.data, self._old_rows, self._old_columns, self.shape)
    
    def to_csr(self, assign_vals=None):
        """Convert this matrix to Compressed Sparse Row format."""
        if assign_vals:
            temp_coo = Coo(self.data, self._old_rows, self._old_columns, self.shape, assign_vals=True)
            return temp_coo.to_csr(assign_vals=True)
        else:
            temp_coo = Coo(self.data, self._old_rows, self._old_columns, self.shape)
            return temp_coo.to_csr()

    def to_csc(self):
        """Convert this matrix to Compressed Sparse Column format."""
        return self

    # Arithmetic operation functions ---------------------------------------------------
    def __plus_scalar(self, scalar):
        self_copy = Csc(self.data, self._old_rows, self._old_columns, self.shape)
        self_copy.data = self.data + scalar
        self_copy._old_data = self._old_data + scalar
        return self_copy

    def __sub_scalar(self, scalar):
        self_copy = Csc(self.data, self._old_rows, self._old_columns, self.shape)
        self_copy.data = self.data - scalar
        self_copy._old_data = self._old_data - scalar
        return self_copy

    def __mul_scalar(self, scalar):
        self_copy = Csc(self.data, self._old_rows, self._old_columns, self.shape)
        self_copy.data = self.data * scalar
        self_copy._old_data = self._old_data * scalar
        return self_copy

    def __plus_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        temp_convert = self.to_csr()
        temp_convert.data = temp_convert.data + vector[temp_convert.cols]
        self_copy = temp_convert.to_csc()
        return self_copy

    def __sub_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        temp_convert = self.to_csr()
        temp_convert.data = temp_convert.data - vector[temp_convert.cols]
        self_copy = temp_convert.to_csc()
        return self_copy

    def __mul_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        temp_convert = self.to_csr()
        temp_convert.data = temp_convert.data * vector[temp_convert.cols]
        self_copy = temp_convert.to_csc()
        return self_copy

    def dot(self, input):
        """ Dot product method for CSR class. Must provide additional matrix of any format to multiply in parameters. """
        if str(type(input)) == "<class 'arkouda.pdarrayclass.pdarray'>":
            temp_csr = self.to_csr()
            return temp_csr.vector_matrix_dot(input)
        if str(type(input)) == "<class ''>":
            raise NotImplementedError
            # temp_csr = self.to_csr()
            # return temp_csr.matrix_matrix_dot(input)
        else:
            raise ArgumentTypeError

    def spgemm(self, other):
        """ Sparse General Matrix Multiplication """
        if os.environ.get('ARKOUDA_INIT') == "1":
            try:
                assert(self.shape[1] == other.shape[0])
            except:
                error_msg = f"array size mismatch"
                raise AttributeError(error_msg)
            
            # identify number of multiplications needed
            starts = other.indptr[self._gb_col_row.unique_keys[0]]
            ends = other.indptr[self._gb_col_row.unique_keys[0] + 1]
            fullsize = (ends - starts).sum()
            nonzero = (ends > starts)
            lengths = (ends - starts)
            segs = ak.cumsum(lengths) - lengths

            fsegs = segs[nonzero]
            fstarts = starts[nonzero]
            fends = ends[nonzero]

            totlen = lengths.sum()
            slices = ak.ones(totlen, dtype=ak.akint64)
            diffs = ak.concatenate((ak.array([fstarts[0]]), fstarts[1:] - fends[:-1] + 1))

            # Set up arrays for multiplication
            slices[fsegs] = diffs
            fullsegs, ranges = fsegs, ak.cumsum(slices)
            fullBdom = other._gb_row_col.unique_keys[1][ranges]
            fullAdom = ak.broadcast(fullsegs, self._gb_col_row.unique_keys[1][nonzero], fullsize)
            fullBval = other.data[ranges]
            fullAval = ak.broadcast(fullsegs, self.data[nonzero], fullsize)
            fullprod = fullAval * fullBval

            # GroupBy indices and perform aggregate sum
            proddomGB = ak.GroupBy([fullAdom, fullBdom])
            result = proddomGB.sum(fullprod)
            return Csr(result[1], result[0][0], result[0][1], shape = (self.shape[0], other.shape[1]))
        else:
            resp = cast(str, ak.client.generic_msg(cmd="spgemm", args={"self_data": self.data, "other_indptr" : other.indptr, "other_data" : other.data, "self_shape_width": self.shape[0], "self_shape_height" : self.shape[1], "other_shape_width" : other.shape[0], "other_shape_height" : other.shape[1], "self_gb_rep" : self._gb_col_row, "other_gb_rep" : other._gb_row_col, "cname": self._cname, "rname": self._rname}));
            arr_ids = resp.split("+")
            data = ak.create_pdarray(f"created {arr_ids[2]}")
            indices = ak.create_pdarray(f"created {arr_ids[1]}")
            ind_ptr = ak.create_pdarray(f"created {arr_ids[0]}")
            return Csr(data, ind_ptr, indices, self.shape, assign_vals=True)