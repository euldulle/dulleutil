#include <cstring>
#include <iostream>
#include <thread>
#include <mutex>
#include <cstring>
#include <unistd.h>  // For close()
#include <arpa/inet.h>  // For socket functions

#include <wiringPi.h>
#include "libindi/indicom.h"

#include "config.h"
#include "indi_eul_focuser.h"

#define INFOCUS (0)
#define OUTFOCUS (1)

std::float eul_position;  // Shared variable
std::mutex data_mutex;  // Mutex to protect shared data

// We declare an auto pointer to EulFocuser.
static std::unique_ptr<EulFocuser> eulFocuser(new EulFocuser());

float EulFocuser::getPosition()
{
    std::lock_guard<std::mutex> lock(data_mutex);
    return eul_position;
    }
}

EulFocuser::EulFocuser()
{
    setVersion(CDRIVER_VERSION_MAJOR, CDRIVER_VERSION_MINOR);

    // Here we tell the base Focuser class what types of connections we can support
    setSupportedConnections(CONNECTION_NONE);

    // And here we tell the base class about our focuser's capabilities.
    SetCapability(FOCUSER_CAN_REL_MOVE | FOCUSER_CAN_ABS_MOVE);
}

void EulFocuser::udp_listener(int port) {
    int udp_socket;
    sockaddr_in server_addr;
    char buffer[32];
    
    // Create a UDP socket
    udp_socket = socket(AF_INET, SOCK_DGRAM, 0);
    if (udp_socket < 0) {
        std::cerr << "Failed to create socket" << std::endl;
        return;
    }

    // Setup server address structure
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(port);

    // Bind the socket to the port
    if (bind(udp_socket, (sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
        std::cerr << "Failed to bind socket" << std::endl;
        close(udp_socket);
        return;
    }

    std::cout << "Listening for UDP messages on port " << port << "..." << std::endl;

    while (true) {
        sockaddr_in client_addr;
        socklen_t addr_len = sizeof(client_addr);
        int bytes_received = recvfrom(udp_socket, buffer, sizeof(buffer) - 1, 0, (sockaddr*)&client_addr, &addr_len);
        if (bytes_received > 0) {
            buffer[bytes_received] = '\0';  // Null-terminate the string
            std::stringstream ss(buffer);

            // Lock the mutex before updating shared_data
            std::lock_guard<std::mutex> lock(data_mutex);
            ss >> eul_position; 
            std::cout << "Received message: " << message << std::endl;
        }
    }

    close(udp_socket);  // Close the socket when done
}

void EulFocuser::process_data() {
    while (true) {
        {
            // Lock the mutex before reading shared_data
            std::lock_guard<std::mutex> lock(data_mutex);
            if (!shared_data.empty()) {
                std::cout << "Processing data: " << shared_data << std::endl;
            }
        }
        std::this_thread::sleep_for(std::chrono::seconds(1));  // Simulate processing delay
    }
}

const char *EulFocuser::getDefaultName()
{
    return "Eul Focuser";
}

bool EulFocuser::initProperties()
{
    // initialize the parent's properties first
    INDI::Focuser::initProperties();

    wiringPiSetupGpio () ;
    wpMode = MODE_GPIO ;
    dir.nr=31;
    step.nr=33;
    enable.nr=22;
    pinMode(step.nr,OUTPUT);
    pinMode(dir.nr,OUTPUT);
    pinMode(enable.nr,OUTPUT);
    snprintf(dir.name,3,"DIR");
    snprintf(step.name,4, "STEP");
    snprintf(enable.name, 4, "ENAB");

    // TODO: Add any custom properties you need here.

    addAuxControls();

    return true;
}

void EulFocuser::ISGetProperties(const char *dev)
{
    INDI::Focuser::ISGetProperties(dev);

    // TODO: Call define* for any custom properties.
}

bool EulFocuser::updateProperties()
{
    INDI::Focuser::updateProperties();

    if (isConnected())
    {
        // TODO: Call define* for any custom properties only visible when connected.
    }
    else
    {
        // TODO: Call deleteProperty for any custom properties only visible when connected.
    }

    return true;
}

bool EulFocuser::ISNewNumber(const char *dev, const char *name, double values[], char *names[], int n)
{
    // Make sure it is for us.
    if (dev != nullptr && strcmp(dev, getDeviceName()) == 0)
    {
        // TODO: Check to see if this is for any of my custom Number properties.
    }

    // Nobody has claimed this, so let the parent handle it
    return INDI::Focuser::ISNewNumber(dev, name, values, names, n);
}

bool EulFocuser::ISNewSwitch(const char *dev, const char *name, ISState *states, char *names[], int n)
{
    // Make sure it is for us.
    if (dev != nullptr && strcmp(dev, getDeviceName()) == 0)
    {
        // TODO: Check to see if this is for any of my custom Switch properties.
    }

    // Nobody has claimed this, so let the parent handle it
    return INDI::Focuser::ISNewSwitch(dev, name, states, names, n);
}

bool EulFocuser::ISNewText(const char *dev, const char *name, char *texts[], char *names[], int n)
{
    // Make sure it is for us.
    if (dev != nullptr && strcmp(dev, getDeviceName()) == 0)
    {
        // TODO: Check to see if this is for any of my custom Text properties.
    }

    // Nobody has claimed this, so let the parent handle it
    return INDI::Focuser::ISNewText(dev, name, texts, names, n);
}

bool EulFocuser::ISSnoopDevice(XMLEle *root)
{
    // TODO: Check to see if this is for any of my custom Snoops. Fo shizzle.

    return INDI::Focuser::ISSnoopDevice(root);
}

bool EulFocuser::saveConfigItems(FILE *fp)
{
    INDI::Focuser::saveConfigItems(fp);

    // TODO: Call IUSaveConfig* for any custom properties I want to save.

    return true;
}

bool EulFocuser::Handshake()
{
    if (isSimulation())
    {
        LOGF_INFO("Connected successfuly to simulated %s.", getDeviceName());
        return true;
    }

    // NOTE: PortFD is set by the base class.

    // TODO: Any initial communciation needed with our focuser, we have an active
    // connection.
    //
    // Start the UDP listener thread 
    std::thread listener_thread(udp_listener, 2345);

    // Start the data processing thread
    std::thread processor_thread(process_data);

    // Wait for both threads to finish (they won’t, because of the infinite loops)
    listener_thread.join();
    processor_thread.join();

    return true;
}

void EulFocuser::TimerHit()
{
    if (!isConnected())
        return;

    // TODO: Poll your device if necessary. Otherwise delete this method and it's
    // declaration in the header file.

    LOG_INFO("timer hit");

    // If you don't call SetTimer, we'll never get called again, until we disconnect
    // and reconnect.
    //SetTimer(POLLMS);
}

IPState EulFocuser::MoveFocuser(FocusDirection dir, int speed, uint16_t duration)
{
    // NOTE: This is needed if we don't specify FOCUSER_CAN_ABS_MOVE
    // TODO: Actual code to move the focuser. You can use IEAddTimer to do a
    // callback after "duration" to stop your focuser.
    LOGF_INFO("MoveFocuser: %d %d %d", dir, speed, duration);
    return IPS_OK;
}

IPState EulFocuser::MoveAbsFocuser(uint32_t targetTicks)
{
    // NOTE: This is needed if we do specify FOCUSER_CAN_ABS_MOVE
    // TODO: Actual code to move the focuser.
    LOGF_INFO("MoveAbsFocuser: %d", targetTicks);
    return IPS_OK;
}

IPState EulFocuser::MoveRelFocuser(FocusDirection dir, uint32_t ticks)
{
    // NOTE: This is needed if we do specify FOCUSER_CAN_REL_MOVE
    // TODO: Actual code to move the focuser.

    do_move(dir, ticks);

    LOGF_INFO("MoveRelFocuser: %d %d", dir, ticks);
    return IPS_OK;
}

bool EulFocuser::Connect()
{
    if(false)    // FIXME if needed
    {
        DEBUG(INDI::Logger::DBG_ERROR, "Failed to connect");
        return false;
    }

    DEBUG(INDI::Logger::DBG_SESSION, "Eul Focuser.");
    return true;
}

bool EulFocuser::Disconnect()
{
    DEBUG(INDI::Logger::DBG_SESSION, "Eul Focuser disconnected successfully.");
    return true;
}

bool EulFocuser::AbortFocuser()
{
    // NOTE: This is needed if we do specify FOCUSER_CAN_ABORT
    // TODO: Actual code to stop the focuser.
    LOG_INFO("AbortFocuser");
    return true;
}

bool EulFocuser::sendCommand(const char * cmd, char * res, bool silent, int nret)
{
    int nbytes_written = 0, nbytes_read = 0, rc = -1;


    LOGF_DEBUG("CMD <%s>", cmd);

    if ((rc = tty_write_string(PortFD, cmd, &nbytes_written)) != TTY_OK)
    {
        char errstr[MAXRBUF] = {0};
        tty_error_msg(rc, errstr, MAXRBUF);
        if (!silent)
            LOGF_ERROR("Serial write error: %s.", errstr);
        return false;
    }

    rc = tty_read(PortFD, res, nret, EF_TIMEOUT, &nbytes_read);

    if (rc != TTY_OK)
    {
        char errstr[MAXRBUF] = {0};
        tty_error_msg(rc, errstr, MAXRBUF);
        if (!silent)
            LOGF_ERROR("Serial read error: %s.", errstr);
        return false;
    }
    return true;
    }    

bool EulFocuser::gprint(gpin pin){
    fprintf(stderr," %4s #%d = %d\n", pin.name, pin.nr, pin.state);
    return true;
}

bool EulFocuser::gwrite(gpin *pin, int state ){
    digitalWrite(pin->nr, state);
    pin->state=state;
    //gprint(*pin);
    return true;
}

bool EulFocuser::gclr(gpin *pin){
    gwrite(pin, 0);
    return true;
}

bool EulFocuser::gset(gpin *pin){
    gwrite(pin, 1);
    return true;
}

int EulFocuser::gread(gpin *pin){
    pin->state=digitalRead(pin->nr);
    return pin->state;
}

bool EulFocuser::gtoggle(gpin *pin){
    gwrite(pin, !gread(pin));
    return true;
}

bool EulFocuser::do_move(int newdir, uint32_t microns){
    static int olddir, pos;
    int step_inc;
    int32_t count;

    gclr(&enable);

    count=(usteps_per_mm*microns)/1000;
    if (olddir!=newdir){
        count=count+backlash[newdir];
    }
    olddir=newdir;
    fprintf(stderr,"initial %d %d\n", count, microns);

    if (newdir==INFOCUS){  // infocus 
        step_inc=-1;
        gclr(&dir);
    }
    else{                   // outfocus
        step_inc=1;
        gset(&dir);
    }

    while (count>0){
        --count;
        gset(&step);
        usleep(delay_step);
        gclr(&step);
        usleep(delay_step);
        pos=pos+step_inc;
    }
    //step_pos=(step_pos+
    fprintf(stderr, "ustep pos # %d\n", pos);
    gset(&enable);
    return true;
}
