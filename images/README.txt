Images taken from Gnome HighContrast theme.

To regenerate the resources file, make sure to have the Qt resources tool install

    rcc -g python -o resources.py images.qrc

Then edit the import line of the generated file to use PyQt instead of PySide and copy into <PROJECT DIRECTORY>/admbrowser/.
