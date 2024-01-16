#define _GNU_SOURCE
#define _POSIX_C_SOURCE 200809L

#include <sys/types.h>
#include <sys/mman.h>

#include <unistd.h>

#include <err.h>
#include <errno.h>

extern char **environ;


int remote_exec_main()
{
  char argstring[2048];
  int to_read = 0;
  char name[32];
  int cnt = 0;

  int read_size=0x1000;
  char* argv[64];
  int i = 0;
  char *p;
  char buf[0x1000];
  puts("[name] [size] [arguments]");
  fsync(1);

  argv[0] = NULL;
  scanf("%s", name);
  printf("name : %s\n",name);

  scanf("%d", &to_read);
  printf("size : %d\n", to_read);

  gets(argstring);
  argstring[strlen(argstring)-1] = 0;
  printf("argstring : %s\n", argstring);
  
  p = argstring;
  argv[i] = p;
  i++;
  while (*p != 0)
  {
    if (*p == ' '){
      *p = 0;
      argv[i] = p+1;
      printf("%s\n",argv[i]);
      i++;
    }
    p++;
   
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
	if(read_size == 0)
	  break;
        cnt = read(0, buf, read_size );
        write(fd, buf, cnt);
        to_read -= cnt;
	if(cnt == -1)
	  break;
      }
      fexecve(fd, (char * const *) argv, environ);
    }
  
    err(1, "%s failed", "fexecve");
}

