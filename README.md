# COCKATOO

- This is a set of open-source UserObjects for [Grasshopper](https://www.rhino3d.com/6/new/grasshopper).
- Grasshopper is a Plugin for the popular CAD-System [McNeel Rhinoceros 6](https://www.rhino3d.com/).
- All code here is written in IronPython 2.7.8.0 as this is the interpreter Rhino & Grasshopper use internally.

## Purpose & Origins

The purpose of this project is to enable Rhino and Grasshopper to automatically derive knitting patterns for computerized knitting machines from NURBS Surfaces and 3D Meshes.

## Installation & Usage

### 1. Download release files

- Go to [releases](https://github.com/fstwn/pyembroideryGH/releases) and download the newest release
- Unzip the downloaded archive. You should get two folders `pyembroidery`, `pyembroideryGH` and a text-file.

### 2. Install ironpyembroidery

- Open the scripts folder of Rhino 6 by opening explorer and navigating to
  
  `C:\Users\%USERNAME%\AppData\Roaming\McNeel\Rhinoceros\6.0\scripts`
- Move the whole `pyembroidery` directory to the scripts folder.

### 3. Install pyembroideryGH UserObjects

- Navigate to the Grasshopper UserObjects folder. This can be done in two ways:
  - *Either* open explorer and go to
    
    `C:\Users\%USERNAME%\AppData\Roaming\Grasshopper\UserObjects`
  - *Or* open Rhino & Grasshopper and in the Grasshopper Window click on

    `File >> Special Folders >> User Object Folder`
- Move the whole `pyembroideryGH` directory to the UserObjects folder.

### 4. Unblock the new UserObjects!

- Go into your `pyembroideryGH` folder inside Grasshoppers UserObjects folder
- Right click onto the first UserObject and go to **Properties**
- If the text *This file came from another computer [...]* is displayed click on **Unblock**!
- **Unfortunately you have to do this for _EVERY_ UserObject in the folder!**

