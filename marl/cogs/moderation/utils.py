import regex

moderation_roles = {
    regex.compile(r'mod(?:erator)?s?', regex.I),
    regex.compile(r'staffs?', regex.I),
    regex.compile(r'admin(?:istrator)?s?', regex.I),
}

def iter_with_permissions(roles, *, permission_value):
    for role in roles:
        if (role.permissions.value | permission_value) == role.permissions.value:
            yield role

def iter_without_permissions(roles, *, permission_value):
    for role in roles:
        if (role.permissions.value | permission_value) != role.permissions.value:
            yield role

def iter_muted(roles):
    yield from iter_without_permissions(roles, permission_value=1 << 11)
