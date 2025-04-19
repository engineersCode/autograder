import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os, importlib, shutil, zipfile, json, time, subprocess

def setupCourse(course_name, temppath=os.path.join(os.getcwd(),'temp'), folder_path=os.getcwd()):
    """
    Function that will setup an nbgrader course with all necessary directories for students. 
    This will:
        1) Create a "scratch" directory where all orginal student files will be stored. 
        2) Create a submitted folder with student subfolders based on information from Blackboard.

    Uses and requirements:
        - This function must have a folder to create everything within with a "temp" folder within 
          the same directory as the course.
        - Meant to be used with a "gradebook" from Blackboard. If that is not an option, columns 
          must be
                    "First Name"   "Last Name"   "Username"
          all other columns will be ignored. No other file is allowed to be in the temp folder 
          during initalization. 

          
    **Setup is meant to be used with Blackboard submission format with a blank temp folder**
    ----------------------------------------------------------------------------------------------

    -------------------------
    Inputs
    -------------------------
    course_name (str) : name of the course you want to setup, e.g., mae1117
    temppath (str)    : full path to a temporary folder where you want all item to be placed for grading. 
                        this script requires a Blackboard dummy .csv with columns "First Name", "Last Name", and "Username".
                        Defult is set to the current working directory.
    folder_path (str) : full path to the location where you want the course setup. Defult is set to the current working directory. 
    """

    # Checking that nbgrader is properly installed
    assert importlib.util.find_spec('nbgrader') is not None, 'You Need to Install nbgrader!' 

    # Creating a nbgrader course
    os.chdir(folder_path)
    subprocess.run(["nbgrader", "quickstart", course_name])
    time.sleep(5)
    cpath = os.path.join(folder_path,course_name)
    subpath = cpath + '/submitted'
    scpath = cpath + '/scratch'
    temppath = folder_path + '/temp'

    if next((sub for sub in os.listdir(cpath) if 'submitted' in sub), None) == None:
        os.mkdir(subpath)
    if next((scr for scr in os.listdir(cpath) if 'scratch' in scr), None) == None:
        os.mkdir(scpath)
    if next((t for t in os.listdir(folder_path) if 'temp' in t), None) == None:
        os.mkdir(temppath)

    print('------------------------------------------------------------------')
    input('Move Gradebook File into temp folder. Hit enter once this is done.')
    
    # Setting up student directories
    try:
        gr_path = os.path.join(temppath, next((cs for cs in os.listdir(temppath) if 'csv' in cs), None))
        gr = pd.read_csv(gr_path)
        last, first, users = gr['Last Name'], gr['First Name'], gr['Username']
    except TypeError:
        print('Temporary Folder is Empty')

    for user in users:
        try:
            user_path = subpath + f'/{user}'
            os.mkdir(user_path)
        except FileExistsError:
            continue
    sn_df = pd.DataFrame({'id':gr['Username'],
                      'first_name':gr['First Name'],
                      'last_name':gr['Last Name'] })

    subprocess.run(["nbgrader", "db", "student", "remove", "bitdiddle"])
    subprocess.run(["nbgrader", "db", "student", "remove", "hacker"])
    sn_df.to_csv('tmp.csv')
    subprocess.run(["nbgrader", "db", "student", "import", "tmp.csv"])
    os.remove('tmp.csv')

    print(f'Course: {course_name} created succesfully with {len(users)} students.')

def calculate_grades(aname, user, coursename, opath):
    """
    Calculate the points earned per graded cell from the notebook dictionary.
    
    For each cell with nbgrader metadata, the function checks whether the cell passed its tests.
    If the cell passed (determined by the lack of errors in its outputs), the full points are awarded.
    Otherwise, no points (0) are given.
    
    The result is returned in a dictionary where:
      - Each key is the cell's 'grade_id' (e.g., '1a', '1b', etc.) and its value is the points earned.
      - There is an extra key 'total' that contains the sum of all earned points.
    
    Parameters:
        notebook_data (dict): The notebook's data structure.
    
    Returns:
        dict: A dictionary of scores by cell id, along with 'total' earned points.
    """
    autograded_assignment_path = os.path.join(opath,coursename,'autograded',user,aname,f'{aname}.ipynb')
    with open(autograded_assignment_path, 'r', encoding='utf-8') as f:
        notebook_content = f.read()
    notebook_data = json.loads(notebook_content)
    
    grades = {}
    total_earned = 0
    
    # Iterate over each cell in the notebook.
    for cell in notebook_data.get("cells", []):
        nbgrader_info = cell.get("metadata", {}).get("nbgrader", {})
        if nbgrader_info.get("grade", False):
            grade_id = nbgrader_info.get("grade_id", None)
            points = nbgrader_info.get("points", 0)
            # Default earned points: 0 if the cell has errors, otherwise full points.
            earned_points = 0
            
            # Determine if the cell passed its hidden tests:
            # If there are no outputs, assume it passed.
            # Otherwise, check that none of the outputs indicate an error.
            outputs = cell.get("outputs", [])
            if not outputs:
                earned_points = points
            else:
                has_error = any(output.get("output_type") == "error" for output in outputs)
                if not has_error:
                    earned_points = points
            
            # If a valid grade_id exists, record the earned points.
            if grade_id is not None:
                grades[grade_id] = earned_points
                total_earned += earned_points

    grades["total"] = total_earned
    return grades

def autogradeAssignment(aname, coursename, opath=os.getcwd()):
    """
    Function that will autograde an assignment using nbgrader. This function assumes the file structure created by setupCourse().

    -------------------------
    Inputs
    -------------------------
    aname (str) : assignment name (not including extension). 
                  Note: assignment must be generated before attempting to autograde and must have the same name in both the directory 
                  where it is located and the actual name of the assignment, e.g.
                          source/ 
                              engcomp0hw0/
                                  engcomp0hw0.ipynb
    coursename (str) : name of the course folder (not the path) with structure setup by previous setupCourse() fucntion. 
                       Must be of the format:
                            coursename/
                                source/
                                submitted/
                                scratch/
                                release/
                                feedback/
    opath (str) : overhead path the houses the course. Subdirectories of opath should look like
                        opath/
                            course/
                            temp/
                            gradebook.db
                            gradingFunctions.py
                  leaving the functions in this file in the opath directory will allow for less path management. 
    
    -------------------------
    Ouputs
    -------------------------
    temp/ : uploadable gradebook to Blackboard
    scratch/aname : png of grade distribution, orginal gradebook, nbgrader gradebook, final gradebook that is also in the /temp folder, 
                    and directory /orginal_files_from_bb which houses the unzipped orginal .txt and .ipynb files. 

    ** NOTE: This is meant to be used with Blackboard Ultra structed files. This Function is to ONLY be used when autogradeing from the zip file. 
             See autogradeStudent() to autograde an individual student. **
    """
    print('------------------------------------------------------------------------------------------')
    input('Move Gradebook File and Blackboard Zip File into temp folder. Hit enter once this is done.')
    print('------------------------------------------------------------------------------------------')
    assert len(os.listdir(os.path.join(opath,'temp'))) == 2, '2 Files Expected'

    temppath = os.path.join(opath,'temp')
    zname = next((z for z in os.listdir(temppath) if 'zip' in z), None)
    gname = next((cs for cs in os.listdir(temppath) if 'csv' in cs), None)

    coursepath = os.path.join(opath,coursename)
    zpath = os.path.join(temppath,zname)
    gpath = os.path.join(temppath,gname)
    scrpath = os.path.join(coursepath,'scratch')
    subpath = os.path.join(coursepath,'submitted')

    assignment_scratch = os.path.join(scrpath,aname)
    orgfiles = os.path.join(assignment_scratch,'orginal_files_from_bb')

    try:
        os.mkdir(assignment_scratch)
    except FileExistsError:
        pass
    try:
        os.mkdir(orgfiles)
    except FileExistsError:
        pass

    def unzip(zip_path, extract_to):
        """
        Extracts all files from a zip archive.

        Args:
            zip_path (str): The path to the zip file.
            extract_to (str): The directory to extract the contents to.
        """
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)

    unzip(zpath, orgfiles)

    dirfiles = os.listdir(orgfiles)

    notebooks = []
    txts = []
    usernames = []

    for f in range(len(dirfiles)-1):
        f_txt, f_ipynb = dirfiles[f], dirfiles[f+1]
        f_txt_ext = os.path.splitext(f_txt)[1]
        f_ipynb_ext = os.path.splitext(f_ipynb)[1]

        userpath = os.path.join(orgfiles, f_txt)
        with open(userpath, 'r') as g:
            firstline = g.readline().strip()

        # Try extracting username only if parentheses exist
        if '(' in firstline and ')' in firstline:
            username = firstline[firstline.find('(') + 1:firstline.find(')')]
        else:
            username = 'UNKNOWN'

        try:
            assert f_txt_ext == '.txt'
            assert f_ipynb_ext == '.ipynb'
        except AssertionError:
            if username != 'UNKNOWN':
                print(f'Student {username} submitted a blank submission')
            continue
    
        notebooks.append(f_ipynb)
        txts.append(f_txt)
        usernames.append(username)
    print('------------------------------------------------------------------------------------------')
    
    for user, notebook in zip(usernames,notebooks):
        usersubpath = os.path.join(subpath,user)
        if os.path.exists(usersubpath):
            src_path = os.path.join(orgfiles,notebook)
        
            student_assign_sub_path = os.path.join(usersubpath,aname)
            try:
                os.mkdir(student_assign_sub_path)
            except FileExistsError:
                pass

            assignment_sub_path = os.path.join(student_assign_sub_path, f'{aname}.ipynb')
        
            shutil.copy2(src_path, assignment_sub_path)
        else:
            print(f'No submitted folder for student {user}.')

    os.chdir(coursepath)
    subprocess.run(["nbgrader", "autograde", aname])
    subprocess.run(["nbgrader", "generate_feedback", aname])

    new_gradebook_path = f'{assignment_scratch}/org_gradebook.csv'
    os.rename(gpath, new_gradebook_path)

    os.remove(zpath)

    # Pull grades from individual autograded assignments
    autograded_qDist = []
    for user in usernames:
        if os.path.exists(os.path.join(os.getcwd(),'autograded',user,aname,f'{aname}.ipynb')):
            grades = calculate_grades(aname, user, coursename, opath)
            autograded_qDist.append(grades)
        else:
            continue
    
    subprocess.run(["nbgrader", "export", "csv", aname])

    export_csv_path =  os.path.join(coursepath,'grades.csv')
    assert os.path.exists(export_csv_path), 'Incorrect exported gradebook path'

    scrgradepath = os.path.join(assignment_scratch,'grades.csv')
    os.rename(export_csv_path,scrgradepath)

    graded_gradebook = shutil.copyfile(new_gradebook_path, f'{assignment_scratch}/gradedAssignment.csv')
    
    grades = pd.read_csv(scrgradepath)
    assignmentgrades = grades.groupby("assignment").get_group(aname)

    finalgrades = pd.read_csv(graded_gradebook)

    for user, score in zip(assignmentgrades['student_id'], assignmentgrades['score']):
        iidx = finalgrades['Username'].tolist().index(user)
        cols = finalgrades.columns
        finalgrades.iat[iidx, -1] = score
    
    updated_scores = finalgrades[finalgrades.columns[-1]].replace("Needs Grading", 0).fillna(0)
    finalgrades[finalgrades.columns[-1]] = pd.to_numeric(updated_scores, downcast='float')
    
    finalgrades.to_csv(graded_gradebook, index=False)

    totpts = list(assignmentgrades['max_score'])[0]

    # Get the last column name (assumed to be the score column)
    score_col = finalgrades.columns[-1]

    # Ensure scores are numeric (just in case any strings slipped in)
    finalgrades[score_col] = pd.to_numeric(finalgrades[score_col], errors='coerce').fillna(0)

    # Filter students with a score of 0
    zero_scores = finalgrades[finalgrades[score_col] == 0]

    # Filter students with score below 50
    below_50 = finalgrades[(finalgrades[score_col] < totpts/2) & (finalgrades[score_col] > 0)]

    # Print students with 0
    print("📍 Students with a score of 0:")
    print(zero_scores[["First Name", "Last Name", "Username", score_col]].copy().rename(columns={score_col: "grade"}).to_string(index=False))

    # Print students below 50
    print("\n📉 Students with a score below 50% (excluding 0):")
    print(below_50[["First Name", "Last Name", "Username", score_col]].copy().rename(columns={score_col: "grade"}).to_string(index=False))
    # Calculate and print statistics
    mean_score = finalgrades[score_col].mean()
    std_score = finalgrades[score_col].std()

    print(f"\n📊 Average Score: {mean_score:.2f}")
    print(f"📈 Standard Deviation: {std_score:.2f}")

    # Plot distribution
    plt.rcParams['font.family'] = 'serif'
    fig = plt.figure(figsize=(8, 5))
    plt.hist(finalgrades[score_col], bins=int(totpts), edgecolor='black', color='skyblue')
    plt.title("Grade Distribution")
    plt.xlabel("Score")
    plt.ylabel("Number of Students")
    plt.axvline(mean_score, color='red', linestyle='dashed', linewidth=1.5, label=f"Mean: {mean_score:.2f}")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.xticks(range(0,int(totpts)+1))
    plt.tight_layout()
    plt.show()
    fig.savefig(os.path.join(assignment_scratch, 'grade_dist.png'))
    plt.close()

    question_ids = [key for key in autograded_qDist[0] if key != 'total']
    question_scores = {qid: [] for qid in question_ids}

    # Fill in the scores
    for student in autograded_qDist:
        for qid in question_ids:
            question_scores[qid].append(student.get(qid, 0))

    # Compute average score per question
    avg_scores = [np.mean(question_scores[qid]) for qid in question_ids]
    std_devs = [np.std(question_scores[qid]) for qid in question_ids]

    # Plot
    fig2 = plt.figure(figsize=(12, 6))
    bars = plt.bar(question_ids, avg_scores, yerr=std_devs, capsize=5, color='skyblue', edgecolor='black')

    plt.title('Average Score per Question with Standard Deviation')
    plt.xlabel('Question ID')
    plt.ylabel('Average Score')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()
    fig2.savefig(os.path.join(assignment_scratch, 'q_dist.png'))

    shutil.copyfile(f'{assignment_scratch}/gradedAssignment.csv', f'{temppath}/gradedAssignment.csv')
    print(f'Successfully Autograded Assignment {aname}!')

def autogradeStudent(username, aname, coursename, opath=os.getcwd()):
    """
    Function that will autograde for a specific student if the autograder has already been run on the whole class.

    -------------------------
    Inputs
    -------------------------
    username (str) : username of the student, this is the name that the students folder is labelled; nbgraders "student_id"
    aname (str) : assignment name to grade (without the extension)
    coursename (str) : name of the autograded course, for more info see autogradeAssignment().
    opath (str) : overhead path that contains the course and the temp folder, see autogradeAssignment() for more detail. 

    -------------------------
    Output
    -------------------------
    HTML visual of the feedback for the student to directly pull the grade. 
    """
    from IPython.display import display, HTML
    
    subpath_student = os.path.join(opath,coursename,'submitted',username)
    assert os.path.exists(subpath_student), 'Student does not have a submitted folder.'
    
    assignment_student_path = os.path.join(subpath_student,aname)
    try:
        os.mkdir(assignment_student_path)
    except FileExistsError:
        pass

    temppath = os.path.join(opath,'temp')
    input('Place student notebook into temp folder')
    assert len(os.listdir(temppath)) == 1, 'temp folder contains to many files'

    notebookpath = os.path.join(temppath,os.listdir(temppath)[0])

    os.rename(notebookpath, os.path.join(assignment_student_path,f'{aname}.ipynb'))
    
    coursepath = os.path.join(opath, coursename)
    os.chdir(coursepath)
    subprocess.run(["nbgrader", "autograde", aname])
    subprocess.run(["nbgrader", "generate_feedback", aname])

    os.chdir('..')
    
    def read_html_file(file_path):
        with open(file_path, 'r') as file:
            html_content = file.read()
        return html_content

    feedback_student = os.path.join(opath,coursename,'feedback',username,aname,f'{aname}.HTML')
    display(HTML(read_html_file(feedback_student)))

def createAssignment(aname, coursename, opath=os.getcwd()):
    """
    Validates an instructor's assignment notebook and generates the corresponding student version
    using `nbgrader`. The function expects a single instructor notebook to be manually placed into
    a `temp/` folder within the given path, and performs the following steps:

    1. Validates that only one file is present in the `temp/` directory.
    2. Moves the instructor notebook to the nbgrader `source/` directory under the course.
    3. Runs `nbgrader validate` to ensure the notebook is properly structured.
    4. If validation fails, deletes the newly created assignment directory in `source/` and exits.
    5. If validation passes, runs `nbgrader generate_assignment` to produce the student notebook.
    6. Copies the generated student notebook from `release/` back into the `temp/` folder.

    Parameters:
    ----------
    aname : str
        The assignment name. This will be used as the folder and filename for the notebook.
    coursename : str
        The course name. This should correspond to the course folder configured for nbgrader.
    opath : str, optional
        The base path where the course and temp folders are located.
        Defaults to the current working directory.

    Notes:
    -----
    - Assumes the nbgrader environment is already set up with the correct config files.
    - Requires the instructor to manually place a single `.ipynb` file in the `temp/` folder
      before proceeding.
    - Any validation failure will result in cleanup of the assignment directory to prevent
      clutter or confusion.
    - The script interacts with the filesystem and will overwrite existing files without prompt.

    Example:
    --------
    >>> createAssignment("hw1", "cs101")
    Place instructor notebook into temp folder and press ENTER...
    Validating notebook...
    Validation successful. Assigning notebook...
    Student notebook copied to /path/to/temp/hw1.ipynb
    """
    
    temppath = os.path.join(opath, 'temp')
    input('Place instructor notebook into temp folder and press ENTER...')
    
    files = os.listdir(temppath)
    assert len(files) == 1, 'Temp folder contains too many files'
    temp_assignment_path = os.path.join(temppath, files[0])
    
    assignment_folder_path = os.path.join(opath, coursename, 'source', aname)
    os.makedirs(assignment_folder_path, exist_ok=True)
    
    instructor_nb_path = os.path.join(assignment_folder_path, f'{aname}.ipynb')
    os.rename(temp_assignment_path, instructor_nb_path)

    os.chdir(os.path.join(opath, coursename, 'source', aname))
    
    print('Validating notebook...')
    validate_result = subprocess.run(['nbgrader', 'validate', f'{aname}.ipynb'], capture_output=True, text=True)
    
    # Check for validation issues in stdout
    if ("VALIDATION FAILED" in validate_result.stdout) or ("ERROR" in validate_result.stdout):
        print("Validation failed with errors:")
        print(validate_result.stdout)
        os.rename(instructor_nb_path,f'{temppath}/failed.ipynb')
        shutil.rmtree(assignment_folder_path)
        os.chdir('../..')
        return
    
    print("Validation successful. Assigning notebook...")

    os.chdir(os.path.join(opath, coursename))  # back to course root
    subprocess.run(['nbgrader', 'generate_assignment', aname,'--force'])

    student_nb_path = os.path.join('release', aname, f'{aname}.ipynb')
    temp_student_copy_path = os.path.join(temppath, f'{aname}.ipynb')
    
    shutil.copy(student_nb_path, temp_student_copy_path)
    os.chdir('..')
    print(f'Student notebook copied to {temp_student_copy_path}')
    print(f'Assignment {aname} created succesfully!')