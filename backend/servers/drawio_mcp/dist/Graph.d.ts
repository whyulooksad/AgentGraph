import { mxGraph } from './mxgraph/index.js';
export type LinkNodesParams = {
    from: string;
    to: string;
    title?: string;
    style?: Record<string, any>;
    undirected?: boolean;
};
export declare class Graph {
    static Kinds: {
        Rectangle: {
            style: {
                rounded: number;
                whiteSpace: string;
                html: number;
            };
            width: number;
            height: number;
        };
        Ellipse: {
            style: {
                ellipse: string;
                whiteSpace: string;
                html: number;
            };
            width: number;
            height: number;
        };
        Cylinder: {
            style: string;
            width: number;
            height: number;
        };
        Cloud: {
            style: string;
            width: number;
            height: number;
        };
        Square: {
            style: string;
            width: number;
            height: number;
        };
        Circle: {
            style: string;
            width: number;
            height: number;
        };
        Step: {
            style: string;
            width: number;
            height: number;
        };
        Actor: {
            style: string;
            width: number;
            height: number;
        };
        Text: {
            style: string;
            width: number;
            height: number;
        };
        RoundedRectangle: {
            style: string;
            width: number;
            height: number;
        };
    };
    static normalizeKind(kind: string): string;
    graph: typeof mxGraph;
    container: HTMLDivElement;
    constructor();
    get root(): any;
    get model(): any;
    toStyleString(data: any): string;
    /**
     * Parses a style definition into a key-value object.
     *
     * Handles both string and object style formats:
     * - String format: "key1=value1;key2=value2;" (semicolon-separated key=value pairs)
     * - Object format: { key1: "value1", key2: "value2" } (plain object)
     *
     * For string styles, empty values (e.g., "key=") are converted to empty strings.
     * For object styles, the input is shallow copied to avoid mutation.
     *
     * @param style - Style definition as either a semicolon-separated string or object
     * @returns Object with style properties as key-value pairs
     *
     * @example
     * parseStyle("rounded=1;whiteSpace=wrap;html=1")
     * // Returns: { rounded: "1", whiteSpace: "wrap", html: "1" }
     *
     * @example
     * parseStyle({ rounded: 1, whiteSpace: "wrap" })
     * // Returns: { rounded: 1, whiteSpace: "wrap" }
     */
    private parseStyle;
    /**
     * Converts a style object into a semicolon-separated style string.
     *
     * This function is the inverse of parseStyle(), converting a key-value object
     * back into the string format used by mxGraph. Properties with undefined values
     * are skipped, while properties with falsy values (empty string, 0, false) are
     * included with just the key name (no equals sign).
     *
     * @param style - Object with style properties as key-value pairs
     * @returns Semicolon-separated style string in format "key1=value1;key2;key3=value3;"
     *
     * @example
     * stringifyStyle({ rounded: "1", whiteSpace: "wrap", html: "1" })
     * // Returns: "rounded=1;whiteSpace=wrap;html=1;"
     *
     * @example
     * stringifyStyle({ rounded: "", whiteSpace: "wrap" })
     * // Returns: "rounded;whiteSpace=wrap;"
     */
    private stringifyStyle;
    /**
     * Adjusts the style string for a specific node kind, applying kind-specific modifications.
     *
     * For RoundedRectangle nodes, this function modifies the corner radius by setting:
     * - absoluteArcSize to '1' to enable absolute arc sizing
     * - arcSize to the calculated value (corner_radius * 2, default to 24)
     *
     * @param style - The base style string to modify
     * @param kind - The node kind (e.g., 'RoundedRectangle', 'Rectangle', etc.)
     * @param corner_radius - The desired corner radius in pixels (only applies to RoundedRectangle)
     * @returns The modified style string with kind-specific adjustments applied
     */
    private adjustStyleByKind;
    addNode({ id, title, parent, kind, x, y, corner_radius, ...rest }: {
        [x: string]: any;
        id: any;
        title: any;
        parent?: string;
        kind?: string;
        x?: number;
        y?: number;
        corner_radius: any;
    }): any;
    editNode({ id, title, kind, x, y, width, height, corner_radius }: {
        id: any;
        title: any;
        kind: any;
        x: any;
        y: any;
        width: any;
        height: any;
        corner_radius: any;
    }): this;
    linkNodes({ from, to, title, style, undirected }: LinkNodesParams): any;
    removeNodes(ids: string[]): this;
    /**
     * Executes a given layout algorithm on the graph's root element.
     *
     * @param layout - An object with an `execute` method, typically an mxGraph layout instance.
     * @param args - Additional arguments to pass to the layout's `execute` method.
     * @returns The current Graph instance for method chaining.
     *
     * @remarks
     * This method is used internally to apply various mxGraph layout algorithms
     * (e.g., hierarchical, circle, organic) to the graph. The layout is executed
     * on the root element of the graph, and any additional arguments are forwarded
     * to the layout's `execute` method.
     */
    private runLayout;
    /**
     * Applies a layout algorithm to the graph.
     *
     * @param params - An object containing the layout algorithm and optional options.
     * @param params.algorithm - The name of the layout algorithm to apply. Supported values are:
     *   - 'hierarchical'
     *   - 'circle'
     *   - 'organic'
     *   - 'compact-tree'
     *   - 'radial-tree'
     *   - 'partition'
     *   - 'stack'
     * @param params.options - Optional parameters for the layout algorithm.
     *   - For 'hierarchical', you may specify `direction` as either 'top-down' or 'left-right'.
     *
     * @throws {Error} If an unsupported algorithm is provided, or if an invalid direction is specified for hierarchical layout.
     *
     * @returns {Graph} The current Graph instance for method chaining.
     *
     * @example
     * graph.applyLayout({ algorithm: 'hierarchical', options: { direction: 'left-right' } });
     * graph.applyLayout({ algorithm: 'circle' });
     */
    applyLayout({ algorithm, options }: {
        algorithm: string;
        options?: any;
    }): this;
    toXML(): any;
    /**
     * Static method to create a Graph instance from XML
     * @param {string} xmlString - XML string in mxGraph format
     * @returns {Graph} - New Graph instance loaded from XML
     */
    static fromXML(xmlString: any): Graph;
}
//# sourceMappingURL=Graph.d.ts.map