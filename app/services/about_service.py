from app.helpers import check_and_generate_build_info, read_build_info

# during application initialization, make sure the build_info file is current
check_and_generate_build_info()


def build_about_info() -> dict:
    return read_build_info()


__all__ = ["build_about_info"]