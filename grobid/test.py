'''
Recursively apply GROBID to the PDF present in a file tree via the grobid client.
'''

import os

grobid = __import__('grobid-client')

if __name__ == "__main__":

    # Scheduling https://datatofish.com/python-script-windows-scheduler/
    # https://docs.docker.com/engine/security/rootless/

    print("Starting Grobid Client")
    client = grobid.grobid_client(config_path="./config.json")
    input_path = "../resources/test_docs"
    print("Starting Dir Walk: ", input_path)
    if os.path.isdir(input_path):
        print("Yes it is a DIR!")
    else:
        print("Not a DIR")

    for root, _, list_of_files in os.walk(input_path):
        print(root, list_of_files)
        client.process(root, root, 1, "processFulltextDocument", False, 1, 0, True, False)
