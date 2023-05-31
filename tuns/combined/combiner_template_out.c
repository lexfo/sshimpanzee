#include <stdio.h>
#include <stdlib.h>

int tun(){
  char *selected_tun;
  selected_tun  = getenv("MODE");
  puts("EXPLOITING TUN COMBINER");
  if (selected_tun != 0)
    {
      printf("Trying tun name: %s\n", selected_tun);
    }
  else
    {
      puts("You need to provide a tun");
      exit(-1);
    }
  if (strcmp(selected_tun, "dns")==0) tun_dns();
if (strcmp(selected_tun, "icmp")==0) tun_icmp();
if (strcmp(selected_tun, "sock")==0) tun_sock();
if (strcmp(selected_tun, "proxysock")==0) tun_proxysock();
if (strcmp(selected_tun, "http_enc")==0) tun_http_enc();


}
