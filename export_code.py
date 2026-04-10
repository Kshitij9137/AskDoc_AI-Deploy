import os

# Root folder of your project
project_dir = r"D:\PROJECTS\askdocs-ai"   # <-- change this

# Output file
output_file = "project_code.txt"

# File extensions to include (customize as needed)
include_extensions = {".py", ".js", ".html", ".css", ".cpp", ".java", ".json", ".ts"}

with open(output_file, "w", encoding="utf-8") as outfile:
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            file_path = os.path.join(root, file)
            _, ext = os.path.splitext(file)

            # Skip unwanted files
            if ext.lower() not in include_extensions:
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as infile:
                    content = infile.read()

                # Write filename + content
                outfile.write(f"\n{'='*80}\n")
                outfile.write(f"FILE: {file_path}\n")
                outfile.write(f"{'='*80}\n")
                outfile.write(content + "\n")

            except Exception as e:
                outfile.write(f"\nError reading {file_path}: {e}\n")

print("✅ All code has been exported successfully!")