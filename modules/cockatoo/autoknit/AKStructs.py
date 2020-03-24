# PYTHON MODULE IMPORTS
import struct

# STRUCTS FOR READING AND WRITING AUTOKNIT *.CONS FILES ------------------------

STRUCT_SCALAR = struct.Struct("=I")
STRUCT_VERTEX = struct.Struct("=3f")
STRUCT_STOREDCONSTRAINT = struct.Struct("=I2f")
