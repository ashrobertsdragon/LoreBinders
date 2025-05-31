import lorebinders.build_lorebinder as builder
import lorebinders.user_input as user_input


def main() -> None:
    """Main entry point for the LoreBinders application."""
    work_base_dir = "work"
    book_dict = user_input.get_book()
    builder.start(book_dict, work_base_dir)


if __name__ == "__main__":
    main()
