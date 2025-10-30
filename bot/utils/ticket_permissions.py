from discord import PermissionOverwrite


def get_moderator_permissions() -> PermissionOverwrite:
    return PermissionOverwrite(
        add_reactions=True,
        view_channel=True,
        send_messages=True,
        embed_links=True,
        attach_files=True,
        read_message_history=True,
        mention_everyone=False,
        manage_permissions=False,
        create_public_threads=False,
        create_private_threads=False,
        manage_messages=False,
    )


def get_member_permissions() -> PermissionOverwrite:
    return PermissionOverwrite(
        add_reactions=True,
        view_channel=True,
        send_messages=True,
        embed_links=True,
        attach_files=True,
        read_message_history=True,
        mention_everyone=False,
        manage_permissions=False,
        create_public_threads=False,
        create_private_threads=False,
        manage_messages=False,
    )


def get_externe_member_permissions() -> PermissionOverwrite:
    return PermissionOverwrite(
        add_reactions=True,
        view_channel=True,
        send_messages=True,
        embed_links=True,
        attach_files=True,
        read_message_history=True,
        mention_everyone=False,
        manage_permissions=False,
        create_public_threads=False,
        create_private_threads=False,
        manage_messages=False,
    )


def get_default_role_permissions() -> PermissionOverwrite:
    return PermissionOverwrite(
        view_channel=False,
    )
