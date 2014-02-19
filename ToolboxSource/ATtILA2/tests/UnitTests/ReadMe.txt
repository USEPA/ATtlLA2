This suite of tests is designed to be used by developers to compare tool results with a reference dataset after changes 
to the code base.  

The suite contains a master module, runAllTests.py, that is configured to run through each of the individual metric 
calculations, a module, parameters.py, that contains all of the configuration parameters for each of the tests, modules 
corresponding to each metric calculation, and a final test module, outputValidation.py, that compares the test output 
against the reference datasets.  

Before making any changes to the ATtILA2 source code, we recommend first setting up a folder with test datasets and 
reference outputs.  It may be most intuitive to use the Toolbox in ArcCatalog to create this baseline.  Run each tool 
that might be affected, collecting the inputs and outputs in a single folder.  Then copy your geoprocessing parameters 
into the parameter.py file.  The first parameter, baseDir, should be your base directory containing all of the test 
inputs and outputs – this is equivalent to setting the  workspace in ArcGIS, so that all of the rest of the dataset 
parameters don’t have to use a full path.   The rest of the variable names should match up reasonably intuitively with 
the Toolbox parameters.  Most of the tools share a consistent set of parameters – these are gathered together at the 
top.  Then, each tool does have a few unique parameters, most importantly, a reference output dataset that is used as a 
control in any future tests.  

Once the parameter file is configured, any individual test can be run at the python command line, or as “Python Run” 
(not “Python Unit Test”) in Eclipse with PyDev.   The script should return:

Running ***TestName*** calculation
Testing ***TestName***  results
Validation was successful

If validation is not successful, it will return a message indicating the first point of failure (missing or extra 
fields, or the first mismatched value).  
