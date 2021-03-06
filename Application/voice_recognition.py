import tkinter as tk
import speech_recognition as sr
import re as re
from fuzzywuzzy import fuzz
from vosk import SetLogLevel
SetLogLevel(-1)
import os
import sys
import json
import pyaudio
import compiler as comp

# list of commands, has some extra strings for testing
commandWords = [ "create new variable", 
                 "assign old variable",
                 "return statement",
                 "create for loop",
                 "create while loop",
                 "create if statement",
                 "create else if statement",
                 "create else statement done",
                 "create array",
                 "move cursor",
                 "indent cursor",
                 "undo command",
                 "redo command",
                 "select word",
                 "select line",
                 "select block",
                 "copy text",
                 "paste text",
                 "cut text",
                 "create function",
                 "print statement",
                 "print variable",
                 "insert characters",
                 "show set of variables"]

# this set will contain variable names created by createNewVariable()                 
setOfVariableNames = []

# flag to determine to use google or sphinx
useGoogleFlag = False

# global variables used for selection of text in text editor
global selBeg, selEnd
# path needed to find location of application
#path = os.getcwd()
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


# function to get voice input and returns as a string
def getVoiceInput():
    """returns a string of the recorded voice input"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
        
        # if useGoogleFlag has been assigned true, use google voice recognition
        if useGoogleFlag:
            audioToText = r.recognize_google(audio)
        else:
            path = resource_path("VoiceTraining/Profiles/en-US")
            print("inside getVoiceInput(): path = " + path)
            audioToText = r.recognize_sphinx(audio, language = path)
            
    return audioToText.lower()

def phraseMatch(audioToText,tex,tex2,tex3,tex4):
    """takes a matched command and calls the related function"""
    win = tk.Toplevel(bg='#2b2b2b')
    win.wm_title("Prompts")
    prompt = tk.Text(win, width=50, height=15,bg='#2b2b2b',foreground="#d1dce8")
    prompt.grid(row=0,column=0,padx=5,pady=5,sticky='nsew')
    print("input: " + audioToText + "\n")
    prompt.insert(tk.END, "input: " + audioToText + "\n")
    validCommand = False
    #send info to command manager window on UI
    tex3.insert(tk.END, "matched voice input to command..." + "\n")
    tex3.see(tk.END)
    closestString = getClosestString(audioToText, commandWords,tex3)
    #send matched command to Command(s) Received window on UI
    tex2.insert(tk.END, closestString + "\n")
    tex2.see(tk.END)
    #set stringP to call for matching functions
    if closestString == "create new variable":
        validCommand = True
        stringP = createNewVariable(tex3, prompt)
        tex.edit_separator()
    elif closestString == "show set of variables":
        validCommand = True
        showSet(tex4)
        stringP = "*"
    elif closestString == "assign old variable":
        validCommand = True
        stringP = assignOldVariable(tex3, prompt)
        tex.edit_separator()
    elif closestString == "return statement":
        validCommand = True
        stringP = returnStatement(tex3, prompt)
        tex.edit_separator()
    elif closestString == "create for loop":
        validCommand = True
        stringP = createForLoop(tex3, prompt)
        tex.edit_separator()
    elif closestString == "create while loop":
        validCommand = True
        stringP = createWhileLoop(tex3, prompt)
        tex.edit_separator()
    elif closestString == "create if statement":
        validCommand = True
        stringP = createIfStatement(tex3, prompt)
        tex.edit_separator()
    elif closestString == "create else if statement":
        validCommand = True
        stringP = createElseIfStatement(tex3, prompt)
        tex.edit_separator()
    elif closestString == "create else statement done":
        validCommand = True
        stringP = createElseStatement(tex3, prompt)
        tex.edit_separator()
    elif closestString == "create array":
        validCommand = True
        stringP = createArray(tex3, prompt)
        tex.edit_separator()
    elif closestString == "move cursor":
        validCommand = True
        moveCursor(tex3, tex, prompt)
        stringP = "*"
        tex.edit_separator()
    elif closestString == "undo command":
        validCommand = True
        tex.edit_undo()
        stringP = "*"
    elif closestString == "redo command":
        validCommand = True
        tex.edit_redo()
        stringP = "*"
    elif closestString == "select word":
        validCommand = True
        selectWord(tex3, tex, prompt)
        stringP = "*"
        tex.edit_separator()
    elif closestString == "select line":
        validCommand = True
        selectLine(tex3, tex, prompt)
        stringP = "*"
        tex.edit_separator()
    elif closestString == "select block":
        validCommand = True
        selectBlock(tex3, tex, prompt)
        stringP = "*"
        tex.edit_separator()
    elif closestString == "create function":
        validCommand = True
        stringP = createDef(tex3, prompt)
        tex.edit_separator()
    elif closestString == "copy text":
        validCommand = True
        copyText(tex3, tex, prompt)
        stringP = "*"
        tex.edit_separator()
    elif closestString == "paste text":
        validCommand = True
        stringP = pasteText(tex3, tex, prompt)
        tex.edit_separator()
    elif closestString == "cut text":
        validCommand = True
        cutText(tex3, tex, prompt)
        stringP = "*"
        tex.edit_separator()
    elif closestString == "indent cursor":
        validCommand = True
        tex.insert(tk.INSERT, "    ")
        stringP = "*"
        tex.edit_separator()
    elif closestString == "print variable":
        validCommand = True
        stringP = printVariable(tex3, prompt)
        tex.edit_separator()
    elif closestString == "print statement":
        validCommand = True
        stringP = printStatement(tex3, prompt)
        tex.edit_separator()
    elif closestString == "insert characters":
        validCommand = True
        stringP = insertChars(tex3, prompt)
        tex.edit_separator()
    else:
        stringP = ""
        #send response to System Output window on UI
        tex4.insert(tk.END, "no matching phrase found: " + audioToText + "\n")
        tex4.see(tk.END)
        win.after(1000, lambda: win.destroy())
    if validCommand:
        #send response to System Output window on UI
        tex4.insert(tk.END, "valid command received..." + "\n")
        tex4.see(tk.END)
        win.after(1000, lambda: win.destroy())
    validCommand = False
    return stringP

def test_compiler(text,root):
    comp.main(text,root)

def getClosestString(inputString, listToMatch,tex3):
    """returns a string that is the closest match to a programmed command"""
    i = 0
    highest = 0
    closestString = ""
    
    # if there is nothing in the listToMatch, return original string
    if not listToMatch:
        return inputString
        
    for i in range(0,len(listToMatch)):
        string = listToMatch[i]
        ratio = fuzz.token_set_ratio(inputString, string)
        print(string + ": " + str(ratio))
        
        if ratio > highest:
            highest = ratio
            closestString = string
    
    # print("\nClosest string to match input was\n")
    # check for threshold of 80 or greater to find matching command
    if highest >= 80:
        # print(closestString + ": " + str(highest))
        # send status to command manager window on UI
        tex3.insert(tk.END, "closest match: " + closestString + "\n")
        tex3.see(tk.END)
    else:
        # print("not found")
        # send status to command manager window on UI
        tex3.insert(tk.END, inputString + " not found.\n")
        tex3.see(tk.END)
        closestString = "invalid"
    return closestString
    
# Operations dictionary for string to symbol
op_dict = {"plus"       :"+", 
           "minus"      :"-", 
           "times"      :"*",
           "divided by" :"/" }
           
compare_dict = { "less than or equal to"      : "<=",
                 "less than"                  : "<",
                 "greater than or equal to"   : ">=",
                 "greater than"               : ">",
                 "not equal to"               : "!=",
                 "equal to"                   : "==" }

# obtained from https://stackoverflow.com/questions/493174/is-there-a-way-to-convert-number-words-to-integers
# will convert number words to int literals
def text2int(textnum, numwords={}):
    """converts spoken numbers to the integer values"""
    if not numwords:
      units = [
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
        "sixteen", "seventeen", "eighteen", "nineteen",
      ]

      tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

      scales = ["hundred", "thousand", "million", "billion", "trillion"]

      numwords["and"] = (1, 0)
      for idx, word in enumerate(units):    numwords[word] = (1, idx)
      for idx, word in enumerate(tens):     numwords[word] = (1, idx * 10)
      for idx, word in enumerate(scales):   numwords[word] = (10 ** (idx * 3 or 2), 0)

    current = result = 0
    for word in textnum.split():
        if word not in numwords:
            # raise Exception("Illegal word: " + word)
            return textnum

        scale, increment = numwords[word]
        current = current * scale + increment
        if scale > 100:
            result += current
            current = 0

    return result + current

# Test function just to see if the set works    
def showSet(tex4):
    """developer command used to test creation of variables"""
    #print("Currently in showSet() function.\n" +
    tex4.insert(tk.END, "Set of variable names:")
    for i in setOfVariableNames:
        tex4.insert(tk.END, "          " + i + ",")
        tex4.see(tk.END)
        
# receives input from user saying yes or no and returns true if yes, false if no
def confirm(prompt):
    """a prompt to confirm with user if voice was captured correctly"""
    vInput = getVoiceInput()
    yesRatio = fuzz.ratio(vInput, "yes")
    noRatio = fuzz.ratio(vInput, "no")
    print("yes: " + str(yesRatio) + "\n" +
          "no:  " + str(noRatio)  + "\n")
    # prompt.insert(tk.END, "\nyes: " + str(yesRatio) + "\n" +"no:  " + str(noRatio)  + "\n" )
    prompt.insert(tk.END, "\n")
    if yesRatio > noRatio: return True 
    else: return False


# Very basic version of create new variable command. The terminal will prompt the user for voice input.
# The program will be able to take any string of characters and uses snake case for variable name.
# The program will be able to convert word versions of +, -, *, /, and numbers into their symbol versions.

# Example
# Voice input
#     variableName = test variable
#     expression   = one plus two minus three
#     output:        test_variable = 1 + 2 - 3

# ***************************************************************************************
# command "create new variable" returns string = variableName + " = " + expression + "\n"
# use case 1, CNV
# ***************************************************************************************
def createNewVariable(tex3,prompt):
    """creates a string for the text editor window: variable = expression"""
    # Get and format variable name, will use snake case
    correctName = False
    nameTaken = True
    while not correctName or nameTaken:
        correctName = False
        nameTaken = True
        
        print("Say name of new variable.\n")
        prompt.insert(tk.END,"Say name of new variable.\n")
        vInput = getVoiceInput()
        vInput = vInput.replace(" ","_")
        variableName = vInput
        
        print("Variable name: " + variableName + "\n" +
              "Is this correct? (Yes/No)")
        prompt.insert(tk.END,"Variable name: " + variableName + '\n' +
              "Is this correct? (Yes/No)")
        if confirm(prompt): correctName = True
        else: continue
        
        if variableName in setOfVariableNames:
            print("Variable name: " + variableName + ", is already used in the program.\n" +
                  "Do you still want to use it? (Yes/No)")
            prompt.insert(tk.END,"Variable name: " + variableName + ", is already used in the program.\n" +
                  "Do you still want to use it? (Yes/No)")
            if confirm(prompt): nameTaken = False
        else:
            nameTaken = False
             
    
    # Get expression
    correctExpression = False
    while not correctExpression:    
        print("State value for variable.\n")
        prompt.insert(tk.END,"State value for variable.\n")
        vInput = getVoiceInput()
        # replace operation words with symbols
        for word, symbol in op_dict.items():
            vInput = vInput.replace(word, symbol)   
            
        # remove any periods
        vInput = vInput.replace(".", "")
        
        # split input by operators    
        vInputSplit = re.split("([+]|[-]|[*]|[/])", vInput)
        
        # find indexes of the operations
        opLocations = []
        for i in range(0, len(vInputSplit)):
            if vInputSplit[i] in op_dict.values():
                opLocations.append(i)
        
        # go through the split string and replace with symbols/literals            
        for i in range(0, len(vInputSplit)):
            if i not in opLocations:   
                vInputSplit[i] = str(text2int(vInputSplit[i]))
                
                # check if the term starts with a letter
                # if so, it must be a preexisting variable name and 
                # match it with one from the setOfVariableNames
                if vInputSplit[i][0].isalpha():
                    closestVariable = getClosestString(vInputSplit[i], setOfVariableNames,tex3)
                    
                    print("Got input of: " + str(vInputSplit) + "\n")
                    prompt.insert(tk.END,"Got input of: " + str(vInputSplit) + "\n")
                    print("Closest match was: " + str(closestVariable) + "\n")
                    prompt.insert(tk.END,"Closest match was: " + str(closestVariable) + "\n")
                    vInputSplit[i] = closestVariable
        
        # reformat expression
        expression = ""
        for i in range(0, len(vInputSplit)): 
            if i in opLocations:   
                expression = expression + vInputSplit[i]
            else:
                expression = expression + vInputSplit[i]
                
        # print("Expression: " + expression + '\n' + "Is this correct? (Yes/No)")
        prompt.insert(tk.END, variableName + " = " + expression + "\n" + "Is this correct? (Yes/No)")
        if confirm(prompt): correctExpression = True
        
    
    # used for checking correctness in terminal    
    # print("expression = " + expression)
    
    if variableName not in setOfVariableNames:
        setOfVariableNames.append(variableName)  
    
    string = variableName + " = " + expression + "\n"
    return string

# *********************************************************************************
# command "assign old variable" returns string = variableName + " = " + expression + "\n"
# use case 2, AOV
# *********************************************************************************
def assignOldVariable(tex3, prompt):
    """identifies an existing variable or creates a new variable if not found"""
    """creates a string for the text editor window: variable = expression"""
    # check if there are any old variables
    if not setOfVariableNames:
        print("No variable names already initialized.\n")
        prompt.insert(tk.END, "No variable names already initialized.\n")
        return ""
        
    # get input for the variable name to be modified
    correctName = False
    while not correctName:
        # print("Say the name of the variable you want to modify.\n")
        # ask user for variable to modify in the GUI popup
        prompt.insert(tk.END, "Say the name of the variable you want to modify.\n")
        vInput = getVoiceInput()
        variableName = getClosestString(vInput, setOfVariableNames,tex3)
        if variableName == "invalid":
            variableName = vInput
            setOfVariableNames.append(variableName)
            prompt.insert(tk.END, "New variable detected.\n")
            tex3.insert(tk.END, variableName + " not found, created new variable.\n")
            tex3.see(tk.END)
        # print("Variable name: " + variableName + "\n" + "Is this correct? (Yes/No)")
        # ask user for confirmation in GUI popup
        prompt.insert(tk.END, "Variable name: " + variableName + "\n" + "Is this correct? (Yes/No)")
        if confirm(prompt): correctName = True
        else: continue
        
    # get expression
    correctExpression = False
    while not correctExpression:    
        # print("State what the variable equals.\n")
        prompt.insert(tk.END, "State value for variable.\n")
        vInput = getVoiceInput()
        
        # replace operation words with symbols
        for word, symbol in op_dict.items():
            vInput = vInput.replace(word, symbol)   
            
        # remove any periods
        vInput = vInput.replace(".", "")
        
        # split input by operators    
        vInputSplit = re.split("([+]|[-]|[*]|[/])", vInput)
        
        # find indexes of the operations
        opLocations = []
        for i in range(0, len(vInputSplit)):
            if vInputSplit[i] in op_dict.values():
                opLocations.append(i)
        
        # go through the split string and replace with symbols/literals            
        for i in range(0, len(vInputSplit)):
            if i not in opLocations:   
                vInputSplit[i] = str(text2int(vInputSplit[i]))
                
                # check if the term starts with a letter
                # if so, it must be a preexisting variable name and 
                # match it with one from the setOfVariableNames
                if vInputSplit[i][0].isalpha():
                    closestVariable = getClosestString(vInputSplit[i], setOfVariableNames,tex3)
                    if closestVariable=="invalid":
                        # print("Got input of: " + str(vInputSplit) + "\n")
                        prompt.insert(tk.END, vInputSplit[i] + " is not defined\n")
                        # vInputSplit[i] = closestVariable
                    else:
                        vInputSplit[i] = closestVariable
        
        # reformat expression
        expression = ""
        for i in range(0, len(vInputSplit)): 
            if i in opLocations:   
                expression = expression + vInputSplit[i]
            else:
                expression = expression + vInputSplit[i]
                
        # print("Expression: " + expression + "\n" + "Is this correct? (Yes/No)")
        # confirm output from user in GUI popup
        prompt.insert(tk.END, variableName + " = " + expression + "\n" + "Is this correct? (Yes/No)")
        if confirm(prompt): correctExpression = True
        
    string = variableName + " = " + expression + "\n"
    return string

# *********************************************************************************
# command "return statement" returns expression = "return " + expression + "\n"
# use case 3, RS
# *********************************************************************************  
def returnStatement(tex3, prompt):
    """creates a string for the text editor window: return expression"""
    # get voice input
    correctExpression = False
    while not correctExpression:    
        print("Say what you want to return.\n")
        prompt.insert(tk.END, "Say what you want to return.\n")
        vInput = getVoiceInput()
        
        if vInput == "none":
            return "return\n"
        
        # replace operation words with symbols
        for word, symbol in op_dict.items():
            vInput = vInput.replace(word, symbol)   
            
        # remove any periods
        vInput = vInput.replace(".", "")
        
        # split input by operators    
        vInputSplit = re.split("([+]|[-]|[*]|[/])", vInput)
        
        # find indexes of the operations
        opLocations = []
        for i in range(0, len(vInputSplit)):
            if vInputSplit[i] in op_dict.values():
                opLocations.append(i)
        
        # go through the split string and replace with symbols/literals            
        for i in range(0, len(vInputSplit)):
            if i not in opLocations:   
                vInputSplit[i] = str(text2int(vInputSplit[i]))
                
                # check if the term starts with a letter
                # if so, it must be a preexisting variable name and 
                # match it with one from the setOfVariableNames
                if vInputSplit[i][0].isalpha():
                    closestVariable = getClosestString(vInputSplit[i], setOfVariableNames,tex3)
                    
                    print("Got input of: " + str(vInputSplit) + "\n")
                    # prompt.insert(tk.END, "Got input of: " + str(vInputSplit) + "\n")
                    print("Closest match was: " + str(closestVariable) + "\n")
                    # prompt.insert(tk.END, "Closest match was: " + str(closestVariable) + "\n")
                    vInputSplit[i] = closestVariable
        
        # reformat expression
        expression = ""
        for i in range(0, len(vInputSplit)): 
            if i in opLocations:   
                expression = expression + vInputSplit[i]
            else:
                expression = expression + vInputSplit[i]
                
        print("Expression: " + expression + "\n" +
              "Is this correct? (Yes/No)")
        prompt.insert(tk.END, "return " + expression + "\n" +
              "Is this correct? (Yes/No)")
        if confirm(prompt): correctExpression = True
    
    expression = "return " + expression + "\n"
    return expression

# *********************************************************************************
# command "create for loop" returns string = "for " + loopingVariable + " in range
#                                             (" + rangeInt + "):\n    "
# for now, can only create a for loop with range function
# use case 4, CFL
# *********************************************************************************
def createForLoop(tex3, prompt):
    """creates a string for the text editor window: for variable in range (int)"""
    correctVariable = False
    while not correctVariable:
        # print("Say the name of looping variable.\n")
        # system asks user for variable in the popup window of GUI
        prompt.insert(tk.END, "Say the name of the looping variable.\n")
        vInput = getVoiceInput()
        
        vInput = vInput.replace(".","")
        vInput = vInput.replace(" ","_")
        # print("Looping variable: " + vInput + "\n" + "Is this correct? (Yes/No)")
        # confirmation sent to user in popup window of GUI
        prompt.insert(tk.END, "Looping variable: " + vInput + "\n" + "Is this correct? (Yes/No)")
        if confirm(prompt): correctVariable = True
        
    loopingVariable = vInput
        
    correctRange = False
    while not correctRange:
        # print("How many times do you want to repeat this loop?\n")
        # question sent to user in popup window of GUI
        prompt.insert(tk.END, "How many times do you want to repeat this loop?\n")
        vInput = getVoiceInput()
        vInput = str(text2int(vInput))
        
        # print("Amount of loops: " + vInput + "\n" + "Is this correct? (Yes/No)")
        # confirmation sent to user in popup window of GUI
        prompt.insert(tk.END, "Amount of loops: " + vInput + "\n" + "Is this correct? (Yes/No)")
        if confirm(prompt): correctRange = True
        
    rangeInt = vInput
    # string created for insertion in text editor window of GUI
    string = "for " + loopingVariable + " in range(" + rangeInt + "):\n    "
    return string

# *****************************************************************************
# a function to simplify the repetition in case 5,6 and 7 of dealing with the
# operator symbols and creating the necessary strings for the text window
# *****************************************************************************
def getCondition(tex3, prompt, case):
    """returns a string for the use cases of 5,6, and 7 to deal with operator symbols"""
    correctCondition = False

    while not correctCondition:
        print("Say the condition you want for the " + case + ".\n")
        prompt.insert(tk.END, "Say the condition you want for the " + case + ".\n")
        vInput = getVoiceInput()
        vInput = vInput.replace(".","")
        
        # replace strings of comparison operators with symbols
        for x, y in compare_dict.items():
            vInput = vInput.replace(x, y)
                
        # split string into array, while keeping the operator symbols
        vInputSplit = re.split("([<=][>=][!=][==]|[>]|[<])", vInput)
        
        # find location of operators    
        opLocations = []
        for i in range(0, len(vInputSplit)):
            if vInputSplit[i] in compare_dict.values():
                opLocations.append(i)    
        
        # go through the split string and replace with symbols/literals            
        for i in range(0, len(vInputSplit)):
            if i not in opLocations:   
                vInputSplit[i] = str(text2int(vInputSplit[i]))
                
                # check if the term starts with a letter
                # if so, it must be a preexisting variable name, if not warn the user 
                # that the variable does not exist
                if vInputSplit[i][0].isalpha():
                    closestVariable = getClosestString(vInputSplit[i], setOfVariableNames,tex3)
                    if closestVariable == "invalid":                   
                        print("Got input of: " + str(vInputSplit) + "\n")
                        # prompt.insert(tk.END, "Got input of: " + str(vInputSplit) + "\n")
                        print(vInputSplit[i] + " is an unknown variable\n")
                        prompt.insert(tk.END, vInputSplit[i] + " is an unknown variable\n")
        
        # reformat expression
        expression = ""
        for i in range(0, len(vInputSplit)): 
            if i in opLocations:   
                expression = expression + vInputSplit[i]
            else:
                expression = expression + vInputSplit[i]
        print("Condition: " + expression + "\n" + "Is this correct? (Yes/No)")
        prompt.insert(tk.END, "Condition: " + expression + "\n" + "Is this correct? (Yes/No)")
        if confirm(prompt): correctCondition = True

    tex3.insert(tk.END, "created condition for " + case + "\n")
    tex3.see(tk.END)
    return expression

# *********************************************************************************
# command "create while loop" returns string = "while " + condition + ":\n"
# use case 5, CWL
# *********************************************************************************
def createWhileLoop(tex3, prompt):
    """creates a string for the text editor window: while condition:"""
    string = "while " + getCondition(tex3,prompt,"while loop") + ":\n    "
    return string

# *********************************************************************************
# command "create if statement" returns string = "if " + condition + ":\n"
# use case 6, CIF
# *********************************************************************************    
def createIfStatement(tex3, prompt):
    """creates a string for the text editor window: if condition:"""
    string = "if " + getCondition(tex3,prompt,"if statement") + ":\n    "
    return string

# *********************************************************************************
# command "create else-if statement" returns string = "elif " + condition + ":\n"
# use case 7, CEIF
# *********************************************************************************
def createElseIfStatement(tex3, prompt):
    """creates a string for the text editor window: elif condition:"""
    string = "elif " + getCondition(tex3,prompt,"else-if statement") + ":\n    "
    return string

# *********************************************************************************
# command "create else statement done" returns string = "else:\n"
# use case 8, CEF
# *********************************************************************************
def createElseStatement(tex3, prompt):
    """creates a string for the text editor window: else:"""
    string = "else:\n    "
    return string
# *********************************************************************************
# command "create array" returns string = "array = [" + var(s) + "]\n"
# use case 9, CA
# *********************************************************************************
def createArray(tex3, prompt):
    """creates a string for the text editor window: array = [variables]"""
    # Get and format variable name, will use snake case
    correctName = False
    nameTaken = True
    while not correctName or nameTaken:
        correctName = False
        nameTaken = True
        
        print("Say name of new array.\n")
        prompt.insert(tk.END,"Say name of new array.\n")
        vInput = getVoiceInput()
        vInput = vInput.replace(" ","_")
        arrayName = vInput
        
        print("Array name: " + arrayName + "\n" +
              "Is this correct? (Yes/No)")
        prompt.insert(tk.END,"Array name: " + arrayName + '\n' +
              "Is this correct? (Yes/No)")
        if confirm(prompt): correctName = True
        else: continue
        
        if arrayName in setOfVariableNames:
            print("Array name: " + arrayName + ", is already used in the program.\n" +
                  "Do you still want to use it? (Yes/No)")
            prompt.insert(tk.END,"Array name: " + arrayName + ", is already used in the program.\n" +
                  "Do you still want to use it? (Yes/No)")
            if confirm(prompt): nameTaken = False
        else:
            nameTaken = False
             
    
    # Get expression
    correctExpression = False
    while not correctExpression:    
        print("State values for array. Say 'stop' to denote seperation of values.\n")
        prompt.insert(tk.END,"State values for array. Say 'stop' to denote seperation of values.\n")
        vInput = getVoiceInput()       
        # replace 'comma' with '", "' to place quotations around elements of array
        vInput = vInput.replace(' stop ', "\", \"")
        expression = vInput    
        # print(arrayName + ' = ["' + expression + '"]' + "\n" + "Is this correct? (Yes/No)")
        prompt.insert(tk.END, arrayName + " = [\"" + expression + "\"]" + "\nIs this correct? (Yes/No)")
        if confirm(prompt): correctExpression = True
    
    if arrayName not in setOfVariableNames:
        setOfVariableNames.append(arrayName)  
    
    string = arrayName + ' = ["' + expression + '"]' + "\n"
    return string
# *********************************************************************************
# command "move cursor"
# use case 10, MC
# *********************************************************************************
def moveCursor(tex3, tex, prompt):
    """moves cursor in text editor window to user provided location"""
    correctLine = False
    while not correctLine:
        prompt.insert(tk.END,"State line number.\n")
        vInput = getVoiceInput()
        line = vInput
        prompt.insert(tk.END,"line number: " + line + "\nIs this correct? (Yes/No)")
        if confirm(prompt): correctLine = True

    correctColumn = False
    while not correctColumn:
        prompt.insert(tk.END,"State column number.\n")
        vInput = getVoiceInput()
        column = vInput
        prompt.insert(tk.END,"column number: " + column + "\nIs this correct? (Yes/No)")
        if confirm(prompt): correctColumn = True

    pos = line + '.' + column
    tex.tag_remove(tk.SEL, "1.0", tk.END)
    tex.mark_set(tk.INSERT, pos)
    tex3.insert(tk.END,"moved cursor to: " + pos + "\n")

# *********************************************************************************
# command "select word"
# use case 14, SW
# *********************************************************************************
def selectWord(tex3, tex, prompt):
    """selects area in text editor window from user provided locations"""
    global selBeg, selEnd
    tex.tag_remove(tk.SEL, "1.0", tk.END)
    correctBLWord = False
    while not correctBLWord:
        prompt.insert(tk.END,"State line of word beginning.\n")
        vInput = getVoiceInput()
        bLWord = vInput
        prompt.insert(tk.END,"line number: " + bLWord + "\nIs this correct? (Yes/No)")
        if confirm(prompt): correctBLWord = True

    correctBCWord = False
    while not correctBCWord:
        prompt.insert(tk.END,"State column of word beginning.\n")
        vInput = getVoiceInput()
        bCWord = vInput
        prompt.insert(tk.END,"column number: " + bCWord + "\nIs this correct? (Yes/No)")
        if confirm(prompt): correctBCWord = True

    correctELWord = False
    while not correctELWord:
        prompt.insert(tk.END,"State line of word ending.\n")
        vInput = getVoiceInput()
        eLWord = vInput
        prompt.insert(tk.END,"line number: " + eLWord + "\nIs this correct? (Yes/No)")
        if confirm(prompt): correctELWord = True

    correctECWord = False
    while not correctECWord:
        prompt.insert(tk.END,"State column of word ending.\n")
        vInput = getVoiceInput()
        eCWord = vInput
        prompt.insert(tk.END,"column number: " + eCWord + "\nIs this correct? (Yes/No)")
        if confirm(prompt): correctECWord = True

    blineNum = str(bLWord)
    bcolNum = str(bCWord)
    elineNum = str(eLWord)
    ecolNum = str(eCWord)
    selBeg = blineNum + '.' + bcolNum
    selEnd = elineNum + '.' + ecolNum
    tex.tag_add('sel', selBeg, selEnd)
    tex.mark_set(tk.INSERT, selBeg)
    #tex.tag_delete('sel')
    tex3.insert(tk.END,"selected word " + selBeg + " through " + selEnd + "\n")
# *********************************************************************************
# command "select line"
# use case 15, SL
# *********************************************************************************
def selectLine(tex3, tex, prompt):
    """selects line in text editor window from user provided location"""
    global selBeg, selEnd
    tex.tag_remove(tk.SEL, "1.0", tk.END)
    correctLine = False
    while not correctLine:
        prompt.insert(tk.END,"State line number.\n")
        vInput = getVoiceInput()
        line = vInput
        prompt.insert(tk.END,"line number: " + line + "\nIs this correct? (Yes/No)")
        if confirm(prompt): correctLine = True

    lineNum = str(line)
    selBeg = lineNum + '.0'
    selEnd = lineNum + '.130'
    tex.tag_add('sel', selBeg, selEnd)
    tex.mark_set(tk.INSERT, selBeg)
    #tex.tag_delete('sel')
    tex3.insert(tk.END,"selected line " + lineNum + "\n")
# *********************************************************************************
# command "select block"
# use case 16, SB
# *********************************************************************************
def selectBlock(tex3, tex, prompt):
    """selects multiple lines in text editor window from user provided locations"""
    global selBeg, selEnd
    tex.tag_remove(tk.SEL, "1.0", tk.END)
    correctBLine = False
    while not correctBLine:
        prompt.insert(tk.END,"State beginning of block line number.\n")
        vInput = getVoiceInput()
        bline = vInput
        prompt.insert(tk.END,"line number: " + bline + "\nIs this correct? (Yes/No)")
        if confirm(prompt): correctBLine = True

    correctELine = False
    while not correctELine:
        prompt.insert(tk.END,"State end of block line number.\n")
        vInput = getVoiceInput()
        eline = vInput
        prompt.insert(tk.END,"line number: " + eline + "\nIs this correct? (Yes/No)")
        if confirm(prompt): correctELine = True

    blineNum = str(bline)
    elineNum = str(eline)
    selBeg = blineNum + '.0'
    selEnd = elineNum + '.130'
    tex.tag_add('sel', selBeg, selEnd)
    tex.mark_set(tk.INSERT, selBeg)
    #tex.tag_delete('sel')
    tex3.insert(tk.END,"selected block of lines " + blineNum + " through " + elineNum + "\n")
# *********************************************************************************
# command "copy text"
# use case 17, CT
# *********************************************************************************
def copyText(tex3, tex, prompt):
    """copies a selected area in text editor window"""
    global selBeg, selEnd
    tex.clipboard_clear()
    prompt.insert(tk.END,selBeg + "to " + selEnd + "\n")
    copyString = tex.get(selBeg ,selEnd)
    tex.clipboard_append(copyString)
    prompt.insert(tk.END,copyString + "\n")
    tex3.insert(tk.END,"copied: " + copyString + "\n")
# *********************************************************************************
# command "paste text"
# use case 18, PT
# *********************************************************************************
def pasteText(tex3, tex, prompt):
    """pastes text in text editor window from users copy command"""
    # global selEnd
    copiedText = tex.clipboard_get()
    prompt.insert(tk.END,"copied text = " + copiedText + "\n")
    tex.tag_remove(tk.SEL, "1.0", tk.END)
    tex3.insert(tk.END,"pasted text\n")
    return copiedText
# *********************************************************************************
# command "cut text"
# use case 11, CUT
# *********************************************************************************
def cutText(tex3, tex, prompt):
    """cuts text from text editor window after users select command"""
    global selBeg, selEnd
    tex.clipboard_clear()
    # prompt.insert(tk.END,selBeg + "to " + selEnd + "\n")
    copyString = tex.get(selBeg ,selEnd)
    tex.clipboard_append(copyString)
    tex.delete(selBeg, selEnd)
    prompt.insert(tk.END,"delete: " + copyString + "\n")
    tex3.insert(tk.END,"deleted: " + copyString + "\n")
# *********************************************************************************
# command "print statement" returns string = "print('" + printLine + "')\n"
# use case 19, PS
# *********************************************************************************
def printStatement(tex3, prompt):
    """creates a string for the text editor window: print(given text)"""
    correctPrint = False
    while not correctPrint:
        print("Say the line for printing.\n")
        prompt.insert(tk.END, "Say the line for printing.\n")
        vInput = getVoiceInput()
        
        # vInput = vInput.replace(".","")
        # vInput = vInput.replace(" ","_")
        print("line: " + vInput + "\n" +
              "Is this correct? (Yes/No)")
        prompt.insert(tk.END, "line: " + vInput + "\nIs this correct? (Yes/No)")
        if confirm(prompt): correctPrint = True
        
    printLine = vInput
    
    string = "print('" + printLine + "')\n"
    return string

# *********************************************************************************
# command "print variable" returns string = "print(" + printVar + ")\n"
# use case 20, PV
# *********************************************************************************
def printVariable(tex3, prompt):
    """creates a string for the text editor window: print(given variable)"""
    correctPrint = False
    while not correctPrint:
        print("Say the variable for printing.\n")
        prompt.insert(tk.END, "Say the variable for printing.\n")
        vInput = getVoiceInput()
        
        # vInput = vInput.replace(".","")
        vInput = vInput.replace(" ","_")
        print("variable: " + vInput + "\n" +
              "Is this correct? (Yes/No)")
        prompt.insert(tk.END, "variable: " + vInput + "\nIs this correct? (Yes/No)")
        if confirm(prompt): correctPrint = True
        
    printVar = vInput
    
    string = "print(" + printVar + ")\n"
    return string

# *********************************************************************************
# command "create function" returns string = "def " + printLine + "():\n    "
# still need to implement functions with arguments
# use case 21, CF
# *********************************************************************************
def createDef(tex3,prompt):
    """creates a string for the text editor window: def name()"""
    #print(str(testInt))
    correctPrint = False
    while not correctPrint:
        print("Say name of function.\n")
        prompt.insert(tk.END, "Say name of the function.\n")
        vInput = getVoiceInput()
        
        # vInput = vInput.replace(".","")
        vInput = vInput.replace(" ","_")
        print("new def(): " + vInput + "\n" +
              "Is this correct? (Yes/No)")
        prompt.insert(tk.END, "def " + vInput + "():\nIs this correct? (Yes/No)")
        if confirm(prompt): correctPrint = True
        
    printLine = vInput
    
    string = "def " + printLine + "():\n    "
    return string

# *****************************************************************************
# a function to replace words with symbols such as quotations, asterix, etc
# creating the intended string for the text editor window
# *****************************************************************************
def getSymbols(tex3, prompt, stringIn):
    """converts spoken words to intended symbols"""
    sym_dict = {"plus"                 :"+",
                "space"                :" ",
                "equal"                :"=",
                "pipe"                 :"|",
                "open angle bracket"   :"<",
                "closed angle bracket" :">",
                "open bracket"         :"[",
                "closed bracket"       :"]" }
    # replace strings of operators with matching symbol(s)
    for x, y in sym_dict.items():
        stringIn = stringIn.replace(x, y)

    return stringIn

# *********************************************************************************
# command "insert characters" adds characters at position of cursor to text field
# use case 23, ICHAR
# *********************************************************************************
def insertChars(tex3, prompt):
    """creates a string for the text editor window: spoken text"""
    correctChars = False
    while not correctChars:
        print("Say the line of character(s).\n")
        prompt.insert(tk.END, "Say the line of character(s).\n")
        tex3.insert(tk.END, "waiting for character(s)...\n")
        vInput = getVoiceInput()

        vInput = getSymbols(tex3, prompt, vInput)

        print("line: " + vInput + "\nIs this correct? (Yes/No)")
        prompt.insert(tk.END, "line: " + vInput + "\nIs this correct? (Yes/No)")
        if confirm(prompt): correctChars = True

    string = vInput
    tex3.insert(tk.END, "character(s): " + string + " added to text field\n")
    return string

# *********************************************************************************
# returns strings to GUI windows: tex,tex2,tex3,tex4
# *********************************************************************************
def listen(tex,tex2,tex3,tex4,useGoogle):
    """returns a user's finished string to the text editor window in addition to applicable"""
    """ text for the other windows of the application"""
    global useGoogleFlag

    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
        try:
            # If useGoogle flag is true, use google voice recognition
            if useGoogle:
                audioToText = r.recognize_google(audio)
                useGoogleFlag = True
            # Else, use sphinx
            else:
                path = resource_path("VoiceTraining/Profiles/en-US")
                print("inside listen(): path = " + path)
                audioToText = r.recognize_sphinx(audio, language = path)
                useGoogleFlag = False
                
            txtEditorTxt = phraseMatch(audioToText,tex,tex2,tex3,tex4)
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            return ""
    return txtEditorTxt
