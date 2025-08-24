import pathlib
import time
from bs4 import BeautifulSoup
import config
from pathlib import Path

def find_nested_components(xml_file):
    # Read the entire XML file
    with open(xml_file, 'r', encoding='utf-8') as file:
        xml_content = file.read()

    # Parse the XML content with BeautifulSoup using lxml
    print("Loading xml file ", xml_file)
    start_time = time.time()
    soup = BeautifulSoup(xml_content, 'lxml-xml')  # Use 'lxml-xml' for XML parsing
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time:.5f} seconds")
    print("Done loading")

    # Ensure the top tag is ClinicalDocument
    if soup.name != 'document':
        print('tag is ', soup.name)
    for tag in soup.children:
        print("sub: ", tag.name)
        if tag.name == 'ClinicalDocument':
            for t2 in tag.children:
                print("sub2: ", t2.name, type(t2))

    components = soup.find_all('component', recursive=False)
    components = soup.find_all('component', recursive=False)
    for component in components:
        print(component.name)
    # Use CSS selectors to find the desired pattern
    # nested_components = soup.select('component > section > entry > organizer > component')
    # nested_components = soup.select('ClinicalDocument > component > section > entry > organizer > component')
    #
    # return nested_components

# Usage example
if __name__ == "__main__":
    # xml_file_path = '/Users/tomhill/Downloads/AppleHealth/apple_health_export/fraction_cda.xml'
    # Later: I don't find fraction_cda.xml, I wonder if I made it from export_cda.xml, which is
    # 770,434,414 bytes, and would be slow. Yeah, it's taking a long time, but not this runs without error.
    file_part : pathlib.Path = Path('export_cda.xml')
    xml_file_path = config.source_dir / file_part

    import time

    # Replace with the path to your XML file
    start = time.perf_counter()
    find_nested_components(xml_file_path)
    end = time.perf_counter()

    elapsed = end - start
    print(f"find_nested_components('{xml_file_path}') took {elapsed:.4f} seconds")

    # Print out the results
    # for idx, component in enumerate(components):
    #     # print(f"Nested Component {idx + 1}: {component.prettify()}")
    #     print(f"Nested Component {idx + 1}: {component.tag}")