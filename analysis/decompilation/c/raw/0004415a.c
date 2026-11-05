/* ORIGINAL ARCADE PC: 0x0004415A  marker-chain terrain/hazard transform handler
 * (actor state 0x1C/0x1D/0x21 band). RECONSTRUCTED_FROM_68000.  Status: COMPLETE.
 *
 * Reached only through the actor state dispatcher jump table 0x40BC2 (no direct xref,
 * which is why Ghidra lists no separate entry for it). %a4 = ActorRecord, %a5 = A5 workram.
 *
 * Structure (0x4415A..0x442B8 own body; 0x442BA is the SHARED H5 anim-countdown tail that
 * belongs to the enclosing behavior framework, entered by fall-through, not part of this body):
 *
 *   1. Y-band gate (0x4415A): if the actor's world-Y (+0x1A) is in [472,488) it is on the
 *      active terrain band and proceeds to materialize; otherwise it re-checks its marker
 *      (0x40E74) and, if that returns 0 (marker not yet due), hands control to the shared
 *      anim tail 0x442BA.
 *   2. Low 0x13E-band (g_prog13e < 0x2F, 0x44182): unconditionally re-targets (0x4103A) to
 *      base 0x0224 (the pit-flame hazard, Tighe visual identity), saving the marker ordinal
 *      (+0x2F) to g_char22b and selecting next-char 0x52 when +0x2F!=0 else 0x4C.
 *   3. High 0x13E-band (g_prog13e >= 0x2F, 0x441A2): a (current-marker +0x0D, band-char
 *      g_prog13e) matrix. The overwhelming product is base 0x0224 (pit flame) with a
 *      per-cell next-char; a few cells emit base 0x0266 or 0x00F4, tail-call the 0x1A band
 *      handler (0x43D44), or retire the record (0x4092E) when the (char,band) pair is not a
 *      legal continuation.
 *
 * Every (base,next,flags) value below is read verbatim from maincpu.bin; no branch invented. */
#include "raw_common.h"

/* shared H5 anim-countdown tail at 0x442BA (decrements +0x09 / advances +0x08 program). */
extern void arc_anim_tail_442ba(uint8_t *r);

void arcade_4415a(uint8_t *r)
{
    uint16_t y = W(r, 0x1a);
    if (!(y >= 472 && y < 488)) {          /* 0x4415A..0x4416A Y-band gate */
        if (arc_40e74(r) == 0) {           /* 0x4416C marker recheck */
            arc_anim_tail_442ba(r);        /* 0x44172 -> shared anim tail 0x442BA */
            return;
        }
    }

    uint16_t band = g_prog13e;             /* 0x44176 a5@0x13E band-char */
    if (band < 0x2f) {                     /* 0x4417A low band */
        g_char22b = B(r, 0x2f);            /* 0x44182 save marker ordinal +0x2F */
        arc_4103a(r);                      /* 0x44188 re-target */
        W(r, 0x1e) = 0x0224;               /* 0x4418C base = pit flame */
        B(r, 0x0d) = (uint8_t)(g_char22b != 0 ? 0x52 : 0x4c); /* 0x44192..0x4419C next-char */
        return;
    }

    /* 0x441A2 high-band (current-marker +0x0D) x (band g_prog13e) transform matrix. */
    uint8_t cur = B(r, 0x0d);
    if (cur == 0x46) {                     /* 'F' marker */
        if (band == 0x56) {                /* 0x441EE */
            arc_4103a(r); W(r, 0x1e) = 0x0266; B(r, 0x0d) = 0x46; return;
        }
        if (band == 0x40) { arc_4092e(r); return; }   /* 0x44200 retire */
        if (band >= 0x41) {                /* 0x441D0 */
            arc_4103a(r); W(r, 0x1e) = 0x0224; B(r, 0x0d) = 0x68;
            B(r, 0x30) = 1; B(r, 0x38) = 2; return;
        }
        arc_4103a(r); W(r, 0x1e) = 0x0224; B(r, 0x0d) = 0x53; return; /* 0x441BE band<0x41 */
    }
    if (cur == 0x6c) {                     /* 'l' marker, 0x44206 */
        if (band != 0x3f) { arc_4092e(r); return; }   /* 0x44200 retire */
        arc_4103a(r); W(r, 0x1e) = 0x0224; B(r, 0x0d) = 0x54; return; /* 0x44212 */
    }
    if (cur == 0x44) {                     /* 'D' marker, 0x44224 */
        arc_4103a(r); W(r, 0x1e) = 0x0224; B(r, 0x0d) = 0x67;
        B(r, 0x30) = 1; B(r, 0x38) = 2; return;       /* 0x4422A */
    }
    if (cur == 0x71) {                     /* 'q' marker, 0x44248 */
        if (band == 0x47) {                /* 0x44254 */
            arc_4103a(r); W(r, 0x1e) = 0x0224; B(r, 0x0d) = 0x67; B(r, 0x38) = 2; return;
        }
        if (band == 0x4c) {                /* 0x44272 */
            arc_4103a(r); W(r, 0x1e) = 0x00f4; B(r, 0x0d) = 0x4f; return;
        }
        if (band == 0x74) {                /* 0x4428A: next 0x71, tail into 0x1A handler */
            arc_4103a(r); B(r, 0x0d) = 0x71; arc_43d44(r); return;
        }
        if (band == 0x77 || band == 0x7b) {/* 0x4429E / 0x442B8 */
            arc_4103a(r); W(r, 0x1e) = 0x0224; B(r, 0x0d) = 0x4c; return;
        }
        arc_4092e(r); return;              /* 0x44200 retire (no legal continuation) */
    }
    arc_4092e(r);                          /* 0x44200 retire (unknown marker) */
}
