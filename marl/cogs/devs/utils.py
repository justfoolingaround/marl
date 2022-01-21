import regex

SITE_REQUESTS_TEMPLATE = """\
Listening to site requests on:
{}

Currently caught requests: {}
Blacklisted requests: {}"""


URL_REGEX = regex.compile(r"(?:https?://)?((?:[@:%_\+~#=\w-]+?\.)+[@:%_\+~#=\w-]{2,})", flags=regex.I)
