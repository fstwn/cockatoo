COCKATOO
========

-  Cockatoo is a prototypical open-source software toolkit for
   generating (3d-)knitting patterns from NURBS surface and mesh
   geometry.
-  It is implemented as a `Python <https://www.python.org/>`__ module
   for use within `McNeel Rhinoceros 6 <https://www.rhino3d.com/>`__
   aswell as
   `Grasshopper <https://www.rhino3d.com/6/new/grasshopper>`__.
-  `...Yeah, yeah... Knitting... Rhino... Python... I get it. Just tell
   me how to install and use it! <#installation--usage>`__

--------------

.. _purpose-&-origins:

Purpose & Origins
-----------------

The purpose of this project is to enable Rhino and Grasshopper to
automatically derive (3d-)knitting patterns for computerized knitting
machines from NURBS surfaces and polygon meshes. The absence of such a
freely available open-source toolkit marks the origin point for this
project.

This open-source software prototype constitutes the practical part of my
diploma project *Knit Relaxation - Knit membranes for (Interior-)
Architecture* (original german title: *Knit Relaxation -
Membrangestricke für die (Innen-) Architektur*) in the `product design
department <https://produktdesignkassel.de/>`__ at `Kunsthochschule
Kassel <https://www.kunsthochschulekassel.de/>`__.

Software Structure
------------------

Python Module
~~~~~~~~~~~~~

-  All datastructures, core logic and algorithms are defined in the
   ``cockatoo`` python module.
-  This module is developed to be compatible with
   `IronPython <https://ironpython.net/>`__ (for more info, see the
   `Pecularities <#pecularities>`__ section).
-  The `RhinoCommon
   API <https://developer.rhino3d.com/guides/rhinocommon/what-is-rhinocommon/>`__
   is used to handle all geometric operations.
-  The ``networkx`` module is used to handle all the necessary graph
   operations (for more info, see the `Pecularities <#pecularities>`__
   section).

Rhino Integration
~~~~~~~~~~~~~~~~~

-  The ``cockatoo`` module can be used from within Rhino.Python scripts
   as well as from within Grasshopper through the GHPython scriptable
   component.

Grasshopper Components
~~~~~~~~~~~~~~~~~~~~~~

-  Cockatoo includes a set of Grasshopper components (``UserObjects``),
   which provide a user interface to the underlying python module
   without the need of scripting.

Extendability
~~~~~~~~~~~~~

-  The python module as well as the UserObjects are designed to be open
   for extension. Everything is open-source.

Pecularities
~~~~~~~~~~~~

-  The RhinoPython and GHPython development environments are
   `very <https://developer.rhino3d.com/guides/rhinopython/what-is-rhinopython/>`__,
   `very <https://developer.rhino3d.com/guides/rhinopython/ghpython-component/>`__
   `special <https://developer.rhino3d.com/guides/rhinopython/python-reference/>`__.
   I am not going to write in-depth about this here. Everybody who is
   working with these tools on a regular basis should have come accross
   their oddities. If not - most information about these topics is
   available in the `Rhino Developer
   Docs <https://developer.rhino3d.com/>`__
-  To do all the juicy graph stuff, Cockatoo uses NetworkX. To be more
   specific, an older version - `NetworkX
   1.5 <https://networkx.github.io/documentation/networkx-1.5/>`__ is
   used for... well,
   `reasons <https://www.grasshopper3d.com/forum/topics/ghpython-ironpython-engine-frames>`__.
   To prevent problems with dead links and for reasons of simplicity,
   **this specific networkx module is bundled with Cockatoo**!

Installation
------------

.. _1.-download-release-files:

1. Download release files
~~~~~~~~~~~~~~~~~~~~~~~~~

-  Go to `releases <https://github.com/fstwn/Cockatoo/releases>`__ and
   download the newest release
-  Unzip the downloaded archive. You should get two folders: ``modules``
   and ``Cockatoo``.

.. _2.-install-python-modules:

2. Install python modules
~~~~~~~~~~~~~~~~~~~~~~~~~

-  Open the scripts folder of Rhino 6

   -  On **Windows**:
      ``C:\Users\%USERNAME%\AppData\Roaming\McNeel\Rhinoceros\6.0\scripts``

   -  On **Mac OSX**: ``Mac_Folder\Here``

-  Move all the Content from inside the ``modules`` directory to this
   scripts folder.

.. _3.-install-cockatoo-userobjects:

3. Install Cockatoo UserObjects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Navigate to the Grasshopper UserObjects folder. This can be done in
   two ways:

   -  *Either* open the following folder:

      -  On **Windows**:
         ``C:\Users\%USERNAME%\AppData\Roaming\Grasshopper\UserObjects``

      -  On **Mac OSX**: ``Mac_Folder\Here``

   -  *Or* open Rhino & Grasshopper and in the Grasshopper Window click
      on

      ``File`` > ``Special Folders`` > ``User Object Folder``

-  Move the whole ``Cockatoo`` directory to the UserObjects folder.

.. _4.-unblock-the-new-userobjects!:

4. Unblock the new UserObjects!
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Go into the ``Cockatoo`` folder inside Grasshoppers UserObjects
   folder
-  Right click onto the first UserObject and go to **Properties**
-  If the text *This file came from another computer [...]* is displayed
   click on **Unblock**!
-  **Unfortunately you have to do this for EVERY UserObject in the
   folder!**

.. _5.-restart-rhino-&-grasshopper:

5. Restart Rhino & Grasshopper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  If Rhino was running during the installation process, you'll have to
   restart it for the changes to take effect!

.. _examples-&-usage:

Examples & Usage
----------------

.. _testing-&-contributing:

Testing & Contributing
----------------------

.. _you-are-invited-to-participate-(yes---you!):

You are invited to participate (yes - you!)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Contributing is easy as Pi (well...easier, actually). Whether you are
   a designer, student, teacher or scientist working with CNC-knitting -
   just find out what Cockatoo can do for you. In order to make Cockatoo
   better, we need real-world testing!
-  If Cockatoo doesn't do the things you expected it to do or simply
   does not work: Tell me about it by `submitting an
   issue <https://github.com/fstwn/Cockatoo/issues/>`__!
-  To find out more about how you can help testing this software and
   making it better, have a look at the contribution guidelines.

.. _sources-&-references:

Sources & References
--------------------

This section states the most important sources used in writing this
software. The full list of sources is - of course - available in the
written version of the diploma project.

-  [1] Popescu, Mariana et al. `Automated Generation of Knit Patterns
   for Non-developable
   Surfaces <https://block.arch.ethz.ch/brg/files/POPESCU_DMSP-2017_automated-generation-knit-patterns_1505737906.pdf>`__
-  [2] Popescu, Mariana `KnitCrete - Stay-in-place knitted formworks for
   complex concrete
   structures <https://block.arch.ethz.ch/brg/files/POPESCU_2019_ETHZ_PhD_KnitCrete-Stay-in-place-knitted-fabric-formwork-for-complex-concrete-structures_small_1586266206.pdf>`__
-  [3] Van Mele, Tom et al. `COMPAS: A framework for computational
   research in architecture and
   structures <https://compas-dev.github.io/>`__
-  [4] Narayanan, Vidya; Albaugh, Lea; Hodgins, Jessica; Coros, Stelian;
   McCann, James `Automatic Machine Knitting of 3D
   Meshes <https://textiles-lab.github.io/publications/2018-autoknit/>`__
-  [5] Narayanan, Vidya; Wu, Kui et al. `Visual Knitting Machine
   Programming <https://textiles-lab.github.io/publications/2019-visualknit/>`__
-  [6] McCann, James; Albaugh, Lea; Narayanan, Vidya; Grow, April;
   Matusik, Wojciech; Mankoff, Jen; Hodgins, Jessica `A Compiler for 3D
   Machine
   Knitting <https://la.disneyresearch.com/publication/machine-knitting-compiler/>`__
-  [7] Hagberg, Aric; Schult, Dan; Swart, Pieter `NetworkX
   1.5 <https://networkx.github.io/documentation/networkx-1.5/_downloads/networkx_reference.pdf>`__
