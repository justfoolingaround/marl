"""
JSON is not a db? lol ok.
"""

import ujson

class MarlDatabase():
    
    db: dict = dict()

    def __init__(self, io_readable):
        self.io_readable = io_readable
        self.load()


    def get_guilds(self):
        return self.db.setdefault('guilds', dict())

    def get_guild(self, guild_id: int):
        return self.get_guilds().setdefault(str(guild_id), dict())
    
    def get_guild_users(self, guild_id: int):
        return self.get_guild(str(guild_id)).setdefault('users', dict())

    def get_guild_user(self, guild_id, user_id):
        return self.get_guild_users(str(guild_id)).setdefault(str(user_id), dict())

    def get_guild_user_reminders(self, guild_id, user_id):
        return self.get_guild_user(str(guild_id), str(user_id)).setdefault('reminders', list())

    def get_guild_tags(self, guild_id):
        return self.get_guild(str(guild_id)).setdefault('tags', list())

    def get_guild_settings(self, guild_id):
        return self.get_guild(str(guild_id)).setdefault('settings', dict())

    def get_guild_prefix(self, guild_id):
        return self.get_guild_settings(str(guild_id)).setdefault('command_prefix', None)

    def get_guild_site_requests(self, guild_id):
        return self.get_guild(str(guild_id)).setdefault('site_requests', dict())

    def get_guild_bug_reports(self, guild_id):
        return self.get_guild(str(guild_id)).setdefault('bug_reports', dict())

    def get_guild_mutes(self, guild_id):
        return self.get_guild(str(guild_id)).setdefault('mutes', list())

    def get_guild_bans(self, guild_id):
        return self.get_guild(str(guild_id)).setdefault('bans', list())

    def get_global(self):
        return self.db.setdefault('global', dict())

    def get_global_blacklist(self):
        return self.get_global().setdefault('blacklist', dict())

    def get_global_blacklist_bool(self):
        return self.get_global_blacklist().setdefault('inverse', False)

    def get_global_blacklist_users(self):
        return self.get_global_blacklist().setdefault('users', list())
    
    def get_global_blacklist_guilds(self):
        return self.get_global_blacklist().setdefault('guilds', list())
    
    def get_global_trusted(self):
        return self.get_global().setdefault('trusted', dict())
    
    def get_global_trusted_users(self):
        return self.get_global_trusted().setdefault('users', list())
    
    def get_global_trusted_guilds(self):
        return self.get_global_trusted().setdefault('guilds', list())
    
    def get_global_administrators(self):
        return self.get_global_trusted().setdefault('administrators', list())
    
    def get_global_divine(self):
        return self.get_global().setdefault('divine', dict())
    
    def get_global_divine_users(self):
        return self.get_global_divine().setdefault('users', list())
    
    def get_global_divine_guilds(self):
        return self.get_global_divine().setdefault('guilds', list())
    
    def get_global_tags(self):
        return self.get_global().setdefault('tags', list())
    
    def get_global_reminders(self):
        return self.get_global().setdefault('reminders', list())

    def remove_guild(self, guild_id):
        guilds = self.get_guilds()

        if guild_id in guilds:
            del guilds[guild_id]

    def update_guild_user(self, guild_id, user_id, update_values):
        self.get_guild_users(str(guild_id)).setdefault(str(user_id), dict()).update(update_values)

    def update_guild(self, guild_id, update_values):
        self.get_guilds().setdefault(str(guild_id), dict()).update(update_values)

    def guild_settings_append(self, guild_id, key, appendlet):
        self.get_guild_settings(str(guild_id)).setdefault(key, []).append(appendlet)

    def guild_settings_remove(self, guild_id, key, predicate):
        settings = self.get_guild_settings(str(guild_id))[key]

        for _ in settings:
            if predicate(_):
                settings.remove(_)

        
    def guild_mute(self, guild_id, user_id, reason, expiry):
        self.guild_settings_append(str(guild_id), 'mutes', {
                'user': str(user_id),
                'reason': reason,
                'expiry': expiry
            })

    def guild_unmute(self, guild_id, user_id):
        self.guild_settings_remove(str(guild_id), 'mutes', lambda _: _.get('user') == user_id)

    def guild_ban(self, guild_id, user_id, reason, expiry):
        self.guild_settings_append(str(guild_id), 'bans', {
                'user': str(user_id),
                'reason': reason,
                'expiry': expiry
            })

    def guild_unban(self, guild_id, user_id):
        self.guild_settings_remove(str(guild_id), 'bans', lambda _: _.get('user') == user_id)


    def get_global_snowflake_list(self, type_of, is_user=True):
        
        assert type_of in ['blacklist', 'trusted', 'divine', 'administrator']

        if type_of == 'blacklist':
            if is_user:
                return self.get_global_blacklist_users()
            else:
                return self.get_global_blacklist_guilds()
            
        else:
            if type_of == 'trusted':
                if is_user:
                    return self.get_global_trusted_users()
                else:
                    return self.get_global_trusted_guilds()
            else:
                if type_of == 'divine':
                    if is_user:
                        return self.get_global_divine_users()
                    else:
                        return self.get_global_divine_guilds()
                else:
                    return self.get_global_administrators()
    
    def append_to_global_snowflake(self, type_of, is_user, snowflake):
        _ = self.get_global_snowflake_list(type_of, is_user)

        if snowflake not in _:
            _.append(snowflake)

    def remove_from_global_snowflake(self, type_of, is_user, snowflake):
        _ = self.get_global_snowflake_list(type_of, is_user)

        if snowflake not in _:
            _.remove(snowflake)

    def toggle_blacklist(self):
        blacklist = self.get_global_blacklist()
        state = self.get_global_blacklist_bool()
        blacklist.update({'inverse': not state})
        return state

    def global_settings_append(self, key, appendlet):
        self.get_global().setdefault(key, list()).append(appendlet)

    def load(self):
        with open(self.io_readable, 'r') as json_db:
            self.db = ujson.load(json_db)

    def save(self):
        with open(self.io_readable, 'w') as db_file:
            ujson.dump(self.db, db_file, indent=4)
