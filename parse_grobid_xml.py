import os
from bs4 import BeautifulSoup
from collections import OrderedDict
from pprint import pprint


def get_xml_tag(soup, tag_str, n=1, allow_multiple=True):
    resultset = soup.find_all(tag_str)
    n_results = len(resultset)
    if n_results == n:
        return resultset[0]
    else:
        raise ValueError(f"Expected N={n} results, got {len(resultset)} results: {resultset}")
        return resultset[0]


def process_author(author):
    author_dict = {}
    forename_list = []
    surname_list = []
    for name in author.find_all('forename'):
        forename_list.append(name.string)

    for name in author.find_all('surname'):
        surname_list.append(name.string)

    author_dict["forename"] = " ".join(forename_list)
    author_dict["surname"] = " ".join(surname_list)
    try:
        author_dict["email"] = get_xml_tag(author, "email").string
        author_dict["org"] = get_xml_tag(author, "orgname").string
    except ValueError:
        pass

    return author_dict


def sanitize(s, default=""):
    if s is not None:
        return s
    else:
        return default


def string_2_ssml(s):
    return s


def parse_grobid_xml_file(xml_file):
    paper_dict = OrderedDict()
    with open(xml_file, 'r', encoding="utf-8") as file_handle:

        soup = BeautifulSoup(file_handle.read(), "xml")
        print("-" * 80)
        print(soup.prettify())
        print("-" * 80)

        # Title
        titlestmt = get_xml_tag(soup, 'titleStmt')
        title = get_xml_tag(titlestmt, 'title')
        paper_dict['title'] = title.string

        # Abstract
        abstract = get_xml_tag(soup, 'abstract')
        p = get_xml_tag(abstract, 'p')
        paper_dict['abstract'] = p.string

        # Authors
        author_list = []
        source = get_xml_tag(soup, 'sourceDesc')
        authors = source.find_all('author')
        for a in authors:
            author_list.append(process_author(a))
        paper_dict['authors'] = author_list

        # References
        # <biblStruct xml:id="b0">
        ref_dict = {}
        bib_list = get_xml_tag(soup, 'listBibl')
        # print("ListBibliography:", bib_list)
        for bib in bib_list.find_all('biblStruct'):
            # Get Reference Title
            ref_title = bib.find('title').string
            if ref_title is None:
                ref_title = bib.find('note').string
                if ref_title is None:
                    ref_title = "No Reference Title Found"

            # Add Reference
            try:
                bib_id = bib['xml:id']
                ref_dict[bib_id] = ref_title
            except KeyError:
                pass

        pprint(ref_dict)
        pprint(paper_dict)

        # Sections
        print("Gathering Sections!")
        body = get_xml_tag(soup, 'body')

        def get_section_content(div):


        for div in body.find_all('div'):
            head = get_xml_tag(div, 'head')
            head_n = sanitize(head['n'], "")
            head_str = sanitize(head.string, "Unnamed Section")
            section_header = f"{head_n} {head_str}"
            print("\nSection Header: ", section_header)

            readable_content = []
            for child in div.descendants:
                name = child.name
                if name == 'p':
                    print("Full:", child)
                    print("Contents:", child.contents)
                    print("Descendants:", list(child.descendants))
                    readable_content.append(sanitize(child.string, ""))
                elif name == 'ref':
                    print("\t", name, child)
                    readable_content.append("*")

            print("Readable Content:", " ".join(readable_content))

        quit()

    pprint(paper_dict)


if __name__ == '__main__':
    input_path = "resources/test_docs"
    for root, _, list_of_files in os.walk(input_path):
        for file in list_of_files:
            if file.endswith(".tei.xml"):
                xml_file_path = os.path.join(root, file)
                print("\n\nProcessing File: {}".format(xml_file_path))
                parsed_doc = parse_grobid_xml_file(xml_file_path)
