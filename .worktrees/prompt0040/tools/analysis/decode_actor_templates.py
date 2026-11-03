#!/usr/bin/env python3
"""Decode actor graphics templates (arcade maincpu.bin). 8-byte entry:
 word@0 -> +0x1E base; byte@2 -> +0x3A; byte@3 -> +0x01 anim; word@4 -> +0x28; word@6 -> +0x2C.
Record-type table 0x45592 idx=(type-8)*8; family tables 0x45502(var0)/0x45562(varN) idx=family*8;
family-2 boss tables 0x454BA(comp0)/0x454D2(comp3)/0x454EA(else) idx=variant*8."""
import struct,json
d=open('build/regions/maincpu.bin','rb').read()
def ent(a):
    return {'base':'0x%04X'%struct.unpack('>H',d[a:a+2])[0],'f3A':'0x%02X'%d[a+2],
            'anim':'0x%02X'%d[a+3],'f28':'0x%04X'%struct.unpack('>H',d[a+4:a+6])[0],
            'f2C':'0x%04X'%struct.unpack('>H',d[a+6:a+8])[0]}
out={}
# record types 8..0x20 (stop where base looks like code/implausible)
rt={}
for t in range(8,0x21):
    a=0x45592+(t-8)*8
    rt['type_0x%02X'%t]=dict(ent(a),addr='0x%05X'%a)
out['record_type_0x45592']=rt
# family templates 0-11 (12)
for name,base in [('family_var0_0x45502',0x45502),('family_varN_0x45562',0x45562)]:
    fam={}
    for f in range(12):
        fam['family_%d'%f]=dict(ent(base+f*8),addr='0x%05X'%(base+f*8))
    out[name]=fam
# family-2 boss tables, variants 0..3
for name,base in [('boss_comp0_0x454BA',0x454ba),('boss_comp3_0x454D2',0x454d2),('boss_else_0x454EA',0x454ea)]:
    bt={}
    for v in range(4):
        bt['variant_%d'%v]=dict(ent(base+v*8),addr='0x%05X'%(base+v*8))
    out[name]=bt
json.dump(out,open('analysis/actor_decompilation/actor_templates.json','w'),indent=1)
# print compact
for sec in out:
    print('===',sec,'===')
    for k,v in out[sec].items():
        print(' %-14s base=%s anim=%s +3A=%s +28=%s +2C=%s'%(k,v['base'],v['anim'],v['f3A'],v['f28'],v['f2C']))
