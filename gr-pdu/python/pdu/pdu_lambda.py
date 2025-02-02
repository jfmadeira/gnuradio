#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2015,2021 Tim O'Shea, Jacob Gilbert.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
#


from gnuradio import gr
import numpy as np
import math, pmt, time


class pdu_lambda(gr.basic_block):
    """
    PDU Lambda Block

    This block allows stateless manipulation of PDU metadata fields and uniform vectors
    through python lambda functions. In uniform vector mode the lamnda function will be
    applied with the python-ified uniform vector as the argument. In metadata dictionary
    mode the lambda function will be applied to the python-ified value associated with
    the PMT key the block is configured with.

    The following python modules are imported for use:
        `import numpy as np`
        `import pmt, math, time`
    These should also be imported in the flowgraph implementing this block if utilized.

    Errors are generally silently dropped as all function application is done within a
    try/catch statement. In the event an exception is thrown the data will be emitted
    as it was received.

    Examples of use:
    - Phase demodulation of a complex PDU: Uniform Vector Mode with function:
        `lambda x: np.unwrap(np.angle(x))`
    - Scale metadata field `val1`: Metadata mode, separate QT range block with name `k`:
        `lambda x: k*x`

    This block cannot add or remove metadata fields, which should be done with the
    application specific blocks in-tree or the more generic `message_lambda` block. This
    block also designed to accept and return explicitly PDU type objects, if the PMT
    object type needs to change, use the `message_lambda` block.
    """

    def __init__(self, fn, metadict, key=pmt.PMT_NIL):
        gr.basic_block.__init__(self,
            name="pdu_lambda",
            in_sig=[],out_sig=[])
        self.set_fn(fn)
        self.set_key(key)
        self.metadict_mode = metadict
        self.message_port_register_in(pmt.intern("pdu"))
        self.message_port_register_out(pmt.intern("pdu"))
        self.set_msg_handler(pmt.intern("pdu"), self.handle_msg)

    def handle_msg(self, pdu):
        if self.metadict_mode:
            meta = pmt.car(pdu)
            try:
                val = pmt.to_python(pmt.dict_ref(meta, self.key, pmt.PMT_NIL))
                if val:
                    val = self.fn(val)
                meta = pmt.dict_add(meta, self.key, pmt.to_pmt(val))
            except Exception as e:
                print(e)
                pass
            self.message_port_pub(pmt.intern("pdu"),
                pmt.cons(meta, pmt.cdr(pdu)));

        else: # PDU Vector mode
            vec = pmt.cdr(pdu)
            try:
                vec = pmt.to_pmt(self.fn(pmt.to_python(vec)))
            except Exception as e:
                print(e)
                pass

            self.message_port_pub(pmt.intern("pdu"),
                pmt.cons(pmt.car(pdu), vec));

    def set_fn(self,fn):
        self.fn = fn

    def set_key(self,key):
        self.key = key
