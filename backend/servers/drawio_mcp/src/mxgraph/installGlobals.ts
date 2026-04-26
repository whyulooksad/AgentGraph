type GlobalName =
  | "window"
  | "document"
  | "XMLSerializer"
  | "navigator"
  | "location"
  | "DOMParser";

function defineGlobal(name: GlobalName, value: unknown) {
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

export type DomLikeWindow = {
  document: Document;
  XMLSerializer: typeof globalThis.XMLSerializer;
  navigator: Navigator;
  location: Location;
  DOMParser: typeof globalThis.DOMParser;
};

export function installDomGlobals(window: DomLikeWindow) {
  defineGlobal("window", window);
  defineGlobal("document", window.document);
  defineGlobal("XMLSerializer", window.XMLSerializer);
  defineGlobal("navigator", window.navigator);
  defineGlobal("location", window.location);
  defineGlobal("DOMParser", window.DOMParser);
}
