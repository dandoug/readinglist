"""
This module provides an interface to manage book data, perform searches, and fetch details.

It imports services for handling book operations, performing searches by various criteria,
fetching product details from external sources, working with category information, and
building related about information. The __all__ list ensures that only the intended public
functions and services are made available for use by external modules.
"""
from app.services.book_service import (add_new_book, update_book, del_book, get_book_by_id,
                                       get_book_status, get_book_feedback, set_book_status,
                                       set_book_feedback, book_to_dict_with_status_and_feedback)
from app.services.search_service import (search_by_categories, search_by_author, search_by_title)
from app.services.asin_data_service import fetch_product_details
from app.services.category_service import get_category_bs_tree, id_to_fullpath
from app.services.about_service import build_about_info
from app.services.tag_service import (get_tags_for_user, get_or_create_tag, tag_book,
                                      find_tag_for_user, get_tags_and_colors, remove_tag_from_book,
                                      get_tags_for_user_with_colors)

__all__ = ["add_new_book", "update_book", "del_book", "get_book_by_id", "get_book_status",
           "get_book_feedback", "set_book_status", "set_book_feedback",
           "book_to_dict_with_status_and_feedback",
           "search_by_categories", "search_by_author", "search_by_title",
           "fetch_product_details", "get_category_bs_tree", "id_to_fullpath",
           "build_about_info", "find_tag_for_user", "get_tags_for_user", "get_or_create_tag",
           "tag_book", "get_tags_and_colors", "remove_tag_from_book", "get_tags_for_user_with_colors"]
