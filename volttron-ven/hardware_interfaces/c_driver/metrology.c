/**
  ******************************************************************************
  * @file    metrology.c
  * @author  AMG/IPC Application Team
  * @brief   This file provides all the Metrology firmware functions.
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
#include "metrology.h"
#include "metrology_hal.h"
#include <stdint.h>


/** @defgroup Metrology
  * @brief Metrology driver modules
  * @{
  */

/* Private typedef -----------------------------------------------------------*/




/* Private define ------------------------------------------------------------*/
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
/* Private function prototypes -----------------------------------------------*/


/* Global variables ----------------------------------------------------------*/
METRO_Device_Config_t Tab_METRO_internal_Devices_Config[NB_MAX_DEVICE];
METRO_Data_Energy_t METRO_Data;



/*===============================================================================
                Private  functions
===============================================================================*/


/** @defgroup Metrology_Group1 Initialization and Configuration functions
*  @brief   Initialization and Configuration functions
*
@verbatim
===============================================================================
                Initialization and Configuration functions
===============================================================================

This section provides a set of functions allowing to initialize the Metrology
Peripherals.

@endverbatim
* @{
*/

/**
  * @brief  Initialize the Metrology peripheral registers to their default
  *         reset values.
  * @param[in]   None
  * @retval None
  */
void Metro_Init(void)
{
   /* Ask HAL to initilisase the METROLOGY part (Metrology Block for int and ext if necessary) ( Clocks, ..) */

  if(Tab_METRO_internal_Devices_Config[EXT1].device != 0)
  {
    Metro_HAL_init_device(EXT1);
  }
}

/**
  * @brief  Initialize the Metrology peripheral registers to their default
  *         reset values.
  * @param[in]   None
  * @retval None
  */
void Metro_power_up_device(void)
{
   /* Ask HAL to enable the METROLOGY part with the right CSS level */

  if(Tab_METRO_internal_Devices_Config[EXT1].device != 0)
  {
    Metro_HAL_power_up_device(EXT1);
  }
}

/**
  * @brief  Resets the Metrology peripherals
  * @param[in]   in_MetroResetType : Reset type  RESET_SYN_SCS = 1, RESET_SW = 2
  * @retval None
  */
void Metro_Config_Reset(METRO_ResetType_t in_MetroResetType)
{

  /* Set the reset in each Metrology chip if necessary */

  if(Tab_METRO_internal_Devices_Config[EXT1].device != 0)
  {
    Metro_HAL_reset_device(in_MetroResetType, EXT1);
  }

}

#ifdef UART_XFER_STPM3X /* UART MODE */ 
/**
  * @brief  Initialize the Metrology peripheral registers to their default
  *         reset values.
  * @param[in]   None
  * @retval None
  */
void Metro_UartSpeed(uint32_t baudrate)
{
   /* Ask HAL to initilisase the METROLOGY part (Metrology Block for int and ext if necessary) ( Clocks, ..) */

  if(Tab_METRO_internal_Devices_Config[EXT1].device != 0)
  {
    Metro_HAL_baudrate_set(EXT1,baudrate);
    Metro_HAL_baudrate_set(HOST,baudrate);
  }
}

#endif

/**
  * @brief  set metrology Config
  * @param[in]   in_stpm_config : STPM  topology config
  * @retval u8
  */


        /******************/
        /* in_stpm_config */
        /******************/
       /*+------------------------------------------------------------------------------------+
         |                                        U32                                         |
         |---------------------|-------------------|-------------------|----------------------|
         |     STPM EXT4       |     STPM EXT3     |     STPM EXT2     |     STPM EXT1        |
         |---------------------|-------------------|-------------------|----------------------|
         |    u4   |     u4    |   u4    |   u4    |     u4  |     u4  |      u4   |  u4      |
         |---------|-----------|--------------------------------------------------------------|
         |CH masks | STPM type |CH masks |STPM type|CH masks |STPM type|  CH masks |STPM type |
         |---------|-----------|--------------------------------------------------------------|

        STPM CFG EXTx (u8):
        -----------------
        MSB u4 : Channel  Mask :  Channels affected to STPM
            0 : No Channel affected
            1 : Channel 1 affected
            2 : Channel 2 affected
            4 : Channel 3 affected
            8 : Channel 4 affected

        LSB u4 :  STPM type : 6 to 8
            0 : No STPM
            6 : STPM32
            7 : STPM33
            8 : STPM34

        EX : STPM EXT 1: One STPM34 with Channels 2 and 3 affected on it
        LSB u4 = 8 (STPM34)
        MSB u4 = 6 ( 4:Channel 3 + 2:Channel 2)

        STPM CONFIG : U32 = 0x00000068

        +------------------------------------------------------------------------------------+*/

/* set metrology Config  */
uint8_t Metro_Setup(uint32_t in_stpm_config)
{

   /* Get STPM devices types and channels config  for STPM */
   Tab_METRO_internal_Devices_Config[EXT1].device   = (METRO_Device_t)(in_stpm_config&0x0000000F);
   Tab_METRO_internal_Devices_Config[EXT1].channels_mask = (uint8_t)(((in_stpm_config)&0x000000F0)>>4);

  /* Send Config to HAL */
  Metro_HAL_Setup((METRO_Device_Config_t *) &Tab_METRO_internal_Devices_Config);

  return 0;

}

/**
  * @brief  Get metrology Config
  * @param[out]   out_p_stpm_config : STPM  topology config
  * @retval u8
  */
/* set metrology Config  */
uint8_t Metro_Get_Setup(uint32_t * out_p_stpm_config)
{

   /* Get STPM devices types and channels config  for each Ext1 STPM*/
   *out_p_stpm_config  = (uint32_t)Tab_METRO_internal_Devices_Config[EXT1].device;
   *out_p_stpm_config |= (uint32_t)(Tab_METRO_internal_Devices_Config[EXT1].channels_mask<<4);

  return 0;
}

/**
  * @brief  Set the config to STPM and read back
  * @param[out]   none
  * @retval u8
  */
/* set metrology Config  */
uint8_t Metro_ApplyConfig(uint32_t in_stpm_config, uint32_t in_stpm_data)
{
  if ((in_stpm_config & 0x0000000F) != 0)
  {
    /* Check if Config device inside RAM can permit access to EXT chip */
    if ( Tab_METRO_internal_Devices_Config[EXT1].device > 0)
    {  
    /* write configuration into STPM */
    Metro_Write_Block_to_Device(EXT1, 0, 19, (uint32_t*)in_stpm_data);
  
    /* Read back configuration to show the read block access */
    Metro_Read_Block_From_Device(EXT1, 0, 19, (uint32_t *)&Tab_METRO_internal_Devices_Config[EXT1].metro_stpm_reg);    
    }
  }

  return 0;

}


/**
  * @brief       set Power and NRJ factors depending of hardware for Channel 1, 2
  * @param[in]   in_Metro_Channel (Channel ID), Channel 1, 2
  * @param[in]   in_Factor_Power : Power factor depending of hardware part sensor in W/LSB
  * @param[in]   in_Factor_Nrj   : Enargy factor depending of hardware part sensor in Wh/LSB
  * @param[in]   in_Factor_Voltage : Voltage factor depending of hardware part sensor in W/LSB
  * @param[in]   in_Factor_Current   : Current factor depending of hardware part sensor in Wh/LSB
  * @retval     None

  // Parameters used for Power factor and NRJ factors calculation to help the user of this function

  #define DPOW         //  NB bits of Internal Regs
  #define CALIB_V      // Default Voltage Calibration value
  #define CALIB_I      // Default Current Calibration value
  #define KINT         // Integrator gain : used only for rogowski
  #define R1           // External resistor for ADC
  #define R2           // External Resistor for ADC
  #define AU           //( ADC Voltage Gain )
  #define AI           // (ADC Current Gain )
  #define VREF         //( ADC vref)
  #define KSI          // Sensivity of Captor
  #define F_XTAL       // frenquency of the Main Clock


  // EX  values for a shunt in Comet board
  #define DPOW        (268435456.0)   // put 2^28 for 28 bits
  #define CALIB_V      (0.875)  //default Calibration value (Middle value)
  #define CALIB_I      (0.875) //default Calibration value (Midle Value)
  #define KINT        (0.8155773)         // this value is used only for rogowski,  otherwise = 1
  #define R1          (780000.0)  // External resistor for ADC
  #define R2          (470.0)    // External Resistor for ADC
  #define AU          (2.0)   //( ADC Voltage Gain )
  #define AI          (2.0)   // (ADC Current Gain )
  #define VREF        (1.18)  //( ADC vref)
  #define KSI         (0.00218)    // Value for a shunt KSI = RShunt in ohms
  #define F_XTAL      (16000000.0)  // frenquency of the Main Clock



KSI = RShunt  (For shunt)
KSI =  Rb/N  (For a VAC T60404-E4626-X002) : Rb = 6.8 ohms for Comet board  and N = 2500 Nb spires of CT -> KSI = 0.00272) theoric
KSI = K_RoCoil (For Rogowski Coil)


  // FORMULAS
**************

with shunt or current transformer
---------------------------------

  power factor = VREF * VREF * (1 + (R1 / R2)) /
            (AU * AI * KSI * CALIB_V * CALIB_I * DPOW);

So for the factor calculation, remove dpow (2^28) to have keep  precision.
The Read power and nrj functions will make a shift of 28 bits before to send the result.

our case with a CT in comet board
----------------------------------
KSI =  Rb/N  (For a VAC T60404-E4626-X002) : Rb = 6.8 ohms for Comet board  and N = 2500 Nb spires of CT -> KSI = 0.00272) theoric

power factor  = (1,18 *1,18 * (1+ (780000/470)) / (2 * 2 * 0,00272  * 0,875 * 0,875) =  277573,09

our case with a CT in STPM34 board
----------------------------------
KSI =  Rb/N  (For a VAC T60404-E4626-X002) : Rb = 6.5 ohms for STPM board board  and N = 2500 Nb spires of CT -> KSI = 0.00240) theoric

power factor  = (1,18 *1,18 * (1+ (810000/470)) / (2 * 2 * 0,00260  * 0,875 * 0,875) =  301546,05



it is not necessary to calculate the NRJ factor when you have already calculated the power factor.
It is always the same ration between Power and NRJ

Our case FACTOR_POWER_ON_ENERGY      (858)   ->  (3600 * 16000000 / 0x4000000) = 858.3...


However  there is the formula below :

energy  = reg * VREF * VREF * (1 + R1 / R2) /
              (3600 * (1<<17) * CALIB_V * CALIB_I * AI * AU * KSI * (F_XTAL / 2048));

With Rogowski ( KINT added inside the formulas)
-------------------------------------------------

  power = reg * VREF * VREF * (1 + (R1 / R2)) /
            (KINT * AU * AI * KSI * DPOW * CALIB_V * CALIB_I);

  energy  = reg * VREF * VREF  *(1 + R1 / R2) /
              (3600 * (1<<17) * KINT * CALIB_V * CALIB_I * AI * AU * KSI * (F_XTAL / 2048));


for STPM34  with CT :
--------------------

   V factor = VREF * (1 + (R1 / R2)) / (AU * CALIB_V * DPOW)
                = (1.18 * (1+ (810000/470))) / ( 2 * 0,875) = 116274,11


Power factor  = 301546,05

Ratio PF / VF = 301546,05 / 116274,11 = 2,5934

DPOW is 2^23 for Momentary values 


for STPM34  with CT :
--------------------

   I factor = VREF  / (AI * CALIB_I * DPOW * KSI * KINT ) = 
               = 1.18  / (2 * 0,875 * 0,00260 * 1)   = 25934,06

Power factor  = 301546,05
Ration PF /IF = 301546,05 / 25934,06 =  11,6274

DPOW is 2^23 for Momentary values  
*/
void Metro_Set_Hardware_Factors(METRO_Channel_t in_Metro_Channel, uint32_t in_Factor_Power,uint32_t in_Factor_Nrj,uint32_t in_Factor_Voltage,uint32_t in_Factor_Current)
{

  /* Copy Factor NRJ and Factor Power inside strcut of device to correct internal Channel */
  if (in_Metro_Channel == CHANNEL_1)
  {
    Tab_METRO_internal_Devices_Config[EXT1].factor_power_int_ch1 = in_Factor_Power;
    Tab_METRO_internal_Devices_Config[EXT1].factor_energy_int_ch1 = in_Factor_Nrj;
    Tab_METRO_internal_Devices_Config[EXT1].factor_voltage_int_ch1 = in_Factor_Voltage;
    Tab_METRO_internal_Devices_Config[EXT1].factor_current_int_ch1 = in_Factor_Current;
  }
  else if (in_Metro_Channel == CHANNEL_2)
  {
    Tab_METRO_internal_Devices_Config[EXT1].factor_power_int_ch2 = in_Factor_Power;
    Tab_METRO_internal_Devices_Config[EXT1].factor_energy_int_ch2 = in_Factor_Nrj;
    Tab_METRO_internal_Devices_Config[EXT1].factor_voltage_int_ch2 = in_Factor_Voltage;
    Tab_METRO_internal_Devices_Config[EXT1].factor_current_int_ch2 = in_Factor_Current;
  }

}


/**
  * @brief  Get a block of registers from a device (Internal or external Metro Chip)
  * @param[in]   in_Metro_Device (Device ID ) EXT1 to EXT4
  * @param[in]   in_Metro_Device_Offset_Adress : Offset Address
  * @param[in]   in_Metro_Nb_of_32b_Reg : NB U32 to read
  * @param[out]   p_buffer : Output buffer filled with read data
* @retval U8 : 0 : Return OK, -1 Error
  */
uint8_t Metro_Read_Block_From_Device ( METRO_NB_Device_t in_Metro_Device_Id, uint8_t in_Metro_Device_Offset_Adress, uint8_t in_Metro_Nb_of_32b_Reg, uint32_t *p_buffer )
{
  uint8_t error =0 ;

  error = Metrology_HAL_ReadBlock(in_Metro_Device_Id, in_Metro_Device_Offset_Adress, in_Metro_Nb_of_32b_Reg, p_buffer);

  return error;
}
/**
  * @brief  Write a block of registers from a device ( Internal or external Metro Chip)
  * @param[in]   in_Metro_Device (Device ID ) EXT1 to EXT4
  * @param[in]   in_Metro_Device_Offset_Adress : Offset Address
  * @param[in]   in_Metro_Nb_of_32b_Reg : NB U32 to write
  * @param[in]   in_p_buffer : Buffer data to write
  * @param[out]  None
* @retval U8 : 0 : Return OK, -1 Error
  */
uint8_t Metro_Write_Block_to_Device(METRO_NB_Device_t in_Metro_Device_Id, uint8_t in_Metro_Device_Offset_Adress, uint8_t in_Metro_Nb_of_32b_Reg, uint32_t *in_p_buffer )
{
 uint8_t error =0 ;

  error = Metrology_HAL_WriteBlock(in_Metro_Device_Id, in_Metro_Device_Offset_Adress, in_Metro_Nb_of_32b_Reg, in_p_buffer);

  return error;
}

/**
  * @brief  Get DSP data inside the device
  * @param[in]   in_Metro_Device (Device ID ), EXT1 to EXT4
  * @param[out]  None
  * @retval     0 : Return OK, -1 Error
  */

uint8_t Metro_Get_Data_device(METRO_NB_Device_t in_Metro_Device)
{

  /* Get DSP data inside the Metrology chip requested  */
  if (in_Metro_Device < (NB_MAX_DEVICE))
  {
    Metro_HAL_Get_Data_device(in_Metro_Device);
  }

  return 0;

}

/**
  * @brief  Set Latch the device type (according to the latch type selection driving SYN pin)
  * or setting auto-latch by S/W Auto Latch bit,
  * @param[in]   in_Metro_Device (Device ID ), HOST or EXT1 to EXT4
  * @param[in]   in_Metro_Latch_Device_Type :Latch_Type : SYN_SCS, SW, AUTO
  * @param[out]  None
  * @retval     0 : Return OK, -1 Error
  */

uint8_t Metro_Set_Latch_device_type(METRO_NB_Device_t in_Metro_Device, METRO_Latch_Device_Type_t in_Metro_Latch_Device_Type)
{

  /* Set latch type  in the Metrology chip requested  */
  if (in_Metro_Device < NB_MAX_DEVICE)
  {
    Metro_HAL_Set_Latch_device_type(in_Metro_Device, in_Metro_Latch_Device_Type);
  }

  return 0;

}

/**
  * @brief  Save Latch device type 
  * @param[in]   in_Metro_Device (Device ID )EXT1 to EXT4
  * @param[in]   in_Metro_Latch_Device_Type :Latch_Type : SYN_SCS, SW, AUTO
  * @param[out]  None
  * @retval     0 : Return OK, -1 Error
  */
uint8_t Metro_Register_Latch_device_Config_type(METRO_NB_Device_t in_Metro_Device, METRO_Latch_Device_Type_t in_Metro_Latch_Device_Type)
{

   /* Save latch config inside internal Metro struct */
   Tab_METRO_internal_Devices_Config[in_Metro_Device].latch_device_type = in_Metro_Latch_Device_Type;
   
   return 0;
}


/**
  * @brief  : Read period for the selected channel.
  * @param[in]   in_Metro_Channel (Channel ID ), CHANNEL_1 to to CHANNEL_4
  * @param[out]  None
  * @retval U16 :  :Return Period in 탎
  */

/* Read period for the selected channel. LSB is 8uSec. */
uint16_t Metro_Read_Period(METRO_Channel_t in_Metro_Channel)
{
  METRO_internal_Channel_t int_Channel;
  METRO_NB_Device_t        Device;
  uint16_t period =0;

  /* Get Device id from Channel to request the value from the good device */
  Device = EXT1;

  /* Get if the channel requested is the one or the two */
  int_Channel =  (METRO_internal_Channel_t) in_Metro_Channel;

  /* Get period according to device and channel */
  period = Metro_HAL_read_period(Device,int_Channel);
  
  /* LSB is 8 탎, so multiply by 8 to have the value in 탎 */
  period = period * 8 ;

  return period;
}

/**
  * @brief      This function Read Power according to the selected type for the given channel
  * @param[in]   in_Metro_Channel (Channel ID ), CHANNEL_1 to CHANNEL_4
  * @param[in]   in_Metro_Power_Selection : W_ACTIVE , F_ACTIVE, REACTIVE, APPARENT_RMS, APPARENT_VEC, MOM_WIDE_ACT, MOM_FUND_ACT
  * @param[out]  None
  * @retval     Return power value in  in mW  , mVAR  or mVA ... 
  */
int32_t Metro_Read_Power(METRO_Channel_t in_Metro_Channel,METRO_Power_selection_t in_Metro_Power_Selection)
{
  METRO_internal_Channel_t int_Channel;
  METRO_NB_Device_t        Device;
  int64_t calc_power = 0;
  int32_t raw_power = 0;

  /* Get Device id from Channel */
  Device = EXT1;

  /* Get if the channel requested is the one or the two of the device */
  int_Channel =(METRO_internal_Channel_t) in_Metro_Channel;

  /* Get raw power according to device and channel */
  raw_power = Metro_HAL_read_power(Device,int_Channel,in_Metro_Power_Selection);

 /* Calc real power  */
  if (int_Channel == INT_CHANNEL_1)
  {
   calc_power =  (int64_t)raw_power * Tab_METRO_internal_Devices_Config[Device].factor_power_int_ch1;
  }
  else if (int_Channel == INT_CHANNEL_2)
  {
    calc_power = (int64_t)raw_power * Tab_METRO_internal_Devices_Config[Device].factor_power_int_ch2;
  }
 
  /* multiply by 10 to have in milli- */
  calc_power *= 10; 
  
  /* Shift calcul result to 28 bits ( resolution of Reg inside metrology block)*/
  calc_power >>= 28;

  /* return power selection calculated with Factor Power */
  return ((int32_t)calc_power);
}


/**
  * @brief      This function Read Energy according to the selected type for the given channel
  * @param[in]   in_Metro_Channel (Channel ID), CHANNEL_1 to CHANNEL_2
  * @param[in]   in_Metro_energy_Selection : W_ACTIVE , F_ACTIVE, REACTIVE, APPARENT
  * @param[out]  None
  * @retval     Return NRJ value in mWh , mVARh  or mVAh ...  
  */
int32_t Metro_Read_energy(METRO_Channel_t in_Metro_Channel,METRO_Energy_selection_t in_Metro_Energy_Selection)
{
  METRO_internal_Channel_t int_Channel;
  METRO_NB_Device_t        Device;
  int64_t calc_nrj = 0;
  uint32_t raw_nrj = 0;

  /* Get Device id from Channel */
  Device = EXT1;

  /* Get if the channel requested is the one or the two of the device */
  int_Channel =(METRO_internal_Channel_t) in_Metro_Channel;
    
  /* Get raw nrj according to device, channel and NRJ type */
  raw_nrj = Metro_HAL_read_energy(Device,int_Channel,in_Metro_Energy_Selection);

  /* manage the 2 U32 to have enougth place to save energy cumulated */
  /* Make sure between two reads inside hardware registers if we have to add carry inside ext U32 */
  if (((uint32_t)(METRO_Data.energy[in_Metro_Channel][in_Metro_Energy_Selection])) > 0xA0000000  && (((uint32_t)raw_nrj) < 0x60000000))
  {
    METRO_Data.energy_extension[in_Metro_Channel][in_Metro_Energy_Selection] ++;
  }
  if (((uint32_t)(METRO_Data.energy[in_Metro_Channel][in_Metro_Energy_Selection])) < 0x60000000 && (((uint32_t)raw_nrj) > 0xA0000000))
  {
    METRO_Data.energy_extension[in_Metro_Channel][in_Metro_Energy_Selection] --;
  }

  /* save the new result cumulated come from register inside internal structure */
  METRO_Data.energy[in_Metro_Channel][in_Metro_Energy_Selection] = raw_nrj;

  /* calculate the nrj value and add the 32 bits extension */
  calc_nrj = (uint64_t)raw_nrj + ((int64_t)METRO_Data.energy_extension[in_Metro_Channel][in_Metro_Energy_Selection] << 32);

   /* Apply Energy factors  */
  if (int_Channel == INT_CHANNEL_1)
  {
   calc_nrj *= (int64_t)Tab_METRO_internal_Devices_Config[Device].factor_energy_int_ch1;
  }
  else if (int_Channel == INT_CHANNEL_2)
  {
    calc_nrj *= (int64_t)Tab_METRO_internal_Devices_Config[Device].factor_energy_int_ch2;
  }

  /* multiply by 10 to have in milli- */
  calc_nrj *= 10;
  
  /* Put the result in 32 bits format */
  calc_nrj >>= 32;

  /* return the nrj value */
  return((int32_t)calc_nrj);

}

/**
  * @brief      This function read RMS values of both voltage and current for the selected channel
  * @param[in]   in_Metro_Channel (Channel ID ), CHANNEL_1 to CHANNEL_3 ( Channel 4 is excluded because is TAMPER )
  * @param[in]   in_RAW_vs_RMS : 0 : Raw values from registers requestest at output, 1 : RMS values in mV or mA requested at output
  * @param[out]  out_Metro_RMS_voltage , out_Metro_RMS_current ( in mV and mA) or RAW values from registers
   * @retval     None


for STPM34  with CT :
--------------------

   V factor = VREF * (1 + (R1 / R2)) / (AU * CALIB_V * DPOW)
                = (1.18 * (1+ (810000/470))) / ( 2 * 0,875) = 116274,11

   I factor = VREF  / (AI * CALIB_I * DPOW * KSI * KINT ) = 
               = 1.18  / (2 * 0,875 * 0,00260 * 1)   = 25934,06

Power factor  = 301546,05
DPOW is 2^15 for RMS values
  */

void Metro_Read_RMS(METRO_Channel_t in_Metro_Channel,uint32_t * out_Metro_RMS_voltage,uint32_t * out_Metro_RMS_current, uint8_t in_RAW_vs_RMS)
{
  METRO_internal_Channel_t int_Channel;
  METRO_NB_Device_t        Device;
  uint32_t raw_RMS_Voltage = 0;
  uint64_t calc_RMS_Voltage = 0;
  uint32_t raw_RMS_Current = 0;
  uint64_t calc_RMS_Current = 0;
  uint32_t Factor_Voltage = 0;
  uint32_t Factor_Current = 0;

  /* Get Device id from Channel */
  Device = EXT1;

  /* Get if the channel requested is the one or the two of the device */
  int_Channel =(METRO_internal_Channel_t) in_Metro_Channel;

  /* Get raw RMS voltage according to device and channel */
  raw_RMS_Voltage = Metro_HAL_read_RMS_Voltage(Device,int_Channel);
  
  /* Get RAW RMS current according to device and channel */
  raw_RMS_Current = Metro_HAL_read_RMS_Current(Device,int_Channel);

  /* gat Voltage and current factors to calculate the RMS values */
  if (int_Channel == INT_CHANNEL_1)
  {
    Factor_Voltage = Tab_METRO_internal_Devices_Config[Device].factor_voltage_int_ch1;
    Factor_Current = Tab_METRO_internal_Devices_Config[Device].factor_current_int_ch1;
  }
  else 
  {
    Factor_Voltage = Tab_METRO_internal_Devices_Config[Device].factor_voltage_int_ch2;
    Factor_Current = Tab_METRO_internal_Devices_Config[Device].factor_current_int_ch2;       
  }

  /* Calculate real values with factors */
  calc_RMS_Voltage = (uint64_t)raw_RMS_Voltage * Factor_Voltage;
  calc_RMS_Current = (uint64_t)raw_RMS_Current * Factor_Current;
  
    /* Multiply  by 10 to have in milli  */
  calc_RMS_Voltage *= 10;
  calc_RMS_Current *= 10;
 
  /* Shift calcul result to 15 bits ( resolution of Reg inside metrology block)*/
  calc_RMS_Voltage >>= 15;

  calc_RMS_Current >>= 17; // 17 bits resolution revBC 
  
  /* if Raw type requested , return registers otherwise return calc values in mV and mA RMS */
  if (in_RAW_vs_RMS == 0)
  {
    /* Return RAW values from registers to ouput  */
    *out_Metro_RMS_voltage = raw_RMS_Voltage;
    *out_Metro_RMS_current = raw_RMS_Current;
  }
  else if (in_RAW_vs_RMS == 1)
  {  
  /* Return values to ouput params in mV and mA */
  *out_Metro_RMS_voltage = (uint32_t)calc_RMS_Voltage;
  *out_Metro_RMS_current = (uint32_t)calc_RMS_Current;
  }

}

/**
  * @brief      This function Read the phase angle between voltage and current for the selected channel
  * @param[in]   in_Metro_Channel (Channel ID ), CHANNEL_1 to CHANNEL_3 ( Channel 4 is excluded =  TAMPER )
  * @param[out]  None
   * @retval     Return S32 , PHI angle in degree for given channel
  */
int32_t Metro_Read_PHI(METRO_Channel_t in_Metro_Channel)
{
  METRO_internal_Channel_t int_Channel;
  METRO_NB_Device_t        Device;
  int32_t raw_phi = 0;
  int32_t Calc_phi = 0;
  uint16_t period = 0;
  
  /* Get period of signal , return is in 탎 */
   period = Metro_Read_Period(in_Metro_Channel);

  /* Get Device id from Channel */
  Device = EXT1;

  /* Get if the channel requested is the one or the two of the device */
  int_Channel =(METRO_internal_Channel_t) in_Metro_Channel;

  /* Get raw PHI according to device and channel */
  raw_phi = Metro_HAL_read_PHI(Device,int_Channel);

 /* Calc real PHI according to signal period and frequency of metro block  */
 /* phase angle = Calc_phi *f*360/Fclk */
   Calc_phi = (int64_t) ((raw_phi * 2880) / period);

  /* return Phase angle in degree calculated  */
  return ((int32_t)Calc_phi);    
}

/************************ (C) COPYRIGHT STMicroelectronics *****END OF FILE****/