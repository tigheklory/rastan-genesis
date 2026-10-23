#!/usr/bin/env python3
"""AUDIO-012 — PROVISIONAL authored-routing renderer: ORIGINAL YM2151 capture -> Genesis YM2612+PSG VGM.

Applies the user's per-channel Genesis routing (approved_routing: arcade YM2151 channel -> destination) to
an original Rastan YM2151 capture and emits a real **YM2612 (FM1-5) + SN76489 (PSG)** VGM — actual chip
register commands (VGM 0x52/0x53 for YM2612, 0x50 for PSG), NOT oscillator/WAV fakery. It plays in the
same webVGM engine, so the user hears the arrangement they authored and can A/B it against the original.

STAGE 1 / PROVISIONAL — limitations are explicit and labeled (not hidden):
  * YM2151 (OPM) operator PARAMETER registers are bit-compatible with YM2612 (OPN2) and are translated
    1:1 (DT/MUL, TL, KS/AR, AM/D1R, D2R, SL/RR, FB, algorithm). OPM DT2 has no OPN2 equivalent -> dropped.
  * OPM operator ORDER (M1,M2,C1,C2) vs OPN2 (S1,S3,S2,S4) is mapped by index; complex algorithms may
    differ in timbre. A later stage (AUDIO-003 instrument decode) replaces this with validated patches.
  * Pitch is converted OPM KC/KF -> Hz -> OPN2 fnum/block using the target YM2612 clock (7.67 MHz).
  * PSG-routed voices become 50%-duty squares: pitch -> 10-bit divider, key-on/off -> 4-bit attenuation
    (fixed audible level; per-note dynamics are a later refinement). noise mode per the profile selector.
  * FM6 is never targeted (DAC-reserved). Unassigned channels are dropped (silent).
  * This is NOT the production converter and does NOT decode ROM sequences/instruments; user listening is
    the acceptance criterion.

No ROM/production/driver change. Routing comes from the request, never from stored profiles.
"""
import argparse, csv, json, math, os, struct, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
YM2612_CLOCK = 7670454
SN76489_CLOCK = 3579545
VGM_RATE = 44100
OCTAVE_OFFSET = 0            # manual override only: shift all pitch by this many WHOLE octaves (0 = exact)
YM2151_ACTUAL_CLOCK = 4000000      # Rastan's real YM2151 clock; pitch is computed exactly from it below
# NOTE: pitch is now exact (PHASEINC_ROM table from the same OPM core webVGM uses). The old A440+ratio
# approximation (YM2151_NOMINAL_CLOCK / PITCH_CLOCK_RATIO) was removed — it was ~1 semitone off.
# PSG level: derive each PSG voice's 4-bit attenuation from the source YM2151 carrier TL so PSG tracks the
# original mix instead of blaring at full volume. FM TL step = 0.75 dB, PSG step = 2 dB -> scale 0.75/2.
PSG_TL_SCALE = 0.375
PSG_HEADROOM = 3            # extra PSG attenuation steps (~6 dB) so squares sit under the FM; tune to taste
# carrier operators per algorithm (op index 0-3); used only to estimate a PSG voice's output level
CARRIER_OPS = {0: (3,), 1: (3,), 2: (3,), 3: (3,), 4: (1, 3), 5: (1, 2, 3), 6: (1, 2, 3), 7: (0, 1, 2, 3)}

FM_TARGET = {"ym2612_fm1": 1, "ym2612_fm2": 2, "ym2612_fm3": 3, "ym2612_fm4": 4, "ym2612_fm5": 5}
PSG_TONE = {"psg_tone1": 0, "psg_tone2": 1, "psg_tone3": 2}
# OPM note4 (KC low nibble) -> semitone in octave (codes 3,7,11,15 are invalid gaps)
NOTE4 = {0: 0, 1: 1, 2: 2, 4: 3, 5: 4, 6: 5, 8: 6, 9: 7, 10: 8, 12: 9, 13: 10, 14: 11}
# OPM operator-param group -> OPN2 group (bit-compatible); value passes through (DT2 masked off for 0xC0)
OPM2OPN2_GROUP = {0x40: 0x30, 0x60: 0x40, 0x80: 0x50, 0xA0: 0x60, 0xC0: 0x70, 0xE0: 0x80}
YM_CH_PORT = {1: (0, 0), 2: (0, 1), 3: (0, 2), 4: (1, 0), 5: (1, 1)}   # ch -> (port, within-port index)
YM_KEYSEL = {1: 0, 2: 1, 3: 2, 4: 4, 5: 5}                            # ch -> 0x28 channel-select nibble


# EXACT YM2151 (OPM) phase-increment ROM (768 entries = 64 steps/semitone x 12), copied verbatim from the
# same VGMPlay/MAME ym2151 core that webVGM uses to play the arcade capture. Using it makes the Genesis
# render land on the IDENTICAL frequency the emulator produces for the arcade, so pitch matches exactly
# (no A440 approximation, no fudge factor). Emulator frequency: Hz = phaseinc_rom[i]*clock*2^(octave-28),
# i = semitone*64 + KF_fraction. Verified: nominal 3.58MHz A4 = 439.94 Hz; Rastan 4.0MHz A4 = 491.6 Hz.
PHASEINC_ROM = (
    1299,1300,1301,1302,1303,1304,1305,1306,1308,1309,1310,1311,1313,1314,1315,1316,
    1318,1319,1320,1321,1322,1323,1324,1325,1327,1328,1329,1330,1332,1333,1334,1335,
    1337,1338,1339,1340,1341,1342,1343,1344,1346,1347,1348,1349,1351,1352,1353,1354,
    1356,1357,1358,1359,1361,1362,1363,1364,1366,1367,1368,1369,1371,1372,1373,1374,
    1376,1377,1378,1379,1381,1382,1383,1384,1386,1387,1388,1389,1391,1392,1393,1394,
    1396,1397,1398,1399,1401,1402,1403,1404,1406,1407,1408,1409,1411,1412,1413,1414,
    1416,1417,1418,1419,1421,1422,1423,1424,1426,1427,1429,1430,1431,1432,1434,1435,
    1437,1438,1439,1440,1442,1443,1444,1445,1447,1448,1449,1450,1452,1453,1454,1455,
    1458,1459,1460,1461,1463,1464,1465,1466,1468,1469,1471,1472,1473,1474,1476,1477,
    1479,1480,1481,1482,1484,1485,1486,1487,1489,1490,1492,1493,1494,1495,1497,1498,
    1501,1502,1503,1504,1506,1507,1509,1510,1512,1513,1514,1515,1517,1518,1520,1521,
    1523,1524,1525,1526,1528,1529,1531,1532,1534,1535,1536,1537,1539,1540,1542,1543,
    1545,1546,1547,1548,1550,1551,1553,1554,1556,1557,1558,1559,1561,1562,1564,1565,
    1567,1568,1569,1570,1572,1573,1575,1576,1578,1579,1580,1581,1583,1584,1586,1587,
    1590,1591,1592,1593,1595,1596,1598,1599,1601,1602,1604,1605,1607,1608,1609,1610,
    1613,1614,1615,1616,1618,1619,1621,1622,1624,1625,1627,1628,1630,1631,1632,1633,
    1637,1638,1639,1640,1642,1643,1645,1646,1648,1649,1651,1652,1654,1655,1656,1657,
    1660,1661,1663,1664,1666,1667,1669,1670,1672,1673,1675,1676,1678,1679,1681,1682,
    1685,1686,1688,1689,1691,1692,1694,1695,1697,1698,1700,1701,1703,1704,1706,1707,
    1709,1710,1712,1713,1715,1716,1718,1719,1721,1722,1724,1725,1727,1728,1730,1731,
    1734,1735,1737,1738,1740,1741,1743,1744,1746,1748,1749,1751,1752,1754,1755,1757,
    1759,1760,1762,1763,1765,1766,1768,1769,1771,1773,1774,1776,1777,1779,1780,1782,
    1785,1786,1788,1789,1791,1793,1794,1796,1798,1799,1801,1802,1804,1806,1807,1809,
    1811,1812,1814,1815,1817,1819,1820,1822,1824,1825,1827,1828,1830,1832,1833,1835,
    1837,1838,1840,1841,1843,1845,1846,1848,1850,1851,1853,1854,1856,1858,1859,1861,
    1864,1865,1867,1868,1870,1872,1873,1875,1877,1879,1880,1882,1884,1885,1887,1888,
    1891,1892,1894,1895,1897,1899,1900,1902,1904,1906,1907,1909,1911,1912,1914,1915,
    1918,1919,1921,1923,1925,1926,1928,1930,1932,1933,1935,1937,1939,1940,1942,1944,
    1946,1947,1949,1951,1953,1954,1956,1958,1960,1961,1963,1965,1967,1968,1970,1972,
    1975,1976,1978,1980,1982,1983,1985,1987,1989,1990,1992,1994,1996,1997,1999,2001,
    2003,2004,2006,2008,2010,2011,2013,2015,2017,2019,2021,2022,2024,2026,2028,2029,
    2032,2033,2035,2037,2039,2041,2043,2044,2047,2048,2050,2052,2054,2056,2058,2059,
    2062,2063,2065,2067,2069,2071,2073,2074,2077,2078,2080,2082,2084,2086,2088,2089,
    2092,2093,2095,2097,2099,2101,2103,2104,2107,2108,2110,2112,2114,2116,2118,2119,
    2122,2123,2125,2127,2129,2131,2133,2134,2137,2139,2141,2142,2145,2146,2148,2150,
    2153,2154,2156,2158,2160,2162,2164,2165,2168,2170,2172,2173,2176,2177,2179,2181,
    2185,2186,2188,2190,2192,2194,2196,2197,2200,2202,2204,2205,2208,2209,2211,2213,
    2216,2218,2220,2222,2223,2226,2227,2230,2232,2234,2236,2238,2239,2242,2243,2246,
    2249,2251,2253,2255,2256,2259,2260,2263,2265,2267,2269,2271,2272,2275,2276,2279,
    2281,2283,2285,2287,2288,2291,2292,2295,2297,2299,2301,2303,2304,2307,2308,2311,
    2315,2317,2319,2321,2322,2325,2326,2329,2331,2333,2335,2337,2338,2341,2342,2345,
    2348,2350,2352,2354,2355,2358,2359,2362,2364,2366,2368,2370,2371,2374,2375,2378,
    2382,2384,2386,2388,2389,2392,2393,2396,2398,2400,2402,2404,2407,2410,2411,2414,
    2417,2419,2421,2423,2424,2427,2428,2431,2433,2435,2437,2439,2442,2445,2446,2449,
    2452,2454,2456,2458,2459,2462,2463,2466,2468,2470,2472,2474,2477,2480,2481,2484,
    2488,2490,2492,2494,2495,2498,2499,2502,2504,2506,2508,2510,2513,2516,2517,2520,
    2524,2526,2528,2530,2531,2534,2535,2538,2540,2542,2544,2546,2549,2552,2553,2556,
    2561,2563,2565,2567,2568,2571,2572,2575,2577,2579,2581,2583,2586,2589,2590,2593,
)


def opm_hz(kc, kf):
    """Exact YM2151 output frequency at the Rastan 4 MHz clock (matches the webVGM OPM emulator)."""
    octave = ((kc >> 4) & 7) + OCTAVE_OFFSET
    note4 = kc & 0xF
    semi = NOTE4.get(note4)
    if semi is None:                       # snap an invalid note code to the nearest valid one
        semi = NOTE4[min(NOTE4, key=lambda k: abs(k - note4))]
    i = semi * 64 + ((kf >> 2) & 0x3F)     # cent-index within the octave (64 steps/semitone)
    return PHASEINC_ROM[i] * YM2151_ACTUAL_CLOCK * 2.0 ** (octave - 28)


def ym2612_fnum_block(f):
    if f <= 0:
        return None
    best = None
    for block in range(8):
        fnum = int(round(f * 144 * (1 << (21 - block)) / YM2612_CLOCK))
        if 1 <= fnum <= 2047:
            best = (block, fnum)
            if fnum >= 1024:
                break
    return best


def psg_divider(f):
    if f <= 0:
        return 1
    return max(1, min(1023, int(round(SN76489_CLOCK / (32.0 * f)))))


class Writer:
    """Accumulates VGM command bytes with sample-accurate waits."""
    def __init__(self):
        self.data = bytearray()
        self.last = 0

    def wait_to(self, sample):
        d = sample - self.last
        while d > 0:
            n = min(d, 65535)
            self.data += bytes([0x61, n & 0xFF, (n >> 8) & 0xFF]); d -= n
        self.last = max(self.last, sample)

    def ym(self, port, reg, val):
        self.data += bytes([0x52 if port == 0 else 0x53, reg & 0xFF, val & 0xFF])

    def psg(self, byte):
        self.data += bytes([0x50, byte & 0xFF])


def level_offsets(levels):
    """Map a per-channel volume (0..200, 100 = original) to (fm_tl_add, psg_atten_add, muted) per channel.
    100 -> no change; <100 -> quieter (ADD attenuation); >100 -> louder (SUBTRACT attenuation, toward the
    chip max); 0 -> muted. The offsets are clamped to the chips' limits at emit time, so "boost" raises a
    voice toward full volume (TL 0 / atten 0) but cannot exceed it. fm_tl_add applies to the CARRIER TL."""
    fm_add = {}; psg_add = {}; muted = set()
    for ch, lv in (levels or {}).items():
        c = str(ch)
        try:
            lv = float(lv)
        except (TypeError, ValueError):
            continue
        if lv <= 0:
            muted.add(c); continue
        if lv == 100:
            continue
        cut_db = -20.0 * math.log10(lv / 100.0)          # +dB = attenuate (lv<100); -dB = boost (lv>100)
        fm_add[c] = int(round(cut_db / 0.75))            # YM2612 TL step = 0.75 dB (negative lowers TL)
        psg_add[c] = int(round(cut_db / 2.0))            # SN76489 atten step = 2 dB (negative lowers atten)
    return fm_add, psg_add, muted


def render(events, routing, noise_mode="fixed_1024", levels=None):
    """events: ordered [(sample,reg,val)]. routing: {ch(str)->dest}. levels: {ch(str)->0..100 volume}.
    Returns (vgm_bytes, stats)."""
    fm_add, psg_add, muted = level_offsets(levels)
    w = Writer()
    # per-arcade-channel pitch state (KC,KF) + key state + loudness state (algorithm, per-op TL)
    kc = [0] * 8
    kf = [0] * 8
    keyed = [False] * 8
    algo = [0] * 8
    tl = [[None] * 4 for _ in range(8)]
    fm_init_done = set()
    psg_atten = [15, 15, 15, 15]
    stats = {"fm_targets": set(), "psg_targets": set(), "ym2612_writes": 0, "psg_writes": 0,
             "dropped_channels": set()}

    def dest_of(ch):
        return routing.get(str(ch), "unassigned")

    # global init: YM2612 LFO off, ch3 normal, DAC off; PSG all channels silent
    w.ym(0, 0x22, 0x00); w.ym(0, 0x27, 0x00); w.ym(0, 0x2B, 0x00)
    for c in range(4):
        w.psg(0x80 | (c << 5) | 0x10 | 0x0F)   # atten 15 (off)

    def ensure_fm_init(tch):
        if tch not in fm_init_done:
            port, idx = YM_CH_PORT[tch]
            w.ym(port, 0xB4 + idx, 0xC0)       # L+R on (so the channel is audible)
            fm_init_done.add(tch); stats["fm_targets"].add(tch)
            stats["ym2612_writes"] += 1

    def fm_set_pitch(ch, tch):
        bf = ym2612_fnum_block(opm_hz(kc[ch], kf[ch]))
        if not bf:
            return
        block, fnum = bf
        port, idx = YM_CH_PORT[tch]
        w.ym(port, 0xA4 + idx, ((block & 7) << 3) | ((fnum >> 8) & 7))   # high first
        w.ym(port, 0xA0 + idx, fnum & 0xFF)                              # low latches
        stats["ym2612_writes"] += 2

    def psg_set_pitch(ch, tone):
        n = psg_divider(opm_hz(kc[ch], kf[ch]))
        w.psg(0x80 | (tone << 5) | (n & 0x0F))          # latch tone low 4 bits
        w.psg((n >> 4) & 0x3F)                           # data high 6 bits
        stats["psg_writes"] += 2

    def psg_atten_for(ch):
        """Estimate a PSG voice's attenuation (0=loud..15=off) from the source carrier TL + headroom +
        the user's per-channel volume trim."""
        carr = [o for o in CARRIER_OPS.get(algo[ch], (3,)) if tl[ch][o] is not None]
        lvl = min(tl[ch][o] for o in carr) if carr else 0      # 0 = loudest if unknown
        return max(0, min(15, int(round(lvl * PSG_TL_SCALE)) + PSG_HEADROOM + psg_add.get(str(ch), 0)))

    def psg_set_atten(tone, atten):
        w.psg(0x80 | (tone << 5) | 0x10 | (atten & 0x0F))
        psg_atten[tone] = atten
        stats["psg_writes"] += 1

    for sample, reg, val in events:
        w.wait_to(sample)
        # identify the arcade channel this register pertains to
        if reg == 0x08:
            ch = val & 7
        elif 0x20 <= reg <= 0x27:
            ch = reg - 0x20
        elif 0x28 <= reg <= 0x2F:
            ch = reg - 0x28
        elif 0x30 <= reg <= 0x37:
            ch = reg - 0x30
        elif 0x40 <= reg <= 0xFF:
            ch = reg & 7
        else:
            continue                                     # LFO/timer/global: skip for this stage
        # track loudness state for every channel (needed to set PSG attenuation from the source mix)
        if 0x20 <= reg <= 0x27:
            algo[ch] = val & 7
        elif 0x60 <= reg <= 0x7F:
            tl[ch][(reg >> 3) & 3] = val & 0x7F
        dest = dest_of(ch)
        if dest == "unassigned" or str(ch) in muted:
            stats["dropped_channels"].add(ch); continue

        is_fm = dest in FM_TARGET
        is_psg_tone = dest in PSG_TONE
        is_psg_noise = dest == "psg_noise"

        if reg == 0x08:                                  # KEY ON/OFF
            slots = (val >> 3) & 0xF
            if is_fm:
                tch = FM_TARGET[dest]; ensure_fm_init(tch)
                if slots:
                    fm_set_pitch(ch, tch)
                port_sel = YM_KEYSEL[tch]
                w.ym(0, 0x28, (slots << 4) | port_sel)   # key reg is always port 0
                stats["ym2612_writes"] += 1
                keyed[ch] = bool(slots)
            elif is_psg_tone:
                tone = PSG_TONE[dest]; stats["psg_targets"].add(dest)
                if slots:
                    psg_set_pitch(ch, tone)
                    psg_set_atten(tone, psg_atten_for(ch))   # volume tracks the source carrier TL
                else:
                    psg_set_atten(tone, 15)                   # off
                keyed[ch] = bool(slots)
            elif is_psg_noise:
                stats["psg_targets"].add("psg_noise")
                fb = 1 if noise_mode != "periodic" else 0     # white vs periodic
                rate = {"fixed_512": 0, "fixed_1024": 1, "fixed_2048": 2, "tone3_clocked": 3}.get(noise_mode, 1)
                if slots:
                    w.psg(0x80 | (3 << 5) | 0x00 | (fb << 2) | rate)  # noise control latch
                    psg_set_atten(3, psg_atten_for(ch))               # noise level tracks source TL
                    stats["psg_writes"] += 1
                else:
                    psg_set_atten(3, 15)                               # off
                keyed[ch] = bool(slots)

        elif 0x28 <= reg <= 0x2F:                        # KC
            kc[ch] = val
            if keyed[ch]:
                if is_fm:
                    fm_set_pitch(ch, FM_TARGET[dest])
                elif is_psg_tone:
                    psg_set_pitch(ch, PSG_TONE[dest])
        elif 0x30 <= reg <= 0x37:                        # KF
            kf[ch] = val
            if keyed[ch]:
                if is_fm:
                    fm_set_pitch(ch, FM_TARGET[dest])
                elif is_psg_tone:
                    psg_set_pitch(ch, PSG_TONE[dest])
        elif (is_psg_tone or is_psg_noise) and 0x60 <= reg <= 0x7F and keyed[ch]:
            # source carrier TL changed mid-note -> track the PSG voice's volume live
            a = psg_atten_for(ch)
            tgt = PSG_TONE[dest] if is_psg_tone else 3
            if a != psg_atten[tgt]:
                psg_set_atten(tgt, a)
        elif is_fm and 0x20 <= reg <= 0x27:              # FB|CONNECT(algo)|RL
            tch = FM_TARGET[dest]; ensure_fm_init(tch)
            port, idx = YM_CH_PORT[tch]
            algval = val & 7; fb = (val >> 3) & 7
            w.ym(port, 0xB0 + idx, (fb << 3) | algval)
            stats["ym2612_writes"] += 1
        elif is_fm and 0x40 <= reg <= 0xFF:              # operator parameter
            tch = FM_TARGET[dest]; ensure_fm_init(tch)
            opm_group = reg & 0xE0
            if opm_group in OPM2OPN2_GROUP:
                op = (reg >> 3) & 3
                port, idx = YM_CH_PORT[tch]
                oreg = OPM2OPN2_GROUP[opm_group] + op * 4 + idx
                v = val & 0x1F if opm_group == 0xC0 else val    # 0xC0->0x70: keep D2R, drop DT2
                if opm_group == 0x60 and op in CARRIER_OPS.get(algo[ch], (3,)):
                    # volume on carrier TL: + attenuates, - boosts; clamp to [0,127] (0 = chip max)
                    v = max(0, min(127, (val & 0x7F) + fm_add.get(str(ch), 0)))
                w.ym(port, oreg, v)
                stats["ym2612_writes"] += 1
        # PSG-routed channels ignore FM operator/algo writes (no equivalent on a square channel)

    w.data += bytes([0x66])                              # end
    total = events[-1][0] if events else 0

    hdr = bytearray(0x40)
    hdr[0x00:0x04] = b"Vgm "
    struct.pack_into("<I", hdr, 0x08, 0x151)
    struct.pack_into("<I", hdr, 0x0C, SN76489_CLOCK)    # SN76489 clock (0x0C)
    struct.pack_into("<I", hdr, 0x18, total)
    struct.pack_into("<I", hdr, 0x24, 60)
    struct.pack_into("<I", hdr, 0x28, 0x0009)           # SN76489 feedback (std)
    hdr[0x2A] = 16                                       # SN76489 shift register width
    struct.pack_into("<I", hdr, 0x2C, YM2612_CLOCK)     # YM2612 clock (0x2C)
    struct.pack_into("<I", hdr, 0x34, 0x0C)
    vgm = bytearray(bytes(hdr) + bytes(w.data))
    struct.pack_into("<I", vgm, 0x04, len(vgm) - 4)
    stats["fm_targets"] = sorted(stats["fm_targets"])
    stats["psg_targets"] = sorted(stats["psg_targets"])
    stats["dropped_channels"] = sorted(stats["dropped_channels"])
    stats["total_samples"] = total
    stats["duration_s"] = round(total / VGM_RATE, 3)
    return bytes(vgm), stats


def read_capture(path):
    ev = []
    for row in csv.DictReader(open(path, newline="")):
        try:
            ev.append((int(float(row["sample"])), int(row["register"], 16), int(row["value"], 16)))
        except (ValueError, KeyError):
            continue
    return ev


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capture", help="path to a *_ym2151_writes.csv")
    ap.add_argument("--routing", required=True, help='JSON {"0":"ym2612_fm1","5":"psg_tone1",...}')
    ap.add_argument("--levels", default="{}", help='JSON {"5":60,...} per-channel volume 0..100 (100=original)')
    ap.add_argument("--noise", default="fixed_1024")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    vgm, stats = render(read_capture(a.capture), json.loads(a.routing), a.noise, json.loads(a.levels))
    open(a.out, "wb").write(vgm)
    print(json.dumps(stats, indent=1))
    print("wrote", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
