#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <sys/time.h>
#include <unistd.h>
#include <sched.h>

struct sched_param sparam;
struct timespec delay;
struct timespec real;

struct timeval temps;
struct timezone tz;
struct tm *tm;

char timer[256]="                                                                                                                                               ";
main(){
	int i,j=0;
	sparam.sched_priority=1;  // on reschedule pour piloter correctement la table
	sched_setscheduler(0,SCHED_FIFO,&sparam);
	delay.tv_sec=0;
	delay.tv_nsec=1000000; /* delay in ns */
	
    while (1){
        nanosleep(&delay,&real);
	j=(j+1)%100;
	//sleep(1);
	gettimeofday(&temps,&tz);
	tm=localtime(&temps);
	timer[j]='a';
	timer[j+1]=0;
	printf("%.2d:%.2d:%.2d.%.2d %.4d %.2d %.2d\r",
			tm->tm_hour,tm->tm_min,tm->tm_sec,
			temps.tv_usec/10000,1900+tm->tm_year,
			tm->tm_mon,tm->tm_mday);
//	printf("%s\r", timer);
	timer[j]=32;
	fflush(NULL);
	}
}
