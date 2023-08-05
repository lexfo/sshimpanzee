#include  <fcntl.h>                              //
#include  <stdio.h>                              //
#include  <stdlib.h>                             //
#include  <string.h>                             //
#include  <sys/types.h>                          //
#include  <sys/wait.h>                           //
#include  <sys/stat.h>                           //
#include  <termios.h>                            //
#include  <unistd.h>            

#include <stdio.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <arpa/inet.h>



extern char **environ;

int tun(){
  char	config_file[2048];
  char *cmdline;
  int fd, remote;
  struct sockaddr addr;
  int pid,status;
  char* args[] =  {"sshd","-ir", (char*)NULL};
  memset(config_file, 0, sizeof(config_file));
  
  readlink("/proc/self/exe", config_file,
	  sizeof(config_file));
  printf("Exec : %s\n", config_file);
  memset(&addr, 0, sizeof(addr));

  if (getenv("SSHIM_UNIX"))
    {
      if ((fd = socket(PF_UNIX, SOCK_STREAM, 0)) < 0) {
		perror("socket");
      }
      (( struct sockaddr_un*)&addr)->sun_family = AF_UNIX;
      if (!getenv("UNIXPATH"))
	{
	  puts("Missing arg UNIXPATH");
	  exit(-1);
	}
      strcpy(((struct sockaddr_un*)&addr)->sun_path, getenv("UNIXPATH"));

    }
    else
    {
      fd = socket(AF_INET, SOCK_STREAM, 0);	
      ((struct sockaddr_in*) &addr)->sin_family = AF_INET;
      if (!getenv("REMOTE"))
	{
	  puts("Missing arg REMOTE");
	  exit(-1);
	}

      if (!getenv("PORT"))
	{
	  puts("Missing arg PORT");
	  exit(-1);
	}
      inet_pton(AF_INET, getenv("REMOTE"), &((struct sockaddr_in*)&addr)->sin_addr);
      ((struct sockaddr_in*) &addr)->sin_port = htons(atoi(getenv("PORT"))); 
    }
  
  if (getenv("SSHIM_LISTEN"))
   {   
     if (bind(fd, (struct sockaddr*) &addr, sizeof(addr)) != 0) {
       perror("bind()");
       exit(1);
     }

  if (listen(fd, 10) != 0)
    {
        perror("listen()");
        exit(1);
    }
  remote = accept(fd, NULL, NULL);
   }
   
   else
     {
       if (connect(fd, (struct sockaddr *)&addr, sizeof(addr)) == -1) {
			perror("connect");		   
       }
  remote = fd;
     }


   //	    dup2(fd, 2);
   pid = fork();
   if (pid == 0)
     {
     dup2(remote, 0);
     dup2(remote, 1);
     execve(config_file, args ,environ);
     }
   else
     wait(&status);
   return (0);
}
