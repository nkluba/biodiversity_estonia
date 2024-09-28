import os
import re
import pandas as pd


### File Handling Functions ###

def read_text_from_file(filepath):
    """
    Reads the text from a file and returns it as a string.
    """
    if os.path.isfile(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        print(f"File {filepath} not found.")
        return None


def save_to_csv(df, output_file):
    """
    Saves the given pandas DataFrame to a CSV file.
    """
    df.to_csv(output_file, index=False)
    print(f"Updated DataFrame saved to {output_file}")


### Text Processing Functions ###

def extract_full_table_of_contents(text):
    """
    Extracts the full Table of Contents (Sisukord) from the provided text,
    including multi-page layouts and handling irregular breaks.
    """
    # Locate the start of the Sisukord section using "Sisukord" as the trigger
    toc_start_index = text.find("Sisukord")
    if toc_start_index == -1:
        return None  # Sisukord not found

    current_index = toc_start_index
    toc_text = ""

    # Regular expression to look for ToC lines ending in dots followed by page numbers
    toc_line_pattern = re.compile(r"\.{5,}\s*\d+$")

    # Track how many lines without '....' separators we've seen in a row
    lines_without_dots = 0
    toc_continues = True

    # Loop over the text in blocks
    while toc_continues and current_index < len(text):
        # Identify the next form feed (page break) or take rest of the text
        page_break_index = text.find("\f", current_index)
        if page_break_index == -1:
            current_chunk = text[current_index:]
            toc_continues = False
        else:
            current_chunk = text[current_index:page_break_index + 1]
            current_index = page_break_index + 1  # Move cursor to after page break

        toc_lines = current_chunk.splitlines()
        capture_chunk = ""

        # Add lines to ToC and stop when consecutive non-ToC lines grow beyond threshold
        for line in toc_lines:
            # Skip completely empty lines
            clean_line = line.strip()
            if not clean_line:
                continue

            if toc_line_pattern.search(line):
                # We have a valid ToC line (ending in '....page#')
                capture_chunk += line + "\n"
                lines_without_dots = 0  # Reset counter when a valid line is found
            else:
                # Check if we've gone too far from the ToC part
                lines_without_dots += 1
                if lines_without_dots > 10:  # Once 10 consecutive lines without dots occur, we can stop
                    toc_continues = False
                    break

        toc_text += capture_chunk

    print(toc_text)
    return toc_text.strip()  # Clean up and return the collected ToC


def find_section_in_toc(toc, section_name):
    """
    Finds the location of a section in the Table of Contents (ToC) and returns its position in the text.
    """
    lines = toc.splitlines()
    for i, line in enumerate(lines):
        if section_name in line:
            return i, line
    return None, None


def extract_text_between_sections(text, start_section, end_section=None):
    """
    Extracts text between two sections in the text. If end_section is not specified, extracts until the end of the document.
    """
    start_index = text.find(start_section)
    if start_index == -1:
        return None

    if end_section:
        end_index = text.find(end_section, start_index)
        if end_index != -1:
            return text[start_index:end_index].strip()

    # If no end_section is found or not specified, extract till the end
    return text[start_index:].strip()


### Extraction Logic Functions ###

def extract_text_for_sections(text, toc, sections):
    """
    Loops through the sections in the ToC and extracts the text for each section.
    """
    extracted_text = []
    for i, section in enumerate(sections):
        # Find the current section
        _, start_section_line = find_section_in_toc(toc, section)
        if not start_section_line:
            print(f"Section '{section}' not found in Table of Contents.")
            continue

        # Check for the next section to mark the end of this section's extraction
        next_section_line = (
            find_section_in_toc(toc, sections[i + 1])[1] if i + 1 < len(sections) else None
        )
        # Extract the relevant portion of the text
        extracted_chunk = extract_text_between_sections(text, start_section_line, next_section_line)
        if extracted_chunk:
            extracted_text.append(extracted_chunk)

    # Return the combined extracted texts, with sections joined by two newlines
    return "\n\n".join(extracted_text)


### CSV Processing Functions ###

def process_row(row, strategy_file_path):
    """
    Processes a single row of the CSV to extract relevant text sections from the corresponding strategy file.
    """
    sections = [
        row['Elupaik'],
        row['Elupaiga seisund'],
        row['Ohud'],
        row['Populatsiooni muutused Eestis'],
        row['Uuringud'],
        row['Seisund ELis'],
        row['Kokkuvõte']
    ]

    # Read text for the current strategy
    text = read_text_from_file(strategy_file_path)
    if text is None:
        return None

    # Extract full Table of Contents
    toc = extract_full_table_of_contents(text)
    if not toc:
        print(f"Sisukord not found for {strategy_file_path}.")
        return None

    # Extract text for the sections
    extracted_text = extract_text_for_sections(text, toc, sections)

    return extracted_text


def process_csv(input_csv, strategy_materials_folder, output_csv):
    """
    Orchestrates the reading of the CSV, processing of each file, and saving the updated CSV.
    """
    # Load the CSV file
    df = pd.read_csv(input_csv)

    for index, row in df.iterrows():
        # Extract the strategy file name and path
        strategy_file = row['strategy_file']
        strategy_file_path = os.path.join(strategy_materials_folder, strategy_file.replace('.pdf', '_cleaned.txt'))

        # Process the row
        extracted_text = process_row(row, strategy_file_path)

        if extracted_text:
            # Store the extracted text into the DataFrame
            df.at[index, 'Extracted_Text'] = extracted_text

    # Save the updated DataFrame to a new CSV file
    save_to_csv(df, output_csv)


### Main Function ###

def main():
    # Define paths
    input_csv = 'output.csv'
    strategy_materials_folder = 'strategy_materials'
    output_csv = 'updated_output.csv'

    # Process the entire CSV
    process_csv(input_csv, strategy_materials_folder, output_csv)


### Script Entry Point ###

if __name__ == '__main__':
    main()
