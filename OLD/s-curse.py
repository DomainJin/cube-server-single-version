/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2025 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "stm32f1xx_hal_uart.h"
#include "math.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */
typedef enum {
    RAMP_UP,
    CRUISE,
    RAMP_DOWN,
    REVERSE_WAIT,
    STOP
} RampState;
/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define SLOT_FREQ 20000 // tần số timer interrupt
#define STEPPER_PORT GPIOA
#define STEPPER_PIN GPIO_PIN_0
#define DIR_PIN GPIO_PIN_1

#define DMX_CHANNELS 512
uint8_t dmx_data[DMX_CHANNELS + 1];
volatile uint16_t dmx_index = 0;
volatile uint8_t dmx_new_frame = 0;

// --- Thông số động cơ ---
#define STEP_RESOLUTION   3200     // xung/vòng
#define FREQ_MAX          10000    // tần số xung cực đại (Hz)
#define ACCEL_TIME        3.0f     // thời gian tăng/giảm tốc mặc định (giây)
#define SLOT_FREQ         20000    // tần số ngắt timer (Hz)

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */
UART_HandleTypeDef huart1;
/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
TIM_HandleTypeDef htim1;
UART_HandleTypeDef huart1;
DMA_HandleTypeDef hdma_usart1_rx;

volatile uint32_t pulse_count = 0;
volatile uint8_t stepper_enabled = 0;
volatile uint32_t pulse_per_second = 0;
volatile uint32_t bresenham_error = 0;
volatile uint8_t state = 0;

float accel = 0;
float t_ramp = ACCEL_TIME;
uint32_t steps_total = 0;
float S_ramp = 0;
uint32_t steps_cruise = 0;

volatile int8_t current_direction = 1; // 1: thuận, -1: nghịch
volatile int8_t target_direction = 1;
volatile RampState ramp_state = STOP;

/* USER CODE BEGIN PV */
// Gọi khi muốn đảo chiều
void stepper_reverse() {
    if (stepper_enabled && current_direction != target_direction) {
        // Nếu đang chạy, chuyển sang trạng thái ramp_down để dừng lại
        ramp_state = RAMP_DOWN;
    }
}

// Hàm gọi khi bắt đầu chạy
void stepper_move(uint32_t steps_input, int8_t dir) {
    steps_total = steps_input;
    target_direction = dir;
    current_direction = dir;
    pulse_per_second = FREQ_MAX;
    accel = FREQ_MAX / ACCEL_TIME;
    S_ramp = (FREQ_MAX * FREQ_MAX) / (2.0f * accel);

    if (2 * S_ramp > steps_total) {
        pulse_per_second = sqrtf(steps_total * accel);
        S_ramp = (pulse_per_second * pulse_per_second) / (2.0f * accel);
    }
    steps_cruise = steps_total - 2 * (uint32_t)S_ramp;
    if ((int32_t)steps_cruise < 0) steps_cruise = 0;

    pulse_count = 0;
    bresenham_error = 0;
    state = 0;
    stepper_enabled = 1;
    ramp_state = RAMP_UP;
}

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_DMA_Init(void);
static void MX_TIM1_Init(void);
static void MX_USART1_UART_Init(void);
/* USER CODE BEGIN PFP */
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */



void TIM1_UP_IRQHandler(void)
{
    HAL_TIM_IRQHandler(&htim1);
}
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
	if (htim->Instance == TIM1)
	    {
	        if (!stepper_enabled) return;
	        if (pulse_count >= steps_total) {
	            stepper_enabled = 0;
	            ramp_state = STOP;
	            // Đảm bảo chân STEP luôn về LOW khi dừng
	            HAL_GPIO_WritePin(STEPPER_PORT, STEPPER_PIN, GPIO_PIN_RESET);
	            return;
	        }

	        float v = 0;
	        switch(ramp_state) {
	            case RAMP_UP:
	                if (pulse_count < S_ramp) {
	                    v = sqrtf(2 * accel * pulse_count);
	                    if (v >= pulse_per_second) {
	                        v = pulse_per_second;
	                        ramp_state = CRUISE;
	                    }
	                } else {
	                    ramp_state = CRUISE;
	                    v = pulse_per_second;
	                }
	                break;
	            case CRUISE:
	                if (pulse_count < (S_ramp + steps_cruise)) {
	                    v = pulse_per_second;
	                } else {
	                    ramp_state = RAMP_DOWN;
	                    v = sqrtf(2 * accel * (steps_total - pulse_count));
	                }
	                break;
	            case RAMP_DOWN:
	                // Tính tốc độ giảm dần
	                v = sqrtf(2 * accel * (steps_total - pulse_count));
	                // Nếu v nhỏ, không phát xung nữa (dừng thực sự)
	                if (v < 2.0f) { // 2.0f đủ lớn cho động cơ bước, có thể tùy chỉnh
	                    stepper_enabled = 0;
	                    ramp_state = STOP;
	                    HAL_GPIO_WritePin(STEPPER_PORT, STEPPER_PIN, GPIO_PIN_RESET);
	                    return;
	                }
	                break;
	            case REVERSE_WAIT:
	                // không phát xung, chờ đổi hướng xong sẽ sang RAMP_UP (đã xử lý ở trên)
	                return;
	            default:
	                return;
	        }

	        uint32_t v_int = (uint32_t)v;
	        if (v_int < 2) v_int = 2; // không phát xung quá sát khi tốc độ giảm

	        // --- Bresenham Pulse Generation ---
	        bresenham_error += v_int * 2;
	        if (bresenham_error >= SLOT_FREQ) {
	            bresenham_error -= SLOT_FREQ;
	            state ^= 1;
	            if (state == 0) {
	                pulse_count++;
	            }
	        }

	        // --- Điều khiển chân GPIO phát xung/đảo chiều ---
	        if (state == 0)
	            HAL_GPIO_WritePin(STEPPER_PORT, STEPPER_PIN, GPIO_PIN_RESET);
	        else
	            HAL_GPIO_WritePin(STEPPER_PORT, STEPPER_PIN, GPIO_PIN_SET);

	        // Đảo chiều khi cần
	        if (current_direction == 1)
	            HAL_GPIO_WritePin(STEPPER_PORT, DIR_PIN, GPIO_PIN_SET);
	        else
	            HAL_GPIO_WritePin(STEPPER_PORT, DIR_PIN, GPIO_PIN_RESET);
	    }
}

void USART1_IRQHandler(void)
{
    HAL_UART_IRQHandler(&huart1);
}


void HAL_UART_ErrorCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART1)
    {
        // Framing error = Break detected
        if (__HAL_UART_GET_FLAG(huart, UART_FLAG_FE))
        {
            dmx_index = 0; // Start of new DMX frame
            __HAL_UART_CLEAR_FEFLAG(huart);
        }
        // Restart reception
        HAL_UART_Receive_IT(huart, &dmx_data[dmx_index], 1);
    }
}

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART1)
    {
        dmx_index++;
        if (dmx_index == (DMX_CHANNELS + 1))
        {
            dmx_new_frame = 1; // Đã nhận đủ 512 kênh + start code
            dmx_index = 0;
        }
        HAL_UART_Receive_IT(huart, &dmx_data[dmx_index], 1);
    }
}

void DMX_StartReceive()
{
    dmx_index = 0;
    HAL_UART_Receive_IT(&huart1, &dmx_data[dmx_index], 1);
}
/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */
  MX_USART1_UART_Init();
  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_DMA_Init();
  MX_TIM1_Init();
  MX_USART1_UART_Init();
  /* USER CODE BEGIN 2 */
  HAL_NVIC_SetPriority(USART1_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(USART1_IRQn);
  HAL_NVIC_SetPriority(TIM1_UP_IRQn, 1, 0);
  HAL_NVIC_EnableIRQ(TIM1_UP_IRQn);
  HAL_TIM_Base_Start_IT(&htim1);
  DMX_StartReceive();

  bresenham_error = 0;

  stepper_move(32000, 1);
  HAL_Delay(5000);
  stepper_move(32000, -1);

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
	stepper_move(32000, 1);
	HAL_Delay(5000);
	stepper_move(32000, -1);
	HAL_Delay(5000);


  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL9;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief TIM1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM1_Init(void)
{

  /* USER CODE BEGIN TIM1_Init 0 */

  /* USER CODE END TIM1_Init 0 */

  TIM_ClockConfigTypeDef sClockSourceConfig = {0};
  TIM_MasterConfigTypeDef sMasterConfig = {0};

  /* USER CODE BEGIN TIM1_Init 1 */

  /* USER CODE END TIM1_Init 1 */
  htim1.Instance = TIM1;
  htim1.Init.Prescaler = 35;
  htim1.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim1.Init.Period = 99;
  htim1.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim1.Init.RepetitionCounter = 0;
  htim1.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
  if (HAL_TIM_Base_Init(&htim1) != HAL_OK)
  {
    Error_Handler();
  }
  sClockSourceConfig.ClockSource = TIM_CLOCKSOURCE_INTERNAL;
  if (HAL_TIM_ConfigClockSource(&htim1, &sClockSourceConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim1, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM1_Init 2 */

  /* USER CODE END TIM1_Init 2 */

}

/**
  * @brief USART1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART1_UART_Init(void)
{

  /* USER CODE BEGIN USART1_Init 0 */

  /* USER CODE END USART1_Init 0 */

  /* USER CODE BEGIN USART1_Init 1 */

  /* USER CODE END USART1_Init 1 */
  huart1.Instance = USART1;
  huart1.Init.BaudRate = 250000;
  huart1.Init.WordLength = UART_WORDLENGTH_8B;
  huart1.Init.StopBits = UART_STOPBITS_2;
  huart1.Init.Parity = UART_PARITY_NONE;
  huart1.Init.Mode = UART_MODE_RX;
  huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart1.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART1_Init 2 */

  /* USER CODE END USART1_Init 2 */

}

/**
  * Enable DMA controller clock
  */
static void MX_DMA_Init(void)
{

  /* DMA controller clock enable */
  __HAL_RCC_DMA1_CLK_ENABLE();

  /* DMA interrupt init */
  /* DMA1_Channel5_IRQn interrupt configuration */
  HAL_NVIC_SetPriority(DMA1_Channel5_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(DMA1_Channel5_IRQn);

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
  /* USER CODE BEGIN MX_GPIO_Init_1 */

  /* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOD_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOA, GPIO_PIN_0|GPIO_PIN_1, GPIO_PIN_RESET);

  /*Configure GPIO pin : PC13 */
  GPIO_InitStruct.Pin = GPIO_PIN_13;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);

  /*Configure GPIO pins : PA0 PA1 */
  GPIO_InitStruct.Pin = GPIO_PIN_0|GPIO_PIN_1;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /* USER CODE BEGIN MX_GPIO_Init_2 */
  GPIO_InitStruct.Pin = GPIO_PIN_10;
  GPIO_InitStruct.Mode = GPIO_MODE_AF_INPUT;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);
  /* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
