import os
import xml.etree.ElementTree as ET
import re

def remove_bracketed_text(text):
    """
    Removes any substring within square brackets, including the brackets.
    Example: "Hello [world]" becomes "Hello ".
    """
    return re.sub(r'\[.*?\]', '', text).strip()

def normalize_spaces(text):
    """
    Replaces multiple consecutive whitespace characters with a single space.
    Example: "Hello   world" becomes "Hello world".
    """
    return re.sub(r'\s+', ' ', text)

def xml_to_csv(xml_content, output_filename):
    root = ET.fromstring(xml_content)

    with open(output_filename, 'w', encoding='utf-8') as file:
        for segment in root.findall('segment'):
            start_elem = segment.find('start')
            end_elem = segment.find('end')
            text_elem = segment.find('text')

            if start_elem is None or end_elem is None or text_elem is None:
                continue

            start = start_elem.text if start_elem.text else ''
            end = end_elem.text if end_elem.text else ''
            text = text_elem.text if text_elem.text else ''

            if text:
                filtered_text = remove_bracketed_text(text)
                normalized_text = normalize_spaces(filtered_text)
            else:
                normalized_text = ''

            file.write(f"{start}\t{end}\t{normalized_text}\n")

def main():
    current_dir = os.getcwd()
    xml_files = [file for file in os.listdir(current_dir) if file.endswith('.xml')]

    for xml in xml_files:
        xml_path = os.path.join(current_dir, xml)
        try:
            with open(xml_path, 'r', encoding='utf-8') as file:
                xml_content = file.read()
            output_filename = xml.replace('.xml', '.txt')
            xml_to_csv(xml_content, output_filename)
        except Exception as e:
            print(f"Failed to process '{xml}': {e}")

    print("Conversion completed successfully.")

if __name__ == "__main__":
    main()
