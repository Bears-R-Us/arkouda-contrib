from argparse import ArgumentError, ArgumentTypeError
import arkouda as ak
from scipy.sparse import coo_matrix, csr_matrix, csc_matrix
from numpy import ndarray

class sparse_matrix:
    """ The parent class for COO, CSR, and CSC sparse matrix formats. 
    This class should not be used on its own in lieu of one of those three. """

    _binop_list = ["+",
                   "-",
                   "*"]

    def __repr__(self):
        return f"V: {self.data}, C: {self.columns}, R: {self.rows}"

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
                    return self.mul_vector_r(other)
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

    def mul_vector_r(self, vector):
        return


class coo(sparse_matrix):
    """ Coordinate Format (COO) """

    # data=None, columns=None, rows=None, shape=None, dense_matrix=None
    def __init__(self, *args):
        self.data = []
        self.columns = []
        self.rows = []
        self.shape = ()
        
        # Converting from dense matrix (either 2d Python list or ndarray)
        try:
            if (isinstance(args[0], list) and isinstance(args[0][0], list)) or (isinstance(args[0], ndarray) and isinstance(args[0][0], ndarray)):
                dense_matrix = args[0]
                temp_data = []
                temp_columns = []
                temp_rows = []
                for i in range(len(dense_matrix[0])):
                    for j in range(len(dense_matrix)):
                        if dense_matrix[j][i] != 0:
                            temp_data.append(dense_matrix[j][i])
                            temp_columns.append(i)
                            temp_rows.append(j)
                self.data = ak.array(temp_data)
                self.columns = ak.array(temp_columns)
                self.rows = ak.array(temp_rows)
                self.shape = (len(dense_matrix), len(dense_matrix[0]))
        except:
            raise ArgumentTypeError
        
        # Converting from another sparse matrix format
        try:
            if issubclass(type(args[0]), csr):
                arg_csr = args[0]
                self.data = arg_csr.data
                self.columns = arg_csr.gb_row_col.unique_keys[1]
                self.rows = arg_csr.gb_row_col.unique_keys[0]
                self.shape = arg_csr.shape
            elif issubclass(type(args[0]), csc):
                arg_csc = args[0]
                self.data = arg_csc.old_data
                self.columns = arg_csc.gb_row_col.unique_keys[1]
                self.rows = arg_csc.gb_row_col.unique_keys[0]
                self.shape = arg_csc.shape
        except:
            raise ArgumentTypeError

    def __repr__(self):
        print_result = ""
        for i in range(len(self.data)):
            print_result += f"  ({self.rows[i]}, {self.columns[i]})        {self.data[i]}"
            if i < len(self.data) - 1:
                print_result += "\n"
        return print_result

    def print_visualization(self):
        rows = []
        for row in range(self.shape[1]):
            row = [0] * self.shape[0]
            rows.append(row)
        for i in range(len(self.data)):
            rows[self.rows[i]][self.columns[i]] = self.data[i]
        coo_string = f"[{rows[0]}\n"
        # Assemble printable string form
        for i in range(1, len(rows) - 1):
            coo_string += f" {str(rows[i])}\n"
        coo_string += f" {rows[-1]}]"
        return f"{coo_string}"

    def toarray(self):
        array = [[0 for i in range(self.shape[1])] for j in range(self.shape[0])]
        for i in range(len(self.data)):
            array[self.rows[i]][self.columns[i]] = self.data[i]
        return array

    # Format conversion functions ---------------------------------------------------
    def tocoo(self):
        return self

    def tocsr(self):
        return csr(self)

    def tocsc(self):
        return csc(self)

    def toscipy(self):
        return coo_matrix((self.data.to_ndarray(), (self.rows.to_ndarray(), self.columns.to_ndarray())), shape=self.shape)

    # Common use functions -------------------------------------------------------------

    def count_nonzero(self):
        return len(self.data)

    def eliminate_zeros(self):
        for i in range(len(self.data)):
            if self.data[i] == 0:
                self.data = self.pop(i)
                self.columns.pop(i)
                self.rows.pop(i)

    # Arithmetic operation functions ---------------------------------------------------
    def plus_scalar(self, scalar):
        # Create new dense rows/columns arrays
        row_range = [0] * (self.shape[0] * self.shape[1])
        for i in range(self.shape[0] + 1):
            row_range[i * self.shape[0]:i * self.shape[0] + self.shape[0]] = [i] * self.shape[0]
        rows = ak.array(row_range)
        col_range = list(range(self.shape[0]))
        columns = ak.array(col_range * self.shape[1])
        self_copy = coo(self.data, columns, rows, self.shape)
        # Create new dense data array
        self_copy.data = ak.zeros(self.shape[0] * self.shape[1], dtype=int) + scalar
        pos_mask = self.columns + (self.rows * self.shape[0])
        self_copy.data[pos_mask] = self_copy.data[pos_mask] + self.data
        return self_copy
    
    def sub_scalar(self, scalar):
        # Create new dense rows/columns arrays
        row_range = [0] * (self.shape[0] * self.shape[1])
        for i in range(self.shape[0] + 1):
            row_range[i * self.shape[0]:i * self.shape[0] + self.shape[0]] = [i] * self.shape[0]
        rows = ak.array(row_range)
        col_range = list(range(self.shape[0]))
        columns = ak.array(col_range * self.shape[1])
        self_copy = coo(self.data, columns, rows, self.shape)
        # Create new dense data array
        self_copy.data = ak.zeros(self.shape[0] * self.shape[1], dtype=int) + scalar
        pos_mask = self.columns + (self.rows * self.shape[0])
        self_copy.data[pos_mask] = self_copy.data[pos_mask] - self.data
        return self_copy

    def mul_scalar(self, scalar):
        # Create new dense rows/columns arrays
        row_range = [0] * (self.shape[0] * self.shape[1])
        for i in range(self.shape[0] + 1):
            row_range[i * self.shape[0]:i * self.shape[0] + self.shape[0]] = [i] * self.shape[0]
        rows = ak.array(row_range)
        col_range = list(range(self.shape[0]))
        columns = ak.array(col_range * self.shape[1])
        self_copy = coo(self.data, columns, rows, self.shape)
        # Create new dense data array
        self_copy.data = ak.zeros(self.shape[0] * self.shape[1], dtype=int) + scalar
        pos_mask = self.columns + (self.rows * self.shape[0])
        self_copy.data[pos_mask] = self_copy.data[pos_mask] * self.data
        return self_copy

    def plus_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        self_copy = coo(self.data, self.columns, self.rows, self.shape)
        self_copy.data = self.data + vector[self.columns]
        return self_copy

    def sub_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        self_copy = coo(self.data, self.columns, self.rows, self.shape)
        self_copy.data = self.data - vector[self.columns]
        return self_copy

    def mul_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        self_copy = coo(self.data, self.columns, self.rows, self.shape)
        self_copy.data = self.data * vector[self.columns]
        return self_copy

    def dot(self, input):
        """ Dot product method for CSR class. Must provide additional matrix of any format to multiply in parameters. """
        if issubclass(type(input), ak.pdarray):
            temp_csr = self.tocsr()
            return temp_csr.vector_matrix_dot(input)
        if issubclass(type(input), ak.pdarray):
            temp_csr = self.tocsr()
            return temp_csr.matrix_matrix_dot(input)
        else:
            raise ArgumentTypeError

    def matrix_matrix_dot(self, matrix):
        return "Matrix/Matrix dot product not implemented yet"



class csr(sparse_matrix):
    """ Compressed Sparse Row """

    def __init__(self, *args):
        self.data = []
        self.columns = []
        self.rows = []
        self.shape = ()
        
        # Converting from another sparse matrix format
        try:
            if issubclass(type(args[0]), sparse_matrix):
                old_matrix = args[0].tocoo()

                self.old_columns = old_matrix.columns
                self.old_rows = old_matrix.rows

                self.gb_row_col = ak.GroupBy([old_matrix.rows, old_matrix.columns])
                self.gb_row = ak.GroupBy(old_matrix.rows)
                self.data = old_matrix.data
                self.columns = old_matrix.columns
                self.gb_row_val = ak.GroupBy([old_matrix.rows, old_matrix.data])
                self.gb_row_val_uk = ak.GroupBy(self.gb_row_val.unique_keys[0])

                self.shape = old_matrix.shape
                
                segs = ak.concatenate([self.gb_row_val_uk.segments, ak.array([len(self.data)])])
                diffs = segs[1:] - segs[:-1]
                ind_ptr = ak.zeros(old_matrix.shape[1] + 1, ak.int64)
                ind_ptr[self.gb_row_val_uk.unique_keys + 1] = diffs
                ind_ptr = ak.cumsum(ind_ptr)
                for i in range(old_matrix.shape[1] - (len(ind_ptr) - 1)):
                    ind_ptr = ak.concatenate([ind_ptr, ind_ptr[-1:]])
                self.rows = ind_ptr
        except:
            raise ArgumentTypeError

    def __repr__(self):
        temp_coo = self.tocoo()
        print_result = ""
        for i in range(len(temp_coo.data)):
            print_result += f"  ({temp_coo.rows[i]}, {temp_coo.columns[i]})        {temp_coo.data[i]}"
            if i < len(temp_coo.data) - 1:
                print_result += "\n"
        return print_result

    # Format conversion functions ---------------------------------------------------
    def tocoo(self):
        return coo(self)

    def tocsr(self):
        return self

    def tocsc(self):
        return csc(self)

    def toscipy(self):
        temp_coo = self.tocoo()
        return csr_matrix((temp_coo.data.to_ndarray(), (temp_coo.rows.to_ndarray(), temp_coo.columns.to_ndarray())), shape=self.shape)

    # Arithmetic operation functions ---------------------------------------------------
    def plus_scalar(self, scalar):
        temp_coo = self.tocoo()
        return temp_coo.plus_scalar().tocsr()

    def sub_scalar(self, scalar):
        temp_coo = self.tocoo()
        return temp_coo.sub_scalar().tocsr()

    def mul_scalar(self, scalar):
        temp_coo = self.tocoo()
        return temp_coo.mul_scalar().tocsr()

    def plus_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        self_copy = csr(self.data, self.old_columns, self.old_rows, self.shape)
        self_copy.data = self.data + vector[self.columns]
        self_copy.gb_row_val = ak.GroupBy([self.old_rows, self.data])
        self_copy.gb_row_val_uk = ak.GroupBy(self.gb_row_val.unique_keys[0])
        return self_copy

    def sub_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        self_copy = csr(self.data, self.old_columns, self.old_rows, self.shape)
        self_copy.data = self.data - vector[self.columns]
        self_copy.gb_row_val = ak.GroupBy([self.old_rows, self.data])
        self_copy.gb_row_val_uk = ak.GroupBy(self.gb_row_val.unique_keys[0])
        return self_copy

    def mul_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        self_copy = csr(self.data, self.old_columns, self.old_rows, self.shape)
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

        

class csc(sparse_matrix):
    """ Compressed Sparse Column """

    def __init__(self, *args):
        self.data = []
        self.columns = []
        self.rows = []
        self.shape = ()
        
        # Converting from another sparse matrix format
        try:
            if issubclass(type(args[0]), sparse_matrix):
                old_matrix = args[0].tocoo()

                self.old_data = old_matrix.data
                self.old_columns = old_matrix.columns
                self.old_rows = old_matrix.rows

                self.gb_row_col = ak.GroupBy([old_matrix.rows, old_matrix.columns])
                self.gb_col_row = ak.GroupBy([old_matrix.columns, old_matrix.rows])
                self.gb_col_row_uk = ak.GroupBy(self.gb_col_row.unique_keys[0])
                self.data = old_matrix.data[self.gb_col_row.permutation]
                self.rows = old_matrix.rows[self.gb_col_row.permutation]

                self.shape = old_matrix.shape

                segs = ak.concatenate([self.gb_col_row_uk.segments, ak.array([len(self.data)])])
                diffs = segs[1:] - segs[:-1]
                ind_ptr = ak.zeros(old_matrix.shape[0] + 1, ak.int64)
                ind_ptr[self.gb_col_row_uk.unique_keys + 1] = diffs
                ind_ptr = ak.cumsum(ind_ptr)
                for i in range(old_matrix.shape[0] - (len(ind_ptr) - 1)):
                    ind_ptr = ak.concatenate([ind_ptr, ind_ptr[-1:]])
                self.columns = ind_ptr
        except:
            raise ArgumentTypeError

    def __repr__(self):
        temp_coo = self.tocoo()
        print_result = ""
        for i in range(len(temp_coo.data)):
            print_result += f"  ({temp_coo.rows[i]}, {temp_coo.columns[i]})        {temp_coo.data[i]}"
            if i < len(temp_coo.data) - 1:
                print_result += "\n"
        return print_result
    
    # Format conversion functions ---------------------------------------------------
    def tocoo(self):
        return coo(self)

    def tocsr(self):
        return csr(self)

    def tocsc(self):
        return self

    def toscipy(self):
        temp_coo = self.tocoo()
        return csc_matrix((temp_coo.data.to_ndarray(), (temp_coo.rows.to_ndarray(), temp_coo.columns.to_ndarray())), shape=self.shape)

    # Arithmetic operation functions ---------------------------------------------------
    def plus_scalar(self, scalar):
        self_copy = csc(self.data, self.old_columns, self.old_rows, self.shape)
        self_copy.data = self.data + scalar
        self_copy.old_data = self.old_data + scalar
        return self_copy

    def sub_scalar(self, scalar):
        self_copy = csc(self.data, self.old_columns, self.old_rows, self.shape)
        self_copy.data = self.data - scalar
        self_copy.old_data = self.old_data - scalar
        return self_copy

    def mul_scalar(self, scalar):
        self_copy = csc(self.data, self.old_columns, self.old_rows, self.shape)
        self_copy.data = self.data * scalar
        self_copy.old_data = self.old_data * scalar
        return self_copy

    def plus_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        temp_convert = self.tocsr()
        temp_convert.data = temp_convert.data + vector[temp_convert.columns]
        self_copy = temp_convert.tocsc()
        return self_copy

    def sub_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        temp_convert = self.tocsr()
        temp_convert.data = temp_convert.data - vector[temp_convert.columns]
        self_copy = temp_convert.tocsc()
        return self_copy

    def mul_vector(self, vector):
        if len(vector) != self.shape[0]:
            return "Size of provided vector does not match number of columns of matrix."
        temp_convert = self.tocsr()
        temp_convert.data = temp_convert.data * vector[temp_convert.columns]
        self_copy = temp_convert.tocsc()
        return self_copy

    def dot(self, input):
        """ Dot product method for CSR class. Must provide additional matrix of any format to multiply in parameters. """
        if str(type(input)) == "<class 'arkouda.pdarrayclass.pdarray'>":
            temp_csr = self.tocsr()
            return temp_csr.vector_matrix_dot(input)
        if str(type(input)) == "<class ''>":
            temp_csr = self.tocsr()
            return temp_csr.matrix_matrix_dot(input)
        else:
            raise ArgumentTypeError

    def matrix_matrix_dot(self, matrix):
        return "Matrix/Matrix dot product not implemented yet"
