/*
 * The MIT License (MIT)
 *
 * Copyright (c) 2016 University of California San Diego
 * Author: Jim Robinson
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

/**
 * Created by jrobinso on 11/27/16.
 */


var igv = (function (igv) {

    igv.TDFSource = function (config) {

        this.windowFunction = config.windowFunction || "mean";
        this.reader = new igv.TDFReader(config);
    };

    igv.TDFSource.prototype.getFeatures = function (chr, bpStart, bpEnd) {

        var self = this,
            bpPerPixel = igv.browser.referenceFrame.bpPerPixel;

        return new Promise(function (fulfill, reject) {

            self.reader.readRootGroup().then(function (group) {

                var zoom = zoomLevelForScale(chr, bpPerPixel),
                    queryChr = self.reader.chrNameMap[chr],
                    maxZoom = self.reader.maxZoom,
                    wf,
                    dataset;

                if (queryChr === undefined) queryChr = chr;
                if (maxZoom === undefined) maxZoom = -1;

                wf = zoom > maxZoom ? "raw" : self.windowFunction;

                self.reader.readDataset(queryChr, wf, zoom).then(function (dataset) {

                    if(dataset == null) {
                        fulfill(null);
                        return;
                    }

                    var tileWidth = dataset.tileWidth,
                        startTile = Math.floor(bpStart / tileWidth),
                        endTile = Math.floor(bpEnd / tileWidth),
                        i,
                        p = [],
                        NTRACKS = 1;   // TODO read this

                    for (i = startTile; i <= endTile; i++) {
                        if(dataset.tiles[i] !== undefined) {
                            p.push(self.reader.readTile(dataset.tiles[i], NTRACKS));
                        }
                    }

                    Promise.all(p).then(function (tiles) {
                        var features = [];
                        tiles.forEach(function (tile) {
                            switch (tile.type) {
                                case "bed":
                                    decodeBedTile(tile, chr, bpStart, bpEnd, bpPerPixel, features);
                                    break;
                                case "variableStep":
                                    decodeVaryTile(tile, chr, bpStart, bpEnd, bpPerPixel, features);
                                    break;
                                case "fixedStep":
                                    decodeFixedTile(tile, chr, bpStart, bpEnd, bpPerPixel, features);
                                    break;
                                default:
                                    reject("Unknown tile type: " + tile.type);
                                    return;
                            }
                        })
                        fulfill(features);

                    }).catch(reject)


                }).catch(reject)
            })
        });
    }

    function decodeBedTile(tile, chr, bpStart, bpEnd, bpPerPixel, features) {

        var nPositions = tile.nPositions,
            starts = tile.start,
            ends = tile.end,
            data = tile.data[0],   // Single track for now
            i;

        for (i = 0; i < nPositions; i++) {

            var s = starts[i];
            var e = ends[i];

            if (e < bpStart) continue;
            if (s > bpEnd) break;

            features.push({
                start: s,
                end: e,
                value: data[i]
            });
        }
    }

    function decodeVaryTile(tile, chr, bpStart, bpEnd, bpPerPixel, features) {

        var nPositions = tile.nPositions,
            starts = tile.start,
            span = tile.span,
            data = tile.data[0],   // Single track for now
            i;

        for (i = 0; i < nPositions; i++) {

            var s = starts[i];
            var e = s + span;

            if (e < bpStart) continue;
            if (s > bpEnd) break;

            features.push({
                start: s,
                end: e,
                value: data[i]
            });
        }
    }

    function decodeFixedTile(tile, chr, bpStart, bpEnd, bpPerPixel, features) {

        var nPositions = tile.nPositions,
            s = tile.start,
            span = tile.span,
            data = tile.data[0],   // Single track for now
            i;

        for (i = 0; i < nPositions; i++) {

            var e = s + span;

            if (e < bpStart) continue;
            if (s > bpEnd) break;

            if(!Number.isNaN(data[i])) {
                features.push({
                    start: s,
                    end: e,
                    value: data[i]
                });
            }

            s = e;
        }
    }


    var log2 = Math.log(2);

    function zoomLevelForScale(chr, bpPerPixel) {

        // Convert bpPerPixel to IGV "zoom" level.   This is a bit convoluted,  IGV computes zoom levels assuming
        // display in a 700 pixel window.  The fully zoomed out view of a chromosome is zoom level "0".
        // Zoom level 1 is magnified 2X,  and so forth

        var chrSize = igv.browser.genome.getChromosome(chr).bpLength;

        return Math.ceil(Math.log(Math.max(0, (chrSize / (bpPerPixel * 700)))) / log2);
    }


    return igv;


})
(igv || {});
