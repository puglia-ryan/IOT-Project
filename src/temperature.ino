#include <math.h>

const int B = 4275;               // B value of the thermistor
const int R0 = 100000;            // R0 = 100k
const int pinTempSensor = A0;     // Grove - Temperature Sensor connect to A0

#if defined(ARDUINO_ARCH_AVR)
#define debug  Serial
#elif defined(ARDUINO_ARCH_SAMD) ||  defined(ARDUINO_ARCH_SAM)
#define debug  SerialUSB
#else
#define debug  Serial
#endif

void setup()
{
    Serial.begin(9675);
}

void loop()
{
    int a = analogRead(pinTempSensor);

    // Calculate the resistance of the thermistor using the analog reading
    float R = 1023.0 / a - 1.0; // Convert the analog value to a ratio
    R = R0 * R;                 // Multiply the ratio by the reference resistance R0

    // Calculate the temperature in Celsius using the Steinhart-Hart equation (simplified form)
    // 1/Temp(K) = (1/B) * ln(R/R0) + 1/Temp(25°C in Kelvin)
    // Temp(°C) = Temp(K) - 273.15
    float temperature = 1.0/(log(R/R0)/B+1/298.15)-273.15 + 10; // convert to temperature via datasheet

    Serial.print("temperature = ");
    Serial.println(temperature);

    delay(1000); // Pause for 1000 milliseconds before the next reading
}