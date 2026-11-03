logerror "SWORD_TRACE_ARMED build=0279 fixup_entry=07391C fixup_store=07397A\n"
bp 7391c,b@ff78a8==1 && (w@ff1116==1 || w@ff1116==4),{ logerror "SWORD_PAL_COMMIT cyc=%d pc=%06X front=%d emitted=%d sprite_ctrl=%04X action=%04X variant=%04X active=%04X phase=%04X\n",totalcycles(),pc,w@ff66ce,w@ff77a8,w@ff7794,w@ff10e8,w@ff1116,w@ff1108,w@ff110a ; g }
bp 7397a,b@ff78a8==1 && (w@ff1116==1 || w@ff1116==4) && b@(ff66d2+d5)==3,{ logerror "SWORD_PAL_FIX cyc=%d pc=%06X front=%d slot=%d emitted=%d nibble=%02X force=%02X sprite_ctrl=%04X colbank=%04X pre=%04X post=%04X sat_addr=%08X action=%04X variant=%04X active=%04X phase=%04X\n",totalcycles(),pc,w@ff66ce,d5,d6,b@(ff66d2+d5),b@(ff6722+d5),w@ff7794,d7,w@(a3+4),d1,a3,w@ff10e8,w@ff1116,w@ff1108,w@ff110a ; g }
g
