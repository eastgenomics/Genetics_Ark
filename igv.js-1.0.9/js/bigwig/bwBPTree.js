/*
 * The MIT License (MIT)
 *
 * Copyright (c) 2014 Broad Institute
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
 * Created by jrobinso on 4/7/14.
 */


var igv = (function (igv) {

    var BPTREE_MAGIC_LTH = 0x78CA8C91;
    var BPTREE_MAGIC_HTL = 0x918CCA78;
    var BPTREE_HEADER_SIZE = 32;


    igv.BPTree = function (binaryParser, startOffset) {

        var self = this,
            genome = igv.browser ? igv.browser.genome : null;

        this.header = {};
        this.header.magic = binaryParser.getInt();
        this.header.blockSize = binaryParser.getInt();
        this.header.keySize = binaryParser.getInt();
        this.header.valSize = binaryParser.getInt();
        this.header.itemCount = binaryParser.getLong();
        this.header.reserved = binaryParser.getLong();

        this.dictionary = {};

        // Recursively walk tree to populate dictionary
        readTreeNode(binaryParser, -1, this.header.keySize, this.dictionary);

        var itemSize = 8 + this.header.keySize;
        var minSize = 4 + itemSize;   // Bytes for a node with 1 item

        function readTreeNode(byteBuffer, offset, keySize, dictionary) {

            if (offset >= 0) byteBuffer.position = offset;

            var type = byteBuffer.getByte(),
                reserved = byteBuffer.getByte(),
                count = byteBuffer.getUShort(),
                i,
                key,
                chromId,
                chromSize,
                childOffset,
                bufferOffset,
                currOffset;


            if (type == 1) {

                for (i = 0; i < count; i++) {

                    key = byteBuffer.getFixedLengthTrimmedString(keySize);
                    chromId = byteBuffer.getInt();
                    chromSize = byteBuffer.getInt();

                    if(genome) key = genome.getChromosomeName(key);  // Translate to canonical chr name
                    dictionary[key] = chromId;

                }
            }
            else { // non-leaf

                for (i = 0; i < count; i++) {

                    key = byteBuffer.getFixedLengthTrimmedString(keySize);
                    childOffset = byteBuffer.getLong();
                    bufferOffset = childOffset - startOffset;
                    currOffset = byteBuffer.position;
                    readTreeNode(byteBuffer, bufferOffset, keySize, dictionary);
                    byteBuffer.position = currOffset;
                }
            }

        }
    }


    return igv;

})(igv || {});
