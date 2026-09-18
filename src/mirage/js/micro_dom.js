/**
 * Mirage Micro-DOM for Plotly.js / D3 v3 static rendering in QuickJS.
 */
(function() {
    'use strict';

    var globalScope = typeof globalThis !== 'undefined' ? globalThis : this;
    if (typeof globalScope.process === 'undefined') {
        globalScope.process = { env: { NODE_ENV: 'production' }, browser: true, version: '' };
    }

    // --- Helpers ---
    function camelToDashed(str) {
        return str.replace(/[A-Z]/g, function(m) { return '-' + m.toLowerCase(); });
    }

    // --- CSSStyleDeclaration ---
    function CSSStyleDeclaration() {
        this._properties = {};
    }
    CSSStyleDeclaration.prototype.setProperty = function(name, value, priority) {
        if (value === null || value === undefined || value === '') {
            delete this._properties[name];
        } else {
            this._properties[name] = String(value);
        }
    };
    CSSStyleDeclaration.prototype.getPropertyValue = function(name) {
        return this._properties[name] || '';
    };
    CSSStyleDeclaration.prototype.removeProperty = function(name) {
        var val = this._properties[name] || '';
        delete this._properties[name];
        return val;
    };
    CSSStyleDeclaration.prototype.cssText = function() {
        var parts = [];
        for (var k in this._properties) {
            parts.push(camelToDashed(k) + ': ' + this._properties[k]);
        }
        return parts.join('; ');
    };

    // Style proxy or property reflection
    function createStyle(element) {
        var decl = new CSSStyleDeclaration();
        decl._element = element;
        // Return a proxy if available, else plain decl with getters/setters for common props
        if (typeof Proxy !== 'undefined') {
            return new Proxy(decl, {
                get: function(target, prop) {
                    if (prop in target || typeof prop === 'symbol') {
                        return target[prop];
                    }
                    var dashed = camelToDashed(String(prop));
                    return target.getPropertyValue(dashed);
                },
                set: function(target, prop, value) {
                    if (prop === '_properties' || prop in target) {
                        target[prop] = value;
                    } else {
                        var dashed = camelToDashed(String(prop));
                        target.setProperty(dashed, value);
                    }
                    return true;
                }
            });
        }
        return decl;
    }

    // --- DOM Node ---
    function Node() {
        this.childNodes = [];
        this.parentNode = null;
        this._ownerDoc = null;
        this.nodeType = 1;
        this.nodeName = '';
    }

    Object.defineProperty(Node.prototype, 'ownerDocument', {
        get: function() {
            if (this.nodeType === 9) return null;
            return this._ownerDoc || (globalScope.document || null);
        },
        set: function(v) {
            this._ownerDoc = v;
        }
    });

    Object.defineProperty(Node.prototype, 'firstChild', {
        get: function() { return this.childNodes[0] || null; }
    });
    Object.defineProperty(Node.prototype, 'lastChild', {
        get: function() { return this.childNodes[this.childNodes.length - 1] || null; }
    });
    Object.defineProperty(Node.prototype, 'nextSibling', {
        get: function() {
            if (!this.parentNode) return null;
            var idx = this.parentNode.childNodes.indexOf(this);
            return (idx !== -1 && idx + 1 < this.parentNode.childNodes.length) ? this.parentNode.childNodes[idx + 1] : null;
        }
    });
    Object.defineProperty(Node.prototype, 'previousSibling', {
        get: function() {
            if (!this.parentNode) return null;
            var idx = this.parentNode.childNodes.indexOf(this);
            return (idx > 0) ? this.parentNode.childNodes[idx - 1] : null;
        }
    });

    Node.prototype.appendChild = function(child) {
        if (child.nodeType === 11) { // DocumentFragment
            var children = child.childNodes.slice();
            for (var i = 0; i < children.length; i++) {
                this.appendChild(children[i]);
            }
            return child;
        }
        if (child.parentNode) {
            child.parentNode.removeChild(child);
        }
        child.parentNode = this;
        child._ownerDoc = this.nodeType === 9 ? this : (this.ownerDocument || globalScope.document);
        this.childNodes.push(child);
        return child;
    };

    Node.prototype.removeChild = function(child) {
        var idx = this.childNodes.indexOf(child);
        if (idx !== -1) {
            this.childNodes.splice(idx, 1);
            child.parentNode = null;
            return child;
        }
        return child;
    };

    Node.prototype.insertBefore = function(newChild, refChild) {
        if (!refChild) return this.appendChild(newChild);
        if (newChild.nodeType === 11) { // DocumentFragment
            var children = newChild.childNodes.slice();
            for (var i = 0; i < children.length; i++) {
                this.insertBefore(children[i], refChild);
            }
            return newChild;
        }
        if (newChild.parentNode) {
            newChild.parentNode.removeChild(newChild);
        }
        var idx = this.childNodes.indexOf(refChild);
        if (idx !== -1) {
            newChild.parentNode = this;
            newChild.ownerDocument = this.ownerDocument || this;
            this.childNodes.splice(idx, 0, newChild);
            return newChild;
        }
        return this.appendChild(newChild);
    };

    Node.prototype.replaceChild = function(newChild, oldChild) {
        this.insertBefore(newChild, oldChild);
        return this.removeChild(oldChild);
    };

    Node.prototype.cloneNode = function(deep) {
        var clone;
        if (this.nodeType === 3) {
            clone = new Text(this.nodeValue);
        } else if (this.nodeType === 1) {
            clone = this.namespaceURI 
                ? (this.ownerDocument || document).createElementNS(this.namespaceURI, this.tagName.toLowerCase())
                : (this.ownerDocument || document).createElement(this.tagName.toLowerCase());
            for (var k in this._attributes) {
                clone.setAttribute(k, this._attributes[k]);
            }
            for (var prop in this.style._properties) {
                clone.style.setProperty(prop, this.style.getPropertyValue(prop));
            }
        } else {
            clone = new Node();
        }
        if (deep && this.childNodes) {
            for (var i = 0; i < this.childNodes.length; i++) {
                clone.appendChild(this.childNodes[i].cloneNode(true));
            }
        }
        return clone;
    };

    Object.defineProperty(Node.prototype, 'textContent', {
        get: function() {
            if (this.nodeType === 3) return this.nodeValue;
            var txt = '';
            for (var i = 0; i < this.childNodes.length; i++) {
                txt += this.childNodes[i].textContent || '';
            }
            return txt;
        },
        set: function(val) {
            this.childNodes = [];
            if (val !== null && val !== undefined && val !== '') {
                this.appendChild(new Text(String(val)));
            }
        }
    });

    // --- Text Node ---
    function Text(text) {
        Node.call(this);
        this.nodeType = 3;
        this.nodeName = '#text';
        this.nodeValue = String(text !== undefined && text !== null ? text : '');
    }
    Text.prototype = Object.create(Node.prototype);
    Object.defineProperty(Text.prototype, 'data', {
        get: function() { return this.nodeValue; },
        set: function(v) { this.nodeValue = String(v); }
    });

    // --- DocumentFragment ---
    function DocumentFragment() {
        Node.call(this);
        this.nodeType = 11;
        this.nodeName = '#document-fragment';
    }
    DocumentFragment.prototype = Object.create(Node.prototype);

    // --- Element ---
    function Element(tagName, namespaceURI) {
        Node.call(this);
        this.nodeType = 1;
        this.namespaceURI = namespaceURI || null;
        var tagStr = String(tagName);
        if (this.namespaceURI === 'http://www.w3.org/2000/svg') {
            var lower = tagStr.toLowerCase();
            this.tagName = SVG_CAMEL_TAGS[lower] || lower;
            this.nodeName = this.tagName;
        } else {
            this.tagName = tagStr.toUpperCase();
            this.nodeName = this.tagName;
        }
        this._attributes = {};
        this.style = createStyle(this);
        this.classList = new ClassList(this);
        this._eventListeners = {};

        // Default dimensions
        this.clientWidth = 0;
        this.clientHeight = 0;
        this.offsetWidth = 0;
        this.offsetHeight = 0;
    }
    Element.prototype = Object.create(Node.prototype);

    Object.defineProperty(Element.prototype, 'id', {
        get: function() { return this.getAttribute('id') || ''; },
        set: function(v) { this.setAttribute('id', v); }
    });

    Object.defineProperty(Element.prototype, 'className', {
        get: function() { return this.getAttribute('class') || ''; },
        set: function(v) { this.setAttribute('class', v); }
    });

    function ClassList(el) { this._el = el; }
    ClassList.prototype.add = function() {
        var current = (this._el.getAttribute('class') || '').split(/\s+/).filter(Boolean);
        for (var i = 0; i < arguments.length; i++) {
            if (current.indexOf(arguments[i]) === -1) current.push(arguments[i]);
        }
        this._el.setAttribute('class', current.join(' '));
    };
    ClassList.prototype.remove = function() {
        var current = (this._el.getAttribute('class') || '').split(/\s+/).filter(Boolean);
        for (var i = 0; i < arguments.length; i++) {
            var idx = current.indexOf(arguments[i]);
            if (idx !== -1) current.splice(idx, 1);
        }
        this._el.setAttribute('class', current.join(' '));
    };
    ClassList.prototype.contains = function(name) {
        var current = (this._el.getAttribute('class') || '').split(/\s+/).filter(Boolean);
        return current.indexOf(name) !== -1;
    };
    ClassList.prototype.toggle = function(name) {
        if (this.contains(name)) { this.remove(name); return false; }
        else { this.add(name); return true; }
    };

    Element.prototype.setAttribute = function(name, value) {
        this._attributes[name] = String(value);
    };
    Element.prototype.getAttribute = function(name) {
        return this._attributes.hasOwnProperty(name) ? this._attributes[name] : null;
    };
    Element.prototype.hasAttribute = function(name) {
        return this._attributes.hasOwnProperty(name);
    };
    Element.prototype.removeAttribute = function(name) {
        delete this._attributes[name];
    };
    Element.prototype.setAttributeNS = function(ns, name, value) {
        this.setAttribute(name, value);
        if (name === 'href' && ns && String(ns).indexOf('xlink') !== -1) {
            this.setAttribute('xlink:href', value);
        } else if (name === 'xlink:href') {
            this.setAttribute('href', value);
        }
    };
    Element.prototype.getAttributeNS = function(ns, name) {
        return this.getAttribute(name);
    };
    Element.prototype.hasAttributeNS = function(ns, name) {
        return this.hasAttribute(name);
    };
    Element.prototype.removeAttributeNS = function(ns, name) {
        this.removeAttribute(name);
    };

    // Event listeners
    Element.prototype.addEventListener = function(event, fn) {
        if (!this._eventListeners[event]) this._eventListeners[event] = [];
        this._eventListeners[event].push(fn);
    };
    Element.prototype.removeEventListener = function(event, fn) {
        if (!this._eventListeners[event]) return;
        var idx = this._eventListeners[event].indexOf(fn);
        if (idx !== -1) this._eventListeners[event].splice(idx, 1);
    };
    Element.prototype.dispatchEvent = function(evt) {
        var fns = this._eventListeners[evt.type];
        if (fns) {
            for (var i = 0; i < fns.length; i++) {
                try { fns[i].call(this, evt); } catch(e) {}
            }
        }
        return true;
    };

    // D3 / Plotly Query Selectors
    Element.prototype.matches = function(selector) {
        if (!selector) return false;
        if (selector === '*') return true;
        if (selector === ':first-child') {
            if (!this.parentNode) return false;
            for (var i = 0; i < this.parentNode.childNodes.length; i++) {
                var ch = this.parentNode.childNodes[i];
                if (ch.nodeType === 1) return ch === this;
            }
            return false;
        }
        if (selector[0] === '#') return this.id === selector.slice(1);
        if (selector[0] === '.') {
            var cls = selector.slice(1);
            return this.classList.contains(cls);
        }

        // Attribute selector e.g. g[class^="barlayer"], [class^="barlayer"], [id="xyz"]
        var attrMatch = selector.match(/^([a-zA-Z0-9_-]*)\[([a-zA-Z0-9_-]+)([\^$*~|]?=)?(["']?)(.*?)\4\]$/);
        if (attrMatch) {
            var tag = attrMatch[1];
            var attr = attrMatch[2];
            var op = attrMatch[3];
            var val = attrMatch[5];
            if (tag && this.tagName.toLowerCase() !== tag.toLowerCase()) return false;
            if (!this.hasAttribute(attr)) return false;
            if (!op) return true;
            var actual = this.getAttribute(attr) || '';
            if (op === '=') return actual === val;
            if (op === '^=') return actual.indexOf(val) === 0;
            if (op === '$=') return actual.slice(-val.length) === val;
            if (op === '*=') return actual.indexOf(val) !== -1;
            if (op === '~=') return (' ' + actual + ' ').indexOf(' ' + val + ' ') !== -1;
            return false;
        }

        // Tag with class(es): e.g. svg.main-svg or g.trace.bars
        if (selector.indexOf('.') !== -1) {
            var parts = selector.split('.');
            var tagMatch = !parts[0] || this.tagName.toLowerCase() === parts[0].toLowerCase();
            if (!tagMatch) return false;
            for (var p = 1; p < parts.length; p++) {
                if (!this.classList.contains(parts[p])) return false;
            }
            return true;
        }
        return this.tagName.toLowerCase() === selector.toLowerCase();
    };

    Element.prototype.querySelector = function(selector) {
        if (selector === ':first-child') {
            for (var i = 0; i < this.childNodes.length; i++) {
                var ch = this.childNodes[i];
                if (ch.nodeType === 1) return ch;
            }
            return null;
        }
        var results = this.querySelectorAll(selector);
        return results.length > 0 ? results[0] : null;
    };

    function querySelectorAllSimple(root, selector) {
        var matches = [];
        function walk(node) {
            for (var i = 0; i < node.childNodes.length; i++) {
                var child = node.childNodes[i];
                if (child.nodeType === 1) {
                    if (child.matches(selector)) matches.push(child);
                    walk(child);
                }
            }
        }
        walk(root);
        return matches;
    }

    function querySelectorAllSingle(root, selector) {
        selector = selector.trim();
        if (!selector) return [];

        // Handle child combinators: e.g. "a > b > c"
        if (selector.indexOf('>') !== -1) {
            var segments = selector.split('>');
            var current = [root];
            for (var s = 0; s < segments.length; s++) {
                var seg = segments[s].trim();
                var next = [];
                for (var c = 0; c < current.length; c++) {
                    var parentNode = current[c];
                    if (s === 0) {
                        var matched = querySelectorAllSingle(parentNode, seg);
                        for (var m = 0; m < matched.length; m++) {
                            if (next.indexOf(matched[m]) === -1) next.push(matched[m]);
                        }
                    } else {
                        for (var ch = 0; ch < parentNode.childNodes.length; ch++) {
                            var kid = parentNode.childNodes[ch];
                            if (kid.nodeType === 1 && kid.matches(seg)) {
                                if (next.indexOf(kid) === -1) next.push(kid);
                            }
                        }
                    }
                }
                current = next;
            }
            return current;
        }

        // Handle space descendant combinators: e.g. "a b c"
        var inBracket = false;
        var hasSpace = false;
        for (var i = 0; i < selector.length; i++) {
            if (selector[i] === '[') inBracket = true;
            else if (selector[i] === ']') inBracket = false;
            else if (selector[i] === ' ' && !inBracket) {
                hasSpace = true;
                break;
            }
        }
        if (hasSpace) {
            var tokens = [];
            var curr = '';
            for (var i = 0; i < selector.length; i++) {
                if (selector[i] === '[') inBracket = true;
                else if (selector[i] === ']') inBracket = false;
                if (selector[i] === ' ' && !inBracket) {
                    if (curr.trim()) tokens.push(curr.trim());
                    curr = '';
                } else {
                    curr += selector[i];
                }
            }
            if (curr.trim()) tokens.push(curr.trim());

            var current = [root];
            for (var t = 0; t < tokens.length; t++) {
                var tok = tokens[t];
                var next = [];
                for (var c = 0; c < current.length; c++) {
                    var descendants = querySelectorAllSimple(current[c], tok);
                    for (var d = 0; d < descendants.length; d++) {
                        if (next.indexOf(descendants[d]) === -1) next.push(descendants[d]);
                    }
                }
                current = next;
            }
            return current;
        }

        return querySelectorAllSimple(root, selector);
    }

    Element.prototype.querySelectorAll = function(selector) {
        if (!selector) return [];
        if (selector.indexOf(',') !== -1) {
            var parts = selector.split(',');
            var all = [];
            for (var p = 0; p < parts.length; p++) {
                var res = querySelectorAllSingle(this, parts[p]);
                for (var r = 0; r < res.length; r++) {
                    if (all.indexOf(res[r]) === -1) all.push(res[r]);
                }
            }
            return all;
        }
        return querySelectorAllSingle(this, selector);
    };

    Element.prototype.getElementsByTagName = function(tagName) {
        var target = tagName.toUpperCase();
        var matches = [];
        function walk(node) {
            for (var i = 0; i < node.childNodes.length; i++) {
                var child = node.childNodes[i];
                if (child.nodeType === 1) {
                    if (target === '*' || child.tagName === target) matches.push(child);
                    walk(child);
                }
            }
        }
        walk(this);
        return matches;
    };

    Element.prototype.getElementsByClassName = function(className) {
        return this.querySelectorAll('.' + className);
    };

    // --- Geometry & Font Measurement ---
    Element.prototype.getCTM = function() {
        return { a: 1, b: 0, c: 0, d: 1, e: 0, f: 0 };
    };
    Element.prototype.getScreenCTM = function() {
        return { a: 1, b: 0, c: 0, d: 1, e: 0, f: 0 };
    };

    function parseTranslate(transform) {
        if (!transform) return { x: 0, y: 0 };
        var m = transform.match(/translate\(\s*([-\d.eE]+)(?:[\s,]+([-\d.eE]+))?\s*\)/);
        if (m) {
            return {
                x: parseFloat(m[1]) || 0,
                y: parseFloat(m[2]) || 0
            };
        }
        return { x: 0, y: 0 };
    }

    function getTextAnchor(node) {
        var cur = node;
        while (cur && cur.nodeType === 1) {
            var anchor = cur.style ? (cur.style.getPropertyValue('text-anchor') || cur.getAttribute('text-anchor')) : null;
            if (anchor) return anchor.trim().toLowerCase();
            cur = cur.parentNode;
        }
        return 'start';
    }

    Element.prototype.getBBox = function() {
        var tag = this.tagName.toLowerCase();
        var x = parseFloat(this.getAttribute('x')) || 0;
        var y = parseFloat(this.getAttribute('y')) || 0;

        if (tag === 'text') {
            // Check if <text> contains child <tspan> elements (e.g. multi-line text)
            var tspans = [];
            for (var i = 0; i < this.childNodes.length; i++) {
                var ch = this.childNodes[i];
                if (ch.nodeType === 1 && ch.tagName.toLowerCase() === 'tspan') {
                    tspans.push(ch);
                }
            }

            if (tspans.length > 0) {
                var parentFontSize = parseFloat(this.style.getPropertyValue('font-size') || this.getAttribute('font-size')) || 12;
                var parentFontFamily = this.style.getPropertyValue('font-family') || this.getAttribute('font-family') || 'sans-serif';
                var parentFontWeight = this.style.getPropertyValue('font-weight') || this.getAttribute('font-weight') || 'normal';
                var parentAnchor = getTextAnchor(this);
                var baseX = x;
                var baseY = y;

                var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
                var curY = baseY;

                for (var j = 0; j < tspans.length; j++) {
                    var tsp = tspans[j];
                    var tText = tsp.textContent || '';
                    var tFontSize = parseFloat(tsp.style.getPropertyValue('font-size') || tsp.getAttribute('font-size')) || parentFontSize;
                    var tFontFamily = tsp.style.getPropertyValue('font-family') || tsp.getAttribute('font-family') || parentFontFamily;
                    var tFontWeight = tsp.style.getPropertyValue('font-weight') || tsp.getAttribute('font-weight') || parentFontWeight;
                    var tAnchor = (tsp.style.getPropertyValue('text-anchor') || tsp.getAttribute('text-anchor') || parentAnchor).trim().toLowerCase();

                    var tx = tsp.hasAttribute('x') ? (parseFloat(tsp.getAttribute('x')) || 0) : baseX;
                    if (tsp.hasAttribute('y')) {
                        curY = parseFloat(tsp.getAttribute('y')) || 0;
                    }
                    if (tsp.hasAttribute('dy')) {
                        var dyStr = tsp.getAttribute('dy') || '';
                        var dyVal = 0;
                        if (dyStr.indexOf('em') !== -1) {
                            dyVal = parseFloat(dyStr) * tFontSize;
                        } else {
                            dyVal = parseFloat(dyStr) || 0;
                        }
                        curY += dyVal;
                    }

                    var tw = 0, th = tFontSize * 1.2, ta = tFontSize * 0.8;
                    if (typeof globalScope._measureTextRaw === 'function') {
                        try {
                            var raw = globalScope._measureTextRaw(tText, tFontFamily, String(tFontSize), tFontWeight);
                            var parts = raw.split(',');
                            tw = parseFloat(parts[0]) || 0;
                            th = parseFloat(parts[1]) || (tFontSize * 1.2);
                            ta = parseFloat(parts[2]) || (tFontSize * 0.8);
                        } catch(e) {
                            tw = tText.length * tFontSize * 0.6;
                        }
                    } else {
                        tw = tText.length * tFontSize * 0.6;
                    }

                    var tMinX;
                    if (tAnchor === 'middle') {
                        tMinX = tx - tw / 2;
                    } else if (tAnchor === 'end') {
                        tMinX = tx - tw;
                    } else {
                        tMinX = tx;
                    }
                    var tMaxX = tMinX + tw;
                    var tMinY = curY - ta;
                    var tMaxY = tMinY + th;

                    if (tMinX < minX) minX = tMinX;
                    if (tMinY < minY) minY = tMinY;
                    if (tMaxX > maxX) maxX = tMaxX;
                    if (tMaxY > maxY) maxY = tMaxY;
                }

                if (minX !== Infinity) {
                    var w = maxX - minX;
                    var h = maxY - minY;
                    return {
                        x: minX,
                        y: minY,
                        width: w,
                        height: h,
                        left: minX,
                        top: minY,
                        right: maxX,
                        bottom: maxY
                    };
                }
            }
        }

        if (tag === 'text' || tag === 'tspan') {
            var text = this.textContent || '';
            var fontSize = parseFloat(this.style.getPropertyValue('font-size') || this.getAttribute('font-size')) || 12;
            var fontFamily = this.style.getPropertyValue('font-family') || this.getAttribute('font-family') || 'sans-serif';
            var fontWeight = this.style.getPropertyValue('font-weight') || this.getAttribute('font-weight') || 'normal';
            var anchor = getTextAnchor(this);

            var w = 0, h = fontSize * 1.2, a = fontSize * 0.8, d = fontSize * 0.2;
            if (typeof globalScope._measureTextRaw === 'function') {
                try {
                    var raw = globalScope._measureTextRaw(text, fontFamily, String(fontSize), fontWeight);
                    var parts = raw.split(',');
                    w = parseFloat(parts[0]) || 0;
                    h = parseFloat(parts[1]) || (fontSize * 1.2);
                    a = parseFloat(parts[2]) || (fontSize * 0.8);
                    d = parseFloat(parts[3]) || (fontSize * 0.2);
                } catch(e) {
                    w = text.length * fontSize * 0.6;
                }
            } else {
                w = text.length * fontSize * 0.6;
            }

            var minX;
            if (anchor === 'middle') {
                minX = x - w / 2;
            } else if (anchor === 'end') {
                minX = x - w;
            } else {
                minX = x;
            }

            return {
                x: minX,
                y: y - a,
                width: w,
                height: h,
                left: minX,
                top: y - a,
                right: minX + w,
                bottom: y - a + h
            };
        }

        // For groups (<g>, <svg>), aggregate children bounding boxes
        var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        var hasKids = false;
        for (var i = 0; i < this.childNodes.length; i++) {
            var child = this.childNodes[i];
            if (child.nodeType === 1 && typeof child.getBBox === 'function') {
                var bb = child.getBBox();
                var tr = parseTranslate(child.getAttribute('transform'));
                var cx = bb.x + tr.x;
                var cy = bb.y + tr.y;
                var cw = bb.width;
                var ch = bb.height;
                if (cw > 0 || ch > 0) {
                    hasKids = true;
                    if (cx < minX) minX = cx;
                    if (cy < minY) minY = cy;
                    if (cx + cw > maxX) maxX = cx + cw;
                    if (cy + ch > maxY) maxY = cy + ch;
                }
            }
        }
        if (!hasKids) {
            return { x: 0, y: 0, width: 0, height: 0, left: 0, top: 0, right: 0, bottom: 0 };
        }
        return {
            x: minX,
            y: minY,
            width: maxX - minX,
            height: maxY - minY,
            left: minX,
            top: minY,
            right: maxX,
            bottom: maxY
        };
    };

    Element.prototype.getBoundingClientRect = function() {
        var bb = this.getBBox();
        var cur = this;
        var tx = 0, ty = 0;
        while (cur && cur.nodeType === 1) {
            if (cur.offsetLeft) tx += cur.offsetLeft;
            if (cur.offsetTop) ty += cur.offsetTop;
            var tr = cur.getAttribute ? parseTranslate(cur.getAttribute('transform')) : null;
            if (tr) {
                tx += tr.x;
                ty += tr.y;
            }
            cur = cur.parentNode;
        }
        var left = tx + bb.x;
        var top = ty + bb.y;
        var width = this.offsetWidth || this.clientWidth || bb.width;
        var height = this.offsetHeight || this.clientHeight || bb.height;
        return {
            left: left,
            top: top,
            right: left + width,
            bottom: top + height,
            width: width,
            height: height
        };
    };

    Element.prototype.getComputedTextLength = function() {
        return this.getBBox().width;
    };

    Element.prototype.getTotalLength = function() {
        var bb = this.getBBox();
        var p = (bb.width + bb.height) * 2;
        return p > 0 ? p : 100;
    };

    Element.prototype.getPointAtLength = function(len) {
        var bb = this.getBBox();
        return { x: bb.x, y: bb.y };
    };

    var SVG_CAMEL_TAGS = {
        'lineargradient': 'linearGradient',
        'radialgradient': 'radialGradient',
        'clippath': 'clipPath',
        'textpath': 'textPath',
        'foreignobject': 'foreignObject',
        'animatetransform': 'animateTransform',
        'fecolormatrix': 'feColorMatrix',
        'fecomposite': 'feComposite',
        'fegaussianblur': 'feGaussianBlur',
        'femerge': 'feMerge',
        'femergenode': 'feMergeNode',
        'feoffset': 'feOffset'
    };

    // Serialization
    function serializeNode(node) {
        if (node.nodeType === 3) {
            return node.nodeValue
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');
        }
        if (node.nodeType === 1) {
            var lowerTag = node.tagName.toLowerCase();
            var tag = SVG_CAMEL_TAGS[lowerTag] || lowerTag;
            var out = '<' + tag;
            var css = (node.style && typeof node.style.cssText === 'function') ? node.style.cssText() : '';
            for (var k in node._attributes) {
                if (k === 'style') continue;
                out += ' ' + k + '="' + String(node._attributes[k]).replace(/"/g, '&quot;') + '"';
            }
            if (css) {
                out += ' style="' + css.replace(/"/g, '&quot;') + '"';
            } else if (node._attributes['style']) {
                out += ' style="' + String(node._attributes['style']).replace(/"/g, '&quot;') + '"';
            }
            if (node.childNodes.length === 0) {
                if (['circle', 'path', 'line', 'rect', 'polygon', 'polyline', 'ellipse'].indexOf(lowerTag) !== -1) {
                    return out + '/>';
                }
                return out + '></' + tag + '>';
            }
            out += '>';
            for (var i = 0; i < node.childNodes.length; i++) {
                out += serializeNode(node.childNodes[i]);
            }
            out += '</' + tag + '>';
            return out;
        }
        return '';
    }

    Object.defineProperty(Element.prototype, 'outerHTML', {
        get: function() { return serializeNode(this); }
    });
    Object.defineProperty(Element.prototype, 'innerHTML', {
        get: function() {
            var out = '';
            for (var i = 0; i < this.childNodes.length; i++) {
                out += serializeNode(this.childNodes[i]);
            }
            return out;
        },
        set: function(html) {
            this.childNodes = [];
            // Basic text assignment if no parser needed
            if (html && html.indexOf('<') === -1) {
                this.appendChild(new Text(html));
            }
        }
    });

    // --- HTML / SVG Specifics ---
    function HTMLElement(tagName) { Element.call(this, tagName, null); }
    HTMLElement.prototype = Object.create(Element.prototype);

    function SVGElement(tagName) { Element.call(this, tagName, 'http://www.w3.org/2000/svg'); }
    SVGElement.prototype = Object.create(Element.prototype);

    function HTMLStyleElement() {
        HTMLElement.call(this, 'style');
        this.sheet = {
            insertRule: function(rule, index) {},
            addRule: function(selector, style, index) {},
            cssRules: []
        };
    }
    HTMLStyleElement.prototype = Object.create(HTMLElement.prototype);

    function HTMLCanvasElement() {
        HTMLElement.call(this, 'canvas');
        this._width = 300;
        this._height = 150;
        this._ctx2d = null;
    }
    HTMLCanvasElement.prototype = Object.create(HTMLElement.prototype);
    Object.defineProperty(HTMLCanvasElement.prototype, 'width', {
        get: function() { return this._width; },
        set: function(v) {
            this._width = parseInt(v, 10) || 0;
            this.setAttribute('width', this._width);
            if (this._ctx2d) { this._ctx2d._commands = []; }
        }
    });
    Object.defineProperty(HTMLCanvasElement.prototype, 'height', {
        get: function() { return this._height; },
        set: function(v) {
            this._height = parseInt(v, 10) || 0;
            this.setAttribute('height', this._height);
            if (this._ctx2d) { this._ctx2d._commands = []; }
        }
    });
    HTMLCanvasElement.prototype.getContext = function(type) {
        if (type === '2d') {
            if (!this._ctx2d) {
                var self = this;
                this._ctx2d = {
                    canvas: self,
                    fillStyle: '#000000',
                    strokeStyle: '#000000',
                    lineWidth: 1,
                    _commands: [],
                    fillRect: function(x, y, w, h) {
                        this._commands.push({
                            op: 'fillRect',
                            x: x,
                            y: y,
                            w: w,
                            h: h,
                            fill: this.fillStyle
                        });
                    },
                    clearRect: function(x, y, w, h) {
                        this._commands.push({
                            op: 'clearRect',
                            x: x,
                            y: y,
                            w: w,
                            h: h
                        });
                    },
                    save: function() {},
                    restore: function() {},
                    beginPath: function() {},
                    closePath: function() {},
                    moveTo: function() {},
                    lineTo: function() {},
                    stroke: function() {},
                    fill: function() {}
                };
            }
            return this._ctx2d;
        }
        return null;
    };
    HTMLCanvasElement.prototype.toDataURL = function(type) {
        if (typeof globalScope._encodeCanvasToPNG === 'function') {
            var cmds = this._ctx2d ? this._ctx2d._commands : [];
            return globalScope._encodeCanvasToPNG(this.width, this.height, JSON.stringify(cmds));
        }
        return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=';
    };

    // --- Document ---
    function Document() {
        Node.call(this);
        this.nodeType = 9;
        this.nodeName = '#document';
        this._ownerDoc = null;
        this.documentElement = new HTMLElement('html');
        this.documentElement._ownerDoc = this;
        this.head = new HTMLElement('head');
        this.head._ownerDoc = this;
        this.body = new HTMLElement('body');
        this.body._ownerDoc = this;
        this.documentElement.appendChild(this.head);
        this.documentElement.appendChild(this.body);
        this._elementsById = {};
    }
    Document.prototype = Object.create(Node.prototype);

    Document.prototype.createElement = function(tag) {
        var lower = String(tag).toLowerCase();
        var el;
        if (lower === 'style') el = new HTMLStyleElement();
        else if (lower === 'canvas') el = new HTMLCanvasElement();
        else el = new HTMLElement(lower);
        el.ownerDocument = this;
        return el;
    };

    Document.prototype.createElementNS = function(ns, tag) {
        var lower = String(tag).toLowerCase();
        var el = new SVGElement(lower);
        el.namespaceURI = ns;
        el.ownerDocument = this;
        return el;
    };

    Document.prototype.createTextNode = function(text) {
        var t = new Text(text);
        t.ownerDocument = this;
        return t;
    };

    Document.prototype.createDocumentFragment = function() {
        var frag = new DocumentFragment();
        frag.ownerDocument = this;
        return frag;
    };

    Document.prototype.getElementById = function(id) {
        return this.documentElement.querySelector('#' + id);
    };

    Document.prototype.querySelector = function(sel) {
        return this.documentElement.querySelector(sel);
    };

    Document.prototype.querySelectorAll = function(sel) {
        return this.documentElement.querySelectorAll(sel);
    };

    Document.prototype.getElementsByTagName = function(tag) {
        return this.documentElement.getElementsByTagName(tag);
    };

    Document.prototype.getElementsByClassName = function(cls) {
        return this.documentElement.getElementsByClassName(cls);
    };

    // --- Global Setup ---
    globalScope.console = {
        log: function() {
            if (typeof globalScope._printLog === 'function') {
                globalScope._printLog(Array.prototype.slice.call(arguments).map(String).join(' '));
            }
        },
        warn: function() {
            if (typeof globalScope._printLog === 'function') {
                globalScope._printLog('[WARN] ' + Array.prototype.slice.call(arguments).map(String).join(' '));
            }
        },
        error: function() {
            if (typeof globalScope._printLog === 'function') {
                globalScope._printLog('[ERROR] ' + Array.prototype.slice.call(arguments).map(String).join(' '));
            }
        }
    };

    var doc = new Document();
    globalScope.window = globalScope;
    globalScope.self = globalScope;
    globalScope.document = doc;
    globalScope.Node = Node;
    globalScope.Element = Element;
    globalScope.HTMLElement = HTMLElement;
    globalScope.HTMLCanvasElement = HTMLCanvasElement;
    globalScope.SVGElement = SVGElement;
    globalScope.DocumentFragment = DocumentFragment;
    globalScope.Text = Text;

    globalScope.Event = function(type) { this.type = type; };
    globalScope.CustomEvent = function(type, p) { this.type = type; this.detail = p ? p.detail : null; };
    globalScope.MouseEvent = function(type) { this.type = type; };

    globalScope.DOMParser = function() {};
    globalScope.DOMParser.prototype.parseFromString = function(str, mime) {
        var d = new Document();
        var root = new SVGElement('svg');
        d.appendChild(root);
        return d;
    };

    globalScope.XMLSerializer = function() {};
    globalScope.XMLSerializer.prototype.serializeToString = function(node) {
        return serializeNode(node);
    };

    globalScope.getComputedStyle = function(el) {
        return el ? el.style : new CSSStyleDeclaration();
    };

    globalScope.setTimeout = function(fn, ms) { return 1; };
    globalScope.clearTimeout = function(id) {};
    globalScope.setInterval = function(fn, ms) { return 1; };
    globalScope.clearInterval = function(id) {};
    globalScope.requestAnimationFrame = function(fn) {
        try { fn(Date.now()); } catch(e) {}
        return 1;
    };
    globalScope.cancelAnimationFrame = function(id) {};

    globalScope.navigator = {
        userAgent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)",
        platform: "MacIntel"
    };

    globalScope.location = {
        href: "http://localhost/",
        protocol: "http:",
        host: "localhost",
        pathname: "/"
    };

    globalScope.screen = { width: 1920, height: 1080 };

})();
