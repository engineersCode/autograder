# Autograder for EngComp

Autograding procedure for _local_ grading using `nbgrader`. Setup to be used with Blackboard.

## Workflow
1. Instructor creates assignment in a Jupyter notebook and uses `nbgrader` formating for autograding.
2. Generate the assignment via `createAssignment()` function within `gradingFunctions.py`.
3. Distribute assignment to students via Blackboard. Set to a _single_ submission. ** code _should_ take the newest submission if there are multiple - has not been tested **. 
4. Collect assignments on Blackboard. 
    - Generate a `.zip` file with student submissions (expecting a `.txt` and `.ipynb` _per_ student). 
    - Download a gradebook file with the specific assignment selected (expects a `.csv`). 
5. Autograde the assignment using the `autogradeAssignment()` function in `gradingFunctions.py`. Assignment results will be displayed and saved into the `scratch` folder. 

## `nbgrader` Directory Structure
This will automatically be properly made when using the `setupCourse()` function, however, there are many `nbgrader` features that will not work because the _must_ be configured manually within the `nbgrader_config.py` file. 

Sample directory structure should look like:
```
opath/                      # overhead directory
├── how-to-grade.ipynb
├── gradingFunctions.py
├── coursename/
│   ├── nbgrader_config.py
│   ├── gradebook.db
│   ├── autograded/
│   │   ├── student_1/
│   │   │   └── ps1/
│   │   │       └── ps1.ipynb
│   │   └── student_2/
│   │       └── ps1/
│   │           └── ps1.ipynb
│   ├── feedback/
│   │   ├── student_1/
│   │   │   └── ps1/
│   │   │       └── ps1.ipynb
│   │   └── student_2/
│   │       └── ps1/
│   │           └── ps1.ipynb
│   ├── source/
│   │   └── ps1/
│   │       └── ps1.ipynb
│   ├── release/
│   │   └── ps1/
│   │       └── ps1.ipynb
│   └── submitted/
│       ├── student_1/
│       │   └── ps1/
│       │       └── ps1.ipynb
│       └── student_2/
│           └── ps1/
│               └── ps1.ipynb
└── temp/
```
**Note** This should not have to be manually made - after the first assignment has been made _and_ graded, every file should appear. 

### Note About `nbgrader`'s GUI:
`formgrader` is still _fully_ functional (besides exchange-setup), however to access it for your course you _must_ be located in the `coursename` directory before launching Jupyter Lab or Jupyter Notebook. 