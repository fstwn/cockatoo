# PYTHON MODULE IMPORTS
from __future__ import division
import heapq
import string

# ENVIRONMENT VARIABLES --------------------------------------------------------

# PATH TO COMPILED AUTOKNIT FOLDER (WHERE INTERFACE.EXE IS LOCATED!)
_AK_RAW_PATH_ = r"C:\Users\EFESTWIN\Documents\01_kh_kassel\01_semester\17_ws19_20\01_KNIT_RELAXATION\02_Software\01_repos\autoknit\dist"

# UTILITY CLASSES --------------------------------------------------------------

class AttributeList(list):
    """
    A subclass of list that can accept additional attributes.
    Should be able to be used just like a regular list.

    Based on a recipe from code.activestate.com

    The problem:
    a = [1, 2, 4, 8]
    a.x = "Hey!" # AttributeError: 'list' object has no attribute 'x'

    The solution:
    a = L(1, 2, 4, 8)
    a.x = "Hey!"
    print a       # [1, 2, 4, 8]
    print a.x     # "Hey!"
    print len(a)  # 4

    You can also do these:
    a = L( 1, 2, 4, 8 , x="Hey!" )                 # [1, 2, 4, 8]
    a = L( 1, 2, 4, 8 )( x="Hey!" )                # [1, 2, 4, 8]
    a = L( [1, 2, 4, 8] , x="Hey!" )               # [1, 2, 4, 8]
    a = L( {1, 2, 4, 8} , x="Hey!" )               # [1, 2, 4, 8]
    a = L( [2 ** b for b in range(4)] , x="Hey!" ) # [1, 2, 4, 8]
    a = L( (2 ** b for b in range(4)) , x="Hey!" ) # [1, 2, 4, 8]
    a = L( 2 ** b for b in range(4) )( x="Hey!" )  # [1, 2, 4, 8]
    a = L( 2 )                                     # [2]
    """
    def __new__(self, *args, **kwargs):
        return super(AttributeList, self).__new__(self, args, kwargs)

    def __init__(self, *args, **kwargs):
        if len(args) == 1 and hasattr(args[0], '__iter__'):
            list.__init__(self, args[0])
        else:
            list.__init__(self, args)
        self.__dict__.update(kwargs)

    def __call__(self, **kwargs):
        self.__dict__.update(kwargs)
        return self

# UTILITY FUNCTIONS ------------------------------------------------------------

# KD TREE ----------------------------------------------------------------------

def make_kd_tree(points, dim, i=0):
    """
    Build a KD-Tree for fast lookup.
    Based on a recipe from code.activestate.com
    """
    if len(points) > 1:
        points.sort(key=lambda x: x[i])
        i = (i + 1) % dim
        half = len(points) >> 1
        return (
            make_kd_tree(points[: half], dim, i),
            make_kd_tree(points[half + 1:], dim, i),
            points[half])
    elif len(points) == 1:
        return (None, None, points[0])

def get_knn(kd_node, point, k, dim, dist_func, return_distances=False, i=0, heap=None):
    """
    K nearest neighbors. The heap is a bounded priority queue.
    Based on a recipe from code.activestate.com
    """
    is_root = not heap
    if is_root:
        heap = []
    if kd_node:
        dist = dist_func(point, kd_node[2])
        dx = kd_node[2][i] - point[i]
        if len(heap) < k:
            heapq.heappush(heap, (-dist, kd_node[2]))
        elif dist < -heap[0][0]:
            heapq.heappushpop(heap, (-dist, kd_node[2]))
        i = (i + 1) % dim
        # Goes into the left branch, and then the right branch if needed
        get_knn(kd_node[dx < 0], point, k, dim,
                dist_func, return_distances, i, heap)
        # -heap[0][0] is the largest distance in the heap
        if dx * dx < -heap[0][0]:
            get_knn(kd_node[dx >= 0], point, k, dim,
                    dist_func, return_distances, i, heap)
    if is_root:
        neighbors = sorted((-h[0], h[1]) for h in heap)
        return neighbors if return_distances else [n[1] for n in neighbors]

def get_nearest(kd_node, point, dim, dist_func, return_distances=False, i=0, best=None):
    """
    Find the closest neighbour of a point in a list of points using a KD-Tree.
    Based on a recipe from code.activestate.com
    """
    if kd_node:
        dist = dist_func(point, kd_node[2])
        dx = kd_node[2][i] - point[i]
        if not best:
            best = [dist, kd_node[2]]
        elif dist < best[0]:
            best[0], best[1] = dist, kd_node[2]
        i = (i + 1) % dim
        # Goes into the left branch, and then the right branch if needed
        get_nearest(
            kd_node[dx < 0], point, dim, dist_func, return_distances, i, best)
        if dx * dx < best[0]:
            get_nearest(
                kd_node[dx >= 0], point, dim, dist_func, return_distances, i, best)
    return best if return_distances else best[1]

# FILE PATHS -------------------------------------------------------------------

def escapeFilePath(fp):
    """Escapes a Grasshopper File Path to make it compatible with Python"""
    return string.join(fp.split("\\"), "\\\\")

def removeTrailingNewlines(s):
    """Removes trailing newlines from a string (most of the time a filepath)."""
    if not s:
        return None
    elif s.endswith("\n"):
        s = removeTrailingNewlines(s[:-1])
    elif s.endswith("\r"):
        s = removeTrailingNewlines(s[:-1])
    return s

# MORE ENVIRONMENT VARIABLES (DON'T CHANGE THIS!) ------------------------------

_AK_PATH_ = escapeFilePath(_AK_RAW_PATH_)
_AK_INTERFACE_ = escapeFilePath(_AK_PATH_ + r"\interface")
