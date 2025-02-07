// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// dice.js
//
// written by drow <drow@bin.sh>
// http://creativecommons.org/licenses/by-nc/3.0/
'use strict';
((k, l) => l(k))(window, k => {
    function l(a) { let c = q(a); c = p(c); console.log(JSON.stringify(c)); return c.string.replace(/\{(\w+)\}/g, (b, d) => c[d].value); }
    function q(a) {
        let c = { string: a };
        [{ regex: /(\d*)d(\d+)/, fn: (b, d, h) => {
                    b = parseInt(d, 10) || 1;
                    d = parseInt(h, 10);
                    var f = 1 == b && 20 == d;
                    h = m();
                    let e = { n: b, d, d20: f, vx: [], sx: [], value: 0, roll_die: () => Math.floor(Math.random() * e.d) + 1, fmt_die: g => e.d20 && 1 == g ? `<b class="miss">${g}</b>` : e.d20 && 20 == g ? `<b class="crit">${g}</b>` : 1 == g || g == e.d ? `<b>${g}</b>` : g, sum: g => g.reduce((n, r) => n + r), fmt_pool: g => `${e.n}d${e.d} (${g.join(', ')})` };
                    for (d = 0; d < b; d++)
                        f = e.roll_die(), e.sx.push(e.fmt_die(f)), e.vx.push(f);
                    e.value = e.sum(e.vx);
                    e.str = e.fmt_pool(e.sx);
                    c[h] = e;
                    return `{${h}}`;
                } }, { regex: /(\d+\.\d+|\d+)/, fn: (b, d) => { b = parseFloat(d); d = m(); c[d] = { value: b, str: b.toString(10) }; return `{${d}}`; } }].forEach(b => { for (; b.regex.test(c.string);)
            c.string = c.string.replace(b.regex, b.fn); });
        return c;
    }
    function p(a) {
        [{ regex: /([a-z]*)\(([^()]+)\)/, fn: (c, b, d) => {
                    a.string = d;
                    a = p(a);
                    let h = m();
                    a.string = a.string.replace(/\{(\w+)\}/, (f, e) => { f = a[e]; e = f.value; var g = `${b}(${f.str})`; if ('avg' == b)
                        f.n && f.d && (e = f.n * (f.d + 1) / 2);
                    else if ('int' == b)
                        e = Math.floor(e);
                    else if ('round' == b)
                        e = Math.floor(e + .5);
                    else if ('sqrt' == b)
                        e = Math.sqrt(e);
                    else if (('adv' == b || 'dis' == b) && f.d20) {
                        g = f.roll_die();
                        let n = f.fmt_die(g);
                        'adv' == b && g > f.vx[0] || 'dis' == b && g < f.vx[0] ? (e = g, g = f.fmt_pool([`<s>${f.sx[0]}</s>`, n])) : g = f.fmt_pool([f.sx[0], `<s>${n}</s>`]);
                        g = `${b}(${g})`;
                    } a[h] = { value: e, str: g }; });
                    return `{${h}}`;
                } }, { regex: /\{(\w+)\}\s*(\*|\/|%)\s*\{(\w+)\}/, fn: (c, b, d, h) => {
                    c =
                        m();
                    let f, e = `${a[b].str} ${d} ${a[h].str}`;
                    '*' == d ? f = a[b].value * a[h].value : '/' == d ? f = a[b].value / a[h].value : '%' == d && (f = a[b].value % a[h].value);
                    a[c] = { value: f, str: e };
                    return `{${c}}`;
                } }, { regex: /\{(\w+)\}\s*(\+|\-)\s*\{(\w+)\}/, fn: (c, b, d, h) => { c = m(); let f, e = `${a[b].str} ${d} ${a[h].str}`; '+' == d ? f = a[b].value + a[h].value : '-' == d && (f = a[b].value - a[h].value); a[c] = { value: f, str: e }; return `{${c}}`; } }].forEach(c => { for (; c.regex.test(a.string);)
            a.string = a.string.replace(c.regex, c.fn); });
        return a;
    }
    function m() {
        let a = Math.floor(Math.random() *
            Number.MAX_SAFE_INTEGER), c = [];
        for (; 0 < a;)
            c.push(String.fromCharCode(97 + a % 26)), a = Math.floor(a / 26);
        return c.join('');
    }
    k.roll_dice = function (a) { return parseInt(l(a)); };
    k.roll_dice_fp = function (a) { return parseFloat(l(a)); };
    k.roll_dice_str = l;
    k.roll_dice_det = function (a) { let c = q(a); c = p(c); console.log(JSON.stringify(c)); return c.string.replace(/\{(\w+)\}/g, (b, d) => { b = c[d].str; d = c[d].value; Number.isInteger(d) || (d = Math.floor(100 * d + .5) / 100); return `<span class="str">${b}</span> = <b>${d}</b>`; }); };
});
