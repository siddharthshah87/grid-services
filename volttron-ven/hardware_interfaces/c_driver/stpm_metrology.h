/**
  ******************************************************************************
  * @file    stpm_metrology.h
  * @author  AMG/IPC Application Team
  * @brief   This file contains all the functions prototypes for the Metrology
  @verbatim
  @endverbatim

  ******************************************************************************
  * @attention
  *
  * <h2><center>&copy; COPYRIGHT(c) 2018 STMicroelectronics</center></h2>
  *
  * Redistribution and use in source and binary forms, with or without modification,
  * are permitted provided that the following conditions are met:
  *   1. Redistributions of source code must retain the above copyright notice,
  *      this list of conditions and the following disclaimer.
  *   2. Redistributions in binary form must reproduce the above copyright notice,
  *      this list of conditions and the following disclaimer in the documentation
  *      and/or other materials provided with the distribution.
  *   3. Neither the name of STMicroelectronics nor the names of its contributors
  *      may be used to endorse or promote products derived from this software
  *      without specific prior written permission.
  *
  * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
  * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
  * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
  * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
  * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
  * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
  * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
  * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
  * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
  * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
  *
  ******************************************************************************
  */


/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __STPM_METROLOGY_H
#define __STPM_METROLOGY_H

#ifdef __cplusplus
 extern "C" {
#endif

   /**
  * @brief Metrology
  */
#include <stdint.h>

typedef struct
{
  /* RW reg */
   uint32_t DSPCTRL1;                       /*!< DSP Control Register 1,	                        Address offset: 0x000 */
   uint32_t DSPCTRL2;                       /*!< DSP Control Register 2,	                        Address offset: 0x004 */
   uint32_t DSPCTRL3;                       /*!< DSP Control Register 3,	                        Address offset: 0x008 */
   uint32_t DSPCTRL4;                       /*!< DSP Control Register 4,	                        Address offset: 0x00C */
   uint32_t DSPCTRL5;                       /*!< DSP Control Register 5,	                        Address offset: 0x010 */
   uint32_t DSPCTRL6;                       /*!< DSP Control Register 6,	                        Address offset: 0x014 */
   uint32_t DSPCTRL7;                       /*!< DSP Control Register 7,	                        Address offset: 0x018 */
   uint32_t DSPCTRL8;                       /*!< DSP Control Register 8,	                        Address offset: 0x01C */
   uint32_t DSPCTRL9;                       /*!< DSP Control Register 9,	                        Address offset: 0x020 */
   uint32_t DSPCTRL10;                      /*!< DSP Control Register 10,	                        Address offset: 0x024 */
   uint32_t DSPCTRL11;                      /*!< DSP Control Register 11,	                        Address offset: 0x028 */
   uint32_t DSPCTRL12;                      /*!< DSP Control Register 12,	                        Address offset: 0x02C */
   uint32_t DFECTRL1;                       /*!< DFE Control Register 1,	                        Address offset: 0x030 */
   uint32_t DFECTRL2;                       /*!< DFE Control Register 2,	                        Address offset: 0x034 */
   uint32_t DSPIRQ1;                        /*!< DSP Interrupt Register 1,	                        Address offset: 0x038 */
   uint32_t DSPIRQ2;                        /*!< DSP Interrupt Register 2,	                        Address offset: 0x03C */
   uint32_t DSPSR1;                         /*!< DSP Status Register 1,	                        Address offset: 0x040 */
   uint32_t DSPSR2;                         /*!< DSP Status Register 2,	                        Address offset: 0x044 */
   uint32_t UARTSPICR1;                     /*!< UART/SPI Control Register 1,	                Address offset: 0x048 */
   uint32_t UARTSPICR2;                     /*!< UART/SPI Control Register 2,	                Address offset: 0x04C */
   uint32_t UARTSPISR;                      /*!< UART/SPI Status Register ,	                        Address offset: 0x050 */
   
   /* RO regs */ 
   uint32_t DSPEVENT1;                      /*!< DSP Events Register 1,	                        Address offset: 0x054 */ 
    uint32_t DSPEVENT2;                      /*!< DSP Events Register 2,	                        Address offset: 0x058 */
    uint32_t DSP_REG1;                       /*!< DSP Register 1,                                    Address offset: 0x05C */
    uint32_t DSP_REG2;                       /*!< DSP Register 2,                                    Address offset: 0x060 */
    uint32_t DSP_REG3;                       /*!< DSP Register 3,                                    Address offset: 0x064 */
    uint32_t DSP_REG4;                       /*!< DSP Register 4,                                    Address offset: 0x068 */
    uint32_t DSP_REG5;                       /*!< DSP Register 5,                                    Address offset: 0x06C */
    uint32_t DSP_REG6;                       /*!< DSP Register 6,                                    Address offset: 0x070 */
    uint32_t DSP_REG7;                       /*!< DSP Register 7,                                    Address offset: 0x074 */
    uint32_t DSP_REG8;                       /*!< DSP Register 8,                                    Address offset: 0x078 */
    uint32_t DSP_REG9;                       /*!< DSP Register 9,                                    Address offset: 0x07C*/
    uint32_t DSP_REG10;                      /*!< DSP Register 10,                                   Address offset: 0x080*/
    uint32_t DSP_REG11;                      /*!< DSP Register 11,                                   Address offset: 0x084*/
    uint32_t DSP_REG12;                      /*!< DSP Register 12,                                   Address offset: 0x088*/
    uint32_t DSP_REG13;                      /*!< DSP Register 13,                                   Address offset: 0x08C*/
    uint32_t DSP_REG14;                      /*!< DSP Register 14,                                   Address offset: 0x090*/
    uint32_t DSP_REG15;                      /*!< DSP Register 15,                                   Address offset: 0x094*/
    uint32_t DSP_REG16;                      /*!< DSP Register 16,                                   Address offset: 0x098 */
    uint32_t DSP_REG17;                      /*!< DSP Register 17,                                   Address offset: 0x09C */
    uint32_t DSP_REG18;                      /*!< DSP Register 18,                                   Address offset: 0x0A0*/
    uint32_t DSP_REG19;                      /*!< DSP Register 19,                                   Address offset: 0x0A4*/
    uint32_t CH1_REG1;                       /*!< Channel 1 Register 1,                              Address offset: 0x0A8*/
    uint32_t CH1_REG2;                       /*!< Channel 1 Register 2,                              Address offset: 0x0AC*/
    uint32_t CH1_REG3;                       /*!< Channel 1 Register 3,                              Address offset: 0x0B0 */
    uint32_t CH1_REG4;                       /*!< Channel 1 Register 4,                              Address offset: 0x0B4*/
    uint32_t CH1_REG5;                       /*!< Channel 1 Register 5,                              Address offset: 0x0B8*/
    uint32_t CH1_REG6;                       /*!< Channel 1 Register 6,                              Address offset:  */
    uint32_t CH1_REG7;                       /*!< Channel 1 Register 7,                              Address offset:  */
    uint32_t CH1_REG8;                       /*!< Channel 1 Register 8,                              Address offset:  */
    uint32_t CH1_REG9;                       /*!< Channel 1 Register 9,                              Address offset:  */
    uint32_t CH1_REG10;                      /*!< Channel 1 Register 10,                             Address offset:  */
    uint32_t CH1_REG11;                      /*!< Channel 1 Register 11,                             Address offset:  */
    uint32_t CH1_REG12;                      /*!< Channel 1 Register 12,                             Address offset:  */
    uint32_t CH2_REG1;                       /*!< Channel 2 Register 1,                              Address offset:  */
    uint32_t CH2_REG2;                       /*!< Channel 2 Register 2,                              Address offset:  */
    uint32_t CH2_REG3;                       /*!< Channel 2 Register 3,                              Address offset:  */
    uint32_t CH2_REG4;                       /*!< Channel 2 Register 4,                              Address offset:  */
    uint32_t CH2_REG5;                       /*!< Channel 2 Register 5,                              Address offset:  */
    uint32_t CH2_REG6;                       /*!< Channel 2 Register 6,                              Address offset:  */
    uint32_t CH2_REG7;                       /*!< Channel 2 Register 7,                              Address offset:  */
    uint32_t CH2_REG8;                       /*!< Channel 2 Register 8,                              Address offset:  */
    uint32_t CH2_REG9;                       /*!< Channel 2 Register 9,                              Address offset:  */
    uint32_t CH2_REG10;                      /*!< Channel 2 Register 10,                             Address offset:  */
    uint32_t CH2_REG11;                      /*!< Channel 2 Register 11,                             Address offset:  */
    uint32_t CH2_REG12;                      /*!< Channel 2 Register 12,                             Address offset:  */
    uint32_t TOT_REG1;                       /*!< Total  Register 1,                                 Address offset:  */
    uint32_t TOT_REG2;                       /*!< Total  Register 2,                                 Address offset:  */
    uint32_t TOT_REG3;                       /*!< Total  Register 3,                                 Address offset:  */
    uint32_t TOT_REG4;                       /*!< Total  Register 4,                                 Address offset:  */

} METRO_STPM_TypeDef;

/* STPM address */
typedef enum {
   STPM_DSPCTRL1        = 0x00, /*!< DSP Control Register 1 */
   STPM_DSPCTRL2        = 0x02, /*!< DSP Control Register 2 */
   STPM_DSPCTRL3        = 0x04, /*!< DSP Control Register 3 */
   STPM_DSPCTRL4        = 0x06, /*!< DSP Control Register 4 */
   STPM_DSPCTRL5        = 0x08, /*!< DSP Control Register 5 */
   STPM_DSPCTRL6        = 0x0A, /*!< DSP Control Register 6 */
   STPM_DSPCTRL7        = 0x0C, /*!< DSP Control Register 7 */
   STPM_DSPCTRL8        = 0x0E, /*!< DSP Control Register 8 */
   STPM_DSPCTRL9        = 0x10, /*!< DSP Control Register 9 */
   STPM_DSPCTRL10       = 0x12, /*!< DSP Control Register 10 */
   STPM_DSPCTRL11       = 0x14, /*!< DSP Control Register 11 */
   STPM_DSPCTRL12       = 0x16, /*!< DSP Control Register 12 */
   STPM_DFECTRL1        = 0x18, /*!< DFE Control Register 1 */
   STPM_DFECTRL2        = 0x1A, /*!< DFE Control Register 2 */
   STPM_DSPIRQ1         = 0x1C, /*!< DSP Interrupt Register 1 */
   STPM_DSPIRQ2         = 0x1E, /*!< DSP Interrupt Register 2 */
   STPM_DSPSR1          = 0x20, /*!< DSP Status Register 1 */
   STPM_DSPSR2          = 0x22, /*!< DSP Status Register 2 */
   STPM_USREG1          = 0x24, /*!< UART/SPI Control Register 1 */
   STPM_USREG2          = 0x26, /*!< UART/SPI Control Register 2 */
   STPM_USREG3          = 0x28, /*!< UART/SPI Status Register */
   
   /* RO regs */ 
   STPM_DSPEVENT1       = 0x2A, /*!< DSP Events Register 1 */ 
   STPM_DSPEVENT2       = 0x2C, /*!< DSP Events Register 2 */
   STPM_DSP_REG1        = 0x2E, /*!< DSP Register 1 */
   STPM_DSP_REG2        = 0x30, /*!< DSP Register 2 */
   STPM_DSP_REG3        = 0x32, /*!< DSP Register 3 */
   STPM_DSP_REG4        = 0x34, /*!< DSP Register 4 */
   STPM_DSP_REG5        = 0x36, /*!< DSP Register 5 */
   STPM_DSP_REG6        = 0x38, /*!< DSP Register 6 */
   STPM_DSP_REG7        = 0x3A, /*!< DSP Register 7 */
   STPM_DSP_REG8        = 0x3C, /*!< DSP Register 8 */
   STPM_DSP_REG9        = 0x3E, /*!< DSP Register 9 */
   STPM_DSP_REG10       = 0x40, /*!< DSP Register 10 */
   STPM_DSP_REG11       = 0x42, /*!< DSP Register 11 */
   STPM_DSP_REG12       = 0x44, /*!< DSP Register 12 */
   STPM_DSP_REG13       = 0x46, /*!< DSP Register 13 */
   STPM_DSP_REG14       = 0x48, /*!< DSP Register 14 */
   STPM_DSP_REG15       = 0x4A, /*!< DSP Register 15 */
   STPM_DSP_REG16       = 0x4C, /*!< DSP Register 16 */
   STPM_DSP_REG17       = 0x4E, /*!< DSP Register 17 */
   STPM_DSP_REG18       = 0x50, /*!< DSP Register 18 */
   STPM_DSP_REG19       = 0x52, /*!< DSP Register 19 */
   STPM_CH1_REG1        = 0x54, /*!< Channel 1 Register 1 */
   STPM_CH1_REG2        = 0x56, /*!< Channel 1 Register 2 */
   STPM_CH1_REG3        = 0x58, /*!< Channel 1 Register 3 */
   STPM_CH1_REG4        = 0x5A, /*!< Channel 1 Register 4 */
   STPM_CH1_REG5        = 0x5C, /*!< Channel 1 Register 5 */
   STPM_CH1_REG6        = 0x5E, /*!< Channel 1 Register 6 */
   STPM_CH1_REG7        = 0x60, /*!< Channel 1 Register 7 */
   STPM_CH1_REG8        = 0x62, /*!< Channel 1 Register 8 */
   STPM_CH1_REG9        = 0x64, /*!< Channel 1 Register 9 */
   STPM_CH1_REG10       = 0x66, /*!< Channel 1 Register 10 */
   STPM_CH1_REG11       = 0x68, /*!< Channel 1 Register 11 */
   STPM_CH1_REG12       = 0x6A, /*!< Channel 1 Register 12 */
   STPM_CH2_REG1        = 0x6C, /*!< Channel 2 Register 1 */
   STPM_CH2_REG2        = 0x6E, /*!< Channel 2 Register 2 */
   STPM_CH2_REG3        = 0x70, /*!< Channel 2 Register 3 */
   STPM_CH2_REG4        = 0x72, /*!< Channel 2 Register 4 */
   STPM_CH2_REG5        = 0x74,  /*!< Channel 2 Register 5 */
   STPM_CH2_REG6        = 0x76, /*!< Channel 2 Register 6 */
   STPM_CH2_REG7        = 0x78, /*!< Channel 2 Register 7 */
   STPM_CH2_REG8        = 0x7A, /*!< Channel 2 Register 8 */
   STPM_CH2_REG9        = 0x7C, /*!< Channel 2 Register 9 */
   STPM_CH2_REG10       = 0x7E, /*!< Channel 2 Register 10 */
   STPM_CH2_REG11       = 0x80, /*!< Channel 2 Register 11 */
   STPM_CH2_REG12       = 0x82, /*!< Channel 2 Register 12 */
   STPM_TOT_REG1        = 0x84, /*!< Total  Register 1 */
   STPM_TOT_REG2        = 0x86, /*!< Total  Register 2 */
   STPM_TOT_REG3        = 0x88, /*!< Total  Register 3 */
   STPM_TOT_REG4        = 0x8A, /*!< Total  Register 4 */

}METRO_STPM_addressTypeDef;


#define METRO_STPM_PERIPH_BASE         0x0000
#define METRO_STPM       ((METRO_STPM_TypeDef *)   METRO_STPM_PERIPH_BASE)   /*!< Metrology Peripheral definition */

#define METRO_STPM_CTRL_REG_NB_BLOCKS       21
#define METRO_STPM_DATA_REG_NB_BLOCKS       49
#define METRO_STPM_DSP_DATA_REG_NB_BLOCKS   21
#define METRO_STPM_PH1_DATA_REG_NB_BLOCKS   12
#define METRO_STPM_PH2_DATA_REG_NB_BLOCKS   12
#define METRO_STPM_TOT_DATA_REG_NB_BLOCKS   4
#define METRO_STPM_TOTAL_DATA_REG           70

/** @addtogroup Metrology
  * @{
  */

/* Exported types ------------------------------------------------------------*/


/* Exported constants --------------------------------------------------------*/

/** @defgroup Metrology_Exported_Constants
  * @{
  */

    

 /** @defgroup METRO_STPM BaudRate for UART
  * @{
  */
#define METRO_STPM_UART_BAUDRATE_2400   ((uint32_t)0x1A0B) /*!< 2400 */
#define METRO_STPM_UART_BAUDRATE_9600   ((uint32_t)0x683)  /*!< 9600 : it is the value after reset of STPM */
#define METRO_STPM_UART_BAUDRATE_19200  ((uint32_t)0x341)  /*!< 19200 */
#define METRO_STPM_UART_BAUDRATE_57600  ((uint32_t)0x116)  /*!< 57600 */
#define METRO_STPM_UART_BAUDRATE_115200 ((uint32_t)0x8B)   /*!< 115200 */
#define METRO_STPM_UART_BAUDRATE_230400 ((uint32_t)0x45)   /*!< 230400 */    
#define METRO_STPM_UART_BAUDRATE_460800 ((uint32_t)0x23)   /*!< 460800 */
    /**
  * @}
  */

/** @defgroup METRO_STPM_Reset
  * @{
  */
#define METRO_STPM_Reset_Bit ((uint32_t)0x00200000) /*!< METROLOGY reset bit */
/**
  * @}
  */


/** @addtogroup METRO_STPM_Bit_Field_Mask_Definitions
  * @{
  */

/********** Bitmask definition for DSP Control Register 1 and 2  for Channel one and 2 of STPM chip ***************/
#define BIT_MASK_STPM_LED_CH_SEL            (uint32_t)0xC0000000 /*!< Bitmask for LED_Program bits in DPS Control register 1 */
#define BIT_MASK_STPM_LED_CH_SEL_SHIFT      30

#define BIT_MASK_STPM_LED_POWER_SEL         (uint32_t)0x30000000 /*!< Bitmask for Primary_Channel_Pulse_Select bits in DPS Control register 1 */
#define BIT_MASK_STPM_LED_POWER_SEL_SHIFT   28

#define BIT_MASK_STPM_LED_SPEED_DIV         (uint32_t)0x0F000000 /*!< Bitmask for Primary_Channel_Pulse_Select bits in DPS Control register 1 */
#define BIT_MASK_STPM_LED_SPEED_DIV_SHIFT   24

#define BIT_MASK_STPM_CURR_LPF_BYPASS       (uint32_t)0x00800000 /*!< Bitmask for Current_LPF_Bypass bit */
#define BIT_MASK_STPM_CURR_LPF_BYPASS_SHIFT 23        
#define BIT_MASK_STPM_VOLT_LPF_BYPASS       (uint32_t)0x00400000 /*!< Bitmask for Voltage_LPF_Bypass bit  */
#define BIT_MASK_STPM_VOLT_LPF_BYPASS_SHIFT 22
#define BIT_MASK_STPM_CURR_ROGOWSKY_SEL     (uint32_t)0x00200000 /*!< Bitmask for Current_Rogowsky_Select bit  */
#define BIT_MASK_STPM_CURR_ROGOWSKY_SEL_SHIFT 21
#define BIT_MASK_STPM_CURR_HPF_BYPASS       (uint32_t)0x00100000 /*!< Bitmask for Current_HPF_Bypass bit  */
#define BIT_MASK_STPM_CURR_HPF_BYPASS_SHIFT  20
#define BIT_MASK_STPM_VOLT_HPF_BYPASS       (uint32_t)0x00080000 /*!< Bitmask for Voltage_HPF_Bypass bit  */
#define BIT_MASK_STPM_VOLT_HPF_BYPASS_SHIFT  19

#define BIT_MASK_STPM_APM                   (uint32_t)0x00040000 /*!< Bitmask for Apparent vectorial power mode  */
#define BIT_MASK_STPM_AEM                   (uint32_t)0x00020000 /*!< Bitmask for Apparent energy mode  */
#define BIT_MASK_STPM_TC                    (uint32_t)0x000001C0 /*!< Bitmask for Temperature compensation coefficient   voltage reference VREF1 */
#define BIT_MASK_STPM_TC_SHIFT              6

#define BIT_MASK_STPM_ENVREF1               (uint32_t)0x00000020 /*!< Bitmask for Enable internal voltage reference  */
#define BIT_MASK_STPM_ENVREF1_SHIFT         5

#define BIT_MASK_STPM_ENVREF2               (uint32_t)0x00000020 /*!< Bitmask for Enable internal voltage reference  */
#define BIT_MASK_STPM_ENVREF2_SHIFT         5

#define BIT_MASK_STPM_CLEAR_SAG_SWELL       (uint32_t)0x00000010 /*!< Clear sag and swell time register and history bits , auto-reset to '0'*/
#define BIT_MASK_STPM_CLR_SS_TIME_OUT       (uint32_t)0x0000000F /*!< Bitmask for Clr_SS_Time_Out bits  */


/**************** Bitmask definition for DSP Control Register 3 ***************/
#define BIT_MASK_STPM_REF_FREQ              (uint32_t)0x08000000 /*!< Bitmask for Reference line frequency : 50 or 60Hz*/
#define BIT_MASK_STPM_EN_CUM                (uint32_t)0x04000000 /*!< Bitmask for Enable cumulative energy calculation */
#define BIT_MASK_STPM_LED2_OFF              (uint32_t)0x02000000 /*!< Bitmask for LED 2 Enable bit in DPS Control register 3 */
#define BIT_MASK_STPM_LED2_OFF_SHIFT         25
#define BIT_MASK_STPM_LED1_OFF              (uint32_t)0x01000000 /*!< Bitmask for LED 1 Enable bit in DPS Control register 3 */
#define BIT_MASK_STPM_LED1_OFF_SHIFT         24
#define BIT_MASK_STPM_AUTO_LATCH            (uint32_t)0x00800000 /*!< Bitmask for Auto_latch bit in DPS Control register 3 */
#define BIT_MASK_STPM_LATCH2                (uint32_t)0x00400000 /*!< Bitmask for Latch2 bit in DPS Control register 3 */
#define BIT_MASK_STPM_LATCH1                (uint32_t)0x00200000 /*!< Bitmask for Latch1 bit in DPS Control register 3 */
#define BIT_MASK_STPM_SW_RESET              (uint32_t)0x00100000 /*!< Bitmask for Reset bit in DPS Control register 3 */
#define BIT_MASK_STPM_TAMPER_ENABLE         (uint32_t)0x00080000 /*!< Bitmask for Tamper_Enable bit in DPS Control register 3 */
#define BIT_MASK_STPM_TAMPER_ENABLE_SHIFT   19     
#define BIT_MASK_STPM_TAMPER_TOLERANCE      (uint32_t)0x00060000 /*!< Bitmask for Tamper_Tolerance bits in DPS Control register 3 */
#define BIT_MASK_STPM_TAMPER_TOLERANCE_SHIFT 17      

/* CLOCK and ZCR are managed inside the same bits in thsi register */
/* Double definition of the same bits are made to not confuse the user */    

#define BIT_MASK_STPM_ZCR_ENA               (uint32_t)0x00010000 /*!< Bitmask for ZCR Enable bit in DPS Control register 3 */
#define BIT_MASK_STPM_ZCR_ENA_SHIFT         16
#define BIT_MASK_STPM_ZCR_SEL               (uint32_t)0x0000C000 /*!< Bitmask for ZCR_Select bits in DPS Control register 3 */
#define BIT_MASK_STPM_ZCR_SEL_SHIFT         14

#define BIT_MASK_STPM_CLK_ENA               (uint32_t)0x00010000 /*!< Bitmask for CLK Enable bit in DPS Control register 3 */
#define BIT_MASK_STPM_CLK_ENA_SHIFT         16
#define BIT_MASK_STPM_CLK_SEL               (uint32_t)0x0000C000 /*!< Bitmask for CLK_Select bits in DPS Control register 3 */
#define BIT_MASK_STPM_CLK_SEL_SHIFT         14


#define BIT_MASK_STPM_TIME_VALUE            (uint32_t)0x00003FFF /*!< Bitmask for Time_Value bits in DPS Control register 3 */

/*************** Bitmask definition for DSP Control Register 4   ***************/
#define BIT_MASK_STPM_PHASE_SHIFT_V1        (uint32_t)0x00C00000 /*!< Bitmask for Phase_Shift_V1 bits  */
#define BIT_MASK_STPM_PHASE_SHIFT_V1_SHIFT   22       
#define BIT_MASK_STPM_PHASE_SHIFT_C1        (uint32_t)0x003FF000 /*!< Bitmask for Phase_Shift_C1 bits  */
#define BIT_MASK_STPM_PHASE_SHIFT_C1_SHIFT   12
#define BIT_MASK_STPM_PHASE_SHIFT_V2        (uint32_t)0x00000C00 /*!< Bitmask for Phase_Shift_V2 bits  */
#define BIT_MASK_STPM_PHASE_SHIFT_V2_SHIFT   10         
#define BIT_MASK_STPM_PHASE_SHIFT_C2        (uint32_t)0x000003FF /*!< Bitmask for Phase_Shift_C2 bits  */



/*************** Bitmask definition for DSP Control Register 5   ***************/
#define BIT_MASK_STPM_SAGVALUE_V1              (uint32_t)0xFFC00000 /*!< Bitmask for SAG_VALUE_V1 bits in dsp_cr5 register */
#define BIT_MASK_STPM_SAGVALUE_V1_SHIFT        22
#define BIT_MASK_STPM_SWELL_VALUE_V1           (uint32_t)0x003FF000 /*!< Bitmask for Swell_Value_V1 bits in dsp_cr5 register */
#define BIT_MASK_STPM_SWELL_VALUE_V1_SHIFT     12
#define BIT_MASK_STPM_CAL_V1                   (uint32_t)0x00000FFF /*!< Bitmask for Cal_V1 bits in dsp_cr5 register */

/*************** Bitmask definition for DSP Control Register 6   ***************/
#define BIT_MASK_STPM_SWELL_VALUE_C1           (uint32_t)0x003FF000 /*!< Bitmask for Swell_Value_C1 bits in dsp_cr6 register */
#define BIT_MASK_STPM_SWELL_VALUE_C1_SHIFT      12
#define BIT_MASK_STPM_CAL_C1                   (uint32_t)0x00000FFF /*!< Bitmask for Cal_C1 bits in dsp_cr6 register */

/*************** Bitmask definition for DSP Control Register 7   ***************/
#define BIT_MASK_STPM_SAGVALUE_V2              (uint32_t)0xFFC00000 /*!< Bitmask for SAG_VALUE_V2 bits in dsp_cr5 register */
#define BIT_MASK_STPM_SAGVALUE_V2_SHIFT        22
#define BIT_MASK_STPM_SWELL_VALUE_V2           (uint32_t)0x003FF000 /*!< Bitmask for Swell_Value_V2 bits in dsp_cr5 register */
#define BIT_MASK_STPM_SWELL_VALUE_V2_SHIFT     12
#define BIT_MASK_STPM_CAL_V2                   (uint32_t)0x00000FFF /*!< Bitmask for Cal_V2 bits in dsp_cr5 register */

/*************** Bitmask definition for DSP Control Register 8  ***************/
#define BIT_MASK_STPM_SWELL_VALUE_C2           (uint32_t)0x003FF000 /*!< Bitmask for Swell_Value_C2 bits in dsp_cr6 register */
#define BIT_MASK_STPM_SWELL_VALUE_C2_SHIFT     12
#define BIT_MASK_STPM_CAL_C2                   (uint32_t)0x00000FFF /*!< Bitmask for Cal_C2 bits in dsp_cr6 register */

/*************** Bitmask definition for DSP Control Register 9 ***************/
#define BIT_MASK_STPM_OFFSET_AF1               (uint32_t)0xFFC00000 /*!< Bitmask for Offset_AF1 bits in dsp_cr9 register */
#define BIT_MASK_STPM_OFFSET_A1                (uint32_t)0x003FF000 /*!< Bitmask for Offset_A1 bits in dsp_cr9 register */
#define BIT_MASK_STPM_RMS1_VALUE_MAX           (uint32_t)0x00000FFF /*!< Bitmask for RMS1_Value_Max bits in dsp_cr9 register */

/*************** Bitmask definition for DSP Control Register 10   **************/
#define BIT_MASK_STPM_OFFSET_S1                (uint32_t)0xFFC00000 /*!< Bitmask for Offset_S1 bits in dsp_cr10 register */
#define BIT_MASK_STPM_OFFSET_R1                (uint32_t)0x003FF000 /*!< Bitmask for Offset_R1 bits in dsp_cr10 register */
#define BIT_MASK_STPM_RMS1_VALUE_MIN           (uint32_t)0x00000FFF /*!< Bitmask for RMS1_Value_Min bits in dsp_cr10 register */

/*************** Bitmask definition for DSP Control Register 11   **************/
#define BIT_MASK_STPM_OFFSET_AF2               (uint32_t)0xFFC00000 /*!< Bitmask for Offset_AF2 bits in dsp_cr9 register */
#define BIT_MASK_STPM_OFFSET_A2                (uint32_t)0x003FF000 /*!< Bitmask for Offset_A2 bits in dsp_cr9 register */
#define BIT_MASK_STPM_RMS2_VALUE_MAX           (uint32_t)0x00000FFF /*!< Bitmask for RMS2_Value_Max bits in dsp_cr9 register */

/*************** Bitmask definition for DSP Control Register 12   **************/
#define BIT_MASK_STPM_OFFSET_S2                (uint32_t)0xFFC00000 /*!< Bitmask for Offset_S2 bits in dsp_cr10 register */
#define BIT_MASK_STPM_OFFSET_R2                (uint32_t)0x003FF000 /*!< Bitmask for Offset_R2 bits in dsp_cr10 register */
#define BIT_MASK_STPM_RMS2_VALUE_MIN           (uint32_t)0x00000FFF /*!< Bitmask for RMS2_Value_Min bits in dsp_cr10 register */

    
#define BIT_MASK_STPM_OFFSET_AF_SHIFT           22   
#define BIT_MASK_STPM_OFFSET_A_SHIFT            12
#define BIT_MASK_STPM_OFFSET_S_SHIFT            22
#define BIT_MASK_STPM_OFFSET_R_SHIFT            12

#define BIT_MASK_STPM_POWER_SIGN                (uint16_t)0x0200

    /*** Bitmask definition for DFE Control Register 1 or 2 ( Channel 1 or 2 ) : V1, C1 and V2 C2 ***/

#define BIT_MASK_STPM_G                       (uint32_t)0x08000000 /*!< Bitmask for Reference line frequency : 50 or 60Hz*/
#define BIT_MASK_STPM_EPRS_C                  (uint32_t)0x04000000 /*!< Bitmask for Enable cumulative energy calculation */
#define BIT_MASK_STPM_N_C                     (uint32_t)0x02000000 /*!< Bitmask for LED 2 Enable bit in DPS Control register 3 */
#define BIT_MASK_STPM_ECHP_HF_C               (uint32_t)0x01000000 /*!< Bitmask for LED 1 Enable bit in DPS Control register 3 */
#define BIT_MASK_STPM_M_C                     (uint32_t)0x00800000 /*!< Bitmask for Auto_latch bit in DPS Control register 3 */
#define BIT_MASK_STPM_ECHP_LF_C               (uint32_t)0x00400000 /*!< Bitmask for Latch2 bit in DPS Control register 3 */
#define BIT_MASK_STPM_PD_C                    (uint32_t)0x00200000 /*!< Bitmask for Latch1 bit in DPS Control register 3 */
#define BIT_MASK_STPM_EPRS_V                  (uint32_t)0x00100000 /*!< Bitmask for Reset bit in DPS Control register 3 */
#define BIT_MASK_STPM_N_V                     (uint32_t)0x00080000 /*!< Bitmask for Tamper_Enable bit in DPS Control register 3 */
#define BIT_MASK_STPM_ECHP_HF_V               (uint32_t)0x00060000 /*!< Bitmask for Tamper_Tolerance bits in DPS Control register 3 */
#define BIT_MASK_STPM_M_V                     (uint32_t)0x00000000 /*!< Bitmask for ZCR_Select bits in DPS Control register 3 */
#define BIT_MASK_STPM_ECHP_LF_V               (uint32_t)0x00000002 /*!< Bitmask for ZCR_Select bits in DPS Control register 3 */
#define BIT_MASK_STPM_PD_V                    (uint32_t)0x00000001 /*!< Bitmask for Time_Value bits in DPS Control register 3 */

/* Bitmask definition for DFE Control Register 1 and 2 for Gain selection for Channel 1 and 2 ***/
#define BIT_MASK_STPM_G_bit2                       (uint32_t)0x08000000     /*!< Bitmask for Current Gain bit 2  in DFE Control Register 1 or 2 */
#define BIT_MASK_STPM_G_bit1                       (uint32_t)0x04000000     /*!< Bitmask for Current Gain bit 1  in DFE Control Register 1 or 2 */

#define BIT_MASK_STPM_G_SHIFT                       26




/***** Bitmask definition for DSP IRQ1  Registers  ****/
#define BIT_MASK_STPM_PH1_PH2_IRQ1_CTRL_REG    (uint32_t)0x0000000F /*!< Bitmask for DSP_IRQ1 PH1 + PH2 Control_Reg bits in DSP IRQ Register 1 */
#define BIT_MASK_STPM_PH2_IRQ1_CTRL_REG        (uint32_t)0x00000FF0 /*!< Bitmask for DSP_IRQ1 PH2 Control_Reg bits in DSP IRQ Register 1  */
#define BIT_MASK_STPM_PH1_IRQ1_CTRL_REG        (uint32_t)0x000FF000 /*!< Bitmask for DSP_IRQ1 PH1 Control_Reg bits in DSP IRQ Register 1 */
#define BIT_MASK_STPM_C1_IRQ1_CTRL_REG         (uint32_t)0x00F00000 /*!< Bitmask for DSP_IRQ1 C1 Control_Reg bits in DSP IRQ Register 1  */
#define BIT_MASK_STPM_V1_IRQ1_CTRL_REG         (uint32_t)0x3F000000 /*!< Bitmask for DSP_IRQ1 V1 Control_Reg bits in DSP IRQ Register 1 */
#define BIT_MASK_STPM_TAMPER1_IRQ1_CTRL_REG     (uint32_t)0xC0000000 /*!< Bitmask for DSP_IRQ1 TAMPER Control_Reg bits in DSP IRQ Register 1 */

#define BIT_MASK_STPM_CHANNEL1_IRQ1             (BIT_MASK_STPM_PH1_PH2_IRQ1_CTRL_REG|BIT_MASK_STPM_PH1_IRQ1_CTRL_REG|BIT_MASK_STPM_C1_IRQ1_CTRL_REG|BIT_MASK_STPM_V1_IRQ1_CTRL_REG|BIT_MASK_STPM_TAMPER1_IRQ1_CTRL_REG)

#define BIT_MASK_STPM_PH1_PH2_IRQ2_CTRL_REG    (uint32_t)0x0000000F /*!< Bitmask for DSP_IRQ2 PH1 + PH2 Control_Reg bits in DSP IRQ Register 2 */
#define BIT_MASK_STPM_PH2_IRQ2_CTRL_REG        (uint32_t)0x00000FF0 /*!< Bitmask for DSP_IRQ2 PH2 Control_Reg bits in DSP IRQ Register 2  */
#define BIT_MASK_STPM_PH1_IRQ2_CTRL_REG        (uint32_t)0x000FF000 /*!< Bitmask for DSP_IRQ2 PH1 Control_Reg bits in DSP IRQ Register 2 */
#define BIT_MASK_STPM_C2_IRQ2_CTRL_REG         (uint32_t)0x00F00000 /*!< Bitmask for DSP_IRQ2 C1 Control_Reg bits in DSP IRQ Register 2  */
#define BIT_MASK_STPM_V2_IRQ2_CTRL_REG         (uint32_t)0x3F000000 /*!< Bitmask for DSP_IRQ2 V1 Control_Reg bits in DSP IRQ Register 2 */
#define BIT_MASK_STPM_TAMPER2_IRQ2_CTRL_REG     (uint32_t)0xC0000000 /*!< Bitmask for DSP_IRQ2 TAMPER Control_Reg bits in DSP IRQ Register 2 */

#define BIT_MASK_STPM_CHANNEL2_IRQ2             (BIT_MASK_STPM_PH2_IRQ2_CTRL_REG|BIT_MASK_STPM_C2_IRQ2_CTRL_REG|BIT_MASK_STPM_V2_IRQ2_CTRL_REG|BIT_MASK_STPM_TAMPER2_IRQ2_CTRL_REG)


/******** Bitmask definition for DSP Status Interrupt Register  DSPSR1 & 2 ********/
#define BIT_MASK_STPM_TAMPER_OR_WRONG          (uint32_t)0x80000000 /*!< Bitmask for Tamper or Wrong Insertion bit in DSP Interrupt Register  */
#define BIT_MASK_STPM_TAMPER_OR_WRONG_SHIFT     31
#define BIT_MASK_STPM_TAMPER_DETECTED          (uint32_t)0x40000000 /*!< Bitmask for Tamper_Detected bit in DSP Interrupt Register */
#define BIT_MASK_STPM_TAMPER_DETECTED_SHIFT     30
#define BIT_MASK_STPM_VOLT_SWELL_DOWN          (uint32_t)0x20000000 /*!< Bitmask for Voltage Swell_Down bit in DSP Interrupt Register */
#define BIT_MASK_STPM_VOLT_SWELL_DOWN_SHIFT     29
#define BIT_MASK_STPM_VOLT_SWELL_UP            (uint32_t)0x10000000 /*!< Bitmask for Voltage Swell_Up bit in DSP Interrupt Register */
#define BIT_MASK_STPM_VOLT_SWELL_UP_SHIFT       28
#define BIT_MASK_STPM_VOLT_SAG_DOWN            (uint32_t)0x08000000 /*!< Bitmask for Voltage Sag_Down bit in DSP Interrupt Register */
#define BIT_MASK_STPM_VOLT_SAG_DOWN_SHIFT       27
#define BIT_MASK_STPM_VOLT_SAG_UP              (uint32_t)0x04000000 /*!< Bitmask for Voltage Sag_Up bit in DSP Interrupt Register */
#define BIT_MASK_STPM_VOLT_SAG_UP_SHIFT         26
#define BIT_MASK_STPM_VOLT_PERIOD_STATUS       (uint32_t)0x02000000 /*!< Bitmask for Voltage Period_Status bit in DSP Interrupt Register */
#define BIT_MASK_STPM_VOLT_PERIOD_STATUS_SHIFT  25
#define BIT_MASK_STPM_VOLT_SIG_STUCK           (uint32_t)0x01000000 /*!< Bitmask for Voltage Signal_Stuck bit in DSP Interrupt Register */
#define BIT_MASK_STPM_VOLT_SIG_STUCK_SHIFT      24
#define BIT_MASK_STPM_CURR_SWELL_DOWN          (uint32_t)0x00800000 /*!< Bitmask for Current Swell_Down bit in DSP Interrupt Register */
#define BIT_MASK_STPM_CURR_SWELL_DOWN_SHIFT     23
#define BIT_MASK_STPM_CURR_SWELL_UP            (uint32_t)0x00400000 /*!< Bitmask for Current Swell_Up bit in DSP Interrupt Register */
#define BIT_MASK_STPM_CURR_SWELL_UP_SHIFT       22
#define BIT_MASK_STPM_CURR_NAH_TMP             (uint32_t)0x00200000 /*!< Bitmask for Current Nah_Tmp bit in DSP Interrupt Register */
#define BIT_MASK_STPM_CURR_NAH_TMP_SHIFT        21
#define BIT_MASK_STPM_CURR_SIG_STUCK           (uint32_t)0x00100000 /*!< Bitmask for Current Signal_Stuck bit in DSP Interrupt Register */
#define BIT_MASK_STPM_CURR_SIG_STUCK_SHIFT      20
#define BIT_MASK_STPM_PH1_EO_S                 (uint32_t)0x00080000 /*!< Bitmask for PHASE1 Channel Energy Overflow S bit in DSP Interrupt Register */
#define BIT_MASK_STPM_PH1_EO_S_SHIFT            19
#define BIT_MASK_STPM_PH1_EO_R                 (uint32_t)0x00040000 /*!< Bitmask for PHASE1 Channel Energy Overflow R bit in DSP Interrupt Register */
#define BIT_MASK_STPM_PH1_EO_R_SHIFT            18
#define BIT_MASK_STPM_PH1_EO_F                 (uint32_t)0x00020000 /*!< Bitmask for PHASE1 Channel Energy Overflow F bit in DSP Interrupt Register */
#define BIT_MASK_STPM_PH1_EO_F_SHIFT            17
#define BIT_MASK_STPM_PH1_EO_A                 (uint32_t)0x00010000 /*!< Bitmask for PHASE1 Channel Energy Overflow A bit in DSP Interrupt Register */
#define BIT_MASK_STPM_PH1_EO_A_SHIFT            16
#define BIT_MASK_STPM_PH1_PS_S                 (uint32_t)0x00008000 /*!< Bitmask for PHASE1 Power Sign  S bit in DSP Interrupt Register */
#define BIT_MASK_STPM_PH1_PS_S_SHIFT            15
#define BIT_MASK_STPM_PH1_PS_R                 (uint32_t)0x00004000 /*!< Bitmask for PHASE1 Power Sign  R bit in DSP Interrupt Register */
#define BIT_MASK_STPM_PH1_PS_R_SHIFT            14
#define BIT_MASK_STPM_PH1_PS_F                 (uint32_t)0x00002000 /*!< Bitmask for PHASE1 Power Sign  F bit in DSP Interrupt Register */
#define BIT_MASK_STPM_PH1_PS_F_SHIFT            13
#define BIT_MASK_STPM_PH1_PS_A                 (uint32_t)0x00001000 /*!< Bitmask for PHASE1 Power Sign  A bit in DSP Interrupt Register */
#define BIT_MASK_STPM_PH1_PS_A_SHIFT            12
#define BIT_MASK_STPM_PH2_EO_S                 (uint32_t)0x00000800 /*!< Bitmask for PHASE2 Channel Energy Overflow S bit in DSP Interrupt Register */
#define BIT_MASK_STPM_PH2_EO_S_SHIFT            11
#define BIT_MASK_STPM_PH2_EO_R                 (uint32_t)0x00000400 /*!< Bitmask for PHASE2 Channel Energy Overflow R bit in DSP Interrupt Register */
#define BIT_MASK_STPM_PH2_EO_R_SHIFT            10
#define BIT_MASK_STPM_PH2_EO_F                 (uint32_t)0x00000200 /*!< Bitmask for PHASE2 Channel Energy Overflow F bit in DSP Interrupt Register */
#define BIT_MASK_STPM_PH2_EO_F_SHIFT            9
#define BIT_MASK_STPM_PH2_EO_A                 (uint32_t)0x00000100 /*!< Bitmask for PHASE2 Channel Energy Overflow A bit in DSP Interrupt Register */
#define BIT_MASK_STPM_PH2_EO_A_SHIFT            8
#define BIT_MASK_STPM_PH2_PS_S                 (uint32_t)0x00000080 /*!< Bitmask for PHASE2 Power Sign  S bit in DSP Interrupt Register */
#define BIT_MASK_STPM_PH2_PS_S_SHIFT            7
#define BIT_MASK_STPM_PH2_PS_R                 (uint32_t)0x00000040 /*!< Bitmask for PHASE2 Power Sign  R bit in DSP Interrupt Register */
#define BIT_MASK_STPM_PH2_PS_R_SHIFT            6
#define BIT_MASK_STPM_PH2_PS_F                 (uint32_t)0x00000020 /*!< Bitmask for PHASE2 Power Sign  F bit in DSP Interrupt Register */
#define BIT_MASK_STPM_PH2_PS_F_SHIFT            5
#define BIT_MASK_STPM_PH2_PS_A                 (uint32_t)0x00000010 /*!< Bitmask for PHASE2 Power Sign  A bit in DSP Interrupt Register */
#define BIT_MASK_STPM_PH2_PS_A_SHIFT            4

    
/******** Bitmask definition for UART SPI Status and Interrupt Register   (UARTSPISR) ********/
#define BIT_MASK_STPM_SPI_SR_RX_OVERRUN          (uint32_t)0x40000000 /*!< Bitmask for SPI RX overrun Status Register */
#define BIT_MASK_STPM_SPI_SR_RX_OVERRUN_SHIFT     30
#define BIT_MASK_STPM_SPI_SR_TX_UNDERRUN          (uint32_t)0x20000000 /*!< Bitmask for SPI TX underrun Status Register */
#define BIT_MASK_STPM_SPI_SR_TX_UNDERRUN_SHIFT     29
#define BIT_MASK_STPM_SPI_SR_CRC_ERROR            (uint32_t)0x10000000 /*!< Bitmask for SPI CRC error Status Register */
#define BIT_MASK_STPM_SPI_SR_CRC_ERROR_SHIFT       28
#define BIT_MASK_STPM_UARTSPI_SR_WRITE_ERROR       (uint32_t)0x08000000 /*!< Bitmask for UART/SPI write error Status Register */
#define BIT_MASK_STPM_UARTSPI_SR_WRITE_ERROR_SHIFT 27
#define BIT_MASK_STPM_UARTSPI_SR_READ_ERROR        (uint32_t)0x04000000 /*!< Bitmask for UART/SPI read error Status Register */
#define BIT_MASK_STPM_UARTSPI_SR_READ_ERROR_SHIFT  26
#define BIT_MASK_STPM_SPI_SR_TX_EMPTY             (uint32_t)0x02000000 /*!< Bitmask for SPI TX EMPTY Status register*/
#define BIT_MASK_STPM_SPI_SR_TX_EMPTY_SHIFT       25
#define BIT_MASK_STPM_SPI_SR_RX_FULL              (uint32_t)0x01000000 /*!< Bitmask for SPI RX FULL Status register */
#define BIT_MASK_STPM_SPI_SR_RX_FULL_SHIFT        24
#define BIT_MASK_STPM_UART_SR_TX_OVERRUN          (uint32_t)0x00400000 /*!< Bitmask for  UART TX OVERUN  status register */
#define BIT_MASK_STPM_UART_SR_TX_OVERRUN_SHIFT    22
#define BIT_MASK_STPM_UART_SR_RX_OVERRUN          (uint32_t)0x00200000 /*!< Bitmask for  UART RX OVERUN  status register*/
#define BIT_MASK_STPM_UART_SR_RX_OVERRUN_SHIFT    21
#define BIT_MASK_STPM_UART_SR_NOISE_ERROR         (uint32_t)0x00100000 /*!< Bitmask for UART Noise error status register */
#define BIT_MASK_STPM_UART_SR_NOISE_ERROR_SHIFT   20
#define BIT_MASK_STPM_UART_SR_FRAMING_ERROR       (uint32_t)0x00080000 /*!< Bitmask for UART Framing error status register */
#define BIT_MASK_STPM_UART_SR_FRAMING_ERROR_SHIFT  19
#define BIT_MASK_STPM_UART_SR_TIMEOUT_ERROR       (uint32_t)0x00040000 /*!< Bitmask for UART Timeout error status register */
#define BIT_MASK_STPM_UART_SR_TIMEOUT_ERROR_SHIFT  18
#define BIT_MASK_STPM_UART_SR_CRC_ERROR           (uint32_t)0x00020000 /*!< Bitmask for UART CRC error status register */
#define BIT_MASK_STPM_UART_SR_CRC_ERROR_SHIFT      17
#define BIT_MASK_STPM_UART_SR_BREAK               (uint32_t)0x00010000 /*!< Bitmask for UART Break status register */
#define BIT_MASK_STPM_UART_SR_BREAK_SHIFT          16
#define BIT_MASK_STPM_SPI_IT_RX_OVERRUN            (uint32_t)0x00004000 /*!< Bitmask for IT SPI RX overrun  */
#define BIT_MASK_STPM_SPI_IT_RX_OVERRUN_SHIFT      14
#define BIT_MASK_STPM_SPI_IT_TX_UNDERRUN           (uint32_t)0x00002000 /*!< Bitmask for IT SPI TX underrun  */
#define BIT_MASK_STPM_SPI_IT_TX_UNDERRUN_SHIFT     13
#define BIT_MASK_STPM_SPI_IT_CRC_ERROR             (uint32_t)0x00001000 /*!< Bitmask for IT SPI CRC ERROR  */
#define BIT_MASK_STPM_SPI_IT_CRC_ERROR_SHIFT       12
#define BIT_MASK_STPM_UARTSPI_IT_WRITE_ERROR       (uint32_t)0x00000800 /*!< Bitmask for IT UART/SPI WRITE ERROR */
#define BIT_MASK_STPM_UARTSPI_IT_WRITE_ERROR_SHIFT 11
#define BIT_MASK_STPM_UARTSPI_IT_READ_ERROR        (uint32_t)0x00000400 /*!< Bitmask for IT UART/SPI READ ERROR  */
#define BIT_MASK_STPM_UARTSPI_IT_READ_ERROR_SHIFT  10
#define BIT_MASK_STPM_UART_IT_TX_OVERRUN           (uint32_t)0x00000040 /*!< Bitmask for IT UART RX OVERUN */
#define BIT_MASK_STPM_UART_IT_TX_OVERRUN_SHIFT     6
#define BIT_MASK_STPM_UART_IT_RX_OVERRUN           (uint32_t)0x00000020 /*!< Bitmask for IT UART RX OVERUN */
#define BIT_MASK_STPM_UART_IT_RX_OVERRUN_SHIFT     5
#define BIT_MASK_STPM_UART_IT_NOISE_ERROR          (uint32_t)0x00000010 /*!< Bitmask for IT UART NOISE ERROR */
#define BIT_MASK_STPM_UART_IT_NOISE_ERROR_SHIFT    4
#define BIT_MASK_STPM_UART_IT_FRAMING_ERROR        (uint32_t)0x00000008 /*!< Bitmask for IT UART FRAMING ERROR */
#define BIT_MASK_STPM_UART_IT_FRAMING_ERROR_SHIFT  3
#define BIT_MASK_STPM_UART_IT_TIMEOUT_ERROR        (uint32_t)0x00000004 /*!< Bitmask for IT UART TIMEOUT ERROR */
#define BIT_MASK_STPM_UART_IT_TIMEOUT_ERROR_SHIFT  2
#define BIT_MASK_STPM_UART_IT_CRC_ERROR            (uint32_t)0x00000002 /*!< Bitmask for IT UART CRC ERROR */
#define BIT_MASK_STPM_UART_IT_CRC_ERROR_SHIFT      1


#define BIT_MASK_STPM_IRQ_LINK      (uint32_t)0x0000FFFF
#define BIT_MASK_STPM_SR_LINK       (uint32_t)0xFFFF0000

    
/******* Bitmask definition for DSP Live Event 1 & 2  ********/
#define BIT_MASK_STPM_VOLT_SAG_EV              (uint32_t)0x3C000000 /*!< Bitmask for Voltage Channel Sag bits in dsp_ev register */
#define BIT_MASK_STPM_VOLT_SAG_EV_SHIFT        26
#define BIT_MASK_STPM_VOLT_SWELL_EV            (uint32_t)0x03C00000 /*!< Bitmask for Voltage Channel Swell bits in dsp_ev register */
#define BIT_MASK_STPM_VOLT_SWELL_EV_SHIFT      22
#define BIT_MASK_STPM_VOLT_PERIOD_STATUS_EV    (uint32_t)0x00200000 /*!< Bitmask for Voltage Channel Period_Status bit in dsp_ev register */
#define BIT_MASK_STPM_VOLT_PERIOD_STATUS_EV_SHIFT 21   
#define BIT_MASK_STPM_VOLT_SIG_STUCK_EV        (uint32_t)0x00100000 /*!< Bitmask for Voltage Channel Signal_Stuck bit in dsp_ev register */
#define BIT_MASK_STPM_VOLT_SIG_STUCK_EV_SHIFT   20   
#define BIT_MASK_STPM_VOLT_ZCR_EV              (uint32_t)0x00080000 /*!< Bitmask for Voltage Channel Signal_Stuck bit in dsp_ev register */
#define BIT_MASK_STPM_VOLT_ZCR_EV_SHIFT         19    
#define BIT_MASK_STPM_CURR_SWELL_EV            (uint32_t)0x00078000 /*!< Bitmask for Voltage Channel Swell bits in dsp_ev register */
#define BIT_MASK_STPM_CURR_SWELL_EV_SHIFT       15    
#define BIT_MASK_STPM_CURR_AH_ACC_EV           (uint32_t)0x00004000 /*!< Bitmask for Voltage Channel Swell bits in dsp_ev register */
#define BIT_MASK_STPM_CURR_AH_ACC_EV_SHIFT      14    
#define BIT_MASK_STPM_CURR_SIG_STUCK_EV        (uint32_t)0x00002000 /*!< Bitmask for Primary Current Channel Signal_Stuck bit in dsp_ev register */
#define BIT_MASK_STPM_CURR_SIG_STUCK_EV_SHIFT   13    
#define BIT_MASK_STPM_CURR_ZCR_EV              (uint32_t)0x00001000 /*!< Bitmask for Voltage Channel Signal_Stuck bit in dsp_ev register */
#define BIT_MASK_STPM_CURR_ZCR_EV_SHIFT         12    
#define BIT_MASK_STPM_CH_OV_S_EV               (uint32_t)0x00000800 /*!< Bitmask for   Channel Overflow S bit in dsp_ev register */
#define BIT_MASK_STPM_CH_OV_S_EV_SHIFT          11     
#define BIT_MASK_STPM_CH_OV_R_EV               (uint32_t)0x00000400 /*!< Bitmask for   Channel Overflow  R bit in dsp_ev register */
#define BIT_MASK_STPM_CH_OV_R_EV_SHIFT          10    
#define BIT_MASK_STPM_CH_OV_F_EV               (uint32_t)0x00000200 /*!< Bitmask for   Channel Overflow  F bit in dsp_ev register */
#define BIT_MASK_STPM_CH_OV_F_EV_SHIFT          9     
#define BIT_MASK_STPM_CH_OV_A_EV               (uint32_t)0x00000100 /*!< Bitmask for   Channel Overflow  A bit in dsp_ev register */
#define BIT_MASK_STPM_CH_OV_A_EV_SHIFT          8     
#define BIT_MASK_STPM_CH_PS_S_EV               (uint32_t)0x00000080 /*!< Bitmask for   Channel Power Sign S bit in dsp_ev register */
#define BIT_MASK_STPM_CH_PS_S_EV_SHIFT          7     
#define BIT_MASK_STPM_CH_PS_R_EV               (uint32_t)0x00000040 /*!< Bitmask for   Channel Power Sign R bit in dsp_ev register */
#define BIT_MASK_STPM_CH_PS_R_EV_SHIFT          6    
#define BIT_MASK_STPM_CH_PS_F_EV               (uint32_t)0x00000020 /*!< Bitmask for   Channel Power Sign F bit in dsp_ev register */
#define BIT_MASK_STPM_CH_PS_F_EV_SHIFT          5     
#define BIT_MASK_STPM_CH_PS_A_EV               (uint32_t)0x00000010 /*!< Bitmask for   Channel Power Sign A bit in dsp_ev register */
#define BIT_MASK_STPM_CH_PS_A_EV_SHIFT          4     

/***** Bitmask definition for dsp_reg registers from offset 0x44 to 0xB8 ******/
#define BIT_MASK_STPM_8BIT_PADDING             (uint32_t)0xF0000000  /*!< Bitmask for Padding bits in dsp_reg1, dsp_reg2 and dsp_reg3 registers */
#define BIT_MASK_STPM_DATA_V                   (uint32_t)0x00FFFFFF  /*!< Bitmask for Data_V bits in dsp_reg1 register */
#define BIT_MASK_STPM_DATA_C1                  (uint32_t)0x00FFFFFF  /*!< Bitmask for Data_C1 bits in dsp_reg2 register */
#define BIT_MASK_STPM_DATA_C2                  (uint32_t)0x00FFFFFF  /*!< Bitmask for Data_C2 bits in dsp_reg3 register */
#define BIT_MASK_STPM_4BIT_PADDING             (uint32_t)0xF0000000  /*!< Bitmask for Padding bits in dsp_reg4/7/8 registers */


#define BIT_MASK_STPM_PERIOD_CHANNEL2_SHIFT     16           
#define BIT_MASK_STPM_PERIOD_CHANNEL_2         (uint32_t)0x0FFF0000  /*!< Bitmask for Period Channel 2 bits in dsp_reg1 register */
#define BIT_MASK_STPM_PERIOD_CHANNEL_1         (uint32_t)0x00000FFF  /*!< Bitmask for Period Channel 1 bits in dsp_reg1 register */
#define BIT_MASK_STPM_DATA_VRMS                (uint32_t)0x00007FFF  /*!< Bitmask for Data_Vrms bits in dsp_reg14 & 15 register */
#define BIT_MASK_STPM_DATA_C1_RMS              (uint32_t)0xFFFF8000  /*!< Bitmask for Data_C1RMS bits in dsp_reg14 register */
#define BIT_MASK_STPM_DATA_C2_RMS              (uint32_t)0xFFFF8000  /*!< Bitmask for Data_C2RMS bits in dsp_reg15 register */
#define BIT_MASK_STPM_DATA_C_RMS_SHIFT         15 /*!< Shift C RMS */

#define BIT_MASK_STPM_PHASE_ANGLE_1            (uint32_t)0x0FFF0000  /*!< Bitmask for Phase_Angle C1 bits in dsp_reg17 register */
#define BIT_MASK_STPM_PHASE_ANGLE_2            (uint32_t)0x0FFF0000  /*!< Bitmask for Phase_Angle C2 bits in dsp_reg19 register */
#define BIT_MASK_STPM_PHASE_ANGLE_SHIFT         16                    /*!< Shift Phase angle register */

#define BIT_MASK_STPM_P_31                     (uint32_t)0x80000000  /*!< Bitmask for P bit in dsp_reg6 register (31st bit) */
#define BIT_MASK_STPM_SAG_TIME_V1              (uint32_t)0x7FFF0000  /*!< Bitmask for Sag_Time bits in dsp_reg16 register */
#define BIT_MASK_STPM_SAG_TIME_V1_SHIFT        16
#define BIT_MASK_STPM_SAG_TIME_V2              (uint32_t)0x7FFF0000  /*!< Bitmask for Sag_Time bits in dsp_reg18 register */
#define BIT_MASK_STPM_SAG_TIME_V2_SHIFT        16

#define BIT_MASK_STPM_P_15                     (uint32_t)0x00008000  /*!< Bitmask for P bit in dsp_reg6/7/8 register (15th bit) */
#define BIT_MASK_STPM_SWELL_TIME_V1            (uint32_t)0x00007FFF  /*!< Bitmask for Swell_Time_V bits in dsp_reg16 register */
#define BIT_MASK_STPM_SWELL_TIME_V2            (uint32_t)0x00007FFF  /*!< Bitmask for Swell_Time_V bits in dsp_reg18 register */
#define BIT_MASK_STPM_SWELL_TIME_C1            (uint32_t)0x00007FFF  /*!< Bitmask for Swell_Time_C1 bits in dsp_reg17 register */
#define BIT_MASK_STPM_SWELL_TIME_C2            (uint32_t)0x00007FFF  /*!< Bitmask for Swell_Time_C2 bits in dsp_reg19 register */

#define BIT_MASK_STPM_PRIM_CURR_ACTV_ENERGY    (uint32_t)0xFFFFFFFF  /*!< Bitmask for Primary_Current_Channel_Active_Energy bits in ch1_reg1 register */
#define BIT_MASK_STPM_PRIM_CURR_FUND_ENERGY    (uint32_t)0xFFFFFFFF  /*!< Bitmask for Primary_Current_Channel_Fundamental_Energy bits in ch1_reg2 register */
#define BIT_MASK_STPM_PRIM_CURR_REACT_ENERGY   (uint32_t)0xFFFFFFFF  /*!< Bitmask for Primary_Current_Channel_Reactive_Energy bits in ch1_reg3 register */
#define BIT_MASK_STPM_PRIM_CURR_RMS_ENERGY     (uint32_t)0xFFFFFFFF  /*!< Bitmask for Primary_Current_Channel_Apparent_RMS_Energy bits in ch1_reg4 register */
#define BIT_MASK_STPM_3BIT_PADDING             (uint32_t)0xE0000000  /*!< Bitmask for Padding bits in ch1_reg5/6/7/8/9/10 and ch2_reg5/6/7/8/9/10 registers */
#define BIT_MASK_STPM_PRIM_CURR_ACTIVE_POW     (uint32_t)0x1FFFFFFF  /*!< Bitmask for Primary_Current_Channel_Active_Power bits in ch1_reg5 register */
#define BIT_MASK_STPM_PRIM_CURR_FUND_POW       (uint32_t)0x1FFFFFFF  /*!< Bitmask for Primary_Current_Channel_Fundamental_Power bits in ch1_reg6 register */
#define BIT_MASK_STPM_PRIM_CURR_REACT_POW      (uint32_t)0x1FFFFFFF  /*!< Bitmask for Primary_Current_Channel_Reactive_Power bits in ch1_reg7 register */
#define BIT_MASK_STPM_PRIM_CURR_RMS_POW        (uint32_t)0x1FFFFFFF  /*!< Bitmask for Primary_Current_Channel_Apparent_RMS_Power bits in ch1_reg8 register */
#define BIT_MASK_STPM_PRIM_CURR_VEC_POW        (uint32_t)0x1FFFFFFF  /*!< Bitmask for Secondary_Current_Channel_Apparent_VEC _Power bits in ch2_reg9 register */
#define BIT_MASK_STPM_PRIM_CURR_MOM_ACTIVE_POW (uint32_t)0x1FFFFFFF  /*!< Bitmask for Primary_Current_Channel_Momentary_Active_Power bits in ch1_reg10 register */
#define BIT_MASK_STPM_PRIM_CURR_MOM_FUND_POW   (uint32_t)0x1FFFFFFF  /*!< Bitmask for Primary_Current_Channel_Momentary_Fundamental_Power bits in ch1_reg11 register */
#define BIT_MASK_STPM_PRIM_CURR_AH_ACC         (uint32_t)0xFFFFFFFF  /*!< Bitmask for Primary_Current_Channel_AhAcc bits in ch1_reg11 register */
#define BIT_MASK_STPM_SEC_CURR_ACTV_ENERGY     (uint32_t)0xFFFFFFFF  /*!< Bitmask for Secondary_Current_Channel_Active_Energy bits in ch2_reg1 register */
#define BIT_MASK_STPM_SEC_CURR_FUND_ENERGY     (uint32_t)0xFFFFFFFF  /*!< Bitmask for Secondary_Current_Channel_Fundamental_Energy bits in ch2_reg2 register */
#define BIT_MASK_STPM_SEC_CURR_REACT_ENERGY    (uint32_t)0xFFFFFFFF  /*!< Bitmask for Secondary_Current_Channel_Reactive_Energy bits in ch2_reg3 register */
#define BIT_MASK_STPM_SEC_CURR_RMS_ENERGY      (uint32_t)0xFFFFFFFF  /*!< Bitmask for Secondary_Current_Channel_Apparent_RMS_Energy bits in ch2_reg4 register */
#define BIT_MASK_STPM_SEC_CURR_ACTIVE_POW      (uint32_t)0x1FFFFFFF  /*!< Bitmask for Secondary_Current_Channel_Active_Power bits in ch2_reg5 register */
#define BIT_MASK_STPM_SEC_CURR_FUND_POW        (uint32_t)0x1FFFFFFF  /*!< Bitmask for Secondary_Current_Channel_Fundamental_Power bits in ch2_reg6 register */
#define BIT_MASK_STPM_SEC_CURR_REACT_POW       (uint32_t)0x1FFFFFFF  /*!< Bitmask for Secondary_Current_Channel_Reactive_Power bits in ch2_reg7 register */
#define BIT_MASK_STPM_SEC_CURR_RMS_POW         (uint32_t)0x1FFFFFFF  /*!< Bitmask for Secondary_Current_Channel_Apparent_RMS_Power bits in ch2_reg8 register */
#define BIT_MASK_STPM_SEC_CURR_VEC_POW         (uint32_t)0x1FFFFFFF  /*!< Bitmask for Secondary_Current_Channel_Apparent_VEC _Power bits in ch2_reg9 register */
#define BIT_MASK_STPM_SEC_CURR_MOM_ACTIVE_POW  (uint32_t)0x1FFFFFFF  /*!< Bitmask for Secondary_Current_Channel_Momentary_Active_Power bits in ch2_reg10 register */
#define BIT_MASK_STPM_SEC_CURR_MOM_FUND_POW    (uint32_t)0x1FFFFFFF  /*!< Bitmask for Secondary_Current_Channel_Momentary_Fundamental_Power bits in ch2_reg11 register */
#define BIT_MASK_STPM_SEC_CURR_AH_ACC          (uint32_t)0xFFFFFFFF  /*!< Bitmask for Secondary_Current_Channel_AhAcc bits in ch2_reg11 register */

/**
  * @}
  */

/**
  * @}
  */

/* Exported macro ------------------------------------------------------------*/
/* Exported functions --------------------------------------------------------*/



#ifdef __cplusplus
}
#endif

#endif /* __STPM_METROLOGY_H */

/**
  * @}
  */

/**
  * @}
  */

/************************ (C) COPYRIGHT STMicroelectronics *****END OF FILE****/
