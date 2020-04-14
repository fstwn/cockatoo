# LOCAL MODULE IMPORTS ---------------------------------------------------------
from .Utility import escapeFilePath

# ALL DICTIONARY ---------------------------------------------------------------
__all__ = [
    "_AK_RAW_PATH_",
    "_AK_PATH_",
    "_AK_INTERFACE_"
]

# ENVIRONMENT VARIABLES --------------------------------------------------------

# PATH TO COMPILED AUTOKNIT FOLDER (WHERE INTERFACE.EXE IS LOCATED!)
_AK_RAW_PATH_ = r"C:\Users\EFESTWIN\Documents\01_kh_kassel\01_semester\17_ws19_20\01_KNIT_RELAXATION\02_Software\01_repos\autoknit\dist"

# MORE ENVIRONMENT VARIABLES (DON'T CHANGE THIS!) ------------------------------
_AK_PATH_ = escapeFilePath(_AK_RAW_PATH_)
_AK_INTERFACE_ = escapeFilePath(_AK_PATH_ + r"\interface")

# MAIN -------------------------------------------------------------------------
if __name__ == '__main__':
    pass
