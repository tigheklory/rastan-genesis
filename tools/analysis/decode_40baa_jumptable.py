#!/usr/bin/env python3
"""Decode the 0x40BAA actor-state jump table (arcade maincpu.bin).
0x40baa: d0=a4@(5); d0*=2; a0=0x40bc2+d0; d0=word@a0; jmp *(0x40bc2+d0).
Table = signed 16-bit self-relative offsets based at 0x40bc2, indexed by state a4@(5)."""
import struct
d=open('build/regions/maincpu.bin','rb').read()
BASE=0x40bc2
HANDLER_NAME={
 0x41180:'actor_ground_scanner_41180 (state0: latent scanner/hunter)',
 0x41cf4:'jmp 0x473b8 FLYING-enemy update',
 0x41cee:'jmp 0x47140 WALKING-enemy update',
 0x41cea:'braw 0x4684e (state 0x11 handler)',
 0x40ccc:'ARMORED MAN (base 0x0A73 sword -> 0x0A5A ball&chain, comp2, fam0x0C)',
 0x40c08:'state0x10 handler (anim-table param setup 0x40c0e)',
 0x40e48:'braw 0x43636','0x40e4c':'','0x40e50':'braw 0x43840',
}
TARGETS={0x40e48:'braw 0x43636',0x40e4c:'braw 0x4375c',0x40e50:'braw 0x43840',
 0x40e54:'braw 0x43ae6',0x40e58:'braw 0x43f88',0x40e5c:'braw 0x44082',
 0x40e60:'braw 0x4396a',0x40e64:'braw 0x43b32',0x40e68:'braw 0x43ecc',
 0x40e6c:'braw 0x4415a',0x40e70:'braw 0x44082',0x40e88:'local marker-check+0x13e gate',
 0x40eda:'state0x1F',0x40ede:'state0x20'}
print("state | handler PC | notes")
for st in range(0x23):
    w=struct.unpack('>h', d[BASE+st*2:BASE+st*2+2])[0]
    tgt=BASE+w
    note=HANDLER_NAME.get(tgt, TARGETS.get(tgt,''))
    print("0x%02X | 0x%05X | %s"%(st,tgt,note))
