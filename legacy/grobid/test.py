'''
Recursively apply GROBID to the PDF present in a file tree via the grobid client.
'''

import os

grobid = __import__('grobid-client')

if __name__ == "__main__":

    # Scheduling https://datatofish.com/python-script-windows-scheduler/
    # https://docs.docker.com/engine/security/rootless/

    input_path = "../resources/test_docs"
    output_path = "../resources/test_xmls"


    print("Starting Grobid Client")
    client = grobid.grobid_client(config_path="./config.json")

    print("Starting Dir Walk: ", input_path)
    if os.path.isdir(input_path):
        print("Yes it is a DIR!")
    else:
        print("Not a DIR")

    for input_dir, _, list_of_files in os.walk(input_path):
        print(input_dir, list_of_files)
        client.process(input=input_dir, output=output_path, n=1, service="processFulltextDocument",
                       generateIDs=True, consolidate_header=1, consolidate_citations=0, force=True,
                       teiCoordinates=True)

