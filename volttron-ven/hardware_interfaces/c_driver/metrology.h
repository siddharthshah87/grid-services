/**
  ******************************************************************************
  * @file    metrology.h
  * @author  AMG/IPC Application Team
  * @brief   This file contains all the functions prototypes for 
  *          the Generic Metrology
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

#ifndef __METROLOGY_H
#define __METROLOGY_H

#ifdef __cplusplus
 extern "C" {
#endif

/* ------------------------------------------------------------------------------------------------------------------*/
/* --------------------------------------------  Includes -----------------------------------------------------------*/
/* ------------------------------------------------------------------------------------------------------------------*/


#include "stpm_metrology.h"
#include "st_device.h"
   
/* ------------------------------------------------------------------------------------------------------------------*/
/* -----------------------------------------  Exported types --------------------------------------------------------*/
/* ------------------------------------------------------------------------------------------------------------------*/


 /**
  * @brief METROLOGY Reset type
  *
  */  
   
typedef enum 
{
  RESET_SYN_SCS = 1,
  RESET_SW
}METRO_ResetType_t;  

/**
  * @brief METROLOGY External device Enable/Disable
  *
  */  
   
typedef enum 
{
  EXT_DISABLE = 0,  
  EXT_ENABLE    
}METRO_CMD_EXT_Device_t;  


 /**
  * @brief METROLOGY generic cmd Enable/Disable
  *
  */  
   
typedef enum 
{
  DEVICE_DISABLE = 0,  
  DEVICE_ENABLE = 1,
  NO_CHANGE
}METRO_CMD_Device_t;  


 /**
  * @brief METROLOGY  Voltage Channel definition
  *
  */  
   
typedef enum 
{
  V_1 = 1,  
  V_2,
  V_3, 
  V_4  
}METRO_Voltage_Channel_t; 

 /**
  * @brief METROLOGY  Current CHANNEL definition
  *
  */  
   
typedef enum 
{
  C_1 = 1,  
  C_2,
  C_3, 
  C_4  
}METRO_Current_Channel_t; 

 /**
  * @brief METROLOGY  Current Gain definition
  *
  */  
   
typedef enum 
{
  X2 = 0,  
  X4,
  X8, 
  X16  
}METRO_Gain_t; 


/**
  * @brief METROLOGY  Vref device definition
  *
  */  
   
typedef enum 
{
  EXT_VREF =0,
  INT_VREF  
}METRO_Vref_t;


 /**
  * @brief METROLOGY  Current CHANNEL definition
  *
  */  
   
typedef enum 
{
  PRIMARY = 0,  
  SECONDARY,
  ALGEBRIC, 
  SIGMA_DELTA  
}METRO_LED_Channel_t; 


 /**
  * @brief METROLOGY  LED Slection type
  *
  */  
   
typedef enum 
{
  LED1 = 1,  
  LED2 
}METRO_LED_Selection_t; 


/**
  * @brief METROLOGY  Power selection type
  *
  */  
   
typedef enum 
{
  W_ACTIVE = 1,  
  F_ACTIVE,
  REACTIVE, 
  APPARENT_RMS,
  APPARENT_VEC,
  MOM_WIDE_ACT,
  MOM_FUND_ACT
}METRO_Power_selection_t;

typedef enum 
{
  LED_W_ACTIVE = 0,  
  LED_F_ACTIVE,
  LED_REACTIVE, 
  LED_APPARENT_RMS,

}METRO_LED_Power_selection_t;


typedef enum 
{
  E_W_ACTIVE = 1,  
  E_F_ACTIVE,
  E_REACTIVE, 
  E_APPARENT,
  NB_MAX_TYPE_NRJ
}METRO_Energy_selection_t;

/**
  * @brief METROLOGY  Calculation Power selection type
  *
  */  
   
typedef enum 
{
  FROM_RMS = 1,  
  FROM_PWIDE,
  FROM_PFUND
}METRO_Calculation_Power_selection_t;

/**
  * @brief METROLOGY  Latch device type
  *
  */  
typedef enum 
{
  LATCH_SYN_SCS = 1,  
  LATCH_SW,
  LATCH_AUTO
 }METRO_Latch_Device_Type_t;

/**
  * @brief METROLOGY  Voltage read type
  *
  */  
typedef enum 
{
  V_WIDE = 1,  
  V_FUND
 }METRO_Voltage_type_t;

/**
  * @brief METROLOGY  Current read type
  *
  */  
typedef enum 
{
  C_WIDE = 1,  
  C_FUND
 }METRO_Current_type_t;



/**
  * @brief METROLOGY  Tamper Tolerance type
  *
  */  
typedef enum 
{
  TOL_12_5 = 0,  
  TOL_8_33,
  TOL_6_25,
  TOL_3_125,
  NO_CHANGE_TOL
 }METRO_Tamper_Tolerance_t;


/**
  * @brief METROLOGY  ZCR Signal Selection
  *
  */  
typedef enum 
{
  ZCR_SEL_V1 = 0,  
  ZCR_SEL_C1,
  ZCR_SEL_V2,
  ZCR_SEL_C2,
  NO_CHANGE_ZCR
 }METRO_ZCR_Sel_t;

 
 /**
  * @brief METROLOGY  CLK  Selection
  *
  */  
typedef enum 
{
  CLK_SEL_7KHz = 0,  
  CLK_SEL_4MHz,
  CLK_SEL_4MHz_50,
  CLK_SEL_16MHz,
  NO_CHANGE_CLK
 }METRO_CLK_Sel_t;
 
   
  /**
  * @brief METROLOGY  Live Event type
  *
  */  
typedef enum 
{
  ALL_LIVE_EVENTS =0,
  LIVE_EVENT_REFRESHED,
  LIVE_EVENT_WRONG_INSERTION,
  LIVE_EVENT_VOLTAGE_SAG,  
  LIVE_EVENT_VOLTAGE_SWELL,
  LIVE_EVENT_CURRENT_SWELL,
  LIVE_EVENT_VOLTAGE_ZCR,
  LIVE_EVENT_CURRENT_ZCR,  
  LIVE_EVENT_VOLTAGE_PERIOD_STATUS,
  LIVE_EVENT_VOLTAGE_SIGNAL_STUCK,
  LIVE_EVENT_CURRENT_SIGNAL_STUCK,
  LIVE_EVENT_CURRENT_TAMPER,
  LIVE_EVENT_CURRENT_SIGN_CHANGE_APPARENT_POWER,
  LIVE_EVENT_CURRENT_SIGN_CHANGE_REACTIVE_POWER,
  LIVE_EVENT_CURRENT_SIGN_CHANGE_FUNDAMENTAL_POWER,
  LIVE_EVENT_CURRENT_SIGN_CHANGE_ACTIVE_POWER,
  LIVE_EVENT_CURRENT_OVERFLOW_APPARENT_NRJ,
  LIVE_EVENT_CURRENT_OVERFLOW_REACTIVE_NRJ,
  LIVE_EVENT_CURRENT_OVERFLOW_FUNDAMENTAL_NRJ,
  LIVE_EVENT_CURRENT_OVERFLOW_ACTIVE_NRJ,
  LIVE_EVENT_CURRENT_NAH
 }METRO_Live_Event_Type_t;

  /**
  * @brief METROLOGY Status type
  *
  */  
typedef enum 
{
  ALL_STATUS = 0,
  STATUS_REFRESHED,
  STATUS_TAMPER_DETECTED,
  STATUS_TAMPER_OR_WRONG,
  STATUS_VOLTAGE_SWELL_DOWN,
  STATUS_VOLTAGE_SWELL_UP,
  STATUS_VOLTAGE_SAG_DOWN,
  STATUS_VOLTAGE_SAG_UP,    
  STATUS_VOLTAGE_PERIOD_STATUS,
  STATUS_VOLTAGE_SIGNAL_STUCK,
  STATUS_CURRENT_OVERFLOW_APPARENT_NRJ,
  STATUS_CURRENT_OVERFLOW_REACTIVE_NRJ,
  STATUS_CURRENT_OVERFLOW_FUNDAMENTAL_NRJ,
  STATUS_CURRENT_OVERFLOW_ACTIVE_NRJ,
  STATUS_CURRENT_SIGN_APPARENT_POWER,
  STATUS_CURRENT_SIGN_CHANGE_REACTIVE_POWER,
  STATUS_CURRENT_SIGN_CHANGE_FUNDAMENTAL_POWER,
  STATUS_CURRENT_SIGN_CHANGE_ACTIVE_POWER,
  STATUS_CURRENT_SWELL_DOWN,
  STATUS_CURRENT_SWELL_UP,
  STATUS_CURRENT_NAH_TMP,
  STATUS_CURRENT_SIGNAL_STUCK
 }METRO_Status_Type_t;
 
  /**
  * @brief METROLOGY Status type
  *
  */  
typedef enum 
{
  ALL_STPM_LINK_STATUS = 0,
  STATUS_STPM_UART_LINK_BREAK,
  STATUS_STPM_UART_LINK_CRC_ERROR,
  STATUS_STPM_UART_LINK_TIME_OUT_ERROR,
  STATUS_STPM_UART_LINK_FRAME_ERROR,
  STATUS_STPM_UART_LINK_NOISE_ERROR,
  STATUS_STPM_UART_LINK_RX_OVERRUN,
  STATUS_STPM_UART_LINK_TX_OVERRUN,    
  STATUS_STPM_SPI_LINK_RX_FULL,
  STATUS_STPM_SPI_LINK_TX_EMPTY,
  STATUS_STPM_LINK_READ_ERROR,
  STATUS_STPM_LINK_WRITE_ERROR,
  STATUS_STPM_SPI_LINK_CRC_ERROR,
  STATUS_STPM_SPI_LINK_UNDERRUN,
  STATUS_STPM_SPI_LINK_OVERRRUN,
 }METRO_STPM_LINK_IRQ_Status_Type_t;
  
 /**
  * @brief METROLOGY  Boolean  type
  *
  */  
typedef enum 
{
  BOOL_FALSE = 0,
  BOOL_TRUE  
}METRO_Bool_Type_t;
  
 /**
  * @brief METROLOGY External device Number
  *
  */  
   
typedef enum 
{
  HOST = 0,  
  EXT1,  
  NB_MAX_DEVICE,
}METRO_NB_Device_t;  

 /**
  * @brief METROLOGY  CHANNEL definition
  *
  */  
   
typedef enum 
{
  CHANNEL_NONE=0,
  CHANNEL_1,  
  CHANNEL_2,
  NB_MAX_CHANNEL  
}METRO_Channel_t; 

typedef enum 
{
  INT_NONE_CHANNEL=0,
  INT_CHANNEL_1,  
  INT_CHANNEL_2,
  CHANNEL_TAMPER
}METRO_internal_Channel_t; 



 /**
  * @brief METROLOGY hardware Device type
  *
  */
     
typedef enum 
{
  Device_NONE=0,
  STM32 = 5,
  STPM32 = 6,                           
  STPM33,                            
  STPM34,
  NB_MAX_STPM
}METRO_Device_t;


/* Struct to define communication between STM32 and STPMs chips */
typedef struct
{
  uint8_t            rxData;
  uint8_t            txData;
  uint8_t            txValid;
  uint8_t            rxValid;
  uint8_t            txOngoing;
  uint8_t            rxOngoing;  
  uint8_t            *pTxReadBuf;
  uint8_t            *pTxWriteBuf;
  uint8_t            *pRxReadBuf;
  uint8_t            *pRxWriteBuf;
} STPM_Com_t;


/* Struct to define communication pin and  port between STM32 and STPMs chips */

typedef struct
{
#ifdef UART_XFER_STPM3X   
  USART_TypeDef*  uart;
#endif 
#ifdef SPI_XFER_STPM3X
  SPI_TypeDef*    spi;
#endif  
  GPIO_TypeDef*   cs_port;
  uint16_t           cs_pin;
  GPIO_TypeDef*   syn_port;
  uint16_t           syn_pin;
  GPIO_TypeDef*   en_port;
  uint16_t           en_pin;
} STPM_Com_port_t;


/**
  * @brief METROLOGY Mapping Channels ( 1 to 4 ) to real V and C chip channels 
  * according to the Device
  *  Put NONE_CHANNEL if the channel is not mapped oterhwise  CHANNEL_1, CHANNEL_2, CHANNEL_3, CHANNEL_4   */


typedef struct
{
  METRO_Device_t              device;      
  uint8_t                     channels_mask;
  uint32_t                    factor_power_int_ch1;
  uint32_t                    factor_energy_int_ch1;
  uint32_t                    factor_power_int_ch2;
  uint32_t                    factor_energy_int_ch2;
  uint32_t                    factor_voltage_int_ch1;
  uint32_t                    factor_current_int_ch1;
  uint32_t                    factor_voltage_int_ch2;
  uint32_t                    factor_current_int_ch2;
  METRO_Latch_Device_Type_t   latch_device_type;  
  STPM_Com_t                  STPM_com;
  STPM_Com_port_t             STPM_com_port;
  METRO_STPM_TypeDef          metro_stpm_reg;
}METRO_Device_Config_t;



typedef struct
{
  int32_t       energy[NB_MAX_CHANNEL][NB_MAX_TYPE_NRJ];
  int32_t       energy_extension[NB_MAX_CHANNEL][NB_MAX_TYPE_NRJ];
}METRO_Data_Energy_t;


#define    CHANNEL_MASK_CONF_CHANNEL_1     0x01
#define    CHANNEL_MASK_CONF_CHANNEL_2     0x02
#define    CHANNEL_MASK_CONF_CHANNEL_3     0x04
#define    CHANNEL_MASK_CONF_CHANNEL_4     0x08
  
#define    NB_NAX_CHANNEL                   3
 
#define    DEVICE_MASK_CONF                0x0F
#define    CHANNEL_MASK_CONF               0xF0

/* ------------------------------------------------------------------------------------------------------------------*/
/* -------------------------------------  Exported functions --------------------------------------------------------*/
/* ------------------------------------------------------------------------------------------------------------------*/

/****************/
/* Device Level */
/****************/

/* Initialization and Setup functions *********************************/
void Metro_Init(void);
void Metro_power_up_device(void);

#ifdef UART_XFER_STPM3X /* UART MODE */ 
void Metro_UartSpeed(uint32_t baudrate);
#endif

void Metro_Config_Reset(METRO_ResetType_t in_MetroResetType);
void Metro_Set_Hardware_Factors(METRO_Channel_t in_Metro_Channel, uint32_t in_Factor_Power,uint32_t in_Factor_Nrj,uint32_t in_Factor_Voltage,uint32_t in_Factor_Current);

/* set metrology Config */
uint8_t Metro_Setup(uint32_t in_stpm_config);

/* Get setup Metrology */
uint8_t Metro_Get_Setup(uint32_t * out_p_stpm_config);

uint8_t Metro_ApplyConfig(uint32_t in_stpm_config, uint32_t in_stpm_data);
uint8_t Metro_Get_Data_device(METRO_NB_Device_t in_Metro_Device);

/* Set / Get Latch the device registers according to the latch type selection driving SYN pin  */
/* or setting auto-latch by S/W Auto Latch bit */
/* Latch_Type : SYN_SCS, SW, AUTO */

uint8_t Metro_Set_Latch_device_type(METRO_NB_Device_t in_Metro_Device, METRO_Latch_Device_Type_t in_Metro_Latch_Device_Type);
uint8_t Metro_Register_Latch_device_Config_type(METRO_NB_Device_t in_Metro_Device, METRO_Latch_Device_Type_t in_Metro_Latch_Device_Type);

/* Read energy */
/* in_Metro_energy_Selection : W_ACTIVE , F_ACTIVE, REACTIVE, APPARENT */
int32_t Metro_Read_energy(METRO_Channel_t in_Metro_Channel,METRO_Energy_selection_t in_Metro_Energy_Selection);

/* Read Power */
/* in_Metro_Power_Selection : W_ACTIVE , F_ACTIVE, REACTIVE, APPARENT_RMS, APPARENT_VEC, MOM_WIDE_ACT, MOM_FUND_ACT */
int32_t Metro_Read_Power(METRO_Channel_t in_Metro_Channel,METRO_Power_selection_t in_Metro_Power_Selection);

/* Read RMS */
/* in_RAW_vs_RMS : 0 : Raw values from registers requestest at output, 1 : RMS values in mV or mA requested at output */
void Metro_Read_RMS(METRO_Channel_t in_Metro_Channel,uint32_t * out_Metro_RMS_voltage,uint32_t * out_Metro_RMS_current, uint8_t in_RAW_vs_RMS);

/* Read Phase */
int32_t Metro_Read_PHI(METRO_Channel_t in_Metro_Channel);

/* Read Period */
uint16_t Metro_Read_Period(METRO_Channel_t in_Metro_Channel);

/* Read / Write data block from Device ( Reg access to External STPM from UART/SPI */
/*********************************************************************************************************/
uint8_t Metro_Read_Block_From_Device ( METRO_NB_Device_t in_Metro_Device_Id, uint8_t in_Metro_Device_Offset_Adress, uint8_t in_Metro_Nb_of_32b_Reg, uint32_t *p_buffer );
uint8_t Metro_Write_Block_to_Device ( METRO_NB_Device_t in_Metro_Device_Id, uint8_t in_Metro_Device_Offset_Adress, uint8_t in_Metro_Nb_of_32b_Reg, uint32_t *in_p_buffer );

#ifdef __cplusplus
}
#endif

#endif /* __METROLOGY_H */

/**
  * @}
  */

/**
  * @}
  */

/************************ (C) COPYRIGHT STMicroelectronics *****END OF FILE****/
