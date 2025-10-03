from discord import ApplicationContext, Member


def has_permission(permission_name: str):
    def predicate(ctx: ApplicationContext) -> bool:
        print(type(ctx))

        if not isinstance(ctx.author, Member):
            return False

        if getattr(ctx.author.guild_permissions, permission_name, False):
            return True
        else:
            return False

    return predicate
