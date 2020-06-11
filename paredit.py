import re
import sublime

from . import sexp
from . import indent


def iterate(view):
    '''
    Iterate over each region in all selections.

    After iteration, add all selections saved by consumers.
    '''
    new_regions = []
    selections = view.sel()

    for region in selections:
        yield region, new_regions

    if new_regions:
        selections.clear()
        for region in new_regions:
            selections.add(region)


def open_bracket(view, edit, open_bracket):
    close_bracket = sexp.OPEN[open_bracket]

    for region, sel in iterate(view):
        begin = region.begin()
        end = region.end() + 1
        view.insert(edit, begin, open_bracket)

        if not sexp.ignore(view, begin):
            view.insert(edit, end, close_bracket)
            new_end = end + 1
            sel.append(sublime.Region(begin + 1, begin + 1))

            # If the character that follows the close bracket we just inserted
            # is a whitespace character, the NUL character, or a close bracket,
            # don't insert a whitespace. Otherwise, do.
            if re.match(r'[^\s\x00\)\]\}]', view.substr(new_end)):
                view.insert(edit, new_end, ' ')


def close_bracket(view, edit, close_bracket):
    for region, sel in iterate(view):
        begin = region.begin()
        end = region.end()

        if sexp.ignore(view, begin):
            view.insert(edit, begin, close_bracket)
        else:
            close_bracket_begin = view.find_by_class(
                begin,
                True,
                sublime.CLASS_PUNCTUATION_END
            ) - 1

            # Get the region that starts at the current point and ends before the
            # close bracket and trim the whitespace on its right.
            replacee = sublime.Region(begin, close_bracket_begin)
            view.replace(edit, replacee, view.substr(replacee).rstrip())
            sel.append(sublime.Region(begin + 1, end + 1))


def double_quote(view, edit):
    for region, sel in iterate(view):
        begin = region.begin()
        end = region.end()

        if view.substr(end) == '"':
            sel.append(sublime.Region(end + 1, end + 1))
        elif sexp.inside_string(view, begin):
            view.insert(edit, begin, '\\"')
        elif sexp.inside_comment(view, begin):
            view.insert(edit, begin, '"')
        else:
            view.insert(edit, begin, '""')
            sel.append(sublime.Region(end + 1, end + 1))


def has_null_character(view, point):
    return view.substr(point) == '\x00'


def extract_scope(view, point):
    '''Like View.extract_scope(), but less fussy.

    For example, take this Clojure keyword:

        :foo

    At point 0, the scope name is:

        'source.clojure constant.other.keyword.clojure punctuation.definition.keyword.clojure '

    At point 1, the scope name is:

        'source.clojure constant.other.keyword.clojure '

    View.extract_scope() considers them different scopes, even though the second part of the scope
    name (constant.other.keyword.clojure) is the same.

    This function considers two adjacent points as having the same scope if the second part of the
    scope name is the same.
    '''
    if sexp.ignore(view, point):
        return None

    scope_name = view.scope_name(point)
    scopes = scope_name.split()

    try:
        selector = scopes[1]
    except IndexError:
        # If this point has a single scope name (in practice, 'source.clojure'), there's no way we
        # can know the extent of the syntax scope of this point, so we bail out.
        return None

    max_size = view.size()
    begin = end = point

    while begin >= 1:
        if has_null_character(view, begin) or (
            not view.match_selector(begin - 1, selector) and view.match_selector(begin, selector)
        ):
            break
        else:
            begin -= 1

    while end <= max_size:
        if has_null_character(view, end) or (
            view.match_selector(end - 1, selector) and not view.match_selector(end, selector)
        ):
            break
        else:
            end += 1

    return sublime.Region(begin, end)


def is_insignificant(view, point):
    return re.match(r'[\s,]', view.substr(point))


def non_number_word(view, point):
    return re.match(r'\w', view.substr(point)) and not re.match(r'\d', view.substr(point))


def find_next_element(view, point):
    max_size = view.size()

    while point < max_size:
        if is_insignificant(view, point) or sexp.is_next_to_close(view, point):
            point += 1
        elif sexp.is_next_to_open(view, point):
            return sexp.innermost(view, point).extent()
        else:
            scope = extract_scope(view, point)

            if scope:
                return scope
            elif non_number_word(view, point):
                return view.word(point)
            else:
                return None


def find_previous_element(view, point):
    while point >= 0:
        if is_insignificant(view, point - 1):
            point -= 1
        elif not sexp.ignore(view, point) and view.substr(point - 1) in sexp.CLOSE:
            return sexp.innermost(view, point).extent()
        else:
            scope = extract_scope(view, point - 1)

            if scope:
                return scope
            elif non_number_word(view, point - 1):
                return view.word(point)
            else:
                return None


def forward_slurp(view, edit):
    for region, sel in iterate(view):
        element = None

        # TODO: It would be faster just to find close brackets instead of the entire sexp.
        for s in sexp.walk_outward(view, region.begin()):
            element = find_next_element(view, s.close.end())
            if element:
                break

        if element:
            close_begin = view.find_by_class(
                element.begin(),
                False,
                sublime.CLASS_PUNCTUATION_END
            ) - 1

            close_end = close_begin + 1

            # Save cursor position so we can restore it after slurping.
            sel.append(region)
            # Save close char.
            char = view.substr(close_begin)
            # Put a copy of the close char we found after the element.
            view.insert(edit, element.end(), char)
            # Erase the close char we copied.
            view.erase(edit, sublime.Region(close_begin, close_end))
            # # If we slurped a sexp, indent it.
            view.run_command('tutkain_indent_region', {'scope': 'innermost', 'prune': True})


def forward_barf(view, edit):
    for region, sel in iterate(view):
        sel.append(region)

        innermost = sexp.innermost(view, region.begin(), edge=False)

        if innermost:
            point = innermost.close.begin()
            element = find_previous_element(view, point)

            if element:
                char = view.substr(point)
                view.erase(edit, sublime.Region(point, point + 1))
                insert_point = max(element.begin() - 1, innermost.open.end())
                view.insert(edit, insert_point, char)

                # If we inserted the close char next to the open char, add a
                # space after the new close char.
                if insert_point - 1 == innermost.open.begin():
                    view.insert(edit, insert_point + 1, ' ')

                view.run_command('tutkain_indent_region', {'scope': 'innermost', 'prune': True})


def adjacent_element_direction(view, point):
    if not sexp.ignore(view, point) and re.match(r'[^\s,\)\]\}\x00]', view.substr(point)):
        return 1
    elif not sexp.ignore(view, point - 1) and re.match(r'[^\s,\(\[\{\x00]', view.substr(point - 1)):
        return -1
    else:
        return 0


def wrap_bracket(view, edit, open_bracket):
    close_bracket = sexp.OPEN[open_bracket]

    for region, sel in iterate(view):
        point = region.begin()
        direction = adjacent_element_direction(view, point)

        if direction == 1:
            element = find_next_element(view, point)
        elif direction == -1:
            element = find_previous_element(view, point)
        else:
            element = sublime.Region(point, point)
            sel.append(sublime.Region(point + 1, point + 1))

        view.insert(edit, element.end(), close_bracket)
        view.insert(edit, element.begin(), open_bracket)


def forward_delete(view, edit):
    for region, sel in iterate(view):
        if not region.empty():
            view.erase(edit, region)
        else:
            point = region.begin()
            innermost = sexp.innermost(view, point, edge=True)

            if view.match_selector(point, 'constant.character.escape'):
                view.erase(edit, sublime.Region(point, point + 2))
            elif not innermost:
                view.erase(edit, sublime.Region(point, point + 1))
            elif innermost.is_empty() and innermost.contains(point):
                view.erase(edit, innermost.extent())
            elif point == innermost.open.begin() or point == innermost.close.begin():
                sel.append(point + 1)
            else:
                view.erase(edit, sublime.Region(point, point + 1))


def backward_delete(view, edit):
    for region, sel in iterate(view):
        if not region.empty():
            view.erase(edit, region)
        else:
            point = region.begin()
            innermost = sexp.innermost(view, point, edge=True)

            if view.match_selector(point - 1, 'constant.character.escape'):
                view.erase(edit, sublime.Region(point - 2, point))
            elif not innermost:
                view.erase(edit, sublime.Region(point - 1, point))
            elif innermost.is_empty() and innermost.contains(point):
                view.erase(edit, innermost.extent())
            elif (point == innermost.open.end() or point == innermost.close.end() or
                  (not sexp.ignore(view, point) and view.substr(point - 1) in sexp.CLOSE)):
                sel.append(point - 1)
            else:
                view.erase(edit, sublime.Region(point - 1, point))


def raise_sexp(view, edit):
    for region, sel in iterate(view):
        point = region.begin()

        if not sexp.ignore(view, point):
            innermost = sexp.innermost(view, point, edge=False)
            element = find_next_element(view, point)
            view.replace(edit, innermost.extent(), view.substr(element))
            view.run_command('tutkain_indent_region', {'scope': 'innermost', 'prune': True})


def splice_sexp(view, edit):
    for region, _ in iterate(view):
        point = region.begin()

        innermost = sexp.innermost(view, point, edge=False)

        # Erase the close character
        view.erase(edit, innermost.close)
        # Erase one or more open characters
        view.erase(edit, innermost.open)
        view.run_command('tutkain_indent_region', {'scope': 'innermost', 'prune': True})


def comment_dwim(view, edit):
    for region, sel in iterate(view):
        line = view.line(region.begin())
        n = view.insert(edit, line.end(), ' ; ')
        sel.append(line.end() + n)


def kill(view, edit):
    for region, _ in iterate(view):
        # What should kill do with a non-empty selection?
        point = region.begin()

        innermost = sexp.innermost(view, point, edge=True)

        # Cursive only deletes until newline, we delete the contents of the sexp regardless of
        # newlines. Not sure which is right, but this is easier to implement and makes more sense
        # to me.
        if point == innermost.open.begin() or point == innermost.close.end():
            view.erase(edit, innermost.extent())
        elif point == innermost.open.end() or point == innermost.close.begin():
            view.erase(edit, sublime.Region(innermost.open.end(), innermost.close.begin()))
