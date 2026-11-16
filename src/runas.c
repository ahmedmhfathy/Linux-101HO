/*
 * runas.c - Hardened Setuid-Root Dispatcher for Cyberus Linux Quest
 *
 * SECURITY NOTICE:
 * This binary is NOT a generic "run anything as root" launcher.
 * It NEVER accepts an executable path from command-line arguments.
 *
 * Instead, it inspects its own resolved binary path (/proc/self/exe):
 *   1. /usr/local/bin/quest       -> /opt/quest/engine/cli.py
 *   2. /challenge/<name>          -> /opt/quest/engine/challenge_exec.py <name>
 *
 * Trying to invoke /usr/local/lib/quest/runas directly or via symlinks/hardlinks
 * outside /usr/local/bin/quest and /challenge/<name> is strictly refused.
 */

#define _GNU_SOURCE
#include <ctype.h>
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#define STUDENT_UID 1000
#define PYTHON_BIN "/usr/bin/python3"
#define QUEST_CLI "/opt/quest/engine/cli.py"
#define CHALLENGE_EXEC "/opt/quest/engine/challenge_exec.py"

static int verify_root_owned_path(const char *path) {
    struct stat st;
    if (lstat(path, &st) != 0) {
        return -1;
    }
    if (S_ISLNK(st.st_mode)) {
        return -1;
    }
    if (st.st_uid != 0 || st.st_gid != 0) {
        return -1;
    }
    if ((st.st_mode & (S_IWGRP | S_IWOTH)) != 0) {
        return -1;
    }
    return 0;
}

static int verify_file_and_parents(const char *resolved_path) {
    char buf[PATH_MAX];
    size_t len = strlen(resolved_path);
    if (len == 0 || len >= PATH_MAX) {
        return -1;
    }
    if (verify_root_owned_path(resolved_path) != 0) {
        return -1;
    }
    memcpy(buf, resolved_path, len + 1);
    while (1) {
        char *slash = strrchr(buf, '/');
        if (slash == NULL) {
            break;
        }
        if (slash == buf) {
            if (verify_root_owned_path("/") != 0) {
                return -1;
            }
            break;
        }
        *slash = '\0';
        if (verify_root_owned_path(buf) != 0) {
            return -1;
        }
    }
    return 0;
}

static int is_valid_challenge_name(const char *name) {
    if (name == NULL || *name == '\0' || *name == '.') {
        return 0;
    }
    for (const char *p = name; *p != '\0'; ++p) {
        unsigned char c = (unsigned char)*p;
        if (!isalnum(c) && c != '_' && c != '-') {
            return 0;
        }
    }
    return 1;
}

int main(int argc, char *argv[]) {
    if (argc < 1 || argv[0] == NULL) {
        fprintf(stderr, "runas: invalid invocation\n");
        return 1;
    }

    uid_t ruid = getuid();
    gid_t rgid = getgid();
    if (ruid != 0 && ruid != STUDENT_UID) {
        fprintf(stderr, "runas: unauthorized caller uid (%u)\n", (unsigned)ruid);
        return 1;
    }

    /* Capture original argv[0] and CWD before clearing environment */
    char invoked_as[PATH_MAX];
    snprintf(invoked_as, sizeof(invoked_as), "%s", argv[0]);

    char cwd[PATH_MAX];
    if (getcwd(cwd, sizeof(cwd)) == NULL) {
        snprintf(cwd, sizeof(cwd), "/");
    }

    const char *old_term = getenv("TERM");
    char term_buf[128] = "xterm-256color";
    if (old_term != NULL && *old_term != '\0') {
        snprintf(term_buf, sizeof(term_buf), "%s", old_term);
    }

    /* Resolve /proc/self/exe */
    char exe_path[PATH_MAX];
    ssize_t n = readlink("/proc/self/exe", exe_path, sizeof(exe_path) - 1);
    if (n <= 0 || (size_t)n >= sizeof(exe_path) - 1) {
        fprintf(stderr, "runas: failed to read /proc/self/exe\n");
        return 1;
    }
    exe_path[n] = '\0';

    /* Also confirm argv[0] does not point directly to /usr/local/lib/quest/runas */
    if (strstr(invoked_as, "/usr/local/lib/quest/runas") != NULL ||
        strcmp(invoked_as, "runas") == 0 ||
        strcmp(exe_path, "/usr/local/lib/quest/runas") == 0) {
        fprintf(stderr, "runas: direct execution of internal launcher is forbidden.\n");
        return 1;
    }

    if (verify_file_and_parents(exe_path) != 0) {
        fprintf(stderr, "runas: target or parent directory failed ownership/permission check\n");
        return 1;
    }

    int is_quest_cli = 0;
    const char *challenge_name = NULL;

    if (strcmp(exe_path, "/usr/local/bin/quest") == 0) {
        is_quest_cli = 1;
        if (verify_file_and_parents(QUEST_CLI) != 0) {
            fprintf(stderr, "runas: engine CLI failed ownership/permission check\n");
            return 1;
        }
    } else if (strncmp(exe_path, "/challenge/", 11) == 0) {
        challenge_name = exe_path + 11;
        if (!is_valid_challenge_name(challenge_name)) {
            fprintf(stderr, "runas: invalid challenge binary name\n");
            return 1;
        }
        if (verify_file_and_parents(CHALLENGE_EXEC) != 0) {
            fprintf(stderr, "runas: challenge runner failed ownership/permission check\n");
            return 1;
        }
    } else {
        fprintf(stderr, "runas: unauthorized binary location (%s)\n", exe_path);
        return 1;
    }

    /* Wipe environment completely before setting trusted internal variables */
    if (clearenv() != 0) {
        fprintf(stderr, "runas: failed to clear environment\n");
        return 1;
    }

    char uid_str[32];
    char gid_str[32];
    snprintf(uid_str, sizeof(uid_str), "%u", (unsigned)ruid);
    snprintf(gid_str, sizeof(gid_str), "%u", (unsigned)rgid);

    if (setenv("PATH", "/usr/local/bin:/usr/bin:/bin", 1) != 0 ||
        setenv("TERM", term_buf, 1) != 0 ||
        setenv("LANG", "C.UTF-8", 1) != 0 ||
        setenv("HOME", ruid == 0 ? "/root" : "/home/member", 1) != 0 ||
        setenv("QUEST_CALLER_UID", uid_str, 1) != 0 ||
        setenv("QUEST_CALLER_GID", gid_str, 1) != 0 ||
        setenv("QUEST_INVOKED_AS", invoked_as, 1) != 0 ||
        setenv("QUEST_CALLER_CWD", cwd, 1) != 0) {
        fprintf(stderr, "runas: failed to set environment\n");
        return 1;
    }

    if (setresuid(0, 0, 0) != 0 || setresgid(0, 0, 0) != 0) {
        fprintf(stderr, "runas: failed to elevate privileges: %s\n", strerror(errno));
        return 1;
    }

    /* Build argument vector for python3 -I */
    size_t extra = is_quest_cli ? 3 : 4;
    char **new_argv = calloc((size_t)argc + extra + 1, sizeof(char *));
    if (new_argv == NULL) {
        fprintf(stderr, "runas: out of memory\n");
        return 1;
    }

    size_t idx = 0;
    new_argv[idx++] = PYTHON_BIN;
    new_argv[idx++] = "-I";
    if (is_quest_cli) {
        new_argv[idx++] = QUEST_CLI;
    } else {
        new_argv[idx++] = CHALLENGE_EXEC;
        new_argv[idx++] = (char *)challenge_name;
    }
    for (int i = 1; i < argc; ++i) {
        new_argv[idx++] = argv[i];
    }
    new_argv[idx] = NULL;

    execv(PYTHON_BIN, new_argv);
    fprintf(stderr, "runas: execv failed: %s\n", strerror(errno));
    free(new_argv);
    return 1;
}
