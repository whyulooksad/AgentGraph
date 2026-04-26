import './jsdom.js';
import mxgraph from 'mxgraph';
export const { mxGraph, mxGraphModel, mxGeometry, mxCodec, mxPoint, mxUtils, mxHierarchicalLayout, mxConstants, mxCircleLayout, mxSwimlaneLayout, mxFastOrganicLayout, mxCompactTreeLayout, mxRadialTreeLayout, mxPartitionLayout, mxStackLayout } = mxgraph({
    mxImageBasePath: "./src/images",
    mxBasePath: "./src"
});
window.mxGraphModel = mxGraphModel;
window.mxGeometry = mxGeometry;
window.mxPoint = mxPoint;
//# sourceMappingURL=index.js.map