from __future__ import absolute_import  # Python 2 only

from compressor.contrib.jinja2ext import CompressorExtension
from django.contrib.humanize.templatetags import humanize
from django.contrib.staticfiles.storage import staticfiles_storage
from django.template import defaultfilters
from django.urls import reverse
from markdown_deux.templatetags import markdown_deux_tags
import re

from jinja2 import ChainableUndefined, Environment, Markup, ext, nodes


def environment(**options):
    options.setdefault("extensions", []).extend((
        CompressorExtension,
        SpacelessExtension,
    ))
    options["undefined"] = ChainableUndefined
    env = Environment(**options)
    env.globals.update({
        'static': staticfiles_storage.url,
        'url': reverse,
    })
    env.filters.update({
        "date": defaultfilters.date,
        "default_if_none": defaultfilters.default_if_none,
        "floatformat": defaultfilters.floatformat,
        "intcomma": humanize.intcomma,
        "linebreaks": defaultfilters.linebreaks_filter,
        "markdown": markdown_filter,
        "pluralize": defaultfilters.pluralize,
        "time": defaultfilters.time,
        "timesince": defaultfilters.timesince_filter,
        "timeuntil": defaultfilters.timeuntil_filter,
        "truncatewords": defaultfilters.truncatewords,
    })
    return env


def markdown_filter(*args, **kwargs):
    # if markdown_deux gets jinja2's Markup type as input, it double-escapes it.
    args = list(args)
    args[0] = unicode(args[0])
    return markdown_deux_tags.markdown_filter(*args, **kwargs)


class SpacelessExtension(ext.Extension):
    tags = {"spaceless"}

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        body = parser.parse_statements(["name:endspaceless"], drop_needle=True)
        return nodes.CallBlock(
            self.call_method("_remove_whitespace"), [], [], body
        ).set_lineno(lineno)

    def _remove_whitespace(self, caller):
        # Django's SpacelessNode first strips outer whitespace off the rendered
        # contents.
        body = caller().strip()

        # Then it calls django.utils.html.strip_spaces_between_tags, which does
        # roughly the following regex substitution. However, in Jinja2, `body`
        # may be an instance of `Markup`, which auto-escapes arguments to
        # methods like `replace`. So we need to ensure that the replacement
        # does not get escaped, by tagging it as `Markup`. This is okay even if
        # `body` is just text, because `Markup` is also a subclass of the
        # appropriate text type.
        return re.sub(r">\s+<", Markup("><"), body)
