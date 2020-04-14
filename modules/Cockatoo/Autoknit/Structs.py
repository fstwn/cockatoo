# PYTHON STANDARD LIBRARY IMPORTS ----------------------------------------------
from __future__ import absolute_import
import struct

# ALL DICTIONARY ---------------------------------------------------------------
__all__ = [
    "STRUCT_SCALAR",
    "STRUCT_VERTEX",
    "STRUCT_STOREDCONSTRAINT"
]

# STRUCTS FOR READING AND WRITING AUTOKNIT *.CONS FILES ------------------------
STRUCT_SCALAR = struct.Struct("=I")
STRUCT_VERTEX = struct.Struct("=3f")
STRUCT_STOREDCONSTRAINT = struct.Struct("=I2f")

# MAIN -------------------------------------------------------------------------
if __name__ == '__main__':
    pass
