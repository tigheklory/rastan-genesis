# Mega EverDrive EX-SSF Mapper Documentation

**Source:** [extended_ssf-v2.txt](https://krikzz.com/pub/support/mega-everdrive/x3x5x7/dev/extended_ssf-v2.txt)  
**Author:** krikzz.com (22.09.2014)  
*Note: Please check `ssf-ex-sample` for details.*

---

## Extensions

1. Mapper allows use of up to 16 or 32 Mbyte of memory (depends on installed memory chip).
2. Write access to ROM memory. **ROM memory can be used as RAM.**
3. First bank can be switched like any other bank.
4. Onboard LED control.
5. Hardware division and multiplication.
6. Access to USB IO.
7. Access to SD IO.

---

## Registers

### Math Registers
*For division or multiplication. Can operate with 16 or 32-bit numbers. Unsigned values.*
*(Note: Math registers were removed in the last OS version due to the lack of space for the SMS FM core.)*

* `0xA130D0` **MATH_ARG_HI** (read/write)
* `0xA130D2` **MATH_ARG_LO** (read/write)
* `0xA130D4` **MATH_MUL_HI** (write only)
* `0xA130D6` **MATH_MUL_LO** (write only)
* `0xA130D8` **MATH_DIV_HI** (write only)
* `0xA130DA` **MATH_DIV_LO** (write only)

**Operations:**
* **Mul result** = `MATH_ARG` * `MATH_MUL`
* **Div result** = `MATH_ARG` / `MATH_DIV`
* *First `MATH_ARG` should be written, then `MATH_MUL` or `MATH_DIV`. Read result from `MATH_ARG`. Check `ssf-ex-sample` for more details.*

### SD Card
* `0xA130E0` `[DDDDDDDD dddddddd]` (read/write)
  * `d`: lo data bits
  * `D`: hi data bits (active only in 16-bit mode)

### USB IO
* `0xA130E2` `[........ DDDDDDDD]` (read/write)
  * `D`: data bits

### IO Status
* `0xA130E4` `[.C...... .....RWS]` (read only)
  * `S`: SPI controller ready
  * `W`: USB fifo ready to write
  * `R`: USB fifo ready to read
  * `C`: SD card type. `0`=SD, `1`=SDHC

### IO Config
* `0xA130E6` `[........ .....AMS]` (write only)
  * `S`: Directly connected to SD card chip select
  * `M`: 16-bit SPI mode
  * `A`: Auto read. Allows reading data from SPI without writing. Should be used in pair with 16-bit mode.

### Mapper Control
* `0xA130F0` `[PXWL.... ...RRRRR]` (write only)
  * `P`: Protection bit. Bit `P` always should be set for any manipulations with reg `0xA130F0` (`0`=access to register is denied, `1`=new value can be loaded).
  * `X`: 32x mode. Should be set in case the game uses 32x.
  * `W`: ROM memory write protect (`0`=not writable, `1`=writable).
  * `L`: LED (`0`=off, `1`=on).
  * `R`: 512Kbyte bank.

* `0xA130F2` - `0xA130FE` `[........ ...RRRRR]` (write only)
  * `R`: 512Kbyte bank.

---

## Important Usage Notes

* **Activation:** Mapper will be activated in case the ROM header contains the `"SEGA SSF"` string, instead of the standard `"SEGA GENESIS"` string.
* **OS Banks:** Banks 30-31 are used by the OS. It is not recommended to touch them, otherwise the OS may not boot after a reset (in this case, the OS will start only after a cold start).
* **Save RAM:** Bank 31 can be used for saves. The upper 256K of this bank is mapped to battery SRAM.