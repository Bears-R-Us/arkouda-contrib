from argparse import ArgumentError, ArgumentTypeError
from typing import cast
import arkouda as ak

class SparseMatrix:
    """ The parent class for COO, CSR, and CSC sparse matrix formats. 
    This class should not be used on its own in lieu of one of those three. """

    _binop_list = ["+",
                   "-",
                   "*",
                   "/"]

    def __repr__(self):
        return f"D: {self.data}, C: {self.columns}, R: {self.rows}"

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
                    return self.plus_scalar(other)
                elif is_float:
                    return self.plus_scalar(other)
                elif is_pdarray:
                    return self.plus_vector(other)
                elif is_sparse_matrix:
                    return "Base sparse_matrix class provided. Please use a specific format (COO, CSC, CSR)"
            elif binop == "-":
                if is_int:
                    return self.sub_scalar(other)
                elif is_float:
                    return self.sub_scalar(other)
                elif is_pdarray:
                    return self.sub_vector(other)
                elif is_sparse_matrix:
                    return "Base sparse_matrix class provided. Please use a specific format (COO, CSC, CSR)"
            elif binop == "*":
                if is_int:
                    return self.mul_scalar(other)
                elif is_float:
                    return self.mul_scalar(other)
                elif is_pdarray:
                    return self.mul_vector(other)
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
                    return self.plus_scalar(other)
                elif is_float:
                    return self.plus_scalar(other)
                elif is_pdarray:
                    return self.plus_vector(other)
                elif is_sparse_matrix:
                    return "Base sparse_matrix class provided. Please use a specific format (COO, CSC, CSR)"
            elif binop == "*":
                if is_int:
                    return self.mul_scalar(other)
                elif is_float:
                    return self.mul_scalar(other)
                elif is_pdarray:
                    return self.mul_vector(other)
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

    def plus_scalar(self, scalar):
        return

    def sub_scalar(self, scalar):
        return

    def mul_scalar(self, scalar):
        return

    def plus_vector(self, vector):
        return

    def sub_vector(self, vector):
        return

    def mul_vector(self, vector):
        return


class Coo(SparseMatrix):
    """ Coordinate Format (COO) """

    def __init__(self, data=None, columns=None, rows=None, shape=None, no_chpl=None, from_csr=None, from_csc=None):
        self.data = None
        self.columns = None
        self.rows = None
        self.shape = shape

        if from_csr or from_csc or no_chpl:
            self.rows = rows
            self.columns = columns
            self.shape = shape
            sorting_gb = ak.GroupBy([self.rows, self.columns])
            self.data = data[sorting_gb.permutation]
        else:
            resp = cast(str, ak.client.generic_msg(cmd="coo_construct", args={"data": data, "columns": columns, "rows": rows}))
            arr_ids = resp.split("+")
            self.data = ak.create_pdarray(f"created {arr_ids[0]}")
            self.columns = ak.create_pdarray(f"created {arr_ids[1]}")
            self.rows = ak.create_pdarray(f"created {arr_ids[2]}")

    # Format conversion functions ---------------------------------------------------
    def to_coo(self):
        return self

    def to_csr(self, no_chpl=None):
        return Csr(self.data, self.columns, self.rows, self.shape, no_chpl)

    def to_csc(self, no_chpl=None):
        return Csc(self.data, self.columns, self.rows, self.shape, no_chpl)

    # Arithmetic operation functions ---------------------------------------------------
    def plus_scalar(self, scalar):
        self_copy = Coo(self.data, self.columns, self.rows, self.shape)
        self_copy.data = self_copy.data + scalar
        return self_copy
    
    def sub_scalar(self, scalar):
        self_copy = Coo(self.data, self.columns, self.rows, self.shape)
        self_copy.data = self.data - scalar
        return self_copy

    def mul_scalar(self, scalar):
        self_copy = Coo(self.data, self.columns, self.rows, self.shape)
        self_copy.data = self.data * scalar
        return self_copy

    def plus_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        self_copy = Coo(self.data, self.columns, self.rows, self.shape)
        self_copy.data = self.data + vector[self.columns]
        return self_copy

    def sub_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        self_copy = Coo(self.data, self.columns, self.rows, self.shape)
        self_copy.data = self.data - vector[self.columns]
        return self_copy

    def mul_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        self_copy = Coo(self.data, self.columns, self.rows, self.shape)
        self_copy.data = self.data * vector[self.columns]
        return self_copy

    def dot(self, input):
        """ Dot product method for CSR class. Must provide additional matrix of any format to multiply in parameters. """
        if issubclass(type(input), ak.pdarray):
            temp_csr = self.to_csr()
            return temp_csr.vector_matrix_dot(input)
        if issubclass(type(input), ak.pdarray):
            temp_csr = self.to_csr()
            return temp_csr.matrix_matrix_dot(input)
        else:
            raise ArgumentTypeError

    def matrix_matrix_dot(self, matrix):
        return "Matrix/Matrix dot product not implemented yet"



class Csr(SparseMatrix):
    """ Compressed Sparse Row """

    def __init__(self, data, columns, rows, shape, no_chpl=None, finished_vals=False):
        if not no_chpl:
            resp = cast(str, ak.client.generic_msg(cmd="coo_to_csr", args={"data": data, "columns": columns, "rows": rows, "shape_width": shape[0], "shape_height": shape[1]}))
            arr_ids = resp.split("+")
            self.data = ak.create_pdarray(f"created {arr_ids[0]}")
            self.indices = ak.create_pdarray(f"created {arr_ids[1]}")
            self.shape = shape
            
            self._old_columns = ak.create_pdarray(f"created {arr_ids[2]}")
            self._old_rows = ak.create_pdarray(f"created {arr_ids[3]}")
            self._gb_row_col = arr_ids[4]
            self._gb_row = arr_ids[5]
            self._gb_row_val = arr_ids[6]
            self._gb_row_val_uk = arr_ids[7]
            self.indptr = ak.create_pdarray(f"created {arr_ids[8]}")
        elif finished_vals:
            self.data = data
            self.indices = columns
            self.indptr = rows
            self.shape = shape
        else:
            self._old_columns = columns
            self._old_rows = rows

            self._gb_row_col = ak.GroupBy([rows, columns])
            self._gb_row = ak.GroupBy(rows)
            self.data = data
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

    def __repr__(self):
        return f"D: {self.data}, C: {self.indices}, R: {self.indptr}"

    # Format conversion functions ---------------------------------------------------
    def to_coo(self, no_chpl=None):
        return Coo(data=self.data, columns=self._old_columns, rows=self._old_rows, shape=self.shape, from_csr=True)

    def to_csr(self):
        return self

    def to_csc(self, no_chpl=None):
        temp_coo = Coo(data=self.data, columns=self._old_columns, rows=self._old_rows, shape=self.shape, from_csr=True)
        return temp_coo.to_csc()

    # Arithmetic operation functions ---------------------------------------------------
    def plus_scalar(self, scalar):
        self_copy = Csr(self.data, self.old_columns, self.old_rows, self.shape)
        self_copy.data = self.data + scalar
        self_copy.gb_row_val = ak.GroupBy([self.old_rows, self.data])
        self_copy.gb_row_val_uk = ak.GroupBy(self.gb_row_val.unique_keys[0])
        return self_copy

    def sub_scalar(self, scalar):
        self_copy = Csr(self.data, self.old_columns, self.old_rows, self.shape)
        self_copy.data = self.data - scalar
        self_copy.gb_row_val = ak.GroupBy([self.old_rows, self.data])
        self_copy.gb_row_val_uk = ak.GroupBy(self.gb_row_val.unique_keys[0])
        return self_copy

    def mul_scalar(self, scalar):
        self_copy = Csr(self.data, self.old_columns, self.old_rows, self.shape)
        self_copy.data = self.data * scalar
        self_copy.gb_row_val = ak.GroupBy([self.old_rows, self.data])
        self_copy.gb_row_val_uk = ak.GroupBy(self.gb_row_val.unique_keys[0])
        return self_copy

    def plus_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        self_copy = Csr(self.data, self.old_columns, self.old_rows, self.shape)
        self_copy.data = self.data + vector[self.columns]
        self_copy.gb_row_val = ak.GroupBy([self.old_rows, self.data])
        self_copy.gb_row_val_uk = ak.GroupBy(self.gb_row_val.unique_keys[0])
        return self_copy

    def sub_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        self_copy = Csr(self.data, self.old_columns, self.old_rows, self.shape)
        self_copy.data = self.data - vector[self.columns]
        self_copy.gb_row_val = ak.GroupBy([self.old_rows, self.data])
        self_copy.gb_row_val_uk = ak.GroupBy(self.gb_row_val.unique_keys[0])
        return self_copy

    def mul_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        self_copy = Csr(self.data, self.old_columns, self.old_rows, self.shape)
        self_copy.data = self.data * vector[self.columns]
        self_copy.gb_row_val = ak.GroupBy([self.old_rows, self.data])
        self_copy.gb_row_val_uk = ak.GroupBy(self.gb_row_val.unique_keys[0])
        return self_copy

    def dot(self, input):
        """ Dot product method for CSR class. Must provide additional matrix of any format to multiply in parameters. """
        if str(type(input)) == "<class 'arkouda.pdarrayclass.pdarray'>":
            return self.vector_matrix_dot(input)
        if str(type(input)) == "<class ''>":
            return self.matrix_matrix_dot(input)
        else:
            print(type(input))

    def vector_matrix_dot(self, vector):
        vec = vector[self.columns]
        return self.gb_row.aggregate(vec * self.data, "sum")[1]

    def matrix_matrix_dot(self, matrix):
        return "Matrix/Matrix dot product not implemented yet"

        

class Csc(SparseMatrix):
    """ Compressed Sparse Column """

    def __init__(self, data, columns, rows, shape, no_chpl=None):
        if not no_chpl:
            resp = cast(str, ak.client.generic_msg(cmd="coo_to_csc", args={"data": data, "columns": columns, "rows": rows, "shape_width": shape[0], "shape_height": shape[1]}))
            arr_ids = resp.split("+")
            self.data = ak.create_pdarray(f"created {arr_ids[0]}")
            self.indices = ak.create_pdarray(f"created {arr_ids[1]}")
            self.shape = shape
            
            self._old_columns = ak.create_pdarray(f"created {arr_ids[2]}")
            self._old_rows = ak.create_pdarray(f"created {arr_ids[3]}")
            self._old_data = ak.create_pdarray(f"created {arr_ids[4]}")
            self._gb_row = arr_ids[5]
            self._gb_col_row = arr_ids[6]
            self._gb_col_row_uk = arr_ids[7]
            self.indptr = ak.create_pdarray(f"created {arr_ids[8]}")
            self._vname = arr_ids[9];
            self._cname = arr_ids[10];
            self._rname = arr_ids[11];
        else:
            self._old_data = data
            self._old_columns = columns
            self._old_rows = rows

            self._gb_row_col = ak.GroupBy([rows, columns])
            self._gb_col_row = ak.GroupBy([columns, rows])
            self._gb_row = ak.GroupBy(rows)
            self._gb_col_row_uk = ak.GroupBy(self._gb_col_row.unique_keys[0])
            self.data = data[self._gb_col_row.permutation]
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

    def __repr__(self):
        return f"D: {self.data}, C: {self.indptr}, R: {self.indices}"
    
    # Format conversion functions ---------------------------------------------------
    def to_coo(self, no_chpl=None):
        return Coo(data=self._old_data, columns=self._old_columns, rows=self._old_rows, shape=self.shape, from_csc=True)

    def to_csr(self, no_chpl=None):
        temp_coo = Coo(data=self._old_data, columns=self._old_columns, rows=self._old_rows, shape=self.shape, from_csc=True)
        return temp_coo.to_csr()

    def to_csc(self):
        return self

    # Arithmetic operation functions ---------------------------------------------------
    def plus_scalar(self, scalar):
        self_copy = Csc(self.data, self.old_columns, self.old_rows, self.shape)
        self_copy.data = self.data + scalar
        self_copy.old_data = self.old_data + scalar
        return self_copy

    def sub_scalar(self, scalar):
        self_copy = Csc(self.data, self.old_columns, self.old_rows, self.shape)
        self_copy.data = self.data - scalar
        self_copy.old_data = self.old_data - scalar
        return self_copy

    def mul_scalar(self, scalar):
        self_copy = Csc(self.data, self.old_columns, self.old_rows, self.shape)
        self_copy.data = self.data * scalar
        self_copy.old_data = self.old_data * scalar
        return self_copy

    def plus_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        temp_convert = self.to_csr()
        temp_convert.data = temp_convert.data + vector[temp_convert.columns]
        self_copy = temp_convert.to_csc()
        return self_copy

    def sub_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        temp_convert = self.to_csr()
        temp_convert.data = temp_convert.data - vector[temp_convert.columns]
        self_copy = temp_convert.to_csc()
        return self_copy

    def mul_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        temp_convert = self.to_csr()
        temp_convert.data = temp_convert.data * vector[temp_convert.columns]
        self_copy = temp_convert.to_csc()
        return self_copy

    def dot(self, input):
        """ Dot product method for CSR class. Must provide additional matrix of any format to multiply in parameters. """
        if str(type(input)) == "<class 'arkouda.pdarrayclass.pdarray'>":
            temp_csr = self.to_csr()
            return temp_csr.vector_matrix_dot(input)
        if str(type(input)) == "<class ''>":
            temp_csr = self.to_csr()
            return temp_csr.matrix_matrix_dot(input)
        else:
            raise ArgumentTypeError

    def spgemm(self, other, no_chpl=None):
        if not no_chpl:
            resp = cast(str, ak.client.generic_msg(cmd="spgemm", args={"self_data": self.data, "other_indptr" : other.indptr, "other_data" : other.data, "self_shape_width": self.shape[0], "self_shape_height" : self.shape[1], "other_shape_width" : other.shape[0], "other_shape_height" : other.shape[1], "self_gb_rep" : self._gb_col_row, "other_gb_rep" : other._gb_row_col, "cname": self._cname, "rname": self._rname}));
            arr_ids = resp.split("+")
            data = ak.create_pdarray(f"created {arr_ids[2]}")
            indices = ak.create_pdarray(f"created {arr_ids[1]}")
            ind_ptr = ak.create_pdarray(f"created {arr_ids[0]}")
            return Csr(data, indices, ind_ptr, self.shape, finished_vals=True)
        else:
            try:
                assert(self.shape[1] == other.shape[0])
            except:
                error_msg = f"array size mismatch"
                raise AttributeError(error_msg)
            starts = other.indptr[self._gb_col_row.unique_keys[0]]
            ends = other.indptr[self._gb_col_row.unique_keys[0] + 1]

            fullsize = (ends - starts).sum()
            nonzero = (ends > starts)

            lengths = (ends - starts)
            segs = ak.cumsum(lengths) - lengths
            totlen = lengths.sum()
            slices = ak.ones(totlen, dtype=ak.akint64)
            diffs = ak.concatenate((ak.array([starts[0]]), starts[1:] - starts[:-1] - (lengths[:-1] - 1)))
            slices[segs] = diffs
            fullsegs, ranges =  segs, ak.cumsum(slices)

            # fullsegs, ranges = ak.gen_ranges(starts[nonzero], ends[nonzero])
            fullBdom = other._gb_row_col.unique_keys[1][ranges]
            fullAdom = ak.broadcast(fullsegs, self._gb_col_row.unique_keys[1][nonzero], fullsize)

            fullBval = other.data[ranges]
            fullAval = ak.broadcast(fullsegs, self.data[nonzero], fullsize)

            fullprod = fullAval * fullBval
            proddomGB = ak.GroupBy([fullAdom, fullBdom])
            result = proddomGB.sum(fullprod)
            
            return Csr(result[1], result[0][1], result[0][0], shape = (self.shape[0], other.shape[1]), no_chpl=True)