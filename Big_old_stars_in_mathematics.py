import requests
from bs4 import BeautifulSoup
import re

# import networkx as nx
# import matplotlib.pyplot as plt
from graphviz import Digraph

IDs = [
    269646,
    305929,
    265132,
    266290,
    286674,
    275618,
    276060,
    303644,
    264716,
    269028,
]  # seed mathematicians ids


class Mathematician:
    def __init__(self, id, name, nationality, num_students, num_descendants):
        self.id = id
        self.name = name
        self.nationality = nationality
        self.num_students = num_students
        self.num_descendants = num_descendants
        self.advisor = None
        self.students = []

    @staticmethod
    def add_advisor(child, advisor):
        child.advisor = advisor
        advisor.students.append(child)

    @staticmethod
    def find_or_create_mathematician(
        mathematicians, id, name, nationality, num_students, num_descendants
    ):
        if id in mathematicians:
            mathematicians[id].name = name
            mathematicians[id].nationality = nationality
            mathematicians[id].num_students = num_students
            mathematicians[id].num_descendants = num_descendants
            return mathematicians[id]
        else:
            mathematician = Mathematician(
                id, name, nationality, num_students, num_descendants
            )
            mathematicians[id] = mathematician
            return mathematician


def find_advisor(soup):
    p_tags = soup.find_all("p")
    for p_tag in p_tags:
        if "advisor" in p_tag.text.lower():
            first_link = p_tag.find("a")
            if first_link:
                advisor_name = first_link.text
                advisor_link = first_link.get("href")
                match = re.search("id=(\d+)", advisor_link)
                advisor_id = match.group(1)
                print("Advisor ID:", advisor_id)
                # print("Advisor Name:", advisor_name)
                # print("Advisor Link:", advisor_link)
                return advisor_name, advisor_id
            else:
                return "", ""
    else:
        print("No <p> tag containing 'advisor' found.")


def find_me(soup):
    h2 = soup.find_all("h2")[0]
    return h2.text


def find_num_students_and_descendants(soup):
    matches_general = re.findall(r"(\d+) students and (\d+) descendants", soup.text)
    if matches_general:
        students_general, descendants_general = matches_general[0]
    else:
        students_general, descendants_general = None, None

    return students_general, descendants_general


def find_nationality(soup):
    target_div = soup.find(id="paddingWrapper").find_all("div", recursive=False)[1]
    nationalities = [img["alt"] for img in target_div.find_all("img")]
    if not nationalities:
        return "UNKNOWN"
    return nationalities[0].lower()


def make_soup(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    return soup


def get_html_content(id):
    url = f"https://genealogy.math.ndsu.nodak.edu/id.php?id={id}"
    html_content = requests.get(url).text
    return html_content


def get_mathematician_data(id):
    html_content = get_html_content(id)
    soup = make_soup(html_content)
    name = find_me(soup)
    first_advisor_name, first_advisor_id = find_advisor(soup)
    num_student, num_descendant = find_num_students_and_descendants(soup)
    nat = find_nationality(soup)
    return id, name, first_advisor_id, nat, num_student, num_descendant


def print_tree(mathematician, level=0):
    indent = " " * (level * 4)
    print(
        f"{indent}{mathematician.name} (ID: {mathematician.id}, Nationality: {mathematician.nationality})"
    )
    for student in mathematician.students:
        print_tree(student, level + 1)


def draw_tree(mathematicians):
    dot = Digraph(comment="Mathematicians Tree")

    for id, mathematician in mathematicians.items():
        str_id = str(id)
        label = f"{mathematician.name}\n{mathematician.nationality}\nStudents: {len(mathematician.students)}"
        dot.node(str_id, label)
        if mathematician.advisor:
            dot.edge(str(mathematician.advisor.id), str_id)
    dot.render("mathematicians_tree", view=True)


def main():
    mathematicians = {}
    for initID in IDs:
        curID = initID
        while True:
            curID, name, advisor_id, nat, num_student, num_descendant = (
                get_mathematician_data(curID)
            )
            mathematician = Mathematician.find_or_create_mathematician(
                mathematicians,
                curID,
                name,
                nat,
                num_student,
                num_descendant,
            )
            curID = advisor_id
            if not advisor_id:
                # found root
                print("ROOT FOUND")
                break
            if advisor_id not in mathematicians:
                advisor = Mathematician.find_or_create_mathematician(
                    mathematicians, advisor_id, "Unknown", "Unknown", None, None
                )
            else:
                advisor = mathematicians[advisor_id]
            Mathematician.add_advisor(mathematician, advisor)
    # root_mathematician = mathematicians["147797"]
    draw_tree(mathematicians)


if __name__ == "__main__":
    main()
