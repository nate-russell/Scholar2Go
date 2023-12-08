import os, bs4
from bs4 import BeautifulSoup
from collections import OrderedDict
from pprint import pprint
import warnings


def get_xml_tag(soup, tag_str, n=1, strict=True):
    resultset = soup.find_all(tag_str)
    n_results = len(resultset)
    if n_results == n:
        return resultset[0]
    elif strict is False:
        return resultset
    else:
        raise ValueError(f"Expected N={n} results, got {len(resultset)} results: {resultset}")


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


def get_section_header(div):
    head = get_xml_tag(div, 'head')
    try:
        head_n = sanitize(head['n'], "")
    except KeyError:
        head_n = ""
    head_str = sanitize(head.string, "Unnamed Section")
    section_header = f"{head_n} {head_str}"
    return section_header


def get_reference_dict(soup):
    ref_dict = {}
    bib_list = get_xml_tag(soup, 'listBibl')
    for bib in bib_list.find_all('biblStruct'):
        # Get Reference Title
        ref_title = bib.find('title').string
        if ref_title is None:
            try:
                ref_title = bib.find('note').string
                if ref_title is None:
                    ref_title = "No Reference Title Found"
            except AttributeError:
                ref_title = "No Reference Title Found"

        # Add Reference
        try:
            bib_id = bib['xml:id']
            ref_dict[bib_id] = ref_title
        except KeyError:
            pass
    return ref_dict


def sanitize(s, default=""):
    if s is not None:
        return s
    else:
        return default


def string_2_ssml(s):
    return s


def extract_sections(div, ref_dict):
    section_header = get_section_header(div)
    print("\nSection Header: ", section_header)

    section_content = []
    inside_figure = False
    figures = OrderedDict()

    for index, sub_div in enumerate(div.children):
        tag = sub_div.name
        print(f"\n---{index}-{tag}---")

        # Figures and References Handling
        if tag == 'ref':
            ref_type = sub_div["type"]

            # Figure
            if ref_type == "figure":
                inside_figure = True
                figure_title = sub_div.string
                print(f"\nFigure~! : {figure_title}")

            # Bib Reference
            elif ref_type == "bibr":
                ref_id = sub_div['target']
                ref_title = ref_dict[ref_id]
                print(f"\nReference~! : {ref_title}")

        #  Paragraph handling
        elif tag == 'p':
            paragraph_content = process_paragraph(sub_div, ref_dict)
            paragraph_content.append("\n\n")

            # Deposit content into appropriate section
            if inside_figure:
                string_2_read = " ".join(paragraph_content)
                figures[figure_title] = string_2_read
                # Rule of thumb is to end a figure at end of the figure that proceeds it. Not fullproof =/
                inside_figure = False
            else:
                section_content.extend(paragraph_content)

        else:
            print(f"Uncategorized Tag: {tag} -> {sub_div}")

    return {section_header: section_content}


def process_paragraph(sub_div, ref_dict):
    print("\n\n----Processing Paragraph-------")
    paragraph_content = []
    for sub_p in sub_div.contents:

        # Tags
        if isinstance(sub_p, bs4.element.Tag):
            tag = sub_p.name

            # References
            if tag == 'ref':
                ref_type = sub_p["type"]

                # Figure
                if ref_type == "figure":
                    figure_title = sub_p.string
                    print(f"\nFigure~! : {figure_title}")
                    print("!!!!!!!!! NOT EXPECTING FIGURE MID PARAGRAPH !!!!!!!!!")

                # Bib Reference
                elif ref_type == "bibr":
                    try:
                        ref_id = sub_p['target'].strip('#')
                        ref_title = ref_dict[ref_id]
                        print(f"\nReference~! : {ref_title}")
                        paragraph_content.append(f", see reference {ref_title}, end reference, ")
                    except KeyError:
                        paragraph_content.append(sub_p.string)

            # Non Reference
            else:
                print("\nUnhandled TAG inside paragraph!!!")
                print("\tType:", type(sub_p), sub_p.name)
                print("\tFull:", sub_p)
                print("\tString:", sub_p.string)
                try:
                    print("\tContents:", sub_p.contents)
                except AttributeError:
                    print("\tNo Contents")

        # Navigable String
        elif isinstance(sub_p, bs4.element.NavigableString):
            s = sub_p.string
            assert s is not None
            print("")
            print(s)
            paragraph_content.append(s)

        else:
            print("\nUnhandled Element Type!!!!: ", type(sub_p))

    return paragraph_content


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
        abstract_paragraphs = get_xml_tag(abstract, 'p', strict=False)
        abstract_text = " ".join([p.string for p in abstract_paragraphs])
        paper_dict['abstract'] = abstract_text

        # Authors
        author_list = []
        source = get_xml_tag(soup, 'sourceDesc')
        authors = source.find_all('author')
        for a in authors:
            author_list.append(process_author(a))
        paper_dict['authors'] = author_list

        # References
        ref_dict = get_reference_dict(soup)

        # Sections
        body = get_xml_tag(soup, 'body')

        def get_section_content(div):


        for div in body.find_all('div'):
            section = extract_sections(div, ref_dict)
            for k, v in section.items():
                assert isinstance(v, list)
                v = " ".join(v)
                if len(v) > 0:
                    section_list.append({"header": k, "content": v})
                else:
                    warnings.warn(f"Section: {k} has no content!")
        paper_dict['sections'] = section_list

        return paper_dict


if __name__ == '__main__':
    input_path = "resources/test_xmls"
    for root, _, list_of_files in os.walk(input_path):
        for findex, file in enumerate(list_of_files):
            if file.endswith(".tei.xml") and findex > 0:
                xml_file_path = os.path.join(root, file)
                print("\n\nProcessing File: {}".format(xml_file_path))
                parsed_doc = parse_grobid_xml_file(xml_file_path)
