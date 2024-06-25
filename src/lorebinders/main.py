from dotenv import load_dotenv

import build_lorebinder
import user_input


def main():
    work_base_dir = "work"
    book_dict = user_input.get_book()
    build_lorebinder.start(book_dict, work_base_dir)


if __name__ == "__main__":
    load_dotenv()
    main()
