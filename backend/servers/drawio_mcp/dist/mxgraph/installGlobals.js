function defineGlobal(name, value) {
    const descriptor = Object.getOwnPropertyDescriptor(globalThis, name);
    if (!descriptor || descriptor.writable || descriptor.set) {
        Reflect.set(globalThis, name, value);
        return;
    }
    if (descriptor.configurable) {
        Object.defineProperty(globalThis, name, {
            configurable: true,
            writable: true,
            value,
        });
        return;
    }
    throw new Error(`Cannot install global ${name}: property is not writable or configurable.`);
}
export function installDomGlobals(window) {
    defineGlobal("window", window);
    defineGlobal("document", window.document);
    defineGlobal("XMLSerializer", window.XMLSerializer);
    defineGlobal("navigator", window.navigator);
    defineGlobal("location", window.location);
    defineGlobal("DOMParser", window.DOMParser);
}
//# sourceMappingURL=installGlobals.js.map