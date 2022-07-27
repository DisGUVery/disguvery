# DisGUVery

version 1.0 

Image analysis software to detect and analyse Giant Unilamellar Vesicles in microscopy images. 

## Getting started

Download the files from the repository and extract the files to a folder of your liking. There should be a folder called `disguvery` and in this folder you should now see a selection of python scripts, including `disguvery.py`.

The software does not need to be installed, but can be started right away. To launch the program, start the command window and navigate to the folder where the code is saved. Then, the software can be started by calling the `disguvery.py` file using the `python` command. For example, in Windows if we are working on the `D:`drive, where we have the folder of  `disguvery`, we can type:

```
D:\> cd disguvery
D:\disGUVery> python disguvery.py
```

*Note: if you start your command prompt or terminal in another drive, e.g. `C:` , just type `D:` in the terminal to change to drive D:*  

When running the software for the first time, you might encounter that some required packages are missing or not up to date. Use `pip` to install missing packages and to update outdated packages. If you need to change your packages versions, and/or install anything new, we recommend to create a virtual environment with the requirements for DisGUVery as to not interfere with your normal installation.

## Usage

After starting the software, you are ready to do GUV analysis! You can do your analysis in many different ways in DisGUVery. For complete instructions on usage and installation, check the quick user guide. Although you can operate the software only with the graphical interface, we recommend for you to keep an eye on the terminal/command propmt, as useful messages (sucessful / error operations) are shown there.

## Requirements

DisGUVery has been developed and tested using the following library versions: 

* python -> v3.7 and v3.10
* tkinter -> v8.6
* numpy -> v1.18 and v1.22
* matplotlib -> v3.4 and v3.5
* opencv -> v4.5
* pillow -> v8.4 and v9.0
* scikit-image -> v0.16 and v0.19
* scipy -> v1.6 and v1.7


## License

GPL
