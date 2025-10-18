/**
  ******************************************************************************
  * @file    metrology_hal.c
  * @author  AMG/IPC Application Team
  * @brief   This file provides The hardware abstraction for Metrology Block.
  * @brief
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

/* Includes ------------------------------------------------------------------*/

#include "stpm_metrology.h"
#include "metrology.h"
#include "metrology_hal.h"
#include <string.h>
#include <stdint.h>
#include "st_device.h"

/* Private typedef -----------------------------------------------------------*/
/* Private define ------------------------------------------------------------*/

#define METRO_BUFF_COM_MAXSIZE  ((uint8_t)(40))

#define CRC_8 (0x07)
#define STPM3x_FRAME_LEN (5)

#define WAIT_DURATION   500   /* 500 * 1 ms = 500 ms */

#ifdef  USE_FULL_ASSERT

/**
  * @brief  The assert_param macro is used for function's parameters check.
  * @param  expr If expr is false, it calls assert_failed function
  *   which reports the name of the source file and the source
  *   line number of the call that failed.
  *   If expr is true, it returns no value.
  * @retval None
  */
  #define assert_param(expr) ((expr) ? (void)0 : assert_failed((uint8_t *)__FILE__, __LINE__))
/* Exported functions ------------------------------------------------------- */
  void assert_failed(uint8_t* file, uint32_t line);
#else
  #define assert_param(expr) ((void)0)
#endif /* USE_FULL_ASSERT */

/* Private macro -------------------------------------------------------------*/
/* Private variables ---------------------------------------------------------*/

static uint8_t CRC_u8Checksum;

/* Private function prototypes -----------------------------------------------*/
#ifdef UART_XFER_STPM3X /* UART MODE */  
static void Metro_HAL_usart_config(METRO_NB_Device_t in_Metro_Device_Id,uint32_t in_baudrate);
static void Metro_HAL_UsartTxStart(METRO_NB_Device_t in_Metro_Device_Id);
static uint8_t UARTWrp_SendAndReceiveByte(METRO_NB_Device_t in_Metro_Device_Id,uint8_t data);
static uint8_t Metro_HAL_byteReverse(uint8_t in_byte);
#endif

static void Metro_HAL_Crc8Calc (uint8_t in_Data);
static uint8_t Metro_HAL_CalcCRC8(uint8_t *pBuf);
static void Metro_HAL_WaitMicroSecond(uint32_t time);
static void Metro_HAL_reset_transfer_context(METRO_NB_Device_t in_Metro_Device_Id);
static void Metro_HAL_STPM_SYN_reset_3_pulses(METRO_NB_Device_t in_Metro_Device_Id);
static void Metro_HAL_STPM_SYN_single_pulse(METRO_NB_Device_t in_Metro_Device_Id);
static void Metro_HAL_CSS_EXT_Device(METRO_NB_Device_t in_Metro_Device_Id,GPIO_PinState in_Metro_enable);
static void Metro_HAL_EN_EXT_Device(METRO_NB_Device_t in_Metro_Device_Id,GPIO_PinState in_Metro_enable);
static void Metro_HAL_SYN_EXT_Device(METRO_NB_Device_t in_Metro_Device_Id,GPIO_PinState in_Metro_enable);


static void Metro_HAL_RxHandler(METRO_NB_Device_t in_Metro_Device_Id);
static void Metro_HAL_TxHandler(METRO_NB_Device_t in_Metro_Device_Id);

#ifdef SPI_XFER_STPM3X /* SPI MODE */ 
static void Metro_HAL_Spi_config(METRO_NB_Device_t in_Metro_Device_Id);
static void Metro_HAL_SpiTxStart(METRO_NB_Device_t in_Metro_Device_Id);
static uint8_t SPIWrp_SendAndReceiveByte(METRO_NB_Device_t in_Metro_Device_Id,uint8_t data);
#endif


/* Global variables ----------------------------------------------------------*/
volatile uint32_t waitDummyCounter;

METRO_Device_Config_t * p_Metro_Device_Config;
uint8_t Metro_Com_TxBuf[METRO_BUFF_COM_MAXSIZE];
uint8_t Metro_Com_RxBuf[METRO_BUFF_COM_MAXSIZE];

#ifdef UART_XFER_STPM3X /* UART MODE */  
UART_HandleTypeDef huart[NB_MAX_DEVICE];
#endif

#ifdef SPI_XFER_STPM3X /* SPI MODE */ 
SPI_HandleTypeDef hspi[NB_MAX_DEVICE];
#endif
/* Private functions ---------------------------------------------------------*/

/** @defgroup Metrology_HAL_Private_Functions
* @{
*/

/** @defgroup Metrology_Group1 Initialization and Configuration functions
*  @brief   Initialization and Configuration functions
*
@verbatim
===============================================================================
                functions
===============================================================================

This section provides a set of functions to make the porting of Metrology Block from STCOMET or STMET or STPM

@endverbatim
* @{
*/


/**
  * @brief  HAL  metrology Config
  *
  *
  * @retval U32
  */
/* set metrology HAL Config  */
uint8_t Metro_HAL_Setup(METRO_Device_Config_t * in_p_Metro_Config)
{
  /* Save the pointer of Config table */
  p_Metro_Device_Config = in_p_Metro_Config;

  return 0;

}


/**
  * @brief  Read Block Registers from device
  *
  *
  * @retval void
  */
uint8_t Metrology_HAL_ReadBlock(METRO_NB_Device_t in_Metro_Device_Id, uint8_t Address, uint8_t BlockNum, uint32_t * out_p_Buffer)
{
  uint32_t tmp_addr = 0x0;
  uint8_t  error=0;

  if ( in_Metro_Device_Id >= EXT1)// modif
  {
    /* The address should be provided (2 bytes -> 16 bits) format for STPM */
    tmp_addr = Address;

    /* read blocks from external chip */
    Metro_HAL_Stpm_Read(in_Metro_Device_Id,(uint8_t*)&tmp_addr,BlockNum,out_p_Buffer);

  }
  return error;
}
/**
  * @brief  Write Block Registers to device
  *
  *
  * @retval void
  */
uint8_t Metrology_HAL_WriteBlock(METRO_NB_Device_t in_Metro_Device_Id, uint8_t Address, uint8_t BlockNum, uint32_t * in_p_Buffer)
{
  uint32_t tmp_addr = 0x0;
  uint32_t ret_size;

  if ( in_Metro_Device_Id >= EXT1)// modif
  {
    /* The address should be provided (2 bytes -> 16 bits) format for STPM */
    tmp_addr = Address;

    /* write blocks from external chip */
    ret_size = Metro_HAL_Stpm_write(in_Metro_Device_Id,(uint8_t*)&tmp_addr,BlockNum,in_p_Buffer,STPM_WAIT); 
  }
  return(ret_size);
}


/**
  * @brief  Init Metrology devices
  *
  *
  * @retval void
  */
void Metro_HAL_init_device(METRO_NB_Device_t in_Metro_Device_Id)
{

  if(in_Metro_Device_Id >= EXT1) 
  {

#ifdef UART_XFER_STPM3X // UART MODE    
    Metro_HAL_usart_config(in_Metro_Device_Id,9600); 
#endif    

#ifdef SPI_XFER_STPM3X // SPI mode  
    Metro_HAL_Spi_config(in_Metro_Device_Id);
#endif 

    /* set good CS with good EXT chip */
    Metro_HAL_CSS_EXT_Device(in_Metro_Device_Id,GPIO_PIN_SET);
    Metro_HAL_WaitMicroSecond(1000); 
  
    /* Reset EXT Chip */
    /* Wait 35 ms */
    Metro_HAL_WaitMicroSecond(35000); 
    /* 3 pulses on SYN */
    Metro_HAL_STPM_SYN_reset_3_pulses(in_Metro_Device_Id);
           
    /* Single pulse on CS rev BC */        
    Metro_HAL_WaitMicroSecond(1000); 
    Metro_HAL_CSS_EXT_Device(in_Metro_Device_Id,GPIO_PIN_RESET);
    Metro_HAL_WaitMicroSecond(100); 
    Metro_HAL_CSS_EXT_Device(in_Metro_Device_Id,GPIO_PIN_SET);
      
   /* Wait 20 ms */
   Metro_HAL_WaitMicroSecond(20000);   
   
   /* Make one access ( first reg u32 reg) to ext chip to check if it is available */
    
    if (Metro_HAL_Stpm_Read(in_Metro_Device_Id, STPM_DSPCTRL1, 1, (uint32_t*)&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1)==0)
   {
    // Reset Config for EXT chip 
    p_Metro_Device_Config[in_Metro_Device_Id].device   = Device_NONE;
    p_Metro_Device_Config[in_Metro_Device_Id].channels_mask = 0;

   }
  }
}

/**
  * @brief  Enable Metrology devices by setting up and down the EN pin
  *         When EN is low the CSS is set low or high depending of the 
  *         protocol used (SPI or UART)
  * @retval void
  */

void Metro_HAL_power_up_device(METRO_NB_Device_t in_Metro_Device_Id)
{
  if(in_Metro_Device_Id >= EXT1) 
  {
  
#ifdef UART_XFER_STPM3X /* UART MODE */   
    /* set UART mode at STPM3x power up, we have to set SS pin */
    Metro_HAL_CSS_EXT_Device(in_Metro_Device_Id,GPIO_PIN_SET);
#endif

#ifdef SPI_XFER_STPM3X /* SPI MODE */   
    /* set SPI mode at STPM3x power up, we have to reset SS pin */
    Metro_HAL_CSS_EXT_Device(in_Metro_Device_Id,GPIO_PIN_RESET); 
#endif

    /* set ENable Pin configured as low in CubeMX*/
    Metro_HAL_WaitMicroSecond(1000); 
    Metro_HAL_EN_EXT_Device(in_Metro_Device_Id,GPIO_PIN_RESET);
    Metro_HAL_WaitMicroSecond(1000); 
    Metro_HAL_EN_EXT_Device(in_Metro_Device_Id,GPIO_PIN_SET);
    Metro_HAL_WaitMicroSecond(1000); 
  }
}

/**
  * @brief      This function reset device requested
  * @param[in]   in_Metro_Device_Id (device ID), EXT1 to EXT4
  * @param[in]   Reset type
  * @param[out]  none
  * @retval
  */
void Metro_HAL_reset_device(METRO_ResetType_t in_MetroResetType,METRO_NB_Device_t in_Metro_Device_Id)
{
  uint32_t tmp_addr = 0;

  if(in_Metro_Device_Id >= EXT1) 
  {
    if (in_MetroResetType ==  RESET_SW)
    {
      /* Set the reset bit in the  DSP Control Register 3 of stpm requested(STPM) */
      /* First put the bit inside internal struct */
      p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3 |= METRO_STPM_Reset_Bit;

      /* second : write into external the chip */
      /* the address should be provided in 2 bytes format (16 bits by 16 bits) for STPM */
      tmp_addr = STPM_DSPCTRL3;

     /* Write blocks inside external chip */
      Metro_HAL_Stpm_write(in_Metro_Device_Id,(uint8_t*)&tmp_addr,1,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3,STPM_WAIT);


    }
    /* reset SYN hardware is requested, send 3 pulses to SYN signal pin */
    else if (in_MetroResetType ==  RESET_SYN_SCS)
    {
    /* Reset ext STPMs with syn PIN : 3 pulses are needed to reset STPM chips */
    Metro_HAL_STPM_SYN_reset_3_pulses(in_Metro_Device_Id);
    }
  }
}

/**
  * @brief      This function set latch inside Metrology devices
               Latch the device registers according to the latch type selection driving SYN pin
               or writing S/W Latchx bits in the DSP_CR3 register
               or setting auto-latch by S/W Auto Latch bit in the DSP_CR3 register
  * @param[in]   in_Metro_Device_Id (device ID), EXT1 to EXT4
  * @param[in]   Latch type
  * @param[out]  none
  * @retval
  */
void Metro_HAL_Set_Latch_device_type(METRO_NB_Device_t in_Metro_Device_Id, METRO_Latch_Device_Type_t in_Metro_Latch_Device_Type)
{
  uint32_t tmp_addr = 0;

  if(in_Metro_Device_Id >= EXT1) 
  {
    switch (in_Metro_Latch_Device_Type)
    {

      case LATCH_AUTO:
      {

        /* reset latch 1 and 2 bits in the internal DSP Control Register 3 */
        p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3 &= ~ BIT_MASK_STPM_LATCH1;
        p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3 &= ~ BIT_MASK_STPM_LATCH2;


        /* Set  latch auto in the internal DSP Control Register 3*/
        p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3 |= BIT_MASK_STPM_AUTO_LATCH;

        /* Now send data to the external chip */
        /* the address should be provided in 2 bytes format (16 bits by 16 bits) for STPM */
        tmp_addr = STPM_DSPCTRL3;

        /* Write register inside external chip */
        Metro_HAL_Stpm_write(in_Metro_Device_Id,(uint8_t*)&tmp_addr,1,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3,STPM_WAIT);

      }
      break;
      case LATCH_SW:
      {
        /* Set  latch SW 1 et 2 for he Two channels  the internal DSP Control Register 3*/
        p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3 |= BIT_MASK_STPM_LATCH1|BIT_MASK_STPM_LATCH2;

        /* Now send data to the external chip */
        /* the address should be provided in 2 bytes format (16 bits by 16 bits) for STPM */
        tmp_addr = STPM_DSPCTRL3;

        /* Write register inside external chip */
        Metro_HAL_Stpm_write(in_Metro_Device_Id,(uint8_t*)&tmp_addr,1,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3,STPM_WAIT);

      }
      break;
      case LATCH_SYN_SCS:
      {
        /* Latch external chip with syn PIN : 1 pulses is needed to latch */
        Metro_HAL_STPM_SYN_single_pulse(in_Metro_Device_Id);
      }
      break;
    }
     
  }

}

/**
  * @brief     This function gets the DSP registers inside Metrology devices
               Latch the device registers according to the latch type selection driving SYN pin
               or writing S/W Latchx bits in the DSP_CR3 register
               or setting auto-latch by S/W Auto Latch bit in the DSP_CR3 register
  * @param[in]   in_Metro_Device_Id (device ID), EXT1 to EXT4
  * @param[out]  none
  * @retval
  */
void Metro_HAL_Get_Data_device(METRO_NB_Device_t in_Metro_Device_Id)
{
  uint32_t tmp_addr = 0;
         
  /* After latch with syn pin or SW reg , we have to retreive metrology data from STPM external chip requested */
  /* from DSPEVENT1 to TOT_REG4 : 49 U32 reg from STPM*/
  /* Calculate the base address of Metrology data to read inisde STPM chip  */
  /* the offset should be provided in 2 bytes format (16 bits by 16 bits) for STPM */
  /* In case of STPM32, only one channel */


  if(in_Metro_Device_Id >= EXT1) 
  {
    if (p_Metro_Device_Config[in_Metro_Device_Id].device == STPM32)
    {
    tmp_addr = STPM_DSPEVENT1;
    Metro_HAL_Stpm_Read(in_Metro_Device_Id,(uint8_t*)&tmp_addr,(METRO_STPM_DSP_DATA_REG_NB_BLOCKS + METRO_STPM_PH1_DATA_REG_NB_BLOCKS),&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT1);
 
    tmp_addr = STPM_TOT_REG1;
    Metro_HAL_Stpm_Read(in_Metro_Device_Id,(uint8_t*)&tmp_addr,METRO_STPM_TOT_DATA_REG_NB_BLOCKS,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.TOT_REG1);
    
    }
    else
    {
    tmp_addr = STPM_DSPEVENT1;
    Metro_HAL_Stpm_Read(in_Metro_Device_Id,(uint8_t*)&tmp_addr,METRO_STPM_DATA_REG_NB_BLOCKS,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT1);     
    }
  } 
}

/**
  * @brief      This function set the gain of the channel
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_internal_Channel_t (Channel ID), Channel 1 or 2 ( according to device ) or CHANNEL_TAMPER
  * @param[in]   METRO_Current_t : X2 , X4 ,X8 , X16 current gain multiplicator
  * @param[out]  none
  * @retval      none
  */
void Metro_HAL_Set_Gain(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel, METRO_Gain_t in_Metro_Gain)
{

  uint32_t tmp_addr = 0;

  if(in_Metro_Device_Id >= EXT1) 
  {

  /* Set the new Current gain multiplicator for the channel requested */
    switch (in_Metro_Gain)
    {
      case (X2):
      {
        if ( in_Metro_int_Channel == INT_CHANNEL_1)
        {  
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DFECTRL1 &= ~ BIT_MASK_STPM_G_bit1;
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DFECTRL1 &= ~ BIT_MASK_STPM_G_bit2;
        }
        else if (( in_Metro_int_Channel == INT_CHANNEL_2) || (in_Metro_int_Channel == CHANNEL_TAMPER))
        {
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DFECTRL2 &= ~ BIT_MASK_STPM_G_bit1;
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DFECTRL2 &= ~ BIT_MASK_STPM_G_bit2;
        }
      }
      break;
      case (X4):
      {
        if ( in_Metro_int_Channel == INT_CHANNEL_1)
        {  
          p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DFECTRL1 |= BIT_MASK_STPM_G_bit1;
          p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DFECTRL1 &= ~ BIT_MASK_STPM_G_bit2;
        }
        else if (( in_Metro_int_Channel == INT_CHANNEL_2) || (in_Metro_int_Channel == CHANNEL_TAMPER))
        {
          p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DFECTRL2 |= BIT_MASK_STPM_G_bit1;
          p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DFECTRL2 &= ~ BIT_MASK_STPM_G_bit2;
        }        
      }
      break;
      case (X8):
      {
        if ( in_Metro_int_Channel == INT_CHANNEL_1)
        {  
          p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DFECTRL1 &= ~ BIT_MASK_STPM_G_bit1;
          p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DFECTRL1 |=  BIT_MASK_STPM_G_bit2;
        }
        else if (( in_Metro_int_Channel == INT_CHANNEL_2) || (in_Metro_int_Channel == CHANNEL_TAMPER))
        {
          p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DFECTRL2 &= ~ BIT_MASK_STPM_G_bit1;
          p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DFECTRL2 |=  BIT_MASK_STPM_G_bit2;
        }        
      }
      break;
      case (X16):
      {
        if ( in_Metro_int_Channel == INT_CHANNEL_1)
        {  
          p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DFECTRL1 |= BIT_MASK_STPM_G_bit1;
          p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DFECTRL1 |= BIT_MASK_STPM_G_bit2;
        }
        else if (( in_Metro_int_Channel == INT_CHANNEL_2) || (in_Metro_int_Channel == CHANNEL_TAMPER))
        {
          p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DFECTRL2 |= BIT_MASK_STPM_G_bit1;
          p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DFECTRL2 |= BIT_MASK_STPM_G_bit2;
        }        
      }
      break;
    }
      
      /* Now send data to the external chip */
      /* the address should be provided in 2 bytes format (16 bits by 16 bits) for STPM */
      tmp_addr = STPM_DFECTRL1;

     /* Write the 2 U32 registers inside external chip  for DFE CR1 and CR2 */
     Metro_HAL_Stpm_write(in_Metro_Device_Id,(uint8_t*)&tmp_addr,2,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DFECTRL1,STPM_WAIT);
  }
}    

/**
  * @brief      This function Get the gain of the channel requested
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_internal_Channel_t (Channel ID), Channel 1 or 2 ( according to device ) or CHANNEL_TAMPER
  * @param[out]  none
  * @retval      METRO_Current_t : X2 , X4 ,X8 , X16 current gain multiplicator
  */
METRO_Gain_t Metro_HAL_Get_Gain(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel)
{

  METRO_Gain_t Gain = X2;
 
  if(in_Metro_Device_Id >= EXT1) 
  {

    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    { 
      Gain = (METRO_Gain_t)((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DFECTRL1&BIT_MASK_STPM_G_bit1)>>BIT_MASK_STPM_G_SHIFT);
      Gain |= (METRO_Gain_t)((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DFECTRL1&BIT_MASK_STPM_G_bit2)>>BIT_MASK_STPM_G_SHIFT);
    }
    else if (( in_Metro_int_Channel == INT_CHANNEL_2) || (in_Metro_int_Channel == CHANNEL_TAMPER))
    {
      Gain = (METRO_Gain_t)((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DFECTRL2&BIT_MASK_STPM_G_bit1)>>BIT_MASK_STPM_G_SHIFT);
      Gain |= (METRO_Gain_t)((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DFECTRL2&BIT_MASK_STPM_G_bit2)>>BIT_MASK_STPM_G_SHIFT);
    }
  }
  return Gain;
} 

/**
  * @brief      This function Set the temperature compensation  of the channel requested
  * @param[in]   in_Metro_Device_Id (device ID), EXT1 to EXT4
  * @param[in]   METRO_internal_Channel_t (Channel ID), Channel 1 or 2 ( according to device )
  * @param[in]   u8 in_Metro_TC_Value  (possible values : 0 to 7)
  * @param[out]  None
  * @retval      None
  */
void Metro_HAL_Set_Temperature_Compensation(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel, uint8_t in_Metro_TC_Value)
{

  if(in_Metro_Device_Id >= EXT1) 
  {
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    { 
      /* Reset all bits for  TC1 value*/
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1) &= ~ BIT_MASK_STPM_TC;

      /* set  TC value to TC1 to RAM struct fir EXT chip */
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1) |= (((uint32_t)in_Metro_TC_Value) << BIT_MASK_STPM_TC_SHIFT);
    }
    else  if ( in_Metro_int_Channel == INT_CHANNEL_2)
    {
       /* Reset all bits for  TC2 value*/
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL2) &= ~ BIT_MASK_STPM_TC;
        
      /* set  TC value to TC2 to RAM struct fir EXT chip */
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL2) |= (((uint32_t)in_Metro_TC_Value) << BIT_MASK_STPM_TC_SHIFT);
    }
      
    /* Now Write the 2 U32 registers inside external chip  for DSP CR1 and CR2 -> start address is DSPCR1 -> address = 0 */
    Metro_HAL_Stpm_write(in_Metro_Device_Id,STPM_DSPCTRL1,2,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1,STPM_WAIT);

  }
}
/**
  * @brief      This function Set the temperature compensation  of the channel requested
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   in_Metro_int_Channel (Channel ID), Channel 1 or 2 ( according to device )
  * @param[out]  None
  * @retval      return u8 Metro_TC_Value  (possible values : 0 to 7)
  */

uint8_t Metro_HAL_Get_Temperature_Compensation(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel)
{
  uint8_t TC_Value = 0;
  
  if(in_Metro_Device_Id >= EXT1) 
  {
    if (in_Metro_int_Channel == INT_CHANNEL_1)
    { 
      /* get TC1 value from EXT chip  */
      TC_Value = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1)&BIT_MASK_STPM_TC)>> BIT_MASK_STPM_TC_SHIFT;
    }
    else if (in_Metro_int_Channel == INT_CHANNEL_2)
    {
      /* get TC2 value from EXT chip */
      TC_Value = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL2)&BIT_MASK_STPM_TC)>> BIT_MASK_STPM_TC_SHIFT;     
    }
  }
  return (TC_Value);  
}

/**
  * @brief  Enable and set the tamper tolerance for detecting unbalanced active energy between the two current channels.
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_internal_Channel_t (Channel ID), Channel tamper according to device
  * @param[in]   in_Metro_Tamper_Tolerance   TOL_12_5 = 0,  TOL_8_33 = 1, TOL_6_25 = 2, TOL_3_125 = 3 or NO_CHANGE_TOL = 4 ( if no change of tolerance is requested)
    TMP_TOL[1:0] Tamper tolerance
      0x00 TOL = 12.5%
      0x01 TOL = 8.33%
      0x10 TOL = 6.25%
      0x11 TOL = 3.125%  
  * @param[in]   in_Metro_CMD :   DEVICE_DISABLE = 0,  DEVICE_ENABLE = 1 No_CHANGE = 2 ( if No change is requested about enable bit)  
  * @param[out]  None
  * @retval      None
  */
void Metro_HAL_Set_Tamper(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel, METRO_Tamper_Tolerance_t in_Metro_Tamper_Tolerance,METRO_CMD_Device_t in_Metro_CMD)
{
  uint32_t tmp_addr =0;

  if(in_Metro_Device_Id >= EXT1) 
  {
  
    if (in_Metro_Tamper_Tolerance != NO_CHANGE_TOL)
    {
      /* Reset all bits for  Tamper tolerance value*/
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3) &= ~ BIT_MASK_STPM_TAMPER_TOLERANCE;
          
      /* set  new  Tamper tolerance to RAM struct for EXT chip */
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3) |= (((uint32_t)in_Metro_Tamper_Tolerance) << BIT_MASK_STPM_TAMPER_TOLERANCE_SHIFT);       
     }
        
     if (in_Metro_CMD != NO_CHANGE)
     {
       /* Reset enable/disable tamper bit */
       (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3) &= ~ BIT_MASK_STPM_TAMPER_ENABLE; 
          
       /* set  new enable/disable tamper bit to RAM struct for EXT chip */
       (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3) |= (((uint32_t)in_Metro_CMD) << BIT_MASK_STPM_TAMPER_ENABLE_SHIFT);    
     }

     /* Now send data to the external chip */
     /* the address should be provided in 2 bytes format (16 bits by 16 bits) for STPM */
     tmp_addr = STPM_DSPCTRL3;
        
     /* Now Write the 1 U32 registers inside external chip  for DSPCR3 -> start address is DSPCR1 -> address = 0 */
     Metro_HAL_Stpm_write(in_Metro_Device_Id,(uint8_t*)&tmp_addr,1,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3,STPM_WAIT);

  }
}
/**
  * @brief   Get Tamper tolerance and TAMPER enable bit 
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_internal_Channel_t (Channel ID), Channel tamper according to device
  * @param[out]  Metro_Tamper_Tolerance  : TOL_12_5 = 1,  TOL_8_33 = 2, TOL_6_25 = 3, TOL_3_125 = 4
  * @retval     in_Metro_CMD :   DEVICE_DISABLE = 0,  DEVICE_ENABLE = 1 
  */
METRO_CMD_Device_t  Metro_HAL_Get_Tamper(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel, METRO_Tamper_Tolerance_t * out_p_Tamper_Tolerance)
{

  METRO_CMD_Device_t CMD_Device = DEVICE_DISABLE;

  if(in_Metro_Device_Id >= EXT1) 
  {
    /* Make something if channel requested is tamper, ifnot nothing to do */
    if (in_Metro_int_Channel == CHANNEL_TAMPER)
    {  
      /* it s a host requested */
      /* Get Tamper Tolerance from EXT chip  */
      *out_p_Tamper_Tolerance = (METRO_Tamper_Tolerance_t) (((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3)&BIT_MASK_STPM_TAMPER_TOLERANCE)>> BIT_MASK_STPM_TAMPER_TOLERANCE_SHIFT);

      /* Get Tamper Enable bit from EXT chip  */
      CMD_Device = (METRO_CMD_Device_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3)&BIT_MASK_STPM_TAMPER_ENABLE)>> BIT_MASK_STPM_TAMPER_ENABLE_SHIFT);   
    }
  }
  return (CMD_Device);  
}

/**
  * @brief       Enable and set ZCR config.
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_ZCR_Sel_t in_Metro_ZCR_Sel_config : ZCR_SEL_V1 = 0, ZCR_SEL_C1, ZCR_SEL_V2, ZCR_SEL_C2
  * @param[in]   in_Metro_CMD :   DEVICE_DISABLE = 0,  DEVICE_ENABLE = 1 No_CHANGE = 2 ( if No change is requested about enable bit)  
  * @param[out]  None
  * @retval      None
  */
void Metro_HAL_Set_ZCR(METRO_NB_Device_t in_Metro_Device_Id, METRO_ZCR_Sel_t in_Metro_ZCR_Sel_config,METRO_CMD_Device_t in_Metro_CMD)
{
  uint32_t tmp_addr =0;

  if(in_Metro_Device_Id >= EXT1) 
  {
  
    if (in_Metro_ZCR_Sel_config != NO_CHANGE_ZCR)
    {
      /* Reset all bits for  ZCR select value*/
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3) &= ~ BIT_MASK_STPM_ZCR_SEL;
        
      /* set  new  ZCR select value to  RAM struct for EXT chip */
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3) |= (((uint32_t)in_Metro_ZCR_Sel_config) << BIT_MASK_STPM_ZCR_SEL_SHIFT);
        
    }
      
    /* Disable ZCR requested */
    if (in_Metro_CMD == DEVICE_DISABLE)
    {
      /* Reset ZCR enable bit to disable ZCR feature */
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3) &= ~ BIT_MASK_STPM_ZCR_ENA; 
          
    } /* Enable Requested */
    else if (in_Metro_CMD == DEVICE_ENABLE)
    {
      /*  enable ZCR  bit to enable ZCR feature to RAM struct for EXT chip */
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3) |= BIT_MASK_STPM_ZCR_ENA;    
    }

    /* Now send data to the external chip */
    /* the address should be provided in 2 bytes format (16 bits by 16 bits) for STPM */
    tmp_addr = STPM_DSPCTRL3;
      
    /* Now Write the 1 U32 registers inside external chip  for DSPCR3 -> start address is DSPCR3 */
    Metro_HAL_Stpm_write(in_Metro_Device_Id,(uint8_t*)&tmp_addr,1,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3,STPM_WAIT);

  }
}

/*
  * @brief       Get ZCR config.
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[out]   METRO_ZCR_Sel_t out_p_Metro_ZCR_Sel_config : ZCR_SEL_V1 = 0, ZCR_SEL_C1, ZCR_SEL_V2, ZCR_SEL_C2
  * @retval      METRO_CMD_Device_t :   DEVICE_DISABLE = 0,  DEVICE_ENABLE = 1  
  */
METRO_CMD_Device_t  Metro_HAL_Get_ZCR(METRO_NB_Device_t in_Metro_Device_Id, METRO_ZCR_Sel_t * out_p_Metro_ZCR_Sel_config)
{

  METRO_CMD_Device_t CMD_Device = DEVICE_DISABLE;

  if(in_Metro_Device_Id >= EXT1) 
  {
    /* Get ZCR config from EXT chip  */
    *out_p_Metro_ZCR_Sel_config = (METRO_ZCR_Sel_t) (((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3)&BIT_MASK_STPM_ZCR_SEL)>> BIT_MASK_STPM_ZCR_SEL_SHIFT);

    /* Get ZCR Enable bit from EXT chip  */
    CMD_Device = (METRO_CMD_Device_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3)&BIT_MASK_STPM_ZCR_ENA)>> BIT_MASK_STPM_ZCR_ENA_SHIFT);   
  }
  return (CMD_Device);  
}

/**
  * @brief       Set CLK config.
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_CLK_Sel_t in_Metro_CLK_Sel_config :   CLK_SEL_7KHz = 0,  CLK_SEL_4MHz, CLK_SEL_4MHz_50,CLK_SEL_16MHz
  * @param[in]   METRO_CMD_Device_t :   DEVICE_DISABLE = 0,  DEVICE_ENABLE = 1  
  * @retval      METRO_CMD_Device_t :   DEVICE_DISABLE = 0,  DEVICE_ENABLE = 1  

  */
void Metro_HAL_Set_CLK(METRO_NB_Device_t in_Metro_Device_Id, METRO_CLK_Sel_t in_Metro_CLK_Sel_config,METRO_CMD_Device_t in_Metro_CMD)
{
  uint32_t tmp_addr =0;

  if(in_Metro_Device_Id >= EXT1) 
  {  
    if (in_Metro_CLK_Sel_config != NO_CHANGE_CLK)
    {
      /* Reset all bits for  CLK select value*/
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3) &= ~ BIT_MASK_STPM_CLK_SEL;
        
      /* set  new  CLK select value to  RAM struct for EXT chip */
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3) |= (((uint32_t)in_Metro_CLK_Sel_config) << BIT_MASK_STPM_CLK_SEL_SHIFT);
        
    }
      
    /* Disable CLK requested */
    if (in_Metro_CMD == DEVICE_DISABLE)
    {
      /* SET CLK  bit to disable CLK feature */
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3) |= BIT_MASK_STPM_CLK_ENA;    
    
    } /* Enable Requested */
    else if (in_Metro_CMD == DEVICE_ENABLE)
    {
      /*  Disable CLK  bit to enable CLK feature to RAM struct for EXT chip */
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3) &= ~ BIT_MASK_STPM_CLK_ENA; 

    }

    /* Now send data to the external chip */
    /* the address should be provided in 2 bytes format (16 bits by 16 bits) for STPM */
    tmp_addr = STPM_DSPCTRL3;
      
    /* Now Write the 1 U32 registers inside external chip  for DSPCR3 -> start address is DSPCR3 */
    Metro_HAL_Stpm_write(in_Metro_Device_Id,(uint8_t*)&tmp_addr,1,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3,STPM_WAIT);
  }
}

/*
  * @brief        Get CLK config.
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[out]   METRO_CLK_Sel_t out_p_Metro_CLK_Sel_config :   CLK_SEL_7KHz = 0,  CLK_SEL_4MHz, CLK_SEL_4MHz_50,CLK_SEL_16MHz,
  * @retval      METRO_CMD_Device_t :   DEVICE_DISABLE = 0,  DEVICE_ENABLE = 1  
  */
METRO_CMD_Device_t  Metro_HAL_Get_CLK(METRO_NB_Device_t in_Metro_Device_Id, METRO_CLK_Sel_t * out_p_Metro_CLK_Sel_config)
{

  METRO_CMD_Device_t CMD_Device = DEVICE_DISABLE;

  if(in_Metro_Device_Id >= EXT1) 
  {
    /* Get CLK config from EXT chip  */
    *out_p_Metro_CLK_Sel_config = (METRO_CLK_Sel_t) (((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3)&BIT_MASK_STPM_CLK_SEL)>> BIT_MASK_STPM_CLK_SEL_SHIFT);

    /* Get CLK Enable bit from EXT chip  */
    CMD_Device = (METRO_CMD_Device_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3)&BIT_MASK_STPM_CLK_ENA)>> BIT_MASK_STPM_CLK_ENA_SHIFT);   
      
    /* reverse the value read inside register,  because 0 : means CLK enable and 1 means disable for CLK output */
    if (CMD_Device == DEVICE_ENABLE)
    {
      CMD_Device = DEVICE_DISABLE;
    }
    else if (CMD_Device == DEVICE_DISABLE)
    {
      CMD_Device = DEVICE_ENABLE;      
    }
  }
  return (CMD_Device);    
}

/**
  * @brief       Set Led Power Config.
  * @param[in]   METRO_NB_Device_t in_Metro_Device (Device ID ), HOST or EXT1 to EXT4 
  * @param[in]   METRO_LED_Selection_t in_Metro_LED_Selection  :     LED1 = 1,  LED2 = 2 
  * @param[in]   METRO_LED_Power_selection_t in_Metro_Power_Selection :   LED_W_ACTIVE = 0,  LED_F_ACTIVE, LED_REACTIVE, LED_APPARENT_RMS 
  * @param[Out]  None 
  * @retval      None
  */
void Metro_HAL_Set_Led_Power_Config(METRO_NB_Device_t in_Metro_Device, METRO_LED_Selection_t in_Metro_LED_Selection,METRO_LED_Power_selection_t in_Metro_Power_Selection)
{ 
  if(in_Metro_Device >= EXT1) 
  {
    /* Set params for Good External LEd pin of external chip (1 or 2)*/
    if (in_Metro_LED_Selection == LED1)
    {  
      
      /* Reset all bits for LED power selection  */
      (p_Metro_Device_Config[in_Metro_Device].metro_stpm_reg.DSPCTRL1) &= ~ BIT_MASK_STPM_LED_POWER_SEL;

      /* Set new LEd power selection config  */
      (p_Metro_Device_Config[in_Metro_Device].metro_stpm_reg.DSPCTRL1) |= (((uint32_t)in_Metro_Power_Selection) << BIT_MASK_STPM_LED_POWER_SEL_SHIFT);
      
    }
    else if (in_Metro_LED_Selection == LED2)
    {
         
      /* Reset all bits for LED power selection    */
      (p_Metro_Device_Config[in_Metro_Device].metro_stpm_reg.DSPCTRL2) &= ~ BIT_MASK_STPM_LED_POWER_SEL;

      /* Set new LEd power slection config    */
      (p_Metro_Device_Config[in_Metro_Device].metro_stpm_reg.DSPCTRL2) |= (((uint32_t)in_Metro_Power_Selection) << BIT_MASK_STPM_LED_POWER_SEL_SHIFT);
        
    }
        
      /* Now Write the 2 U32 registers inside external chip  for DSPCR -> start address is DSPCR1 */
      Metro_HAL_Stpm_write(in_Metro_Device,STPM_DSPCTRL1,2,&p_Metro_Device_Config[in_Metro_Device].metro_stpm_reg.DSPCTRL1,STPM_WAIT);
  }
}

/**
  * @brief       Set Led Channel Config.
  * @param[in]   METRO_NB_Device_t in_Metro_Device (Device ID ), HOST or EXT1 to EXT4 
  * @param[in]   METRO_LED_Selection_t in_Metro_LED_Selection  :     LED1 = 1,  LED2 = 2 
  * @param[in]   METRO_LED_Channel_t in_Metro_LED_Channel :    PRIMARY = 0,  SECONDARY, ALGEBRIC, SIGMA_DELTA  
  * @param[Out]  None 
  * @retval      None
  */
void Metro_HAL_Set_Led_Channel_Config(METRO_NB_Device_t in_Metro_Device, METRO_LED_Selection_t in_Metro_LED_Selection,METRO_LED_Channel_t in_Metro_LED_Channel)
{ 

  if(in_Metro_Device >= EXT1) 
  {
    /* Set params for Good External LEd pin of external chip (1 or 2)*/
    if (in_Metro_LED_Selection == LED1)
    {  
      /* Reset all bits for LED Channel selection */
      (p_Metro_Device_Config[in_Metro_Device].metro_stpm_reg.DSPCTRL1) &= ~ BIT_MASK_STPM_LED_CH_SEL;

       /* Set new LEd Channel config  */
      (p_Metro_Device_Config[in_Metro_Device].metro_stpm_reg.DSPCTRL1) |= (((uint32_t)in_Metro_LED_Channel) << BIT_MASK_STPM_LED_CH_SEL_SHIFT);    
    }
    else if (in_Metro_LED_Selection == LED2)
    {
      /* Reset all bits for LED Channel selection PROG   */
      (p_Metro_Device_Config[in_Metro_Device].metro_stpm_reg.DSPCTRL2) &= ~ BIT_MASK_STPM_LED_CH_SEL;

      /* Set new LEd Channel config config  */
      (p_Metro_Device_Config[in_Metro_Device].metro_stpm_reg.DSPCTRL2) |= (((uint32_t)in_Metro_LED_Channel) << BIT_MASK_STPM_LED_CH_SEL_SHIFT);     
    }
        
    /* Now Write the 2 U32 registers inside external chip  for DSPCR -> start address is DSPCR1 */
    Metro_HAL_Stpm_write(in_Metro_Device,STPM_DSPCTRL1,2,&p_Metro_Device_Config[in_Metro_Device].metro_stpm_reg.DSPCTRL1,STPM_WAIT);
  }
}
/**
  * @brief       Get Led Power Config.
  * @param[in]   METRO_NB_Device_t in_Metro_Device (Device ID ), HOST or EXT1 to EXT4 
  * @param[in]   METRO_LED_Selection_t in_Metro_LED_Selection  :     LED1 = 1,  LED2 = 2 
  * @param[out]  METRO_LED_Power_selection_t * out_p_Metro_Power_Selection :   LED_W_ACTIVE = 0,  LED_F_ACTIVE, LED_REACTIVE, LED_APPARENT_RMS 
  * @retval      None
  */
void Metro_HAL_Get_Led_Power_Config(METRO_NB_Device_t in_Metro_Device, METRO_LED_Selection_t in_Metro_LED_Selection,METRO_LED_Power_selection_t * out_p_Metro_Power_Selection)
{
  if(in_Metro_Device >= EXT1) 
  {
    /* Get params for Good External LEd pin of external chip (1 or 2)*/
    if (in_Metro_LED_Selection == LED1)
    {  
      /* Get  LEd power selection config   */
       *out_p_Metro_Power_Selection = (METRO_LED_Power_selection_t) (((p_Metro_Device_Config[in_Metro_Device].metro_stpm_reg.DSPCTRL1)&BIT_MASK_STPM_LED_POWER_SEL)>> BIT_MASK_STPM_LED_POWER_SEL_SHIFT);
    }
    else if (in_Metro_LED_Selection == LED2)
    {
      /* Get  LEd power selection config   */
       *out_p_Metro_Power_Selection = (METRO_LED_Power_selection_t) (((p_Metro_Device_Config[in_Metro_Device].metro_stpm_reg.DSPCTRL2)&BIT_MASK_STPM_LED_POWER_SEL)>> BIT_MASK_STPM_LED_POWER_SEL_SHIFT);
    }
  }
}
/**
  * @brief       Get Led Channel Config.
  * @param[in]   METRO_NB_Device_t in_Metro_Device (Device ID ), HOST or EXT1 to EXT4 
  * @param[in]   METRO_LED_Selection_t in_Metro_LED_Selection  :     LED1 = 1,  LED2 = 2 
  * @param[out]  METRO_LED_Channel_t * out_p_Metro_LED_Channel :    PRIMARY = 0,  SECONDARY, ALGEBRIC, SIGMA_DELTA  
  * @retval      None
  */
void Metro_HAL_Get_Led_Channel_Config(METRO_NB_Device_t in_Metro_Device, METRO_LED_Selection_t in_Metro_LED_Selection,METRO_LED_Channel_t * out_p_Metro_LED_Channel)
{
  if(in_Metro_Device >= EXT1) 
  {
    /* Get params for Good External LEd pin of external chip (1 or 2)*/
    if (in_Metro_LED_Selection == LED1)
    {  
      /* Get  LEd Channel config  */
       *out_p_Metro_LED_Channel = (METRO_LED_Channel_t) (((p_Metro_Device_Config[in_Metro_Device].metro_stpm_reg.DSPCTRL1)&BIT_MASK_STPM_LED_CH_SEL)>> BIT_MASK_STPM_LED_CH_SEL_SHIFT);
    }
    else if (in_Metro_LED_Selection == LED2)
    {
      /* Get  LEd Channel config  */
       *out_p_Metro_LED_Channel = (METRO_LED_Channel_t) (((p_Metro_Device_Config[in_Metro_Device].metro_stpm_reg.DSPCTRL2)&BIT_MASK_STPM_LED_CH_SEL)>> BIT_MASK_STPM_LED_CH_SEL_SHIFT);
    }
  }
}
/**
  * @brief       Set Led Speed divisor.
  * @param[in]   METRO_NB_Device_t in_Metro_Device (Device ID ), HOST or EXT1 to EXT4 
  * @param[in]   METRO_LED_Selection_t in_Metro_LED_Selection  :     LED1 = 1,  LED2 = 2 
  * @param[in]   u8 in_Metro_LED_Speed_divisor  :     0 to 15 ( 4 bits only used amoung the U8) 
  * @param[Out]  None 
  * @retval      None
  */
void Metro_HAL_Set_Led_Speed_divisor(METRO_NB_Device_t in_Metro_Device, METRO_LED_Selection_t in_Metro_LED_Selection,uint8_t in_Metro_LED_Speed_divisor)
{

  if(in_Metro_Device >= EXT1) 
  {
    /* Set params for Good External LEd pin of external chip (1 or 2)*/
    if (in_Metro_LED_Selection == LED1)
    {  
      /* Reset all bits for LED Speed divider   */
      (p_Metro_Device_Config[in_Metro_Device].metro_stpm_reg.DSPCTRL1) &= ~ BIT_MASK_STPM_LED_SPEED_DIV;

      /* Set new LEd Speed divider  config  */
      (p_Metro_Device_Config[in_Metro_Device].metro_stpm_reg.DSPCTRL1) |= (((uint32_t)in_Metro_LED_Speed_divisor) << BIT_MASK_STPM_LED_SPEED_DIV_SHIFT);
      
    }
    else if (in_Metro_LED_Selection == LED2)
    {      
      /* Reset all bits for LED Speed divider     */
      (p_Metro_Device_Config[in_Metro_Device].metro_stpm_reg.DSPCTRL2) &= ~ BIT_MASK_STPM_LED_SPEED_DIV;

      /* Set new LEd Speed divider  config    */
      (p_Metro_Device_Config[in_Metro_Device].metro_stpm_reg.DSPCTRL2) |= (((uint32_t)in_Metro_LED_Speed_divisor) << BIT_MASK_STPM_LED_SPEED_DIV_SHIFT);     
    }
      
    /* Now Write the 2 U32 registers inside external chip  for DSPCR -> start address is DSPCR1 */
    Metro_HAL_Stpm_write(in_Metro_Device,STPM_DSPCTRL1,2,&p_Metro_Device_Config[in_Metro_Device].metro_stpm_reg.DSPCTRL1,STPM_WAIT);
  }
}

/**
  * @brief       Get Led Speed divisor.
  * @param[in]   METRO_NB_Device_t in_Metro_Device (Device ID ), HOST or EXT1 to EXT4 
  * @param[in]   METRO_LED_Selection_t in_Metro_LED_Selection  :     LED1 = 1,  LED2 = 2 
  * @retval      u8 Metro_LED_Speed_divisor  :     0 to 15 ( 4 bits only used amoung the U8)
  */
uint8_t Metro_HAL_Get_Led_Speed_divisor(METRO_NB_Device_t in_Metro_Device,METRO_LED_Selection_t in_Metro_LED_Selection)
{
  uint8_t Led_speed_divisor = 0;

  if(in_Metro_Device >= EXT1) 
  {
    /* Get LEd Speed diviser config for Good External LEd pin of external chip (1 or 2)*/
    if (in_Metro_LED_Selection == LED1)
    {      
      /* Get  LEd Speed diviser config  */
       Led_speed_divisor = (uint8_t) (((p_Metro_Device_Config[in_Metro_Device].metro_stpm_reg.DSPCTRL1)&BIT_MASK_STPM_LED_SPEED_DIV)>> BIT_MASK_STPM_LED_SPEED_DIV_SHIFT);
    }
    else if (in_Metro_LED_Selection == LED2)
    { 
      /* Get  LEd Speed diviser config  */
       Led_speed_divisor = (uint8_t) (((p_Metro_Device_Config[in_Metro_Device].metro_stpm_reg.DSPCTRL2)&BIT_MASK_STPM_LED_SPEED_DIV)>> BIT_MASK_STPM_LED_SPEED_DIV_SHIFT); 
    }
  }
  return Led_speed_divisor;
}

/**
  * @brief       Set Led On Off config.
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_LED_Selection_t in_Metro_LED_Selection  :     LED1 = 1,  LED2 = 2 
  * @param[in]   METRO_CMD_Device_t :   DEVICE_DISABLE = 0,  DEVICE_ENABLE = 1  
  * @retval      None 
  */
void Metro_HAL_Set_Led_On_Off(METRO_NB_Device_t in_Metro_Device_Id, METRO_LED_Selection_t in_Metro_LED_Selection,METRO_CMD_Device_t in_Metro_CMD)
{
  uint32_t tmp_addr =0;

  if(in_Metro_Device_Id >= EXT1) 
  {  
    if (in_Metro_LED_Selection == LED1)
    {       
      /* Disable LED output requested */
      if (in_Metro_CMD == DEVICE_DISABLE)
      {
        /* SET Led  bit to disable LED feature */
         (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3) |= BIT_MASK_STPM_LED1_OFF;    
      
      } /* Enable Led output Requested */
      else if (in_Metro_CMD == DEVICE_ENABLE)
      {
        /*  Disable Led  bit to enable LEd feature to RAM struct for EXT chip */
        (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3) &= ~ BIT_MASK_STPM_LED1_OFF; 
      }
    }
    else if (in_Metro_LED_Selection == LED2)
    {
      /* Disable LED output requested */
      if (in_Metro_CMD == DEVICE_DISABLE)
      {
        /* SET Led  bit to disable LED feature */
         (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3) |= BIT_MASK_STPM_LED2_OFF;    
      
      } /* Enable Led output Requested */
      else if (in_Metro_CMD == DEVICE_ENABLE)
      {
        /*  Disable Led  bit to enable LEd feature to RAM struct for EXT chip */
        (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3) &= ~ BIT_MASK_STPM_LED2_OFF; 

      }
        
    }

    /* Now send data to the external chip */
    /* the address should be provided in 2 bytes format (16 bits by 16 bits) for STPM */
    tmp_addr = STPM_DSPCTRL3;
    
    /* Now Write the 1 U32 registers inside external chip  for DSPCR3 -> start address is DSPCR3 */
    Metro_HAL_Stpm_write(in_Metro_Device_Id,(uint8_t*)&tmp_addr,1,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3,STPM_WAIT);

  }
}
/*
  * @brief        Get Led On Off config.
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_LED_Selection_t in_Metro_LED_Selection  :     LED1 = 1,  LED2 = 2 
  * @retval      METRO_CMD_Device_t :   DEVICE_DISABLE = 0,  DEVICE_ENABLE = 1  
  */
METRO_CMD_Device_t  Metro_HAL_Get_Led_On_Off(METRO_NB_Device_t in_Metro_Device_Id, METRO_LED_Selection_t in_Metro_LED_Selection)
{

  METRO_CMD_Device_t CMD_Device = DEVICE_ENABLE;

  if(in_Metro_Device_Id >= EXT1) 
  {

    if (in_Metro_LED_Selection == LED1)
    {       
      /* Get LED 1 Enable bit from EXT chip  */
      CMD_Device = (METRO_CMD_Device_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3)&BIT_MASK_STPM_LED1_OFF)>> BIT_MASK_STPM_LED1_OFF_SHIFT);   
        
      /* reverse the value read inside register,  because 0 : means LEED enable and 1 means disable for LEDs output */
      if (CMD_Device == DEVICE_ENABLE)
      {
        CMD_Device = DEVICE_DISABLE;
      }
      else if (CMD_Device == DEVICE_DISABLE)
      {
        CMD_Device = DEVICE_ENABLE;      
      }
    }
    else if (in_Metro_LED_Selection == LED2)
    {
      /* Get LED 2 Enable bit from EXT chip  */
      CMD_Device = (METRO_CMD_Device_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3)&BIT_MASK_STPM_LED2_OFF)>> BIT_MASK_STPM_LED2_OFF_SHIFT);   
        
      /* reverse the value read inside register,  because 0 : means LED enable and 1 means disable for LED output */
      if (CMD_Device == DEVICE_ENABLE)
      {
        CMD_Device = DEVICE_DISABLE;
      }
      else if (CMD_Device == DEVICE_DISABLE)
      {
        CMD_Device = DEVICE_ENABLE;      
      }      
    }
  }
  return (CMD_Device);    
}

/**
  * @brief  Set VRef of device according to internal channel
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_internal_Channel_t (Channel ID), Channel 1 or 2 ( according to device )
  * @param[in]   in_Metro_Vref :INT_VREF , EXT_VREF
  * @param[out]  None
  * @retval      None
  */
void Metro_HAL_Set_Vref(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel, METRO_Vref_t in_Metro_Vref)
{
  if(in_Metro_Device_Id >= EXT1) 
  {
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    {
      if (in_Metro_Vref == EXT_VREF)
      {  
        /* Disable bit ENVREF1 to force EXT VREF use */
        (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1) &= ~ BIT_MASK_STPM_ENVREF1;
      }
      else if (in_Metro_Vref == INT_VREF)
      {  
        /* set bit ENVREF1 to force Internal Vref use */
        (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1) |= BIT_MASK_STPM_ENVREF1;
      }
    }
    else  if ( in_Metro_int_Channel == INT_CHANNEL_2)
    {
      if (in_Metro_Vref == EXT_VREF)
      {  
        /* Disable bit ENVREF2 to force EXT VREF use */
        (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL2) &= ~ BIT_MASK_STPM_ENVREF2;
      }
      else if (in_Metro_Vref == INT_VREF)
      {  
        /* set bit ENVREF1 to force Internal Vref use */
        (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL2) |= BIT_MASK_STPM_ENVREF2;
      }
    }   
    /* Now Write the 2 U32 registers inside external chip  for DSP CR1 and CR2 -> start address is DSPCR1 -> address = 0 */
    Metro_HAL_Stpm_write(in_Metro_Device_Id,STPM_DSPCTRL1,2,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1,STPM_WAIT);
  }
}

/**
  * @brief  Get VRef  of device according to internal channel
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_internal_Channel_t (Channel ID), Channel 1 or 2 ( according to device )
  * @param[out]  None
* @retval        METRO_Vref_t :  EXT_VREF = 0, INT_VREF = 1
  */
METRO_Vref_t Metro_HAL_Get_Vref(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel)
{
  METRO_Vref_t  vref = EXT_VREF ;

  if(in_Metro_Device_Id >= EXT1) 
  {  
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    {
      /* Get bit ENVREF1 */
      vref =(METRO_Vref_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1)&BIT_MASK_STPM_ENVREF1) >> BIT_MASK_STPM_ENVREF1_SHIFT);
    }
    else  if (in_Metro_int_Channel == INT_CHANNEL_2)
    {
      /* Get bit ENVREF2  */
      vref=(METRO_Vref_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL2)&BIT_MASK_STPM_ENVREF2) >> BIT_MASK_STPM_ENVREF2_SHIFT);
    }   
  }
  return vref;
}

/**
  * @brief  enable/disable HightPass filters ( DC remover )  for Current  Channel (  C )
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_internal_Channel_t (Channel ID), Channel 1 or 2 ( according to device )
  * @param[in]   in_Metro_CMD :   DEVICE_DISABLE = 0,  DEVICE_ENABLE = 1
  * @param[out]  None
  * @retval      None
  */
void Metro_HAL_Set_Current_HP_Filter(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel, METRO_CMD_Device_t in_Metro_CMD)
{
  if(in_Metro_Device_Id >= EXT1) 
  {
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    {
      /* Reset enable/disable Current_HP_Filter bit */
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1) &= ~ BIT_MASK_STPM_CURR_HPF_BYPASS; 
          
      /* set  new enable/disable Current_HP_Filter bit to RAM struct for EXT chip */
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1) |= (((uint32_t)in_Metro_CMD) << BIT_MASK_STPM_CURR_HPF_BYPASS_SHIFT);
    }
    else  if( in_Metro_int_Channel == INT_CHANNEL_2)
    {
      /* Reset enable/disable Current_HP_Filter bit */
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL2) &= ~ BIT_MASK_STPM_CURR_HPF_BYPASS; 
          
      /* set  new enable/disable Current_HP_Filter bit to RAM struct for EXT chip */
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL2) |= (((uint32_t)in_Metro_CMD) << BIT_MASK_STPM_CURR_HPF_BYPASS_SHIFT);    
    }

    /* Now send data to the external chip */      
    /* Now Write the 2 U32 registers inside external chip  for DSPCR1 -> start address is DSPCR1 -> address = 0 */
    Metro_HAL_Stpm_write(in_Metro_Device_Id,STPM_DSPCTRL1,2,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1,STPM_WAIT);
  }
}


/**
  * @brief  enable/disable HightPass filters ( DC remover )  for Voltage Channel (  V )
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_internal_Channel_t (Channel ID), Channel 1 or 2 ( according to device )
  * @param[in]   in_Metro_CMD :   DEVICE_DISABLE = 0,  DEVICE_ENABLE = 1
  * @param[out]  None
  * @retval      None
  */
void Metro_HAL_Set_Voltage_HP_Filter(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel, METRO_CMD_Device_t in_Metro_CMD)
{

  if(in_Metro_Device_Id >= EXT1) 
  {
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    {
      /* Reset enable/disable Voltage HP Filter  bit */
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1) &= ~ BIT_MASK_STPM_VOLT_HPF_BYPASS; 
        
      /* set  new enable/disable Voltage HPF _Filter bit to RAM struct for EXT chip */
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1) |= (((uint32_t)in_Metro_CMD) << BIT_MASK_STPM_VOLT_HPF_BYPASS_SHIFT);
     }
     else if ( in_Metro_int_Channel == INT_CHANNEL_2)
     {
       /* Reset enable/disable Voltage HP_Filter bit */
       (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL2) &= ~ BIT_MASK_STPM_VOLT_HPF_BYPASS; 
        
       /* set  new enable/disable Voltage HP_Filter bit to RAM struct for EXT chip */
       (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL2) |= (((uint32_t)in_Metro_CMD) << BIT_MASK_STPM_VOLT_HPF_BYPASS_SHIFT);    
     }

     /* Now send data to the external chip */      
     /* Now Write the 2 U32 registers inside external chip  for DSPCR1 -> start address is DSPCR1 -> address = 0 */
     Metro_HAL_Stpm_write(in_Metro_Device_Id,STPM_DSPCTRL1,2,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1,STPM_WAIT);
  }
}

/**
  * @brief      Get configs for HP filters for Current Channel requested
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_internal_Channel_t (Channel ID), Channel 1 or 2 ( according to device )
  * @param[out]  None
  * @retval      Return METRO_CMD_Device_t :   DEVICE_DISABLE = 0,  DEVICE_ENABLE = 1
  */
METRO_CMD_Device_t Metro_HAL_Get_Current_HP_Filter(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel)
{
  METRO_CMD_Device_t CMD_Device = DEVICE_DISABLE;
  
  if(in_Metro_Device_Id >= EXT1) 
  {
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    {
      /* Get Current_HP_Filter Enable bit from EXT chip  */
      CMD_Device = (METRO_CMD_Device_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1)&BIT_MASK_STPM_CURR_HPF_BYPASS)>> BIT_MASK_STPM_CURR_HPF_BYPASS_SHIFT);   
    }
    else if ( in_Metro_int_Channel == INT_CHANNEL_2)
    {
      /* Get Current_HP_Filter Enable bit from EXT chip  */
      CMD_Device = (METRO_CMD_Device_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL2)&BIT_MASK_STPM_CURR_HPF_BYPASS)>> BIT_MASK_STPM_CURR_HPF_BYPASS_SHIFT);   
    }
  }
  return (CMD_Device);  
}

/**
  * @brief      Get configs for HP filters for Voltage Channel requested
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_internal_Channel_t (Channel ID), Channel 1 or 2 ( according to device )
  * @param[out]  None
  * @retval      Return METRO_CMD_Device_t :   DEVICE_DISABLE = 0,  DEVICE_ENABLE = 1
  */
METRO_CMD_Device_t Metro_HAL_Get_Voltage_HP_Filter(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel)
{
  METRO_CMD_Device_t CMD_Device = DEVICE_DISABLE;
  
  if(in_Metro_Device_Id >= EXT1) 
  {
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    {
      /* Get Voltage hP Filter Enable bit from EXT chip  */
      CMD_Device = (METRO_CMD_Device_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1)&BIT_MASK_STPM_VOLT_HPF_BYPASS)>> BIT_MASK_STPM_VOLT_HPF_BYPASS_SHIFT);   
    }
    else if ( in_Metro_int_Channel == INT_CHANNEL_2)
    {
      /* Get Voltage hP_Filter Enable bit from EXT chip  */
      CMD_Device = (METRO_CMD_Device_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL2)&BIT_MASK_STPM_VOLT_HPF_BYPASS)>> BIT_MASK_STPM_VOLT_HPF_BYPASS_SHIFT);   
    }
  }
  return (CMD_Device);  
}

/**
  * @brief       Enable or disable Coil integrator (Rogowski) for a  channel 
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_internal_Channel_t (Channel ID), Channel 1 or 2 ( according to device )
  * @param[in]   in_Metro_CMD :   DEVICE_DISABLE = 0,  DEVICE_ENABLE = 1
  * @param[out]  None
  * @retval      None
  */
void Metro_HAL_Set_Coil_integrator(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel, METRO_CMD_Device_t in_Metro_CMD)
{
  if(in_Metro_Device_Id >= EXT1) 
  {
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    {
      /* Reset enable/disable Coil_integrator bit */
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1) &= ~ BIT_MASK_STPM_CURR_ROGOWSKY_SEL; 
          
       /* set  new enable/disable Coil_integrator bit to RAM struct for EXT chip */
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1) |= (((uint32_t)in_Metro_CMD) << BIT_MASK_STPM_CURR_ROGOWSKY_SEL_SHIFT);
    }
    else  if( in_Metro_int_Channel == INT_CHANNEL_2)
    {
       /* Reset enable/disable Coil_integrator bit */
       (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL2) &= ~ BIT_MASK_STPM_CURR_ROGOWSKY_SEL; 
          
       /* set  new enable/disable Coil_integrator bit to RAM struct for EXT chip */
       (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL2) |= (((uint32_t)in_Metro_CMD) << BIT_MASK_STPM_CURR_ROGOWSKY_SEL_SHIFT);    
    }

    /* Now send data to the external chip */      
    /* Now Write the 2 U32 registers inside external chip  for DSPCR1 -> start address is DSPCR1 -> address = 0 */
    Metro_HAL_Stpm_write(in_Metro_Device_Id,STPM_DSPCTRL1,2,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1,STPM_WAIT);
  }
}
/**
  * @brief      Get configs for Coil integrator Rogowski  for Channel requested
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_internal_Channel_t (Channel ID), Channel 1 or 2 ( according to device )
  * @param[out]  None
  * @retval     Return METRO_CMD_Device_t :   DEVICE_DISABLE = 0,  DEVICE_ENABLE = 1,
  */
METRO_CMD_Device_t Metro_HAL_Get_Coil_integrator(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel)
{
  METRO_CMD_Device_t CMD_Device = DEVICE_DISABLE;
  
  if(in_Metro_Device_Id >= EXT1) 
  {
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    {
      /* Get Coil integrator Enable bit from EXT chip  */
      CMD_Device = (METRO_CMD_Device_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1)&BIT_MASK_STPM_CURR_ROGOWSKY_SEL)>> BIT_MASK_STPM_CURR_ROGOWSKY_SEL_SHIFT);   
    }
    else if ( in_Metro_int_Channel == INT_CHANNEL_2)
    {
      /* Get Coil integrator Enable bit from EXT chip  */
      CMD_Device = (METRO_CMD_Device_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL2)&BIT_MASK_STPM_CURR_ROGOWSKY_SEL)>> BIT_MASK_STPM_CURR_ROGOWSKY_SEL_SHIFT);   
    }
  }
  return (CMD_Device);     
}

/**
  * @brief       Get Ah Accumulation Down Threshold  for Channel requested
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_internal_Channel_t (Channel ID), Channel 1 or 2 ( according to device )
  * @param[out]  None
  * @retval     Return u16 :   Ah Accumulation Down Threshold
  */
uint16_t Metro_HAL_Get_Ah_Accumulation_Down_Threshold(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel)
{
  uint16_t Ah_Accumulation_Down_Threshold=0;
  
  if(in_Metro_Device_Id >= EXT1) 
  {
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    {
      /* Get Ah Accumulation Down Threshold from EXT chip  */
      Ah_Accumulation_Down_Threshold = (uint16_t)((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL10)&BIT_MASK_STPM_RMS1_VALUE_MIN);   
    }
    else if ( in_Metro_int_Channel == INT_CHANNEL_2)
    {
      /* Get Ah Accumulation Down Threshold EXT chip  */
      Ah_Accumulation_Down_Threshold = (uint16_t)((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL12)&BIT_MASK_STPM_RMS2_VALUE_MIN);   
    }
  }
  return (Ah_Accumulation_Down_Threshold);   
}


/**
  * @brief       Get Ah Accumulation Up Threshold  for Channel requested
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_internal_Channel_t (Channel ID), Channel 1 or 2 ( according to device )
  * @param[out]  None
  * @retval     Return u16 :   Ah Accumulation Up Threshold
  */
uint16_t Metro_HAL_Get_Ah_Accumulation_Up_Threshold(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel)
{
  uint16_t Ah_Accumulation_Up_Threshold=0;
  
  if(in_Metro_Device_Id >= EXT1) 
  {
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    {
      /* Get Ah Accumulation Up Threshold from EXT chip  */
      Ah_Accumulation_Up_Threshold = (uint16_t)((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL9)&BIT_MASK_STPM_RMS1_VALUE_MAX);   
    }
    else if ( in_Metro_int_Channel == INT_CHANNEL_2)
    {
      /* Get Ah Accumulation Up Threshold EXT chip  */
      Ah_Accumulation_Up_Threshold = (uint16_t)((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL11)&BIT_MASK_STPM_RMS2_VALUE_MAX);   
    }
  }
  return (Ah_Accumulation_Up_Threshold);     
}


/**
  * @brief       Set Ah Accumulation Down Threshold for a  channel 
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_internal_Channel_t (Channel ID), Channel 1 or 2 ( according to device )
  * @param[in]   u16 :   Ah Accumulation Down Threshold
  * @param[out]  None
  * @retval      None
  */
void Metro_HAL_Set_Ah_Accumulation_Down_Threshold(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel,uint16_t in_Metro_Ah_Down_Threshold)
{
  uint32_t tmp_addr =0;
  
  if(in_Metro_Device_Id >= EXT1) 
  {
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    {
      /* Reset Ah_Accumulation_Down_Threshold */
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL10) &= ~ BIT_MASK_STPM_RMS1_VALUE_MIN; 
        
      /* set  Ah_Accumulation_Down_Threshold to RAM struct for EXT chip */
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL10) |= ((uint32_t)in_Metro_Ah_Down_Threshold);
     }
     else  if( in_Metro_int_Channel == INT_CHANNEL_2)
     {
       /* Reset Ah_Accumulation_Down_Threshold */
       (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL12) &= ~ BIT_MASK_STPM_RMS2_VALUE_MIN; 
        
       /* set  Ah_Accumulation_Down_Threshold to RAM struct for EXT chip */
       (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL12) |= ((uint32_t)in_Metro_Ah_Down_Threshold);
     }

     /* Now send data to the external chip */
     /* the address should be provided in 2 bytes format (16 bits by 16 bits) for STPM */
     tmp_addr = STPM_DSPCTRL9;
            
            
     /* Now send data to the external chip */      
     /* Now Write the 4 U32 registers inside external chip  for DSPCR9 to 12 -> start address is DSPCR9 adress */
     Metro_HAL_Stpm_write(in_Metro_Device_Id,(uint8_t*)&tmp_addr,4,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL9,STPM_WAIT);

  }
}
/**
  * @brief       Set Ah Accumulation Up Threshold for a  channel 
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_internal_Channel_t (Channel ID), Channel 1 or 2 ( according to device )
  * @param[in]   u16 :   Ah Accumulation Up Threshold
  * @param[out]  None
  * @retval      None
  */
void Metro_HAL_Set_Ah_Accumulation_Up_Threshold(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel,uint16_t in_Metro_Ah_Up_Threshold)
{
  uint32_t tmp_addr =0;
  
  if(in_Metro_Device_Id >= EXT1) 
  {
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    {
      /* Reset Ah Accumulation Up Threshold */
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL9) &= ~ BIT_MASK_STPM_RMS1_VALUE_MAX; 
        
      /* set  Ah Accumulation Up Threshold to RAM struct for EXT chip */
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL9) |= ((uint32_t)in_Metro_Ah_Up_Threshold);
     }
     else  if( in_Metro_int_Channel == INT_CHANNEL_2)
     {
       /* Reset Ah Accumulation Up Threshold */
       (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL11) &= ~ BIT_MASK_STPM_RMS2_VALUE_MAX; 
        
       /* set  Ah Accumulation Up Threshold to RAM struct for EXT chip */
       (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL11) |= ((uint32_t)in_Metro_Ah_Up_Threshold);
     }

     /* Now send data to the external chip */
     /* the address should be provided in 2 bytes format (16 bits by 16 bits) for STPM */
     tmp_addr = STPM_DSPCTRL9;
            
     /* Now send data to the external chip */      
     /* Now Write the 4 U32 registers inside external chip  for DSPCR9 to 12 -> start address is DSPCR9 adress */
     Metro_HAL_Stpm_write(in_Metro_Device_Id,(uint8_t*)&tmp_addr,4,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL9,STPM_WAIT);
  }
}
/**
  * @brief       Set Power Offset Compensation from a channel and device
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_internal_Channel_t (Channel ID), Channel 1 or 2 ( according to device )
  * @param[in]   METRO_Power_selection_t in_Metro_Power_Selection : W_ACTIVE, F_ACTIVE, REACTIVE, APPARENT_RMS 
  * @param[in]   s16 in_Metro_Power_Offset
* @retval      None
  */
void Metro_HAL_Set_Power_Offset_Compensation(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel,METRO_Power_selection_t in_Metro_Power_Selection, int16_t in_Metro_Power_Offset)
{
  uint32_t tmp_addr =0;
  
  if(in_Metro_Device_Id >= EXT1) 
  {
    switch (in_Metro_Power_Selection)
    {
      case (W_ACTIVE):
      {
        if ( in_Metro_int_Channel == INT_CHANNEL_1)
        {  
          /* Reset Power Offset Compensation value  (COMET) */
          p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL9 &= ~ BIT_MASK_STPM_OFFSET_A1;
            
          /* Set Power Offset Compensation from EXT chip  */
          (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL9) |= (((uint32_t)(in_Metro_Power_Offset)<<BIT_MASK_STPM_OFFSET_A_SHIFT)& BIT_MASK_STPM_OFFSET_A1); 
        }
        else if ( in_Metro_int_Channel == INT_CHANNEL_2)
        {
          /* Reset Power Offset Compensation value  (COMET) */
          p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL11 &= ~ BIT_MASK_STPM_OFFSET_A2;
            
          /* Set Power Offset Compensation from EXT chip  */
          (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL11) |= (((uint32_t)(in_Metro_Power_Offset)<<BIT_MASK_STPM_OFFSET_A_SHIFT)& BIT_MASK_STPM_OFFSET_A2); 
        }
          
        /* Now send data to the external chip */
        /* the address should be provided in 2 bytes format (16 bits by 16 bits) for STPM */
        tmp_addr = STPM_DSPCTRL9;
                
                
        /* Now send data to the external chip */      
        /* Now Write the 4 U32 registers inside external chip  for DSPCR9 to 12 -> start address is DSPCR9 adress */
        Metro_HAL_Stpm_write(in_Metro_Device_Id,(uint8_t*)&tmp_addr,4,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL9,STPM_WAIT);
      }
      break;
      case (F_ACTIVE):
      {
        if ( in_Metro_int_Channel == INT_CHANNEL_1)
        {
          /* Reset Power Offset Compensation value  (COMET) */
          p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL9 &= ~ BIT_MASK_STPM_OFFSET_AF1;
            
          /* Set Power Offset Compensation from EXT chip  */
          (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL9) |= (((uint32_t)(in_Metro_Power_Offset)<<BIT_MASK_STPM_OFFSET_AF_SHIFT)& BIT_MASK_STPM_OFFSET_AF1); 
        }
        else if ( in_Metro_int_Channel == INT_CHANNEL_2)
        {
          /* Reset Power Offset Compensation value  (COMET) */
          p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL11 &= ~ BIT_MASK_STPM_OFFSET_AF2;
            
          /* Set Power Offset Compensation from EXT chip  */
          (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL11) |= (((uint32_t)(in_Metro_Power_Offset)<<BIT_MASK_STPM_OFFSET_AF_SHIFT)& BIT_MASK_STPM_OFFSET_AF2); 
        }
          
        /* Now send data to the external chip */
        /* the address should be provided in 2 bytes format (16 bits by 16 bits) for STPM */
        tmp_addr = STPM_DSPCTRL9;
                
        /* Now send data to the external chip */      
        /* Now Write the 4 U32 registers inside external chip  for DSPCR9 to 12 -> start address is DSPCR9 adress */
        Metro_HAL_Stpm_write(in_Metro_Device_Id,(uint8_t*)&tmp_addr,4,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL9,STPM_WAIT);

      }
      break;
      case (REACTIVE):
      {
        if ( in_Metro_int_Channel == INT_CHANNEL_1)
        {
          /* Reset Power Offset Compensation value  (COMET) */
          p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL10 &= ~ BIT_MASK_STPM_OFFSET_R1;
            
          /* Set Power Offset Compensation from EXT chip  */
          (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL10) |= (((uint32_t)(in_Metro_Power_Offset)<<BIT_MASK_STPM_OFFSET_R_SHIFT)& BIT_MASK_STPM_OFFSET_R1); 
        }
        else if ( in_Metro_int_Channel == INT_CHANNEL_2)
        {
          /* Reset Power Offset Compensation value  (COMET) */
          p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL12 &= ~ BIT_MASK_STPM_OFFSET_R2;
            
          /* Set Power Offset Compensation from EXT chip  */
          (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL12) |= (((uint32_t)(in_Metro_Power_Offset)<<BIT_MASK_STPM_OFFSET_R_SHIFT)& BIT_MASK_STPM_OFFSET_R2); 
        }
          
        /* Now send data to the external chip */
        /* the address should be provided in 2 bytes format (16 bits by 16 bits) for STPM */
        tmp_addr = STPM_DSPCTRL9;
                
        /* Now send data to the external chip */      
        /* Now Write the 4 U32 registers inside external chip  for DSPCR9 to 12 -> start address is DSPCR9 adress */
        Metro_HAL_Stpm_write(in_Metro_Device_Id,(uint8_t*)&tmp_addr,4,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL9,STPM_WAIT);

      }
      break;
      case (APPARENT_RMS):
      {
        if ( in_Metro_int_Channel == INT_CHANNEL_1)
        {
          /* Reset Power Offset Compensation value  (COMET) */
          p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL10 &= ~ BIT_MASK_STPM_OFFSET_S1;
            
          /* Set Power Offset Compensation from EXT chip  */
          (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL10) |= (((uint32_t)(in_Metro_Power_Offset)<<BIT_MASK_STPM_OFFSET_S_SHIFT)& BIT_MASK_STPM_OFFSET_S1); 
        }
        else if ( in_Metro_int_Channel == INT_CHANNEL_2)
        {
          /* Reset Power Offset Compensation value  (COMET) */
          p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL12 &= ~ BIT_MASK_STPM_OFFSET_S2;
            
          /* Set Power Offset Compensation from EXT chip  */
          (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL12) |= (((uint32_t)(in_Metro_Power_Offset)<<BIT_MASK_STPM_OFFSET_S_SHIFT)& BIT_MASK_STPM_OFFSET_S2); 
        }
          
        /* Now send data to the external chip */
        /* the address should be provided in 2 bytes format (16 bits by 16 bits) for STPM */
        tmp_addr = STPM_DSPCTRL9;
                       
        /* Now send data to the external chip */      
        /* Now Write the 4 U32 registers inside external chip  for DSPCR9 to 12 -> start address is DSPCR9 adress */
        Metro_HAL_Stpm_write(in_Metro_Device_Id,(uint8_t*)&tmp_addr,4,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL9,STPM_WAIT);

      }
      break;    

    }
  }   
}

/**
  * @brief       Get Power Offset Compensation from a channel and device
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_internal_Channel_t (Channel ID), Channel 1 or 2 ( according to device )
  * @param[in]  METRO_Power_selection_t in_Metro_Power_Selection : W_ACTIVE, F_ACTIVE, REACTIVE, APPARENT_RMS 
  * @retval     Return s16 :   Power_Offset_Compensation
  */
int16_t Metro_HAL_Get_Power_Offset_Compensation(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel,METRO_Power_selection_t in_Metro_Power_Selection)
{
  int16_t Power_Offset_Compensation=0;
  
  if(in_Metro_Device_Id >= EXT1) 
  {
    switch (in_Metro_Power_Selection)
    {
      case (W_ACTIVE):
      {
        if ( in_Metro_int_Channel == INT_CHANNEL_1)
        {
          /* Get Power Offset Compensation from EXT chip  */
          Power_Offset_Compensation = (int16_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL9)&BIT_MASK_STPM_OFFSET_A1) >> BIT_MASK_STPM_OFFSET_A_SHIFT) ;   
        }
        else if ( in_Metro_int_Channel == INT_CHANNEL_2)
        {
          /* Get Power Offset Compensation EXT chip  */
          Power_Offset_Compensation = (int16_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL11)&BIT_MASK_STPM_OFFSET_A2) >> BIT_MASK_STPM_OFFSET_A_SHIFT) ;   
        }
      }
      break;
      case (F_ACTIVE):
      {
        if ( in_Metro_int_Channel == INT_CHANNEL_1)
        {
          /* Get Power Offset Compensation from EXT chip  */
          Power_Offset_Compensation = (int16_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL9)&BIT_MASK_STPM_OFFSET_AF1) >> BIT_MASK_STPM_OFFSET_AF_SHIFT) ;   
        }
        else if ( in_Metro_int_Channel == INT_CHANNEL_2)
        {
          /* Get Power Offset Compensation EXT chip  */
          Power_Offset_Compensation = (int16_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL11)&BIT_MASK_STPM_OFFSET_AF2) >> BIT_MASK_STPM_OFFSET_AF_SHIFT) ;   
        }
      }
      break;
      case (REACTIVE):
      {
        if ( in_Metro_int_Channel == INT_CHANNEL_1)
        {
          /* Get Power Offset Compensation from EXT chip  */
          Power_Offset_Compensation = (int16_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL10)&BIT_MASK_STPM_OFFSET_R1) >> BIT_MASK_STPM_OFFSET_R_SHIFT) ;   
        }
        else if ( in_Metro_int_Channel == INT_CHANNEL_2)
        {
          /* Get Power Offset Compensation EXT chip  */
          Power_Offset_Compensation = (int16_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL12)&BIT_MASK_STPM_OFFSET_R2) >> BIT_MASK_STPM_OFFSET_R_SHIFT) ;   
        }
      }
      break;
      case (APPARENT_RMS):
      {
        if ( in_Metro_int_Channel == INT_CHANNEL_1)
        {
          /* Get Power Offset Compensation from EXT chip  */
          Power_Offset_Compensation = (int16_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL10)&BIT_MASK_STPM_OFFSET_S1) >> BIT_MASK_STPM_OFFSET_S_SHIFT) ;   
        }
        else if ( in_Metro_int_Channel == INT_CHANNEL_2)
        {
          /* Get Power Offset Compensation EXT chip  */
          Power_Offset_Compensation = (int16_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL12)&BIT_MASK_STPM_OFFSET_S2) >> BIT_MASK_STPM_OFFSET_S_SHIFT) ;   
        }
      }
      break;    

    }
   
    /* The return Metro_Power_Offset is in 16 signed */
    /* depending of device, the internal regisers are under 9 bits ( for COMET or STMET) and 10 bits (For STPM) in Two's cpomplemented format */
    /* So put the value in good format before to return it inside registers */
    
    /* Detect if the value is negative inside register   -> MSB of 10 bit = 1*/
    if ((Power_Offset_Compensation & BIT_MASK_STPM_POWER_SIGN) > 0)
    {
      /* now convert value in 10 bits two's Complemented format to S16 format */
      Power_Offset_Compensation |= 0xFC00;
    }
  }
  return (Power_Offset_Compensation);   
}

/**
  * @brief       Set V Calibration for a  channel 
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_internal_Channel_t (Channel ID), Channel 1 or 2 ( according to device )
  * @param[in]   u16 in_Metro_V_calibrator_value
  * @param[out]  None
  * @retval      None
  */
void Metro_HAL_Set_V_Calibration(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel, uint16_t in_Metro_V_calibrator_value)
{
  uint32_t tmp_addr =0;

  if(in_Metro_Device_Id >= EXT1) 
  {
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    {
      /* Reset  V Calibration value bits */
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL5) &= ~ BIT_MASK_STPM_CAL_V1; 
        
      /* Set new V Calibration value to RAM struct for EXT chip */
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL5) |= ((in_Metro_V_calibrator_value)& BIT_MASK_STPM_CAL_V1);
    }
    else  if( in_Metro_int_Channel == INT_CHANNEL_2)
    {
      /* Reset  V Calibration value bits */
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL7) &= ~ BIT_MASK_STPM_CAL_V2; 
        
      /* Set new V Calibration value to RAM struct for EXT chip */
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL7) |= ((in_Metro_V_calibrator_value)& BIT_MASK_STPM_CAL_V2);
    }

    /* Now send data to the external chip */
    /* the address should be provided in 2 bytes format (16 bits by 16 bits) for STPM */
    tmp_addr = STPM_DSPCTRL5;
       
    /* Now Write the 3 U32 registers inside external chip  for DSPCR5 to 7  */
    Metro_HAL_Stpm_write(in_Metro_Device_Id,(uint8_t*)&tmp_addr,3,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL5,STPM_WAIT);

  }
}
/**
  * @brief       Get V Calibration  for Channel requested
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_internal_Channel_t (Channel ID), Channel 1 or 2 ( according to device )
  * @param[out]  None
  * @retval     Return in_Metro_V_calibrator_value
  */
uint16_t Metro_HAL_Get_V_Calibration(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel)
{
  uint16_t  V_calibrator_value = 0;
  
  if(in_Metro_Device_Id >= EXT1) 
  {
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    {    
      /* Get  V Calibration value from RAM struct for EXT chip */
      V_calibrator_value = (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL5)&BIT_MASK_STPM_CAL_V1;
    }
    else  if( in_Metro_int_Channel == INT_CHANNEL_2)
    {     
      /* Get V Calibration value from RAM struct for EXT chip */
      V_calibrator_value = (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL7)&BIT_MASK_STPM_CAL_V2;
    }
  }
  return V_calibrator_value;
}

/**
  * @brief       Set C Calibration for a  channel 
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_internal_Channel_t (Channel ID), Channel 1 or 2 ( according to device )
  * @param[in]   u16 in_Metro_C_calibrator_value
  * @param[out]  None
  * @retval      None
  */
void Metro_HAL_Set_C_Calibration(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel, uint16_t in_Metro_C_calibrator_value)
{
  uint32_t tmp_addr =0;
    
  if(in_Metro_Device_Id >= EXT1) 
  {
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    {
      /* Reset  C Calibration value bits */
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL6) &= ~ BIT_MASK_STPM_CAL_C1; 
        
      /* Set new C Calibration value to RAM struct for EXT chip */
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL6) |= ((in_Metro_C_calibrator_value)& BIT_MASK_STPM_CAL_C1);
     }
     else  if( in_Metro_int_Channel == INT_CHANNEL_2)
     {
       /* Reset  C Calibration value bits */
       (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL8) &= ~ BIT_MASK_STPM_CAL_C2; 
        
       /* Set new C Calibration value to RAM struct for EXT chip */
       (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL8) |= ((in_Metro_C_calibrator_value)& BIT_MASK_STPM_CAL_C2);
     }

     /* Now send data to the external chip */
     /* the address should be provided in 2 bytes format (16 bits by 16 bits) for STPM */
     tmp_addr = STPM_DSPCTRL6;
       
     /* Now Write the 3 U32 registers inside external chip  for DSPCR6 to 8  */
     Metro_HAL_Stpm_write(in_Metro_Device_Id,(uint8_t*)&tmp_addr,3,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL6,STPM_WAIT);  
  }
}

/**
  * @brief       Get  C Calibration for Channel requested
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_internal_Channel_t (Channel ID), Channel 1 or 2 ( according to device )
  * @param[out]  None
  * @retval     Return in_Metro_C_calibrator_value
  */
uint16_t Metro_HAL_Get_C_Calibration(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel)
{
  uint16_t C_calibrator_value =0;
    
  if(in_Metro_Device_Id >= EXT1) 
  {
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    {     
       /* Get C Calibration value from RAM struct for EXT chip */
       C_calibrator_value = (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL6) & BIT_MASK_STPM_CAL_C1;
    }
    else  if( in_Metro_int_Channel == INT_CHANNEL_2)
    {      
       /* Get  C Calibration value from RAM struct for EXT chip */
       C_calibrator_value = (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL8) &BIT_MASK_STPM_CAL_C2;
    }
  }
  return C_calibrator_value;
}

/**
  * @brief       Set Phase V Calibration for a  channel 
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_internal_Channel_t (Channel ID), Channel 1 or 2 ( according to device )
  * @param[in]   u8 in_Metro_Phase_V_calibrator_value
  * @param[out]  None
  * @retval      None
  */
void Metro_HAL_Set_Phase_V_Calibration(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel, uint8_t in_Metro_Phase_V_calibrator_value)
{
   uint32_t tmp_addr =0;
    
  if(in_Metro_Device_Id >= EXT1) 
  {
     if ( in_Metro_int_Channel == INT_CHANNEL_1)
     {
        /* Reset  Phase V Calibration value bits */
        (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL4) &= ~ BIT_MASK_STPM_PHASE_SHIFT_V1; 
        
        /* Set new Phase V Calibration value to RAM struct for EXT chip */
        (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL4) |= (((uint32_t)(in_Metro_Phase_V_calibrator_value)<<BIT_MASK_STPM_PHASE_SHIFT_V1_SHIFT)& BIT_MASK_STPM_PHASE_SHIFT_V1);
     }
     else  if( in_Metro_int_Channel == INT_CHANNEL_2)
     {
         /* Reset Phase V Calibration value bits */
         (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL4) &= ~ BIT_MASK_STPM_PHASE_SHIFT_V2; 
        
         /* Set new Phase V Calibration value to RAM struct for EXT chip */
         (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL4) |= (((uint32_t)(in_Metro_Phase_V_calibrator_value)<<BIT_MASK_STPM_PHASE_SHIFT_V2_SHIFT)& BIT_MASK_STPM_PHASE_SHIFT_V2);
     }

      /* Now send data to the external chip */
      /* the address should be provided in 2 bytes format (16 bits by 16 bits) for STPM */
      tmp_addr = STPM_DSPCTRL4;
       
      /* Now Write the 1 U32 register inside external chip  for DSPCR4  */
      Metro_HAL_Stpm_write(in_Metro_Device_Id,(uint8_t*)&tmp_addr,1,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL4,STPM_WAIT);

  }
}
/**
  * @brief      Get Phase V Calibration  for Channel requested
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_internal_Channel_t (Channel ID), Channel 1 or 2 ( according to device )
  * @param[out]  None
  * @retval     Return in_Metro_Phase_V_calibrator_value
  */
uint8_t Metro_HAL_Get_Phase_V_Calibration(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel)
{
  uint16_t  Phase_V_calibrator_value =0;
    
  if(in_Metro_Device_Id >= EXT1) 
  {
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    {     
       /* Get  Phase V Calibration value from RAM struct for EXT chip */
       Phase_V_calibrator_value = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL4) & BIT_MASK_STPM_PHASE_SHIFT_V1) >>  BIT_MASK_STPM_PHASE_SHIFT_V1_SHIFT;
    }
    else  if( in_Metro_int_Channel == INT_CHANNEL_2)
    {     
       /* Get  Phase V Calibration value from RAM struct for EXT chip */
       Phase_V_calibrator_value = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL4) & BIT_MASK_STPM_PHASE_SHIFT_V2) >>  BIT_MASK_STPM_PHASE_SHIFT_V2_SHIFT;
    }
  }
  return Phase_V_calibrator_value;
}

/**
  * @brief       Set Phase C Calibration for a  channel 
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_internal_Channel_t (Channel ID), Channel 1 or 2 ( according to device )
  * @param[in]   u16 in_Metro_Phase_C_calibrator_value
  * @param[out]  None
  * @retval      None
  */
void Metro_HAL_Set_Phase_C_Calibration(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel, uint16_t in_Metro_Phase_C_calibrator_value)
{
   uint32_t tmp_addr =0;
  if(in_Metro_Device_Id >= EXT1) 
  {   
     if ( in_Metro_int_Channel == INT_CHANNEL_1)
     {
        /* Reset  Phase C Calibration value bits */
        (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL4) &= ~ BIT_MASK_STPM_PHASE_SHIFT_C1; 
        
        /* Set new Phase C Calibration value to RAM struct for EXT chip */
        (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL4) |= (((uint32_t)(in_Metro_Phase_C_calibrator_value)<<BIT_MASK_STPM_PHASE_SHIFT_C1_SHIFT)& BIT_MASK_STPM_PHASE_SHIFT_C1);
     }
     else  if( in_Metro_int_Channel == INT_CHANNEL_2)
     {
        /* Reset Phase C Calibration value bits */
        (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL4) &= ~ BIT_MASK_STPM_PHASE_SHIFT_C2; 
        
        /* Set new Phase C Calibration value to RAM struct for EXT chip */
        (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL4) |= ((uint32_t)(in_Metro_Phase_C_calibrator_value)& BIT_MASK_STPM_PHASE_SHIFT_C2);
     }

     /* Now send data to the external chip */
     /* the address should be provided in 2 bytes format (16 bits by 16 bits) for STPM */
     tmp_addr = STPM_DSPCTRL4;
       
     /* Now Write the 1 U32 register inside external chip  for DSPCR4  */
     Metro_HAL_Stpm_write(in_Metro_Device_Id,(uint8_t*)&tmp_addr,1,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL4,STPM_WAIT);
  }
}
/**
  * @brief        Get_Phase C Calibration for Channel requested
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_internal_Channel_t (Channel ID), Channel 1 or 2 ( according to device )
  * @param[out]  None
  * @retval     Return in_Metro_Phase_C_calibrator_value
  */
uint16_t Metro_HAL_Get_Phase_C_Calibration(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel)
{
  uint16_t Phase_C_calibrator_value =0;
    
  if(in_Metro_Device_Id >= EXT1) 
  {
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    {     
       /* Get Phase C Calibration value from RAM struct for EXT chip */
       Phase_C_calibrator_value = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL4) & BIT_MASK_STPM_PHASE_SHIFT_C1)>>BIT_MASK_STPM_PHASE_SHIFT_C1_SHIFT;
    }
    else  if( in_Metro_int_Channel == INT_CHANNEL_2)
    {      
       /* Get Phase C Calibration value from RAM struct for EXT chip */
       Phase_C_calibrator_value = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL4) & BIT_MASK_STPM_PHASE_SHIFT_C2);
    }
  }
  return Phase_C_calibrator_value;
}

/**
  * @brief      This function read the Power of signal come from one Channel mapped in one device
* @param[in]   in_Metro_Device_Id : EXT1 to EXT4
  * @param[in]   in_Metro_int_Channel (Channel ID), Channel 1 or 2 ( according to device )
  * @param[in]   in_Metro_Power_Selection : W_ACTIVE , F_ACTIVE, REACTIVE, APPARENT_RMS, APPARENT_VEC, MOM_WIDE_ACT, MOM_FUND_ACT
  * @param[out]  None
  * @retval     int32_t raw_power according to power type  read inside device register
  */

int32_t Metro_HAL_read_power(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel,METRO_Power_selection_t in_Metro_Power_Selection)
{
  int32_t raw_power = 0;

  if(in_Metro_Device_Id >= EXT1) 
  {
    switch (in_Metro_Power_Selection)
    {
      case (W_ACTIVE):
      {
        if (in_Metro_int_Channel == INT_CHANNEL_1)
        {
          /* get directly from RAM, be carrefull : latch should be made before to have coherents values inside DSP data reg */
          raw_power = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.CH1_REG5)&BIT_MASK_STPM_PRIM_CURR_ACTIVE_POW);
        }
        else if (in_Metro_int_Channel == INT_CHANNEL_2)/* is channel 2 */
        {
          /* get directly from RAM, be carrefull !!!!! : latch should be made before to have coherents values inside DSP data reg */
          raw_power = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.CH2_REG5)&BIT_MASK_STPM_SEC_CURR_ACTIVE_POW);
        }
      }
      break;
      case (F_ACTIVE):
      {
        if (in_Metro_int_Channel == INT_CHANNEL_1)
        {
          /* get directly from RAM, be carrefull : latch should be made before to have coherents values inside DSP data reg */
          raw_power = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.CH1_REG6)&BIT_MASK_STPM_PRIM_CURR_FUND_POW);
        }
        else if (in_Metro_int_Channel == INT_CHANNEL_2)/* is channel 2 */
        {
          /* get directly from RAM, be carrefull !!!!! : latch should be made before to have coherents values inside DSP data reg */
          raw_power = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.CH2_REG6)&BIT_MASK_STPM_SEC_CURR_FUND_POW);
        }
      }
      break;
      case (REACTIVE):
      {
        /* is Channel is the first or the second  channel of the chip */
        if (in_Metro_int_Channel == INT_CHANNEL_1)
        {
          /* get directly from RAM, be carrefull : latch should be made before to have coherents values inside DSP data reg */
          raw_power = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.CH1_REG7)&BIT_MASK_STPM_PRIM_CURR_REACT_POW);
        }
        else if (in_Metro_int_Channel == INT_CHANNEL_2)/* is channel 2 */
        {
          /* get directly from RAM, be carrefull !!!!! : latch should be made before to have coherents values inside DSP data reg */
          raw_power = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.CH2_REG7)&BIT_MASK_STPM_SEC_CURR_REACT_POW);
         }
      }
      break;
      case (APPARENT_RMS):
      {
        if (in_Metro_int_Channel == INT_CHANNEL_1)
        {
          /* get directly from RAM, be carrefull : latch should be made before to have coherents values inside DSP data reg */
          raw_power = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.CH1_REG8)&BIT_MASK_STPM_PRIM_CURR_RMS_POW);
        }
        else if (in_Metro_int_Channel == INT_CHANNEL_2)/* is channel 2 */
        {
          /* get directly from RAM, be carrefull !!!!! : latch should be made before to have coherents values inside DSP data reg */
          raw_power = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.CH2_REG8)&BIT_MASK_STPM_SEC_CURR_RMS_POW);
        }
      }
      break;
      case (APPARENT_VEC):
      {
        if (in_Metro_int_Channel == INT_CHANNEL_1)
        {
          /* get directly from RAM, be carrefull : latch should be made before to have coherents values inside DSP data reg */
          raw_power = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.CH1_REG9)&BIT_MASK_STPM_PRIM_CURR_VEC_POW);
        }
        else if (in_Metro_int_Channel == INT_CHANNEL_2)/* is channel 2 */
        {
          /* get directly from RAM, be carrefull !!!!! : latch should be made before to have coherents values inside DSP data reg */
          raw_power = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.CH2_REG9)&BIT_MASK_STPM_SEC_CURR_VEC_POW);
        }
      }
      break;
      case (MOM_WIDE_ACT):
      {
        if (in_Metro_int_Channel == INT_CHANNEL_1)
        {
          /* get directly from RAM, be carrefull : latch should be made before to have coherents values inside DSP data reg */
          raw_power = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.CH1_REG10)&BIT_MASK_STPM_PRIM_CURR_MOM_ACTIVE_POW);
        }
        else if (in_Metro_int_Channel == INT_CHANNEL_2)/* is channel 2 */
        {
          /* get directly from RAM, be carrefull !!!!! : latch should be made before to have coherents values inside DSP data reg */
          raw_power = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.CH2_REG10)&BIT_MASK_STPM_SEC_CURR_MOM_ACTIVE_POW);
        }
      }
      break;
      case (MOM_FUND_ACT):
      {
        if (in_Metro_int_Channel == INT_CHANNEL_1)
        {
          /* get directly from RAM, be carrefull : latch should be made before to have coherents values inside DSP data reg */
          raw_power = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.CH1_REG11)&BIT_MASK_STPM_PRIM_CURR_MOM_FUND_POW);
        }
        else if (in_Metro_int_Channel == INT_CHANNEL_2)/* is channel 2 */
        {
           /* get directly from RAM, be carrefull !!!!! : latch should be made before to have coherents values inside DSP data reg */
          raw_power = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.CH2_REG11)&BIT_MASK_STPM_SEC_CURR_MOM_FUND_POW);
        }
      }
      break;
    } /* end switch */

    raw_power <<= 4;  // handle sign extension as power is on 28 bits
    raw_power >>= 4;
  }
  return raw_power;
}

/**
  * @brief      This function read the Energy of signal come from one Channel mapped in one device
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   in_Metro_int_Channel (Channel ID), Channel 1 or 2 ( according to device )
  * @param[in]   in_Metro_Energy_Selection : E_W_ACTIVE , E_F_ACTIVE, E_REACTIVE, E_APPARENT
  * @param[out]  None
  * @retval     int32_t raw_nrj according to Energy type  read inside device register
  */

int64_t Metro_HAL_read_energy(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel,METRO_Energy_selection_t in_Metro_Energy_Selection)
{
  int32_t raw_nrj = 0;

  if(in_Metro_Device_Id >= EXT1) 
  {
    switch (in_Metro_Energy_Selection)
    {
      case (E_W_ACTIVE):
      {
      if (in_Metro_int_Channel == INT_CHANNEL_1)
        {
         /* get directly from RAM, be carrefull : latch should be made before to have coherents values inside DSP data reg */
          raw_nrj = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.CH1_REG1));
        }
        else if (in_Metro_int_Channel == INT_CHANNEL_2)
        {
          /* get directly from RAM, be carrefull !!!!! : latch should be made before to have coherents values inside DSP data reg */
          raw_nrj = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.CH2_REG1));
        }
      }
      break;
      case (E_F_ACTIVE):
      {
        if (in_Metro_int_Channel == INT_CHANNEL_1)
        {
          /* get directly from RAM, be carrefull : latch should be made before to have coherents values inside DSP data reg */
          raw_nrj = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.CH1_REG2));
        }
        else if (in_Metro_int_Channel == INT_CHANNEL_2)/* is channel 2 */
        {
          /* get directly from RAM, be carrefull !!!!! : latch should be made before to have coherents values inside DSP data reg */
          raw_nrj = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.CH2_REG2));
        }
      }
      break;
      case (E_REACTIVE):
      {
        if (in_Metro_int_Channel == INT_CHANNEL_1)
        {
          /* get directly from RAM, be carrefull : latch should be made before to have coherents values inside DSP data reg */
          raw_nrj = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.CH1_REG3));
        }
        else if (in_Metro_int_Channel == INT_CHANNEL_2)/* is channel 2 */
        {
          /* get directly from RAM, be carrefull !!!!! : latch should be made before to have coherents values inside DSP data reg */
          raw_nrj = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.CH2_REG3));
        }
      }
      break;
      case (E_APPARENT):
      {
      if (in_Metro_int_Channel == INT_CHANNEL_1)
        {
          /* get directly from RAM, be carrefull : latch should be made before to have coherents values inside DSP data reg */
          raw_nrj = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.CH1_REG4));
        }
        else if (in_Metro_int_Channel == INT_CHANNEL_2)/* is channel 2 */
        {
          /* get directly from RAM, be carrefull !!!!! : latch should be made before to have coherents values inside DSP data reg */
          raw_nrj = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.CH2_REG4));
        }
      }
      break;
    } /* end switch */
  }
  return raw_nrj;
}

/**
  * @brief       Set IRQ Mask for a channel
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   in_Metro_int_Channel (Channel ID), Channel 1 or 2 ( according to device )
  * @param[in]   in_Metro_IT_Mask :  Mask of interruption according to the channel
  * @param[out]  None
  * @retval      None
  */
void Metro_HAL_Set_IRQ_Mask_for_Channel(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel,uint32_t in_Metro_IT_Mask)
{
  uint32_t tmp_addr =0; 
   
  if(in_Metro_Device_Id >= EXT1) 
  {
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    {      
       /* Set new IRQ Mask for IRQ1 to RAM struct for EXT chip */
       (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPIRQ1) = in_Metro_IT_Mask&BIT_MASK_STPM_CHANNEL1_IRQ1;
    }
    else  if( in_Metro_int_Channel == INT_CHANNEL_2)
    {      
       /* Set new IRQ Mask for IRQ2 to RAM struct for EXT chip */
       (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPIRQ2) = in_Metro_IT_Mask&BIT_MASK_STPM_CHANNEL2_IRQ2;
    }

    /* Now send data to the external chip */
    /* the address should be provided in 2 bytes format (16 bits by 16 bits) for STPM */
    tmp_addr = STPM_DSPIRQ1;
       
    /* Now Write the 2 U32 register inside external chip  for DSPIRQ1 and DSPIRQ2  */
    Metro_HAL_Stpm_write(in_Metro_Device_Id,(uint8_t*)&tmp_addr,2,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPIRQ1,STPM_WAIT);
  }
}

/**
  * @brief      Get IRQ Mask for a channel
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   in_Metro_int_Channel (Channel ID), Channel 1 or 2 ( according to device )
  * @param[out]  None
  * @retval     u32 Metro_IT_Mask
  */
uint32_t Metro_HAL_Get_IRQ_Mask_for_Channel(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel)
{
  uint32_t Metro_IT_Mask =0;
    
  if(in_Metro_Device_Id >= EXT1) 
  {
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    {      
       /* Get IRQ Mask for IRQ1 from RAM struct for EXT chip */
       Metro_IT_Mask=(p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPIRQ1);
    }
    else  if( in_Metro_int_Channel == INT_CHANNEL_2)
    {      
       /* Get IRQ Mask for IRQ2 from RAM struct for EXT chip */
       Metro_IT_Mask=(p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPIRQ2);
    }
  }
  return Metro_IT_Mask;
}

/**
  * @brief       Get the specified live event for a channel
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   in_Metro_int_Channel (Channel ID), Channel 1 or 2 ( according to device )
  * @param[in]   METRO_Live_Event_Type_t type ( Live events are generated by DSP)
  * @param[out]  None
  * @retval     u32 : return full Live event Register  if in_Metro_Live_Event_requested == ALL_LIVE_EVENTS
  *             otherwise :the  Live event requested
  */
uint32_t Metro_HAL_Read_Live_Event_from_Channel(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel, METRO_Live_Event_Type_t in_Metro_Live_Event_requested)
{
  uint32_t Metro_Live_Event_reg =0;
   
  if(in_Metro_Device_Id >= EXT1) 
  {
    switch (in_Metro_Live_Event_requested)
    {
      /* All events requested, send back the full u32 reg */
      case ALL_LIVE_EVENTS:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Live Event Mask  from RAM struct for EXT chip */
            Metro_Live_Event_reg=(p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT1);
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Live Event Mask from RAM struct for EXT chip */
            Metro_Live_Event_reg=(p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT2);
         }
       }
       break;
       /* now the other cases , are bit by bit inside DSPEVEnts register */
       case LIVE_EVENT_VOLTAGE_SAG:
       {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Live Event Mask  from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT1)&BIT_MASK_STPM_VOLT_SAG_EV)>>BIT_MASK_STPM_VOLT_SAG_EV_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Live Event Mask from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT2)&BIT_MASK_STPM_VOLT_SAG_EV)>>BIT_MASK_STPM_VOLT_SAG_EV_SHIFT;
         }
       }
       break;
       case LIVE_EVENT_VOLTAGE_SWELL:
       {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Live Event Mask  from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT1)&BIT_MASK_STPM_VOLT_SWELL_EV)>>BIT_MASK_STPM_VOLT_SWELL_EV_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Live Event Mask from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT2)&BIT_MASK_STPM_VOLT_SWELL_EV)>>BIT_MASK_STPM_VOLT_SWELL_EV_SHIFT;
         }
       }
       break;
       case LIVE_EVENT_VOLTAGE_PERIOD_STATUS:
       {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Live Event Mask  from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT1)&BIT_MASK_STPM_VOLT_PERIOD_STATUS_EV)>>BIT_MASK_STPM_VOLT_PERIOD_STATUS_EV_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Live Event Mask from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT2)&BIT_MASK_STPM_VOLT_PERIOD_STATUS_EV)>>BIT_MASK_STPM_VOLT_PERIOD_STATUS_EV_SHIFT;
         }
       }
       break;
       case LIVE_EVENT_VOLTAGE_SIGNAL_STUCK:
       {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Live Event Mask  from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT1)&BIT_MASK_STPM_VOLT_SIG_STUCK_EV)>>BIT_MASK_STPM_VOLT_SIG_STUCK_EV_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Live Event Mask from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT2)&BIT_MASK_STPM_VOLT_SIG_STUCK_EV)>>BIT_MASK_STPM_VOLT_SIG_STUCK_EV_SHIFT;
         }
       }
       break;
       case LIVE_EVENT_VOLTAGE_ZCR:
       {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Live Event Mask  from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT1)&BIT_MASK_STPM_VOLT_ZCR_EV)>>BIT_MASK_STPM_VOLT_ZCR_EV_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Live Event Mask from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT2)&BIT_MASK_STPM_VOLT_ZCR_EV)>>BIT_MASK_STPM_VOLT_ZCR_EV_SHIFT;
         }
       }
       break;
       case LIVE_EVENT_CURRENT_SWELL:
       {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Live Event Mask  from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT1)&BIT_MASK_STPM_CURR_SWELL_EV)>>BIT_MASK_STPM_CURR_SWELL_EV_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Live Event Mask from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT2)&BIT_MASK_STPM_CURR_SWELL_EV)>>BIT_MASK_STPM_CURR_SWELL_EV_SHIFT;
         }
       }
       break;
       case LIVE_EVENT_CURRENT_SIGNAL_STUCK:
       {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Live Event Mask  from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT1)&BIT_MASK_STPM_CURR_SIG_STUCK_EV)>>BIT_MASK_STPM_CURR_SIG_STUCK_EV_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Live Event Mask from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT2)&BIT_MASK_STPM_CURR_SIG_STUCK_EV)>>BIT_MASK_STPM_CURR_SIG_STUCK_EV_SHIFT;
         }
       }
       break;
       case LIVE_EVENT_CURRENT_ZCR:
       {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Live Event Mask  from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT1)&BIT_MASK_STPM_CURR_ZCR_EV)>>BIT_MASK_STPM_CURR_ZCR_EV_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Live Event Mask from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT2)&BIT_MASK_STPM_CURR_ZCR_EV)>>BIT_MASK_STPM_CURR_ZCR_EV_SHIFT;
         }
       }
       break;
       case LIVE_EVENT_CURRENT_OVERFLOW_APPARENT_NRJ:
       {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Live Event Mask  from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT1)&BIT_MASK_STPM_CH_OV_S_EV)>>BIT_MASK_STPM_CH_OV_S_EV_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Live Event Mask from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT2)&BIT_MASK_STPM_CH_OV_S_EV)>>BIT_MASK_STPM_CH_OV_S_EV_SHIFT;
         }
       }
       break;
       case LIVE_EVENT_CURRENT_OVERFLOW_REACTIVE_NRJ:
       {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Live Event Mask  from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT1)&BIT_MASK_STPM_CH_OV_R_EV)>>BIT_MASK_STPM_CH_OV_R_EV_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Live Event Mask from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT2)&BIT_MASK_STPM_CH_OV_R_EV)>>BIT_MASK_STPM_CH_OV_R_EV_SHIFT;
         }
       }
       break;
       case LIVE_EVENT_CURRENT_OVERFLOW_FUNDAMENTAL_NRJ:
       {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Live Event Mask  from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT1)&BIT_MASK_STPM_CH_OV_F_EV)>>BIT_MASK_STPM_CH_OV_F_EV_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Live Event Mask from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT2)&BIT_MASK_STPM_CH_OV_F_EV)>>BIT_MASK_STPM_CH_OV_F_EV_SHIFT;
         }
       }
       break;
       case LIVE_EVENT_CURRENT_OVERFLOW_ACTIVE_NRJ:
       {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Live Event Mask  from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT1)&BIT_MASK_STPM_CH_OV_A_EV)>>BIT_MASK_STPM_CH_OV_A_EV_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Live Event Mask from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT2)&BIT_MASK_STPM_CH_OV_A_EV)>>BIT_MASK_STPM_CH_OV_A_EV_SHIFT;
         }
       }
       break;
       case LIVE_EVENT_CURRENT_SIGN_CHANGE_APPARENT_POWER:
       {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Live Event Mask  from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT1)&BIT_MASK_STPM_CH_PS_S_EV)>>BIT_MASK_STPM_CH_PS_S_EV_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Live Event Mask from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT2)&BIT_MASK_STPM_CH_PS_S_EV)>>BIT_MASK_STPM_CH_PS_S_EV_SHIFT;
         }
       }
       break;
       case LIVE_EVENT_CURRENT_SIGN_CHANGE_REACTIVE_POWER:
       {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Live Event Mask  from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT1)&BIT_MASK_STPM_CH_PS_R_EV)>>BIT_MASK_STPM_CH_PS_R_EV_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Live Event Mask from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT2)&BIT_MASK_STPM_CH_PS_R_EV)>>BIT_MASK_STPM_CH_PS_R_EV_SHIFT;
         }
       }
       break;
       case LIVE_EVENT_CURRENT_SIGN_CHANGE_FUNDAMENTAL_POWER:
       {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Live Event Mask  from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT1)&BIT_MASK_STPM_CH_PS_F_EV)>>BIT_MASK_STPM_CH_PS_F_EV_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Live Event Mask from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT2)&BIT_MASK_STPM_CH_PS_F_EV)>>BIT_MASK_STPM_CH_PS_F_EV_SHIFT;
         }
       }
       break;
       case LIVE_EVENT_CURRENT_SIGN_CHANGE_ACTIVE_POWER:
       {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Live Event Mask  from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT1)&BIT_MASK_STPM_CH_PS_A_EV)>>BIT_MASK_STPM_CH_PS_A_EV_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Live Event Mask from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT2)&BIT_MASK_STPM_CH_PS_A_EV)>>BIT_MASK_STPM_CH_PS_A_EV_SHIFT;
         }
       }
       break;
       case LIVE_EVENT_CURRENT_NAH:
       {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Live Event Mask  from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT1)&BIT_MASK_STPM_CURR_AH_ACC_EV)>>BIT_MASK_STPM_CURR_AH_ACC_EV_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Live Event Mask from RAM struct for EXT chip */
            Metro_Live_Event_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPEVENT2)&BIT_MASK_STPM_CURR_AH_ACC_EV)>>BIT_MASK_STPM_CURR_AH_ACC_EV_SHIFT;
         }
       }
       break;
    }
  }
  return Metro_Live_Event_reg; 
}

/**
  * @brief       Get the specified status for a channel
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   in_Metro_int_Channel (Channel ID), Channel 1 or 2 ( according to device )
  * @param[in]   METRO_Status_Type_t type ( Status registers are generated by IRQ  )
  * @param[out]  None
  * @retval     u32 : Full Status  Register  if in_Metro_Status_requested == ALL_STATUS
  *             otherwise : 0 if Status requested (IRQ) is NOT occured,  1 if Status requested IRQ occured
  */
uint32_t Metro_HAL_Read_Status_from_Channel(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel, METRO_Status_Type_t in_Metro_Status_requested)
{
  uint32_t Metro_Status_reg =0;
  
  if(in_Metro_Device_Id >= EXT1) 
  {
    switch (in_Metro_Status_requested)
    {
      /* All events requested, send back the full u32 reg */
      case ALL_STATUS:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Status Mask  from RAM struct for EXT chip */
            Metro_Status_reg=(p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1);
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Status Mask from RAM struct for EXT chip */
            Metro_Status_reg=(p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2);
         }
      }
      break;
       /* now the other cases , are bit by bit inside DSPSR1 or 2 register for STPM chips */
      case STATUS_TAMPER_OR_WRONG:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Status Mask  from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1)&BIT_MASK_STPM_TAMPER_OR_WRONG)>>BIT_MASK_STPM_TAMPER_OR_WRONG_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Status Mask from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2)&BIT_MASK_STPM_TAMPER_OR_WRONG)>>BIT_MASK_STPM_TAMPER_OR_WRONG_SHIFT;
         }
      }
      break;
      case STATUS_TAMPER_DETECTED:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Status Mask  from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1)&BIT_MASK_STPM_TAMPER_DETECTED)>>BIT_MASK_STPM_TAMPER_DETECTED_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Status Mask from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2)&BIT_MASK_STPM_TAMPER_DETECTED)>>BIT_MASK_STPM_TAMPER_DETECTED_SHIFT;
         }
      }
      break;
      case STATUS_VOLTAGE_SWELL_DOWN:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Status Mask  from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1)&BIT_MASK_STPM_VOLT_SWELL_DOWN)>>BIT_MASK_STPM_VOLT_SWELL_DOWN_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Status Mask from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2)&BIT_MASK_STPM_VOLT_SWELL_DOWN)>>BIT_MASK_STPM_VOLT_SWELL_DOWN_SHIFT;
         }
      }
      break;
      case STATUS_VOLTAGE_SWELL_UP:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Status Mask  from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1)&BIT_MASK_STPM_VOLT_SWELL_UP)>>BIT_MASK_STPM_VOLT_SWELL_UP_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Status Mask from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2)&BIT_MASK_STPM_VOLT_SWELL_UP)>>BIT_MASK_STPM_VOLT_SWELL_UP_SHIFT;
         }
      }
      break;
      case STATUS_VOLTAGE_SAG_DOWN:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Status Mask  from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1)&BIT_MASK_STPM_VOLT_SAG_DOWN)>>BIT_MASK_STPM_VOLT_SAG_DOWN_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Status Mask from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2)&BIT_MASK_STPM_VOLT_SAG_DOWN)>>BIT_MASK_STPM_VOLT_SAG_DOWN_SHIFT;
         }
      }
      break;
      case STATUS_VOLTAGE_SAG_UP:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Status Mask  from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1)&BIT_MASK_STPM_VOLT_SAG_UP)>>BIT_MASK_STPM_VOLT_SAG_UP_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Status Mask from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2)&BIT_MASK_STPM_VOLT_SAG_UP)>>BIT_MASK_STPM_VOLT_SAG_UP_SHIFT;
         }
      }
      break;
      case STATUS_VOLTAGE_PERIOD_STATUS:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Status Mask  from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1)&BIT_MASK_STPM_VOLT_PERIOD_STATUS)>>BIT_MASK_STPM_VOLT_PERIOD_STATUS_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Status Mask from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2)&BIT_MASK_STPM_VOLT_PERIOD_STATUS)>>BIT_MASK_STPM_VOLT_PERIOD_STATUS_SHIFT;
         }
      }
      break;
      case STATUS_VOLTAGE_SIGNAL_STUCK:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Status Mask  from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1)&BIT_MASK_STPM_VOLT_SIG_STUCK)>>BIT_MASK_STPM_VOLT_SIG_STUCK_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Status Mask from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2)&BIT_MASK_STPM_VOLT_SIG_STUCK)>>BIT_MASK_STPM_VOLT_SIG_STUCK_SHIFT;
         }
      }
      break;
      case STATUS_CURRENT_SWELL_DOWN:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Status Mask  from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1)&BIT_MASK_STPM_CURR_SWELL_DOWN)>>BIT_MASK_STPM_CURR_SWELL_DOWN_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Status Mask from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2)&BIT_MASK_STPM_CURR_SWELL_DOWN)>>BIT_MASK_STPM_CURR_SWELL_DOWN_SHIFT;
         }
      }
      break;
      case STATUS_CURRENT_SWELL_UP:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Status Mask  from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1)&BIT_MASK_STPM_CURR_SWELL_UP)>>BIT_MASK_STPM_CURR_SWELL_UP_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Status Mask from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2)&BIT_MASK_STPM_CURR_SWELL_UP)>>BIT_MASK_STPM_CURR_SWELL_UP_SHIFT;
         }
      }
      break;
      case STATUS_CURRENT_NAH_TMP:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Status Mask  from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1)&BIT_MASK_STPM_CURR_NAH_TMP)>>BIT_MASK_STPM_CURR_NAH_TMP_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Status Mask from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2)&BIT_MASK_STPM_CURR_NAH_TMP)>>BIT_MASK_STPM_CURR_NAH_TMP_SHIFT;
         }
      }
      break;
      case STATUS_CURRENT_SIGNAL_STUCK:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Status Mask  from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1)&BIT_MASK_STPM_CURR_SIG_STUCK)>>BIT_MASK_STPM_CURR_SIG_STUCK_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Status Mask from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2)&BIT_MASK_STPM_CURR_SIG_STUCK)>>BIT_MASK_STPM_CURR_SIG_STUCK_SHIFT;
         }
      }
      break;
      case STATUS_CURRENT_OVERFLOW_APPARENT_NRJ:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Status Mask  from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1)&BIT_MASK_STPM_PH1_EO_S)>>BIT_MASK_STPM_PH1_EO_S_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Status Mask from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2)&BIT_MASK_STPM_PH2_EO_S)>>BIT_MASK_STPM_PH2_EO_S_SHIFT;
         }
      }
      break;
      case STATUS_CURRENT_OVERFLOW_REACTIVE_NRJ:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Status Mask  from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1)&BIT_MASK_STPM_PH1_EO_R)>>BIT_MASK_STPM_PH1_EO_R_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Status Mask from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2)&BIT_MASK_STPM_PH2_EO_R)>>BIT_MASK_STPM_PH2_EO_R_SHIFT;
         }
      }
      break;
      case STATUS_CURRENT_OVERFLOW_FUNDAMENTAL_NRJ:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Status Mask  from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1)&BIT_MASK_STPM_PH1_EO_F)>>BIT_MASK_STPM_PH1_EO_F_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Status Mask from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2)&BIT_MASK_STPM_PH2_EO_F)>>BIT_MASK_STPM_PH2_EO_F_SHIFT;
         }
      }
      break;
      case STATUS_CURRENT_OVERFLOW_ACTIVE_NRJ:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Status Mask  from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1)&BIT_MASK_STPM_PH1_EO_A)>>BIT_MASK_STPM_PH1_EO_A_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Status Mask from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2)&BIT_MASK_STPM_PH2_EO_A)>>BIT_MASK_STPM_PH2_EO_A_SHIFT;
         }
      }
      break;
      case STATUS_CURRENT_SIGN_APPARENT_POWER:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Status Mask  from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1)&BIT_MASK_STPM_PH1_PS_S)>>BIT_MASK_STPM_PH1_PS_S_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Status Mask from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2)&BIT_MASK_STPM_PH2_PS_S)>>BIT_MASK_STPM_PH2_PS_S_SHIFT;
         }
      }
      break;
      case STATUS_CURRENT_SIGN_CHANGE_REACTIVE_POWER:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Status Mask  from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1)&BIT_MASK_STPM_PH1_PS_R)>>BIT_MASK_STPM_PH1_PS_R_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Status Mask from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2)&BIT_MASK_STPM_PH2_PS_R)>>BIT_MASK_STPM_PH2_PS_R_SHIFT;
         }
      }
      break;
      case STATUS_CURRENT_SIGN_CHANGE_FUNDAMENTAL_POWER:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Status Mask  from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1)&BIT_MASK_STPM_PH1_PS_F)>>BIT_MASK_STPM_PH1_PS_F_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Status Mask from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2)&BIT_MASK_STPM_PH2_PS_F)>>BIT_MASK_STPM_PH2_PS_F_SHIFT;
         }
      }
      break;
      case STATUS_CURRENT_SIGN_CHANGE_ACTIVE_POWER:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Get Status Mask  from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1)&BIT_MASK_STPM_PH1_PS_A)>>BIT_MASK_STPM_PH1_PS_A_SHIFT;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Get Status Mask from RAM struct for EXT chip */
            Metro_Status_reg=((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2)&BIT_MASK_STPM_PH2_PS_A)>>BIT_MASK_STPM_PH2_PS_A_SHIFT;
         }
      }
      break;
   
    }
  }
  return Metro_Status_reg; 
}

/**
  * @brief       Clear  the specified status for a channel
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   in_Metro_int_Channel (Channel ID), Channel 1 or 2 ( according to device )
  * @param[in]   METRO_Status_Type_t type ( Status registers are generated by IRQ  )
  * @param[out]  None
  * @retval      None
  */
void Metro_HAL_Clear_Status_for_Channel(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel, METRO_Status_Type_t in_Metro_Status_requested)
{
   uint32_t tmp_addr =0;
  
  if(in_Metro_Device_Id >= EXT1) 
  {
    switch (in_Metro_Status_requested)
    {
      /* All events requested, send back the full u32 reg */
      case ALL_STATUS:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1 = 0 ;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2 = 0;
         }
      }
      break;
       /* now the other cases , are bit by bit inside DSPSR1 or 2 register for STPM chips */
      case STATUS_TAMPER_OR_WRONG:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1 &= ~BIT_MASK_STPM_TAMPER_OR_WRONG;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2 &= ~BIT_MASK_STPM_TAMPER_OR_WRONG;
         }
      }
      break;
      case STATUS_TAMPER_DETECTED:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1 &= ~BIT_MASK_STPM_TAMPER_DETECTED;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2 &= ~BIT_MASK_STPM_TAMPER_DETECTED;
         }
      }
      break;
      case STATUS_VOLTAGE_SWELL_DOWN:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1 &= ~BIT_MASK_STPM_VOLT_SWELL_DOWN;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2 &= ~BIT_MASK_STPM_VOLT_SWELL_DOWN;
         }
      }
      break;
      case STATUS_VOLTAGE_SWELL_UP:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1 &= ~BIT_MASK_STPM_VOLT_SWELL_UP;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2 &= ~BIT_MASK_STPM_VOLT_SWELL_UP;
         }
      }
      break;
      case STATUS_VOLTAGE_SAG_DOWN:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1 &= ~BIT_MASK_STPM_VOLT_SAG_DOWN;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2 &= ~BIT_MASK_STPM_VOLT_SAG_DOWN;
         }
      }
      break;
      case STATUS_VOLTAGE_SAG_UP:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1 &= ~BIT_MASK_STPM_VOLT_SAG_UP;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2 &= ~BIT_MASK_STPM_VOLT_SAG_UP;
         }
      }
      break;
      case STATUS_VOLTAGE_PERIOD_STATUS:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1 &= ~BIT_MASK_STPM_VOLT_PERIOD_STATUS;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2 &= ~BIT_MASK_STPM_VOLT_PERIOD_STATUS;
         }
      }
      break;
      case STATUS_VOLTAGE_SIGNAL_STUCK:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1 &= ~BIT_MASK_STPM_VOLT_SIG_STUCK;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2 &= ~BIT_MASK_STPM_VOLT_SIG_STUCK;
         }
      }
      break;
      case STATUS_CURRENT_SWELL_DOWN:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1 &= ~BIT_MASK_STPM_CURR_SWELL_DOWN;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2 &= ~BIT_MASK_STPM_CURR_SWELL_DOWN;
         }
      }
      break;
      case STATUS_CURRENT_SWELL_UP:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1 &= ~BIT_MASK_STPM_CURR_SWELL_UP;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2 &= ~BIT_MASK_STPM_CURR_SWELL_UP;
         }
      }
      break;
      case STATUS_CURRENT_NAH_TMP:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1 &= ~BIT_MASK_STPM_CURR_NAH_TMP;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2 &= ~BIT_MASK_STPM_CURR_NAH_TMP;
         }
      }
      break;
      case STATUS_CURRENT_SIGNAL_STUCK:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1 &= ~BIT_MASK_STPM_CURR_SIG_STUCK;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2 &= ~BIT_MASK_STPM_CURR_SIG_STUCK;
         }
      }
      break;
      case STATUS_CURRENT_OVERFLOW_APPARENT_NRJ:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1 &= ~BIT_MASK_STPM_PH1_EO_S;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2 &= ~BIT_MASK_STPM_PH2_EO_S;
         }
      }
      break;
      case STATUS_CURRENT_OVERFLOW_REACTIVE_NRJ:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1 &= ~BIT_MASK_STPM_PH1_EO_R;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2 &= ~BIT_MASK_STPM_PH2_EO_R;
         }
      }
      break;
      case STATUS_CURRENT_OVERFLOW_FUNDAMENTAL_NRJ:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1 &= ~BIT_MASK_STPM_PH1_EO_F;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2 &= ~BIT_MASK_STPM_PH2_EO_F;
         }
      }
      break;
      case STATUS_CURRENT_OVERFLOW_ACTIVE_NRJ:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1 &= ~BIT_MASK_STPM_PH1_EO_A;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2 &= ~BIT_MASK_STPM_PH2_EO_A;
         }
      }
      break;
      case STATUS_CURRENT_SIGN_APPARENT_POWER:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1 &= ~BIT_MASK_STPM_PH1_PS_S;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2 &= ~BIT_MASK_STPM_PH2_PS_S;
         }
      }
      break;
      case STATUS_CURRENT_SIGN_CHANGE_REACTIVE_POWER:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1 &= ~BIT_MASK_STPM_PH1_PS_R;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2 &= ~BIT_MASK_STPM_PH2_PS_R;
         }
      }
      break;
      case STATUS_CURRENT_SIGN_CHANGE_FUNDAMENTAL_POWER:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1 &= ~BIT_MASK_STPM_PH1_PS_F;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2 &= ~BIT_MASK_STPM_PH2_PS_F;
         }
      }
      break;
      case STATUS_CURRENT_SIGN_CHANGE_ACTIVE_POWER:
      {
         if ( in_Metro_int_Channel == INT_CHANNEL_1)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1 &= ~BIT_MASK_STPM_PH1_PS_A;
         }
         else  if( in_Metro_int_Channel == INT_CHANNEL_2)
         {      
            /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR2 &= ~BIT_MASK_STPM_PH2_PS_A;
         }
      }
      break;
    }
    
    /* Now send data to the external chip */
    /* the address should be provided in 2 bytes format (16 bits by 16 bits) for STPM */
    tmp_addr = STPM_DSPSR1;
     
    /* Now Write the 1 U32 register inside external chip  for DSPCR4  */
    Metro_HAL_Stpm_write(in_Metro_Device_Id,(uint8_t*)&tmp_addr,2,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPSR1,STPM_WAIT);

  }
}

/*************************************************************************************************/
/* IRQ and Status for STPM only ( IRQ and status for UART/SPI link between Host and STPM chips) */
/***************************************************************************************************/

/*

Register US_REG3  Bit position Description 

Status bits
----------------
30 SPI RX overrun 0 RW
29 SPI TX underrun 0 RW
28 SPI CRC error 0 RW
27 UART/SPI write address error 0 RW
26 UART/SPI read address error 0 RW
25 SPI TX empty 0 RO
24 SPI RX full 0 RO
22 UART TX overrun 0 RW
21 UART RX overrun 0 RW
20 UART noise error 0 RW
19 UART frame error 0 RW
18 UART timeout error 0 RW
17 UART CRC error 0 RW
16 UART break 0 RW
IRQ CR Bits
-----------
14 mask for SPI RX overrun error status bit 0 RW
13 mask for SPI TX underrun error status bit 0 RW
12 mask for SPI CRC error status bit 0 RW
11 mask for write address error status bit 0 RW
10 mask for read address error status bit 0 RW
6 mask for UART TX overrun 0 RW
5 mask for UART RX overrun 0 RW
4 mask for UART noise error 0 RW
3 mask for UART frame error 0 RW
2 mask for UART timeout error 0 RW
1 mask for UART CRC error 0 RW

*/


/**
  * @brief       Set IRQ Mask for a Ext device
  * @param[in]   METRO_NB_Device_t in_Metro_Device_Id : EXT1 to EXT4 ( HOST forbidden )
  * @param[in]   in_Metro_IT_Mask :  Mask of interruption according to the device
  * @param[out]  None
  * @retval      None
  */
void Metro_HAL_Set_IRQ_Mask_for_STPM_device( METRO_NB_Device_t in_Metro_Device_Id, uint16_t in_Metro_IT_Mask)
{
  uint32_t tmp_addr =0; 
   
  if(in_Metro_Device_Id >= EXT1) 
  {
      /* Set new IRQ Mask for US_REG3 to RAM struct for EXT chip */
      (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR) = in_Metro_IT_Mask&BIT_MASK_STPM_IRQ_LINK;

      /* Now send data to the external chip */
      /* the address should be provided in 2 bytes format (16 bits by 16 bits) for STPM */
      tmp_addr = STPM_USREG3;
     
      /* Now Write the 1 U32 register inside external chip  for UARTSPISR */
      Metro_HAL_Stpm_write(in_Metro_Device_Id,(uint8_t*)&tmp_addr,1,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR,STPM_WAIT);
  }
}

/**
  * @brief       Get IRQ Mask for a Ext Device
  * @param[in]   METRO_NB_Device_t in_Metro_Device_Id : EXT1 to EXT4 ( HOST forbidden )
  * @param[out]  None
  * @retval     u16 Metro_IT_Mask
  */
uint16_t Metro_HAL_Get_IRQ_Mask_from_STPM_device( METRO_NB_Device_t in_Metro_Device_Id)
{
  
 uint16_t Metro_IT_Mask =0;
    
  if(in_Metro_Device_Id >= EXT1) 
  {
    /* Get IRQ Mask for UARTSPISR from RAM struct for EXT chip */
    Metro_IT_Mask=(uint16_t)(p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR)&BIT_MASK_STPM_IRQ_LINK;
  }

  return Metro_IT_Mask;
  
}

/**
  * @brief       Get the specified IRQ Link  status for STPM device
  * @param[in]   METRO_NB_Device_t in_Metro_Device_Id : EXT1 to EXT4 ( HOST forbidden )
  * @param[in]   METRO_STPM_LINK_IRQ_Status_Type_t type ( Status registers are generated by IRQ  )
  * @param[out]  None
  * @retval     u16 : Full Status  Register  if in_Metro_Status_requested == ALL_STATUS
  *             otherwise : 0 if Status requested (IRQ) is NOT occured,  1 if Status requested IRQ occured
  */
uint16_t Metro_HAL_Read_Status_from_STPM_device(METRO_NB_Device_t in_Metro_Device_Id, METRO_STPM_LINK_IRQ_Status_Type_t in_Metro_Status_requested)
{
 uint16_t Metro_Status_reg =0;
 
  if(in_Metro_Device_Id >= EXT1) 
  {
    switch (in_Metro_Status_requested)
    {
      /* All events requested, send back the full u16  ( bit 31 to 16 of UARTSPISR)  */
      case ALL_STATUS:
      {
        /* Get STPM link Status Mask  from RAM struct for EXT chip */
        Metro_Status_reg=(uint16_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR)&BIT_MASK_STPM_SR_LINK)>>16);
      }
      break;
      
       /* now the other cases , are bit by bit inside UARTSPISR ( bits 16 to 31) for STPM chips */
      case STATUS_STPM_UART_LINK_BREAK:
      {
        /* Get Status Mask bit from RAM struct for EXT chip */
        Metro_Status_reg=(uint16_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR)&BIT_MASK_STPM_UART_SR_BREAK)>>BIT_MASK_STPM_UART_SR_BREAK_SHIFT);
      }
      break;
      case STATUS_STPM_UART_LINK_CRC_ERROR:
      {
        /* Get Status Mask bit from RAM struct for EXT chip */
        Metro_Status_reg=(uint16_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR)&BIT_MASK_STPM_UART_SR_CRC_ERROR)>>BIT_MASK_STPM_UART_SR_CRC_ERROR_SHIFT);
      }
      break;
      case STATUS_STPM_UART_LINK_TIME_OUT_ERROR:
      {
        /* Get Status Mask bit from RAM struct for EXT chip */
        Metro_Status_reg=(uint16_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR)&BIT_MASK_STPM_UART_SR_TIMEOUT_ERROR)>>BIT_MASK_STPM_UART_SR_TIMEOUT_ERROR_SHIFT);
      }
      break;
      case STATUS_STPM_UART_LINK_FRAME_ERROR:
      {
        /* Get Status Mask bit from RAM struct for EXT chip */
        Metro_Status_reg=(uint16_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR)&BIT_MASK_STPM_UART_SR_FRAMING_ERROR)>>BIT_MASK_STPM_UART_SR_FRAMING_ERROR_SHIFT);
      }
      break;
      case STATUS_STPM_UART_LINK_NOISE_ERROR:
      {
        /* Get Status Mask bit from RAM struct for EXT chip */
        Metro_Status_reg=(uint16_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR)&BIT_MASK_STPM_UART_SR_NOISE_ERROR)>>BIT_MASK_STPM_UART_SR_NOISE_ERROR_SHIFT);
      }
      break;
      case STATUS_STPM_UART_LINK_RX_OVERRUN:
      {
        /* Get Status Mask bit from RAM struct for EXT chip */
        Metro_Status_reg=(uint16_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR)&BIT_MASK_STPM_UART_SR_RX_OVERRUN)>>BIT_MASK_STPM_UART_SR_RX_OVERRUN_SHIFT);
      }
      break;
      case STATUS_STPM_UART_LINK_TX_OVERRUN:
      {
        /* Get Status Mask bit from RAM struct for EXT chip */
        Metro_Status_reg=(uint16_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR)&BIT_MASK_STPM_UART_SR_TX_OVERRUN)>>BIT_MASK_STPM_UART_SR_TX_OVERRUN_SHIFT);
      }
      break;
      case STATUS_STPM_SPI_LINK_RX_FULL:
      {
        /* Get Status Mask bit from RAM struct for EXT chip */
        Metro_Status_reg=(uint16_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR)&BIT_MASK_STPM_SPI_SR_RX_FULL)>>BIT_MASK_STPM_SPI_SR_RX_FULL_SHIFT);
      }
      break;
      case STATUS_STPM_SPI_LINK_TX_EMPTY:
      {
        /* Get Status Mask bit from RAM struct for EXT chip */
        Metro_Status_reg=(uint16_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR)&BIT_MASK_STPM_SPI_SR_TX_EMPTY)>>BIT_MASK_STPM_SPI_SR_TX_EMPTY_SHIFT);
      }
      break;
      case STATUS_STPM_LINK_READ_ERROR:
      {
        /* Get Status Mask bit from RAM struct for EXT chip */
        Metro_Status_reg=(uint16_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR)&BIT_MASK_STPM_UARTSPI_SR_READ_ERROR)>>BIT_MASK_STPM_UARTSPI_SR_READ_ERROR_SHIFT);
      }
      break;
      case STATUS_STPM_LINK_WRITE_ERROR:
      {
        /* Get Status Mask bit from RAM struct for EXT chip */
        Metro_Status_reg=(uint16_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR)&BIT_MASK_STPM_UARTSPI_SR_WRITE_ERROR)>>BIT_MASK_STPM_UARTSPI_SR_WRITE_ERROR_SHIFT);
      }
      break;
      case STATUS_STPM_SPI_LINK_CRC_ERROR:
      {
        /* Get Status Mask bit from RAM struct for EXT chip */
        Metro_Status_reg=(uint16_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR)&BIT_MASK_STPM_SPI_SR_CRC_ERROR)>>BIT_MASK_STPM_SPI_SR_CRC_ERROR_SHIFT);
      }
      break;
      case STATUS_STPM_SPI_LINK_UNDERRUN:
      {
        /* Get Status Mask bit from RAM struct for EXT chip */
        Metro_Status_reg=(uint16_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR)&BIT_MASK_STPM_SPI_SR_TX_UNDERRUN)>>BIT_MASK_STPM_SPI_SR_TX_UNDERRUN_SHIFT);
      }
      break;
      case STATUS_STPM_SPI_LINK_OVERRRUN:
      {
        /* Get Status Mask bit from RAM struct for EXT chip */
        Metro_Status_reg=(uint16_t)(((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR)&BIT_MASK_STPM_SPI_SR_RX_OVERRUN)>>BIT_MASK_STPM_SPI_SR_RX_OVERRUN_SHIFT);
      }
      break;
    }    
  }
  return Metro_Status_reg; 
}

/**
  * @brief       Clear the specified IRQ status for a channel
  * @param[in]   METRO_NB_Device_t in_Metro_Device_Id : EXT1 to EXT4 ( HOST forbidden )
  * @param[in]   METRO_STPM_LINK_IRQ_Status_Type_t type ( Status registers are generated by IRQ  )
  * @param[out]  None
  * @retval      None
  */
void Metro_HAL_Clear_Status_for_STPM_device(METRO_NB_Device_t in_Metro_Device_Id, METRO_STPM_LINK_IRQ_Status_Type_t in_Metro_Status_requested)
{

  uint32_t tmp_addr =0;
   
  if(in_Metro_Device_Id >= EXT1) 
  {
    switch (in_Metro_Status_requested)
    {
      /* All events requested, send back the full u32 reg */
      case ALL_STATUS:
      {
            /* Clear  full Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR &= ~BIT_MASK_STPM_SR_LINK;
      }
      break;
       /* now the other cases , are bit by bit inside UARTSPISR for STPM chips */
      case STATUS_STPM_UART_LINK_BREAK:
      {
        /* Clear  Status Mask  inside RAM struct for EXT chip */
        p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR &= ~BIT_MASK_STPM_UART_SR_BREAK;
      }
      break;
      case STATUS_STPM_UART_LINK_CRC_ERROR:
      {
        /* Clear  Status Mask  inside RAM struct for EXT chip */
        p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR &= ~BIT_MASK_STPM_UART_SR_CRC_ERROR;
      }
      break;
      case STATUS_STPM_UART_LINK_TIME_OUT_ERROR:
      {
           /* Clear  Status Mask  inside RAM struct for EXT chip */
            p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR &= ~BIT_MASK_STPM_UART_SR_TIMEOUT_ERROR;
      }
      break;
      case STATUS_STPM_UART_LINK_FRAME_ERROR:
      {
        /* Clear  Status Mask  inside RAM struct for EXT chip */
        p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR &= ~BIT_MASK_STPM_UART_SR_FRAMING_ERROR;
      }
      break;
      case STATUS_STPM_UART_LINK_NOISE_ERROR:
      {
        /* Clear  Status Mask  inside RAM struct for EXT chip */
        p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR &= ~BIT_MASK_STPM_UART_SR_NOISE_ERROR;
      }
      break;
      case STATUS_STPM_UART_LINK_RX_OVERRUN:
      {
        /* Clear  Status Mask  inside RAM struct for EXT chip */
        p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR &= ~BIT_MASK_STPM_UART_SR_RX_OVERRUN;
      }
      break;
      case STATUS_STPM_UART_LINK_TX_OVERRUN:
      {
        /* Clear  Status Mask  inside RAM struct for EXT chip */
        p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR &= ~BIT_MASK_STPM_UART_SR_TX_OVERRUN;
      }
      break;
      case STATUS_STPM_SPI_LINK_RX_FULL:
      {
        /* Clear  Status Mask  inside RAM struct for EXT chip */
        p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR &= ~BIT_MASK_STPM_SPI_SR_RX_FULL;
      }
      break;
      case STATUS_STPM_SPI_LINK_TX_EMPTY:
      {
        /* Clear  Status Mask  inside RAM struct for EXT chip */
        p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR &= ~BIT_MASK_STPM_SPI_SR_TX_EMPTY;
      }
      break;
      case STATUS_STPM_LINK_READ_ERROR:
      {
        /* Clear  Status Mask  inside RAM struct for EXT chip */
        p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR &= ~BIT_MASK_STPM_UARTSPI_SR_READ_ERROR;
      }
      break;
      case STATUS_STPM_LINK_WRITE_ERROR:
      {
        /* Clear  Status Mask  inside RAM struct for EXT chip */
        p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR &= ~BIT_MASK_STPM_UARTSPI_SR_WRITE_ERROR;
      }
      break;
      case STATUS_STPM_SPI_LINK_CRC_ERROR:
      {
        /* Clear  Status Mask  inside RAM struct for EXT chip */
        p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR &= ~BIT_MASK_STPM_SPI_SR_CRC_ERROR;
      }
      break;
      case STATUS_STPM_SPI_LINK_UNDERRUN:
      {
        /* Clear  Status Mask  inside RAM struct for EXT chip */
        p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR &= ~BIT_MASK_STPM_SPI_SR_TX_UNDERRUN;
      }
      break;
      case STATUS_STPM_SPI_LINK_OVERRRUN:
      {
        /* Clear  Status Mask  inside RAM struct for EXT chip */
        p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR &= ~BIT_MASK_STPM_SPI_SR_RX_OVERRUN;
      }
      break;
    }
    
    /* Now send data to the external chip */
    /* the address should be provided in 2 bytes format (16 bits by 16 bits) for STPM */
    tmp_addr = STPM_USREG3;
     
    /* Now Write the 1 U32 register inside external chip  for UARTSPISR */
     Metro_HAL_Stpm_write(in_Metro_Device_Id,(uint8_t*)&tmp_addr,1,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPISR,STPM_WAIT);

  }
   
}

/**
  * @brief       Set the thresholds and the time to detect the sag event for each channel ( Voltage )
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   in_Metro_int_Channel (Channel ID), Channel 1 or 2 ( according to device )
  * @param[in]   u16 in_Metro_SAG_Threshold (Register value) ( under 10 bits)
  * @param[in]   u16 in_Metro_SAG_detect_time (Register value in 8µs LSB) (under 14 bits)
  * @param[out]  None
  * @retval      None
  */
void Metro_HAL_Set_SAG_Config(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel,uint16_t in_Metro_SAG_Threshold,uint16_t in_Metro_SAG_detect_time)
{
    
  if(in_Metro_Device_Id >= EXT1) 
  {
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    {
      /* Test if Threshold and Time are not null, change values inside Metro block */
      if ( in_Metro_SAG_Threshold != 0) 
      {
        /* Reset  SAG value bits for Channel 1*/
        (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL5) &= ~ BIT_MASK_STPM_SAGVALUE_V1; 
          
         /* Set new Sag value for channel 1 */
         (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL5) |= (((uint32_t)(in_Metro_SAG_Threshold)<<BIT_MASK_STPM_SAGVALUE_V1_SHIFT)& BIT_MASK_STPM_SAGVALUE_V1);
       }
       /* Time value is the same for all channels , so set it only inside channel one when requested */
       if (in_Metro_SAG_detect_time != 0)
       {
          /* Clear Old Time value inside register   */
          p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3 &= ~ BIT_MASK_STPM_TIME_VALUE;

          /* Set new Time value (14 bits)   */
          p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3 |= ((uint32_t)(in_Metro_SAG_detect_time)&BIT_MASK_STPM_TIME_VALUE);
             
       }
       /* All input values are Null so disable the SAG mechanism inside Metro block */
       if (( in_Metro_SAG_Threshold == 0)&&(in_Metro_SAG_detect_time == 0))
       {
         /* Set ClearSS Bit to disable the SAG  (STPM) */
         (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1) |= BIT_MASK_STPM_CLEAR_SAG_SWELL;
       }
     }
       
     else  if(( in_Metro_int_Channel == INT_CHANNEL_2) || (in_Metro_int_Channel == CHANNEL_TAMPER))
     {    
       /* Test if Threshold is not null, change values inside Metro block */
       if ( in_Metro_SAG_Threshold != 0)
       {       
         /* Reset  SAG value bits for Channel 2  */
         (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL7) &= ~ BIT_MASK_STPM_SAGVALUE_V2; 
        
         /* Set new Sag value Channel 2*/
         (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL7) |= (((uint32_t)(in_Metro_SAG_Threshold)<<BIT_MASK_STPM_SAGVALUE_V2_SHIFT)& BIT_MASK_STPM_SAGVALUE_V2);
       }
       /* if all input values are Null so disable the SAG mechanism inside Metro block */   
       else if (( in_Metro_SAG_Threshold == 0) && (in_Metro_SAG_detect_time == 0)) 
       {
         /* Set ClearSS Bit to disable the SAG  (STPM) */
         (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL2) |= BIT_MASK_STPM_CLEAR_SAG_SWELL;
       }    
     }
       
     /* Now Write the 7 U32 register inside external chip  for DSPCR1 to 7  */
     Metro_HAL_Stpm_write(in_Metro_Device_Id,STPM_DSPCTRL1,7,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1,STPM_WAIT);
  }
}

/**
  * @brief       Set voltage swell threshold for each voltage channel
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   in_Metro_int_Channel (Channel ID), Channel 1 or 2 ( according to device )
  * @param[in]   u16 in_Metro_V_SWELL_Threshold
  * @param[out]  None
  * @retval      None
  */
void Metro_HAL_Set_V_SWELL_Config(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel,uint16_t in_Metro_V_SWELL_Threshold)
{
    
  if(in_Metro_Device_Id >= EXT1) 
  {
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    {
      /* Test if Threshold is null, change values inside Metro block */
      if ( in_Metro_V_SWELL_Threshold != 0)
      {
         /* Reset  Swell value bits for Channel 1*/
         (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL5) &= ~ BIT_MASK_STPM_SWELL_VALUE_V1; 
          
         /* Set new Swell value for channel 1 */
         (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL5) |= (((uint32_t)(in_Metro_V_SWELL_Threshold)<<BIT_MASK_STPM_SWELL_VALUE_V1_SHIFT)& BIT_MASK_STPM_SWELL_VALUE_V1);
                    
      }
      /* some input values are Null so disable the SAG mechanism inside Metro block */
      else
      {
        /* Set ClearSS Bit to disable the SAG  (STPM) */
         (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1) |= BIT_MASK_STPM_CLEAR_SAG_SWELL;
      }
    }
    else  if(( in_Metro_int_Channel == INT_CHANNEL_2) || (in_Metro_int_Channel == CHANNEL_TAMPER))
    {
      /* Test if Threshold is not null, change values inside Metro block */
      if (in_Metro_V_SWELL_Threshold != 0)
      {       
        /* Reset  Swell value bits for Channel 2  */
        (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL7) &= ~ BIT_MASK_STPM_SWELL_VALUE_V2; 
        
        /* Set new Swell value Channel 2*/
        (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL7) |= (((uint32_t)(in_Metro_V_SWELL_Threshold)<<BIT_MASK_STPM_SWELL_VALUE_V2_SHIFT)& BIT_MASK_STPM_SWELL_VALUE_V2);
      }
      /* some input values are Null so disable the SAG mechanism inside Metro block */   
      else
      {
        /* Set ClearSS Bit to disable the Swell  (STPM) */
        (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL2) |= BIT_MASK_STPM_CLEAR_SAG_SWELL;
      }    
    }
       
     /* Now Write the 7 U32 register inside external chip  for DSPCR1 to 7  */
     Metro_HAL_Stpm_write(in_Metro_Device_Id,STPM_DSPCTRL1,7,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1,STPM_WAIT);

  }
}
/**
  * @brief       Set Current swell threshold for each current channel
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   in_Metro_int_Channel (Channel ID), Channel 1 or 2 ( according to device )
  * @param[in]   u16 in_Metro_C_SWELL_Threshold
  * @param[out]  None
  * @retval      None
  */
void Metro_HAL_Set_C_SWELL_Config(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel,uint16_t in_Metro_C_SWELL_Threshold) 
{
    
  if(in_Metro_Device_Id >= EXT1) 
  {
     if ( in_Metro_int_Channel == INT_CHANNEL_1)
     {
       /* Test if Threshold is null, change values inside Metro block */
       if ( in_Metro_C_SWELL_Threshold != 0)
       {
          /* Reset  Swell value bits for Channel 1*/
          (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL6) &= ~ BIT_MASK_STPM_SWELL_VALUE_C1; 
        
          /* Set new Swell value for channel 1 */
          (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL6) |= (((uint32_t)(in_Metro_C_SWELL_Threshold)<<BIT_MASK_STPM_SWELL_VALUE_C1_SHIFT)& BIT_MASK_STPM_SWELL_VALUE_C1);
                  
       }
       /* some input values are Null so disable the SAG mechanism inside Metro block */
       else
       {
         /* Set ClearSS Bit to disable the SAG  (STPM) */
          (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1) |= BIT_MASK_STPM_CLEAR_SAG_SWELL;
       }
     }
     
     else  if(( in_Metro_int_Channel == INT_CHANNEL_2) || (in_Metro_int_Channel == CHANNEL_TAMPER))
     {
       
       /* Test if Threshold is not null, change values inside Metro block */
       if (in_Metro_C_SWELL_Threshold != 0)
       {       
         /* Reset  Swell value bits for Channel 2  */
        (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL8) &= ~ BIT_MASK_STPM_SWELL_VALUE_C2; 
      
        /* Set new Swell value Channel 2*/
        (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL8) |= (((uint32_t)(in_Metro_C_SWELL_Threshold)<<BIT_MASK_STPM_SWELL_VALUE_C2_SHIFT)& BIT_MASK_STPM_SWELL_VALUE_C2);
       }
       /* some input values are Null so disable the SAG mechanism inside Metro block */   
       else
       {
         /* Set ClearSS Bit to disable the Swell  (STPM) */
          (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL2) |= BIT_MASK_STPM_CLEAR_SAG_SWELL;
       }    
     }
     
      /* Now Write the 8 U32 register inside external chip  for DSPCR1 to 8  */
      Metro_HAL_Stpm_write(in_Metro_Device_Id,STPM_DSPCTRL1,8,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1,STPM_WAIT);
  }
}

/**
  * @brief       Set the thresholds and the time to detect the sag event for each channel ( Voltage )
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   in_Metro_int_Channel (Channel ID), Channel 1 or 2 ( according to device )
  * @param[out]   u16 * out_p_Metro_SAG_Threshold (Register value) ( under 10 bits)
  * @param[out]   u16 * out_p_Metro_SAG_detect_time (Register value in 8µs LSB) (under 14 bits)
  * @param[out]  None
  * @retval      None
  */
void Metro_HAL_Get_SAG_Config(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel,uint16_t * out_p_Metro_SAG_Threshold,uint16_t * out_p_Metro_SAG_detect_time)
{
    
  if(in_Metro_Device_Id >= EXT1) 
  {
      /* Get Time value (14 bits) valid for both channels  */
      *out_p_Metro_SAG_detect_time = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL3)&BIT_MASK_STPM_TIME_VALUE);  
      
     if ( in_Metro_int_Channel == INT_CHANNEL_1)
     {
        
      /* Get Sag value for channel 1 */
      *out_p_Metro_SAG_Threshold = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL5)&BIT_MASK_STPM_SAGVALUE_V1)>> BIT_MASK_STPM_SAGVALUE_V1_SHIFT;
           
     }
     else  if(( in_Metro_int_Channel == INT_CHANNEL_2) || (in_Metro_int_Channel == CHANNEL_TAMPER))
     {     
      /* Get Sag value Channel 2*/
      *out_p_Metro_SAG_Threshold = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL7)&BIT_MASK_STPM_SAGVALUE_V2)>> BIT_MASK_STPM_SAGVALUE_V2_SHIFT;
     }
  }
}

/**
  * @brief       Get voltage swell threshold for each voltage channel
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   in_Metro_int_Channel (Channel ID), Channel 1 or 2 ( according to device )
  * @param[out]  None
  * @retval      u16 Metro_V_SWELL_Threshold
  */
uint16_t  Metro_HAL_Get_V_SWELL_Config(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel)
{
  uint16_t Metro_V_SWELL_Threshold = 0;
  
  if(in_Metro_Device_Id >= EXT1) 
  {
     if ( in_Metro_int_Channel == INT_CHANNEL_1)
     {
        /* Get Swell value for channel 1 */
        Metro_V_SWELL_Threshold = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL5)& BIT_MASK_STPM_SWELL_VALUE_V1)>> BIT_MASK_STPM_SWELL_VALUE_V1_SHIFT;           
     }   
     else  if(( in_Metro_int_Channel == INT_CHANNEL_2) || (in_Metro_int_Channel == CHANNEL_TAMPER))
     {    
      /* Get  Swell value Channel 2*/
      Metro_V_SWELL_Threshold = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL7)& BIT_MASK_STPM_SWELL_VALUE_V2)>> BIT_MASK_STPM_SWELL_VALUE_V2_SHIFT;
     }
  }
  return Metro_V_SWELL_Threshold;
}
/**
  * @brief       Get Current swell threshold for each current channel
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   in_Metro_int_Channel (Channel ID), Channel 1 or 2 ( according to device )
  * @param[out]  None
  * @retval      u16 Metro_C_SWELL_Threshold
  */
uint16_t Metro_HAL_Get_C_SWELL_Config(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel) 
{
  uint16_t Metro_C_SWELL_Threshold = 0;
    
  if(in_Metro_Device_Id >= EXT1) 
  {
     if ( in_Metro_int_Channel == INT_CHANNEL_1)
     {  
        /* Get  Swell value for channel 1 */
        Metro_C_SWELL_Threshold = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL6) & BIT_MASK_STPM_SWELL_VALUE_C1)>> BIT_MASK_STPM_SWELL_VALUE_C1_SHIFT;   
     }  
     else  if(( in_Metro_int_Channel == INT_CHANNEL_2) || (in_Metro_int_Channel == CHANNEL_TAMPER))
     {
      
        /* Get  Swell value for channel 2 */
        Metro_C_SWELL_Threshold = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL8) & BIT_MASK_STPM_SWELL_VALUE_C2)>> BIT_MASK_STPM_SWELL_VALUE_C2_SHIFT;   
     }
  }
  return Metro_C_SWELL_Threshold;
}

/**
  * @brief       Get  SAG time counter for each Voltage channel
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   in_Metro_int_Channel (Channel ID), Channel 1 or 2 ( according to device )
  * @param[out]  None
  * @retval      u16 Metro_V_SAG_Time
  */
uint16_t Metro_HAL_Read_SAG_Time(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel)
{
  uint16_t Metro_V_SAG_Time = 0;
    
  if(in_Metro_Device_Id >= EXT1) 
  {
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    {  
       /* Get  SAG time value for channel 1 */
       Metro_V_SAG_Time = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSP_REG16) & BIT_MASK_STPM_SAG_TIME_V1)>> BIT_MASK_STPM_SAG_TIME_V1_SHIFT;   
    }  
    else  if(( in_Metro_int_Channel == INT_CHANNEL_2) || (in_Metro_int_Channel == CHANNEL_TAMPER))
    {     
       /* Get  SAG time value for channel 2 */
       Metro_V_SAG_Time = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSP_REG18) & BIT_MASK_STPM_SAG_TIME_V2)>> BIT_MASK_STPM_SAG_TIME_V2_SHIFT;   
    }
  }
  return Metro_V_SAG_Time;
}

/**
  * @brief       Get  swell time counter for each Current channel
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   in_Metro_int_Channel (Channel ID), Channel 1 or 2 ( according to device )
  * @param[out]  None
  * @retval      u16 Metro_C_SWELL_Time
  */
uint16_t Metro_HAL_Read_C_SWELL_Time(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel)
{
  uint16_t Metro_C_SWELL_Time = 0;
    
  if(in_Metro_Device_Id >= EXT1) 
  {
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    {  
       /* Get  Swell time value for channel 1 */
       Metro_C_SWELL_Time = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSP_REG17) & BIT_MASK_STPM_SWELL_TIME_C1);   
    }  
    else  if(( in_Metro_int_Channel == INT_CHANNEL_2) || (in_Metro_int_Channel == CHANNEL_TAMPER))
    {     
       /* Get  Swell time value for channel 2 */
       Metro_C_SWELL_Time = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSP_REG19) & BIT_MASK_STPM_SWELL_TIME_C2);   
    }
  }
  return Metro_C_SWELL_Time;
}

/**
  * @brief       Get  swell time counter for each voltage channel
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   in_Metro_int_Channel (Channel ID), Channel 1 or 2 ( according to device )
  * @param[out]  None
  * @retval      u16 Metro_V_SWELL_time
  */
uint16_t  Metro_HAL_Read_V_SWELL_Time(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel)
{
  uint16_t Metro_V_SWELL_time = 0;
    
  if(in_Metro_Device_Id >= EXT1) 
  {
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    {  
       /* Get  Swell time value for channel 1 */
       Metro_V_SWELL_time = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSP_REG16) & BIT_MASK_STPM_SWELL_TIME_V1);   
    }  
    else  if(( in_Metro_int_Channel == INT_CHANNEL_2) || (in_Metro_int_Channel == CHANNEL_TAMPER))
    {
       /* Get  Swell time value for channel 2 */
       Metro_V_SWELL_time = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSP_REG18) & BIT_MASK_STPM_SWELL_TIME_V2);   
    }
  }
  return Metro_V_SWELL_time;  
}

/**
  * @brief       Set  Sag and swell Clear time out from channel
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   in_Metro_int_Channel (Channel ID), Channel 1 or 2 ( according to device )
  * @param[in]   u8 in_Metro_Sag_and_Swell_Clear_Timeout
  * @param[out]  None
  * @retval      None
  */
void Metro_HAL_Set_SAG_and_SWELL_Clear_Timeout(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel,uint8_t in_Metro_Sag_and_Swell_Clear_Timeout)
{
  
  if(in_Metro_Device_Id >= EXT1) 
  {
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    {        
       /* Reset Old value */
       p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1 &= ~ BIT_MASK_STPM_CLR_SS_TIME_OUT;
         
       /* Set  Clear Time Out for channel 1 */
       p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1 |= (in_Metro_Sag_and_Swell_Clear_Timeout & BIT_MASK_STPM_CLR_SS_TIME_OUT);   
    }  
    else  if(( in_Metro_int_Channel == INT_CHANNEL_2) || (in_Metro_int_Channel == CHANNEL_TAMPER))
    {
       /* Reset Old value */
       p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL2 &= ~ BIT_MASK_STPM_CLR_SS_TIME_OUT;
        
       /* Set  Clear Time Out for channel 2 */
       p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL2 |= (in_Metro_Sag_and_Swell_Clear_Timeout & BIT_MASK_STPM_CLR_SS_TIME_OUT);  
    }
       
       
     /* Now Write the 2 U32 register inside external chip  for DSPCR1 and 2  */
     Metro_HAL_Stpm_write(in_Metro_Device_Id,STPM_DSPCTRL1,2,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1,STPM_WAIT);
  }
}

/**
  * @brief       Get  Sag and swell Clear time out from channel
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   in_Metro_int_Channel (Channel ID), Channel 1 or 2 ( according to device )
  * @param[out]  None
  * @retval      u8 Metro_Clear_TimeOut
  */
uint8_t Metro_HAL_Get_SAG_and_SWELL_Clear_Timeout(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel)
{
  uint8_t Metro_Clear_TimeOut =0;
     
  if(in_Metro_Device_Id >= EXT1) 
  {
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    {  
       /* Get  Clear Time Out for channel 1 */
       Metro_Clear_TimeOut = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1) & BIT_MASK_STPM_CLR_SS_TIME_OUT);   
    }  
    else  if(( in_Metro_int_Channel == INT_CHANNEL_2) || (in_Metro_int_Channel == CHANNEL_TAMPER))
    {
       /* Get  Clear Time Out for channel 2 */
       Metro_Clear_TimeOut = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL2) & BIT_MASK_STPM_CLR_SS_TIME_OUT);   
    }
  }
  return Metro_Clear_TimeOut;    
}
/**
  * @brief       Clear  Sag and swell Events
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   in_Metro_int_Channel (Channel ID), Channel 1 or 2 ( according to device )
  * @param[out]  None
  * @retval      None
  */
void Metro_HAL_Clear_SAG_and_SWELL_Events(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel)
{
  
  if(in_Metro_Device_Id >= EXT1) 
  {
    if ( in_Metro_int_Channel == INT_CHANNEL_1)
    {  
      /* Set bit Clear to Reset SAG V1  , SWELL V1 and C1 Events Bits */
      p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1 |= BIT_MASK_STPM_CLEAR_SAG_SWELL;
    }  
    else  if(( in_Metro_int_Channel == INT_CHANNEL_2) || (in_Metro_int_Channel == CHANNEL_TAMPER))
    {
       /* Set bit Clear to Reset SAG V2  , SWELL V2 and C2 Events Bits */
       p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL2 |= BIT_MASK_STPM_CLEAR_SAG_SWELL;
     
    }    
     
    /* Now Write the 2 U32 register inside external chip  for DSPCTRL1 and 2  */
    Metro_HAL_Stpm_write(in_Metro_Device_Id,STPM_DSPCTRL1,2,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSPCTRL1,STPM_WAIT);
  }
}

/**
  * @brief      This function read the momentary Cuurent from one device and one channel 
  * @param[in]   in_Metro_Device_Id (device ID), EXT1 to EXT4
  * @param[in]   in_Metro_int_Channel (Channel ID), Channel 1, 2 of device
  * @param[out]  None
  * @retval     uint32_t raw RMS voltage
  */
uint32_t Metro_HAL_read_RMS_Voltage(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel)
{
  uint32_t RMS_voltage = 0;

  if(in_Metro_Device_Id >= EXT1) 
  {
    if (in_Metro_int_Channel == INT_CHANNEL_1)
    {
      /* get directly from RAM, be carrefull : latch should be made before to have coherents values inside DSP data reg */
      RMS_voltage = (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSP_REG14)&BIT_MASK_STPM_DATA_VRMS;
    }
    else if (in_Metro_int_Channel == INT_CHANNEL_2)/* is channel 2 */
    {
      /* get directly from RAM, be carrefull !!!!! : latch should be made before to have coherents values inside DSP data reg */
      RMS_voltage = (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSP_REG15)&BIT_MASK_STPM_DATA_VRMS;
    }
  }
  return (RMS_voltage);
}

/**
  * @brief      This function read the momentary Cuurent from one device and one channel 
  * @param[in]   in_Metro_Device_Id (device ID), EXT1 to EXT4
  * @param[in]   in_Metro_int_Channel (Channel ID), Channel 1, 2 of device
  * @param[out]  None
  * @retval     uint32_t raw RMS current
  */
uint32_t Metro_HAL_read_RMS_Current(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel)
{
  uint32_t RMS_current = 0;

  if(in_Metro_Device_Id >= EXT1) 
  {
    if (in_Metro_int_Channel == INT_CHANNEL_1)
    {
      /* get directly from RAM, be carrefull : latch should be made before to have coherents values inside DSP data reg */
      RMS_current = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSP_REG14)&BIT_MASK_STPM_DATA_C1_RMS)>>BIT_MASK_STPM_DATA_C_RMS_SHIFT;
    }
    else if (in_Metro_int_Channel == INT_CHANNEL_2)/* is channel 2 */
    {
      /* get directly from RAM, be carrefull !!!!! : latch should be made before to have coherents values inside DSP data reg */
      RMS_current = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSP_REG15)&BIT_MASK_STPM_DATA_C2_RMS)>>BIT_MASK_STPM_DATA_C_RMS_SHIFT;
    }
  }
  return (RMS_current);
}

/**
  * @brief       This function Read the phase angle between voltage and current for the selected channel
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   in_Metro_int_Channel (Channel ID), Channel 1 or 2 of device
  * @param[out]  None
  * @retval     s32 Raw PHI 
  */
int32_t Metro_HAL_read_PHI(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel)
{
  int32_t PHI = 0;

  if(in_Metro_Device_Id >= EXT1) 
  {
    /* is Channel is the first or the second  channel of the chip */
    if (in_Metro_int_Channel == INT_CHANNEL_1)
    {
      /* get directly from RAM, be carrefull : latch should be made before to have coherents values inside DSP data reg */
      PHI = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSP_REG17)&BIT_MASK_STPM_PHASE_ANGLE_1)>>BIT_MASK_STPM_PHASE_ANGLE_SHIFT;
    }
    else if (in_Metro_int_Channel == INT_CHANNEL_2)/* is channel 2 */
    {
      /* get directly from RAM, be carrefull !!!!! : latch should be made before to have coherents values inside DSP data reg */
      PHI = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSP_REG19)&BIT_MASK_STPM_PHASE_ANGLE_2)>>BIT_MASK_STPM_PHASE_ANGLE_SHIFT;
    }
  }
  return (PHI);
}

/**
  * @brief       This function Read the AH Accumulation value  for the selected channel from a device
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   in_Metro_int_Channel (Channel ID), Channel 1 or 2 of device
  * @param[out]  None
  * @retval     s32 AH Accumulation 
  */
int32_t Metro_HAL_Read_AH_Acc(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel)
{
  int32_t AH_Acc = 0;

  if(in_Metro_Device_Id >= EXT1) 
  {
    /* is Channel is the first or the second  channel of the chip */
    if (in_Metro_int_Channel == INT_CHANNEL_1)
    {
      /* get directly from RAM, be carrefull : latch should be made before to have coherents values inside DSP data reg */
      AH_Acc = p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.CH1_REG12;
    }
    else if (in_Metro_int_Channel == INT_CHANNEL_2)/* is channel 2 */
    {
      /* get directly from RAM, be carrefull !!!!! : latch should be made before to have coherents values inside DSP data reg */
      AH_Acc = p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.CH2_REG12;
    }
  }
  return (AH_Acc);  
}

/**
  * @brief      This function read the period of signal come from one Channel mapped in one device
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   METRO_internal_Channel_t (Channel ID), Channel 1 or 2 ( according to device )
  * @param[out]  u16 period of channel
  * @retval
  */
uint16_t Metro_HAL_read_period(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel)
{
  uint32_t period = 0;

  if(in_Metro_Device_Id >= EXT1) 
  {
    /* is Channel is the first or the second  channel of the chip */
    if (in_Metro_int_Channel == INT_CHANNEL_2)
    {
      /* get directly from RAM, be carrefull : latch should be made before to have coherents values inside DSP data reg */
      period = ((p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSP_REG1)&BIT_MASK_STPM_PERIOD_CHANNEL_2)>>BIT_MASK_STPM_PERIOD_CHANNEL2_SHIFT;
    }
    else if (in_Metro_int_Channel == INT_CHANNEL_1)/* is channel one */
    {
      /* get directly from RAM, be carrefull !!!!! : latch should be made before to have coherents values inside DSP data reg */
      period = (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSP_REG1&BIT_MASK_STPM_PERIOD_CHANNEL_1);
    }
  }
  return ((uint16_t)period);
}

/**
  * @brief       This function Read momentary voltage data for the selected channel
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   in_Metro_int_Channel (Channel ID), Channel 1 or 2 ( according to device )
  * @param[in]   in_Metro_V_type :   V_WIDE = 1,  V_FUND = 2
  * @param[out]  None
  * @retval     int32_t raw_M_Voltage according to voltage type  read inside device register
  */
int32_t Metro_HAL_read_Momentary_Voltage(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel,METRO_Voltage_type_t in_Metro_V_type)
{
   int32_t M_voltage = 0;

  if(in_Metro_Device_Id >= EXT1) 
  {
    /* is Channel is the first or the second  channel of the chip */
    if (in_Metro_int_Channel == INT_CHANNEL_1)
    {
      if (in_Metro_V_type == V_FUND)
      {
        /* get directly from RAM, be carrefull : latch should be made before to have coherents values inside DSP data reg */
        M_voltage = (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSP_REG6)&BIT_MASK_STPM_DATA_V;
      }
      else if (in_Metro_V_type == V_WIDE)
      {
        /* get directly from RAM, be carrefull : latch should be made before to have coherents values inside DSP data reg */
        M_voltage = (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSP_REG2)&BIT_MASK_STPM_DATA_V;        
      }
    }
    else if (in_Metro_int_Channel == INT_CHANNEL_2)/* is channel two */
    {
      if (in_Metro_V_type == V_FUND)
      {
        /* get directly from RAM, be carrefull : latch should be made before to have coherents values inside DSP data reg */
        M_voltage = (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSP_REG8)&BIT_MASK_STPM_DATA_V;
      }
      else if (in_Metro_V_type == V_WIDE)
      {
        /* get directly from RAM, be carrefull : latch should be made before to have coherents values inside DSP data reg */
        M_voltage = (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSP_REG4)&BIT_MASK_STPM_DATA_V;     
      }
    }
  }
  return (M_voltage); 
}

/**
  * @brief      This function read the momentary Cuurent from one device and one channel 
  * @param[in]   in_Metro_Device_Id (device ID), HOST or EXT1 to EXT4
  * @param[in]   in_Metro_int_Channel (Channel ID), Channel 1, 2 or Tamper ( according to device )
  * @param[in]   METRO_Current_type_t :     C_WIDE = 1,  C_FUND = 2
  * @param[out]  None
  * @retval     s32 raw_M_Current according to Current type  read inside device register
  */
int32_t Metro_HAL_read_Momentary_Current(METRO_NB_Device_t in_Metro_Device_Id,METRO_internal_Channel_t in_Metro_int_Channel,METRO_Current_type_t in_Metro_C_type)
{
  int32_t M_Current = 0;

  if(in_Metro_Device_Id >= EXT1) 
  {
    /* is Channel is the first or the second  channel of the chip */
    if (in_Metro_int_Channel == INT_CHANNEL_1)
    {
      if (in_Metro_C_type == C_FUND)
      {
        /* get directly from RAM, be carrefull : latch should be made before to have coherents values inside DSP data reg */
        M_Current = (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSP_REG7)&BIT_MASK_STPM_DATA_C1;
      }
      else if (in_Metro_C_type == C_WIDE)
      {
        /* get directly from RAM, be carrefull : latch should be made before to have coherents values inside DSP data reg */
        M_Current = (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSP_REG3)&BIT_MASK_STPM_DATA_C1;        
      }
    }
    else if ((in_Metro_int_Channel == INT_CHANNEL_2) || (in_Metro_int_Channel == CHANNEL_TAMPER)) /* is channel two or tamper */
    {
      if (in_Metro_C_type == C_FUND)
      {
        /* get directly from RAM, be carrefull : latch should be made before to have coherents values inside DSP data reg */
        M_Current = (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSP_REG9)&BIT_MASK_STPM_DATA_C2;
      }
      else if (in_Metro_C_type == C_WIDE)
      {
        /* get directly from RAM, be carrefull : latch should be made before to have coherents values inside DSP data reg */
        M_Current = (p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.DSP_REG5)&BIT_MASK_STPM_DATA_C2;     
      }
    }
  }
  return M_Current;
}

/*************************************************************************/
/*        Porting wrapper UART Interface to dialog with STPM             */
/*************************************************************************/

/*******************/
/* LOCAL FUNCTIONS */
/*******************/


/**
  * @brief  This function send 1 pulse on SYN signal to latch metrology registers of STPM external chips
  * @param  METRO_NB_Device_t in_Metro_Device_Id
  * @retval None
  */
static void Metro_HAL_STPM_SYN_single_pulse(METRO_NB_Device_t in_Metro_Device_Id)
{

#ifdef UART_XFER_STPM3X /* UART MODE */   
  
    /* Before to toogle SYN pin , we have to Clear  SS  pin ( Chip select to Ext device ) */
  Metro_HAL_CSS_EXT_Device(in_Metro_Device_Id,GPIO_PIN_RESET);
  Metro_HAL_WaitMicroSecond(10); 
  Metro_HAL_CSS_EXT_Device(in_Metro_Device_Id,GPIO_PIN_SET);

#endif
  
  Metro_HAL_SYN_EXT_Device(in_Metro_Device_Id,GPIO_PIN_SET);
  /* reset SYNC pulse */
  Metro_HAL_SYN_EXT_Device(in_Metro_Device_Id,GPIO_PIN_RESET);

  Metro_HAL_WaitMicroSecond(10); 
  /* set SYNC pulse */
  Metro_HAL_SYN_EXT_Device(in_Metro_Device_Id,GPIO_PIN_SET);
  Metro_HAL_WaitMicroSecond(10); 

}

/**
  * @brief  This function send 3 pulses on SYN signal to golbal reset STPM external chips
  * @param  METRO_NB_Device_t in_Metro_Device_Id
  * @retval None
  */
static void Metro_HAL_STPM_SYN_reset_3_pulses(METRO_NB_Device_t in_Metro_Device_Id)
{
  Metro_HAL_SYN_EXT_Device(in_Metro_Device_Id,GPIO_PIN_SET);
  
  for(uint8_t i=0;i<=2; i++) 
  {
    /* reset SYNC pulse */
    Metro_HAL_SYN_EXT_Device(in_Metro_Device_Id,GPIO_PIN_RESET);

    Metro_HAL_WaitMicroSecond(100); 
    /* set SYNC pulse */
    Metro_HAL_SYN_EXT_Device(in_Metro_Device_Id,GPIO_PIN_SET);
    Metro_HAL_WaitMicroSecond(100); 

  }
}

/**
  * @brief      This function reset transfer context for external chip Only
  * @param[in]   in_Metro_Device_Id (device ID), EXT1 to EXT4
  * @retval     None
  */
static void Metro_HAL_reset_transfer_context(METRO_NB_Device_t in_Metro_Device_Id)
{
  /* Reset Fields transfer */

   /* TX side */
   p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pTxReadBuf  = Metro_Com_TxBuf;
   p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pTxWriteBuf = Metro_Com_TxBuf;
   p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.txValid = 0;
   p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.txOngoing = 0;
   p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.txData = 0;

   /* Rx Side */
   p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pRxReadBuf = Metro_Com_RxBuf;
   p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pRxWriteBuf = Metro_Com_RxBuf;
   p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.rxValid = 0;
   p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.rxOngoing = 0;
   p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.rxData = 0;

}


/**
  * @brief  This function handles wait
  * @param  time : time to wait in microseconds
  * @retval None
  */
static void Metro_HAL_WaitMicroSecond(uint32_t time)
{
  int i;
  uint32_t tmp;
#define ACCURACY               8
#define ADJ_RATIO              104
#define OVERHEAD               3
  if (SystemCoreClock == 96000000)
  {
    tmp = time * ((4<<ACCURACY)*ADJ_RATIO/100);
    tmp >>= ACCURACY;
  }
  else if (SystemCoreClock == 72000000)
  {
    tmp = time * ((3<<ACCURACY)*ADJ_RATIO/100);
    tmp >>= ACCURACY;
  }
  else if (SystemCoreClock == 48000000)
  {
    tmp = time * ((2<<ACCURACY)*ADJ_RATIO/100);
    tmp >>= ACCURACY;
  }
  else // default is 24000000
  {
    tmp = time * ((1<<ACCURACY)*ADJ_RATIO/100);
    tmp >>= ACCURACY;
  }
  if (tmp >= OVERHEAD)
  {
    tmp -= OVERHEAD;
  }
  for (i=0; i<tmp; i++)
  {
    waitDummyCounter++;
  }
}

#ifdef UART_XFER_STPM3X /* UART MODE */   
/**
  * @brief      Reverse byte
  * @param      one Byte
  * @retval     Byte reversed
  */
static uint8_t Metro_HAL_byteReverse(uint8_t in_byte)
{
    in_byte = ((in_byte >> 1) & 0x55) | ((in_byte << 1) & 0xaa);
    in_byte = ((in_byte >> 2) & 0x33) | ((in_byte << 2) & 0xcc);
    in_byte = ((in_byte >> 4) & 0x0F) | ((in_byte << 4) & 0xF0);

    return in_byte;
}
#endif 
/**
  * @brief      Calculate CRC of a byte
  * @param      one Byte
  * @retval     None
  */
static void Metro_HAL_Crc8Calc (uint8_t in_Data)
{
    uint8_t loc_u8Idx;
    uint8_t loc_u8Temp;
    loc_u8Idx=0;
    while(loc_u8Idx<8)
    {
        loc_u8Temp=in_Data^CRC_u8Checksum;
        CRC_u8Checksum<<=1;
        if(loc_u8Temp&0x80)
        {
            CRC_u8Checksum^=CRC_8;
        }
        in_Data<<=1;
        loc_u8Idx++;
    }
}
/**
  * @brief      Calculate CRC of a frame
  * @param      Buf Frame
  * @retval     u8 checksum of the frame
  */
static uint8_t Metro_HAL_CalcCRC8(uint8_t *pBuf)
{
    uint8_t     i;
    CRC_u8Checksum = 0x00;

    for (i=0; i<STPM3x_FRAME_LEN-1; i++)
    {
        Metro_HAL_Crc8Calc(pBuf[i]);
    }

    return CRC_u8Checksum;
}


/**
  * @brief        This function trigs a read of a set of U32 reg (frame) from ext devices
  * @param[in]   in_Metro_Device_Id (device ID), EXT1 to EXT4
  * @param[in]   Base adress of data to write (U16 base address for STPM),
  * @param[in]   Nb of blocks (nb of u32 to write )
  *@param[in]    in_wait_stpm : 0 : no wait RX frame from STPM after the write 1 : wait RX frame from STPM
  * @param[in]  in_p_Buffer : Data to write
  * @retval
  */
uint32_t Metro_HAL_Stpm_write(METRO_NB_Device_t in_Metro_Device_Id,uint8_t * in_p_data,uint8_t nb_blocks,uint32_t * in_p_Buffer,uint8_t in_wait_stpm)
{
   uint32_t retSize = 0;
   uint8_t nb_blocks_tmp;
#ifdef UART_XFER_STPM3X /* UART MODE */  
   uint8_t CRC_on_reversed_buf;
#endif
   uint8_t i=0;
   uint8_t *p_writePointer = (uint8_t*)in_p_Buffer;
   uint8_t k=0;

   uint8_t frame_with_CRC[STPM3x_FRAME_LEN];
   uint8_t frame_without_CRC[STPM3x_FRAME_LEN -1];


    /* Reset Buffers */
   memset(Metro_Com_TxBuf,0,METRO_BUFF_COM_MAXSIZE);
   memset(Metro_Com_RxBuf,0,METRO_BUFF_COM_MAXSIZE);

   /* Reset Fields transfer */
   Metro_HAL_reset_transfer_context(in_Metro_Device_Id);


   /* Format the Frames according to NB blocks to write */
   /* One block is an U32 but STPM need to write in two times ( 2 U16 )*/
   /* Nb blocks * 2 to multiply by 2 the write requets */
   if (nb_blocks==0)
   {
     nb_blocks_tmp = 1;
   }
   else
   {
     nb_blocks_tmp = nb_blocks*2;
   }
   
#ifdef UART_XFER_STPM3X /* UART MODE */      
  Metro_HAL_CSS_EXT_Device(in_Metro_Device_Id,GPIO_PIN_SET); 
#endif
  
#ifdef SPI_XFER_STPM3X     
  /* toggle CSS signal to level 0 of good EXT chip during Full duplex transfert */
  Metro_HAL_CSS_EXT_Device(in_Metro_Device_Id,GPIO_PIN_RESET); 
#endif
  
  
   for (k=0;k<nb_blocks_tmp;k++)
   {

     /* Format the frame with Write base address */
     frame_with_CRC[0] = 0xff; /*  No read requested, put dummy frame  */
     frame_with_CRC[1] = (*in_p_data) + k; /*  write Address requested */
     frame_with_CRC[2] = *(p_writePointer); /*   DATA for 16-bit register to be written, LSB */
     frame_with_CRC[3] = *(++p_writePointer); /*  DATA for 16-bit register to be written, MSB */

     /* Increment Pointer to next U16 data for the next loop */
     p_writePointer++;

#ifdef UART_XFER_STPM3X /* UART MODE */ 
     /* Reverse bytes */
     for (i=0;i<(STPM3x_FRAME_LEN-1);i++)
     {
       frame_without_CRC[i] = Metro_HAL_byteReverse(frame_with_CRC[i]);
     }

     /* Calculate CRC and put it at the end of the frame */
     CRC_on_reversed_buf = Metro_HAL_CalcCRC8(frame_without_CRC);
     frame_with_CRC[4] = Metro_HAL_byteReverse(CRC_on_reversed_buf);
#endif

#ifdef SPI_XFER_STPM3X     
     for (i=0;i<(STPM3x_FRAME_LEN-1);i++)
     {
       frame_without_CRC[i] = frame_with_CRC[i];
     }  
     frame_with_CRC[4] = Metro_HAL_CalcCRC8(frame_without_CRC);
     
#endif
     
     
     /* Put the frame inside the TX queue      */
     memcpy(p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pTxWriteBuf,&frame_with_CRC,STPM3x_FRAME_LEN);

     retSize = retSize + STPM3x_FRAME_LEN;
     p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pTxWriteBuf+= STPM3x_FRAME_LEN;

     
#ifdef UART_XFER_STPM3X /* UART MODE */      
     /* Send  Data */
     Metro_HAL_UsartTxStart(in_Metro_Device_Id);
#endif
     
#ifdef SPI_XFER_STPM3X     
     /* Send  Data */
     Metro_HAL_SpiTxStart(in_Metro_Device_Id);
#endif

     /* Wait STPM RX reception frame for STPM after a write */
     if (in_wait_stpm == STPM_WAIT)
     {
        /* Wait end of RX frame reception to go to next tx frame*/
        while (p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.rxValid < 1);        
     }
     
     
   /* Reset Fields transfer */
   Metro_HAL_reset_transfer_context(in_Metro_Device_Id);


   } /* end For Nb blocks loop */


#ifdef SPI_XFER_STPM3X /* SPI MODE */ 
  /* toggle CSS signal to level 1 end of transfert */
  Metro_HAL_CSS_EXT_Device(in_Metro_Device_Id,GPIO_PIN_SET); 
#endif     
  
   /* Reset Fields transfer */
   Metro_HAL_reset_transfer_context(in_Metro_Device_Id);


   /* Reset RX/TX Buffers */
   memset(Metro_Com_TxBuf,0,METRO_BUFF_COM_MAXSIZE);
   memset(Metro_Com_RxBuf,0,METRO_BUFF_COM_MAXSIZE);


   return(retSize);
}

/**
  * @brief      This function trigs a read of a set of U32 reg (frame) from ext devices
  * @param[in]   in_Metro_Device_Id (device ID), EXT1 to EXT4
  * @param[in]   Base adress (U16 for STPM),
  * @param[in]  Nb of blocks (nb of u32 to read )
  * @param[out]  output buffer filled
  * @retval
  */
uint32_t Metro_HAL_Stpm_Read(METRO_NB_Device_t in_Metro_Device_Id,uint8_t * in_p_data,uint8_t nb_blocks,uint32_t * out_p_read_data)
{
   uint32_t retSize = 0;
#ifdef UART_XFER_STPM3X /* UART MODE */  
   uint8_t CRC_on_reversed_buf;
#endif   
   uint8_t i =0;
   uint8_t k=0;
   uint8_t * p_read_data = (uint8_t*) out_p_read_data;

   uint8_t frame_with_CRC[STPM3x_FRAME_LEN];
   uint8_t frame_without_CRC[STPM3x_FRAME_LEN -1];

   /* init struct of device requested*/
   //memset(p_Metro_Device_Config[in_Metro_Device_Id],0,sizeof(METRO_Device_Config_t));

   /* Reset Buffers */
   memset(Metro_Com_TxBuf,0,METRO_BUFF_COM_MAXSIZE);
   memset(Metro_Com_RxBuf,0,METRO_BUFF_COM_MAXSIZE);

   /* Reset Fields transfer */
   Metro_HAL_reset_transfer_context(in_Metro_Device_Id);

   /* First frame send the data read pointer inside frame */
   /* Format the frame with Read base address */
   frame_with_CRC[0] = (*in_p_data); /* put the read adress */
   frame_with_CRC[1] = 0xFF; /* no write requested */
   frame_with_CRC[2] = 0xFF; /* no Data */
   frame_with_CRC[3] = 0xFF; /* no Data */
  
#ifdef UART_XFER_STPM3X /* UART MODE */ 
     /* Reverse bytes */
     for (i=0;i<(STPM3x_FRAME_LEN-1);i++)
     {
       frame_without_CRC[i] = Metro_HAL_byteReverse(frame_with_CRC[i]);
     }

     /* Calculate CRC and put it at the end of the frame */
     CRC_on_reversed_buf = Metro_HAL_CalcCRC8(frame_without_CRC);
     frame_with_CRC[4] = Metro_HAL_byteReverse(CRC_on_reversed_buf);
#endif 
     
#ifdef SPI_XFER_STPM3X     
     for (i=0;i<(STPM3x_FRAME_LEN-1);i++)
     {
       frame_without_CRC[i] = frame_with_CRC[i];
     }  
     frame_with_CRC[4] = Metro_HAL_CalcCRC8(frame_without_CRC);
     
#endif   
   
   /* Put the frame inside the TX queue      */
   memcpy(p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pTxWriteBuf,&frame_with_CRC,STPM3x_FRAME_LEN);

   retSize = retSize + STPM3x_FRAME_LEN;
   p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pTxWriteBuf+= STPM3x_FRAME_LEN;

#ifdef UART_XFER_STPM3X /* UART MODE */      
     /* toggle CSS signal to level 1 of good EXT chip during Full duplex transfert */
     Metro_HAL_CSS_EXT_Device(in_Metro_Device_Id,GPIO_PIN_SET);     
  
     /* Send  Data */
     Metro_HAL_UsartTxStart(in_Metro_Device_Id);
#endif
     
#ifdef SPI_XFER_STPM3X     
     /* toggle CSS signal to level 0 of good EXT chip during Full duplex transfert */
     Metro_HAL_CSS_EXT_Device(in_Metro_Device_Id,GPIO_PIN_RESET);     
     
     /* Send  Data */
     Metro_HAL_SpiTxStart(in_Metro_Device_Id);
#endif


   volatile uint32_t tmp2 = 0;
        
   /* Wait end of RX frame reception to go to next tx frame and check if anwser is not too long : detect no ext chip connected  */
   while (p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.rxValid < 1)
   {

     tmp2++;
       
     if (tmp2 > WAIT_DURATION)
     {
        Metro_HAL_reset_transfer_context(in_Metro_Device_Id);
        return 0;
     }    
   }  


   /* Reset Fields transfer */
   Metro_HAL_reset_transfer_context(in_Metro_Device_Id);

   /* Format the Frames according to NB blocks to read, one block is one U32 register inside STPM */
   for (k=0;k<nb_blocks;k++)
   {

     /* send FF to read next frame*/

    /* Format the frame with Read base address */
     frame_with_CRC[0] = 0xFF; /* put FF to read */
     frame_with_CRC[1] = 0xFF; /* no write requested */
     frame_with_CRC[2] = 0xFF; /* no Data */
     frame_with_CRC[3] = 0xFF; /* no Data */

#ifdef UART_XFER_STPM3X /* UART MODE */ 
     /* Reverse bytes */
     for (i=0;i<(STPM3x_FRAME_LEN-1);i++)
     {
       frame_without_CRC[i] = Metro_HAL_byteReverse(frame_with_CRC[i]);
     }

     /* Calculate CRC and put it at the end of the frame */
     CRC_on_reversed_buf = Metro_HAL_CalcCRC8(frame_without_CRC);
     frame_with_CRC[4] = Metro_HAL_byteReverse(CRC_on_reversed_buf);
#endif
     
#ifdef SPI_XFER_STPM3X     
     for (i=0;i<(STPM3x_FRAME_LEN-1);i++)
     {
       frame_without_CRC[i] = frame_with_CRC[i];
     }  
     frame_with_CRC[4] = Metro_HAL_CalcCRC8(frame_without_CRC);
     
#endif

     /* Put the frame inside the TX queue      */
     memcpy(p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pTxWriteBuf,&frame_with_CRC,STPM3x_FRAME_LEN);

     retSize = retSize + STPM3x_FRAME_LEN;
     p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pTxWriteBuf+= STPM3x_FRAME_LEN;

#ifdef UART_XFER_STPM3X /* UART MODE */      
     /* Send  Data */
     Metro_HAL_UsartTxStart(in_Metro_Device_Id);
#endif
     
#ifdef SPI_XFER_STPM3X     
     /* Send  Data */
     Metro_HAL_SpiTxStart(in_Metro_Device_Id);
#endif

     /* Wait end of RX frame reception to go to next tx frame*/
     while (p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.rxValid < 1);

    /* Now Retreive RX data (one frame of 4 bytes : one U32): memcpy from RX buffer */
    /* first increment pointer of data and put new data at the end of buffer */
    memcpy(p_read_data+(k*4), p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pRxReadBuf,4);

    /* Reset Fields transfer */
    Metro_HAL_reset_transfer_context(in_Metro_Device_Id);

   } /* end For Nb blocks loop */

#ifdef SPI_XFER_STPM3X /* SPI MODE */        
  /* toggle CSS signal to 0 of good EXT chip after Full duplex transfert */
  Metro_HAL_CSS_EXT_Device(in_Metro_Device_Id,GPIO_PIN_SET);
#endif
  
   /* Reset Buffers */
   memset(Metro_Com_TxBuf,0,METRO_BUFF_COM_MAXSIZE);
   memset(Metro_Com_RxBuf,0,METRO_BUFF_COM_MAXSIZE);

   return(retSize);
}

/**
  * @brief  CSS management for External Metrology Devices
  *
  *
  * @retval void
  */
static void Metro_HAL_CSS_EXT_Device(METRO_NB_Device_t in_Metro_Device_Id,GPIO_PinState in_Metro_enable)
{    
  HAL_GPIO_WritePin(p_Metro_Device_Config[in_Metro_Device_Id].STPM_com_port.cs_port,p_Metro_Device_Config[in_Metro_Device_Id].STPM_com_port.cs_pin,in_Metro_enable);     
}

/**
  * @brief  EN management for External Metrology Devices
  *         It is used in case of EN can be controlled
  *
  * @retval void
  */
static void Metro_HAL_EN_EXT_Device(METRO_NB_Device_t in_Metro_Device_Id,GPIO_PinState in_Metro_enable)
{    
  HAL_GPIO_WritePin(p_Metro_Device_Config[in_Metro_Device_Id].STPM_com_port.en_port,p_Metro_Device_Config[in_Metro_Device_Id].STPM_com_port.en_pin,in_Metro_enable);     
}

/**
  * @brief  SYN management for External Metrology Devices
  *         It is used in case of EN can be controlled
  *
  * @retval void
  */
static void Metro_HAL_SYN_EXT_Device(METRO_NB_Device_t in_Metro_Device_Id,GPIO_PinState in_Metro_enable)
{    
  HAL_GPIO_WritePin(p_Metro_Device_Config[in_Metro_Device_Id].STPM_com_port.syn_port,p_Metro_Device_Config[in_Metro_Device_Id].STPM_com_port.syn_pin,in_Metro_enable);     
}

/**
  * @brief      handles  RX data
  * @param      None
  * @retval     None
  */
static void Metro_HAL_RxHandler(METRO_NB_Device_t in_Metro_Device_Id)
{
  static uint8_t Cpt_char;

  if (p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pRxWriteBuf == p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pRxReadBuf)
  {
    p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.rxValid = 0;
    p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.rxOngoing = 0;
    p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pRxReadBuf = Metro_Com_RxBuf;
    p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pRxWriteBuf = Metro_Com_RxBuf;
    Cpt_char = 0;

    /* get the first u8 of the first frame */
    *p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pRxWriteBuf = p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.rxData;
    p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pRxWriteBuf += 1;
    p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.rxOngoing = 1;
    Cpt_char++;
  }
  else
  {
    Cpt_char ++;

    /* if frame is not completed  (5 bytes) continue to received bytes */
    if (Cpt_char <= 4)
    {
      *p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pRxWriteBuf = p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.rxData;
      p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pRxWriteBuf += 1;
      p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.rxOngoing = 1;

    }
    /* if 5 Bytes are received  : 4 data bytes + 1 CRC byte)*/
    else if (Cpt_char > 4)
    {
      /* it is the last Char of frame => CRC, trash it for the moment */
      /* No copy inside the buffer */

      /* increment RX Nb frame Valid */
      p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.rxValid++;

      /* reset CPT char, go to Next frame if necessary*/
      Cpt_char = 0;
    }
  }

}

/**
  * @brief      handles TX data
  * @param      None
  * @retval     None
  */
static void Metro_HAL_TxHandler(METRO_NB_Device_t in_Metro_Device_Id)
{
  if (p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pTxWriteBuf == p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pTxReadBuf)
  {
    p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.txValid = 0;
    p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.txOngoing = 0;
    p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pTxReadBuf = Metro_Com_TxBuf;
    p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pTxWriteBuf = Metro_Com_TxBuf;
  }
  else
  {
    p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.txData = *p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pTxReadBuf;
    p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pTxReadBuf += 1;
    p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.txValid = 1;
  }
}


/*****************************/
/* USART Interface FUNCTIONS */
/*****************************/

#ifdef UART_XFER_STPM3X /* UART MODE */   

/**
  * @brief  USART Config for External Metrology Devices
  *
  *
  * @retval void
  */

static void Metro_HAL_usart_config(METRO_NB_Device_t in_Metro_Device_Id, uint32_t in_baudrate)
{

  huart[in_Metro_Device_Id].Instance = p_Metro_Device_Config[in_Metro_Device_Id].STPM_com_port.uart;
  huart[in_Metro_Device_Id].Init.BaudRate = in_baudrate;
  huart[in_Metro_Device_Id].Init.WordLength = UART_WORDLENGTH_8B;
  huart[in_Metro_Device_Id].Init.StopBits = UART_STOPBITS_1;
  huart[in_Metro_Device_Id].Init.Parity = UART_PARITY_NONE;
  huart[in_Metro_Device_Id].Init.Mode = UART_MODE_TX_RX;
  huart[in_Metro_Device_Id].Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart[in_Metro_Device_Id].Init.OverSampling = UART_OVERSAMPLING_16;
  HAL_UART_Init(&huart[in_Metro_Device_Id]);
  
  __HAL_UART_ENABLE(&huart[in_Metro_Device_Id]);
}

/**
  * @brief      handles first TX data
  * @param[in]   in_Metro_Device_Id (device ID), EXT1 to EXT4
  * @retval     None
  */
static void Metro_HAL_UsartTxStart(METRO_NB_Device_t in_Metro_Device_Id)
{  
  uint8_t data;

    
  if (p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.txOngoing == 0)
  {  
    data  = UARTWrp_SendAndReceiveByte(in_Metro_Device_Id,*p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pTxReadBuf);
    p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pTxReadBuf += 1;
    p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.txOngoing = 1;  
    
    do
    {
      p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.rxData = data;
      Metro_HAL_RxHandler(in_Metro_Device_Id);

      if (p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pTxWriteBuf != 0)
      {
        Metro_HAL_TxHandler(in_Metro_Device_Id);

        if (p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.txValid==1)
        {
          data  = UARTWrp_SendAndReceiveByte(in_Metro_Device_Id,p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.txData);
        }
      }
    }while(p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.txOngoing);

  }
}


/**
  * @brief      Send and receive byte through UART
  * @param[in]  in_Metro_Device_Id (device ID), EXT1 to EXT4 and Data to send
  * @retval     Data recieved
  */

static uint8_t UARTWrp_SendAndReceiveByte(METRO_NB_Device_t in_Metro_Device_Id,uint8_t data)
{

  HAL_UART_Transmit(&huart[in_Metro_Device_Id], &data, 1, 0);
  HAL_UART_Receive(&huart[in_Metro_Device_Id], &data, 1, USART_TIMEOUT);
  return(data);
   
}


/**
  * @brief      This function set the baud rate of HOST between host and STPM
  * @brief      !!!! Be Carrefull, change baud rate of external chip before to change baud rate of HOST...
  * @param[in]  in_Metro_Device_Id: Device ID
  * @param[in]  in_baudrate: new baudrate to transmit
  * @retval     return true if the baudsate is change, False if not because transmission is on going in STPM side
  */
uint8_t Metro_HAL_baudrate_set(METRO_NB_Device_t in_Metro_Device_Id,uint32_t in_baudrate)
{
    uint32_t tmp_addr = 0;
    static uint32_t tmp_data = 0;
    
    uint32_t stpm_baudrate = 0;
    
    if (in_Metro_Device_Id == HOST)
    {
       return 1;
    }    
    else if (in_Metro_Device_Id < NB_MAX_DEVICE)
    {
       switch (in_baudrate)
       {
        case 2400 :
          stpm_baudrate = METRO_STPM_UART_BAUDRATE_2400;
          break;
        case 9600 :
          stpm_baudrate = METRO_STPM_UART_BAUDRATE_9600;
          break;
        case 19200 :
          stpm_baudrate = METRO_STPM_UART_BAUDRATE_19200;
          break;

        case 57600 :
          stpm_baudrate = METRO_STPM_UART_BAUDRATE_57600;
          break;

        case 115200 :
           stpm_baudrate = METRO_STPM_UART_BAUDRATE_115200;
          break;

        case 230400 :
           stpm_baudrate = METRO_STPM_UART_BAUDRATE_230400;
          break;

        case 460800 :
          stpm_baudrate = METRO_STPM_UART_BAUDRATE_460800;
          break;

       default :
         return 0;
         break;

       }

        /* Set  new baudrate according to request*/
        p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPICR2 = stpm_baudrate;

        /* Now send data to the external chip */
        /* the address should be provided in 2 bytes format (16 bits by 16 bits) for STPM */
        tmp_addr = STPM_USREG2;

        Metro_HAL_Stpm_Read(in_Metro_Device_Id,(uint8_t*)&tmp_addr,1,&tmp_data);

        /* Write register inside external chip with "no wait" option because the return frame will not be at the same baudrate */
        Metro_HAL_Stpm_write(in_Metro_Device_Id,(uint8_t*)&tmp_addr,0,&p_Metro_Device_Config[in_Metro_Device_Id].metro_stpm_reg.UARTSPICR2,STPM_NO_WAIT);

        Metro_HAL_WaitMicroSecond(1000);
      
        Metro_HAL_usart_config(in_Metro_Device_Id,in_baudrate);
        
        return 1;
    }
    else
    {
        return 0;
    }

}
#endif


/*****************************/
/* SPI  Interface FUNCTIONS */
/*****************************/

#ifdef SPI_XFER_STPM3X /* SPI MODE */   

/**
  * @brief  SPI Config for External Metrology Devices
  *
  *
  * @retval void
  */

static void Metro_HAL_Spi_config(METRO_NB_Device_t in_Metro_Device_Id)
{

  
  hspi[in_Metro_Device_Id].Instance = p_Metro_Device_Config[in_Metro_Device_Id].STPM_com_port.spi;
  hspi[in_Metro_Device_Id].Init.Mode = SPI_MODE_MASTER;
  hspi[in_Metro_Device_Id].Init.Direction = SPI_DIRECTION_2LINES;
  hspi[in_Metro_Device_Id].Init.DataSize = SPI_DATASIZE_8BIT;
  hspi[in_Metro_Device_Id].Init.CLKPolarity = SPI_POLARITY_HIGH;
  hspi[in_Metro_Device_Id].Init.CLKPhase = SPI_PHASE_2EDGE;
  hspi[in_Metro_Device_Id].Init.NSS = SPI_NSS_SOFT;
  hspi[in_Metro_Device_Id].Init.BaudRatePrescaler = SPI_STPM_SPEED;
  hspi[in_Metro_Device_Id].Init.FirstBit = SPI_FIRSTBIT_MSB;
  hspi[in_Metro_Device_Id].Init.TIMode = SPI_TIMODE_DISABLED;
  hspi[in_Metro_Device_Id].Init.CRCCalculation = SPI_CRCCALCULATION_DISABLED;
  hspi[in_Metro_Device_Id].Init.CRCPolynomial = 7;
  
  HAL_SPI_Init(&hspi[in_Metro_Device_Id]);
  
  __HAL_SPI_ENABLE(&hspi[in_Metro_Device_Id]);
}

/**
  * @brief      handles first TX data
  * @param[in]   in_Metro_Device_Id (device ID), EXT1 to EXT4
  * @retval     None
  */
static void Metro_HAL_SpiTxStart(METRO_NB_Device_t in_Metro_Device_Id)
{  
  uint8_t data;
    
  if (p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.txOngoing == 0)
  {  
    data  = SPIWrp_SendAndReceiveByte(in_Metro_Device_Id,*p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pTxReadBuf);
    p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pTxReadBuf += 1;
    p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.txOngoing = 1;  
    
    do
    {
      p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.rxData = data;
      Metro_HAL_RxHandler(in_Metro_Device_Id);

      if (p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.pTxWriteBuf != 0)
      {
        Metro_HAL_TxHandler(in_Metro_Device_Id);

        if (p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.txValid==1)
        {
          data  = SPIWrp_SendAndReceiveByte(in_Metro_Device_Id,p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.txData);
        }
      }
    }while(p_Metro_Device_Config[in_Metro_Device_Id].STPM_com.txOngoing);

  }
}

/**
  * @brief      Send and receive byte through SPI
  * @param[in]  in_Metro_Device_Id (device ID), EXT1 to EXT4 and Data to send
  * @retval     Data recieved
  */

static uint8_t SPIWrp_SendAndReceiveByte(METRO_NB_Device_t in_Metro_Device_Id,uint8_t data)
{  
  
  uint8_t data_in;
  
  HAL_SPI_TransmitReceive(&hspi[in_Metro_Device_Id],&data,&data_in,1,SPI_TIMEOUT);
  
  return(data_in);
  

}


#endif
/**
  * @}
  */

/**
  * @}
  */

/**
  * @}
  */

/**
  * @}
  */

/************************ (C) COPYRIGHT STMicroelectronics *****END OF FILE****/
