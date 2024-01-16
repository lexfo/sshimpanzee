from src.cmd import run_cmd

def generate_subsystem_string(opt):
    subsys_str = ""
    for i in opt.subsystems:
        if opt.subsystems[i]["enabled"]:
            exe = opt.subsystems[i]['exec'].replace('"','\\"')
            subsys_str += f"Subsystem {opt.subsystems[i]['name']} {exe}\\n"
    return subsys_str


def remote_exec(opt):
    print("[+] build with internal remote exec")
    cflags = f"-DREMOTE_EXEC_INTERNAL='\\\"{opt.subsystems['remote_exec']['exec']}\\\"'"
    ldflags = "-lremote_exec"

    print("\t-> Building remote-exec stub")
    run_cmd("cd subsystems/remote_exec/; gcc -c -o remote_exec.o remote_exec.c; ar rcs ../../build/libremote_exec.a remote_exec.o")
    extraconfig = ""
    return cflags, ldflags, extraconfig

def internal_sftp(opt):
    return "","",""
