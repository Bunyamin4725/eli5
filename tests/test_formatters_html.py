import re

import pytest
from sklearn.datasets import make_regression
from sklearn.linear_model import LinearRegression

from eli5.base import WeightedSpans
from eli5 import explain_weights_sklearn, explain_prediction_sklearn
from eli5.formatters import (
    format_as_text, format_as_html, format_html_styles, FormattedFeatureName)
from eli5.formatters.html import (
    _format_unhashed_feature, render_weighted_spans, _format_single_feature,
    _format_feature, _remaining_weight_color, _weight_color)
from .utils import write_html


def test_render_styles():
    styles = format_html_styles()
    assert styles.strip().startswith('<style')


def format_unhashed_feature(feature, weight=1, hl_spaces=True):
    return _format_unhashed_feature(feature, weight=weight, hl_spaces=hl_spaces)


def format_feature(feature, weight=1, hl_spaces=True):
    return _format_feature(feature, weight=weight, hl_spaces=hl_spaces)


def format_single_feature(feature, weight=1, hl_spaces=True):
    return _format_single_feature(feature, weight=weight, hl_spaces=hl_spaces)


def test_format_unhashed_feature():
    assert format_unhashed_feature([]) == ''
    assert format_unhashed_feature([{'name': 'foo', 'sign': 1}]) == 'foo'
    assert format_unhashed_feature([{'name': 'foo', 'sign': -1}]) == '(-)foo'
    assert format_unhashed_feature([
        {'name': 'foo', 'sign': 1},
        {'name': 'bar', 'sign': -1}
        ]) == 'foo <span title="(-)bar">&hellip;</span>'
    assert format_unhashed_feature([
        {'name': 'foo', 'sign': 1},
        {'name': 'bar', 'sign': -1},
        {'name': 'boo', 'sign': 1},
        ]) == 'foo <span title="(-)bar\nboo">&hellip;</span>'


def test_format_formatted_feature():
    assert format_feature(FormattedFeatureName('a b')) == 'a b'
    assert format_feature('a b') != 'a b'
    assert format_feature('a b') == format_single_feature('a b')


def test_format_single_feature():
    assert format_single_feature('a') == 'a'
    assert format_single_feature('<>') == '&lt;&gt;'
    assert format_single_feature('aa bb') == (
        'aa'
        '<span '
        'style="background-color: hsl(120, 80%, 70%); margin: 0 0.1em 0 0.1em" '
        'title="A space symbol">'
        '&emsp;'
        '</span>'
        'bb')
    assert format_single_feature('  aa bb ', weight=-1) == (
        '<span '
        'style="background-color: hsl(0, 80%, 70%); margin: 0 0.1em 0 0" '
        'title="2 space symbols">'
        '&emsp;'
        '&emsp;'
        '</span>'
        'aa'
        '<span '
        'style="background-color: hsl(0, 80%, 70%); margin: 0 0.1em 0 0.1em" '
        'title="A space symbol">'
        '&emsp;'
        '</span>'
        'bb'
        '<span '
        'style="background-color: hsl(0, 80%, 70%); margin: 0 0 0 0.1em" '
        'title="A space symbol">'
        '&emsp;'
        '</span>'
    )


def test_render_weighted_spans_word():
    weighted_spans = WeightedSpans(
        analyzer='word',
        document='i see: a leaning lemon tree',
        weighted_spans=[
            ('see', [(2, 5)], 0.2),
            ('tree', [(23, 27)], -0.6),
            ('leaning lemon', [(9, 16), (17, 22)], 0.5),
            ('lemon tree', [(17, 22), (23, 27)], 0.8)],
    )
    s = render_weighted_spans(weighted_spans)
    assert s.startswith(
        '<span style="opacity: 0.80">i</span>'
        '<span style="opacity: 0.80"> </span>'
        '<span'
        ' style="background-color: hsl(120, 100.00%, 89.21%); opacity: 0.83"'
        ' title="0.200">s</span>'
    )
    s_without_styles = re.sub('style=".*?"', '', s)
    assert s_without_styles == (
         '<span >i</span>'
         '<span > </span>'
         '<span  title="0.200">s</span>'
         '<span  title="0.200">e</span>'
         '<span  title="0.200">e</span>'
         '<span >:</span>'
         '<span > </span>'
         '<span >a</span>'
         '<span > </span>'
         '<span  title="0.500">l</span>'
         '<span  title="0.500">e</span>'
         '<span  title="0.500">a</span>'
         '<span  title="0.500">n</span>'
         '<span  title="0.500">i</span>'
         '<span  title="0.500">n</span>'
         '<span  title="0.500">g</span>'
         '<span > </span>'
         '<span  title="1.300">l</span>'
         '<span  title="1.300">e</span>'
         '<span  title="1.300">m</span>'
         '<span  title="1.300">o</span>'
         '<span  title="1.300">n</span>'
         '<span > </span>'
         '<span  title="0.200">t</span>'
         '<span  title="0.200">r</span>'
         '<span  title="0.200">e</span>'
         '<span  title="0.200">e</span>'
    )


def test_render_weighted_spans_char():
    weighted_spans = WeightedSpans(
        analyzer='char',
        document='see',
        weighted_spans=[
            ('se', [(0, 2)], 0.2),
            ('ee', [(1, 3)], 0.1),
            ],
    )
    s = render_weighted_spans(weighted_spans)
    assert s == (
        '<span'
        ' style="background-color: hsl(120, 100.00%, 69.88%); opacity: 0.93"'
        ' title="0.100">s</span>'
        '<span'
        ' style="background-color: hsl(120, 100.00%, 60.00%); opacity: 1.00"'
        ' title="0.150">e</span>'
        '<span'
        ' style="background-color: hsl(120, 100.00%, 81.46%); opacity: 0.87"'
        ' title="0.050">e</span>'
    )


def test_override_preserve_density():
    weighted_spans = WeightedSpans(
        analyzer='char',
        document='see',
        weighted_spans=[
            ('se', [(0, 2)], 0.2),
            ('ee', [(1, 3)], 0.1),
        ],
    )
    s = render_weighted_spans(weighted_spans, preserve_density=False)
    assert s.startswith(
        '<span '
        'style="background-color: hsl(120, 100.00%, 69.88%); opacity: 0.93" '
        'title="0.200">s</span>')


def test_remaining_weight_color():
    assert _remaining_weight_color([], 0, 'pos') == _weight_color(1, 1)
    assert _remaining_weight_color([], 2, 'neg') == _weight_color(-2, 2)
    assert _remaining_weight_color([('a', -1), ('b', -2)], 3, 'neg') == \
        _weight_color(-1, 3)
    assert _remaining_weight_color([('a', 1), ('b', 2)], 3, 'pos') == \
           _weight_color(1, 3)


@pytest.mark.parametrize(
    ['force_weights', 'dense_multitarget'],
    [[f, d] for f in [True, False] for d in [True, False]])
def test_format_html_options(force_weights, dense_multitarget):
    # test options that are not tested elsewhere
    X, y = make_regression(n_samples=100, n_targets=3, n_features=10,
                           random_state=42)
    reg = LinearRegression()
    reg.fit(X, y)
    res = explain_weights_sklearn(reg)
    kwargs = dict(
        force_weights=force_weights, dense_multitarget=dense_multitarget)
    postfix = '_' + '_'.join(
        '{}-{}'.format(k, v) for k, v in sorted(kwargs.items()))
    print(kwargs, postfix)
    # just check that it does not crash
    expl = format_as_html(res, **kwargs)
    write_html(reg, expl, format_as_text(res), postfix=postfix)
    pred_res = explain_prediction_sklearn(reg, X[0])
    pred_expl = format_as_html(pred_res, **kwargs)
    write_html(reg, pred_expl, format_as_text(pred_res),
               postfix='_expl' + postfix)
