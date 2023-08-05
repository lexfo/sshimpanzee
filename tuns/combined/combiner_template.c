#include <stdio.h>
#include <stdlib.h>

int tun(){
  char *selected_tun;
  selected_tun  = getenv("MODE");
  if (selected_tun != 0)
    {
      printf("Trying tun name: %s\n", selected_tun);
    }
  else
    {
      puts("You need to provide a tun, use TUN env var");
      exit(-1);
    }
  <CONTENT>

}
