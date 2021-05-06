from .. import state


def create(window, client):
    num_groups = window.num_groups()
    target_group = num_groups - 1

    for group_num in range(0, num_groups):
        if group_num > 0 and not window.views_in_group(group_num):
            target_group = group_num
            break

    view_count = len(window.views_in_group(target_group))
    suffix = "" if view_count == 0 else f" ({view_count})"

    view = window.new_file()
    view.set_name(f"REPL · {client.namespace} · {client.host}:{client.port}{suffix}")
    view.settings().set("line_numbers", False)
    view.settings().set("gutter", False)
    view.settings().set("is_widget", True)
    view.settings().set("scroll_past_end", False)
    view.settings().set("show_definitions", False)
    view.settings().set("translate_tabs_to_spaces", False)
    view.settings().set("auto_indent", False)
    view.settings().set("smart_indent", False)
    view.settings().set("spell_check", False)
    view.settings().set("indent_subsequent_lines", False)
    view.settings().set("detect_indentation", False)
    view.settings().set("auto_complete", False)
    view.settings().set("tutkain_repl_output_view", True)
    view.settings().set("tutkain_repl_host", client.host)
    view.settings().set("tutkain_repl_port", client.port)
    view.settings().set("result_file_regex", r"""\s*\[.+?\"(.+?)" (\d+)\]""")
    view.set_read_only(True)
    view.set_scratch(True)

    if client.bare:
        view.assign_syntax("Packages/Text/Plain Text.tmLanguage")
    else:
        view.assign_syntax("REPL (Tutkain).sublime-syntax")

    window.set_view_index(view, target_group, view_count)

    return view


def configure(window, client, view_id=None):
    view = view_id and next(
        filter(lambda view: view.id() == view_id, window.views()),
        None,
    ) or create(window, client)

    state.set_view_client(view, client)
    state.set_repl_view(view)

    return view


def is_output_view(view):
    return view.settings().get("tutkain_repl_output_view")
