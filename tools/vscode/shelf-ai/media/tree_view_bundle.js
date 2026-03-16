"use strict";
(() => {
  var __create = Object.create;
  var __defProp = Object.defineProperty;
  var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __getProtoOf = Object.getPrototypeOf;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __require = /* @__PURE__ */ ((x) => typeof require !== "undefined" ? require : typeof Proxy !== "undefined" ? new Proxy(x, {
    get: (a, b) => (typeof require !== "undefined" ? require : a)[b]
  }) : x)(function(x) {
    if (typeof require !== "undefined") return require.apply(this, arguments);
    throw Error('Dynamic require of "' + x + '" is not supported');
  });
  var __commonJS = (cb, mod) => function __require2() {
    return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
  };
  var __copyProps = (to, from, except, desc) => {
    if (from && typeof from === "object" || typeof from === "function") {
      for (let key of __getOwnPropNames(from))
        if (!__hasOwnProp.call(to, key) && key !== except)
          __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
    }
    return to;
  };
  var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
    // If the importer is in node compatibility mode or this is not an ESM
    // file that has been converted to a CommonJS file using a Babel-
    // compatible transform (i.e. "__esModule" has not been set), then set
    // "default" to the CommonJS "module.exports" for node compatibility.
    isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
    mod
  ));

  // node_modules/lodash/_listCacheClear.js
  var require_listCacheClear = __commonJS({
    "node_modules/lodash/_listCacheClear.js"(exports, module) {
      function listCacheClear() {
        this.__data__ = [];
        this.size = 0;
      }
      module.exports = listCacheClear;
    }
  });

  // node_modules/lodash/eq.js
  var require_eq = __commonJS({
    "node_modules/lodash/eq.js"(exports, module) {
      function eq(value, other) {
        return value === other || value !== value && other !== other;
      }
      module.exports = eq;
    }
  });

  // node_modules/lodash/_assocIndexOf.js
  var require_assocIndexOf = __commonJS({
    "node_modules/lodash/_assocIndexOf.js"(exports, module) {
      var eq = require_eq();
      function assocIndexOf(array2, key) {
        var length = array2.length;
        while (length--) {
          if (eq(array2[length][0], key)) {
            return length;
          }
        }
        return -1;
      }
      module.exports = assocIndexOf;
    }
  });

  // node_modules/lodash/_listCacheDelete.js
  var require_listCacheDelete = __commonJS({
    "node_modules/lodash/_listCacheDelete.js"(exports, module) {
      var assocIndexOf = require_assocIndexOf();
      var arrayProto = Array.prototype;
      var splice = arrayProto.splice;
      function listCacheDelete(key) {
        var data = this.__data__, index = assocIndexOf(data, key);
        if (index < 0) {
          return false;
        }
        var lastIndex = data.length - 1;
        if (index == lastIndex) {
          data.pop();
        } else {
          splice.call(data, index, 1);
        }
        --this.size;
        return true;
      }
      module.exports = listCacheDelete;
    }
  });

  // node_modules/lodash/_listCacheGet.js
  var require_listCacheGet = __commonJS({
    "node_modules/lodash/_listCacheGet.js"(exports, module) {
      var assocIndexOf = require_assocIndexOf();
      function listCacheGet(key) {
        var data = this.__data__, index = assocIndexOf(data, key);
        return index < 0 ? void 0 : data[index][1];
      }
      module.exports = listCacheGet;
    }
  });

  // node_modules/lodash/_listCacheHas.js
  var require_listCacheHas = __commonJS({
    "node_modules/lodash/_listCacheHas.js"(exports, module) {
      var assocIndexOf = require_assocIndexOf();
      function listCacheHas(key) {
        return assocIndexOf(this.__data__, key) > -1;
      }
      module.exports = listCacheHas;
    }
  });

  // node_modules/lodash/_listCacheSet.js
  var require_listCacheSet = __commonJS({
    "node_modules/lodash/_listCacheSet.js"(exports, module) {
      var assocIndexOf = require_assocIndexOf();
      function listCacheSet(key, value) {
        var data = this.__data__, index = assocIndexOf(data, key);
        if (index < 0) {
          ++this.size;
          data.push([key, value]);
        } else {
          data[index][1] = value;
        }
        return this;
      }
      module.exports = listCacheSet;
    }
  });

  // node_modules/lodash/_ListCache.js
  var require_ListCache = __commonJS({
    "node_modules/lodash/_ListCache.js"(exports, module) {
      var listCacheClear = require_listCacheClear();
      var listCacheDelete = require_listCacheDelete();
      var listCacheGet = require_listCacheGet();
      var listCacheHas = require_listCacheHas();
      var listCacheSet = require_listCacheSet();
      function ListCache(entries) {
        var index = -1, length = entries == null ? 0 : entries.length;
        this.clear();
        while (++index < length) {
          var entry = entries[index];
          this.set(entry[0], entry[1]);
        }
      }
      ListCache.prototype.clear = listCacheClear;
      ListCache.prototype["delete"] = listCacheDelete;
      ListCache.prototype.get = listCacheGet;
      ListCache.prototype.has = listCacheHas;
      ListCache.prototype.set = listCacheSet;
      module.exports = ListCache;
    }
  });

  // node_modules/lodash/_stackClear.js
  var require_stackClear = __commonJS({
    "node_modules/lodash/_stackClear.js"(exports, module) {
      var ListCache = require_ListCache();
      function stackClear() {
        this.__data__ = new ListCache();
        this.size = 0;
      }
      module.exports = stackClear;
    }
  });

  // node_modules/lodash/_stackDelete.js
  var require_stackDelete = __commonJS({
    "node_modules/lodash/_stackDelete.js"(exports, module) {
      function stackDelete(key) {
        var data = this.__data__, result = data["delete"](key);
        this.size = data.size;
        return result;
      }
      module.exports = stackDelete;
    }
  });

  // node_modules/lodash/_stackGet.js
  var require_stackGet = __commonJS({
    "node_modules/lodash/_stackGet.js"(exports, module) {
      function stackGet(key) {
        return this.__data__.get(key);
      }
      module.exports = stackGet;
    }
  });

  // node_modules/lodash/_stackHas.js
  var require_stackHas = __commonJS({
    "node_modules/lodash/_stackHas.js"(exports, module) {
      function stackHas(key) {
        return this.__data__.has(key);
      }
      module.exports = stackHas;
    }
  });

  // node_modules/lodash/_freeGlobal.js
  var require_freeGlobal = __commonJS({
    "node_modules/lodash/_freeGlobal.js"(exports, module) {
      var freeGlobal = typeof global == "object" && global && global.Object === Object && global;
      module.exports = freeGlobal;
    }
  });

  // node_modules/lodash/_root.js
  var require_root = __commonJS({
    "node_modules/lodash/_root.js"(exports, module) {
      var freeGlobal = require_freeGlobal();
      var freeSelf = typeof self == "object" && self && self.Object === Object && self;
      var root2 = freeGlobal || freeSelf || Function("return this")();
      module.exports = root2;
    }
  });

  // node_modules/lodash/_Symbol.js
  var require_Symbol = __commonJS({
    "node_modules/lodash/_Symbol.js"(exports, module) {
      var root2 = require_root();
      var Symbol2 = root2.Symbol;
      module.exports = Symbol2;
    }
  });

  // node_modules/lodash/_getRawTag.js
  var require_getRawTag = __commonJS({
    "node_modules/lodash/_getRawTag.js"(exports, module) {
      var Symbol2 = require_Symbol();
      var objectProto = Object.prototype;
      var hasOwnProperty = objectProto.hasOwnProperty;
      var nativeObjectToString = objectProto.toString;
      var symToStringTag = Symbol2 ? Symbol2.toStringTag : void 0;
      function getRawTag(value) {
        var isOwn = hasOwnProperty.call(value, symToStringTag), tag = value[symToStringTag];
        try {
          value[symToStringTag] = void 0;
          var unmasked = true;
        } catch (e) {
        }
        var result = nativeObjectToString.call(value);
        if (unmasked) {
          if (isOwn) {
            value[symToStringTag] = tag;
          } else {
            delete value[symToStringTag];
          }
        }
        return result;
      }
      module.exports = getRawTag;
    }
  });

  // node_modules/lodash/_objectToString.js
  var require_objectToString = __commonJS({
    "node_modules/lodash/_objectToString.js"(exports, module) {
      var objectProto = Object.prototype;
      var nativeObjectToString = objectProto.toString;
      function objectToString(value) {
        return nativeObjectToString.call(value);
      }
      module.exports = objectToString;
    }
  });

  // node_modules/lodash/_baseGetTag.js
  var require_baseGetTag = __commonJS({
    "node_modules/lodash/_baseGetTag.js"(exports, module) {
      var Symbol2 = require_Symbol();
      var getRawTag = require_getRawTag();
      var objectToString = require_objectToString();
      var nullTag = "[object Null]";
      var undefinedTag = "[object Undefined]";
      var symToStringTag = Symbol2 ? Symbol2.toStringTag : void 0;
      function baseGetTag(value) {
        if (value == null) {
          return value === void 0 ? undefinedTag : nullTag;
        }
        return symToStringTag && symToStringTag in Object(value) ? getRawTag(value) : objectToString(value);
      }
      module.exports = baseGetTag;
    }
  });

  // node_modules/lodash/isObject.js
  var require_isObject = __commonJS({
    "node_modules/lodash/isObject.js"(exports, module) {
      function isObject(value) {
        var type = typeof value;
        return value != null && (type == "object" || type == "function");
      }
      module.exports = isObject;
    }
  });

  // node_modules/lodash/isFunction.js
  var require_isFunction = __commonJS({
    "node_modules/lodash/isFunction.js"(exports, module) {
      var baseGetTag = require_baseGetTag();
      var isObject = require_isObject();
      var asyncTag = "[object AsyncFunction]";
      var funcTag = "[object Function]";
      var genTag = "[object GeneratorFunction]";
      var proxyTag = "[object Proxy]";
      function isFunction(value) {
        if (!isObject(value)) {
          return false;
        }
        var tag = baseGetTag(value);
        return tag == funcTag || tag == genTag || tag == asyncTag || tag == proxyTag;
      }
      module.exports = isFunction;
    }
  });

  // node_modules/lodash/_coreJsData.js
  var require_coreJsData = __commonJS({
    "node_modules/lodash/_coreJsData.js"(exports, module) {
      var root2 = require_root();
      var coreJsData = root2["__core-js_shared__"];
      module.exports = coreJsData;
    }
  });

  // node_modules/lodash/_isMasked.js
  var require_isMasked = __commonJS({
    "node_modules/lodash/_isMasked.js"(exports, module) {
      var coreJsData = require_coreJsData();
      var maskSrcKey = (function() {
        var uid = /[^.]+$/.exec(coreJsData && coreJsData.keys && coreJsData.keys.IE_PROTO || "");
        return uid ? "Symbol(src)_1." + uid : "";
      })();
      function isMasked(func) {
        return !!maskSrcKey && maskSrcKey in func;
      }
      module.exports = isMasked;
    }
  });

  // node_modules/lodash/_toSource.js
  var require_toSource = __commonJS({
    "node_modules/lodash/_toSource.js"(exports, module) {
      var funcProto = Function.prototype;
      var funcToString = funcProto.toString;
      function toSource(func) {
        if (func != null) {
          try {
            return funcToString.call(func);
          } catch (e) {
          }
          try {
            return func + "";
          } catch (e) {
          }
        }
        return "";
      }
      module.exports = toSource;
    }
  });

  // node_modules/lodash/_baseIsNative.js
  var require_baseIsNative = __commonJS({
    "node_modules/lodash/_baseIsNative.js"(exports, module) {
      var isFunction = require_isFunction();
      var isMasked = require_isMasked();
      var isObject = require_isObject();
      var toSource = require_toSource();
      var reRegExpChar = /[\\^$.*+?()[\]{}|]/g;
      var reIsHostCtor = /^\[object .+?Constructor\]$/;
      var funcProto = Function.prototype;
      var objectProto = Object.prototype;
      var funcToString = funcProto.toString;
      var hasOwnProperty = objectProto.hasOwnProperty;
      var reIsNative = RegExp(
        "^" + funcToString.call(hasOwnProperty).replace(reRegExpChar, "\\$&").replace(/hasOwnProperty|(function).*?(?=\\\()| for .+?(?=\\\])/g, "$1.*?") + "$"
      );
      function baseIsNative(value) {
        if (!isObject(value) || isMasked(value)) {
          return false;
        }
        var pattern = isFunction(value) ? reIsNative : reIsHostCtor;
        return pattern.test(toSource(value));
      }
      module.exports = baseIsNative;
    }
  });

  // node_modules/lodash/_getValue.js
  var require_getValue = __commonJS({
    "node_modules/lodash/_getValue.js"(exports, module) {
      function getValue(object, key) {
        return object == null ? void 0 : object[key];
      }
      module.exports = getValue;
    }
  });

  // node_modules/lodash/_getNative.js
  var require_getNative = __commonJS({
    "node_modules/lodash/_getNative.js"(exports, module) {
      var baseIsNative = require_baseIsNative();
      var getValue = require_getValue();
      function getNative(object, key) {
        var value = getValue(object, key);
        return baseIsNative(value) ? value : void 0;
      }
      module.exports = getNative;
    }
  });

  // node_modules/lodash/_Map.js
  var require_Map = __commonJS({
    "node_modules/lodash/_Map.js"(exports, module) {
      var getNative = require_getNative();
      var root2 = require_root();
      var Map2 = getNative(root2, "Map");
      module.exports = Map2;
    }
  });

  // node_modules/lodash/_nativeCreate.js
  var require_nativeCreate = __commonJS({
    "node_modules/lodash/_nativeCreate.js"(exports, module) {
      var getNative = require_getNative();
      var nativeCreate = getNative(Object, "create");
      module.exports = nativeCreate;
    }
  });

  // node_modules/lodash/_hashClear.js
  var require_hashClear = __commonJS({
    "node_modules/lodash/_hashClear.js"(exports, module) {
      var nativeCreate = require_nativeCreate();
      function hashClear() {
        this.__data__ = nativeCreate ? nativeCreate(null) : {};
        this.size = 0;
      }
      module.exports = hashClear;
    }
  });

  // node_modules/lodash/_hashDelete.js
  var require_hashDelete = __commonJS({
    "node_modules/lodash/_hashDelete.js"(exports, module) {
      function hashDelete(key) {
        var result = this.has(key) && delete this.__data__[key];
        this.size -= result ? 1 : 0;
        return result;
      }
      module.exports = hashDelete;
    }
  });

  // node_modules/lodash/_hashGet.js
  var require_hashGet = __commonJS({
    "node_modules/lodash/_hashGet.js"(exports, module) {
      var nativeCreate = require_nativeCreate();
      var HASH_UNDEFINED = "__lodash_hash_undefined__";
      var objectProto = Object.prototype;
      var hasOwnProperty = objectProto.hasOwnProperty;
      function hashGet(key) {
        var data = this.__data__;
        if (nativeCreate) {
          var result = data[key];
          return result === HASH_UNDEFINED ? void 0 : result;
        }
        return hasOwnProperty.call(data, key) ? data[key] : void 0;
      }
      module.exports = hashGet;
    }
  });

  // node_modules/lodash/_hashHas.js
  var require_hashHas = __commonJS({
    "node_modules/lodash/_hashHas.js"(exports, module) {
      var nativeCreate = require_nativeCreate();
      var objectProto = Object.prototype;
      var hasOwnProperty = objectProto.hasOwnProperty;
      function hashHas(key) {
        var data = this.__data__;
        return nativeCreate ? data[key] !== void 0 : hasOwnProperty.call(data, key);
      }
      module.exports = hashHas;
    }
  });

  // node_modules/lodash/_hashSet.js
  var require_hashSet = __commonJS({
    "node_modules/lodash/_hashSet.js"(exports, module) {
      var nativeCreate = require_nativeCreate();
      var HASH_UNDEFINED = "__lodash_hash_undefined__";
      function hashSet(key, value) {
        var data = this.__data__;
        this.size += this.has(key) ? 0 : 1;
        data[key] = nativeCreate && value === void 0 ? HASH_UNDEFINED : value;
        return this;
      }
      module.exports = hashSet;
    }
  });

  // node_modules/lodash/_Hash.js
  var require_Hash = __commonJS({
    "node_modules/lodash/_Hash.js"(exports, module) {
      var hashClear = require_hashClear();
      var hashDelete = require_hashDelete();
      var hashGet = require_hashGet();
      var hashHas = require_hashHas();
      var hashSet = require_hashSet();
      function Hash(entries) {
        var index = -1, length = entries == null ? 0 : entries.length;
        this.clear();
        while (++index < length) {
          var entry = entries[index];
          this.set(entry[0], entry[1]);
        }
      }
      Hash.prototype.clear = hashClear;
      Hash.prototype["delete"] = hashDelete;
      Hash.prototype.get = hashGet;
      Hash.prototype.has = hashHas;
      Hash.prototype.set = hashSet;
      module.exports = Hash;
    }
  });

  // node_modules/lodash/_mapCacheClear.js
  var require_mapCacheClear = __commonJS({
    "node_modules/lodash/_mapCacheClear.js"(exports, module) {
      var Hash = require_Hash();
      var ListCache = require_ListCache();
      var Map2 = require_Map();
      function mapCacheClear() {
        this.size = 0;
        this.__data__ = {
          "hash": new Hash(),
          "map": new (Map2 || ListCache)(),
          "string": new Hash()
        };
      }
      module.exports = mapCacheClear;
    }
  });

  // node_modules/lodash/_isKeyable.js
  var require_isKeyable = __commonJS({
    "node_modules/lodash/_isKeyable.js"(exports, module) {
      function isKeyable(value) {
        var type = typeof value;
        return type == "string" || type == "number" || type == "symbol" || type == "boolean" ? value !== "__proto__" : value === null;
      }
      module.exports = isKeyable;
    }
  });

  // node_modules/lodash/_getMapData.js
  var require_getMapData = __commonJS({
    "node_modules/lodash/_getMapData.js"(exports, module) {
      var isKeyable = require_isKeyable();
      function getMapData(map, key) {
        var data = map.__data__;
        return isKeyable(key) ? data[typeof key == "string" ? "string" : "hash"] : data.map;
      }
      module.exports = getMapData;
    }
  });

  // node_modules/lodash/_mapCacheDelete.js
  var require_mapCacheDelete = __commonJS({
    "node_modules/lodash/_mapCacheDelete.js"(exports, module) {
      var getMapData = require_getMapData();
      function mapCacheDelete(key) {
        var result = getMapData(this, key)["delete"](key);
        this.size -= result ? 1 : 0;
        return result;
      }
      module.exports = mapCacheDelete;
    }
  });

  // node_modules/lodash/_mapCacheGet.js
  var require_mapCacheGet = __commonJS({
    "node_modules/lodash/_mapCacheGet.js"(exports, module) {
      var getMapData = require_getMapData();
      function mapCacheGet(key) {
        return getMapData(this, key).get(key);
      }
      module.exports = mapCacheGet;
    }
  });

  // node_modules/lodash/_mapCacheHas.js
  var require_mapCacheHas = __commonJS({
    "node_modules/lodash/_mapCacheHas.js"(exports, module) {
      var getMapData = require_getMapData();
      function mapCacheHas(key) {
        return getMapData(this, key).has(key);
      }
      module.exports = mapCacheHas;
    }
  });

  // node_modules/lodash/_mapCacheSet.js
  var require_mapCacheSet = __commonJS({
    "node_modules/lodash/_mapCacheSet.js"(exports, module) {
      var getMapData = require_getMapData();
      function mapCacheSet(key, value) {
        var data = getMapData(this, key), size = data.size;
        data.set(key, value);
        this.size += data.size == size ? 0 : 1;
        return this;
      }
      module.exports = mapCacheSet;
    }
  });

  // node_modules/lodash/_MapCache.js
  var require_MapCache = __commonJS({
    "node_modules/lodash/_MapCache.js"(exports, module) {
      var mapCacheClear = require_mapCacheClear();
      var mapCacheDelete = require_mapCacheDelete();
      var mapCacheGet = require_mapCacheGet();
      var mapCacheHas = require_mapCacheHas();
      var mapCacheSet = require_mapCacheSet();
      function MapCache(entries) {
        var index = -1, length = entries == null ? 0 : entries.length;
        this.clear();
        while (++index < length) {
          var entry = entries[index];
          this.set(entry[0], entry[1]);
        }
      }
      MapCache.prototype.clear = mapCacheClear;
      MapCache.prototype["delete"] = mapCacheDelete;
      MapCache.prototype.get = mapCacheGet;
      MapCache.prototype.has = mapCacheHas;
      MapCache.prototype.set = mapCacheSet;
      module.exports = MapCache;
    }
  });

  // node_modules/lodash/_stackSet.js
  var require_stackSet = __commonJS({
    "node_modules/lodash/_stackSet.js"(exports, module) {
      var ListCache = require_ListCache();
      var Map2 = require_Map();
      var MapCache = require_MapCache();
      var LARGE_ARRAY_SIZE = 200;
      function stackSet(key, value) {
        var data = this.__data__;
        if (data instanceof ListCache) {
          var pairs = data.__data__;
          if (!Map2 || pairs.length < LARGE_ARRAY_SIZE - 1) {
            pairs.push([key, value]);
            this.size = ++data.size;
            return this;
          }
          data = this.__data__ = new MapCache(pairs);
        }
        data.set(key, value);
        this.size = data.size;
        return this;
      }
      module.exports = stackSet;
    }
  });

  // node_modules/lodash/_Stack.js
  var require_Stack = __commonJS({
    "node_modules/lodash/_Stack.js"(exports, module) {
      var ListCache = require_ListCache();
      var stackClear = require_stackClear();
      var stackDelete = require_stackDelete();
      var stackGet = require_stackGet();
      var stackHas = require_stackHas();
      var stackSet = require_stackSet();
      function Stack(entries) {
        var data = this.__data__ = new ListCache(entries);
        this.size = data.size;
      }
      Stack.prototype.clear = stackClear;
      Stack.prototype["delete"] = stackDelete;
      Stack.prototype.get = stackGet;
      Stack.prototype.has = stackHas;
      Stack.prototype.set = stackSet;
      module.exports = Stack;
    }
  });

  // node_modules/lodash/_arrayEach.js
  var require_arrayEach = __commonJS({
    "node_modules/lodash/_arrayEach.js"(exports, module) {
      function arrayEach(array2, iteratee) {
        var index = -1, length = array2 == null ? 0 : array2.length;
        while (++index < length) {
          if (iteratee(array2[index], index, array2) === false) {
            break;
          }
        }
        return array2;
      }
      module.exports = arrayEach;
    }
  });

  // node_modules/lodash/_defineProperty.js
  var require_defineProperty = __commonJS({
    "node_modules/lodash/_defineProperty.js"(exports, module) {
      var getNative = require_getNative();
      var defineProperty = (function() {
        try {
          var func = getNative(Object, "defineProperty");
          func({}, "", {});
          return func;
        } catch (e) {
        }
      })();
      module.exports = defineProperty;
    }
  });

  // node_modules/lodash/_baseAssignValue.js
  var require_baseAssignValue = __commonJS({
    "node_modules/lodash/_baseAssignValue.js"(exports, module) {
      var defineProperty = require_defineProperty();
      function baseAssignValue(object, key, value) {
        if (key == "__proto__" && defineProperty) {
          defineProperty(object, key, {
            "configurable": true,
            "enumerable": true,
            "value": value,
            "writable": true
          });
        } else {
          object[key] = value;
        }
      }
      module.exports = baseAssignValue;
    }
  });

  // node_modules/lodash/_assignValue.js
  var require_assignValue = __commonJS({
    "node_modules/lodash/_assignValue.js"(exports, module) {
      var baseAssignValue = require_baseAssignValue();
      var eq = require_eq();
      var objectProto = Object.prototype;
      var hasOwnProperty = objectProto.hasOwnProperty;
      function assignValue(object, key, value) {
        var objValue = object[key];
        if (!(hasOwnProperty.call(object, key) && eq(objValue, value)) || value === void 0 && !(key in object)) {
          baseAssignValue(object, key, value);
        }
      }
      module.exports = assignValue;
    }
  });

  // node_modules/lodash/_copyObject.js
  var require_copyObject = __commonJS({
    "node_modules/lodash/_copyObject.js"(exports, module) {
      var assignValue = require_assignValue();
      var baseAssignValue = require_baseAssignValue();
      function copyObject(source, props, object, customizer) {
        var isNew = !object;
        object || (object = {});
        var index = -1, length = props.length;
        while (++index < length) {
          var key = props[index];
          var newValue = customizer ? customizer(object[key], source[key], key, object, source) : void 0;
          if (newValue === void 0) {
            newValue = source[key];
          }
          if (isNew) {
            baseAssignValue(object, key, newValue);
          } else {
            assignValue(object, key, newValue);
          }
        }
        return object;
      }
      module.exports = copyObject;
    }
  });

  // node_modules/lodash/_baseTimes.js
  var require_baseTimes = __commonJS({
    "node_modules/lodash/_baseTimes.js"(exports, module) {
      function baseTimes(n, iteratee) {
        var index = -1, result = Array(n);
        while (++index < n) {
          result[index] = iteratee(index);
        }
        return result;
      }
      module.exports = baseTimes;
    }
  });

  // node_modules/lodash/isObjectLike.js
  var require_isObjectLike = __commonJS({
    "node_modules/lodash/isObjectLike.js"(exports, module) {
      function isObjectLike(value) {
        return value != null && typeof value == "object";
      }
      module.exports = isObjectLike;
    }
  });

  // node_modules/lodash/_baseIsArguments.js
  var require_baseIsArguments = __commonJS({
    "node_modules/lodash/_baseIsArguments.js"(exports, module) {
      var baseGetTag = require_baseGetTag();
      var isObjectLike = require_isObjectLike();
      var argsTag = "[object Arguments]";
      function baseIsArguments(value) {
        return isObjectLike(value) && baseGetTag(value) == argsTag;
      }
      module.exports = baseIsArguments;
    }
  });

  // node_modules/lodash/isArguments.js
  var require_isArguments = __commonJS({
    "node_modules/lodash/isArguments.js"(exports, module) {
      var baseIsArguments = require_baseIsArguments();
      var isObjectLike = require_isObjectLike();
      var objectProto = Object.prototype;
      var hasOwnProperty = objectProto.hasOwnProperty;
      var propertyIsEnumerable = objectProto.propertyIsEnumerable;
      var isArguments = baseIsArguments(/* @__PURE__ */ (function() {
        return arguments;
      })()) ? baseIsArguments : function(value) {
        return isObjectLike(value) && hasOwnProperty.call(value, "callee") && !propertyIsEnumerable.call(value, "callee");
      };
      module.exports = isArguments;
    }
  });

  // node_modules/lodash/isArray.js
  var require_isArray = __commonJS({
    "node_modules/lodash/isArray.js"(exports, module) {
      var isArray = Array.isArray;
      module.exports = isArray;
    }
  });

  // node_modules/lodash/stubFalse.js
  var require_stubFalse = __commonJS({
    "node_modules/lodash/stubFalse.js"(exports, module) {
      function stubFalse() {
        return false;
      }
      module.exports = stubFalse;
    }
  });

  // node_modules/lodash/isBuffer.js
  var require_isBuffer = __commonJS({
    "node_modules/lodash/isBuffer.js"(exports, module) {
      var root2 = require_root();
      var stubFalse = require_stubFalse();
      var freeExports = typeof exports == "object" && exports && !exports.nodeType && exports;
      var freeModule = freeExports && typeof module == "object" && module && !module.nodeType && module;
      var moduleExports = freeModule && freeModule.exports === freeExports;
      var Buffer2 = moduleExports ? root2.Buffer : void 0;
      var nativeIsBuffer = Buffer2 ? Buffer2.isBuffer : void 0;
      var isBuffer = nativeIsBuffer || stubFalse;
      module.exports = isBuffer;
    }
  });

  // node_modules/lodash/_isIndex.js
  var require_isIndex = __commonJS({
    "node_modules/lodash/_isIndex.js"(exports, module) {
      var MAX_SAFE_INTEGER = 9007199254740991;
      var reIsUint = /^(?:0|[1-9]\d*)$/;
      function isIndex(value, length) {
        var type = typeof value;
        length = length == null ? MAX_SAFE_INTEGER : length;
        return !!length && (type == "number" || type != "symbol" && reIsUint.test(value)) && (value > -1 && value % 1 == 0 && value < length);
      }
      module.exports = isIndex;
    }
  });

  // node_modules/lodash/isLength.js
  var require_isLength = __commonJS({
    "node_modules/lodash/isLength.js"(exports, module) {
      var MAX_SAFE_INTEGER = 9007199254740991;
      function isLength(value) {
        return typeof value == "number" && value > -1 && value % 1 == 0 && value <= MAX_SAFE_INTEGER;
      }
      module.exports = isLength;
    }
  });

  // node_modules/lodash/_baseIsTypedArray.js
  var require_baseIsTypedArray = __commonJS({
    "node_modules/lodash/_baseIsTypedArray.js"(exports, module) {
      var baseGetTag = require_baseGetTag();
      var isLength = require_isLength();
      var isObjectLike = require_isObjectLike();
      var argsTag = "[object Arguments]";
      var arrayTag = "[object Array]";
      var boolTag = "[object Boolean]";
      var dateTag = "[object Date]";
      var errorTag = "[object Error]";
      var funcTag = "[object Function]";
      var mapTag = "[object Map]";
      var numberTag = "[object Number]";
      var objectTag = "[object Object]";
      var regexpTag = "[object RegExp]";
      var setTag = "[object Set]";
      var stringTag = "[object String]";
      var weakMapTag = "[object WeakMap]";
      var arrayBufferTag = "[object ArrayBuffer]";
      var dataViewTag = "[object DataView]";
      var float32Tag = "[object Float32Array]";
      var float64Tag = "[object Float64Array]";
      var int8Tag = "[object Int8Array]";
      var int16Tag = "[object Int16Array]";
      var int32Tag = "[object Int32Array]";
      var uint8Tag = "[object Uint8Array]";
      var uint8ClampedTag = "[object Uint8ClampedArray]";
      var uint16Tag = "[object Uint16Array]";
      var uint32Tag = "[object Uint32Array]";
      var typedArrayTags = {};
      typedArrayTags[float32Tag] = typedArrayTags[float64Tag] = typedArrayTags[int8Tag] = typedArrayTags[int16Tag] = typedArrayTags[int32Tag] = typedArrayTags[uint8Tag] = typedArrayTags[uint8ClampedTag] = typedArrayTags[uint16Tag] = typedArrayTags[uint32Tag] = true;
      typedArrayTags[argsTag] = typedArrayTags[arrayTag] = typedArrayTags[arrayBufferTag] = typedArrayTags[boolTag] = typedArrayTags[dataViewTag] = typedArrayTags[dateTag] = typedArrayTags[errorTag] = typedArrayTags[funcTag] = typedArrayTags[mapTag] = typedArrayTags[numberTag] = typedArrayTags[objectTag] = typedArrayTags[regexpTag] = typedArrayTags[setTag] = typedArrayTags[stringTag] = typedArrayTags[weakMapTag] = false;
      function baseIsTypedArray(value) {
        return isObjectLike(value) && isLength(value.length) && !!typedArrayTags[baseGetTag(value)];
      }
      module.exports = baseIsTypedArray;
    }
  });

  // node_modules/lodash/_baseUnary.js
  var require_baseUnary = __commonJS({
    "node_modules/lodash/_baseUnary.js"(exports, module) {
      function baseUnary(func) {
        return function(value) {
          return func(value);
        };
      }
      module.exports = baseUnary;
    }
  });

  // node_modules/lodash/_nodeUtil.js
  var require_nodeUtil = __commonJS({
    "node_modules/lodash/_nodeUtil.js"(exports, module) {
      var freeGlobal = require_freeGlobal();
      var freeExports = typeof exports == "object" && exports && !exports.nodeType && exports;
      var freeModule = freeExports && typeof module == "object" && module && !module.nodeType && module;
      var moduleExports = freeModule && freeModule.exports === freeExports;
      var freeProcess = moduleExports && freeGlobal.process;
      var nodeUtil = (function() {
        try {
          var types = freeModule && freeModule.require && freeModule.require("util").types;
          if (types) {
            return types;
          }
          return freeProcess && freeProcess.binding && freeProcess.binding("util");
        } catch (e) {
        }
      })();
      module.exports = nodeUtil;
    }
  });

  // node_modules/lodash/isTypedArray.js
  var require_isTypedArray = __commonJS({
    "node_modules/lodash/isTypedArray.js"(exports, module) {
      var baseIsTypedArray = require_baseIsTypedArray();
      var baseUnary = require_baseUnary();
      var nodeUtil = require_nodeUtil();
      var nodeIsTypedArray = nodeUtil && nodeUtil.isTypedArray;
      var isTypedArray = nodeIsTypedArray ? baseUnary(nodeIsTypedArray) : baseIsTypedArray;
      module.exports = isTypedArray;
    }
  });

  // node_modules/lodash/_arrayLikeKeys.js
  var require_arrayLikeKeys = __commonJS({
    "node_modules/lodash/_arrayLikeKeys.js"(exports, module) {
      var baseTimes = require_baseTimes();
      var isArguments = require_isArguments();
      var isArray = require_isArray();
      var isBuffer = require_isBuffer();
      var isIndex = require_isIndex();
      var isTypedArray = require_isTypedArray();
      var objectProto = Object.prototype;
      var hasOwnProperty = objectProto.hasOwnProperty;
      function arrayLikeKeys(value, inherited) {
        var isArr = isArray(value), isArg = !isArr && isArguments(value), isBuff = !isArr && !isArg && isBuffer(value), isType = !isArr && !isArg && !isBuff && isTypedArray(value), skipIndexes = isArr || isArg || isBuff || isType, result = skipIndexes ? baseTimes(value.length, String) : [], length = result.length;
        for (var key in value) {
          if ((inherited || hasOwnProperty.call(value, key)) && !(skipIndexes && // Safari 9 has enumerable `arguments.length` in strict mode.
          (key == "length" || // Node.js 0.10 has enumerable non-index properties on buffers.
          isBuff && (key == "offset" || key == "parent") || // PhantomJS 2 has enumerable non-index properties on typed arrays.
          isType && (key == "buffer" || key == "byteLength" || key == "byteOffset") || // Skip index properties.
          isIndex(key, length)))) {
            result.push(key);
          }
        }
        return result;
      }
      module.exports = arrayLikeKeys;
    }
  });

  // node_modules/lodash/_isPrototype.js
  var require_isPrototype = __commonJS({
    "node_modules/lodash/_isPrototype.js"(exports, module) {
      var objectProto = Object.prototype;
      function isPrototype(value) {
        var Ctor = value && value.constructor, proto = typeof Ctor == "function" && Ctor.prototype || objectProto;
        return value === proto;
      }
      module.exports = isPrototype;
    }
  });

  // node_modules/lodash/_overArg.js
  var require_overArg = __commonJS({
    "node_modules/lodash/_overArg.js"(exports, module) {
      function overArg(func, transform2) {
        return function(arg) {
          return func(transform2(arg));
        };
      }
      module.exports = overArg;
    }
  });

  // node_modules/lodash/_nativeKeys.js
  var require_nativeKeys = __commonJS({
    "node_modules/lodash/_nativeKeys.js"(exports, module) {
      var overArg = require_overArg();
      var nativeKeys = overArg(Object.keys, Object);
      module.exports = nativeKeys;
    }
  });

  // node_modules/lodash/_baseKeys.js
  var require_baseKeys = __commonJS({
    "node_modules/lodash/_baseKeys.js"(exports, module) {
      var isPrototype = require_isPrototype();
      var nativeKeys = require_nativeKeys();
      var objectProto = Object.prototype;
      var hasOwnProperty = objectProto.hasOwnProperty;
      function baseKeys(object) {
        if (!isPrototype(object)) {
          return nativeKeys(object);
        }
        var result = [];
        for (var key in Object(object)) {
          if (hasOwnProperty.call(object, key) && key != "constructor") {
            result.push(key);
          }
        }
        return result;
      }
      module.exports = baseKeys;
    }
  });

  // node_modules/lodash/isArrayLike.js
  var require_isArrayLike = __commonJS({
    "node_modules/lodash/isArrayLike.js"(exports, module) {
      var isFunction = require_isFunction();
      var isLength = require_isLength();
      function isArrayLike(value) {
        return value != null && isLength(value.length) && !isFunction(value);
      }
      module.exports = isArrayLike;
    }
  });

  // node_modules/lodash/keys.js
  var require_keys = __commonJS({
    "node_modules/lodash/keys.js"(exports, module) {
      var arrayLikeKeys = require_arrayLikeKeys();
      var baseKeys = require_baseKeys();
      var isArrayLike = require_isArrayLike();
      function keys(object) {
        return isArrayLike(object) ? arrayLikeKeys(object) : baseKeys(object);
      }
      module.exports = keys;
    }
  });

  // node_modules/lodash/_baseAssign.js
  var require_baseAssign = __commonJS({
    "node_modules/lodash/_baseAssign.js"(exports, module) {
      var copyObject = require_copyObject();
      var keys = require_keys();
      function baseAssign(object, source) {
        return object && copyObject(source, keys(source), object);
      }
      module.exports = baseAssign;
    }
  });

  // node_modules/lodash/_nativeKeysIn.js
  var require_nativeKeysIn = __commonJS({
    "node_modules/lodash/_nativeKeysIn.js"(exports, module) {
      function nativeKeysIn(object) {
        var result = [];
        if (object != null) {
          for (var key in Object(object)) {
            result.push(key);
          }
        }
        return result;
      }
      module.exports = nativeKeysIn;
    }
  });

  // node_modules/lodash/_baseKeysIn.js
  var require_baseKeysIn = __commonJS({
    "node_modules/lodash/_baseKeysIn.js"(exports, module) {
      var isObject = require_isObject();
      var isPrototype = require_isPrototype();
      var nativeKeysIn = require_nativeKeysIn();
      var objectProto = Object.prototype;
      var hasOwnProperty = objectProto.hasOwnProperty;
      function baseKeysIn(object) {
        if (!isObject(object)) {
          return nativeKeysIn(object);
        }
        var isProto = isPrototype(object), result = [];
        for (var key in object) {
          if (!(key == "constructor" && (isProto || !hasOwnProperty.call(object, key)))) {
            result.push(key);
          }
        }
        return result;
      }
      module.exports = baseKeysIn;
    }
  });

  // node_modules/lodash/keysIn.js
  var require_keysIn = __commonJS({
    "node_modules/lodash/keysIn.js"(exports, module) {
      var arrayLikeKeys = require_arrayLikeKeys();
      var baseKeysIn = require_baseKeysIn();
      var isArrayLike = require_isArrayLike();
      function keysIn(object) {
        return isArrayLike(object) ? arrayLikeKeys(object, true) : baseKeysIn(object);
      }
      module.exports = keysIn;
    }
  });

  // node_modules/lodash/_baseAssignIn.js
  var require_baseAssignIn = __commonJS({
    "node_modules/lodash/_baseAssignIn.js"(exports, module) {
      var copyObject = require_copyObject();
      var keysIn = require_keysIn();
      function baseAssignIn(object, source) {
        return object && copyObject(source, keysIn(source), object);
      }
      module.exports = baseAssignIn;
    }
  });

  // node_modules/lodash/_cloneBuffer.js
  var require_cloneBuffer = __commonJS({
    "node_modules/lodash/_cloneBuffer.js"(exports, module) {
      var root2 = require_root();
      var freeExports = typeof exports == "object" && exports && !exports.nodeType && exports;
      var freeModule = freeExports && typeof module == "object" && module && !module.nodeType && module;
      var moduleExports = freeModule && freeModule.exports === freeExports;
      var Buffer2 = moduleExports ? root2.Buffer : void 0;
      var allocUnsafe = Buffer2 ? Buffer2.allocUnsafe : void 0;
      function cloneBuffer(buffer, isDeep) {
        if (isDeep) {
          return buffer.slice();
        }
        var length = buffer.length, result = allocUnsafe ? allocUnsafe(length) : new buffer.constructor(length);
        buffer.copy(result);
        return result;
      }
      module.exports = cloneBuffer;
    }
  });

  // node_modules/lodash/_copyArray.js
  var require_copyArray = __commonJS({
    "node_modules/lodash/_copyArray.js"(exports, module) {
      function copyArray(source, array2) {
        var index = -1, length = source.length;
        array2 || (array2 = Array(length));
        while (++index < length) {
          array2[index] = source[index];
        }
        return array2;
      }
      module.exports = copyArray;
    }
  });

  // node_modules/lodash/_arrayFilter.js
  var require_arrayFilter = __commonJS({
    "node_modules/lodash/_arrayFilter.js"(exports, module) {
      function arrayFilter(array2, predicate) {
        var index = -1, length = array2 == null ? 0 : array2.length, resIndex = 0, result = [];
        while (++index < length) {
          var value = array2[index];
          if (predicate(value, index, array2)) {
            result[resIndex++] = value;
          }
        }
        return result;
      }
      module.exports = arrayFilter;
    }
  });

  // node_modules/lodash/stubArray.js
  var require_stubArray = __commonJS({
    "node_modules/lodash/stubArray.js"(exports, module) {
      function stubArray() {
        return [];
      }
      module.exports = stubArray;
    }
  });

  // node_modules/lodash/_getSymbols.js
  var require_getSymbols = __commonJS({
    "node_modules/lodash/_getSymbols.js"(exports, module) {
      var arrayFilter = require_arrayFilter();
      var stubArray = require_stubArray();
      var objectProto = Object.prototype;
      var propertyIsEnumerable = objectProto.propertyIsEnumerable;
      var nativeGetSymbols = Object.getOwnPropertySymbols;
      var getSymbols = !nativeGetSymbols ? stubArray : function(object) {
        if (object == null) {
          return [];
        }
        object = Object(object);
        return arrayFilter(nativeGetSymbols(object), function(symbol) {
          return propertyIsEnumerable.call(object, symbol);
        });
      };
      module.exports = getSymbols;
    }
  });

  // node_modules/lodash/_copySymbols.js
  var require_copySymbols = __commonJS({
    "node_modules/lodash/_copySymbols.js"(exports, module) {
      var copyObject = require_copyObject();
      var getSymbols = require_getSymbols();
      function copySymbols(source, object) {
        return copyObject(source, getSymbols(source), object);
      }
      module.exports = copySymbols;
    }
  });

  // node_modules/lodash/_arrayPush.js
  var require_arrayPush = __commonJS({
    "node_modules/lodash/_arrayPush.js"(exports, module) {
      function arrayPush(array2, values) {
        var index = -1, length = values.length, offset = array2.length;
        while (++index < length) {
          array2[offset + index] = values[index];
        }
        return array2;
      }
      module.exports = arrayPush;
    }
  });

  // node_modules/lodash/_getPrototype.js
  var require_getPrototype = __commonJS({
    "node_modules/lodash/_getPrototype.js"(exports, module) {
      var overArg = require_overArg();
      var getPrototype = overArg(Object.getPrototypeOf, Object);
      module.exports = getPrototype;
    }
  });

  // node_modules/lodash/_getSymbolsIn.js
  var require_getSymbolsIn = __commonJS({
    "node_modules/lodash/_getSymbolsIn.js"(exports, module) {
      var arrayPush = require_arrayPush();
      var getPrototype = require_getPrototype();
      var getSymbols = require_getSymbols();
      var stubArray = require_stubArray();
      var nativeGetSymbols = Object.getOwnPropertySymbols;
      var getSymbolsIn = !nativeGetSymbols ? stubArray : function(object) {
        var result = [];
        while (object) {
          arrayPush(result, getSymbols(object));
          object = getPrototype(object);
        }
        return result;
      };
      module.exports = getSymbolsIn;
    }
  });

  // node_modules/lodash/_copySymbolsIn.js
  var require_copySymbolsIn = __commonJS({
    "node_modules/lodash/_copySymbolsIn.js"(exports, module) {
      var copyObject = require_copyObject();
      var getSymbolsIn = require_getSymbolsIn();
      function copySymbolsIn(source, object) {
        return copyObject(source, getSymbolsIn(source), object);
      }
      module.exports = copySymbolsIn;
    }
  });

  // node_modules/lodash/_baseGetAllKeys.js
  var require_baseGetAllKeys = __commonJS({
    "node_modules/lodash/_baseGetAllKeys.js"(exports, module) {
      var arrayPush = require_arrayPush();
      var isArray = require_isArray();
      function baseGetAllKeys(object, keysFunc, symbolsFunc) {
        var result = keysFunc(object);
        return isArray(object) ? result : arrayPush(result, symbolsFunc(object));
      }
      module.exports = baseGetAllKeys;
    }
  });

  // node_modules/lodash/_getAllKeys.js
  var require_getAllKeys = __commonJS({
    "node_modules/lodash/_getAllKeys.js"(exports, module) {
      var baseGetAllKeys = require_baseGetAllKeys();
      var getSymbols = require_getSymbols();
      var keys = require_keys();
      function getAllKeys(object) {
        return baseGetAllKeys(object, keys, getSymbols);
      }
      module.exports = getAllKeys;
    }
  });

  // node_modules/lodash/_getAllKeysIn.js
  var require_getAllKeysIn = __commonJS({
    "node_modules/lodash/_getAllKeysIn.js"(exports, module) {
      var baseGetAllKeys = require_baseGetAllKeys();
      var getSymbolsIn = require_getSymbolsIn();
      var keysIn = require_keysIn();
      function getAllKeysIn(object) {
        return baseGetAllKeys(object, keysIn, getSymbolsIn);
      }
      module.exports = getAllKeysIn;
    }
  });

  // node_modules/lodash/_DataView.js
  var require_DataView = __commonJS({
    "node_modules/lodash/_DataView.js"(exports, module) {
      var getNative = require_getNative();
      var root2 = require_root();
      var DataView = getNative(root2, "DataView");
      module.exports = DataView;
    }
  });

  // node_modules/lodash/_Promise.js
  var require_Promise = __commonJS({
    "node_modules/lodash/_Promise.js"(exports, module) {
      var getNative = require_getNative();
      var root2 = require_root();
      var Promise2 = getNative(root2, "Promise");
      module.exports = Promise2;
    }
  });

  // node_modules/lodash/_Set.js
  var require_Set = __commonJS({
    "node_modules/lodash/_Set.js"(exports, module) {
      var getNative = require_getNative();
      var root2 = require_root();
      var Set2 = getNative(root2, "Set");
      module.exports = Set2;
    }
  });

  // node_modules/lodash/_WeakMap.js
  var require_WeakMap = __commonJS({
    "node_modules/lodash/_WeakMap.js"(exports, module) {
      var getNative = require_getNative();
      var root2 = require_root();
      var WeakMap = getNative(root2, "WeakMap");
      module.exports = WeakMap;
    }
  });

  // node_modules/lodash/_getTag.js
  var require_getTag = __commonJS({
    "node_modules/lodash/_getTag.js"(exports, module) {
      var DataView = require_DataView();
      var Map2 = require_Map();
      var Promise2 = require_Promise();
      var Set2 = require_Set();
      var WeakMap = require_WeakMap();
      var baseGetTag = require_baseGetTag();
      var toSource = require_toSource();
      var mapTag = "[object Map]";
      var objectTag = "[object Object]";
      var promiseTag = "[object Promise]";
      var setTag = "[object Set]";
      var weakMapTag = "[object WeakMap]";
      var dataViewTag = "[object DataView]";
      var dataViewCtorString = toSource(DataView);
      var mapCtorString = toSource(Map2);
      var promiseCtorString = toSource(Promise2);
      var setCtorString = toSource(Set2);
      var weakMapCtorString = toSource(WeakMap);
      var getTag = baseGetTag;
      if (DataView && getTag(new DataView(new ArrayBuffer(1))) != dataViewTag || Map2 && getTag(new Map2()) != mapTag || Promise2 && getTag(Promise2.resolve()) != promiseTag || Set2 && getTag(new Set2()) != setTag || WeakMap && getTag(new WeakMap()) != weakMapTag) {
        getTag = function(value) {
          var result = baseGetTag(value), Ctor = result == objectTag ? value.constructor : void 0, ctorString = Ctor ? toSource(Ctor) : "";
          if (ctorString) {
            switch (ctorString) {
              case dataViewCtorString:
                return dataViewTag;
              case mapCtorString:
                return mapTag;
              case promiseCtorString:
                return promiseTag;
              case setCtorString:
                return setTag;
              case weakMapCtorString:
                return weakMapTag;
            }
          }
          return result;
        };
      }
      module.exports = getTag;
    }
  });

  // node_modules/lodash/_initCloneArray.js
  var require_initCloneArray = __commonJS({
    "node_modules/lodash/_initCloneArray.js"(exports, module) {
      var objectProto = Object.prototype;
      var hasOwnProperty = objectProto.hasOwnProperty;
      function initCloneArray(array2) {
        var length = array2.length, result = new array2.constructor(length);
        if (length && typeof array2[0] == "string" && hasOwnProperty.call(array2, "index")) {
          result.index = array2.index;
          result.input = array2.input;
        }
        return result;
      }
      module.exports = initCloneArray;
    }
  });

  // node_modules/lodash/_Uint8Array.js
  var require_Uint8Array = __commonJS({
    "node_modules/lodash/_Uint8Array.js"(exports, module) {
      var root2 = require_root();
      var Uint8Array2 = root2.Uint8Array;
      module.exports = Uint8Array2;
    }
  });

  // node_modules/lodash/_cloneArrayBuffer.js
  var require_cloneArrayBuffer = __commonJS({
    "node_modules/lodash/_cloneArrayBuffer.js"(exports, module) {
      var Uint8Array2 = require_Uint8Array();
      function cloneArrayBuffer(arrayBuffer) {
        var result = new arrayBuffer.constructor(arrayBuffer.byteLength);
        new Uint8Array2(result).set(new Uint8Array2(arrayBuffer));
        return result;
      }
      module.exports = cloneArrayBuffer;
    }
  });

  // node_modules/lodash/_cloneDataView.js
  var require_cloneDataView = __commonJS({
    "node_modules/lodash/_cloneDataView.js"(exports, module) {
      var cloneArrayBuffer = require_cloneArrayBuffer();
      function cloneDataView(dataView, isDeep) {
        var buffer = isDeep ? cloneArrayBuffer(dataView.buffer) : dataView.buffer;
        return new dataView.constructor(buffer, dataView.byteOffset, dataView.byteLength);
      }
      module.exports = cloneDataView;
    }
  });

  // node_modules/lodash/_cloneRegExp.js
  var require_cloneRegExp = __commonJS({
    "node_modules/lodash/_cloneRegExp.js"(exports, module) {
      var reFlags = /\w*$/;
      function cloneRegExp(regexp) {
        var result = new regexp.constructor(regexp.source, reFlags.exec(regexp));
        result.lastIndex = regexp.lastIndex;
        return result;
      }
      module.exports = cloneRegExp;
    }
  });

  // node_modules/lodash/_cloneSymbol.js
  var require_cloneSymbol = __commonJS({
    "node_modules/lodash/_cloneSymbol.js"(exports, module) {
      var Symbol2 = require_Symbol();
      var symbolProto = Symbol2 ? Symbol2.prototype : void 0;
      var symbolValueOf = symbolProto ? symbolProto.valueOf : void 0;
      function cloneSymbol(symbol) {
        return symbolValueOf ? Object(symbolValueOf.call(symbol)) : {};
      }
      module.exports = cloneSymbol;
    }
  });

  // node_modules/lodash/_cloneTypedArray.js
  var require_cloneTypedArray = __commonJS({
    "node_modules/lodash/_cloneTypedArray.js"(exports, module) {
      var cloneArrayBuffer = require_cloneArrayBuffer();
      function cloneTypedArray(typedArray, isDeep) {
        var buffer = isDeep ? cloneArrayBuffer(typedArray.buffer) : typedArray.buffer;
        return new typedArray.constructor(buffer, typedArray.byteOffset, typedArray.length);
      }
      module.exports = cloneTypedArray;
    }
  });

  // node_modules/lodash/_initCloneByTag.js
  var require_initCloneByTag = __commonJS({
    "node_modules/lodash/_initCloneByTag.js"(exports, module) {
      var cloneArrayBuffer = require_cloneArrayBuffer();
      var cloneDataView = require_cloneDataView();
      var cloneRegExp = require_cloneRegExp();
      var cloneSymbol = require_cloneSymbol();
      var cloneTypedArray = require_cloneTypedArray();
      var boolTag = "[object Boolean]";
      var dateTag = "[object Date]";
      var mapTag = "[object Map]";
      var numberTag = "[object Number]";
      var regexpTag = "[object RegExp]";
      var setTag = "[object Set]";
      var stringTag = "[object String]";
      var symbolTag = "[object Symbol]";
      var arrayBufferTag = "[object ArrayBuffer]";
      var dataViewTag = "[object DataView]";
      var float32Tag = "[object Float32Array]";
      var float64Tag = "[object Float64Array]";
      var int8Tag = "[object Int8Array]";
      var int16Tag = "[object Int16Array]";
      var int32Tag = "[object Int32Array]";
      var uint8Tag = "[object Uint8Array]";
      var uint8ClampedTag = "[object Uint8ClampedArray]";
      var uint16Tag = "[object Uint16Array]";
      var uint32Tag = "[object Uint32Array]";
      function initCloneByTag(object, tag, isDeep) {
        var Ctor = object.constructor;
        switch (tag) {
          case arrayBufferTag:
            return cloneArrayBuffer(object);
          case boolTag:
          case dateTag:
            return new Ctor(+object);
          case dataViewTag:
            return cloneDataView(object, isDeep);
          case float32Tag:
          case float64Tag:
          case int8Tag:
          case int16Tag:
          case int32Tag:
          case uint8Tag:
          case uint8ClampedTag:
          case uint16Tag:
          case uint32Tag:
            return cloneTypedArray(object, isDeep);
          case mapTag:
            return new Ctor();
          case numberTag:
          case stringTag:
            return new Ctor(object);
          case regexpTag:
            return cloneRegExp(object);
          case setTag:
            return new Ctor();
          case symbolTag:
            return cloneSymbol(object);
        }
      }
      module.exports = initCloneByTag;
    }
  });

  // node_modules/lodash/_baseCreate.js
  var require_baseCreate = __commonJS({
    "node_modules/lodash/_baseCreate.js"(exports, module) {
      var isObject = require_isObject();
      var objectCreate = Object.create;
      var baseCreate = /* @__PURE__ */ (function() {
        function object() {
        }
        return function(proto) {
          if (!isObject(proto)) {
            return {};
          }
          if (objectCreate) {
            return objectCreate(proto);
          }
          object.prototype = proto;
          var result = new object();
          object.prototype = void 0;
          return result;
        };
      })();
      module.exports = baseCreate;
    }
  });

  // node_modules/lodash/_initCloneObject.js
  var require_initCloneObject = __commonJS({
    "node_modules/lodash/_initCloneObject.js"(exports, module) {
      var baseCreate = require_baseCreate();
      var getPrototype = require_getPrototype();
      var isPrototype = require_isPrototype();
      function initCloneObject(object) {
        return typeof object.constructor == "function" && !isPrototype(object) ? baseCreate(getPrototype(object)) : {};
      }
      module.exports = initCloneObject;
    }
  });

  // node_modules/lodash/_baseIsMap.js
  var require_baseIsMap = __commonJS({
    "node_modules/lodash/_baseIsMap.js"(exports, module) {
      var getTag = require_getTag();
      var isObjectLike = require_isObjectLike();
      var mapTag = "[object Map]";
      function baseIsMap(value) {
        return isObjectLike(value) && getTag(value) == mapTag;
      }
      module.exports = baseIsMap;
    }
  });

  // node_modules/lodash/isMap.js
  var require_isMap = __commonJS({
    "node_modules/lodash/isMap.js"(exports, module) {
      var baseIsMap = require_baseIsMap();
      var baseUnary = require_baseUnary();
      var nodeUtil = require_nodeUtil();
      var nodeIsMap = nodeUtil && nodeUtil.isMap;
      var isMap = nodeIsMap ? baseUnary(nodeIsMap) : baseIsMap;
      module.exports = isMap;
    }
  });

  // node_modules/lodash/_baseIsSet.js
  var require_baseIsSet = __commonJS({
    "node_modules/lodash/_baseIsSet.js"(exports, module) {
      var getTag = require_getTag();
      var isObjectLike = require_isObjectLike();
      var setTag = "[object Set]";
      function baseIsSet(value) {
        return isObjectLike(value) && getTag(value) == setTag;
      }
      module.exports = baseIsSet;
    }
  });

  // node_modules/lodash/isSet.js
  var require_isSet = __commonJS({
    "node_modules/lodash/isSet.js"(exports, module) {
      var baseIsSet = require_baseIsSet();
      var baseUnary = require_baseUnary();
      var nodeUtil = require_nodeUtil();
      var nodeIsSet = nodeUtil && nodeUtil.isSet;
      var isSet = nodeIsSet ? baseUnary(nodeIsSet) : baseIsSet;
      module.exports = isSet;
    }
  });

  // node_modules/lodash/_baseClone.js
  var require_baseClone = __commonJS({
    "node_modules/lodash/_baseClone.js"(exports, module) {
      var Stack = require_Stack();
      var arrayEach = require_arrayEach();
      var assignValue = require_assignValue();
      var baseAssign = require_baseAssign();
      var baseAssignIn = require_baseAssignIn();
      var cloneBuffer = require_cloneBuffer();
      var copyArray = require_copyArray();
      var copySymbols = require_copySymbols();
      var copySymbolsIn = require_copySymbolsIn();
      var getAllKeys = require_getAllKeys();
      var getAllKeysIn = require_getAllKeysIn();
      var getTag = require_getTag();
      var initCloneArray = require_initCloneArray();
      var initCloneByTag = require_initCloneByTag();
      var initCloneObject = require_initCloneObject();
      var isArray = require_isArray();
      var isBuffer = require_isBuffer();
      var isMap = require_isMap();
      var isObject = require_isObject();
      var isSet = require_isSet();
      var keys = require_keys();
      var keysIn = require_keysIn();
      var CLONE_DEEP_FLAG = 1;
      var CLONE_FLAT_FLAG = 2;
      var CLONE_SYMBOLS_FLAG = 4;
      var argsTag = "[object Arguments]";
      var arrayTag = "[object Array]";
      var boolTag = "[object Boolean]";
      var dateTag = "[object Date]";
      var errorTag = "[object Error]";
      var funcTag = "[object Function]";
      var genTag = "[object GeneratorFunction]";
      var mapTag = "[object Map]";
      var numberTag = "[object Number]";
      var objectTag = "[object Object]";
      var regexpTag = "[object RegExp]";
      var setTag = "[object Set]";
      var stringTag = "[object String]";
      var symbolTag = "[object Symbol]";
      var weakMapTag = "[object WeakMap]";
      var arrayBufferTag = "[object ArrayBuffer]";
      var dataViewTag = "[object DataView]";
      var float32Tag = "[object Float32Array]";
      var float64Tag = "[object Float64Array]";
      var int8Tag = "[object Int8Array]";
      var int16Tag = "[object Int16Array]";
      var int32Tag = "[object Int32Array]";
      var uint8Tag = "[object Uint8Array]";
      var uint8ClampedTag = "[object Uint8ClampedArray]";
      var uint16Tag = "[object Uint16Array]";
      var uint32Tag = "[object Uint32Array]";
      var cloneableTags = {};
      cloneableTags[argsTag] = cloneableTags[arrayTag] = cloneableTags[arrayBufferTag] = cloneableTags[dataViewTag] = cloneableTags[boolTag] = cloneableTags[dateTag] = cloneableTags[float32Tag] = cloneableTags[float64Tag] = cloneableTags[int8Tag] = cloneableTags[int16Tag] = cloneableTags[int32Tag] = cloneableTags[mapTag] = cloneableTags[numberTag] = cloneableTags[objectTag] = cloneableTags[regexpTag] = cloneableTags[setTag] = cloneableTags[stringTag] = cloneableTags[symbolTag] = cloneableTags[uint8Tag] = cloneableTags[uint8ClampedTag] = cloneableTags[uint16Tag] = cloneableTags[uint32Tag] = true;
      cloneableTags[errorTag] = cloneableTags[funcTag] = cloneableTags[weakMapTag] = false;
      function baseClone(value, bitmask, customizer, key, object, stack) {
        var result, isDeep = bitmask & CLONE_DEEP_FLAG, isFlat = bitmask & CLONE_FLAT_FLAG, isFull = bitmask & CLONE_SYMBOLS_FLAG;
        if (customizer) {
          result = object ? customizer(value, key, object, stack) : customizer(value);
        }
        if (result !== void 0) {
          return result;
        }
        if (!isObject(value)) {
          return value;
        }
        var isArr = isArray(value);
        if (isArr) {
          result = initCloneArray(value);
          if (!isDeep) {
            return copyArray(value, result);
          }
        } else {
          var tag = getTag(value), isFunc = tag == funcTag || tag == genTag;
          if (isBuffer(value)) {
            return cloneBuffer(value, isDeep);
          }
          if (tag == objectTag || tag == argsTag || isFunc && !object) {
            result = isFlat || isFunc ? {} : initCloneObject(value);
            if (!isDeep) {
              return isFlat ? copySymbolsIn(value, baseAssignIn(result, value)) : copySymbols(value, baseAssign(result, value));
            }
          } else {
            if (!cloneableTags[tag]) {
              return object ? value : {};
            }
            result = initCloneByTag(value, tag, isDeep);
          }
        }
        stack || (stack = new Stack());
        var stacked = stack.get(value);
        if (stacked) {
          return stacked;
        }
        stack.set(value, result);
        if (isSet(value)) {
          value.forEach(function(subValue) {
            result.add(baseClone(subValue, bitmask, customizer, subValue, value, stack));
          });
        } else if (isMap(value)) {
          value.forEach(function(subValue, key2) {
            result.set(key2, baseClone(subValue, bitmask, customizer, key2, value, stack));
          });
        }
        var keysFunc = isFull ? isFlat ? getAllKeysIn : getAllKeys : isFlat ? keysIn : keys;
        var props = isArr ? void 0 : keysFunc(value);
        arrayEach(props || value, function(subValue, key2) {
          if (props) {
            key2 = subValue;
            subValue = value[key2];
          }
          assignValue(result, key2, baseClone(subValue, bitmask, customizer, key2, value, stack));
        });
        return result;
      }
      module.exports = baseClone;
    }
  });

  // node_modules/lodash/clone.js
  var require_clone = __commonJS({
    "node_modules/lodash/clone.js"(exports, module) {
      var baseClone = require_baseClone();
      var CLONE_SYMBOLS_FLAG = 4;
      function clone(value) {
        return baseClone(value, CLONE_SYMBOLS_FLAG);
      }
      module.exports = clone;
    }
  });

  // node_modules/lodash/constant.js
  var require_constant = __commonJS({
    "node_modules/lodash/constant.js"(exports, module) {
      function constant(value) {
        return function() {
          return value;
        };
      }
      module.exports = constant;
    }
  });

  // node_modules/lodash/_createBaseFor.js
  var require_createBaseFor = __commonJS({
    "node_modules/lodash/_createBaseFor.js"(exports, module) {
      function createBaseFor(fromRight) {
        return function(object, iteratee, keysFunc) {
          var index = -1, iterable = Object(object), props = keysFunc(object), length = props.length;
          while (length--) {
            var key = props[fromRight ? length : ++index];
            if (iteratee(iterable[key], key, iterable) === false) {
              break;
            }
          }
          return object;
        };
      }
      module.exports = createBaseFor;
    }
  });

  // node_modules/lodash/_baseFor.js
  var require_baseFor = __commonJS({
    "node_modules/lodash/_baseFor.js"(exports, module) {
      var createBaseFor = require_createBaseFor();
      var baseFor = createBaseFor();
      module.exports = baseFor;
    }
  });

  // node_modules/lodash/_baseForOwn.js
  var require_baseForOwn = __commonJS({
    "node_modules/lodash/_baseForOwn.js"(exports, module) {
      var baseFor = require_baseFor();
      var keys = require_keys();
      function baseForOwn(object, iteratee) {
        return object && baseFor(object, iteratee, keys);
      }
      module.exports = baseForOwn;
    }
  });

  // node_modules/lodash/_createBaseEach.js
  var require_createBaseEach = __commonJS({
    "node_modules/lodash/_createBaseEach.js"(exports, module) {
      var isArrayLike = require_isArrayLike();
      function createBaseEach(eachFunc, fromRight) {
        return function(collection, iteratee) {
          if (collection == null) {
            return collection;
          }
          if (!isArrayLike(collection)) {
            return eachFunc(collection, iteratee);
          }
          var length = collection.length, index = fromRight ? length : -1, iterable = Object(collection);
          while (fromRight ? index-- : ++index < length) {
            if (iteratee(iterable[index], index, iterable) === false) {
              break;
            }
          }
          return collection;
        };
      }
      module.exports = createBaseEach;
    }
  });

  // node_modules/lodash/_baseEach.js
  var require_baseEach = __commonJS({
    "node_modules/lodash/_baseEach.js"(exports, module) {
      var baseForOwn = require_baseForOwn();
      var createBaseEach = require_createBaseEach();
      var baseEach = createBaseEach(baseForOwn);
      module.exports = baseEach;
    }
  });

  // node_modules/lodash/identity.js
  var require_identity = __commonJS({
    "node_modules/lodash/identity.js"(exports, module) {
      function identity3(value) {
        return value;
      }
      module.exports = identity3;
    }
  });

  // node_modules/lodash/_castFunction.js
  var require_castFunction = __commonJS({
    "node_modules/lodash/_castFunction.js"(exports, module) {
      var identity3 = require_identity();
      function castFunction(value) {
        return typeof value == "function" ? value : identity3;
      }
      module.exports = castFunction;
    }
  });

  // node_modules/lodash/forEach.js
  var require_forEach = __commonJS({
    "node_modules/lodash/forEach.js"(exports, module) {
      var arrayEach = require_arrayEach();
      var baseEach = require_baseEach();
      var castFunction = require_castFunction();
      var isArray = require_isArray();
      function forEach(collection, iteratee) {
        var func = isArray(collection) ? arrayEach : baseEach;
        return func(collection, castFunction(iteratee));
      }
      module.exports = forEach;
    }
  });

  // node_modules/lodash/each.js
  var require_each = __commonJS({
    "node_modules/lodash/each.js"(exports, module) {
      module.exports = require_forEach();
    }
  });

  // node_modules/lodash/_baseFilter.js
  var require_baseFilter = __commonJS({
    "node_modules/lodash/_baseFilter.js"(exports, module) {
      var baseEach = require_baseEach();
      function baseFilter(collection, predicate) {
        var result = [];
        baseEach(collection, function(value, index, collection2) {
          if (predicate(value, index, collection2)) {
            result.push(value);
          }
        });
        return result;
      }
      module.exports = baseFilter;
    }
  });

  // node_modules/lodash/_setCacheAdd.js
  var require_setCacheAdd = __commonJS({
    "node_modules/lodash/_setCacheAdd.js"(exports, module) {
      var HASH_UNDEFINED = "__lodash_hash_undefined__";
      function setCacheAdd(value) {
        this.__data__.set(value, HASH_UNDEFINED);
        return this;
      }
      module.exports = setCacheAdd;
    }
  });

  // node_modules/lodash/_setCacheHas.js
  var require_setCacheHas = __commonJS({
    "node_modules/lodash/_setCacheHas.js"(exports, module) {
      function setCacheHas(value) {
        return this.__data__.has(value);
      }
      module.exports = setCacheHas;
    }
  });

  // node_modules/lodash/_SetCache.js
  var require_SetCache = __commonJS({
    "node_modules/lodash/_SetCache.js"(exports, module) {
      var MapCache = require_MapCache();
      var setCacheAdd = require_setCacheAdd();
      var setCacheHas = require_setCacheHas();
      function SetCache(values) {
        var index = -1, length = values == null ? 0 : values.length;
        this.__data__ = new MapCache();
        while (++index < length) {
          this.add(values[index]);
        }
      }
      SetCache.prototype.add = SetCache.prototype.push = setCacheAdd;
      SetCache.prototype.has = setCacheHas;
      module.exports = SetCache;
    }
  });

  // node_modules/lodash/_arraySome.js
  var require_arraySome = __commonJS({
    "node_modules/lodash/_arraySome.js"(exports, module) {
      function arraySome(array2, predicate) {
        var index = -1, length = array2 == null ? 0 : array2.length;
        while (++index < length) {
          if (predicate(array2[index], index, array2)) {
            return true;
          }
        }
        return false;
      }
      module.exports = arraySome;
    }
  });

  // node_modules/lodash/_cacheHas.js
  var require_cacheHas = __commonJS({
    "node_modules/lodash/_cacheHas.js"(exports, module) {
      function cacheHas(cache, key) {
        return cache.has(key);
      }
      module.exports = cacheHas;
    }
  });

  // node_modules/lodash/_equalArrays.js
  var require_equalArrays = __commonJS({
    "node_modules/lodash/_equalArrays.js"(exports, module) {
      var SetCache = require_SetCache();
      var arraySome = require_arraySome();
      var cacheHas = require_cacheHas();
      var COMPARE_PARTIAL_FLAG = 1;
      var COMPARE_UNORDERED_FLAG = 2;
      function equalArrays(array2, other, bitmask, customizer, equalFunc, stack) {
        var isPartial = bitmask & COMPARE_PARTIAL_FLAG, arrLength = array2.length, othLength = other.length;
        if (arrLength != othLength && !(isPartial && othLength > arrLength)) {
          return false;
        }
        var arrStacked = stack.get(array2);
        var othStacked = stack.get(other);
        if (arrStacked && othStacked) {
          return arrStacked == other && othStacked == array2;
        }
        var index = -1, result = true, seen = bitmask & COMPARE_UNORDERED_FLAG ? new SetCache() : void 0;
        stack.set(array2, other);
        stack.set(other, array2);
        while (++index < arrLength) {
          var arrValue = array2[index], othValue = other[index];
          if (customizer) {
            var compared = isPartial ? customizer(othValue, arrValue, index, other, array2, stack) : customizer(arrValue, othValue, index, array2, other, stack);
          }
          if (compared !== void 0) {
            if (compared) {
              continue;
            }
            result = false;
            break;
          }
          if (seen) {
            if (!arraySome(other, function(othValue2, othIndex) {
              if (!cacheHas(seen, othIndex) && (arrValue === othValue2 || equalFunc(arrValue, othValue2, bitmask, customizer, stack))) {
                return seen.push(othIndex);
              }
            })) {
              result = false;
              break;
            }
          } else if (!(arrValue === othValue || equalFunc(arrValue, othValue, bitmask, customizer, stack))) {
            result = false;
            break;
          }
        }
        stack["delete"](array2);
        stack["delete"](other);
        return result;
      }
      module.exports = equalArrays;
    }
  });

  // node_modules/lodash/_mapToArray.js
  var require_mapToArray = __commonJS({
    "node_modules/lodash/_mapToArray.js"(exports, module) {
      function mapToArray(map) {
        var index = -1, result = Array(map.size);
        map.forEach(function(value, key) {
          result[++index] = [key, value];
        });
        return result;
      }
      module.exports = mapToArray;
    }
  });

  // node_modules/lodash/_setToArray.js
  var require_setToArray = __commonJS({
    "node_modules/lodash/_setToArray.js"(exports, module) {
      function setToArray(set3) {
        var index = -1, result = Array(set3.size);
        set3.forEach(function(value) {
          result[++index] = value;
        });
        return result;
      }
      module.exports = setToArray;
    }
  });

  // node_modules/lodash/_equalByTag.js
  var require_equalByTag = __commonJS({
    "node_modules/lodash/_equalByTag.js"(exports, module) {
      var Symbol2 = require_Symbol();
      var Uint8Array2 = require_Uint8Array();
      var eq = require_eq();
      var equalArrays = require_equalArrays();
      var mapToArray = require_mapToArray();
      var setToArray = require_setToArray();
      var COMPARE_PARTIAL_FLAG = 1;
      var COMPARE_UNORDERED_FLAG = 2;
      var boolTag = "[object Boolean]";
      var dateTag = "[object Date]";
      var errorTag = "[object Error]";
      var mapTag = "[object Map]";
      var numberTag = "[object Number]";
      var regexpTag = "[object RegExp]";
      var setTag = "[object Set]";
      var stringTag = "[object String]";
      var symbolTag = "[object Symbol]";
      var arrayBufferTag = "[object ArrayBuffer]";
      var dataViewTag = "[object DataView]";
      var symbolProto = Symbol2 ? Symbol2.prototype : void 0;
      var symbolValueOf = symbolProto ? symbolProto.valueOf : void 0;
      function equalByTag(object, other, tag, bitmask, customizer, equalFunc, stack) {
        switch (tag) {
          case dataViewTag:
            if (object.byteLength != other.byteLength || object.byteOffset != other.byteOffset) {
              return false;
            }
            object = object.buffer;
            other = other.buffer;
          case arrayBufferTag:
            if (object.byteLength != other.byteLength || !equalFunc(new Uint8Array2(object), new Uint8Array2(other))) {
              return false;
            }
            return true;
          case boolTag:
          case dateTag:
          case numberTag:
            return eq(+object, +other);
          case errorTag:
            return object.name == other.name && object.message == other.message;
          case regexpTag:
          case stringTag:
            return object == other + "";
          case mapTag:
            var convert = mapToArray;
          case setTag:
            var isPartial = bitmask & COMPARE_PARTIAL_FLAG;
            convert || (convert = setToArray);
            if (object.size != other.size && !isPartial) {
              return false;
            }
            var stacked = stack.get(object);
            if (stacked) {
              return stacked == other;
            }
            bitmask |= COMPARE_UNORDERED_FLAG;
            stack.set(object, other);
            var result = equalArrays(convert(object), convert(other), bitmask, customizer, equalFunc, stack);
            stack["delete"](object);
            return result;
          case symbolTag:
            if (symbolValueOf) {
              return symbolValueOf.call(object) == symbolValueOf.call(other);
            }
        }
        return false;
      }
      module.exports = equalByTag;
    }
  });

  // node_modules/lodash/_equalObjects.js
  var require_equalObjects = __commonJS({
    "node_modules/lodash/_equalObjects.js"(exports, module) {
      var getAllKeys = require_getAllKeys();
      var COMPARE_PARTIAL_FLAG = 1;
      var objectProto = Object.prototype;
      var hasOwnProperty = objectProto.hasOwnProperty;
      function equalObjects(object, other, bitmask, customizer, equalFunc, stack) {
        var isPartial = bitmask & COMPARE_PARTIAL_FLAG, objProps = getAllKeys(object), objLength = objProps.length, othProps = getAllKeys(other), othLength = othProps.length;
        if (objLength != othLength && !isPartial) {
          return false;
        }
        var index = objLength;
        while (index--) {
          var key = objProps[index];
          if (!(isPartial ? key in other : hasOwnProperty.call(other, key))) {
            return false;
          }
        }
        var objStacked = stack.get(object);
        var othStacked = stack.get(other);
        if (objStacked && othStacked) {
          return objStacked == other && othStacked == object;
        }
        var result = true;
        stack.set(object, other);
        stack.set(other, object);
        var skipCtor = isPartial;
        while (++index < objLength) {
          key = objProps[index];
          var objValue = object[key], othValue = other[key];
          if (customizer) {
            var compared = isPartial ? customizer(othValue, objValue, key, other, object, stack) : customizer(objValue, othValue, key, object, other, stack);
          }
          if (!(compared === void 0 ? objValue === othValue || equalFunc(objValue, othValue, bitmask, customizer, stack) : compared)) {
            result = false;
            break;
          }
          skipCtor || (skipCtor = key == "constructor");
        }
        if (result && !skipCtor) {
          var objCtor = object.constructor, othCtor = other.constructor;
          if (objCtor != othCtor && ("constructor" in object && "constructor" in other) && !(typeof objCtor == "function" && objCtor instanceof objCtor && typeof othCtor == "function" && othCtor instanceof othCtor)) {
            result = false;
          }
        }
        stack["delete"](object);
        stack["delete"](other);
        return result;
      }
      module.exports = equalObjects;
    }
  });

  // node_modules/lodash/_baseIsEqualDeep.js
  var require_baseIsEqualDeep = __commonJS({
    "node_modules/lodash/_baseIsEqualDeep.js"(exports, module) {
      var Stack = require_Stack();
      var equalArrays = require_equalArrays();
      var equalByTag = require_equalByTag();
      var equalObjects = require_equalObjects();
      var getTag = require_getTag();
      var isArray = require_isArray();
      var isBuffer = require_isBuffer();
      var isTypedArray = require_isTypedArray();
      var COMPARE_PARTIAL_FLAG = 1;
      var argsTag = "[object Arguments]";
      var arrayTag = "[object Array]";
      var objectTag = "[object Object]";
      var objectProto = Object.prototype;
      var hasOwnProperty = objectProto.hasOwnProperty;
      function baseIsEqualDeep(object, other, bitmask, customizer, equalFunc, stack) {
        var objIsArr = isArray(object), othIsArr = isArray(other), objTag = objIsArr ? arrayTag : getTag(object), othTag = othIsArr ? arrayTag : getTag(other);
        objTag = objTag == argsTag ? objectTag : objTag;
        othTag = othTag == argsTag ? objectTag : othTag;
        var objIsObj = objTag == objectTag, othIsObj = othTag == objectTag, isSameTag = objTag == othTag;
        if (isSameTag && isBuffer(object)) {
          if (!isBuffer(other)) {
            return false;
          }
          objIsArr = true;
          objIsObj = false;
        }
        if (isSameTag && !objIsObj) {
          stack || (stack = new Stack());
          return objIsArr || isTypedArray(object) ? equalArrays(object, other, bitmask, customizer, equalFunc, stack) : equalByTag(object, other, objTag, bitmask, customizer, equalFunc, stack);
        }
        if (!(bitmask & COMPARE_PARTIAL_FLAG)) {
          var objIsWrapped = objIsObj && hasOwnProperty.call(object, "__wrapped__"), othIsWrapped = othIsObj && hasOwnProperty.call(other, "__wrapped__");
          if (objIsWrapped || othIsWrapped) {
            var objUnwrapped = objIsWrapped ? object.value() : object, othUnwrapped = othIsWrapped ? other.value() : other;
            stack || (stack = new Stack());
            return equalFunc(objUnwrapped, othUnwrapped, bitmask, customizer, stack);
          }
        }
        if (!isSameTag) {
          return false;
        }
        stack || (stack = new Stack());
        return equalObjects(object, other, bitmask, customizer, equalFunc, stack);
      }
      module.exports = baseIsEqualDeep;
    }
  });

  // node_modules/lodash/_baseIsEqual.js
  var require_baseIsEqual = __commonJS({
    "node_modules/lodash/_baseIsEqual.js"(exports, module) {
      var baseIsEqualDeep = require_baseIsEqualDeep();
      var isObjectLike = require_isObjectLike();
      function baseIsEqual(value, other, bitmask, customizer, stack) {
        if (value === other) {
          return true;
        }
        if (value == null || other == null || !isObjectLike(value) && !isObjectLike(other)) {
          return value !== value && other !== other;
        }
        return baseIsEqualDeep(value, other, bitmask, customizer, baseIsEqual, stack);
      }
      module.exports = baseIsEqual;
    }
  });

  // node_modules/lodash/_baseIsMatch.js
  var require_baseIsMatch = __commonJS({
    "node_modules/lodash/_baseIsMatch.js"(exports, module) {
      var Stack = require_Stack();
      var baseIsEqual = require_baseIsEqual();
      var COMPARE_PARTIAL_FLAG = 1;
      var COMPARE_UNORDERED_FLAG = 2;
      function baseIsMatch(object, source, matchData, customizer) {
        var index = matchData.length, length = index, noCustomizer = !customizer;
        if (object == null) {
          return !length;
        }
        object = Object(object);
        while (index--) {
          var data = matchData[index];
          if (noCustomizer && data[2] ? data[1] !== object[data[0]] : !(data[0] in object)) {
            return false;
          }
        }
        while (++index < length) {
          data = matchData[index];
          var key = data[0], objValue = object[key], srcValue = data[1];
          if (noCustomizer && data[2]) {
            if (objValue === void 0 && !(key in object)) {
              return false;
            }
          } else {
            var stack = new Stack();
            if (customizer) {
              var result = customizer(objValue, srcValue, key, object, source, stack);
            }
            if (!(result === void 0 ? baseIsEqual(srcValue, objValue, COMPARE_PARTIAL_FLAG | COMPARE_UNORDERED_FLAG, customizer, stack) : result)) {
              return false;
            }
          }
        }
        return true;
      }
      module.exports = baseIsMatch;
    }
  });

  // node_modules/lodash/_isStrictComparable.js
  var require_isStrictComparable = __commonJS({
    "node_modules/lodash/_isStrictComparable.js"(exports, module) {
      var isObject = require_isObject();
      function isStrictComparable(value) {
        return value === value && !isObject(value);
      }
      module.exports = isStrictComparable;
    }
  });

  // node_modules/lodash/_getMatchData.js
  var require_getMatchData = __commonJS({
    "node_modules/lodash/_getMatchData.js"(exports, module) {
      var isStrictComparable = require_isStrictComparable();
      var keys = require_keys();
      function getMatchData(object) {
        var result = keys(object), length = result.length;
        while (length--) {
          var key = result[length], value = object[key];
          result[length] = [key, value, isStrictComparable(value)];
        }
        return result;
      }
      module.exports = getMatchData;
    }
  });

  // node_modules/lodash/_matchesStrictComparable.js
  var require_matchesStrictComparable = __commonJS({
    "node_modules/lodash/_matchesStrictComparable.js"(exports, module) {
      function matchesStrictComparable(key, srcValue) {
        return function(object) {
          if (object == null) {
            return false;
          }
          return object[key] === srcValue && (srcValue !== void 0 || key in Object(object));
        };
      }
      module.exports = matchesStrictComparable;
    }
  });

  // node_modules/lodash/_baseMatches.js
  var require_baseMatches = __commonJS({
    "node_modules/lodash/_baseMatches.js"(exports, module) {
      var baseIsMatch = require_baseIsMatch();
      var getMatchData = require_getMatchData();
      var matchesStrictComparable = require_matchesStrictComparable();
      function baseMatches(source) {
        var matchData = getMatchData(source);
        if (matchData.length == 1 && matchData[0][2]) {
          return matchesStrictComparable(matchData[0][0], matchData[0][1]);
        }
        return function(object) {
          return object === source || baseIsMatch(object, source, matchData);
        };
      }
      module.exports = baseMatches;
    }
  });

  // node_modules/lodash/isSymbol.js
  var require_isSymbol = __commonJS({
    "node_modules/lodash/isSymbol.js"(exports, module) {
      var baseGetTag = require_baseGetTag();
      var isObjectLike = require_isObjectLike();
      var symbolTag = "[object Symbol]";
      function isSymbol(value) {
        return typeof value == "symbol" || isObjectLike(value) && baseGetTag(value) == symbolTag;
      }
      module.exports = isSymbol;
    }
  });

  // node_modules/lodash/_isKey.js
  var require_isKey = __commonJS({
    "node_modules/lodash/_isKey.js"(exports, module) {
      var isArray = require_isArray();
      var isSymbol = require_isSymbol();
      var reIsDeepProp = /\.|\[(?:[^[\]]*|(["'])(?:(?!\1)[^\\]|\\.)*?\1)\]/;
      var reIsPlainProp = /^\w*$/;
      function isKey(value, object) {
        if (isArray(value)) {
          return false;
        }
        var type = typeof value;
        if (type == "number" || type == "symbol" || type == "boolean" || value == null || isSymbol(value)) {
          return true;
        }
        return reIsPlainProp.test(value) || !reIsDeepProp.test(value) || object != null && value in Object(object);
      }
      module.exports = isKey;
    }
  });

  // node_modules/lodash/memoize.js
  var require_memoize = __commonJS({
    "node_modules/lodash/memoize.js"(exports, module) {
      var MapCache = require_MapCache();
      var FUNC_ERROR_TEXT = "Expected a function";
      function memoize(func, resolver) {
        if (typeof func != "function" || resolver != null && typeof resolver != "function") {
          throw new TypeError(FUNC_ERROR_TEXT);
        }
        var memoized = function() {
          var args = arguments, key = resolver ? resolver.apply(this, args) : args[0], cache = memoized.cache;
          if (cache.has(key)) {
            return cache.get(key);
          }
          var result = func.apply(this, args);
          memoized.cache = cache.set(key, result) || cache;
          return result;
        };
        memoized.cache = new (memoize.Cache || MapCache)();
        return memoized;
      }
      memoize.Cache = MapCache;
      module.exports = memoize;
    }
  });

  // node_modules/lodash/_memoizeCapped.js
  var require_memoizeCapped = __commonJS({
    "node_modules/lodash/_memoizeCapped.js"(exports, module) {
      var memoize = require_memoize();
      var MAX_MEMOIZE_SIZE = 500;
      function memoizeCapped(func) {
        var result = memoize(func, function(key) {
          if (cache.size === MAX_MEMOIZE_SIZE) {
            cache.clear();
          }
          return key;
        });
        var cache = result.cache;
        return result;
      }
      module.exports = memoizeCapped;
    }
  });

  // node_modules/lodash/_stringToPath.js
  var require_stringToPath = __commonJS({
    "node_modules/lodash/_stringToPath.js"(exports, module) {
      var memoizeCapped = require_memoizeCapped();
      var rePropName = /[^.[\]]+|\[(?:(-?\d+(?:\.\d+)?)|(["'])((?:(?!\2)[^\\]|\\.)*?)\2)\]|(?=(?:\.|\[\])(?:\.|\[\]|$))/g;
      var reEscapeChar = /\\(\\)?/g;
      var stringToPath = memoizeCapped(function(string) {
        var result = [];
        if (string.charCodeAt(0) === 46) {
          result.push("");
        }
        string.replace(rePropName, function(match, number, quote, subString) {
          result.push(quote ? subString.replace(reEscapeChar, "$1") : number || match);
        });
        return result;
      });
      module.exports = stringToPath;
    }
  });

  // node_modules/lodash/_arrayMap.js
  var require_arrayMap = __commonJS({
    "node_modules/lodash/_arrayMap.js"(exports, module) {
      function arrayMap(array2, iteratee) {
        var index = -1, length = array2 == null ? 0 : array2.length, result = Array(length);
        while (++index < length) {
          result[index] = iteratee(array2[index], index, array2);
        }
        return result;
      }
      module.exports = arrayMap;
    }
  });

  // node_modules/lodash/_baseToString.js
  var require_baseToString = __commonJS({
    "node_modules/lodash/_baseToString.js"(exports, module) {
      var Symbol2 = require_Symbol();
      var arrayMap = require_arrayMap();
      var isArray = require_isArray();
      var isSymbol = require_isSymbol();
      var INFINITY = 1 / 0;
      var symbolProto = Symbol2 ? Symbol2.prototype : void 0;
      var symbolToString = symbolProto ? symbolProto.toString : void 0;
      function baseToString(value) {
        if (typeof value == "string") {
          return value;
        }
        if (isArray(value)) {
          return arrayMap(value, baseToString) + "";
        }
        if (isSymbol(value)) {
          return symbolToString ? symbolToString.call(value) : "";
        }
        var result = value + "";
        return result == "0" && 1 / value == -INFINITY ? "-0" : result;
      }
      module.exports = baseToString;
    }
  });

  // node_modules/lodash/toString.js
  var require_toString = __commonJS({
    "node_modules/lodash/toString.js"(exports, module) {
      var baseToString = require_baseToString();
      function toString(value) {
        return value == null ? "" : baseToString(value);
      }
      module.exports = toString;
    }
  });

  // node_modules/lodash/_castPath.js
  var require_castPath = __commonJS({
    "node_modules/lodash/_castPath.js"(exports, module) {
      var isArray = require_isArray();
      var isKey = require_isKey();
      var stringToPath = require_stringToPath();
      var toString = require_toString();
      function castPath(value, object) {
        if (isArray(value)) {
          return value;
        }
        return isKey(value, object) ? [value] : stringToPath(toString(value));
      }
      module.exports = castPath;
    }
  });

  // node_modules/lodash/_toKey.js
  var require_toKey = __commonJS({
    "node_modules/lodash/_toKey.js"(exports, module) {
      var isSymbol = require_isSymbol();
      var INFINITY = 1 / 0;
      function toKey(value) {
        if (typeof value == "string" || isSymbol(value)) {
          return value;
        }
        var result = value + "";
        return result == "0" && 1 / value == -INFINITY ? "-0" : result;
      }
      module.exports = toKey;
    }
  });

  // node_modules/lodash/_baseGet.js
  var require_baseGet = __commonJS({
    "node_modules/lodash/_baseGet.js"(exports, module) {
      var castPath = require_castPath();
      var toKey = require_toKey();
      function baseGet(object, path) {
        path = castPath(path, object);
        var index = 0, length = path.length;
        while (object != null && index < length) {
          object = object[toKey(path[index++])];
        }
        return index && index == length ? object : void 0;
      }
      module.exports = baseGet;
    }
  });

  // node_modules/lodash/get.js
  var require_get = __commonJS({
    "node_modules/lodash/get.js"(exports, module) {
      var baseGet = require_baseGet();
      function get3(object, path, defaultValue) {
        var result = object == null ? void 0 : baseGet(object, path);
        return result === void 0 ? defaultValue : result;
      }
      module.exports = get3;
    }
  });

  // node_modules/lodash/_baseHasIn.js
  var require_baseHasIn = __commonJS({
    "node_modules/lodash/_baseHasIn.js"(exports, module) {
      function baseHasIn(object, key) {
        return object != null && key in Object(object);
      }
      module.exports = baseHasIn;
    }
  });

  // node_modules/lodash/_hasPath.js
  var require_hasPath = __commonJS({
    "node_modules/lodash/_hasPath.js"(exports, module) {
      var castPath = require_castPath();
      var isArguments = require_isArguments();
      var isArray = require_isArray();
      var isIndex = require_isIndex();
      var isLength = require_isLength();
      var toKey = require_toKey();
      function hasPath(object, path, hasFunc) {
        path = castPath(path, object);
        var index = -1, length = path.length, result = false;
        while (++index < length) {
          var key = toKey(path[index]);
          if (!(result = object != null && hasFunc(object, key))) {
            break;
          }
          object = object[key];
        }
        if (result || ++index != length) {
          return result;
        }
        length = object == null ? 0 : object.length;
        return !!length && isLength(length) && isIndex(key, length) && (isArray(object) || isArguments(object));
      }
      module.exports = hasPath;
    }
  });

  // node_modules/lodash/hasIn.js
  var require_hasIn = __commonJS({
    "node_modules/lodash/hasIn.js"(exports, module) {
      var baseHasIn = require_baseHasIn();
      var hasPath = require_hasPath();
      function hasIn(object, path) {
        return object != null && hasPath(object, path, baseHasIn);
      }
      module.exports = hasIn;
    }
  });

  // node_modules/lodash/_baseMatchesProperty.js
  var require_baseMatchesProperty = __commonJS({
    "node_modules/lodash/_baseMatchesProperty.js"(exports, module) {
      var baseIsEqual = require_baseIsEqual();
      var get3 = require_get();
      var hasIn = require_hasIn();
      var isKey = require_isKey();
      var isStrictComparable = require_isStrictComparable();
      var matchesStrictComparable = require_matchesStrictComparable();
      var toKey = require_toKey();
      var COMPARE_PARTIAL_FLAG = 1;
      var COMPARE_UNORDERED_FLAG = 2;
      function baseMatchesProperty(path, srcValue) {
        if (isKey(path) && isStrictComparable(srcValue)) {
          return matchesStrictComparable(toKey(path), srcValue);
        }
        return function(object) {
          var objValue = get3(object, path);
          return objValue === void 0 && objValue === srcValue ? hasIn(object, path) : baseIsEqual(srcValue, objValue, COMPARE_PARTIAL_FLAG | COMPARE_UNORDERED_FLAG);
        };
      }
      module.exports = baseMatchesProperty;
    }
  });

  // node_modules/lodash/_baseProperty.js
  var require_baseProperty = __commonJS({
    "node_modules/lodash/_baseProperty.js"(exports, module) {
      function baseProperty(key) {
        return function(object) {
          return object == null ? void 0 : object[key];
        };
      }
      module.exports = baseProperty;
    }
  });

  // node_modules/lodash/_basePropertyDeep.js
  var require_basePropertyDeep = __commonJS({
    "node_modules/lodash/_basePropertyDeep.js"(exports, module) {
      var baseGet = require_baseGet();
      function basePropertyDeep(path) {
        return function(object) {
          return baseGet(object, path);
        };
      }
      module.exports = basePropertyDeep;
    }
  });

  // node_modules/lodash/property.js
  var require_property = __commonJS({
    "node_modules/lodash/property.js"(exports, module) {
      var baseProperty = require_baseProperty();
      var basePropertyDeep = require_basePropertyDeep();
      var isKey = require_isKey();
      var toKey = require_toKey();
      function property(path) {
        return isKey(path) ? baseProperty(toKey(path)) : basePropertyDeep(path);
      }
      module.exports = property;
    }
  });

  // node_modules/lodash/_baseIteratee.js
  var require_baseIteratee = __commonJS({
    "node_modules/lodash/_baseIteratee.js"(exports, module) {
      var baseMatches = require_baseMatches();
      var baseMatchesProperty = require_baseMatchesProperty();
      var identity3 = require_identity();
      var isArray = require_isArray();
      var property = require_property();
      function baseIteratee(value) {
        if (typeof value == "function") {
          return value;
        }
        if (value == null) {
          return identity3;
        }
        if (typeof value == "object") {
          return isArray(value) ? baseMatchesProperty(value[0], value[1]) : baseMatches(value);
        }
        return property(value);
      }
      module.exports = baseIteratee;
    }
  });

  // node_modules/lodash/filter.js
  var require_filter = __commonJS({
    "node_modules/lodash/filter.js"(exports, module) {
      var arrayFilter = require_arrayFilter();
      var baseFilter = require_baseFilter();
      var baseIteratee = require_baseIteratee();
      var isArray = require_isArray();
      function filter2(collection, predicate) {
        var func = isArray(collection) ? arrayFilter : baseFilter;
        return func(collection, baseIteratee(predicate, 3));
      }
      module.exports = filter2;
    }
  });

  // node_modules/lodash/_baseHas.js
  var require_baseHas = __commonJS({
    "node_modules/lodash/_baseHas.js"(exports, module) {
      var objectProto = Object.prototype;
      var hasOwnProperty = objectProto.hasOwnProperty;
      function baseHas(object, key) {
        return object != null && hasOwnProperty.call(object, key);
      }
      module.exports = baseHas;
    }
  });

  // node_modules/lodash/has.js
  var require_has = __commonJS({
    "node_modules/lodash/has.js"(exports, module) {
      var baseHas = require_baseHas();
      var hasPath = require_hasPath();
      function has(object, path) {
        return object != null && hasPath(object, path, baseHas);
      }
      module.exports = has;
    }
  });

  // node_modules/lodash/isEmpty.js
  var require_isEmpty = __commonJS({
    "node_modules/lodash/isEmpty.js"(exports, module) {
      var baseKeys = require_baseKeys();
      var getTag = require_getTag();
      var isArguments = require_isArguments();
      var isArray = require_isArray();
      var isArrayLike = require_isArrayLike();
      var isBuffer = require_isBuffer();
      var isPrototype = require_isPrototype();
      var isTypedArray = require_isTypedArray();
      var mapTag = "[object Map]";
      var setTag = "[object Set]";
      var objectProto = Object.prototype;
      var hasOwnProperty = objectProto.hasOwnProperty;
      function isEmpty(value) {
        if (value == null) {
          return true;
        }
        if (isArrayLike(value) && (isArray(value) || typeof value == "string" || typeof value.splice == "function" || isBuffer(value) || isTypedArray(value) || isArguments(value))) {
          return !value.length;
        }
        var tag = getTag(value);
        if (tag == mapTag || tag == setTag) {
          return !value.size;
        }
        if (isPrototype(value)) {
          return !baseKeys(value).length;
        }
        for (var key in value) {
          if (hasOwnProperty.call(value, key)) {
            return false;
          }
        }
        return true;
      }
      module.exports = isEmpty;
    }
  });

  // node_modules/lodash/isUndefined.js
  var require_isUndefined = __commonJS({
    "node_modules/lodash/isUndefined.js"(exports, module) {
      function isUndefined(value) {
        return value === void 0;
      }
      module.exports = isUndefined;
    }
  });

  // node_modules/lodash/_baseMap.js
  var require_baseMap = __commonJS({
    "node_modules/lodash/_baseMap.js"(exports, module) {
      var baseEach = require_baseEach();
      var isArrayLike = require_isArrayLike();
      function baseMap(collection, iteratee) {
        var index = -1, result = isArrayLike(collection) ? Array(collection.length) : [];
        baseEach(collection, function(value, key, collection2) {
          result[++index] = iteratee(value, key, collection2);
        });
        return result;
      }
      module.exports = baseMap;
    }
  });

  // node_modules/lodash/map.js
  var require_map = __commonJS({
    "node_modules/lodash/map.js"(exports, module) {
      var arrayMap = require_arrayMap();
      var baseIteratee = require_baseIteratee();
      var baseMap = require_baseMap();
      var isArray = require_isArray();
      function map(collection, iteratee) {
        var func = isArray(collection) ? arrayMap : baseMap;
        return func(collection, baseIteratee(iteratee, 3));
      }
      module.exports = map;
    }
  });

  // node_modules/lodash/_arrayReduce.js
  var require_arrayReduce = __commonJS({
    "node_modules/lodash/_arrayReduce.js"(exports, module) {
      function arrayReduce(array2, iteratee, accumulator, initAccum) {
        var index = -1, length = array2 == null ? 0 : array2.length;
        if (initAccum && length) {
          accumulator = array2[++index];
        }
        while (++index < length) {
          accumulator = iteratee(accumulator, array2[index], index, array2);
        }
        return accumulator;
      }
      module.exports = arrayReduce;
    }
  });

  // node_modules/lodash/_baseReduce.js
  var require_baseReduce = __commonJS({
    "node_modules/lodash/_baseReduce.js"(exports, module) {
      function baseReduce(collection, iteratee, accumulator, initAccum, eachFunc) {
        eachFunc(collection, function(value, index, collection2) {
          accumulator = initAccum ? (initAccum = false, value) : iteratee(accumulator, value, index, collection2);
        });
        return accumulator;
      }
      module.exports = baseReduce;
    }
  });

  // node_modules/lodash/reduce.js
  var require_reduce = __commonJS({
    "node_modules/lodash/reduce.js"(exports, module) {
      var arrayReduce = require_arrayReduce();
      var baseEach = require_baseEach();
      var baseIteratee = require_baseIteratee();
      var baseReduce = require_baseReduce();
      var isArray = require_isArray();
      function reduce(collection, iteratee, accumulator) {
        var func = isArray(collection) ? arrayReduce : baseReduce, initAccum = arguments.length < 3;
        return func(collection, baseIteratee(iteratee, 4), accumulator, initAccum, baseEach);
      }
      module.exports = reduce;
    }
  });

  // node_modules/lodash/isString.js
  var require_isString = __commonJS({
    "node_modules/lodash/isString.js"(exports, module) {
      var baseGetTag = require_baseGetTag();
      var isArray = require_isArray();
      var isObjectLike = require_isObjectLike();
      var stringTag = "[object String]";
      function isString(value) {
        return typeof value == "string" || !isArray(value) && isObjectLike(value) && baseGetTag(value) == stringTag;
      }
      module.exports = isString;
    }
  });

  // node_modules/lodash/_asciiSize.js
  var require_asciiSize = __commonJS({
    "node_modules/lodash/_asciiSize.js"(exports, module) {
      var baseProperty = require_baseProperty();
      var asciiSize = baseProperty("length");
      module.exports = asciiSize;
    }
  });

  // node_modules/lodash/_hasUnicode.js
  var require_hasUnicode = __commonJS({
    "node_modules/lodash/_hasUnicode.js"(exports, module) {
      var rsAstralRange = "\\ud800-\\udfff";
      var rsComboMarksRange = "\\u0300-\\u036f";
      var reComboHalfMarksRange = "\\ufe20-\\ufe2f";
      var rsComboSymbolsRange = "\\u20d0-\\u20ff";
      var rsComboRange = rsComboMarksRange + reComboHalfMarksRange + rsComboSymbolsRange;
      var rsVarRange = "\\ufe0e\\ufe0f";
      var rsZWJ = "\\u200d";
      var reHasUnicode = RegExp("[" + rsZWJ + rsAstralRange + rsComboRange + rsVarRange + "]");
      function hasUnicode(string) {
        return reHasUnicode.test(string);
      }
      module.exports = hasUnicode;
    }
  });

  // node_modules/lodash/_unicodeSize.js
  var require_unicodeSize = __commonJS({
    "node_modules/lodash/_unicodeSize.js"(exports, module) {
      var rsAstralRange = "\\ud800-\\udfff";
      var rsComboMarksRange = "\\u0300-\\u036f";
      var reComboHalfMarksRange = "\\ufe20-\\ufe2f";
      var rsComboSymbolsRange = "\\u20d0-\\u20ff";
      var rsComboRange = rsComboMarksRange + reComboHalfMarksRange + rsComboSymbolsRange;
      var rsVarRange = "\\ufe0e\\ufe0f";
      var rsAstral = "[" + rsAstralRange + "]";
      var rsCombo = "[" + rsComboRange + "]";
      var rsFitz = "\\ud83c[\\udffb-\\udfff]";
      var rsModifier = "(?:" + rsCombo + "|" + rsFitz + ")";
      var rsNonAstral = "[^" + rsAstralRange + "]";
      var rsRegional = "(?:\\ud83c[\\udde6-\\uddff]){2}";
      var rsSurrPair = "[\\ud800-\\udbff][\\udc00-\\udfff]";
      var rsZWJ = "\\u200d";
      var reOptMod = rsModifier + "?";
      var rsOptVar = "[" + rsVarRange + "]?";
      var rsOptJoin = "(?:" + rsZWJ + "(?:" + [rsNonAstral, rsRegional, rsSurrPair].join("|") + ")" + rsOptVar + reOptMod + ")*";
      var rsSeq = rsOptVar + reOptMod + rsOptJoin;
      var rsSymbol = "(?:" + [rsNonAstral + rsCombo + "?", rsCombo, rsRegional, rsSurrPair, rsAstral].join("|") + ")";
      var reUnicode = RegExp(rsFitz + "(?=" + rsFitz + ")|" + rsSymbol + rsSeq, "g");
      function unicodeSize(string) {
        var result = reUnicode.lastIndex = 0;
        while (reUnicode.test(string)) {
          ++result;
        }
        return result;
      }
      module.exports = unicodeSize;
    }
  });

  // node_modules/lodash/_stringSize.js
  var require_stringSize = __commonJS({
    "node_modules/lodash/_stringSize.js"(exports, module) {
      var asciiSize = require_asciiSize();
      var hasUnicode = require_hasUnicode();
      var unicodeSize = require_unicodeSize();
      function stringSize(string) {
        return hasUnicode(string) ? unicodeSize(string) : asciiSize(string);
      }
      module.exports = stringSize;
    }
  });

  // node_modules/lodash/size.js
  var require_size = __commonJS({
    "node_modules/lodash/size.js"(exports, module) {
      var baseKeys = require_baseKeys();
      var getTag = require_getTag();
      var isArrayLike = require_isArrayLike();
      var isString = require_isString();
      var stringSize = require_stringSize();
      var mapTag = "[object Map]";
      var setTag = "[object Set]";
      function size(collection) {
        if (collection == null) {
          return 0;
        }
        if (isArrayLike(collection)) {
          return isString(collection) ? stringSize(collection) : collection.length;
        }
        var tag = getTag(collection);
        if (tag == mapTag || tag == setTag) {
          return collection.size;
        }
        return baseKeys(collection).length;
      }
      module.exports = size;
    }
  });

  // node_modules/lodash/transform.js
  var require_transform = __commonJS({
    "node_modules/lodash/transform.js"(exports, module) {
      var arrayEach = require_arrayEach();
      var baseCreate = require_baseCreate();
      var baseForOwn = require_baseForOwn();
      var baseIteratee = require_baseIteratee();
      var getPrototype = require_getPrototype();
      var isArray = require_isArray();
      var isBuffer = require_isBuffer();
      var isFunction = require_isFunction();
      var isObject = require_isObject();
      var isTypedArray = require_isTypedArray();
      function transform2(object, iteratee, accumulator) {
        var isArr = isArray(object), isArrLike = isArr || isBuffer(object) || isTypedArray(object);
        iteratee = baseIteratee(iteratee, 4);
        if (accumulator == null) {
          var Ctor = object && object.constructor;
          if (isArrLike) {
            accumulator = isArr ? new Ctor() : [];
          } else if (isObject(object)) {
            accumulator = isFunction(Ctor) ? baseCreate(getPrototype(object)) : {};
          } else {
            accumulator = {};
          }
        }
        (isArrLike ? arrayEach : baseForOwn)(object, function(value, index, object2) {
          return iteratee(accumulator, value, index, object2);
        });
        return accumulator;
      }
      module.exports = transform2;
    }
  });

  // node_modules/lodash/_isFlattenable.js
  var require_isFlattenable = __commonJS({
    "node_modules/lodash/_isFlattenable.js"(exports, module) {
      var Symbol2 = require_Symbol();
      var isArguments = require_isArguments();
      var isArray = require_isArray();
      var spreadableSymbol = Symbol2 ? Symbol2.isConcatSpreadable : void 0;
      function isFlattenable(value) {
        return isArray(value) || isArguments(value) || !!(spreadableSymbol && value && value[spreadableSymbol]);
      }
      module.exports = isFlattenable;
    }
  });

  // node_modules/lodash/_baseFlatten.js
  var require_baseFlatten = __commonJS({
    "node_modules/lodash/_baseFlatten.js"(exports, module) {
      var arrayPush = require_arrayPush();
      var isFlattenable = require_isFlattenable();
      function baseFlatten(array2, depth, predicate, isStrict, result) {
        var index = -1, length = array2.length;
        predicate || (predicate = isFlattenable);
        result || (result = []);
        while (++index < length) {
          var value = array2[index];
          if (depth > 0 && predicate(value)) {
            if (depth > 1) {
              baseFlatten(value, depth - 1, predicate, isStrict, result);
            } else {
              arrayPush(result, value);
            }
          } else if (!isStrict) {
            result[result.length] = value;
          }
        }
        return result;
      }
      module.exports = baseFlatten;
    }
  });

  // node_modules/lodash/_apply.js
  var require_apply = __commonJS({
    "node_modules/lodash/_apply.js"(exports, module) {
      function apply(func, thisArg, args) {
        switch (args.length) {
          case 0:
            return func.call(thisArg);
          case 1:
            return func.call(thisArg, args[0]);
          case 2:
            return func.call(thisArg, args[0], args[1]);
          case 3:
            return func.call(thisArg, args[0], args[1], args[2]);
        }
        return func.apply(thisArg, args);
      }
      module.exports = apply;
    }
  });

  // node_modules/lodash/_overRest.js
  var require_overRest = __commonJS({
    "node_modules/lodash/_overRest.js"(exports, module) {
      var apply = require_apply();
      var nativeMax = Math.max;
      function overRest(func, start2, transform2) {
        start2 = nativeMax(start2 === void 0 ? func.length - 1 : start2, 0);
        return function() {
          var args = arguments, index = -1, length = nativeMax(args.length - start2, 0), array2 = Array(length);
          while (++index < length) {
            array2[index] = args[start2 + index];
          }
          index = -1;
          var otherArgs = Array(start2 + 1);
          while (++index < start2) {
            otherArgs[index] = args[index];
          }
          otherArgs[start2] = transform2(array2);
          return apply(func, this, otherArgs);
        };
      }
      module.exports = overRest;
    }
  });

  // node_modules/lodash/_baseSetToString.js
  var require_baseSetToString = __commonJS({
    "node_modules/lodash/_baseSetToString.js"(exports, module) {
      var constant = require_constant();
      var defineProperty = require_defineProperty();
      var identity3 = require_identity();
      var baseSetToString = !defineProperty ? identity3 : function(func, string) {
        return defineProperty(func, "toString", {
          "configurable": true,
          "enumerable": false,
          "value": constant(string),
          "writable": true
        });
      };
      module.exports = baseSetToString;
    }
  });

  // node_modules/lodash/_shortOut.js
  var require_shortOut = __commonJS({
    "node_modules/lodash/_shortOut.js"(exports, module) {
      var HOT_COUNT = 800;
      var HOT_SPAN = 16;
      var nativeNow = Date.now;
      function shortOut(func) {
        var count = 0, lastCalled = 0;
        return function() {
          var stamp = nativeNow(), remaining = HOT_SPAN - (stamp - lastCalled);
          lastCalled = stamp;
          if (remaining > 0) {
            if (++count >= HOT_COUNT) {
              return arguments[0];
            }
          } else {
            count = 0;
          }
          return func.apply(void 0, arguments);
        };
      }
      module.exports = shortOut;
    }
  });

  // node_modules/lodash/_setToString.js
  var require_setToString = __commonJS({
    "node_modules/lodash/_setToString.js"(exports, module) {
      var baseSetToString = require_baseSetToString();
      var shortOut = require_shortOut();
      var setToString = shortOut(baseSetToString);
      module.exports = setToString;
    }
  });

  // node_modules/lodash/_baseRest.js
  var require_baseRest = __commonJS({
    "node_modules/lodash/_baseRest.js"(exports, module) {
      var identity3 = require_identity();
      var overRest = require_overRest();
      var setToString = require_setToString();
      function baseRest(func, start2) {
        return setToString(overRest(func, start2, identity3), func + "");
      }
      module.exports = baseRest;
    }
  });

  // node_modules/lodash/_baseFindIndex.js
  var require_baseFindIndex = __commonJS({
    "node_modules/lodash/_baseFindIndex.js"(exports, module) {
      function baseFindIndex(array2, predicate, fromIndex, fromRight) {
        var length = array2.length, index = fromIndex + (fromRight ? 1 : -1);
        while (fromRight ? index-- : ++index < length) {
          if (predicate(array2[index], index, array2)) {
            return index;
          }
        }
        return -1;
      }
      module.exports = baseFindIndex;
    }
  });

  // node_modules/lodash/_baseIsNaN.js
  var require_baseIsNaN = __commonJS({
    "node_modules/lodash/_baseIsNaN.js"(exports, module) {
      function baseIsNaN(value) {
        return value !== value;
      }
      module.exports = baseIsNaN;
    }
  });

  // node_modules/lodash/_strictIndexOf.js
  var require_strictIndexOf = __commonJS({
    "node_modules/lodash/_strictIndexOf.js"(exports, module) {
      function strictIndexOf(array2, value, fromIndex) {
        var index = fromIndex - 1, length = array2.length;
        while (++index < length) {
          if (array2[index] === value) {
            return index;
          }
        }
        return -1;
      }
      module.exports = strictIndexOf;
    }
  });

  // node_modules/lodash/_baseIndexOf.js
  var require_baseIndexOf = __commonJS({
    "node_modules/lodash/_baseIndexOf.js"(exports, module) {
      var baseFindIndex = require_baseFindIndex();
      var baseIsNaN = require_baseIsNaN();
      var strictIndexOf = require_strictIndexOf();
      function baseIndexOf(array2, value, fromIndex) {
        return value === value ? strictIndexOf(array2, value, fromIndex) : baseFindIndex(array2, baseIsNaN, fromIndex);
      }
      module.exports = baseIndexOf;
    }
  });

  // node_modules/lodash/_arrayIncludes.js
  var require_arrayIncludes = __commonJS({
    "node_modules/lodash/_arrayIncludes.js"(exports, module) {
      var baseIndexOf = require_baseIndexOf();
      function arrayIncludes(array2, value) {
        var length = array2 == null ? 0 : array2.length;
        return !!length && baseIndexOf(array2, value, 0) > -1;
      }
      module.exports = arrayIncludes;
    }
  });

  // node_modules/lodash/_arrayIncludesWith.js
  var require_arrayIncludesWith = __commonJS({
    "node_modules/lodash/_arrayIncludesWith.js"(exports, module) {
      function arrayIncludesWith(array2, value, comparator) {
        var index = -1, length = array2 == null ? 0 : array2.length;
        while (++index < length) {
          if (comparator(value, array2[index])) {
            return true;
          }
        }
        return false;
      }
      module.exports = arrayIncludesWith;
    }
  });

  // node_modules/lodash/noop.js
  var require_noop = __commonJS({
    "node_modules/lodash/noop.js"(exports, module) {
      function noop2() {
      }
      module.exports = noop2;
    }
  });

  // node_modules/lodash/_createSet.js
  var require_createSet = __commonJS({
    "node_modules/lodash/_createSet.js"(exports, module) {
      var Set2 = require_Set();
      var noop2 = require_noop();
      var setToArray = require_setToArray();
      var INFINITY = 1 / 0;
      var createSet = !(Set2 && 1 / setToArray(new Set2([, -0]))[1] == INFINITY) ? noop2 : function(values) {
        return new Set2(values);
      };
      module.exports = createSet;
    }
  });

  // node_modules/lodash/_baseUniq.js
  var require_baseUniq = __commonJS({
    "node_modules/lodash/_baseUniq.js"(exports, module) {
      var SetCache = require_SetCache();
      var arrayIncludes = require_arrayIncludes();
      var arrayIncludesWith = require_arrayIncludesWith();
      var cacheHas = require_cacheHas();
      var createSet = require_createSet();
      var setToArray = require_setToArray();
      var LARGE_ARRAY_SIZE = 200;
      function baseUniq(array2, iteratee, comparator) {
        var index = -1, includes = arrayIncludes, length = array2.length, isCommon = true, result = [], seen = result;
        if (comparator) {
          isCommon = false;
          includes = arrayIncludesWith;
        } else if (length >= LARGE_ARRAY_SIZE) {
          var set3 = iteratee ? null : createSet(array2);
          if (set3) {
            return setToArray(set3);
          }
          isCommon = false;
          includes = cacheHas;
          seen = new SetCache();
        } else {
          seen = iteratee ? [] : result;
        }
        outer:
          while (++index < length) {
            var value = array2[index], computed = iteratee ? iteratee(value) : value;
            value = comparator || value !== 0 ? value : 0;
            if (isCommon && computed === computed) {
              var seenIndex = seen.length;
              while (seenIndex--) {
                if (seen[seenIndex] === computed) {
                  continue outer;
                }
              }
              if (iteratee) {
                seen.push(computed);
              }
              result.push(value);
            } else if (!includes(seen, computed, comparator)) {
              if (seen !== result) {
                seen.push(computed);
              }
              result.push(value);
            }
          }
        return result;
      }
      module.exports = baseUniq;
    }
  });

  // node_modules/lodash/isArrayLikeObject.js
  var require_isArrayLikeObject = __commonJS({
    "node_modules/lodash/isArrayLikeObject.js"(exports, module) {
      var isArrayLike = require_isArrayLike();
      var isObjectLike = require_isObjectLike();
      function isArrayLikeObject(value) {
        return isObjectLike(value) && isArrayLike(value);
      }
      module.exports = isArrayLikeObject;
    }
  });

  // node_modules/lodash/union.js
  var require_union = __commonJS({
    "node_modules/lodash/union.js"(exports, module) {
      var baseFlatten = require_baseFlatten();
      var baseRest = require_baseRest();
      var baseUniq = require_baseUniq();
      var isArrayLikeObject = require_isArrayLikeObject();
      var union = baseRest(function(arrays) {
        return baseUniq(baseFlatten(arrays, 1, isArrayLikeObject, true));
      });
      module.exports = union;
    }
  });

  // node_modules/lodash/_baseValues.js
  var require_baseValues = __commonJS({
    "node_modules/lodash/_baseValues.js"(exports, module) {
      var arrayMap = require_arrayMap();
      function baseValues(object, props) {
        return arrayMap(props, function(key) {
          return object[key];
        });
      }
      module.exports = baseValues;
    }
  });

  // node_modules/lodash/values.js
  var require_values = __commonJS({
    "node_modules/lodash/values.js"(exports, module) {
      var baseValues = require_baseValues();
      var keys = require_keys();
      function values(object) {
        return object == null ? [] : baseValues(object, keys(object));
      }
      module.exports = values;
    }
  });

  // node_modules/graphlib/lib/lodash.js
  var require_lodash = __commonJS({
    "node_modules/graphlib/lib/lodash.js"(exports, module) {
      var lodash;
      if (typeof __require === "function") {
        try {
          lodash = {
            clone: require_clone(),
            constant: require_constant(),
            each: require_each(),
            filter: require_filter(),
            has: require_has(),
            isArray: require_isArray(),
            isEmpty: require_isEmpty(),
            isFunction: require_isFunction(),
            isUndefined: require_isUndefined(),
            keys: require_keys(),
            map: require_map(),
            reduce: require_reduce(),
            size: require_size(),
            transform: require_transform(),
            union: require_union(),
            values: require_values()
          };
        } catch (e) {
        }
      }
      if (!lodash) {
        lodash = window._;
      }
      module.exports = lodash;
    }
  });

  // node_modules/graphlib/lib/graph.js
  var require_graph = __commonJS({
    "node_modules/graphlib/lib/graph.js"(exports, module) {
      "use strict";
      var _ = require_lodash();
      module.exports = Graph;
      var DEFAULT_EDGE_NAME = "\0";
      var GRAPH_NODE = "\0";
      var EDGE_KEY_DELIM = "";
      function Graph(opts) {
        this._isDirected = _.has(opts, "directed") ? opts.directed : true;
        this._isMultigraph = _.has(opts, "multigraph") ? opts.multigraph : false;
        this._isCompound = _.has(opts, "compound") ? opts.compound : false;
        this._label = void 0;
        this._defaultNodeLabelFn = _.constant(void 0);
        this._defaultEdgeLabelFn = _.constant(void 0);
        this._nodes = {};
        if (this._isCompound) {
          this._parent = {};
          this._children = {};
          this._children[GRAPH_NODE] = {};
        }
        this._in = {};
        this._preds = {};
        this._out = {};
        this._sucs = {};
        this._edgeObjs = {};
        this._edgeLabels = {};
      }
      Graph.prototype._nodeCount = 0;
      Graph.prototype._edgeCount = 0;
      Graph.prototype.isDirected = function() {
        return this._isDirected;
      };
      Graph.prototype.isMultigraph = function() {
        return this._isMultigraph;
      };
      Graph.prototype.isCompound = function() {
        return this._isCompound;
      };
      Graph.prototype.setGraph = function(label) {
        this._label = label;
        return this;
      };
      Graph.prototype.graph = function() {
        return this._label;
      };
      Graph.prototype.setDefaultNodeLabel = function(newDefault) {
        if (!_.isFunction(newDefault)) {
          newDefault = _.constant(newDefault);
        }
        this._defaultNodeLabelFn = newDefault;
        return this;
      };
      Graph.prototype.nodeCount = function() {
        return this._nodeCount;
      };
      Graph.prototype.nodes = function() {
        return _.keys(this._nodes);
      };
      Graph.prototype.sources = function() {
        var self2 = this;
        return _.filter(this.nodes(), function(v) {
          return _.isEmpty(self2._in[v]);
        });
      };
      Graph.prototype.sinks = function() {
        var self2 = this;
        return _.filter(this.nodes(), function(v) {
          return _.isEmpty(self2._out[v]);
        });
      };
      Graph.prototype.setNodes = function(vs, value) {
        var args = arguments;
        var self2 = this;
        _.each(vs, function(v) {
          if (args.length > 1) {
            self2.setNode(v, value);
          } else {
            self2.setNode(v);
          }
        });
        return this;
      };
      Graph.prototype.setNode = function(v, value) {
        if (_.has(this._nodes, v)) {
          if (arguments.length > 1) {
            this._nodes[v] = value;
          }
          return this;
        }
        this._nodes[v] = arguments.length > 1 ? value : this._defaultNodeLabelFn(v);
        if (this._isCompound) {
          this._parent[v] = GRAPH_NODE;
          this._children[v] = {};
          this._children[GRAPH_NODE][v] = true;
        }
        this._in[v] = {};
        this._preds[v] = {};
        this._out[v] = {};
        this._sucs[v] = {};
        ++this._nodeCount;
        return this;
      };
      Graph.prototype.node = function(v) {
        return this._nodes[v];
      };
      Graph.prototype.hasNode = function(v) {
        return _.has(this._nodes, v);
      };
      Graph.prototype.removeNode = function(v) {
        var self2 = this;
        if (_.has(this._nodes, v)) {
          var removeEdge = function(e) {
            self2.removeEdge(self2._edgeObjs[e]);
          };
          delete this._nodes[v];
          if (this._isCompound) {
            this._removeFromParentsChildList(v);
            delete this._parent[v];
            _.each(this.children(v), function(child) {
              self2.setParent(child);
            });
            delete this._children[v];
          }
          _.each(_.keys(this._in[v]), removeEdge);
          delete this._in[v];
          delete this._preds[v];
          _.each(_.keys(this._out[v]), removeEdge);
          delete this._out[v];
          delete this._sucs[v];
          --this._nodeCount;
        }
        return this;
      };
      Graph.prototype.setParent = function(v, parent) {
        if (!this._isCompound) {
          throw new Error("Cannot set parent in a non-compound graph");
        }
        if (_.isUndefined(parent)) {
          parent = GRAPH_NODE;
        } else {
          parent += "";
          for (var ancestor = parent; !_.isUndefined(ancestor); ancestor = this.parent(ancestor)) {
            if (ancestor === v) {
              throw new Error("Setting " + parent + " as parent of " + v + " would create a cycle");
            }
          }
          this.setNode(parent);
        }
        this.setNode(v);
        this._removeFromParentsChildList(v);
        this._parent[v] = parent;
        this._children[parent][v] = true;
        return this;
      };
      Graph.prototype._removeFromParentsChildList = function(v) {
        delete this._children[this._parent[v]][v];
      };
      Graph.prototype.parent = function(v) {
        if (this._isCompound) {
          var parent = this._parent[v];
          if (parent !== GRAPH_NODE) {
            return parent;
          }
        }
      };
      Graph.prototype.children = function(v) {
        if (_.isUndefined(v)) {
          v = GRAPH_NODE;
        }
        if (this._isCompound) {
          var children2 = this._children[v];
          if (children2) {
            return _.keys(children2);
          }
        } else if (v === GRAPH_NODE) {
          return this.nodes();
        } else if (this.hasNode(v)) {
          return [];
        }
      };
      Graph.prototype.predecessors = function(v) {
        var predsV = this._preds[v];
        if (predsV) {
          return _.keys(predsV);
        }
      };
      Graph.prototype.successors = function(v) {
        var sucsV = this._sucs[v];
        if (sucsV) {
          return _.keys(sucsV);
        }
      };
      Graph.prototype.neighbors = function(v) {
        var preds = this.predecessors(v);
        if (preds) {
          return _.union(preds, this.successors(v));
        }
      };
      Graph.prototype.isLeaf = function(v) {
        var neighbors;
        if (this.isDirected()) {
          neighbors = this.successors(v);
        } else {
          neighbors = this.neighbors(v);
        }
        return neighbors.length === 0;
      };
      Graph.prototype.filterNodes = function(filter2) {
        var copy = new this.constructor({
          directed: this._isDirected,
          multigraph: this._isMultigraph,
          compound: this._isCompound
        });
        copy.setGraph(this.graph());
        var self2 = this;
        _.each(this._nodes, function(value, v) {
          if (filter2(v)) {
            copy.setNode(v, value);
          }
        });
        _.each(this._edgeObjs, function(e) {
          if (copy.hasNode(e.v) && copy.hasNode(e.w)) {
            copy.setEdge(e, self2.edge(e));
          }
        });
        var parents = {};
        function findParent(v) {
          var parent = self2.parent(v);
          if (parent === void 0 || copy.hasNode(parent)) {
            parents[v] = parent;
            return parent;
          } else if (parent in parents) {
            return parents[parent];
          } else {
            return findParent(parent);
          }
        }
        if (this._isCompound) {
          _.each(copy.nodes(), function(v) {
            copy.setParent(v, findParent(v));
          });
        }
        return copy;
      };
      Graph.prototype.setDefaultEdgeLabel = function(newDefault) {
        if (!_.isFunction(newDefault)) {
          newDefault = _.constant(newDefault);
        }
        this._defaultEdgeLabelFn = newDefault;
        return this;
      };
      Graph.prototype.edgeCount = function() {
        return this._edgeCount;
      };
      Graph.prototype.edges = function() {
        return _.values(this._edgeObjs);
      };
      Graph.prototype.setPath = function(vs, value) {
        var self2 = this;
        var args = arguments;
        _.reduce(vs, function(v, w) {
          if (args.length > 1) {
            self2.setEdge(v, w, value);
          } else {
            self2.setEdge(v, w);
          }
          return w;
        });
        return this;
      };
      Graph.prototype.setEdge = function() {
        var v, w, name, value;
        var valueSpecified = false;
        var arg0 = arguments[0];
        if (typeof arg0 === "object" && arg0 !== null && "v" in arg0) {
          v = arg0.v;
          w = arg0.w;
          name = arg0.name;
          if (arguments.length === 2) {
            value = arguments[1];
            valueSpecified = true;
          }
        } else {
          v = arg0;
          w = arguments[1];
          name = arguments[3];
          if (arguments.length > 2) {
            value = arguments[2];
            valueSpecified = true;
          }
        }
        v = "" + v;
        w = "" + w;
        if (!_.isUndefined(name)) {
          name = "" + name;
        }
        var e = edgeArgsToId(this._isDirected, v, w, name);
        if (_.has(this._edgeLabels, e)) {
          if (valueSpecified) {
            this._edgeLabels[e] = value;
          }
          return this;
        }
        if (!_.isUndefined(name) && !this._isMultigraph) {
          throw new Error("Cannot set a named edge when isMultigraph = false");
        }
        this.setNode(v);
        this.setNode(w);
        this._edgeLabels[e] = valueSpecified ? value : this._defaultEdgeLabelFn(v, w, name);
        var edgeObj = edgeArgsToObj(this._isDirected, v, w, name);
        v = edgeObj.v;
        w = edgeObj.w;
        Object.freeze(edgeObj);
        this._edgeObjs[e] = edgeObj;
        incrementOrInitEntry(this._preds[w], v);
        incrementOrInitEntry(this._sucs[v], w);
        this._in[w][e] = edgeObj;
        this._out[v][e] = edgeObj;
        this._edgeCount++;
        return this;
      };
      Graph.prototype.edge = function(v, w, name) {
        var e = arguments.length === 1 ? edgeObjToId(this._isDirected, arguments[0]) : edgeArgsToId(this._isDirected, v, w, name);
        return this._edgeLabels[e];
      };
      Graph.prototype.hasEdge = function(v, w, name) {
        var e = arguments.length === 1 ? edgeObjToId(this._isDirected, arguments[0]) : edgeArgsToId(this._isDirected, v, w, name);
        return _.has(this._edgeLabels, e);
      };
      Graph.prototype.removeEdge = function(v, w, name) {
        var e = arguments.length === 1 ? edgeObjToId(this._isDirected, arguments[0]) : edgeArgsToId(this._isDirected, v, w, name);
        var edge = this._edgeObjs[e];
        if (edge) {
          v = edge.v;
          w = edge.w;
          delete this._edgeLabels[e];
          delete this._edgeObjs[e];
          decrementOrRemoveEntry(this._preds[w], v);
          decrementOrRemoveEntry(this._sucs[v], w);
          delete this._in[w][e];
          delete this._out[v][e];
          this._edgeCount--;
        }
        return this;
      };
      Graph.prototype.inEdges = function(v, u) {
        var inV = this._in[v];
        if (inV) {
          var edges = _.values(inV);
          if (!u) {
            return edges;
          }
          return _.filter(edges, function(edge) {
            return edge.v === u;
          });
        }
      };
      Graph.prototype.outEdges = function(v, w) {
        var outV = this._out[v];
        if (outV) {
          var edges = _.values(outV);
          if (!w) {
            return edges;
          }
          return _.filter(edges, function(edge) {
            return edge.w === w;
          });
        }
      };
      Graph.prototype.nodeEdges = function(v, w) {
        var inEdges = this.inEdges(v, w);
        if (inEdges) {
          return inEdges.concat(this.outEdges(v, w));
        }
      };
      function incrementOrInitEntry(map, k) {
        if (map[k]) {
          map[k]++;
        } else {
          map[k] = 1;
        }
      }
      function decrementOrRemoveEntry(map, k) {
        if (!--map[k]) {
          delete map[k];
        }
      }
      function edgeArgsToId(isDirected, v_, w_, name) {
        var v = "" + v_;
        var w = "" + w_;
        if (!isDirected && v > w) {
          var tmp = v;
          v = w;
          w = tmp;
        }
        return v + EDGE_KEY_DELIM + w + EDGE_KEY_DELIM + (_.isUndefined(name) ? DEFAULT_EDGE_NAME : name);
      }
      function edgeArgsToObj(isDirected, v_, w_, name) {
        var v = "" + v_;
        var w = "" + w_;
        if (!isDirected && v > w) {
          var tmp = v;
          v = w;
          w = tmp;
        }
        var edgeObj = { v, w };
        if (name) {
          edgeObj.name = name;
        }
        return edgeObj;
      }
      function edgeObjToId(isDirected, edgeObj) {
        return edgeArgsToId(isDirected, edgeObj.v, edgeObj.w, edgeObj.name);
      }
    }
  });

  // node_modules/graphlib/lib/version.js
  var require_version = __commonJS({
    "node_modules/graphlib/lib/version.js"(exports, module) {
      module.exports = "2.1.8";
    }
  });

  // node_modules/graphlib/lib/index.js
  var require_lib = __commonJS({
    "node_modules/graphlib/lib/index.js"(exports, module) {
      module.exports = {
        Graph: require_graph(),
        version: require_version()
      };
    }
  });

  // node_modules/graphlib/lib/json.js
  var require_json = __commonJS({
    "node_modules/graphlib/lib/json.js"(exports, module) {
      var _ = require_lodash();
      var Graph = require_graph();
      module.exports = {
        write,
        read
      };
      function write(g) {
        var json = {
          options: {
            directed: g.isDirected(),
            multigraph: g.isMultigraph(),
            compound: g.isCompound()
          },
          nodes: writeNodes(g),
          edges: writeEdges(g)
        };
        if (!_.isUndefined(g.graph())) {
          json.value = _.clone(g.graph());
        }
        return json;
      }
      function writeNodes(g) {
        return _.map(g.nodes(), function(v) {
          var nodeValue = g.node(v);
          var parent = g.parent(v);
          var node = { v };
          if (!_.isUndefined(nodeValue)) {
            node.value = nodeValue;
          }
          if (!_.isUndefined(parent)) {
            node.parent = parent;
          }
          return node;
        });
      }
      function writeEdges(g) {
        return _.map(g.edges(), function(e) {
          var edgeValue = g.edge(e);
          var edge = { v: e.v, w: e.w };
          if (!_.isUndefined(e.name)) {
            edge.name = e.name;
          }
          if (!_.isUndefined(edgeValue)) {
            edge.value = edgeValue;
          }
          return edge;
        });
      }
      function read(json) {
        var g = new Graph(json.options).setGraph(json.value);
        _.each(json.nodes, function(entry) {
          g.setNode(entry.v, entry.value);
          if (entry.parent) {
            g.setParent(entry.v, entry.parent);
          }
        });
        _.each(json.edges, function(entry) {
          g.setEdge({ v: entry.v, w: entry.w, name: entry.name }, entry.value);
        });
        return g;
      }
    }
  });

  // node_modules/graphlib/lib/alg/components.js
  var require_components = __commonJS({
    "node_modules/graphlib/lib/alg/components.js"(exports, module) {
      var _ = require_lodash();
      module.exports = components;
      function components(g) {
        var visited = {};
        var cmpts = [];
        var cmpt;
        function dfs(v) {
          if (_.has(visited, v)) return;
          visited[v] = true;
          cmpt.push(v);
          _.each(g.successors(v), dfs);
          _.each(g.predecessors(v), dfs);
        }
        _.each(g.nodes(), function(v) {
          cmpt = [];
          dfs(v);
          if (cmpt.length) {
            cmpts.push(cmpt);
          }
        });
        return cmpts;
      }
    }
  });

  // node_modules/graphlib/lib/data/priority-queue.js
  var require_priority_queue = __commonJS({
    "node_modules/graphlib/lib/data/priority-queue.js"(exports, module) {
      var _ = require_lodash();
      module.exports = PriorityQueue;
      function PriorityQueue() {
        this._arr = [];
        this._keyIndices = {};
      }
      PriorityQueue.prototype.size = function() {
        return this._arr.length;
      };
      PriorityQueue.prototype.keys = function() {
        return this._arr.map(function(x) {
          return x.key;
        });
      };
      PriorityQueue.prototype.has = function(key) {
        return _.has(this._keyIndices, key);
      };
      PriorityQueue.prototype.priority = function(key) {
        var index = this._keyIndices[key];
        if (index !== void 0) {
          return this._arr[index].priority;
        }
      };
      PriorityQueue.prototype.min = function() {
        if (this.size() === 0) {
          throw new Error("Queue underflow");
        }
        return this._arr[0].key;
      };
      PriorityQueue.prototype.add = function(key, priority) {
        var keyIndices = this._keyIndices;
        key = String(key);
        if (!_.has(keyIndices, key)) {
          var arr = this._arr;
          var index = arr.length;
          keyIndices[key] = index;
          arr.push({ key, priority });
          this._decrease(index);
          return true;
        }
        return false;
      };
      PriorityQueue.prototype.removeMin = function() {
        this._swap(0, this._arr.length - 1);
        var min = this._arr.pop();
        delete this._keyIndices[min.key];
        this._heapify(0);
        return min.key;
      };
      PriorityQueue.prototype.decrease = function(key, priority) {
        var index = this._keyIndices[key];
        if (priority > this._arr[index].priority) {
          throw new Error("New priority is greater than current priority. Key: " + key + " Old: " + this._arr[index].priority + " New: " + priority);
        }
        this._arr[index].priority = priority;
        this._decrease(index);
      };
      PriorityQueue.prototype._heapify = function(i) {
        var arr = this._arr;
        var l = 2 * i;
        var r = l + 1;
        var largest = i;
        if (l < arr.length) {
          largest = arr[l].priority < arr[largest].priority ? l : largest;
          if (r < arr.length) {
            largest = arr[r].priority < arr[largest].priority ? r : largest;
          }
          if (largest !== i) {
            this._swap(i, largest);
            this._heapify(largest);
          }
        }
      };
      PriorityQueue.prototype._decrease = function(index) {
        var arr = this._arr;
        var priority = arr[index].priority;
        var parent;
        while (index !== 0) {
          parent = index >> 1;
          if (arr[parent].priority < priority) {
            break;
          }
          this._swap(index, parent);
          index = parent;
        }
      };
      PriorityQueue.prototype._swap = function(i, j) {
        var arr = this._arr;
        var keyIndices = this._keyIndices;
        var origArrI = arr[i];
        var origArrJ = arr[j];
        arr[i] = origArrJ;
        arr[j] = origArrI;
        keyIndices[origArrJ.key] = i;
        keyIndices[origArrI.key] = j;
      };
    }
  });

  // node_modules/graphlib/lib/alg/dijkstra.js
  var require_dijkstra = __commonJS({
    "node_modules/graphlib/lib/alg/dijkstra.js"(exports, module) {
      var _ = require_lodash();
      var PriorityQueue = require_priority_queue();
      module.exports = dijkstra;
      var DEFAULT_WEIGHT_FUNC = _.constant(1);
      function dijkstra(g, source, weightFn, edgeFn) {
        return runDijkstra(
          g,
          String(source),
          weightFn || DEFAULT_WEIGHT_FUNC,
          edgeFn || function(v) {
            return g.outEdges(v);
          }
        );
      }
      function runDijkstra(g, source, weightFn, edgeFn) {
        var results = {};
        var pq = new PriorityQueue();
        var v, vEntry;
        var updateNeighbors = function(edge) {
          var w = edge.v !== v ? edge.v : edge.w;
          var wEntry = results[w];
          var weight = weightFn(edge);
          var distance = vEntry.distance + weight;
          if (weight < 0) {
            throw new Error("dijkstra does not allow negative edge weights. Bad edge: " + edge + " Weight: " + weight);
          }
          if (distance < wEntry.distance) {
            wEntry.distance = distance;
            wEntry.predecessor = v;
            pq.decrease(w, distance);
          }
        };
        g.nodes().forEach(function(v2) {
          var distance = v2 === source ? 0 : Number.POSITIVE_INFINITY;
          results[v2] = { distance };
          pq.add(v2, distance);
        });
        while (pq.size() > 0) {
          v = pq.removeMin();
          vEntry = results[v];
          if (vEntry.distance === Number.POSITIVE_INFINITY) {
            break;
          }
          edgeFn(v).forEach(updateNeighbors);
        }
        return results;
      }
    }
  });

  // node_modules/graphlib/lib/alg/dijkstra-all.js
  var require_dijkstra_all = __commonJS({
    "node_modules/graphlib/lib/alg/dijkstra-all.js"(exports, module) {
      var dijkstra = require_dijkstra();
      var _ = require_lodash();
      module.exports = dijkstraAll;
      function dijkstraAll(g, weightFunc, edgeFunc) {
        return _.transform(g.nodes(), function(acc, v) {
          acc[v] = dijkstra(g, v, weightFunc, edgeFunc);
        }, {});
      }
    }
  });

  // node_modules/graphlib/lib/alg/tarjan.js
  var require_tarjan = __commonJS({
    "node_modules/graphlib/lib/alg/tarjan.js"(exports, module) {
      var _ = require_lodash();
      module.exports = tarjan;
      function tarjan(g) {
        var index = 0;
        var stack = [];
        var visited = {};
        var results = [];
        function dfs(v) {
          var entry = visited[v] = {
            onStack: true,
            lowlink: index,
            index: index++
          };
          stack.push(v);
          g.successors(v).forEach(function(w2) {
            if (!_.has(visited, w2)) {
              dfs(w2);
              entry.lowlink = Math.min(entry.lowlink, visited[w2].lowlink);
            } else if (visited[w2].onStack) {
              entry.lowlink = Math.min(entry.lowlink, visited[w2].index);
            }
          });
          if (entry.lowlink === entry.index) {
            var cmpt = [];
            var w;
            do {
              w = stack.pop();
              visited[w].onStack = false;
              cmpt.push(w);
            } while (v !== w);
            results.push(cmpt);
          }
        }
        g.nodes().forEach(function(v) {
          if (!_.has(visited, v)) {
            dfs(v);
          }
        });
        return results;
      }
    }
  });

  // node_modules/graphlib/lib/alg/find-cycles.js
  var require_find_cycles = __commonJS({
    "node_modules/graphlib/lib/alg/find-cycles.js"(exports, module) {
      var _ = require_lodash();
      var tarjan = require_tarjan();
      module.exports = findCycles;
      function findCycles(g) {
        return _.filter(tarjan(g), function(cmpt) {
          return cmpt.length > 1 || cmpt.length === 1 && g.hasEdge(cmpt[0], cmpt[0]);
        });
      }
    }
  });

  // node_modules/graphlib/lib/alg/floyd-warshall.js
  var require_floyd_warshall = __commonJS({
    "node_modules/graphlib/lib/alg/floyd-warshall.js"(exports, module) {
      var _ = require_lodash();
      module.exports = floydWarshall;
      var DEFAULT_WEIGHT_FUNC = _.constant(1);
      function floydWarshall(g, weightFn, edgeFn) {
        return runFloydWarshall(
          g,
          weightFn || DEFAULT_WEIGHT_FUNC,
          edgeFn || function(v) {
            return g.outEdges(v);
          }
        );
      }
      function runFloydWarshall(g, weightFn, edgeFn) {
        var results = {};
        var nodes = g.nodes();
        nodes.forEach(function(v) {
          results[v] = {};
          results[v][v] = { distance: 0 };
          nodes.forEach(function(w) {
            if (v !== w) {
              results[v][w] = { distance: Number.POSITIVE_INFINITY };
            }
          });
          edgeFn(v).forEach(function(edge) {
            var w = edge.v === v ? edge.w : edge.v;
            var d = weightFn(edge);
            results[v][w] = { distance: d, predecessor: v };
          });
        });
        nodes.forEach(function(k) {
          var rowK = results[k];
          nodes.forEach(function(i) {
            var rowI = results[i];
            nodes.forEach(function(j) {
              var ik = rowI[k];
              var kj = rowK[j];
              var ij = rowI[j];
              var altDistance = ik.distance + kj.distance;
              if (altDistance < ij.distance) {
                ij.distance = altDistance;
                ij.predecessor = kj.predecessor;
              }
            });
          });
        });
        return results;
      }
    }
  });

  // node_modules/graphlib/lib/alg/topsort.js
  var require_topsort = __commonJS({
    "node_modules/graphlib/lib/alg/topsort.js"(exports, module) {
      var _ = require_lodash();
      module.exports = topsort;
      topsort.CycleException = CycleException;
      function topsort(g) {
        var visited = {};
        var stack = {};
        var results = [];
        function visit(node) {
          if (_.has(stack, node)) {
            throw new CycleException();
          }
          if (!_.has(visited, node)) {
            stack[node] = true;
            visited[node] = true;
            _.each(g.predecessors(node), visit);
            delete stack[node];
            results.push(node);
          }
        }
        _.each(g.sinks(), visit);
        if (_.size(visited) !== g.nodeCount()) {
          throw new CycleException();
        }
        return results;
      }
      function CycleException() {
      }
      CycleException.prototype = new Error();
    }
  });

  // node_modules/graphlib/lib/alg/is-acyclic.js
  var require_is_acyclic = __commonJS({
    "node_modules/graphlib/lib/alg/is-acyclic.js"(exports, module) {
      var topsort = require_topsort();
      module.exports = isAcyclic;
      function isAcyclic(g) {
        try {
          topsort(g);
        } catch (e) {
          if (e instanceof topsort.CycleException) {
            return false;
          }
          throw e;
        }
        return true;
      }
    }
  });

  // node_modules/graphlib/lib/alg/dfs.js
  var require_dfs = __commonJS({
    "node_modules/graphlib/lib/alg/dfs.js"(exports, module) {
      var _ = require_lodash();
      module.exports = dfs;
      function dfs(g, vs, order) {
        if (!_.isArray(vs)) {
          vs = [vs];
        }
        var navigation = (g.isDirected() ? g.successors : g.neighbors).bind(g);
        var acc = [];
        var visited = {};
        _.each(vs, function(v) {
          if (!g.hasNode(v)) {
            throw new Error("Graph does not have node: " + v);
          }
          doDfs(g, v, order === "post", visited, navigation, acc);
        });
        return acc;
      }
      function doDfs(g, v, postorder, visited, navigation, acc) {
        if (!_.has(visited, v)) {
          visited[v] = true;
          if (!postorder) {
            acc.push(v);
          }
          _.each(navigation(v), function(w) {
            doDfs(g, w, postorder, visited, navigation, acc);
          });
          if (postorder) {
            acc.push(v);
          }
        }
      }
    }
  });

  // node_modules/graphlib/lib/alg/postorder.js
  var require_postorder = __commonJS({
    "node_modules/graphlib/lib/alg/postorder.js"(exports, module) {
      var dfs = require_dfs();
      module.exports = postorder;
      function postorder(g, vs) {
        return dfs(g, vs, "post");
      }
    }
  });

  // node_modules/graphlib/lib/alg/preorder.js
  var require_preorder = __commonJS({
    "node_modules/graphlib/lib/alg/preorder.js"(exports, module) {
      var dfs = require_dfs();
      module.exports = preorder;
      function preorder(g, vs) {
        return dfs(g, vs, "pre");
      }
    }
  });

  // node_modules/graphlib/lib/alg/prim.js
  var require_prim = __commonJS({
    "node_modules/graphlib/lib/alg/prim.js"(exports, module) {
      var _ = require_lodash();
      var Graph = require_graph();
      var PriorityQueue = require_priority_queue();
      module.exports = prim;
      function prim(g, weightFunc) {
        var result = new Graph();
        var parents = {};
        var pq = new PriorityQueue();
        var v;
        function updateNeighbors(edge) {
          var w = edge.v === v ? edge.w : edge.v;
          var pri = pq.priority(w);
          if (pri !== void 0) {
            var edgeWeight = weightFunc(edge);
            if (edgeWeight < pri) {
              parents[w] = v;
              pq.decrease(w, edgeWeight);
            }
          }
        }
        if (g.nodeCount() === 0) {
          return result;
        }
        _.each(g.nodes(), function(v2) {
          pq.add(v2, Number.POSITIVE_INFINITY);
          result.setNode(v2);
        });
        pq.decrease(g.nodes()[0], 0);
        var init2 = false;
        while (pq.size() > 0) {
          v = pq.removeMin();
          if (_.has(parents, v)) {
            result.setEdge(v, parents[v]);
          } else if (init2) {
            throw new Error("Input graph is not connected: " + g);
          } else {
            init2 = true;
          }
          g.nodeEdges(v).forEach(updateNeighbors);
        }
        return result;
      }
    }
  });

  // node_modules/graphlib/lib/alg/index.js
  var require_alg = __commonJS({
    "node_modules/graphlib/lib/alg/index.js"(exports, module) {
      module.exports = {
        components: require_components(),
        dijkstra: require_dijkstra(),
        dijkstraAll: require_dijkstra_all(),
        findCycles: require_find_cycles(),
        floydWarshall: require_floyd_warshall(),
        isAcyclic: require_is_acyclic(),
        postorder: require_postorder(),
        preorder: require_preorder(),
        prim: require_prim(),
        tarjan: require_tarjan(),
        topsort: require_topsort()
      };
    }
  });

  // node_modules/graphlib/index.js
  var require_graphlib = __commonJS({
    "node_modules/graphlib/index.js"(exports, module) {
      var lib = require_lib();
      module.exports = {
        Graph: lib.Graph,
        json: require_json(),
        alg: require_alg(),
        version: lib.version
      };
    }
  });

  // node_modules/dagre/lib/graphlib.js
  var require_graphlib2 = __commonJS({
    "node_modules/dagre/lib/graphlib.js"(exports, module) {
      var graphlib;
      if (typeof __require === "function") {
        try {
          graphlib = require_graphlib();
        } catch (e) {
        }
      }
      if (!graphlib) {
        graphlib = window.graphlib;
      }
      module.exports = graphlib;
    }
  });

  // node_modules/lodash/cloneDeep.js
  var require_cloneDeep = __commonJS({
    "node_modules/lodash/cloneDeep.js"(exports, module) {
      var baseClone = require_baseClone();
      var CLONE_DEEP_FLAG = 1;
      var CLONE_SYMBOLS_FLAG = 4;
      function cloneDeep(value) {
        return baseClone(value, CLONE_DEEP_FLAG | CLONE_SYMBOLS_FLAG);
      }
      module.exports = cloneDeep;
    }
  });

  // node_modules/lodash/_isIterateeCall.js
  var require_isIterateeCall = __commonJS({
    "node_modules/lodash/_isIterateeCall.js"(exports, module) {
      var eq = require_eq();
      var isArrayLike = require_isArrayLike();
      var isIndex = require_isIndex();
      var isObject = require_isObject();
      function isIterateeCall(value, index, object) {
        if (!isObject(object)) {
          return false;
        }
        var type = typeof index;
        if (type == "number" ? isArrayLike(object) && isIndex(index, object.length) : type == "string" && index in object) {
          return eq(object[index], value);
        }
        return false;
      }
      module.exports = isIterateeCall;
    }
  });

  // node_modules/lodash/defaults.js
  var require_defaults = __commonJS({
    "node_modules/lodash/defaults.js"(exports, module) {
      var baseRest = require_baseRest();
      var eq = require_eq();
      var isIterateeCall = require_isIterateeCall();
      var keysIn = require_keysIn();
      var objectProto = Object.prototype;
      var hasOwnProperty = objectProto.hasOwnProperty;
      var defaults = baseRest(function(object, sources) {
        object = Object(object);
        var index = -1;
        var length = sources.length;
        var guard = length > 2 ? sources[2] : void 0;
        if (guard && isIterateeCall(sources[0], sources[1], guard)) {
          length = 1;
        }
        while (++index < length) {
          var source = sources[index];
          var props = keysIn(source);
          var propsIndex = -1;
          var propsLength = props.length;
          while (++propsIndex < propsLength) {
            var key = props[propsIndex];
            var value = object[key];
            if (value === void 0 || eq(value, objectProto[key]) && !hasOwnProperty.call(object, key)) {
              object[key] = source[key];
            }
          }
        }
        return object;
      });
      module.exports = defaults;
    }
  });

  // node_modules/lodash/_createFind.js
  var require_createFind = __commonJS({
    "node_modules/lodash/_createFind.js"(exports, module) {
      var baseIteratee = require_baseIteratee();
      var isArrayLike = require_isArrayLike();
      var keys = require_keys();
      function createFind(findIndexFunc) {
        return function(collection, predicate, fromIndex) {
          var iterable = Object(collection);
          if (!isArrayLike(collection)) {
            var iteratee = baseIteratee(predicate, 3);
            collection = keys(collection);
            predicate = function(key) {
              return iteratee(iterable[key], key, iterable);
            };
          }
          var index = findIndexFunc(collection, predicate, fromIndex);
          return index > -1 ? iterable[iteratee ? collection[index] : index] : void 0;
        };
      }
      module.exports = createFind;
    }
  });

  // node_modules/lodash/_trimmedEndIndex.js
  var require_trimmedEndIndex = __commonJS({
    "node_modules/lodash/_trimmedEndIndex.js"(exports, module) {
      var reWhitespace = /\s/;
      function trimmedEndIndex(string) {
        var index = string.length;
        while (index-- && reWhitespace.test(string.charAt(index))) {
        }
        return index;
      }
      module.exports = trimmedEndIndex;
    }
  });

  // node_modules/lodash/_baseTrim.js
  var require_baseTrim = __commonJS({
    "node_modules/lodash/_baseTrim.js"(exports, module) {
      var trimmedEndIndex = require_trimmedEndIndex();
      var reTrimStart = /^\s+/;
      function baseTrim(string) {
        return string ? string.slice(0, trimmedEndIndex(string) + 1).replace(reTrimStart, "") : string;
      }
      module.exports = baseTrim;
    }
  });

  // node_modules/lodash/toNumber.js
  var require_toNumber = __commonJS({
    "node_modules/lodash/toNumber.js"(exports, module) {
      var baseTrim = require_baseTrim();
      var isObject = require_isObject();
      var isSymbol = require_isSymbol();
      var NAN = 0 / 0;
      var reIsBadHex = /^[-+]0x[0-9a-f]+$/i;
      var reIsBinary = /^0b[01]+$/i;
      var reIsOctal = /^0o[0-7]+$/i;
      var freeParseInt = parseInt;
      function toNumber(value) {
        if (typeof value == "number") {
          return value;
        }
        if (isSymbol(value)) {
          return NAN;
        }
        if (isObject(value)) {
          var other = typeof value.valueOf == "function" ? value.valueOf() : value;
          value = isObject(other) ? other + "" : other;
        }
        if (typeof value != "string") {
          return value === 0 ? value : +value;
        }
        value = baseTrim(value);
        var isBinary = reIsBinary.test(value);
        return isBinary || reIsOctal.test(value) ? freeParseInt(value.slice(2), isBinary ? 2 : 8) : reIsBadHex.test(value) ? NAN : +value;
      }
      module.exports = toNumber;
    }
  });

  // node_modules/lodash/toFinite.js
  var require_toFinite = __commonJS({
    "node_modules/lodash/toFinite.js"(exports, module) {
      var toNumber = require_toNumber();
      var INFINITY = 1 / 0;
      var MAX_INTEGER = 17976931348623157e292;
      function toFinite(value) {
        if (!value) {
          return value === 0 ? value : 0;
        }
        value = toNumber(value);
        if (value === INFINITY || value === -INFINITY) {
          var sign = value < 0 ? -1 : 1;
          return sign * MAX_INTEGER;
        }
        return value === value ? value : 0;
      }
      module.exports = toFinite;
    }
  });

  // node_modules/lodash/toInteger.js
  var require_toInteger = __commonJS({
    "node_modules/lodash/toInteger.js"(exports, module) {
      var toFinite = require_toFinite();
      function toInteger(value) {
        var result = toFinite(value), remainder = result % 1;
        return result === result ? remainder ? result - remainder : result : 0;
      }
      module.exports = toInteger;
    }
  });

  // node_modules/lodash/findIndex.js
  var require_findIndex = __commonJS({
    "node_modules/lodash/findIndex.js"(exports, module) {
      var baseFindIndex = require_baseFindIndex();
      var baseIteratee = require_baseIteratee();
      var toInteger = require_toInteger();
      var nativeMax = Math.max;
      function findIndex(array2, predicate, fromIndex) {
        var length = array2 == null ? 0 : array2.length;
        if (!length) {
          return -1;
        }
        var index = fromIndex == null ? 0 : toInteger(fromIndex);
        if (index < 0) {
          index = nativeMax(length + index, 0);
        }
        return baseFindIndex(array2, baseIteratee(predicate, 3), index);
      }
      module.exports = findIndex;
    }
  });

  // node_modules/lodash/find.js
  var require_find = __commonJS({
    "node_modules/lodash/find.js"(exports, module) {
      var createFind = require_createFind();
      var findIndex = require_findIndex();
      var find2 = createFind(findIndex);
      module.exports = find2;
    }
  });

  // node_modules/lodash/flatten.js
  var require_flatten = __commonJS({
    "node_modules/lodash/flatten.js"(exports, module) {
      var baseFlatten = require_baseFlatten();
      function flatten(array2) {
        var length = array2 == null ? 0 : array2.length;
        return length ? baseFlatten(array2, 1) : [];
      }
      module.exports = flatten;
    }
  });

  // node_modules/lodash/forIn.js
  var require_forIn = __commonJS({
    "node_modules/lodash/forIn.js"(exports, module) {
      var baseFor = require_baseFor();
      var castFunction = require_castFunction();
      var keysIn = require_keysIn();
      function forIn(object, iteratee) {
        return object == null ? object : baseFor(object, castFunction(iteratee), keysIn);
      }
      module.exports = forIn;
    }
  });

  // node_modules/lodash/last.js
  var require_last = __commonJS({
    "node_modules/lodash/last.js"(exports, module) {
      function last(array2) {
        var length = array2 == null ? 0 : array2.length;
        return length ? array2[length - 1] : void 0;
      }
      module.exports = last;
    }
  });

  // node_modules/lodash/mapValues.js
  var require_mapValues = __commonJS({
    "node_modules/lodash/mapValues.js"(exports, module) {
      var baseAssignValue = require_baseAssignValue();
      var baseForOwn = require_baseForOwn();
      var baseIteratee = require_baseIteratee();
      function mapValues(object, iteratee) {
        var result = {};
        iteratee = baseIteratee(iteratee, 3);
        baseForOwn(object, function(value, key, object2) {
          baseAssignValue(result, key, iteratee(value, key, object2));
        });
        return result;
      }
      module.exports = mapValues;
    }
  });

  // node_modules/lodash/_baseExtremum.js
  var require_baseExtremum = __commonJS({
    "node_modules/lodash/_baseExtremum.js"(exports, module) {
      var isSymbol = require_isSymbol();
      function baseExtremum(array2, iteratee, comparator) {
        var index = -1, length = array2.length;
        while (++index < length) {
          var value = array2[index], current = iteratee(value);
          if (current != null && (computed === void 0 ? current === current && !isSymbol(current) : comparator(current, computed))) {
            var computed = current, result = value;
          }
        }
        return result;
      }
      module.exports = baseExtremum;
    }
  });

  // node_modules/lodash/_baseGt.js
  var require_baseGt = __commonJS({
    "node_modules/lodash/_baseGt.js"(exports, module) {
      function baseGt(value, other) {
        return value > other;
      }
      module.exports = baseGt;
    }
  });

  // node_modules/lodash/max.js
  var require_max = __commonJS({
    "node_modules/lodash/max.js"(exports, module) {
      var baseExtremum = require_baseExtremum();
      var baseGt = require_baseGt();
      var identity3 = require_identity();
      function max(array2) {
        return array2 && array2.length ? baseExtremum(array2, identity3, baseGt) : void 0;
      }
      module.exports = max;
    }
  });

  // node_modules/lodash/_assignMergeValue.js
  var require_assignMergeValue = __commonJS({
    "node_modules/lodash/_assignMergeValue.js"(exports, module) {
      var baseAssignValue = require_baseAssignValue();
      var eq = require_eq();
      function assignMergeValue(object, key, value) {
        if (value !== void 0 && !eq(object[key], value) || value === void 0 && !(key in object)) {
          baseAssignValue(object, key, value);
        }
      }
      module.exports = assignMergeValue;
    }
  });

  // node_modules/lodash/isPlainObject.js
  var require_isPlainObject = __commonJS({
    "node_modules/lodash/isPlainObject.js"(exports, module) {
      var baseGetTag = require_baseGetTag();
      var getPrototype = require_getPrototype();
      var isObjectLike = require_isObjectLike();
      var objectTag = "[object Object]";
      var funcProto = Function.prototype;
      var objectProto = Object.prototype;
      var funcToString = funcProto.toString;
      var hasOwnProperty = objectProto.hasOwnProperty;
      var objectCtorString = funcToString.call(Object);
      function isPlainObject(value) {
        if (!isObjectLike(value) || baseGetTag(value) != objectTag) {
          return false;
        }
        var proto = getPrototype(value);
        if (proto === null) {
          return true;
        }
        var Ctor = hasOwnProperty.call(proto, "constructor") && proto.constructor;
        return typeof Ctor == "function" && Ctor instanceof Ctor && funcToString.call(Ctor) == objectCtorString;
      }
      module.exports = isPlainObject;
    }
  });

  // node_modules/lodash/_safeGet.js
  var require_safeGet = __commonJS({
    "node_modules/lodash/_safeGet.js"(exports, module) {
      function safeGet(object, key) {
        if (key === "constructor" && typeof object[key] === "function") {
          return;
        }
        if (key == "__proto__") {
          return;
        }
        return object[key];
      }
      module.exports = safeGet;
    }
  });

  // node_modules/lodash/toPlainObject.js
  var require_toPlainObject = __commonJS({
    "node_modules/lodash/toPlainObject.js"(exports, module) {
      var copyObject = require_copyObject();
      var keysIn = require_keysIn();
      function toPlainObject(value) {
        return copyObject(value, keysIn(value));
      }
      module.exports = toPlainObject;
    }
  });

  // node_modules/lodash/_baseMergeDeep.js
  var require_baseMergeDeep = __commonJS({
    "node_modules/lodash/_baseMergeDeep.js"(exports, module) {
      var assignMergeValue = require_assignMergeValue();
      var cloneBuffer = require_cloneBuffer();
      var cloneTypedArray = require_cloneTypedArray();
      var copyArray = require_copyArray();
      var initCloneObject = require_initCloneObject();
      var isArguments = require_isArguments();
      var isArray = require_isArray();
      var isArrayLikeObject = require_isArrayLikeObject();
      var isBuffer = require_isBuffer();
      var isFunction = require_isFunction();
      var isObject = require_isObject();
      var isPlainObject = require_isPlainObject();
      var isTypedArray = require_isTypedArray();
      var safeGet = require_safeGet();
      var toPlainObject = require_toPlainObject();
      function baseMergeDeep(object, source, key, srcIndex, mergeFunc, customizer, stack) {
        var objValue = safeGet(object, key), srcValue = safeGet(source, key), stacked = stack.get(srcValue);
        if (stacked) {
          assignMergeValue(object, key, stacked);
          return;
        }
        var newValue = customizer ? customizer(objValue, srcValue, key + "", object, source, stack) : void 0;
        var isCommon = newValue === void 0;
        if (isCommon) {
          var isArr = isArray(srcValue), isBuff = !isArr && isBuffer(srcValue), isTyped = !isArr && !isBuff && isTypedArray(srcValue);
          newValue = srcValue;
          if (isArr || isBuff || isTyped) {
            if (isArray(objValue)) {
              newValue = objValue;
            } else if (isArrayLikeObject(objValue)) {
              newValue = copyArray(objValue);
            } else if (isBuff) {
              isCommon = false;
              newValue = cloneBuffer(srcValue, true);
            } else if (isTyped) {
              isCommon = false;
              newValue = cloneTypedArray(srcValue, true);
            } else {
              newValue = [];
            }
          } else if (isPlainObject(srcValue) || isArguments(srcValue)) {
            newValue = objValue;
            if (isArguments(objValue)) {
              newValue = toPlainObject(objValue);
            } else if (!isObject(objValue) || isFunction(objValue)) {
              newValue = initCloneObject(srcValue);
            }
          } else {
            isCommon = false;
          }
        }
        if (isCommon) {
          stack.set(srcValue, newValue);
          mergeFunc(newValue, srcValue, srcIndex, customizer, stack);
          stack["delete"](srcValue);
        }
        assignMergeValue(object, key, newValue);
      }
      module.exports = baseMergeDeep;
    }
  });

  // node_modules/lodash/_baseMerge.js
  var require_baseMerge = __commonJS({
    "node_modules/lodash/_baseMerge.js"(exports, module) {
      var Stack = require_Stack();
      var assignMergeValue = require_assignMergeValue();
      var baseFor = require_baseFor();
      var baseMergeDeep = require_baseMergeDeep();
      var isObject = require_isObject();
      var keysIn = require_keysIn();
      var safeGet = require_safeGet();
      function baseMerge(object, source, srcIndex, customizer, stack) {
        if (object === source) {
          return;
        }
        baseFor(source, function(srcValue, key) {
          stack || (stack = new Stack());
          if (isObject(srcValue)) {
            baseMergeDeep(object, source, key, srcIndex, baseMerge, customizer, stack);
          } else {
            var newValue = customizer ? customizer(safeGet(object, key), srcValue, key + "", object, source, stack) : void 0;
            if (newValue === void 0) {
              newValue = srcValue;
            }
            assignMergeValue(object, key, newValue);
          }
        }, keysIn);
      }
      module.exports = baseMerge;
    }
  });

  // node_modules/lodash/_createAssigner.js
  var require_createAssigner = __commonJS({
    "node_modules/lodash/_createAssigner.js"(exports, module) {
      var baseRest = require_baseRest();
      var isIterateeCall = require_isIterateeCall();
      function createAssigner(assigner) {
        return baseRest(function(object, sources) {
          var index = -1, length = sources.length, customizer = length > 1 ? sources[length - 1] : void 0, guard = length > 2 ? sources[2] : void 0;
          customizer = assigner.length > 3 && typeof customizer == "function" ? (length--, customizer) : void 0;
          if (guard && isIterateeCall(sources[0], sources[1], guard)) {
            customizer = length < 3 ? void 0 : customizer;
            length = 1;
          }
          object = Object(object);
          while (++index < length) {
            var source = sources[index];
            if (source) {
              assigner(object, source, index, customizer);
            }
          }
          return object;
        });
      }
      module.exports = createAssigner;
    }
  });

  // node_modules/lodash/merge.js
  var require_merge = __commonJS({
    "node_modules/lodash/merge.js"(exports, module) {
      var baseMerge = require_baseMerge();
      var createAssigner = require_createAssigner();
      var merge = createAssigner(function(object, source, srcIndex) {
        baseMerge(object, source, srcIndex);
      });
      module.exports = merge;
    }
  });

  // node_modules/lodash/_baseLt.js
  var require_baseLt = __commonJS({
    "node_modules/lodash/_baseLt.js"(exports, module) {
      function baseLt(value, other) {
        return value < other;
      }
      module.exports = baseLt;
    }
  });

  // node_modules/lodash/min.js
  var require_min = __commonJS({
    "node_modules/lodash/min.js"(exports, module) {
      var baseExtremum = require_baseExtremum();
      var baseLt = require_baseLt();
      var identity3 = require_identity();
      function min(array2) {
        return array2 && array2.length ? baseExtremum(array2, identity3, baseLt) : void 0;
      }
      module.exports = min;
    }
  });

  // node_modules/lodash/minBy.js
  var require_minBy = __commonJS({
    "node_modules/lodash/minBy.js"(exports, module) {
      var baseExtremum = require_baseExtremum();
      var baseIteratee = require_baseIteratee();
      var baseLt = require_baseLt();
      function minBy(array2, iteratee) {
        return array2 && array2.length ? baseExtremum(array2, baseIteratee(iteratee, 2), baseLt) : void 0;
      }
      module.exports = minBy;
    }
  });

  // node_modules/lodash/now.js
  var require_now = __commonJS({
    "node_modules/lodash/now.js"(exports, module) {
      var root2 = require_root();
      var now2 = function() {
        return root2.Date.now();
      };
      module.exports = now2;
    }
  });

  // node_modules/lodash/_baseSet.js
  var require_baseSet = __commonJS({
    "node_modules/lodash/_baseSet.js"(exports, module) {
      var assignValue = require_assignValue();
      var castPath = require_castPath();
      var isIndex = require_isIndex();
      var isObject = require_isObject();
      var toKey = require_toKey();
      function baseSet(object, path, value, customizer) {
        if (!isObject(object)) {
          return object;
        }
        path = castPath(path, object);
        var index = -1, length = path.length, lastIndex = length - 1, nested = object;
        while (nested != null && ++index < length) {
          var key = toKey(path[index]), newValue = value;
          if (key === "__proto__" || key === "constructor" || key === "prototype") {
            return object;
          }
          if (index != lastIndex) {
            var objValue = nested[key];
            newValue = customizer ? customizer(objValue, key, nested) : void 0;
            if (newValue === void 0) {
              newValue = isObject(objValue) ? objValue : isIndex(path[index + 1]) ? [] : {};
            }
          }
          assignValue(nested, key, newValue);
          nested = nested[key];
        }
        return object;
      }
      module.exports = baseSet;
    }
  });

  // node_modules/lodash/_basePickBy.js
  var require_basePickBy = __commonJS({
    "node_modules/lodash/_basePickBy.js"(exports, module) {
      var baseGet = require_baseGet();
      var baseSet = require_baseSet();
      var castPath = require_castPath();
      function basePickBy(object, paths, predicate) {
        var index = -1, length = paths.length, result = {};
        while (++index < length) {
          var path = paths[index], value = baseGet(object, path);
          if (predicate(value, path)) {
            baseSet(result, castPath(path, object), value);
          }
        }
        return result;
      }
      module.exports = basePickBy;
    }
  });

  // node_modules/lodash/_basePick.js
  var require_basePick = __commonJS({
    "node_modules/lodash/_basePick.js"(exports, module) {
      var basePickBy = require_basePickBy();
      var hasIn = require_hasIn();
      function basePick(object, paths) {
        return basePickBy(object, paths, function(value, path) {
          return hasIn(object, path);
        });
      }
      module.exports = basePick;
    }
  });

  // node_modules/lodash/_flatRest.js
  var require_flatRest = __commonJS({
    "node_modules/lodash/_flatRest.js"(exports, module) {
      var flatten = require_flatten();
      var overRest = require_overRest();
      var setToString = require_setToString();
      function flatRest(func) {
        return setToString(overRest(func, void 0, flatten), func + "");
      }
      module.exports = flatRest;
    }
  });

  // node_modules/lodash/pick.js
  var require_pick = __commonJS({
    "node_modules/lodash/pick.js"(exports, module) {
      var basePick = require_basePick();
      var flatRest = require_flatRest();
      var pick = flatRest(function(object, paths) {
        return object == null ? {} : basePick(object, paths);
      });
      module.exports = pick;
    }
  });

  // node_modules/lodash/_baseRange.js
  var require_baseRange = __commonJS({
    "node_modules/lodash/_baseRange.js"(exports, module) {
      var nativeCeil = Math.ceil;
      var nativeMax = Math.max;
      function baseRange(start2, end, step, fromRight) {
        var index = -1, length = nativeMax(nativeCeil((end - start2) / (step || 1)), 0), result = Array(length);
        while (length--) {
          result[fromRight ? length : ++index] = start2;
          start2 += step;
        }
        return result;
      }
      module.exports = baseRange;
    }
  });

  // node_modules/lodash/_createRange.js
  var require_createRange = __commonJS({
    "node_modules/lodash/_createRange.js"(exports, module) {
      var baseRange = require_baseRange();
      var isIterateeCall = require_isIterateeCall();
      var toFinite = require_toFinite();
      function createRange(fromRight) {
        return function(start2, end, step) {
          if (step && typeof step != "number" && isIterateeCall(start2, end, step)) {
            end = step = void 0;
          }
          start2 = toFinite(start2);
          if (end === void 0) {
            end = start2;
            start2 = 0;
          } else {
            end = toFinite(end);
          }
          step = step === void 0 ? start2 < end ? 1 : -1 : toFinite(step);
          return baseRange(start2, end, step, fromRight);
        };
      }
      module.exports = createRange;
    }
  });

  // node_modules/lodash/range.js
  var require_range = __commonJS({
    "node_modules/lodash/range.js"(exports, module) {
      var createRange = require_createRange();
      var range = createRange();
      module.exports = range;
    }
  });

  // node_modules/lodash/_baseSortBy.js
  var require_baseSortBy = __commonJS({
    "node_modules/lodash/_baseSortBy.js"(exports, module) {
      function baseSortBy(array2, comparer) {
        var length = array2.length;
        array2.sort(comparer);
        while (length--) {
          array2[length] = array2[length].value;
        }
        return array2;
      }
      module.exports = baseSortBy;
    }
  });

  // node_modules/lodash/_compareAscending.js
  var require_compareAscending = __commonJS({
    "node_modules/lodash/_compareAscending.js"(exports, module) {
      var isSymbol = require_isSymbol();
      function compareAscending(value, other) {
        if (value !== other) {
          var valIsDefined = value !== void 0, valIsNull = value === null, valIsReflexive = value === value, valIsSymbol = isSymbol(value);
          var othIsDefined = other !== void 0, othIsNull = other === null, othIsReflexive = other === other, othIsSymbol = isSymbol(other);
          if (!othIsNull && !othIsSymbol && !valIsSymbol && value > other || valIsSymbol && othIsDefined && othIsReflexive && !othIsNull && !othIsSymbol || valIsNull && othIsDefined && othIsReflexive || !valIsDefined && othIsReflexive || !valIsReflexive) {
            return 1;
          }
          if (!valIsNull && !valIsSymbol && !othIsSymbol && value < other || othIsSymbol && valIsDefined && valIsReflexive && !valIsNull && !valIsSymbol || othIsNull && valIsDefined && valIsReflexive || !othIsDefined && valIsReflexive || !othIsReflexive) {
            return -1;
          }
        }
        return 0;
      }
      module.exports = compareAscending;
    }
  });

  // node_modules/lodash/_compareMultiple.js
  var require_compareMultiple = __commonJS({
    "node_modules/lodash/_compareMultiple.js"(exports, module) {
      var compareAscending = require_compareAscending();
      function compareMultiple(object, other, orders) {
        var index = -1, objCriteria = object.criteria, othCriteria = other.criteria, length = objCriteria.length, ordersLength = orders.length;
        while (++index < length) {
          var result = compareAscending(objCriteria[index], othCriteria[index]);
          if (result) {
            if (index >= ordersLength) {
              return result;
            }
            var order = orders[index];
            return result * (order == "desc" ? -1 : 1);
          }
        }
        return object.index - other.index;
      }
      module.exports = compareMultiple;
    }
  });

  // node_modules/lodash/_baseOrderBy.js
  var require_baseOrderBy = __commonJS({
    "node_modules/lodash/_baseOrderBy.js"(exports, module) {
      var arrayMap = require_arrayMap();
      var baseGet = require_baseGet();
      var baseIteratee = require_baseIteratee();
      var baseMap = require_baseMap();
      var baseSortBy = require_baseSortBy();
      var baseUnary = require_baseUnary();
      var compareMultiple = require_compareMultiple();
      var identity3 = require_identity();
      var isArray = require_isArray();
      function baseOrderBy(collection, iteratees, orders) {
        if (iteratees.length) {
          iteratees = arrayMap(iteratees, function(iteratee) {
            if (isArray(iteratee)) {
              return function(value) {
                return baseGet(value, iteratee.length === 1 ? iteratee[0] : iteratee);
              };
            }
            return iteratee;
          });
        } else {
          iteratees = [identity3];
        }
        var index = -1;
        iteratees = arrayMap(iteratees, baseUnary(baseIteratee));
        var result = baseMap(collection, function(value, key, collection2) {
          var criteria = arrayMap(iteratees, function(iteratee) {
            return iteratee(value);
          });
          return { "criteria": criteria, "index": ++index, "value": value };
        });
        return baseSortBy(result, function(object, other) {
          return compareMultiple(object, other, orders);
        });
      }
      module.exports = baseOrderBy;
    }
  });

  // node_modules/lodash/sortBy.js
  var require_sortBy = __commonJS({
    "node_modules/lodash/sortBy.js"(exports, module) {
      var baseFlatten = require_baseFlatten();
      var baseOrderBy = require_baseOrderBy();
      var baseRest = require_baseRest();
      var isIterateeCall = require_isIterateeCall();
      var sortBy = baseRest(function(collection, iteratees) {
        if (collection == null) {
          return [];
        }
        var length = iteratees.length;
        if (length > 1 && isIterateeCall(collection, iteratees[0], iteratees[1])) {
          iteratees = [];
        } else if (length > 2 && isIterateeCall(iteratees[0], iteratees[1], iteratees[2])) {
          iteratees = [iteratees[0]];
        }
        return baseOrderBy(collection, baseFlatten(iteratees, 1), []);
      });
      module.exports = sortBy;
    }
  });

  // node_modules/lodash/uniqueId.js
  var require_uniqueId = __commonJS({
    "node_modules/lodash/uniqueId.js"(exports, module) {
      var toString = require_toString();
      var idCounter = 0;
      function uniqueId(prefix) {
        var id2 = ++idCounter;
        return toString(prefix) + id2;
      }
      module.exports = uniqueId;
    }
  });

  // node_modules/lodash/_baseZipObject.js
  var require_baseZipObject = __commonJS({
    "node_modules/lodash/_baseZipObject.js"(exports, module) {
      function baseZipObject(props, values, assignFunc) {
        var index = -1, length = props.length, valsLength = values.length, result = {};
        while (++index < length) {
          var value = index < valsLength ? values[index] : void 0;
          assignFunc(result, props[index], value);
        }
        return result;
      }
      module.exports = baseZipObject;
    }
  });

  // node_modules/lodash/zipObject.js
  var require_zipObject = __commonJS({
    "node_modules/lodash/zipObject.js"(exports, module) {
      var assignValue = require_assignValue();
      var baseZipObject = require_baseZipObject();
      function zipObject(props, values) {
        return baseZipObject(props || [], values || [], assignValue);
      }
      module.exports = zipObject;
    }
  });

  // node_modules/dagre/lib/lodash.js
  var require_lodash2 = __commonJS({
    "node_modules/dagre/lib/lodash.js"(exports, module) {
      var lodash;
      if (typeof __require === "function") {
        try {
          lodash = {
            cloneDeep: require_cloneDeep(),
            constant: require_constant(),
            defaults: require_defaults(),
            each: require_each(),
            filter: require_filter(),
            find: require_find(),
            flatten: require_flatten(),
            forEach: require_forEach(),
            forIn: require_forIn(),
            has: require_has(),
            isUndefined: require_isUndefined(),
            last: require_last(),
            map: require_map(),
            mapValues: require_mapValues(),
            max: require_max(),
            merge: require_merge(),
            min: require_min(),
            minBy: require_minBy(),
            now: require_now(),
            pick: require_pick(),
            range: require_range(),
            reduce: require_reduce(),
            sortBy: require_sortBy(),
            uniqueId: require_uniqueId(),
            values: require_values(),
            zipObject: require_zipObject()
          };
        } catch (e) {
        }
      }
      if (!lodash) {
        lodash = window._;
      }
      module.exports = lodash;
    }
  });

  // node_modules/dagre/lib/data/list.js
  var require_list = __commonJS({
    "node_modules/dagre/lib/data/list.js"(exports, module) {
      module.exports = List;
      function List() {
        var sentinel = {};
        sentinel._next = sentinel._prev = sentinel;
        this._sentinel = sentinel;
      }
      List.prototype.dequeue = function() {
        var sentinel = this._sentinel;
        var entry = sentinel._prev;
        if (entry !== sentinel) {
          unlink(entry);
          return entry;
        }
      };
      List.prototype.enqueue = function(entry) {
        var sentinel = this._sentinel;
        if (entry._prev && entry._next) {
          unlink(entry);
        }
        entry._next = sentinel._next;
        sentinel._next._prev = entry;
        sentinel._next = entry;
        entry._prev = sentinel;
      };
      List.prototype.toString = function() {
        var strs = [];
        var sentinel = this._sentinel;
        var curr = sentinel._prev;
        while (curr !== sentinel) {
          strs.push(JSON.stringify(curr, filterOutLinks));
          curr = curr._prev;
        }
        return "[" + strs.join(", ") + "]";
      };
      function unlink(entry) {
        entry._prev._next = entry._next;
        entry._next._prev = entry._prev;
        delete entry._next;
        delete entry._prev;
      }
      function filterOutLinks(k, v) {
        if (k !== "_next" && k !== "_prev") {
          return v;
        }
      }
    }
  });

  // node_modules/dagre/lib/greedy-fas.js
  var require_greedy_fas = __commonJS({
    "node_modules/dagre/lib/greedy-fas.js"(exports, module) {
      var _ = require_lodash2();
      var Graph = require_graphlib2().Graph;
      var List = require_list();
      module.exports = greedyFAS;
      var DEFAULT_WEIGHT_FN = _.constant(1);
      function greedyFAS(g, weightFn) {
        if (g.nodeCount() <= 1) {
          return [];
        }
        var state = buildState(g, weightFn || DEFAULT_WEIGHT_FN);
        var results = doGreedyFAS(state.graph, state.buckets, state.zeroIdx);
        return _.flatten(_.map(results, function(e) {
          return g.outEdges(e.v, e.w);
        }), true);
      }
      function doGreedyFAS(g, buckets, zeroIdx) {
        var results = [];
        var sources = buckets[buckets.length - 1];
        var sinks = buckets[0];
        var entry;
        while (g.nodeCount()) {
          while (entry = sinks.dequeue()) {
            removeNode(g, buckets, zeroIdx, entry);
          }
          while (entry = sources.dequeue()) {
            removeNode(g, buckets, zeroIdx, entry);
          }
          if (g.nodeCount()) {
            for (var i = buckets.length - 2; i > 0; --i) {
              entry = buckets[i].dequeue();
              if (entry) {
                results = results.concat(removeNode(g, buckets, zeroIdx, entry, true));
                break;
              }
            }
          }
        }
        return results;
      }
      function removeNode(g, buckets, zeroIdx, entry, collectPredecessors) {
        var results = collectPredecessors ? [] : void 0;
        _.forEach(g.inEdges(entry.v), function(edge) {
          var weight = g.edge(edge);
          var uEntry = g.node(edge.v);
          if (collectPredecessors) {
            results.push({ v: edge.v, w: edge.w });
          }
          uEntry.out -= weight;
          assignBucket(buckets, zeroIdx, uEntry);
        });
        _.forEach(g.outEdges(entry.v), function(edge) {
          var weight = g.edge(edge);
          var w = edge.w;
          var wEntry = g.node(w);
          wEntry["in"] -= weight;
          assignBucket(buckets, zeroIdx, wEntry);
        });
        g.removeNode(entry.v);
        return results;
      }
      function buildState(g, weightFn) {
        var fasGraph = new Graph();
        var maxIn = 0;
        var maxOut = 0;
        _.forEach(g.nodes(), function(v) {
          fasGraph.setNode(v, { v, "in": 0, out: 0 });
        });
        _.forEach(g.edges(), function(e) {
          var prevWeight = fasGraph.edge(e.v, e.w) || 0;
          var weight = weightFn(e);
          var edgeWeight = prevWeight + weight;
          fasGraph.setEdge(e.v, e.w, edgeWeight);
          maxOut = Math.max(maxOut, fasGraph.node(e.v).out += weight);
          maxIn = Math.max(maxIn, fasGraph.node(e.w)["in"] += weight);
        });
        var buckets = _.range(maxOut + maxIn + 3).map(function() {
          return new List();
        });
        var zeroIdx = maxIn + 1;
        _.forEach(fasGraph.nodes(), function(v) {
          assignBucket(buckets, zeroIdx, fasGraph.node(v));
        });
        return { graph: fasGraph, buckets, zeroIdx };
      }
      function assignBucket(buckets, zeroIdx, entry) {
        if (!entry.out) {
          buckets[0].enqueue(entry);
        } else if (!entry["in"]) {
          buckets[buckets.length - 1].enqueue(entry);
        } else {
          buckets[entry.out - entry["in"] + zeroIdx].enqueue(entry);
        }
      }
    }
  });

  // node_modules/dagre/lib/acyclic.js
  var require_acyclic = __commonJS({
    "node_modules/dagre/lib/acyclic.js"(exports, module) {
      "use strict";
      var _ = require_lodash2();
      var greedyFAS = require_greedy_fas();
      module.exports = {
        run,
        undo
      };
      function run(g) {
        var fas = g.graph().acyclicer === "greedy" ? greedyFAS(g, weightFn(g)) : dfsFAS(g);
        _.forEach(fas, function(e) {
          var label = g.edge(e);
          g.removeEdge(e);
          label.forwardName = e.name;
          label.reversed = true;
          g.setEdge(e.w, e.v, label, _.uniqueId("rev"));
        });
        function weightFn(g2) {
          return function(e) {
            return g2.edge(e).weight;
          };
        }
      }
      function dfsFAS(g) {
        var fas = [];
        var stack = {};
        var visited = {};
        function dfs(v) {
          if (_.has(visited, v)) {
            return;
          }
          visited[v] = true;
          stack[v] = true;
          _.forEach(g.outEdges(v), function(e) {
            if (_.has(stack, e.w)) {
              fas.push(e);
            } else {
              dfs(e.w);
            }
          });
          delete stack[v];
        }
        _.forEach(g.nodes(), dfs);
        return fas;
      }
      function undo(g) {
        _.forEach(g.edges(), function(e) {
          var label = g.edge(e);
          if (label.reversed) {
            g.removeEdge(e);
            var forwardName = label.forwardName;
            delete label.reversed;
            delete label.forwardName;
            g.setEdge(e.w, e.v, label, forwardName);
          }
        });
      }
    }
  });

  // node_modules/dagre/lib/util.js
  var require_util = __commonJS({
    "node_modules/dagre/lib/util.js"(exports, module) {
      "use strict";
      var _ = require_lodash2();
      var Graph = require_graphlib2().Graph;
      module.exports = {
        addDummyNode,
        simplify,
        asNonCompoundGraph,
        successorWeights,
        predecessorWeights,
        intersectRect,
        buildLayerMatrix,
        normalizeRanks,
        removeEmptyRanks,
        addBorderNode,
        maxRank,
        partition,
        time,
        notime
      };
      function addDummyNode(g, type, attrs, name) {
        var v;
        do {
          v = _.uniqueId(name);
        } while (g.hasNode(v));
        attrs.dummy = type;
        g.setNode(v, attrs);
        return v;
      }
      function simplify(g) {
        var simplified = new Graph().setGraph(g.graph());
        _.forEach(g.nodes(), function(v) {
          simplified.setNode(v, g.node(v));
        });
        _.forEach(g.edges(), function(e) {
          var simpleLabel = simplified.edge(e.v, e.w) || { weight: 0, minlen: 1 };
          var label = g.edge(e);
          simplified.setEdge(e.v, e.w, {
            weight: simpleLabel.weight + label.weight,
            minlen: Math.max(simpleLabel.minlen, label.minlen)
          });
        });
        return simplified;
      }
      function asNonCompoundGraph(g) {
        var simplified = new Graph({ multigraph: g.isMultigraph() }).setGraph(g.graph());
        _.forEach(g.nodes(), function(v) {
          if (!g.children(v).length) {
            simplified.setNode(v, g.node(v));
          }
        });
        _.forEach(g.edges(), function(e) {
          simplified.setEdge(e, g.edge(e));
        });
        return simplified;
      }
      function successorWeights(g) {
        var weightMap = _.map(g.nodes(), function(v) {
          var sucs = {};
          _.forEach(g.outEdges(v), function(e) {
            sucs[e.w] = (sucs[e.w] || 0) + g.edge(e).weight;
          });
          return sucs;
        });
        return _.zipObject(g.nodes(), weightMap);
      }
      function predecessorWeights(g) {
        var weightMap = _.map(g.nodes(), function(v) {
          var preds = {};
          _.forEach(g.inEdges(v), function(e) {
            preds[e.v] = (preds[e.v] || 0) + g.edge(e).weight;
          });
          return preds;
        });
        return _.zipObject(g.nodes(), weightMap);
      }
      function intersectRect(rect, point) {
        var x = rect.x;
        var y = rect.y;
        var dx = point.x - x;
        var dy = point.y - y;
        var w = rect.width / 2;
        var h = rect.height / 2;
        if (!dx && !dy) {
          throw new Error("Not possible to find intersection inside of the rectangle");
        }
        var sx, sy;
        if (Math.abs(dy) * w > Math.abs(dx) * h) {
          if (dy < 0) {
            h = -h;
          }
          sx = h * dx / dy;
          sy = h;
        } else {
          if (dx < 0) {
            w = -w;
          }
          sx = w;
          sy = w * dy / dx;
        }
        return { x: x + sx, y: y + sy };
      }
      function buildLayerMatrix(g) {
        var layering = _.map(_.range(maxRank(g) + 1), function() {
          return [];
        });
        _.forEach(g.nodes(), function(v) {
          var node = g.node(v);
          var rank = node.rank;
          if (!_.isUndefined(rank)) {
            layering[rank][node.order] = v;
          }
        });
        return layering;
      }
      function normalizeRanks(g) {
        var min = _.min(_.map(g.nodes(), function(v) {
          return g.node(v).rank;
        }));
        _.forEach(g.nodes(), function(v) {
          var node = g.node(v);
          if (_.has(node, "rank")) {
            node.rank -= min;
          }
        });
      }
      function removeEmptyRanks(g) {
        var offset = _.min(_.map(g.nodes(), function(v) {
          return g.node(v).rank;
        }));
        var layers = [];
        _.forEach(g.nodes(), function(v) {
          var rank = g.node(v).rank - offset;
          if (!layers[rank]) {
            layers[rank] = [];
          }
          layers[rank].push(v);
        });
        var delta = 0;
        var nodeRankFactor = g.graph().nodeRankFactor;
        _.forEach(layers, function(vs, i) {
          if (_.isUndefined(vs) && i % nodeRankFactor !== 0) {
            --delta;
          } else if (delta) {
            _.forEach(vs, function(v) {
              g.node(v).rank += delta;
            });
          }
        });
      }
      function addBorderNode(g, prefix, rank, order) {
        var node = {
          width: 0,
          height: 0
        };
        if (arguments.length >= 4) {
          node.rank = rank;
          node.order = order;
        }
        return addDummyNode(g, "border", node, prefix);
      }
      function maxRank(g) {
        return _.max(_.map(g.nodes(), function(v) {
          var rank = g.node(v).rank;
          if (!_.isUndefined(rank)) {
            return rank;
          }
        }));
      }
      function partition(collection, fn) {
        var result = { lhs: [], rhs: [] };
        _.forEach(collection, function(value) {
          if (fn(value)) {
            result.lhs.push(value);
          } else {
            result.rhs.push(value);
          }
        });
        return result;
      }
      function time(name, fn) {
        var start2 = _.now();
        try {
          return fn();
        } finally {
          console.log(name + " time: " + (_.now() - start2) + "ms");
        }
      }
      function notime(name, fn) {
        return fn();
      }
    }
  });

  // node_modules/dagre/lib/normalize.js
  var require_normalize = __commonJS({
    "node_modules/dagre/lib/normalize.js"(exports, module) {
      "use strict";
      var _ = require_lodash2();
      var util = require_util();
      module.exports = {
        run,
        undo
      };
      function run(g) {
        g.graph().dummyChains = [];
        _.forEach(g.edges(), function(edge) {
          normalizeEdge2(g, edge);
        });
      }
      function normalizeEdge2(g, e) {
        var v = e.v;
        var vRank = g.node(v).rank;
        var w = e.w;
        var wRank = g.node(w).rank;
        var name = e.name;
        var edgeLabel = g.edge(e);
        var labelRank = edgeLabel.labelRank;
        if (wRank === vRank + 1) return;
        g.removeEdge(e);
        var dummy, attrs, i;
        for (i = 0, ++vRank; vRank < wRank; ++i, ++vRank) {
          edgeLabel.points = [];
          attrs = {
            width: 0,
            height: 0,
            edgeLabel,
            edgeObj: e,
            rank: vRank
          };
          dummy = util.addDummyNode(g, "edge", attrs, "_d");
          if (vRank === labelRank) {
            attrs.width = edgeLabel.width;
            attrs.height = edgeLabel.height;
            attrs.dummy = "edge-label";
            attrs.labelpos = edgeLabel.labelpos;
          }
          g.setEdge(v, dummy, { weight: edgeLabel.weight }, name);
          if (i === 0) {
            g.graph().dummyChains.push(dummy);
          }
          v = dummy;
        }
        g.setEdge(v, w, { weight: edgeLabel.weight }, name);
      }
      function undo(g) {
        _.forEach(g.graph().dummyChains, function(v) {
          var node = g.node(v);
          var origLabel = node.edgeLabel;
          var w;
          g.setEdge(node.edgeObj, origLabel);
          while (node.dummy) {
            w = g.successors(v)[0];
            g.removeNode(v);
            origLabel.points.push({ x: node.x, y: node.y });
            if (node.dummy === "edge-label") {
              origLabel.x = node.x;
              origLabel.y = node.y;
              origLabel.width = node.width;
              origLabel.height = node.height;
            }
            v = w;
            node = g.node(v);
          }
        });
      }
    }
  });

  // node_modules/dagre/lib/rank/util.js
  var require_util2 = __commonJS({
    "node_modules/dagre/lib/rank/util.js"(exports, module) {
      "use strict";
      var _ = require_lodash2();
      module.exports = {
        longestPath,
        slack
      };
      function longestPath(g) {
        var visited = {};
        function dfs(v) {
          var label = g.node(v);
          if (_.has(visited, v)) {
            return label.rank;
          }
          visited[v] = true;
          var rank = _.min(_.map(g.outEdges(v), function(e) {
            return dfs(e.w) - g.edge(e).minlen;
          }));
          if (rank === Number.POSITIVE_INFINITY || // return value of _.map([]) for Lodash 3
          rank === void 0 || // return value of _.map([]) for Lodash 4
          rank === null) {
            rank = 0;
          }
          return label.rank = rank;
        }
        _.forEach(g.sources(), dfs);
      }
      function slack(g, e) {
        return g.node(e.w).rank - g.node(e.v).rank - g.edge(e).minlen;
      }
    }
  });

  // node_modules/dagre/lib/rank/feasible-tree.js
  var require_feasible_tree = __commonJS({
    "node_modules/dagre/lib/rank/feasible-tree.js"(exports, module) {
      "use strict";
      var _ = require_lodash2();
      var Graph = require_graphlib2().Graph;
      var slack = require_util2().slack;
      module.exports = feasibleTree;
      function feasibleTree(g) {
        var t = new Graph({ directed: false });
        var start2 = g.nodes()[0];
        var size = g.nodeCount();
        t.setNode(start2, {});
        var edge, delta;
        while (tightTree(t, g) < size) {
          edge = findMinSlackEdge(t, g);
          delta = t.hasNode(edge.v) ? slack(g, edge) : -slack(g, edge);
          shiftRanks(t, g, delta);
        }
        return t;
      }
      function tightTree(t, g) {
        function dfs(v) {
          _.forEach(g.nodeEdges(v), function(e) {
            var edgeV = e.v, w = v === edgeV ? e.w : edgeV;
            if (!t.hasNode(w) && !slack(g, e)) {
              t.setNode(w, {});
              t.setEdge(v, w, {});
              dfs(w);
            }
          });
        }
        _.forEach(t.nodes(), dfs);
        return t.nodeCount();
      }
      function findMinSlackEdge(t, g) {
        return _.minBy(g.edges(), function(e) {
          if (t.hasNode(e.v) !== t.hasNode(e.w)) {
            return slack(g, e);
          }
        });
      }
      function shiftRanks(t, g, delta) {
        _.forEach(t.nodes(), function(v) {
          g.node(v).rank += delta;
        });
      }
    }
  });

  // node_modules/dagre/lib/rank/network-simplex.js
  var require_network_simplex = __commonJS({
    "node_modules/dagre/lib/rank/network-simplex.js"(exports, module) {
      "use strict";
      var _ = require_lodash2();
      var feasibleTree = require_feasible_tree();
      var slack = require_util2().slack;
      var initRank = require_util2().longestPath;
      var preorder = require_graphlib2().alg.preorder;
      var postorder = require_graphlib2().alg.postorder;
      var simplify = require_util().simplify;
      module.exports = networkSimplex;
      networkSimplex.initLowLimValues = initLowLimValues;
      networkSimplex.initCutValues = initCutValues;
      networkSimplex.calcCutValue = calcCutValue;
      networkSimplex.leaveEdge = leaveEdge;
      networkSimplex.enterEdge = enterEdge;
      networkSimplex.exchangeEdges = exchangeEdges;
      function networkSimplex(g) {
        g = simplify(g);
        initRank(g);
        var t = feasibleTree(g);
        initLowLimValues(t);
        initCutValues(t, g);
        var e, f;
        while (e = leaveEdge(t)) {
          f = enterEdge(t, g, e);
          exchangeEdges(t, g, e, f);
        }
      }
      function initCutValues(t, g) {
        var vs = postorder(t, t.nodes());
        vs = vs.slice(0, vs.length - 1);
        _.forEach(vs, function(v) {
          assignCutValue(t, g, v);
        });
      }
      function assignCutValue(t, g, child) {
        var childLab = t.node(child);
        var parent = childLab.parent;
        t.edge(child, parent).cutvalue = calcCutValue(t, g, child);
      }
      function calcCutValue(t, g, child) {
        var childLab = t.node(child);
        var parent = childLab.parent;
        var childIsTail = true;
        var graphEdge = g.edge(child, parent);
        var cutValue = 0;
        if (!graphEdge) {
          childIsTail = false;
          graphEdge = g.edge(parent, child);
        }
        cutValue = graphEdge.weight;
        _.forEach(g.nodeEdges(child), function(e) {
          var isOutEdge = e.v === child, other = isOutEdge ? e.w : e.v;
          if (other !== parent) {
            var pointsToHead = isOutEdge === childIsTail, otherWeight = g.edge(e).weight;
            cutValue += pointsToHead ? otherWeight : -otherWeight;
            if (isTreeEdge(t, child, other)) {
              var otherCutValue = t.edge(child, other).cutvalue;
              cutValue += pointsToHead ? -otherCutValue : otherCutValue;
            }
          }
        });
        return cutValue;
      }
      function initLowLimValues(tree, root2) {
        if (arguments.length < 2) {
          root2 = tree.nodes()[0];
        }
        dfsAssignLowLim(tree, {}, 1, root2);
      }
      function dfsAssignLowLim(tree, visited, nextLim, v, parent) {
        var low = nextLim;
        var label = tree.node(v);
        visited[v] = true;
        _.forEach(tree.neighbors(v), function(w) {
          if (!_.has(visited, w)) {
            nextLim = dfsAssignLowLim(tree, visited, nextLim, w, v);
          }
        });
        label.low = low;
        label.lim = nextLim++;
        if (parent) {
          label.parent = parent;
        } else {
          delete label.parent;
        }
        return nextLim;
      }
      function leaveEdge(tree) {
        return _.find(tree.edges(), function(e) {
          return tree.edge(e).cutvalue < 0;
        });
      }
      function enterEdge(t, g, edge) {
        var v = edge.v;
        var w = edge.w;
        if (!g.hasEdge(v, w)) {
          v = edge.w;
          w = edge.v;
        }
        var vLabel = t.node(v);
        var wLabel = t.node(w);
        var tailLabel = vLabel;
        var flip = false;
        if (vLabel.lim > wLabel.lim) {
          tailLabel = wLabel;
          flip = true;
        }
        var candidates = _.filter(g.edges(), function(edge2) {
          return flip === isDescendant(t, t.node(edge2.v), tailLabel) && flip !== isDescendant(t, t.node(edge2.w), tailLabel);
        });
        return _.minBy(candidates, function(edge2) {
          return slack(g, edge2);
        });
      }
      function exchangeEdges(t, g, e, f) {
        var v = e.v;
        var w = e.w;
        t.removeEdge(v, w);
        t.setEdge(f.v, f.w, {});
        initLowLimValues(t);
        initCutValues(t, g);
        updateRanks(t, g);
      }
      function updateRanks(t, g) {
        var root2 = _.find(t.nodes(), function(v) {
          return !g.node(v).parent;
        });
        var vs = preorder(t, root2);
        vs = vs.slice(1);
        _.forEach(vs, function(v) {
          var parent = t.node(v).parent, edge = g.edge(v, parent), flipped = false;
          if (!edge) {
            edge = g.edge(parent, v);
            flipped = true;
          }
          g.node(v).rank = g.node(parent).rank + (flipped ? edge.minlen : -edge.minlen);
        });
      }
      function isTreeEdge(tree, u, v) {
        return tree.hasEdge(u, v);
      }
      function isDescendant(tree, vLabel, rootLabel) {
        return rootLabel.low <= vLabel.lim && vLabel.lim <= rootLabel.lim;
      }
    }
  });

  // node_modules/dagre/lib/rank/index.js
  var require_rank = __commonJS({
    "node_modules/dagre/lib/rank/index.js"(exports, module) {
      "use strict";
      var rankUtil = require_util2();
      var longestPath = rankUtil.longestPath;
      var feasibleTree = require_feasible_tree();
      var networkSimplex = require_network_simplex();
      module.exports = rank;
      function rank(g) {
        switch (g.graph().ranker) {
          case "network-simplex":
            networkSimplexRanker(g);
            break;
          case "tight-tree":
            tightTreeRanker(g);
            break;
          case "longest-path":
            longestPathRanker(g);
            break;
          default:
            networkSimplexRanker(g);
        }
      }
      var longestPathRanker = longestPath;
      function tightTreeRanker(g) {
        longestPath(g);
        feasibleTree(g);
      }
      function networkSimplexRanker(g) {
        networkSimplex(g);
      }
    }
  });

  // node_modules/dagre/lib/parent-dummy-chains.js
  var require_parent_dummy_chains = __commonJS({
    "node_modules/dagre/lib/parent-dummy-chains.js"(exports, module) {
      var _ = require_lodash2();
      module.exports = parentDummyChains;
      function parentDummyChains(g) {
        var postorderNums = postorder(g);
        _.forEach(g.graph().dummyChains, function(v) {
          var node = g.node(v);
          var edgeObj = node.edgeObj;
          var pathData = findPath(g, postorderNums, edgeObj.v, edgeObj.w);
          var path = pathData.path;
          var lca = pathData.lca;
          var pathIdx = 0;
          var pathV = path[pathIdx];
          var ascending2 = true;
          while (v !== edgeObj.w) {
            node = g.node(v);
            if (ascending2) {
              while ((pathV = path[pathIdx]) !== lca && g.node(pathV).maxRank < node.rank) {
                pathIdx++;
              }
              if (pathV === lca) {
                ascending2 = false;
              }
            }
            if (!ascending2) {
              while (pathIdx < path.length - 1 && g.node(pathV = path[pathIdx + 1]).minRank <= node.rank) {
                pathIdx++;
              }
              pathV = path[pathIdx];
            }
            g.setParent(v, pathV);
            v = g.successors(v)[0];
          }
        });
      }
      function findPath(g, postorderNums, v, w) {
        var vPath = [];
        var wPath = [];
        var low = Math.min(postorderNums[v].low, postorderNums[w].low);
        var lim = Math.max(postorderNums[v].lim, postorderNums[w].lim);
        var parent;
        var lca;
        parent = v;
        do {
          parent = g.parent(parent);
          vPath.push(parent);
        } while (parent && (postorderNums[parent].low > low || lim > postorderNums[parent].lim));
        lca = parent;
        parent = w;
        while ((parent = g.parent(parent)) !== lca) {
          wPath.push(parent);
        }
        return { path: vPath.concat(wPath.reverse()), lca };
      }
      function postorder(g) {
        var result = {};
        var lim = 0;
        function dfs(v) {
          var low = lim;
          _.forEach(g.children(v), dfs);
          result[v] = { low, lim: lim++ };
        }
        _.forEach(g.children(), dfs);
        return result;
      }
    }
  });

  // node_modules/dagre/lib/nesting-graph.js
  var require_nesting_graph = __commonJS({
    "node_modules/dagre/lib/nesting-graph.js"(exports, module) {
      var _ = require_lodash2();
      var util = require_util();
      module.exports = {
        run,
        cleanup
      };
      function run(g) {
        var root2 = util.addDummyNode(g, "root", {}, "_root");
        var depths = treeDepths(g);
        var height = _.max(_.values(depths)) - 1;
        var nodeSep = 2 * height + 1;
        g.graph().nestingRoot = root2;
        _.forEach(g.edges(), function(e) {
          g.edge(e).minlen *= nodeSep;
        });
        var weight = sumWeights(g) + 1;
        _.forEach(g.children(), function(child) {
          dfs(g, root2, nodeSep, weight, height, depths, child);
        });
        g.graph().nodeRankFactor = nodeSep;
      }
      function dfs(g, root2, nodeSep, weight, height, depths, v) {
        var children2 = g.children(v);
        if (!children2.length) {
          if (v !== root2) {
            g.setEdge(root2, v, { weight: 0, minlen: nodeSep });
          }
          return;
        }
        var top = util.addBorderNode(g, "_bt");
        var bottom = util.addBorderNode(g, "_bb");
        var label = g.node(v);
        g.setParent(top, v);
        label.borderTop = top;
        g.setParent(bottom, v);
        label.borderBottom = bottom;
        _.forEach(children2, function(child) {
          dfs(g, root2, nodeSep, weight, height, depths, child);
          var childNode = g.node(child);
          var childTop = childNode.borderTop ? childNode.borderTop : child;
          var childBottom = childNode.borderBottom ? childNode.borderBottom : child;
          var thisWeight = childNode.borderTop ? weight : 2 * weight;
          var minlen = childTop !== childBottom ? 1 : height - depths[v] + 1;
          g.setEdge(top, childTop, {
            weight: thisWeight,
            minlen,
            nestingEdge: true
          });
          g.setEdge(childBottom, bottom, {
            weight: thisWeight,
            minlen,
            nestingEdge: true
          });
        });
        if (!g.parent(v)) {
          g.setEdge(root2, top, { weight: 0, minlen: height + depths[v] });
        }
      }
      function treeDepths(g) {
        var depths = {};
        function dfs2(v, depth) {
          var children2 = g.children(v);
          if (children2 && children2.length) {
            _.forEach(children2, function(child) {
              dfs2(child, depth + 1);
            });
          }
          depths[v] = depth;
        }
        _.forEach(g.children(), function(v) {
          dfs2(v, 1);
        });
        return depths;
      }
      function sumWeights(g) {
        return _.reduce(g.edges(), function(acc, e) {
          return acc + g.edge(e).weight;
        }, 0);
      }
      function cleanup(g) {
        var graphLabel = g.graph();
        g.removeNode(graphLabel.nestingRoot);
        delete graphLabel.nestingRoot;
        _.forEach(g.edges(), function(e) {
          var edge = g.edge(e);
          if (edge.nestingEdge) {
            g.removeEdge(e);
          }
        });
      }
    }
  });

  // node_modules/dagre/lib/add-border-segments.js
  var require_add_border_segments = __commonJS({
    "node_modules/dagre/lib/add-border-segments.js"(exports, module) {
      var _ = require_lodash2();
      var util = require_util();
      module.exports = addBorderSegments;
      function addBorderSegments(g) {
        function dfs(v) {
          var children2 = g.children(v);
          var node = g.node(v);
          if (children2.length) {
            _.forEach(children2, dfs);
          }
          if (_.has(node, "minRank")) {
            node.borderLeft = [];
            node.borderRight = [];
            for (var rank = node.minRank, maxRank = node.maxRank + 1; rank < maxRank; ++rank) {
              addBorderNode(g, "borderLeft", "_bl", v, node, rank);
              addBorderNode(g, "borderRight", "_br", v, node, rank);
            }
          }
        }
        _.forEach(g.children(), dfs);
      }
      function addBorderNode(g, prop, prefix, sg, sgNode, rank) {
        var label = { width: 0, height: 0, rank, borderType: prop };
        var prev = sgNode[prop][rank - 1];
        var curr = util.addDummyNode(g, "border", label, prefix);
        sgNode[prop][rank] = curr;
        g.setParent(curr, sg);
        if (prev) {
          g.setEdge(prev, curr, { weight: 1 });
        }
      }
    }
  });

  // node_modules/dagre/lib/coordinate-system.js
  var require_coordinate_system = __commonJS({
    "node_modules/dagre/lib/coordinate-system.js"(exports, module) {
      "use strict";
      var _ = require_lodash2();
      module.exports = {
        adjust,
        undo
      };
      function adjust(g) {
        var rankDir = g.graph().rankdir.toLowerCase();
        if (rankDir === "lr" || rankDir === "rl") {
          swapWidthHeight(g);
        }
      }
      function undo(g) {
        var rankDir = g.graph().rankdir.toLowerCase();
        if (rankDir === "bt" || rankDir === "rl") {
          reverseY(g);
        }
        if (rankDir === "lr" || rankDir === "rl") {
          swapXY(g);
          swapWidthHeight(g);
        }
      }
      function swapWidthHeight(g) {
        _.forEach(g.nodes(), function(v) {
          swapWidthHeightOne(g.node(v));
        });
        _.forEach(g.edges(), function(e) {
          swapWidthHeightOne(g.edge(e));
        });
      }
      function swapWidthHeightOne(attrs) {
        var w = attrs.width;
        attrs.width = attrs.height;
        attrs.height = w;
      }
      function reverseY(g) {
        _.forEach(g.nodes(), function(v) {
          reverseYOne(g.node(v));
        });
        _.forEach(g.edges(), function(e) {
          var edge = g.edge(e);
          _.forEach(edge.points, reverseYOne);
          if (_.has(edge, "y")) {
            reverseYOne(edge);
          }
        });
      }
      function reverseYOne(attrs) {
        attrs.y = -attrs.y;
      }
      function swapXY(g) {
        _.forEach(g.nodes(), function(v) {
          swapXYOne(g.node(v));
        });
        _.forEach(g.edges(), function(e) {
          var edge = g.edge(e);
          _.forEach(edge.points, swapXYOne);
          if (_.has(edge, "x")) {
            swapXYOne(edge);
          }
        });
      }
      function swapXYOne(attrs) {
        var x = attrs.x;
        attrs.x = attrs.y;
        attrs.y = x;
      }
    }
  });

  // node_modules/dagre/lib/order/init-order.js
  var require_init_order = __commonJS({
    "node_modules/dagre/lib/order/init-order.js"(exports, module) {
      "use strict";
      var _ = require_lodash2();
      module.exports = initOrder;
      function initOrder(g) {
        var visited = {};
        var simpleNodes = _.filter(g.nodes(), function(v) {
          return !g.children(v).length;
        });
        var maxRank = _.max(_.map(simpleNodes, function(v) {
          return g.node(v).rank;
        }));
        var layers = _.map(_.range(maxRank + 1), function() {
          return [];
        });
        function dfs(v) {
          if (_.has(visited, v)) return;
          visited[v] = true;
          var node = g.node(v);
          layers[node.rank].push(v);
          _.forEach(g.successors(v), dfs);
        }
        var orderedVs = _.sortBy(simpleNodes, function(v) {
          return g.node(v).rank;
        });
        _.forEach(orderedVs, dfs);
        return layers;
      }
    }
  });

  // node_modules/dagre/lib/order/cross-count.js
  var require_cross_count = __commonJS({
    "node_modules/dagre/lib/order/cross-count.js"(exports, module) {
      "use strict";
      var _ = require_lodash2();
      module.exports = crossCount;
      function crossCount(g, layering) {
        var cc = 0;
        for (var i = 1; i < layering.length; ++i) {
          cc += twoLayerCrossCount(g, layering[i - 1], layering[i]);
        }
        return cc;
      }
      function twoLayerCrossCount(g, northLayer, southLayer) {
        var southPos = _.zipObject(
          southLayer,
          _.map(southLayer, function(v, i) {
            return i;
          })
        );
        var southEntries = _.flatten(_.map(northLayer, function(v) {
          return _.sortBy(_.map(g.outEdges(v), function(e) {
            return { pos: southPos[e.w], weight: g.edge(e).weight };
          }), "pos");
        }), true);
        var firstIndex = 1;
        while (firstIndex < southLayer.length) firstIndex <<= 1;
        var treeSize = 2 * firstIndex - 1;
        firstIndex -= 1;
        var tree = _.map(new Array(treeSize), function() {
          return 0;
        });
        var cc = 0;
        _.forEach(southEntries.forEach(function(entry) {
          var index = entry.pos + firstIndex;
          tree[index] += entry.weight;
          var weightSum = 0;
          while (index > 0) {
            if (index % 2) {
              weightSum += tree[index + 1];
            }
            index = index - 1 >> 1;
            tree[index] += entry.weight;
          }
          cc += entry.weight * weightSum;
        }));
        return cc;
      }
    }
  });

  // node_modules/dagre/lib/order/barycenter.js
  var require_barycenter = __commonJS({
    "node_modules/dagre/lib/order/barycenter.js"(exports, module) {
      var _ = require_lodash2();
      module.exports = barycenter;
      function barycenter(g, movable) {
        return _.map(movable, function(v) {
          var inV = g.inEdges(v);
          if (!inV.length) {
            return { v };
          } else {
            var result = _.reduce(inV, function(acc, e) {
              var edge = g.edge(e), nodeU = g.node(e.v);
              return {
                sum: acc.sum + edge.weight * nodeU.order,
                weight: acc.weight + edge.weight
              };
            }, { sum: 0, weight: 0 });
            return {
              v,
              barycenter: result.sum / result.weight,
              weight: result.weight
            };
          }
        });
      }
    }
  });

  // node_modules/dagre/lib/order/resolve-conflicts.js
  var require_resolve_conflicts = __commonJS({
    "node_modules/dagre/lib/order/resolve-conflicts.js"(exports, module) {
      "use strict";
      var _ = require_lodash2();
      module.exports = resolveConflicts;
      function resolveConflicts(entries, cg) {
        var mappedEntries = {};
        _.forEach(entries, function(entry, i) {
          var tmp = mappedEntries[entry.v] = {
            indegree: 0,
            "in": [],
            out: [],
            vs: [entry.v],
            i
          };
          if (!_.isUndefined(entry.barycenter)) {
            tmp.barycenter = entry.barycenter;
            tmp.weight = entry.weight;
          }
        });
        _.forEach(cg.edges(), function(e) {
          var entryV = mappedEntries[e.v];
          var entryW = mappedEntries[e.w];
          if (!_.isUndefined(entryV) && !_.isUndefined(entryW)) {
            entryW.indegree++;
            entryV.out.push(mappedEntries[e.w]);
          }
        });
        var sourceSet = _.filter(mappedEntries, function(entry) {
          return !entry.indegree;
        });
        return doResolveConflicts(sourceSet);
      }
      function doResolveConflicts(sourceSet) {
        var entries = [];
        function handleIn(vEntry) {
          return function(uEntry) {
            if (uEntry.merged) {
              return;
            }
            if (_.isUndefined(uEntry.barycenter) || _.isUndefined(vEntry.barycenter) || uEntry.barycenter >= vEntry.barycenter) {
              mergeEntries(vEntry, uEntry);
            }
          };
        }
        function handleOut(vEntry) {
          return function(wEntry) {
            wEntry["in"].push(vEntry);
            if (--wEntry.indegree === 0) {
              sourceSet.push(wEntry);
            }
          };
        }
        while (sourceSet.length) {
          var entry = sourceSet.pop();
          entries.push(entry);
          _.forEach(entry["in"].reverse(), handleIn(entry));
          _.forEach(entry.out, handleOut(entry));
        }
        return _.map(
          _.filter(entries, function(entry2) {
            return !entry2.merged;
          }),
          function(entry2) {
            return _.pick(entry2, ["vs", "i", "barycenter", "weight"]);
          }
        );
      }
      function mergeEntries(target, source) {
        var sum = 0;
        var weight = 0;
        if (target.weight) {
          sum += target.barycenter * target.weight;
          weight += target.weight;
        }
        if (source.weight) {
          sum += source.barycenter * source.weight;
          weight += source.weight;
        }
        target.vs = source.vs.concat(target.vs);
        target.barycenter = sum / weight;
        target.weight = weight;
        target.i = Math.min(source.i, target.i);
        source.merged = true;
      }
    }
  });

  // node_modules/dagre/lib/order/sort.js
  var require_sort = __commonJS({
    "node_modules/dagre/lib/order/sort.js"(exports, module) {
      var _ = require_lodash2();
      var util = require_util();
      module.exports = sort;
      function sort(entries, biasRight) {
        var parts = util.partition(entries, function(entry) {
          return _.has(entry, "barycenter");
        });
        var sortable = parts.lhs, unsortable = _.sortBy(parts.rhs, function(entry) {
          return -entry.i;
        }), vs = [], sum = 0, weight = 0, vsIndex = 0;
        sortable.sort(compareWithBias(!!biasRight));
        vsIndex = consumeUnsortable(vs, unsortable, vsIndex);
        _.forEach(sortable, function(entry) {
          vsIndex += entry.vs.length;
          vs.push(entry.vs);
          sum += entry.barycenter * entry.weight;
          weight += entry.weight;
          vsIndex = consumeUnsortable(vs, unsortable, vsIndex);
        });
        var result = { vs: _.flatten(vs, true) };
        if (weight) {
          result.barycenter = sum / weight;
          result.weight = weight;
        }
        return result;
      }
      function consumeUnsortable(vs, unsortable, index) {
        var last;
        while (unsortable.length && (last = _.last(unsortable)).i <= index) {
          unsortable.pop();
          vs.push(last.vs);
          index++;
        }
        return index;
      }
      function compareWithBias(bias) {
        return function(entryV, entryW) {
          if (entryV.barycenter < entryW.barycenter) {
            return -1;
          } else if (entryV.barycenter > entryW.barycenter) {
            return 1;
          }
          return !bias ? entryV.i - entryW.i : entryW.i - entryV.i;
        };
      }
    }
  });

  // node_modules/dagre/lib/order/sort-subgraph.js
  var require_sort_subgraph = __commonJS({
    "node_modules/dagre/lib/order/sort-subgraph.js"(exports, module) {
      var _ = require_lodash2();
      var barycenter = require_barycenter();
      var resolveConflicts = require_resolve_conflicts();
      var sort = require_sort();
      module.exports = sortSubgraph;
      function sortSubgraph(g, v, cg, biasRight) {
        var movable = g.children(v);
        var node = g.node(v);
        var bl = node ? node.borderLeft : void 0;
        var br = node ? node.borderRight : void 0;
        var subgraphs = {};
        if (bl) {
          movable = _.filter(movable, function(w) {
            return w !== bl && w !== br;
          });
        }
        var barycenters = barycenter(g, movable);
        _.forEach(barycenters, function(entry) {
          if (g.children(entry.v).length) {
            var subgraphResult = sortSubgraph(g, entry.v, cg, biasRight);
            subgraphs[entry.v] = subgraphResult;
            if (_.has(subgraphResult, "barycenter")) {
              mergeBarycenters(entry, subgraphResult);
            }
          }
        });
        var entries = resolveConflicts(barycenters, cg);
        expandSubgraphs(entries, subgraphs);
        var result = sort(entries, biasRight);
        if (bl) {
          result.vs = _.flatten([bl, result.vs, br], true);
          if (g.predecessors(bl).length) {
            var blPred = g.node(g.predecessors(bl)[0]), brPred = g.node(g.predecessors(br)[0]);
            if (!_.has(result, "barycenter")) {
              result.barycenter = 0;
              result.weight = 0;
            }
            result.barycenter = (result.barycenter * result.weight + blPred.order + brPred.order) / (result.weight + 2);
            result.weight += 2;
          }
        }
        return result;
      }
      function expandSubgraphs(entries, subgraphs) {
        _.forEach(entries, function(entry) {
          entry.vs = _.flatten(entry.vs.map(function(v) {
            if (subgraphs[v]) {
              return subgraphs[v].vs;
            }
            return v;
          }), true);
        });
      }
      function mergeBarycenters(target, other) {
        if (!_.isUndefined(target.barycenter)) {
          target.barycenter = (target.barycenter * target.weight + other.barycenter * other.weight) / (target.weight + other.weight);
          target.weight += other.weight;
        } else {
          target.barycenter = other.barycenter;
          target.weight = other.weight;
        }
      }
    }
  });

  // node_modules/dagre/lib/order/build-layer-graph.js
  var require_build_layer_graph = __commonJS({
    "node_modules/dagre/lib/order/build-layer-graph.js"(exports, module) {
      var _ = require_lodash2();
      var Graph = require_graphlib2().Graph;
      module.exports = buildLayerGraph;
      function buildLayerGraph(g, rank, relationship) {
        var root2 = createRootNode(g), result = new Graph({ compound: true }).setGraph({ root: root2 }).setDefaultNodeLabel(function(v) {
          return g.node(v);
        });
        _.forEach(g.nodes(), function(v) {
          var node = g.node(v), parent = g.parent(v);
          if (node.rank === rank || node.minRank <= rank && rank <= node.maxRank) {
            result.setNode(v);
            result.setParent(v, parent || root2);
            _.forEach(g[relationship](v), function(e) {
              var u = e.v === v ? e.w : e.v, edge = result.edge(u, v), weight = !_.isUndefined(edge) ? edge.weight : 0;
              result.setEdge(u, v, { weight: g.edge(e).weight + weight });
            });
            if (_.has(node, "minRank")) {
              result.setNode(v, {
                borderLeft: node.borderLeft[rank],
                borderRight: node.borderRight[rank]
              });
            }
          }
        });
        return result;
      }
      function createRootNode(g) {
        var v;
        while (g.hasNode(v = _.uniqueId("_root"))) ;
        return v;
      }
    }
  });

  // node_modules/dagre/lib/order/add-subgraph-constraints.js
  var require_add_subgraph_constraints = __commonJS({
    "node_modules/dagre/lib/order/add-subgraph-constraints.js"(exports, module) {
      var _ = require_lodash2();
      module.exports = addSubgraphConstraints;
      function addSubgraphConstraints(g, cg, vs) {
        var prev = {}, rootPrev;
        _.forEach(vs, function(v) {
          var child = g.parent(v), parent, prevChild;
          while (child) {
            parent = g.parent(child);
            if (parent) {
              prevChild = prev[parent];
              prev[parent] = child;
            } else {
              prevChild = rootPrev;
              rootPrev = child;
            }
            if (prevChild && prevChild !== child) {
              cg.setEdge(prevChild, child);
              return;
            }
            child = parent;
          }
        });
      }
    }
  });

  // node_modules/dagre/lib/order/index.js
  var require_order = __commonJS({
    "node_modules/dagre/lib/order/index.js"(exports, module) {
      "use strict";
      var _ = require_lodash2();
      var initOrder = require_init_order();
      var crossCount = require_cross_count();
      var sortSubgraph = require_sort_subgraph();
      var buildLayerGraph = require_build_layer_graph();
      var addSubgraphConstraints = require_add_subgraph_constraints();
      var Graph = require_graphlib2().Graph;
      var util = require_util();
      module.exports = order;
      function order(g) {
        var maxRank = util.maxRank(g), downLayerGraphs = buildLayerGraphs(g, _.range(1, maxRank + 1), "inEdges"), upLayerGraphs = buildLayerGraphs(g, _.range(maxRank - 1, -1, -1), "outEdges");
        var layering = initOrder(g);
        assignOrder(g, layering);
        var bestCC = Number.POSITIVE_INFINITY, best;
        for (var i = 0, lastBest = 0; lastBest < 4; ++i, ++lastBest) {
          sweepLayerGraphs(i % 2 ? downLayerGraphs : upLayerGraphs, i % 4 >= 2);
          layering = util.buildLayerMatrix(g);
          var cc = crossCount(g, layering);
          if (cc < bestCC) {
            lastBest = 0;
            best = _.cloneDeep(layering);
            bestCC = cc;
          }
        }
        assignOrder(g, best);
      }
      function buildLayerGraphs(g, ranks, relationship) {
        return _.map(ranks, function(rank) {
          return buildLayerGraph(g, rank, relationship);
        });
      }
      function sweepLayerGraphs(layerGraphs, biasRight) {
        var cg = new Graph();
        _.forEach(layerGraphs, function(lg) {
          var root2 = lg.graph().root;
          var sorted = sortSubgraph(lg, root2, cg, biasRight);
          _.forEach(sorted.vs, function(v, i) {
            lg.node(v).order = i;
          });
          addSubgraphConstraints(lg, cg, sorted.vs);
        });
      }
      function assignOrder(g, layering) {
        _.forEach(layering, function(layer) {
          _.forEach(layer, function(v, i) {
            g.node(v).order = i;
          });
        });
      }
    }
  });

  // node_modules/dagre/lib/position/bk.js
  var require_bk = __commonJS({
    "node_modules/dagre/lib/position/bk.js"(exports, module) {
      "use strict";
      var _ = require_lodash2();
      var Graph = require_graphlib2().Graph;
      var util = require_util();
      module.exports = {
        positionX,
        findType1Conflicts,
        findType2Conflicts,
        addConflict,
        hasConflict,
        verticalAlignment,
        horizontalCompaction,
        alignCoordinates,
        findSmallestWidthAlignment,
        balance
      };
      function findType1Conflicts(g, layering) {
        var conflicts = {};
        function visitLayer(prevLayer, layer) {
          var k0 = 0, scanPos = 0, prevLayerLength = prevLayer.length, lastNode = _.last(layer);
          _.forEach(layer, function(v, i) {
            var w = findOtherInnerSegmentNode(g, v), k1 = w ? g.node(w).order : prevLayerLength;
            if (w || v === lastNode) {
              _.forEach(layer.slice(scanPos, i + 1), function(scanNode) {
                _.forEach(g.predecessors(scanNode), function(u) {
                  var uLabel = g.node(u), uPos = uLabel.order;
                  if ((uPos < k0 || k1 < uPos) && !(uLabel.dummy && g.node(scanNode).dummy)) {
                    addConflict(conflicts, u, scanNode);
                  }
                });
              });
              scanPos = i + 1;
              k0 = k1;
            }
          });
          return layer;
        }
        _.reduce(layering, visitLayer);
        return conflicts;
      }
      function findType2Conflicts(g, layering) {
        var conflicts = {};
        function scan(south, southPos, southEnd, prevNorthBorder, nextNorthBorder) {
          var v;
          _.forEach(_.range(southPos, southEnd), function(i) {
            v = south[i];
            if (g.node(v).dummy) {
              _.forEach(g.predecessors(v), function(u) {
                var uNode = g.node(u);
                if (uNode.dummy && (uNode.order < prevNorthBorder || uNode.order > nextNorthBorder)) {
                  addConflict(conflicts, u, v);
                }
              });
            }
          });
        }
        function visitLayer(north, south) {
          var prevNorthPos = -1, nextNorthPos, southPos = 0;
          _.forEach(south, function(v, southLookahead) {
            if (g.node(v).dummy === "border") {
              var predecessors = g.predecessors(v);
              if (predecessors.length) {
                nextNorthPos = g.node(predecessors[0]).order;
                scan(south, southPos, southLookahead, prevNorthPos, nextNorthPos);
                southPos = southLookahead;
                prevNorthPos = nextNorthPos;
              }
            }
            scan(south, southPos, south.length, nextNorthPos, north.length);
          });
          return south;
        }
        _.reduce(layering, visitLayer);
        return conflicts;
      }
      function findOtherInnerSegmentNode(g, v) {
        if (g.node(v).dummy) {
          return _.find(g.predecessors(v), function(u) {
            return g.node(u).dummy;
          });
        }
      }
      function addConflict(conflicts, v, w) {
        if (v > w) {
          var tmp = v;
          v = w;
          w = tmp;
        }
        var conflictsV = conflicts[v];
        if (!conflictsV) {
          conflicts[v] = conflictsV = {};
        }
        conflictsV[w] = true;
      }
      function hasConflict(conflicts, v, w) {
        if (v > w) {
          var tmp = v;
          v = w;
          w = tmp;
        }
        return _.has(conflicts[v], w);
      }
      function verticalAlignment(g, layering, conflicts, neighborFn) {
        var root2 = {}, align = {}, pos = {};
        _.forEach(layering, function(layer) {
          _.forEach(layer, function(v, order) {
            root2[v] = v;
            align[v] = v;
            pos[v] = order;
          });
        });
        _.forEach(layering, function(layer) {
          var prevIdx = -1;
          _.forEach(layer, function(v) {
            var ws = neighborFn(v);
            if (ws.length) {
              ws = _.sortBy(ws, function(w2) {
                return pos[w2];
              });
              var mp = (ws.length - 1) / 2;
              for (var i = Math.floor(mp), il = Math.ceil(mp); i <= il; ++i) {
                var w = ws[i];
                if (align[v] === v && prevIdx < pos[w] && !hasConflict(conflicts, v, w)) {
                  align[w] = v;
                  align[v] = root2[v] = root2[w];
                  prevIdx = pos[w];
                }
              }
            }
          });
        });
        return { root: root2, align };
      }
      function horizontalCompaction(g, layering, root2, align, reverseSep) {
        var xs = {}, blockG = buildBlockGraph(g, layering, root2, reverseSep), borderType = reverseSep ? "borderLeft" : "borderRight";
        function iterate(setXsFunc, nextNodesFunc) {
          var stack = blockG.nodes();
          var elem = stack.pop();
          var visited = {};
          while (elem) {
            if (visited[elem]) {
              setXsFunc(elem);
            } else {
              visited[elem] = true;
              stack.push(elem);
              stack = stack.concat(nextNodesFunc(elem));
            }
            elem = stack.pop();
          }
        }
        function pass1(elem) {
          xs[elem] = blockG.inEdges(elem).reduce(function(acc, e) {
            return Math.max(acc, xs[e.v] + blockG.edge(e));
          }, 0);
        }
        function pass2(elem) {
          var min = blockG.outEdges(elem).reduce(function(acc, e) {
            return Math.min(acc, xs[e.w] - blockG.edge(e));
          }, Number.POSITIVE_INFINITY);
          var node = g.node(elem);
          if (min !== Number.POSITIVE_INFINITY && node.borderType !== borderType) {
            xs[elem] = Math.max(xs[elem], min);
          }
        }
        iterate(pass1, blockG.predecessors.bind(blockG));
        iterate(pass2, blockG.successors.bind(blockG));
        _.forEach(align, function(v) {
          xs[v] = xs[root2[v]];
        });
        return xs;
      }
      function buildBlockGraph(g, layering, root2, reverseSep) {
        var blockGraph = new Graph(), graphLabel = g.graph(), sepFn = sep(graphLabel.nodesep, graphLabel.edgesep, reverseSep);
        _.forEach(layering, function(layer) {
          var u;
          _.forEach(layer, function(v) {
            var vRoot = root2[v];
            blockGraph.setNode(vRoot);
            if (u) {
              var uRoot = root2[u], prevMax = blockGraph.edge(uRoot, vRoot);
              blockGraph.setEdge(uRoot, vRoot, Math.max(sepFn(g, v, u), prevMax || 0));
            }
            u = v;
          });
        });
        return blockGraph;
      }
      function findSmallestWidthAlignment(g, xss) {
        return _.minBy(_.values(xss), function(xs) {
          var max = Number.NEGATIVE_INFINITY;
          var min = Number.POSITIVE_INFINITY;
          _.forIn(xs, function(x, v) {
            var halfWidth = width(g, v) / 2;
            max = Math.max(x + halfWidth, max);
            min = Math.min(x - halfWidth, min);
          });
          return max - min;
        });
      }
      function alignCoordinates(xss, alignTo) {
        var alignToVals = _.values(alignTo), alignToMin = _.min(alignToVals), alignToMax = _.max(alignToVals);
        _.forEach(["u", "d"], function(vert) {
          _.forEach(["l", "r"], function(horiz) {
            var alignment = vert + horiz, xs = xss[alignment], delta;
            if (xs === alignTo) return;
            var xsVals = _.values(xs);
            delta = horiz === "l" ? alignToMin - _.min(xsVals) : alignToMax - _.max(xsVals);
            if (delta) {
              xss[alignment] = _.mapValues(xs, function(x) {
                return x + delta;
              });
            }
          });
        });
      }
      function balance(xss, align) {
        return _.mapValues(xss.ul, function(ignore, v) {
          if (align) {
            return xss[align.toLowerCase()][v];
          } else {
            var xs = _.sortBy(_.map(xss, v));
            return (xs[1] + xs[2]) / 2;
          }
        });
      }
      function positionX(g) {
        var layering = util.buildLayerMatrix(g);
        var conflicts = _.merge(
          findType1Conflicts(g, layering),
          findType2Conflicts(g, layering)
        );
        var xss = {};
        var adjustedLayering;
        _.forEach(["u", "d"], function(vert) {
          adjustedLayering = vert === "u" ? layering : _.values(layering).reverse();
          _.forEach(["l", "r"], function(horiz) {
            if (horiz === "r") {
              adjustedLayering = _.map(adjustedLayering, function(inner) {
                return _.values(inner).reverse();
              });
            }
            var neighborFn = (vert === "u" ? g.predecessors : g.successors).bind(g);
            var align = verticalAlignment(g, adjustedLayering, conflicts, neighborFn);
            var xs = horizontalCompaction(
              g,
              adjustedLayering,
              align.root,
              align.align,
              horiz === "r"
            );
            if (horiz === "r") {
              xs = _.mapValues(xs, function(x) {
                return -x;
              });
            }
            xss[vert + horiz] = xs;
          });
        });
        var smallestWidth = findSmallestWidthAlignment(g, xss);
        alignCoordinates(xss, smallestWidth);
        return balance(xss, g.graph().align);
      }
      function sep(nodeSep, edgeSep, reverseSep) {
        return function(g, v, w) {
          var vLabel = g.node(v);
          var wLabel = g.node(w);
          var sum = 0;
          var delta;
          sum += vLabel.width / 2;
          if (_.has(vLabel, "labelpos")) {
            switch (vLabel.labelpos.toLowerCase()) {
              case "l":
                delta = -vLabel.width / 2;
                break;
              case "r":
                delta = vLabel.width / 2;
                break;
            }
          }
          if (delta) {
            sum += reverseSep ? delta : -delta;
          }
          delta = 0;
          sum += (vLabel.dummy ? edgeSep : nodeSep) / 2;
          sum += (wLabel.dummy ? edgeSep : nodeSep) / 2;
          sum += wLabel.width / 2;
          if (_.has(wLabel, "labelpos")) {
            switch (wLabel.labelpos.toLowerCase()) {
              case "l":
                delta = wLabel.width / 2;
                break;
              case "r":
                delta = -wLabel.width / 2;
                break;
            }
          }
          if (delta) {
            sum += reverseSep ? delta : -delta;
          }
          delta = 0;
          return sum;
        };
      }
      function width(g, v) {
        return g.node(v).width;
      }
    }
  });

  // node_modules/dagre/lib/position/index.js
  var require_position = __commonJS({
    "node_modules/dagre/lib/position/index.js"(exports, module) {
      "use strict";
      var _ = require_lodash2();
      var util = require_util();
      var positionX = require_bk().positionX;
      module.exports = position;
      function position(g) {
        g = util.asNonCompoundGraph(g);
        positionY(g);
        _.forEach(positionX(g), function(x, v) {
          g.node(v).x = x;
        });
      }
      function positionY(g) {
        var layering = util.buildLayerMatrix(g);
        var rankSep = g.graph().ranksep;
        var prevY = 0;
        _.forEach(layering, function(layer) {
          var maxHeight = _.max(_.map(layer, function(v) {
            return g.node(v).height;
          }));
          _.forEach(layer, function(v) {
            g.node(v).y = prevY + maxHeight / 2;
          });
          prevY += maxHeight + rankSep;
        });
      }
    }
  });

  // node_modules/dagre/lib/layout.js
  var require_layout = __commonJS({
    "node_modules/dagre/lib/layout.js"(exports, module) {
      "use strict";
      var _ = require_lodash2();
      var acyclic = require_acyclic();
      var normalize = require_normalize();
      var rank = require_rank();
      var normalizeRanks = require_util().normalizeRanks;
      var parentDummyChains = require_parent_dummy_chains();
      var removeEmptyRanks = require_util().removeEmptyRanks;
      var nestingGraph = require_nesting_graph();
      var addBorderSegments = require_add_border_segments();
      var coordinateSystem = require_coordinate_system();
      var order = require_order();
      var position = require_position();
      var util = require_util();
      var Graph = require_graphlib2().Graph;
      module.exports = layout;
      function layout(g, opts) {
        var time = opts && opts.debugTiming ? util.time : util.notime;
        time("layout", function() {
          var layoutGraph = time("  buildLayoutGraph", function() {
            return buildLayoutGraph(g);
          });
          time("  runLayout", function() {
            runLayout(layoutGraph, time);
          });
          time("  updateInputGraph", function() {
            updateInputGraph(g, layoutGraph);
          });
        });
      }
      function runLayout(g, time) {
        time("    makeSpaceForEdgeLabels", function() {
          makeSpaceForEdgeLabels(g);
        });
        time("    removeSelfEdges", function() {
          removeSelfEdges(g);
        });
        time("    acyclic", function() {
          acyclic.run(g);
        });
        time("    nestingGraph.run", function() {
          nestingGraph.run(g);
        });
        time("    rank", function() {
          rank(util.asNonCompoundGraph(g));
        });
        time("    injectEdgeLabelProxies", function() {
          injectEdgeLabelProxies(g);
        });
        time("    removeEmptyRanks", function() {
          removeEmptyRanks(g);
        });
        time("    nestingGraph.cleanup", function() {
          nestingGraph.cleanup(g);
        });
        time("    normalizeRanks", function() {
          normalizeRanks(g);
        });
        time("    assignRankMinMax", function() {
          assignRankMinMax(g);
        });
        time("    removeEdgeLabelProxies", function() {
          removeEdgeLabelProxies(g);
        });
        time("    normalize.run", function() {
          normalize.run(g);
        });
        time("    parentDummyChains", function() {
          parentDummyChains(g);
        });
        time("    addBorderSegments", function() {
          addBorderSegments(g);
        });
        time("    order", function() {
          order(g);
        });
        time("    insertSelfEdges", function() {
          insertSelfEdges(g);
        });
        time("    adjustCoordinateSystem", function() {
          coordinateSystem.adjust(g);
        });
        time("    position", function() {
          position(g);
        });
        time("    positionSelfEdges", function() {
          positionSelfEdges(g);
        });
        time("    removeBorderNodes", function() {
          removeBorderNodes(g);
        });
        time("    normalize.undo", function() {
          normalize.undo(g);
        });
        time("    fixupEdgeLabelCoords", function() {
          fixupEdgeLabelCoords(g);
        });
        time("    undoCoordinateSystem", function() {
          coordinateSystem.undo(g);
        });
        time("    translateGraph", function() {
          translateGraph(g);
        });
        time("    assignNodeIntersects", function() {
          assignNodeIntersects(g);
        });
        time("    reversePoints", function() {
          reversePointsForReversedEdges(g);
        });
        time("    acyclic.undo", function() {
          acyclic.undo(g);
        });
      }
      function updateInputGraph(inputGraph, layoutGraph) {
        _.forEach(inputGraph.nodes(), function(v) {
          var inputLabel = inputGraph.node(v);
          var layoutLabel = layoutGraph.node(v);
          if (inputLabel) {
            inputLabel.x = layoutLabel.x;
            inputLabel.y = layoutLabel.y;
            if (layoutGraph.children(v).length) {
              inputLabel.width = layoutLabel.width;
              inputLabel.height = layoutLabel.height;
            }
          }
        });
        _.forEach(inputGraph.edges(), function(e) {
          var inputLabel = inputGraph.edge(e);
          var layoutLabel = layoutGraph.edge(e);
          inputLabel.points = layoutLabel.points;
          if (_.has(layoutLabel, "x")) {
            inputLabel.x = layoutLabel.x;
            inputLabel.y = layoutLabel.y;
          }
        });
        inputGraph.graph().width = layoutGraph.graph().width;
        inputGraph.graph().height = layoutGraph.graph().height;
      }
      var graphNumAttrs = ["nodesep", "edgesep", "ranksep", "marginx", "marginy"];
      var graphDefaults = { ranksep: 50, edgesep: 20, nodesep: 50, rankdir: "tb" };
      var graphAttrs = ["acyclicer", "ranker", "rankdir", "align"];
      var nodeNumAttrs = ["width", "height"];
      var nodeDefaults = { width: 0, height: 0 };
      var edgeNumAttrs = ["minlen", "weight", "width", "height", "labeloffset"];
      var edgeDefaults = {
        minlen: 1,
        weight: 1,
        width: 0,
        height: 0,
        labeloffset: 10,
        labelpos: "r"
      };
      var edgeAttrs = ["labelpos"];
      function buildLayoutGraph(inputGraph) {
        var g = new Graph({ multigraph: true, compound: true });
        var graph = canonicalize(inputGraph.graph());
        g.setGraph(_.merge(
          {},
          graphDefaults,
          selectNumberAttrs(graph, graphNumAttrs),
          _.pick(graph, graphAttrs)
        ));
        _.forEach(inputGraph.nodes(), function(v) {
          var node = canonicalize(inputGraph.node(v));
          g.setNode(v, _.defaults(selectNumberAttrs(node, nodeNumAttrs), nodeDefaults));
          g.setParent(v, inputGraph.parent(v));
        });
        _.forEach(inputGraph.edges(), function(e) {
          var edge = canonicalize(inputGraph.edge(e));
          g.setEdge(e, _.merge(
            {},
            edgeDefaults,
            selectNumberAttrs(edge, edgeNumAttrs),
            _.pick(edge, edgeAttrs)
          ));
        });
        return g;
      }
      function makeSpaceForEdgeLabels(g) {
        var graph = g.graph();
        graph.ranksep /= 2;
        _.forEach(g.edges(), function(e) {
          var edge = g.edge(e);
          edge.minlen *= 2;
          if (edge.labelpos.toLowerCase() !== "c") {
            if (graph.rankdir === "TB" || graph.rankdir === "BT") {
              edge.width += edge.labeloffset;
            } else {
              edge.height += edge.labeloffset;
            }
          }
        });
      }
      function injectEdgeLabelProxies(g) {
        _.forEach(g.edges(), function(e) {
          var edge = g.edge(e);
          if (edge.width && edge.height) {
            var v = g.node(e.v);
            var w = g.node(e.w);
            var label = { rank: (w.rank - v.rank) / 2 + v.rank, e };
            util.addDummyNode(g, "edge-proxy", label, "_ep");
          }
        });
      }
      function assignRankMinMax(g) {
        var maxRank = 0;
        _.forEach(g.nodes(), function(v) {
          var node = g.node(v);
          if (node.borderTop) {
            node.minRank = g.node(node.borderTop).rank;
            node.maxRank = g.node(node.borderBottom).rank;
            maxRank = _.max(maxRank, node.maxRank);
          }
        });
        g.graph().maxRank = maxRank;
      }
      function removeEdgeLabelProxies(g) {
        _.forEach(g.nodes(), function(v) {
          var node = g.node(v);
          if (node.dummy === "edge-proxy") {
            g.edge(node.e).labelRank = node.rank;
            g.removeNode(v);
          }
        });
      }
      function translateGraph(g) {
        var minX = Number.POSITIVE_INFINITY;
        var maxX = 0;
        var minY = Number.POSITIVE_INFINITY;
        var maxY = 0;
        var graphLabel = g.graph();
        var marginX = graphLabel.marginx || 0;
        var marginY = graphLabel.marginy || 0;
        function getExtremes(attrs) {
          var x = attrs.x;
          var y = attrs.y;
          var w = attrs.width;
          var h = attrs.height;
          minX = Math.min(minX, x - w / 2);
          maxX = Math.max(maxX, x + w / 2);
          minY = Math.min(minY, y - h / 2);
          maxY = Math.max(maxY, y + h / 2);
        }
        _.forEach(g.nodes(), function(v) {
          getExtremes(g.node(v));
        });
        _.forEach(g.edges(), function(e) {
          var edge = g.edge(e);
          if (_.has(edge, "x")) {
            getExtremes(edge);
          }
        });
        minX -= marginX;
        minY -= marginY;
        _.forEach(g.nodes(), function(v) {
          var node = g.node(v);
          node.x -= minX;
          node.y -= minY;
        });
        _.forEach(g.edges(), function(e) {
          var edge = g.edge(e);
          _.forEach(edge.points, function(p) {
            p.x -= minX;
            p.y -= minY;
          });
          if (_.has(edge, "x")) {
            edge.x -= minX;
          }
          if (_.has(edge, "y")) {
            edge.y -= minY;
          }
        });
        graphLabel.width = maxX - minX + marginX;
        graphLabel.height = maxY - minY + marginY;
      }
      function assignNodeIntersects(g) {
        _.forEach(g.edges(), function(e) {
          var edge = g.edge(e);
          var nodeV = g.node(e.v);
          var nodeW = g.node(e.w);
          var p1, p2;
          if (!edge.points) {
            edge.points = [];
            p1 = nodeW;
            p2 = nodeV;
          } else {
            p1 = edge.points[0];
            p2 = edge.points[edge.points.length - 1];
          }
          edge.points.unshift(util.intersectRect(nodeV, p1));
          edge.points.push(util.intersectRect(nodeW, p2));
        });
      }
      function fixupEdgeLabelCoords(g) {
        _.forEach(g.edges(), function(e) {
          var edge = g.edge(e);
          if (_.has(edge, "x")) {
            if (edge.labelpos === "l" || edge.labelpos === "r") {
              edge.width -= edge.labeloffset;
            }
            switch (edge.labelpos) {
              case "l":
                edge.x -= edge.width / 2 + edge.labeloffset;
                break;
              case "r":
                edge.x += edge.width / 2 + edge.labeloffset;
                break;
            }
          }
        });
      }
      function reversePointsForReversedEdges(g) {
        _.forEach(g.edges(), function(e) {
          var edge = g.edge(e);
          if (edge.reversed) {
            edge.points.reverse();
          }
        });
      }
      function removeBorderNodes(g) {
        _.forEach(g.nodes(), function(v) {
          if (g.children(v).length) {
            var node = g.node(v);
            var t = g.node(node.borderTop);
            var b = g.node(node.borderBottom);
            var l = g.node(_.last(node.borderLeft));
            var r = g.node(_.last(node.borderRight));
            node.width = Math.abs(r.x - l.x);
            node.height = Math.abs(b.y - t.y);
            node.x = l.x + node.width / 2;
            node.y = t.y + node.height / 2;
          }
        });
        _.forEach(g.nodes(), function(v) {
          if (g.node(v).dummy === "border") {
            g.removeNode(v);
          }
        });
      }
      function removeSelfEdges(g) {
        _.forEach(g.edges(), function(e) {
          if (e.v === e.w) {
            var node = g.node(e.v);
            if (!node.selfEdges) {
              node.selfEdges = [];
            }
            node.selfEdges.push({ e, label: g.edge(e) });
            g.removeEdge(e);
          }
        });
      }
      function insertSelfEdges(g) {
        var layers = util.buildLayerMatrix(g);
        _.forEach(layers, function(layer) {
          var orderShift = 0;
          _.forEach(layer, function(v, i) {
            var node = g.node(v);
            node.order = i + orderShift;
            _.forEach(node.selfEdges, function(selfEdge) {
              util.addDummyNode(g, "selfedge", {
                width: selfEdge.label.width,
                height: selfEdge.label.height,
                rank: node.rank,
                order: i + ++orderShift,
                e: selfEdge.e,
                label: selfEdge.label
              }, "_se");
            });
            delete node.selfEdges;
          });
        });
      }
      function positionSelfEdges(g) {
        _.forEach(g.nodes(), function(v) {
          var node = g.node(v);
          if (node.dummy === "selfedge") {
            var selfNode = g.node(node.e.v);
            var x = selfNode.x + selfNode.width / 2;
            var y = selfNode.y;
            var dx = node.x - x;
            var dy = selfNode.height / 2;
            g.setEdge(node.e, node.label);
            g.removeNode(v);
            node.label.points = [
              { x: x + 2 * dx / 3, y: y - dy },
              { x: x + 5 * dx / 6, y: y - dy },
              { x: x + dx, y },
              { x: x + 5 * dx / 6, y: y + dy },
              { x: x + 2 * dx / 3, y: y + dy }
            ];
            node.label.x = node.x;
            node.label.y = node.y;
          }
        });
      }
      function selectNumberAttrs(obj, attrs) {
        return _.mapValues(_.pick(obj, attrs), Number);
      }
      function canonicalize(attrs) {
        var newAttrs = {};
        _.forEach(attrs, function(v, k) {
          newAttrs[k.toLowerCase()] = v;
        });
        return newAttrs;
      }
    }
  });

  // node_modules/dagre/lib/debug.js
  var require_debug = __commonJS({
    "node_modules/dagre/lib/debug.js"(exports, module) {
      var _ = require_lodash2();
      var util = require_util();
      var Graph = require_graphlib2().Graph;
      module.exports = {
        debugOrdering
      };
      function debugOrdering(g) {
        var layerMatrix = util.buildLayerMatrix(g);
        var h = new Graph({ compound: true, multigraph: true }).setGraph({});
        _.forEach(g.nodes(), function(v) {
          h.setNode(v, { label: v });
          h.setParent(v, "layer" + g.node(v).rank);
        });
        _.forEach(g.edges(), function(e) {
          h.setEdge(e.v, e.w, {}, e.name);
        });
        _.forEach(layerMatrix, function(layer, i) {
          var layerV = "layer" + i;
          h.setNode(layerV, { rank: "same" });
          _.reduce(layer, function(u, v) {
            h.setEdge(u, v, { style: "invis" });
            return v;
          });
        });
        return h;
      }
    }
  });

  // node_modules/dagre/lib/version.js
  var require_version2 = __commonJS({
    "node_modules/dagre/lib/version.js"(exports, module) {
      module.exports = "0.8.5";
    }
  });

  // node_modules/dagre/index.js
  var require_dagre = __commonJS({
    "node_modules/dagre/index.js"(exports, module) {
      module.exports = {
        graphlib: require_graphlib2(),
        layout: require_layout(),
        debug: require_debug(),
        util: {
          time: require_util().time,
          notime: require_util().notime
        },
        version: require_version2()
      };
    }
  });

  // webview/tree/bridge.ts
  function asWindowWithAcquire(value) {
    return value;
  }
  function normalizePersistedState(candidate) {
    if (!candidate || typeof candidate !== "object") {
      return null;
    }
    const raw = candidate;
    return {
      selectedNodeId: String(raw.selectedNodeId || ""),
      focusMode: raw.focusMode === "upstream" || raw.focusMode === "downstream" ? raw.focusMode : "all",
      searchQuery: String(raw.searchQuery || ""),
      inspectorPinned: raw.inspectorPinned === true,
      zoomScale: Number.isFinite(Number(raw.zoomScale)) ? Math.max(0.2, Number(raw.zoomScale)) : 1,
      zoomX: Number.isFinite(Number(raw.zoomX)) ? Number(raw.zoomX) : 0,
      zoomY: Number.isFinite(Number(raw.zoomY)) ? Number(raw.zoomY) : 0
    };
  }
  function clampInt(value, minimum, maximum, fallback) {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) {
      return fallback;
    }
    return Math.min(maximum, Math.max(minimum, Math.round(parsed)));
  }
  function normalizeLayoutSettings(candidate) {
    const raw = candidate && typeof candidate === "object" ? candidate : {};
    return {
      frameworkNodeHorizontalGap: clampInt(raw.frameworkNodeHorizontalGap, 0, 40, 8),
      frameworkLevelVerticalGap: clampInt(raw.frameworkLevelVerticalGap, 48, 180, 80)
    };
  }
  function clampNumber(value, minimum, maximum, fallback) {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) {
      return fallback;
    }
    return Math.min(maximum, Math.max(minimum, parsed));
  }
  function normalizeViewSettings(candidate) {
    const raw = candidate && typeof candidate === "object" ? candidate : {};
    const zoomMinScale = clampNumber(raw.zoomMinScale, 0.2, 3, 0.68);
    const zoomMaxScale = clampNumber(raw.zoomMaxScale, zoomMinScale, 5, 1.55);
    return {
      zoomMinScale,
      zoomMaxScale,
      wheelSensitivity: clampNumber(raw.wheelSensitivity, 0.25, 3, 1),
      inspectorWidth: clampInt(raw.inspectorWidth, 240, 520, 338),
      inspectorRailWidth: clampInt(raw.inspectorRailWidth, 32, 72, 42)
    };
  }
  var WebviewBridge = class {
    constructor(hostWindow = window) {
      const host = asWindowWithAcquire(hostWindow);
      this.vscodeApi = typeof host.acquireVsCodeApi === "function" ? host.acquireVsCodeApi() : null;
    }
    readPersistedState() {
      if (!this.vscodeApi) {
        return null;
      }
      return normalizePersistedState(this.vscodeApi.getState());
    }
    persistState(state) {
      if (!this.vscodeApi) {
        return;
      }
      this.vscodeApi.setState(state);
    }
    openSource(file, line) {
      if (!this.vscodeApi) {
        return;
      }
      this.vscodeApi.postMessage({
        type: "shelf.openSource",
        file,
        line: Math.max(1, Math.floor(Number(line || 1)))
      });
    }
  };
  function readBootstrapElement() {
    const element = document.getElementById("shelf-tree-bootstrap");
    if (!(element instanceof HTMLScriptElement)) {
      throw new Error("Missing #shelf-tree-bootstrap payload.");
    }
    return element;
  }
  function readRuntimeBootstrap() {
    const element = readBootstrapElement();
    const raw = JSON.parse(element.textContent || "{}");
    const model = raw.model;
    if (!model || typeof model !== "object") {
      throw new Error("Invalid bootstrap payload: missing model.");
    }
    const kind = raw.kind === "evidence" ? "evidence" : "framework";
    return {
      version: Number(raw.version || 1),
      kind,
      layoutSettings: normalizeLayoutSettings(raw.layoutSettings),
      viewSettings: normalizeViewSettings(raw.viewSettings),
      model: {
        title: String(model.title || ""),
        description: String(model.description || ""),
        kind,
        nodes: Array.isArray(model.nodes) ? model.nodes : [],
        edges: Array.isArray(model.edges) ? model.edges : [],
        footText: typeof model.footText === "string" ? model.footText : "",
        layoutMode: model.layoutMode === "framework_columns" ? "framework_columns" : "global_levels",
        levelLabels: model.levelLabels && typeof model.levelLabels === "object" ? model.levelLabels : {},
        frameworkGroups: Array.isArray(model.frameworkGroups) ? model.frameworkGroups : [],
        relationCounts: model.relationCounts && typeof model.relationCounts === "object" ? model.relationCounts : {},
        objectIndex: model.objectIndex && typeof model.objectIndex === "object" ? model.objectIndex : {},
        validationSummary: model.validationSummary && typeof model.validationSummary === "object" ? model.validationSummary : {
          passed: false,
          ruleCount: 0,
          errorCount: 0,
          issues: [],
          issueCountByObject: {}
        }
      }
    };
  }

  // webview/tree/layout.ts
  var import_dagre = __toESM(require_dagre());
  var FRAMEWORK_PANEL_Y = 16;
  var FRAMEWORK_PANEL_HEADER_HEIGHT = 40;
  var FRAMEWORK_PANEL_MIN_WIDTH = 192;
  var FRAMEWORK_PANEL_LEFT_MARGIN = 18;
  var FRAMEWORK_PANEL_RIGHT_MARGIN = 14;
  var FRAMEWORK_PANEL_BOTTOM_MARGIN = 18;
  var FRAMEWORK_PANEL_GAP = 12;
  var FRAMEWORK_PANEL_PADDING_LEFT = 10;
  var FRAMEWORK_PANEL_PADDING_RIGHT = 10;
  var FRAMEWORK_LEVEL_GAP = 80;
  var FRAMEWORK_LEVEL_BAND_HEIGHT = 68;
  var FRAMEWORK_NODE_Y_OFFSET = FRAMEWORK_LEVEL_BAND_HEIGHT / 2;
  var FRAMEWORK_BOTTOM_PADDING = 16;
  var FRAMEWORK_TOP_PADDING = 8;
  var FRAMEWORK_ROW_NODE_GAP = 8;
  var FRAMEWORK_ROW_EDGE_PADDING = 2;
  var FRAMEWORK_LEVEL_GAP_MIN = 48;
  var FRAMEWORK_LEVEL_GAP_MAX = 180;
  var FRAMEWORK_ROW_NODE_GAP_MIN = 0;
  var FRAMEWORK_ROW_NODE_GAP_MAX = 40;
  function clampInt2(value, minimum, maximum, fallback) {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) {
      return fallback;
    }
    return Math.min(maximum, Math.max(minimum, Math.round(parsed)));
  }
  function normalizeLayoutSettings2(settings) {
    return {
      frameworkNodeHorizontalGap: clampInt2(
        settings?.frameworkNodeHorizontalGap,
        FRAMEWORK_ROW_NODE_GAP_MIN,
        FRAMEWORK_ROW_NODE_GAP_MAX,
        FRAMEWORK_ROW_NODE_GAP
      ),
      frameworkLevelVerticalGap: clampInt2(
        settings?.frameworkLevelVerticalGap,
        FRAMEWORK_LEVEL_GAP_MIN,
        FRAMEWORK_LEVEL_GAP_MAX,
        FRAMEWORK_LEVEL_GAP
      )
    };
  }
  function buildLayoutEdges(model, nodesById) {
    const edges = [];
    for (const edge of model.edges) {
      const from = nodesById.get(edge.from);
      const to = nodesById.get(edge.to);
      if (!from || !to) {
        continue;
      }
      edges.push({
        ...edge,
        fromX: from.x,
        fromY: from.y,
        toX: to.x,
        toY: to.y
      });
    }
    return edges;
  }
  function depthBands(model, nodes) {
    const buckets = /* @__PURE__ */ new Map();
    for (const node of nodes) {
      if (!buckets.has(node.depth)) {
        buckets.set(node.depth, []);
      }
      buckets.get(node.depth)?.push(node);
    }
    const bands = [];
    for (const [depth, items] of buckets.entries()) {
      let minX = Number.POSITIVE_INFINITY;
      let maxX = Number.NEGATIVE_INFINITY;
      let minY = Number.POSITIVE_INFINITY;
      let maxY = Number.NEGATIVE_INFINITY;
      for (const node of items) {
        minX = Math.min(minX, node.x - node.width / 2);
        maxX = Math.max(maxX, node.x + node.width / 2);
        minY = Math.min(minY, node.y - node.height / 2);
        maxY = Math.max(maxY, node.y + node.height / 2);
      }
      bands.push({
        depth,
        label: model.levelLabel(depth),
        x: minX - 28,
        y: minY - 26,
        width: Math.max(1, maxX - minX + 56),
        height: Math.max(1, maxY - minY + 52)
      });
    }
    return bands.sort((left, right) => left.depth - right.depth);
  }
  function nodeSortKey(node) {
    return [
      node.order === void 0 ? 1 : 0,
      node.order ?? 0,
      node.id
    ];
  }
  function refineLevelOrders(levels, levelOrders, nodeById, incoming, outgoing) {
    const sweep = (levelSequence, neighborsOf) => {
      const nodeSlot = /* @__PURE__ */ new Map();
      for (const level of levels) {
        const row = levelOrders.get(level) || [];
        row.forEach((nodeId, index) => {
          nodeSlot.set(nodeId, index);
        });
      }
      for (const level of levelSequence) {
        const row = [...levelOrders.get(level) || []];
        row.sort((leftId, rightId) => {
          const leftNode = nodeById.get(leftId);
          const rightNode = nodeById.get(rightId);
          if (!leftNode || !rightNode) {
            return leftId.localeCompare(rightId);
          }
          if (leftNode.order !== void 0 || rightNode.order !== void 0) {
            const leftKey = nodeSortKey(leftNode);
            const rightKey = nodeSortKey(rightNode);
            if (leftKey[0] !== rightKey[0]) {
              return leftKey[0] - rightKey[0];
            }
            if (leftKey[1] !== rightKey[1]) {
              return leftKey[1] - rightKey[1];
            }
            return leftKey[2].localeCompare(rightKey[2]);
          }
          const barycenterFor = (nodeId) => {
            const rankedNeighbors = (neighborsOf.get(nodeId) || []).map((neighborId) => nodeSlot.get(neighborId)).filter((slot) => slot !== void 0);
            if (!rankedNeighbors.length) {
              const index = row.indexOf(nodeId);
              return index >= 0 ? index : 0;
            }
            return rankedNeighbors.reduce((sum, slot) => sum + slot, 0) / rankedNeighbors.length;
          };
          const leftCenter = barycenterFor(leftId);
          const rightCenter = barycenterFor(rightId);
          if (leftCenter !== rightCenter) {
            return leftCenter - rightCenter;
          }
          return leftId.localeCompare(rightId);
        });
        levelOrders.set(level, row);
      }
    };
    if (levels.length <= 1) {
      return;
    }
    for (let iteration = 0; iteration < 6; iteration += 1) {
      sweep(levels.slice(1), incoming);
      sweep(levels.slice(0, -1).reverse(), outgoing);
    }
  }
  function computeFrameworkColumnsLayout(model, settings) {
    const groups = model.frameworkGroups.length ? model.frameworkGroups : [...new Set(model.nodes.map((node) => node.group).filter((value) => Boolean(value)))].sort((left, right) => left.localeCompare(right)).map((name, index) => ({
      name,
      order: index,
      localLevels: model.nodes.filter((node) => node.group === name).map((node) => node.depth).sort((left, right) => left - right),
      levelNodeCounts: Object.fromEntries(
        model.nodes.filter((node) => node.group === name).reduce((counts, node) => {
          counts.set(node.depth, (counts.get(node.depth) || 0) + 1);
          return counts;
        }, /* @__PURE__ */ new Map()).entries()
      )
    }));
    if (!groups.length) {
      return computeGlobalLayout(model);
    }
    const nodeById = new Map(model.nodes.map((node) => [node.id, node]));
    const nodeIdsByFramework = /* @__PURE__ */ new Map();
    for (const node of model.nodes) {
      const frameworkName = node.group || node.moduleName;
      if (!frameworkName) {
        continue;
      }
      const nodeIds = nodeIdsByFramework.get(frameworkName) || [];
      nodeIds.push(node.id);
      nodeIdsByFramework.set(frameworkName, nodeIds);
    }
    const incoming = /* @__PURE__ */ new Map();
    const outgoing = /* @__PURE__ */ new Map();
    for (const node of model.nodes) {
      incoming.set(node.id, []);
      outgoing.set(node.id, []);
    }
    for (const edge of model.edges) {
      incoming.get(edge.to)?.push(edge.from);
      outgoing.get(edge.from)?.push(edge.to);
    }
    const nodesById = /* @__PURE__ */ new Map();
    const groupFrames = [];
    const bands = [];
    let cursorX = FRAMEWORK_PANEL_LEFT_MARGIN;
    let maxHeight = FRAMEWORK_PANEL_Y + FRAMEWORK_PANEL_HEADER_HEIGHT + FRAMEWORK_BOTTOM_PADDING;
    for (const group of groups.sort((left, right) => {
      if (left.order !== right.order) {
        return left.order - right.order;
      }
      return left.name.localeCompare(right.name);
    })) {
      const groupNodeIds = nodeIdsByFramework.get(group.name) || [];
      if (!groupNodeIds.length) {
        continue;
      }
      const levelOrders = /* @__PURE__ */ new Map();
      const localLevels = [...new Set(group.localLevels)].sort((left, right) => left - right);
      for (const localLevel of localLevels) {
        const rowIds = groupNodeIds.filter((nodeId) => nodeById.get(nodeId)?.depth === localLevel).sort((leftId, rightId) => {
          const leftNode = nodeById.get(leftId);
          const rightNode = nodeById.get(rightId);
          if (!leftNode || !rightNode) {
            return leftId.localeCompare(rightId);
          }
          const leftKey = nodeSortKey(leftNode);
          const rightKey = nodeSortKey(rightNode);
          if (leftKey[0] !== rightKey[0]) {
            return leftKey[0] - rightKey[0];
          }
          if (leftKey[1] !== rightKey[1]) {
            return leftKey[1] - rightKey[1];
          }
          return leftKey[2].localeCompare(rightKey[2]);
        });
        if (rowIds.length) {
          levelOrders.set(localLevel, rowIds);
        }
      }
      if (!levelOrders.size) {
        continue;
      }
      const sortedLevels = [...levelOrders.keys()].sort((left, right) => left - right);
      refineLevelOrders(sortedLevels, levelOrders, nodeById, incoming, outgoing);
      const rowWidthByLevel = /* @__PURE__ */ new Map();
      for (const level of sortedLevels) {
        const rowIds = levelOrders.get(level) || [];
        const rowWidth = rowIds.reduce((sum, nodeId) => {
          const node = nodeById.get(nodeId);
          return sum + (node?.width || 0);
        }, 0) + Math.max(0, rowIds.length - 1) * settings.frameworkNodeHorizontalGap;
        rowWidthByLevel.set(level, rowWidth);
      }
      const widestRowWidth = Math.max(...sortedLevels.map((level) => rowWidthByLevel.get(level) || 0));
      const usableWidth = Math.max(
        FRAMEWORK_PANEL_MIN_WIDTH - FRAMEWORK_PANEL_PADDING_LEFT - FRAMEWORK_PANEL_PADDING_RIGHT,
        widestRowWidth + FRAMEWORK_ROW_EDGE_PADDING * 2
      );
      const groupWidth = Math.max(
        FRAMEWORK_PANEL_MIN_WIDTH,
        usableWidth + FRAMEWORK_PANEL_PADDING_LEFT + FRAMEWORK_PANEL_PADDING_RIGHT
      );
      const levelStackHeight = Math.max(0, sortedLevels.length - 1) * settings.frameworkLevelVerticalGap + FRAMEWORK_LEVEL_BAND_HEIGHT;
      const groupHeight = FRAMEWORK_PANEL_HEADER_HEIGHT + FRAMEWORK_TOP_PADDING + levelStackHeight + FRAMEWORK_BOTTOM_PADDING;
      groupFrames.push({
        name: group.name,
        x: cursorX,
        y: FRAMEWORK_PANEL_Y,
        width: groupWidth,
        height: groupHeight,
        localLevels: sortedLevels,
        order: group.order
      });
      for (const [levelIndex, level] of sortedLevels.entries()) {
        const rowIds = levelOrders.get(level) || [];
        const bandY = FRAMEWORK_PANEL_Y + FRAMEWORK_PANEL_HEADER_HEIGHT + FRAMEWORK_TOP_PADDING + levelIndex * settings.frameworkLevelVerticalGap;
        bands.push({
          depth: level,
          label: model.levelLabel(level),
          x: cursorX + 10,
          y: bandY,
          width: groupWidth - 20,
          height: FRAMEWORK_LEVEL_BAND_HEIGHT,
          groupName: group.name
        });
        const y = bandY + FRAMEWORK_NODE_Y_OFFSET;
        const rowWidth = rowWidthByLevel.get(level) || 0;
        const centeredStart = cursorX + (groupWidth - rowWidth) / 2;
        const minStart = cursorX + FRAMEWORK_PANEL_PADDING_LEFT;
        const maxStart = cursorX + groupWidth - FRAMEWORK_PANEL_PADDING_RIGHT - rowWidth;
        let rowCursorX = Math.min(
          Math.max(centeredStart, minStart),
          Math.max(minStart, maxStart)
        );
        rowIds.forEach((nodeId) => {
          const node = nodeById.get(nodeId);
          if (!node) {
            return;
          }
          const x = rowCursorX + node.width / 2;
          rowCursorX += node.width + settings.frameworkNodeHorizontalGap;
          nodesById.set(nodeId, {
            ...node,
            x,
            y
          });
        });
      }
      cursorX += groupWidth + FRAMEWORK_PANEL_GAP;
      maxHeight = Math.max(maxHeight, FRAMEWORK_PANEL_Y + groupHeight + FRAMEWORK_PANEL_BOTTOM_MARGIN);
    }
    const width = Math.max(1080, Math.round(cursorX - FRAMEWORK_PANEL_GAP + FRAMEWORK_PANEL_RIGHT_MARGIN));
    const height = Math.max(600, Math.round(maxHeight));
    const edges = buildLayoutEdges(model, nodesById);
    return {
      width,
      height,
      nodes: nodesById,
      edges,
      bands,
      groupFrames
    };
  }
  function computeGlobalLayout(model) {
    const graph = new import_dagre.default.graphlib.Graph({ multigraph: false, compound: false });
    graph.setGraph({
      rankdir: "LR",
      align: "UL",
      ranksep: 132,
      nodesep: 32,
      edgesep: 20,
      marginx: 84,
      marginy: 56
    });
    graph.setDefaultEdgeLabel(() => ({}));
    for (const node of model.nodes) {
      graph.setNode(node.id, {
        width: node.width,
        height: node.height,
        rank: node.depth
      });
    }
    for (const edge of model.edges) {
      graph.setEdge(edge.from, edge.to);
    }
    import_dagre.default.layout(graph);
    const nodesById = /* @__PURE__ */ new Map();
    for (const node of model.nodes) {
      const point = graph.node(node.id);
      const fallbackX = 180 + node.depth * 240;
      const fallbackY = 120 + nodesById.size * 90;
      nodesById.set(node.id, {
        ...node,
        x: Number(point?.x || fallbackX),
        y: Number(point?.y || fallbackY)
      });
    }
    const edges = buildLayoutEdges(model, nodesById);
    const graphLabel = graph.graph();
    const width = Math.max(980, Number(graphLabel.width || 0) + 180);
    const height = Math.max(620, Number(graphLabel.height || 0) + 160);
    return {
      width,
      height,
      nodes: nodesById,
      edges,
      bands: depthBands(model, nodesById.values()),
      groupFrames: []
    };
  }
  function computeTreeLayout(model, rawSettings) {
    const settings = normalizeLayoutSettings2(rawSettings);
    return model.layoutMode === "framework_columns" ? computeFrameworkColumnsLayout(model, settings) : computeGlobalLayout(model);
  }

  // webview/tree/model.ts
  var NODE_DIMENSIONS = {
    framework_root: { width: 142, height: 40 },
    framework_group: { width: 166, height: 44 }
  };
  function nodeDimensions(kind) {
    if (NODE_DIMENSIONS[kind]) {
      return NODE_DIMENSIONS[kind];
    }
    if (kind.includes("root")) {
      return { width: 142, height: 40 };
    }
    if (kind.includes("group")) {
      return { width: 166, height: 44 };
    }
    if (kind.includes("project") || kind.includes("evidence")) {
      return { width: 168, height: 44 };
    }
    return { width: 160, height: 42 };
  }
  function normalizeText(value) {
    return String(value ?? "").trim();
  }
  function normalizePositiveInt(value, fallback) {
    const parsed = Number(value);
    if (!Number.isFinite(parsed) || parsed <= 0) {
      return fallback;
    }
    return Math.max(1, Math.floor(parsed));
  }
  function normalizeHoverItems(candidate) {
    if (!Array.isArray(candidate)) {
      return [];
    }
    return candidate.map((entry) => {
      if (!entry || typeof entry !== "object") {
        return null;
      }
      const token = normalizeText(entry.token);
      const text = normalizeText(entry.text);
      if (!token && !text) {
        return null;
      }
      return {
        token,
        text: text || token
      };
    }).filter((entry) => Boolean(entry));
  }
  function normalizeNavigationTarget(candidate) {
    if (!candidate || typeof candidate !== "object") {
      return null;
    }
    const raw = candidate;
    const targetKind = normalizeText(raw.targetKind ?? raw.target_kind);
    const layer = normalizeText(raw.layer);
    const filePath = normalizeText(raw.filePath ?? raw.file_path);
    if (!targetKind || !layer || !filePath) {
      return null;
    }
    return {
      targetKind,
      layer,
      filePath,
      startLine: normalizePositiveInt(raw.startLine ?? raw.start_line, 1),
      endLine: normalizePositiveInt(raw.endLine ?? raw.end_line, normalizePositiveInt(raw.startLine ?? raw.start_line, 1)),
      symbol: normalizeText(raw.symbol),
      label: normalizeText(raw.label) || targetKind,
      isPrimary: raw.isPrimary === true || raw.is_primary === true,
      isEditable: raw.isEditable === true || raw.is_editable === true,
      isDeprecatedAlias: raw.isDeprecatedAlias === true || raw.is_deprecated_alias === true
    };
  }
  function normalizeNavigationTargets(candidate) {
    if (!Array.isArray(candidate)) {
      return [];
    }
    return candidate.map((entry) => normalizeNavigationTarget(entry)).filter((entry) => Boolean(entry));
  }
  function normalizeCorrespondenceObject(candidate) {
    if (!candidate || typeof candidate !== "object") {
      return null;
    }
    const raw = candidate;
    const objectId = normalizeText(raw.objectId ?? raw.object_id);
    if (!objectId) {
      return null;
    }
    const correspondenceAnchor = normalizeNavigationTarget(raw.correspondenceAnchor ?? raw.correspondence_anchor);
    const implementationAnchor = normalizeNavigationTarget(raw.implementationAnchor ?? raw.implementation_anchor);
    return {
      objectKind: normalizeText(raw.objectKind ?? raw.object_kind),
      objectId,
      ownerModuleId: normalizeText(raw.ownerModuleId ?? raw.owner_module_id),
      displayName: normalizeText(raw.displayName ?? raw.display_name) || objectId,
      materializationKind: normalizeText(raw.materializationKind ?? raw.materialization_kind),
      primaryNavTargetKind: normalizeText(raw.primaryNavTargetKind ?? raw.primary_nav_target_kind),
      primaryEditTargetKind: normalizeText(raw.primaryEditTargetKind ?? raw.primary_edit_target_kind),
      navigationTargets: normalizeNavigationTargets(raw.navigationTargets ?? raw.navigation_targets),
      ...correspondenceAnchor ? { correspondenceAnchor } : {},
      ...implementationAnchor ? { implementationAnchor } : {}
    };
  }
  function normalizeValidationSummary(candidate) {
    if (!candidate || typeof candidate !== "object") {
      return {
        passed: false,
        ruleCount: 0,
        errorCount: 0,
        issues: [],
        issueCountByObject: {}
      };
    }
    const raw = candidate;
    const issues = Array.isArray(raw.issues) ? raw.issues.filter((entry) => entry && typeof entry === "object").map((entry) => {
      const issue = entry;
      const objectIds = issue.objectIds ?? issue.object_ids;
      return {
        issueKind: normalizeText(issue.issueKind ?? issue.issue_kind),
        level: normalizeText(issue.level) || "error",
        reason: normalizeText(issue.reason),
        objectIds: Array.isArray(objectIds) ? objectIds.map((value) => normalizeText(value)).filter(Boolean) : [],
        primaryObjectId: normalizeText(issue.primaryObjectId ?? issue.primary_object_id)
      };
    }) : [];
    const issueCountByObject = {};
    const rawCounts = raw.issueCountByObject ?? raw.issue_count_by_object;
    if (rawCounts && typeof rawCounts === "object") {
      for (const [objectId, count] of Object.entries(rawCounts)) {
        issueCountByObject[normalizeText(objectId)] = Math.max(0, Math.floor(Number(count) || 0));
      }
    }
    return {
      passed: raw.passed === true,
      ruleCount: Math.max(0, Math.floor(Number(raw.ruleCount ?? raw.rule_count) || 0)),
      errorCount: Math.max(0, Math.floor(Number(raw.errorCount ?? raw.error_count) || issues.length)),
      issues,
      issueCountByObject
    };
  }
  function visualLength(value) {
    let length = 0;
    for (const char of value) {
      length += /[\u1100-\u11ff\u2e80-\u9fff\uf900-\ufaff]/.test(char) ? 1.9 : 1;
    }
    return length;
  }
  function moduleDimensionsFromText(compactId) {
    const width = Math.min(118, Math.max(72, Math.round(28 + visualLength(compactId) * 3.85)));
    const height = 38;
    return { width, height };
  }
  function normalizeNode(node) {
    if (!node || typeof node !== "object") {
      return null;
    }
    const candidate = node;
    const id2 = normalizeText(candidate.id);
    if (!id2) {
      return null;
    }
    const kind = normalizeText(candidate.kind) || "node";
    const group = normalizeText(candidate.group);
    const title = normalizeText(candidate.title);
    const detail = normalizeText(candidate.detail);
    const label = normalizeText(candidate.label) || id2;
    const moduleName = normalizeText(candidate.moduleName);
    const moduleRef = normalizeText(candidate.moduleRef);
    const compactModuleId = moduleName && moduleRef ? `${moduleName}.${moduleRef}` : label;
    const size = kind.includes("module") ? moduleDimensionsFromText(compactModuleId) : nodeDimensions(kind);
    const hoverKicker = normalizeText(candidate.hoverKicker);
    const order = Number.isFinite(Number(candidate.order)) ? Math.max(0, Number(candidate.order)) : null;
    const sourceLine = Number.isFinite(Number(candidate.sourceLine)) ? normalizePositiveInt(candidate.sourceLine, 1) : null;
    const docLine = Number.isFinite(Number(candidate.docLine)) ? normalizePositiveInt(candidate.docLine, 1) : null;
    const defaultTarget = normalizeNavigationTarget(candidate.defaultTarget);
    const editTarget = normalizeNavigationTarget(candidate.editTarget);
    const correspondenceAnchor = normalizeNavigationTarget(candidate.correspondenceAnchor);
    const implementationAnchor = normalizeNavigationTarget(candidate.implementationAnchor);
    const secondaryTargets = Array.isArray(candidate.secondaryTargets) ? normalizeNavigationTargets(candidate.secondaryTargets) : [];
    const relatedObjectIds = Array.isArray(candidate.relatedObjectIds) ? candidate.relatedObjectIds.map((value) => normalizeText(value)).filter(Boolean) : [];
    return {
      id: id2,
      label,
      detail,
      file: normalizeText(candidate.file),
      line: normalizePositiveInt(candidate.line, 1),
      depth: Math.max(0, Number(candidate.depth || 0)),
      kind,
      ...group ? { group } : {},
      ...order !== null ? { order } : {},
      ...title ? { title } : {},
      ...moduleName ? { moduleName } : {},
      ...moduleRef ? { moduleRef } : {},
      ...sourceLine !== null ? { sourceLine } : {},
      ...docLine !== null ? { docLine } : {},
      ...hoverKicker ? { hoverKicker } : {},
      capabilityItems: normalizeHoverItems(candidate.capabilityItems),
      baseItems: normalizeHoverItems(candidate.baseItems),
      ...normalizeText(candidate.objectId) ? { objectId: normalizeText(candidate.objectId) } : {},
      ...defaultTarget ? { defaultTarget } : {},
      ...editTarget ? { editTarget } : {},
      ...correspondenceAnchor ? { correspondenceAnchor } : {},
      ...implementationAnchor ? { implementationAnchor } : {},
      ...secondaryTargets.length ? { secondaryTargets } : {},
      ...relatedObjectIds.length ? { relatedObjectIds } : {},
      width: size.width,
      height: size.height
    };
  }
  function normalizeEdge(edge) {
    if (!edge || typeof edge !== "object") {
      return null;
    }
    const candidate = edge;
    const from = normalizeText(candidate.from);
    const to = normalizeText(candidate.to);
    if (!from || !to) {
      return null;
    }
    const rules = normalizeText(candidate.rules);
    const terms = normalizeText(candidate.terms);
    const file = normalizeText(candidate.file);
    const line = Number.isFinite(Number(candidate.line)) ? normalizePositiveInt(candidate.line, 1) : null;
    return {
      id: normalizeText(candidate.id) || `${from}->${to}`,
      from,
      to,
      relation: normalizeText(candidate.relation) || "tree_child",
      ...rules ? { rules } : {},
      ...terms ? { terms } : {},
      ...file ? { file } : {},
      ...line !== null ? { line } : {}
    };
  }
  function normalizeLevelLabels(candidate) {
    const labels = /* @__PURE__ */ new Map();
    if (!candidate || typeof candidate !== "object") {
      return labels;
    }
    for (const [rawKey, rawValue] of Object.entries(candidate)) {
      const level = Number(rawKey);
      if (!Number.isFinite(level)) {
        continue;
      }
      const label = normalizeText(rawValue);
      if (!label) {
        continue;
      }
      labels.set(level, label);
    }
    return labels;
  }
  function normalizeFrameworkGroup(candidate) {
    if (!candidate || typeof candidate !== "object") {
      return null;
    }
    const raw = candidate;
    const name = normalizeText(raw.name);
    if (!name) {
      return null;
    }
    const localLevels = Array.isArray(raw.localLevels) ? raw.localLevels.map((value) => Number(value)).filter((value) => Number.isFinite(value)).map((value) => Math.max(0, Math.floor(value))).sort((left, right) => left - right) : [];
    const levelNodeCounts = /* @__PURE__ */ new Map();
    if (raw.levelNodeCounts && typeof raw.levelNodeCounts === "object") {
      for (const [rawKey, rawValue] of Object.entries(raw.levelNodeCounts)) {
        const level = Number(rawKey);
        const count = Number(rawValue);
        if (!Number.isFinite(level) || !Number.isFinite(count)) {
          continue;
        }
        levelNodeCounts.set(Math.max(0, Math.floor(level)), Math.max(0, Math.floor(count)));
      }
    }
    return {
      name,
      order: Number.isFinite(Number(raw.order)) ? Math.max(0, Number(raw.order)) : 0,
      localLevels,
      levelNodeCounts: Object.fromEntries(levelNodeCounts.entries())
    };
  }
  var TreeGraphModel = class {
    constructor(rawModel) {
      this.title = normalizeText(rawModel.title) || "Shelf Tree";
      this.description = normalizeText(rawModel.description);
      this.footText = normalizeText(rawModel.footText);
      this.layoutMode = rawModel.layoutMode === "framework_columns" ? "framework_columns" : "global_levels";
      const nodeById = /* @__PURE__ */ new Map();
      const nodes = [];
      for (const candidate of rawModel.nodes || []) {
        const node = normalizeNode(candidate);
        if (!node || nodeById.has(node.id)) {
          continue;
        }
        nodeById.set(node.id, node);
        nodes.push(node);
      }
      const edgeById = /* @__PURE__ */ new Map();
      const edges = [];
      for (const candidate of rawModel.edges || []) {
        const edge = normalizeEdge(candidate);
        if (!edge) {
          continue;
        }
        if (!nodeById.has(edge.from) || !nodeById.has(edge.to)) {
          continue;
        }
        if (edgeById.has(edge.id)) {
          continue;
        }
        edgeById.set(edge.id, edge);
        edges.push(edge);
      }
      this.nodes = nodes;
      this.edges = edges;
      this.nodeById = nodeById;
      this.edgeById = edgeById;
      this.outgoingById = /* @__PURE__ */ new Map();
      this.incomingById = /* @__PURE__ */ new Map();
      this.outgoingEdgesById = /* @__PURE__ */ new Map();
      this.incomingEdgesById = /* @__PURE__ */ new Map();
      this.levelLabels = normalizeLevelLabels(rawModel.levelLabels);
      this.frameworkGroups = (rawModel.frameworkGroups || []).map((candidate) => normalizeFrameworkGroup(candidate)).filter((entry) => Boolean(entry)).sort((left, right) => {
        if (left.order !== right.order) {
          return left.order - right.order;
        }
        return left.name.localeCompare(right.name);
      });
      this.frameworkGroupByName = new Map(this.frameworkGroups.map((group) => [group.name, group]));
      this.relationCounts = /* @__PURE__ */ new Map();
      this.objectIndex = /* @__PURE__ */ new Map();
      this.validationSummary = normalizeValidationSummary(rawModel.validationSummary);
      for (const node of nodes) {
        this.outgoingById.set(node.id, /* @__PURE__ */ new Set());
        this.incomingById.set(node.id, /* @__PURE__ */ new Set());
        this.outgoingEdgesById.set(node.id, []);
        this.incomingEdgesById.set(node.id, []);
      }
      for (const edge of edges) {
        this.outgoingById.get(edge.from)?.add(edge.to);
        this.incomingById.get(edge.to)?.add(edge.from);
        this.outgoingEdgesById.get(edge.from)?.push(edge);
        this.incomingEdgesById.get(edge.to)?.push(edge);
        this.relationCounts.set(edge.relation, (this.relationCounts.get(edge.relation) || 0) + 1);
      }
      if (rawModel.relationCounts && typeof rawModel.relationCounts === "object") {
        for (const [relation, count] of Object.entries(rawModel.relationCounts)) {
          const normalizedCount = Number(count);
          if (!Number.isFinite(normalizedCount)) {
            continue;
          }
          this.relationCounts.set(relation, Math.max(0, Math.floor(normalizedCount)));
        }
      }
      if (rawModel.objectIndex && typeof rawModel.objectIndex === "object") {
        for (const [objectId, candidate] of Object.entries(rawModel.objectIndex)) {
          const objectValue = normalizeCorrespondenceObject(candidate);
          if (!objectValue || objectValue.objectId !== objectId) {
            continue;
          }
          this.objectIndex.set(objectId, objectValue);
        }
      }
    }
    hasNode(nodeId) {
      return this.nodeById.has(nodeId);
    }
    node(nodeId) {
      return this.nodeById.get(nodeId) || null;
    }
    edge(edgeId) {
      return this.edgeById.get(edgeId) || null;
    }
    object(objectId) {
      return this.objectIndex.get(objectId) || null;
    }
    outgoingEdges(nodeId) {
      return [...this.outgoingEdgesById.get(nodeId) || []];
    }
    incomingEdges(nodeId) {
      return [...this.incomingEdgesById.get(nodeId) || []];
    }
    levelLabel(level) {
      return this.levelLabels.get(level) || `L${level}`;
    }
    matchNodeIdsByQuery(rawQuery) {
      const query = normalizeText(rawQuery).toLowerCase();
      if (!query) {
        return new Set(this.nodeById.keys());
      }
      const matched = /* @__PURE__ */ new Set();
      for (const node of this.nodes) {
        const haystack = [
          node.id,
          node.label,
          node.detail,
          node.group || "",
          node.title || "",
          node.moduleName || "",
          node.moduleRef || ""
        ].join(" ").toLowerCase();
        if (haystack.includes(query)) {
          matched.add(node.id);
        }
      }
      return matched;
    }
    collectReachable(nodeId, direction) {
      if (!this.nodeById.has(nodeId)) {
        return /* @__PURE__ */ new Set();
      }
      const visited = /* @__PURE__ */ new Set();
      const queue = [nodeId];
      while (queue.length) {
        const current = queue.shift() || "";
        if (!current || visited.has(current)) {
          continue;
        }
        visited.add(current);
        const neighbors = direction === "incoming" ? this.incomingById.get(current) : this.outgoingById.get(current);
        for (const neighbor of neighbors || []) {
          if (!visited.has(neighbor)) {
            queue.push(neighbor);
          }
        }
      }
      return visited;
    }
    computeFilterResult(params) {
      const queryMatches = this.matchNodeIdsByQuery(params.query);
      const selectedNodeId = normalizeText(params.selectedNodeId);
      let focusSet = new Set(this.nodeById.keys());
      if (selectedNodeId && params.focusMode !== "all" && this.nodeById.has(selectedNodeId)) {
        focusSet = this.collectReachable(
          selectedNodeId,
          params.focusMode === "upstream" ? "incoming" : "outgoing"
        );
        focusSet.add(selectedNodeId);
      }
      const visibleNodeIds = /* @__PURE__ */ new Set();
      for (const nodeId of focusSet) {
        if (queryMatches.has(nodeId)) {
          visibleNodeIds.add(nodeId);
        }
      }
      if (selectedNodeId && this.nodeById.has(selectedNodeId)) {
        visibleNodeIds.add(selectedNodeId);
      }
      const visibleEdgeIds = /* @__PURE__ */ new Set();
      for (const edge of this.edges) {
        if (visibleNodeIds.has(edge.from) && visibleNodeIds.has(edge.to)) {
          visibleEdgeIds.add(edge.id);
        }
      }
      return {
        visibleNodeIds,
        visibleEdgeIds
      };
    }
    adjacentNodeIds(nodeId) {
      const adjacent = /* @__PURE__ */ new Set();
      for (const upstream of this.incomingById.get(nodeId) || []) {
        adjacent.add(upstream);
      }
      for (const downstream of this.outgoingById.get(nodeId) || []) {
        adjacent.add(downstream);
      }
      return adjacent;
    }
  };

  // node_modules/d3-selection/src/namespaces.js
  var xhtml = "http://www.w3.org/1999/xhtml";
  var namespaces_default = {
    svg: "http://www.w3.org/2000/svg",
    xhtml,
    xlink: "http://www.w3.org/1999/xlink",
    xml: "http://www.w3.org/XML/1998/namespace",
    xmlns: "http://www.w3.org/2000/xmlns/"
  };

  // node_modules/d3-selection/src/namespace.js
  function namespace_default(name) {
    var prefix = name += "", i = prefix.indexOf(":");
    if (i >= 0 && (prefix = name.slice(0, i)) !== "xmlns") name = name.slice(i + 1);
    return namespaces_default.hasOwnProperty(prefix) ? { space: namespaces_default[prefix], local: name } : name;
  }

  // node_modules/d3-selection/src/creator.js
  function creatorInherit(name) {
    return function() {
      var document2 = this.ownerDocument, uri = this.namespaceURI;
      return uri === xhtml && document2.documentElement.namespaceURI === xhtml ? document2.createElement(name) : document2.createElementNS(uri, name);
    };
  }
  function creatorFixed(fullname) {
    return function() {
      return this.ownerDocument.createElementNS(fullname.space, fullname.local);
    };
  }
  function creator_default(name) {
    var fullname = namespace_default(name);
    return (fullname.local ? creatorFixed : creatorInherit)(fullname);
  }

  // node_modules/d3-selection/src/selector.js
  function none() {
  }
  function selector_default(selector) {
    return selector == null ? none : function() {
      return this.querySelector(selector);
    };
  }

  // node_modules/d3-selection/src/selection/select.js
  function select_default(select) {
    if (typeof select !== "function") select = selector_default(select);
    for (var groups = this._groups, m = groups.length, subgroups = new Array(m), j = 0; j < m; ++j) {
      for (var group = groups[j], n = group.length, subgroup = subgroups[j] = new Array(n), node, subnode, i = 0; i < n; ++i) {
        if ((node = group[i]) && (subnode = select.call(node, node.__data__, i, group))) {
          if ("__data__" in node) subnode.__data__ = node.__data__;
          subgroup[i] = subnode;
        }
      }
    }
    return new Selection(subgroups, this._parents);
  }

  // node_modules/d3-selection/src/array.js
  function array(x) {
    return x == null ? [] : Array.isArray(x) ? x : Array.from(x);
  }

  // node_modules/d3-selection/src/selectorAll.js
  function empty() {
    return [];
  }
  function selectorAll_default(selector) {
    return selector == null ? empty : function() {
      return this.querySelectorAll(selector);
    };
  }

  // node_modules/d3-selection/src/selection/selectAll.js
  function arrayAll(select) {
    return function() {
      return array(select.apply(this, arguments));
    };
  }
  function selectAll_default(select) {
    if (typeof select === "function") select = arrayAll(select);
    else select = selectorAll_default(select);
    for (var groups = this._groups, m = groups.length, subgroups = [], parents = [], j = 0; j < m; ++j) {
      for (var group = groups[j], n = group.length, node, i = 0; i < n; ++i) {
        if (node = group[i]) {
          subgroups.push(select.call(node, node.__data__, i, group));
          parents.push(node);
        }
      }
    }
    return new Selection(subgroups, parents);
  }

  // node_modules/d3-selection/src/matcher.js
  function matcher_default(selector) {
    return function() {
      return this.matches(selector);
    };
  }
  function childMatcher(selector) {
    return function(node) {
      return node.matches(selector);
    };
  }

  // node_modules/d3-selection/src/selection/selectChild.js
  var find = Array.prototype.find;
  function childFind(match) {
    return function() {
      return find.call(this.children, match);
    };
  }
  function childFirst() {
    return this.firstElementChild;
  }
  function selectChild_default(match) {
    return this.select(match == null ? childFirst : childFind(typeof match === "function" ? match : childMatcher(match)));
  }

  // node_modules/d3-selection/src/selection/selectChildren.js
  var filter = Array.prototype.filter;
  function children() {
    return Array.from(this.children);
  }
  function childrenFilter(match) {
    return function() {
      return filter.call(this.children, match);
    };
  }
  function selectChildren_default(match) {
    return this.selectAll(match == null ? children : childrenFilter(typeof match === "function" ? match : childMatcher(match)));
  }

  // node_modules/d3-selection/src/selection/filter.js
  function filter_default(match) {
    if (typeof match !== "function") match = matcher_default(match);
    for (var groups = this._groups, m = groups.length, subgroups = new Array(m), j = 0; j < m; ++j) {
      for (var group = groups[j], n = group.length, subgroup = subgroups[j] = [], node, i = 0; i < n; ++i) {
        if ((node = group[i]) && match.call(node, node.__data__, i, group)) {
          subgroup.push(node);
        }
      }
    }
    return new Selection(subgroups, this._parents);
  }

  // node_modules/d3-selection/src/selection/sparse.js
  function sparse_default(update) {
    return new Array(update.length);
  }

  // node_modules/d3-selection/src/selection/enter.js
  function enter_default() {
    return new Selection(this._enter || this._groups.map(sparse_default), this._parents);
  }
  function EnterNode(parent, datum2) {
    this.ownerDocument = parent.ownerDocument;
    this.namespaceURI = parent.namespaceURI;
    this._next = null;
    this._parent = parent;
    this.__data__ = datum2;
  }
  EnterNode.prototype = {
    constructor: EnterNode,
    appendChild: function(child) {
      return this._parent.insertBefore(child, this._next);
    },
    insertBefore: function(child, next) {
      return this._parent.insertBefore(child, next);
    },
    querySelector: function(selector) {
      return this._parent.querySelector(selector);
    },
    querySelectorAll: function(selector) {
      return this._parent.querySelectorAll(selector);
    }
  };

  // node_modules/d3-selection/src/constant.js
  function constant_default(x) {
    return function() {
      return x;
    };
  }

  // node_modules/d3-selection/src/selection/data.js
  function bindIndex(parent, group, enter, update, exit, data) {
    var i = 0, node, groupLength = group.length, dataLength = data.length;
    for (; i < dataLength; ++i) {
      if (node = group[i]) {
        node.__data__ = data[i];
        update[i] = node;
      } else {
        enter[i] = new EnterNode(parent, data[i]);
      }
    }
    for (; i < groupLength; ++i) {
      if (node = group[i]) {
        exit[i] = node;
      }
    }
  }
  function bindKey(parent, group, enter, update, exit, data, key) {
    var i, node, nodeByKeyValue = /* @__PURE__ */ new Map(), groupLength = group.length, dataLength = data.length, keyValues = new Array(groupLength), keyValue;
    for (i = 0; i < groupLength; ++i) {
      if (node = group[i]) {
        keyValues[i] = keyValue = key.call(node, node.__data__, i, group) + "";
        if (nodeByKeyValue.has(keyValue)) {
          exit[i] = node;
        } else {
          nodeByKeyValue.set(keyValue, node);
        }
      }
    }
    for (i = 0; i < dataLength; ++i) {
      keyValue = key.call(parent, data[i], i, data) + "";
      if (node = nodeByKeyValue.get(keyValue)) {
        update[i] = node;
        node.__data__ = data[i];
        nodeByKeyValue.delete(keyValue);
      } else {
        enter[i] = new EnterNode(parent, data[i]);
      }
    }
    for (i = 0; i < groupLength; ++i) {
      if ((node = group[i]) && nodeByKeyValue.get(keyValues[i]) === node) {
        exit[i] = node;
      }
    }
  }
  function datum(node) {
    return node.__data__;
  }
  function data_default(value, key) {
    if (!arguments.length) return Array.from(this, datum);
    var bind = key ? bindKey : bindIndex, parents = this._parents, groups = this._groups;
    if (typeof value !== "function") value = constant_default(value);
    for (var m = groups.length, update = new Array(m), enter = new Array(m), exit = new Array(m), j = 0; j < m; ++j) {
      var parent = parents[j], group = groups[j], groupLength = group.length, data = arraylike(value.call(parent, parent && parent.__data__, j, parents)), dataLength = data.length, enterGroup = enter[j] = new Array(dataLength), updateGroup = update[j] = new Array(dataLength), exitGroup = exit[j] = new Array(groupLength);
      bind(parent, group, enterGroup, updateGroup, exitGroup, data, key);
      for (var i0 = 0, i1 = 0, previous, next; i0 < dataLength; ++i0) {
        if (previous = enterGroup[i0]) {
          if (i0 >= i1) i1 = i0 + 1;
          while (!(next = updateGroup[i1]) && ++i1 < dataLength) ;
          previous._next = next || null;
        }
      }
    }
    update = new Selection(update, parents);
    update._enter = enter;
    update._exit = exit;
    return update;
  }
  function arraylike(data) {
    return typeof data === "object" && "length" in data ? data : Array.from(data);
  }

  // node_modules/d3-selection/src/selection/exit.js
  function exit_default() {
    return new Selection(this._exit || this._groups.map(sparse_default), this._parents);
  }

  // node_modules/d3-selection/src/selection/join.js
  function join_default(onenter, onupdate, onexit) {
    var enter = this.enter(), update = this, exit = this.exit();
    if (typeof onenter === "function") {
      enter = onenter(enter);
      if (enter) enter = enter.selection();
    } else {
      enter = enter.append(onenter + "");
    }
    if (onupdate != null) {
      update = onupdate(update);
      if (update) update = update.selection();
    }
    if (onexit == null) exit.remove();
    else onexit(exit);
    return enter && update ? enter.merge(update).order() : update;
  }

  // node_modules/d3-selection/src/selection/merge.js
  function merge_default(context) {
    var selection2 = context.selection ? context.selection() : context;
    for (var groups0 = this._groups, groups1 = selection2._groups, m0 = groups0.length, m1 = groups1.length, m = Math.min(m0, m1), merges = new Array(m0), j = 0; j < m; ++j) {
      for (var group0 = groups0[j], group1 = groups1[j], n = group0.length, merge = merges[j] = new Array(n), node, i = 0; i < n; ++i) {
        if (node = group0[i] || group1[i]) {
          merge[i] = node;
        }
      }
    }
    for (; j < m0; ++j) {
      merges[j] = groups0[j];
    }
    return new Selection(merges, this._parents);
  }

  // node_modules/d3-selection/src/selection/order.js
  function order_default() {
    for (var groups = this._groups, j = -1, m = groups.length; ++j < m; ) {
      for (var group = groups[j], i = group.length - 1, next = group[i], node; --i >= 0; ) {
        if (node = group[i]) {
          if (next && node.compareDocumentPosition(next) ^ 4) next.parentNode.insertBefore(node, next);
          next = node;
        }
      }
    }
    return this;
  }

  // node_modules/d3-selection/src/selection/sort.js
  function sort_default(compare) {
    if (!compare) compare = ascending;
    function compareNode(a, b) {
      return a && b ? compare(a.__data__, b.__data__) : !a - !b;
    }
    for (var groups = this._groups, m = groups.length, sortgroups = new Array(m), j = 0; j < m; ++j) {
      for (var group = groups[j], n = group.length, sortgroup = sortgroups[j] = new Array(n), node, i = 0; i < n; ++i) {
        if (node = group[i]) {
          sortgroup[i] = node;
        }
      }
      sortgroup.sort(compareNode);
    }
    return new Selection(sortgroups, this._parents).order();
  }
  function ascending(a, b) {
    return a < b ? -1 : a > b ? 1 : a >= b ? 0 : NaN;
  }

  // node_modules/d3-selection/src/selection/call.js
  function call_default() {
    var callback = arguments[0];
    arguments[0] = this;
    callback.apply(null, arguments);
    return this;
  }

  // node_modules/d3-selection/src/selection/nodes.js
  function nodes_default() {
    return Array.from(this);
  }

  // node_modules/d3-selection/src/selection/node.js
  function node_default() {
    for (var groups = this._groups, j = 0, m = groups.length; j < m; ++j) {
      for (var group = groups[j], i = 0, n = group.length; i < n; ++i) {
        var node = group[i];
        if (node) return node;
      }
    }
    return null;
  }

  // node_modules/d3-selection/src/selection/size.js
  function size_default() {
    let size = 0;
    for (const node of this) ++size;
    return size;
  }

  // node_modules/d3-selection/src/selection/empty.js
  function empty_default() {
    return !this.node();
  }

  // node_modules/d3-selection/src/selection/each.js
  function each_default(callback) {
    for (var groups = this._groups, j = 0, m = groups.length; j < m; ++j) {
      for (var group = groups[j], i = 0, n = group.length, node; i < n; ++i) {
        if (node = group[i]) callback.call(node, node.__data__, i, group);
      }
    }
    return this;
  }

  // node_modules/d3-selection/src/selection/attr.js
  function attrRemove(name) {
    return function() {
      this.removeAttribute(name);
    };
  }
  function attrRemoveNS(fullname) {
    return function() {
      this.removeAttributeNS(fullname.space, fullname.local);
    };
  }
  function attrConstant(name, value) {
    return function() {
      this.setAttribute(name, value);
    };
  }
  function attrConstantNS(fullname, value) {
    return function() {
      this.setAttributeNS(fullname.space, fullname.local, value);
    };
  }
  function attrFunction(name, value) {
    return function() {
      var v = value.apply(this, arguments);
      if (v == null) this.removeAttribute(name);
      else this.setAttribute(name, v);
    };
  }
  function attrFunctionNS(fullname, value) {
    return function() {
      var v = value.apply(this, arguments);
      if (v == null) this.removeAttributeNS(fullname.space, fullname.local);
      else this.setAttributeNS(fullname.space, fullname.local, v);
    };
  }
  function attr_default(name, value) {
    var fullname = namespace_default(name);
    if (arguments.length < 2) {
      var node = this.node();
      return fullname.local ? node.getAttributeNS(fullname.space, fullname.local) : node.getAttribute(fullname);
    }
    return this.each((value == null ? fullname.local ? attrRemoveNS : attrRemove : typeof value === "function" ? fullname.local ? attrFunctionNS : attrFunction : fullname.local ? attrConstantNS : attrConstant)(fullname, value));
  }

  // node_modules/d3-selection/src/window.js
  function window_default(node) {
    return node.ownerDocument && node.ownerDocument.defaultView || node.document && node || node.defaultView;
  }

  // node_modules/d3-selection/src/selection/style.js
  function styleRemove(name) {
    return function() {
      this.style.removeProperty(name);
    };
  }
  function styleConstant(name, value, priority) {
    return function() {
      this.style.setProperty(name, value, priority);
    };
  }
  function styleFunction(name, value, priority) {
    return function() {
      var v = value.apply(this, arguments);
      if (v == null) this.style.removeProperty(name);
      else this.style.setProperty(name, v, priority);
    };
  }
  function style_default(name, value, priority) {
    return arguments.length > 1 ? this.each((value == null ? styleRemove : typeof value === "function" ? styleFunction : styleConstant)(name, value, priority == null ? "" : priority)) : styleValue(this.node(), name);
  }
  function styleValue(node, name) {
    return node.style.getPropertyValue(name) || window_default(node).getComputedStyle(node, null).getPropertyValue(name);
  }

  // node_modules/d3-selection/src/selection/property.js
  function propertyRemove(name) {
    return function() {
      delete this[name];
    };
  }
  function propertyConstant(name, value) {
    return function() {
      this[name] = value;
    };
  }
  function propertyFunction(name, value) {
    return function() {
      var v = value.apply(this, arguments);
      if (v == null) delete this[name];
      else this[name] = v;
    };
  }
  function property_default(name, value) {
    return arguments.length > 1 ? this.each((value == null ? propertyRemove : typeof value === "function" ? propertyFunction : propertyConstant)(name, value)) : this.node()[name];
  }

  // node_modules/d3-selection/src/selection/classed.js
  function classArray(string) {
    return string.trim().split(/^|\s+/);
  }
  function classList(node) {
    return node.classList || new ClassList(node);
  }
  function ClassList(node) {
    this._node = node;
    this._names = classArray(node.getAttribute("class") || "");
  }
  ClassList.prototype = {
    add: function(name) {
      var i = this._names.indexOf(name);
      if (i < 0) {
        this._names.push(name);
        this._node.setAttribute("class", this._names.join(" "));
      }
    },
    remove: function(name) {
      var i = this._names.indexOf(name);
      if (i >= 0) {
        this._names.splice(i, 1);
        this._node.setAttribute("class", this._names.join(" "));
      }
    },
    contains: function(name) {
      return this._names.indexOf(name) >= 0;
    }
  };
  function classedAdd(node, names) {
    var list = classList(node), i = -1, n = names.length;
    while (++i < n) list.add(names[i]);
  }
  function classedRemove(node, names) {
    var list = classList(node), i = -1, n = names.length;
    while (++i < n) list.remove(names[i]);
  }
  function classedTrue(names) {
    return function() {
      classedAdd(this, names);
    };
  }
  function classedFalse(names) {
    return function() {
      classedRemove(this, names);
    };
  }
  function classedFunction(names, value) {
    return function() {
      (value.apply(this, arguments) ? classedAdd : classedRemove)(this, names);
    };
  }
  function classed_default(name, value) {
    var names = classArray(name + "");
    if (arguments.length < 2) {
      var list = classList(this.node()), i = -1, n = names.length;
      while (++i < n) if (!list.contains(names[i])) return false;
      return true;
    }
    return this.each((typeof value === "function" ? classedFunction : value ? classedTrue : classedFalse)(names, value));
  }

  // node_modules/d3-selection/src/selection/text.js
  function textRemove() {
    this.textContent = "";
  }
  function textConstant(value) {
    return function() {
      this.textContent = value;
    };
  }
  function textFunction(value) {
    return function() {
      var v = value.apply(this, arguments);
      this.textContent = v == null ? "" : v;
    };
  }
  function text_default(value) {
    return arguments.length ? this.each(value == null ? textRemove : (typeof value === "function" ? textFunction : textConstant)(value)) : this.node().textContent;
  }

  // node_modules/d3-selection/src/selection/html.js
  function htmlRemove() {
    this.innerHTML = "";
  }
  function htmlConstant(value) {
    return function() {
      this.innerHTML = value;
    };
  }
  function htmlFunction(value) {
    return function() {
      var v = value.apply(this, arguments);
      this.innerHTML = v == null ? "" : v;
    };
  }
  function html_default(value) {
    return arguments.length ? this.each(value == null ? htmlRemove : (typeof value === "function" ? htmlFunction : htmlConstant)(value)) : this.node().innerHTML;
  }

  // node_modules/d3-selection/src/selection/raise.js
  function raise() {
    if (this.nextSibling) this.parentNode.appendChild(this);
  }
  function raise_default() {
    return this.each(raise);
  }

  // node_modules/d3-selection/src/selection/lower.js
  function lower() {
    if (this.previousSibling) this.parentNode.insertBefore(this, this.parentNode.firstChild);
  }
  function lower_default() {
    return this.each(lower);
  }

  // node_modules/d3-selection/src/selection/append.js
  function append_default(name) {
    var create2 = typeof name === "function" ? name : creator_default(name);
    return this.select(function() {
      return this.appendChild(create2.apply(this, arguments));
    });
  }

  // node_modules/d3-selection/src/selection/insert.js
  function constantNull() {
    return null;
  }
  function insert_default(name, before) {
    var create2 = typeof name === "function" ? name : creator_default(name), select = before == null ? constantNull : typeof before === "function" ? before : selector_default(before);
    return this.select(function() {
      return this.insertBefore(create2.apply(this, arguments), select.apply(this, arguments) || null);
    });
  }

  // node_modules/d3-selection/src/selection/remove.js
  function remove() {
    var parent = this.parentNode;
    if (parent) parent.removeChild(this);
  }
  function remove_default() {
    return this.each(remove);
  }

  // node_modules/d3-selection/src/selection/clone.js
  function selection_cloneShallow() {
    var clone = this.cloneNode(false), parent = this.parentNode;
    return parent ? parent.insertBefore(clone, this.nextSibling) : clone;
  }
  function selection_cloneDeep() {
    var clone = this.cloneNode(true), parent = this.parentNode;
    return parent ? parent.insertBefore(clone, this.nextSibling) : clone;
  }
  function clone_default(deep) {
    return this.select(deep ? selection_cloneDeep : selection_cloneShallow);
  }

  // node_modules/d3-selection/src/selection/datum.js
  function datum_default(value) {
    return arguments.length ? this.property("__data__", value) : this.node().__data__;
  }

  // node_modules/d3-selection/src/selection/on.js
  function contextListener(listener) {
    return function(event) {
      listener.call(this, event, this.__data__);
    };
  }
  function parseTypenames(typenames) {
    return typenames.trim().split(/^|\s+/).map(function(t) {
      var name = "", i = t.indexOf(".");
      if (i >= 0) name = t.slice(i + 1), t = t.slice(0, i);
      return { type: t, name };
    });
  }
  function onRemove(typename) {
    return function() {
      var on = this.__on;
      if (!on) return;
      for (var j = 0, i = -1, m = on.length, o; j < m; ++j) {
        if (o = on[j], (!typename.type || o.type === typename.type) && o.name === typename.name) {
          this.removeEventListener(o.type, o.listener, o.options);
        } else {
          on[++i] = o;
        }
      }
      if (++i) on.length = i;
      else delete this.__on;
    };
  }
  function onAdd(typename, value, options) {
    return function() {
      var on = this.__on, o, listener = contextListener(value);
      if (on) for (var j = 0, m = on.length; j < m; ++j) {
        if ((o = on[j]).type === typename.type && o.name === typename.name) {
          this.removeEventListener(o.type, o.listener, o.options);
          this.addEventListener(o.type, o.listener = listener, o.options = options);
          o.value = value;
          return;
        }
      }
      this.addEventListener(typename.type, listener, options);
      o = { type: typename.type, name: typename.name, value, listener, options };
      if (!on) this.__on = [o];
      else on.push(o);
    };
  }
  function on_default(typename, value, options) {
    var typenames = parseTypenames(typename + ""), i, n = typenames.length, t;
    if (arguments.length < 2) {
      var on = this.node().__on;
      if (on) for (var j = 0, m = on.length, o; j < m; ++j) {
        for (i = 0, o = on[j]; i < n; ++i) {
          if ((t = typenames[i]).type === o.type && t.name === o.name) {
            return o.value;
          }
        }
      }
      return;
    }
    on = value ? onAdd : onRemove;
    for (i = 0; i < n; ++i) this.each(on(typenames[i], value, options));
    return this;
  }

  // node_modules/d3-selection/src/selection/dispatch.js
  function dispatchEvent(node, type, params) {
    var window2 = window_default(node), event = window2.CustomEvent;
    if (typeof event === "function") {
      event = new event(type, params);
    } else {
      event = window2.document.createEvent("Event");
      if (params) event.initEvent(type, params.bubbles, params.cancelable), event.detail = params.detail;
      else event.initEvent(type, false, false);
    }
    node.dispatchEvent(event);
  }
  function dispatchConstant(type, params) {
    return function() {
      return dispatchEvent(this, type, params);
    };
  }
  function dispatchFunction(type, params) {
    return function() {
      return dispatchEvent(this, type, params.apply(this, arguments));
    };
  }
  function dispatch_default(type, params) {
    return this.each((typeof params === "function" ? dispatchFunction : dispatchConstant)(type, params));
  }

  // node_modules/d3-selection/src/selection/iterator.js
  function* iterator_default() {
    for (var groups = this._groups, j = 0, m = groups.length; j < m; ++j) {
      for (var group = groups[j], i = 0, n = group.length, node; i < n; ++i) {
        if (node = group[i]) yield node;
      }
    }
  }

  // node_modules/d3-selection/src/selection/index.js
  var root = [null];
  function Selection(groups, parents) {
    this._groups = groups;
    this._parents = parents;
  }
  function selection() {
    return new Selection([[document.documentElement]], root);
  }
  function selection_selection() {
    return this;
  }
  Selection.prototype = selection.prototype = {
    constructor: Selection,
    select: select_default,
    selectAll: selectAll_default,
    selectChild: selectChild_default,
    selectChildren: selectChildren_default,
    filter: filter_default,
    data: data_default,
    enter: enter_default,
    exit: exit_default,
    join: join_default,
    merge: merge_default,
    selection: selection_selection,
    order: order_default,
    sort: sort_default,
    call: call_default,
    nodes: nodes_default,
    node: node_default,
    size: size_default,
    empty: empty_default,
    each: each_default,
    attr: attr_default,
    style: style_default,
    property: property_default,
    classed: classed_default,
    text: text_default,
    html: html_default,
    raise: raise_default,
    lower: lower_default,
    append: append_default,
    insert: insert_default,
    remove: remove_default,
    clone: clone_default,
    datum: datum_default,
    on: on_default,
    dispatch: dispatch_default,
    [Symbol.iterator]: iterator_default
  };
  var selection_default = selection;

  // node_modules/d3-selection/src/select.js
  function select_default2(selector) {
    return typeof selector === "string" ? new Selection([[document.querySelector(selector)]], [document.documentElement]) : new Selection([[selector]], root);
  }

  // node_modules/d3-selection/src/sourceEvent.js
  function sourceEvent_default(event) {
    let sourceEvent;
    while (sourceEvent = event.sourceEvent) event = sourceEvent;
    return event;
  }

  // node_modules/d3-selection/src/pointer.js
  function pointer_default(event, node) {
    event = sourceEvent_default(event);
    if (node === void 0) node = event.currentTarget;
    if (node) {
      var svg = node.ownerSVGElement || node;
      if (svg.createSVGPoint) {
        var point = svg.createSVGPoint();
        point.x = event.clientX, point.y = event.clientY;
        point = point.matrixTransform(node.getScreenCTM().inverse());
        return [point.x, point.y];
      }
      if (node.getBoundingClientRect) {
        var rect = node.getBoundingClientRect();
        return [event.clientX - rect.left - node.clientLeft, event.clientY - rect.top - node.clientTop];
      }
    }
    return [event.pageX, event.pageY];
  }

  // node_modules/d3-dispatch/src/dispatch.js
  var noop = { value: () => {
  } };
  function dispatch() {
    for (var i = 0, n = arguments.length, _ = {}, t; i < n; ++i) {
      if (!(t = arguments[i] + "") || t in _ || /[\s.]/.test(t)) throw new Error("illegal type: " + t);
      _[t] = [];
    }
    return new Dispatch(_);
  }
  function Dispatch(_) {
    this._ = _;
  }
  function parseTypenames2(typenames, types) {
    return typenames.trim().split(/^|\s+/).map(function(t) {
      var name = "", i = t.indexOf(".");
      if (i >= 0) name = t.slice(i + 1), t = t.slice(0, i);
      if (t && !types.hasOwnProperty(t)) throw new Error("unknown type: " + t);
      return { type: t, name };
    });
  }
  Dispatch.prototype = dispatch.prototype = {
    constructor: Dispatch,
    on: function(typename, callback) {
      var _ = this._, T = parseTypenames2(typename + "", _), t, i = -1, n = T.length;
      if (arguments.length < 2) {
        while (++i < n) if ((t = (typename = T[i]).type) && (t = get(_[t], typename.name))) return t;
        return;
      }
      if (callback != null && typeof callback !== "function") throw new Error("invalid callback: " + callback);
      while (++i < n) {
        if (t = (typename = T[i]).type) _[t] = set(_[t], typename.name, callback);
        else if (callback == null) for (t in _) _[t] = set(_[t], typename.name, null);
      }
      return this;
    },
    copy: function() {
      var copy = {}, _ = this._;
      for (var t in _) copy[t] = _[t].slice();
      return new Dispatch(copy);
    },
    call: function(type, that) {
      if ((n = arguments.length - 2) > 0) for (var args = new Array(n), i = 0, n, t; i < n; ++i) args[i] = arguments[i + 2];
      if (!this._.hasOwnProperty(type)) throw new Error("unknown type: " + type);
      for (t = this._[type], i = 0, n = t.length; i < n; ++i) t[i].value.apply(that, args);
    },
    apply: function(type, that, args) {
      if (!this._.hasOwnProperty(type)) throw new Error("unknown type: " + type);
      for (var t = this._[type], i = 0, n = t.length; i < n; ++i) t[i].value.apply(that, args);
    }
  };
  function get(type, name) {
    for (var i = 0, n = type.length, c; i < n; ++i) {
      if ((c = type[i]).name === name) {
        return c.value;
      }
    }
  }
  function set(type, name, callback) {
    for (var i = 0, n = type.length; i < n; ++i) {
      if (type[i].name === name) {
        type[i] = noop, type = type.slice(0, i).concat(type.slice(i + 1));
        break;
      }
    }
    if (callback != null) type.push({ name, value: callback });
    return type;
  }
  var dispatch_default2 = dispatch;

  // node_modules/d3-drag/src/noevent.js
  var nonpassivecapture = { capture: true, passive: false };
  function noevent_default(event) {
    event.preventDefault();
    event.stopImmediatePropagation();
  }

  // node_modules/d3-drag/src/nodrag.js
  function nodrag_default(view) {
    var root2 = view.document.documentElement, selection2 = select_default2(view).on("dragstart.drag", noevent_default, nonpassivecapture);
    if ("onselectstart" in root2) {
      selection2.on("selectstart.drag", noevent_default, nonpassivecapture);
    } else {
      root2.__noselect = root2.style.MozUserSelect;
      root2.style.MozUserSelect = "none";
    }
  }
  function yesdrag(view, noclick) {
    var root2 = view.document.documentElement, selection2 = select_default2(view).on("dragstart.drag", null);
    if (noclick) {
      selection2.on("click.drag", noevent_default, nonpassivecapture);
      setTimeout(function() {
        selection2.on("click.drag", null);
      }, 0);
    }
    if ("onselectstart" in root2) {
      selection2.on("selectstart.drag", null);
    } else {
      root2.style.MozUserSelect = root2.__noselect;
      delete root2.__noselect;
    }
  }

  // node_modules/d3-color/src/define.js
  function define_default(constructor, factory, prototype) {
    constructor.prototype = factory.prototype = prototype;
    prototype.constructor = constructor;
  }
  function extend(parent, definition) {
    var prototype = Object.create(parent.prototype);
    for (var key in definition) prototype[key] = definition[key];
    return prototype;
  }

  // node_modules/d3-color/src/color.js
  function Color() {
  }
  var darker = 0.7;
  var brighter = 1 / darker;
  var reI = "\\s*([+-]?\\d+)\\s*";
  var reN = "\\s*([+-]?(?:\\d*\\.)?\\d+(?:[eE][+-]?\\d+)?)\\s*";
  var reP = "\\s*([+-]?(?:\\d*\\.)?\\d+(?:[eE][+-]?\\d+)?)%\\s*";
  var reHex = /^#([0-9a-f]{3,8})$/;
  var reRgbInteger = new RegExp(`^rgb\\(${reI},${reI},${reI}\\)$`);
  var reRgbPercent = new RegExp(`^rgb\\(${reP},${reP},${reP}\\)$`);
  var reRgbaInteger = new RegExp(`^rgba\\(${reI},${reI},${reI},${reN}\\)$`);
  var reRgbaPercent = new RegExp(`^rgba\\(${reP},${reP},${reP},${reN}\\)$`);
  var reHslPercent = new RegExp(`^hsl\\(${reN},${reP},${reP}\\)$`);
  var reHslaPercent = new RegExp(`^hsla\\(${reN},${reP},${reP},${reN}\\)$`);
  var named = {
    aliceblue: 15792383,
    antiquewhite: 16444375,
    aqua: 65535,
    aquamarine: 8388564,
    azure: 15794175,
    beige: 16119260,
    bisque: 16770244,
    black: 0,
    blanchedalmond: 16772045,
    blue: 255,
    blueviolet: 9055202,
    brown: 10824234,
    burlywood: 14596231,
    cadetblue: 6266528,
    chartreuse: 8388352,
    chocolate: 13789470,
    coral: 16744272,
    cornflowerblue: 6591981,
    cornsilk: 16775388,
    crimson: 14423100,
    cyan: 65535,
    darkblue: 139,
    darkcyan: 35723,
    darkgoldenrod: 12092939,
    darkgray: 11119017,
    darkgreen: 25600,
    darkgrey: 11119017,
    darkkhaki: 12433259,
    darkmagenta: 9109643,
    darkolivegreen: 5597999,
    darkorange: 16747520,
    darkorchid: 10040012,
    darkred: 9109504,
    darksalmon: 15308410,
    darkseagreen: 9419919,
    darkslateblue: 4734347,
    darkslategray: 3100495,
    darkslategrey: 3100495,
    darkturquoise: 52945,
    darkviolet: 9699539,
    deeppink: 16716947,
    deepskyblue: 49151,
    dimgray: 6908265,
    dimgrey: 6908265,
    dodgerblue: 2003199,
    firebrick: 11674146,
    floralwhite: 16775920,
    forestgreen: 2263842,
    fuchsia: 16711935,
    gainsboro: 14474460,
    ghostwhite: 16316671,
    gold: 16766720,
    goldenrod: 14329120,
    gray: 8421504,
    green: 32768,
    greenyellow: 11403055,
    grey: 8421504,
    honeydew: 15794160,
    hotpink: 16738740,
    indianred: 13458524,
    indigo: 4915330,
    ivory: 16777200,
    khaki: 15787660,
    lavender: 15132410,
    lavenderblush: 16773365,
    lawngreen: 8190976,
    lemonchiffon: 16775885,
    lightblue: 11393254,
    lightcoral: 15761536,
    lightcyan: 14745599,
    lightgoldenrodyellow: 16448210,
    lightgray: 13882323,
    lightgreen: 9498256,
    lightgrey: 13882323,
    lightpink: 16758465,
    lightsalmon: 16752762,
    lightseagreen: 2142890,
    lightskyblue: 8900346,
    lightslategray: 7833753,
    lightslategrey: 7833753,
    lightsteelblue: 11584734,
    lightyellow: 16777184,
    lime: 65280,
    limegreen: 3329330,
    linen: 16445670,
    magenta: 16711935,
    maroon: 8388608,
    mediumaquamarine: 6737322,
    mediumblue: 205,
    mediumorchid: 12211667,
    mediumpurple: 9662683,
    mediumseagreen: 3978097,
    mediumslateblue: 8087790,
    mediumspringgreen: 64154,
    mediumturquoise: 4772300,
    mediumvioletred: 13047173,
    midnightblue: 1644912,
    mintcream: 16121850,
    mistyrose: 16770273,
    moccasin: 16770229,
    navajowhite: 16768685,
    navy: 128,
    oldlace: 16643558,
    olive: 8421376,
    olivedrab: 7048739,
    orange: 16753920,
    orangered: 16729344,
    orchid: 14315734,
    palegoldenrod: 15657130,
    palegreen: 10025880,
    paleturquoise: 11529966,
    palevioletred: 14381203,
    papayawhip: 16773077,
    peachpuff: 16767673,
    peru: 13468991,
    pink: 16761035,
    plum: 14524637,
    powderblue: 11591910,
    purple: 8388736,
    rebeccapurple: 6697881,
    red: 16711680,
    rosybrown: 12357519,
    royalblue: 4286945,
    saddlebrown: 9127187,
    salmon: 16416882,
    sandybrown: 16032864,
    seagreen: 3050327,
    seashell: 16774638,
    sienna: 10506797,
    silver: 12632256,
    skyblue: 8900331,
    slateblue: 6970061,
    slategray: 7372944,
    slategrey: 7372944,
    snow: 16775930,
    springgreen: 65407,
    steelblue: 4620980,
    tan: 13808780,
    teal: 32896,
    thistle: 14204888,
    tomato: 16737095,
    turquoise: 4251856,
    violet: 15631086,
    wheat: 16113331,
    white: 16777215,
    whitesmoke: 16119285,
    yellow: 16776960,
    yellowgreen: 10145074
  };
  define_default(Color, color, {
    copy(channels) {
      return Object.assign(new this.constructor(), this, channels);
    },
    displayable() {
      return this.rgb().displayable();
    },
    hex: color_formatHex,
    // Deprecated! Use color.formatHex.
    formatHex: color_formatHex,
    formatHex8: color_formatHex8,
    formatHsl: color_formatHsl,
    formatRgb: color_formatRgb,
    toString: color_formatRgb
  });
  function color_formatHex() {
    return this.rgb().formatHex();
  }
  function color_formatHex8() {
    return this.rgb().formatHex8();
  }
  function color_formatHsl() {
    return hslConvert(this).formatHsl();
  }
  function color_formatRgb() {
    return this.rgb().formatRgb();
  }
  function color(format) {
    var m, l;
    format = (format + "").trim().toLowerCase();
    return (m = reHex.exec(format)) ? (l = m[1].length, m = parseInt(m[1], 16), l === 6 ? rgbn(m) : l === 3 ? new Rgb(m >> 8 & 15 | m >> 4 & 240, m >> 4 & 15 | m & 240, (m & 15) << 4 | m & 15, 1) : l === 8 ? rgba(m >> 24 & 255, m >> 16 & 255, m >> 8 & 255, (m & 255) / 255) : l === 4 ? rgba(m >> 12 & 15 | m >> 8 & 240, m >> 8 & 15 | m >> 4 & 240, m >> 4 & 15 | m & 240, ((m & 15) << 4 | m & 15) / 255) : null) : (m = reRgbInteger.exec(format)) ? new Rgb(m[1], m[2], m[3], 1) : (m = reRgbPercent.exec(format)) ? new Rgb(m[1] * 255 / 100, m[2] * 255 / 100, m[3] * 255 / 100, 1) : (m = reRgbaInteger.exec(format)) ? rgba(m[1], m[2], m[3], m[4]) : (m = reRgbaPercent.exec(format)) ? rgba(m[1] * 255 / 100, m[2] * 255 / 100, m[3] * 255 / 100, m[4]) : (m = reHslPercent.exec(format)) ? hsla(m[1], m[2] / 100, m[3] / 100, 1) : (m = reHslaPercent.exec(format)) ? hsla(m[1], m[2] / 100, m[3] / 100, m[4]) : named.hasOwnProperty(format) ? rgbn(named[format]) : format === "transparent" ? new Rgb(NaN, NaN, NaN, 0) : null;
  }
  function rgbn(n) {
    return new Rgb(n >> 16 & 255, n >> 8 & 255, n & 255, 1);
  }
  function rgba(r, g, b, a) {
    if (a <= 0) r = g = b = NaN;
    return new Rgb(r, g, b, a);
  }
  function rgbConvert(o) {
    if (!(o instanceof Color)) o = color(o);
    if (!o) return new Rgb();
    o = o.rgb();
    return new Rgb(o.r, o.g, o.b, o.opacity);
  }
  function rgb(r, g, b, opacity) {
    return arguments.length === 1 ? rgbConvert(r) : new Rgb(r, g, b, opacity == null ? 1 : opacity);
  }
  function Rgb(r, g, b, opacity) {
    this.r = +r;
    this.g = +g;
    this.b = +b;
    this.opacity = +opacity;
  }
  define_default(Rgb, rgb, extend(Color, {
    brighter(k) {
      k = k == null ? brighter : Math.pow(brighter, k);
      return new Rgb(this.r * k, this.g * k, this.b * k, this.opacity);
    },
    darker(k) {
      k = k == null ? darker : Math.pow(darker, k);
      return new Rgb(this.r * k, this.g * k, this.b * k, this.opacity);
    },
    rgb() {
      return this;
    },
    clamp() {
      return new Rgb(clampi(this.r), clampi(this.g), clampi(this.b), clampa(this.opacity));
    },
    displayable() {
      return -0.5 <= this.r && this.r < 255.5 && (-0.5 <= this.g && this.g < 255.5) && (-0.5 <= this.b && this.b < 255.5) && (0 <= this.opacity && this.opacity <= 1);
    },
    hex: rgb_formatHex,
    // Deprecated! Use color.formatHex.
    formatHex: rgb_formatHex,
    formatHex8: rgb_formatHex8,
    formatRgb: rgb_formatRgb,
    toString: rgb_formatRgb
  }));
  function rgb_formatHex() {
    return `#${hex(this.r)}${hex(this.g)}${hex(this.b)}`;
  }
  function rgb_formatHex8() {
    return `#${hex(this.r)}${hex(this.g)}${hex(this.b)}${hex((isNaN(this.opacity) ? 1 : this.opacity) * 255)}`;
  }
  function rgb_formatRgb() {
    const a = clampa(this.opacity);
    return `${a === 1 ? "rgb(" : "rgba("}${clampi(this.r)}, ${clampi(this.g)}, ${clampi(this.b)}${a === 1 ? ")" : `, ${a})`}`;
  }
  function clampa(opacity) {
    return isNaN(opacity) ? 1 : Math.max(0, Math.min(1, opacity));
  }
  function clampi(value) {
    return Math.max(0, Math.min(255, Math.round(value) || 0));
  }
  function hex(value) {
    value = clampi(value);
    return (value < 16 ? "0" : "") + value.toString(16);
  }
  function hsla(h, s, l, a) {
    if (a <= 0) h = s = l = NaN;
    else if (l <= 0 || l >= 1) h = s = NaN;
    else if (s <= 0) h = NaN;
    return new Hsl(h, s, l, a);
  }
  function hslConvert(o) {
    if (o instanceof Hsl) return new Hsl(o.h, o.s, o.l, o.opacity);
    if (!(o instanceof Color)) o = color(o);
    if (!o) return new Hsl();
    if (o instanceof Hsl) return o;
    o = o.rgb();
    var r = o.r / 255, g = o.g / 255, b = o.b / 255, min = Math.min(r, g, b), max = Math.max(r, g, b), h = NaN, s = max - min, l = (max + min) / 2;
    if (s) {
      if (r === max) h = (g - b) / s + (g < b) * 6;
      else if (g === max) h = (b - r) / s + 2;
      else h = (r - g) / s + 4;
      s /= l < 0.5 ? max + min : 2 - max - min;
      h *= 60;
    } else {
      s = l > 0 && l < 1 ? 0 : h;
    }
    return new Hsl(h, s, l, o.opacity);
  }
  function hsl(h, s, l, opacity) {
    return arguments.length === 1 ? hslConvert(h) : new Hsl(h, s, l, opacity == null ? 1 : opacity);
  }
  function Hsl(h, s, l, opacity) {
    this.h = +h;
    this.s = +s;
    this.l = +l;
    this.opacity = +opacity;
  }
  define_default(Hsl, hsl, extend(Color, {
    brighter(k) {
      k = k == null ? brighter : Math.pow(brighter, k);
      return new Hsl(this.h, this.s, this.l * k, this.opacity);
    },
    darker(k) {
      k = k == null ? darker : Math.pow(darker, k);
      return new Hsl(this.h, this.s, this.l * k, this.opacity);
    },
    rgb() {
      var h = this.h % 360 + (this.h < 0) * 360, s = isNaN(h) || isNaN(this.s) ? 0 : this.s, l = this.l, m2 = l + (l < 0.5 ? l : 1 - l) * s, m1 = 2 * l - m2;
      return new Rgb(
        hsl2rgb(h >= 240 ? h - 240 : h + 120, m1, m2),
        hsl2rgb(h, m1, m2),
        hsl2rgb(h < 120 ? h + 240 : h - 120, m1, m2),
        this.opacity
      );
    },
    clamp() {
      return new Hsl(clamph(this.h), clampt(this.s), clampt(this.l), clampa(this.opacity));
    },
    displayable() {
      return (0 <= this.s && this.s <= 1 || isNaN(this.s)) && (0 <= this.l && this.l <= 1) && (0 <= this.opacity && this.opacity <= 1);
    },
    formatHsl() {
      const a = clampa(this.opacity);
      return `${a === 1 ? "hsl(" : "hsla("}${clamph(this.h)}, ${clampt(this.s) * 100}%, ${clampt(this.l) * 100}%${a === 1 ? ")" : `, ${a})`}`;
    }
  }));
  function clamph(value) {
    value = (value || 0) % 360;
    return value < 0 ? value + 360 : value;
  }
  function clampt(value) {
    return Math.max(0, Math.min(1, value || 0));
  }
  function hsl2rgb(h, m1, m2) {
    return (h < 60 ? m1 + (m2 - m1) * h / 60 : h < 180 ? m2 : h < 240 ? m1 + (m2 - m1) * (240 - h) / 60 : m1) * 255;
  }

  // node_modules/d3-interpolate/src/basis.js
  function basis(t1, v0, v1, v2, v3) {
    var t2 = t1 * t1, t3 = t2 * t1;
    return ((1 - 3 * t1 + 3 * t2 - t3) * v0 + (4 - 6 * t2 + 3 * t3) * v1 + (1 + 3 * t1 + 3 * t2 - 3 * t3) * v2 + t3 * v3) / 6;
  }
  function basis_default(values) {
    var n = values.length - 1;
    return function(t) {
      var i = t <= 0 ? t = 0 : t >= 1 ? (t = 1, n - 1) : Math.floor(t * n), v1 = values[i], v2 = values[i + 1], v0 = i > 0 ? values[i - 1] : 2 * v1 - v2, v3 = i < n - 1 ? values[i + 2] : 2 * v2 - v1;
      return basis((t - i / n) * n, v0, v1, v2, v3);
    };
  }

  // node_modules/d3-interpolate/src/basisClosed.js
  function basisClosed_default(values) {
    var n = values.length;
    return function(t) {
      var i = Math.floor(((t %= 1) < 0 ? ++t : t) * n), v0 = values[(i + n - 1) % n], v1 = values[i % n], v2 = values[(i + 1) % n], v3 = values[(i + 2) % n];
      return basis((t - i / n) * n, v0, v1, v2, v3);
    };
  }

  // node_modules/d3-interpolate/src/constant.js
  var constant_default2 = (x) => () => x;

  // node_modules/d3-interpolate/src/color.js
  function linear(a, d) {
    return function(t) {
      return a + t * d;
    };
  }
  function exponential(a, b, y) {
    return a = Math.pow(a, y), b = Math.pow(b, y) - a, y = 1 / y, function(t) {
      return Math.pow(a + t * b, y);
    };
  }
  function gamma(y) {
    return (y = +y) === 1 ? nogamma : function(a, b) {
      return b - a ? exponential(a, b, y) : constant_default2(isNaN(a) ? b : a);
    };
  }
  function nogamma(a, b) {
    var d = b - a;
    return d ? linear(a, d) : constant_default2(isNaN(a) ? b : a);
  }

  // node_modules/d3-interpolate/src/rgb.js
  var rgb_default = (function rgbGamma(y) {
    var color2 = gamma(y);
    function rgb2(start2, end) {
      var r = color2((start2 = rgb(start2)).r, (end = rgb(end)).r), g = color2(start2.g, end.g), b = color2(start2.b, end.b), opacity = nogamma(start2.opacity, end.opacity);
      return function(t) {
        start2.r = r(t);
        start2.g = g(t);
        start2.b = b(t);
        start2.opacity = opacity(t);
        return start2 + "";
      };
    }
    rgb2.gamma = rgbGamma;
    return rgb2;
  })(1);
  function rgbSpline(spline) {
    return function(colors) {
      var n = colors.length, r = new Array(n), g = new Array(n), b = new Array(n), i, color2;
      for (i = 0; i < n; ++i) {
        color2 = rgb(colors[i]);
        r[i] = color2.r || 0;
        g[i] = color2.g || 0;
        b[i] = color2.b || 0;
      }
      r = spline(r);
      g = spline(g);
      b = spline(b);
      color2.opacity = 1;
      return function(t) {
        color2.r = r(t);
        color2.g = g(t);
        color2.b = b(t);
        return color2 + "";
      };
    };
  }
  var rgbBasis = rgbSpline(basis_default);
  var rgbBasisClosed = rgbSpline(basisClosed_default);

  // node_modules/d3-interpolate/src/number.js
  function number_default(a, b) {
    return a = +a, b = +b, function(t) {
      return a * (1 - t) + b * t;
    };
  }

  // node_modules/d3-interpolate/src/string.js
  var reA = /[-+]?(?:\d+\.?\d*|\.?\d+)(?:[eE][-+]?\d+)?/g;
  var reB = new RegExp(reA.source, "g");
  function zero(b) {
    return function() {
      return b;
    };
  }
  function one(b) {
    return function(t) {
      return b(t) + "";
    };
  }
  function string_default(a, b) {
    var bi = reA.lastIndex = reB.lastIndex = 0, am, bm, bs, i = -1, s = [], q = [];
    a = a + "", b = b + "";
    while ((am = reA.exec(a)) && (bm = reB.exec(b))) {
      if ((bs = bm.index) > bi) {
        bs = b.slice(bi, bs);
        if (s[i]) s[i] += bs;
        else s[++i] = bs;
      }
      if ((am = am[0]) === (bm = bm[0])) {
        if (s[i]) s[i] += bm;
        else s[++i] = bm;
      } else {
        s[++i] = null;
        q.push({ i, x: number_default(am, bm) });
      }
      bi = reB.lastIndex;
    }
    if (bi < b.length) {
      bs = b.slice(bi);
      if (s[i]) s[i] += bs;
      else s[++i] = bs;
    }
    return s.length < 2 ? q[0] ? one(q[0].x) : zero(b) : (b = q.length, function(t) {
      for (var i2 = 0, o; i2 < b; ++i2) s[(o = q[i2]).i] = o.x(t);
      return s.join("");
    });
  }

  // node_modules/d3-interpolate/src/transform/decompose.js
  var degrees = 180 / Math.PI;
  var identity = {
    translateX: 0,
    translateY: 0,
    rotate: 0,
    skewX: 0,
    scaleX: 1,
    scaleY: 1
  };
  function decompose_default(a, b, c, d, e, f) {
    var scaleX, scaleY, skewX;
    if (scaleX = Math.sqrt(a * a + b * b)) a /= scaleX, b /= scaleX;
    if (skewX = a * c + b * d) c -= a * skewX, d -= b * skewX;
    if (scaleY = Math.sqrt(c * c + d * d)) c /= scaleY, d /= scaleY, skewX /= scaleY;
    if (a * d < b * c) a = -a, b = -b, skewX = -skewX, scaleX = -scaleX;
    return {
      translateX: e,
      translateY: f,
      rotate: Math.atan2(b, a) * degrees,
      skewX: Math.atan(skewX) * degrees,
      scaleX,
      scaleY
    };
  }

  // node_modules/d3-interpolate/src/transform/parse.js
  var svgNode;
  function parseCss(value) {
    const m = new (typeof DOMMatrix === "function" ? DOMMatrix : WebKitCSSMatrix)(value + "");
    return m.isIdentity ? identity : decompose_default(m.a, m.b, m.c, m.d, m.e, m.f);
  }
  function parseSvg(value) {
    if (value == null) return identity;
    if (!svgNode) svgNode = document.createElementNS("http://www.w3.org/2000/svg", "g");
    svgNode.setAttribute("transform", value);
    if (!(value = svgNode.transform.baseVal.consolidate())) return identity;
    value = value.matrix;
    return decompose_default(value.a, value.b, value.c, value.d, value.e, value.f);
  }

  // node_modules/d3-interpolate/src/transform/index.js
  function interpolateTransform(parse, pxComma, pxParen, degParen) {
    function pop(s) {
      return s.length ? s.pop() + " " : "";
    }
    function translate(xa, ya, xb, yb, s, q) {
      if (xa !== xb || ya !== yb) {
        var i = s.push("translate(", null, pxComma, null, pxParen);
        q.push({ i: i - 4, x: number_default(xa, xb) }, { i: i - 2, x: number_default(ya, yb) });
      } else if (xb || yb) {
        s.push("translate(" + xb + pxComma + yb + pxParen);
      }
    }
    function rotate(a, b, s, q) {
      if (a !== b) {
        if (a - b > 180) b += 360;
        else if (b - a > 180) a += 360;
        q.push({ i: s.push(pop(s) + "rotate(", null, degParen) - 2, x: number_default(a, b) });
      } else if (b) {
        s.push(pop(s) + "rotate(" + b + degParen);
      }
    }
    function skewX(a, b, s, q) {
      if (a !== b) {
        q.push({ i: s.push(pop(s) + "skewX(", null, degParen) - 2, x: number_default(a, b) });
      } else if (b) {
        s.push(pop(s) + "skewX(" + b + degParen);
      }
    }
    function scale(xa, ya, xb, yb, s, q) {
      if (xa !== xb || ya !== yb) {
        var i = s.push(pop(s) + "scale(", null, ",", null, ")");
        q.push({ i: i - 4, x: number_default(xa, xb) }, { i: i - 2, x: number_default(ya, yb) });
      } else if (xb !== 1 || yb !== 1) {
        s.push(pop(s) + "scale(" + xb + "," + yb + ")");
      }
    }
    return function(a, b) {
      var s = [], q = [];
      a = parse(a), b = parse(b);
      translate(a.translateX, a.translateY, b.translateX, b.translateY, s, q);
      rotate(a.rotate, b.rotate, s, q);
      skewX(a.skewX, b.skewX, s, q);
      scale(a.scaleX, a.scaleY, b.scaleX, b.scaleY, s, q);
      a = b = null;
      return function(t) {
        var i = -1, n = q.length, o;
        while (++i < n) s[(o = q[i]).i] = o.x(t);
        return s.join("");
      };
    };
  }
  var interpolateTransformCss = interpolateTransform(parseCss, "px, ", "px)", "deg)");
  var interpolateTransformSvg = interpolateTransform(parseSvg, ", ", ")", ")");

  // node_modules/d3-interpolate/src/zoom.js
  var epsilon2 = 1e-12;
  function cosh(x) {
    return ((x = Math.exp(x)) + 1 / x) / 2;
  }
  function sinh(x) {
    return ((x = Math.exp(x)) - 1 / x) / 2;
  }
  function tanh(x) {
    return ((x = Math.exp(2 * x)) - 1) / (x + 1);
  }
  var zoom_default = (function zoomRho(rho, rho2, rho4) {
    function zoom(p0, p1) {
      var ux0 = p0[0], uy0 = p0[1], w0 = p0[2], ux1 = p1[0], uy1 = p1[1], w1 = p1[2], dx = ux1 - ux0, dy = uy1 - uy0, d2 = dx * dx + dy * dy, i, S;
      if (d2 < epsilon2) {
        S = Math.log(w1 / w0) / rho;
        i = function(t) {
          return [
            ux0 + t * dx,
            uy0 + t * dy,
            w0 * Math.exp(rho * t * S)
          ];
        };
      } else {
        var d1 = Math.sqrt(d2), b0 = (w1 * w1 - w0 * w0 + rho4 * d2) / (2 * w0 * rho2 * d1), b1 = (w1 * w1 - w0 * w0 - rho4 * d2) / (2 * w1 * rho2 * d1), r0 = Math.log(Math.sqrt(b0 * b0 + 1) - b0), r1 = Math.log(Math.sqrt(b1 * b1 + 1) - b1);
        S = (r1 - r0) / rho;
        i = function(t) {
          var s = t * S, coshr0 = cosh(r0), u = w0 / (rho2 * d1) * (coshr0 * tanh(rho * s + r0) - sinh(r0));
          return [
            ux0 + u * dx,
            uy0 + u * dy,
            w0 * coshr0 / cosh(rho * s + r0)
          ];
        };
      }
      i.duration = S * 1e3 * rho / Math.SQRT2;
      return i;
    }
    zoom.rho = function(_) {
      var _1 = Math.max(1e-3, +_), _2 = _1 * _1, _4 = _2 * _2;
      return zoomRho(_1, _2, _4);
    };
    return zoom;
  })(Math.SQRT2, 2, 4);

  // node_modules/d3-timer/src/timer.js
  var frame = 0;
  var timeout = 0;
  var interval = 0;
  var pokeDelay = 1e3;
  var taskHead;
  var taskTail;
  var clockLast = 0;
  var clockNow = 0;
  var clockSkew = 0;
  var clock = typeof performance === "object" && performance.now ? performance : Date;
  var setFrame = typeof window === "object" && window.requestAnimationFrame ? window.requestAnimationFrame.bind(window) : function(f) {
    setTimeout(f, 17);
  };
  function now() {
    return clockNow || (setFrame(clearNow), clockNow = clock.now() + clockSkew);
  }
  function clearNow() {
    clockNow = 0;
  }
  function Timer() {
    this._call = this._time = this._next = null;
  }
  Timer.prototype = timer.prototype = {
    constructor: Timer,
    restart: function(callback, delay, time) {
      if (typeof callback !== "function") throw new TypeError("callback is not a function");
      time = (time == null ? now() : +time) + (delay == null ? 0 : +delay);
      if (!this._next && taskTail !== this) {
        if (taskTail) taskTail._next = this;
        else taskHead = this;
        taskTail = this;
      }
      this._call = callback;
      this._time = time;
      sleep();
    },
    stop: function() {
      if (this._call) {
        this._call = null;
        this._time = Infinity;
        sleep();
      }
    }
  };
  function timer(callback, delay, time) {
    var t = new Timer();
    t.restart(callback, delay, time);
    return t;
  }
  function timerFlush() {
    now();
    ++frame;
    var t = taskHead, e;
    while (t) {
      if ((e = clockNow - t._time) >= 0) t._call.call(void 0, e);
      t = t._next;
    }
    --frame;
  }
  function wake() {
    clockNow = (clockLast = clock.now()) + clockSkew;
    frame = timeout = 0;
    try {
      timerFlush();
    } finally {
      frame = 0;
      nap();
      clockNow = 0;
    }
  }
  function poke() {
    var now2 = clock.now(), delay = now2 - clockLast;
    if (delay > pokeDelay) clockSkew -= delay, clockLast = now2;
  }
  function nap() {
    var t0, t1 = taskHead, t2, time = Infinity;
    while (t1) {
      if (t1._call) {
        if (time > t1._time) time = t1._time;
        t0 = t1, t1 = t1._next;
      } else {
        t2 = t1._next, t1._next = null;
        t1 = t0 ? t0._next = t2 : taskHead = t2;
      }
    }
    taskTail = t0;
    sleep(time);
  }
  function sleep(time) {
    if (frame) return;
    if (timeout) timeout = clearTimeout(timeout);
    var delay = time - clockNow;
    if (delay > 24) {
      if (time < Infinity) timeout = setTimeout(wake, time - clock.now() - clockSkew);
      if (interval) interval = clearInterval(interval);
    } else {
      if (!interval) clockLast = clock.now(), interval = setInterval(poke, pokeDelay);
      frame = 1, setFrame(wake);
    }
  }

  // node_modules/d3-timer/src/timeout.js
  function timeout_default(callback, delay, time) {
    var t = new Timer();
    delay = delay == null ? 0 : +delay;
    t.restart((elapsed) => {
      t.stop();
      callback(elapsed + delay);
    }, delay, time);
    return t;
  }

  // node_modules/d3-transition/src/transition/schedule.js
  var emptyOn = dispatch_default2("start", "end", "cancel", "interrupt");
  var emptyTween = [];
  var CREATED = 0;
  var SCHEDULED = 1;
  var STARTING = 2;
  var STARTED = 3;
  var RUNNING = 4;
  var ENDING = 5;
  var ENDED = 6;
  function schedule_default(node, name, id2, index, group, timing) {
    var schedules = node.__transition;
    if (!schedules) node.__transition = {};
    else if (id2 in schedules) return;
    create(node, id2, {
      name,
      index,
      // For context during callback.
      group,
      // For context during callback.
      on: emptyOn,
      tween: emptyTween,
      time: timing.time,
      delay: timing.delay,
      duration: timing.duration,
      ease: timing.ease,
      timer: null,
      state: CREATED
    });
  }
  function init(node, id2) {
    var schedule = get2(node, id2);
    if (schedule.state > CREATED) throw new Error("too late; already scheduled");
    return schedule;
  }
  function set2(node, id2) {
    var schedule = get2(node, id2);
    if (schedule.state > STARTED) throw new Error("too late; already running");
    return schedule;
  }
  function get2(node, id2) {
    var schedule = node.__transition;
    if (!schedule || !(schedule = schedule[id2])) throw new Error("transition not found");
    return schedule;
  }
  function create(node, id2, self2) {
    var schedules = node.__transition, tween;
    schedules[id2] = self2;
    self2.timer = timer(schedule, 0, self2.time);
    function schedule(elapsed) {
      self2.state = SCHEDULED;
      self2.timer.restart(start2, self2.delay, self2.time);
      if (self2.delay <= elapsed) start2(elapsed - self2.delay);
    }
    function start2(elapsed) {
      var i, j, n, o;
      if (self2.state !== SCHEDULED) return stop();
      for (i in schedules) {
        o = schedules[i];
        if (o.name !== self2.name) continue;
        if (o.state === STARTED) return timeout_default(start2);
        if (o.state === RUNNING) {
          o.state = ENDED;
          o.timer.stop();
          o.on.call("interrupt", node, node.__data__, o.index, o.group);
          delete schedules[i];
        } else if (+i < id2) {
          o.state = ENDED;
          o.timer.stop();
          o.on.call("cancel", node, node.__data__, o.index, o.group);
          delete schedules[i];
        }
      }
      timeout_default(function() {
        if (self2.state === STARTED) {
          self2.state = RUNNING;
          self2.timer.restart(tick, self2.delay, self2.time);
          tick(elapsed);
        }
      });
      self2.state = STARTING;
      self2.on.call("start", node, node.__data__, self2.index, self2.group);
      if (self2.state !== STARTING) return;
      self2.state = STARTED;
      tween = new Array(n = self2.tween.length);
      for (i = 0, j = -1; i < n; ++i) {
        if (o = self2.tween[i].value.call(node, node.__data__, self2.index, self2.group)) {
          tween[++j] = o;
        }
      }
      tween.length = j + 1;
    }
    function tick(elapsed) {
      var t = elapsed < self2.duration ? self2.ease.call(null, elapsed / self2.duration) : (self2.timer.restart(stop), self2.state = ENDING, 1), i = -1, n = tween.length;
      while (++i < n) {
        tween[i].call(node, t);
      }
      if (self2.state === ENDING) {
        self2.on.call("end", node, node.__data__, self2.index, self2.group);
        stop();
      }
    }
    function stop() {
      self2.state = ENDED;
      self2.timer.stop();
      delete schedules[id2];
      for (var i in schedules) return;
      delete node.__transition;
    }
  }

  // node_modules/d3-transition/src/interrupt.js
  function interrupt_default(node, name) {
    var schedules = node.__transition, schedule, active, empty2 = true, i;
    if (!schedules) return;
    name = name == null ? null : name + "";
    for (i in schedules) {
      if ((schedule = schedules[i]).name !== name) {
        empty2 = false;
        continue;
      }
      active = schedule.state > STARTING && schedule.state < ENDING;
      schedule.state = ENDED;
      schedule.timer.stop();
      schedule.on.call(active ? "interrupt" : "cancel", node, node.__data__, schedule.index, schedule.group);
      delete schedules[i];
    }
    if (empty2) delete node.__transition;
  }

  // node_modules/d3-transition/src/selection/interrupt.js
  function interrupt_default2(name) {
    return this.each(function() {
      interrupt_default(this, name);
    });
  }

  // node_modules/d3-transition/src/transition/tween.js
  function tweenRemove(id2, name) {
    var tween0, tween1;
    return function() {
      var schedule = set2(this, id2), tween = schedule.tween;
      if (tween !== tween0) {
        tween1 = tween0 = tween;
        for (var i = 0, n = tween1.length; i < n; ++i) {
          if (tween1[i].name === name) {
            tween1 = tween1.slice();
            tween1.splice(i, 1);
            break;
          }
        }
      }
      schedule.tween = tween1;
    };
  }
  function tweenFunction(id2, name, value) {
    var tween0, tween1;
    if (typeof value !== "function") throw new Error();
    return function() {
      var schedule = set2(this, id2), tween = schedule.tween;
      if (tween !== tween0) {
        tween1 = (tween0 = tween).slice();
        for (var t = { name, value }, i = 0, n = tween1.length; i < n; ++i) {
          if (tween1[i].name === name) {
            tween1[i] = t;
            break;
          }
        }
        if (i === n) tween1.push(t);
      }
      schedule.tween = tween1;
    };
  }
  function tween_default(name, value) {
    var id2 = this._id;
    name += "";
    if (arguments.length < 2) {
      var tween = get2(this.node(), id2).tween;
      for (var i = 0, n = tween.length, t; i < n; ++i) {
        if ((t = tween[i]).name === name) {
          return t.value;
        }
      }
      return null;
    }
    return this.each((value == null ? tweenRemove : tweenFunction)(id2, name, value));
  }
  function tweenValue(transition2, name, value) {
    var id2 = transition2._id;
    transition2.each(function() {
      var schedule = set2(this, id2);
      (schedule.value || (schedule.value = {}))[name] = value.apply(this, arguments);
    });
    return function(node) {
      return get2(node, id2).value[name];
    };
  }

  // node_modules/d3-transition/src/transition/interpolate.js
  function interpolate_default(a, b) {
    var c;
    return (typeof b === "number" ? number_default : b instanceof color ? rgb_default : (c = color(b)) ? (b = c, rgb_default) : string_default)(a, b);
  }

  // node_modules/d3-transition/src/transition/attr.js
  function attrRemove2(name) {
    return function() {
      this.removeAttribute(name);
    };
  }
  function attrRemoveNS2(fullname) {
    return function() {
      this.removeAttributeNS(fullname.space, fullname.local);
    };
  }
  function attrConstant2(name, interpolate, value1) {
    var string00, string1 = value1 + "", interpolate0;
    return function() {
      var string0 = this.getAttribute(name);
      return string0 === string1 ? null : string0 === string00 ? interpolate0 : interpolate0 = interpolate(string00 = string0, value1);
    };
  }
  function attrConstantNS2(fullname, interpolate, value1) {
    var string00, string1 = value1 + "", interpolate0;
    return function() {
      var string0 = this.getAttributeNS(fullname.space, fullname.local);
      return string0 === string1 ? null : string0 === string00 ? interpolate0 : interpolate0 = interpolate(string00 = string0, value1);
    };
  }
  function attrFunction2(name, interpolate, value) {
    var string00, string10, interpolate0;
    return function() {
      var string0, value1 = value(this), string1;
      if (value1 == null) return void this.removeAttribute(name);
      string0 = this.getAttribute(name);
      string1 = value1 + "";
      return string0 === string1 ? null : string0 === string00 && string1 === string10 ? interpolate0 : (string10 = string1, interpolate0 = interpolate(string00 = string0, value1));
    };
  }
  function attrFunctionNS2(fullname, interpolate, value) {
    var string00, string10, interpolate0;
    return function() {
      var string0, value1 = value(this), string1;
      if (value1 == null) return void this.removeAttributeNS(fullname.space, fullname.local);
      string0 = this.getAttributeNS(fullname.space, fullname.local);
      string1 = value1 + "";
      return string0 === string1 ? null : string0 === string00 && string1 === string10 ? interpolate0 : (string10 = string1, interpolate0 = interpolate(string00 = string0, value1));
    };
  }
  function attr_default2(name, value) {
    var fullname = namespace_default(name), i = fullname === "transform" ? interpolateTransformSvg : interpolate_default;
    return this.attrTween(name, typeof value === "function" ? (fullname.local ? attrFunctionNS2 : attrFunction2)(fullname, i, tweenValue(this, "attr." + name, value)) : value == null ? (fullname.local ? attrRemoveNS2 : attrRemove2)(fullname) : (fullname.local ? attrConstantNS2 : attrConstant2)(fullname, i, value));
  }

  // node_modules/d3-transition/src/transition/attrTween.js
  function attrInterpolate(name, i) {
    return function(t) {
      this.setAttribute(name, i.call(this, t));
    };
  }
  function attrInterpolateNS(fullname, i) {
    return function(t) {
      this.setAttributeNS(fullname.space, fullname.local, i.call(this, t));
    };
  }
  function attrTweenNS(fullname, value) {
    var t0, i0;
    function tween() {
      var i = value.apply(this, arguments);
      if (i !== i0) t0 = (i0 = i) && attrInterpolateNS(fullname, i);
      return t0;
    }
    tween._value = value;
    return tween;
  }
  function attrTween(name, value) {
    var t0, i0;
    function tween() {
      var i = value.apply(this, arguments);
      if (i !== i0) t0 = (i0 = i) && attrInterpolate(name, i);
      return t0;
    }
    tween._value = value;
    return tween;
  }
  function attrTween_default(name, value) {
    var key = "attr." + name;
    if (arguments.length < 2) return (key = this.tween(key)) && key._value;
    if (value == null) return this.tween(key, null);
    if (typeof value !== "function") throw new Error();
    var fullname = namespace_default(name);
    return this.tween(key, (fullname.local ? attrTweenNS : attrTween)(fullname, value));
  }

  // node_modules/d3-transition/src/transition/delay.js
  function delayFunction(id2, value) {
    return function() {
      init(this, id2).delay = +value.apply(this, arguments);
    };
  }
  function delayConstant(id2, value) {
    return value = +value, function() {
      init(this, id2).delay = value;
    };
  }
  function delay_default(value) {
    var id2 = this._id;
    return arguments.length ? this.each((typeof value === "function" ? delayFunction : delayConstant)(id2, value)) : get2(this.node(), id2).delay;
  }

  // node_modules/d3-transition/src/transition/duration.js
  function durationFunction(id2, value) {
    return function() {
      set2(this, id2).duration = +value.apply(this, arguments);
    };
  }
  function durationConstant(id2, value) {
    return value = +value, function() {
      set2(this, id2).duration = value;
    };
  }
  function duration_default(value) {
    var id2 = this._id;
    return arguments.length ? this.each((typeof value === "function" ? durationFunction : durationConstant)(id2, value)) : get2(this.node(), id2).duration;
  }

  // node_modules/d3-transition/src/transition/ease.js
  function easeConstant(id2, value) {
    if (typeof value !== "function") throw new Error();
    return function() {
      set2(this, id2).ease = value;
    };
  }
  function ease_default(value) {
    var id2 = this._id;
    return arguments.length ? this.each(easeConstant(id2, value)) : get2(this.node(), id2).ease;
  }

  // node_modules/d3-transition/src/transition/easeVarying.js
  function easeVarying(id2, value) {
    return function() {
      var v = value.apply(this, arguments);
      if (typeof v !== "function") throw new Error();
      set2(this, id2).ease = v;
    };
  }
  function easeVarying_default(value) {
    if (typeof value !== "function") throw new Error();
    return this.each(easeVarying(this._id, value));
  }

  // node_modules/d3-transition/src/transition/filter.js
  function filter_default2(match) {
    if (typeof match !== "function") match = matcher_default(match);
    for (var groups = this._groups, m = groups.length, subgroups = new Array(m), j = 0; j < m; ++j) {
      for (var group = groups[j], n = group.length, subgroup = subgroups[j] = [], node, i = 0; i < n; ++i) {
        if ((node = group[i]) && match.call(node, node.__data__, i, group)) {
          subgroup.push(node);
        }
      }
    }
    return new Transition(subgroups, this._parents, this._name, this._id);
  }

  // node_modules/d3-transition/src/transition/merge.js
  function merge_default2(transition2) {
    if (transition2._id !== this._id) throw new Error();
    for (var groups0 = this._groups, groups1 = transition2._groups, m0 = groups0.length, m1 = groups1.length, m = Math.min(m0, m1), merges = new Array(m0), j = 0; j < m; ++j) {
      for (var group0 = groups0[j], group1 = groups1[j], n = group0.length, merge = merges[j] = new Array(n), node, i = 0; i < n; ++i) {
        if (node = group0[i] || group1[i]) {
          merge[i] = node;
        }
      }
    }
    for (; j < m0; ++j) {
      merges[j] = groups0[j];
    }
    return new Transition(merges, this._parents, this._name, this._id);
  }

  // node_modules/d3-transition/src/transition/on.js
  function start(name) {
    return (name + "").trim().split(/^|\s+/).every(function(t) {
      var i = t.indexOf(".");
      if (i >= 0) t = t.slice(0, i);
      return !t || t === "start";
    });
  }
  function onFunction(id2, name, listener) {
    var on0, on1, sit = start(name) ? init : set2;
    return function() {
      var schedule = sit(this, id2), on = schedule.on;
      if (on !== on0) (on1 = (on0 = on).copy()).on(name, listener);
      schedule.on = on1;
    };
  }
  function on_default2(name, listener) {
    var id2 = this._id;
    return arguments.length < 2 ? get2(this.node(), id2).on.on(name) : this.each(onFunction(id2, name, listener));
  }

  // node_modules/d3-transition/src/transition/remove.js
  function removeFunction(id2) {
    return function() {
      var parent = this.parentNode;
      for (var i in this.__transition) if (+i !== id2) return;
      if (parent) parent.removeChild(this);
    };
  }
  function remove_default2() {
    return this.on("end.remove", removeFunction(this._id));
  }

  // node_modules/d3-transition/src/transition/select.js
  function select_default3(select) {
    var name = this._name, id2 = this._id;
    if (typeof select !== "function") select = selector_default(select);
    for (var groups = this._groups, m = groups.length, subgroups = new Array(m), j = 0; j < m; ++j) {
      for (var group = groups[j], n = group.length, subgroup = subgroups[j] = new Array(n), node, subnode, i = 0; i < n; ++i) {
        if ((node = group[i]) && (subnode = select.call(node, node.__data__, i, group))) {
          if ("__data__" in node) subnode.__data__ = node.__data__;
          subgroup[i] = subnode;
          schedule_default(subgroup[i], name, id2, i, subgroup, get2(node, id2));
        }
      }
    }
    return new Transition(subgroups, this._parents, name, id2);
  }

  // node_modules/d3-transition/src/transition/selectAll.js
  function selectAll_default2(select) {
    var name = this._name, id2 = this._id;
    if (typeof select !== "function") select = selectorAll_default(select);
    for (var groups = this._groups, m = groups.length, subgroups = [], parents = [], j = 0; j < m; ++j) {
      for (var group = groups[j], n = group.length, node, i = 0; i < n; ++i) {
        if (node = group[i]) {
          for (var children2 = select.call(node, node.__data__, i, group), child, inherit2 = get2(node, id2), k = 0, l = children2.length; k < l; ++k) {
            if (child = children2[k]) {
              schedule_default(child, name, id2, k, children2, inherit2);
            }
          }
          subgroups.push(children2);
          parents.push(node);
        }
      }
    }
    return new Transition(subgroups, parents, name, id2);
  }

  // node_modules/d3-transition/src/transition/selection.js
  var Selection2 = selection_default.prototype.constructor;
  function selection_default2() {
    return new Selection2(this._groups, this._parents);
  }

  // node_modules/d3-transition/src/transition/style.js
  function styleNull(name, interpolate) {
    var string00, string10, interpolate0;
    return function() {
      var string0 = styleValue(this, name), string1 = (this.style.removeProperty(name), styleValue(this, name));
      return string0 === string1 ? null : string0 === string00 && string1 === string10 ? interpolate0 : interpolate0 = interpolate(string00 = string0, string10 = string1);
    };
  }
  function styleRemove2(name) {
    return function() {
      this.style.removeProperty(name);
    };
  }
  function styleConstant2(name, interpolate, value1) {
    var string00, string1 = value1 + "", interpolate0;
    return function() {
      var string0 = styleValue(this, name);
      return string0 === string1 ? null : string0 === string00 ? interpolate0 : interpolate0 = interpolate(string00 = string0, value1);
    };
  }
  function styleFunction2(name, interpolate, value) {
    var string00, string10, interpolate0;
    return function() {
      var string0 = styleValue(this, name), value1 = value(this), string1 = value1 + "";
      if (value1 == null) string1 = value1 = (this.style.removeProperty(name), styleValue(this, name));
      return string0 === string1 ? null : string0 === string00 && string1 === string10 ? interpolate0 : (string10 = string1, interpolate0 = interpolate(string00 = string0, value1));
    };
  }
  function styleMaybeRemove(id2, name) {
    var on0, on1, listener0, key = "style." + name, event = "end." + key, remove2;
    return function() {
      var schedule = set2(this, id2), on = schedule.on, listener = schedule.value[key] == null ? remove2 || (remove2 = styleRemove2(name)) : void 0;
      if (on !== on0 || listener0 !== listener) (on1 = (on0 = on).copy()).on(event, listener0 = listener);
      schedule.on = on1;
    };
  }
  function style_default2(name, value, priority) {
    var i = (name += "") === "transform" ? interpolateTransformCss : interpolate_default;
    return value == null ? this.styleTween(name, styleNull(name, i)).on("end.style." + name, styleRemove2(name)) : typeof value === "function" ? this.styleTween(name, styleFunction2(name, i, tweenValue(this, "style." + name, value))).each(styleMaybeRemove(this._id, name)) : this.styleTween(name, styleConstant2(name, i, value), priority).on("end.style." + name, null);
  }

  // node_modules/d3-transition/src/transition/styleTween.js
  function styleInterpolate(name, i, priority) {
    return function(t) {
      this.style.setProperty(name, i.call(this, t), priority);
    };
  }
  function styleTween(name, value, priority) {
    var t, i0;
    function tween() {
      var i = value.apply(this, arguments);
      if (i !== i0) t = (i0 = i) && styleInterpolate(name, i, priority);
      return t;
    }
    tween._value = value;
    return tween;
  }
  function styleTween_default(name, value, priority) {
    var key = "style." + (name += "");
    if (arguments.length < 2) return (key = this.tween(key)) && key._value;
    if (value == null) return this.tween(key, null);
    if (typeof value !== "function") throw new Error();
    return this.tween(key, styleTween(name, value, priority == null ? "" : priority));
  }

  // node_modules/d3-transition/src/transition/text.js
  function textConstant2(value) {
    return function() {
      this.textContent = value;
    };
  }
  function textFunction2(value) {
    return function() {
      var value1 = value(this);
      this.textContent = value1 == null ? "" : value1;
    };
  }
  function text_default2(value) {
    return this.tween("text", typeof value === "function" ? textFunction2(tweenValue(this, "text", value)) : textConstant2(value == null ? "" : value + ""));
  }

  // node_modules/d3-transition/src/transition/textTween.js
  function textInterpolate(i) {
    return function(t) {
      this.textContent = i.call(this, t);
    };
  }
  function textTween(value) {
    var t0, i0;
    function tween() {
      var i = value.apply(this, arguments);
      if (i !== i0) t0 = (i0 = i) && textInterpolate(i);
      return t0;
    }
    tween._value = value;
    return tween;
  }
  function textTween_default(value) {
    var key = "text";
    if (arguments.length < 1) return (key = this.tween(key)) && key._value;
    if (value == null) return this.tween(key, null);
    if (typeof value !== "function") throw new Error();
    return this.tween(key, textTween(value));
  }

  // node_modules/d3-transition/src/transition/transition.js
  function transition_default() {
    var name = this._name, id0 = this._id, id1 = newId();
    for (var groups = this._groups, m = groups.length, j = 0; j < m; ++j) {
      for (var group = groups[j], n = group.length, node, i = 0; i < n; ++i) {
        if (node = group[i]) {
          var inherit2 = get2(node, id0);
          schedule_default(node, name, id1, i, group, {
            time: inherit2.time + inherit2.delay + inherit2.duration,
            delay: 0,
            duration: inherit2.duration,
            ease: inherit2.ease
          });
        }
      }
    }
    return new Transition(groups, this._parents, name, id1);
  }

  // node_modules/d3-transition/src/transition/end.js
  function end_default() {
    var on0, on1, that = this, id2 = that._id, size = that.size();
    return new Promise(function(resolve, reject) {
      var cancel = { value: reject }, end = { value: function() {
        if (--size === 0) resolve();
      } };
      that.each(function() {
        var schedule = set2(this, id2), on = schedule.on;
        if (on !== on0) {
          on1 = (on0 = on).copy();
          on1._.cancel.push(cancel);
          on1._.interrupt.push(cancel);
          on1._.end.push(end);
        }
        schedule.on = on1;
      });
      if (size === 0) resolve();
    });
  }

  // node_modules/d3-transition/src/transition/index.js
  var id = 0;
  function Transition(groups, parents, name, id2) {
    this._groups = groups;
    this._parents = parents;
    this._name = name;
    this._id = id2;
  }
  function transition(name) {
    return selection_default().transition(name);
  }
  function newId() {
    return ++id;
  }
  var selection_prototype = selection_default.prototype;
  Transition.prototype = transition.prototype = {
    constructor: Transition,
    select: select_default3,
    selectAll: selectAll_default2,
    selectChild: selection_prototype.selectChild,
    selectChildren: selection_prototype.selectChildren,
    filter: filter_default2,
    merge: merge_default2,
    selection: selection_default2,
    transition: transition_default,
    call: selection_prototype.call,
    nodes: selection_prototype.nodes,
    node: selection_prototype.node,
    size: selection_prototype.size,
    empty: selection_prototype.empty,
    each: selection_prototype.each,
    on: on_default2,
    attr: attr_default2,
    attrTween: attrTween_default,
    style: style_default2,
    styleTween: styleTween_default,
    text: text_default2,
    textTween: textTween_default,
    remove: remove_default2,
    tween: tween_default,
    delay: delay_default,
    duration: duration_default,
    ease: ease_default,
    easeVarying: easeVarying_default,
    end: end_default,
    [Symbol.iterator]: selection_prototype[Symbol.iterator]
  };

  // node_modules/d3-ease/src/cubic.js
  function cubicInOut(t) {
    return ((t *= 2) <= 1 ? t * t * t : (t -= 2) * t * t + 2) / 2;
  }

  // node_modules/d3-transition/src/selection/transition.js
  var defaultTiming = {
    time: null,
    // Set on use.
    delay: 0,
    duration: 250,
    ease: cubicInOut
  };
  function inherit(node, id2) {
    var timing;
    while (!(timing = node.__transition) || !(timing = timing[id2])) {
      if (!(node = node.parentNode)) {
        throw new Error(`transition ${id2} not found`);
      }
    }
    return timing;
  }
  function transition_default2(name) {
    var id2, timing;
    if (name instanceof Transition) {
      id2 = name._id, name = name._name;
    } else {
      id2 = newId(), (timing = defaultTiming).time = now(), name = name == null ? null : name + "";
    }
    for (var groups = this._groups, m = groups.length, j = 0; j < m; ++j) {
      for (var group = groups[j], n = group.length, node, i = 0; i < n; ++i) {
        if (node = group[i]) {
          schedule_default(node, name, id2, i, group, timing || inherit(node, id2));
        }
      }
    }
    return new Transition(groups, this._parents, name, id2);
  }

  // node_modules/d3-transition/src/selection/index.js
  selection_default.prototype.interrupt = interrupt_default2;
  selection_default.prototype.transition = transition_default2;

  // node_modules/d3-zoom/src/constant.js
  var constant_default3 = (x) => () => x;

  // node_modules/d3-zoom/src/event.js
  function ZoomEvent(type, {
    sourceEvent,
    target,
    transform: transform2,
    dispatch: dispatch2
  }) {
    Object.defineProperties(this, {
      type: { value: type, enumerable: true, configurable: true },
      sourceEvent: { value: sourceEvent, enumerable: true, configurable: true },
      target: { value: target, enumerable: true, configurable: true },
      transform: { value: transform2, enumerable: true, configurable: true },
      _: { value: dispatch2 }
    });
  }

  // node_modules/d3-zoom/src/transform.js
  function Transform(k, x, y) {
    this.k = k;
    this.x = x;
    this.y = y;
  }
  Transform.prototype = {
    constructor: Transform,
    scale: function(k) {
      return k === 1 ? this : new Transform(this.k * k, this.x, this.y);
    },
    translate: function(x, y) {
      return x === 0 & y === 0 ? this : new Transform(this.k, this.x + this.k * x, this.y + this.k * y);
    },
    apply: function(point) {
      return [point[0] * this.k + this.x, point[1] * this.k + this.y];
    },
    applyX: function(x) {
      return x * this.k + this.x;
    },
    applyY: function(y) {
      return y * this.k + this.y;
    },
    invert: function(location) {
      return [(location[0] - this.x) / this.k, (location[1] - this.y) / this.k];
    },
    invertX: function(x) {
      return (x - this.x) / this.k;
    },
    invertY: function(y) {
      return (y - this.y) / this.k;
    },
    rescaleX: function(x) {
      return x.copy().domain(x.range().map(this.invertX, this).map(x.invert, x));
    },
    rescaleY: function(y) {
      return y.copy().domain(y.range().map(this.invertY, this).map(y.invert, y));
    },
    toString: function() {
      return "translate(" + this.x + "," + this.y + ") scale(" + this.k + ")";
    }
  };
  var identity2 = new Transform(1, 0, 0);
  transform.prototype = Transform.prototype;
  function transform(node) {
    while (!node.__zoom) if (!(node = node.parentNode)) return identity2;
    return node.__zoom;
  }

  // node_modules/d3-zoom/src/noevent.js
  function nopropagation(event) {
    event.stopImmediatePropagation();
  }
  function noevent_default2(event) {
    event.preventDefault();
    event.stopImmediatePropagation();
  }

  // node_modules/d3-zoom/src/zoom.js
  function defaultFilter(event) {
    return (!event.ctrlKey || event.type === "wheel") && !event.button;
  }
  function defaultExtent() {
    var e = this;
    if (e instanceof SVGElement) {
      e = e.ownerSVGElement || e;
      if (e.hasAttribute("viewBox")) {
        e = e.viewBox.baseVal;
        return [[e.x, e.y], [e.x + e.width, e.y + e.height]];
      }
      return [[0, 0], [e.width.baseVal.value, e.height.baseVal.value]];
    }
    return [[0, 0], [e.clientWidth, e.clientHeight]];
  }
  function defaultTransform() {
    return this.__zoom || identity2;
  }
  function defaultWheelDelta(event) {
    return -event.deltaY * (event.deltaMode === 1 ? 0.05 : event.deltaMode ? 1 : 2e-3) * (event.ctrlKey ? 10 : 1);
  }
  function defaultTouchable() {
    return navigator.maxTouchPoints || "ontouchstart" in this;
  }
  function defaultConstrain(transform2, extent, translateExtent) {
    var dx0 = transform2.invertX(extent[0][0]) - translateExtent[0][0], dx1 = transform2.invertX(extent[1][0]) - translateExtent[1][0], dy0 = transform2.invertY(extent[0][1]) - translateExtent[0][1], dy1 = transform2.invertY(extent[1][1]) - translateExtent[1][1];
    return transform2.translate(
      dx1 > dx0 ? (dx0 + dx1) / 2 : Math.min(0, dx0) || Math.max(0, dx1),
      dy1 > dy0 ? (dy0 + dy1) / 2 : Math.min(0, dy0) || Math.max(0, dy1)
    );
  }
  function zoom_default2() {
    var filter2 = defaultFilter, extent = defaultExtent, constrain = defaultConstrain, wheelDelta = defaultWheelDelta, touchable = defaultTouchable, scaleExtent = [0, Infinity], translateExtent = [[-Infinity, -Infinity], [Infinity, Infinity]], duration = 250, interpolate = zoom_default, listeners = dispatch_default2("start", "zoom", "end"), touchstarting, touchfirst, touchending, touchDelay = 500, wheelDelay = 150, clickDistance2 = 0, tapDistance = 10;
    function zoom(selection2) {
      selection2.property("__zoom", defaultTransform).on("wheel.zoom", wheeled, { passive: false }).on("mousedown.zoom", mousedowned).on("dblclick.zoom", dblclicked).filter(touchable).on("touchstart.zoom", touchstarted).on("touchmove.zoom", touchmoved).on("touchend.zoom touchcancel.zoom", touchended).style("-webkit-tap-highlight-color", "rgba(0,0,0,0)");
    }
    zoom.transform = function(collection, transform2, point, event) {
      var selection2 = collection.selection ? collection.selection() : collection;
      selection2.property("__zoom", defaultTransform);
      if (collection !== selection2) {
        schedule(collection, transform2, point, event);
      } else {
        selection2.interrupt().each(function() {
          gesture(this, arguments).event(event).start().zoom(null, typeof transform2 === "function" ? transform2.apply(this, arguments) : transform2).end();
        });
      }
    };
    zoom.scaleBy = function(selection2, k, p, event) {
      zoom.scaleTo(selection2, function() {
        var k0 = this.__zoom.k, k1 = typeof k === "function" ? k.apply(this, arguments) : k;
        return k0 * k1;
      }, p, event);
    };
    zoom.scaleTo = function(selection2, k, p, event) {
      zoom.transform(selection2, function() {
        var e = extent.apply(this, arguments), t0 = this.__zoom, p0 = p == null ? centroid(e) : typeof p === "function" ? p.apply(this, arguments) : p, p1 = t0.invert(p0), k1 = typeof k === "function" ? k.apply(this, arguments) : k;
        return constrain(translate(scale(t0, k1), p0, p1), e, translateExtent);
      }, p, event);
    };
    zoom.translateBy = function(selection2, x, y, event) {
      zoom.transform(selection2, function() {
        return constrain(this.__zoom.translate(
          typeof x === "function" ? x.apply(this, arguments) : x,
          typeof y === "function" ? y.apply(this, arguments) : y
        ), extent.apply(this, arguments), translateExtent);
      }, null, event);
    };
    zoom.translateTo = function(selection2, x, y, p, event) {
      zoom.transform(selection2, function() {
        var e = extent.apply(this, arguments), t = this.__zoom, p0 = p == null ? centroid(e) : typeof p === "function" ? p.apply(this, arguments) : p;
        return constrain(identity2.translate(p0[0], p0[1]).scale(t.k).translate(
          typeof x === "function" ? -x.apply(this, arguments) : -x,
          typeof y === "function" ? -y.apply(this, arguments) : -y
        ), e, translateExtent);
      }, p, event);
    };
    function scale(transform2, k) {
      k = Math.max(scaleExtent[0], Math.min(scaleExtent[1], k));
      return k === transform2.k ? transform2 : new Transform(k, transform2.x, transform2.y);
    }
    function translate(transform2, p0, p1) {
      var x = p0[0] - p1[0] * transform2.k, y = p0[1] - p1[1] * transform2.k;
      return x === transform2.x && y === transform2.y ? transform2 : new Transform(transform2.k, x, y);
    }
    function centroid(extent2) {
      return [(+extent2[0][0] + +extent2[1][0]) / 2, (+extent2[0][1] + +extent2[1][1]) / 2];
    }
    function schedule(transition2, transform2, point, event) {
      transition2.on("start.zoom", function() {
        gesture(this, arguments).event(event).start();
      }).on("interrupt.zoom end.zoom", function() {
        gesture(this, arguments).event(event).end();
      }).tween("zoom", function() {
        var that = this, args = arguments, g = gesture(that, args).event(event), e = extent.apply(that, args), p = point == null ? centroid(e) : typeof point === "function" ? point.apply(that, args) : point, w = Math.max(e[1][0] - e[0][0], e[1][1] - e[0][1]), a = that.__zoom, b = typeof transform2 === "function" ? transform2.apply(that, args) : transform2, i = interpolate(a.invert(p).concat(w / a.k), b.invert(p).concat(w / b.k));
        return function(t) {
          if (t === 1) t = b;
          else {
            var l = i(t), k = w / l[2];
            t = new Transform(k, p[0] - l[0] * k, p[1] - l[1] * k);
          }
          g.zoom(null, t);
        };
      });
    }
    function gesture(that, args, clean) {
      return !clean && that.__zooming || new Gesture(that, args);
    }
    function Gesture(that, args) {
      this.that = that;
      this.args = args;
      this.active = 0;
      this.sourceEvent = null;
      this.extent = extent.apply(that, args);
      this.taps = 0;
    }
    Gesture.prototype = {
      event: function(event) {
        if (event) this.sourceEvent = event;
        return this;
      },
      start: function() {
        if (++this.active === 1) {
          this.that.__zooming = this;
          this.emit("start");
        }
        return this;
      },
      zoom: function(key, transform2) {
        if (this.mouse && key !== "mouse") this.mouse[1] = transform2.invert(this.mouse[0]);
        if (this.touch0 && key !== "touch") this.touch0[1] = transform2.invert(this.touch0[0]);
        if (this.touch1 && key !== "touch") this.touch1[1] = transform2.invert(this.touch1[0]);
        this.that.__zoom = transform2;
        this.emit("zoom");
        return this;
      },
      end: function() {
        if (--this.active === 0) {
          delete this.that.__zooming;
          this.emit("end");
        }
        return this;
      },
      emit: function(type) {
        var d = select_default2(this.that).datum();
        listeners.call(
          type,
          this.that,
          new ZoomEvent(type, {
            sourceEvent: this.sourceEvent,
            target: zoom,
            type,
            transform: this.that.__zoom,
            dispatch: listeners
          }),
          d
        );
      }
    };
    function wheeled(event, ...args) {
      if (!filter2.apply(this, arguments)) return;
      var g = gesture(this, args).event(event), t = this.__zoom, k = Math.max(scaleExtent[0], Math.min(scaleExtent[1], t.k * Math.pow(2, wheelDelta.apply(this, arguments)))), p = pointer_default(event);
      if (g.wheel) {
        if (g.mouse[0][0] !== p[0] || g.mouse[0][1] !== p[1]) {
          g.mouse[1] = t.invert(g.mouse[0] = p);
        }
        clearTimeout(g.wheel);
      } else if (t.k === k) return;
      else {
        g.mouse = [p, t.invert(p)];
        interrupt_default(this);
        g.start();
      }
      noevent_default2(event);
      g.wheel = setTimeout(wheelidled, wheelDelay);
      g.zoom("mouse", constrain(translate(scale(t, k), g.mouse[0], g.mouse[1]), g.extent, translateExtent));
      function wheelidled() {
        g.wheel = null;
        g.end();
      }
    }
    function mousedowned(event, ...args) {
      if (touchending || !filter2.apply(this, arguments)) return;
      var currentTarget = event.currentTarget, g = gesture(this, args, true).event(event), v = select_default2(event.view).on("mousemove.zoom", mousemoved, true).on("mouseup.zoom", mouseupped, true), p = pointer_default(event, currentTarget), x0 = event.clientX, y0 = event.clientY;
      nodrag_default(event.view);
      nopropagation(event);
      g.mouse = [p, this.__zoom.invert(p)];
      interrupt_default(this);
      g.start();
      function mousemoved(event2) {
        noevent_default2(event2);
        if (!g.moved) {
          var dx = event2.clientX - x0, dy = event2.clientY - y0;
          g.moved = dx * dx + dy * dy > clickDistance2;
        }
        g.event(event2).zoom("mouse", constrain(translate(g.that.__zoom, g.mouse[0] = pointer_default(event2, currentTarget), g.mouse[1]), g.extent, translateExtent));
      }
      function mouseupped(event2) {
        v.on("mousemove.zoom mouseup.zoom", null);
        yesdrag(event2.view, g.moved);
        noevent_default2(event2);
        g.event(event2).end();
      }
    }
    function dblclicked(event, ...args) {
      if (!filter2.apply(this, arguments)) return;
      var t0 = this.__zoom, p0 = pointer_default(event.changedTouches ? event.changedTouches[0] : event, this), p1 = t0.invert(p0), k1 = t0.k * (event.shiftKey ? 0.5 : 2), t1 = constrain(translate(scale(t0, k1), p0, p1), extent.apply(this, args), translateExtent);
      noevent_default2(event);
      if (duration > 0) select_default2(this).transition().duration(duration).call(schedule, t1, p0, event);
      else select_default2(this).call(zoom.transform, t1, p0, event);
    }
    function touchstarted(event, ...args) {
      if (!filter2.apply(this, arguments)) return;
      var touches = event.touches, n = touches.length, g = gesture(this, args, event.changedTouches.length === n).event(event), started, i, t, p;
      nopropagation(event);
      for (i = 0; i < n; ++i) {
        t = touches[i], p = pointer_default(t, this);
        p = [p, this.__zoom.invert(p), t.identifier];
        if (!g.touch0) g.touch0 = p, started = true, g.taps = 1 + !!touchstarting;
        else if (!g.touch1 && g.touch0[2] !== p[2]) g.touch1 = p, g.taps = 0;
      }
      if (touchstarting) touchstarting = clearTimeout(touchstarting);
      if (started) {
        if (g.taps < 2) touchfirst = p[0], touchstarting = setTimeout(function() {
          touchstarting = null;
        }, touchDelay);
        interrupt_default(this);
        g.start();
      }
    }
    function touchmoved(event, ...args) {
      if (!this.__zooming) return;
      var g = gesture(this, args).event(event), touches = event.changedTouches, n = touches.length, i, t, p, l;
      noevent_default2(event);
      for (i = 0; i < n; ++i) {
        t = touches[i], p = pointer_default(t, this);
        if (g.touch0 && g.touch0[2] === t.identifier) g.touch0[0] = p;
        else if (g.touch1 && g.touch1[2] === t.identifier) g.touch1[0] = p;
      }
      t = g.that.__zoom;
      if (g.touch1) {
        var p0 = g.touch0[0], l0 = g.touch0[1], p1 = g.touch1[0], l1 = g.touch1[1], dp = (dp = p1[0] - p0[0]) * dp + (dp = p1[1] - p0[1]) * dp, dl = (dl = l1[0] - l0[0]) * dl + (dl = l1[1] - l0[1]) * dl;
        t = scale(t, Math.sqrt(dp / dl));
        p = [(p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2];
        l = [(l0[0] + l1[0]) / 2, (l0[1] + l1[1]) / 2];
      } else if (g.touch0) p = g.touch0[0], l = g.touch0[1];
      else return;
      g.zoom("touch", constrain(translate(t, p, l), g.extent, translateExtent));
    }
    function touchended(event, ...args) {
      if (!this.__zooming) return;
      var g = gesture(this, args).event(event), touches = event.changedTouches, n = touches.length, i, t;
      nopropagation(event);
      if (touchending) clearTimeout(touchending);
      touchending = setTimeout(function() {
        touchending = null;
      }, touchDelay);
      for (i = 0; i < n; ++i) {
        t = touches[i];
        if (g.touch0 && g.touch0[2] === t.identifier) delete g.touch0;
        else if (g.touch1 && g.touch1[2] === t.identifier) delete g.touch1;
      }
      if (g.touch1 && !g.touch0) g.touch0 = g.touch1, delete g.touch1;
      if (g.touch0) g.touch0[1] = this.__zoom.invert(g.touch0[0]);
      else {
        g.end();
        if (g.taps === 2) {
          t = pointer_default(t, this);
          if (Math.hypot(touchfirst[0] - t[0], touchfirst[1] - t[1]) < tapDistance) {
            var p = select_default2(this).on("dblclick.zoom");
            if (p) p.apply(this, arguments);
          }
        }
      }
    }
    zoom.wheelDelta = function(_) {
      return arguments.length ? (wheelDelta = typeof _ === "function" ? _ : constant_default3(+_), zoom) : wheelDelta;
    };
    zoom.filter = function(_) {
      return arguments.length ? (filter2 = typeof _ === "function" ? _ : constant_default3(!!_), zoom) : filter2;
    };
    zoom.touchable = function(_) {
      return arguments.length ? (touchable = typeof _ === "function" ? _ : constant_default3(!!_), zoom) : touchable;
    };
    zoom.extent = function(_) {
      return arguments.length ? (extent = typeof _ === "function" ? _ : constant_default3([[+_[0][0], +_[0][1]], [+_[1][0], +_[1][1]]]), zoom) : extent;
    };
    zoom.scaleExtent = function(_) {
      return arguments.length ? (scaleExtent[0] = +_[0], scaleExtent[1] = +_[1], zoom) : [scaleExtent[0], scaleExtent[1]];
    };
    zoom.translateExtent = function(_) {
      return arguments.length ? (translateExtent[0][0] = +_[0][0], translateExtent[1][0] = +_[1][0], translateExtent[0][1] = +_[0][1], translateExtent[1][1] = +_[1][1], zoom) : [[translateExtent[0][0], translateExtent[0][1]], [translateExtent[1][0], translateExtent[1][1]]];
    };
    zoom.constrain = function(_) {
      return arguments.length ? (constrain = _, zoom) : constrain;
    };
    zoom.duration = function(_) {
      return arguments.length ? (duration = +_, zoom) : duration;
    };
    zoom.interpolate = function(_) {
      return arguments.length ? (interpolate = _, zoom) : interpolate;
    };
    zoom.on = function() {
      var value = listeners.on.apply(listeners, arguments);
      return value === listeners ? zoom : value;
    };
    zoom.clickDistance = function(_) {
      return arguments.length ? (clickDistance2 = (_ = +_) * _, zoom) : Math.sqrt(clickDistance2);
    };
    zoom.tapDistance = function(_) {
      return arguments.length ? (tapDistance = +_, zoom) : tapDistance;
    };
    return zoom;
  }

  // webview/tree/render.ts
  var EDGE_ARROW_DEFAULT_MARKER_ID = "tree-edge-arrow-default";
  var EDGE_ARROW_ACTIVE_MARKER_ID = "tree-edge-arrow-active";
  var DEFAULT_ZOOM_MIN_SCALE = 0.68;
  var DEFAULT_ZOOM_MAX_SCALE = 1.55;
  var DEFAULT_WHEEL_SENSITIVITY = 1;
  var ZOOM_WHEEL_DELTA_BASE_MIN = -0.08;
  var ZOOM_WHEEL_DELTA_BASE_MAX = 0.08;
  var MODULE_NODE_RADIUS = 18;
  var DEFAULT_NODE_RADIUS = 16;
  function clampNumber2(value, minimum, maximum, fallback) {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) {
      return fallback;
    }
    return Math.min(maximum, Math.max(minimum, parsed));
  }
  function normalizeViewSettings2(settings) {
    const zoomMinScale = clampNumber2(settings?.zoomMinScale, 0.2, 3, DEFAULT_ZOOM_MIN_SCALE);
    const zoomMaxScale = clampNumber2(settings?.zoomMaxScale, zoomMinScale, 5, DEFAULT_ZOOM_MAX_SCALE);
    return {
      zoomMinScale,
      zoomMaxScale,
      wheelSensitivity: clampNumber2(settings?.wheelSensitivity, 0.25, 3, DEFAULT_WHEEL_SENSITIVITY),
      inspectorWidth: Number.isFinite(Number(settings?.inspectorWidth)) ? Number(settings?.inspectorWidth) : 338,
      inspectorRailWidth: Number.isFinite(Number(settings?.inspectorRailWidth)) ? Number(settings?.inspectorRailWidth) : 42
    };
  }
  function shortText(value, maxLength) {
    if (value.length <= maxLength) {
      return value;
    }
    return `${value.slice(0, Math.max(0, maxLength - 1))}…`;
  }
  function escapeHtml(value) {
    return value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  function kindClass(kind) {
    if (kind.includes("root")) {
      return "node-root";
    }
    if (kind.includes("group")) {
      return "node-group";
    }
    if (kind.includes("module")) {
      return "node-module";
    }
    if (kind.includes("project")) {
      return "node-project";
    }
    if (kind.includes("config")) {
      return "node-config";
    }
    if (kind.includes("code")) {
      return "node-code";
    }
    if (kind.includes("evidence")) {
      return "node-evidence";
    }
    return "node-generic";
  }
  function compactNodeId(node) {
    const moduleName = String(node.moduleName || "").trim();
    const moduleRef = String(node.moduleRef || "").trim();
    if (moduleName && moduleRef) {
      return `${moduleName}.${moduleRef}`;
    }
    if (moduleRef) {
      return moduleRef;
    }
    if (node.label) {
      return node.label;
    }
    return node.id;
  }
  function nodeRadius(node) {
    return node.kind.includes("module") ? MODULE_NODE_RADIUS : DEFAULT_NODE_RADIUS;
  }
  function edgeEndpoints(fromNode, toNode) {
    const dx = toNode.x - fromNode.x;
    const dy = toNode.y - fromNode.y;
    const distance = Math.max(1, Math.hypot(dx, dy));
    const ux = dx / distance;
    const uy = dy / distance;
    const maxPad = Math.max(0, distance / 2 - 6);
    const startPad = Math.min(nodeRadius(fromNode) + 4, maxPad);
    const endPad = Math.min(nodeRadius(toNode) + 3, maxPad);
    return {
      startX: fromNode.x + ux * startPad,
      startY: fromNode.y + uy * startPad,
      endX: toNode.x - ux * endPad,
      endY: toNode.y - uy * endPad
    };
  }
  function edgePath(fromNode, toNode) {
    const points = edgeEndpoints(fromNode, toNode);
    const dx = points.endX - points.startX;
    const dy = points.endY - points.startY;
    const curve = Math.max(28, Math.min(92, Math.abs(dy) * 0.36));
    const sidePull = dx === 0 ? 0 : Math.sign(dx) * Math.max(20, Math.min(84, Math.abs(dx) * 0.22));
    const c1x = points.startX + sidePull;
    const c1y = points.startY + curve;
    const c2x = points.endX - sidePull;
    const c2y = points.endY - curve;
    return `M ${points.startX} ${points.startY} C ${c1x} ${c1y}, ${c2x} ${c2y}, ${points.endX} ${points.endY}`;
  }
  function sanitizeState(state, viewSettings) {
    return {
      selectedNodeId: String(state?.selectedNodeId || ""),
      focusMode: state?.focusMode === "upstream" || state?.focusMode === "downstream" ? state.focusMode : "all",
      searchQuery: String(state?.searchQuery || ""),
      inspectorPinned: state?.inspectorPinned === true,
      zoomScale: Number.isFinite(Number(state?.zoomScale)) ? Math.min(viewSettings.zoomMaxScale, Math.max(viewSettings.zoomMinScale, Number(state?.zoomScale))) : Math.min(viewSettings.zoomMaxScale, Math.max(viewSettings.zoomMinScale, 1)),
      zoomX: Number.isFinite(Number(state?.zoomX)) ? Number(state?.zoomX) : 0,
      zoomY: Number.isFinite(Number(state?.zoomY)) ? Number(state?.zoomY) : 0
    };
  }
  function computeNodeBounds(nodes) {
    if (!nodes.length) {
      return null;
    }
    let minX = Number.POSITIVE_INFINITY;
    let minY = Number.POSITIVE_INFINITY;
    let maxX = Number.NEGATIVE_INFINITY;
    let maxY = Number.NEGATIVE_INFINITY;
    for (const node of nodes) {
      minX = Math.min(minX, node.x - node.width / 2);
      minY = Math.min(minY, node.y - node.height / 2);
      maxX = Math.max(maxX, node.x + node.width / 2);
      maxY = Math.max(maxY, node.y + node.height / 2);
    }
    return { minX, minY, maxX, maxY };
  }
  function hoverList(items, emptyText, maxItems = 3) {
    if (!items.length) {
      return `<li class="hover-item">${escapeHtml(emptyText)}</li>`;
    }
    const visibleItems = items.slice(0, maxItems).map((item) => {
      const token = escapeHtml(item.token);
      const text = escapeHtml(item.text);
      return `<li class="hover-item">${token ? `<b>${token}</b> ` : ""}${text}</li>`;
    });
    if (items.length > maxItems) {
      visibleItems.push(`<li class="hover-item">还有 ${items.length - maxItems} 项</li>`);
    }
    return visibleItems.join("");
  }
  var TreeCanvasRenderer = class {
    constructor(elements, model, layout, viewSettings, callbacks) {
      this.elements = elements;
      this.model = model;
      this.layout = layout;
      this.viewSettings = normalizeViewSettings2(viewSettings);
      this.callbacks = callbacks;
      this.svgSelection = select_default2(elements.svgElement);
      this.viewportSelection = select_default2(elements.viewportElement);
      this.zoomBehavior = zoom_default2().scaleExtent([this.viewSettings.zoomMinScale, this.viewSettings.zoomMaxScale]).wheelDelta((event) => {
        const factor = (event.deltaMode === 1 ? 6e-3 : 9e-4) * this.viewSettings.wheelSensitivity;
        const delta = -event.deltaY * factor;
        const minDelta = ZOOM_WHEEL_DELTA_BASE_MIN * this.viewSettings.wheelSensitivity;
        const maxDelta = ZOOM_WHEEL_DELTA_BASE_MAX * this.viewSettings.wheelSensitivity;
        return Math.max(minDelta, Math.min(maxDelta, delta));
      }).on("zoom", (event) => {
        this.viewportSelection.attr("transform", event.transform.toString());
        this.elements.zoomChipElement.textContent = `${Math.round(event.transform.k * 100)}%`;
        this.hideHoverCard();
        this.callbacks.onStateChanged();
      });
      this.nodeElementById = /* @__PURE__ */ new Map();
      this.edgeElementById = /* @__PURE__ */ new Map();
      this.initialPositions = new Map(
        [...this.layout.nodes.entries()].map(([nodeId, node]) => [nodeId, { x: node.x, y: node.y }])
      );
      this.selectedNodeId = "";
      this.selectedEdgeId = "";
      this.hoveredNodeId = "";
      this.hoveredEdgeId = "";
      this.visibleNodeIds = /* @__PURE__ */ new Set();
      this.visibleEdgeIds = /* @__PURE__ */ new Set();
      this.geometryFrame = null;
    }
    mount(initialState) {
      this.svgSelection.call(this.zoomBehavior);
      this.ensureEdgeMarker();
      this.renderGroups();
      this.renderBands();
      this.renderEdges();
      this.renderNodes();
      this.elements.svgElement.setAttribute("viewBox", `0 0 ${this.layout.width} ${this.layout.height}`);
      this.elements.countChipElement.textContent = `Nodes ${this.model.nodes.length} / Edges ${this.model.edges.length}`;
      this.applyPersistedState(initialState);
    }
    applyFilter(result) {
      this.visibleNodeIds = result.visibleNodeIds;
      this.visibleEdgeIds = result.visibleEdgeIds;
      this.elements.visibleChipElement.textContent = `Visible ${this.visibleNodeIds.size}`;
      for (const [nodeId, element] of this.nodeElementById.entries()) {
        const isVisible = this.visibleNodeIds.has(nodeId);
        element.classList.toggle("hidden", !isVisible);
      }
      for (const [edgeId, refs] of this.edgeElementById.entries()) {
        const isVisible = this.visibleEdgeIds.has(edgeId);
        refs.visiblePath.classList.toggle("hidden", !isVisible);
        refs.hitPath.classList.toggle("hidden", !isVisible);
      }
      if (this.selectedNodeId && !this.visibleNodeIds.has(this.selectedNodeId)) {
        this.selectedNodeId = "";
      }
      if (this.selectedEdgeId && !this.visibleEdgeIds.has(this.selectedEdgeId)) {
        this.selectedEdgeId = "";
      }
      this.refreshHighlightState();
      this.callbacks.onSelectionChanged(this.selectedSelection());
    }
    selectNode(nodeId) {
      this.selectedNodeId = nodeId && this.model.hasNode(nodeId) ? nodeId : "";
      this.selectedEdgeId = "";
      this.refreshHighlightState();
      this.callbacks.onSelectionChanged(this.selectedSelection());
      this.callbacks.onStateChanged();
    }
    selectEdge(edgeId) {
      this.selectedEdgeId = edgeId && this.model.edge(edgeId) ? edgeId : "";
      this.selectedNodeId = "";
      this.refreshHighlightState();
      this.callbacks.onSelectionChanged(this.selectedSelection());
    }
    clearSelection() {
      this.selectedNodeId = "";
      this.selectedEdgeId = "";
      this.refreshHighlightState();
      this.callbacks.onSelectionChanged({ kind: "none" });
    }
    selectedNodeIdOrEmpty() {
      return this.selectedNodeId;
    }
    selectedNode() {
      if (!this.selectedNodeId) {
        return null;
      }
      return this.layout.nodes.get(this.selectedNodeId) || null;
    }
    selectedEdge() {
      if (!this.selectedEdgeId) {
        return null;
      }
      return this.layout.edges.find((edge) => edge.id === this.selectedEdgeId) || null;
    }
    selectedSelection() {
      if (this.selectedNodeId) {
        return { kind: "node", nodeId: this.selectedNodeId };
      }
      if (this.selectedEdgeId) {
        return { kind: "edge", edgeId: this.selectedEdgeId };
      }
      return { kind: "none" };
    }
    focusVisible() {
      const nodes = [...this.layout.nodes.values()].filter((node) => this.visibleNodeIds.has(node.id));
      this.fitNodes(nodes);
    }
    focusAll() {
      this.fitNodes([...this.layout.nodes.values()]);
    }
    zoomIn() {
      this.svgSelection.call(this.zoomBehavior.scaleBy, 1.08);
    }
    zoomOut() {
      this.svgSelection.call(this.zoomBehavior.scaleBy, 0.92);
    }
    currentTransform() {
      return transform(this.elements.svgElement);
    }
    moveSelection(direction) {
      const visibleNodes = [...this.layout.nodes.values()].filter((node) => this.visibleNodeIds.has(node.id));
      if (!visibleNodes.length) {
        return;
      }
      if (!this.selectedNodeId || !this.visibleNodeIds.has(this.selectedNodeId)) {
        const firstNode = [...visibleNodes].sort((left, right) => left.label.localeCompare(right.label))[0];
        if (firstNode) {
          this.selectNode(firstNode.id);
        }
        return;
      }
      const current = this.layout.nodes.get(this.selectedNodeId);
      if (!current) {
        return;
      }
      let best = null;
      let bestScore = Number.POSITIVE_INFINITY;
      for (const node of visibleNodes) {
        if (node.id === current.id) {
          continue;
        }
        const dx = node.x - current.x;
        const dy = node.y - current.y;
        if (direction === "left" && dx >= 0) {
          continue;
        }
        if (direction === "right" && dx <= 0) {
          continue;
        }
        if (direction === "up" && dy >= 0) {
          continue;
        }
        if (direction === "down" && dy <= 0) {
          continue;
        }
        const major = direction === "left" || direction === "right" ? Math.abs(dx) : Math.abs(dy);
        const minor = direction === "left" || direction === "right" ? Math.abs(dy) : Math.abs(dx);
        const score = major * 2 + minor;
        if (score < bestScore) {
          bestScore = score;
          best = node;
        }
      }
      if (best) {
        this.selectNode(best.id);
      }
    }
    openSelectedSource() {
      if (this.selectedNodeId) {
        this.callbacks.onNodeOpened(this.selectedNodeId);
        return;
      }
      if (this.selectedEdgeId) {
        this.callbacks.onEdgeOpened(this.selectedEdgeId);
      }
    }
    resetLayout() {
      for (const [nodeId, point] of this.initialPositions.entries()) {
        const node = this.layout.nodes.get(nodeId);
        if (!node) {
          continue;
        }
        node.x = point.x;
        node.y = point.y;
      }
      this.hideHoverCard();
      this.scheduleGeometryUpdate();
      this.focusAll();
      this.callbacks.onStateChanged();
    }
    persistableState(extraState) {
      const transform2 = this.currentTransform();
      return {
        selectedNodeId: this.selectedNodeId,
        searchQuery: extraState.searchQuery,
        focusMode: extraState.focusMode,
        inspectorPinned: extraState.inspectorPinned,
        zoomScale: transform2.k,
        zoomX: transform2.x,
        zoomY: transform2.y
      };
    }
    renderGroups() {
      const groupLayer = this.elements.groupLayerElement;
      while (groupLayer.firstChild) {
        groupLayer.removeChild(groupLayer.firstChild);
      }
      for (const groupFrame of this.layout.groupFrames) {
        const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
        group.setAttribute("class", "framework-group-panel");
        group.setAttribute("data-framework-group", groupFrame.name);
        groupLayer.appendChild(group);
        const frame2 = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        frame2.setAttribute("x", String(groupFrame.x));
        frame2.setAttribute("y", String(groupFrame.y));
        frame2.setAttribute("width", String(groupFrame.width));
        frame2.setAttribute("height", String(groupFrame.height));
        frame2.setAttribute("rx", "22");
        frame2.setAttribute("ry", "22");
        frame2.setAttribute("class", "framework-group-frame");
        group.appendChild(frame2);
        const header = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        header.setAttribute("x", String(groupFrame.x));
        header.setAttribute("y", String(groupFrame.y));
        header.setAttribute("width", String(groupFrame.width));
        header.setAttribute("height", "54");
        header.setAttribute("rx", "22");
        header.setAttribute("ry", "22");
        header.setAttribute("class", "framework-group-header");
        group.appendChild(header);
        const title = document.createElementNS("http://www.w3.org/2000/svg", "text");
        title.setAttribute("x", String(groupFrame.x + 20));
        title.setAttribute("y", String(groupFrame.y + 34));
        title.setAttribute("class", "framework-group-title");
        title.textContent = groupFrame.name;
        group.appendChild(title);
        const subtitle = document.createElementNS("http://www.w3.org/2000/svg", "text");
        subtitle.setAttribute("x", String(groupFrame.x + groupFrame.width - 18));
        subtitle.setAttribute("y", String(groupFrame.y + 34));
        subtitle.setAttribute("text-anchor", "end");
        subtitle.setAttribute("class", "framework-group-meta");
        subtitle.textContent = `${groupFrame.localLevels.length} level${groupFrame.localLevels.length === 1 ? "" : "s"}`;
        group.appendChild(subtitle);
      }
    }
    renderBands() {
      const bandLayer = this.elements.bandLayerElement;
      while (bandLayer.firstChild) {
        bandLayer.removeChild(bandLayer.firstChild);
      }
      for (const band of this.layout.bands) {
        const bandRect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        bandRect.setAttribute("x", String(band.x));
        bandRect.setAttribute("y", String(band.y));
        bandRect.setAttribute("width", String(band.width));
        bandRect.setAttribute("height", String(band.height));
        bandRect.setAttribute("rx", "16");
        bandRect.setAttribute("ry", "16");
        bandRect.setAttribute("class", `depth-band depth-${Math.max(0, band.depth % 6)}`);
        bandLayer.appendChild(bandRect);
        const bandLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
        bandLabel.setAttribute("x", String(band.x + 14));
        bandLabel.setAttribute("y", String(band.y + 22));
        bandLabel.setAttribute("class", "depth-label");
        bandLabel.textContent = band.label;
        bandLayer.appendChild(bandLabel);
      }
    }
    renderEdges() {
      const edgeLayer = this.elements.edgeLayerElement;
      while (edgeLayer.firstChild) {
        edgeLayer.removeChild(edgeLayer.firstChild);
      }
      this.edgeElementById.clear();
      for (const edge of this.layout.edges) {
        const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
        group.setAttribute("class", "graph-edge-group");
        group.setAttribute("data-edge-id", edge.id);
        edgeLayer.appendChild(group);
        const visiblePath = document.createElementNS("http://www.w3.org/2000/svg", "path");
        visiblePath.setAttribute("class", "graph-edge");
        visiblePath.setAttribute("data-edge-id", edge.id);
        visiblePath.setAttribute("marker-end", `url(#${EDGE_ARROW_DEFAULT_MARKER_ID})`);
        group.appendChild(visiblePath);
        const hitPath = document.createElementNS("http://www.w3.org/2000/svg", "path");
        hitPath.setAttribute("class", "graph-edge-hit");
        hitPath.setAttribute("data-edge-id", edge.id);
        group.appendChild(hitPath);
        hitPath.addEventListener("click", (event) => {
          event.stopPropagation();
          this.selectEdge(edge.id);
        });
        hitPath.addEventListener("dblclick", (event) => {
          event.stopPropagation();
          this.selectEdge(edge.id);
          this.callbacks.onEdgeOpened(edge.id);
        });
        hitPath.addEventListener("mouseenter", () => {
          this.hoveredEdgeId = edge.id;
          this.refreshHighlightState();
        });
        hitPath.addEventListener("mouseleave", () => {
          this.hoveredEdgeId = "";
          this.refreshHighlightState();
        });
        this.edgeElementById.set(edge.id, { visiblePath, hitPath });
      }
    }
    renderNodes() {
      const nodeLayer = this.elements.nodeLayerElement;
      while (nodeLayer.firstChild) {
        nodeLayer.removeChild(nodeLayer.firstChild);
      }
      this.nodeElementById.clear();
      const nodeSelection = select_default2(nodeLayer).selectAll("g.graph-node").data([...this.layout.nodes.values()], (d) => d.id).join((enter) => {
        const group = enter.append("g").attr("class", (d) => `graph-node ${kindClass(d.kind)}`).attr("data-node-id", (d) => d.id).on("click", (event, d) => {
          event.stopPropagation();
          this.selectNode(d.id);
          const mouseEvent = event;
          if (mouseEvent.metaKey || mouseEvent.ctrlKey) {
            this.callbacks.onNodeOpened(d.id);
          }
        }).on("dblclick", (event, d) => {
          event.stopPropagation();
          this.selectNode(d.id);
          this.callbacks.onNodeOpened(d.id);
        }).on("mouseenter", (event, d) => {
          const target = event.currentTarget;
          target?.classList.add("hovered");
          this.hoveredNodeId = d.id;
          this.refreshHighlightState();
          const mouseEvent = event;
          this.showNodeHover(d, mouseEvent.clientX, mouseEvent.clientY);
        }).on("mousemove", (event, d) => {
          const mouseEvent = event;
          this.showNodeHover(d, mouseEvent.clientX, mouseEvent.clientY);
        }).on("mouseleave", (event) => {
          const target = event.currentTarget;
          target?.classList.remove("hovered");
          this.hoveredNodeId = "";
          this.refreshHighlightState();
          this.hideHoverCard();
        });
        group.append("circle").attr("cx", 0).attr("cy", 0).attr("r", (d) => String(nodeRadius(d))).attr("class", "node-circle");
        group.append("rect").attr("class", "node-label-box").attr("rx", 7).attr("ry", 7);
        group.append("text").attr("class", "node-label").attr("x", 0).attr("y", 26).attr("text-anchor", "middle").attr("dominant-baseline", "hanging").text((d) => shortText(compactNodeId(d), 32));
        group.append("rect").attr("class", "node-hit-area");
        return group;
      });
      nodeSelection.each((node, index, groups) => {
        const element = groups[index];
        if (element) {
          this.nodeElementById.set(node.id, element);
          const label = element.querySelector("text.node-label");
          const labelBox = element.querySelector("rect.node-label-box");
          const hitArea = element.querySelector("rect.node-hit-area");
          if (label && labelBox && hitArea) {
            const labelBounds = label.getBBox();
            const padX = 5;
            const padY = 1;
            labelBox.setAttribute("x", String(labelBounds.x - padX));
            labelBox.setAttribute("y", String(labelBounds.y - padY));
            labelBox.setAttribute("width", String(Math.max(10, labelBounds.width + padX * 2)));
            labelBox.setAttribute("height", String(Math.max(10, labelBounds.height + padY * 2)));
            const radius = nodeRadius(node);
            const hitPadding = 10;
            const minX = Math.min(-radius - hitPadding, labelBounds.x - padX - hitPadding);
            const maxX = Math.max(radius + hitPadding, labelBounds.x + labelBounds.width + padX + hitPadding);
            const minY = Math.min(-radius - hitPadding, labelBounds.y - padY - hitPadding);
            const maxY = Math.max(radius + hitPadding, labelBounds.y + labelBounds.height + padY + hitPadding);
            hitArea.setAttribute("x", String(minX));
            hitArea.setAttribute("y", String(minY));
            hitArea.setAttribute("width", String(Math.max(1, maxX - minX)));
            hitArea.setAttribute("height", String(Math.max(1, maxY - minY)));
            hitArea.setAttribute("rx", "14");
            hitArea.setAttribute("ry", "14");
          }
        }
      });
      select_default2(this.elements.svgElement).on("click.canvas", () => {
        this.clearSelection();
      });
      this.scheduleGeometryUpdate();
    }
    scheduleGeometryUpdate() {
      if (this.geometryFrame !== null) {
        return;
      }
      this.geometryFrame = window.requestAnimationFrame(() => {
        this.geometryFrame = null;
        this.updateGeometry();
      });
    }
    updateGeometry() {
      for (const edge of this.layout.edges) {
        const fromNode = this.layout.nodes.get(edge.from);
        const toNode = this.layout.nodes.get(edge.to);
        const refs = this.edgeElementById.get(edge.id);
        if (!fromNode || !toNode || !refs) {
          continue;
        }
        edge.fromX = fromNode.x;
        edge.fromY = fromNode.y;
        edge.toX = toNode.x;
        edge.toY = toNode.y;
        const path = edgePath(fromNode, toNode);
        refs.visiblePath.setAttribute("d", path);
        refs.hitPath.setAttribute("d", path);
      }
      for (const [nodeId, element] of this.nodeElementById.entries()) {
        const node = this.layout.nodes.get(nodeId);
        if (!node) {
          continue;
        }
        element.setAttribute("transform", `translate(${node.x} ${node.y})`);
      }
      this.refreshHighlightState();
    }
    refreshHighlightState() {
      const selectedNodes = /* @__PURE__ */ new Set();
      const neighborNodes = /* @__PURE__ */ new Set();
      const activeEdges = /* @__PURE__ */ new Set();
      const fadedNodes = /* @__PURE__ */ new Set();
      const fadedEdges = /* @__PURE__ */ new Set();
      if (this.selectedEdgeId) {
        const edge = this.model.edge(this.selectedEdgeId);
        if (edge) {
          selectedNodes.add(edge.from);
          selectedNodes.add(edge.to);
          activeEdges.add(edge.id);
          for (const node of this.layout.nodes.keys()) {
            if (!selectedNodes.has(node)) {
              fadedNodes.add(node);
            }
          }
          for (const layoutEdge of this.layout.edges) {
            if (layoutEdge.id !== edge.id) {
              fadedEdges.add(layoutEdge.id);
            }
          }
        }
      } else if (this.selectedNodeId) {
        selectedNodes.add(this.selectedNodeId);
        for (const adjacent of this.model.adjacentNodeIds(this.selectedNodeId)) {
          neighborNodes.add(adjacent);
        }
        for (const edge of this.layout.edges) {
          if (edge.from === this.selectedNodeId || edge.to === this.selectedNodeId) {
            activeEdges.add(edge.id);
          } else {
            fadedEdges.add(edge.id);
          }
        }
        for (const nodeId of this.layout.nodes.keys()) {
          if (nodeId !== this.selectedNodeId && !neighborNodes.has(nodeId)) {
            fadedNodes.add(nodeId);
          }
        }
      }
      if (!this.selectedEdgeId && !this.selectedNodeId) {
        if (this.hoveredNodeId) {
          selectedNodes.add(this.hoveredNodeId);
          for (const adjacent of this.model.adjacentNodeIds(this.hoveredNodeId)) {
            neighborNodes.add(adjacent);
          }
          for (const edge of this.layout.edges) {
            if (edge.from === this.hoveredNodeId || edge.to === this.hoveredNodeId) {
              activeEdges.add(edge.id);
            }
          }
        } else if (this.hoveredEdgeId) {
          const hoveredEdge = this.model.edge(this.hoveredEdgeId);
          if (hoveredEdge) {
            selectedNodes.add(hoveredEdge.from);
            selectedNodes.add(hoveredEdge.to);
            activeEdges.add(hoveredEdge.id);
          }
        }
      }
      for (const [nodeId, element] of this.nodeElementById.entries()) {
        const selected = this.selectedNodeId === nodeId || Boolean(this.selectedEdgeId && selectedNodes.has(nodeId));
        const neighbor = neighborNodes.has(nodeId) && !selected;
        const faded = fadedNodes.has(nodeId);
        element.classList.toggle("selected", selected);
        element.classList.toggle("neighbor", neighbor);
        element.classList.toggle("faded", faded);
      }
      for (const [edgeId, refs] of this.edgeElementById.entries()) {
        const active = activeEdges.has(edgeId);
        const faded = fadedEdges.has(edgeId);
        refs.visiblePath.classList.toggle("active", active);
        refs.visiblePath.classList.toggle("faded", faded);
        refs.hitPath.classList.toggle("active", active);
      }
    }
    applyPersistedState(rawState) {
      const state = sanitizeState(rawState, this.viewSettings);
      const hasCustomViewport = Math.abs(state.zoomScale - 1) > 1e-3 || Math.abs(state.zoomX) > 0.01 || Math.abs(state.zoomY) > 0.01;
      if (hasCustomViewport) {
        const transform2 = identity2.translate(state.zoomX, state.zoomY).scale(state.zoomScale);
        this.svgSelection.call(this.zoomBehavior.transform, transform2);
      } else {
        this.focusAll();
      }
      if (state.selectedNodeId && this.model.hasNode(state.selectedNodeId)) {
        this.selectNode(state.selectedNodeId);
      } else {
        this.clearSelection();
      }
    }
    fitNodes(nodes) {
      const bounds = computeNodeBounds(nodes);
      if (!bounds) {
        return;
      }
      const container = this.elements.scrollElement.getBoundingClientRect();
      const containerWidth = Math.max(320, container.width || 1280);
      const containerHeight = Math.max(260, container.height || 760);
      const pad = 36;
      const contentWidth = Math.max(1, bounds.maxX - bounds.minX);
      const contentHeight = Math.max(1, bounds.maxY - bounds.minY);
      const scaleX = (containerWidth - pad * 2) / contentWidth;
      const scaleY = (containerHeight - pad * 2) / contentHeight;
      const scale = Math.max(
        this.viewSettings.zoomMinScale,
        Math.min(this.viewSettings.zoomMaxScale, Math.min(scaleX, scaleY))
      );
      const tx = (containerWidth - contentWidth * scale) / 2 - bounds.minX * scale;
      const ty = (containerHeight - contentHeight * scale) / 2 - bounds.minY * scale;
      const transform2 = identity2.translate(tx, ty).scale(scale);
      this.svgSelection.call(this.zoomBehavior.transform, transform2);
      this.callbacks.onStateChanged();
    }
    renderHoverContent(node) {
      const kicker = escapeHtml(node.hoverKicker || "Hierarchy Node");
      const title = escapeHtml(node.title || node.label || node.id);
      const subtitle = escapeHtml(
        [node.moduleName || "", node.moduleRef || ""].filter(Boolean).join(" · ") || node.label
      );
      const footer = escapeHtml(
        node.file ? `${node.file}:${node.docLine || node.line} · Ctrl/⌘ + 点击跳转到文档` : "Ctrl/⌘ + 点击跳转到文档"
      );
      return `
      <p class="hover-kicker">${kicker}</p>
      <h3 class="hover-title">${title}</h3>
      <p class="hover-subtitle">${subtitle}</p>
      <div class="hover-grid">
        <section class="hover-section">
          <h4 class="hover-section-title">能力声明</h4>
          <ul class="hover-list">${hoverList(node.capabilityItems || [], "无能力声明", 2)}</ul>
        </section>
        <section class="hover-section">
          <h4 class="hover-section-title">最小可行基</h4>
          <ul class="hover-list">${hoverList(node.baseItems || [], "无最小可行基", 2)}</ul>
        </section>
      </div>
      <div class="hover-footer">${footer}</div>
    `;
    }
    positionHoverCard(clientX, clientY) {
      const card = this.elements.hoverCardElement;
      const margin = 18;
      const rect = card.getBoundingClientRect();
      let left = clientX + margin;
      let top = clientY + margin;
      if (left + rect.width > window.innerWidth - 12) {
        left = clientX - rect.width - margin;
      }
      if (top + rect.height > window.innerHeight - 12) {
        top = clientY - rect.height - margin;
      }
      card.style.left = `${Math.max(12, left)}px`;
      card.style.top = `${Math.max(12, top)}px`;
    }
    showNodeHover(node, clientX, clientY) {
      if (!this.elements.hoverCardElement || this.currentTransform().k <= 0) {
        return;
      }
      this.elements.hoverCardElement.innerHTML = this.renderHoverContent(node);
      this.elements.hoverCardElement.classList.add("visible");
      this.elements.hoverCardElement.setAttribute("aria-hidden", "false");
      this.positionHoverCard(clientX, clientY);
    }
    hideHoverCard() {
      this.elements.hoverCardElement.classList.remove("visible");
      this.elements.hoverCardElement.setAttribute("aria-hidden", "true");
    }
    ensureEdgeMarker() {
      const svg = this.elements.svgElement;
      let defs = svg.querySelector("defs#tree-edge-defs");
      if (!defs) {
        defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
        defs.setAttribute("id", "tree-edge-defs");
        svg.insertBefore(defs, svg.firstChild);
      }
      if (defs.querySelector(`marker#${EDGE_ARROW_DEFAULT_MARKER_ID}`) && defs.querySelector(`marker#${EDGE_ARROW_ACTIVE_MARKER_ID}`)) {
        return;
      }
      const buildMarker = (id2, shapeClass) => {
        const marker = document.createElementNS("http://www.w3.org/2000/svg", "marker");
        marker.setAttribute("id", id2);
        marker.setAttribute("viewBox", "0 0 12 9");
        marker.setAttribute("refX", "10.5");
        marker.setAttribute("refY", "4.5");
        marker.setAttribute("markerWidth", "12");
        marker.setAttribute("markerHeight", "12");
        marker.setAttribute("orient", "auto");
        marker.setAttribute("markerUnits", "userSpaceOnUse");
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("d", "M0,0 L0,9 L12,4.5 z");
        path.setAttribute("class", shapeClass);
        marker.appendChild(path);
        return marker;
      };
      if (!defs.querySelector(`marker#${EDGE_ARROW_DEFAULT_MARKER_ID}`)) {
        defs.appendChild(buildMarker(EDGE_ARROW_DEFAULT_MARKER_ID, "graph-edge-arrow-default"));
      }
      if (!defs.querySelector(`marker#${EDGE_ARROW_ACTIVE_MARKER_ID}`)) {
        defs.appendChild(buildMarker(EDGE_ARROW_ACTIVE_MARKER_ID, "graph-edge-arrow-active"));
      }
    }
  };

  // webview/tree/index.ts
  function requiredElementById(elementId, ctor) {
    const element = document.getElementById(elementId);
    if (!(element instanceof ctor)) {
      throw new Error(`Missing required element #${elementId}`);
    }
    return element;
  }
  function normalizeFocusMode(value) {
    if (value === "upstream" || value === "downstream") {
      return value;
    }
    return "all";
  }
  function escapeHtml2(value) {
    return String(value ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  function detailList(items) {
    if (!items.length) {
      return '<li class="detail-item">无</li>';
    }
    return items.map((item) => `<li class="detail-item">${escapeHtml2(item)}</li>`).join("");
  }
  function targetSignature(target) {
    if (!target) {
      return "";
    }
    return [
      target.targetKind,
      target.filePath,
      String(target.startLine),
      target.symbol
    ].join("|");
  }
  function actionButton(label, target, options) {
    if (!target) {
      return '<span class="detail-value">无</span>';
    }
    const classes = ["detail-action"];
    if (options?.muted) {
      classes.push("ghost");
    }
    return `<button type="button" class="${classes.join(" ")}" data-open-source="1" data-file="${escapeHtml2(target.filePath)}" data-line="${target.startLine}">${escapeHtml2(label)}</button>`;
  }
  function relatedObjectButton(objectId, label) {
    return `<button type="button" class="detail-action ghost" data-show-object="1" data-object-id="${escapeHtml2(objectId)}">${escapeHtml2(label)}</button>`;
  }
  function targetSummary(target) {
    if (!target) {
      return "无";
    }
    return `${target.targetKind} · ${target.filePath}:${target.startLine}`;
  }
  function formatTargetList(targets) {
    if (!targets.length) {
      return '<li class="detail-item">无</li>';
    }
    return targets.map((target) => `<li class="detail-item">${actionButton(target.label || target.targetKind, target, { muted: true })} <span class="mono">${escapeHtml2(target.targetKind)}</span> · <span class="mono">${escapeHtml2(target.filePath)}:${target.startLine}</span></li>`).join("");
  }
  function main() {
    const bootstrap = readRuntimeBootstrap();
    const bridge = new WebviewBridge();
    const persistedState = bridge.readPersistedState();
    const model = new TreeGraphModel(bootstrap.model);
    const layout = computeTreeLayout(model, bootstrap.layoutSettings);
    document.documentElement.style.setProperty("--inspector-width-px", `${bootstrap.viewSettings.inspectorWidth}px`);
    document.documentElement.style.setProperty("--inspector-rail-width-px", `${bootstrap.viewSettings.inspectorRailWidth}px`);
    const elements = {
      scrollElement: requiredElementById("treeCanvasScroll", HTMLElement),
      svgElement: requiredElementById("treeCanvas", SVGSVGElement),
      viewportElement: requiredElementById("treeViewport", SVGGElement),
      groupLayerElement: requiredElementById("treeGroupLayer", SVGGElement),
      bandLayerElement: requiredElementById("treeBandLayer", SVGGElement),
      edgeLayerElement: requiredElementById("treeEdgeLayer", SVGGElement),
      nodeLayerElement: requiredElementById("treeNodeLayer", SVGGElement),
      hoverCardElement: requiredElementById("treeHoverCard", HTMLElement),
      statusElement: requiredElementById("treeStatusText", HTMLElement),
      zoomChipElement: requiredElementById("treeZoomChip", HTMLElement),
      countChipElement: requiredElementById("treeCountChip", HTMLElement),
      visibleChipElement: requiredElementById("treeVisibleChip", HTMLElement)
    };
    const searchInput = requiredElementById("treeSearchInput", HTMLInputElement);
    const focusSelect = requiredElementById("treeFocusSelect", HTMLSelectElement);
    const clearFilterButton = requiredElementById("treeClearFilterBtn", HTMLButtonElement);
    const fitButton = requiredElementById("treeFitBtn", HTMLButtonElement);
    const resetButton = requiredElementById("treeResetBtn", HTMLButtonElement);
    const zoomInButton = requiredElementById("treeZoomInBtn", HTMLButtonElement);
    const zoomOutButton = requiredElementById("treeZoomOutBtn", HTMLButtonElement);
    const inspectorShell = requiredElementById("treeInspector", HTMLElement);
    const inspectorRail = requiredElementById("treeInspectorRail", HTMLElement);
    const inspectorRailValue = requiredElementById("inspectorRailValue", HTMLElement);
    const inspectorSummaryValue = requiredElementById("inspectorSummaryValue", HTMLElement);
    const selectionKindPill = requiredElementById("selectionKindPill", HTMLElement);
    const pinInspectorButton = requiredElementById("pinInspectorBtn", HTMLButtonElement);
    const inspectorDetailBox = requiredElementById("inspectorDetailBox", HTMLElement);
    if (persistedState) {
      searchInput.value = persistedState.searchQuery;
      focusSelect.value = persistedState.focusMode;
    }
    let inspectorPinned = Boolean(persistedState?.inspectorPinned);
    const setInspectorExpandedState = (expanded) => {
      inspectorRail.setAttribute("aria-expanded", String(expanded || inspectorPinned));
    };
    let isApplyingFilters = false;
    let persistTimer = null;
    const schedulePersist = () => {
      if (persistTimer !== null) {
        window.clearTimeout(persistTimer);
      }
      persistTimer = window.setTimeout(() => {
        persistTimer = null;
        bridge.persistState(renderer.persistableState({
          searchQuery: searchInput.value,
          focusMode: normalizeFocusMode(focusSelect.value),
          inspectorPinned
        }));
      }, 120);
    };
    const applyInspectorPinnedState = (nextPinned, options) => {
      inspectorPinned = nextPinned;
      inspectorShell.dataset.pinned = String(nextPinned);
      setInspectorExpandedState(nextPinned);
      pinInspectorButton.textContent = nextPinned ? "Unpin" : "Pin";
      pinInspectorButton.setAttribute("aria-pressed", String(nextPinned));
      if (options?.persist !== false) {
        schedulePersist();
      }
    };
    let currentSelection = { kind: "none" };
    const openTarget = (target) => {
      if (!target?.filePath) {
        return;
      }
      bridge.openSource(target.filePath, target.startLine);
    };
    const nodeDefaultTarget = (node) => {
      if (!node) {
        return null;
      }
      return node.defaultTarget || node.editTarget || null;
    };
    const objectSecondaryTargets = (objectValue) => {
      const excluded = new Set(
        [
          objectValue.navigationTargets.find((target) => target.targetKind === objectValue.primaryNavTargetKind) || null,
          objectValue.navigationTargets.find((target) => target.targetKind === objectValue.primaryEditTargetKind) || null,
          objectValue.correspondenceAnchor || null,
          objectValue.implementationAnchor || null
        ].map((target) => targetSignature(target)).filter(Boolean)
      );
      return objectValue.navigationTargets.filter((target) => !excluded.has(targetSignature(target)));
    };
    const renderObjectLinkList = (objectIds) => {
      if (!objectIds.length) {
        return '<li class="detail-item">无</li>';
      }
      return objectIds.map((objectId) => {
        const objectValue = model.object(objectId);
        const label = objectValue?.displayName || objectId;
        const issueCount = model.validationSummary.issueCountByObject[objectId] || 0;
        const suffix = issueCount > 0 ? ` · ${issueCount} issue(s)` : "";
        return `<li class="detail-item">${relatedObjectButton(objectId, label)}${suffix ? ` <span class="mono">${escapeHtml2(suffix)}</span>` : ""}</li>`;
      }).join("");
    };
    const attachDetailActions = () => {
      inspectorDetailBox.querySelectorAll("[data-open-source='1']").forEach((element) => {
        element.addEventListener("click", (event) => {
          event.stopPropagation();
          const filePath = element.getAttribute("data-file") || "";
          const lineNumber = Number(element.getAttribute("data-line") || "1");
          if (filePath) {
            bridge.openSource(filePath, lineNumber);
          }
        });
      });
      inspectorDetailBox.querySelectorAll("[data-show-object='1']").forEach((element) => {
        element.addEventListener("click", (event) => {
          event.stopPropagation();
          const objectId = element.getAttribute("data-object-id") || "";
          if (objectId) {
            renderCorrespondenceObjectDetail(objectId);
          }
        });
      });
      inspectorDetailBox.querySelectorAll("[data-reset-inspector='1']").forEach((element) => {
        element.addEventListener("click", (event) => {
          event.stopPropagation();
          updateInspector(currentSelection);
        });
      });
    };
    const renderEmptyDetail = () => {
      selectionKindPill.textContent = "none";
      selectionKindPill.className = "pill kind-pill";
      inspectorRailValue.textContent = "No selection";
      inspectorRailValue.title = "No selection";
      inspectorSummaryValue.textContent = "Click a node or edge to inspect details.";
      inspectorDetailBox.innerHTML = `
      <p class="detail-empty">
        Click a node or edge to inspect details. Search, focus mode, hover, and source jumps stay available while the canvas remains primary.
      </p>
    `;
    };
    const renderCorrespondenceObjectDetail = (objectId) => {
      const objectValue = model.object(objectId);
      if (!objectValue) {
        renderEmptyDetail();
        return;
      }
      const primaryNavTarget = objectValue.navigationTargets.find(
        (target) => target.targetKind === objectValue.primaryNavTargetKind
      ) || null;
      const primaryEditTarget = objectValue.navigationTargets.find(
        (target) => target.targetKind === objectValue.primaryEditTargetKind
      ) || null;
      const secondaryTargets = objectSecondaryTargets(objectValue);
      const issueCount = model.validationSummary.issueCountByObject[objectValue.objectId] || 0;
      const ownerModuleObject = objectValue.ownerModuleId ? model.object(objectValue.ownerModuleId) : null;
      selectionKindPill.textContent = objectValue.objectKind;
      selectionKindPill.className = `pill kind-pill ${objectValue.objectKind.replace(/[^a-zA-Z0-9_-]/g, "-")}`;
      inspectorRailValue.textContent = objectValue.displayName;
      inspectorRailValue.title = objectValue.displayName;
      inspectorSummaryValue.textContent = `${objectValue.objectId} · nav=${objectValue.primaryNavTargetKind}`;
      inspectorDetailBox.innerHTML = `
      <section class="detail-group">
        <h3 class="detail-section-title">对象概览</h3>
        <div class="detail-kv"><span class="detail-key">Object ID</span><span class="detail-value mono">${escapeHtml2(objectValue.objectId)}</span></div>
        <div class="detail-kv"><span class="detail-key">类型</span><span class="detail-value">${escapeHtml2(objectValue.objectKind)}</span></div>
        <div class="detail-kv"><span class="detail-key">显示名</span><span class="detail-value">${escapeHtml2(objectValue.displayName)}</span></div>
        <div class="detail-kv"><span class="detail-key">Materialization</span><span class="detail-value mono">${escapeHtml2(objectValue.materializationKind || "unknown")}</span></div>
        <div class="detail-kv"><span class="detail-key">Owner Module</span><span class="detail-value">${ownerModuleObject ? relatedObjectButton(ownerModuleObject.objectId, ownerModuleObject.displayName) : escapeHtml2(objectValue.ownerModuleId || "无")}</span></div>
        <div class="detail-kv"><span class="detail-key">Issues</span><span class="detail-value">${issueCount ? `${issueCount} issue(s)` : "0"}</span></div>
      </section>
      <section class="detail-group">
        <h3 class="detail-section-title">默认跳转</h3>
        <div class="detail-kv"><span class="detail-key">Primary Nav</span><span class="detail-value mono">${escapeHtml2(targetSummary(primaryNavTarget))}</span></div>
        <div class="detail-kv"><span class="detail-key">Primary Edit</span><span class="detail-value mono">${escapeHtml2(targetSummary(primaryEditTarget))}</span></div>
        <div class="action-row">
          ${actionButton("默认打开", primaryNavTarget)}
          ${targetSignature(primaryEditTarget) && targetSignature(primaryEditTarget) !== targetSignature(primaryNavTarget) ? actionButton("编辑落点", primaryEditTarget, { muted: true }) : ""}
          <button type="button" class="detail-action ghost" data-reset-inspector="1">返回节点</button>
        </div>
      </section>
      <section class="detail-group">
        <h3 class="detail-section-title">结构与实现锚点</h3>
        <div class="detail-kv"><span class="detail-key">Correspondence</span><span class="detail-value mono">${escapeHtml2(targetSummary(objectValue.correspondenceAnchor))}</span></div>
        <div class="detail-kv"><span class="detail-key">Implementation</span><span class="detail-value mono">${escapeHtml2(targetSummary(objectValue.implementationAnchor))}</span></div>
        <div class="action-row">
          ${actionButton("结构锚点", objectValue.correspondenceAnchor, { muted: true })}
          ${actionButton("实现锚点", objectValue.implementationAnchor, { muted: true })}
        </div>
      </section>
      <section class="detail-group">
        <h3 class="detail-section-title">次级跳转</h3>
        <ul class="detail-list">${formatTargetList(secondaryTargets)}</ul>
      </section>
    `;
      attachDetailActions();
    };
    const renderNodeDetail = (nodeId) => {
      const node = layout.nodes.get(nodeId);
      if (!node) {
        renderEmptyDetail();
        return;
      }
      const upstream = model.incomingEdges(nodeId).map((edge) => {
        const peer = model.node(edge.from);
        return `${peer?.label || edge.from} · ${edge.relation}`;
      });
      const downstream = model.outgoingEdges(nodeId).map((edge) => {
        const peer = model.node(edge.to);
        return `${peer?.label || edge.to} · ${edge.relation}`;
      });
      const sourceFile = node.file;
      const docLine = node.docLine || node.line;
      const sourceLine = node.sourceLine || node.line;
      const defaultTarget = nodeDefaultTarget(node);
      const levelLabel = node.moduleName ? `${node.moduleName} · ${model.levelLabel(node.depth)}` : model.levelLabel(node.depth);
      const objectValue = node.objectId ? model.object(node.objectId) : null;
      const issueCount = node.objectId ? model.validationSummary.issueCountByObject[node.objectId] || 0 : 0;
      const secondaryTargets = node.secondaryTargets || [];
      selectionKindPill.textContent = node.kind;
      selectionKindPill.className = `pill kind-pill ${node.kind.replace(/[^a-zA-Z0-9_-]/g, "-")}`;
      inspectorRailValue.textContent = node.title || node.label;
      inspectorRailValue.title = node.title || node.label;
      inspectorSummaryValue.textContent = node.moduleRef ? `${node.moduleName || ""} · ${node.moduleRef}`.replace(/^\s*·\s*/, "") : node.label;
      inspectorDetailBox.innerHTML = `
      <section class="detail-group">
        <h3 class="detail-section-title">节点概览</h3>
        <div class="detail-kv"><span class="detail-key">ID</span><span class="detail-value mono">${escapeHtml2(node.id)}</span></div>
        <div class="detail-kv"><span class="detail-key">标题</span><span class="detail-value">${escapeHtml2(node.title || node.label)}</span></div>
        <div class="detail-kv"><span class="detail-key">层级</span><span class="detail-value">${escapeHtml2(levelLabel)}</span></div>
        <div class="detail-kv"><span class="detail-key">标签</span><span class="detail-value">${escapeHtml2(node.label)}</span></div>
        <div class="detail-kv"><span class="detail-key">描述</span><span class="detail-value">${escapeHtml2(node.detail || "无")}</span></div>
        <div class="detail-kv"><span class="detail-key">Object ID</span><span class="detail-value mono">${escapeHtml2(node.objectId || "无")}</span></div>
        <div class="detail-kv"><span class="detail-key">Issue Count</span><span class="detail-value">${issueCount}</span></div>
      </section>
      <section class="detail-group">
        <h3 class="detail-section-title">来源与跳转</h3>
        <div class="detail-kv"><span class="detail-key">文档位置</span><span class="detail-value mono">${sourceFile ? `${escapeHtml2(sourceFile)}:${docLine}` : "无"}</span></div>
        <div class="detail-kv"><span class="detail-key">结构来源</span><span class="detail-value mono">${sourceFile ? `${escapeHtml2(sourceFile)}:${sourceLine}` : "无"}</span></div>
        <div class="detail-kv"><span class="detail-key">默认跳转</span><span class="detail-value mono">${escapeHtml2(targetSummary(defaultTarget))}</span></div>
        <div class="action-row">
          ${actionButton("默认打开", defaultTarget)}
          ${actionButton("打开文档", sourceFile ? {
        targetKind: "framework_definition",
        layer: "framework",
        filePath: sourceFile,
        startLine: docLine,
        endLine: docLine,
        symbol: node.id,
        label: "Framework definition",
        isPrimary: false,
        isEditable: true,
        isDeprecatedAlias: false
      } : null, { muted: true })}
          ${objectValue ? relatedObjectButton(objectValue.objectId, "查看对象详情") : ""}
        </div>
      </section>
      <section class="detail-group">
        <h3 class="detail-section-title">锚点与次级跳转</h3>
        <div class="detail-kv"><span class="detail-key">Correspondence</span><span class="detail-value mono">${escapeHtml2(targetSummary(node.correspondenceAnchor || objectValue?.correspondenceAnchor))}</span></div>
        <div class="detail-kv"><span class="detail-key">Implementation</span><span class="detail-value mono">${escapeHtml2(targetSummary(node.implementationAnchor || objectValue?.implementationAnchor))}</span></div>
        <ul class="detail-list">${formatTargetList(secondaryTargets)}</ul>
      </section>
      <section class="detail-group">
        <h3 class="detail-section-title">关联对象</h3>
        <ul class="detail-list">${renderObjectLinkList(node.relatedObjectIds || [])}</ul>
      </section>
      <section class="detail-group">
        <h3 class="detail-section-title">上游节点</h3>
        <ul class="detail-list">${detailList(upstream)}</ul>
      </section>
      <section class="detail-group">
        <h3 class="detail-section-title">下游节点</h3>
        <ul class="detail-list">${detailList(downstream)}</ul>
      </section>
    `;
      attachDetailActions();
    };
    const renderEdgeDetail = (edgeId) => {
      const edge = model.edge(edgeId);
      if (!edge) {
        renderEmptyDetail();
        return;
      }
      const fromNode = model.node(edge.from);
      const toNode = model.node(edge.to);
      const sourceFile = edge.file || "";
      const sourceLine = edge.line || 1;
      selectionKindPill.textContent = "edge";
      selectionKindPill.className = "pill kind-pill edge-selection";
      inspectorRailValue.textContent = edge.relation;
      inspectorRailValue.title = edge.relation;
      inspectorSummaryValue.textContent = `${fromNode?.label || edge.from} -> ${toNode?.label || edge.to}`;
      inspectorDetailBox.innerHTML = `
      <section class="detail-group">
        <h3 class="detail-section-title">关系概览</h3>
        <div class="detail-kv"><span class="detail-key">起点</span><span class="detail-value">${escapeHtml2(fromNode?.label || edge.from)}</span></div>
        <div class="detail-kv"><span class="detail-key">终点</span><span class="detail-value">${escapeHtml2(toNode?.label || edge.to)}</span></div>
        <div class="detail-kv"><span class="detail-key">关系</span><span class="detail-value mono">${escapeHtml2(edge.relation)}</span></div>
      </section>
      <section class="detail-group">
        <h3 class="detail-section-title">规则与术语</h3>
        <div class="detail-kv"><span class="detail-key">规则</span><span class="detail-value mono">${escapeHtml2(edge.rules || "无")}</span></div>
        <div class="detail-kv"><span class="detail-key">术语</span><span class="detail-value mono">${escapeHtml2(edge.terms || "无")}</span></div>
      </section>
      <section class="detail-group">
        <h3 class="detail-section-title">来源与跳转</h3>
        <div class="detail-kv"><span class="detail-key">结构来源</span><span class="detail-value mono">${sourceFile ? `${escapeHtml2(sourceFile)}:${sourceLine}` : "无"}</span></div>
        <div class="action-row">
          ${sourceFile ? `<button type="button" class="detail-action" data-open-source="1" data-file="${escapeHtml2(sourceFile)}" data-line="${sourceLine}">打开来源</button>` : "无"}
        </div>
      </section>
    `;
      attachDetailActions();
    };
    const updateInspector = (selection2) => {
      currentSelection = selection2;
      if (selection2.kind === "node") {
        renderNodeDetail(selection2.nodeId);
        return;
      }
      if (selection2.kind === "edge") {
        renderEdgeDetail(selection2.edgeId);
        return;
      }
      renderEmptyDetail();
    };
    const renderer = new TreeCanvasRenderer(elements, model, layout, bootstrap.viewSettings, {
      onSelectionChanged: (selection2) => {
        if (!isApplyingFilters && selection2.kind === "node" && normalizeFocusMode(focusSelect.value) !== "all") {
          applyFilters();
          return;
        }
        updateInspector(selection2);
      },
      onNodeOpened: (nodeId) => {
        const node = layout.nodes.get(nodeId);
        const target = nodeDefaultTarget(node || null);
        if (target) {
          openTarget(target);
          return;
        }
        if (node?.file) {
          bridge.openSource(node.file, node.docLine || node.line);
        }
      },
      onEdgeOpened: (edgeId) => {
        const edge = model.edge(edgeId);
        if (edge?.file) {
          bridge.openSource(edge.file, edge.line || 1);
        }
      },
      onStateChanged: () => {
        schedulePersist();
      }
    });
    const applyFilters = () => {
      isApplyingFilters = true;
      try {
        const filter2 = model.computeFilterResult({
          query: searchInput.value,
          focusMode: normalizeFocusMode(focusSelect.value),
          selectedNodeId: renderer.selectedNodeIdOrEmpty()
        });
        renderer.applyFilter(filter2);
        const selectedNodeId = renderer.selectedNodeIdOrEmpty();
        const validationSuffix = model.validationSummary.errorCount ? ` · ${model.validationSummary.errorCount} correspondence issue(s)` : "";
        elements.statusElement.textContent = selectedNodeId ? `Selected ${selectedNodeId}${validationSuffix}` : `Ready${validationSuffix}`;
        schedulePersist();
      } finally {
        isApplyingFilters = false;
      }
    };
    renderer.mount(persistedState);
    applyInspectorPinnedState(inspectorPinned, { persist: false });
    if (persistedState?.selectedNodeId) {
      renderer.selectNode(persistedState.selectedNodeId);
    } else {
      updateInspector({ kind: "none" });
    }
    searchInput.addEventListener("input", () => {
      applyFilters();
    });
    focusSelect.addEventListener("change", () => {
      applyFilters();
    });
    clearFilterButton.addEventListener("click", () => {
      searchInput.value = "";
      focusSelect.value = "all";
      renderer.clearSelection();
      applyFilters();
      renderer.focusAll();
    });
    fitButton.addEventListener("click", () => {
      renderer.focusVisible();
      schedulePersist();
    });
    resetButton.addEventListener("click", () => {
      renderer.resetLayout();
      applyFilters();
    });
    zoomInButton.addEventListener("click", () => {
      renderer.zoomIn();
      schedulePersist();
    });
    zoomOutButton.addEventListener("click", () => {
      renderer.zoomOut();
      schedulePersist();
    });
    inspectorRail.addEventListener("click", () => {
      applyInspectorPinnedState(!inspectorPinned);
    });
    inspectorShell.addEventListener("mouseenter", () => {
      setInspectorExpandedState(true);
    });
    inspectorShell.addEventListener("mouseleave", () => {
      if (!inspectorPinned) {
        setInspectorExpandedState(false);
      }
    });
    inspectorShell.addEventListener("focusin", () => {
      setInspectorExpandedState(true);
    });
    inspectorShell.addEventListener("focusout", () => {
      window.setTimeout(() => {
        if (!inspectorPinned && !inspectorShell.contains(document.activeElement)) {
          setInspectorExpandedState(false);
        }
      }, 0);
    });
    inspectorRail.addEventListener("keydown", (event) => {
      if (!(event instanceof KeyboardEvent)) {
        return;
      }
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        applyInspectorPinnedState(!inspectorPinned);
      }
    });
    pinInspectorButton.addEventListener("click", () => {
      applyInspectorPinnedState(!inspectorPinned);
    });
    elements.scrollElement.addEventListener("keydown", (event) => {
      if (!(event instanceof KeyboardEvent)) {
        return;
      }
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        renderer.moveSelection("left");
        applyFilters();
        return;
      }
      if (event.key === "ArrowRight") {
        event.preventDefault();
        renderer.moveSelection("right");
        applyFilters();
        return;
      }
      if (event.key === "ArrowUp") {
        event.preventDefault();
        renderer.moveSelection("up");
        applyFilters();
        return;
      }
      if (event.key === "ArrowDown") {
        event.preventDefault();
        renderer.moveSelection("down");
        applyFilters();
        return;
      }
      if (event.key === "Enter") {
        event.preventDefault();
        renderer.openSelectedSource();
        return;
      }
      if (event.key === "/") {
        event.preventDefault();
        searchInput.focus();
        searchInput.select();
      }
    });
    applyFilters();
  }
  main();
})();
