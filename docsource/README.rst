COCKATOO
========

-  Cockatoo is a prototypical open-source software toolkit for
   generating (3d-)knitting patterns from NURBS surface and mesh
   geometry.
-  It is implemented as a `Python <https://www.python.org/>`__ module
   for use within `McNeel Rhinoceros 6 <https://www.rhino3d.com/>`__
   aswell as
   `Grasshopper <https://www.rhino3d.com/6/new/grasshopper>`__.
-  `Yeah, yeah... Knitting... Rhino... Python... I get it. Just tell me
   how to install and use it! <#installation>`__ \ `1 <#misc>`__\ 

--------------

.. _purpose-&-origins:

Purpose & Origins
-----------------

The purpose of this project is to enable Rhino and Grasshopper to
automatically derive (3d-)knitting patterns for computerized knitting
machines from NURBS surfaces and unstructured triangle meshes. The
absence of such a freely available open-source toolkit marks the origin
point for this project. Programming Cockatoo was only possible thanks to
some brilliant research done by lots of other people. Please check the
`Sources & References <#sources--references>`__ section if you're
curious.

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

The ``cockatoo`` module can be used from within Rhino.Python scripts as
well as from within Grasshopper through the GHPython scriptable
component.

Grasshopper Components
~~~~~~~~~~~~~~~~~~~~~~

Cockatoo includes a set of Grasshopper components (``UserObjects``),
which provide a user interface to the underlying python module without
the need of scripting.

Extendability
~~~~~~~~~~~~~

The python module as well as the UserObjects are designed to be open for
extension. Everything is open-source.

Pecularities
~~~~~~~~~~~~

The RhinoPython and GHPython development environments are
`very <https://developer.rhino3d.com/guides/rhinopython/what-is-rhinopython/>`__,
`very <https://developer.rhino3d.com/guides/rhinopython/ghpython-component/>`__
`special <https://developer.rhino3d.com/guides/rhinopython/python-reference/>`__.
I am not going to write in-depth about this here. Everybody who is
working with these tools on a regular basis should have come accross
their oddities. If not - most information about these topics is
available in the `Rhino Developer
Docs <https://developer.rhino3d.com/>`__.

To do all the juicy graph stuff, Cockatoo uses NetworkX. To be more
specific, an older version - `NetworkX
1.5 <https://networkx.github.io/documentation/networkx-1.5/>`__ is used
for... well,
`reasons <https://www.grasshopper3d.com/forum/topics/ghpython-ironpython-engine-frames>`__.
**This specific networkx module is bundled with Cockatoo** for
simplicity!

Installation
------------

.. _1.-download-release-files:

1. Download release files
~~~~~~~~~~~~~~~~~~~~~~~~~

-  Go to `releases <https://github.com/fstwn/cockatoo/releases>`__ and
   download the newest release
-  Unzip the downloaded archive. You should get two folders: ``modules``
   and ``Cockatoo``.

.. _2.-install-python-modules:

2. Install python modules
~~~~~~~~~~~~~~~~~~~~~~~~~

-  Open the scripts folder of Rhino 6

   -  On **Windows**:
      ``C:\Users\%USERNAME%\AppData\Roaming\McNeel\Rhinoceros\6.0\scripts``

   -  On **Mac OSX**:
      ``~/Library/Application Support/McNeel/Rhinoceros/6.0/scripts``

-  Move all the Content from inside the ``modules`` directory to this
   scripts folder.

.. _3.-install-cockatoo-userobjects:

3. Install Cockatoo UserObjects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Navigate to the Grasshopper UserObjects folder

   -  On **Windows**:
      ``C:\Users\%USERNAME%\AppData\Roaming\Grasshopper\UserObjects``

   -  On **Mac OSX**:
      ``~/Library/Application Support/McNeel/Rhinoceros/6.0/scripts``

   -  *Alternative:* Open Rhino & Grasshopper and in the Grasshopper
      Window click on ``File`` > ``Special Folders`` >
      ``User Object Folder``

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

TODO: Provide some images here

.. _testing-&-contributing:

Testing & Contributing
----------------------

.. _you-are-invited-to-participate!:

You are invited to participate!
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contributing is easy as Pi (well...easier, actually). First off,
Cockatoo needs software testing to find bugs and make it more robust. So
just by trying out Cockatoo out of curiosity, you can actually help!

If you find a bug (which is very likely because they always sneak in
somewhere) please tell me about it by `submitting an
issue <https://github.com/fstwn/cockatoo/issues/>`__ so I can improve
Cockatoo further.

Testing
~~~~~~~

A sad truth is that I currently don't have access to a computerized
knitting machine. As a consequence, it was not possible to actually test
or verify a knitting pattern generated by Cockatoo in the real world,
yet. If you have access to a machine and you would be willing to
collaborate with me in testing, I would be more than happy!

Also, if you know a thing or two about computational knitting and find a
fundamental (or minor) mistake in the workings of Cockatoo, please `let
me know <https://github.com/fstwn/cockatoo/issues/>`__. I'm always eager
to learn from others and fix mistakes.

Code
~~~~

If you're willing to contribute to Cockatoo by writing new code or
improving existing code, that's great! Please have a look at the
contribution guidelines.

.. _sources-&-references:

Sources & References
--------------------

This section states the most important sources used in writing this
software. The full and proper list of sources is - of course - available
in the written version of the diploma thesis.

-  Cherif, Chokri: `Textile Werkstoffe für den Leichtbau. Techniken -
   Verfahren - Materialien -
   Eigenschaften. <https://link.springer.com/book/10.1007/978-3-642-17992-1>`__
-  CITAstudio: `Textile. Light. Architecture. SOFT
   SPACES <https://issuu.com/cita_copenhagen/docs/catalogue>`__
-  Hagberg, Aric; Schult, Dan; Swart, Pieter: `NetworkX
   1.5 <https://networkx.github.io/documentation/networkx-1.5/_downloads/networkx_reference.pdf>`__
-  McCann, James; Albaugh, Lea; Narayanan, Vidya; Grow, April; Matusik,
   Wojciech; Mankoff, Jen; Hodgins, Jessica: `A Compiler for 3D Machine
   Knitting <https://la.disneyresearch.com/publication/machine-knitting-compiler/>`__
-  Narayanan, Vidya; Albaugh, Lea; Hodgins, Jessica; Coros, Stelian;
   McCann, James: `Automatic Machine Knitting of 3D
   Meshes <https://textiles-lab.github.io/publications/2018-autoknit/>`__
-  Narayanan, Vidya; Wu, Kui; Yuksel, Cem; McCann, James: `Visual
   Knitting Machine
   Programming <https://textiles-lab.github.io/publications/2019-visualknit/>`__
-  Popescu, Mariana; Rippmann, Matthias; van Mele, Tom; Block, Philippe:
   `Automated Generation of Knit Patterns for Non-developable
   Surfaces <https://block.arch.ethz.ch/brg/files/POPESCU_DMSP-2017_automated-generation-knit-patterns_1505737906.pdf>`__
-  Popescu, Mariana: `KnitCrete - Stay-in-place knitted formworks for
   complex concrete
   structures <https://block.arch.ethz.ch/brg/files/POPESCU_2019_ETHZ_PhD_KnitCrete-Stay-in-place-knitted-fabric-formwork-for-complex-concrete-structures_small_1586266206.pdf>`__
-  Thomsen, Mette Ramsgaard; Tamke, Martin; Deleuran, Anders Holden;
   Tinning, Ida Katrine Friis; Evers, Henrik Leander; Gengnagel,
   Christoph; Schmeck, Michel: *»Hybrid Tower, Designing Soft
   Structures«.* In: `Modelling behaviour. Design Modelling Symposium
   2015, hrsg. von Mette Ramsgaard Thomsen, Martin Tamke, Christoph
   Gengnagel, Billie Faircloth und Fabian Scheurer. Cham/Heidelberg/New
   York/Dordrecht/London
   2015 <https://doi.org/10.1007/978-3-319-24208-8_8>`__
-  Ramsgaard Thomsen, Mette; Tamke, Martin; Ayres, Phil; Nicholas, Paul:
   `CITA Complex Modelling, Toronto
   2019 <https://issuu.com/cita_copenhagen/docs/20190823_cita_complex_modellingshor_27ae721ee28ba3>`__
-  Van Mele, Tom; others, many: `COMPAS: A framework for computational
   research in architecture and
   structures <https://compas-dev.github.io/>`__

Licensing
---------

-  NetworkX is licensed under the 3-clause BSD license which can be
   found in ``licenses/networkx``.
-  Some code snippets from the COMPAS framework are used within this
   software. This code is licensed under the MIT License which can be
   found in ``licenses/COMPAS``.

Misc
----

-  [1] This is a hommage to `David
   Ruttens <https://ieatbugsforbreakfast.wordpress.com/>`__ delightful
   sense of humor which has changed many of my darker days for the
   better.
