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
char continue_http;

void sighandler(int sig)
{
    int status;
    unlink(FIFO_IN);
    unlink(FIFO_OUT);
    wait(&status);
    continue_http = 0;
}


int tun(){
  char	config_file[2048];
  int fd0[2];
  int fd1[2];

  fd_set fds;
  int pid;
  int ret;
  int fifo_out;
  int fifo_in;
  struct sigaction sa;
  
 memset(&sa, 0, sizeof(sa));
 sa.sa_handler = sighandler;

 sigaction(SIGCHLD, &sa, NULL);
 sigaction(SIGKILL, &sa, NULL);
 
 
  char* args[] =  {"sshd","-ire", (char*)NULL};
  memset(config_file, 0, sizeof(config_file));
  
  readlink("/proc/self/exe", config_file,
	  sizeof(config_file));
  printf("Exec : %s\n", config_file);
  
  pipe(fd0);
  pipe(fd1);
  
  pid = fork();
  if (pid==0){ 
   dup2(fd0[0], 0);
   dup2(fd1[1], 1);
   close(fd0[1]);
   close(fd1[0]);
   
   execve(config_file, args ,environ); 
  }
  else{

    if (mkfifo(FIFO_OUT, S_IRWXU | S_IRWXO) != 0 || mkfifo(FIFO_IN, S_IRWXU  | S_IRWXO) != 0){
      //unlink(FIFO_IN);
      //unlink(FIFO_OUT);
     perror("mkfifo() error");
     //exit(-1);
    }
    
   
    if ((fifo_out = open(FIFO_OUT, O_RDWR)) < 0)
      {
      perror("open() out error");
      exit(-1);
      }
    if ((fifo_in = open(FIFO_IN, O_RDWR)) < 0)
      {
      perror("open() in error");
      exit(-1);
      }
    close(fd0[0]);
    close(fd1[1]);
    continue_http = 1;
   while(continue_http){
     FD_ZERO(&fds);
     FD_SET(fifo_in, &fds);
     FD_SET(fd1[0], &fds);

     ret = select(fifo_in + 1, &fds, NULL, NULL, NULL);
     if (ret < 0)
       perror("select() error");
     else
       {
	 if (FD_ISSET(fifo_in, &fds)){
	     ret = read(fifo_in, config_file, 2048);
	     config_file[ret] = 0;
	     write(fd0[1], config_file, ret);
	  }
	 if (FD_ISSET(fd1[0], &fds)){
	     ret = read(fd1[0], config_file, 2048);
	     config_file[ret] = 0;
	     write(fifo_out, config_file, ret);
	  }
       }
   }
   kill(pid, SIGKILL);
   waitpid(pid,&pid, WEXITED|WSTOPPED);  
   unlink(FIFO_IN);
   unlink(FIFO_OUT);
  

  }
  

  return (0);
}
