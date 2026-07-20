
/* ===== arcade_pc 0x000000 vector_2e_target_000000 ===== */

/* WARNING: Control flow encountered bad instruction data */

void vector_2e_target_000000(void)

{
  undefined1 *in_A0;
  byte *in_A1;
  
  *in_A0 = *in_A0;
  *in_A1 = *in_A1 | 0xcc;
  *in_A1 = *in_A1 | 0xe8;
  *in_A1 = *in_A1 | 8;
  *in_A1 = *in_A1 | 0x30;
  *in_A1 = *in_A1 | 0x50;
  *in_A1 = *in_A1 | 0x74;
  *in_A1 = *in_A1 | 0x9a;
  *in_A1 = *in_A1 | 0xc4;
  *in_A1 = *in_A1 | 0xde;
  *in_A1 = *in_A1 | 2;
                    /* WARNING: Bad instruction - Truncating control flow here */
  halt_baddata();
}



/* ===== arcade_pc 0x000100 FUN_00000100 ===== */

void FUN_00000100(void)

{
  short sVar1;
  byte bVar2;
  int unaff_A5;
  
  FUN_0000016a();
  FUN_00000264();
  FUN_00000180();
  *(undefined2 *)(unaff_A5 + 10) = 0;
  FUN_00000180();
  FUN_0000052a();
  FUN_000002ca();
  do {
    sVar1 = *(short *)(unaff_A5 + 2);
    if (sVar1 != 0) {
LAB_00000132:
      if (sVar1 < 2) {
        FUN_00000502();
        FUN_0000038e();
        if (*(short *)(unaff_A5 + 10) == -1) {
          do {
            FUN_000003a4();
            FUN_000004a2();
            FUN_00000252();
          } while( true );
        }
        FUN_000001e2();
        *(short *)(unaff_A5 + 2) = *(short *)(unaff_A5 + 2) + 1;
      }
      do {
        FUN_000003a4();
        FUN_000005cc();
        FUN_00000252();
      } while( true );
    }
    bVar2 = DAT_00390007;
    if ((bVar2 & 8) == 0) {
      *(short *)(unaff_A5 + 2) = *(short *)(unaff_A5 + 2) + 1;
      goto LAB_00000132;
    }
    FUN_00000252();
  } while( true );
}



/* ===== arcade_pc 0x00016A FUN_0000016a ===== */

void FUN_0000016a(void)

{
  DAT_00c20002 = 0;
  DAT_00c40002 = 0;
  return;
}



/* ===== arcade_pc 0x000180 FUN_00000180 ===== */

void FUN_00000180(void)

{
  short sVar1;
  short sVar2;
  short *psVar3;
  short *psVar4;
  int unaff_A5;
  
  FUN_000001e2();
  do {
    FUN_000001c2();
  } while (DAT_0000023a != -1);
  psVar3 = &DAT_0000023c;
  psVar4 = &DAT_0010c010;
  do {
    if (*psVar3 == 0xf0) {
      return;
    }
    sVar1 = *psVar3;
    sVar2 = *psVar4;
    psVar3 = psVar3 + 1;
    psVar4 = psVar4 + 1;
  } while (sVar1 == sVar2);
  *(undefined2 *)(unaff_A5 + 10) = 0xffff;
  return;
}



/* ===== arcade_pc 0x0001C2 FUN_000001c2 ===== */

void FUN_000001c2(void)

{
  ushort unaff_D3w;
  ushort unaff_D4w;
  short *unaff_A6;
  
  FUN_000001d8();
  *unaff_A6 = (unaff_D3w & 0xf) + (unaff_D4w & 0xf) * 0x10;
  return;
}



/* ===== arcade_pc 0x0001D8 FUN_000001d8 ===== */

void FUN_000001d8(void)

{
  FUN_000001e2();
  FUN_00000210();
  return;
}



/* ===== arcade_pc 0x0001E2 FUN_000001e2 ===== */

void FUN_000001e2(void)

{
  byte in_D0b;
  uint unaff_D5;
  
  do {
    PC060HA_master_port_3e0001 = 0;
    PC060HA_master_comm_3e0003 = in_D0b;
    PC060HA_master_comm_3e0003 = in_D0b >> 4;
    in_D0b = FUN_000006aa();
  } while ((unaff_D5 & 1) == 0);
  do {
    FUN_000006aa();
  } while ((unaff_D5 & 1) != 0);
  return;
}



/* ===== arcade_pc 0x000210 FUN_00000210 ===== */

void FUN_00000210(void)

{
  undefined1 uVar1;
  uint unaff_D5;
  
  do {
    FUN_000006aa();
  } while ((unaff_D5 & 4) == 0);
  PC060HA_master_port_3e0001 = 0;
  uVar1 = PC060HA_master_comm_3e0003;
  uVar1 = PC060HA_master_comm_3e0003;
  do {
    FUN_000006aa();
  } while ((unaff_D5 & 4) != 0);
  return;
}



/* ===== arcade_pc 0x000252 FUN_00000252 ===== */

void FUN_00000252(void)

{
  short sVar1;
  
  sVar1 = 0x50;
  do {
    Ram003c0000 = 0;
    sVar1 = sVar1 + -1;
  } while (sVar1 != 0);
  return;
}



/* ===== arcade_pc 0x000264 FUN_00000264 ===== */

void FUN_00000264(void)

{
  ushort uVar1;
  short sVar2;
  short *psVar3;
  short *psVar4;
  ushort *puVar5;
  ushort *puVar6;
  
  psVar3 = &CLCS_palette_RAM;
  puVar5 = &DAT_000002a6;
  while( true ) {
    puVar6 = puVar5 + 1;
    uVar1 = *puVar5;
    if (uVar1 == 0xffff) break;
    sVar2 = 0xf;
    *psVar3 = 0;
    psVar4 = psVar3 + 1;
    do {
      *psVar4 = (uVar1 & 0xf00) << 3;
      *psVar4 = (uVar1 & 0xf0) * 4 + *psVar4;
      psVar3 = psVar4 + 1;
      *psVar4 = (uVar1 & 0xf) * 2 + *psVar4;
      sVar2 = sVar2 + -1;
      psVar4 = psVar3;
      puVar5 = puVar6;
    } while (sVar2 != 0);
  }
  return;
}



/* ===== arcade_pc 0x0002CA FUN_000002ca ===== */

void FUN_000002ca(void)

{
  short sVar1;
  short sVar2;
  undefined2 *puVar3;
  undefined2 *puVar4;
  undefined2 *puVar5;
  undefined2 *puVar6;
  undefined2 *puVar7;
  
  puVar3 = &DAT_00c08218;
  puVar4 = &DAT_00c08318;
  sVar2 = 0xe;
  do {
    sVar1 = 0x10;
    puVar5 = puVar3;
    puVar7 = puVar4;
    do {
      *puVar5 = 0;
      puVar5[1] = 0x21;
      puVar6 = puVar5 + 3;
      puVar5[2] = 0x4000;
      puVar5 = puVar5 + 4;
      *puVar6 = 0x21;
      *puVar7 = 0x8000;
      puVar7[1] = 0x21;
      puVar6 = puVar7 + 3;
      puVar7[2] = 0xc000;
      puVar7 = puVar7 + 4;
      *puVar6 = 0x21;
      sVar1 = sVar1 + -1;
    } while (sVar1 != 0);
    puVar3 = puVar3 + 0x100;
    puVar4 = puVar4 + 0x100;
    sVar2 = sVar2 + -1;
  } while (sVar2 != 0);
  sVar2 = 4;
  do {
    FUN_00000350();
    sVar2 = sVar2 + -1;
  } while (sVar2 != 0);
  return;
}



/* ===== arcade_pc 0x000350 FUN_00000350 ===== */

void FUN_00000350(void)

{
  short in_D0w;
  short sVar1;
  uint unaff_D3;
  int in_A0;
  int in_A1;
  int unaff_A2;
  int unaff_A3;
  
  do {
    sVar1 = 4;
    do {
      *(short *)(in_A0 + unaff_D3) = in_D0w;
      *(undefined2 *)(in_A0 + 2 + unaff_D3) = 0x19;
      *(short *)(in_A1 + unaff_D3) = in_D0w;
      *(undefined2 *)(in_A1 + 2 + unaff_D3) = 0x19;
      *(short *)(unaff_A2 + unaff_D3) = in_D0w;
      *(undefined2 *)(unaff_A2 + 2 + unaff_D3) = 0x19;
      *(short *)(unaff_A3 + unaff_D3) = in_D0w;
      *(undefined2 *)(unaff_A3 + 2 + unaff_D3) = 0x19;
      unaff_D3 = unaff_D3 + 4;
      sVar1 = sVar1 + -1;
    } while (sVar1 != 0);
    in_D0w = in_D0w + 1;
  } while (unaff_D3 < 0x40);
  return;
}



/* ===== arcade_pc 0x00038E FUN_0000038e ===== */

void FUN_0000038e(void)

{
  int extraout_D1;
  
  do {
    FUN_0003bb48();
  } while (extraout_D1 != 0x33);
  return;
}



/* ===== arcade_pc 0x0003A4 FUN_000003a4 ===== */

void FUN_000003a4(void)

{
  undefined1 uVar1;
  
  uVar1 = DAT_00390007;
  FUN_000004b2();
  FUN_000004b2();
  FUN_000004b2();
  FUN_000004b2();
  FUN_000004b2();
  FUN_000004b2();
  FUN_000004b2();
  uVar1 = DAT_00390001;
  FUN_000004b2();
  FUN_000004b2();
  FUN_000004b2();
  FUN_000004b2();
  FUN_000004b2();
  FUN_000004b2();
  uVar1 = DAT_00390003;
  FUN_000004b2();
  FUN_000004b2();
  FUN_000004b2();
  FUN_000004b2();
  FUN_000004b2();
  FUN_000004b2();
  uVar1 = DAT_00390009;
  FUN_000004c8();
  uVar1 = DAT_0039000b;
  FUN_000004c8();
  return;
}



/* ===== arcade_pc 0x0004A2 FUN_000004a2 ===== */

void FUN_000004a2(void)

{
  undefined2 uVar1;
  char cVar2;
  undefined2 *in_A1;
  char *pcVar3;
  undefined2 *unaff_A2;
  short *psVar4;
  
  uVar1 = *in_A1;
  pcVar3 = (char *)(in_A1 + 1);
  while( true ) {
    cVar2 = *pcVar3;
    if (cVar2 == '\0') break;
    psVar4 = unaff_A2 + 1;
    *unaff_A2 = uVar1;
    unaff_A2 = unaff_A2 + 2;
    *psVar4 = (short)cVar2;
    pcVar3 = pcVar3 + 1;
  }
  return;
}



/* ===== arcade_pc 0x0004B2 FUN_000004b2 ===== */

short FUN_000004b2(void)

{
  short sVar1;
  
  sVar1 = FUN_000004a2();
  return sVar1 + 1;
}



/* ===== arcade_pc 0x0004C8 FUN_000004c8 ===== */

void FUN_000004c8(void)

{
  short sVar1;
  
  do {
    sVar1 = FUN_000004a2();
  } while (sVar1 != 0);
  return;
}



/* ===== arcade_pc 0x000502 FUN_00000502 ===== */

void FUN_00000502(void)

{
  short sVar1;
  undefined2 *puVar2;
  undefined2 *puVar3;
  undefined2 *puVar4;
  
  puVar2 = &DAT_00c08000;
  do {
    sVar1 = 0x28;
    puVar3 = puVar2;
    do {
      puVar4 = puVar3 + 1;
      *puVar3 = 0;
      puVar3 = puVar3 + 2;
      *puVar4 = 0x20;
      sVar1 = sVar1 + -1;
    } while (sVar1 != 0);
    puVar2 = puVar2 + 0x80;
  } while (puVar2 < &DAT_00c0c000);
  return;
}



/* ===== arcade_pc 0x00052A FUN_0000052a ===== */

void FUN_0000052a(void)

{
  FUN_0000057c();
  FUN_0000057c();
  FUN_0000057c();
  FUN_0000057c();
  FUN_0000057c();
  return;
}



/* ===== arcade_pc 0x00057C FUN_0000057c ===== */

void FUN_0000057c(void)

{
  short sVar1;
  short *in_A0;
  short *psVar2;
  short *in_A1;
  
  while( true ) {
    sVar1 = *in_A0;
    *in_A0 = 0;
    if ((*in_A0 != 0) || (*in_A0 = -1, *in_A0 != -1)) break;
    psVar2 = in_A0 + 1;
    *in_A0 = sVar1;
    in_A0 = psVar2;
    if (in_A1 <= psVar2) {
      return;
    }
  }
  *in_A0 = sVar1;
  FUN_0003bb48();
  do {
    FUN_00000252();
  } while( true );
}



/* ===== arcade_pc 0x0005CC FUN_000005cc ===== */

void FUN_000005cc(void)

{
  byte bVar1;
  int unaff_A5;
  
  bVar1 = DAT_00390007;
  if ((bVar1 & 8) != 0) {
    *(undefined2 *)(unaff_A5 + 8) = 0;
  }
  if (*(short *)(unaff_A5 + 8) == 0) {
    Ram003c0000 = 0;
    *(short *)(unaff_A5 + 6) = *(short *)(unaff_A5 + 6) + 1;
    if (*(short *)(unaff_A5 + 6) == 0x50) {
      bVar1 = DAT_00390001;
      if (((bVar1 & 1) == 0) &&
         (*(short *)(unaff_A5 + 4) = *(short *)(unaff_A5 + 4) + 1, 0x2f < *(short *)(unaff_A5 + 4)))
      {
        *(undefined2 *)(unaff_A5 + 4) = 0;
      }
      bVar1 = DAT_00390001;
      if (((bVar1 & 2) == 0) &&
         (*(short *)(unaff_A5 + 4) = *(short *)(unaff_A5 + 4) + -1, *(short *)(unaff_A5 + 4) < 0)) {
        *(undefined2 *)(unaff_A5 + 4) = 0x2f;
      }
      FUN_00000664();
      *(undefined2 *)(unaff_A5 + 6) = 0;
    }
    bVar1 = DAT_00390007;
    if ((bVar1 & 8) == 0) {
      FUN_000001e2();
      FUN_000001e2();
      *(short *)(unaff_A5 + 8) = *(short *)(unaff_A5 + 8) + 1;
    }
  }
  return;
}



/* ===== arcade_pc 0x000664 FUN_00000664 ===== */

void FUN_00000664(void)

{
  FUN_0000067c();
  FUN_0000067c();
  return;
}



/* ===== arcade_pc 0x00067C FUN_0000067c ===== */

void FUN_0000067c(void)

{
  short in_D1w;
  undefined2 *in_A0;
  
  if (9 < in_D1w) {
    in_D1w = in_D1w + 7;
  }
  *in_A0 = 0;
  in_A0[1] = in_D1w + 0x30;
  return;
}



/* ===== arcade_pc 0x0006AA FUN_000006aa ===== */

void FUN_000006aa(void)

{
  undefined1 uVar1;
  
  PC060HA_master_port_3e0001 = 4;
  uVar1 = PC060HA_master_comm_3e0003;
  return;
}



/* ===== arcade_pc 0x039F80 warm_restart_watchdog_gate ===== */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void warm_restart_watchdog_gate(void)

{
  int iVar1;
  int unaff_A5;
  
  if (*(short *)(unaff_A5 + 0x2c) != 0) {
    *(short *)(unaff_A5 + 0x2c) = *(short *)(unaff_A5 + 0x2c) + -1;
    return;
  }
  iVar1 = 0xa0000;
  do {
    iVar1 = iVar1 + -1;
  } while (iVar1 != 0);
                    /* WARNING: Could not recover jumptable at 0x00039fa6. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*pcRam00000004)();
  return;
}



/* ===== arcade_pc 0x039FA8 FUN_00039fa8 ===== */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_00039fa8(void)

{
  int iVar1;
  bool in_CF;
  
  if (!in_CF) {
    iVar1 = 0xa0000;
    do {
      iVar1 = iVar1 + -1;
    } while (iVar1 != 0);
                    /* WARNING: Could not recover jumptable at 0x00039fa6. Too many branches */
                    /* WARNING: Treating indirect jump as call */
    (*pcRam00000004)();
    return;
  }
  return;
}



/* ===== arcade_pc 0x03A000 vector_01_target_03a000 ===== */

void vector_01_target_03a000(void)

{
  byte bVar1;
  short sVar2;
  undefined2 uVar3;
  undefined2 *puVar4;
  undefined2 *puVar5;
  
  Ram00c50000 = 0;
  Ram00d01bfe = 0;
  Ram00350008 = 0;
  Ram00380000 = 0;
  PC060HA_master_port_3e0001 = 4;
  PC060HA_master_comm_3e0003 = 1;
  sVar2 = 0x1fff;
  do {
    uVar3 = CLCS_palette_RAM;
    CLCS_palette_RAM = uVar3;
    sVar2 = sVar2 + -1;
  } while (sVar2 != 0);
  PC060HA_master_port_3e0001 = 4;
  PC060HA_master_comm_3e0003 = 0;
  sVar2 = 0x1fff;
  do {
    uVar3 = CLCS_palette_RAM;
    CLCS_palette_RAM = uVar3;
    sVar2 = sVar2 + -1;
  } while (sVar2 != 0);
  arcade_WRAM_base_A5 = 0;
  sVar2 = 0x1fff;
  puVar4 = &arcade_WRAM_base_A5;
  puVar5 = &DAT_0010c002;
  do {
    *puVar5 = *puVar4;
    sVar2 = sVar2 + -1;
    puVar4 = puVar4 + 1;
    puVar5 = puVar5 + 1;
  } while (sVar2 != 0);
  Ram003c0000 = 0;
  uVar3 = FUN_0003b9f8();
  Ram003c0000 = uVar3;
  Ram00380000 = 0x60;
  DAT_0010c014 = 0x60;
  FUN_0003ad72();
  FUN_0003ad44();
  uVar3 = FUN_0003ad44();
  Ram003c0000 = uVar3;
  FUN_0003ad3c();
  uVar3 = FUN_0003ad3c();
  Ram003c0000 = uVar3;
  bVar1 = DAT_00390009;
  DAT_0010c018 = (ushort)(byte)~bVar1;
  bVar1 = DAT_0039000b;
  DAT_0010c01c = (ushort)(byte)~bVar1;
  DAT_0010c038 = *(undefined2 *)(&DAT_0003b010 + (short)((DAT_0010c01c & 0xff0c) >> 1));
  DAT_0010c036 = *(undefined2 *)
                  ((int)&PTR_PTR_0003b018 + (int)(short)((DAT_0010c01c & 0xff30) >> 3));
  DAT_0010c030 = DAT_0010c018 & 0xff01;
  DAT_0010c032 = DAT_0010c018 & 0xff02;
  DAT_0010c02e = DAT_0010c01c & 3;
  if ((~bVar1 & 3) == 0) {
    DAT_0010c02e = 1;
  }
  else if (DAT_0010c02e == 1) {
    DAT_0010c02e = 0;
  }
  DAT_0010c040 = ~DAT_0005ff9e & 0xff40;
  DAT_0010c044 = ~DAT_0005ff9e & 0xff80;
  DAT_0010c026 = 1;
  FUN_0005ffa2();
  FUN_0005ffb2();
  FUN_0003b0c2();
  if ((DAT_0010c018 & 4) != 0) {
    FUN_00000100();
    return;
  }
  FUN_0003f084();
  DAT_0010c04a = 0xaa;
  FUN_0003b8b0();
  FUN_0003b098();
  FUN_0003add8();
  uVar3 = FUN_0003ae28();
  do {
    Ram003c0000 = uVar3;
    uVar3 = FUN_00039fa8();
  } while( true );
}



/* ===== arcade_pc 0x03A004 vector_1e_target_03a004 ===== */

void vector_1e_target_03a004(void)

{
  FUN_000510c6();
  do {
                    /* WARNING: Do nothing block with infinite loop */
  } while( true );
}



/* ===== arcade_pc 0x03A008 vector_1d_target_03a008 ===== */

void vector_1d_target_03a008(void)

{
  undefined2 in_D0w;
  short *unaff_A5;
  
  Ram00350008 = 0;
  Ram003c0000 = in_D0w;
  if ((1 < (ushort)unaff_A5[1]) && ((ushort)unaff_A5[1] < 4)) {
    FUN_0003a126();
    if ((*unaff_A5 != 0) && (unaff_A5[0x9ca] != 1)) {
      FUN_00041f30();
    }
  }
  warm_restart_gate_caller_a();
  FUN_0003abe2();
  FUN_0003a0a8();
  FUN_0003eefa();
  FUN_0003ef5c();
                    /* WARNING: Could not recover jumptable at 0x0003a06a. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(&DAT_0003a06c + *(short *)(&DAT_0003a06c + (short)(*unaff_A5 * 2))))();
  return;
}



/* ===== arcade_pc 0x03A080 FUN_0003a080 ===== */

void FUN_0003a080(void)

{
  FUN_000510c6();
  do {
                    /* WARNING: Do nothing block with infinite loop */
  } while( true );
}



/* ===== arcade_pc 0x03A08C FUN_0003a08c ===== */

void FUN_0003a08c(void)

{
  int unaff_A5;
  
  if (*(short *)(unaff_A5 + 0x2be) == 0) {
    *(undefined2 *)(unaff_A5 + 0x2be) = 1;
  }
  return;
}



/* ===== arcade_pc 0x03A09A FUN_0003a09a ===== */

void FUN_0003a09a(void)

{
  int unaff_A5;
  
  if (*(short *)(unaff_A5 + 0x2c2) == 0) {
    *(undefined2 *)(unaff_A5 + 0x2c2) = 1;
    return;
  }
  return;
}



/* ===== arcade_pc 0x03A0A8 FUN_0003a0a8 ===== */

void FUN_0003a0a8(void)

{
  byte bVar1;
  int unaff_A5;
  
  bVar1 = DAT_00390005;
  if ((bVar1 & 0x40) != 0) {
    bVar1 = DAT_00390005;
    if (((bVar1 & 0x10) == 0) && (*(ushort *)(unaff_A5 + 0x12) < 9)) {
      FUN_0003ae28();
    }
    else {
      FUN_0003ae3c();
    }
    bVar1 = DAT_00390005;
    if (((bVar1 & 0x20) == 0) && (*(ushort *)(unaff_A5 + 0x12) < 9)) {
      FUN_0003ae28();
    }
    else {
      FUN_0003ae46();
    }
  }
  return;
}



/* ===== arcade_pc 0x03A0EC FUN_0003a0ec ===== */

void FUN_0003a0ec(void)

{
  char in_D0b;
  short sVar1;
  int unaff_A5;
  char *pcVar2;
  
  if ((*(short *)(unaff_A5 + 0x34) != 0) && (in_D0b != '#')) {
    pcVar2 = (char *)(unaff_A5 + 0x292);
    sVar1 = 6;
    do {
      if (*pcVar2 == '\0') {
        *pcVar2 = in_D0b;
        return;
      }
      pcVar2 = pcVar2 + 1;
      sVar1 = sVar1 + -1;
    } while (sVar1 != 0);
  }
  return;
}



/* ===== arcade_pc 0x03A126 FUN_0003a126 ===== */

void FUN_0003a126(void)

{
  uint uVar1;
  short sVar2;
  int unaff_A5;
  char *pcVar3;
  
  if ((*(short *)(unaff_A5 + 0x34) != 0) || (*(short *)(&DAT_00001394 + unaff_A5) == 1)) {
    pcVar3 = (char *)(unaff_A5 + 0x292);
    sVar2 = 6;
    do {
      if (*pcVar3 != '\0') {
        do {
          uVar1 = FUN_0003f09c();
        } while ((uVar1 & 1) != 0);
        FUN_0003f084();
        *pcVar3 = '\0';
        return;
      }
      pcVar3 = pcVar3 + 1;
      sVar2 = sVar2 + -1;
    } while (sVar2 != 0);
  }
  return;
}



/* ===== arcade_pc 0x03A2D0 FUN_0003a2d0 ===== */

void FUN_0003a2d0(void)

{
  short in_D0w;
  undefined2 *in_A0;
  undefined2 *in_A1;
  
  do {
    *in_A1 = *in_A0;
    in_D0w = in_D0w + -1;
    in_A0 = in_A0 + 1;
    in_A1 = in_A1 + 1;
  } while (in_D0w != 0);
  return;
}



/* ===== arcade_pc 0x03A552 FUN_0003a552 ===== */

void FUN_0003a552(void)

{
  char cVar1;
  
  cVar1 = DAT_00c09ea3;
  if (cVar1 == '0') {
    DAT_00c09ea3 = 0x20;
  }
  return;
}



/* ===== arcade_pc 0x03AB7C warm_restart_gate_caller_a ===== */

void warm_restart_gate_caller_a(void)

{
  byte bVar1;
  short *unaff_A5;
  
  FUN_00039fa8();
  if ((*unaff_A5 != 3) && (bVar1 = DAT_00390007, (bVar1 & 4) == 0)) {
    FUN_0003f084();
    unaff_A5[0x25] = 0x1f;
    FUN_0003add8();
    FUN_0003ae50();
    FUN_0003ad72();
    Ram00c20000 = 0;
    Ram00c40000 = 0;
    FUN_0003ae64();
    FUN_0003bb48();
    unaff_A5[0x16] = 0x10;
    *unaff_A5 = 3;
    unaff_A5[1] = 0;
  }
  return;
}



/* ===== arcade_pc 0x03ABE2 FUN_0003abe2 ===== */

void FUN_0003abe2(void)

{
  int unaff_A5;
  
  FUN_0003ac04();
  FUN_0003ac8a();
  if (*(short *)(unaff_A5 + 0x26) != 0) {
    FUN_0003acf4();
  }
  return;
}



/* ===== arcade_pc 0x03AC04 FUN_0003ac04 ===== */

void FUN_0003ac04(void)

{
  byte bVar1;
  char cVar2;
  ushort uVar3;
  undefined2 *unaff_A5;
  
  bVar1 = DAT_00390007;
  if ((bVar1 & 1) == 0) {
    unaff_A5[0x10] = 1;
  }
  else if (unaff_A5[0x10] != 0) {
    unaff_A5[0x10] = 0;
    uVar3 = unaff_A5[9] + 1;
    if (uVar3 < 0x99) {
      if (9 < (uVar3 & 0xf)) {
        uVar3 = unaff_A5[9] + 7;
      }
    }
    else {
      uVar3 = 0x99;
    }
    unaff_A5[9] = uVar3;
    if (8 < uVar3) {
      FUN_0003ae50();
    }
    cVar2 = DAT_00c09e87;
    if (cVar2 == 'C') {
      FUN_0003c2e2();
      FUN_0003a552();
    }
    FUN_0003f084();
    if (unaff_A5[0x1a] == 0) {
      unaff_A5[0x16] = 0;
      *unaff_A5 = 1;
      unaff_A5[1] = 0;
      unaff_A5[2] = 0;
      return;
    }
  }
  return;
}



/* ===== arcade_pc 0x03AC8A FUN_0003ac8a ===== */

void FUN_0003ac8a(void)

{
  ushort *puVar1;
  byte bVar2;
  char cVar3;
  ushort uVar4;
  undefined2 *unaff_A5;
  
  if (0x98 < (ushort)unaff_A5[9]) {
    unaff_A5[0x10] = 0;
    unaff_A5[0x11] = 0;
    unaff_A5[0x12] = 0;
    return;
  }
  bVar2 = DAT_00390007;
  if ((bVar2 & 0x20) != 0) {
    unaff_A5[0x11] = 1;
    return;
  }
  if (unaff_A5[0x11] != 0) {
    unaff_A5[0x11] = 0;
    bVar2 = DAT_00390005;
    if (((bVar2 & 0x40) != 0) && (bVar2 = DAT_00390005, (bVar2 & 0x10) != 0)) {
      return;
    }
    FUN_0003a08c();
    puVar1 = unaff_A5 + 3;
    uVar4 = *puVar1 + 1;
    if (uVar4 < (ushort)unaff_A5[4]) {
      *puVar1 = uVar4;
      return;
    }
    *puVar1 = uVar4 - unaff_A5[4];
    uVar4 = unaff_A5[5] + unaff_A5[9];
    if (uVar4 < 0x99) {
      if (9 < (uVar4 & 0xf)) {
        uVar4 = uVar4 + 6;
      }
    }
    else {
      uVar4 = 0x99;
    }
    unaff_A5[9] = uVar4;
    if (8 < uVar4) {
      FUN_0003ae50();
    }
    cVar3 = DAT_00c09e87;
    if (cVar3 == 'C') {
      FUN_0003c2e2();
      FUN_0003a552();
    }
    FUN_0003f084();
    if (unaff_A5[0x1a] == 0) {
      unaff_A5[0x16] = 0;
      *unaff_A5 = 1;
      unaff_A5[1] = 0;
      unaff_A5[2] = 0;
      return;
    }
  }
  return;
}



/* ===== arcade_pc 0x03ACAE title_fg_glyph_producer_3acae ===== */

void title_fg_glyph_producer_3acae(void)

{
  ushort *puVar1;
  byte bVar2;
  char cVar3;
  ushort uVar4;
  undefined2 *unaff_A5;
  
  unaff_A5[0x11] = 0;
  bVar2 = DAT_00390005;
  if (((bVar2 & 0x40) != 0) && (bVar2 = DAT_00390005, (bVar2 & 0x10) != 0)) {
    return;
  }
  FUN_0003a08c();
  puVar1 = unaff_A5 + 3;
  uVar4 = *puVar1 + 1;
  if (uVar4 < (ushort)unaff_A5[4]) {
    *puVar1 = uVar4;
    return;
  }
  *puVar1 = uVar4 - unaff_A5[4];
  uVar4 = unaff_A5[5] + unaff_A5[9];
  if (uVar4 < 0x99) {
    if (9 < (uVar4 & 0xf)) {
      uVar4 = uVar4 + 6;
    }
  }
  else {
    uVar4 = 0x99;
  }
  unaff_A5[9] = uVar4;
  if (8 < uVar4) {
    FUN_0003ae50();
  }
  cVar3 = DAT_00c09e87;
  if (cVar3 == 'C') {
    FUN_0003c2e2();
    FUN_0003a552();
  }
  FUN_0003f084();
  if (unaff_A5[0x1a] == 0) {
    unaff_A5[0x16] = 0;
    *unaff_A5 = 1;
    unaff_A5[1] = 0;
    unaff_A5[2] = 0;
    return;
  }
  return;
}



/* ===== arcade_pc 0x03ACF4 FUN_0003acf4 ===== */

void FUN_0003acf4(void)

{
  ushort *puVar1;
  byte bVar2;
  char cVar3;
  ushort uVar4;
  undefined2 *unaff_A5;
  
  if (0x98 < (ushort)unaff_A5[9]) {
    unaff_A5[0x10] = 0;
    unaff_A5[0x11] = 0;
    unaff_A5[0x12] = 0;
    return;
  }
  bVar2 = DAT_00390007;
  if ((bVar2 & 0x40) != 0) {
    unaff_A5[0x12] = 1;
    return;
  }
  if (unaff_A5[0x12] != 0) {
    unaff_A5[0x12] = 0;
    bVar2 = DAT_00390005;
    if (((bVar2 & 0x40) != 0) && (bVar2 = DAT_00390005, (bVar2 & 0x20) != 0)) {
      return;
    }
    FUN_0003a09a();
    puVar1 = unaff_A5 + 6;
    uVar4 = *puVar1 + 1;
    if (uVar4 < (ushort)unaff_A5[7]) {
      *puVar1 = uVar4;
      return;
    }
    *puVar1 = uVar4 - unaff_A5[7];
    uVar4 = unaff_A5[8] + unaff_A5[9];
    if (uVar4 < 0x99) {
      if (9 < (uVar4 & 0xf)) {
        uVar4 = uVar4 + 6;
      }
    }
    else {
      uVar4 = 0x99;
    }
    unaff_A5[9] = uVar4;
    if (8 < uVar4) {
      FUN_0003ae50();
    }
    cVar3 = DAT_00c09e87;
    if (cVar3 == 'C') {
      FUN_0003c2e2();
      FUN_0003a552();
    }
    FUN_0003f084();
    if (unaff_A5[0x1a] == 0) {
      unaff_A5[0x16] = 0;
      *unaff_A5 = 1;
      unaff_A5[1] = 0;
      unaff_A5[2] = 0;
      return;
    }
  }
  return;
}



/* ===== arcade_pc 0x03AD3C FUN_0003ad3c ===== */

void FUN_0003ad3c(void)

{
  undefined2 in_D0w;
  short in_D1w;
  undefined2 *in_A0;
  
  do {
    *in_A0 = in_D0w;
    in_D1w = in_D1w + -1;
    in_A0 = in_A0 + 1;
  } while (in_D1w != 0);
  return;
}



/* ===== arcade_pc 0x03AD44 FUN_0003ad44 ===== */

void FUN_0003ad44(void)

{
  undefined4 in_D0;
  short in_D1w;
  undefined4 *in_A0;
  
  do {
    *in_A0 = in_D0;
    in_D1w = in_D1w + -1;
    in_A0 = in_A0 + 1;
  } while (in_D1w != 0);
  return;
}



/* ===== arcade_pc 0x03AD72 FUN_0003ad72 ===== */

void FUN_0003ad72(void)

{
  uint uVar1;
  short sVar2;
  uint *extraout_A0;
  uint *puVar3;
  
  FUN_0003ad44();
  FUN_0005b512();
  FUN_0003adaa();
  sVar2 = 3;
  uVar1 = 200;
  puVar3 = extraout_A0;
  do {
    *puVar3 = uVar1;
    puVar3[1] = 0x160;
    puVar3 = puVar3 + 2;
    uVar1 = (uint)(ushort)((short)uVar1 + 0x10);
    sVar2 = sVar2 + -1;
  } while (sVar2 != 0);
  return;
}



/* ===== arcade_pc 0x03ADAA FUN_0003adaa ===== */

void FUN_0003adaa(void)

{
  undefined4 in_D0;
  short in_D1w;
  undefined4 unaff_D7;
  undefined4 *in_A0;
  
  do {
    *in_A0 = in_D0;
    in_A0[1] = unaff_D7;
    in_A0 = in_A0 + 2;
    in_D0 = CONCAT22((short)((uint)in_D0 >> 0x10),(short)in_D0 + 0x10);
    in_D1w = in_D1w + -1;
  } while (in_D1w != 0);
  return;
}



/* ===== arcade_pc 0x03ADD8 FUN_0003add8 ===== */

void FUN_0003add8(void)

{
  int unaff_A5;
  
  if (*(short *)(unaff_A5 + 0x32) == 0) {
    if ((*(short *)(unaff_A5 + 0x30) != 0) || (*(short *)(unaff_A5 + 0x2a) == 0)) goto LAB_0003adfa;
  }
  else if ((*(short *)(unaff_A5 + 0x30) == 0) && (*(short *)(unaff_A5 + 0x2a) != 0)) {
LAB_0003adfa:
    *(undefined2 *)(unaff_A5 + 0x1e) = 0;
    Ram00c50000 = 0;
    Ram00d01bfe = 1;
    return;
  }
  *(undefined2 *)(unaff_A5 + 0x1e) = 1;
  Ram00c50000 = 1;
  Ram00d01bfe = 0;
  return;
}



/* ===== arcade_pc 0x03AE28 FUN_0003ae28 ===== */

void FUN_0003ae28(void)

{
  ushort uVar1;
  int unaff_A5;
  
  uVar1 = *(ushort *)(unaff_A5 + 0x14) | 3;
  *(ushort *)(unaff_A5 + 0x14) = uVar1;
  Ram00380000 = uVar1;
  return;
}



/* ===== arcade_pc 0x03AE3C FUN_0003ae3c ===== */

void FUN_0003ae3c(void)

{
  ushort uVar1;
  int unaff_A5;
  
  uVar1 = *(ushort *)(unaff_A5 + 0x14) & 0xfffd;
  *(ushort *)(unaff_A5 + 0x14) = uVar1;
  Ram00380000 = uVar1;
  return;
}



/* ===== arcade_pc 0x03AE46 FUN_0003ae46 ===== */

void FUN_0003ae46(void)

{
  ushort uVar1;
  int unaff_A5;
  
  uVar1 = *(ushort *)(unaff_A5 + 0x14) & 0xfffe;
  *(ushort *)(unaff_A5 + 0x14) = uVar1;
  Ram00380000 = uVar1;
  return;
}



/* ===== arcade_pc 0x03AE50 FUN_0003ae50 ===== */

void FUN_0003ae50(void)

{
  ushort uVar1;
  int unaff_A5;
  
  uVar1 = *(ushort *)(unaff_A5 + 0x14) & 0xfffc;
  *(ushort *)(unaff_A5 + 0x14) = uVar1;
  Ram00380000 = uVar1;
  return;
}



/* ===== arcade_pc 0x03AE64 FUN_0003ae64 ===== */

void FUN_0003ae64(void)

{
  FUN_0003ad44();
  FUN_0003ad44();
  return;
}



/* ===== arcade_pc 0x03AE86 startup_common_body ===== */

void startup_common_body(void)

{
  byte bVar1;
  short sVar2;
  undefined2 uVar3;
  undefined2 *puVar4;
  undefined2 *puVar5;
  
  Ram00c50000 = 0;
  Ram00d01bfe = 0;
  Ram00350008 = 0;
  Ram00380000 = 0;
  PC060HA_master_port_3e0001 = 4;
  PC060HA_master_comm_3e0003 = 1;
  sVar2 = 0x1fff;
  do {
    uVar3 = CLCS_palette_RAM;
    CLCS_palette_RAM = uVar3;
    sVar2 = sVar2 + -1;
  } while (sVar2 != 0);
  PC060HA_master_port_3e0001 = 4;
  PC060HA_master_comm_3e0003 = 0;
  sVar2 = 0x1fff;
  do {
    uVar3 = CLCS_palette_RAM;
    CLCS_palette_RAM = uVar3;
    sVar2 = sVar2 + -1;
  } while (sVar2 != 0);
  arcade_WRAM_base_A5 = 0;
  sVar2 = 0x1fff;
  puVar4 = &arcade_WRAM_base_A5;
  puVar5 = &DAT_0010c002;
  do {
    *puVar5 = *puVar4;
    sVar2 = sVar2 + -1;
    puVar4 = puVar4 + 1;
    puVar5 = puVar5 + 1;
  } while (sVar2 != 0);
  Ram003c0000 = 0;
  uVar3 = FUN_0003b9f8();
  Ram003c0000 = uVar3;
  Ram00380000 = 0x60;
  DAT_0010c014 = 0x60;
  FUN_0003ad72();
  FUN_0003ad44();
  uVar3 = FUN_0003ad44();
  Ram003c0000 = uVar3;
  FUN_0003ad3c();
  uVar3 = FUN_0003ad3c();
  Ram003c0000 = uVar3;
  bVar1 = DAT_00390009;
  DAT_0010c018 = (ushort)(byte)~bVar1;
  bVar1 = DAT_0039000b;
  DAT_0010c01c = (ushort)(byte)~bVar1;
  DAT_0010c038 = *(undefined2 *)(&DAT_0003b010 + (short)((DAT_0010c01c & 0xff0c) >> 1));
  DAT_0010c036 = *(undefined2 *)
                  ((int)&PTR_PTR_0003b018 + (int)(short)((DAT_0010c01c & 0xff30) >> 3));
  DAT_0010c030 = DAT_0010c018 & 0xff01;
  DAT_0010c032 = DAT_0010c018 & 0xff02;
  DAT_0010c02e = DAT_0010c01c & 3;
  if ((~bVar1 & 3) == 0) {
    DAT_0010c02e = 1;
  }
  else if (DAT_0010c02e == 1) {
    DAT_0010c02e = 0;
  }
  DAT_0010c040 = ~DAT_0005ff9e & 0xff40;
  DAT_0010c044 = ~DAT_0005ff9e & 0xff80;
  DAT_0010c026 = 1;
  FUN_0005ffa2();
  FUN_0005ffb2();
  FUN_0003b0c2();
  if ((DAT_0010c018 & 4) != 0) {
    FUN_00000100();
    return;
  }
  FUN_0003f084();
  DAT_0010c04a = 0xaa;
  FUN_0003b8b0();
  FUN_0003b098();
  FUN_0003add8();
  uVar3 = FUN_0003ae28();
  do {
    Ram003c0000 = uVar3;
    uVar3 = FUN_00039fa8();
  } while( true );
}



/* ===== arcade_pc 0x03B084 warm_restart_gate_caller_b ===== */

void warm_restart_gate_caller_b(void)

{
  undefined2 uVar1;
  
  do {
    uVar1 = FUN_00039fa8();
    Ram003c0000 = uVar1;
  } while( true );
}



/* ===== arcade_pc 0x03B098 FUN_0003b098 ===== */

void FUN_0003b098(void)

{
  int unaff_A5;
  
  Ram00c20000 = 0;
  Ram00c40000 = 0;
  FUN_0003bb48();
  FUN_0003c2e2();
  FUN_0003a552();
  if (*(short *)(unaff_A5 + 0x40) != 0) {
    FUN_0003bb48();
  }
  return;
}



/* ===== arcade_pc 0x03B0C2 FUN_0003b0c2 ===== */

void FUN_0003b0c2(void)

{
  short sVar1;
  undefined1 *puVar2;
  undefined1 *puVar3;
  int unaff_A5;
  
  sVar1 = 0x26;
  puVar2 = &DAT_0003b0d4;
  puVar3 = (undefined1 *)(unaff_A5 + 0x140);
  do {
    *puVar3 = *puVar2;
    sVar1 = sVar1 + -1;
    puVar2 = puVar2 + 1;
    puVar3 = puVar3 + 1;
  } while (sVar1 != 0);
  return;
}



/* ===== arcade_pc 0x03B710 FUN_0003b710 ===== */

void FUN_0003b710(void)

{
  int in_D0;
  int unaff_D7;
  
  do {
    FUN_0003c2e2(in_D0);
    in_D0 = in_D0 + 1;
    unaff_D7 = unaff_D7 + -1;
  } while (unaff_D7 != 0);
  return;
}



/* ===== arcade_pc 0x03B802 pc090oj_sprite_producer_3b802 ===== */

void pc090oj_sprite_producer_3b802(void)

{
  undefined1 uVar1;
  short in_D0w;
  ushort uVar2;
  short sVar3;
  short extraout_D1w;
  short extraout_D1w_00;
  int extraout_A1;
  int extraout_A1_00;
  
  uVar2 = (ushort)(byte)(&DAT_0003b87e)[(short)(in_D0w * 10)];
  uVar1 = (&DAT_0003b87f)[(short)(in_D0w * 10)];
  do {
    if ((uVar2 & 1) == 0) {
      sVar3 = FUN_0003b866();
      *(undefined1 *)(extraout_A1_00 + 3) = uVar1;
      *(short *)(extraout_A1_00 + 4) = extraout_D1w_00 + 0x2a;
    }
    else {
      sVar3 = FUN_0003b866();
      *(undefined1 *)(extraout_A1 + 3) = uVar1;
      *(short *)(extraout_A1 + 4) = extraout_D1w + 0x2a;
    }
    uVar2 = sVar3 - 1;
  } while (uVar2 != 0);
  return;
}



/* ===== arcade_pc 0x03B866 FUN_0003b866 ===== */

void FUN_0003b866(void)

{
  short in_D1w;
  short unaff_D5w;
  int in_A1;
  
  if ((unaff_D5w == 0) && (in_D1w == 0)) {
    *(undefined1 *)(in_A1 + 2) = 1;
    return;
  }
  *(undefined1 *)(in_A1 + 2) = 0;
  return;
}



/* ===== arcade_pc 0x03B8B0 FUN_0003b8b0 ===== */

void FUN_0003b8b0(void)

{
  pc090oj_sprite_producer_3b930();
  pc090oj_sprite_producer_3b802();
  pc090oj_sprite_producer_3b930();
  pc090oj_sprite_producer_3b930();
  FUN_0003b902();
  return;
}



/* ===== arcade_pc 0x03B902 FUN_0003b902 ===== */

void FUN_0003b902(void)

{
  int iVar1;
  short in_D1w;
  undefined *puVar2;
  
  puVar2 = &DAT_00d00088;
  if (in_D1w == 0) {
    pc090oj_sprite_producer_3b930();
    return;
  }
  iVar1 = 5;
  do {
    puVar2[2] = (char)in_D1w;
    puVar2 = puVar2 + 8;
    iVar1 = iVar1 + -1;
  } while (iVar1 != 0);
  return;
}



/* ===== arcade_pc 0x03B930 pc090oj_sprite_producer_3b930 ===== */

void pc090oj_sprite_producer_3b930(void)

{
  undefined2 uVar1;
  int extraout_D1;
  byte *in_A0;
  byte *extraout_A0;
  undefined2 *in_A1;
  undefined2 *extraout_A1;
  
  do {
    *in_A1 = 0;
    in_A1[1] = (ushort)*in_A0;
    in_A1[2] = (ushort)in_A0[1];
    uVar1 = *(undefined2 *)(in_A0 + 2);
    FUN_0005b512();
    in_A1 = extraout_A1 + 1;
    *extraout_A1 = uVar1;
    in_A0 = extraout_A0;
  } while (extraout_D1 != 1);
  return;
}



/* ===== arcade_pc 0x03B9F8 FUN_0003b9f8 ===== */

void FUN_0003b9f8(void)

{
  FUN_0003ba64();
  FUN_0003ba64();
  return;
}



/* ===== arcade_pc 0x03BA20 FUN_0003ba20 ===== */

void FUN_0003ba20(void)

{
  int unaff_A5;
  
  *(undefined2 *)(unaff_A5 + 0x21a) = 0;
  do {
    FUN_0003ba56();
    *(short *)(unaff_A5 + 0x21a) = *(short *)(unaff_A5 + 0x21a) + 1;
  } while (*(short *)(unaff_A5 + 0x21a) != 0x20);
  return;
}



/* ===== arcade_pc 0x03BA56 FUN_0003ba56 ===== */

void FUN_0003ba56(void)

{
  ushort uVar1;
  short in_D0w;
  int iVar2;
  ushort *in_A0;
  ushort *puVar3;
  
  iVar2 = 0x10;
  puVar3 = (ushort *)(&DAT_0004fd02 + (short)(in_D0w * 0x20));
  do {
    uVar1 = *puVar3;
    *in_A0 = (uVar1 & 0xf) << 0xb | (uVar1 & 0xf0) << 2 | (uVar1 & 0xf00) >> 7;
    iVar2 = iVar2 + -1;
    in_A0 = in_A0 + 1;
    puVar3 = puVar3 + 1;
  } while (iVar2 != 0);
  return;
}



/* ===== arcade_pc 0x03BA64 FUN_0003ba64 ===== */

void FUN_0003ba64(void)

{
  ushort uVar1;
  int unaff_D3;
  ushort *in_A0;
  ushort *unaff_A3;
  
  do {
    uVar1 = *unaff_A3;
    *in_A0 = (uVar1 & 0xf) << 0xb | (uVar1 & 0xf0) << 2 | (uVar1 & 0xf00) >> 7;
    unaff_D3 = unaff_D3 + -1;
    in_A0 = in_A0 + 1;
    unaff_A3 = unaff_A3 + 1;
  } while (unaff_D3 != 0);
  return;
}



/* ===== arcade_pc 0x03BB48 FUN_0003bb48 ===== */

short FUN_0003bb48(void)

{
  undefined4 *puVar1;
  undefined2 uVar2;
  char cVar3;
  ushort in_D0w;
  short sVar4;
  char *pcVar5;
  short *psVar6;
  undefined2 *puVar7;
  undefined2 *puVar8;
  
  sVar4 = (in_D0w & 0x7f) << 2;
  puVar1 = *(undefined4 **)((int)&PTR_PTR_0003bb7c + (int)sVar4);
  puVar7 = (undefined2 *)*puVar1;
  pcVar5 = (char *)((int)puVar1 + 6);
  uVar2 = *(undefined2 *)(puVar1 + 1);
  if ((char)in_D0w < '\0') {
    while( true ) {
      sVar4 = CONCAT11((char)((ushort)sVar4 >> 8),*pcVar5);
      if (*pcVar5 == '\0') break;
      puVar8 = puVar7 + 1;
      *puVar7 = uVar2;
      puVar7 = puVar7 + 2;
      *puVar8 = 0x20;
      pcVar5 = pcVar5 + 1;
    }
  }
  else {
    while( true ) {
      cVar3 = *pcVar5;
      sVar4 = CONCAT11((char)((ushort)sVar4 >> 8),cVar3);
      if (cVar3 == '\0') break;
      sVar4 = (short)cVar3;
      psVar6 = puVar7 + 1;
      *puVar7 = uVar2;
      puVar7 = puVar7 + 2;
      *psVar6 = sVar4;
      pcVar5 = pcVar5 + 1;
    }
  }
  return sVar4;
}



/* ===== arcade_pc 0x03BD48 shared_glyph_renderer_3bd48 ===== */

/* WARNING: Control flow encountered bad instruction data */

void shared_glyph_renderer_3bd48(void)

{
                    /* WARNING: Bad instruction - Truncating control flow here */
  halt_baddata();
}



/* ===== arcade_pc 0x03C2E2 FUN_0003c2e2 ===== */

void FUN_0003c2e2(void)

{
  byte bVar1;
  short in_D0w;
  ushort uVar2;
  ushort *puVar3;
  undefined2 *puVar4;
  int iVar5;
  byte *pbVar6;
  
  iVar5 = (int)(short)(in_D0w * 10);
  puVar3 = (ushort *)(&DAT_0003c37c + iVar5);
  uVar2 = *puVar3;
  puVar4 = *(undefined2 **)((int)&PTR_DAT_0003c37e + iVar5);
  pbVar6 = *(byte **)((int)&PTR_DAT_0003c382 + iVar5);
  if (uVar2 == 0xffff) {
    if ((*pbVar6 & 0xf) == 7) {
      puVar4[-4] = 0;
      puVar4[-3] = 0x41;
      puVar4[-2] = 0;
      puVar4[-1] = 0x4c;
      *puVar4 = 0;
      puVar4[1] = 0x4c;
      return;
    }
    uVar2 = 1;
  }
  do {
    if ((uVar2 & 1) == 0) {
      bVar1 = *pbVar6;
      *puVar4 = 0;
      puVar4[1] = bVar1 >> 4 | 0x30;
    }
    else {
      bVar1 = *pbVar6;
      *puVar4 = 0;
      puVar4[1] = bVar1 & 0xf | 0x30;
      pbVar6 = pbVar6 + -1;
    }
    puVar4 = puVar4 + 2;
    uVar2 = uVar2 - 1;
  } while (uVar2 != 0);
  if (*puVar3 == 6) {
    uVar2 = *puVar3;
    iVar5 = *(int *)((int)&PTR_DAT_0003c37e + iVar5);
    do {
      if (*(short *)(iVar5 + 2) != 0x30) {
        return;
      }
      *(undefined2 *)(iVar5 + 2) = 0x20;
      iVar5 = iVar5 + 4;
      uVar2 = uVar2 - 1;
    } while (uVar2 != 0);
  }
  return;
}



/* ===== arcade_pc 0x03C516 FUN_0003c516 ===== */

void FUN_0003c516(void)

{
  short sVar1;
  short unaff_D2w;
  char unaff_D3b;
  short unaff_D4w;
  char *in_A0;
  char *extraout_A0;
  int in_A1;
  int extraout_A1;
  int unaff_A4;
  
  while ((unaff_D3b != 'P' || (unaff_D4w != 1))) {
    *(short *)(in_A1 + 2) =
         *(short *)(unaff_A4 + 0x18) + *(short *)(unaff_A4 + 0x1a) + (short)*in_A0;
    sVar1 = *(short *)(unaff_A4 + 0x16);
    FUN_0005b512();
    *(ushort *)(extraout_A1 + 6) = unaff_D2w + sVar1 & 0x1ff;
    in_A1 = extraout_A1 + 8;
    unaff_D4w = unaff_D4w + -1;
    in_A0 = extraout_A0;
    if (unaff_D4w == 0) {
      return;
    }
  }
  return;
}



/* ===== arcade_pc 0x03C606 FUN_0003c606 ===== */

void FUN_0003c606(void)

{
  short unaff_D2w;
  short unaff_D3w;
  char *in_A0;
  int in_A1;
  int unaff_A4;
  
  do {
    if (*in_A0 == -1) {
      *(undefined2 *)(in_A1 + 2) = 0x180;
    }
    else {
      *(short *)(in_A1 + 6) = *(short *)(unaff_A4 + 0x16) + (short)*in_A0;
      *(ushort *)(in_A1 + 2) = unaff_D2w + *(short *)(unaff_A4 + 0x1a) & 0x1ff;
    }
    in_A1 = in_A1 + 8;
    unaff_D3w = unaff_D3w + -1;
    in_A0 = in_A0 + 1;
  } while (unaff_D3w != 0);
  return;
}



/* ===== arcade_pc 0x03C6AC FUN_0003c6ac ===== */

void FUN_0003c6ac(void)

{
  short unaff_D2w;
  short unaff_D3w;
  char *in_A0;
  int in_A1;
  int unaff_A4;
  
  do {
    if (*in_A0 == -1) {
      *(undefined2 *)(in_A1 + 2) = 0x180;
    }
    else {
      *(short *)(in_A1 + 2) = *(short *)(unaff_A4 + 0x1a) + (short)*in_A0;
    }
    *(ushort *)(in_A1 + 6) = unaff_D2w + *(short *)(unaff_A4 + 0x16) & 0x1ff;
    in_A1 = in_A1 + 8;
    unaff_D3w = unaff_D3w + -1;
    in_A0 = in_A0 + 1;
  } while (unaff_D3w != 0);
  return;
}



/* ===== arcade_pc 0x03C70A FUN_0003c70a ===== */

void FUN_0003c70a(void)

{
  short sVar1;
  char cVar2;
  short in_D1w;
  short extraout_D1w;
  short unaff_D3w;
  short unaff_D4w;
  char *in_A0;
  char *pcVar3;
  char *extraout_A0;
  int in_A1;
  int extraout_A1;
  int unaff_A4;
  
  do {
    pcVar3 = in_A0 + 1;
    cVar2 = *in_A0;
    if (cVar2 == 0) {
      *(undefined2 *)(in_A1 + 2) = 0x180;
    }
    else {
      *(short *)(in_A1 + 2) = *(short *)(unaff_A4 + 0x1a) + in_D1w;
      sVar1 = *(short *)(unaff_A4 + 0x16);
      FUN_0005b512();
      *(ushort *)(extraout_A1 + 6) = cVar2 + sVar1 & 0x1ff;
      in_D1w = unaff_D4w + extraout_D1w;
      pcVar3 = extraout_A0;
      in_A1 = extraout_A1;
    }
    in_A1 = in_A1 + 8;
    unaff_D3w = unaff_D3w + -1;
    in_A0 = pcVar3;
  } while (unaff_D3w != 0);
  return;
}



/* ===== arcade_pc 0x03C742 FUN_0003c742 ===== */

void FUN_0003c742(void)

{
  short unaff_D6w;
  short unaff_D7w;
  int in_A1;
  int unaff_A4;
  
  *(ushort *)(in_A1 + 2) = *(short *)(unaff_A4 + 0x1a) + unaff_D6w & 0x1ff;
  *(ushort *)(in_A1 + 6) = *(short *)(unaff_A4 + 0x16) + unaff_D7w & 0x1ff;
  return;
}



/* ===== arcade_pc 0x03C7D2 FUN_0003c7d2 ===== */

void FUN_0003c7d2(void)

{
  short unaff_D2w;
  short unaff_D3w;
  char *in_A0;
  int in_A1;
  int unaff_A4;
  
  do {
    if (*in_A0 == -1) {
      *(undefined2 *)(in_A1 + 2) = 0x180;
    }
    else {
      *(short *)(in_A1 + 2) = *(short *)(unaff_A4 + 0x1a) + (short)*in_A0;
    }
    *(ushort *)(in_A1 + 6) = unaff_D2w + *(short *)(unaff_A4 + 0x16) & 0x1ff;
    in_A1 = in_A1 + 8;
    unaff_D3w = unaff_D3w + -1;
    in_A0 = in_A0 + 1;
  } while (unaff_D3w != 0);
  return;
}



/* ===== arcade_pc 0x03C804 FUN_0003c804 ===== */

void FUN_0003c804(void)

{
  short sVar1;
  short unaff_D2w;
  short unaff_D3w;
  int in_A1;
  int unaff_A4;
  
  do {
    sVar1 = -0x20;
    if (unaff_D3w != 2) {
      sVar1 = -0x30;
    }
    *(short *)(in_A1 + 2) = *(short *)(unaff_A4 + 0x1a) + sVar1;
    *(ushort *)(in_A1 + 6) = unaff_D2w + *(short *)(unaff_A4 + 0x16) & 0x1ff;
    in_A1 = in_A1 + 8;
    unaff_D3w = unaff_D3w + -1;
  } while (unaff_D3w != 0);
  return;
}



/* ===== arcade_pc 0x03C85E FUN_0003c85e ===== */

void FUN_0003c85e(void)

{
  short sVar1;
  short unaff_D2w;
  short unaff_D3w;
  char *in_A0;
  char *extraout_A0;
  char *pcVar2;
  int in_A1;
  int extraout_A1;
  int unaff_A4;
  
  do {
    if (unaff_D3w == 5) {
      sVar1 = FUN_0003c89a();
      pcVar2 = extraout_A0;
      in_A1 = extraout_A1;
LAB_0003c87c:
      *(short *)(in_A1 + 2) = *(short *)(unaff_A4 + 0x1a) + sVar1;
    }
    else {
      pcVar2 = in_A0 + 1;
      sVar1 = (short)*in_A0;
      if (sVar1 != 0) goto LAB_0003c87c;
      *(undefined2 *)(in_A1 + 2) = 0x180;
    }
    *(ushort *)(in_A1 + 6) = unaff_D2w + *(short *)(unaff_A4 + 0x16) & 0x1ff;
    in_A1 = in_A1 + 8;
    unaff_D3w = unaff_D3w + -1;
    in_A0 = pcVar2;
    if (unaff_D3w == 0) {
      return;
    }
  } while( true );
}



/* ===== arcade_pc 0x03C89A FUN_0003c89a ===== */

void FUN_0003c89a(void)

{
  char unaff_D2b;
  short sVar1;
  int in_A1;
  int unaff_A5;
  
  if (*(char *)(unaff_A5 + 0x118) == '\x03') {
    sVar1 = 0xa0d;
    if (unaff_D2b == -8) {
      sVar1 = 0xa0e;
    }
    if (0x3e < *(ushort *)(unaff_A5 + 0x13e)) {
      sVar1 = sVar1 + 7;
    }
    *(short *)(in_A1 + 4) = sVar1;
  }
  return;
}



/* ===== arcade_pc 0x03C8F6 FUN_0003c8f6 ===== */

void FUN_0003c8f6(void)

{
  return;
}



/* ===== arcade_pc 0x03C902 FUN_0003c902 ===== */

/* WARNING: Removing unreachable block (ram,0x0003c9f6) */

void FUN_0003c902(void)

{
  char cVar1;
  byte bVar2;
  undefined2 uVar3;
  undefined2 extraout_D1w;
  int unaff_D2;
  short sVar4;
  short sVar5;
  uint unaff_D6;
  char unaff_D7b;
  byte *in_A0;
  char *extraout_A0;
  char *extraout_A0_00;
  char *extraout_A0_01;
  int in_A1;
  undefined2 *extraout_A1;
  undefined2 *extraout_A1_00;
  short *extraout_A1_01;
  undefined2 *extraout_A1_02;
  short *extraout_A1_03;
  int unaff_A4;
  int unaff_A5;
  
  bVar2 = *in_A0 & 0xf0;
  if (bVar2 == 0x10) {
    if (*(char *)(unaff_A4 + 0x38) == '\0') {
      FUN_0003c85e();
      FUN_0003c85e();
      return;
    }
    FUN_0003c742();
    FUN_0003c742();
    FUN_0003c85e();
    FUN_0003c85e();
    FUN_0003c85e();
    return;
  }
  if (bVar2 == 0x20) {
    FUN_0003c804();
    FUN_0003c804();
    FUN_0003c7d2();
    return;
  }
  if (bVar2 == 0x30) {
    FUN_0003c70a();
    FUN_0003c70a();
    return;
  }
  if ((bVar2 == 0x50) || (bVar2 == 0x60)) {
    if (*(char *)(unaff_A4 + 0xb) == ' ') {
      sVar5 = 10;
      do {
        *(undefined2 *)(in_A1 + 2) = 0x180;
        in_A1 = in_A1 + 8;
        sVar5 = sVar5 + -1;
      } while (sVar5 != 0);
    }
    else {
      FUN_0003c516();
      FUN_0003c516();
    }
    return;
  }
  if (bVar2 == 0x90) {
    FUN_0003c742();
    FUN_0003c7d2();
    FUN_0003c7d2();
    FUN_0003c7d2();
    FUN_0003c7d2();
    return;
  }
  if (bVar2 == 0xa0) {
    sVar5 = 0;
    sVar4 = 4;
    cVar1 = *(char *)((int)(short)*(char *)(unaff_A4 + 0xb) + *(int *)(in_A0 + 2));
    do {
      *(short *)(in_A1 + 6) = sVar5 + *(short *)(unaff_A4 + 0x16) + (short)cVar1;
      *(undefined2 *)(in_A1 + 2) = *(undefined2 *)(unaff_A4 + 0x1a);
      in_A1 = in_A1 + 8;
      sVar5 = sVar5 + 0x10;
      sVar4 = sVar4 + -1;
    } while (sVar4 != 0);
    return;
  }
  if (bVar2 != 0xb0) {
    if (bVar2 == 0xc0) {
      if (*(char *)(unaff_A4 + 1) != '\x06') {
        FUN_0003c606();
        FUN_0003c742();
        FUN_0003c606();
        FUN_0003c742();
        return;
      }
      FUN_0003c742();
      FUN_0003c606();
      FUN_0003c742();
      FUN_0003c606();
      return;
    }
    if ((unaff_D6 & 1) == 0) {
      if (unaff_D7b == '\0') {
        do {
          FUN_0003ca00();
          uVar3 = FUN_0003c9e8();
          *extraout_A1_02 = uVar3;
          extraout_A1_02[1] = *(short *)(unaff_A4 + 0x1a) + (short)*extraout_A0_00;
          FUN_0003ca12();
          *extraout_A1_03 = *(short *)(unaff_A4 + 0x16) + (-0x11 - *extraout_A0_01);
          unaff_D2 = unaff_D2 + -1;
        } while (unaff_D2 != 0);
        return;
      }
    }
    else if ((*(char *)(unaff_A4 + 3) == '\0') && (unaff_D7b != '\0')) {
      FUN_0003c9a6();
      return;
    }
    do {
      FUN_0003ca00();
      uVar3 = FUN_0003c9e8();
      *extraout_A1 = uVar3;
      FUN_0003c8f6();
      *extraout_A1_00 = extraout_D1w;
      FUN_0003ca12();
      *extraout_A1_01 = *(short *)(unaff_A4 + 0x16) + (short)*extraout_A0;
      unaff_D2 = unaff_D2 + -1;
    } while (unaff_D2 != 0);
    return;
  }
  if ((*(char *)(unaff_A5 + 0x118) == '\x02') ||
     ((0x61 < *(ushort *)(unaff_A5 + 0x13e) && (*(ushort *)(unaff_A5 + 0x13e) < 100)))) {
    FUN_0003c742();
    FUN_0003c742();
  }
  FUN_0003c6ac();
  FUN_0003c6ac();
  if ((*(char *)(unaff_A5 + 0x118) != '\x02') &&
     ((*(ushort *)(unaff_A5 + 0x13e) < 0x62 || (99 < *(ushort *)(unaff_A5 + 0x13e))))) {
    return;
  }
  return;
}



/* ===== arcade_pc 0x03C9A6 FUN_0003c9a6 ===== */

void FUN_0003c9a6(void)

{
  undefined2 uVar1;
  undefined2 extraout_D1w;
  int unaff_D2;
  short unaff_D5w;
  char *extraout_A0;
  char *extraout_A0_00;
  char *extraout_A0_01;
  int extraout_A1;
  undefined2 *extraout_A1_00;
  undefined2 *extraout_A1_01;
  short *extraout_A1_02;
  int extraout_A1_03;
  undefined2 *extraout_A1_04;
  short *extraout_A1_05;
  int iVar2;
  int unaff_A4;
  
  do {
    FUN_0003ca00();
    iVar2 = extraout_A1_03;
    if (unaff_D5w != 0) {
      do {
        *(undefined2 *)(iVar2 + 2) = 0x180;
        while( true ) {
          unaff_D2 = unaff_D2 + -1;
          if (unaff_D2 == 0) {
            return;
          }
          FUN_0003ca00();
          iVar2 = extraout_A1;
          if (unaff_D5w != 0) break;
          uVar1 = FUN_0003c9e8();
          *extraout_A1_00 = uVar1;
          FUN_0003c8f6();
          *extraout_A1_01 = extraout_D1w;
          FUN_0003ca12();
          *extraout_A1_02 = *(short *)(unaff_A4 + 0x16) + (short)*extraout_A0;
        }
      } while( true );
    }
    uVar1 = FUN_0003c9e8();
    *extraout_A1_04 = uVar1;
    extraout_A1_04[1] = *(short *)(unaff_A4 + 0x1a) + (short)*extraout_A0_00;
    FUN_0003ca12();
    *extraout_A1_05 = *(short *)(unaff_A4 + 0x16) + (-0x11 - *extraout_A0_01);
    unaff_D2 = unaff_D2 + -1;
  } while (unaff_D2 != 0);
  return;
}



/* ===== arcade_pc 0x03C9E8 FUN_0003c9e8 ===== */

void FUN_0003c9e8(void)

{
  return;
}



/* ===== arcade_pc 0x03CA00 FUN_0003ca00 ===== */

void FUN_0003ca00(void)

{
  return;
}



/* ===== arcade_pc 0x03CA12 FUN_0003ca12 ===== */

undefined2 FUN_0003ca12(void)

{
  ushort uVar1;
  short unaff_D7w;
  byte *in_A0;
  short *in_A1;
  int unaff_A4;
  
  uVar1 = (ushort)*in_A0;
  if (unaff_D7w != 0) {
    uVar1 = -uVar1;
  }
  *in_A1 = *(short *)(unaff_A4 + 0x1e) + uVar1;
  return 0;
}



/* ===== arcade_pc 0x03CF40 FUN_0003cf40 ===== */

undefined4 FUN_0003cf40(void)

{
  undefined4 in_D0;
  
  if ((char)in_D0 == '\0') {
    return 0x38;
  }
  if ((char)in_D0 == '9') {
    in_D0 = 1;
  }
  return in_D0;
}



/* ===== arcade_pc 0x03CF52 FUN_0003cf52 ===== */

void FUN_0003cf52(void)

{
  short in_D0w;
  short sVar1;
  int unaff_A4;
  
  sVar1 = (in_D0w + -1) * 2;
  *(short *)(unaff_A4 + 0x14) = (short)(char)(&DAT_0003cfd4)[sVar1];
  *(short *)(unaff_A4 + 0x18) = (short)(char)(&DAT_0003cfd5)[sVar1];
  if ((*(byte *)(unaff_A4 + 0x13) & 1) == 0) {
    if ((*(byte *)(unaff_A4 + 0x13) & 2) == 0) {
      if ((*(byte *)(unaff_A4 + 0x13) & 4) != 0) {
        sVar1 = FUN_0003cfb0();
        if (sVar1 == 0) {
          return;
        }
        *(undefined2 *)(unaff_A4 + 0x14) = 0;
      }
      if ((*(byte *)(unaff_A4 + 0x13) & 8) != 0) {
        *(undefined2 *)(unaff_A4 + 0x18) = *(undefined2 *)(unaff_A4 + 0x14);
      }
    }
    else {
      *(undefined2 *)(unaff_A4 + 0x14) = 0;
    }
  }
  else {
    *(undefined2 *)(unaff_A4 + 0x18) = 0;
  }
  return;
}



/* ===== arcade_pc 0x03CFB0 FUN_0003cfb0 ===== */

uint FUN_0003cfb0(void)

{
  byte bVar1;
  uint in_D0;
  int unaff_A4;
  
  bVar1 = *(byte *)(unaff_A4 + 0xd);
  if ((3 < bVar1) && ((bVar1 < 0x1a || ((0x1f < bVar1 && (bVar1 < 0x36)))))) {
    return in_D0 & 0xffff0000;
  }
  return 1;
}



/* ===== arcade_pc 0x03D054 FUN_0003d054 ===== */

void FUN_0003d054(void)

{
  char cVar1;
  int unaff_A4;
  
  cVar1 = *(char *)(unaff_A4 + 0x38);
  if (cVar1 == '\x01') {
    FUN_0004770e();
    return;
  }
  if (cVar1 == '\x02') {
    FUN_0003f0bc();
    return;
  }
  if (cVar1 == '\x03') {
    FUN_0003ffdc();
    return;
  }
  if (cVar1 == '\x04') {
    FUN_0003fff0();
    return;
  }
  FUN_0003c902();
  return;
}



/* ===== arcade_pc 0x03EEFA FUN_0003eefa ===== */

ushort FUN_0003eefa(void)

{
  ushort in_D0w;
  ushort uVar1;
  int unaff_A5;
  
  if (*(short *)(unaff_A5 + 700) != 0) {
    *(short *)(unaff_A5 + 700) = *(short *)(unaff_A5 + 700) + -1;
    return in_D0w;
  }
  uVar1 = *(ushort *)(unaff_A5 + 0x2be);
  if (uVar1 != 0) {
    if (uVar1 == 1) {
      uVar1 = *(ushort *)(unaff_A5 + 0x14) | 8;
      *(ushort *)(unaff_A5 + 0x14) = uVar1;
      Ram00380000 = uVar1;
      *(undefined2 *)(unaff_A5 + 700) = 3;
      *(undefined2 *)(unaff_A5 + 0x2be) = 2;
      return uVar1;
    }
    uVar1 = uVar1 - 2;
    if (uVar1 == 0) {
      uVar1 = *(ushort *)(unaff_A5 + 0x14) & 0xfff7;
      *(ushort *)(unaff_A5 + 0x14) = uVar1;
      Ram00380000 = uVar1;
      *(undefined2 *)(unaff_A5 + 700) = 3;
      *(undefined2 *)(unaff_A5 + 0x2be) = 3;
      return uVar1;
    }
    *(undefined2 *)(unaff_A5 + 0x2be) = 0;
  }
  return uVar1;
}



/* ===== arcade_pc 0x03EF5C FUN_0003ef5c ===== */

ushort FUN_0003ef5c(void)

{
  ushort in_D0w;
  ushort uVar1;
  int unaff_A5;
  
  if (*(short *)(unaff_A5 + 0x2c0) != 0) {
    *(short *)(unaff_A5 + 0x2c0) = *(short *)(unaff_A5 + 0x2c0) + -1;
    return in_D0w;
  }
  uVar1 = *(ushort *)(unaff_A5 + 0x2c2);
  if (uVar1 != 0) {
    if (uVar1 == 1) {
      uVar1 = *(ushort *)(unaff_A5 + 0x14) | 4;
      *(ushort *)(unaff_A5 + 0x14) = uVar1;
      Ram00380000 = uVar1;
      *(undefined2 *)(unaff_A5 + 0x2c0) = 3;
      *(undefined2 *)(unaff_A5 + 0x2c2) = 2;
      return uVar1;
    }
    uVar1 = uVar1 - 2;
    if (uVar1 == 0) {
      uVar1 = *(ushort *)(unaff_A5 + 0x14) & 0xfffb;
      *(ushort *)(unaff_A5 + 0x14) = uVar1;
      Ram00380000 = uVar1;
      *(undefined2 *)(unaff_A5 + 0x2c0) = 3;
      *(undefined2 *)(unaff_A5 + 0x2c2) = 3;
      return uVar1;
    }
    *(undefined2 *)(unaff_A5 + 0x2c2) = 0;
  }
  return uVar1;
}



/* ===== arcade_pc 0x03F084 FUN_0003f084 ===== */

byte FUN_0003f084(void)

{
  byte in_D0b;
  
  PC060HA_master_port_3e0001 = 0;
  PC060HA_master_comm_3e0003 = in_D0b;
  PC060HA_master_comm_3e0003 = in_D0b >> 4;
  return in_D0b >> 4;
}



/* ===== arcade_pc 0x03F09C FUN_0003f09c ===== */

undefined1 FUN_0003f09c(void)

{
  undefined1 uVar1;
  
  PC060HA_master_port_3e0001 = 4;
  uVar1 = PC060HA_master_comm_3e0003;
  return uVar1;
}



/* ===== arcade_pc 0x03F0BC FUN_0003f0bc ===== */

void FUN_0003f0bc(void)

{
  FUN_0003c902();
  return;
}



/* ===== arcade_pc 0x03FFDC FUN_0003ffdc ===== */

void FUN_0003ffdc(void)

{
  FUN_0003c902();
  return;
}



/* ===== arcade_pc 0x03FFF0 FUN_0003fff0 ===== */

void FUN_0003fff0(void)

{
  FUN_0003c902();
  return;
}



/* ===== arcade_pc 0x04092E FUN_0004092e ===== */

void FUN_0004092e(void)

{
  short sVar1;
  uint extraout_A0;
  undefined2 *unaff_A4;
  
  *unaff_A4 = 0;
  FUN_0003a2d0();
  sVar1 = 0x702;
  if ((0x10c507 < extraout_A0) && (sVar1 = 0x4e2, 0x10c747 < extraout_A0)) {
    sVar1 = 0x4e2;
  }
  *(undefined2 *)((int)sVar1 + extraout_A0) = 0;
  FUN_0003a2d0();
  return;
}



/* ===== arcade_pc 0x041D08 FUN_00041d08 ===== */

void FUN_00041d08(void)

{
  undefined1 *in_A0;
  int unaff_A4;
  
  *(undefined1 *)(unaff_A4 + 8) = *in_A0;
  *(undefined1 *)(unaff_A4 + 0xd) = in_A0[1];
  *(undefined1 *)(unaff_A4 + 0xe) = in_A0[2];
  *(undefined1 *)(unaff_A4 + 0xf) = in_A0[3];
  *(undefined1 *)(unaff_A4 + 0x10) = in_A0[4];
  *(undefined1 *)(unaff_A4 + 0x11) = in_A0[5];
  *(undefined1 *)(unaff_A4 + 0x13) = in_A0[6];
  return;
}



/* ===== arcade_pc 0x041DAE FUN_00041dae ===== */

void FUN_00041dae(void)

{
  char cVar1;
  short sVar2;
  undefined *puVar3;
  undefined *extraout_A1;
  undefined *extraout_A1_00;
  undefined *extraout_A1_01;
  undefined *extraout_A1_02;
  char *pcVar4;
  int unaff_A5;
  
  pcVar4 = (char *)(unaff_A5 + 0x508);
  puVar3 = &DAT_00d001c8;
  *(undefined2 *)(unaff_A5 + 0x214) = 0;
  do {
    if (*pcVar4 == '\0') {
      sVar2 = 0xd;
      do {
        *(undefined2 *)(puVar3 + 2) = 0x180;
        puVar3 = puVar3 + 8;
        sVar2 = sVar2 + -1;
      } while (sVar2 != 0);
    }
    else {
      FUN_0003d054();
      puVar3 = extraout_A1;
    }
    pcVar4 = pcVar4 + 0x40;
    *(short *)(unaff_A5 + 0x214) = *(short *)(unaff_A5 + 0x214) + 1;
  } while (*(short *)(unaff_A5 + 0x214) != 2);
  pcVar4 = (char *)(unaff_A5 + 0x5c8);
  puVar3 = &DAT_00d00300;
  *(undefined2 *)(unaff_A5 + 0x214) = 0;
  do {
    if (*pcVar4 == '\0') {
      sVar2 = 4;
      do {
        *(undefined2 *)(puVar3 + 2) = 0x180;
        puVar3 = puVar3 + 8;
        sVar2 = sVar2 + -1;
      } while (sVar2 != 0);
    }
    else {
      FUN_0003d054();
      puVar3 = extraout_A1_00;
    }
    pcVar4 = pcVar4 + 0x40;
    *(short *)(unaff_A5 + 0x214) = *(short *)(unaff_A5 + 0x214) + 1;
  } while (*(short *)(unaff_A5 + 0x214) != 6);
  pcVar4 = (char *)(unaff_A5 + 0x2c8);
  *(undefined2 *)(unaff_A5 + 0x214) = 0;
  puVar3 = &DAT_00d00460;
  do {
    if ((*pcVar4 == '\0') || (pcVar4[5] == '\0')) goto code_r0x00041ede;
    if (pcVar4[3] == '\0') goto LAB_00041e60;
    cVar1 = pcVar4[5];
    if (cVar1 == '\x17') {
LAB_0003efc8:
      if (((pcVar4[0x34] & 0x80U) == 0) && (0x17f < (*(ushort *)(pcVar4 + 0x16) & 0x1ff))) {
        FUN_00041ede();
        return;
      }
LAB_00041e60:
      FUN_0003d054();
      puVar3 = extraout_A1_01;
    }
    else {
      if (cVar1 != '\x1a') {
        if (cVar1 == ' ') goto LAB_0003efc8;
        if (cVar1 == '\x13') {
          if (((pcVar4[1] & 1U) == 0) && ((pcVar4[0x34] & 0x80U) == 0)) {
            FUN_00041ede();
            return;
          }
        }
        else if (cVar1 == '\"') {
          if (((pcVar4[0xd] == 'y') && (0x4f < *(ushort *)(pcVar4 + 0x34))) &&
             (*(ushort *)(pcVar4 + 0x34) < 0xfe60)) {
            FUN_00041ede();
            return;
          }
        }
        else if (((cVar1 == '\x15') && (*(short *)(unaff_A5 + 0x13e) == 0x71)) &&
                ((pcVar4[0x16] & 0x80U) != 0)) {
          FUN_00041ede();
          return;
        }
        goto LAB_00041e60;
      }
      if (*(ushort *)(unaff_A5 + 0x13e) < 0x87) {
        if (pcVar4[0x32] == '\0') goto LAB_0003efc8;
        if ((pcVar4[0x742] & 0x80U) != 0) goto code_r0x00041ede;
        goto LAB_00041e60;
      }
      if (0xfe07 < *(ushort *)(pcVar4 + 0x34)) goto LAB_00041e60;
code_r0x00041ede:
      sVar2 = 10;
      if (*(short *)(unaff_A5 + 0x214) == 8) {
        sVar2 = 0x13;
      }
      do {
        *(undefined2 *)(puVar3 + 2) = 0x180;
        puVar3 = puVar3 + 8;
        sVar2 = sVar2 + -1;
      } while (sVar2 != 0);
    }
    pcVar4 = pcVar4 + 0x40;
    *(short *)(unaff_A5 + 0x214) = *(short *)(unaff_A5 + 0x214) + 1;
    if (*(short *)(unaff_A5 + 0x214) == 9) {
      pcVar4 = (char *)(unaff_A5 + 0x748);
      puVar3 = &DAT_00d00170;
      *(undefined2 *)(unaff_A5 + 0x214) = 0;
      do {
        if ((*pcVar4 == '\0') || (pcVar4[0x36] != '\0')) {
          sVar2 = 1;
          do {
            *(undefined2 *)(puVar3 + 2) = 0x180;
            puVar3 = puVar3 + 8;
            sVar2 = sVar2 + -1;
          } while (sVar2 != 0);
        }
        else {
          FUN_0003d054();
          puVar3 = extraout_A1_02;
        }
        pcVar4 = pcVar4 + 0x40;
        *(short *)(unaff_A5 + 0x214) = *(short *)(unaff_A5 + 0x214) + 1;
      } while (*(short *)(unaff_A5 + 0x214) != 0xb);
      return;
    }
  } while( true );
}



/* ===== arcade_pc 0x041EDE FUN_00041ede ===== */

void FUN_00041ede(void)

{
  char cVar1;
  short sVar2;
  int extraout_A1;
  undefined *puVar3;
  undefined *extraout_A1_00;
  int in_A1;
  char *pcVar4;
  char *unaff_A4;
  int unaff_A5;
  
  do {
    sVar2 = 10;
    if (*(short *)(unaff_A5 + 0x214) == 8) {
      sVar2 = 0x13;
    }
    do {
      *(undefined2 *)(in_A1 + 2) = 0x180;
      in_A1 = in_A1 + 8;
      sVar2 = sVar2 + -1;
      pcVar4 = unaff_A4;
    } while (sVar2 != 0);
    while( true ) {
      unaff_A4 = pcVar4 + 0x40;
      *(short *)(unaff_A5 + 0x214) = *(short *)(unaff_A5 + 0x214) + 1;
      if (*(short *)(unaff_A5 + 0x214) == 9) {
        pcVar4 = (char *)(unaff_A5 + 0x748);
        puVar3 = &DAT_00d00170;
        *(undefined2 *)(unaff_A5 + 0x214) = 0;
        do {
          if ((*pcVar4 == '\0') || (pcVar4[0x36] != '\0')) {
            sVar2 = 1;
            do {
              *(undefined2 *)(puVar3 + 2) = 0x180;
              puVar3 = puVar3 + 8;
              sVar2 = sVar2 + -1;
            } while (sVar2 != 0);
          }
          else {
            FUN_0003d054();
            puVar3 = extraout_A1_00;
          }
          pcVar4 = pcVar4 + 0x40;
          *(short *)(unaff_A5 + 0x214) = *(short *)(unaff_A5 + 0x214) + 1;
        } while (*(short *)(unaff_A5 + 0x214) != 0xb);
        return;
      }
      if ((*unaff_A4 == '\0') || (pcVar4[0x45] == '\0')) break;
      if (pcVar4[0x43] != '\0') {
        cVar1 = pcVar4[0x45];
        if (cVar1 == '\x17') {
LAB_0003efc8:
          if (((pcVar4[0x74] & 0x80U) == 0) && (0x17f < (*(ushort *)(pcVar4 + 0x56) & 0x1ff))) {
            FUN_00041ede();
            return;
          }
        }
        else if (cVar1 == '\x1a') {
          if (*(ushort *)(unaff_A5 + 0x13e) < 0x87) {
            if (pcVar4[0x72] == '\0') goto LAB_0003efc8;
            if ((pcVar4[0x782] & 0x80U) != 0) break;
          }
          else if (*(ushort *)(pcVar4 + 0x74) < 0xfe08) break;
        }
        else {
          if (cVar1 == ' ') goto LAB_0003efc8;
          if (cVar1 == '\x13') {
            if (((pcVar4[0x41] & 1U) == 0) && ((pcVar4[0x74] & 0x80U) == 0)) {
              FUN_00041ede();
              return;
            }
          }
          else if (cVar1 == '\"') {
            if (((pcVar4[0x4d] == 'y') && (0x4f < *(ushort *)(pcVar4 + 0x74))) &&
               (*(ushort *)(pcVar4 + 0x74) < 0xfe60)) {
              FUN_00041ede();
              return;
            }
          }
          else if (((cVar1 == '\x15') && (*(short *)(unaff_A5 + 0x13e) == 0x71)) &&
                  ((pcVar4[0x56] & 0x80U) != 0)) {
            FUN_00041ede();
            return;
          }
        }
      }
      FUN_0003d054();
      in_A1 = extraout_A1;
      pcVar4 = unaff_A4;
    }
  } while( true );
}



/* ===== arcade_pc 0x041F30 FUN_00041f30 ===== */

void FUN_00041f30(void)

{
  short sVar1;
  undefined *puVar2;
  undefined *extraout_A1;
  undefined *extraout_A1_00;
  undefined *extraout_A1_01;
  char *pcVar3;
  int unaff_A5;
  
  FUN_00055ab4();
  FUN_00045d72();
  FUN_0005988c();
  FUN_00059882();
  FUN_00047004();
  FUN_00041f5e();
  if (*(short *)(unaff_A5 + 0x2a2) != 2) {
    FUN_00041dae();
    return;
  }
  pcVar3 = (char *)(unaff_A5 + 0x5c8);
  puVar2 = &DAT_00d00460;
  *(undefined2 *)(unaff_A5 + 0x214) = 0;
  do {
    if (*pcVar3 == '\0') {
      sVar1 = 10;
      if (2 < *(ushort *)(unaff_A5 + 0x214)) {
        sVar1 = 0x14;
      }
      do {
        *(undefined2 *)(puVar2 + 2) = 0x180;
        puVar2 = puVar2 + 8;
        sVar1 = sVar1 + -1;
      } while (sVar1 != 0);
    }
    else {
      FUN_0003d054();
      puVar2 = extraout_A1;
    }
    pcVar3 = pcVar3 + 0x40;
    *(short *)(unaff_A5 + 0x214) = *(short *)(unaff_A5 + 0x214) + 1;
  } while (*(short *)(unaff_A5 + 0x214) != 6);
  pcVar3 = (char *)(unaff_A5 + 0x748);
  puVar2 = &DAT_00d00170;
  *(undefined2 *)(unaff_A5 + 0x214) = 0;
  do {
    if (*pcVar3 == '\0') {
      sVar1 = 6;
      do {
        *(undefined2 *)(puVar2 + 2) = 0x180;
        puVar2 = puVar2 + 8;
        sVar1 = sVar1 + -1;
      } while (sVar1 != 0);
    }
    else {
      FUN_0003d054();
      puVar2 = extraout_A1_00;
    }
    pcVar3 = pcVar3 + 0x40;
    *(short *)(unaff_A5 + 0x214) = *(short *)(unaff_A5 + 0x214) + 1;
  } while (*(short *)(unaff_A5 + 0x214) != 6);
  pcVar3 = (char *)(unaff_A5 + 0x8c8);
  puVar2 = &DAT_00d00300;
  *(undefined2 *)(unaff_A5 + 0x214) = 0;
  do {
    if (*pcVar3 == '\0') {
      sVar1 = 4;
      do {
        *(undefined2 *)(puVar2 + 2) = 0x180;
        puVar2 = puVar2 + 8;
        sVar1 = sVar1 + -1;
      } while (sVar1 != 0);
    }
    else {
      FUN_0003d054();
      puVar2 = extraout_A1_01;
    }
    pcVar3 = pcVar3 + 0x40;
    *(short *)(unaff_A5 + 0x214) = *(short *)(unaff_A5 + 0x214) + 1;
  } while (*(short *)(unaff_A5 + 0x214) != 5);
  return;
}



/* ===== arcade_pc 0x041F5E FUN_00041f5e ===== */

void FUN_00041f5e(void)

{
  short sVar1;
  short *psVar2;
  short *psVar3;
  short *psVar4;
  int unaff_A5;
  
  FUN_00041f7a();
  psVar3 = (short *)(unaff_A5 + 0x170);
  sVar1 = 4;
  psVar4 = (short *)&DAT_00d002e0;
  do {
    if (*psVar3 == 0) {
      psVar4[1] = 0x180;
    }
    else {
      *psVar4 = *psVar3;
      psVar4[1] = psVar3[1];
      psVar2 = psVar3 + 3;
      psVar4[2] = psVar3[2];
      psVar3 = psVar3 + 4;
      psVar4[3] = *psVar2;
    }
    psVar4 = psVar4 + 4;
    sVar1 = sVar1 + -1;
  } while (sVar1 != 0);
  return;
}



/* ===== arcade_pc 0x041F7A FUN_00041f7a ===== */

void FUN_00041f7a(void)

{
  short in_D0w;
  short *in_A0;
  short *psVar1;
  short *in_A1;
  
  do {
    if (*in_A0 == 0) {
      in_A1[1] = 0x180;
    }
    else {
      *in_A1 = *in_A0;
      in_A1[1] = in_A0[1];
      psVar1 = in_A0 + 3;
      in_A1[2] = in_A0[2];
      in_A0 = in_A0 + 4;
      in_A1[3] = *psVar1;
    }
    in_A1 = in_A1 + 4;
    in_D0w = in_D0w + -1;
  } while (in_D0w != 0);
  return;
}



/* ===== arcade_pc 0x042D20 FUN_00042d20 ===== */

void FUN_00042d20(void)

{
  short in_D0w;
  int unaff_A4;
  
  if (*(byte *)(unaff_A4 + 5) < 3) {
    *(undefined1 *)(unaff_A4 + 2) =
         *(undefined1 *)((int)&PTR_DAT_00042d91 + (int)(short)(in_D0w << 3));
  }
  FUN_00041d08();
  return;
}



/* ===== arcade_pc 0x042E38 FUN_00042e38 ===== */

void FUN_00042e38(void)

{
  byte bVar1;
  char cVar2;
  undefined1 uVar3;
  int extraout_A0;
  int unaff_A4;
  
  if (*(char *)(unaff_A4 + 7) == '\0') {
    *(undefined1 *)(unaff_A4 + 9) = *(undefined1 *)(unaff_A4 + 8);
    *(undefined1 *)(unaff_A4 + 7) = 1;
  }
  else {
    cVar2 = *(char *)(unaff_A4 + 9) + -1;
    *(char *)(unaff_A4 + 9) = cVar2;
    if (cVar2 != '\0') {
      return;
    }
    *(undefined1 *)(unaff_A4 + 9) = *(undefined1 *)(unaff_A4 + 8);
    cVar2 = *(char *)(unaff_A4 + 0x12) + -1;
    *(char *)(unaff_A4 + 0x12) = cVar2;
    if (cVar2 != '\0') goto LAB_00042eb6;
    cVar2 = *(char *)(unaff_A4 + 0xe) + -1;
    *(char *)(unaff_A4 + 0xe) = cVar2;
    if (cVar2 == '\0') {
      *(undefined1 *)(unaff_A4 + 7) = 0;
      return;
    }
    uVar3 = FUN_0003cf40();
    *(undefined1 *)(unaff_A4 + 0xd) = uVar3;
  }
  FUN_0003cf52();
  bVar1 = *(byte *)(unaff_A4 + 0xd);
  if ((bVar1 < 8) ||
     ((0xd < (byte)(bVar1 - 8) && (((byte)(bVar1 - 0x16) < 0xe || (0xd < (byte)(bVar1 - 0x24)))))))
  {
    uVar3 = *(undefined1 *)(unaff_A4 + 0x10);
  }
  else {
    uVar3 = *(undefined1 *)(unaff_A4 + 0x11);
  }
  *(undefined1 *)(unaff_A4 + 0x12) = uVar3;
LAB_00042eb6:
  if (*(char *)(unaff_A4 + 0x26) == '\0') {
    *(short *)(unaff_A4 + 0x16) = *(short *)(unaff_A4 + 0x14) + *(short *)(unaff_A4 + 0x16);
    *(short *)(unaff_A4 + 0x1a) = *(short *)(unaff_A4 + 0x18) + *(short *)(unaff_A4 + 0x1a);
    if ((*(byte *)(unaff_A4 + 6) < 5) && (FUN_00053a2e(), (*(byte *)(extraout_A0 + 1) & 1) != 0)) {
      FUN_000447f0();
    }
  }
  return;
}



/* ===== arcade_pc 0x0447F0 FUN_000447f0 ===== */

void FUN_000447f0(void)

{
  int unaff_A4;
  
  *(undefined1 *)(unaff_A4 + 0x3d) = 1;
  if (*(char *)(unaff_A4 + 6) != '\a') {
    FUN_000448b2();
  }
  return;
}



/* ===== arcade_pc 0x0448B2 FUN_000448b2 ===== */

void FUN_000448b2(void)

{
  int unaff_A4;
  
  *(undefined1 *)(unaff_A4 + 7) = 0;
  *(undefined1 *)(unaff_A4 + 8) = 0xff;
  *(undefined1 *)(unaff_A4 + 0x3c) = 0;
  *(undefined1 *)(unaff_A4 + 5) = 0xf;
  *(undefined1 *)(unaff_A4 + 9) = 1;
  FUN_0003a0ec();
  return;
}



/* ===== arcade_pc 0x045248 FUN_00045248 ===== */

void FUN_00045248(void)

{
  undefined1 in_D0b;
  undefined1 in_D1b;
  undefined1 unaff_D2b;
  undefined2 unaff_D3w;
  undefined1 *unaff_A4;
  
  *unaff_A4 = 1;
  unaff_A4[3] = 1;
  unaff_A4[0x2f] = in_D0b;
  unaff_A4[4] = 1;
  *(undefined2 *)(unaff_A4 + 0x1c) = 1;
  unaff_A4[0x20] = 1;
  unaff_A4[0x21] = in_D1b;
  unaff_A4[0xd] = unaff_D2b;
  *(undefined2 *)(unaff_A4 + 0x1e) = unaff_D3w;
  *(undefined2 *)(unaff_A4 + 0x1a) = 0x180;
  return;
}



/* ===== arcade_pc 0x045342 FUN_00045342 ===== */

void FUN_00045342(void)

{
  int unaff_A5;
  
  if (*(char *)(unaff_A5 + 0x548) == '\0') {
    if (*(short *)(unaff_A5 + 0xc5a) == 0) {
      *(undefined1 *)(unaff_A5 + 0x50e) = 8;
      *(undefined1 *)(unaff_A5 + 0x54e) = 8;
    }
    else {
      *(undefined1 *)(unaff_A5 + 0x50e) = 9;
      *(undefined1 *)(unaff_A5 + 0x54e) = 9;
    }
    *(undefined1 *)(unaff_A5 + 0x547) = 1;
    *(byte *)(unaff_A5 + 0x52f) = *(byte *)(unaff_A5 + 0x52f) | 0x80;
    FUN_000453a2();
    FUN_000453c0();
    *(byte *)(unaff_A5 + 0x56f) = *(byte *)(unaff_A5 + 0x56f) | 0x80;
    FUN_000453a2();
    FUN_000453c0();
    FUN_0003a0ec();
    return;
  }
  return;
}



/* ===== arcade_pc 0x0453A2 FUN_000453a2 ===== */

void FUN_000453a2(void)

{
  undefined1 *unaff_A4;
  
  *(undefined2 *)(unaff_A4 + 0x1c) = 1;
  *unaff_A4 = 1;
  unaff_A4[5] = 3;
  *(undefined2 *)(unaff_A4 + 0x1a) = 0x180;
  FUN_0004543e();
  return;
}



/* ===== arcade_pc 0x0453C0 FUN_000453c0 ===== */

void FUN_000453c0(void)

{
  int unaff_A4;
  int unaff_A5;
  
  if (4 < *(byte *)(unaff_A5 + 0x118)) {
    *(undefined1 *)(unaff_A4 + 0x28) = 4;
    *(undefined2 *)(unaff_A4 + 0x2c) = 7;
  }
  return;
}



/* ===== arcade_pc 0x0453D6 FUN_000453d6 ===== */

char FUN_000453d6(void)

{
  char cVar1;
  char in_D0b;
  int unaff_A4;
  int unaff_A5;
  
  if (*(char *)(unaff_A4 + 6) != '\f') {
    cVar1 = *(char *)(unaff_A5 + 0x2f);
    if (cVar1 == '\0') {
      if (1 < *(byte *)(unaff_A4 + 0x28)) {
        *(char *)(unaff_A4 + 0x28) = *(char *)(unaff_A4 + 0x28) + -1;
      }
      in_D0b = '\0';
      if (1 < *(byte *)(unaff_A4 + 0x29)) {
        *(char *)(unaff_A4 + 0x29) = *(char *)(unaff_A4 + 0x29) + -1;
        return '\0';
      }
    }
    else {
      in_D0b = '\0';
      if (cVar1 != '\x01') {
        in_D0b = cVar1 + -2;
        if (in_D0b == '\0') {
          *(char *)(unaff_A4 + 0x29) = *(char *)(unaff_A4 + 0x29) + '\x01';
          return '\0';
        }
        *(char *)(unaff_A4 + 0x28) = *(char *)(unaff_A4 + 0x28) + '\x01';
        *(char *)(unaff_A4 + 0x29) = *(char *)(unaff_A4 + 0x29) + '\x01';
      }
    }
  }
  return in_D0b;
}



/* ===== arcade_pc 0x04543E FUN_0004543e ===== */

void FUN_0004543e(void)

{
  int iVar1;
  int unaff_A4;
  
  iVar1 = (int)(short)((*(byte *)(unaff_A4 + 6) - 8) * 8);
  *(undefined2 *)(unaff_A4 + 0x1e) = *(undefined2 *)(&DAT_00045592 + iVar1);
  *(undefined *)(unaff_A4 + 0x3a) = (&DAT_00045594)[iVar1];
  *(undefined *)(unaff_A4 + 1) = (&DAT_00045595)[iVar1];
  *(undefined2 *)(unaff_A4 + 0x28) = *(undefined2 *)(&DAT_00045596 + iVar1);
  *(undefined2 *)(unaff_A4 + 0x2c) = *(undefined2 *)((int)&PTR_DAT_00045598 + iVar1);
  FUN_000453d6();
  return;
}



/* ===== arcade_pc 0x045AA0 FUN_00045aa0 ===== */

void FUN_00045aa0(void)

{
  int unaff_A4;
  
  *(undefined2 *)(unaff_A4 + 0x1a) = 0x1f0;
  *(undefined1 *)(unaff_A4 + 6) = 0xd;
  FUN_0004543e();
  FUN_00045cfc();
  return;
}



/* ===== arcade_pc 0x045B18 FUN_00045b18 ===== */

void FUN_00045b18(void)

{
  undefined2 in_D0w;
  undefined2 uVar1;
  int unaff_A4;
  int unaff_A5;
  
  *(undefined2 *)(unaff_A4 + 0x1a) = in_D0w;
  FUN_00045ce0();
  if (*(short *)(unaff_A5 + 0x13e) == 0x58) {
    return;
  }
  FUN_0004092e();
  *(char *)(unaff_A5 + 0x6e9) = (char)*(undefined2 *)(unaff_A5 + 0x200);
  uVar1 = 0x112;
  if (*(char *)(unaff_A5 + 0x118) != '\x02') {
    uVar1 = 10;
  }
  *(char *)(unaff_A5 + 0x6ce) = (char)uVar1;
  *(char *)(unaff_A5 + 0x700) = (char)((ushort)uVar1 >> 8);
  FUN_0004543e();
  FUN_00045cfc();
  FUN_00045be8();
  FUN_0004092e();
  *(char *)(unaff_A5 + 0x9e9) = (char)*(undefined2 *)(unaff_A5 + 0x200) + '\x01';
  *(undefined1 *)(unaff_A5 + 0x9ce) = 0xb;
  FUN_0004543e();
  FUN_00045cfc();
  FUN_00045be8();
  if (3 < *(byte *)(unaff_A5 + 0x118)) {
    FUN_0004092e();
    *(char *)(unaff_A5 + 0x9a9) = (char)*(undefined2 *)(unaff_A5 + 0x200) + '\x02';
    *(undefined1 *)(unaff_A5 + 0x98e) = 0xb;
    FUN_0004543e();
    FUN_00045cfc();
    FUN_00045be8();
    if (5 < *(byte *)(unaff_A5 + 0x118)) {
      FUN_0004092e();
      *(char *)(unaff_A5 + 0x969) = (char)*(undefined2 *)(unaff_A5 + 0x200) + '\x03';
      *(undefined1 *)(unaff_A5 + 0x94e) = 0xb;
      FUN_0004543e();
      FUN_00045cfc();
      FUN_00045be8();
    }
  }
  FUN_0003a0ec();
  return;
}



/* ===== arcade_pc 0x045BE8 FUN_00045be8 ===== */

void FUN_00045be8(void)

{
  undefined2 uVar1;
  short sVar2;
  int unaff_A4;
  int unaff_A5;
  
  uVar1 = *(undefined2 *)(unaff_A5 + 0x71e);
  *(undefined2 *)(unaff_A4 + 0x16) = uVar1;
  *(undefined2 *)(unaff_A4 + 0x32) = uVar1;
  sVar2 = *(short *)(unaff_A5 + 0x722) + 0x14;
  *(short *)(unaff_A4 + 0x1a) = sVar2;
  *(short *)(unaff_A4 + 0x30) = sVar2;
  *(byte *)(unaff_A4 + 0x27) = *(byte *)(unaff_A4 + 0x27) | 0x80;
  return;
}



/* ===== arcade_pc 0x045CE0 FUN_00045ce0 ===== */

void FUN_00045ce0(void)

{
  char cVar1;
  undefined1 *unaff_A4;
  int unaff_A5;
  
  unaff_A4[6] = 0xc;
  FUN_0004543e();
  cVar1 = (char)*(undefined2 *)(unaff_A5 + 0x254);
  unaff_A4[0x25] = cVar1;
  unaff_A4[1] = cVar1 + unaff_A4[1];
  unaff_A4[0x26] = 1;
  *unaff_A4 = 1;
  unaff_A4[5] = 3;
  *(undefined2 *)(unaff_A4 + 0x1c) = 1;
  return;
}



/* ===== arcade_pc 0x045CFC FUN_00045cfc ===== */

void FUN_00045cfc(void)

{
  undefined1 *unaff_A4;
  
  *unaff_A4 = 1;
  unaff_A4[5] = 3;
  *(undefined2 *)(unaff_A4 + 0x1c) = 1;
  return;
}



/* ===== arcade_pc 0x045D10 FUN_00045d10 ===== */

undefined4 FUN_00045d10(void)

{
  ushort uVar1;
  short sVar2;
  ushort *extraout_A0;
  ushort *puVar3;
  ushort *puVar4;
  int unaff_A5;
  
  *(undefined2 *)(unaff_A5 + 0x21a) = 0x40;
  *(undefined2 *)(unaff_A5 + 0x216) = 0x144;
  *(ushort *)(unaff_A5 + 0x218) = *(short *)(&DAT_000010b0 + unaff_A5) - 4U & 0x1ff;
  FUN_00053a2e();
  uVar1 = *(ushort *)(unaff_A5 + 0x256);
  puVar3 = extraout_A0;
  do {
    if (uVar1 < 0x30) {
      if ((char)*puVar3 == (char)uVar1) {
        return 1;
      }
    }
    else if (*puVar3 >> 8 == uVar1) {
      return 1;
    }
    *(short *)(unaff_A5 + 0x218) = *(short *)(unaff_A5 + 0x218) + -8;
    puVar4 = puVar3 + -0x40;
    if (puVar4 < (ushort *)0x10de00) {
      puVar4 = puVar3 + 0xfc0;
    }
    sVar2 = *(short *)(unaff_A5 + 0x21a) + -1;
    *(short *)(unaff_A5 + 0x21a) = sVar2;
    puVar3 = puVar4;
  } while (sVar2 != 0);
  return 0;
}



/* ===== arcade_pc 0x045D72 FUN_00045d72 ===== */

void FUN_00045d72(void)

{
  FUN_00045d7c();
  FUN_00045dc4();
  return;
}



/* ===== arcade_pc 0x045D7C FUN_00045d7c ===== */

void FUN_00045d7c(void)

{
  int unaff_A5;
  
  if (*(short *)(unaff_A5 + 0x238) != 0) {
    if (7 < (ushort)(*(short *)(unaff_A5 + 0x238) - 1U)) {
      *(undefined2 *)(unaff_A5 + 0x238) = 0;
      *(undefined2 *)(&DAT_000013b0 + unaff_A5) = 1;
      FUN_0003ba20();
      *(undefined2 *)(unaff_A5 + 0xc50) = 1;
      return;
    }
    FUN_0003a2d0();
    *(short *)(unaff_A5 + 0x238) = *(short *)(unaff_A5 + 0x238) + 1;
  }
  return;
}



/* ===== arcade_pc 0x045DC4 FUN_00045dc4 ===== */

void FUN_00045dc4(void)

{
  int unaff_A5;
  
  if (*(short *)(unaff_A5 + 0xc50) == 0) {
    return;
  }
  if (7 < (ushort)(*(short *)(unaff_A5 + 0xc50) - 1U)) {
    *(undefined2 *)(unaff_A5 + 0xc50) = 0;
    return;
  }
  FUN_0003a2d0();
  *(short *)(unaff_A5 + 0xc50) = *(short *)(unaff_A5 + 0xc50) + 1;
  return;
}



/* ===== arcade_pc 0x045DFA FUN_00045dfa ===== */

void FUN_00045dfa(void)

{
  short sVar1;
  undefined *puVar2;
  undefined *extraout_A1;
  undefined *extraout_A1_00;
  undefined *extraout_A1_01;
  char *pcVar3;
  int unaff_A5;
  
  pcVar3 = (char *)(unaff_A5 + 0x5c8);
  puVar2 = &DAT_00d00460;
  *(undefined2 *)(unaff_A5 + 0x214) = 0;
  do {
    if (*pcVar3 == '\0') {
      sVar1 = 10;
      if (2 < *(ushort *)(unaff_A5 + 0x214)) {
        sVar1 = 0x14;
      }
      do {
        *(undefined2 *)(puVar2 + 2) = 0x180;
        puVar2 = puVar2 + 8;
        sVar1 = sVar1 + -1;
      } while (sVar1 != 0);
    }
    else {
      FUN_0003d054();
      puVar2 = extraout_A1;
    }
    pcVar3 = pcVar3 + 0x40;
    *(short *)(unaff_A5 + 0x214) = *(short *)(unaff_A5 + 0x214) + 1;
  } while (*(short *)(unaff_A5 + 0x214) != 6);
  pcVar3 = (char *)(unaff_A5 + 0x748);
  puVar2 = &DAT_00d00170;
  *(undefined2 *)(unaff_A5 + 0x214) = 0;
  do {
    if (*pcVar3 == '\0') {
      sVar1 = 6;
      do {
        *(undefined2 *)(puVar2 + 2) = 0x180;
        puVar2 = puVar2 + 8;
        sVar1 = sVar1 + -1;
      } while (sVar1 != 0);
    }
    else {
      FUN_0003d054();
      puVar2 = extraout_A1_00;
    }
    pcVar3 = pcVar3 + 0x40;
    *(short *)(unaff_A5 + 0x214) = *(short *)(unaff_A5 + 0x214) + 1;
  } while (*(short *)(unaff_A5 + 0x214) != 6);
  pcVar3 = (char *)(unaff_A5 + 0x8c8);
  puVar2 = &DAT_00d00300;
  *(undefined2 *)(unaff_A5 + 0x214) = 0;
  do {
    if (*pcVar3 == '\0') {
      sVar1 = 4;
      do {
        *(undefined2 *)(puVar2 + 2) = 0x180;
        puVar2 = puVar2 + 8;
        sVar1 = sVar1 + -1;
      } while (sVar1 != 0);
    }
    else {
      FUN_0003d054();
      puVar2 = extraout_A1_01;
    }
    pcVar3 = pcVar3 + 0x40;
    *(short *)(unaff_A5 + 0x214) = *(short *)(unaff_A5 + 0x214) + 1;
  } while (*(short *)(unaff_A5 + 0x214) != 5);
  return;
}



/* ===== arcade_pc 0x046790 FUN_00046790 ===== */

void FUN_00046790(void)

{
  FUN_00045248();
  return;
}



/* ===== arcade_pc 0x046AB4 FUN_00046ab4 ===== */

void FUN_00046ab4(void)

{
  short sVar1;
  undefined2 *puVar2;
  int unaff_A5;
  int iVar3;
  
  sVar1 = 2;
  if ((0x47 < *(ushort *)(&DAT_000010be + unaff_A5)) &&
     (sVar1 = 1, 0xf7 < *(ushort *)(&DAT_000010be + unaff_A5))) {
    sVar1 = 0;
  }
  puVar2 = (undefined2 *)((int)&DAT_00046b30 + (int)(short)(sVar1 * 0x1e));
  sVar1 = 0;
  iVar3 = unaff_A5 + 0x748;
  do {
    if ((((*(char *)(iVar3 + 5) != '\x03') && (*(char *)(iVar3 + 5) != '\v')) &&
        (*(char *)(iVar3 + 5) != '\x0f')) && (*(char *)(iVar3 + 7) != '\0')) {
      *(undefined2 *)(iVar3 + 0x14) = *puVar2;
      *(undefined2 *)(iVar3 + 0x18) = puVar2[1];
      *(undefined1 *)(iVar3 + 1) = *(undefined1 *)((int)puVar2 + 5);
      *(undefined1 *)(iVar3 + 5) = 0xb;
      *(undefined1 *)(iVar3 + 7) = 1;
      *(undefined1 *)(iVar3 + 9) = 1;
      *(undefined1 *)(iVar3 + 0x12) = 0;
    }
    iVar3 = iVar3 + 0x40;
    puVar2 = puVar2 + 3;
    sVar1 = sVar1 + 1;
  } while (sVar1 != 5);
  return;
}



/* ===== arcade_pc 0x046BC4 FUN_00046bc4 ===== */

void FUN_00046bc4(void)

{
  ushort uVar1;
  int unaff_A4;
  int unaff_A5;
  
  uVar1 = (ushort)(0x9f < *(ushort *)(&DAT_000010c0 + unaff_A5));
  if (0x9f < *(ushort *)(unaff_A4 + 0x1a)) {
    uVar1 = uVar1 + 2;
  }
  *(ushort *)(unaff_A5 + 0x274) = uVar1;
  return;
}



/* ===== arcade_pc 0x047004 FUN_00047004 ===== */

void FUN_00047004(void)

{
  int unaff_A5;
  
  if (*(short *)(unaff_A5 + 0x26e) != 0) {
    if (6 < *(ushort *)(unaff_A5 + 0x270)) {
      *(undefined2 *)(unaff_A5 + 0x26e) = 0;
    }
    FUN_0004703c();
  }
  return;
}



/* ===== arcade_pc 0x04703C FUN_0004703c ===== */

void FUN_0004703c(void)

{
  ushort uVar1;
  ushort extraout_D1w;
  ushort extraout_D1w_00;
  int unaff_D3;
  ushort *extraout_A0;
  ushort *unaff_A3;
  
  do {
    uVar1 = *unaff_A3;
    FUN_00047076();
    FUN_00047076();
    FUN_00047076();
    *extraout_A0 = ((extraout_D1w & 0xf0) >> 4) << 6 |
                   (uVar1 & 0xf) << 0xb | ((extraout_D1w_00 & 0xf00) >> 8) << 1;
    unaff_D3 = unaff_D3 + -1;
    unaff_A3 = unaff_A3 + 1;
  } while (unaff_D3 != 0);
  return;
}



/* ===== arcade_pc 0x047076 FUN_00047076 ===== */

void FUN_00047076(void)

{
  return;
}



/* ===== arcade_pc 0x04736A FUN_0004736a ===== */

void FUN_0004736a(void)

{
  undefined2 *extraout_A0;
  int unaff_A4;
  
  if ((*(char *)(unaff_A4 + 7) == '\0') && (*(byte *)(unaff_A4 + 5) < 0xd)) {
    FUN_00053a2e();
    if ((char)((ushort)*extraout_A0 >> 8) == '\0') {
      *(char *)(unaff_A4 + 0x74f) = *(char *)(unaff_A4 + 0x74f) + '\x01';
    }
    else {
      *(undefined1 *)(unaff_A4 + 0x74f) = 0;
    }
    if (2 < *(byte *)(unaff_A4 + 0x74f)) {
      *(undefined1 *)(unaff_A4 + 0x39) = 1;
      FUN_000447f0();
    }
  }
  return;
}



/* ===== arcade_pc 0x04770E FUN_0004770e ===== */

void FUN_0004770e(void)

{
  FUN_0003c902();
  return;
}



/* ===== arcade_pc 0x04AF0A FUN_0004af0a ===== */

void FUN_0004af0a(void)

{
  int unaff_A4;
  
  FUN_00046790();
  *(undefined1 *)(unaff_A4 + 0x38) = 2;
  return;
}



/* ===== arcade_pc 0x04BBCA FUN_0004bbca ===== */

void FUN_0004bbca(void)

{
  int unaff_A4;
  
  *(undefined2 *)(unaff_A4 + 0x16) = 0x140;
  *(undefined1 *)(unaff_A4 + 0x531) = 1;
  *(undefined2 *)(unaff_A4 + 0x1a) = 0x120;
  *(undefined1 *)(unaff_A4 + 6) = 0x1c;
  *(undefined1 *)(unaff_A4 + 0x38) = 1;
  FUN_0004543e();
  FUN_00045cfc();
  return;
}



/* ===== arcade_pc 0x0510C6 FUN_000510c6 ===== */

void FUN_000510c6(void)

{
  return;
}



/* ===== arcade_pc 0x052466 FUN_00052466 ===== */

void FUN_00052466(void)

{
  ushort uVar1;
  byte *pbVar2;
  int unaff_A5;
  
  *(short *)(&DAT_00001336 + unaff_A5) = *(short *)(&DAT_00001336 + unaff_A5) + 1;
  pbVar2 = (byte *)((int)(short)(*(short *)(&DAT_00001336 + unaff_A5) << 1) +
                   *(int *)(&DAT_00001332 + unaff_A5));
  uVar1 = (ushort)*pbVar2;
  if (uVar1 == 0xff) {
    *(undefined2 *)(&DAT_000010e8 + unaff_A5) = 3;
  }
  else {
    *(ushort *)(&DAT_00001268 + unaff_A5) = uVar1 + *(short *)(&DAT_00001268 + unaff_A5);
    *(ushort *)(&DAT_00001262 + unaff_A5) = (ushort)pbVar2[1] + *(short *)(&DAT_00001262 + unaff_A5)
    ;
  }
  return;
}



/* ===== arcade_pc 0x0527D4 FUN_000527d4 ===== */

void FUN_000527d4(void)

{
  if ((DAT_0010c016 & 2) == 0) {
    FUN_00052912();
  }
  if ((DAT_0010c016 & 1) == 0) {
    FUN_0005290c();
  }
  if ((DAT_0010c016 & 4) == 0) {
    FUN_0005291e();
  }
  if ((DAT_0010c016 & 8) == 0) {
    FUN_00052918();
  }
  return;
}



/* ===== arcade_pc 0x052816 FUN_00052816 ===== */

void FUN_00052816(void)

{
  int extraout_A0;
  undefined2 *extraout_A1;
  int unaff_A5;
  
  *(undefined2 *)(&DAT_000010be + unaff_A5) = *(undefined2 *)(&DAT_00001354 + unaff_A5);
  *(undefined2 *)(&DAT_000010c0 + unaff_A5) = *(undefined2 *)(&DAT_00001356 + unaff_A5);
  FUN_0005283e();
  *(int *)(&DAT_0000135c + unaff_A5) = extraout_A0;
  *(undefined2 *)(&DAT_00001358 + unaff_A5) = *(undefined2 *)(extraout_A0 + 2);
  *(undefined2 *)(&DAT_0000135a + unaff_A5) = *extraout_A1;
  return;
}



/* ===== arcade_pc 0x05283E FUN_0005283e ===== */

int FUN_0005283e(void)

{
  short in_D1w;
  short unaff_D2w;
  int unaff_A5;
  
  return ((uint)((int)(short)((unaff_D2w +
                               ((*(ushort *)(&DAT_000010b0 + unaff_A5) ^ 0x1ff) + 1 & 0x1ff) & 0x1f8
                              ) << 5) +
                (int)(short)(((ushort)(in_D1w + ((*(ushort *)(&DAT_000010ae + unaff_A5) ^ 0x1ff) + 1
                                                & 0x1ff)) >> 1) + 8 & 0xfc)) >> 1) + 0x10de00;
}



/* ===== arcade_pc 0x05288C FUN_0005288c ===== */

void FUN_0005288c(void)

{
  int unaff_A5;
  
  if (*(short *)(&DAT_00001296 + unaff_A5) == 1) {
    DAT_0010d1b2 = 5;
  }
  else {
    DAT_0010d1b2 = 1;
  }
  DAT_0010d1b4 = *(short *)(&DAT_00001356 + unaff_A5) + -8;
  if ((*(ushort *)(&DAT_00001308 + unaff_A5) & 8) == 0) {
    DAT_0010d1b6 = 0;
  }
  else {
    DAT_0010d1b6 = 0x6e1;
  }
  DAT_0010d1b8 = *(short *)(&DAT_00001354 + unaff_A5) + -8;
  return;
}



/* ===== arcade_pc 0x0528CA FUN_000528ca ===== */

void FUN_000528ca(void)

{
  if ((DAT_0010c016 & 2) == 0) {
    FUN_00052938();
  }
  if ((DAT_0010c016 & 1) == 0) {
    FUN_00052924();
  }
  if ((DAT_0010c016 & 4) == 0) {
    FUN_00052960();
  }
  if ((DAT_0010c016 & 8) == 0) {
    FUN_0005294c();
  }
  return;
}



/* ===== arcade_pc 0x05290C FUN_0005290c ===== */

void FUN_0005290c(void)

{
  int unaff_A5;
  
  *(short *)(&DAT_00001356 + unaff_A5) = *(short *)(&DAT_00001356 + unaff_A5) + -2;
  return;
}



/* ===== arcade_pc 0x052912 FUN_00052912 ===== */

void FUN_00052912(void)

{
  int unaff_A5;
  
  *(short *)(&DAT_00001356 + unaff_A5) = *(short *)(&DAT_00001356 + unaff_A5) + 2;
  return;
}



/* ===== arcade_pc 0x052918 FUN_00052918 ===== */

void FUN_00052918(void)

{
  int unaff_A5;
  
  *(short *)(&DAT_00001354 + unaff_A5) = *(short *)(&DAT_00001354 + unaff_A5) + 2;
  return;
}



/* ===== arcade_pc 0x05291E FUN_0005291e ===== */

void FUN_0005291e(void)

{
  int unaff_A5;
  
  *(short *)(&DAT_00001354 + unaff_A5) = *(short *)(&DAT_00001354 + unaff_A5) + -2;
  return;
}



/* ===== arcade_pc 0x052924 FUN_00052924 ===== */

void FUN_00052924(void)

{
  int unaff_A5;
  
  *(ushort *)(&DAT_000010d0 + unaff_A5) = *(ushort *)(&DAT_000010d0 + unaff_A5) | 1;
  *(undefined2 *)(&DAT_000010da + unaff_A5) = 4;
  return;
}



/* ===== arcade_pc 0x052938 FUN_00052938 ===== */

void FUN_00052938(void)

{
  int unaff_A5;
  
  *(ushort *)(&DAT_000010d0 + unaff_A5) = *(ushort *)(&DAT_000010d0 + unaff_A5) | 2;
  *(undefined2 *)(&DAT_000010da + unaff_A5) = 4;
  return;
}



/* ===== arcade_pc 0x05294C FUN_0005294c ===== */

void FUN_0005294c(void)

{
  int unaff_A5;
  
  *(ushort *)(&DAT_000010d0 + unaff_A5) = *(ushort *)(&DAT_000010d0 + unaff_A5) | 8;
  *(undefined2 *)(&DAT_000010d8 + unaff_A5) = 4;
  return;
}



/* ===== arcade_pc 0x052960 FUN_00052960 ===== */

void FUN_00052960(void)

{
  int unaff_A5;
  
  *(ushort *)(&DAT_000010d0 + unaff_A5) = *(ushort *)(&DAT_000010d0 + unaff_A5) | 4;
  *(undefined2 *)(&DAT_000010d8 + unaff_A5) = 4;
  return;
}



/* ===== arcade_pc 0x052974 FUN_00052974 ===== */

void FUN_00052974(void)

{
  short sVar1;
  short sVar2;
  undefined2 *puVar3;
  short *psVar4;
  short *psVar5;
  int *piVar6;
  int *piVar7;
  
  puVar3 = &DAT_00c08000;
  piVar6 = &DAT_0010d420;
  sVar2 = 0x1000;
  do {
    psVar4 = puVar3 + 1;
    puVar3 = puVar3 + 2;
    psVar5 = &DAT_000529aa;
    do {
      sVar1 = *psVar5;
      if (sVar1 == -1) goto LAB_000529a2;
      psVar5 = psVar5 + 1;
    } while (sVar1 != *psVar4);
    piVar7 = piVar6 + 1;
    *piVar6 = (int)sVar1;
    piVar6 = piVar6 + 2;
    *piVar7 = (int)puVar3;
LAB_000529a2:
    sVar2 = sVar2 + -1;
    if (sVar2 == 0) {
      return;
    }
  } while( true );
}



/* ===== arcade_pc 0x0529CC FUN_000529cc ===== */

void FUN_000529cc(void)

{
  int unaff_A5;
  
  if (*(short *)(&DAT_00001296 + unaff_A5) == 0xff) {
    *(undefined2 *)(&DAT_00001296 + unaff_A5) = 1;
    *(undefined2 *)(&DAT_00001298 + unaff_A5) = 0;
  }
  FUN_0003a0ec();
  *(short *)(unaff_A5 + 0x13a) = *(short *)(unaff_A5 + 0x13a) + -0x40;
  *(undefined2 *)(&DAT_000012fc + unaff_A5) = 1;
  (&DAT_00001254)[unaff_A5] = 4;
  (&DAT_00001255)[unaff_A5] = 4;
  (&DAT_00001256)[unaff_A5] = 4;
  (&DAT_00001257)[unaff_A5] = 4;
  *(undefined2 *)(&DAT_000012f8 + unaff_A5) = 1;
  *(undefined2 *)(&DAT_00001310 + unaff_A5) = 8;
  return;
}



/* ===== arcade_pc 0x052AA2 FUN_00052aa2 ===== */

void FUN_00052aa2(void)

{
  short in_D0w;
  short sVar1;
  undefined2 *puVar2;
  undefined2 *puVar3;
  ushort *puVar4;
  int unaff_A5;
  
  puVar3 = &PC090OJ_sprite_RAM_d00000;
  puVar2 = (undefined2 *)(&DAT_0005da5e + (short)(in_D0w * 0x18));
  sVar1 = 4;
  do {
    *puVar3 = puVar2[2];
    puVar3[1] = *(short *)(&DAT_0000129c + unaff_A5) + (short)*(char *)((int)puVar2 + 3) + 1U &
                0x1ff;
    puVar4 = puVar3 + 3;
    puVar3[2] = *puVar2;
    puVar3 = puVar3 + 4;
    *puVar4 = *(short *)(&DAT_0000129a + unaff_A5) + (short)*(char *)(puVar2 + 1) & 0x1ff;
    puVar2 = puVar2 + 3;
    sVar1 = sVar1 + -1;
  } while (sVar1 != 0);
  return;
}



/* ===== arcade_pc 0x0538C8 FUN_000538c8 ===== */

void FUN_000538c8(void)

{
  short unaff_D6w;
  int unaff_A5;
  
  if (8 < *(ushort *)(&DAT_000010c0 + unaff_A5)) {
    *(short *)(&DAT_000010c0 + unaff_A5) = *(short *)(&DAT_000010c0 + unaff_A5) - unaff_D6w;
  }
  return;
}



/* ===== arcade_pc 0x0538D6 FUN_000538d6 ===== */

void FUN_000538d6(void)

{
  undefined2 in_D1w;
  int unaff_A5;
  
  *(ushort *)(&DAT_000010d0 + unaff_A5) = *(ushort *)(&DAT_000010d0 + unaff_A5) | 1;
  *(undefined2 *)(&DAT_000010da + unaff_A5) = in_D1w;
  return;
}



/* ===== arcade_pc 0x053934 FUN_00053934 ===== */

void FUN_00053934(void)

{
  short unaff_D6w;
  int unaff_A5;
  
  if (*(ushort *)(&DAT_000010c0 + unaff_A5) < 0x100) {
    *(short *)(&DAT_000010c0 + unaff_A5) = unaff_D6w + *(short *)(&DAT_000010c0 + unaff_A5);
  }
  return;
}



/* ===== arcade_pc 0x053942 FUN_00053942 ===== */

void FUN_00053942(void)

{
  undefined2 in_D1w;
  int unaff_A5;
  
  *(ushort *)(&DAT_000010d0 + unaff_A5) = *(ushort *)(&DAT_000010d0 + unaff_A5) | 2;
  *(undefined2 *)(&DAT_000010da + unaff_A5) = in_D1w;
  return;
}



/* ===== arcade_pc 0x053A2E FUN_00053a2e ===== */

ushort FUN_00053a2e(void)

{
  short in_D1w;
  short unaff_D2w;
  int unaff_A5;
  
  return (ushort)((unaff_D2w + ((*(ushort *)(&DAT_000010b0 + unaff_A5) ^ 0x1ff) + 1 & 0x1ff) & 0x1f8
                  ) * 0x20 +
                 (((ushort)(in_D1w + ((*(ushort *)(&DAT_000010ae + unaff_A5) ^ 0x1ff) + 1 & 0x1ff))
                  >> 1) + 8 & 0xfc)) >> 1;
}



/* ===== arcade_pc 0x053A6E FUN_00053a6e ===== */

void FUN_00053a6e(void)

{
  ushort *extraout_A0;
  ushort *extraout_A0_00;
  ushort *extraout_A0_01;
  ushort *puVar1;
  int unaff_A5;
  
  *(ushort *)(&DAT_000010ce + unaff_A5) = *(ushort *)(&DAT_000010ce + unaff_A5) & 0xffdd;
  FUN_00053a2e();
  puVar1 = extraout_A0;
  if ((*extraout_A0 & 0x7f) == 2) {
LAB_00053b22:
    *(ushort *)(&DAT_000010ce + unaff_A5) = *(ushort *)(&DAT_000010ce + unaff_A5) | 0x20;
    *(ushort **)(&DAT_0000111c + unaff_A5) = puVar1;
  }
  else {
    if ((*extraout_A0 & 0x7f) != 1) {
      FUN_00053a2e();
      puVar1 = extraout_A0_00;
      if ((*extraout_A0_00 & 0x7f) == 2) goto LAB_00053b22;
      if ((*extraout_A0_00 & 0x7f) != 1) {
        FUN_00053a2e();
        puVar1 = extraout_A0_01;
        if ((*extraout_A0_01 & 0x7f) == 2) goto LAB_00053b22;
        if ((*extraout_A0_01 & 0x7f) != 1) {
          return;
        }
      }
    }
    *(ushort *)(&DAT_000010ce + unaff_A5) = *(ushort *)(&DAT_000010ce + unaff_A5) | 2;
  }
  return;
}



/* ===== arcade_pc 0x053B34 FUN_00053b34 ===== */

void FUN_00053b34(void)

{
  ushort *extraout_A0;
  ushort *extraout_A0_00;
  ushort *extraout_A0_01;
  ushort *extraout_A0_02;
  ushort *extraout_A0_03;
  ushort *extraout_A0_04;
  ushort *extraout_A0_05;
  ushort *extraout_A0_06;
  ushort *extraout_A0_07;
  ushort *extraout_A0_08;
  ushort *extraout_A0_09;
  ushort *extraout_A0_10;
  ushort *extraout_A0_11;
  ushort *extraout_A0_12;
  ushort *extraout_A0_13;
  ushort *extraout_A0_14;
  ushort *extraout_A0_15;
  ushort *extraout_A0_16;
  ushort *puVar1;
  int unaff_A5;
  
  *(undefined2 *)(&DAT_000013d4 + unaff_A5) = 0xff;
  *(ushort *)(&DAT_000010ce + unaff_A5) = *(ushort *)(&DAT_000010ce + unaff_A5) & 0xfc3b;
  *(undefined2 *)(&DAT_00001132 + unaff_A5) = 0;
  FUN_00053a2e();
  puVar1 = extraout_A0;
  if ((*extraout_A0 & 0x7f) == 1) {
    FUN_00053dc8();
    *(ushort *)(&DAT_00001132 + unaff_A5) = *(ushort *)(&DAT_00001132 + unaff_A5) | 0x10;
    puVar1 = extraout_A0_00;
  }
  if ((*puVar1 & 0x7f) == 3) {
    FUN_00053dc8();
    *(undefined2 *)(&DAT_000013d4 + unaff_A5) = 1;
    *(ushort *)(&DAT_00001132 + unaff_A5) = *(ushort *)(&DAT_00001132 + unaff_A5) | 0x10;
    puVar1 = extraout_A0_01;
  }
  if ((*puVar1 & 0x7f) == 4) {
    FUN_00053dd6();
    *(ushort *)(&DAT_00001132 + unaff_A5) = *(ushort *)(&DAT_00001132 + unaff_A5) | 0x10;
    puVar1 = extraout_A0_02;
  }
  if ((*puVar1 & 0x7f) == 7) {
    FUN_00053de4();
    FUN_00053dc8();
    *(ushort *)(&DAT_00001132 + unaff_A5) = *(ushort *)(&DAT_00001132 + unaff_A5) | 0x10;
    puVar1 = extraout_A0_03;
  }
  if ((*puVar1 & 0x7f) == 6) {
    FUN_00053df2();
    puVar1 = extraout_A0_04;
  }
  if ((*puVar1 & 0x7f) == 8) {
    FUN_00053e00();
    return;
  }
  if ((*puVar1 & 0x7f) != 0x7e) {
    FUN_00053a2e();
    puVar1 = extraout_A0_05;
    if ((*extraout_A0_05 & 0x7f) == 1) {
      FUN_00053dc8();
      *(ushort *)(&DAT_00001132 + unaff_A5) = *(ushort *)(&DAT_00001132 + unaff_A5) | 4;
      puVar1 = extraout_A0_06;
    }
    if ((*puVar1 & 0x7f) == 3) {
      FUN_00053dc8();
      *(undefined2 *)(&DAT_000013d4 + unaff_A5) = 1;
      *(ushort *)(&DAT_00001132 + unaff_A5) = *(ushort *)(&DAT_00001132 + unaff_A5) | 4;
      puVar1 = extraout_A0_07;
    }
    if ((*puVar1 & 0x7f) == 4) {
      FUN_00053dd6();
      *(ushort *)(&DAT_00001132 + unaff_A5) = *(ushort *)(&DAT_00001132 + unaff_A5) | 4;
      puVar1 = extraout_A0_08;
    }
    if ((*puVar1 & 0x7f) == 7) {
      FUN_00053de4();
      FUN_00053dc8();
      *(ushort *)(&DAT_00001132 + unaff_A5) = *(ushort *)(&DAT_00001132 + unaff_A5) | 4;
      puVar1 = extraout_A0_09;
    }
    if ((*puVar1 & 0x7f) == 6) {
      FUN_00053df2();
      puVar1 = extraout_A0_10;
    }
    if ((*puVar1 & 0x7f) == 8) {
      FUN_00053e00();
      return;
    }
    if ((*puVar1 & 0x7f) != 0x7e) {
      FUN_00053a2e();
      puVar1 = extraout_A0_11;
      if ((*extraout_A0_11 & 0x7f) == 1) {
        FUN_00053dc8();
        *(ushort *)(&DAT_00001132 + unaff_A5) = *(ushort *)(&DAT_00001132 + unaff_A5) | 8;
        puVar1 = extraout_A0_12;
      }
      if ((*puVar1 & 0x7f) == 3) {
        FUN_00053dc8();
        *(undefined2 *)(&DAT_000013d4 + unaff_A5) = 1;
        *(ushort *)(&DAT_00001132 + unaff_A5) = *(ushort *)(&DAT_00001132 + unaff_A5) | 8;
        puVar1 = extraout_A0_13;
      }
      if ((*puVar1 & 0x7f) == 4) {
        FUN_00053dd6();
        *(ushort *)(&DAT_00001132 + unaff_A5) = *(ushort *)(&DAT_00001132 + unaff_A5) | 8;
        puVar1 = extraout_A0_14;
      }
      if ((*puVar1 & 0x7f) == 7) {
        FUN_00053de4();
        FUN_00053dc8();
        *(ushort *)(&DAT_00001132 + unaff_A5) = *(ushort *)(&DAT_00001132 + unaff_A5) | 8;
        puVar1 = extraout_A0_15;
      }
      if ((*puVar1 & 0x7f) == 6) {
        FUN_00053df2();
        puVar1 = extraout_A0_16;
      }
      if ((*puVar1 & 0x7f) == 8) {
        FUN_00053e00();
        return;
      }
      if ((*puVar1 & 0x7f) != 0x7e) {
        return;
      }
    }
  }
  *(ushort *)(&DAT_000010ce + unaff_A5) = *(ushort *)(&DAT_000010ce + unaff_A5) | 0x80;
  return;
}



/* ===== arcade_pc 0x053DC8 FUN_00053dc8 ===== */

void FUN_00053dc8(void)

{
  int unaff_A5;
  
  *(ushort *)(&DAT_000010ce + unaff_A5) = *(ushort *)(&DAT_000010ce + unaff_A5) | 4;
  return;
}



/* ===== arcade_pc 0x053DD6 FUN_00053dd6 ===== */

void FUN_00053dd6(void)

{
  int unaff_A5;
  
  *(ushort *)(&DAT_000010ce + unaff_A5) = *(ushort *)(&DAT_000010ce + unaff_A5) | 0x40;
  return;
}



/* ===== arcade_pc 0x053DE4 FUN_00053de4 ===== */

void FUN_00053de4(void)

{
  int unaff_A5;
  
  *(ushort *)(&DAT_000010ce + unaff_A5) = *(ushort *)(&DAT_000010ce + unaff_A5) | 0x100;
  return;
}



/* ===== arcade_pc 0x053DF2 FUN_00053df2 ===== */

void FUN_00053df2(void)

{
  int unaff_A5;
  
  *(ushort *)(&DAT_000010ce + unaff_A5) = *(ushort *)(&DAT_000010ce + unaff_A5) | 0x200;
  return;
}



/* ===== arcade_pc 0x053E00 FUN_00053e00 ===== */

void FUN_00053e00(void)

{
  int unaff_A5;
  
  *(ushort *)(&DAT_000010ce + unaff_A5) = *(ushort *)(&DAT_000010ce + unaff_A5) | 0x200;
  *(undefined2 *)(&DAT_000010e8 + unaff_A5) = 8;
  return;
}



/* ===== arcade_pc 0x0555B8 FUN_000555b8 ===== */

void FUN_000555b8(void)

{
  ushort unaff_D2w;
  int unaff_A5;
  
  FUN_0003a0ec();
  if (*(short *)(&DAT_00001108 + unaff_A5) == 1) {
    *(undefined2 *)(&DAT_00001366 + unaff_A5) = 1;
    *(undefined2 *)(&DAT_00001368 + unaff_A5) = 0;
    FUN_00055642();
  }
  else {
    *(undefined2 *)(&DAT_000012f0 + unaff_A5) = 1;
    *(undefined2 *)(&DAT_000012f2 + unaff_A5) = 0;
    if (*(short *)(&DAT_000010e8 + unaff_A5) == 4) {
      *(undefined2 *)(&DAT_000012f6 + unaff_A5) = 0xff;
    }
    else if (unaff_D2w < *(ushort *)(&DAT_000010be + unaff_A5)) {
      *(undefined2 *)(&DAT_000012f6 + unaff_A5) = 3;
    }
    else {
      *(undefined2 *)(&DAT_000012f6 + unaff_A5) = 2;
    }
  }
  return;
}



/* ===== arcade_pc 0x05560C FUN_0005560c ===== */

void FUN_0005560c(void)

{
  int unaff_A5;
  
  FUN_0003a0ec();
  if (*(short *)(&DAT_00001108 + unaff_A5) == 1) {
    *(undefined2 *)(&DAT_00001366 + unaff_A5) = 1;
    *(undefined2 *)(&DAT_00001368 + unaff_A5) = 0;
    FUN_00055642();
  }
  else {
    *(undefined2 *)(&DAT_000012f0 + unaff_A5) = 1;
    *(undefined2 *)(&DAT_000012f2 + unaff_A5) = 0xc;
    *(undefined2 *)(&DAT_000012f6 + unaff_A5) = 0xff;
  }
  return;
}



/* ===== arcade_pc 0x055642 FUN_00055642 ===== */

void FUN_00055642(void)

{
  int unaff_A5;
  
  *(undefined2 *)(&DAT_0000130e + unaff_A5) = 1;
  *(undefined2 *)(&DAT_0000130c + unaff_A5) = 0x10;
  return;
}



/* ===== arcade_pc 0x055AB4 FUN_00055ab4 ===== */

void FUN_00055ab4(void)

{
  int unaff_A5;
  
  Ram00c20000 = *(undefined2 *)(&DAT_000010ee + unaff_A5);
  Ram00c40000 = *(undefined2 *)(&DAT_000010ec + unaff_A5);
  DAT_00c20002 = *(undefined2 *)(&DAT_000010b0 + unaff_A5);
  DAT_00c40002 = *(undefined2 *)(&DAT_000010ae + unaff_A5);
  return;
}



/* ===== arcade_pc 0x055CA2 FUN_00055ca2 ===== */

void FUN_00055ca2(void)

{
  int unaff_A5;
  
  if (*(short *)(unaff_A5 + 0x4a) != 0) {
    if (*(short *)(unaff_A5 + 0x4a) == 0xaa) {
      if (*(short *)(&DAT_000013cc + unaff_A5) != 0x3c) {
        *(short *)(&DAT_000013cc + unaff_A5) = *(short *)(&DAT_000013cc + unaff_A5) + 1;
        return;
      }
      DAT_0010ffff = 0xaa;
      *(undefined2 *)(unaff_A5 + 0x4a) = 0;
    }
    else if (*(short *)(unaff_A5 + 0x4a) == 1) {
      DAT_0010ffff = 1;
      *(undefined2 *)(unaff_A5 + 0x4a) = 0;
    }
    else if (*(short *)(unaff_A5 + 0x4a) == 2) {
      DAT_0010ffff = 2;
      *(undefined2 *)(unaff_A5 + 0x4a) = 0;
    }
    else if (*(short *)(unaff_A5 + 0x4a) == 3) {
      DAT_0010ffff = 3;
      *(undefined2 *)(unaff_A5 + 0x4a) = 0;
    }
    else {
      if (*(short *)(unaff_A5 + 0x4a) == 0xe) {
        DAT_0010ffff = 0xe;
        *(undefined2 *)(unaff_A5 + 0x4a) = 0x20;
        return;
      }
      if (*(short *)(unaff_A5 + 0x4a) == 0xf) {
        DAT_0010ffff = 0xf;
        *(undefined2 *)(unaff_A5 + 0x4a) = 0x20;
        return;
      }
      if (*(short *)(unaff_A5 + 0x4a) == 0x12) {
        DAT_0010ffff = 0x12;
        *(undefined2 *)(unaff_A5 + 0x4a) = 0;
      }
      else if (*(short *)(unaff_A5 + 0x4a) == 0x13) {
        DAT_0010ffff = 0x13;
        *(undefined2 *)(unaff_A5 + 0x4a) = 0;
      }
      else if (*(short *)(unaff_A5 + 0x4a) == 0x1f) {
        DAT_0010ffff = 0x1f;
        *(undefined2 *)(unaff_A5 + 0x4a) = 0;
      }
      else if (*(short *)(unaff_A5 + 0x4a) == 0x20) {
        if (*(short *)(&DAT_000013cc + unaff_A5) != 5) {
          DAT_0010ffff = (&DAT_0010c04c)[*(short *)(&DAT_000013cc + unaff_A5)];
          *(short *)(&DAT_000013cc + unaff_A5) = *(short *)(&DAT_000013cc + unaff_A5) + 1;
          return;
        }
        *(undefined2 *)(unaff_A5 + 0x4a) = 0;
      }
    }
  }
  *(undefined2 *)(&DAT_000013cc + unaff_A5) = 0;
  return;
}



/* ===== arcade_pc 0x0565A6 shared_pc080sn_text_writer_565a6 ===== */

/* WARNING: Control flow encountered bad instruction data */

void shared_pc080sn_text_writer_565a6(void)

{
  int in_A0;
  short *unaff_A5;
  
  *(char *)(in_A0 + -1) = -*(char *)(in_A0 + -1);
  *unaff_A5 = *unaff_A5 + -1;
                    /* WARNING: Bad instruction - Truncating control flow here */
  halt_baddata();
}



/* ===== arcade_pc 0x05743C FUN_0005743c ===== */

undefined2 FUN_0005743c(void)

{
  int unaff_A2;
  
  return *(undefined2 *)(unaff_A2 + 8);
}



/* ===== arcade_pc 0x05744E FUN_0005744e ===== */

void FUN_0005744e(void)

{
  int unaff_A5;
  
  *(undefined2 *)(&DAT_000010ec + unaff_A5) = 0x160;
  FUN_00055ab4();
  FUN_0005743c();
  FUN_0005a4de();
  FUN_0005743c();
  FUN_0005a4de();
  FUN_0005743c();
  FUN_0005a4de();
  FUN_0005743c();
  FUN_0005a4de();
  return;
}



/* ===== arcade_pc 0x0574A4 FUN_000574a4 ===== */

void FUN_000574a4(void)

{
  FUN_0005743c();
  FUN_0005a4de();
  return;
}



/* ===== arcade_pc 0x059882 FUN_00059882 ===== */

void FUN_00059882(void)

{
  FUN_00059962();
  FUN_000599b2();
  return;
}



/* ===== arcade_pc 0x05988C FUN_0005988c ===== */

void FUN_0005988c(void)

{
  int unaff_A5;
  
  if (*(short *)(&DAT_0000136a + unaff_A5) != 0) {
    if (*(short *)(&DAT_00001366 + unaff_A5) != 1) {
      return;
    }
    if (*(short *)(&DAT_00001368 + unaff_A5) == 0) {
      FUN_00059ad4();
      goto LAB_000598f6;
    }
    if (*(short *)(&DAT_00001368 + unaff_A5) != 0x10) goto LAB_000598f6;
  }
  FUN_00059ad4();
LAB_000598f6:
  if (*(short *)(&DAT_00001368 + unaff_A5) == 0x50) {
    *(undefined2 *)(&DAT_00001368 + unaff_A5) = 0;
    *(undefined2 *)(&DAT_00001366 + unaff_A5) = 0xff;
  }
  else {
    *(short *)(&DAT_00001368 + unaff_A5) = *(short *)(&DAT_00001368 + unaff_A5) + 1;
  }
  return;
}



/* ===== arcade_pc 0x059962 FUN_00059962 ===== */

void FUN_00059962(void)

{
  int unaff_A5;
  
  if (*(short *)(&DAT_000012ee + unaff_A5) == 8) {
    if ((*(ushort *)(&DAT_000012e8 + unaff_A5) & 7) == 0) {
      FUN_00059ad4();
    }
    if (*(short *)(&DAT_000012e8 + unaff_A5) == 0x17) {
      *(undefined2 *)(&DAT_000012e8 + unaff_A5) = 0;
    }
    else {
      *(short *)(&DAT_000012e8 + unaff_A5) = *(short *)(&DAT_000012e8 + unaff_A5) + 1;
    }
  }
  return;
}



/* ===== arcade_pc 0x0599B2 FUN_000599b2 ===== */

void FUN_000599b2(void)

{
  int unaff_A5;
  
  if (*(short *)(&DAT_000012ee + unaff_A5) == 9) {
    if ((*(ushort *)(&DAT_000012ea + unaff_A5) & 7) == 0) {
      FUN_00059ad4();
      FUN_00059ad4();
      FUN_00059ad4();
      FUN_00059ad4();
    }
    if (*(short *)(&DAT_000012ea + unaff_A5) == 0x1f) {
      *(undefined2 *)(&DAT_000012ea + unaff_A5) = 0;
    }
    else {
      *(short *)(&DAT_000012ea + unaff_A5) = *(short *)(&DAT_000012ea + unaff_A5) + 1;
    }
  }
  return;
}



/* ===== arcade_pc 0x059AD4 FUN_00059ad4 ===== */

void FUN_00059ad4(void)

{
  ushort uVar1;
  short in_D0w;
  short in_D1w;
  short sVar2;
  int in_A0;
  ushort *puVar3;
  short *psVar4;
  
  sVar2 = 0;
  psVar4 = (short *)((short)(in_D0w << 5) + 0x200000);
  puVar3 = (ushort *)((short)(in_D1w * 0x20) + in_A0);
  while( true ) {
    uVar1 = *puVar3;
    if (uVar1 != 0xffff) {
      *psVar4 = (uVar1 & 0xf0) * 4 + ((uVar1 & 0xf00) >> 7) + (uVar1 & 0xf) * 0x800;
    }
    if (sVar2 == 0xf) break;
    sVar2 = sVar2 + 1;
    psVar4 = psVar4 + 1;
    puVar3 = puVar3 + 1;
  }
  return;
}



/* ===== arcade_pc 0x05A4DE FUN_0005a4de ===== */

void FUN_0005a4de(void)

{
  short in_D0w;
  short sVar1;
  short in_D1w;
  undefined2 unaff_D2w;
  undefined2 *in_A0;
  undefined2 *puVar2;
  undefined2 *in_A1;
  undefined2 *puVar3;
  undefined2 *puVar4;
  
  sVar1 = in_D0w;
  puVar4 = in_A1;
  do {
    do {
      puVar3 = in_A1 + 1;
      *in_A1 = unaff_D2w;
      puVar2 = in_A0 + 1;
      in_A1 = in_A1 + 2;
      *puVar3 = *in_A0;
      sVar1 = sVar1 + -1;
      in_A0 = puVar2;
    } while (sVar1 != 0);
    in_A1 = puVar4 + 0x80;
    in_D1w = in_D1w + -1;
    sVar1 = in_D0w;
    puVar4 = in_A1;
  } while (in_D1w != 0);
  return;
}



/* ===== arcade_pc 0x05B512 FUN_0005b512 ===== */

void FUN_0005b512(void)

{
  return;
}



/* ===== arcade_pc 0x05FFA2 FUN_0005ffa2 ===== */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_0005ffa2(void)

{
  undefined2 in_D0w;
  undefined2 *in_A0;
  undefined *puVar1;
  
  if (_DAT_0005fffe == 0) {
    puVar1 = &DAT_0005ffce;
  }
  else {
    puVar1 = &DAT_0005ffde;
  }
  *in_A0 = *(undefined2 *)(puVar1 + CONCAT11((char)((ushort)in_D0w >> 8),(byte)in_D0w >> 2));
  in_A0[1] = *(undefined2 *)
              ((int)(puVar1 + CONCAT11((char)((ushort)in_D0w >> 8),(byte)in_D0w >> 2)) + 2);
  return;
}



/* ===== arcade_pc 0x05FFB2 FUN_0005ffb2 ===== */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_0005ffb2(void)

{
  undefined2 in_D0w;
  undefined2 *in_A0;
  undefined *puVar1;
  
  if (_DAT_0005fffe == 0) {
    puVar1 = &DAT_0005ffce;
  }
  else {
    puVar1 = &DAT_0005ffee;
  }
  *in_A0 = *(undefined2 *)(puVar1 + CONCAT11((char)((ushort)in_D0w >> 8),(byte)in_D0w >> 4));
  in_A0[1] = *(undefined2 *)
              ((int)(puVar1 + CONCAT11((char)((ushort)in_D0w >> 8),(byte)in_D0w >> 4)) + 2);
  return;
}


