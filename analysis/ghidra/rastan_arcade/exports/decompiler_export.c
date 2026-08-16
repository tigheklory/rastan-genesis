
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



/* ===== arcade_pc 0x03A116 FUN_0003a116 ===== */

void FUN_0003a116(void)

{
  undefined1 in_D0b;
  int unaff_A5;
  
  if (*(short *)(unaff_A5 + 0x34) != 0) {
    *(undefined1 *)(unaff_A5 + 0x292) = in_D0b;
    *(undefined4 *)(unaff_A5 + 0x294) = 0;
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



/* ===== arcade_pc 0x03A196 frontend_state_dispatch_3a196 ===== */

void frontend_state_dispatch_3a196(void)

{
  int unaff_A5;
  
                    /* WARNING: Could not recover jumptable at 0x0003a1aa. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(&frontend_state_dispatch_offsets_3a1ac +
            *(short *)(&frontend_state_dispatch_offsets_3a1ac +
                      (short)(*(short *)(unaff_A5 + 4) * 2))))();
  return;
}



/* ===== arcade_pc 0x03A1C4 frontend_state0_init_3a1c4 ===== */

void frontend_state0_init_3a1c4(void)

{
  ushort uVar1;
  int unaff_A5;
  
  FUN_0003f084();
  *(ushort *)(unaff_A5 + 0x14) = *(ushort *)(unaff_A5 + 0x14) & 0xf;
  uVar1 = *(ushort *)(unaff_A5 + 0x14) | 0x60;
  Ram00380000 = uVar1;
  *(ushort *)(unaff_A5 + 0x14) = uVar1;
  *(undefined2 *)(unaff_A5 + 0x46) = 0;
  *(undefined2 *)(unaff_A5 + 0x292) = 0;
  *(undefined2 *)(unaff_A5 + 0x294) = 0;
  *(undefined2 *)(unaff_A5 + 0x296) = 0;
  *(undefined1 *)(unaff_A5 + 0x104) = 1;
  *(undefined2 *)(unaff_A5 + 4) = 1;
  return;
}



/* ===== arcade_pc 0x03A200 frontend_state1_update_3a200 ===== */

void frontend_state1_update_3a200(void)

{
  short sVar1;
  undefined2 uVar2;
  int unaff_A5;
  
  sVar1 = *(short *)(unaff_A5 + 0x100) + -1;
  *(short *)(unaff_A5 + 0x100) = sVar1;
  if (sVar1 == 0) {
    *(undefined2 *)(unaff_A5 + 4) = 2;
    FUN_0003b902();
    if (*(short *)(unaff_A5 + 0x34) != 0) {
      uVar2 = 0xe;
      if ((*(short *)(unaff_A5 + 0x28) != 0) && (*(short *)(unaff_A5 + 0x2a) != 0)) {
        uVar2 = 0xf;
      }
      *(undefined2 *)(unaff_A5 + 0x4a) = uVar2;
      FUN_0003a37c();
      FUN_0003f084();
    }
    return;
  }
  FUN_0003ae5a();
  FUN_0003ad4c();
  FUN_0003add8();
  if (*(short *)(unaff_A5 + 0x28) != 0) {
    FUN_0003f084();
    FUN_0003b902();
    if (*(short *)(unaff_A5 + 0x2a) == 0) {
      if ((*(byte *)(unaff_A5 + 0x3b) & 2) == 0) {
        FUN_0003a294();
        *(undefined2 *)(unaff_A5 + 0x2a) = 1;
      }
    }
    else if ((*(byte *)(unaff_A5 + 0x3b) & 1) == 0) {
      FUN_0003a2b2();
      *(undefined2 *)(unaff_A5 + 0x2a) = 0;
    }
  }
  *(undefined2 *)(unaff_A5 + 2) = 0;
  *(undefined2 *)(unaff_A5 + 4) = 0;
  return;
}



/* ===== arcade_pc 0x03A294 FUN_0003a294 ===== */

void FUN_0003a294(void)

{
  FUN_0003a2d0();
  FUN_0003a2d0();
  return;
}



/* ===== arcade_pc 0x03A2B2 FUN_0003a2b2 ===== */

void FUN_0003a2b2(void)

{
  FUN_0003a2d0();
  FUN_0003a2d0();
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



/* ===== arcade_pc 0x03A2D8 frontend_state2_update_3a2d8 ===== */

void frontend_state2_update_3a2d8(void)

{
  undefined2 *unaff_A5;
  
  FUN_0003ae5a();
  FUN_0003ad4c();
  FUN_0003add8();
  if (unaff_A5[0x1a] == 0) {
    *unaff_A5 = 0;
    unaff_A5[1] = 0;
    unaff_A5[2] = 0;
    return;
  }
  unaff_A5[0x21] = 0;
  unaff_A5[2] = 9;
  return;
}



/* ===== arcade_pc 0x03A304 frontend_state3_update_3a304 ===== */

void frontend_state3_update_3a304(void)

{
  int unaff_A5;
  
  if (((*(byte *)(unaff_A5 + 0x1d) & 0x40) == 0) && (*(byte *)(unaff_A5 + 0x118) < 6)) {
    Ram002005c2 = 0x3ff;
    Ram002005e2 = 0x1f;
    FUN_0005a3ac();
    FUN_0003bb48();
    FUN_0003bb48();
    FUN_0003bb48();
    FUN_0003bb48();
    if (*(short *)(unaff_A5 + 0x2a) != 0) {
      Ram00c08a52 = 0x32;
    }
    if (*(short *)(unaff_A5 + 0x12) == 0) {
      FUN_0003bb48();
    }
    *(undefined2 *)(unaff_A5 + 0x202) = 0;
    FUN_0003d044();
    *(undefined2 *)(unaff_A5 + 0x204) = 0x60;
    *(undefined2 *)(unaff_A5 + 4) = 8;
    return;
  }
  *(undefined2 *)(unaff_A5 + 4) = 4;
  return;
}



/* ===== arcade_pc 0x03A37C FUN_0003a37c ===== */

void FUN_0003a37c(void)

{
  int unaff_A5;
  
  *(undefined1 *)(unaff_A5 + 0x4c) = *(undefined1 *)(unaff_A5 + 0x11e);
  *(undefined1 *)(unaff_A5 + 0x4d) = *(undefined1 *)(unaff_A5 + 0x11d);
  *(undefined1 *)(unaff_A5 + 0x4e) = *(undefined1 *)(unaff_A5 + 0x11c);
  *(undefined1 *)(unaff_A5 + 0x4f) = 0;
  *(undefined1 *)(unaff_A5 + 0x50) = *(undefined1 *)(unaff_A5 + 0x13f);
  return;
}



/* ===== arcade_pc 0x03A39A frontend_state4_update_3a39a ===== */

void frontend_state4_update_3a39a(void)

{
  int unaff_A5;
  
  if (*(short *)(unaff_A5 + 0x28) == 0) {
    FUN_0005a442();
    FUN_0003bb48();
    FUN_0003bb48();
    *(undefined2 *)(unaff_A5 + 0x2a) = 0;
    FUN_0003add8();
    *(undefined2 *)(unaff_A5 + 0x2c) = 0xa0;
    *(undefined2 *)(unaff_A5 + 0x3a) = 0;
    *(undefined2 *)(unaff_A5 + 4) = 6;
    return;
  }
  FUN_0005a442();
  if (*(short *)(unaff_A5 + 0x2a) == 0) {
    FUN_0003bb48();
    FUN_0003bb48();
    *(ushort *)(unaff_A5 + 0x3a) = *(ushort *)(unaff_A5 + 0x3a) | 1;
  }
  else {
    FUN_0003bb48();
    FUN_0003bb48();
    *(ushort *)(unaff_A5 + 0x3a) = *(ushort *)(unaff_A5 + 0x3a) | 2;
  }
  *(undefined2 *)(unaff_A5 + 0x2c) = 0xa0;
  if (*(short *)(unaff_A5 + 0x3a) == 3) {
    *(undefined2 *)(unaff_A5 + 4) = 5;
    return;
  }
  if (*(short *)(unaff_A5 + 0x2a) == 0) {
    if ((*(byte *)(unaff_A5 + 0x3b) & 2) != 0) {
LAB_0003a250:
      *(undefined2 *)(unaff_A5 + 2) = 0;
      *(undefined2 *)(unaff_A5 + 4) = 0;
      return;
    }
    FUN_0003a294();
    *(undefined2 *)(unaff_A5 + 0x2a) = 1;
  }
  else {
    if ((*(byte *)(unaff_A5 + 0x3b) & 1) != 0) goto LAB_0003a250;
    FUN_0003a2b2();
    *(undefined2 *)(unaff_A5 + 0x2a) = 0;
  }
  *(undefined2 *)(unaff_A5 + 4) = 7;
  return;
}



/* ===== arcade_pc 0x03A420 frontend_state5_update_3a420 ===== */

void frontend_state5_update_3a420(void)

{
  int unaff_A5;
  
  FUN_0005a442();
  FUN_0003bb48();
  FUN_0003bb48();
  *(undefined2 *)(unaff_A5 + 0x2a) = 0;
  FUN_0003add8();
  *(undefined2 *)(unaff_A5 + 0x2c) = 0xa0;
  *(undefined2 *)(unaff_A5 + 0x3a) = 0;
  *(undefined2 *)(unaff_A5 + 4) = 6;
  return;
}



/* ===== arcade_pc 0x03A450 frontend_state6_update_3a450 ===== */

void frontend_state6_update_3a450(void)

{
  undefined2 *unaff_A5;
  
  *unaff_A5 = 0;
  if (unaff_A5[9] != 0) {
    *unaff_A5 = 1;
  }
  unaff_A5[0x1a] = 0;
  unaff_A5[0x14] = 0;
  unaff_A5[0x15] = 0;
  FUN_0003add8();
  unaff_A5[1] = 0;
  unaff_A5[2] = 0;
  return;
}



/* ===== arcade_pc 0x03A474 frontend_state7_update_3a474 ===== */

void frontend_state7_update_3a474(void)

{
  int unaff_A5;
  
  *(undefined2 *)(unaff_A5 + 2) = 0;
  *(undefined2 *)(unaff_A5 + 4) = 0;
  return;
}



/* ===== arcade_pc 0x03A478 frontend_state8_update_3a478 ===== */

void frontend_state8_update_3a478(void)

{
  short sVar1;
  byte bVar2;
  byte bVar4;
  undefined2 uVar3;
  undefined2 uVar5;
  undefined2 extraout_D1u;
  undefined4 in_D1;
  byte bVar7;
  uint uVar6;
  int unaff_A5;
  undefined1 uVar8;
  
  uVar5 = (undefined2)((uint)in_D1 >> 0x10);
  if ((*(short *)(unaff_A5 + 0x12) != 0) && (sVar1 = DAT_00c0883a, sVar1 == 0x49)) {
    FUN_0003bb48();
    uVar5 = extraout_D1u;
  }
  bVar2 = DAT_00390007;
  if ((bVar2 & 0x18) == 0x18) {
    bVar2 = DAT_00390001;
    bVar7 = DAT_00390003;
    bVar4 = bVar2;
    if ((*(byte *)(unaff_A5 + 0x1f) & 1) != 0) {
      bVar4 = bVar7;
      bVar7 = bVar2;
    }
    if (*(short *)(unaff_A5 + 0x32) != 0) {
      bVar4 = bVar7;
    }
    if ((bVar4 & 0x30) != 0x30) goto LAB_0003a4f2;
  }
  else if (*(short *)(unaff_A5 + 0x12) != 0) {
    uVar3 = 0x12;
    if ((*(short *)(unaff_A5 + 0x28) != 0) && (*(short *)(unaff_A5 + 0x2a) != 0)) {
      uVar3 = 0x13;
    }
    *(undefined2 *)(unaff_A5 + 0x4a) = uVar3;
    *(undefined2 *)(unaff_A5 + 0x100) = *(undefined2 *)(unaff_A5 + 0x36);
    uVar8 = bcdAdjust((char)*(undefined2 *)(unaff_A5 + 0x12) + -1);
    uVar6 = CONCAT31((int3)(CONCAT22(uVar5,*(undefined2 *)(unaff_A5 + 0x12)) >> 8),uVar8);
    *(short *)(unaff_A5 + 0x12) = (short)uVar6;
    if (uVar6 < 9) {
      FUN_0003ae28();
    }
    FUN_0003c2e2();
    FUN_0003a552();
    if (*(short *)(unaff_A5 + 0x28) != 0) {
      FUN_0003f084();
      FUN_0003b902();
      if (*(short *)(unaff_A5 + 0x2a) == 0) {
        if ((*(byte *)(unaff_A5 + 0x3b) & 2) == 0) {
          FUN_0003a294();
          *(undefined2 *)(unaff_A5 + 0x2a) = 1;
        }
      }
      else if ((*(byte *)(unaff_A5 + 0x3b) & 1) == 0) {
        FUN_0003a2b2();
        *(undefined2 *)(unaff_A5 + 0x2a) = 0;
      }
    }
    *(undefined2 *)(unaff_A5 + 2) = 0;
    *(undefined2 *)(unaff_A5 + 4) = 0;
    return;
  }
  sVar1 = *(short *)(unaff_A5 + 0x204) + -1;
  *(short *)(unaff_A5 + 0x204) = sVar1;
  if (sVar1 != 0) {
    return;
  }
  *(undefined2 *)(unaff_A5 + 0x204) = 0x60;
  if (*(ushort *)(unaff_A5 + 0x202) < 9) {
    *(short *)(unaff_A5 + 0x202) = *(short *)(unaff_A5 + 0x202) + 1;
    FUN_0003d044();
    return;
  }
LAB_0003a4f2:
  if (*(short *)(unaff_A5 + 0x202) != 0) {
    FUN_0003ae5a();
    *(undefined2 *)(unaff_A5 + 4) = 4;
  }
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



/* ===== arcade_pc 0x03AD4C FUN_0003ad4c ===== */

void FUN_0003ad4c(void)

{
  FUN_0003ad44();
  FUN_0003ad44();
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



/* ===== arcade_pc 0x03AE5A FUN_0003ae5a ===== */

void FUN_0003ae5a(void)

{
  FUN_0003ae64();
  FUN_0003b098();
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



/* ===== arcade_pc 0x03B726 FUN_0003b726 ===== */

void FUN_0003b726(void)

{
  undefined2 in_D0w;
  short sVar1;
  byte *pbVar2;
  int iVar3;
  int iVar4;
  int unaff_A5;
  bool bVar5;
  bool bVar6;
  
  if (*(short *)(unaff_A5 + 0x34) != 0) {
    *(char *)(unaff_A5 + 0x119) = (char)in_D0w;
    *(char *)(unaff_A5 + 0x11a) = (char)((ushort)in_D0w >> 8);
    iVar4 = unaff_A5 + 0x11a;
    iVar3 = unaff_A5 + 0x11d;
    sVar1 = 2;
    bVar5 = false;
    do {
      pbVar2 = (byte *)(iVar3 + -1);
      bVar6 = CARRY1(*pbVar2,CARRY1(*(byte *)(iVar4 + -1),bVar5));
      *pbVar2 = *pbVar2 + *(byte *)(iVar4 + -1) + bVar5;
      bcdAdjust(*pbVar2);
      iVar3 = iVar3 + 1;
      iVar4 = iVar4 + 1;
      sVar1 = sVar1 + -1;
      bVar5 = bVar6;
    } while (sVar1 != -1);
    if (bVar6) {
      *(undefined1 *)(unaff_A5 + 0x11c) = 0x99;
      *(undefined1 *)(unaff_A5 + 0x11d) = 0x99;
      *(undefined1 *)(unaff_A5 + 0x11e) = 0x99;
    }
    else if ((*(byte *)(unaff_A5 + 0x133) <= *(byte *)(unaff_A5 + 0x11e)) &&
            (((*(byte *)(unaff_A5 + 0x133) < *(byte *)(unaff_A5 + 0x11e) ||
              (*(byte *)(unaff_A5 + 0x132) <= *(byte *)(unaff_A5 + 0x11d))) &&
             (*(short *)(unaff_A5 + 0x132) != -0x6667)))) {
      FUN_00059ee0();
      FUN_0003a0ec();
      *(short *)(unaff_A5 + 0x100) = *(short *)(unaff_A5 + 0x100) + 1;
      *(short *)(unaff_A5 + 0x102) = *(short *)(unaff_A5 + 0x102) + 1;
      pc090oj_sprite_producer_3b802();
    }
    pc090oj_sprite_producer_3b802();
    FUN_0003b7c0();
    return;
  }
  return;
}



/* ===== arcade_pc 0x03B7C0 FUN_0003b7c0 ===== */

void FUN_0003b7c0(void)

{
  short sVar1;
  int unaff_A5;
  
  sVar1 = FUN_0003b7e6();
  if (sVar1 != 0) {
    *(undefined1 *)(unaff_A5 + 0x140) = *(undefined1 *)(unaff_A5 + 0x11c);
    *(undefined1 *)(unaff_A5 + 0x141) = *(undefined1 *)(unaff_A5 + 0x11d);
    *(undefined1 *)(unaff_A5 + 0x142) = *(undefined1 *)(unaff_A5 + 0x11e);
    pc090oj_sprite_producer_3b802();
    return;
  }
  return;
}



/* ===== arcade_pc 0x03B7E6 FUN_0003b7e6 ===== */

uint FUN_0003b7e6(void)

{
  uint in_D0;
  uint uVar1;
  byte *in_A0;
  byte *in_A1;
  
  uVar1 = in_D0 & 0xffff0000;
  if ((*in_A0 <= *in_A1) &&
     ((*in_A1 != *in_A0 ||
      ((in_A0[-1] <= in_A1[-1] && ((in_A1[-1] != in_A0[-1] || (in_A0[-2] <= in_A1[-2])))))))) {
    uVar1 = 1;
  }
  return uVar1;
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



/* ===== arcade_pc 0x03C902 actor_four_record_expand_3c902 ===== */

/* WARNING: Removing unreachable block (ram,0x0003c9f6) */

void actor_four_record_expand_3c902(void)

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



/* ===== arcade_pc 0x03D044 FUN_0003d044 ===== */

void FUN_0003d044(void)

{
  short in_D0w;
  
  Ram00c08c66 = 0x39 - in_D0w;
  return;
}



/* ===== arcade_pc 0x03D054 actor_family0_render_3d054 ===== */

void actor_family0_render_3d054(void)

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
  actor_four_record_expand_3c902();
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
  actor_four_record_expand_3c902();
  return;
}



/* ===== arcade_pc 0x03FFDC FUN_0003ffdc ===== */

void FUN_0003ffdc(void)

{
  actor_four_record_expand_3c902();
  return;
}



/* ===== arcade_pc 0x03FFF0 FUN_0003fff0 ===== */

void FUN_0003fff0(void)

{
  actor_four_record_expand_3c902();
  return;
}



/* ===== arcade_pc 0x0406A4 FUN_000406a4 ===== */

void FUN_000406a4(void)

{
  short sVar1;
  short sVar2;
  short unaff_D2w;
  char *pcVar3;
  int unaff_A5;
  
  sVar1 = *(short *)(&DAT_000010d8 + unaff_A5);
  if ((unaff_D2w != 2) && (sVar1 = -sVar1, unaff_D2w != 3)) {
    sVar1 = 0;
  }
  sVar2 = *(short *)(&DAT_000010da + unaff_A5);
  if ((unaff_D2w != 0) && (sVar2 = -sVar2, unaff_D2w != 1)) {
    sVar2 = 0;
  }
  pcVar3 = (char *)(unaff_A5 + 0x2c8);
  *(undefined2 *)(unaff_A5 + 0x214) = 0;
  do {
    if ((*pcVar3 != '\0') && (pcVar3[5] != '\0')) {
      *(short *)(pcVar3 + 0x16) = sVar1 + *(short *)(pcVar3 + 0x16);
      *(short *)(pcVar3 + 0x1a) = sVar2 + *(short *)(pcVar3 + 0x1a);
      if (pcVar3[3] != '\0') {
        *(short *)(pcVar3 + 0x34) = sVar1 + *(short *)(pcVar3 + 0x34);
        *(short *)(pcVar3 + 0x742) = sVar1 + *(short *)(pcVar3 + 0x742);
        *(short *)(pcVar3 + 0x744) = sVar2 + *(short *)(pcVar3 + 0x744);
      }
    }
    pcVar3 = pcVar3 + 0x40;
    *(short *)(unaff_A5 + 0x214) = *(short *)(unaff_A5 + 0x214) + 1;
  } while (*(short *)(unaff_A5 + 0x214) != 9);
  pcVar3 = (char *)(unaff_A5 + 0x508);
  *(undefined2 *)(unaff_A5 + 0x214) = 0;
  do {
    if (((*pcVar3 != '\0') && (pcVar3[5] != '\x03')) && (pcVar3[0x24] == '\0')) {
      *(short *)(pcVar3 + 0x34) = sVar1 + *(short *)(pcVar3 + 0x34);
      *(short *)(pcVar3 + 0x16) = sVar1 + *(short *)(pcVar3 + 0x16);
      *(short *)(pcVar3 + 0x1a) = sVar2 + *(short *)(pcVar3 + 0x1a);
      if ((pcVar3[0x27] & 0x80U) != 0) {
        *(short *)(pcVar3 + 0x32) = sVar1 + *(short *)(pcVar3 + 0x32);
        *(short *)(pcVar3 + 0x30) = sVar2 + *(short *)(pcVar3 + 0x30);
      }
    }
    pcVar3 = pcVar3 + 0x40;
    *(short *)(unaff_A5 + 0x214) = *(short *)(unaff_A5 + 0x214) + 1;
  } while (*(short *)(unaff_A5 + 0x214) != 9);
  pcVar3 = (char *)(unaff_A5 + 0x748);
  *(undefined2 *)(unaff_A5 + 0x214) = 0;
  do {
    if (((*pcVar3 != '\0') && (pcVar3[5] != '\0')) && (pcVar3[0x24] == '\0')) {
      *(short *)(pcVar3 + 0x34) = sVar1 + *(short *)(pcVar3 + 0x34);
      *(short *)(pcVar3 + 0x16) = sVar1 + *(short *)(pcVar3 + 0x16);
      *(short *)(pcVar3 + 0x1a) = sVar2 + *(short *)(pcVar3 + 0x1a);
      if ((pcVar3[0x27] & 0x80U) != 0) {
        *(short *)(pcVar3 + 0x32) = sVar1 + *(short *)(pcVar3 + 0x32);
        *(short *)(pcVar3 + 0x30) = sVar2 + *(short *)(pcVar3 + 0x30);
      }
    }
    pcVar3 = pcVar3 + 0x40;
    *(short *)(unaff_A5 + 0x214) = *(short *)(unaff_A5 + 0x214) + 1;
  } while (*(short *)(unaff_A5 + 0x214) != 0xb);
  *(short *)(unaff_A5 + 0x24e) = *(short *)(unaff_A5 + 0x24e) - sVar1;
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



/* ===== arcade_pc 0x040A06 FUN_00040a06 ===== */

void FUN_00040a06(void)

{
  char unaff_D2b;
  int unaff_A4;
  
  FUN_00040a60();
  if (unaff_D2b != -1) {
    FUN_00040ae6();
    FUN_00040b16();
    *(char *)(unaff_A4 + 5) = unaff_D2b;
  }
  return;
}



/* ===== arcade_pc 0x040A1E FUN_00040a1e ===== */

void FUN_00040a1e(void)

{
  int unaff_A4;
  int unaff_A5;
  
  *(undefined1 *)(unaff_A5 + 0x22b) = *(undefined1 *)(unaff_A4 + 0x26);
  *(undefined1 *)(unaff_A5 + 0x2b7) = *(undefined1 *)(unaff_A4 + 0x38);
  *(undefined1 *)(unaff_A5 + 0xc5f) = *(undefined1 *)(unaff_A4 + 0x753);
  FUN_0004092e();
  *(undefined1 *)(unaff_A4 + 0x26) = *(undefined1 *)(unaff_A5 + 0x22b);
  *(undefined1 *)(unaff_A4 + 0x38) = *(undefined1 *)(unaff_A5 + 0x2b7);
  *(undefined1 *)(unaff_A4 + 0x753) = *(undefined1 *)(unaff_A5 + 0xc5f);
  FUN_0004a0d8();
  *(char *)(unaff_A4 + 0x21) =
       (char)*(undefined2 *)(unaff_A5 + 0x214) + (char)*(undefined2 *)(unaff_A5 + 0x200);
  *(undefined2 *)(unaff_A4 + 0x1c) = *(undefined2 *)(unaff_A4 + 0x34);
  return;
}



/* ===== arcade_pc 0x040A60 FUN_00040a60 ===== */

void FUN_00040a60(void)

{
  char in_D0b;
  char *pcVar1;
  int unaff_A4;
  
  for (pcVar1 = &DAT_00040a86;
      ((*(char *)(unaff_A4 + 5) != *pcVar1 || (in_D0b != pcVar1[1])) && (pcVar1[3] != -1));
      pcVar1 = pcVar1 + 4) {
  }
  return;
}



/* ===== arcade_pc 0x040AE6 FUN_00040ae6 ===== */

void FUN_00040ae6(void)

{
  char unaff_D2b;
  int unaff_A4;
  
  if ((*(char *)(unaff_A4 + 0x3e) == '\x02') || ((unaff_D2b != '\r' && (unaff_D2b != '\x0e')))) {
    return;
  }
  if (*(char *)(unaff_A4 + 5) == '\x01') {
    return;
  }
  if (*(char *)(unaff_A4 + 5) != '\x02') {
    return;
  }
  return;
}



/* ===== arcade_pc 0x040B16 FUN_00040b16 ===== */

void FUN_00040b16(void)

{
  byte unaff_D2b;
  int unaff_A4;
  
  if (((unaff_D2b < 3) || (0xc < unaff_D2b)) || (*(char *)(unaff_A4 + 0x755) == '\0')) {
    return;
  }
  if (*(char *)(unaff_A4 + 5) == '\x01') {
    return;
  }
  if (*(char *)(unaff_A4 + 5) != '\x02') {
    return;
  }
  return;
}



/* ===== arcade_pc 0x040BAA FUN_00040baa ===== */

void FUN_00040baa(void)

{
  int unaff_A4;
  
                    /* WARNING: Could not recover jumptable at 0x00040bc0. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(&DAT_00040bc2 +
            *(short *)(&DAT_00040bc2 + (short)((ushort)*(byte *)(unaff_A4 + 5) * 2))))();
  return;
}



/* ===== arcade_pc 0x041064 actor_surface_marker_find_41064 ===== */

longlong actor_surface_marker_find_41064(void)

{
  char cVar1;
  short sVar2;
  undefined2 extraout_D0u;
  undefined4 in_D0;
  undefined2 uVar3;
  ushort uVar4;
  undefined4 in_D1;
  ushort *extraout_A0;
  ushort *puVar5;
  ushort *puVar6;
  ushort *extraout_A0_00;
  int unaff_A4;
  int unaff_A5;
  
  uVar3 = (undefined2)((uint)in_D1 >> 0x10);
  if ((*(char *)(unaff_A4 + 3) != '\0') && (*(char *)(unaff_A4 + 0x30) != '\0')) {
    *(undefined2 *)(unaff_A5 + 0x224) = 0;
    *(undefined2 *)(unaff_A5 + 0x216) = 0;
    uVar3 = 8;
    if (*(char *)(unaff_A4 + 0x30) == '\x02') {
      uVar3 = 0x100;
    }
    *(undefined2 *)(unaff_A5 + 0x218) = uVar3;
    *(undefined2 *)(unaff_A5 + 0x21a) = 0x10;
    in_D0 = collision_map_lookup_53a2e();
    uVar3 = 0;
    cVar1 = *(char *)(unaff_A4 + 0xd);
    puVar5 = extraout_A0;
    do {
      uVar4 = *puVar5 >> 8;
      in_D0 = CONCAT22((short)((uint)in_D0 >> 0x10),uVar4);
      if ((char)(*puVar5 >> 8) == cVar1) {
        if ((char)*(undefined2 *)(unaff_A5 + 0x224) == *(char *)(unaff_A4 + 0x2f)) {
          *(ushort *)(unaff_A5 + 0x222) = uVar4;
          *(ushort **)(unaff_A5 + 0x226) = puVar5;
          while( true ) {
            collision_map_lookup_53a2e();
            if (*extraout_A0_00 >> 8 != *(ushort *)(unaff_A5 + 0x222)) break;
            *(ushort **)(unaff_A5 + 0x226) = extraout_A0_00;
            *(short *)(unaff_A5 + 0x216) = *(short *)(unaff_A5 + 0x216) + 8;
          }
          if ((*(ushort *)(&DAT_000010ae + unaff_A5) & 7) != 0) {
            *(ushort *)(unaff_A5 + 0x216) =
                 (*(ushort *)(&DAT_000010ae + unaff_A5) & 7) + *(short *)(unaff_A5 + 0x216) + -8;
          }
          if ((*(ushort *)(&DAT_000010b0 + unaff_A5) & 7) != 0) {
            *(ushort *)(unaff_A5 + 0x218) =
                 (*(ushort *)(&DAT_000010b0 + unaff_A5) & 7) + *(short *)(unaff_A5 + 0x218) + -8;
          }
          return CONCAT44(CONCAT22(extraout_D0u,*(undefined2 *)(unaff_A5 + 0x222)),1);
        }
        *(short *)(unaff_A5 + 0x224) = *(short *)(unaff_A5 + 0x224) + 1;
      }
      *(short *)(unaff_A5 + 0x216) = *(short *)(unaff_A5 + 0x216) + 0x20;
      puVar6 = puVar5 + 4;
      if ((ushort *)((uint)extraout_A0 | 0x7f) <= puVar6) {
        puVar6 = puVar5 + -0x3c;
      }
      sVar2 = *(short *)(unaff_A5 + 0x21a) + -1;
      *(short *)(unaff_A5 + 0x21a) = sVar2;
      puVar5 = puVar6;
    } while (sVar2 != 0);
  }
  return (ulonglong)CONCAT42(in_D0,uVar3) << 0x10;
}



/* ===== arcade_pc 0x04114A actor_spawn_x_bound_select_4114a ===== */

void actor_spawn_x_bound_select_4114a(void)

{
  int unaff_A4;
  int unaff_A5;
  
  if (((*(ushort *)(&DAT_000010b8 + unaff_A5) < 6) || (0x9f < *(ushort *)(&DAT_000010b8 + unaff_A5))
      ) && ((*(byte *)(unaff_A4 + 4) & 1) != 0)) {
    return;
  }
  return;
}



/* ===== arcade_pc 0x041180 actor_spawn_ground_and_activate_41180 ===== */

void actor_spawn_ground_and_activate_41180(void)

{
  byte bVar1;
  byte bVar3;
  undefined1 uVar4;
  char cVar5;
  ushort uVar2;
  short extraout_D1w;
  short extraout_D1w_00;
  undefined2 uVar6;
  short sVar7;
  undefined2 *extraout_A0;
  undefined2 *extraout_A0_00;
  undefined2 *puVar8;
  undefined2 *puVar9;
  int unaff_A4;
  int unaff_A5;
  
  sVar7 = *(short *)(unaff_A4 + 0x1c) + -1;
  *(short *)(unaff_A4 + 0x1c) = sVar7;
  if (sVar7 != 0) {
    return;
  }
  *(undefined2 *)(unaff_A4 + 0x1c) = 2;
  bVar3 = actor_surface_marker_find_41064();
  puVar8 = extraout_A0;
  if (extraout_D1w == 0) {
    if (*(char *)(unaff_A4 + 0x30) != '\0') {
      return;
    }
    actor_spawn_x_bound_select_4114a();
    if (((*(char *)(unaff_A4 + 3) == '\0') && (*(short *)(unaff_A5 + 0x13e) == 0x85)) &&
       (*(short *)(&DAT_000010cc + unaff_A5) != 0)) {
      return;
    }
    if ((*(short *)(unaff_A5 + 0x13e) == 0x6e) && (0xc < *(ushort *)(&DAT_000010cc + unaff_A5))) {
      return;
    }
    *(ushort *)(unaff_A5 + 0x216) = (*(ushort *)(&DAT_000010ae + unaff_A5) & 7) + extraout_D1w_00;
    *(undefined2 *)(unaff_A5 + 0x218) = 0;
    if ((*(char *)(unaff_A4 + 3) == '\0') && (0xaf < *(ushort *)(&DAT_000010c0 + unaff_A5))) {
      *(undefined2 *)(unaff_A5 + 0x218) = 0x300;
    }
    uVar6 = 0x26;
    if ((*(char *)(unaff_A4 + 3) != '\0') &&
       ((((((uVar2 = *(ushort *)(unaff_A5 + 0x13e), uVar2 == 0x31 || (uVar2 == 0x3f)) ||
           ((uVar2 == 0x47 ||
            ((((uVar2 == 0x53 || (uVar2 == 0x54)) || (uVar2 == 0x58)) ||
             ((uVar2 == 0x59 || (uVar2 == 0x61)))))))) || (uVar2 == 0x66)) ||
         (((uVar2 == 0x67 || (uVar2 == 0x69)) ||
          (((uVar2 == 0x6a || (((uVar2 == 0x78 || (uVar2 == 0x7b)) || (uVar2 == 0x80)))) ||
           ((uVar2 == 0x84 || (uVar2 == 0x87)))))))) ||
        ((0x28 < uVar2 && ((uVar2 < 0x2c || ((0x34 < uVar2 && (uVar2 < 0x39)))))))))) {
      uVar6 = 0x40;
    }
    *(undefined2 *)(unaff_A5 + 0x21a) = uVar6;
    collision_map_lookup_53a2e();
    bVar1 = *(byte *)(unaff_A4 + 0xd);
    puVar8 = extraout_A0_00;
    do {
      bVar3 = (byte)((ushort)*puVar8 >> 8);
      if ((bVar3 != 0x34) && (0x30 < bVar3)) {
        if (*(char *)(unaff_A4 + 3) == '\0') {
          if (bVar3 < 0x3d) goto LAB_000412fc;
        }
        else if (bVar3 == bVar1) {
LAB_000412fc:
          if ((*(ushort *)(&DAT_000010b0 + unaff_A5) & 7) != 0) {
            *(ushort *)(unaff_A5 + 0x218) =
                 (*(ushort *)(&DAT_000010b0 + unaff_A5) & 7) + *(short *)(unaff_A5 + 0x218) + -8;
          }
          if (*(char *)(unaff_A4 + 3) != '\0') break;
          *(char *)(unaff_A4 + 5) = *(char *)(unaff_A4 + 4) + '\x01';
          FUN_00041336();
          *(undefined2 *)(unaff_A4 + 0x1a) = *(undefined2 *)(unaff_A5 + 0x218);
          FUN_00040a06();
          goto LAB_00041332;
        }
      }
      if ((*(char *)(unaff_A4 + 3) == '\0') && (0xaf < *(ushort *)(&DAT_000010c0 + unaff_A5))) {
        *(short *)(unaff_A5 + 0x218) = *(short *)(unaff_A5 + 0x218) + -8;
        puVar9 = puVar8 + -0x40;
        if (puVar9 < &collision_map_64x64_words_base) {
          puVar9 = puVar8 + 0xfc0;
        }
        sVar7 = *(short *)(unaff_A5 + 0x21a) + -1;
        *(short *)(unaff_A5 + 0x21a) = sVar7;
        puVar8 = puVar9;
        if (sVar7 == 0) {
          return;
        }
      }
      else {
        *(short *)(unaff_A5 + 0x218) = *(short *)(unaff_A5 + 0x218) + 8;
        puVar9 = puVar8 + 0x40;
        if ((undefined2 *)0x10fdff < puVar9) {
          puVar9 = puVar8 + -0xfc0;
        }
        sVar7 = *(short *)(unaff_A5 + 0x21a) + -1;
        *(short *)(unaff_A5 + 0x21a) = sVar7;
        puVar8 = puVar9;
        if (sVar7 == 0) {
          return;
        }
      }
    } while( true );
  }
  *(undefined2 **)(unaff_A4 + 0xe) = puVar8;
  *(undefined1 *)(unaff_A4 + 7) = 1;
  *(undefined1 *)(unaff_A4 + 9) = 1;
  if (bVar3 < 0x4f) {
    if (bVar3 != 0x4c) {
      if (bVar3 == 0x45) {
LAB_00041834:
        if (bVar3 != *(byte *)(unaff_A4 + 0xd)) {
          return;
        }
        *(undefined1 *)(unaff_A4 + 5) = 0x18;
        FUN_00041854();
        *(undefined1 *)(unaff_A4 + 1) = 0x91;
        FUN_00045418();
        goto LAB_00041332;
      }
      if (0x44 < bVar3) {
        if (bVar3 == 0x4b) goto LAB_000418a2;
        if (bVar3 == 0x48) {
          if (*(char *)(unaff_A4 + 0xd) != 'H') {
            return;
          }
          *(undefined1 *)(unaff_A4 + 5) = 0x1e;
          FUN_00041b90();
          *(undefined1 *)(unaff_A4 + 1) = 0x70;
          goto LAB_00041332;
        }
        if (bVar3 == 0x49) {
          if (*(char *)(unaff_A4 + 0xd) != 'I') {
            return;
          }
          *(undefined1 *)(unaff_A4 + 6) = 1;
          *(short *)(unaff_A4 + 0x16) = *(short *)(unaff_A5 + 0x216) + 8;
          *(short *)(unaff_A4 + 0x1a) = *(short *)(unaff_A5 + 0x218) + -0x1f;
          FUN_0003a2d0();
          FUN_0004092e();
          return;
        }
        if (bVar3 != 0x46) {
          if (bVar3 == 0x47) {
            if (*(char *)(unaff_A4 + 0xd) != 'G') {
              return;
            }
            *(undefined1 *)(unaff_A4 + 5) = 0x1c;
            *(short *)(unaff_A4 + 0x16) = *(short *)(unaff_A5 + 0x216) + -8;
            *(ushort *)(unaff_A4 + 0x1a) = *(short *)(unaff_A5 + 0x218) - 0x62U & 0x1ff;
            *(undefined1 *)(unaff_A4 + 1) = 0x77;
          }
          else {
            if (bVar3 != 0x4d) {
              return;
            }
            if (*(char *)(unaff_A4 + 0xd) != 'M') {
              return;
            }
            *(undefined1 *)(unaff_A4 + 5) = 0x1b;
            *(short *)(unaff_A4 + 0x16) = *(short *)(unaff_A5 + 0x216) + 8;
            *(ushort *)(unaff_A4 + 0x1a) = *(short *)(unaff_A5 + 0x218) - 0x40U & 0x1ff;
            *(undefined1 *)(unaff_A4 + 1) = 0x79;
          }
          goto LAB_00041332;
        }
      }
LAB_00041a48:
      if (bVar3 != *(byte *)(unaff_A4 + 0xd)) {
        return;
      }
      *(undefined1 *)(unaff_A4 + 5) = 0x1d;
      FUN_00041ada();
      if (*(char *)(unaff_A4 + 0x30) != '\0') {
        *(short *)(unaff_A4 + 0x16) = *(short *)(unaff_A4 + 0x16) + -0x18;
      }
      *(undefined1 *)(unaff_A4 + 1) = 0x75;
      FUN_00045418();
      if ((*(short *)(unaff_A5 + 0x13e) == 0x57) && (*(char *)(unaff_A4 + 0xd) == 'F')) {
        *(undefined2 *)(unaff_A5 + 0x286) = 3;
        FUN_00043f52();
        *(undefined2 *)(unaff_A5 + 0x2a4) = 1;
        *(undefined2 *)(unaff_A5 + 0x2c6) = 1;
      }
      else if ((*(short *)(unaff_A5 + 0x13e) == 0x5a) &&
              ((*(char *)(unaff_A4 + 0xd) == 'F' && (*(char *)(unaff_A4 + 0x2f) == '\x01')))) {
        *(undefined2 *)(unaff_A5 + 0x286) = 2;
        FUN_00043f52();
        *(undefined2 *)(unaff_A5 + 0x2a4) = 1;
        *(undefined2 *)(unaff_A5 + 0x220) = 1;
      }
      goto LAB_00041332;
    }
  }
  else {
    if (bVar3 < 0x52) {
      if (bVar3 != *(byte *)(unaff_A4 + 0xd)) {
        return;
      }
      FUN_00041c1e();
      FUN_00041c60();
      *(undefined1 *)(unaff_A4 + 8) = 0xff;
      *(undefined1 *)(unaff_A4 + 5) = 0x20;
      FUN_00041bee();
      goto LAB_00041332;
    }
    if (0x56 < bVar3) {
      if (bVar3 < 0x59) {
LAB_000418a2:
        if (bVar3 != *(byte *)(unaff_A4 + 0xd)) {
          return;
        }
        *(undefined1 *)(unaff_A4 + 5) = 0x19;
        *(short *)(unaff_A4 + 0x16) = *(short *)(unaff_A5 + 0x216) + 8;
        *(ushort *)(unaff_A4 + 0x1a) = *(short *)(unaff_A5 + 0x218) - 0x18U & 0x1ff;
        *(undefined1 *)(unaff_A4 + 1) = 0x87;
        *(undefined2 *)(unaff_A4 + 0x1c) = 7;
        FUN_00045418();
        goto LAB_00041332;
      }
      if (bVar3 < 0x5e) {
        if (bVar3 != *(byte *)(unaff_A4 + 0xd)) {
          return;
        }
        *(undefined1 *)(unaff_A4 + 5) = 0x17;
        *(undefined2 *)(unaff_A4 + 0x16) = *(undefined2 *)(unaff_A5 + 0x216);
        sVar7 = *(short *)(unaff_A5 + 0x218) + -8;
        if (0x65 < *(ushort *)(unaff_A5 + 0x13e)) {
          sVar7 = *(short *)(unaff_A5 + 0x218) + -0x28;
        }
        *(short *)(unaff_A4 + 0x1a) = sVar7;
        *(undefined1 *)(unaff_A4 + 1) = 0xef;
        if ((*(ushort *)(unaff_A5 + 0x13e) < 0x20) && (*(char *)(unaff_A4 + 0xd) == 'Y')) {
          *(undefined2 *)(unaff_A5 + 0x286) = 3;
          FUN_00043f4e();
          *(undefined2 *)(unaff_A5 + 0x21c) = 1;
          *(undefined2 *)(unaff_A5 + 0x2a4) = 1;
        }
        goto LAB_00041332;
      }
      if (bVar3 < 0x61) {
        if (bVar3 != *(byte *)(unaff_A4 + 0xd)) {
          return;
        }
        *(undefined1 *)(unaff_A4 + 5) = 0x16;
        *(short *)(unaff_A4 + 0x16) = *(short *)(unaff_A5 + 0x216) + 8;
        sVar7 = *(short *)(unaff_A5 + 0x218) + 0x18;
        if (*(short *)(unaff_A5 + 0x13e) == 0x69) {
          sVar7 = *(short *)(unaff_A5 + 0x218) + 0x20;
        }
        *(short *)(unaff_A4 + 0x1a) = sVar7;
        *(undefined1 *)(unaff_A4 + 1) = 0xf1;
        FUN_00045418();
        goto LAB_00041332;
      }
      if (99 < bVar3) {
        if (bVar3 < 0x65) {
          if (bVar3 != *(byte *)(unaff_A4 + 0xd)) {
            return;
          }
          *(undefined2 *)(unaff_A4 + 0x16) = *(undefined2 *)(unaff_A5 + 0x216);
          *(undefined2 *)(unaff_A4 + 0x1a) = *(undefined2 *)(unaff_A5 + 0x218);
          *(undefined1 *)(unaff_A4 + 5) = 0x14;
          *(undefined1 *)(unaff_A4 + 1) = 1;
          FUN_00045418();
          goto LAB_00041332;
        }
        if (bVar3 < 0x67) {
          if (bVar3 != *(byte *)(unaff_A4 + 0xd)) {
            return;
          }
          *(undefined2 *)(unaff_A4 + 0x16) = *(undefined2 *)(unaff_A5 + 0x216);
          *(short *)(unaff_A4 + 0x1a) = *(short *)(unaff_A5 + 0x218) + 0x20;
          *(undefined1 *)(unaff_A4 + 5) = 0x13;
          uVar4 = 3;
          if (*(short *)(unaff_A5 + 0x13e) == 0x35) {
            if (*(char *)(unaff_A4 + 0xd) == 'f') {
              *(undefined2 *)(unaff_A5 + 0x286) = 2;
              FUN_00043f52();
              *(undefined2 *)(unaff_A5 + 0x2a4) = 1;
              *(undefined2 *)(unaff_A5 + 0x21c) = 1;
            }
            uVar4 = 5;
            *(short *)(unaff_A4 + 0x16) = *(short *)(unaff_A4 + 0x16) + 0x20;
          }
          *(undefined1 *)(unaff_A4 + 1) = uVar4;
          FUN_00045418();
          goto LAB_00041332;
        }
        if (bVar3 < 0x6a) {
LAB_00041596:
          if (bVar3 != *(byte *)(unaff_A4 + 0xd)) {
            return;
          }
          if (bVar3 == 0x67) {
            *(undefined2 *)(&DAT_000012ee + unaff_A5) = 8;
            FUN_0003a0ec();
            if (*(short *)(unaff_A5 + 0x13e) == 0x47) {
              *(undefined2 *)(unaff_A5 + 0x286) = 4;
              FUN_00043f52();
              *(undefined2 *)(unaff_A5 + 0x2a4) = 1;
              *(undefined2 *)(unaff_A5 + 0x21c) = 1;
            }
          }
          sVar7 = 0x10;
          if (*(char *)(unaff_A4 + 0x30) != '\0') {
            sVar7 = -8;
          }
          *(short *)(unaff_A4 + 0x16) = sVar7 + *(short *)(unaff_A5 + 0x216);
          *(short *)(unaff_A4 + 0x1a) = *(short *)(unaff_A5 + 0x218) + -0x20;
          *(undefined1 *)(unaff_A4 + 5) = 0x1a;
          *(undefined1 *)(unaff_A4 + 1) = 7;
          FUN_00045418();
          FUN_0004354e();
          goto LAB_00041332;
        }
        if (bVar3 < 0x6c) goto LAB_00041834;
        if (bVar3 < 0x6e) goto LAB_00041a48;
        if (bVar3 < 0x71) goto LAB_000416b2;
        if (0x72 < bVar3) {
          if (bVar3 < 0x76) {
LAB_0004145a:
            if (bVar3 != *(byte *)(unaff_A4 + 0xd)) {
              return;
            }
            FUN_00041492();
            sVar7 = 0;
            if ((*(char *)(unaff_A4 + 0x30) != '\0') &&
               (sVar7 = -0x18, *(char *)(unaff_A4 + 0x20) == '\0')) {
              sVar7 = -0x20;
            }
            *(short *)(unaff_A4 + 0x16) = sVar7 + *(short *)(unaff_A4 + 0x16);
            *(undefined1 *)(unaff_A4 + 5) = 0x22;
            *(undefined1 *)(unaff_A4 + 1) = 0x29;
            FUN_00045418();
            goto LAB_00041332;
          }
          if (bVar3 < 0x78) goto LAB_00041596;
          if (0x78 < bVar3) {
            if (bVar3 < 0x7a) goto LAB_0004145a;
            if (bVar3 < 0x7b) goto LAB_000416b2;
            if (0x7b < bVar3) {
              return;
            }
          }
        }
        if (bVar3 != *(byte *)(unaff_A4 + 0xd)) {
          return;
        }
        *(undefined1 *)(unaff_A4 + 5) = 0x21;
        *(short *)(unaff_A4 + 0x16) = *(short *)(unaff_A5 + 0x216) + 0x10;
        *(short *)(unaff_A4 + 0x1a) = *(short *)(unaff_A5 + 0x218) + -0x10;
        *(undefined1 *)(unaff_A4 + 1) = 0x27;
        FUN_00045418();
        if (*(short *)(unaff_A5 + 0x13e) == 0x4b) {
          if (*(char *)(unaff_A4 + 0xd) == 'q') {
            *(undefined2 *)(unaff_A5 + 0x286) = 2;
            FUN_00043f52();
            *(undefined2 *)(unaff_A5 + 0x2a4) = 1;
            *(undefined2 *)(unaff_A5 + 0x288) = 1;
          }
        }
        else if (*(short *)(unaff_A5 + 0x13e) == 0x4f) {
          if (*(char *)(unaff_A4 + 0xd) == 'q') {
            *(undefined2 *)(unaff_A5 + 0x286) = 4;
            FUN_00043f52();
            *(undefined2 *)(unaff_A5 + 0x2a4) = 1;
            *(undefined2 *)(unaff_A5 + 0x28a) = 1;
          }
        }
        else if ((*(short *)(unaff_A5 + 0x13e) == 0x53) && (*(char *)(unaff_A4 + 0xd) == 'q')) {
          *(undefined2 *)(unaff_A5 + 0x286) = 4;
          FUN_00043f52();
          *(undefined2 *)(unaff_A5 + 0x2a4) = 1;
          *(undefined2 *)(unaff_A5 + 0x2c4) = 1;
        }
        goto LAB_00041332;
      }
LAB_000416b2:
      if (bVar3 != *(byte *)(unaff_A4 + 0xd)) {
        return;
      }
      *(undefined1 *)(unaff_A4 + 5) = 0x15;
      *(short *)(unaff_A4 + 0x16) = *(short *)(unaff_A5 + 0x216) + 8;
      if (*(short *)(unaff_A5 + 0x13e) == 0x78) {
        sVar7 = 0x10;
        if (*(byte *)(unaff_A4 + 0xd) < 0x70) {
          sVar7 = 0x38;
        }
        *(short *)(unaff_A4 + 0x16) = sVar7 + *(short *)(unaff_A4 + 0x16);
      }
      else if (*(ushort *)(unaff_A5 + 0x13e) < 0x85) {
        if (*(short *)(unaff_A5 + 0x13e) == 0x70) {
          *(short *)(unaff_A4 + 0x16) = *(short *)(unaff_A4 + 0x16) + -0x30;
        }
        else if ((*(short *)(unaff_A5 + 0x13e) == 100) && (*(char *)(unaff_A4 + 0xd) != 'n'))
        goto LAB_0004170e;
      }
      else {
LAB_0004170e:
        *(short *)(unaff_A4 + 0x16) = *(short *)(unaff_A4 + 0x16) + 0x20;
      }
      sVar7 = *(short *)(unaff_A5 + 0x218);
      uVar4 = 0xf5;
      uVar2 = sVar7 - 0x20;
      if ((*(char *)(unaff_A5 + 0x118) != '\x02') && (*(short *)(unaff_A5 + 0x13e) != 0x62)) {
        FUN_00041752();
        uVar4 = 0xf7;
        uVar2 = sVar7 + 0x20;
      }
      *(ushort *)(unaff_A4 + 0x1a) = uVar2 & 0x1ff;
      *(undefined1 *)(unaff_A4 + 1) = uVar4;
      goto LAB_00041332;
    }
  }
  if (bVar3 != *(byte *)(unaff_A4 + 0xd)) {
    return;
  }
  cVar5 = FUN_000418e2();
  if ((cVar5 == 'L') || (cVar5 == 'U')) {
    *(undefined2 *)(&DAT_000012ee + unaff_A5) = 8;
    FUN_0003a0ec();
  }
  *(undefined1 *)(unaff_A4 + 5) = 0x1a;
  uVar2 = FUN_000419b2();
  *(ushort *)(unaff_A4 + 0x16) = uVar2 & 0x1ff;
  uVar2 = FUN_000419b8();
  *(ushort *)(unaff_A4 + 0x1a) = uVar2 & 0x1ff;
  *(undefined1 *)(unaff_A4 + 1) = 0x7b;
  FUN_00045418();
  bVar3 = *(byte *)(unaff_A5 + 0x118);
  if (bVar3 < 2) goto LAB_00041332;
  if (bVar3 != 2) {
    cVar5 = *(char *)(unaff_A4 + 0xd);
    if (bVar3 == 3) {
      if ((cVar5 == 'L') || ((cVar5 == 'R' || (cVar5 == 'U')))) goto LAB_00041332;
    }
    else {
      if ((*(short *)(unaff_A5 + 0x13e) == 100) || (*(short *)(unaff_A5 + 0x13e) == 0x70))
      goto LAB_00041332;
      if (*(short *)(unaff_A5 + 0x13e) == 0x78) {
        if (cVar5 != 'R') goto LAB_00041332;
      }
      else if ((0x84 < *(ushort *)(unaff_A5 + 0x13e)) ||
              ((cVar5 != 'L' && (*(ushort *)(unaff_A5 + 0x13e) < 0x59)))) goto LAB_00041332;
    }
  }
  FUN_0004354e();
LAB_00041332:
  FUN_00040baa();
  return;
}



/* ===== arcade_pc 0x041336 FUN_00041336 ===== */

void FUN_00041336(void)

{
  char in_D0b;
  char cVar1;
  short sVar2;
  int in_A0;
  int unaff_A4;
  int unaff_A5;
  
  sVar2 = 0;
  if (in_D0b != ':') {
    cVar1 = *(char *)(in_A0 + 2);
    sVar2 = 8;
    if (*(char *)(unaff_A4 + 4) == '\0') {
      cVar1 = *(char *)(in_A0 + -2);
      sVar2 = -8;
    }
    if (in_D0b != cVar1) {
      sVar2 = 0;
    }
  }
  *(short *)(unaff_A4 + 0x16) = *(short *)(unaff_A5 + 0x216) + sVar2;
  return;
}



/* ===== arcade_pc 0x041492 FUN_00041492 ===== */

void FUN_00041492(void)

{
  char in_D0b;
  short sVar1;
  int unaff_A4;
  int unaff_A5;
  
  sVar1 = 0x24;
  if ((((in_D0b != 't') && (sVar1 = 0x44, in_D0b != 's')) && (sVar1 = 4, in_D0b == 'y')) &&
     (*(char *)(unaff_A4 + 0x30) == '\0')) {
    sVar1 = -4;
  }
  *(short *)(unaff_A4 + 0x16) = sVar1 + *(short *)(unaff_A5 + 0x216);
  *(short *)(unaff_A4 + 0x1a) = *(short *)(unaff_A5 + 0x218) + 4;
  return;
}



/* ===== arcade_pc 0x041752 FUN_00041752 ===== */

void FUN_00041752(void)

{
  int unaff_A4;
  int unaff_A5;
  
  if (*(short *)(unaff_A5 + 0x13e) == 0x38) {
    if (*(char *)(unaff_A4 + 0xd) == 'n') {
      *(undefined2 *)(unaff_A5 + 0x286) = 4;
      FUN_00043f52();
      *(undefined2 *)(unaff_A5 + 0x288) = 1;
      *(undefined2 *)(unaff_A5 + 0x2a4) = 1;
    }
    else if (*(char *)(unaff_A4 + 0xd) == 'p') {
      *(short *)(unaff_A4 + 0x16) = *(short *)(unaff_A4 + 0x16) + 0x20;
      return;
    }
  }
  return;
}



/* ===== arcade_pc 0x041854 FUN_00041854 ===== */

void FUN_00041854(void)

{
  undefined4 uVar1;
  int unaff_A4;
  int unaff_A5;
  
  uVar1 = 0x8ffb0;
  if (*(char *)(unaff_A5 + 0x118) == '\x03') {
    *(undefined2 *)(unaff_A5 + 0x286) = 4;
    FUN_00043f52();
    *(undefined2 *)(unaff_A5 + 0x2a4) = 1;
    *(undefined2 *)(unaff_A5 + 0x28a) = 1;
    uVar1 = 0x100010;
  }
  *(ushort *)(unaff_A4 + 0x1a) = (short)uVar1 + *(short *)(unaff_A5 + 0x218) & 0x1ff;
  *(short *)(unaff_A4 + 0x16) = (short)((uint)uVar1 >> 0x10) + *(short *)(unaff_A5 + 0x216);
  return;
}



/* ===== arcade_pc 0x0418E2 FUN_000418e2 ===== */

void FUN_000418e2(void)

{
  int unaff_A4;
  int unaff_A5;
  
  if (*(char *)(unaff_A4 + 0x30) != '\0') {
    *(int *)(unaff_A4 + 0xe) = *(int *)(unaff_A4 + 0xe) + -4;
    *(short *)(unaff_A5 + 0x216) = *(short *)(unaff_A5 + 0x216) + -0x10;
  }
  return;
}



/* ===== arcade_pc 0x0419B2 FUN_000419b2 ===== */

short FUN_000419b2(void)

{
  short in_D0w;
  
  return in_D0w + 8;
}



/* ===== arcade_pc 0x0419B8 FUN_000419b8 ===== */

short FUN_000419b8(void)

{
  ushort uVar1;
  short in_D0w;
  int unaff_A5;
  
  uVar1 = *(ushort *)(unaff_A5 + 0x13e);
  if (uVar1 == 0x29) {
    return in_D0w + 0x20;
  }
  if (uVar1 == 0x2a) {
    return in_D0w + -0x10;
  }
  if (0x35 < uVar1) {
    in_D0w = in_D0w + -0x20;
  }
  return in_D0w;
}



/* ===== arcade_pc 0x041ADA FUN_00041ada ===== */

void FUN_00041ada(void)

{
  short sVar1;
  int unaff_A4;
  int unaff_A5;
  
  if ((*(ushort *)(unaff_A5 + 0x13e) < 0x18) && (*(char *)(unaff_A4 + 0x30) != '\0')) {
    *(short *)(unaff_A4 + 0x16) = *(short *)(unaff_A5 + 0x216) + -0x18;
    *(ushort *)(unaff_A4 + 0x1a) = *(short *)(unaff_A5 + 0x218) + 0x50U & 0x1ff;
    return;
  }
  sVar1 = 0x10;
  if (*(short *)(unaff_A5 + 0x13e) != 0x37) {
    sVar1 = 0x18;
  }
  *(short *)(unaff_A4 + 0x16) = sVar1 + *(short *)(unaff_A5 + 0x216);
  *(ushort *)(unaff_A4 + 0x1a) = *(short *)(unaff_A5 + 0x218) - 0x10U & 0x1ff;
  return;
}



/* ===== arcade_pc 0x041B90 FUN_00041b90 ===== */

void FUN_00041b90(void)

{
  short in_D0w;
  short in_D1w;
  short sVar1;
  short sVar2;
  int unaff_A4;
  int unaff_A5;
  
  sVar1 = 8;
  sVar2 = -0x20;
  if ((*(char *)(unaff_A5 + 0x118) != '\x01') && (*(char *)(unaff_A5 + 0x118) != '\x04')) {
    sVar1 = 0x10;
    sVar2 = -2;
    if (*(char *)(unaff_A5 + 0x118) == '\x06') {
      sVar2 = -0x1e;
    }
  }
  *(short *)(unaff_A4 + 0x16) = sVar1 + in_D0w;
  *(short *)(unaff_A4 + 0x1a) = sVar2 + in_D1w;
  return;
}



/* ===== arcade_pc 0x041BEE FUN_00041bee ===== */

void FUN_00041bee(void)

{
  ushort uVar1;
  undefined2 *puVar2;
  int unaff_A4;
  int unaff_A5;
  
  *(undefined2 *)(&DAT_00001280 + unaff_A5) = 1;
  uVar1 = *(ushort *)(unaff_A5 + 0x214);
  puVar2 = (undefined2 *)((int)(short)((ushort)*(byte *)(unaff_A4 + 0x2f) * 6) + unaff_A5 + 0x1282);
  *puVar2 = 1;
  *(undefined **)(puVar2 + 1) = &DAT_00d00460 + (uint)uVar1 * 0x50;
  return;
}



/* ===== arcade_pc 0x041C1E FUN_00041c1e ===== */

void FUN_00041c1e(void)

{
  char in_D0b;
  short sVar1;
  int unaff_A4;
  int unaff_A5;
  
  sVar1 = 0x18;
  if ((in_D0b != 'O') && (sVar1 = 0xc, in_D0b != 'P')) {
    sVar1 = 0;
  }
  *(short *)(unaff_A4 + 0x16) = *(short *)(unaff_A5 + 0x216) + sVar1;
  if (*(short *)(unaff_A5 + 0x13e) != 0x53) {
    if (*(short *)(unaff_A5 + 0x13e) == 0x58) {
      *(short *)(unaff_A4 + 0x16) = *(short *)(unaff_A4 + 0x16) + 0x10;
      return;
    }
    if (*(short *)(unaff_A5 + 0x13e) != 0x75) {
      return;
    }
  }
  *(short *)(unaff_A4 + 0x16) = *(short *)(unaff_A4 + 0x16) + -0x10;
  return;
}



/* ===== arcade_pc 0x041C60 FUN_00041c60 ===== */

void FUN_00041c60(void)

{
  ushort uVar1;
  short sVar2;
  int unaff_A4;
  int unaff_A5;
  
  sVar2 = *(short *)(unaff_A5 + 0x218);
  uVar1 = *(ushort *)(unaff_A5 + 0x13e);
  if (0x17 < uVar1) {
    if (uVar1 < 0x25) {
      if (*(short *)(unaff_A5 + 0x13e) == 0x22) {
        *(undefined2 *)(unaff_A5 + 0x286) = 2;
        FUN_00043f52();
        *(undefined2 *)(unaff_A5 + 0x288) = 1;
        *(undefined2 *)(unaff_A5 + 0x2a4) = 1;
        sVar2 = *(short *)(unaff_A5 + 0x218);
      }
LAB_00041cbe:
      *(short *)(unaff_A4 + 0x1a) = sVar2 + -0x88;
      return;
    }
    if (0x4c < uVar1) {
      if (uVar1 < 0x53) {
        sVar2 = sVar2 + -0x40;
        goto LAB_00041ccc;
      }
      if (0x57 < uVar1) {
        if (uVar1 == 0x70) {
          sVar2 = sVar2 + -0x20;
        }
        else {
          if (uVar1 != 0x75) goto LAB_00041cbe;
          sVar2 = sVar2 + -0x78;
        }
        goto LAB_00041ccc;
      }
    }
  }
  sVar2 = sVar2 + -0x60;
LAB_00041ccc:
  *(short *)(unaff_A4 + 0x1a) = sVar2;
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
  byte bVar2;
  short sVar3;
  undefined *puVar4;
  undefined *extraout_A1;
  undefined *extraout_A1_00;
  undefined *extraout_A1_01;
  undefined *extraout_A1_02;
  char *pcVar5;
  int unaff_A5;
  
  pcVar5 = (char *)(unaff_A5 + 0x508);
  puVar4 = &DAT_00d001c8;
  *(undefined2 *)(unaff_A5 + 0x214) = 0;
  do {
    if (*pcVar5 == '\0') {
      sVar3 = 0xd;
      do {
        *(undefined2 *)(puVar4 + 2) = 0x180;
        puVar4 = puVar4 + 8;
        sVar3 = sVar3 + -1;
      } while (sVar3 != 0);
    }
    else {
      actor_family0_render_3d054();
      puVar4 = extraout_A1;
    }
    pcVar5 = pcVar5 + 0x40;
    *(short *)(unaff_A5 + 0x214) = *(short *)(unaff_A5 + 0x214) + 1;
  } while (*(short *)(unaff_A5 + 0x214) != 2);
  pcVar5 = (char *)(unaff_A5 + 0x5c8);
  puVar4 = &DAT_00d00300;
  *(undefined2 *)(unaff_A5 + 0x214) = 0;
  do {
    if (*pcVar5 == '\0') {
      sVar3 = 4;
      do {
        *(undefined2 *)(puVar4 + 2) = 0x180;
        puVar4 = puVar4 + 8;
        sVar3 = sVar3 + -1;
      } while (sVar3 != 0);
    }
    else {
      actor_family0_render_3d054();
      puVar4 = extraout_A1_00;
    }
    pcVar5 = pcVar5 + 0x40;
    *(short *)(unaff_A5 + 0x214) = *(short *)(unaff_A5 + 0x214) + 1;
  } while (*(short *)(unaff_A5 + 0x214) != 6);
  pcVar5 = (char *)(unaff_A5 + 0x2c8);
  *(undefined2 *)(unaff_A5 + 0x214) = 0;
  puVar4 = &DAT_00d00460;
  do {
    if ((*pcVar5 == '\0') || (pcVar5[5] == '\0')) goto FUN_00041ede;
    if (pcVar5[3] == '\0') goto LAB_00041e60;
    cVar1 = pcVar5[5];
    if (cVar1 == '\x17') {
LAB_0003efc8:
      if (((pcVar5[0x34] & 0x80U) == 0) && (0x17f < (*(ushort *)(pcVar5 + 0x16) & 0x1ff)))
      goto FUN_00041ede;
LAB_00041e60:
      actor_family0_render_3d054();
      puVar4 = extraout_A1_01;
    }
    else {
      if (cVar1 != '\x1a') {
        if (cVar1 == ' ') goto LAB_0003efc8;
        if (cVar1 == '\x13') {
          if (((pcVar5[1] & 1U) == 0) && ((pcVar5[0x34] & 0x80U) == 0)) goto FUN_00041ede;
        }
        else if (cVar1 == '\"') {
          if (((pcVar5[0xd] == 'y') && (0x4f < *(ushort *)(pcVar5 + 0x34))) &&
             (*(ushort *)(pcVar5 + 0x34) < 0xfe60)) goto FUN_00041ede;
        }
        else if ((cVar1 == '\x15') && (*(short *)(unaff_A5 + 0x13e) == 0x71)) {
          bVar2 = pcVar5[0x16];
          goto joined_r0x0003f07c;
        }
        goto LAB_00041e60;
      }
      if (*(ushort *)(unaff_A5 + 0x13e) < 0x87) {
        if (pcVar5[0x32] == '\0') goto LAB_0003efc8;
        bVar2 = pcVar5[0x742];
joined_r0x0003f07c:
        if ((bVar2 & 0x80) == 0) goto LAB_00041e60;
      }
      else if (0xfe07 < *(ushort *)(pcVar5 + 0x34)) goto LAB_00041e60;
FUN_00041ede:
      sVar3 = 10;
      if (*(short *)(unaff_A5 + 0x214) == 8) {
        sVar3 = 0x13;
      }
      do {
        *(undefined2 *)(puVar4 + 2) = 0x180;
        puVar4 = puVar4 + 8;
        sVar3 = sVar3 + -1;
      } while (sVar3 != 0);
    }
    pcVar5 = pcVar5 + 0x40;
    *(short *)(unaff_A5 + 0x214) = *(short *)(unaff_A5 + 0x214) + 1;
    if (*(short *)(unaff_A5 + 0x214) == 9) {
      pcVar5 = (char *)(unaff_A5 + 0x748);
      puVar4 = &DAT_00d00170;
      *(undefined2 *)(unaff_A5 + 0x214) = 0;
      do {
        if ((*pcVar5 == '\0') || (pcVar5[0x36] != '\0')) {
          sVar3 = 1;
          do {
            *(undefined2 *)(puVar4 + 2) = 0x180;
            puVar4 = puVar4 + 8;
            sVar3 = sVar3 + -1;
          } while (sVar3 != 0);
        }
        else {
          actor_family0_render_3d054();
          puVar4 = extraout_A1_02;
        }
        pcVar5 = pcVar5 + 0x40;
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
  byte bVar2;
  short sVar3;
  int extraout_A1;
  undefined *puVar4;
  undefined *extraout_A1_00;
  int in_A1;
  char *pcVar5;
  char *unaff_A4;
  int unaff_A5;
  
  do {
    sVar3 = 10;
    if (*(short *)(unaff_A5 + 0x214) == 8) {
      sVar3 = 0x13;
    }
    do {
      *(undefined2 *)(in_A1 + 2) = 0x180;
      in_A1 = in_A1 + 8;
      sVar3 = sVar3 + -1;
      pcVar5 = unaff_A4;
    } while (sVar3 != 0);
    while( true ) {
      unaff_A4 = pcVar5 + 0x40;
      *(short *)(unaff_A5 + 0x214) = *(short *)(unaff_A5 + 0x214) + 1;
      if (*(short *)(unaff_A5 + 0x214) == 9) {
        pcVar5 = (char *)(unaff_A5 + 0x748);
        puVar4 = &DAT_00d00170;
        *(undefined2 *)(unaff_A5 + 0x214) = 0;
        do {
          if ((*pcVar5 == '\0') || (pcVar5[0x36] != '\0')) {
            sVar3 = 1;
            do {
              *(undefined2 *)(puVar4 + 2) = 0x180;
              puVar4 = puVar4 + 8;
              sVar3 = sVar3 + -1;
            } while (sVar3 != 0);
          }
          else {
            actor_family0_render_3d054();
            puVar4 = extraout_A1_00;
          }
          pcVar5 = pcVar5 + 0x40;
          *(short *)(unaff_A5 + 0x214) = *(short *)(unaff_A5 + 0x214) + 1;
        } while (*(short *)(unaff_A5 + 0x214) != 0xb);
        return;
      }
      if ((*unaff_A4 == '\0') || (pcVar5[0x45] == '\0')) break;
      if (pcVar5[0x43] != '\0') {
        cVar1 = pcVar5[0x45];
        if (cVar1 == '\x17') {
LAB_0003efc8:
          if (((pcVar5[0x74] & 0x80U) == 0) && (0x17f < (*(ushort *)(pcVar5 + 0x56) & 0x1ff)))
          break;
        }
        else if (cVar1 == '\x1a') {
          if (*(ushort *)(unaff_A5 + 0x13e) < 0x87) {
            if (pcVar5[0x72] == '\0') goto LAB_0003efc8;
            bVar2 = pcVar5[0x782];
joined_r0x0003f07c:
            if ((bVar2 & 0x80) != 0) break;
          }
          else if (*(ushort *)(pcVar5 + 0x74) < 0xfe08) break;
        }
        else {
          if (cVar1 == ' ') goto LAB_0003efc8;
          if (cVar1 == '\x13') {
            if (((pcVar5[0x41] & 1U) == 0) && ((pcVar5[0x74] & 0x80U) == 0)) break;
          }
          else if (cVar1 == '\"') {
            if (((pcVar5[0x4d] == 'y') && (0x4f < *(ushort *)(pcVar5 + 0x74))) &&
               (*(ushort *)(pcVar5 + 0x74) < 0xfe60)) break;
          }
          else if ((cVar1 == '\x15') && (*(short *)(unaff_A5 + 0x13e) == 0x71)) {
            bVar2 = pcVar5[0x56];
            goto joined_r0x0003f07c;
          }
        }
      }
      actor_family0_render_3d054();
      in_A1 = extraout_A1;
      pcVar5 = unaff_A4;
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
      actor_family0_render_3d054();
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
      actor_family0_render_3d054();
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
      actor_family0_render_3d054();
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



/* ===== arcade_pc 0x041F96 FUN_00041f96 ===== */

undefined1 FUN_00041f96(void)

{
  return 3;
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



/* ===== arcade_pc 0x042E38 actor_velocity_and_map_collision_42e38 ===== */

void actor_velocity_and_map_collision_42e38(void)

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
    if ((*(byte *)(unaff_A4 + 6) < 5) &&
       (collision_map_lookup_53a2e(), (*(byte *)(extraout_A0 + 1) & 1) != 0)) {
      FUN_000447f0();
    }
  }
  return;
}



/* ===== arcade_pc 0x043394 FUN_00043394 ===== */

int FUN_00043394(void)

{
  short sVar1;
  ushort uVar2;
  undefined4 in_D0;
  char *unaff_A6;
  
  do {
    uVar2 = (ushort)((uint)in_D0 >> 0x10);
    if (*unaff_A6 == '\0') {
      return (uint)uVar2 << 0x10;
    }
    unaff_A6 = unaff_A6 + 0x40;
    sVar1 = (short)in_D0 + -1;
    in_D0 = CONCAT22(uVar2,sVar1);
  } while (sVar1 != 0);
  return 1;
}



/* ===== arcade_pc 0x0433AC FUN_000433ac ===== */

void FUN_000433ac(void)

{
  short sVar1;
  int unaff_A5;
  
  sVar1 = FUN_00043394();
  if (sVar1 == 0) {
    *(undefined1 *)(unaff_A5 + 0x748) = 1;
    *(undefined1 *)(unaff_A5 + 0x74d) = 0;
    *(undefined2 *)(unaff_A5 + 0x766) = 0x275;
    *(undefined1 *)(unaff_A5 + 0x749) = 0xa7;
    *(undefined1 *)(unaff_A5 + 0x768) = 1;
    *(undefined1 *)(unaff_A5 + 0x750) = 0xff;
    *(undefined1 *)(unaff_A5 + 0x751) = 1;
    *(undefined1 *)(unaff_A5 + 0x74e) = 2;
    FUN_00043450();
  }
  return;
}



/* ===== arcade_pc 0x043450 FUN_00043450 ===== */

void FUN_00043450(void)

{
  char cVar1;
  short in_D0w;
  short sVar2;
  int unaff_A4;
  int unaff_A6;
  
  *(undefined1 *)(unaff_A6 + 0x38) = 0;
  *(char *)(unaff_A6 + 0x23) = (char)in_D0w;
  sVar2 = (short)(char)(&DAT_00043484)[(short)(in_D0w * 2)];
  cVar1 = (&DAT_00043485)[(short)(in_D0w * 2)];
  if (*(char *)(unaff_A4 + 2) == '\0') {
    sVar2 = -sVar2;
  }
  *(short *)(unaff_A6 + 0x16) = *(short *)(unaff_A4 + 0x16) + sVar2;
  *(short *)(unaff_A6 + 0x1a) = *(short *)(unaff_A4 + 0x1a) + (short)cVar1;
  return;
}



/* ===== arcade_pc 0x04354E FUN_0004354e ===== */

void FUN_0004354e(void)

{
  short sVar1;
  undefined1 uVar2;
  int unaff_A4;
  int unaff_A5;
  
  sVar1 = FUN_00043394();
  if (sVar1 == 0) {
    *(undefined2 *)(unaff_A5 + 0x766) = 0xd5c;
    uVar2 = FUN_00041f96();
    *(undefined1 *)(unaff_A5 + 0x771) = uVar2;
    *(undefined1 *)(unaff_A5 + 0x749) = 0xf0;
    *(undefined1 *)(unaff_A5 + 0x74e) = 7;
    *(undefined1 *)(unaff_A5 + 0x74d) = 0xc;
    *(undefined1 *)(unaff_A5 + 0x780) = 1;
    *(undefined2 *)(unaff_A5 + 0x75e) = *(undefined2 *)(unaff_A4 + 0x16);
    *(undefined2 *)(unaff_A5 + 0x762) = *(undefined2 *)(unaff_A4 + 0x1a);
    *(int *)(unaff_A5 + 0xc70) = unaff_A4;
    *(undefined1 *)(unaff_A5 + 0xc6f) = *(undefined1 *)(unaff_A4 + 0xd);
    *(undefined1 *)(unaff_A5 + 0x769) = *(undefined1 *)(unaff_A4 + 0xd);
    *(undefined1 *)(unaff_A5 + 0x748) = 1;
    *(undefined1 *)(unaff_A5 + 0x768) = 1;
  }
  return;
}



/* ===== arcade_pc 0x043F4E FUN_00043f4e ===== */

void FUN_00043f4e(void)

{
  char *pcVar1;
  int unaff_A5;
  
  pcVar1 = (char *)(unaff_A5 + 0x3c8);
  *(undefined2 *)(unaff_A5 + 0x232) = 0;
  do {
    if (*pcVar1 != '\0') {
      if (pcVar1[5] == '\0') {
        FUN_0004092e();
      }
      else {
        pcVar1[0x39] = '\x01';
        FUN_000447f0();
      }
    }
    pcVar1 = pcVar1 + 0x40;
    *(short *)(unaff_A5 + 0x232) = *(short *)(unaff_A5 + 0x232) + 1;
  } while (*(short *)(unaff_A5 + 0x286) != *(short *)(unaff_A5 + 0x232));
  return;
}



/* ===== arcade_pc 0x043F52 FUN_00043f52 ===== */

void FUN_00043f52(void)

{
  char *unaff_A4;
  int unaff_A5;
  
  *(undefined2 *)(unaff_A5 + 0x232) = 0;
  do {
    if (*unaff_A4 != '\0') {
      if (unaff_A4[5] == '\0') {
        FUN_0004092e();
      }
      else {
        unaff_A4[0x39] = '\x01';
        FUN_000447f0();
      }
    }
    unaff_A4 = unaff_A4 + 0x40;
    *(short *)(unaff_A5 + 0x232) = *(short *)(unaff_A5 + 0x232) + 1;
  } while (*(short *)(unaff_A5 + 0x286) != *(short *)(unaff_A5 + 0x232));
  return;
}



/* ===== arcade_pc 0x0446B0 actor_hurtbox_base_selector_446b0 ===== */

void actor_hurtbox_base_selector_446b0(void)

{
  return;
}



/* ===== arcade_pc 0x0446BC actor_hurtbox_selector_446bc ===== */

ushort actor_hurtbox_selector_446bc(void)

{
  byte bVar1;
  ushort in_D0w;
  ushort uVar2;
  int unaff_A4;
  int unaff_A5;
  
  if (*(ushort *)(unaff_A5 + 0x214) < 9) {
    if (*(char *)(unaff_A4 + 3) == '\0') {
      return (ushort)*(byte *)(unaff_A4 + 0x3e);
    }
    return in_D0w;
  }
  bVar1 = *(byte *)(unaff_A4 + 6);
  if (0xb < bVar1) {
    if (*(char *)(unaff_A4 + 0x26) != '\0') {
      return (ushort)bVar1;
    }
    if (bVar1 != 0x16) {
      if (bVar1 == 0x11) {
        actor_hurtbox_base_selector_446b0();
        uVar2 = (ushort)*(byte *)(unaff_A4 + 0x30) << 1;
      }
      else if ((bVar1 == 0x18) || (bVar1 == 0x19)) {
        uVar2 = actor_hurtbox_base_selector_446b0();
      }
      else {
        if (bVar1 != 0x17) goto LAB_000446d2;
        actor_hurtbox_base_selector_446b0();
        uVar2 = (ushort)*(byte *)(unaff_A4 + 0x30) << 1;
      }
      return uVar2;
    }
    if (*(char *)(unaff_A4 + 0x37) != '\0') {
      return 0x16;
    }
  }
LAB_000446d2:
  uVar2 = actor_hurtbox_base_selector_446b0();
  return uVar2;
}



/* ===== arcade_pc 0x0447A6 FUN_000447a6 ===== */

void FUN_000447a6(void)

{
  return;
}



/* ===== arcade_pc 0x0447CE FUN_000447ce ===== */

void FUN_000447ce(void)

{
  char cVar1;
  int unaff_A3;
  int unaff_A4;
  int unaff_A5;
  
  cVar1 = *(char *)(unaff_A4 + 6);
  if (((cVar1 != '\n') && (cVar1 != '\v')) && (cVar1 != '\x12')) {
    if (0x11 < *(ushort *)(unaff_A5 + 0x214)) {
      *(undefined1 *)(unaff_A3 + 2) = 0;
      *(undefined1 *)(unaff_A4 + 0x3d) = 1;
      if (*(char *)(unaff_A4 + 6) != '\a') {
        FUN_000448b2();
      }
    }
    return;
  }
  *(undefined2 *)(unaff_A4 + 0x32) = *(undefined2 *)(&DAT_000010be + unaff_A5);
  *(undefined2 *)(unaff_A4 + 0x30) = *(undefined2 *)(&DAT_000010c0 + unaff_A5);
  *(undefined1 *)(unaff_A4 + 0xc) = 0xff;
  *(undefined1 *)(unaff_A4 + 7) = 0;
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



/* ===== arcade_pc 0x044804 FUN_00044804 ===== */

void FUN_00044804(void)

{
  char cVar1;
  int unaff_A4;
  int unaff_A5;
  
  *(undefined1 *)(unaff_A4 + 0x3d) = 0x10;
  cVar1 = '\x01';
  if ((*(short *)(&DAT_00001310 + unaff_A5) != 2) &&
     (cVar1 = '\x02', *(short *)(&DAT_00001310 + unaff_A5) != 4)) {
    cVar1 = '\x03';
  }
  *(char *)(unaff_A4 + 0x3c) = cVar1 + *(char *)(unaff_A4 + 0x3c);
  if (*(byte *)(unaff_A4 + 0x3c) < *(byte *)(unaff_A4 + 0x3a)) {
    FUN_0003a0ec();
    if (*(ushort *)(unaff_A5 + 0x214) < 9) {
      *(undefined1 *)(unaff_A4 + 0x747) = 1;
    }
    return;
  }
  FUN_000448b2();
  if ((*(ushort *)(unaff_A5 + 0x214) < 0x12) || (*(char *)(unaff_A4 + 6) == '\v')) {
    FUN_0003b726();
    if (*(short *)(&DAT_0000140c + unaff_A5) == 1) {
      FUN_0003b726();
    }
    if ((*(char *)(unaff_A4 + 6) == '\b') || (*(char *)(unaff_A4 + 6) == '\t')) {
      DAT_0010c545 = 1;
      FUN_000448b2();
      *(short *)(unaff_A4 + 0x1a) = *(short *)(unaff_A4 + 0x1a) + -0x10;
      return;
    }
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



/* ===== arcade_pc 0x0448D8 FUN_000448d8 ===== */

void FUN_000448d8(void)

{
  int unaff_A4;
  
  if (*(char *)(unaff_A4 + 0x3e) == '\f') {
    FUN_0003b726();
    FUN_00040a1e();
  }
  return;
}



/* ===== arcade_pc 0x0448F2 FUN_000448f2 ===== */

void FUN_000448f2(void)

{
  int unaff_A5;
  
  *(char *)(unaff_A5 + 0x22c) = (&DAT_00001248)[unaff_A5] + '\b';
  *(char *)(unaff_A5 + 0x22d) = (&DAT_00001249)[unaff_A5] + -8;
  *(undefined2 *)(unaff_A5 + 0x22e) = *(undefined2 *)(&DAT_0000124a + unaff_A5);
  return;
}



/* ===== arcade_pc 0x044910 FUN_00044910 ===== */

void FUN_00044910(void)

{
  int unaff_A5;
  
  if (*(short *)(&DAT_000013b4 + unaff_A5) == 1) {
    *(undefined2 *)(unaff_A5 + 0x2b0) = *(undefined2 *)(&DAT_00001248 + unaff_A5);
    *(undefined2 *)(unaff_A5 + 0x2b2) = *(undefined2 *)(&DAT_0000124a + unaff_A5);
    *(char *)(unaff_A5 + 0x2b3) = *(char *)(unaff_A5 + 0x2b3) + '\x10';
  }
  return;
}



/* ===== arcade_pc 0x044930 FUN_00044930 ===== */

void FUN_00044930(void)

{
  int unaff_A4;
  int unaff_A5;
  
  if ((*(short *)(&DAT_000013b4 + unaff_A5) == 1) && (*(char *)(unaff_A4 + 5) == '\x15')) {
    FUN_00044c66();
    return;
  }
  if (*(ushort *)(unaff_A5 + 0x214) < 0x12) {
    FUN_00044c6c();
    return;
  }
  FUN_00044c72();
  return;
}



/* ===== arcade_pc 0x04495A FUN_0004495a ===== */

void FUN_0004495a(void)

{
  undefined2 uVar1;
  int unaff_A3;
  int unaff_A4;
  
  uVar1 = 0;
  if (((*(char *)(unaff_A4 + 6) == '\f') && (uVar1 = 1, *(char *)(unaff_A4 + 0x25) != '\0')) &&
     (uVar1 = 2, *(char *)(unaff_A4 + 0x25) != '\x03')) {
    uVar1 = 3;
  }
  *(undefined2 *)(unaff_A3 + 2) = uVar1;
  return;
}



/* ===== arcade_pc 0x04498C FUN_0004498c ===== */

void FUN_0004498c(void)

{
  char cVar1;
  int unaff_A3;
  int unaff_A4;
  
  cVar1 = *(char *)(unaff_A4 + 5);
  if ((((cVar1 == '\x18') || (cVar1 == '\x1d')) || (cVar1 == '!')) &&
     (*(char *)(unaff_A4 + 8) == '\x02')) {
    *(undefined1 *)(unaff_A3 + 3) = 3;
    return;
  }
  return;
}



/* ===== arcade_pc 0x0449B4 player_actor_collision_scan_449b4 ===== */

void player_actor_collision_scan_449b4(void)

{
  char cVar1;
  short sVar2;
  byte bVar3;
  undefined2 *puVar4;
  undefined2 *puVar5;
  short *psVar6;
  char *pcVar7;
  int unaff_A5;
  
  *(undefined2 *)(unaff_A5 + 0x242) = 0;
  puVar4 = (undefined2 *)(&DAT_000012a8 + unaff_A5);
  puVar5 = (undefined2 *)(&DAT_000012c8 + unaff_A5);
  sVar2 = 4;
  do {
    *puVar4 = 0;
    *puVar5 = 0;
    puVar4 = puVar4 + 4;
    puVar5 = puVar5 + 4;
    sVar2 = sVar2 + -1;
  } while (sVar2 != 0);
  FUN_000448f2();
  FUN_00044910();
  *(undefined2 *)(unaff_A5 + 0x21e) = 0;
  puVar4 = (undefined2 *)(&DAT_000012a8 + unaff_A5);
  pcVar7 = (char *)(unaff_A5 + 0x2c8);
  *(undefined2 *)(unaff_A5 + 0x214) = 0;
  do {
    if (((*pcVar7 != '\0') && (pcVar7[5] != '\0')) && (pcVar7[0x3d] == '\0')) {
      if (pcVar7[3] == '\0') {
        actor_hurtbox_selector_446bc();
        goto LAB_00044a0e;
      }
      cVar1 = (&DAT_00044582)[(short)(ushort)(byte)(pcVar7[0xd] + 0xbd)];
      if ((pcVar7[0x38] == '\x02') || (cVar1 != '\0')) {
        if (cVar1 == '\x04') goto LAB_0004456c;
        if (cVar1 == '\x13') {
          bVar3 = ((byte)pcVar7[0xb] >> 1) + 0x13;
          goto LAB_0004461c;
        }
        if (cVar1 != '\'') {
          if (cVar1 == '7') {
            if (pcVar7[8] != '\x02') goto LAB_00044a5c;
          }
          else {
            if (cVar1 == 'C') {
              if ((byte)pcVar7[0xb] >> 1 == 0) goto LAB_00044a5c;
              bVar3 = ((byte)pcVar7[0xb] >> 1) + 0x42;
            }
            else if (cVar1 == 'R') {
              bVar3 = 0x52;
            }
            else {
              if (cVar1 != 'j') {
                if ((cVar1 == '\v') || (cVar1 == '\0')) {
LAB_0004456c:
                  if ((byte)pcVar7[0xb] >> 1 != 0) goto LAB_00044a0e;
                }
                else if (cVar1 == -0x7d) {
                  if (pcVar7[0xb] != '\x10') goto LAB_0004464c;
                }
                else {
                  if (cVar1 == -0x7e) goto LAB_00044a0e;
                  if ((cVar1 == '\x17') || (cVar1 == '\x18')) {
                    if (pcVar7[0xb] == '\x06') goto LAB_00044a0e;
                  }
                  else if (cVar1 == '=') goto LAB_0004456c;
                }
                goto LAB_00044a5c;
              }
LAB_0004464c:
              bVar3 = cVar1 + pcVar7[0xb];
            }
LAB_0004461c:
            *(undefined2 *)(unaff_A5 + 0x2ac) =
                 *(undefined2 *)(&actor_hurtbox_extent_table_44ce0 + (short)((ushort)bVar3 * 4));
            *(undefined2 *)(unaff_A5 + 0x2ae) =
                 *(undefined2 *)(&DAT_00044ce2 + (short)((ushort)bVar3 * 4));
          }
        }
LAB_00044a0e:
        sVar2 = FUN_00044930();
        if (sVar2 != 0) {
          if ((pcVar7[3] == '\0') ||
             ((((cVar1 = pcVar7[5], cVar1 != '\x15' && (cVar1 != '\x17')) && (cVar1 != '\x1b')) &&
              ((cVar1 != '\x1c' && (cVar1 != '\x1e')))))) {
            if (*(ushort *)(unaff_A5 + 0x21e) < 4) {
              *puVar4 = 1;
              puVar4[2] = *(undefined2 *)(pcVar7 + 0x16);
              puVar4[3] = *(undefined2 *)(pcVar7 + 0x1a);
              *(undefined1 *)(puVar4 + 1) = 1;
              *(char *)((int)puVar4 + 3) = pcVar7[0x29];
              FUN_0004498c();
              FUN_000448d8();
              FUN_000447ce();
              *(short *)(unaff_A5 + 0x21e) = *(short *)(unaff_A5 + 0x21e) + 1;
              puVar4 = puVar4 + 4;
            }
          }
          else {
            *(undefined2 *)(unaff_A5 + 0x242) = 1;
            *(undefined2 *)(unaff_A5 + 0x24a) = *(undefined2 *)(unaff_A5 + 0x2ac);
            *(undefined2 *)(unaff_A5 + 0x24c) = *(undefined2 *)(unaff_A5 + 0x2ae);
            *(undefined2 *)(unaff_A5 + 0x246) = *(undefined2 *)(pcVar7 + 0x16);
            *(undefined2 *)(unaff_A5 + 0x248) = *(undefined2 *)(pcVar7 + 0x1a);
            *(ushort *)(unaff_A5 + 0x244) = (ushort)(byte)pcVar7[5];
          }
        }
      }
    }
LAB_00044a5c:
    pcVar7 = pcVar7 + 0x40;
    *(short *)(unaff_A5 + 0x214) = *(short *)(unaff_A5 + 0x214) + 1;
  } while (*(short *)(unaff_A5 + 0x214) != 0x1d);
  if (*(short *)(&DAT_000012fa + unaff_A5) == 4) {
    *(undefined2 *)(unaff_A5 + 0x28c) = 0x10;
    *(undefined2 *)(unaff_A5 + 0x28e) = 0xf808;
    psVar6 = (short *)(&DAT_00001338 + unaff_A5);
    *(undefined2 *)(unaff_A5 + 0x21e) = 0;
    *(undefined2 *)(unaff_A5 + 0x290) = 0;
    do {
      if (*psVar6 != 0xff) {
        *(short *)(unaff_A5 + 0x290) = *(short *)(unaff_A5 + 0x290) + 1;
        pcVar7 = (char *)(unaff_A5 + 0x2c8);
        *(undefined2 *)(unaff_A5 + 0x214) = 0;
        do {
          if ((((*pcVar7 != '\0') && (pcVar7[5] != '\0')) &&
              ((pcVar7[0x3d] == '\0' &&
               (((*(short *)(unaff_A5 + 0x214) != 9 && (pcVar7[3] == '\0')) &&
                (pcVar7[0x3e] != '\f')))))) && (pcVar7[6] != '\f')) {
            actor_hurtbox_selector_446bc();
            sVar2 = FUN_00044c60();
            if (sVar2 != 0) {
              *psVar6 = 0xff;
              FUN_00044804();
            }
          }
          pcVar7 = pcVar7 + 0x40;
          *(short *)(unaff_A5 + 0x214) = *(short *)(unaff_A5 + 0x214) + 1;
        } while (*(short *)(unaff_A5 + 0x214) != 0x1d);
      }
      psVar6 = psVar6 + 4;
      *(short *)(unaff_A5 + 0x21e) = *(short *)(unaff_A5 + 0x21e) + 1;
    } while (*(short *)(unaff_A5 + 0x21e) != 3);
    if (*(short *)(unaff_A5 + 0x290) != 0) {
      return;
    }
  }
  if (*(short *)(&DAT_000012f8 + unaff_A5) == 1) {
    *(undefined2 *)(unaff_A5 + 0x21e) = 0;
    puVar4 = (undefined2 *)(&DAT_000012c8 + unaff_A5);
    pcVar7 = (char *)(unaff_A5 + 0x2c8);
    *(undefined2 *)(unaff_A5 + 0x214) = 0;
    do {
      if (((*pcVar7 != '\0') && (pcVar7[5] != '\0')) &&
         ((pcVar7[0x3d] == '\0' && (*(ushort *)(unaff_A5 + 0x214) != 9)))) {
        if (*(ushort *)(unaff_A5 + 0x214) < 9) {
          if ((pcVar7[3] == '\0') || (pcVar7[0xd] == 'H')) goto LAB_00044ad6;
        }
        else {
          bVar3 = pcVar7[6];
          if ((bVar3 == 3) || (((7 < bVar3 && (bVar3 != 0xf)) && (bVar3 != 0x16)))) {
LAB_00044ad6:
            actor_hurtbox_selector_446bc();
            sVar2 = player_attack_overlap_entry_44c5a();
            if ((sVar2 != 0) && (*(ushort *)(unaff_A5 + 0x21e) < 4)) {
              *puVar4 = 1;
              FUN_0004495a();
              puVar4[2] = *(undefined2 *)(pcVar7 + 0x16);
              puVar4[3] = *(undefined2 *)(pcVar7 + 0x1a);
              *(short *)(unaff_A5 + 0x21e) = *(short *)(unaff_A5 + 0x21e) + 1;
              puVar4 = puVar4 + 4;
              FUN_00044804();
            }
          }
        }
      }
      pcVar7 = pcVar7 + 0x40;
      *(short *)(unaff_A5 + 0x214) = *(short *)(unaff_A5 + 0x214) + 1;
    } while (*(short *)(unaff_A5 + 0x214) != 0x1d);
  }
  pcVar7 = (char *)(unaff_A5 + 0x2c8);
  *(undefined2 *)(unaff_A5 + 0x214) = 0;
  do {
    if (((*pcVar7 != '\0') && (pcVar7[0x22] != '\0')) && (pcVar7[0x3d] == '\0')) {
      FUN_000447a6();
      sVar2 = FUN_00044c6c();
      if (sVar2 != 0) {
        *(undefined2 *)(&DAT_000012a8 + unaff_A5) = 1;
        (&DAT_000012aa)[unaff_A5] = 0;
        (&DAT_000012ab)[unaff_A5] = pcVar7[0x28];
        *(undefined2 *)(&DAT_000012ac + unaff_A5) = *(undefined2 *)(pcVar7 + 0x16);
        *(undefined2 *)(&DAT_000012ae + unaff_A5) = *(undefined2 *)(pcVar7 + 0x1a);
        if (*(byte *)(unaff_A5 + 0x118) < 5) {
          FUN_000433ac();
        }
        pcVar7[0x22] = '\0';
        return;
      }
    }
    pcVar7 = pcVar7 + 0x40;
    *(short *)(unaff_A5 + 0x214) = *(short *)(unaff_A5 + 0x214) + 1;
  } while (*(short *)(unaff_A5 + 0x214) != 0x12);
  return;
}



/* ===== arcade_pc 0x044C5A player_attack_overlap_entry_44c5a ===== */

void player_attack_overlap_entry_44c5a(void)

{
  short sVar1;
  
  sVar1 = signed_interval_overlap_44cba();
  if (sVar1 != 0) {
    signed_interval_overlap_44cba();
  }
  return;
}



/* ===== arcade_pc 0x044C60 FUN_00044c60 ===== */

void FUN_00044c60(void)

{
  short sVar1;
  
  sVar1 = signed_interval_overlap_44cba();
  if (sVar1 != 0) {
    signed_interval_overlap_44cba();
  }
  return;
}



/* ===== arcade_pc 0x044C66 FUN_00044c66 ===== */

void FUN_00044c66(void)

{
  short sVar1;
  
  sVar1 = signed_interval_overlap_44cba();
  if (sVar1 != 0) {
    signed_interval_overlap_44cba();
  }
  return;
}



/* ===== arcade_pc 0x044C6C FUN_00044c6c ===== */

void FUN_00044c6c(void)

{
  short sVar1;
  
  sVar1 = signed_interval_overlap_44cba();
  if (sVar1 != 0) {
    signed_interval_overlap_44cba();
  }
  return;
}



/* ===== arcade_pc 0x044C72 FUN_00044c72 ===== */

void FUN_00044c72(void)

{
  short sVar1;
  
  sVar1 = signed_interval_overlap_44cba();
  if (sVar1 != 0) {
    signed_interval_overlap_44cba();
  }
  return;
}



/* ===== arcade_pc 0x044CBA signed_interval_overlap_44cba ===== */

undefined4 signed_interval_overlap_44cba(void)

{
  undefined4 uVar1;
  short in_D1w;
  short unaff_D4w;
  char *in_A0;
  char *in_A1;
  
  uVar1 = 0;
  if (((ushort)(unaff_D4w + *in_A1) <= (ushort)(in_D1w + in_A0[1])) &&
     ((ushort)(in_D1w + *in_A0) <= (ushort)(in_A1[1] + unaff_D4w))) {
    uVar1 = 1;
  }
  return uVar1;
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



/* ===== arcade_pc 0x045342 paired_actor_init_45342 ===== */

void paired_actor_init_45342(void)

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
    paired_actor_activate_453a2();
    FUN_000453c0();
    *(byte *)(unaff_A5 + 0x56f) = *(byte *)(unaff_A5 + 0x56f) | 0x80;
    paired_actor_activate_453a2();
    FUN_000453c0();
    FUN_0003a0ec();
    return;
  }
  return;
}



/* ===== arcade_pc 0x0453A2 paired_actor_activate_453a2 ===== */

void paired_actor_activate_453a2(void)

{
  undefined1 *unaff_A4;
  
  *(undefined2 *)(unaff_A4 + 0x1c) = 1;
  *unaff_A4 = 1;
  unaff_A4[5] = 3;
  *(undefined2 *)(unaff_A4 + 0x1a) = 0x180;
  actor_record_loader_4543e();
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



/* ===== arcade_pc 0x045418 FUN_00045418 ===== */

void FUN_00045418(void)

{
  int unaff_A4;
  
  *(undefined *)(unaff_A4 + 0x29) = (&DAT_0004542e)[(short)(*(byte *)(unaff_A4 + 5) - 0x13)];
  return;
}



/* ===== arcade_pc 0x04543E actor_record_loader_4543e ===== */

void actor_record_loader_4543e(void)

{
  int iVar1;
  int unaff_A4;
  
  iVar1 = (int)(short)((*(byte *)(unaff_A4 + 6) - 8) * 8);
  *(undefined2 *)(unaff_A4 + 0x1e) = *(undefined2 *)(&actor_record_table_45592 + iVar1);
  *(undefined1 *)(unaff_A4 + 0x3a) = *(undefined1 *)(iVar1 + 0x45594);
  *(undefined1 *)(unaff_A4 + 1) = *(undefined1 *)(iVar1 + 0x45595);
  *(undefined2 *)(unaff_A4 + 0x28) = *(undefined2 *)(iVar1 + 0x45596);
  *(undefined2 *)(unaff_A4 + 0x2c) = *(undefined2 *)(iVar1 + 0x45598);
  FUN_000453d6();
  return;
}



/* ===== arcade_pc 0x04544E FUN_0004544e ===== */

void FUN_0004544e(void)

{
  undefined *puVar1;
  undefined2 *puVar2;
  int unaff_A4;
  
  if (*(char *)(unaff_A4 + 0x3e) == '\x02') {
    puVar1 = &DAT_000454ba;
    if ((*(char *)(unaff_A4 + 0x38) != '\0') &&
       (puVar1 = &DAT_000454d2, *(char *)(unaff_A4 + 0x38) != '\x03')) {
      puVar1 = &DAT_000454ea;
    }
    puVar2 = (undefined2 *)(puVar1 + (short)((ushort)*(byte *)(unaff_A4 + 0x752) << 3));
  }
  else {
    puVar1 = &DAT_00045502;
    if (*(char *)(unaff_A4 + 0x752) != '\0') {
      puVar1 = &DAT_00045562;
    }
    puVar2 = (undefined2 *)(puVar1 + (short)((ushort)*(byte *)(unaff_A4 + 0x3e) << 3));
  }
  *(undefined2 *)(unaff_A4 + 0x1e) = *puVar2;
  *(undefined1 *)(unaff_A4 + 0x3a) = *(undefined1 *)(puVar2 + 1);
  *(undefined *)(unaff_A4 + 1) = *(undefined *)((int)puVar2 + 3);
  *(undefined2 *)(unaff_A4 + 0x28) = puVar2[2];
  *(undefined2 *)(unaff_A4 + 0x2c) = puVar2[3];
  FUN_000453d6();
  return;
}



/* ===== arcade_pc 0x045684 FUN_00045684 ===== */

void FUN_00045684(void)

{
  byte bVar1;
  undefined *puVar2;
  byte *pbVar3;
  int unaff_A4;
  int unaff_A5;
  
  if (*(char *)(unaff_A4 + 0x3e) == '\x02') {
    bVar1 = *(byte *)(unaff_A4 + 0x38);
    if (2 < bVar1) {
      bVar1 = bVar1 - 2;
    }
    pbVar3 = &DAT_000456ec +
             (int)(short)(ushort)bVar1 +
             (int)(short)((*(byte *)(unaff_A5 + 0x118) - 1) * 3) +
             (int)(short)((ushort)*(byte *)(unaff_A4 + 0x752) * 0x12);
  }
  else {
    puVar2 = &DAT_00045722;
    if (*(short *)(unaff_A5 + 0x2a2) != 0) {
      puVar2 = &DAT_0004576a;
    }
    pbVar3 = puVar2 + (int)(short)(ushort)*(byte *)(unaff_A4 + 0x3e) +
                      (int)(short)((*(byte *)(unaff_A5 + 0x118) - 1) * 0xc);
  }
  *(byte *)(unaff_A4 + 0x27) = *pbVar3 | 0x40 | *(byte *)(unaff_A4 + 0x27);
  return;
}



/* ===== arcade_pc 0x045AA0 FUN_00045aa0 ===== */

void FUN_00045aa0(void)

{
  int unaff_A4;
  
  *(undefined2 *)(unaff_A4 + 0x1a) = 0x1f0;
  *(undefined1 *)(unaff_A4 + 6) = 0xd;
  actor_record_loader_4543e();
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
  actor_record_loader_4543e();
  FUN_00045cfc();
  FUN_00045be8();
  FUN_0004092e();
  *(char *)(unaff_A5 + 0x9e9) = (char)*(undefined2 *)(unaff_A5 + 0x200) + '\x01';
  *(undefined1 *)(unaff_A5 + 0x9ce) = 0xb;
  actor_record_loader_4543e();
  FUN_00045cfc();
  FUN_00045be8();
  if (3 < *(byte *)(unaff_A5 + 0x118)) {
    FUN_0004092e();
    *(char *)(unaff_A5 + 0x9a9) = (char)*(undefined2 *)(unaff_A5 + 0x200) + '\x02';
    *(undefined1 *)(unaff_A5 + 0x98e) = 0xb;
    actor_record_loader_4543e();
    FUN_00045cfc();
    FUN_00045be8();
    if (5 < *(byte *)(unaff_A5 + 0x118)) {
      FUN_0004092e();
      *(char *)(unaff_A5 + 0x969) = (char)*(undefined2 *)(unaff_A5 + 0x200) + '\x03';
      *(undefined1 *)(unaff_A5 + 0x94e) = 0xb;
      actor_record_loader_4543e();
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
  actor_record_loader_4543e();
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



/* ===== arcade_pc 0x045D10 actor_map_collision_variant_45d10 ===== */

undefined4 actor_map_collision_variant_45d10(void)

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
  collision_map_lookup_53a2e();
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
    if (puVar4 < &collision_map_64x64_words_base) {
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
      actor_family0_render_3d054();
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
      actor_family0_render_3d054();
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
      actor_family0_render_3d054();
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



/* ===== arcade_pc 0x04736A actor_map_collision_variant_4736a ===== */

void actor_map_collision_variant_4736a(void)

{
  undefined2 *extraout_A0;
  int unaff_A4;
  
  if ((*(char *)(unaff_A4 + 7) == '\0') && (*(byte *)(unaff_A4 + 5) < 0xd)) {
    collision_map_lookup_53a2e();
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
  actor_four_record_expand_3c902();
  return;
}



/* ===== arcade_pc 0x04A086 FUN_0004a086 ===== */

void FUN_0004a086(void)

{
  ushort uVar1;
  byte bVar2;
  undefined1 *in_A0;
  undefined1 *unaff_A4;
  
  unaff_A4[4] = *in_A0;
  unaff_A4[0x3e] = in_A0[1];
  bVar2 = in_A0[2];
  unaff_A4[0x38] = bVar2 & 0xf;
  unaff_A4[0x752] = bVar2 >> 4;
  unaff_A4[0x36] = in_A0[3];
  uVar1 = *(ushort *)(in_A0 + 4);
  if ((uVar1 & 1) != 0) {
    unaff_A4[0x2a] = 1;
  }
  *(ushort *)(unaff_A4 + 0x1c) = uVar1 & 0xfffe;
  *(undefined2 *)(unaff_A4 + 0x34) = *(undefined2 *)(in_A0 + 6);
  *unaff_A4 = 1;
  *(undefined2 *)(unaff_A4 + 0x1a) = 0x180;
  FUN_0004544e();
  FUN_00045684();
  return;
}



/* ===== arcade_pc 0x04A0D8 FUN_0004a0d8 ===== */

void FUN_0004a0d8(void)

{
  FUN_0004a086();
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
  actor_record_loader_4543e();
  FUN_00045cfc();
  return;
}



/* ===== arcade_pc 0x051090 player_main_update_51090 ===== */

void player_main_update_51090(void)

{
  int unaff_A5;
  
  FUN_00052732();
  FUN_00055650();
  FUN_00055ad6();
  FUN_00059de8();
  FUN_000512c8();
  collision_map_surface_postprocess_5a29c();
  FUN_000596f4();
  FUN_00051156();
  FUN_0005122a();
  *(short *)(&DAT_00001308 + unaff_A5) = *(short *)(&DAT_00001308 + unaff_A5) + 1;
  return;
}



/* ===== arcade_pc 0x0510C6 FUN_000510c6 ===== */

void FUN_000510c6(void)

{
  return;
}



/* ===== arcade_pc 0x05113A FUN_0005113a ===== */

void FUN_0005113a(void)

{
  int unaff_A5;
  
  if ((0x73 < *(ushort *)(unaff_A5 + 0x13e)) && (*(ushort *)(unaff_A5 + 0x13e) < 0x84)) {
    *(undefined2 *)(&DAT_00001414 + unaff_A5) = 1;
    *(undefined2 *)(&DAT_00001416 + unaff_A5) = 0;
  }
  return;
}



/* ===== arcade_pc 0x051156 FUN_00051156 ===== */

void FUN_00051156(void)

{
  int unaff_A5;
  
  if (*(short *)(&DAT_00001414 + unaff_A5) == 1) {
    FUN_00051190();
    *(short *)(&DAT_00001416 + unaff_A5) = *(short *)(&DAT_00001416 + unaff_A5) + 1;
    if (*(short *)(&DAT_00001416 + unaff_A5) == 0x70) {
      *(undefined2 *)(&DAT_000013b0 + unaff_A5) = 1;
    }
    else if (*(short *)(&DAT_00001416 + unaff_A5) == 0x300) {
      *(undefined2 *)(&DAT_00001416 + unaff_A5) = 0;
      *(undefined2 *)(&DAT_00001414 + unaff_A5) = 0xff;
    }
  }
  else {
    FUN_0005113a();
  }
  return;
}



/* ===== arcade_pc 0x051190 FUN_00051190 ===== */

void FUN_00051190(void)

{
  int unaff_A5;
  
  if (*(short *)(&DAT_00001416 + unaff_A5) == 1) {
    FUN_0003a0ec();
  }
  else if (*(short *)(&DAT_00001416 + unaff_A5) == 0x50) {
    FUN_00059ad4();
    FUN_00059ad4();
  }
  return;
}



/* ===== arcade_pc 0x05122A FUN_0005122a ===== */

void FUN_0005122a(void)

{
  int unaff_A5;
  
  if ((*(short *)(&DAT_00001360 + unaff_A5) == 1) && (*(short *)(&DAT_000013ac + unaff_A5) == 8)) {
    if (*(short *)((int)&PTR_DAT_000013ba + unaff_A5) == 0x80) {
      *(undefined2 *)(&DAT_000010e8 + unaff_A5) = 0x10;
      FUN_0003a116();
      player_sprite_slot_init_54052();
      FUN_00059f5e();
    }
    else if (*(short *)(&DAT_000012f4 + unaff_A5) == 0) {
      *(short *)((int)&PTR_DAT_000013ba + unaff_A5) =
           *(short *)((int)&PTR_DAT_000013ba + unaff_A5) + 1;
    }
  }
  return;
}



/* ===== arcade_pc 0x0512C8 FUN_000512c8 ===== */

void FUN_000512c8(void)

{
  int unaff_A5;
  
  if ((*(ushort *)(&DAT_000010d0 + unaff_A5) & 0x10) != 0) {
    FUN_00053934();
  }
  if ((*(ushort *)(&DAT_000010d0 + unaff_A5) & 0x20) != 0) {
    FUN_000538c8();
  }
  if ((*(ushort *)(&DAT_000010d0 + unaff_A5) & 0x40) != 0) {
    FUN_000539a0();
  }
  if (((*(ushort *)(&DAT_000010d0 + unaff_A5) & 0x80) != 0) &&
     (0x20 < *(ushort *)(&DAT_000010be + unaff_A5))) {
    FUN_00053a0c();
  }
  return;
}



/* ===== arcade_pc 0x051CA0 player_attack_initialize_51ca0 ===== */

void player_attack_initialize_51ca0(void)

{
  int unaff_A5;
  
  if ((DAT_0010d37a & 4) == 0) {
    *(undefined2 *)((int)&PTR_DAT_00001116 + unaff_A5) = 4;
    *(undefined2 *)(&DAT_00001114 + unaff_A5) = 2;
  }
  else if ((DAT_0010d37a & 8) == 0) {
    *(undefined2 *)((int)&PTR_DAT_00001116 + unaff_A5) = 4;
    *(undefined2 *)(&DAT_00001114 + unaff_A5) = 3;
  }
  else {
    if (((*(short *)(&DAT_000010e8 + unaff_A5) != 4) && (*(short *)(&DAT_000010e8 + unaff_A5) != 6))
       && (*(short *)(&DAT_000010e8 + unaff_A5) != 9)) {
      if ((DAT_0010d37a & 1) == 0) {
        *(undefined2 *)((int)&PTR_DAT_00001116 + unaff_A5) = 0;
        goto LAB_00051d20;
      }
      if (((*(short *)(&DAT_000010e8 + unaff_A5) == 2) ||
          (*(short *)(&DAT_000010e8 + unaff_A5) == 3)) && ((DAT_0010d37a & 2) == 0)) {
        *(undefined2 *)((int)&PTR_DAT_00001116 + unaff_A5) = 1;
        goto LAB_00051d20;
      }
    }
    *(undefined2 *)((int)&PTR_DAT_00001116 + unaff_A5) = 4;
  }
LAB_00051d20:
  *(undefined2 *)((int)&PTR_DAT_0000110c + unaff_A5) = 1;
  *(undefined2 *)(&DAT_0000110a + unaff_A5) = 0;
  *(undefined2 *)(&DAT_00001108 + unaff_A5) = 1;
  return;
}



/* ===== arcade_pc 0x051D32 player_attack_advance_51d32 ===== */

void player_attack_advance_51d32(void)

{
  short sVar1;
  int unaff_A5;
  
  if (((*(short *)(&DAT_000010e8 + unaff_A5) == 9) || (*(short *)(&DAT_000010e8 + unaff_A5) == 4))
     || (*(short *)(&DAT_000010e8 + unaff_A5) == 6)) {
    if (*(short *)((int)&PTR_DAT_00001116 + unaff_A5) != 4) goto LAB_00051d98;
  }
  else if (*(short *)(&DAT_000010e8 + unaff_A5) == 5) {
    *(undefined2 *)((int)&PTR_DAT_00001116 + unaff_A5) = 4;
  }
  sVar1 = *(short *)(&DAT_0000110a + unaff_A5);
  if (sVar1 == 0xb) {
    *(undefined2 *)(&DAT_000012a0 + unaff_A5) = 1;
    sVar1 = FUN_00051dae();
  }
  else {
    *(undefined2 *)(&DAT_000012a0 + unaff_A5) = 0xff;
  }
  *(short *)(&DAT_0000110a + unaff_A5) = sVar1 + 1;
  if ((short)(sVar1 + 1) != *(short *)(&DAT_00001390 + unaff_A5)) {
    return;
  }
  if ((*(short *)((int)&PTR_DAT_00001116 + unaff_A5) == 1) &&
     (*(short *)(&DAT_000010e8 + unaff_A5) == 3)) {
    *(short *)(&DAT_0000110a + unaff_A5) = *(short *)(&DAT_0000110a + unaff_A5) + -1;
    return;
  }
LAB_00051d98:
  *(undefined2 *)(&DAT_00001108 + unaff_A5) = 0xff;
  return;
}



/* ===== arcade_pc 0x051DAE FUN_00051dae ===== */

void FUN_00051dae(void)

{
  short sVar1;
  short *psVar2;
  int unaff_A5;
  
  if (*(short *)(&DAT_000012fa + unaff_A5) == 4) {
    sVar1 = 3;
    for (psVar2 = &DAT_0010d338; *psVar2 != 0xff; psVar2 = psVar2 + 4) {
      sVar1 = sVar1 + -1;
      if (sVar1 == 0) {
        return;
      }
    }
    if (*(short *)((int)&PTR_DAT_00001116 + unaff_A5) == 1) {
      *psVar2 = 1;
    }
    else if (*(short *)((int)&PTR_DAT_00001116 + unaff_A5) == 0) {
      *psVar2 = 0;
    }
    else if (*(short *)(&DAT_00001114 + unaff_A5) == 2) {
      *psVar2 = 2;
    }
    else {
      *psVar2 = 3;
    }
    psVar2[2] = DAT_0010d1b4;
    psVar2[1] = DAT_0010d1b8;
    psVar2[3] = 0;
  }
  return;
}



/* ===== arcade_pc 0x051E24 player_crouch_enter_51e24 ===== */

void player_crouch_enter_51e24(void)

{
  int unaff_A5;
  
  *(undefined2 *)(&DAT_000010ea + unaff_A5) = 0;
  *(undefined2 *)(&DAT_000010e8 + unaff_A5) = 5;
  if ((DAT_0010d37a & 4) == 0) {
    *(undefined2 *)(&DAT_00001114 + unaff_A5) = 2;
  }
  else if ((DAT_0010d37a & 8) == 0) {
    *(undefined2 *)(&DAT_00001114 + unaff_A5) = 3;
  }
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



/* ===== arcade_pc 0x052732 FUN_00052732 ===== */

void FUN_00052732(void)

{
  int unaff_A5;
  
  *(undefined2 *)(&DAT_000010d0 + unaff_A5) = 0;
  if (*(short *)(&DAT_00001296 + unaff_A5) == 1) {
    FUN_00052af6();
    FUN_00052a64();
  }
  FUN_00052a1a();
  if (((*(short *)(&DAT_000010a8 + unaff_A5) == 4) || (*(short *)(&DAT_000010a8 + unaff_A5) == 5))
     || (*(short *)(&DAT_000010a8 + unaff_A5) == 6)) {
    *(undefined2 *)(&DAT_000010e8 + unaff_A5) = 7;
  }
  if (*(short *)(&DAT_00001352 + unaff_A5) == 1) {
    FUN_00052974();
    *(undefined2 *)(&DAT_00001352 + unaff_A5) = 0xff;
  }
  else {
    if ((DAT_0010c016 & 0x20) == 0) {
      FUN_000527d4();
    }
    else {
      FUN_000528ca();
    }
    FUN_0005288c();
    FUN_00052816();
    *(undefined2 *)(&DAT_000012f8 + unaff_A5) = 0xff;
    if (*(short *)(&DAT_000013ca + unaff_A5) == 0x11) {
      FUN_000529cc();
    }
    if (*(short *)(unaff_A5 + 0x13a) == 0) {
      *(undefined2 *)(unaff_A5 + 2) = 4;
      *(undefined2 *)(unaff_A5 + 4) = 0;
    }
    *(short *)(unaff_A5 + 0x13a) = *(short *)(unaff_A5 + 0x13a) + -2;
    *(undefined2 *)(&DAT_000012fc + unaff_A5) = 1;
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

undefined * FUN_0005283e(void)

{
  short in_D1w;
  short unaff_D2w;
  int unaff_A5;
  
  return &collision_map_64x64_words_base +
         ((uint)((int)(short)((unaff_D2w +
                               ((*(ushort *)(&DAT_000010b0 + unaff_A5) ^ 0x1ff) + 1 & 0x1ff) & 0x1f8
                              ) << 5) +
                (int)(short)(((ushort)(in_D1w + ((*(ushort *)(&DAT_000010ae + unaff_A5) ^ 0x1ff) + 1
                                                & 0x1ff)) >> 1) + 8 & 0xfc)) >> 1);
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



/* ===== arcade_pc 0x052A1A FUN_00052a1a ===== */

void FUN_00052a1a(void)

{
  int unaff_A5;
  
  if ((DAT_0010d37a & 0x10) == 0) {
    if (*(short *)(&DAT_000013c8 + unaff_A5) == 0xff) {
      *(undefined2 *)(&DAT_000013ca + unaff_A5) = 0x11;
    }
    else {
      *(undefined2 *)(&DAT_000013ca + unaff_A5) = 1;
    }
    *(undefined2 *)(&DAT_000013c8 + unaff_A5) = 1;
  }
  else {
    if (*(short *)(&DAT_000013c8 + unaff_A5) == 1) {
      *(undefined2 *)(&DAT_000013ca + unaff_A5) = 0xfe;
    }
    else {
      *(undefined2 *)(&DAT_000013ca + unaff_A5) = 0xff;
    }
    *(undefined2 *)(&DAT_000013c8 + unaff_A5) = 0xff;
  }
  return;
}



/* ===== arcade_pc 0x052A64 FUN_00052a64 ===== */

void FUN_00052a64(void)

{
  int unaff_A5;
  
  if (*(short *)(&DAT_00001298 + unaff_A5) == 1) {
    *(undefined2 *)(&DAT_0000129c + unaff_A5) = DAT_0010d1b4;
    *(undefined2 *)(&DAT_0000129a + unaff_A5) = DAT_0010d1b8;
  }
  if (*(short *)(&DAT_0000129e + unaff_A5) == 1) {
    FUN_00052aa2();
  }
  else {
    FUN_00052aa2();
  }
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
  puVar2 = (undefined2 *)(&player_aux_piece_table_5da5e + (short)(in_D0w * 0x18));
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



/* ===== arcade_pc 0x052AF6 FUN_00052af6 ===== */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_00052af6(void)

{
  int unaff_A5;
  
  if (*(short *)(&DAT_0000129e + unaff_A5) == 1) {
    if (*(short *)(&DAT_00001298 + unaff_A5) == 0xc) {
      _DAT_0010d296 = 0xff;
    }
    else {
      *(short *)(&DAT_00001298 + unaff_A5) = *(short *)(&DAT_00001298 + unaff_A5) + 1;
    }
  }
  else if (*(short *)(&DAT_00001298 + unaff_A5) == 0x14) {
    _DAT_0010d296 = 0xff;
  }
  else {
    *(short *)(&DAT_00001298 + unaff_A5) = *(short *)(&DAT_00001298 + unaff_A5) + 1;
  }
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



/* ===== arcade_pc 0x0539A0 FUN_000539a0 ===== */

void FUN_000539a0(void)

{
  short unaff_D6w;
  int unaff_A5;
  
  if (*(ushort *)(&DAT_000010be + unaff_A5) < 0x130) {
    *(short *)(&DAT_000010be + unaff_A5) = unaff_D6w + *(short *)(&DAT_000010be + unaff_A5);
  }
  return;
}



/* ===== arcade_pc 0x053A0C FUN_00053a0c ===== */

void FUN_00053a0c(void)

{
  short unaff_D6w;
  int unaff_A5;
  
  if (0x20 < *(ushort *)(&DAT_000010be + unaff_A5)) {
    *(short *)(&DAT_000010be + unaff_A5) = *(short *)(&DAT_000010be + unaff_A5) - unaff_D6w;
  }
  return;
}



/* ===== arcade_pc 0x053A2E collision_map_lookup_53a2e ===== */

ushort collision_map_lookup_53a2e(void)

{
  short in_D1w;
  short unaff_D2w;
  int unaff_A5;
  
  return (ushort)((unaff_D2w + ((*(ushort *)(&DAT_000010b0 + unaff_A5) ^ 0x1ff) + 1 & 0x1ff) & 0x1f8
                  ) * 0x20 +
                 (((ushort)(in_D1w + ((*(ushort *)(&DAT_000010ae + unaff_A5) ^ 0x1ff) + 1 & 0x1ff))
                  >> 1) + 8 & 0xfc)) >> 1;
}



/* ===== arcade_pc 0x053A6E player_collision_probe_family_53a6e ===== */

void player_collision_probe_family_53a6e(void)

{
  ushort *extraout_A0;
  ushort *extraout_A0_00;
  ushort *extraout_A0_01;
  ushort *puVar1;
  int unaff_A5;
  
  *(ushort *)(&DAT_000010ce + unaff_A5) = *(ushort *)(&DAT_000010ce + unaff_A5) & 0xffdd;
  collision_map_lookup_53a2e();
  puVar1 = extraout_A0;
  if ((*extraout_A0 & 0x7f) == 2) {
LAB_00053b22:
    *(ushort *)(&DAT_000010ce + unaff_A5) = *(ushort *)(&DAT_000010ce + unaff_A5) | 0x20;
    *(ushort **)(&DAT_0000111c + unaff_A5) = puVar1;
  }
  else {
    if ((*extraout_A0 & 0x7f) != 1) {
      collision_map_lookup_53a2e();
      puVar1 = extraout_A0_00;
      if ((*extraout_A0_00 & 0x7f) == 2) goto LAB_00053b22;
      if ((*extraout_A0_00 & 0x7f) != 1) {
        collision_map_lookup_53a2e();
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



/* ===== arcade_pc 0x053B34 player_ground_contact_probe_family_53b34 ===== */

void player_ground_contact_probe_family_53b34(void)

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
  collision_map_lookup_53a2e();
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
    collision_map_lookup_53a2e();
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
      collision_map_lookup_53a2e();
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



/* ===== arcade_pc 0x054052 player_sprite_slot_init_54052 ===== */

void player_sprite_slot_init_54052(void)

{
  short sVar1;
  undefined2 *puVar2;
  undefined2 *puVar3;
  
  puVar2 = &DAT_0010d1d2;
  sVar1 = 6;
  do {
    *puVar2 = 3;
    puVar2[1] = 0;
    puVar3 = puVar2 + 3;
    puVar2[2] = 0;
    puVar2 = puVar2 + 4;
    *puVar3 = 0;
    sVar1 = sVar1 + -1;
  } while (sVar1 != 0);
  sVar1 = 4;
  puVar2 = &DAT_0010d1b2;
  do {
    *puVar2 = 3;
    puVar2[1] = 0;
    puVar3 = puVar2 + 3;
    puVar2[2] = 0;
    puVar2 = puVar2 + 4;
    *puVar3 = 0;
    sVar1 = sVar1 + -1;
  } while (sVar1 != 0);
  puVar2 = &DAT_0010d1f2;
  sVar1 = 6;
  do {
    *puVar2 = 3;
    puVar2[1] = 0;
    puVar3 = puVar2 + 3;
    puVar2[2] = 0;
    puVar2 = puVar2 + 4;
    *puVar3 = 0;
    sVar1 = sVar1 + -1;
  } while (sVar1 != 0);
  puVar2 = &PC090OJ_sprite_RAM_d00000;
  sVar1 = 4;
  do {
    *puVar2 = 3;
    puVar2[1] = 0;
    puVar3 = puVar2 + 3;
    puVar2[2] = 0;
    puVar2 = puVar2 + 4;
    *puVar3 = 0;
    sVar1 = sVar1 + -1;
  } while (sVar1 != 0);
  return;
}



/* ===== arcade_pc 0x0540AC FUN_000540ac ===== */

void FUN_000540ac(void)

{
  short sVar1;
  undefined2 *puVar2;
  undefined2 *puVar3;
  
  puVar2 = &PC090OJ_sprite_RAM_d00000;
  sVar1 = 4;
  do {
    *puVar2 = 3;
    puVar2[1] = 0;
    puVar3 = puVar2 + 3;
    puVar2[2] = 0;
    puVar2 = puVar2 + 4;
    *puVar3 = 0;
    sVar1 = sVar1 + -1;
  } while (sVar1 != 0);
  return;
}



/* ===== arcade_pc 0x0540CC player_body_constructor_540cc ===== */

void player_body_constructor_540cc(void)

{
  short sVar1;
  undefined2 *puVar2;
  int unaff_A5;
  
  if (*(short *)(&DAT_000010e8 + unaff_A5) == 7) {
    sVar1 = 0x18;
    puVar2 = &DAT_0010d1d2;
    do {
      *puVar2 = 0;
      sVar1 = sVar1 + -1;
      puVar2 = puVar2 + 1;
    } while (sVar1 != 0);
    sVar1 = 0x18;
    puVar2 = &DAT_0010d1f2;
    do {
      *puVar2 = 0;
      sVar1 = sVar1 + -1;
      puVar2 = puVar2 + 1;
    } while (sVar1 != 0);
    sVar1 = 0x10;
    puVar2 = &DAT_0010d1b2;
    do {
      *puVar2 = 0;
      sVar1 = sVar1 + -1;
      puVar2 = puVar2 + 1;
    } while (sVar1 != 0);
  }
  else {
    FUN_00054326();
  }
  return;
}



/* ===== arcade_pc 0x054326 FUN_00054326 ===== */

void FUN_00054326(void)

{
  undefined *unaff_A2;
  int unaff_A3;
  int unaff_A4;
  int unaff_A5;
  
  if (*(short *)(&DAT_000010e8 + unaff_A5) == 8) {
    *(ushort *)(&DAT_00001244 + unaff_A5) =
         (ushort)*(byte *)(unaff_A3 + *(short *)(&DAT_000012f4 + unaff_A5));
    FUN_00054492();
    goto LAB_000543ca;
  }
  if ((*(short *)(&DAT_000010e8 + unaff_A5) != 9) && (*(short *)(&DAT_000012f0 + unaff_A5) == 1)) {
    *(ushort *)(&DAT_00001244 + unaff_A5) =
         (ushort)*(byte *)(unaff_A3 + *(short *)(&DAT_000012f2 + unaff_A5));
    FUN_00054492();
    goto LAB_000543ca;
  }
  if (*(short *)(&DAT_00001108 + unaff_A5) == 1) {
    if (*(short *)((int)&PTR_DAT_00001116 + unaff_A5) != 4) {
      if (*(short *)(&DAT_000010e8 + unaff_A5) == 5) goto LAB_00054346;
      if (*(short *)((int)&PTR_DAT_00001116 + unaff_A5) == 0) {
        unaff_A2 = &player_attack_selector0_table_5bae0;
      }
      else {
        unaff_A2 = &player_attack_selector_nonzero_table_5bb10;
      }
    }
    *(ushort *)(&DAT_00001244 + unaff_A5) =
         (ushort)(byte)unaff_A2[(short)(*(short *)(&DAT_0000110a + unaff_A5) << 1)];
    FUN_00054492();
  }
  else {
LAB_00054346:
    *(ushort *)(&DAT_00001244 + unaff_A5) =
         (ushort)*(byte *)(unaff_A3 + *(short *)(&DAT_000010ea + unaff_A5));
    FUN_00054492();
  }
LAB_000543ca:
  if (*(short *)(&DAT_000010e8 + unaff_A5) == 8) {
    *(ushort *)(&DAT_00001246 + unaff_A5) =
         (ushort)*(byte *)(unaff_A4 + *(short *)(&DAT_000012f4 + unaff_A5));
    FUN_000546a8();
  }
  else if ((*(short *)(&DAT_000010e8 + unaff_A5) == 9) ||
          (*(short *)(&DAT_000012f0 + unaff_A5) != 1)) {
    if ((((*(short *)(&DAT_000010e8 + unaff_A5) == 5) &&
         (*(short *)((int)&PTR_DAT_00001116 + unaff_A5) != 1)) &&
        (*(short *)(&DAT_00001108 + unaff_A5) == 1)) ||
       ((((*(short *)(&DAT_000010e8 + unaff_A5) == 2 || (*(short *)(&DAT_000010e8 + unaff_A5) == 3))
         || (*(short *)(&DAT_000010e8 + unaff_A5) == 0)) &&
        ((*(short *)(&DAT_00001108 + unaff_A5) == 1 &&
         (*(short *)((int)&PTR_DAT_00001116 + unaff_A5) == 1)))))) {
      *(ushort *)(&DAT_00001246 + unaff_A5) =
           (ushort)*(byte *)(unaff_A4 + (short)(*(short *)(&DAT_0000110a + unaff_A5) << 1));
      FUN_000546a8();
    }
    else {
      *(ushort *)(&DAT_00001246 + unaff_A5) =
           (ushort)*(byte *)(unaff_A4 + *(short *)(&DAT_000010ea + unaff_A5));
      FUN_000546a8();
    }
  }
  else {
    *(ushort *)(&DAT_00001246 + unaff_A5) =
         (ushort)*(byte *)(unaff_A4 + *(short *)(&DAT_000012f2 + unaff_A5));
    FUN_000546a8();
  }
  return;
}



/* ===== arcade_pc 0x054492 FUN_00054492 ===== */

void FUN_00054492(void)

{
  ushort uVar1;
  short sVar2;
  short sVar3;
  ushort *puVar4;
  undefined *puVar5;
  ushort *puVar6;
  undefined2 *puVar7;
  undefined2 *puVar8;
  int unaff_A5;
  
  puVar6 = &DAT_0010d1d2;
  sVar3 = *(short *)(&DAT_00001244 + unaff_A5);
  if ((*(short *)(&DAT_000010e8 + unaff_A5) == 9) && (*(short *)(&DAT_00001114 + unaff_A5) == 3)) {
    sVar3 = sVar3 + -1;
  }
  puVar4 = (ushort *)
           (s_________________________00000000_0005bd08 +
           *(short *)(s_________________________00000000_0005bd08 + (short)(sVar3 << 1) + 0x38) +
           0x38);
  sVar3 = 4;
  do {
    if (*puVar4 == 0) {
      *puVar6 = 3;
      puVar6[1] = 0;
      puVar6[2] = 0;
      puVar6[3] = 0;
    }
    else {
      uVar1 = puVar4[2];
      if (*(short *)(&DAT_00001114 + unaff_A5) != 2) {
        uVar1 = uVar1 | 0x4000;
      }
      *puVar6 = uVar1;
      puVar6[1] = *(short *)(&DAT_000010c0 + unaff_A5) + (short)*(char *)((int)puVar4 + 3) + 1U &
                  0x1ff;
      puVar6[2] = *puVar4;
      uVar1 = (ushort)*(char *)(puVar4 + 1);
      if (*(short *)(&DAT_00001114 + unaff_A5) != 2) {
        uVar1 = (uVar1 ^ 0xffff) - 0xf;
      }
      puVar6[3] = *(short *)(&DAT_000010be + unaff_A5) + uVar1 & 0x1ff;
      puVar4 = puVar4 + 3;
    }
    puVar6 = puVar6 + 4;
    sVar3 = sVar3 + -1;
  } while (sVar3 != 0);
  if (*(short *)(&DAT_000012fa + unaff_A5) == 1) {
    puVar5 = &DAT_0005cd8a;
  }
  else if (*(short *)(&DAT_000012fa + unaff_A5) == 4) {
    puVar5 = &DAT_0005d068;
  }
  else if (*(short *)(&DAT_000012fa + unaff_A5) == 2) {
    puVar5 = &DAT_0005d346;
  }
  else {
    if (*(short *)(&DAT_000012fa + unaff_A5) != 3) {
      sVar3 = 4;
      puVar7 = &DAT_0010d1b2;
      do {
        *puVar7 = 3;
        puVar7[1] = 0;
        puVar8 = puVar7 + 3;
        puVar7[2] = 0;
        puVar7 = puVar7 + 4;
        *puVar8 = 0;
        sVar3 = sVar3 + -1;
      } while (sVar3 != 0);
      return;
    }
    puVar5 = &DAT_0005d666;
  }
  sVar3 = *(short *)(&DAT_00001244 + unaff_A5);
  if ((*(short *)(&DAT_000010e8 + unaff_A5) == 9) && (*(short *)(&DAT_00001114 + unaff_A5) == 3)) {
    sVar3 = sVar3 + -1;
  }
  puVar6 = (ushort *)(puVar5 + *(short *)(puVar5 + (short)(sVar3 << 1)));
  puVar4 = &DAT_0010d1b2;
  sVar3 = 4;
  do {
    if (*puVar6 == 0) {
      *puVar4 = 3;
      puVar4[1] = 0;
      puVar4[2] = 0;
      puVar4[3] = 0;
    }
    else {
      uVar1 = puVar6[2];
      if (*(short *)(&DAT_00001114 + unaff_A5) != 2) {
        uVar1 = uVar1 | 0x4000;
      }
      *puVar4 = uVar1;
      puVar4[1] = *(short *)(&DAT_000010c0 + unaff_A5) + (short)*(char *)((int)puVar6 + 3) + 1U &
                  0x1ff;
      sVar2 = (*(ushort *)(&DAT_00001308 + unaff_A5) >> 1 & 3) << 1;
      uVar1 = *puVar6;
      if (uVar1 == 0x46e) {
        uVar1 = *(ushort *)(&DAT_00054688 + sVar2);
      }
      else if (uVar1 == 0x46f) {
        uVar1 = *(ushort *)(&DAT_00054690 + sVar2);
      }
      else if (uVar1 == 0x47b) {
        uVar1 = *(ushort *)(&DAT_00054698 + sVar2);
      }
      else if (uVar1 == 0x47c) {
        uVar1 = *(ushort *)(&DAT_000546a0 + sVar2);
      }
      puVar4[2] = uVar1;
      uVar1 = (ushort)*(char *)(puVar6 + 1);
      if (*(short *)(&DAT_00001114 + unaff_A5) != 2) {
        uVar1 = (uVar1 ^ 0xffff) - 0xf;
      }
      puVar4[3] = *(short *)(&DAT_000010be + unaff_A5) + uVar1 & 0x1ff;
      puVar6 = puVar6 + 3;
    }
    puVar4 = puVar4 + 4;
    sVar3 = sVar3 + -1;
  } while (sVar3 != 0);
  return;
}



/* ===== arcade_pc 0x0546A8 FUN_000546a8 ===== */

void FUN_000546a8(void)

{
  ushort uVar1;
  short sVar2;
  ushort *puVar3;
  ushort *puVar4;
  int unaff_A5;
  
  puVar4 = &DAT_0010d1f2;
  sVar2 = *(short *)(&DAT_00001246 + unaff_A5);
  if ((*(short *)(&DAT_000010e8 + unaff_A5) == 9) && (*(short *)(&DAT_00001114 + unaff_A5) == 3)) {
    sVar2 = sVar2 + -1;
  }
  puVar3 = (ushort *)
           (&player_secondary_piece_descriptors_5c466 +
           *(short *)(&player_secondary_piece_descriptors_5c466 + (short)(sVar2 << 1)));
  sVar2 = 4;
  do {
    if (*puVar3 == 0) {
      *puVar4 = 3;
      puVar4[1] = 0;
      puVar4[2] = 0;
      puVar4[3] = 0;
    }
    else {
      uVar1 = puVar3[2];
      if (*(short *)(&DAT_00001114 + unaff_A5) != 2) {
        uVar1 = uVar1 | 0x4000;
      }
      *puVar4 = uVar1;
      puVar4[1] = *(short *)(&DAT_000010c0 + unaff_A5) + (short)*(char *)((int)puVar3 + 3) + 1U &
                  0x1ff;
      puVar4[2] = *puVar3;
      uVar1 = (ushort)*(char *)(puVar3 + 1);
      if (*(short *)(&DAT_00001114 + unaff_A5) != 2) {
        uVar1 = (uVar1 ^ 0xffff) - 0xf;
      }
      puVar4[3] = *(short *)(&DAT_000010be + unaff_A5) + uVar1 & 0x1ff;
      puVar3 = puVar3 + 3;
    }
    puVar4 = puVar4 + 4;
    sVar2 = sVar2 + -1;
  } while (sVar2 != 0);
  return;
}



/* ===== arcade_pc 0x0547C0 player_aux_update_547c0 ===== */

void player_aux_update_547c0(void)

{
  int unaff_A5;
  
  if (*(short *)(&DAT_00001298 + unaff_A5) == 1) {
    *(undefined2 *)(&DAT_0000129c + unaff_A5) = DAT_0010d1b4;
    *(undefined2 *)(&DAT_0000129a + unaff_A5) = DAT_0010d1b8;
  }
  if (*(short *)(&DAT_0000129e + unaff_A5) == 1) {
    if (*(short *)(&DAT_00001298 + unaff_A5) != 0xc) {
      player_aux_sprite_constructor_54810();
      return;
    }
  }
  else if (*(short *)(&DAT_00001298 + unaff_A5) != 0x14) {
    player_aux_sprite_constructor_54810();
    return;
  }
  FUN_000540ac();
  return;
}



/* ===== arcade_pc 0x054810 player_aux_sprite_constructor_54810 ===== */

void player_aux_sprite_constructor_54810(void)

{
  short in_D0w;
  short sVar1;
  undefined2 *puVar2;
  undefined2 *puVar3;
  ushort *puVar4;
  int unaff_A5;
  
  puVar3 = &PC090OJ_sprite_RAM_d00000;
  puVar2 = (undefined2 *)(&player_aux_piece_table_5da5e + (short)(in_D0w * 0x18));
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



/* ===== arcade_pc 0x054864 player_collision_boxes_update_54864 ===== */

void player_collision_boxes_update_54864(void)

{
  byte *pbVar1;
  short sVar2;
  undefined *puVar3;
  int unaff_A5;
  
  player_attack_box_enable_update_54982();
  sVar2 = *(short *)(&DAT_00001244 + unaff_A5) * 4;
  if (*(short *)(&DAT_00001114 + unaff_A5) == 2) {
    (&DAT_00001248)[unaff_A5] = (&player_body_collision_extent_table_5c90e)[sVar2];
    (&DAT_00001249)[unaff_A5] = (&DAT_0005c90f)[sVar2];
    (&DAT_0000124a)[unaff_A5] = (&DAT_0005c910)[sVar2];
  }
  else {
    (&DAT_00001248)[unaff_A5] = ((&DAT_0005c90f)[sVar2] ^ 0xff) + 1;
    (&DAT_00001249)[unaff_A5] = ((&player_body_collision_extent_table_5c90e)[sVar2] ^ 0xff) + 1;
    (&DAT_0000124a)[unaff_A5] = (&DAT_0005c910)[sVar2];
  }
  (&DAT_0000124b)[unaff_A5] = (&DAT_0005cd5a)[*(short *)(&DAT_00001246 + unaff_A5)];
  if (*(short *)(&DAT_000012fa + unaff_A5) == 1) {
    puVar3 = &stage1_player_attack_extent_table_5c9ea;
  }
  else if (*(short *)(&DAT_000012fa + unaff_A5) == 2) {
    puVar3 = &stage2_player_attack_extent_table_5cac6;
  }
  else if (*(short *)(&DAT_000012fa + unaff_A5) == 3) {
    puVar3 = &stage3_player_attack_extent_table_5cba2;
  }
  else {
    if (*(short *)(&DAT_000012fa + unaff_A5) != 4) {
      return;
    }
    puVar3 = &stage4_player_attack_extent_table_5cc7e;
  }
  pbVar1 = puVar3 + (short)(*(short *)(&DAT_00001244 + unaff_A5) * 4);
  if (*(short *)(&DAT_00001114 + unaff_A5) == 2) {
    (&DAT_00001254)[unaff_A5] = *pbVar1;
    (&DAT_00001255)[unaff_A5] = pbVar1[1];
    (&DAT_00001256)[unaff_A5] = pbVar1[2];
    (&DAT_00001257)[unaff_A5] = pbVar1[3];
  }
  else {
    (&DAT_00001254)[unaff_A5] = (pbVar1[1] ^ 0xff) + 1;
    (&DAT_00001255)[unaff_A5] = (*pbVar1 ^ 0xff) + 1;
    (&DAT_00001256)[unaff_A5] = pbVar1[2];
    (&DAT_00001257)[unaff_A5] = pbVar1[3];
  }
  return;
}



/* ===== arcade_pc 0x054982 player_attack_box_enable_update_54982 ===== */

void player_attack_box_enable_update_54982(void)

{
  int unaff_A5;
  
  if (*(short *)(&DAT_000012f0 + unaff_A5) == 1) {
LAB_000549d4:
    *(undefined2 *)(&DAT_000012f8 + unaff_A5) = 0xff;
  }
  else {
    if (*(short *)(&DAT_00001108 + unaff_A5) == 1) {
      if ((((*(short *)(&DAT_000012fa + unaff_A5) != 4) &&
           (*(short *)((int)&PTR_DAT_00001116 + unaff_A5) != 1)) &&
          (*(short *)(&DAT_000010e8 + unaff_A5) != 4)) &&
         ((*(short *)(&DAT_000010e8 + unaff_A5) != 6 &&
          ((*(ushort *)(&DAT_0000110a + unaff_A5) < 3 ||
           (0xd < *(ushort *)(&DAT_0000110a + unaff_A5))))))) goto LAB_000549d4;
    }
    else if (*(short *)(&DAT_000010e8 + unaff_A5) != 2) goto LAB_000549d4;
    *(undefined2 *)(&DAT_000012f8 + unaff_A5) = 1;
  }
  return;
}



/* ===== arcade_pc 0x055650 FUN_00055650 ===== */

void FUN_00055650(void)

{
  int unaff_A5;
  
  *(undefined2 *)(&DAT_000013d0 + unaff_A5) = 0xff;
  *(undefined2 *)(&DAT_00001330 + unaff_A5) = 0xff;
  if ((*(ushort *)(&DAT_000010d0 + unaff_A5) & 1) != 0) {
    FUN_00055696();
  }
  if ((*(ushort *)(&DAT_000010d0 + unaff_A5) & 2) != 0) {
    FUN_0005572e();
  }
  if ((*(ushort *)(&DAT_000010d0 + unaff_A5) & 8) != 0) {
    FUN_000557ba();
  }
  if ((*(ushort *)(&DAT_000010d0 + unaff_A5) & 4) != 0) {
    FUN_00055854();
  }
  return;
}



/* ===== arcade_pc 0x055696 FUN_00055696 ===== */

void FUN_00055696(void)

{
  ushort uVar1;
  int unaff_A5;
  
  *(undefined2 *)(&DAT_00001330 + unaff_A5) = 1;
  if (*(short *)(&DAT_000010ba + unaff_A5) < 0x100) {
    *(short *)(&DAT_000010ba + unaff_A5) =
         *(short *)(&DAT_000010da + unaff_A5) + *(short *)(&DAT_000010ba + unaff_A5);
  }
  else {
    if (*(short *)(&DAT_000010a8 + unaff_A5) != 1) {
      *(ushort *)(&DAT_000010d0 + unaff_A5) = *(ushort *)(&DAT_000010d0 + unaff_A5) | 0x20;
      return;
    }
    uVar1 = *(short *)(&DAT_000010da + unaff_A5) + *(short *)(&DAT_000010b4 + unaff_A5);
    *(ushort *)(&DAT_000010b4 + unaff_A5) = uVar1;
    if ((uVar1 & 8) != 0) {
      *(ushort *)(&DAT_000010b4 + unaff_A5) = uVar1 & 0xfff7;
      *(uint *)(&DAT_000010a4 + unaff_A5) =
           (int)&DAT_00c08000 +
           (uint)(ushort)(0x3f00 - (*(short *)(&DAT_000010ca + unaff_A5) * 0x100 +
                                   *(short *)(&DAT_000010cc + unaff_A5) * 0x400));
      FUN_00055948();
    }
  }
  *(ushort *)(&DAT_000010b0 + unaff_A5) =
       *(short *)(&DAT_000010da + unaff_A5) + *(short *)(&DAT_000010b0 + unaff_A5) & 0x1ff;
  *(undefined2 *)(&DAT_000013d0 + unaff_A5) = 0;
  FUN_000406a4();
  return;
}



/* ===== arcade_pc 0x05572E FUN_0005572e ===== */

void FUN_0005572e(void)

{
  ushort uVar1;
  int unaff_A5;
  
  if (*(short *)(&DAT_000010ba + unaff_A5) < 8) {
    if (*(short *)(&DAT_000010a8 + unaff_A5) != 2) {
      *(ushort *)(&DAT_000010d0 + unaff_A5) = *(ushort *)(&DAT_000010d0 + unaff_A5) | 0x10;
      return;
    }
    uVar1 = *(short *)(&DAT_000010da + unaff_A5) + *(short *)(&DAT_000010b6 + unaff_A5);
    *(ushort *)(&DAT_000010b6 + unaff_A5) = uVar1;
    if ((uVar1 & 8) != 0) {
      *(ushort *)(&DAT_000010b6 + unaff_A5) = uVar1 & 0xfff7;
      *(uint *)(&DAT_000010a4 + unaff_A5) =
           (int)&DAT_00c08000 +
           (uint)(ushort)(*(short *)(&DAT_000010ca + unaff_A5) * 0x100 +
                         *(short *)(&DAT_000010cc + unaff_A5) * 0x400);
      FUN_00055948();
    }
  }
  else {
    *(short *)(&DAT_000010ba + unaff_A5) =
         *(short *)(&DAT_000010ba + unaff_A5) - *(short *)(&DAT_000010da + unaff_A5);
  }
  *(ushort *)(&DAT_000010b0 + unaff_A5) =
       *(short *)(&DAT_000010b0 + unaff_A5) - *(short *)(&DAT_000010da + unaff_A5) & 0x1ff;
  *(undefined2 *)(&DAT_000013d0 + unaff_A5) = 1;
  FUN_000406a4();
  return;
}



/* ===== arcade_pc 0x0557BA FUN_000557ba ===== */

void FUN_000557ba(void)

{
  ushort uVar1;
  int unaff_A5;
  
  if (*(short *)(&DAT_000010b8 + unaff_A5) < 0xa0) {
    *(short *)(&DAT_000010b8 + unaff_A5) =
         *(short *)(&DAT_000010d8 + unaff_A5) + *(short *)(&DAT_000010b8 + unaff_A5);
  }
  else {
    if (*(short *)(&DAT_000010a8 + unaff_A5) != 0) {
      *(ushort *)(&DAT_000010d0 + unaff_A5) = *(ushort *)(&DAT_000010d0 + unaff_A5) | 0x40;
      return;
    }
    uVar1 = *(short *)(&DAT_000010d8 + unaff_A5) + *(short *)(&DAT_000010b2 + unaff_A5);
    *(ushort *)(&DAT_000010b2 + unaff_A5) = uVar1;
    if ((uVar1 & 8) != 0) {
      *(ushort *)(&DAT_000010b2 + unaff_A5) = uVar1 & 0xfff7;
      *(uint *)(&DAT_000010a0 + unaff_A5) =
           (int)&DAT_00c08000 +
           (uint)(ushort)(*(short *)(&DAT_000010ca + unaff_A5) * 4 +
                         *(short *)(&DAT_000010cc + unaff_A5) * 0x10);
      FUN_00055948();
    }
  }
  *(ushort *)(&DAT_000010ae + unaff_A5) =
       *(short *)(&DAT_000010ae + unaff_A5) - *(short *)(&DAT_000010d8 + unaff_A5) & 0x1ff;
  *(undefined2 *)(&DAT_000013d0 + unaff_A5) = 3;
  FUN_000406a4();
  return;
}



/* ===== arcade_pc 0x055854 FUN_00055854 ===== */

void FUN_00055854(void)

{
  int unaff_A5;
  
  if ((*(short *)(unaff_A5 + 0x20c) == 1) || (*(short *)(&DAT_000010b8 + unaff_A5) < 0)) {
    *(ushort *)(&DAT_000010d0 + unaff_A5) = *(ushort *)(&DAT_000010d0 + unaff_A5) | 0x80;
  }
  else {
    *(short *)(&DAT_000010b8 + unaff_A5) =
         *(short *)(&DAT_000010b8 + unaff_A5) - *(short *)(&DAT_000010d8 + unaff_A5);
    *(ushort *)(&DAT_000010ae + unaff_A5) =
         *(short *)(&DAT_000010d8 + unaff_A5) + *(short *)(&DAT_000010ae + unaff_A5) & 0x1ff;
    *(undefined2 *)(&DAT_000013d0 + unaff_A5) = 2;
    FUN_000406a4();
  }
  return;
}



/* ===== arcade_pc 0x0558A2 FUN_000558a2 ===== */

void FUN_000558a2(void)

{
  int unaff_A5;
  
  if (*(short *)(&DAT_000010ca + unaff_A5) == 4) {
    FUN_000558c6();
    FUN_00055904();
    *(short *)(&DAT_000010cc + unaff_A5) = *(short *)(&DAT_000010cc + unaff_A5) + 1;
    if (*(short *)(&DAT_000010cc + unaff_A5) == 0x10) {
      FUN_000558e0();
    }
  }
  return;
}



/* ===== arcade_pc 0x0558C6 FUN_000558c6 ===== */

void FUN_000558c6(void)

{
  short sVar1;
  int *piVar2;
  int unaff_A5;
  
  sVar1 = 0x10;
  piVar2 = &DAT_0010d000;
  do {
    *piVar2 = *piVar2 + 4;
    piVar2 = piVar2 + 1;
    sVar1 = sVar1 + -1;
  } while (sVar1 != 0);
  *(undefined2 *)(&DAT_000010ca + unaff_A5) = 0;
  return;
}



/* ===== arcade_pc 0x0558E0 FUN_000558e0 ===== */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_000558e0(void)

{
  int unaff_A5;
  
  *(undefined2 *)(&DAT_000010cc + unaff_A5) = 0;
  *(int *)(&DAT_000010c6 + unaff_A5) = *(int *)(&DAT_000010c6 + unaff_A5) + 1;
  *(undefined2 *)(&DAT_0000132c + unaff_A5) = *(undefined2 *)(&DAT_000010a8 + unaff_A5);
  _DAT_0010d0a8 = (ushort)**(byte **)(&DAT_000010c6 + unaff_A5);
  *(short *)(unaff_A5 + 0x13e) = *(short *)(unaff_A5 + 0x13e) + 1;
  return;
}



/* ===== arcade_pc 0x055904 FUN_00055904 ===== */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_00055904(void)

{
  undefined2 *puVar1;
  short sVar2;
  int *piVar3;
  uint *puVar4;
  undefined2 *puVar5;
  int unaff_A5;
  
  piVar3 = &DAT_0010d000;
  sVar2 = 0x10;
  puVar4 = &DAT_0010d040;
  puVar5 = &DAT_0010d080;
  do {
    puVar1 = (undefined2 *)*piVar3;
    *puVar5 = *puVar1;
    *puVar4 = (uint)(ushort)puVar1[1];
    piVar3 = piVar3 + 1;
    sVar2 = sVar2 + -1;
    puVar4 = puVar4 + 1;
    puVar5 = puVar5 + 1;
  } while (sVar2 != 0);
  _DAT_0010d0a8 = (ushort)**(byte **)(&DAT_000010c6 + unaff_A5);
  return;
}



/* ===== arcade_pc 0x055948 FUN_00055948 ===== */

void FUN_00055948(void)

{
  int unaff_A5;
  
  if (*(short *)(&DAT_000010a8 + unaff_A5) == 0) {
    FUN_00055968();
    *(short *)(&DAT_000010ca + unaff_A5) = *(short *)(&DAT_000010ca + unaff_A5) + 1;
  }
  else {
    FUN_00055990();
    *(short *)(&DAT_000010ca + unaff_A5) = *(short *)(&DAT_000010ca + unaff_A5) + 1;
  }
  FUN_000558a2();
  return;
}



/* ===== arcade_pc 0x055968 FUN_00055968 ===== */

void FUN_00055968(void)

{
  short extraout_D1w;
  undefined4 extraout_A0;
  int unaff_A5;
  
  do {
    FUN_000559b2();
    *(undefined4 *)(&DAT_000010a0 + unaff_A5) = extraout_A0;
  } while (extraout_D1w != 1);
  return;
}



/* ===== arcade_pc 0x055990 FUN_00055990 ===== */

void FUN_00055990(void)

{
  short extraout_D1w;
  
  do {
    FUN_00055a14();
  } while (extraout_D1w != 1);
  return;
}



/* ===== arcade_pc 0x0559B2 FUN_000559b2 ===== */

void FUN_000559b2(void)

{
  short sVar1;
  undefined2 *in_A0;
  undefined2 *in_A1;
  int unaff_A2;
  int unaff_A5;
  undefined2 *puVar2;
  
  sVar1 = 0;
  do {
    *in_A0 = *in_A1;
    if (*(short *)(unaff_A2 + 0x20) == 0xff) {
      puVar2 = (undefined2 *)(unaff_A2 + 0x22);
    }
    else {
      puVar2 = (undefined2 *)
               (unaff_A2 + 0x20 + (int)(short)(sVar1 * 8 + *(short *)(&DAT_000010ca + unaff_A5) * 2)
               );
    }
    *(undefined2 *)(&collision_map_64x64_words_base + ((uint)(in_A0 + -0x604000) >> 1)) = *puVar2;
    in_A0[1] = *(undefined2 *)
                (unaff_A2 + (short)(*(short *)(&DAT_000010ca + unaff_A5) * 2 + sVar1 * 8));
    in_A0 = in_A0 + 0x80;
    sVar1 = sVar1 + 1;
  } while (sVar1 != 4);
  return;
}



/* ===== arcade_pc 0x055A14 FUN_00055a14 ===== */

void FUN_00055a14(void)

{
  short sVar1;
  ushort uVar2;
  undefined2 *in_A0;
  undefined2 *in_A1;
  int unaff_A2;
  int unaff_A5;
  undefined2 *puVar3;
  
  *(undefined2 *)(&DAT_00001330 + unaff_A5) = 1;
  sVar1 = 0;
  do {
    *in_A0 = *in_A1;
    if (*(short *)(unaff_A2 + 0x20) == 0xff) {
      puVar3 = (undefined2 *)(unaff_A2 + 0x22);
    }
    else {
      uVar2 = *(ushort *)(&DAT_000010ca + unaff_A5);
      if (*(short *)(&DAT_000010a8 + unaff_A5) != 2) {
        uVar2 = ~uVar2 & 3;
      }
      puVar3 = (undefined2 *)(unaff_A2 + 0x20 + (int)(short)(sVar1 * 2 + uVar2 * 8));
    }
    *(undefined2 *)(&collision_map_64x64_words_base + ((uint)(in_A0 + -0x604000) >> 1)) = *puVar3;
    uVar2 = *(ushort *)(&DAT_000010ca + unaff_A5);
    if (*(short *)(&DAT_000010a8 + unaff_A5) != 2) {
      uVar2 = ~uVar2 & 3;
    }
    in_A0[1] = *(undefined2 *)(unaff_A2 + (short)(sVar1 * 2 + uVar2 * 8));
    in_A0 = in_A0 + 2;
    sVar1 = sVar1 + 1;
  } while (sVar1 != 4);
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



/* ===== arcade_pc 0x055AD6 FUN_00055ad6 ===== */

void FUN_00055ad6(void)

{
  int unaff_A5;
  
  if (((*(ushort *)(&DAT_000010d0 + unaff_A5) & 1) != 0) &&
     ((*(ushort *)(&DAT_000010d0 + unaff_A5) & 0x20) == 0)) {
    FUN_00055b28();
  }
  if (((*(ushort *)(&DAT_000010d0 + unaff_A5) & 2) != 0) &&
     ((*(ushort *)(&DAT_000010d0 + unaff_A5) & 0x10) == 0)) {
    FUN_00055b32();
  }
  if (((*(ushort *)(&DAT_000010d0 + unaff_A5) & 8) != 0) &&
     ((*(ushort *)(&DAT_000010d0 + unaff_A5) & 0x40) == 0)) {
    FUN_00055b3c();
  }
  if (((*(ushort *)(&DAT_000010d0 + unaff_A5) & 4) != 0) &&
     ((*(ushort *)(&DAT_000010d0 + unaff_A5) & 0x80) == 0)) {
    FUN_00055bb6();
  }
  return;
}



/* ===== arcade_pc 0x055B28 FUN_00055b28 ===== */

void FUN_00055b28(void)

{
  int unaff_A5;
  
  *(undefined2 *)(&DAT_000010ee + unaff_A5) = *(undefined2 *)(&DAT_000010b0 + unaff_A5);
  return;
}



/* ===== arcade_pc 0x055B32 FUN_00055b32 ===== */

void FUN_00055b32(void)

{
  int unaff_A5;
  
  *(undefined2 *)(&DAT_000010ee + unaff_A5) = *(undefined2 *)(&DAT_000010b0 + unaff_A5);
  return;
}



/* ===== arcade_pc 0x055B3C FUN_00055b3c ===== */

void FUN_00055b3c(void)

{
  short sVar1;
  ushort uVar2;
  int unaff_A5;
  
  if (0x9f < *(short *)(&DAT_000010b8 + unaff_A5)) {
    if (*(short *)(&DAT_000010a8 + unaff_A5) != 0) {
      return;
    }
    uVar2 = ((ushort)(*(short *)(&DAT_000010f0 + unaff_A5) + *(short *)(&DAT_000010d8 + unaff_A5))
            >> 1) + *(short *)(&DAT_000010f2 + unaff_A5);
    *(ushort *)(&DAT_000010f2 + unaff_A5) = uVar2;
    if ((uVar2 & 8) != 0) {
      *(ushort *)(&DAT_000010f2 + unaff_A5) = uVar2 & 0xfff7;
      *(uint *)(&DAT_000010f8 + unaff_A5) =
           (ushort)(*(short *)(&DAT_000010f6 + unaff_A5) * 4 +
                   *(short *)(&DAT_000010f4 + unaff_A5) * 0x40) + 0xc00000;
      FUN_00055c4a();
    }
  }
  sVar1 = *(short *)(&DAT_000010f0 + unaff_A5);
  *(ushort *)(&DAT_000010f0 + unaff_A5) = sVar1 + *(short *)(&DAT_000010d8 + unaff_A5) & 1;
  *(ushort *)(&DAT_000010ec + unaff_A5) =
       *(short *)(&DAT_000010ec + unaff_A5) -
       ((ushort)(sVar1 + *(short *)(&DAT_000010d8 + unaff_A5)) >> 1) & 0x1ff;
  return;
}



/* ===== arcade_pc 0x055BB6 FUN_00055bb6 ===== */

void FUN_00055bb6(void)

{
  short sVar1;
  int unaff_A5;
  
  if (-1 < *(short *)(&DAT_000010b8 + unaff_A5)) {
    sVar1 = *(short *)(&DAT_000010f0 + unaff_A5);
    *(ushort *)(&DAT_000010f0 + unaff_A5) =
         (*(short *)(&DAT_000010d8 + unaff_A5) - sVar1 & 1U ^ 0xffff) + 1;
    *(ushort *)(&DAT_000010ec + unaff_A5) =
         ((ushort)(*(short *)(&DAT_000010d8 + unaff_A5) - sVar1) >> 1) +
         *(short *)(&DAT_000010ec + unaff_A5) & 0x1ff;
  }
  return;
}



/* ===== arcade_pc 0x055BEC FUN_00055bec ===== */

void FUN_00055bec(void)

{
  short sVar1;
  int unaff_A5;
  
  if (*(short *)(&DAT_000010f6 + unaff_A5) == 0x10) {
    FUN_00055c14();
    FUN_00055c2e();
    sVar1 = *(short *)(&DAT_000010f4 + unaff_A5);
    *(short *)(&DAT_000010f4 + unaff_A5) = sVar1 + 1;
    if ((short)(sVar1 + 1) == 4) {
      FUN_00055c22();
    }
  }
  return;
}



/* ===== arcade_pc 0x055C14 FUN_00055c14 ===== */

void FUN_00055c14(void)

{
  int unaff_A5;
  
  DAT_0010d0fc = DAT_0010d0fc + 6;
  *(undefined2 *)(&DAT_000010f6 + unaff_A5) = 0;
  return;
}



/* ===== arcade_pc 0x055C22 FUN_00055c22 ===== */

void FUN_00055c22(void)

{
  int unaff_A5;
  
  *(undefined2 *)(&DAT_000010f4 + unaff_A5) = 0;
  *(undefined2 *)(&DAT_000013b0 + unaff_A5) = 1;
  return;
}



/* ===== arcade_pc 0x055C2E FUN_00055c2e ===== */

void FUN_00055c2e(void)

{
  DAT_0010d104 = *DAT_0010d0fc;
  DAT_0010d100 = *(undefined4 *)(DAT_0010d0fc + 1);
  return;
}



/* ===== arcade_pc 0x055C4A FUN_00055c4a ===== */

void FUN_00055c4a(void)

{
  int unaff_A5;
  
  *(undefined4 *)(&DAT_00001126 + unaff_A5) = *(undefined4 *)((int)&PTR_DAT_000010fc + unaff_A5);
  FUN_00055c5e();
  *(short *)(&DAT_000010f6 + unaff_A5) = *(short *)(&DAT_000010f6 + unaff_A5) + 1;
  FUN_00055bec();
  return;
}



/* ===== arcade_pc 0x055C5E FUN_00055c5e ===== */

void FUN_00055c5e(void)

{
  undefined4 extraout_A0;
  int unaff_A5;
  
  FUN_00055c7a();
  *(undefined4 *)(&DAT_000010f8 + unaff_A5) = extraout_A0;
  return;
}



/* ===== arcade_pc 0x055C7A FUN_00055c7a ===== */

void FUN_00055c7a(void)

{
  short sVar1;
  undefined2 *in_A0;
  undefined2 *in_A1;
  int unaff_A2;
  int unaff_A5;
  
  sVar1 = 0;
  do {
    *in_A0 = *in_A1;
    in_A0[1] = *(undefined2 *)
                (unaff_A2 + (short)(*(short *)(&DAT_000010f6 + unaff_A5) * 2 + sVar1 * 0x20));
    in_A0 = in_A0 + 0x80;
    sVar1 = sVar1 + 1;
  } while (sVar1 != 0x40);
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



/* ===== arcade_pc 0x0596F4 FUN_000596f4 ===== */

void FUN_000596f4(void)

{
  int iVar1;
  undefined2 *puVar2;
  undefined2 uVar3;
  undefined2 uVar4;
  ushort uVar5;
  ushort uVar6;
  ushort uVar7;
  ushort *puVar8;
  int unaff_A5;
  
  if (*(short *)(&DAT_00001360 + unaff_A5) == 1) {
    iVar1 = (int)(short)((DAT_0010c118 - 1) * 6);
    uVar4 = *(undefined2 *)(&DAT_00059772 + iVar1);
    puVar8 = *(ushort **)((int)&PTR_PTR_0005976e + iVar1);
    uVar5 = *puVar8;
    if (uVar5 != 0) {
      uVar7 = puVar8[1];
      puVar8 = puVar8 + 2;
      uVar6 = *(ushort *)(&DAT_00001362 + unaff_A5);
      while( true ) {
        puVar2 = *(undefined2 **)puVar8;
        *puVar2 = uVar4;
        uVar3 = *(undefined2 *)((int)puVar8 + (int)(short)((uVar6 >> 2) * 2 + 8));
        puVar2[1] = uVar3;
        puVar2 = *(undefined2 **)(puVar8 + 2);
        *puVar2 = uVar4;
        puVar2[1] = uVar3;
        uVar7 = uVar7 - 1;
        if (uVar7 == 0) break;
        puVar8 = (ushort *)((int)(short)((uVar5 + 4) * 2) + (int)puVar8);
      }
      *(short *)(&DAT_00001362 + unaff_A5) = *(short *)(&DAT_00001362 + unaff_A5) + 1;
      if (uVar5 == *(ushort *)(&DAT_00001362 + unaff_A5) >> 2) {
        *(undefined2 *)(&DAT_00001362 + unaff_A5) = 0;
      }
    }
  }
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



/* ===== arcade_pc 0x059DE8 FUN_00059de8 ===== */

void FUN_00059de8(void)

{
  short sVar1;
  int unaff_A5;
  
  if (*(short *)(&DAT_000013b0 + unaff_A5) == 1) {
    FUN_00059e1e();
    FUN_00059e36();
    sVar1 = 0;
    do {
      FUN_00059e6c();
      FUN_00059e50();
      FUN_00059ad4();
      sVar1 = sVar1 + 1;
    } while (sVar1 != *(short *)(&DAT_000013d6 + unaff_A5));
  }
  *(undefined2 *)(&DAT_000013b0 + unaff_A5) = 0xff;
  return;
}



/* ===== arcade_pc 0x059E1E FUN_00059e1e ===== */

void FUN_00059e1e(void)

{
  int unaff_A5;
  
  *(ushort *)(&DAT_000013ae + unaff_A5) =
       (ushort)(byte)(&DAT_0005e24e)[*(short *)(unaff_A5 + 0x13e)];
  return;
}



/* ===== arcade_pc 0x059E36 FUN_00059e36 ===== */

void FUN_00059e36(void)

{
  int unaff_A5;
  
  *(undefined2 *)(&DAT_000013d6 + unaff_A5) =
       *(undefined2 *)((int)&PTR_DAT_00059ebc + (int)(short)((*(byte *)(unaff_A5 + 0x118) - 1) * 2))
  ;
  return;
}



/* ===== arcade_pc 0x059E50 FUN_00059e50 ===== */

undefined2 FUN_00059e50(void)

{
  short unaff_D5w;
  int unaff_A5;
  
  return *(undefined2 *)
          ((int)&PTR_DAT_00059e8c +
          (int)(short)(unaff_D5w * 2 + (*(byte *)(unaff_A5 + 0x118) - 1) * 8));
}



/* ===== arcade_pc 0x059E6C FUN_00059e6c ===== */

void FUN_00059e6c(void)

{
  return;
}



/* ===== arcade_pc 0x059EE0 FUN_00059ee0 ===== */

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_00059ee0(void)

{
  ushort uVar1;
  int unaff_A5;
  
  DAT_0010c10c = DAT_0010c10c + 1;
  uVar1 = *(ushort *)
           (*(int *)(&DAT_00059f1e + (short)(ushort)(*(byte *)(unaff_A5 + 0x1d) & 0xc)) +
           (int)(short)(DAT_0010c10c * 2));
  _DAT_0010c132 = uVar1 * 0x100 + (uVar1 >> 8);
  return;
}



/* ===== arcade_pc 0x059F5E FUN_00059f5e ===== */

void FUN_00059f5e(void)

{
  short sVar1;
  undefined4 *puVar2;
  undefined4 *puVar3;
  undefined2 *puVar4;
  undefined2 *puVar5;
  
  sVar1 = 8;
  puVar2 = &DAT_00d00048;
  do {
    puVar3 = puVar2 + 1;
    *puVar2 = 0;
    puVar2 = puVar2 + 2;
    *puVar3 = 0;
    sVar1 = sVar1 + -1;
  } while (sVar1 != 0);
  sVar1 = 4;
  puVar4 = &DAT_0010c170;
  do {
    *puVar4 = 0x80;
    puVar4[1] = 0;
    puVar5 = puVar4 + 3;
    puVar4[2] = 0;
    puVar4 = puVar4 + 4;
    *puVar5 = 0;
    sVar1 = sVar1 + -1;
  } while (sVar1 != 0);
  return;
}



/* ===== arcade_pc 0x05A29C collision_map_surface_postprocess_5a29c ===== */

void collision_map_surface_postprocess_5a29c(void)

{
  short sVar1;
  short extraout_D1w;
  ushort *extraout_A0;
  ushort *puVar2;
  int unaff_A5;
  
  if ((*(short *)(&DAT_00001330 + unaff_A5) == 1) && (*(short *)(&DAT_000010a8 + unaff_A5) == 1)) {
    puVar2 = (ushort *)
             (&collision_map_64x64_words_base +
             ((ushort)((((*(ushort *)(&DAT_000010b0 + unaff_A5) ^ 0x1ff) + 1 & 0x1f8) + 0xf8 & 0x1f8
                       ) << 5) >> 1));
    sVar1 = 0x10;
    do {
      if ((*puVar2 & 0x80) != 0) {
        collision_map_surface_mark_5a2ee();
        sVar1 = extraout_D1w;
        puVar2 = extraout_A0;
      }
      puVar2 = puVar2 + 4;
      sVar1 = sVar1 + -1;
    } while (sVar1 != 0);
  }
  return;
}



/* ===== arcade_pc 0x05A2EE collision_map_surface_mark_5a2ee ===== */

void collision_map_surface_mark_5a2ee(void)

{
  undefined2 *puVar1;
  undefined2 *in_A0;
  
  *in_A0 = 1;
  in_A0[1] = 1;
  in_A0[2] = 1;
  in_A0[3] = 1;
  in_A0[-0x140] = in_A0[-0x140] & 0xff | 0x3400;
  in_A0[-0x13f] = in_A0[-0x13f] & 0xff | 0x3400;
  in_A0[-0x13e] = in_A0[-0x13e] & 0xff | 0x3400;
  in_A0[-0x13d] = in_A0[-0x13d] & 0xff | 0x3400;
  puVar1 = in_A0 + -0x86f00;
  *(undefined **)(&DAT_00c08000 + (int)puVar1) = &DAT_000025c7;
  *(undefined **)(&DAT_00c08004 + (int)puVar1) = &DAT_000025c7;
  *(undefined **)(&DAT_00c08008 + (int)puVar1 * 2) = &DAT_000025c7;
  *(undefined **)(&DAT_00c0800c + (int)puVar1 * 2) = &DAT_000025c7;
  return;
}



/* ===== arcade_pc 0x05A3AC FUN_0005a3ac ===== */

void FUN_0005a3ac(void)

{
  FUN_00059ad4();
  FUN_0005a4de();
  return;
}



/* ===== arcade_pc 0x05A442 FUN_0005a442 ===== */

void FUN_0005a442(void)

{
  FUN_00059ad4();
  FUN_0005a4de();
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


