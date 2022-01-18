import regex

moderation_roles = {
    regex.compile(r'mod(?:erator)?s?', regex.I),
    regex.compile(r'staffs?', regex.I),
    regex.compile(r'admin(?:istrator)?s?', regex.I),
}


URL_REGEX = regex.compile(r"(?:https?://)?((?:[@:%_\+~#=\w-]+?\.)+[@:%_\+~#=\w-]{2,})", flags=regex.I)

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

def iter_likely_staffs(roles):
    for role in roles:
        for moderation_role_name in moderation_roles:
            if moderation_role_name.match(role.name):
                yield role
                break


def iter_every_text_segment(message):

    yield message.content

    for embed in message.embeds:

        if embed.title:
            yield embed.title

        if embed.description:
            yield embed.description

        if embed.author.name:
            yield embed.author.name
        
        if embed.footer.text:
            yield embed.footer.text
        
        if embed.url:
            yield embed.url

        for field in embed.fields:
            
            if field.name:
                yield field.name

            if field.value:
                yield field.value
