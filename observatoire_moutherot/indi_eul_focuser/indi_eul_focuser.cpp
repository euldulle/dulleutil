#include <cstring>
#include <iostream>
#include <thread>
#include <mutex>
#include <cstring>
#include <fcntl.h>
#include <unistd.h>  // For close()
#include <arpa/inet.h>  // For socket functions
#include <cmath>

#include <wiringPi.h>
#include "libindi/indicom.h"

#include "config.h"
#include "indi_eul_focuser.h"

#define INFOCUS (0)
#define OUTFOCUS (1)

std::mutex data_mutex;  // Mutex to protect shared data

// We declare an auto pointer to EulFocuser.
static std::unique_ptr<EulFocuser> eulFocuser(new EulFocuser());
float EulFocuser::eul_position;

EulFocuser::EulFocuser()
{
    setVersion(CDRIVER_VERSION_MAJOR, CDRIVER_VERSION_MINOR);

    // Here we tell the base Focuser class what types of connections we can support
    setSupportedConnections(CONNECTION_NONE);

    // And here we tell the base class about our focuser's capabilities.
    SetCapability(FOCUSER_CAN_REL_MOVE | FOCUSER_CAN_ABS_MOVE);
}

void EulFocuser::readPosition()
{
    char buffer[32];
    sockaddr_in client_addr;
    socklen_t addr_len = sizeof(client_addr);
    int bytes_received;

    sockaddr_in server_addr;
    int udp_socket;
    int port=2345;

    // Create a UDP socket
    udp_socket= socket(AF_INET, SOCK_DGRAM, 0);
    if (udp_socket < 0) {
        std::cerr << "Failed to create socket" << std::endl;
        return;
    }

    // Setup server address structure
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(port);
    // fprintf(stderr," going to be Listening for UDP messages on port %d.",port);

    if (bind(udp_socket, (sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
        fprintf(stderr," Socket failed ");
        return ;
    }

    int flags = fcntl(udp_socket, F_GETFL, 0);
    fcntl(udp_socket, F_SETFL, flags | O_NONBLOCK);
    fprintf(stderr," Socket ok ");

    while(true){
        bytes_received = recvfrom(udp_socket, buffer, sizeof(buffer) - 1, 0, (sockaddr*)&client_addr, &addr_len);
        if (bytes_received > 0) {
            buffer[bytes_received] = '\0';  // Null-terminate the string
            // std::string message(buffer);
            std::stringstream ss(buffer);

            // Lock the mutex before updating shared_data
            std::lock_guard<std::mutex> lock(data_mutex);
            ss >> eul_position; 
            eul_position*=1000;
            // fprintf(stderr,"pos %f\n",eul_position);
            // std::cout << "Received message: " << buffer ;
        }
        else{
            // std::cout << "silence " << std::endl;
            std::this_thread::sleep_for(std::chrono::milliseconds(50));  // Simulate processing delay
        }
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
    addDebugControl();

    // Set limits as per documentation
    FocusAbsPosN[0].min  = 100;
    FocusAbsPosN[0].max  = 9100;
    FocusAbsPosN[0].step = 10;
    strncpy(FocusRelPosN[0].label, "um", MAXINDILABEL);
    strncpy(FocusAbsPosN[0].label, "um", MAXINDILABEL);
    strncpy(FocusMaxPosN[0].label, "um", MAXINDILABEL);
    FocusMaxPosN[0].value=9100;

    FocusRelPosN[0].min  = 0;
    FocusRelPosN[0].max  = 2000;
    FocusRelPosN[0].step = 10;

    FocusSpeedN[0].min  = 1;
    FocusSpeedN[0].max  = 254;
    FocusSpeedN[0].step = 10;

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

void EulFocuser::TimerHit()
{
    LOG_INFO("timer hit");
    //readPosition();
    if (!isConnected())
        return;

    // TODO: Poll your device if necessary. Otherwise delete this method and it's
    // declaration in the header file.
    //readPosition();
    //fprintf(stderr,"eulpos: %.3f\n",eul_position);
    //fflush(stderr);
    FocusAbsPosN[0].value = eul_position;
    //FocusAbsPosN[0].value = 5000;
    IDSetNumber(&FocusAbsPosNP, nullptr);

    LOG_INFO("timer hit");

    // If you don't call SetTimer, we'll never get called again, until we disconnect
    // and reconnect.
    SetTimer(1000);
}

IPState EulFocuser::MoveFocuser(FocusDirection dir, int speed, uint16_t duration)
{
    // NOTE: This is needed if we don't specify FOCUSER_CAN_ABS_MOVE
    // TODO: Actual code to move the focuser. You can use IEAddTimer to do a
    // callback after "duration" to stop your focuser.
    LOGF_INFO("MoveFocuser: %d %d %d", dir, speed, duration);
    return IPS_OK;
}

IPState EulFocuser::MoveAbsFocuser(uint32_t targetPos)
{
    // NOTE: This is needed if we do specify FOCUSER_CAN_ABS_MOVE
    // TODO: Actual code to move the focuser.
    //eul_goto(targetPos);
    static FocusDirection last_direction;
    uint32_t maxmove=60, count=0;
    uint32_t current, usteps, backl;
    int32_t delta_dist;
    FocusDirection direction;

    current=(uint32_t)eul_position;
    delta_dist=targetPos-current;

    direction = delta_dist < 0 ? FOCUS_INWARD : FOCUS_OUTWARD;
    usteps=get_usteps_from_dist(delta_dist,usteps_per_mm); // delta_dist in um

    backl=backlash[0];
    if (direction==last_direction) backl=0;
    else if (direction>last_direction) backl=backlash[1];

    usteps=backl*(direction!=last_direction);
    last_direction=direction;
    fprintf(stderr,"EulFocuser::MoveAbsFocuser current %u target %u dir %d\n",current, targetPos, direction);
    while(labs(targetPos-current)>accuracy && count<maxmove) {
        ++count;
        usteps=get_usteps_from_dist(current-targetPos,usteps_per_mm);
        usteps=backl+std::max((uint32_t)4,usteps);
        fprintf(stderr,"  MoveAbsFocuser looping current %u target %u dir %d\n",current, targetPos, direction);
        do_move(direction,usteps);
        last_direction=direction;
        current=(uint32_t)eul_position;
        delta_dist=targetPos-current;
        direction = delta_dist < 0 ? FOCUS_INWARD : FOCUS_OUTWARD;
    }


    LOGF_INFO("MoveAbsFocuser: %d", targetPos);

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
    //std::thread listener_thread(udp_listener, 2345);
    //DEBUG(INDI::Logger::DBG_SESSION, "starting listener ");
    // udp_socket=init_udp_listener(2345);
    //readPosition();
    SetTimer(getCurrentPollingPeriod());
    // Start the data processing thread
    // readThread = new std::thread processor_thread(readPosition, this);
    readThread = new std::thread(&EulFocuser::readPosition);
    DEBUG(INDI::Logger::DBG_SESSION, "starting processor ");

    fflush(stderr);
    DEBUG(INDI::Logger::DBG_SESSION, "Eul Focuser.");
    return true;
}

bool EulFocuser::Disconnect()
{
    DEBUG(INDI::Logger::DBG_SESSION, "Eul Focuser disconnected successfully.");
    readThread->join();
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

uint32_t EulFocuser::get_usteps_from_dist(int32_t dist,uint32_t rate){
    // dist is in um
    // rate is in usteps per mm
    //
    // return value is in usteps
    //return abs(int(ceil(dist)*rate))
    return labs(dist)*rate/1000;
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

bool EulFocuser::do_move(FocusDirection newdir, uint32_t microns){
    static FocusDirection olddir;
    static int pos;
    int step_inc;
    int32_t count;

    gclr(&enable);

    count=(usteps_per_mm*microns)/1000;
    if (olddir!=newdir){
        count=count+backlash[newdir];
    }
    olddir=newdir;
    fprintf(stderr,"do_move initial %d %d\n", count, microns);

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

    gset(&enable);
    return true;
}
