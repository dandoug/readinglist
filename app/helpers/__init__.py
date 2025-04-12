"""
This module acts as the central aggregator for utility functions, global registrations, 
and build information management tasks within the project.

Imports:
- `utilities`: Provides multiple utility functions such as rendering icons, building
  search URLs, computing next URLs, and parsing URLs.
- `globals`: Contains functionality for registering global variables.
- `buildinfo`: Manages the build information such as reading, writing, generating, and
  removing build info files.

Exports:
- All imported functions, classes, or constants are included under __all__ for controlled
  module-level visibility.
"""
from app.helpers.utilities import (build_library_search_urls, render_icon, PLACEHOLDER,  # pylint: disable=unused-import
                                   compute_next_url, parse_url)  # pylint: disable=unused-import
from app.helpers.globals import register_globals  # pylint: disable=unused-import
from app.helpers.buildinfo import (check_and_generate_build_info, read_build_info,  # pylint: disable=unused-import
                                   write_empty_build_info, remove_build_info,  # pylint: disable=unused-import
                                   BUILD_INFO_FILE)  # pylint: disable=unused-import


_all__ = ["build_library_search_urls", "render_icon", "PLACEHOLDER", "compute_next_url",
          "parse_url", "register_globals", "check_and_generate_build_info", "read_build_info",
          "write_empty_build_info", "remove_build_info", "BUILD_INFO_FILE"]
