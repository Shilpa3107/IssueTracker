import csv
from io import StringIO
from typing import List, Dict

def parse_csv(file_contents: str) -> List[Dict]:
    """
    Parses CSV string and returns a list of dictionaries.
    Example CSV headers: title,description,assignee_email
    """
    reader = csv.DictReader(StringIO(file_contents))
    return [row for row in reader]
