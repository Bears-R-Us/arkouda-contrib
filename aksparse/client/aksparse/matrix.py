from argparse import ArgumentError, ArgumentTypeError
import arkouda as ak

class sparse_matrix:
    """ The parent class for COO, CSR, and CSC sparse matrix formats. 
    This class should not be used on its own in lieu of one of those three. """

    _binop_list = ["+",
                   "-",
                   "*"]

    def __repr__(self):
        return f"V: {self.values}, C: {self.columns}, R: {self.rows}"

    def _binop(self, other, binop):
        # Supported types for arithmetic operations
        is_pdarray = issubclass(type(other), ak.pdarray)
        is_sparse_matrix = issubclass(type(other), sparse_matrix)
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
        is_sparse_matrix = issubclass(type(other), sparse_matrix)
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


class coo(sparse_matrix):
    """ Coordinate Format (COO) """

    def __init__(self, values=None, columns=None, rows=None, shape=None, dense_matrix=None):
        self.values = None
        self.columns = None
        self.rows = None
        self.shape = None
        
        # Build from existing matrix
        if dense_matrix:
            v, x, y = [], [], []
            for row in range(len(dense_matrix)):
                for col in range(len(dense_matrix[0])):
                    if dense_matrix[row][col] != 0:
                        v.append(dense_matrix[row][col])
                        x.append(col)
                        y.append(row)
            self.values = ak.array(v)
            self.columns = ak.array(x)
            self.rows = ak.array(y)
            if shape == None:
                self.shape = (len(dense_matrix[0]), len(dense_matrix))
            else:
                self.shape = shape
        # Build from provided data arrays
        elif values is not None and columns is not None and rows is not None:
            self.values = ak.array(values)
            self.columns = ak.array(columns)
            self.rows = ak.array(rows)
            if shape == None:
                self.shape = (len(columns), len(rows))
            else:
                self.shape = shape
        else:
            return None

    # Format conversion functions ---------------------------------------------------
    def to_coo(self):
        return self

    def to_csr(self):
        return csr(self.values, self.columns, self.rows, self.shape)

    def to_csc(self):
        return csc(self.values, self.columns, self.rows, self.shape)

    # Arithmetic operation functions ---------------------------------------------------
    def plus_scalar(self, scalar):
        self_copy = coo(self.values, self.columns, self.rows, self.shape)
        self_copy.values = self_copy.values + scalar
        return self_copy
    
    def sub_scalar(self, scalar):
        self_copy = coo(self.values, self.columns, self.rows, self.shape)
        self_copy.values = self.values - scalar
        return self_copy

    def mul_scalar(self, scalar):
        self_copy = coo(self.values, self.columns, self.rows, self.shape)
        self_copy.values = self.values * scalar
        return self_copy

    def plus_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        self_copy = coo(self.values, self.columns, self.rows, self.shape)
        self_copy.values = self.values + vector[self.columns]
        return self_copy

    def sub_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        self_copy = coo(self.values, self.columns, self.rows, self.shape)
        self_copy.values = self.values - vector[self.columns]
        return self_copy

    def mul_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        self_copy = coo(self.values, self.columns, self.rows, self.shape)
        self_copy.values = self.values * vector[self.columns]
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



class csr(sparse_matrix):
    """ Compressed Sparse Row """

    def __init__(self, values, columns, rows, shape):
        self.old_columns = columns
        self.old_rows = rows

        self.gb_row_col = ak.GroupBy([rows, columns])
        self.gb_row = ak.GroupBy(rows)
        self.values = values
        self.columns = columns
        self.gb_row_val = ak.GroupBy([rows, values])
        self.gb_row_val_uk = ak.GroupBy(self.gb_row_val.unique_keys[0])

        self.shape = shape
        
        segs = ak.concatenate([self.gb_row_val_uk.segments, ak.array([len(self.values)])])
        diffs = segs[1:] - segs[:-1]
        ind_ptr = ak.zeros(shape[1] + 1, ak.int64)
        ind_ptr[self.gb_row_val_uk.unique_keys + 1] = diffs
        ind_ptr = ak.cumsum(ind_ptr)
        for i in range(shape[1] - (len(ind_ptr) - 1)):
            ind_ptr = ak.concatenate([ind_ptr, ind_ptr[-1:]])
        self.rows = ind_ptr

    # Format conversion functions ---------------------------------------------------
    def to_coo(self):
        return coo(values=self.values, columns=self.gb_row_col.unique_keys[1], rows=self.gb_row_col.unique_keys[0], shape=self.shape)

    def to_csr(self):
        return self

    def to_csc(self):
        return csc(values=self.values, columns=self.gb_row_col.unique_keys[1], rows=self.gb_row_col.unique_keys[0], shape=self.shape)

    # Arithmetic operation functions ---------------------------------------------------
    def plus_scalar(self, scalar):
        self_copy = csr(self.values, self.old_columns, self.old_rows, self.shape)
        self_copy.values = self.values + scalar
        self_copy.gb_row_val = ak.GroupBy([self.old_rows, self.values])
        self_copy.gb_row_val_uk = ak.GroupBy(self.gb_row_val.unique_keys[0])
        return self_copy

    def sub_scalar(self, scalar):
        self_copy = csr(self.values, self.old_columns, self.old_rows, self.shape)
        self_copy.values = self.values - scalar
        self_copy.gb_row_val = ak.GroupBy([self.old_rows, self.values])
        self_copy.gb_row_val_uk = ak.GroupBy(self.gb_row_val.unique_keys[0])
        return self_copy

    def mul_scalar(self, scalar):
        self_copy = csr(self.values, self.old_columns, self.old_rows, self.shape)
        self_copy.values = self.values * scalar
        self_copy.gb_row_val = ak.GroupBy([self.old_rows, self.values])
        self_copy.gb_row_val_uk = ak.GroupBy(self.gb_row_val.unique_keys[0])
        return self_copy

    def plus_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        self_copy = csr(self.values, self.old_columns, self.old_rows, self.shape)
        self_copy.values = self.values + vector[self.columns]
        self_copy.gb_row_val = ak.GroupBy([self.old_rows, self.values])
        self_copy.gb_row_val_uk = ak.GroupBy(self.gb_row_val.unique_keys[0])
        return self_copy

    def sub_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        self_copy = csr(self.values, self.old_columns, self.old_rows, self.shape)
        self_copy.values = self.values - vector[self.columns]
        self_copy.gb_row_val = ak.GroupBy([self.old_rows, self.values])
        self_copy.gb_row_val_uk = ak.GroupBy(self.gb_row_val.unique_keys[0])
        return self_copy

    def mul_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        self_copy = csr(self.values, self.old_columns, self.old_rows, self.shape)
        self_copy.values = self.values * vector[self.columns]
        self_copy.gb_row_val = ak.GroupBy([self.old_rows, self.values])
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
        return self.gb_row.aggregate(vec * self.values, "sum")[1]

    def matrix_matrix_dot(self, matrix):
        return "Matrix/Matrix dot product not implemented yet"

        

class csc(sparse_matrix):
    """ Compressed Sparse Column """

    def __init__(self, values, columns, rows, shape):
        self.old_values = values
        self.old_columns = columns
        self.old_rows = rows

        self.gb_row_col = ak.GroupBy([rows, columns])
        self.gb_col_row = ak.GroupBy([columns, rows])
        self.gb_col_row_uk = ak.GroupBy(self.gb_col_row.unique_keys[0])
        self.values = values[self.gb_col_row.permutation]
        self.rows = rows[self.gb_col_row.permutation]

        self.shape = shape

        segs = ak.concatenate([self.gb_col_row_uk.segments, ak.array([len(self.values)])])
        diffs = segs[1:] - segs[:-1]
        ind_ptr = ak.zeros(shape[0] + 1, ak.int64)
        ind_ptr[self.gb_col_row_uk.unique_keys + 1] = diffs
        ind_ptr = ak.cumsum(ind_ptr)
        for i in range(shape[0] - (len(ind_ptr) - 1)):
            ind_ptr = ak.concatenate([ind_ptr, ind_ptr[-1:]])
        self.columns = ind_ptr
    
    # Format conversion functions ---------------------------------------------------
    def to_coo(self):
        return coo(values=self.old_values, columns=self.gb_row_col.unique_keys[1], rows=self.gb_row_col.unique_keys[0], shape=self.shape)

    def to_csr(self):
        return csr(values=self.old_values, columns=self.gb_row_col.unique_keys[1], rows=self.gb_row_col.unique_keys[0], shape=self.shape)

    def to_csc(self):
        return self

    # Arithmetic operation functions ---------------------------------------------------
    def plus_scalar(self, scalar):
        self_copy = csc(self.values, self.old_columns, self.old_rows, self.shape)
        self_copy.values = self.values + scalar
        self_copy.old_values = self.old_values + scalar
        return self_copy

    def sub_scalar(self, scalar):
        self_copy = csc(self.values, self.old_columns, self.old_rows, self.shape)
        self_copy.values = self.values - scalar
        self_copy.old_values = self.old_values - scalar
        return self_copy

    def mul_scalar(self, scalar):
        self_copy = csc(self.values, self.old_columns, self.old_rows, self.shape)
        self_copy.values = self.values * scalar
        self_copy.old_values = self.old_values * scalar
        return self_copy

    def plus_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        temp_convert = self.to_csr()
        temp_convert.values = temp_convert.values + vector[temp_convert.columns]
        self_copy = temp_convert.to_csc()
        return self_copy

    def sub_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        temp_convert = self.to_csr()
        temp_convert.values = temp_convert.values - vector[temp_convert.columns]
        self_copy = temp_convert.to_csc()
        return self_copy

    def mul_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        temp_convert = self.to_csr()
        temp_convert.values = temp_convert.values * vector[temp_convert.columns]
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

    def matrix_matrix_dot(self, matrix):
        return "Matrix/Matrix dot product not implemented yet"
