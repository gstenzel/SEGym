from diff_patch_search.call_openai import call_model
import json

TASK_TYPES = {
    "list_files_to_be_changed": ["Select the files that need to be changed based on the issue description.", "listing files to be changed", "Affected files"], 
    "detect_lines_to_be_changed_in_files": ["Detect the lines that need to be changed in the files based on the issue description.", "detecting lines to be changed in files", "Lines to be changed"],
    "generate_code_snippets_for_changes": ["Generate the code snippets that need to be changed based on the issue description.", "generating code snippets for changes", "Code snippets for changes"],
    "create_patch_string": ["Create a patch string based on the issue description.", "creating patch strings", "Patch string"]
}

# JSON Schemas for Each Task Type
# These schemas define the JSON structure for each tasks type's output.
JSON_SCHEMAS = {
    "list_files_to_be_changed": {
        "file": "string (full path to file)",
    },
    "detect_code_snippets_for_changes": {
        "file": "string (full path to file)",
        "details": "string (detailed info about code snippet)"
    }, 
    "detect_lines_to_be_changed_in_files": {
        "file": "string (full path to file)",
        "lines_to_be_changed_in_original_and_changed_file": "array of strings (@@ -1,2 +1,10 @@)",
    },
    "generate_code_snippets_for_changes": {
        "file": "string (full path to file)",
        "code_snippet": "string (code snippet)"
    },
    "create_patch_string": {
        "patch_string": "string (diff --git a/...)"
    }
}

# Function to Generate System Prompts
def get_system_prompt(task_type: str) -> str:
    # Fetch the specific instruction and JSON schema for the given analysis type
    specific_instruction = TASK_TYPES.get(task_type, "Perform the task as per the specified type.")[0]
    json_schema = JSON_SCHEMAS.get(task_type, {})

    # Format the JSON schema into a string representation
    json_schema_str = ', '.join([f"'{key}': {value}" for key, value in json_schema.items()])

    # Construct the system prompt with updated instruction
    return (f"You are an expert software engineer capable of {TASK_TYPES[task_type][1]}. "
            f"{specific_instruction} Please respond with your analysis directly in JSON format "
            f"The JSON schema should include: {{{json_schema_str}}}.")


def generate_diff_patch(issue_description: str   ):
    # read the repo description
    
    with open("repo-description.txt", 'r') as file:
        repo_description = file.read()

    with open(issue_description, 'r') as file:
        issue = file.read()

    user_prompt = f"""Please create a detailed implementation proposal for the described task and the following issue based on the provided code base.\n"""
    user_prompt += f"""Code Base: {repo_description}\n"""
    user_prompt += f"""Issue: {issue}\n"""

    for i, task_type in enumerate(TASK_TYPES.keys()):

        system_prompt = get_system_prompt(task_type)

        with open(f'gpt-4/prompt-{i}.md', 'w') as file:
            file.write("System Prompt:\n")
            file.write("----------------\n")
            file.write(system_prompt)
            file.write("\n\n")
            file.write("User Prompt:\n")
            file.write("--------------\n")
            file.write(user_prompt)
        
        json_data = call_model(system_prompt, user_prompt, model="gpt-4-0125-preview")
        
        user_prompt += f"""{TASK_TYPES[task_type][2]}: {json_data}\n"""

        # Create a new file
        with open(f'gpt-4/{task_type}.md', 'w') as file:
            file.write(json_data)

        if task_type == "create_patch_string":
            # write the patch to a file
            with open(f'gpt-4/{task_type}.patch', 'w') as file:
                patch_dict = json.loads(json_data)
                file.write(patch_dict['patch_string'])
                file.write('\n')