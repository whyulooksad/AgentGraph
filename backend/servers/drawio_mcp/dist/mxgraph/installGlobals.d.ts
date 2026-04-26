export type DomLikeWindow = {
    document: Document;
    XMLSerializer: typeof globalThis.XMLSerializer;
    navigator: Navigator;
    location: Location;
    DOMParser: typeof globalThis.DOMParser;
};
export declare function installDomGlobals(window: DomLikeWindow): void;
//# sourceMappingURL=installGlobals.d.ts.map