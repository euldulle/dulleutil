/*
   MPU6050 DMP6

   Digital Motion Processor or DMP performs complex motion processing tasks.
   - Fuses the data from the accel, gyro, and external magnetometer if applied, 
   compensating individual sensor noise and errors.
   - Detect specific types of motion without the need to continuously monitor 
   raw sensor data with a microcontroller.
   - Reduce workload on the microprocessor.
   - Output processed data such as quaternions, Euler angles, and gravity vectors.

   The code includes an auto-calibration and offsets generator tasks. Different 
   output formats available.

   This code is compatible with the teapot project by using the teapot output format.

Circuit: In addition to connection 3.3v, GND, SDA, and SCL, this sketch
depends on the MPU6050's INT pin being connected to the Arduino's
external interrupt #0 pin.

The teapot processing example may be broken due FIFO structure change if using DMP
6.12 firmware version. 

Find the full MPU6050 library documentation here:
https://github.com/ElectronicCats/mpu6050/wiki

 */
#include "WiFi.h"
#include "AsyncUDP.h"
#include "ADS1X15.h"
char message[512];
const char * ssid = "ed";
const char * password = "gsin2hhlx48f6v25jlgz";
const char * wrtSsid = "OpenWrt";
const char * wrtPassword = "Auvma2TKF9gZZYmW";

AsyncUDP udp;

#include "I2Cdev.h"
#include "MPU6050_6Axis_MotionApps20.h"
//#include "MPU6050_6Axis_MotionApps612.h" // Uncomment this library to work with DMP 6.12 and comment on the above library.

/* MPU6050 default I2C address is 0x68*/
MPU6050 mpu;
//MPU6050 mpu(0x69); //Use for AD0 high
//MPU6050 mpu(0x68, &Wire1); //Use for AD0 low, but 2nd Wire (TWI/I2C) object.
ADS1115 ADS(0x48);

/* OUTPUT FORMAT DEFINITION-------------------------------------------------------------------------------------------
   - Use "OUTPUT_READABLE_QUATERNION" for quaternion commponents in [w, x, y, z] format. Quaternion does not 
   suffer from gimbal lock problems but is harder to parse or process efficiently on a remote host or software 
   environment like Processing.

   - Use "OUTPUT_READABLE_EULER" for Euler angles (in degrees) output, calculated from the quaternions coming 
   from the FIFO. EULER ANGLES SUFFER FROM GIMBAL LOCK PROBLEM.

   - Use "OUTPUT_READABLE_YAWPITCHROLL" for yaw/pitch/roll angles (in degrees) calculated from the quaternions
   coming from the FIFO. THIS REQUIRES GRAVITY VECTOR CALCULATION.
   YAW/PITCH/ROLL ANGLES SUFFER FROM GIMBAL LOCK PROBLEM.

   - Use "OUTPUT_READABLE_REALACCEL" for acceleration components with gravity removed. The accel reference frame
   is not compensated for orientation. +X will always be +X according to the sensor.

   - Use "OUTPUT_READABLE_WORLDACCEL" for acceleration components with gravity removed and adjusted for the world
   reference frame. Yaw is relative if there is no magnetometer present.

   -  Use "OUTPUT_TEAPOT" for output that matches the InvenSense teapot demo. 
   -------------------------------------------------------------------------------------------------------------------------------*/ 
//#define OUTPUT_READABLE_YAWPITCHROLL
#define LED_BUILTIN 4
#define OUTPUT_READABLE_QUATERNION
//#define OUTPUT_READABLE_EULER
//#define OUTPUT_READABLE_REALACCEL
//#define OUTPUT_READABLE_WORLDACCEL
//#define OUTPUT_TEAPOT

int const INTERRUPT_PIN = 2;  // Define the interruption #0 pin
bool blinkState;

/*---MPU6050 Control/Status Variables---*/
bool DMPReady = false;  // Set true if DMP init was successful
uint8_t MPUIntStatus;   // Holds actual interrupt status byte from MPU
uint8_t connected=0;    // Wifi status
uint8_t devStatus;      // Return status after each device operation (0 = success, !0 = error)
uint16_t packetSize;    // Expected DMP packet size (default is 42 bytes)
uint8_t FIFOBuffer[64]; // FIFO storage buffer

/*---Orientation/Motion Variables---*/ 
Quaternion q;           // [w, x, y, z]         Quaternion container
VectorInt16 aa;         // [x, y, z]            Accel sensor measurements
VectorInt16 gy;         // [x, y, z]            Gyro sensor measurements
VectorInt16 aaReal;     // [x, y, z]            Gravity-free accel sensor measurements
VectorInt16 aaWorld;    // [x, y, z]            World-frame accel sensor measurements
VectorFloat gravity;    // [x, y, z]            Gravity vector
float euler[3];         // [psi, theta, phi]    Euler angle container
float ypr[3];           // [yaw, pitch, roll]   Yaw/Pitch/Roll container and gravity vector

/*-Packet structure for InvenSense teapot demo-*/ 
uint8_t teapotPacket[14] = { '$', 0x02, 0, 0, 0, 0, 0, 0, 0, 0, 0x00, 0x00, '\r', '\n' };

/*------Interrupt detection routine------*/
volatile bool MPUInterrupt = false;     // Indicates whether MPU6050 interrupt pin has gone high
void DMPDataReady() {
    MPUInterrupt = true;
}

void setup() {
#if I2CDEV_IMPLEMENTATION == I2CDEV_ARDUINO_WIRE
    Wire.begin();
    Wire.setClock(400000); // 400kHz I2C clock. Comment on this line if having compilation difficulties
#elif I2CDEV_IMPLEMENTATION == I2CDEV_BUILTIN_FASTWIRE
    Fastwire::setup(400, true);
#endif

    Serial.begin(115200); //115200 is required for Teapot Demo output
    while (!Serial);

    /*Initialize device*/
    Serial.println(F("Initializing I2C devices..."));
    mpu.initialize();
    pinMode(INTERRUPT_PIN, INPUT);

    /*Verify connection*/
    Serial.println(F("Testing MPU6050 connection..."));
    if(mpu.testConnection() == false){
        Serial.println("MPU6050 connection failed");
        while(true);
    }
    else {
        Serial.println("MPU6050 connection successful");
    }

    /*Wait for Serial input*/
    //  Serial.println(F("\nSend any character to begin: "));
    //  while (Serial.available() && Serial.read()); // Empty buffer
    //  while (!Serial.available());                 // Wait for data
    while (Serial.available() && Serial.read()); // Empty buffer again
    
    WiFi.mode(WIFI_STA);
    while(!connected) {
      WiFi.begin(ssid, password);
      if (WiFi.waitForConnectResult(5000) != WL_CONNECTED) {
        Serial.println("OpenWRT WiFi Failed");
        delay(1000);
        
        WiFi.begin(wrtSsid, wrtPassword);
        if (WiFi.waitForConnectResult(5000) != WL_CONNECTED) {
          Serial.println("ed WiFi Failed");
          delay(5000);
          }
        else{
          connected=1;
          Serial.println("Connected (ed)");
          }
        }
      else{
        connected=1;
        Serial.println("Connected (OpenWrt)");
        }
    }

    Serial.println("Wifi Ok");

    /* Initializate and configure the DMP*/
    Serial.println(F("Initializing DMP..."));
    devStatus = mpu.dmpInitialize();

    /* Supply your gyro offsets here, scaled for min sensitivity
       /home/fmeyer/Arguino/calibration/gyrocalib 
       /home/fmeyer/Arguino/calibration/calibration.ino
       acelX acelY acelZ giroX giroY giroZ
       sensor 2 (RA connector) -204    473     1354    101     -32     81
       sensor tak Rigth connector :-1489   -105    644     -35     -60     38
       */

    mpu.setXAccelOffset(-1489);
    mpu.setYAccelOffset(-105);
    mpu.setZAccelOffset(644);
    mpu.setXGyroOffset(-35);
    mpu.setYGyroOffset(-60);
    mpu.setZGyroOffset(38);
    
    /* Making sure it worked (returns 0 if so) */ 
    if (devStatus == 0) {
        // mpu.CalibrateAccel(6);  // Calibration Time: generate offsets and calibrate our MPU6050
        // mpu.CalibrateGyro(6);
        Serial.println("These are the Active offsets: ");
        mpu.PrintActiveOffsets();
        Serial.println(F("Enabling DMP..."));   //Turning ON DMP
        mpu.setDMPEnabled(true);

        /*Enable Arduino interrupt detection*/
        Serial.print(F("Enabling interrupt detection (Arduino external interrupt "));
        Serial.print(digitalPinToInterrupt(INTERRUPT_PIN));
        Serial.println(F(")..."));
        attachInterrupt(digitalPinToInterrupt(INTERRUPT_PIN), DMPDataReady, RISING);
        MPUIntStatus = mpu.getIntStatus();

        /* Set the DMP Ready flag so the main loop() function knows it is okay to use it */
        Serial.println(F("DMP ready! Waiting for first interrupt..."));
        DMPReady = true;
        packetSize = mpu.dmpGetFIFOPacketSize(); //Get expected DMP packet size for later comparison
    } 
    else {
        Serial.print(F("DMP Initialization failed (code ")); //Print the error code
        Serial.print(devStatus);
        Serial.println(F(")"));
        // 1 = initial memory load failed
        // 2 = DMP configuration updates failed
    }
    pinMode(LED_BUILTIN, OUTPUT);
    udp.listen(2346);
}

void loop() {
    if (!DMPReady) return; // Stop the program if DMP programming fails.

    /* Read a packet from FIFO */
    if (mpu.dmpGetCurrentFIFOPacket(FIFOBuffer)) { // Get the Latest packet 
#ifdef OUTPUT_READABLE_YAWPITCHROLL
        /* Display Euler angles in degrees */
        mpu.dmpGetQuaternion(&q, FIFOBuffer);
        mpu.dmpGetGravity(&gravity, &q);
        mpu.dmpGetYawPitchRoll(ypr, &q, &gravity);
        Serial.print("ypr\t");
        Serial.print(ypr[0] * 180/M_PI);
        Serial.print("\t");
        Serial.print(ypr[1] * 180/M_PI);
        Serial.print("\t");
        Serial.println(ypr[2] * 180/M_PI);
#endif

#ifdef OUTPUT_READABLE_QUATERNION
        /* Display Quaternion values in easy matrix form: [w, x, y, z] */
        mpu.dmpGetQuaternion(&q, FIFOBuffer);
        snprintf(message,511,"w%fwa%fab%fbc%fc\r\n",q.w,q.x,q.y,q.z);
        Serial.print(message);
        udp.broadcast(message);
#endif

#ifdef OUTPUT_READABLE_EULER
        /* Display Euler angles in degrees */
        mpu.dmpGetQuaternion(&q, FIFOBuffer);
        mpu.dmpGetEuler(euler, &q);
        Serial.println("euler:");
        snprintf(message,511,"y%fyp%fpr%fr\r\n",euler[0] * 180/M_PI,
                                         euler[1] * 180/M_PI,
                                         euler[2] * 180/M_PI);
        Serial.print(message);
        udp.broadcast(message);
#endif

#ifdef OUTPUT_READABLE_REALACCEL
        /* Display real acceleration, adjusted to remove gravity */
        mpu.dmpGetQuaternion(&q, FIFOBuffer);
        mpu.dmpGetAccel(&aa, FIFOBuffer);
        mpu.dmpGetGravity(&gravity, &q);
        mpu.dmpGetLinearAccel(&aaReal, &aa, &gravity);
        Serial.print("areal\t");
        Serial.print(aaReal.x);
        Serial.print("\t");
        Serial.print(aaReal.y);
        Serial.print("\t");
        Serial.println(aaReal.z);
#endif

#ifdef OUTPUT_READABLE_WORLDACCEL
        /* Display initial world-frame acceleration, adjusted to remove gravity
           and rotated based on known orientation from Quaternion */
        mpu.dmpGetQuaternion(&q, FIFOBuffer);
        mpu.dmpGetAccel(&aa, FIFOBuffer);
        mpu.dmpGetGravity(&gravity, &q);
        mpu.dmpGetLinearAccel(&aaReal, &aa, &gravity);
        mpu.dmpGetLinearAccelInWorld(&aaWorld, &aaReal, &q);
        Serial.print("aworld\t");
        Serial.print(aaWorld.x);
        Serial.print("\t");
        Serial.print(aaWorld.y);
        Serial.print("\t");
        Serial.println(aaWorld.z);
#endif

#ifdef OUTPUT_TEAPOT
        /* Display quaternion values in InvenSense Teapot demo format */
        teapotPacket[2] = FIFOBuffer[0];
        teapotPacket[3] = FIFOBuffer[1];
        teapotPacket[4] = FIFOBuffer[4];
        teapotPacket[5] = FIFOBuffer[5];
        teapotPacket[6] = FIFOBuffer[8];
        teapotPacket[7] = FIFOBuffer[9];
        teapotPacket[8] = FIFOBuffer[12];
        teapotPacket[9] = FIFOBuffer[13];
        Serial.write(teapotPacket, 14);
        teapotPacket[11]++; // PacketCount, loops at 0xFF on purpose
#endif
        delay(100);
        /* Blink LED to indicate activity */
        blinkState = !blinkState;
        digitalWrite(LED_BUILTIN, blinkState);
    }
}
