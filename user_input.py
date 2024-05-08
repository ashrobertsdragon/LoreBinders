import os

def get_book() -> dict:
    title: str = input("Enter book title")
    author: str = input("Enter author name")
    book: str = input("Enter the path to the ebook to process")
    path_parts: str = book.split("/") if "/" in book else book.split("\\")
    book_path: str = os.path.join(path_parts)
    return {
        "title": title,
        "author": author,
        "book_file": book_path
    }
    