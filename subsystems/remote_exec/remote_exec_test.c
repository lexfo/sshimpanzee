#define _GNU_SOURCE
#define _POSIX_C_SOURCE 200809L

#include <sys/types.h>
#include <sys/mman.h>

#include <unistd.h>

#include <err.h>
#include <errno.h>
#include <string.h>
int main(int argc, char* argv2[])
{
  char argstring[2048];
  char *argv[64];
  char *p;
  int to_read = 0;
  char name[32];
  int cnt = 0;

  int i=0;
  int read_size=0x1000;

  char buf[0x1000];

  scanf("%31s %d", name, &to_read);

  printf("Scanf %s %d\n", name, to_read); 

  gets(argstring);
  gets(argstring);
  
  
  p = strtok(argstring, " ");
  argv[i] = p;
      
  while (p != NULL)
    {
      argv[i] = p;
      p = strtok (NULL, " ");
      
      i++;
    }

  
  argv[i] = NULL;
  
  int fd = memfd_create(name, 0);
  if (fd == -1)
    err(1, "%s failed", "memfd_create");
  else
    {

      while( to_read > 0 ){
        if ( to_read < read_size ){
         read_size = to_read;
        }                           

        cnt = read(0, buf, read_size );
        write(fd, buf, cnt);
        to_read -= cnt;
	if (cnt == 0)
	  break;
      }
      //const char * const argv[] = {"script", NULL};                                                                                                                                                                
      const char * const envp[] = {NULL};
      fexecve(fd, (char * const *) argv, (char * const *) envp);
    }

    err(1, "%s failed", "fexecve");
}
