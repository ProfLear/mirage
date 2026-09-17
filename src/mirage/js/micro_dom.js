/**
 * Mirage Micro-DOM for Plotly.js / D3 v3 static rendering in QuickJS.
 */
(function() {
    'use strict';

    var globalScope = typeof globalThis !== 'undefined' ? globalThis : this;

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
        this.tagName = String(tagName).toUpperCase();
        this.nodeName = this.tagName;
        this.namespaceURI = namespaceURI || null;
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
        if (selector[0] === '#') return this.id === selector.slice(1);
        if (selector[0] === '.') {
            var cls = selector.slice(1);
            return this.classList.contains(cls);
        }
        // Tag with class: e.g. svg.main-svg
        if (selector.indexOf('.') !== -1) {
            var parts = selector.split('.');
            var tagMatch = !parts[0] || this.tagName.toLowerCase() === parts[0].toLowerCase();
            return tagMatch && this.classList.contains(parts[1]);
        }
        return this.tagName.toLowerCase() === selector.toLowerCase();
    };

    Element.prototype.querySelector = function(selector) {
        var results = this.querySelectorAll(selector);
        return results.length > 0 ? results[0] : null;
    };

    Element.prototype.querySelectorAll = function(selector) {
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
        walk(this);
        return matches;
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

    Element.prototype.getBBox = function() {
        var tag = this.tagName.toLowerCase();
        var x = parseFloat(this.getAttribute('x')) || 0;
        var y = parseFloat(this.getAttribute('y')) || 0;

        if (tag === 'text' || tag === 'tspan') {
            var text = this.textContent || '';
            var fontSize = parseFloat(this.style.getPropertyValue('font-size') || this.getAttribute('font-size')) || 12;
            var fontFamily = this.style.getPropertyValue('font-family') || this.getAttribute('font-family') || 'sans-serif';
            var fontWeight = this.style.getPropertyValue('font-weight') || this.getAttribute('font-weight') || 'normal';

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
            return {
                x: x,
                y: y - a,
                width: w,
                height: h,
                left: x,
                top: y - a,
                right: x + w,
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
        var left = (this.offsetLeft || 0) + bb.x;
        var top = (this.offsetTop || 0) + bb.y;
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

    // Serialization
    function serializeNode(node) {
        if (node.nodeType === 3) {
            return node.nodeValue
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');
        }
        if (node.nodeType === 1) {
            var tag = node.tagName.toLowerCase();
            var out = '<' + tag;
            for (var k in node._attributes) {
                out += ' ' + k + '="' + String(node._attributes[k]).replace(/"/g, '&quot;') + '"';
            }
            var css = node.style.cssText();
            if (css && !node.hasAttribute('style')) {
                out += ' style="' + css.replace(/"/g, '&quot;') + '"';
            }
            if (node.childNodes.length === 0) {
                if (['circle', 'path', 'line', 'rect', 'polygon', 'polyline', 'ellipse'].indexOf(tag) !== -1) {
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
