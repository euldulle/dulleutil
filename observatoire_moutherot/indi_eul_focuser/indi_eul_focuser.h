#pragma once

#include "libindi/indifocuser.h"
class EulFocuser : public INDI::Focuser
{
public:
    EulFocuser();
    virtual ~EulFocuser() = default;

    virtual const char *getDefaultName() override;

    virtual bool initProperties() override;
    virtual bool updateProperties() override;

    virtual void ISGetProperties(const char *dev) override;
    virtual bool ISNewNumber(const char *dev, const char *name, double values[], char *names[], int n) override;
    virtual bool ISNewSwitch(const char *dev, const char *name, ISState *states, char *names[], int n) override;
    virtual bool ISNewText(const char *dev, const char *name, char *texts[], char *names[], int n) override;
    virtual bool ISSnoopDevice(XMLEle *root) override;

    virtual void TimerHit() override;

protected:
    virtual bool saveConfigItems(FILE *fp) override;

    virtual IPState MoveFocuser(FocusDirection dir, int speed, uint16_t duration);
    virtual IPState MoveAbsFocuser(uint32_t targetTicks);
    virtual IPState MoveRelFocuser(FocusDirection dir, uint32_t ticks);
    virtual bool AbortFocuser();

private:
    virtual bool Connect();
    virtual bool Disconnect();
    bool sendCommand(const char * cmd, char * res = nullptr, bool silent = false, int nret = 0);
    static const uint8_t EF_TIMEOUT { 3 };
    // int udp_socket;
    static int init_udp_listener(int port);
    static uint32_t get_usteps_from_dist(int32_t dist,uint32_t rate);
    static void udp_listener(int port);

   typedef struct {
        int nr;
        int state;
        char name[16];
        } gpin;

    gpin step, dir, enable;
    std::thread *readThread;

    static float eul_position;  // Shared variable
    static int udp_port;
    static void process_data();

    int  last_direction=1;
    uint32_t usteps_per_mm=750;
    uint32_t usteps_per_step=32;
    uint32_t delay_step=400;
    uint32_t backlash[2]={
        0, // [0] = backlash when going from OUTFOCUS to INFOCUS
        0  // [1] = backlash when going from INFOCUS to OUTFOCUS
    };
    uint32_t accuracy=15; // accuracy = 8 * fd^2 * wl / rms (final unit is um)
                          // 8 is a constant
                          // fd f/D ratio, eg 8
                          // wl = wavelength in um, eg band=0.6um)
                          // rms = max tolerated impact on wavefront (eg rms=1/8)

    int wpMode ;

    bool gprint(gpin pin);
    bool gwrite(gpin *pin, int state );
    bool gclr(gpin *pin);
    bool gset(gpin *pin);
    int gread(gpin *pin);
    bool gtoggle(gpin *pin);
    bool do_move(FocusDirection newdir, uint32_t microns);
    uint32_t getPosition(void);
    static void readPosition(void);

};
