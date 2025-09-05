from flask import Flask, render_template, request
import os
import re

app = Flask(__name__)

# A special dictionary to represent a file in the structure.
# This makes it easy to distinguish files from folders.
FILE_SENTINEL = "__file__"



def parse_structure(structure_string: str) -> dict:
    """
    Parses a tree-like string into a nested dictionary, handling the root
    directory as a special case.
    """
    lines = structure_string.strip().splitlines()
    if not lines:
        return {}
    
    # The first line is always the root.
    root_name = lines[0].strip().replace("├──", "").replace("│", "").replace("└──", "").strip()
    if not root_name:
        raise ValueError("The project structure cannot be empty.")
        
    tree = {root_name: {}}
    path_map = {0: tree[root_name]}
    
    # Use a regex to get indentation and name for subsequent lines
    pattern = re.compile(r'^(?P<indent>[\s│├──└──]*)?(?P<name>[^\s│├──└──].*)$')

    for line in lines[1:]:
        if not line.strip():
            continue

        match = pattern.match(line)
        if not match:
            continue

        indent_str = match.group('indent') if match.group('indent') else ''
        name = match.group('name').strip()

        # The depth calculation should be based on the number of indentation symbols.
        depth = indent_str.count('│') + indent_str.count('├──') + indent_str.count('└──')

        parent_dict = path_map.get(depth - 1)
        if parent_dict is None:
            raise ValueError(f"Improperly formatted indentation for '{name}'. Check parent directory.")

        is_folder = not ('.' in name)

        if is_folder:
            new_dict = {}
            parent_dict[name] = new_dict
            path_map[depth] = new_dict
        else:
            parent_dict[name] = FILE_SENTINEL

    return tree
def create_structure(base_path: str, structure: dict):
    """
    Recursively creates files and folders based on a nested dictionary.
    """
    for name, content in structure.items():
        path = os.path.join(base_path, name)
        
        if content == FILE_SENTINEL:
            # It's a file, so create it
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"// This file was created by the project scaffold generator.")
        elif isinstance(content, dict):
            # It's a directory, so create it and recurse
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file_structure_string = request.form['structure']
        target_path = request.form['target_path']

        if not os.path.exists(target_path):
            return f"Error: Target path '{target_path}' does not exist."

        # Define the project name and full path
        project_name = 'my-generated-project'
        full_project_path = os.path.join(target_path, project_name)

        # Parse the string into a nested dictionary
        try:
            parsed_structure = parse_structure(file_structure_string)
        except ValueError as e:
            return f"Error: {e}"

        # Create the project structure on the user's system
        create_structure(full_project_path, parsed_structure)
        
        return f"Project structure created inside '{full_project_path}'!"
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
