from dotenv import load_dotenv

from build_lorebinder import run
from user_input import get_book


def main():
    book_dict = get_book()
    run(book_dict)


if __name__ == "__main__":
    load_dotenv()
    main()
