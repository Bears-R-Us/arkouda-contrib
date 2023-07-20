from argparse import ArgumentError, ArgumentTypeError
from typing import cast
import arkouda as ak
import os
import json

PROC_METHOD = bool(os.getenv("AK_PROC_METHOD", default=0))

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
                    return self._plus_scalar(other)
                elif is_float:
                    return self._plus_scalar(other)
                elif is_pdarray:
                    return self._plus_vector(other)
                elif is_sparse_matrix:
                    return "Base sparse_matrix class provided. Please use a specific format (COO, CSC, CSR)"
            elif binop == "-":
                if is_int:
                    return self._sub_scalar(other)
                elif is_float:
                    return self._sub_scalar(other)
                elif is_pdarray:
                    return self._sub_vector(other)
                elif is_sparse_matrix:
                    return "Base sparse_matrix class provided. Please use a specific format (COO, CSC, CSR)"
            elif binop == "*":
                if is_int:
                    return self._mul_scalar(other)
                elif is_float:
                    return self._mul_scalar(other)
                elif is_pdarray:
                    return self._mul_vector(other)
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
                    return self._plus_scalar(other)
                elif is_float:
                    return self._plus_scalar(other)
                elif is_pdarray:
                    return self._plus_vector(other)
                elif is_sparse_matrix:
                    return "Base sparse_matrix class provided. Please use a specific format (COO, CSC, CSR)"
            elif binop == "*":
                if is_int:
                    return self._mul_scalar(other)
                elif is_float:
                    return self._mul_scalar(other)
                elif is_pdarray:
                    return self._mul_vector(other)
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

    def _plus_scalar(self, scalar):
        return

    def _sub_scalar(self, scalar):
        return

    def _mul_scalar(self, scalar):
        return

    def _plus_vector(self, vector):
        return

    def _sub_vector(self, vector):
        return

    def _mul_vector(self, vector):
        return

    # Additional features to be added from scipy.sparse.coo_matrix()
    # https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.coo_matrix.html#scipy.sparse.coo_matrix

class Coo(SparseMatrix):
    """A sparse matrix in COOrdinate format. Also known as the 'ijv' or 'triplet' format."""

    def __init__(self, data, rows, columns, shape):
        if PROC_METHOD:
            self.rows = rows
            self.cols = columns
            self.shape = shape
            self.data = data
            self.nnz = len(self.data)
        else:
            self.shape = shape
            resp = cast(str, ak.client.generic_msg(cmd="coo_construct", args={"data": data, "rows": rows, "columns": columns}))
            arr_ids = json.loads(resp)
            self.data = ak.create_pdarray(arr_ids["valname"])
            self.cols = ak.create_pdarray(arr_ids["colname"])
            self.rows = ak.create_pdarray(arr_ids["rowname"])
            self.nnz = len(self.data)

    # Format conversion functions (must currently assign to new variable)-----------------------------------------
    def to_coo(self):
        """Convert this array to COOrdinate format."""
        return self

    def to_csr(self):
        """Convert this matrix to Compressed Sparse Row format."""
        return Csr(self.data, self.rows, self.cols, self.shape)

    def to_csc(self):
        """Convert this matrix to Compressed Sparse Column format."""
        return Csc(self.data, self.rows, self.cols, self.shape)

    # Arithmetic operation functions ---------------------------------------------------
    def _plus_scalar(self, scalar):
        self_copy = Coo(self.data, self.rows, self.cols, self.shape)
        self_copy.data = self_copy.data + scalar
        return self_copy
    
    def _sub_scalar(self, scalar):
        self_copy = Coo(self.data, self.rows, self.cols, self.shape)
        self_copy.data = self.data - scalar
        return self_copy

    def _mul_scalar(self, scalar):
        self_copy = Coo(self.data, self.rows, self.cols, self.shape)
        self_copy.data = self.data * scalar
        return self_copy

    def _plus_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        self_copy = Coo(self.data, self.rows, self.cols, self.shape)
        self_copy.data = self.data + vector[self.cols]
        return self_copy

    def _sub_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        self_copy = Coo(self.data, self.rows, self.cols, self.shape)
        self_copy.data = self.data - vector[self.cols]
        return self_copy

    def _mul_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        self_copy = Coo(self.data, self.rows, self.cols, self.shape)
        self_copy.data = self.data * vector[self.cols]
        return self_copy

    def dot(self, input):
        """Dot product method for CSR class. Must provide additional matrix of any format to multiply in parameters."""
        if issubclass(type(input), ak.pdarray):
            temp_csr = self.to_csr()
            return temp_csr.vector_matrix_dot(input)
        if issubclass(type(input), ak.pdarray):
            raise NotImplementedError
        else:
            raise ArgumentTypeError



class Csr(SparseMatrix):
    """Compressed Sparse Row matrix."""

    def __init__(self, data, rows, columns, shape, assign_vals=None):
        if PROC_METHOD:
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
        elif assign_vals:               # Used exclusively for server-side SpGeMM results
            self.data = data
            self.nnz = len(self.data)
            self.indices = columns
            self.indptr = rows
            self.shape = shape
        else:
            resp = cast(str, ak.client.generic_msg(cmd="coo_to_csr", args={"data": data, "rows": rows, "columns": columns, "shape_width": shape[0], "shape_height": shape[1]}))
            arr_ids = json.loads(resp)
            self.data = ak.create_pdarray(arr_ids["valsname"])
            self.nnz = len(self.data)
            self.indices = ak.create_pdarray(arr_ids["colsname"])
            self.shape = shape
            
            self._gb_row_col = arr_ids["gb_row_col_name"]
            self._gb_row = arr_ids["gb_row_name"]
            self._gb_row_val = arr_ids["gb_row_val_name"]
            self._gb_row_val_uk = arr_ids["gb_row_val_uk_name"]
            self.indptr = ak.create_pdarray(arr_ids["final_rows_name"])

    def __repr__(self):
        return f"Data: {self.data}\nColumn Indices: {self.indices}\nRow Pointers: {self.indptr}"

    # Format conversion functions (must currently assign to new variable)-----------------------------------------
    def to_coo(self):  
        """Convert this array to COOrdinate format."""
        gb = ak.GroupBy(self.indptr, assume_sorted=True)
        uk, count = gb.count()
        self._temp = ak.zeros_like(self.indices)
        self._temp[uk[:-1]] = count[:-1]
        self._temp[0] -= 1
        self._temp = ak.cumsum(self._temp)
        return Coo(self.data, self._temp, self.indices, self.shape)

    def to_csr(self):
        """Convert this matrix to Compressed Sparse Row format."""
        return self

    def to_csc(self):
        """Convert this matrix to Compressed Sparse Column format."""
        temp_coo = self.to_coo()
        return temp_coo.to_csc()

    # Arithmetic operation functions ---------------------------------------------------
    def _plus_scalar(self, scalar):
        temp_coo = self.to_coo()
        self_copy = Csr(temp_coo.data, temp_coo.rows, temp_coo.cols, temp_coo.shape)
        self_copy.data = self.data + scalar
        self_copy.gb_row_val = ak.GroupBy([temp_coo.rows, self.data])
        self_copy.gb_row_val_uk = ak.GroupBy(self.gb_row_val.unique_keys[0])
        return self_copy

    def _sub_scalar(self, scalar):
        temp_coo = self.to_coo()
        self_copy = Csr(temp_coo.data, temp_coo.rows, temp_coo.cols, temp_coo.shape)
        self_copy.data = temp_coo.data - scalar
        self_copy.gb_row_val = ak.GroupBy([temp_coo.rows, temp_coo.data])
        self_copy.gb_row_val_uk = ak.GroupBy(self.gb_row_val.unique_keys[0])
        return self_copy

    def _mul_scalar(self, scalar):
        temp_coo = self.to_coo()
        self_copy = Csr(temp_coo.data, temp_coo.rows, temp_coo.cols, temp_coo.shape)
        self_copy.data = temp_coo.data * scalar
        self_copy.gb_row_val = ak.GroupBy([temp_coo.rows, temp_coo.data])
        self_copy.gb_row_val_uk = ak.GroupBy(self.gb_row_val.unique_keys[0])
        return self_copy

    def _plus_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        temp_coo = self.to_coo()
        self_copy = Csr(temp_coo.data, temp_coo.rows, temp_coo.cols, temp_coo.shape)
        self_copy.data = temp_coo.data + vector[temp_coo.cols]
        self_copy.gb_row_val = ak.GroupBy([temp_coo.rows, temp_coo.data])
        self_copy.gb_row_val_uk = ak.GroupBy(self.gb_row_val.unique_keys[0])
        return self_copy

    def _sub_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        temp_coo = self.to_coo()
        self_copy = Csr(temp_coo.data, temp_coo.rows, temp_coo.cols, temp_coo.shape)
        self_copy.data = temp_coo.data - vector[temp_coo.cols]
        self_copy.gb_row_val = ak.GroupBy([temp_coo.rows, temp_coo.data])
        self_copy.gb_row_val_uk = ak.GroupBy(self.gb_row_val.unique_keys[0])
        return self_copy

    def _mul_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        temp_coo = self.to_coo()
        self_copy = Csr(temp_coo.data, temp_coo.rows, temp_coo.cols, temp_coo.shape)
        self_copy.data = temp_coo.data * vector[temp_coo.cols]
        self_copy.gb_row_val = ak.GroupBy([temp_coo.rows, temp_coo.data])
        self_copy.gb_row_val_uk = ak.GroupBy(self.gb_row_val.unique_keys[0])
        return self_copy

    def dot(self, input):
        """Dot product method for CSR class. Must provide additional matrix of any format to multiply in parameters."""
        if str(type(input)) == "<class 'arkouda.pdarrayclass.pdarray'>":
            return self.vector_matrix_dot(input)
        if str(type(input)) == "<class ''>":
            raise NotImplementedError
        else:
            print(type(input))

    def vector_matrix_dot(self, vector):
        vec = vector[self.cols]
        return self.gb_row.aggregate(vec * self.data, "sum")[1]

        

class Csc(SparseMatrix):
    """Compressed Sparse Column matrix."""

    def __init__(self, data, rows, columns, shape):
        if PROC_METHOD:
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
        else:
            resp = cast(str, ak.client.generic_msg(cmd="coo_to_csc", args={"data": data, "rows": rows, "columns": columns, "shape_width": shape[0], "shape_height": shape[1]}))
            arr_ids = json.loads(resp)
            self.data = ak.create_pdarray(arr_ids["valsname"])
            self.nnz = len(self.data)
            self.indices = ak.create_pdarray(arr_ids["rowsname"])
            self.shape = shape
            
            self._gb_row = arr_ids["gb_row_name"]
            self._gb_col_row = arr_ids["gb_col_row_name"]
            self._gb_col_row_uk = arr_ids["gb_col_row_uk_name"]
            self.indptr = ak.create_pdarray(arr_ids["final_cols_name"])
            self._vname = arr_ids["vname"]
            self._cname = arr_ids["cname"]
            self._rname = arr_ids["rname"]

    def __repr__(self):
        return f"Data: {self.data}\nRow Indices: {self.indices}\nColumn Pointers: {self.indptr}"
    
    # Format conversion functions (must currently assign to new variable)-----------------------------------------
    def to_coo(self):
        """Convert this array to COOrdinate format."""
        gb = ak.GroupBy(self.indptr, assume_sorted=True)
        uk, count = gb.count()
        temp = ak.zeros_like(self.indices)
        temp[uk[:-1]] = count[:-1]
        temp[0] -= 1
        self._temp = ak.cumsum(temp)
        return Coo(self.data, self.indices, self._temp, self.shape)   
    
    def to_csr(self):
        """Convert this matrix to Compressed Sparse Row format."""
        temp_coo = self.to_coo()
        return temp_coo.to_csr()

    def to_csc(self):
        """Convert this matrix to Compressed Sparse Column format."""
        return self

    # Arithmetic operation functions ---------------------------------------------------
    def _plus_scalar(self, scalar):
        temp_coo = self.to_coo()
        self_copy = Csc(temp_coo.data, temp_coo.rows, temp_coo.cols, temp_coo.shape)
        self_copy.data = temp_coo.data + scalar
        return self_copy

    def _sub_scalar(self, scalar):
        temp_coo = self.to_coo()
        self_copy = Csc(temp_coo.data, temp_coo.rows, temp_coo.cols, temp_coo.shape)
        self_copy.data = temp_coo.data - scalar
        return self_copy

    def _mul_scalar(self, scalar):
        temp_coo = self.to_coo()
        self_copy = Csc(temp_coo.data, temp_coo.rows, temp_coo.cols, temp_coo.shape)
        self_copy.data = temp_coo.data * scalar
        return self_copy

    def _plus_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        temp_convert = self.to_csr()
        temp_convert.data = temp_convert.data + vector[temp_convert.cols]
        self_copy = temp_convert.to_csc()
        return self_copy

    def _sub_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        temp_convert = self.to_csr()
        temp_convert.data = temp_convert.data - vector[temp_convert.cols]
        self_copy = temp_convert.to_csc()
        return self_copy

    def _mul_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        temp_convert = self.to_csr()
        temp_convert.data = temp_convert.data * vector[temp_convert.cols]
        self_copy = temp_convert.to_csc()
        return self_copy

    def dot(self, input):
        """Dot product method for CSR class. Must provide additional matrix of any format to multiply in parameters."""
        if str(type(input)) == "<class 'arkouda.pdarrayclass.pdarray'>":
            temp_csr = self.to_csr()
            return temp_csr.vector_matrix_dot(input)
        if str(type(input)) == "<class ''>":
            raise NotImplementedError
        else:
            raise ArgumentTypeError

    def spgemm(self, other):
        """Sparse General Matrix Multiplication"""
        if PROC_METHOD:
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
            arr_ids = json.loads(resp)
            data = ak.create_pdarray(arr_ids["reorderedname"])
            indices = ak.create_pdarray(arr_ids["result2name"])
            ind_ptr = ak.create_pdarray(arr_ids["ind_ptrname"])
            return Csr(data, ind_ptr, indices, self.shape, assign_vals=True)