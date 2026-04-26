import { Graph } from './Graph.js';
/**
 * Handles diagram file operations and SVG content parsing
 * Works directly with file paths
 */
export declare class GraphFileManager {
    static default: GraphFileManager;
    /**
     * Load a graph from a .drawio.svg file
     */
    loadGraphFromSvg(filePath: string): Promise<Graph>;
    /**
     * Save a graph to a .drawio.svg file
     * @param {Graph} graph - Graph instance to save
     * @param {string} filePath - Absolute or relative path to save the .drawio.svg file
     */
    saveGraphToSvg(graph: Graph, filePath: string): Promise<void>;
    /**
     * Get diagram statistics from file
     * @param {string} filePath - Absolute or relative path to the file
     * @returns {Object} - Object with nodeCount and edgeCount
     */
    getDiagramStats(filePath: string): Promise<{
        nodeCount: number;
        edgeCount: number;
    }>;
    /**
     * Extract raw XML data from SVG content attribute for direct mxGraph loading
     * @param {string} svgContent - Raw SVG file content
     * @returns {string|null} - Raw mxGraph XML data or null if extraction fails
     */
    extractXMLFromSVG(svgContent: string): string;
}
//# sourceMappingURL=GraphFileManager.d.ts.map