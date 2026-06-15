import re
import ast


def string_to_python_list(string):
    cleaned_string = re.sub(r'```(?:python)?|\(three backtick\)', '', string).strip()
    list_match = re.search(r'\[.*\]', cleaned_string, re.DOTALL)

    if list_match:
        python_list_string = list_match.group()
        python_list = ast.literal_eval(python_list_string)
        print(type(python_list))
        if type(python_list) is list:
            return python_list
    else:
        print("No valid Python list found in the string.")
        return []
