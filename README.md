# facify
![Facify_img1](https://raw.githubusercontent.com/wayneyip/facify/master/tools_facify.gif)

Maya Python tool to automate curve-based rigging for flexible mouth/eye animation.

[Video Link](https://vimeo.com/365357089)

## Features
- Joints aim constrained to locators bound to a high-density curve
- Wire deformer to drive high-density linear curve with a low-density cubic curve
- Controls angled to follow joint direction/face curvature
- Blendshape-based Smart Close system for adjustable blink/close attributes

## Instructions

- Place `wy_facify.py` and `wy_facifyUI.py` in your Maya Scripts folder, found in:
    - Windows: `C:\Users\<Your-Username>\Documents\maya\<20xx>\scripts`
    - OSX: `/Users/<Your-Username>/Library/Preferences/Autodesk/maya/<20xx>/scripts`
    - Linux: `/home/<Your-Username>/maya/<20xx>/scripts`
- Restart/open Maya, then open the Script Editor by:
	- Going to `Windows > General Editors > Script Editor`

		**or**
	- Left-clicking the `{;}` icon at the bottom-right of your Maya window
- Copy/paste and run the following code in your Script Editor:

	```
	import wy_facifyUI
	reload (wy_facifyUI)
	facifyUI = wy_facifyUI.FacifyUI()
	facifyUI.createUI()
	```
	to launch the Facify tool UI.

- (Extra) Save the UI launch code to a shelf button:
	- Go to `File > Save Script to Shelf` in the Script Editor
	- Type in a name for the button (e.g. "Facify"), and hit OK
	- Facify should now be saved as a button in your shelf.

## Details

**Technologies**: Maya, Python

**Developer**: Wayne Yip

**Contact**: yipw@usc.edu