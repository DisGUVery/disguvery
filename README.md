# DisGUVery

Image analysis software to detect and analyse Giant Unilamellar Vesicles in microscopy images. Read the original [DisGUVery preprint](https://www.biorxiv.org/content/10.1101/2022.01.25.477663v1) on bioRxiv. 

## Getting started

Download the files from the repository and extract the files to a folder of your liking (typically this folder will be called `disguvery-main`). There should be a folder called `disguvery` and in this folder you should now see a selection of python scripts, including `disguvery.py`.

The software does not need to be installed, but can be started right away. To launch the program, start the command window and navigate to the folder where the code is saved. Then, the software can be started by calling the `disguvery.py` file using the `python` command. For example, in Windows if we are working on the `D:`drive, where we have the folder of  `disguvery-main`, we can type:

```
D:\> cd disguvery-main\disguvery
D:\disguvery-main\disguvery> python disguvery.py
```

*Note: if you start your command prompt or terminal in another drive, e.g. `C:` , just type `D:` in the terminal to change to drive D:*  

When running the software for the first time, you might encounter that some required packages are missing or not up to date. Use `pip` to install missing packages and to update outdated packages. If you need to change your packages versions, and/or install anything new, we recommend to create a virtual environment with the requirements for DisGUVery as to not interfere with your normal installation. You can find a step-by-step guide below.

### Installing required packages on a virtual environment

To create a virtual environment, navigate to the `disguvery-main` folder and type:

```
D:\disguvery-main> python -m venv disguvery-env
```

where `disguvery-env` is the name of the virtual environment we're going to dedicate for working with DisGUVery. Here, you'll have a 'clean' installation of python where you can install *only* the packages that are required for DisGUVery to run. Before you can work in this virtual environment, it needs to be activated:

```
D:\disguvery-main> .\disguvery-env\Scripts\activate
```

Now we can install the required packages, listed in the file `requirements.txt`:

```
D:\disguvery-main> python -m pip install -r requirements.txt
```

This will install all the packages in the specific versions that were used during development and testing. You're now ready to use DisGUVery!

**Activating and deactivating the virtual environment** 

Once you're done working with DisGUVery, you can deactivate the environment by typing:

```
D:\disguvery-main> deactivate
```

Next time you'll want to use DisGUVery, it is only necessary to activate the virtual environment where the installation was done. Don't forget to navigate to the right directory to launch DisGUVery:

```
D:\disguvery-main> .\disguvery-env\Scripts\activate
D:\disguvery-main> cd disguvery
D:\disguvery-main\disguvery> python disguvery.py
```

## Usage

After starting the software, you are ready to do GUV analysis! You can do your analysis in many different ways in DisGUVery. For complete instructions on usage and installation, check the quick user guide. Although you can operate the software only with the graphical interface, we recommend for you to keep an eye on the terminal/command propmt, as useful messages (successful / error operations) are shown there.


## Feedback

We welcome any questions about the use of DisGUVery, as well as bug reports and suggestions for improvement, both for the software and for the user guide. Please post your questions, remarks or suggestions in the appropriate issue boards or discussion forum. 

## License

GPL
