from .util import ViewTestCase


class TestExpandSelectionCommand(ViewTestCase):
    def expand(self):
        self.view.window().run_command("tutkain_expand_selection")

    def shrink(self):
        self.view.window().run_command("soft_undo")

    def test_before_lparen(self):
        self.set_view_content("(foo)")
        self.set_selections((0, 0))
        self.expand()
        self.assertEquals("(foo)", self.selection(0))

    def test_after_lparen(self):
        self.set_view_content("(foo)")
        self.set_selections((1, 1))
        self.expand()
        self.assertEquals("foo", self.selection(0))

    def test_before_rparen(self):
        self.set_view_content("(foo)")
        self.set_selections((4, 4))
        self.expand()
        self.assertEquals("foo", self.selection(0))

    def test_after_rparen(self):
        self.set_view_content("(foo)")
        self.set_selections((6, 6))
        self.expand()
        self.assertEquals("(foo)", self.selection(0))

    def test_before_lbracket(self):
        self.set_view_content("[foo]")
        self.set_selections((0, 0))
        self.expand()
        self.assertEquals("[foo]", self.selection(0))

    def test_after_lbracket(self):
        self.set_view_content("[foo]")
        self.set_selections((1, 1))
        self.expand()
        self.assertEquals("foo", self.selection(0))

    def test_after_rbracket(self):
        self.set_view_content("[foo]")
        self.set_selections((6, 6))
        self.expand()
        self.assertEquals("[foo]", self.selection(0))

    def test_before_lcurly(self):
        self.set_view_content("{:a 1}")
        self.set_selections((0, 0))
        self.expand()
        self.assertEquals("{:a 1}", self.selection(0))

    def test_after_lcurly(self):
        self.set_view_content("{:a 1}")
        self.set_selections((1, 1))
        self.expand()
        self.assertEquals(":a", self.selection(0))

    def test_after_rcurly(self):
        self.set_view_content("{:a 1}")
        self.set_selections((7, 7))
        self.expand()
        self.assertEquals("{:a 1}", self.selection(0))

    def test_before_set(self):
        self.set_view_content("#{1}")
        self.set_selections((0, 0))
        self.expand()
        self.assertEquals("#{1}", self.selection(0))

    def test_between_set_hash_and_bracket(self):
        self.set_view_content("#{1}")
        self.set_selections((1, 1))
        self.expand()
        self.assertEquals("#{1}", self.selection(0))

    def test_between_on_symbol(self):
        self.set_view_content("(inc 1)")
        self.set_selections((2, 2))
        self.expand()
        self.assertEquals("inc", self.selection(0))

    def test_before_at(self):
        self.set_view_content("@(foo)")
        self.set_selections((0, 0))
        self.expand()
        self.assertEquals("@(foo)", self.selection(0))

    def test_after_at(self):
        self.set_view_content("@(foo)")
        self.set_selections((1, 1))
        self.expand()
        self.assertEquals("@(foo)", self.selection(0))

    def test_after_at_rparen(self):
        self.set_view_content("@(foo)")
        self.set_selections((6, 6))
        self.expand()
        self.assertEquals("@(foo)", self.selection(0))

    def test_before_quoted_list(self):
        self.set_view_content("'(foo)")
        self.set_selections((0, 0))
        self.expand()
        self.assertEquals("'(foo)", self.selection(0))

    def test_after_quoted_list(self):
        self.set_view_content("'(foo)")
        self.set_selections((6, 6))
        self.expand()
        self.assertEquals("'(foo)", self.selection(0))

    def test_nested(self):
        self.set_view_content("(foo (bar))")
        self.set_selections((5, 5))
        self.expand()
        self.assertEquals("(bar)", self.selection(0))
        self.expand()
        self.assertEquals("(foo (bar))", self.selection(0))

    def test_before_string(self):
        self.set_view_content('(a "b" c)')
        self.set_selections((3, 3))
        self.expand()
        self.assertEquals('"b"', self.selection(0))

    def test_meta(self):
        self.set_view_content("^{:foo true}")
        self.set_selections((0, 0))
        self.expand()
        self.assertEquals("^{:foo true}", self.selection(0))
        self.set_selections((12, 12))
        self.expand()
        self.assertEquals("^{:foo true}", self.selection(0))

        self.set_view_content("^:foo")
        self.set_selections((0, 0))
        self.expand()
        self.assertEquals("^:foo", self.selection(0))
        self.set_view_content("^:foo")
        self.set_selections((5, 5))
        self.expand()
        self.assertEquals("^:foo", self.selection(0))

    def test_numbers(self):
        self.set_view_content("0.2")
        self.set_selections((0, 0))
        self.expand()
        self.assertEquals("0.2", self.selection(0))
        self.set_view_content("0.2")
        self.set_selections((3, 3))
        self.expand()
        self.assertEquals("0.2", self.selection(0))
        self.set_view_content("1/2")
        self.set_selections((0, 0))
        self.expand()
        self.assertEquals("1/2", self.selection(0))
        self.set_selections((3, 3))
        self.expand()
        self.assertEquals("1/2", self.selection(0))

    def test_string_close_paren(self):
        self.set_view_content('(a "b")')
        self.set_selections((6, 6))
        self.expand()
        self.assertEquals('"b"', self.selection(0))

    def test_qualified_map(self):
        self.set_view_content("#:foo{:bar 1} #:foo/bar{:baz 1} #::foo{:bar 1}")
        self.set_selections((0, 0))
        self.expand()
        self.assertEquals("#:foo{:bar 1}", self.selection(0))
        self.set_selections((13, 13))
        self.expand()
        self.assertEquals("#:foo{:bar 1}", self.selection(0))
        self.set_selections((14, 14))
        self.expand()
        self.assertEquals("#:foo/bar{:baz 1}", self.selection(0))
        self.set_selections((32, 32))
        self.expand()
        self.assertEquals("#::foo{:bar 1}", self.selection(0))
        self.set_selections((46, 46))
        self.expand()
        self.assertEquals("#::foo{:bar 1}", self.selection(0))

    def test_list_head(self):
        self.set_view_content("(ns foo.bar)")
        self.set_selections((1, 1))
        self.expand()
        self.assertEquals("ns", self.selection(0))

    def test_special_form(self):
        self.set_view_content("(fn [foo])")
        self.set_selections((1, 1))
        self.expand()
        self.assertEquals("fn", self.selection(0))

    def test_empty_sexp(self):
        self.set_view_content("[]")
        self.set_selections((1, 1))
        self.expand()
        self.assertEquals("[]", self.selection(0))
        self.set_view_content("()")
        self.set_selections((1, 1))
        self.expand()
        self.assertEquals("()", self.selection(0))
        self.set_view_content("{}")
        self.set_selections((1, 1))
        self.expand()
        self.assertEquals("{}", self.selection(0))
        self.set_view_content("( )")
        self.set_selections((1, 1))
        self.expand()
        self.assertEquals(" ", self.selection(0))
        self.expand()
        self.assertEquals("( )", self.selection(0))
        self.expand()
        self.assertEquals("( )", self.selection(0))
        self.set_view_content("[ (  a  ) ]")
        self.set_selections((4, 4))
        self.expand()
        self.assertEquals("  a  ", self.selection(0))
        self.expand()
        self.assertEquals("(  a  )", self.selection(0))
        self.expand()
        self.assertEquals("[ (  a  ) ]", self.selection(0))

    def test_shrink(self):
        self.set_view_content("(a (b (c) d) e)")
        self.set_selections((7, 7))
        self.expand()
        self.assertEquals("c", self.selection(0))
        self.expand()
        self.assertEquals("(c)", self.selection(0))
        self.expand()
        self.assertEquals("(b (c) d)", self.selection(0))
        self.expand()
        self.assertEquals("(a (b (c) d) e)", self.selection(0))
        self.expand()
        self.assertEquals("(a (b (c) d) e)", self.selection(0))
        self.shrink()
        self.assertEquals("(b (c) d)", self.selection(0))
        self.shrink()
        self.assertEquals("(c)", self.selection(0))
        self.shrink()
        self.assertEquals("c", self.selection(0))
        self.shrink()
        self.assertEquals("", self.selection(0))
        self.shrink()
        self.assertEquals("", self.selection(0))

    def test_comment_after_open(self):
        self.set_view_content("[;;foo\n]")
        self.set_selections((0, 0))
        self.expand()
        self.assertEquals("[;;foo\n]", self.selection(0))
        self.set_selections((1, 1))
        self.expand()
        self.assertEquals(";;", self.selection(0))

    def test_issue_48(self):
        self.set_view_content("[state @state-ref]")
        self.set_selections((8, 8))
        self.expand()
        self.assertEquals("@state-ref", self.selection(0))
        self.expand()
        self.assertEquals("state @state-ref", self.selection(0))
        self.expand()
        self.assertEquals("[state @state-ref]", self.selection(0))

    def test_tagged_literal(self):
        self.set_view_content("(foo #bar/baz [:quux 1])")
        self.set_selections((5, 5))
        self.expand()
        self.assertEquals("#bar/baz", self.selection(0))
        self.expand()
        self.assertEquals("foo #bar/baz [:quux 1]", self.selection(0))
        self.expand()
        self.assertEquals("(foo #bar/baz [:quux 1])", self.selection(0))
